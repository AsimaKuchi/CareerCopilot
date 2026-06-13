"""
routes/comparison_routes.py - Job match comparison endpoints.

Endpoints (under /api):
  POST /jobs/{job_id}/compare              -- Generate match analysis
  GET  /jobs/{job_id}/compare              -- Fetch saved analysis
  PUT  /jobs/{job_id}/compare/notes        -- Update personal notes

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone
from typing import Optional
import json
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Request

from core import db, logger, EMERGENT_LLM_KEY, get_current_user
from models import JobComparisonRequest, JobComparison
from stripe_routes import check_usage_limit, increment_usage

router = APIRouter()


@router.post("/jobs/{job_id}/compare")
async def analyze_job_match(request: Request, job_id: str, req: JobComparisonRequest):
    """
    Analyze match between user's resume and job description.
    Returns cached result if available, otherwise generates new analysis.
    """
    user = await get_current_user(request)
    
    # Check for existing comparison
    existing = await db.job_comparisons.find_one(
        {"user_id": user.user_id, "job_id": job_id},
        {"_id": 0}
    )
    
    # Return cached if complete
    if existing and existing.get("status") == "complete":
        logger.info(f"Returning cached comparison for job {job_id}")
        return existing
    
    # Get user's resume
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile or not profile.get("resume_text"):
        raise HTTPException(status_code=400, detail="Resume not uploaded. Please upload your resume first.")
    
    resume_text = profile.get("resume_text", "")
    
    # Check if resume is too short
    if len(resume_text) < 100:
        raise HTTPException(status_code=400, detail="Resume is too short. Please upload a complete resume.")
    
    try:
        # Generate analysis using LLM
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"job_compare_{user.user_id}_{uuid.uuid4().hex[:8]}",
            system_message="""You are an expert resume strategist and recruiter. 
You produce structured, grounded analysis comparing resumes to job descriptions.
You ONLY use evidence from the resume text provided. You never invent experience."""
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""You are an expert resume strategist and recruiter. Compare a candidate's resume to a job description and produce a structured, grounded analysis.

RULES:
- Only use evidence that appears in the RESUME TEXT. Do not invent experience.
- When suggesting changes, rephrase existing experience to better match the role; do not fabricate tools, employers, or projects.
- Prioritize REQUIRED qualifications over preferred.
- Output MUST be valid JSON only (no markdown, no commentary, no code blocks).

INPUTS:

RESUME TEXT:
<<<{resume_text}>>>

JOB DESCRIPTION:
<<<{req.job_description}>>>

TASK:
1) Generate a Decision Summary (2-3 sentences):
   - decision_summary: Overall fit assessment
   - primary_risk: Main gap or concern (if any)
   - recommendation: "Apply with confidence" | "Apply with targeted changes" | "Stretch role - proceed with caution" | "Not recommended"
   - readiness_level: "Ready to apply" | "Light tailoring needed" | "Moderate changes needed" | "Significant gaps"

2) Identify 4–6 Strengths grouped by theme. Each must include:
   - title (short, e.g., "Technical Skills Match")
   - summary (one-line summary for collapsed view)
   - why_it_matches (1 sentence explaining the alignment)
   - evidence (1–3 resume snippets or close paraphrases tied to resume content)

3) Identify 4–6 Improvement Opportunities (biggest gaps/weak signals). Frame as opportunities, not deficiencies. Each must include:
   - title (short, opportunity-focused, e.g., "Opportunity to Strengthen Cloud Skills")
   - summary (one-line summary for collapsed view)
   - why_it_matters (1 sentence explaining impact)
   - fix (resume-safe suggestion using existing experience)
   - priority ("high"|"medium"|"low")

4) Provide 6–12 keywords_to_include as short chips (1–3 words each) based on the job description, excluding ones already strongly evidenced in the resume.

5) Provide 3–6 suggested_resume_edits as before/after bullet rewrites using only existing experience. Keep "after" under 2 lines. Each edit must include:
   - target_section (e.g., "Work Experience - Software Engineer at XYZ")
   - before (original bullet point from resume)
   - after (improved version tailored to job)

JSON SCHEMA (respond with valid JSON only, no markdown):
{{
  "decision_summary": {{
    "overall_fit": "Strong alignment with role requirements. Your background in data analysis and Python programming directly matches 80% of core responsibilities.",
    "primary_risk": "Limited cloud platform experience may require highlighting transferable infrastructure skills",
    "recommendation": "Apply with targeted changes",
    "readiness_level": "Light tailoring needed"
  }},
  "strengths": [
    {{
      "title": "Technical Skills Match",
      "summary": "Python, SQL, and data analysis experience aligns with core requirements",
      "why_it_matches": "Your Python and SQL experience directly aligns with the role's core technical requirements",
      "evidence": [
        "Built data pipelines using Python and SQL",
        "Analyzed datasets with 1M+ records using SQL queries"
      ]
    }}
  ],
  "improvement_opportunities": [
    {{
      "title": "Opportunity to Strengthen Cloud Skills",
      "summary": "Highlighting cloud exposure will strengthen your application",
      "why_it_matters": "Role requires AWS knowledge for deploying data solutions",
      "fix": "Highlight any cloud exposure or emphasize transferable skills in infrastructure",
      "priority": "high"
    }}
  ],
  "keywords_to_include": ["AWS", "ETL", "Data Warehousing", "Tableau", "Agile"],
  "suggested_resume_edits": [
    {{
      "target_section": "Work Experience - Data Analyst at ABC Corp",
      "before": "Analyzed customer data to improve retention",
      "after": "Built ETL pipelines to analyze customer behavior data, improving retention by 15% through data-driven insights"
    }}
  ]
}}

Generate the analysis now. Respond with ONLY valid JSON, no other text."""

        # Call LLM
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON response
        import json
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Remove markdown code blocks
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            comparison_json = json.loads(clean_response)
            
            # Validate structure
            required_keys = ["decision_summary", "strengths", "improvement_opportunities", "keywords_to_include", "suggested_resume_edits"]
            for key in required_keys:
                if key not in comparison_json:
                    raise ValueError(f"Missing required key: {key}")
            
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {str(parse_error)}\nResponse: {response[:500]}")
            # Retry once with explicit JSON instruction
            retry_prompt = f"{prompt}\n\nIMPORTANT: Your previous response was not valid JSON. Respond with ONLY a valid JSON object, no markdown, no explanatory text."
            response = await chat.send_message(UserMessage(text=retry_prompt))
            
            try:
                clean_response = response.strip()
                if clean_response.startswith("```"):
                    clean_response = clean_response.split("```")[1]
                    if clean_response.startswith("json"):
                        clean_response = clean_response[4:]
                clean_response = clean_response.strip()
                comparison_json = json.loads(clean_response)
            except:
                raise HTTPException(status_code=500, detail="Failed to parse LLM response. Please try again.")
        
        # Save to database
        comparison_doc = {
            "comparison_id": f"cmp_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "job_id": job_id,
            "job_title": req.job_title,
            "company": req.company,
            "comparison_json": comparison_json,
            "personal_notes": "",
            "status": "complete",
            "error_message": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert (update if exists, insert if not)
        await db.job_comparisons.update_one(
            {"user_id": user.user_id, "job_id": job_id},
            {"$set": comparison_doc},
            upsert=True
        )
        
        logger.info(f"Generated and saved comparison for job {job_id}")
        return comparison_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job comparison error: {str(e)}")
        
        # Save error status
        error_doc = {
            "comparison_id": f"cmp_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "job_id": job_id,
            "job_title": req.job_title,
            "company": req.company,
            "comparison_json": {},
            "personal_notes": "",
            "status": "error",
            "error_message": str(e),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.job_comparisons.update_one(
            {"user_id": user.user_id, "job_id": job_id},
            {"$set": error_doc},
            upsert=True
        )
        
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

@router.get("/jobs/{job_id}/compare")
async def get_job_comparison(request: Request, job_id: str):
    """Get cached job comparison if it exists."""
    user = await get_current_user(request)
    
    comparison = await db.job_comparisons.find_one(
        {"user_id": user.user_id, "job_id": job_id},
        {"_id": 0}
    )
    
    if not comparison:
        raise HTTPException(status_code=404, detail="No comparison found for this job")
    
    return comparison

@router.put("/jobs/{job_id}/compare/notes")
async def update_comparison_notes(request: Request, job_id: str):
    """Update personal notes for a job comparison."""
    user = await get_current_user(request)
    body = await request.json()
    notes = body.get("notes", "")
    
    result = await db.job_comparisons.update_one(
        {"user_id": user.user_id, "job_id": job_id},
        {"$set": {
            "personal_notes": notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No comparison found for this job")
    
    return {"success": True, "notes": notes}


# ========================
# APPLICATION ROUTES
# ========================

