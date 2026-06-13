"""
routes/extension_routes.py - Browser extension API: autofill data, screening Q&A, submission tracking.

Endpoints (under /api):
  GET  /autofill/data                        -- Generic autofill payload (web)
  GET  /extension/autofill-data              -- Extension-specific autofill payload
  POST /extension/track-submission           -- Track an extension auto-submission
  GET  /screening-questions/templates        -- Built-in screening templates
  GET  /screening-questions/answers          -- User's saved screening answers
  PUT  /screening-questions/answers          -- Save screening answers
  POST /screening-questions/custom           -- Add a custom screening Q&A
  POST /extension/answer-questions           -- AI-answer free-form screening questions

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import base64
import hashlib
import json
import re

from fastapi import APIRouter, HTTPException, Request
import httpx

from core import db, logger, EMERGENT_LLM_KEY, get_current_user
from models import (
    ScreeningAnswersUpdate,
    CustomQuestionAdd,
    AnswerQuestionsRequest,
)
from profile_schema import get_autofill_data, get_normalized_value
from encryption import decrypt_sensitive_data
from stripe_routes import check_usage_limit, increment_usage
from routes.application_routes import create_docx_from_text
from job_url_match import canonical_job_key, normalize_url_for_match

# Backward-compat alias for code paths that reference EMERGENT_API_KEY (legacy name).
EMERGENT_API_KEY = EMERGENT_LLM_KEY

router = APIRouter()


@router.get("/autofill/data")
async def get_autofill_data_endpoint(request: Request, url: str = None):
    """Get user data for bookmarklet auto-fill using v2 structured schema."""
    user = await get_current_user(request)
    
    # Get user info
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get profile
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Decrypt sensitive data if encrypted
    if profile:
        profile = decrypt_sensitive_data(profile)
    
    # Get structured autofill data from v2 schema
    autofill = get_autofill_data(profile) if profile else {}
    
    # Parse name from user doc if not in autofill
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = autofill.get("firstName") or (name_parts[0] if name_parts else "")
    last_name = autofill.get("lastName") or (name_parts[1] if len(name_parts) > 1 else "")
    email = autofill.get("email") or (user_doc.get("email", "") if user_doc else "")
    
    # Use normalized values from structured schema
    phone = autofill.get("phone") or ""  # E.164 format
    linkedin = autofill.get("linkedinUrl") or ""
    github = autofill.get("githubUrl") or ""
    portfolio = autofill.get("portfolioUrl") or ""
    
    # Location fields
    city = autofill.get("city") or ""
    state = autofill.get("state") or ""
    country = autofill.get("country") or ""
    
    # Work authorization (normalized)
    work_authorization = autofill.get("workAuthorizationStatus") or ""
    requires_sponsorship = autofill.get("requiresSponsorship")
    
    # Try to find matching application by URL
    app_doc = None
    if url:
        app_doc = await db.applications.find_one(
            {"user_id": user.user_id, "apply_link": {"$regex": url.split("?")[0], "$options": "i"}},
            {"_id": 0}
        )
    
    # If no match, get most recent approved application
    if not app_doc:
        app_doc = await db.applications.find_one(
            {"user_id": user.user_id, "status": "applied"},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
    
    # If still no match, get most recent pending application
    if not app_doc:
        app_doc = await db.applications.find_one(
            {"user_id": user.user_id, "status": "pending"},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
    
    resume_text = ""
    cover_letter = ""
    job_title = ""
    company = ""
    
    if app_doc:
        resume_text = app_doc.get("optimized_resume") or ""
        cover_letter = app_doc.get("cover_letter") or ""
        job_title = app_doc.get("job_title") or ""
        company = app_doc.get("company") or ""
    
    # Fallback to profile resume if no optimized version
    if not resume_text and profile:
        resume_text = profile.get("resume_text") or ""
    
    return {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "phone": phone,
        "phoneFormatted": autofill.get("phoneFormatted") or "",
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "city": city,
        "state": state,
        "country": country,
        "workAuthorization": work_authorization,
        "requiresSponsorship": requires_sponsorship,
        "education": autofill.get("education") or "",
        "seniorityLevel": autofill.get("seniorityLevel") or "",
        "willingToRelocate": autofill.get("willingToRelocate") or "",
        "noticePeriod": autofill.get("noticePeriod") or "",
        "skills": autofill.get("skills") or [],
        "resume": resume_text,
        "coverLetter": cover_letter,
        "jobTitle": job_title,
        "company": company,
        "hasApplication": app_doc is not None
    }

# ========================
# BROWSER EXTENSION API
# ========================

# Helper functions to map normalized DB values to exact UI labels from Profile.jsx
def _map_willing_to_relocate(value: str) -> str:
    """Map willing_to_relocate DB value to exact UI label from Profile.jsx SelectItem."""
    mapping = {
        "yes": "Yes - willing to relocate",
        "no": "No - not willing to relocate",
        "open_to_discussion": "Open to discussion",
    }
    return mapping.get(value, value) if value else ""

def _map_notice_period(value: str) -> str:
    """Map notice_period DB value to exact UI label from Profile.jsx SelectItem."""
    mapping = {
        "immediately": "Immediately available",
        "two_weeks": "2 weeks notice",
        "one_month": "1 month notice",
        "two_months": "2 months notice",
        "three_months_plus": "3+ months notice",
    }
    return mapping.get(value, value) if value else ""

def _map_education(value: str) -> str:
    """Map education DB value to exact UI label from Profile.jsx SelectItem."""
    mapping = {
        "high_school": "High School Diploma / GED",
        "some_college": "Some College (No Degree)",
        "associate": "Associate Degree",
        "bachelor": "Bachelor's Degree",
        "master": "Master's Degree",
        "doctorate": "Doctorate (PhD, MD, JD, etc.)",
        "professional": "Professional Certification",
        "other": "Other",
    }
    return mapping.get(value, value) if value else ""

def _map_work_arrangement(value: str) -> str:
    """Map work_arrangement DB value to exact UI label from Profile.jsx SelectItem."""
    mapping = {
        "remote": "Remote",
        "hybrid": "Hybrid",
        "onsite": "On-site",
        "flexible": "Flexible",
    }
    return mapping.get(value, value) if value else ""

@router.get("/extension/autofill-data")
async def get_extension_autofill_data(request: Request, job_url: str = None):
    """
    Get structured autofill data for the browser extension.
    Returns all user profile data including resume and cover letter.
    If job_url is provided, tries to match to a saved application for optimized content.
    """
    user = await get_current_user(request)
    
    # Check usage limits for extension
    usage_check = await check_usage_limit(user.user_id, "extension_uses")
    if not usage_check["allowed"]:
        raise HTTPException(status_code=402, detail={
            "error": "usage_limit_reached",
            "feature": "extension_uses",
            "current": usage_check["current"],
            "limit": usage_check["limit"],
            "message": f"You've used all {usage_check['limit']} extension uses this month. Upgrade to Pro for unlimited access."
        })
    
    await increment_usage(user.user_id, "extension_uses")
    
    # Get user info
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get profile
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Decrypt sensitive data if encrypted
    if profile:
        profile = decrypt_sensitive_data(profile)
    
    # Check if we have a matching saved application with optimized content
    optimized_resume = None
    optimized_cover_letter = None
    matched_application = None
    
    if job_url:
        # 1. Canonical-key match (Greenhouse gh_jid, Lever uuid, LinkedIn id, etc.)
        incoming_key = canonical_job_key(job_url)
        incoming_norm = normalize_url_for_match(job_url)
        base_url = job_url.split("?")[0]
        if incoming_key:
            matched_application = await db.applications.find_one(
                {"user_id": user.user_id, "apply_link_key": incoming_key},
                {"_id": 0}
            )
            if matched_application:
                logger.info(f"Autofill match via canonical key={incoming_key}")
        # 2. Normalized-URL match (strip query/fragment/trailing slash)
        if not matched_application and incoming_norm:
            matched_application = await db.applications.find_one(
                {"user_id": user.user_id, "apply_link_norm": incoming_norm},
                {"_id": 0}
            )
            if matched_application:
                logger.info(f"Autofill match via normalized URL={incoming_norm}")
        # 3. Legacy regex match (covers older applications that pre-date canonical_key)
        if not matched_application:
            matched_application = await db.applications.find_one(
                {
                    "user_id": user.user_id,
                    "$or": [
                        {"apply_link": {"$regex": base_url, "$options": "i"}},
                        {"job_url": {"$regex": base_url, "$options": "i"}}
                    ]
                },
                {"_id": 0}
            )
            if matched_application:
                logger.info(f"Autofill match via legacy substring URL={base_url}")

        if matched_application:
            optimized_resume = matched_application.get("optimized_resume")
            optimized_cover_letter = matched_application.get("cover_letter")
        else:
            logger.info(f"No autofill application match for URL: {job_url}")
    
    # Get structured autofill data from v2 schema
    autofill = get_autofill_data(profile) if profile else {}
    
    # Parse name
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = autofill.get("firstName") or (name_parts[0] if name_parts else "")
    last_name = autofill.get("lastName") or (name_parts[1] if len(name_parts) > 1 else "")
    email = autofill.get("email") or (user_doc.get("email", "") if user_doc else "")
    
    # Build structured response for extension
    response = {
        "personal_info": {
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": autofill.get("phone") or "",
            "linkedin": autofill.get("linkedinUrl") or "",
            "github": autofill.get("githubUrl") or "",
            "portfolio": autofill.get("portfolioUrl") or "",
            "location": {
                "city": autofill.get("city") or "",
                "state": autofill.get("state") or "",
                "country": autofill.get("country") or ""
            }
        },
        "questions": [
            {
                "field_type": "work_authorization",
                "question": "Are you authorized to work in this country?",
                "current_value": autofill.get("workAuthorizationStatus") or ""
            },
            {
                "field_type": "sponsorship",
                "question": "Do you require sponsorship?",
                "current_value": "No" if autofill.get("requiresSponsorship") == False else ("Yes" if autofill.get("requiresSponsorship") else "")
            },
            {
                "field_type": "years_experience",
                "question": "Years of experience",
                "current_value": str(profile.get("experience_years") or "") if profile else ""
            }
        ],
        "documents": {},
        "matched_job": matched_application.get("job_title") if matched_application else None,
        # Include profile data for AI question answering
        # Map normalized DB values to human-readable UI labels that match Profile.jsx exactly
        "profile_context": {
            "skills": autofill.get("skills", []),
            "skills_with_years": autofill.get("skillsWithYears", []),
            "experience_years": autofill.get("experienceYears"),
            "resume_text": profile.get("resume_text", "") if profile else "",
            "work_authorization": autofill.get("workAuthorizationStatus") or "",
            "requires_sponsorship": autofill.get("requiresSponsorship"),
            "preferred_name": first_name,
            "country": autofill.get("countryFull") or autofill.get("country") or "",
            "city": autofill.get("city") or "",
            "state": autofill.get("state") or "",
            # Map willing_to_relocate to exact UI labels from Profile.jsx
            "willing_to_relocate": _map_willing_to_relocate(autofill.get("willingToRelocate")),
            "salary_min": autofill.get("salaryMin"),
            "salary_max": autofill.get("salaryMax"),
            # Map notice_period to exact UI labels from Profile.jsx
            "notice_period": _map_notice_period(autofill.get("noticePeriod")),
            "availability_date": autofill.get("availabilityDate"),
            # Map education to exact UI labels from Profile.jsx
            "education": _map_education(autofill.get("education")),
            # Map work_arrangement to exact UI labels from Profile.jsx
            "work_arrangement": _map_work_arrangement(autofill.get("workArrangement")),
            "referral_source": autofill.get("referralSource"),
        }
    }
    
    # Add resume data - prefer optimized version if available
    resume_text = optimized_resume or (profile.get("resume_text") if profile else None)
    if resume_text:
        # Generate DOCX file from optimized resume text
        try:
            # Create filename using FirstnameLastnameCV.docx format
            # Remove spaces and special characters from names
            clean_first = "".join(c for c in first_name if c.isalnum())
            clean_last = "".join(c for c in last_name if c.isalnum())
            resume_filename = f"{clean_first}{clean_last}CV.docx"
            
            # Create DOCX from optimized text
            docx_bytes = create_docx_from_text(resume_text)
            file_data_b64 = base64.b64encode(docx_bytes).decode('utf-8')
            
            resume_data = {
                "text": resume_text,
                "filename": resume_filename,
                "file_data": file_data_b64,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "is_optimized": bool(optimized_resume)
            }
            response["documents"]["resume"] = resume_data
            logger.info(f"Generated optimized resume DOCX for extension: {resume_filename} (is_optimized: {bool(optimized_resume)})")
        except Exception as e:
            logger.error(f"Failed to generate resume DOCX for extension: {e}")
            # Fallback to text only
            response["documents"]["resume"] = {
                "text": resume_text,
                "filename": "resume.txt",
                "is_optimized": bool(optimized_resume)
            }
    elif profile and profile.get("resume_file_data"):
        # Use original uploaded file if no optimized version
        response["documents"]["resume"] = {
            "text": profile.get("resume_text"),
            "filename": profile.get("resume_filename") or "resume.pdf",
            "file_data": profile.get("resume_file_data"),
            "mime_type": profile.get("resume_mime_type") or "application/pdf",
            "is_optimized": False
        }
    
    # Add cover letter - prefer optimized version if available
    cover_letter_text = optimized_cover_letter or (profile.get("default_cover_letter") if profile else None)
    if cover_letter_text:
        # Generate DOCX file from cover letter text
        try:
            # Create filename using FirstnameLastnameCL.docx format
            # Remove spaces and special characters from names
            clean_first = "".join(c for c in first_name if c.isalnum())
            clean_last = "".join(c for c in last_name if c.isalnum())
            cover_letter_filename = f"{clean_first}{clean_last}CL.docx"
            
            # Create DOCX from cover letter text
            docx_bytes = create_docx_from_text(cover_letter_text)
            file_data_b64 = base64.b64encode(docx_bytes).decode('utf-8')
            
            response["documents"]["cover_letter"] = {
                "text": cover_letter_text,
                "filename": cover_letter_filename,
                "file_data": file_data_b64,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "is_optimized": bool(optimized_cover_letter)
            }
            logger.info(f"Generated cover letter DOCX for extension: {cover_letter_filename} (is_optimized: {bool(optimized_cover_letter)})")
        except Exception as e:
            logger.error(f"Failed to generate cover letter DOCX for extension: {e}")
            # Fallback to text only
            response["documents"]["cover_letter"] = {
                "text": cover_letter_text,
                "is_optimized": bool(optimized_cover_letter)
            }
    
    # Add skills for custom question matching
    if profile and profile.get("skills"):
        response["skills"] = profile.get("skills")
    
    # Add stored screening question answers
    if profile and profile.get("screening_answers"):
        response["screening_answers"] = profile.get("screening_answers")
    
    return response


@router.post("/extension/track-submission")
async def track_extension_submission(request: Request):
    """
    Track when a user submits a job application via the browser extension.
    Updates the existing application status to 'applied'.
    """
    user = await get_current_user(request)
    
    body = await request.json()
    job_url = body.get("job_url")
    job_title = body.get("job_title")
    company = body.get("company")
    
    if not job_url:
        raise HTTPException(status_code=400, detail="job_url is required")
    
    # Try to find the matching application by URL using the same multi-stage
    # strategy as /extension/autofill-data so users get consistent matches.
    incoming_key = canonical_job_key(job_url)
    incoming_norm = normalize_url_for_match(job_url)
    base_url = job_url.split("?")[0]

    matched_application = None
    if incoming_key:
        matched_application = await db.applications.find_one(
            {"user_id": user.user_id, "apply_link_key": incoming_key}
        )
    if not matched_application and incoming_norm:
        matched_application = await db.applications.find_one(
            {"user_id": user.user_id, "apply_link_norm": incoming_norm}
        )
    if not matched_application:
        matched_application = await db.applications.find_one(
            {
                "user_id": user.user_id,
                "$or": [
                    {"apply_link": {"$regex": base_url, "$options": "i"}},
                    {"job_url": {"$regex": base_url, "$options": "i"}}
                ]
            }
        )
    
    if matched_application:
        # Update the existing application to "applied" status
        await db.applications.update_one(
            {"_id": matched_application["_id"]},
            {
                "$set": {
                    "status": "applied",
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "submission_method": "browser_extension",
                    "submission_url": job_url
                }
            }
        )
        
        logger.info(f"Application {matched_application.get('application_id')} marked as applied via extension")
        
        return {
            "success": True,
            "message": "Application status updated to 'applied'",
            "application_id": matched_application.get("application_id"),
            "job_title": matched_application.get("job_title"),
            "company": matched_application.get("company")
        }
    else:
        # No matching application found - this shouldn't happen in normal flow
        # but we can still log it
        logger.warning(f"No matching application found for URL: {job_url}")
        
        return {
            "success": False,
            "message": "No matching application found. Please ensure you opened this job from the dashboard.",
            "job_url": job_url
        }


# Common screening questions template
COMMON_SCREENING_QUESTIONS = [
    {
        "id": "preferred_name",
        "question": "What name would you like us to use?",
        "type": "text",
        "category": "Personal",
        "keywords": ["preferred name", "like us to use", "call you"]
    },
    {
        "id": "work_authorization",
        "question": "Are you legally authorized to work in this country?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Work Authorization",
        "keywords": ["authorized to work", "legally authorized", "work authorization", "eligible to work"]
    },
    {
        "id": "sponsorship_required",
        "question": "Will you now or in the future require sponsorship?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Work Authorization",
        "keywords": ["require sponsorship", "need sponsorship", "visa sponsorship", "immigration sponsorship"]
    },
    {
        "id": "employment_restrictions",
        "question": "Are you subject to any employment agreements or restrictions?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Legal",
        "keywords": ["employment agreement", "non-compete", "restrictions", "post-employment"]
    },
    {
        "id": "country_residence",
        "question": "What is your current country of residence?",
        "type": "text",
        "category": "Location",
        "keywords": ["country of residence", "current country", "reside in", "living in"]
    },
    {
        "id": "us_canada_location",
        "question": "Are you located in the US or Canada?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Location",
        "keywords": ["located in us", "located in canada", "us or canada", "united states or canada"]
    },
    {
        "id": "timezone_est",
        "question": "Are you available to work in EST timezone?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Location",
        "keywords": ["est timezone", "eastern time", "est hours"]
    },
    {
        "id": "timezone_pst",
        "question": "Are you available to work in PST timezone?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Location",
        "keywords": ["pst timezone", "pacific time", "pst hours"]
    },
    {
        "id": "remote_work",
        "question": "Are you comfortable working remotely?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Work Preferences",
        "keywords": ["remote work", "work remotely", "work from home", "wfh"]
    },
    {
        "id": "hybrid_work",
        "question": "Are you open to hybrid work arrangements?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Work Preferences",
        "keywords": ["hybrid", "in-office", "office days"]
    },
    {
        "id": "relocation",
        "question": "Are you willing to relocate?",
        "type": "select",
        "options": ["Yes", "No", "Maybe"],
        "category": "Work Preferences",
        "keywords": ["relocate", "relocation", "move to", "willing to move"]
    },
    {
        "id": "start_date",
        "question": "When can you start?",
        "type": "text",
        "category": "Availability",
        "keywords": ["start date", "when can you start", "available to start", "earliest start"]
    },
    {
        "id": "notice_period",
        "question": "What is your notice period?",
        "type": "text",
        "category": "Availability",
        "keywords": ["notice period", "two weeks notice", "current notice"]
    },
    {
        "id": "salary_expectations",
        "question": "What are your salary expectations?",
        "type": "text",
        "category": "Compensation",
        "keywords": ["salary expectation", "compensation", "desired salary", "salary range"]
    },
    {
        "id": "years_experience_total",
        "question": "How many years of total work experience do you have?",
        "type": "text",
        "category": "Experience",
        "keywords": ["years of experience", "total experience", "work experience"]
    },
    {
        "id": "highest_education",
        "question": "What is your highest level of education?",
        "type": "select",
        "options": ["High School", "Associate's", "Bachelor's", "Master's", "PhD", "Other"],
        "category": "Education",
        "keywords": ["highest education", "degree", "educational background"]
    },
    {
        "id": "criminal_record",
        "question": "Have you ever been convicted of a crime?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Background",
        "keywords": ["convicted", "criminal", "felony", "misdemeanor"]
    },
    {
        "id": "referred_by",
        "question": "How did you hear about this position?",
        "type": "text",
        "category": "Source",
        "keywords": ["hear about", "referred", "found this job", "source"]
    },
    {
        "id": "linkedin_url",
        "question": "What is your LinkedIn profile URL?",
        "type": "text",
        "category": "Links",
        "keywords": ["linkedin", "linkedin profile", "linkedin url"]
    },
    {
        "id": "github_url",
        "question": "What is your GitHub profile URL?",
        "type": "text",
        "category": "Links",
        "keywords": ["github", "github profile", "github url"]
    },
    {
        "id": "portfolio_url",
        "question": "What is your portfolio/website URL?",
        "type": "text",
        "category": "Links",
        "keywords": ["portfolio", "website", "personal site"]
    },
    {
        "id": "age_18_plus",
        "question": "Are you at least 18 years of age?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Legal",
        "keywords": ["18 years", "age requirement", "legal age"]
    },
    {
        "id": "background_check",
        "question": "Are you willing to undergo a background check?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Background",
        "keywords": ["background check", "background screening"]
    },
    {
        "id": "drug_test",
        "question": "Are you willing to take a drug test?",
        "type": "select",
        "options": ["Yes", "No"],
        "category": "Background",
        "keywords": ["drug test", "drug screening"]
    },
]


@router.get("/screening-questions/templates")
async def get_screening_question_templates(request: Request):
    """Get the list of common screening questions with templates."""
    await get_current_user(request)  # Ensure authenticated
    return {"questions": COMMON_SCREENING_QUESTIONS}


@router.get("/screening-questions/answers")
async def get_user_screening_answers(request: Request):
    """Get user's stored screening question answers."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "screening_answers": 1}
    )
    
    return {
        "answers": profile.get("screening_answers", {}) if profile else {},
        "templates": COMMON_SCREENING_QUESTIONS
    }



@router.put("/screening-questions/answers")
async def update_screening_answers(request: Request, data: ScreeningAnswersUpdate):
    """Update user's screening question answers."""
    user = await get_current_user(request)
    
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {"$set": {"screening_answers": data.answers}},
        upsert=True
    )
    
    return {"success": True, "message": "Screening answers saved"}


@router.post("/screening-questions/custom")
async def add_custom_screening_question(request: Request, data: CustomQuestionAdd):
    """Add a custom screening question and answer."""
    user = await get_current_user(request)
    
    # Generate a unique ID for the custom question
    import hashlib
    question_id = f"custom_{hashlib.md5(data.question.encode()).hexdigest()[:8]}"
    
    custom_question = {
        "id": question_id,
        "question": data.question,
        "answer": data.answer,
        "keywords": data.keywords or [word.lower() for word in data.question.split() if len(word) > 3],
        "is_custom": True
    }
    
    # Add to user's custom questions
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {
            "$push": {"custom_screening_questions": custom_question},
            "$set": {f"screening_answers.{question_id}": data.answer}
        },
        upsert=True
    )
    
    return {"success": True, "question_id": question_id}


@router.post("/extension/answer-questions")
async def answer_screening_questions(request: Request, req: AnswerQuestionsRequest):
    """
    Use AI to answer custom screening questions based on user's profile and resume.
    """
    user = await get_current_user(request)
    
    # Get profile
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if profile:
        profile = decrypt_sensitive_data(profile)
    
    # Get user info
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    autofill = get_autofill_data(profile) if profile else {}
    full_name = user_doc.get("name", "") if user_doc else ""
    first_name = full_name.split(" ")[0] if full_name else ""
    
    # Build context about the user
    user_context = f"""
User Profile:
- Name: {full_name}
- Preferred Name: {first_name}
- Location: {autofill.get('city', '')}, {autofill.get('state', '')}, {autofill.get('country', '')}
- Work Authorization: {autofill.get('workAuthorizationStatus', 'Not specified')}
- Requires Sponsorship: {'No' if autofill.get('requiresSponsorship') == False else ('Yes' if autofill.get('requiresSponsorship') else 'Not specified')}
- Years of Experience: {profile.get('experience_years', 'Not specified') if profile else 'Not specified'}
- Skills: {', '.join(profile.get('skills', [])) if profile else 'Not specified'}

Resume Summary:
{profile.get('resume_text', 'No resume available')[:3000] if profile else 'No resume available'}
"""

    # Format questions for AI
    questions_text = ""
    for i, q in enumerate(req.questions):
        questions_text += f"\n{i+1}. {q.get('question', '')}"
        if q.get('options'):
            questions_text += f"\n   Options: {', '.join(q['options'])}"
    
    prompt = f"""Based on the user's profile and resume, answer these job application screening questions.
Be truthful - if you don't have enough information, say "Unable to determine".
If it's a Yes/No question, answer with just "Yes" or "No".
If there are dropdown options provided, pick the most appropriate option that matches the user's profile.

{user_context}

Questions to answer:
{questions_text}

Respond in JSON format:
{{
  "answers": [
    {{"question_index": 0, "answer": "your answer", "confidence": "high/medium/low"}},
    ...
  ]
}}
"""

    try:
        from emergentintegrations.llm.chat import chat, Message

        response = await chat(
            api_key=EMERGENT_API_KEY,
            model=Model.OPENAI_GPT4O,
            messages=[Message(role="user", content=prompt)]
        )
        
        # Parse JSON response
        response_text = response.message
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"answers": [], "error": "Could not parse AI response"}
            
    except Exception as e:
        logger.error(f"Error answering questions: {str(e)}")
        return {"answers": [], "error": str(e)}

# ========================
# DASHBOARD STATS
# ========================

