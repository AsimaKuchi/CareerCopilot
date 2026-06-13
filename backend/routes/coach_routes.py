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
    """Build a 'what we know about the user' block for the system prompt.

    The coach gets the user's FULL profile + a chunk of their resume so it
    can refer to specific experience, skip questions the user already
    answered in onboarding, and ground its advice in their actual situation.
    """
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        return "No profile on file yet - ask discovery questions to fill in gaps."

    profile = decrypt_sensitive_data(profile)
    skills = get_skill_names(profile.get("skills", []))
    titles = profile.get("job_titles", [])
    locations = profile.get("preferred_locations", [])
    job_types = profile.get("job_type", [])
    industries = profile.get("industries", [])

    bits = []
    if titles:
        bits.append(f"Recent titles: {', '.join(titles[:5])}")
    if profile.get("current_company"):
        bits.append(f"Current company: {profile['current_company']}")
    if profile.get("experience_years"):
        bits.append(f"Total years of experience: {profile['experience_years']}")
    if profile.get("seniority_level"):
        bits.append(f"Seniority: {profile['seniority_level']}")
    if profile.get("highest_education"):
        bits.append(f"Highest education: {profile['highest_education']}")
    if skills:
        bits.append(f"Skills ({len(skills)}): {', '.join(skills[:30])}")
    if industries:
        bits.append(f"Industries: {', '.join(industries[:5])}")
    if locations:
        bits.append(f"Preferred locations: {', '.join(locations[:5])}")
    if profile.get("address_city") or profile.get("address_country"):
        loc_parts = [profile.get("address_city"), profile.get("address_state"), profile.get("address_country")]
        bits.append(f"Lives in: {', '.join([p for p in loc_parts if p])}")
    if job_types:
        bits.append(f"Open to: {', '.join(job_types)}")
    if profile.get("salary_min") or profile.get("salary_max"):
        sal_lo, sal_hi = profile.get("salary_min"), profile.get("salary_max")
        bits.append(
            "Target salary: "
            + (f"${sal_lo:,}-${sal_hi:,}" if sal_lo and sal_hi else f"${sal_lo or sal_hi:,}+")
        )
    if profile.get("work_authorization"):
        bits.append(f"Work authorization: {profile['work_authorization']}")
    if profile.get("willing_to_relocate"):
        bits.append(f"Willing to relocate: {profile['willing_to_relocate']}")
    if profile.get("notice_period"):
        bits.append(f"Notice period: {profile['notice_period']}")
    if profile.get("application_intensity"):
        bits.append(f"Job-search intensity: {profile['application_intensity']}")

    profile_block = (
        "WHAT WE ALREADY KNOW (do NOT ask about these unless going deeper or "
        "you have a specific reason to verify):\n- " + "\n- ".join(bits)
        if bits else
        "Profile exists but is mostly empty - feel free to ask the basics."
    )

    # Include a chunk of the actual resume so the coach can reference real
    # accomplishments and specific phrasing from the user's experience.
    resume_block = ""
    resume_text = profile.get("resume_text") or ""
    if resume_text:
        # Use up to ~3500 chars (~1200 tokens) of resume. Truncate to first
        # half + last 1500 chars so we keep both the summary at the top and
        # the most recent role at the bottom even on long resumes.
        if len(resume_text) > 3500:
            resume_text = resume_text[:2000].strip() + "\n\n[...resume trimmed...]\n\n" + resume_text[-1500:].strip()
        resume_block = (
            "\n\nRESUME CONTENT (use to cite specific experience, projects, "
            "or accomplishments when relevant):\n---\n" + resume_text + "\n---"
        )

    return profile_block + resume_block


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

    # Opening message - tailored to whether we have profile data or not.
    profile_doc = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "job_titles": 1, "experience_years": 1, "resume_text": 1},
    ) or {}
    titles = profile_doc.get("job_titles") or []
    years = profile_doc.get("experience_years")
    has_resume = bool(profile_doc.get("resume_text"))

    if titles and years:
        title_str = titles[0]
        opening = (
            f"I've already pulled your profile and resume - {title_str} with {years} years of "
            f"experience. I won't waste time on basics I can read for myself. "
            "We have maybe 6-8 messages before I have enough signal to propose 3 real paths. "
            "Start with this: in one or two sentences, what's actually broken about your current situation? "
            "Not what's missing - what's broken."
        )
    elif has_resume:
        opening = (
            "I've read your resume so I'll skip the small talk. "
            "We have maybe 6-8 messages before I have enough signal to propose 3 real paths. "
            "Start with this: in one or two sentences, what's actually broken about your current situation? "
            "Not what's missing - what's broken."
        )
    else:
        opening = (
            "Heads up - your profile is mostly empty, so I'll need to ask a few basics along the way. "
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


# ============================================================
# CAREER-PATH GUIDANCE TRIPLET
#   - Skill-gap checklist with progress
#   - 30-day game plan per path
#   - Per-path "Ask the coach" Q&A log
#
# All three persist on a single `path_guidance` doc keyed by
# (user_id, path_title). Lightweight schema:
#   {
#     user_id, path_title,
#     skills_checked: [str],
#     plan_30d: {generated_at, weeks: [{week, focus, tasks: [str]}]},
#     qna: [{question, answer, created_at}],
#     updated_at,
#   }
# ============================================================


class SkillToggleRequest(BaseModel):
    path_title: str
    skill: str
    checked: bool


class PlanRequest(BaseModel):
    path_title: str
    path_data: Optional[Dict[str, Any]] = None  # full path object from career analysis


class AskRequest(BaseModel):
    path_title: str
    question: str
    path_data: Optional[Dict[str, Any]] = None


def _serialize_guidance(doc: dict) -> dict:
    if not doc:
        return {"skills_checked": [], "plan_30d": None, "qna": []}
    return {
        "skills_checked": doc.get("skills_checked", []),
        "plan_30d": doc.get("plan_30d"),
        "qna": doc.get("qna", []),
    }


@router.get("/paths/guidance")
async def get_path_guidance(request: Request, path_title: str):
    """Return the user's saved guidance state for a given career path."""
    user = await get_current_user(request)
    doc = await db.path_guidance.find_one(
        {"user_id": user.user_id, "path_title": path_title},
        {"_id": 0},
    )
    return _serialize_guidance(doc)


@router.put("/paths/guidance/skills")
async def toggle_path_skill(request: Request, body: SkillToggleRequest):
    """Mark a skill as checked/unchecked on the user's progress tracker."""
    user = await get_current_user(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    if body.checked:
        await db.path_guidance.update_one(
            {"user_id": user.user_id, "path_title": body.path_title},
            {
                "$addToSet": {"skills_checked": body.skill},
                "$set": {"updated_at": now_iso},
                "$setOnInsert": {
                    "user_id": user.user_id,
                    "path_title": body.path_title,
                    "created_at": now_iso,
                },
            },
            upsert=True,
        )
    else:
        await db.path_guidance.update_one(
            {"user_id": user.user_id, "path_title": body.path_title},
            {
                "$pull": {"skills_checked": body.skill},
                "$set": {"updated_at": now_iso},
            },
        )
    doc = await db.path_guidance.find_one(
        {"user_id": user.user_id, "path_title": body.path_title},
        {"_id": 0, "skills_checked": 1},
    ) or {}
    return {"skills_checked": doc.get("skills_checked", [])}


@router.post("/paths/guidance/plan")
async def generate_30d_plan(request: Request, body: PlanRequest):
    """Generate (and cache) a 30-day game plan for a path.

    Returns cached plan if one already exists. Pass `force=true` query param to
    regenerate.
    """
    user = await get_current_user(request)
    force = request.query_params.get("force", "").lower() in ("1", "true", "yes")

    existing = await db.path_guidance.find_one(
        {"user_id": user.user_id, "path_title": body.path_title},
        {"_id": 0, "plan_30d": 1},
    )
    if not force and existing and existing.get("plan_30d"):
        return existing["plan_30d"]

    # Need the path context to generate a useful plan
    path_data = body.path_data or {}
    if not path_data:
        # Fall back to whatever we have in career_analyses
        analysis_doc = await db.career_analyses.find_one(
            {"user_id": user.user_id},
            {"_id": 0, "analysis": 1},
        ) or {}
        analysis = analysis_doc.get("analysis", {})
        for p in analysis.get("recommended_paths", []) or []:
            if p.get("title") == body.path_title:
                path_data = p
                break

    if not path_data:
        raise HTTPException(status_code=400, detail="No path context available; regenerate career analysis first.")

    profile = await db.user_profiles.find_one({"user_id": user.user_id}, {"_id": 0}) or {}
    profile = decrypt_sensitive_data(profile) if profile else {}
    have_skills = path_data.get("skills_you_have", []) or []
    learn_skills = path_data.get("skills_to_learn", []) or []
    location = (
        profile.get("address_city")
        or profile.get("address_country")
        or "their region"
    )

    system_msg = (
        "You are a direct, no-fluff career mentor producing a 30-day execution plan. "
        "Be specific, time-bound and realistic for a working professional with ~6-10 hrs/week to invest. "
        "Output VALID JSON ONLY — no markdown fences, no commentary."
    )
    prompt = f"""Build a 30-day game plan to position the user for: {body.path_title}

Path details:
- Current strengths: {', '.join(have_skills) or 'not specified'}
- Skills to learn: {', '.join(learn_skills) or 'not specified'}
- Difficulty: {path_data.get('difficulty', 'moderate')}
- Time-to-transition estimate: {path_data.get('time_to_transition', 'unknown')}
- User location (for networking realism): {location}

Return JSON with this exact shape:
{{
  "headline": "1 sentence north star for the 30 days",
  "weeks": [
    {{
      "week": 1,
      "focus": "short label - what is this week about",
      "tasks": [
        "concrete task with hours, deliverable, or measurable outcome",
        "another concrete task"
      ]
    }},
    {{"week": 2, "focus": "...", "tasks": ["..."]}},
    {{"week": 3, "focus": "...", "tasks": ["..."]}},
    {{"week": 4, "focus": "...", "tasks": ["..."]}}
  ],
  "success_signal": "1 sentence: what proves the plan worked at end of 30 days"
}}

Rules:
- Each week has 3-5 tasks. Each task is one line and actionable.
- Include at least 1 learning task, 1 portfolio/practice task, and 1 networking/visibility task across the plan.
- Reference real platforms by name (Coursera, GitHub, LinkedIn, etc.) when helpful.
- Don't recommend quitting a job. Assume the user is doing this on top of their current work."""

    chat = _llm_chat(session_id=f"plan_{user.user_id}_{uuid.uuid4().hex[:8]}", system=system_msg)
    from emergentintegrations.llm.chat import UserMessage
    try:
        raw = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error(f"30d plan gen error: {e}")
        raise HTTPException(status_code=500, detail="Plan generation failed")

    clean = raw.strip()
    clean = re.sub(r"^```json\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    try:
        plan = json.loads(clean)
    except Exception:
        logger.error(f"30d plan JSON parse failed: {raw[:400]}")
        raise HTTPException(status_code=500, detail="Plan returned in unexpected format, try again")

    plan["generated_at"] = datetime.now(timezone.utc).isoformat()
    plan["path_title"] = body.path_title

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.path_guidance.update_one(
        {"user_id": user.user_id, "path_title": body.path_title},
        {
            "$set": {"plan_30d": plan, "updated_at": now_iso},
            "$setOnInsert": {
                "user_id": user.user_id,
                "path_title": body.path_title,
                "created_at": now_iso,
            },
        },
        upsert=True,
    )
    return plan


@router.post("/paths/guidance/ask")
async def ask_path_coach(request: Request, body: AskRequest):
    """Single-turn 'ask the coach' for a specific career path.

    Each question/answer is appended to the guidance doc's qna log for replay.
    Non-streaming (kept simple - response is typically 1-3 short paragraphs).
    """
    user = await get_current_user(request)
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty question")
    if len(q) > 1500:
        raise HTTPException(status_code=400, detail="Question too long (max 1500 chars)")

    # Get path context
    path_data = body.path_data or {}
    if not path_data:
        analysis_doc = await db.career_analyses.find_one(
            {"user_id": user.user_id},
            {"_id": 0, "analysis": 1},
        ) or {}
        for p in (analysis_doc.get("analysis", {}) or {}).get("recommended_paths", []) or []:
            if p.get("title") == body.path_title:
                path_data = p
                break

    # Pull prior qna to thread the conversation (last 6 exchanges max)
    existing = await db.path_guidance.find_one(
        {"user_id": user.user_id, "path_title": body.path_title},
        {"_id": 0, "qna": 1},
    ) or {}
    prior = (existing.get("qna") or [])[-6:]

    prior_text = ""
    if prior:
        prior_text = "\n\nPRIOR Q&A FOR THIS PATH:\n" + "\n".join(
            f"Q: {p['question']}\nA: {p['answer']}" for p in prior
        )

    system_msg = (
        COACH_SYSTEM_PROMPT
        + "\n\nYou are answering a SPECIFIC question about ONE career path the user is exploring. "
        + "Stay tightly on this path. Keep answer to 80-150 words. No fluff. "
        + "End with a question or concrete challenge."
    )
    prompt = f"""User is exploring: {body.path_title}

Path details:
- Match: {path_data.get('match_score', '?')}%
- Skills they have: {', '.join(path_data.get('skills_you_have', []) or ['unknown'])}
- Skills to learn: {', '.join(path_data.get('skills_to_learn', []) or ['unknown'])}
- Difficulty: {path_data.get('difficulty', 'unknown')}
- Salary range: {path_data.get('salary_range', {})}
{prior_text}

USER ASKED:
{q}

Respond as the direct mentor. Reference path details when relevant."""

    chat = _llm_chat(session_id=f"path_ask_{user.user_id}_{uuid.uuid4().hex[:8]}", system=system_msg)
    from emergentintegrations.llm.chat import UserMessage
    try:
        answer = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error(f"Path-ask coach error: {e}")
        raise HTTPException(status_code=500, detail="Coach failed to respond, try again")

    answer = answer.strip()
    qna_entry = {
        "question": q,
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.path_guidance.update_one(
        {"user_id": user.user_id, "path_title": body.path_title},
        {
            "$push": {"qna": qna_entry},
            "$set": {"updated_at": now_iso},
            "$setOnInsert": {
                "user_id": user.user_id,
                "path_title": body.path_title,
                "created_at": now_iso,
            },
        },
        upsert=True,
    )
    return qna_entry
