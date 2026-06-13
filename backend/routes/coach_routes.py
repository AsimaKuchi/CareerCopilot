"""
routes/coach_routes.py - Personal Career Coach (multi-turn).

Endpoints (under /api):
  POST   /coach/sessions                 -- Create a coaching session (returns id + first msg)
  GET    /coach/sessions                 -- List user's coach sessions (newest first)
  GET    /coach/sessions/{session_id}    -- Fetch a single session with all messages
  POST   /coach/sessions/{session_id}/messages
                                         -- Send a user message, get streaming AI reply
  POST   /coach/sessions/{session_id}/synthesize
                                         -- After enough discovery, ask the coach to
                                            synthesize the conversation into 3 career
                                            paths + a rationale per path
  DELETE /coach/sessions/{session_id}    -- Delete the session

Persona: "Brutal Mentor" - direct, no fluff, treats user as a competent adult,
calls out vague thinking. See COACH_SYSTEM_PROMPT below.

Refactored from a monolithic server (Feb 2026).
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import db, logger, EMERGENT_LLM_KEY, get_current_user
from profile_schema import get_skill_names
from encryption import decrypt_sensitive_data
from stripe_routes import check_usage_limit, increment_usage

router = APIRouter()


# ============================================================
# COACH PERSONA - "Brutal Mentor"
# ============================================================
COACH_SYSTEM_PROMPT = """You are a Direct & Honest career mentor. Your job is to help the user
get unstuck about their career without coddling them.

CRITICAL RULES:
1. NO FLUFF. No "great question!" No "that's a really interesting point." Get to substance immediately.
2. TREAT THE USER AS A COMPETENT ADULT. Don't soften bad news. Don't pad with empathy theater.
3. CALL OUT VAGUE THINKING. If the user says "I'm not sure what I want," push back: ask one
   sharp question that forces specificity. Vague answers get a follow-up, not validation.
4. EVERY MESSAGE ENDS WITH A QUESTION OR A CONCRETE CHALLENGE. Never a soft "let me know what you think."
5. KEEP MESSAGES SHORT. 80-150 words MAX. Long therapy paragraphs are forbidden.
6. ASK ONE OR TWO QUESTIONS AT A TIME, NOT FIVE. Force depth, not breadth.
7. WHEN THE USER GIVES YOU A REAL ANSWER, STATE WHAT YOU LEARNED ABOUT THEM before asking next.
   Show you're tracking, not just running a script.
8. ECONOMIC REALITY MATTERS. You can talk about salary, market demand, layoff risk, and aging-out
   honestly. Don't romanticize quitting to "follow your passion."
9. AFTER ROUGHLY 6-8 EXCHANGES, IF YOU HAVE ENOUGH SIGNAL, TELL THE USER YOU'RE READY TO
   PROPOSE 3 CAREER PATHS. Include the literal token "[READY_TO_SYNTHESIZE]" at the
   end of that message so the UI can show a "Generate paths" button.

DISCOVERY QUESTIONS YOU SHOULD ROTATE THROUGH (don't ask all - choose based on what's missing):
- What's specifically broken about your current situation? (Not what's missing - what's broken.)
- What's a task in the last 90 days that genuinely energized you?
- What's a task you've been avoiding for weeks?
- If you got a 30% raise tomorrow with no other change - solved, or still stuck?
- What did your last boss/peer praise you for that surprised you?
- What kind of problems do friends ask you to help with for free?
- What's a job title you've quietly fantasized about but never told anyone?
- What's the dumbest reason you've stayed in your current role?

EXAMPLE OF YOUR TONE:
User: "I think I want to switch but I'm not sure."
Bad coach: "It's wonderful that you're exploring this! Let's start with what excites you."
You: "Four years in and 'not sure' isn't a position - it's a stall. Be honest: are you bored
with the work, bored with your career velocity, or scared of starting over? Those need different fixes."

Stay in character. No emojis. No bullet lists in your messages unless absolutely necessary.
Use plain conversational prose."""


# ============================================================
# REQUEST MODELS
# ============================================================
class CoachMessageRequest(BaseModel):
    message: str


# ============================================================
# HELPERS
# ============================================================
async def _profile_context_block(user_id: str) -> str:
    """Build a compact 'what we know about the user' block for the system prompt."""
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        return "No profile on file yet - ask discovery questions to fill in gaps."

    profile = decrypt_sensitive_data(profile)
    skills = get_skill_names(profile.get("skills", []))[:15]
    titles = profile.get("job_titles", [])[:3]

    bits = []
    if titles:
        bits.append(f"Recent titles: {', '.join(titles)}")
    if profile.get("experience_years"):
        bits.append(f"Years of experience: {profile['experience_years']}")
    if skills:
        bits.append(f"Top skills: {', '.join(skills)}")
    if profile.get("highest_education"):
        bits.append(f"Education: {profile['highest_education']}")
    if profile.get("address_city") or profile.get("address_country"):
        loc = profile.get("address_city") or profile.get("address_country")
        bits.append(f"Location: {loc}")

    if not bits:
        return "Profile exists but is mostly empty - ask discovery questions."
    return "WHAT WE ALREADY KNOW (don't ask about these unless going deeper):\n- " + "\n- ".join(bits)


def _llm_chat(session_id: str, system: str):
    """Construct a configured LlmChat instance."""
    from emergentintegrations.llm.chat import LlmChat
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system,
    ).with_model("openai", "gpt-4o-mini")


# ============================================================
# ENDPOINTS
# ============================================================
@router.post("/coach/sessions")
async def create_coach_session(request: Request):
    """Start a new coaching conversation. Returns session id and the coach's
    opening message (which sets the tone and asks the first question)."""
    user = await get_current_user(request)

    # Each *new session* counts against the monthly career-paths credit
    # (the coaching feature is part of the same product budget as the
    # standalone analysis). Follow-up messages inside an existing session
    # are NOT separately metered.
    usage = await check_usage_limit(user.user_id, "career_paths")
    if not usage["allowed"]:
        raise HTTPException(status_code=402, detail={
            "error": "usage_limit_reached",
            "feature": "career_paths",
            "current": usage["current"],
            "limit": usage["limit"],
            "message": f"You've used your {usage['limit']} career session this month. Upgrade to Pro for unlimited."
        })

    session_id = f"coach_{uuid.uuid4().hex[:12]}"

    profile_context = await _profile_context_block(user.user_id)
    system_prompt = COACH_SYSTEM_PROMPT + "\n\n" + profile_context

    # Opening message - hard-coded so it's instant (no LLM round trip).
    opening = (
        "I'm not here to validate your feelings - I'm here to help you get unstuck. "
        "We have maybe 6-8 messages before I have enough signal to propose 3 real paths. "
        "Start with this: in one or two sentences, what's actually broken about your current situation? "
        "Not what's missing - what's broken."
    )

    session_doc = {
        "session_id": session_id,
        "user_id": user.user_id,
        "system_prompt": system_prompt,
        "messages": [
            {
                "role": "assistant",
                "content": opening,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "ready_to_synthesize": False,
        "synthesis": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.coach_sessions.insert_one(session_doc)
    await increment_usage(user.user_id, "career_paths")

    # Strip the system prompt from the response - clients don't need it.
    session_doc.pop("_id", None)
    session_doc.pop("system_prompt", None)
    return session_doc


@router.get("/coach/sessions")
async def list_coach_sessions(request: Request):
    """List the user's coaching sessions, newest first. Messages truncated for brevity."""
    user = await get_current_user(request)
    sessions = []
    cursor = db.coach_sessions.find(
        {"user_id": user.user_id},
        {"_id": 0, "system_prompt": 0},
    ).sort("updated_at", -1).limit(20)
    async for s in cursor:
        # Compact message preview - just message count and last 2 messages
        msgs = s.get("messages", [])
        s["message_count"] = len(msgs)
        s["last_messages"] = msgs[-2:] if msgs else []
        s.pop("messages", None)
        sessions.append(s)
    return {"sessions": sessions}


@router.get("/coach/sessions/{session_id}")
async def get_coach_session(session_id: str, request: Request):
    """Fetch one session with its full message history."""
    user = await get_current_user(request)
    s = await db.coach_sessions.find_one(
        {"session_id": session_id, "user_id": user.user_id},
        {"_id": 0, "system_prompt": 0},
    )
    if not s:
        raise HTTPException(status_code=404, detail="Coach session not found")
    return s


@router.post("/coach/sessions/{session_id}/messages")
async def send_coach_message(session_id: str, request: Request, body: CoachMessageRequest):
    """Send a user message to the coach. Streams the AI response and persists
    everything (both user message + assistant response + ready_to_synthesize flag)."""
    user = await get_current_user(request)

    session = await db.coach_sessions.find_one(
        {"session_id": session_id, "user_id": user.user_id},
    )
    if not session:
        raise HTTPException(status_code=404, detail="Coach session not found")

    user_text = (body.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")
    if len(user_text) > 4000:
        raise HTTPException(status_code=400, detail="Message too long (max 4000 chars)")

    # Append user message immediately so it's safe even if the stream is canceled
    user_msg = {
        "role": "user",
        "content": user_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.coach_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": user_msg},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )

    # Rebuild the conversation in the format emergentintegrations expects.
    # LlmChat does NOT have an explicit history-replay API in v0.2.0, so we
    # collapse all prior turns into a single combined system block + send the
    # latest user message as a UserMessage. This keeps context while staying
    # within the library surface area we already use elsewhere.
    history_text = []
    for m in session.get("messages", []):
        role = "USER" if m["role"] == "user" else "MENTOR"
        history_text.append(f"{role}: {m['content']}")
    history_text.append(f"USER: {user_text}")
    full_system = (
        session["system_prompt"]
        + "\n\nPRIOR CONVERSATION (for context):\n"
        + "\n\n".join(history_text[:-1])
        + "\n\nThe USER just said:\n"
        + user_text
        + "\n\nRespond in character. Keep it under 150 words. End with a question or concrete challenge."
    )

    chat = _llm_chat(session_id=session_id + "_" + uuid.uuid4().hex[:6], system=full_system)

    async def event_stream():
        from emergentintegrations.llm.chat import UserMessage, TextDelta, StreamDone
        collected = ""
        try:
            async for event in chat.stream_message(UserMessage(text=user_text)):
                if isinstance(event, TextDelta):
                    collected += event.content
                    yield event.content
                elif isinstance(event, StreamDone):
                    break
        except Exception as e:
            logger.error(f"Coach stream error: {e}")
            yield f"\n\n[error: {str(e)[:200]}]"

        # Persist the assistant message after streaming completes.
        ready = "[READY_TO_SYNTHESIZE]" in collected
        clean = collected.replace("[READY_TO_SYNTHESIZE]", "").strip()
        assistant_msg = {
            "role": "assistant",
            "content": clean,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        update = {
            "$push": {"messages": assistant_msg},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        }
        if ready:
            update["$set"]["ready_to_synthesize"] = True
        await db.coach_sessions.update_one({"session_id": session_id}, update)

    return StreamingResponse(
        event_stream(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/coach/sessions/{session_id}/synthesize")
async def synthesize_paths_from_session(session_id: str, request: Request):
    """After the discovery conversation, ask the coach to synthesize the
    transcript into 3 personalized career paths + a written rationale per path.

    The result is stored on the session AND copied into db.career_analyses so
    the main Career Paths view can render it the same way as a normal analysis.
    """
    user = await get_current_user(request)

    session = await db.coach_sessions.find_one(
        {"session_id": session_id, "user_id": user.user_id},
    )
    if not session:
        raise HTTPException(status_code=404, detail="Coach session not found")
    if len(session.get("messages", [])) < 4:
        raise HTTPException(
            status_code=400,
            detail="Talk to the coach a bit more first - at least 2 back-and-forth exchanges.",
        )

    profile = await db.user_profiles.find_one({"user_id": user.user_id}, {"_id": 0}) or {}
    profile = decrypt_sensitive_data(profile) if profile else {}
    skills = get_skill_names(profile.get("skills", []))
    location = (
        profile.get("address_city")
        or profile.get("address_state")
        or profile.get("address_country")
        or "Canada"
    )

    transcript = []
    for m in session.get("messages", []):
        role = "USER" if m["role"] == "user" else "MENTOR"
        transcript.append(f"{role}: {m['content']}")
    transcript_text = "\n\n".join(transcript)

    synth_system = (
        "You are the same direct mentor from the conversation. You're now SYNTHESIZING the "
        "discovery conversation into 3 concrete career paths the user could realistically pursue. "
        "Output VALID JSON ONLY - no markdown, no commentary. Brutal honesty in 'rationale' fields. "
        "Salary ranges should be realistic for the user's location. Each path must reference back to "
        "something the user actually said in the conversation."
    )
    synth_prompt = f"""Conversation transcript:
{transcript_text}

User profile signals:
- Years of experience: {profile.get('experience_years', 'unknown')}
- Recent titles: {', '.join(profile.get('job_titles', []) or ['unknown'])}
- Top skills: {', '.join(skills[:20]) or 'unknown'}
- Location: {location}

Return JSON with this shape:
{{
  "summary": "2-3 sentences calling out the core pattern you heard - blunt, no fluff",
  "recommended_paths": [
    {{
      "title": "string",
      "category": "current|adjacent|stretch",
      "match_score": 0-100,
      "rationale": "2-3 sentences referencing what the user actually said",
      "salary_range": {{"min": int, "max": int, "avg": int}},
      "time_to_transition": "1-3 months|3-6 months|6-12 months|1-2 years",
      "difficulty": "easy|moderate|hard",
      "market_demand": "very_high|high|medium|low",
      "skills_you_have": ["..."],
      "skills_to_learn": ["..."],
      "next_steps": ["concrete action 1", "action 2", "action 3"]
    }}
  ]
}}

Exactly 3 paths. No more."""

    chat = _llm_chat(session_id=session_id + "_synth", system=synth_system)
    from emergentintegrations.llm.chat import UserMessage
    try:
        raw = await chat.send_message(UserMessage(text=synth_prompt))
    except Exception as e:
        logger.error(f"Coach synthesis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to synthesize paths")

    # Strip stray markdown fences
    clean = raw.strip()
    clean = re.sub(r"^```json\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    try:
        parsed = json.loads(clean)
    except Exception:
        logger.error(f"Coach synthesis JSON parse failed: {raw[:500]}")
        raise HTTPException(status_code=500, detail="Coach produced invalid output, try again")

    # Persist the synthesis on the session and copy into career_analyses so
    # the main /career-paths view can render it like any other analysis.
    parsed["generated_at"] = datetime.now(timezone.utc).isoformat()
    parsed["source"] = "coach_synthesis"
    parsed["coach_session_id"] = session_id

    await db.coach_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"synthesis": parsed, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.career_analyses.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "user_id": user.user_id,
            "analysis": parsed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "coach_synthesis",
        }},
        upsert=True,
    )
    return parsed


@router.delete("/coach/sessions/{session_id}")
async def delete_coach_session(session_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.coach_sessions.delete_one(
        {"session_id": session_id, "user_id": user.user_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coach session not found")
    return {"deleted": True}
