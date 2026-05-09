"""
routes/application_routes.py - Job application lifecycle (apply, autofill, downloads, next-steps).

Endpoints (under /api):
  POST   /applications                                         -- Create application
  GET    /applications                                         -- List user applications
  PUT    /applications/{id}/approve                            -- Approve generated content
  GET    /applications/{id}/autofill-payload                   -- Browser autofill payload
  POST   /applications/{id}/auto-fill                          -- Backend Playwright autofill
  PUT    /applications/{id}/reject                             -- Reject application
  DELETE /applications/{id}                                    -- Delete application
  GET    /applications/{id}/next-steps                         -- Get next steps progress
  PUT    /applications/{id}/next-steps                         -- Update single next step
  POST   /applications/{id}/next-steps/generate                -- Generate AI content
  POST   /applications/{id}/generate-resume-docx               -- Generate resume DOCX
  POST   /applications/{id}/generate-cover-letter-docx         -- Generate cover letter DOCX
  POST   /applications/{id}/prepare-download/resume            -- Prepare resume download
  POST   /applications/{id}/prepare-download/cover-letter      -- Prepare cover letter download
  GET    /applications/{id}/download/resume                    -- Download resume DOCX
  GET    /applications/{id}/download/cover-letter              -- Download cover letter DOCX
  GET    /applications/{id}/autofill-script                    -- Bookmarklet autofill script
  GET    /download/{file_id}                                   -- Direct download file
  GET    /download-page/{file_id}                              -- Download landing page

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import base64
import io
import json
import os
import re
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
import httpx

# Set Playwright browsers path before importing
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/pw-browsers')
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from docx import Document

from core import db, logger, EMERGENT_LLM_KEY, FRONTEND_URL, STATIC_DOWNLOADS_DIR, get_current_user
from models import (
    ApplyRequest,
    NextStepUpdate,
    NextStepContentRequest,
    AutoFillRequest,
    JobApplication,
)
from profile_schema import get_autofill_data
from encryption import decrypt_sensitive_data
from stripe_routes import check_usage_limit, increment_usage

router = APIRouter()


@router.post("/applications")
async def create_application(request: Request, req: ApplyRequest):
    """Create a new job application (pending approval)."""
    user = await get_current_user(request)
    
    # Check usage limits
    usage_check = await check_usage_limit(user.user_id, "job_applications")
    if not usage_check["allowed"]:
        raise HTTPException(status_code=402, detail={
            "error": "usage_limit_reached",
            "feature": "job_applications",
            "current": usage_check["current"],
            "limit": usage_check["limit"],
            "message": f"You've used all {usage_check['limit']} job applications this month. Upgrade to Pro for unlimited access."
        })
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Calculate match score
    match_score = 70  # Default
    if profile:
        job_mock = {
            "job_title": req.job_title,
            "job_description": req.job_description,
            "job_city": req.location or "",
            "job_state": ""
        }
        match_score = calculate_match_score(job_mock, profile)
    
    # Format salary range
    salary_range = format_salary_range(req.salary_min, req.salary_max, req.job_description)
    
    application = {
        "application_id": f"app_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "job_id": req.job_id,
        "job_title": req.job_title,
        "company": req.company,
        "location": req.location,
        "job_description": req.job_description,
        "salary_range": salary_range,
        "apply_link": req.apply_link,
        "optimized_resume": req.optimized_resume,
        "cover_letter": req.cover_letter,
        "status": "pending",
        "match_score": match_score,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "applied_at": None
    }
    
    await db.applications.insert_one(application)
    application.pop("_id", None)
    
    await increment_usage(user.user_id, "job_applications")
    return application

@router.get("/applications")
async def get_applications(request: Request):
    """Get all applications for current user."""
    user = await get_current_user(request)
    
    applications = await db.applications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"applications": applications}

@router.put("/applications/{application_id}/approve")
async def approve_application(request: Request, application_id: str):
    """Approve and submit application."""
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update status to applied
    await db.applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "status": "applied",
            "applied_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.applications.find_one(
        {"application_id": application_id},
        {"_id": 0}
    )
    
    return updated

# NOTE: Playwright auto-fill functions removed - to be reimplemented
# Removed: auto_fill_application(), auto_submit_greenhouse()
# Removed: POST /applications/{application_id}/auto-fill
# Removed: POST /applications/{application_id}/auto-submit

@router.get("/applications/{application_id}/autofill-payload")
async def get_autofill_payload(request: Request, application_id: str):
    """
    Get complete autofill payload for a specific application.
    Returns application metadata, structured profile v2, and documents.
    Used by external auto-fill bots (Claude + Playwright).
    """
    user = await get_current_user(request)
    
    # Get application
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get user info
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get profile and decrypt
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if profile:
        profile = decrypt_sensitive_data(profile)
        # Ensure v2 migration
        if profile.get("profile_version") != 2:
            profile = migrate_profile_to_v2(profile)
    else:
        profile = {}
    
    # Determine ATS type from apply_link with confidence scoring
    apply_link = app_doc.get("apply_link", "")
    apply_link_lower = apply_link.lower()
    ats_type = "unknown"
    ats_confidence = "none"
    ats_detected_from = None
    
    # High confidence: domain-based detection
    if "greenhouse.io" in apply_link_lower or "boards.greenhouse" in apply_link_lower:
        ats_type = "greenhouse"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "lever.co" in apply_link_lower or "jobs.lever" in apply_link_lower:
        ats_type = "lever"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "ashbyhq.com" in apply_link_lower or "jobs.ashby" in apply_link_lower:
        ats_type = "ashby"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "myworkdayjobs.com" in apply_link_lower or "workday.com" in apply_link_lower:
        ats_type = "workday"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "icims.com" in apply_link_lower:
        ats_type = "icims"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "taleo" in apply_link_lower:
        ats_type = "taleo"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "smartrecruiters.com" in apply_link_lower:
        ats_type = "smartrecruiters"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "pinpointhq.com" in apply_link_lower:
        ats_type = "pinpoint"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "jobvite.com" in apply_link_lower:
        ats_type = "jobvite"
        ats_confidence = "high"
        ats_detected_from = "domain"
    elif "breezy.hr" in apply_link_lower:
        ats_type = "breezy"
        ats_confidence = "high"
        ats_detected_from = "domain"
    # Medium confidence: path-based detection
    elif "/jobs/" in apply_link_lower or "/careers/" in apply_link_lower:
        ats_type = "custom"
        ats_confidence = "low"
        ats_detected_from = "path_pattern"
    
    # Parse user name
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Get autofill data from v2 schema
    autofill_data = get_autofill_data(profile) if profile else {}
    
    # Build confirm_required list - fields that need user confirmation before submitting
    confirm_required = []
    
    # Work authorization - always confirm (legal implications)
    if autofill_data.get("workAuthorizationStatus"):
        confirm_required.append({
            "field": "work_authorization",
            "reason": "Legal implications - verify authorization status is accurate",
            "current_value": autofill_data.get("workAuthorizationStatus")
        })
    
    # Salary - always confirm (negotiation implications)
    if autofill_data.get("salaryMin") or autofill_data.get("salaryMax"):
        confirm_required.append({
            "field": "salary",
            "reason": "Compensation expectations may vary by role",
            "current_value": {
                "min": autofill_data.get("salaryMin"),
                "max": autofill_data.get("salaryMax"),
                "currency": autofill_data.get("salaryCurrency", "USD")
            }
        })
    
    # Relocation - confirm if set
    if autofill_data.get("willingToRelocate"):
        confirm_required.append({
            "field": "willing_to_relocate",
            "reason": "Relocation preference may depend on specific role/location",
            "current_value": autofill_data.get("willingToRelocate")
        })
    
    # Notice period - confirm if set
    if autofill_data.get("noticePeriod"):
        confirm_required.append({
            "field": "notice_period",
            "reason": "Availability may have changed",
            "current_value": autofill_data.get("noticePeriod")
        })
    
    # Referral source - confirm (company-specific)
    confirm_required.append({
        "field": "referral_source",
        "reason": "How you heard about this role may vary",
        "current_value": autofill_data.get("referralSource", "LinkedIn")
    })
    
    # Requires sponsorship - critical legal field
    if autofill_data.get("requiresSponsorship") is not None:
        confirm_required.append({
            "field": "requires_sponsorship",
            "reason": "Sponsorship requirement is a critical legal field",
            "current_value": autofill_data.get("requiresSponsorship")
        })
    
    # Document file URLs and metadata
    # Resume file handling
    resume_filename = profile.get("resume_filename")
    resume_format = profile.get("resume_format", "").lower()
    resume_has_original = bool(profile.get("resume_raw"))  # Original file stored as base64
    resume_mime_type = None
    
    if resume_filename:
        # Determine MIME type from format/filename
        if resume_format == "pdf" or resume_filename.endswith(".pdf"):
            resume_mime_type = "application/pdf"
        elif resume_format == "docx" or resume_filename.endswith(".docx"):
            resume_mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif resume_format == "doc" or resume_filename.endswith(".doc"):
            resume_mime_type = "application/msword"
        elif resume_format == "txt" or resume_filename.endswith(".txt"):
            resume_mime_type = "text/plain"
        else:
            resume_mime_type = "application/octet-stream"
    
    # Cover letter file handling (generated as .docx)
    cover_letter_text = app_doc.get("cover_letter") or ""
    cover_letter_mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if cover_letter_text else None
    cover_letter_filename = f"cover_letter_{app_doc.get('company', 'company').replace(' ', '_').lower()}.docx" if cover_letter_text else None
    
    # Build response
    response = {
        "confirm_required": confirm_required,
        "application": {
            "application_id": app_doc.get("application_id"),
            "job_id": app_doc.get("job_id"),
            "job_title": app_doc.get("job_title"),
            "company": app_doc.get("company"),
            "location": app_doc.get("location"),
            "apply_url": apply_link,
            "ats_type": ats_type,
            "ats_confidence": ats_confidence,
            "ats_detected_from": ats_detected_from,
            "status": app_doc.get("status"),
            "match_score": app_doc.get("match_score"),
            "created_at": app_doc.get("created_at"),
        },
        "profile": {
            # Identity
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "email": autofill_data.get("email") or user_doc.get("email", "") if user_doc else "",
            
            # Contact - normalized
            "phone": autofill_data.get("phone"),  # E.164 format
            "phone_formatted": autofill_data.get("phoneFormatted"),
            "phone_country_code": autofill_data.get("phoneCountryCode"),
            
            # Location - normalized
            "city": autofill_data.get("city"),
            "state": autofill_data.get("state"),
            "country": autofill_data.get("country"),
            "country_full": autofill_data.get("countryFull"),
            
            # Links
            "linkedin_url": autofill_data.get("linkedinUrl"),
            "github_url": autofill_data.get("githubUrl"),
            "portfolio_url": autofill_data.get("portfolioUrl"),
            "website_url": autofill_data.get("websiteUrl"),
            
            # Work Authorization - normalized with sponsorship flag
            "work_authorization": {
                "status": autofill_data.get("workAuthorizationStatus"),
                "country": autofill_data.get("workAuthorizationCountry"),
                "requires_sponsorship": autofill_data.get("requiresSponsorship"),
                "expiry_date": autofill_data.get("workAuthorizationExpiry"),
                "raw": profile.get("work_authorization"),
            },
            
            # Professional
            "seniority_level": autofill_data.get("seniorityLevel"),
            "education": autofill_data.get("education"),
            "experience_years": autofill_data.get("experienceYears") or profile.get("experience_years", 0),
            "current_company": autofill_data.get("currentCompany") or profile.get("current_company"),
            
            # Preferences
            "desired_job_titles": autofill_data.get("desiredJobTitles", []),
            "preferred_locations": autofill_data.get("preferredLocations", []),
            "work_arrangement": autofill_data.get("workArrangement"),
            "job_types": autofill_data.get("jobTypes", []),
            "willing_to_relocate": autofill_data.get("willingToRelocate"),
            "notice_period": autofill_data.get("noticePeriod"),
            "availability_date": autofill_data.get("availabilityDate"),
            
            # Compensation
            "salary_min": autofill_data.get("salaryMin"),
            "salary_max": autofill_data.get("salaryMax"),
            "salary_currency": autofill_data.get("salaryCurrency", "USD"),
            
            # Skills - simple list for matching
            "skills": autofill_data.get("skills", []),
            # Skills with years - full structured data
            "skills_with_years": autofill_data.get("skillsWithYears", []),
            
            # Industries
            "target_industries": autofill_data.get("targetIndustries", []),
            "open_to_any_industry": autofill_data.get("openToAnyIndustry", False),
            
            # Application defaults
            "referral_source": autofill_data.get("referralSource", "LinkedIn"),
            
            # Raw structured data for advanced use cases
            "structured": profile.get("structured", {}),
        },
        "documents": {
            "resume": {
                # Text version (for textarea-based ATS flows)
                "text": app_doc.get("optimized_resume") or profile.get("resume_text") or "",
                "is_optimized": bool(app_doc.get("optimized_resume")),
                
                # Original file (preserves user's formatting)
                "original": {
                    "available": resume_has_original,
                    "file_name": resume_filename,
                    "format": resume_format,
                    "mime_type": resume_mime_type,
                    "download_url": f"/api/profile/resume/download/original" if resume_has_original else None,
                },
                
                # Generated DOCX from optimized text (for ATS that need file upload)
                "generated_docx": {
                    "available": bool(app_doc.get("optimized_resume")),
                    "download_url": f"/api/applications/{application_id}/download/resume" if app_doc.get("optimized_resume") else None,
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }
            },
            "cover_letter": {
                # Text version (for textarea-based ATS flows)
                "text": cover_letter_text,
                
                # Generated DOCX (for ATS that need file upload)
                "generated_docx": {
                    "available": bool(cover_letter_text),
                    "file_name": cover_letter_filename,
                    "download_url": f"/api/applications/{application_id}/download/cover-letter" if cover_letter_text else None,
                    "mime_type": cover_letter_mime_type,
                }
            }
        }
    }
    
    return response

@router.post("/applications/{application_id}/auto-fill")
async def auto_fill_application_data(request: Request, application_id: str, body: AutoFillRequest = None):
    """
    Auto-fill a job application using Playwright.
    
    Flow:
    1. Try server-side Playwright automation
    2. If CAPTCHA detected → Return data for user to complete manually
    3. If submit_form=True → Also click submit button
    4. Return filled fields and submission status
    
    The user can always fall back to manual copy mode.
    """
    submit_form = body.submit_form if body else False
    user = await get_current_user(request)
    
    # Get application
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    apply_link = app_doc.get("apply_link", "")
    if not apply_link:
        return {
            "success": False,
            "message": "No application link found for this job",
            "auto_fill_data": {}
        }
    
    # Get user profile and decrypt
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if profile:
        profile = decrypt_sensitive_data(profile)
    else:
        profile = {}
    
    # Get user doc for name
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Parse name
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Get autofill data from v2 schema
    autofill = get_autofill_data(profile)
    
    # Build comprehensive auto-fill data with all available profile fields
    auto_fill_data = {
        # Basic info
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "email": autofill.get("email") or user_doc.get("email", "") if user_doc else "",
        "phone": autofill.get("phoneFormatted") or autofill.get("phone") or profile.get("phone_number", ""),
        
        # Social/professional links
        "linkedin": autofill.get("linkedinUrl") or profile.get("linkedin_url", ""),
        "github": autofill.get("githubUrl") or profile.get("github_url", ""),
        "portfolio": autofill.get("portfolioUrl") or profile.get("portfolio_url", ""),
        "website": autofill.get("portfolioUrl") or profile.get("portfolio_url", ""),
        
        # Location
        "city": autofill.get("city") or profile.get("address_city", ""),
        "state": autofill.get("state") or profile.get("address_state", ""),
        "province": autofill.get("state") or profile.get("address_state", ""),
        "country": autofill.get("countryFull") or autofill.get("country") or profile.get("address_country", ""),
        "address": f"{autofill.get('city', '')}, {autofill.get('state', '')}, {autofill.get('country', '')}".strip(", "),
        "postal_code": profile.get("postal_code", ""),
        "zip_code": profile.get("postal_code", ""),
        
        # Work info
        "current_company": autofill.get("currentCompany") or profile.get("current_company", ""),
        "current_title": autofill.get("currentTitle") or profile.get("current_title", ""),
        "years_experience": str(profile.get("experience_years", "")) if profile.get("experience_years") else "",
        
        # Education
        "education": autofill.get("education") or profile.get("highest_education", ""),
        "degree": autofill.get("education") or profile.get("highest_education", ""),
        "university": profile.get("university", ""),
        "school": profile.get("university", ""),
        
        # Work authorization
        "work_authorization": autofill.get("workAuthorizationStatus") or profile.get("work_authorization", ""),
        "authorized_to_work": "Yes" if profile.get("work_authorization") in ["citizen", "permanent_resident", "work_permit"] else "No",
        "requires_sponsorship": "No" if profile.get("work_authorization") in ["citizen", "permanent_resident"] else "Yes",
        "sponsorship": "No" if profile.get("work_authorization") in ["citizen", "permanent_resident"] else "Yes",
        "visa_status": autofill.get("workAuthorizationStatus") or profile.get("work_authorization", ""),
        
        # Availability
        "willing_to_relocate": "Yes" if profile.get("willing_to_relocate") else "No",
        "relocate": "Yes" if profile.get("willing_to_relocate") else "No",
        "notice_period": profile.get("notice_period", "2 weeks"),
        "start_date": profile.get("available_start_date", "Immediately available"),
        "availability": profile.get("available_start_date", "Immediately available"),
        "earliest_start_date": profile.get("available_start_date", "Immediately available"),
        
        # Salary
        "salary_expectation": str(profile.get("expected_salary_min", "")) if profile.get("expected_salary_min") else "",
        "desired_salary": str(profile.get("expected_salary_min", "")) if profile.get("expected_salary_min") else "",
        
        # Referral
        "referral_source": profile.get("referral_source", "LinkedIn"),
        "how_did_you_hear": profile.get("referral_source", "LinkedIn"),
        "source": profile.get("referral_source", "LinkedIn"),
        
        # Documents
        "resume_text": app_doc.get("optimized_resume") or profile.get("resume_text", ""),
        "cover_letter": app_doc.get("cover_letter", ""),
        
        # Gender/Demographics (optional, often asked)
        "gender": profile.get("gender", ""),
        "pronouns": profile.get("pronouns", ""),
        "veteran_status": profile.get("veteran_status", ""),
        "disability_status": profile.get("disability_status", ""),
        "race_ethnicity": profile.get("race_ethnicity", ""),
    }
    
    # Determine ATS type
    ats_type = "unknown"
    apply_link_lower = apply_link.lower()
    if "greenhouse.io" in apply_link_lower or "boards.greenhouse" in apply_link_lower:
        ats_type = "greenhouse"
    elif "lever.co" in apply_link_lower or "jobs.lever" in apply_link_lower:
        ats_type = "lever"
    elif "ashbyhq.com" in apply_link_lower:
        ats_type = "ashby"
    elif "smartrecruiters.com" in apply_link_lower or "jobs.smartrecruiters" in apply_link_lower:
        ats_type = "smartrecruiters"
    elif "pinpointhq.com" in apply_link_lower:
        ats_type = "pinpoint"
    
    # Get resume file data for upload
    resume_file_data = None
    resume_filename = profile.get("resume_filename", "resume.pdf")
    resume_raw = profile.get("resume_raw")
    
    if resume_raw:
        # Decrypt if encrypted
        if isinstance(resume_raw, str) and resume_raw.startswith("gAAAAA"):
            try:
                resume_raw = decrypt_field(resume_raw)
            except:
                pass
        resume_file_data = resume_raw
    
    # Try Playwright automation
    try:
        result = await playwright_auto_fill(
            apply_link=apply_link,
            ats_type=ats_type,
            auto_fill_data=auto_fill_data,
            resume_file_data=resume_file_data,
            resume_filename=resume_filename,
            submit_form=submit_form
        )
        
        if result["captcha_detected"]:
            # CAPTCHA found - user needs to complete manually
            return {
                "success": False,
                "message": "🔒 CAPTCHA detected! Please complete the application in your browser.",
                "captcha_detected": True,
                "apply_link": apply_link,
                "auto_fill_data": auto_fill_data,
                "fields_filled": result.get("fields_filled", []),
                "fields_failed": result.get("fields_failed", []),
                "manual_mode": True,
                "submitted": False,
                "hint": "Click 'Open Application' to continue in your browser with your data ready to paste."
            }
        
        submitted = result.get("submitted", False)
        submission_confirmed = result.get("submission_confirmed", False)
        submit_error = result.get("submit_error")
        final_url = result.get("final_url")
        screenshot = result.get("screenshot")
        
        if result["success"]:
            # Successfully filled (and possibly submitted)
            if submitted:
                # Update application status - but be honest about confirmation
                status_update = {
                    "status": "applied", 
                    "applied_at": datetime.now(timezone.utc), 
                    "auto_submitted": True,
                    "submission_confirmed": submission_confirmed,
                    "final_url": final_url,
                }
                if screenshot:
                    status_update["submission_screenshot"] = screenshot
                    
                await db.applications.update_one(
                    {"application_id": application_id},
                    {"$set": status_update}
                )
                
                if submission_confirmed:
                    message = f"🎉 Application likely submitted! {len(result['fields_filled'])} fields filled. Check email for confirmation."
                else:
                    message = f"⚠️ Submit clicked but confirmation unclear. {len(result['fields_filled'])} fields filled. Please verify via email."
            else:
                message = f"✅ Auto-filled {len(result['fields_filled'])} fields!"
            
            return {
                "success": True,
                "message": message,
                "apply_link": apply_link,
                "auto_fill_data": auto_fill_data,
                "fields_filled": result["fields_filled"],
                "fields_failed": result["fields_failed"],
                "manual_mode": False,
                "ats_type": ats_type,
                "submitted": submitted,
                "submission_confirmed": submission_confirmed,
                "final_url": final_url,
                "screenshot": screenshot,
                "submit_error": submit_error,
            }
        else:
            # Failed for other reason - fall back to manual
            return {
                "success": False,
                "message": result.get("error", "Auto-fill failed. Use copy buttons instead."),
                "apply_link": apply_link,
                "auto_fill_data": auto_fill_data,
                "fields_filled": result.get("fields_filled", []),
                "fields_failed": result.get("fields_failed", []),
                "manual_mode": True,
                "submitted": False,
            }
            
    except Exception as e:
        logger.error(f"Playwright auto-fill error: {str(e)}")
        # Fall back to manual mode
        return {
            "success": False,
            "message": f"Auto-fill unavailable: {str(e)}. Use copy buttons instead.",
            "apply_link": apply_link,
            "auto_fill_data": auto_fill_data,
            "fields_filled": [],
            "fields_failed": [],
            "manual_mode": True,
            "submitted": False,
        }


async def playwright_auto_fill(apply_link: str, ats_type: str, auto_fill_data: dict, resume_file_data: str = None, resume_filename: str = "resume.pdf", submit_form: bool = False) -> dict:
    """
    Use Playwright to auto-fill a job application form.
    Returns dict with success status, filled fields, and CAPTCHA detection.
    
    Args:
        apply_link: URL of the application form
        ats_type: Type of ATS (greenhouse, lever, ashby)
        auto_fill_data: Dict of field values to fill
        resume_file_data: Base64 encoded resume file (optional)
        resume_filename: Name of the resume file
        submit_form: If True, will click the submit button after filling
    """
    fields_filled = []
    fields_failed = []
    captcha_detected = False
    temp_resume_path = None
    
    # Ensure browsers are installed before attempting to use Playwright
    browser_path = "/pw-browsers/chromium-1200"
    headless_shell_path = "/pw-browsers/chromium_headless_shell-1200"
    
    if not os.path.exists(browser_path) and not os.path.exists(headless_shell_path):
        logger.warning("Playwright browsers not found, attempting to install...")
        try:
            import subprocess
            import sys
            env = os.environ.copy()
            env['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'
            result = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                env=env,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "captcha_detected": False,
                    "fields_filled": [],
                    "fields_failed": [],
                    "error": "Browser installation failed. Please try again or use manual mode."
                }
            logger.info("Playwright browsers installed successfully")
        except Exception as e:
            logger.error(f"Browser installation error: {e}")
            return {
                "success": False,
                "captcha_detected": False,
                "fields_filled": [],
                "fields_failed": [],
                "error": f"Browser setup failed: {str(e)}. Please use manual mode."
            }
    
    try:
        # Create temp file for resume if we have data
        if resume_file_data:
            try:
                import tempfile
                resume_bytes = base64.b64decode(resume_file_data)
                # Create temp file with proper extension
                ext = os.path.splitext(resume_filename)[1] or '.pdf'
                temp_fd, temp_resume_path = tempfile.mkstemp(suffix=ext)
                with os.fdopen(temp_fd, 'wb') as f:
                    f.write(resume_bytes)
                logger.info(f"Created temp resume file: {temp_resume_path}")
            except Exception as e:
                logger.error(f"Failed to create temp resume file: {e}")
                temp_resume_path = None
        
        async with async_playwright() as p:
            # Launch headless browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to application page
                await page.goto(apply_link, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # Check for CAPTCHA - ONLY detect ACTIVE, BLOCKING captcha challenges
                # Do NOT trigger on background reCAPTCHA scripts or "Protected by reCAPTCHA" badges
                captcha_detected = False
                
                try:
                    # Strategy 1: Check for visible CAPTCHA iframes (most reliable)
                    # These specific iframe URLs only appear when CAPTCHA is actually shown
                    # reCAPTCHA v3 badges do NOT use these URLs
                    captcha_iframe_selectors = [
                        'iframe[src*="recaptcha"][src*="/anchor"]',  # Active reCAPTCHA checkbox
                        'iframe[src*="recaptcha"][src*="/bframe"]',  # Active reCAPTCHA challenge
                        'iframe[src*="hcaptcha"]',
                        'iframe[src*="turnstile"]',
                    ]
                    
                    for selector in captcha_iframe_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                is_visible = await element.is_visible()
                                if is_visible:
                                    # Double-check it's actually rendered and taking space
                                    # reCAPTCHA v2 challenges are typically 300x75px or larger
                                    # The small "Protected by reCAPTCHA" badge is only ~256x60px
                                    box = await element.bounding_box()
                                    if box and box['width'] > 270 and box['height'] > 70:
                                        captcha_detected = True
                                        logger.info(f"✋ ACTIVE CAPTCHA detected: {selector}")
                                        break
                        except:
                            continue
                    
                    # Strategy 2: Check for visible CAPTCHA container divs (secondary check)
                    # Skip small containers - those are likely just badges
                    if not captcha_detected:
                        container_selectors = [
                            '.g-recaptcha',
                            '.h-captcha',
                            '.cf-turnstile',
                        ]
                        
                        for selector in container_selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    is_visible = await element.is_visible()
                                    if is_visible:
                                        # Check if it has actual content (not just hidden script container)
                                        # Real CAPTCHA challenges are at least 300x75px
                                        # The "Protected by reCAPTCHA" badge is much smaller (~256x60)
                                        box = await element.bounding_box()
                                        if box and box['width'] > 280 and box['height'] > 70:
                                            captcha_detected = True
                                            logger.info(f"✋ ACTIVE CAPTCHA container detected: {selector}")
                                            break
                            except:
                                continue
                    
                    # Strategy 3: Check for explicit blocking challenge text (last resort)
                    # ONLY ultra-specific phrases that actually block user access
                    # Do NOT trigger on "Protected by reCAPTCHA" or "Privacy - Terms" text
                    if not captcha_detected:
                        try:
                            visible_text = await page.inner_text('body')
                            visible_text_lower = visible_text.lower()
                            
                            # Only these extremely specific blocking phrases
                            # Generic phrases like "verify you are human" are removed to prevent false positives
                            # "protected by recaptcha" is NOT a blocking phrase - it's just a badge
                            blocking_phrases = [
                                'complete the captcha to continue',
                                'complete the security check to continue',
                                'verify you are human to continue',
                                'solve the captcha to proceed',
                                'you must complete the captcha',
                            ]
                            
                            for phrase in blocking_phrases:
                                if phrase in visible_text_lower:
                                    captcha_detected = True
                                    logger.info(f"✋ BLOCKING CAPTCHA text detected: {phrase}")
                                    break
                        except:
                            pass
                    
                except Exception as e:
                    logger.error(f"CAPTCHA detection error: {e}")
                    # On error, assume no CAPTCHA rather than blocking the user
                    captcha_detected = False
                
                logger.info(f"🔍 CAPTCHA check: {'CAPTCHA FOUND' if captcha_detected else 'No CAPTCHA - proceeding'}")
                
                if captcha_detected:
                    await browser.close()
                    return {
                        "success": False,
                        "captcha_detected": True,
                        "fields_filled": [],
                        "fields_failed": [],
                        "error": "CAPTCHA detected"
                    }
                
                # Check for login requirement - use visible text, not raw HTML
                # Many job sites have "sign in" links but don't require login to apply
                login_blockers = [
                    'login required',
                    'please sign in to continue',
                    'you must be logged in',
                    'sign in to apply'
                ]
                
                try:
                    visible_text = await page.inner_text('body')
                    visible_text_lower = visible_text.lower()
                    for blocker in login_blockers:
                        if blocker in visible_text_lower:
                            await browser.close()
                            return {
                                "success": False,
                                "captcha_detected": False,
                                "fields_filled": [],
                                "fields_failed": [],
                                "error": "Login required - please apply directly"
                            }
                except:
                    pass
                
                # Define field selectors based on ATS type
                field_selectors = get_field_selectors(ats_type)
                
                # ========================================
                # SMART FIELD DETECTION AND FILLING
                # ========================================
                
                # First, find all required fields on the page
                required_field_script = """
                () => {
                    const requiredFields = [];
                    
                    // Find all input, select, and textarea elements
                    const formElements = document.querySelectorAll('input, select, textarea');
                    
                    formElements.forEach(el => {
                        const isRequired = 
                            el.hasAttribute('required') ||
                            el.getAttribute('aria-required') === 'true' ||
                            el.classList.contains('required') ||
                            (el.closest('label') && el.closest('label').textContent.includes('*')) ||
                            (el.closest('.field') && el.closest('.field').querySelector('.required')) ||
                            (el.previousElementSibling && el.previousElementSibling.textContent.includes('*')) ||
                            (document.querySelector(`label[for="${el.id}"]`)?.textContent.includes('*'));
                        
                        if (isRequired || el.type === 'email' || el.name?.toLowerCase().includes('email')) {
                            const label = 
                                document.querySelector(`label[for="${el.id}"]`)?.textContent ||
                                el.closest('label')?.textContent ||
                                el.placeholder ||
                                el.name ||
                                el.id ||
                                '';
                            
                            requiredFields.push({
                                type: el.tagName.toLowerCase(),
                                inputType: el.type || 'text',
                                name: el.name || '',
                                id: el.id || '',
                                placeholder: el.placeholder || '',
                                label: label.replace('*', '').trim().substring(0, 100),
                                isVisible: el.offsetParent !== null,
                                selector: el.id ? `#${el.id}` : (el.name ? `[name="${el.name}"]` : null)
                            });
                        }
                    });
                    
                    return requiredFields;
                }
                """
                
                try:
                    required_fields = await page.evaluate(required_field_script)
                    logger.info(f"📋 Found {len(required_fields)} required/important fields")
                    for rf in required_fields[:10]:  # Log first 10
                        logger.debug(f"   - {rf.get('label', 'unknown')}: {rf.get('type')}/{rf.get('inputType')} [{rf.get('name') or rf.get('id')}]")
                except Exception as e:
                    logger.warning(f"Could not detect required fields: {e}")
                    required_fields = []
                
                # Build smart field mapping (label/name patterns -> auto_fill_data keys)
                field_mapping = {
                    # Name fields
                    r'first.?name|given.?name|fname': 'first_name',
                    r'last.?name|family.?name|surname|lname': 'last_name',
                    r'full.?name|name': 'full_name',
                    
                    # Contact
                    r'email|e-mail': 'email',
                    r'phone|mobile|cell|telephone': 'phone',
                    
                    # Location
                    r'city|town': 'city',
                    r'state|province|region': 'state',
                    r'country|nation': 'country',
                    r'postal|zip|postcode': 'postal_code',
                    r'address': 'address',
                    
                    # Professional links
                    r'linkedin': 'linkedin',
                    r'github': 'github',
                    r'portfolio|website|personal.?site|url': 'portfolio',
                    
                    # Work
                    r'company|employer|organization|current.?company': 'current_company',
                    r'title|position|role|job.?title|current.?title': 'current_title',
                    r'experience|years': 'years_experience',
                    
                    # Education
                    r'education|degree|qualification': 'education',
                    r'university|school|college|institution': 'university',
                    
                    # Work authorization
                    r'authorized|authorization|legal|eligible|right.?to.?work': 'authorized_to_work',
                    r'sponsor|visa.?sponsor': 'requires_sponsorship',
                    r'visa|work.?permit|immigration': 'visa_status',
                    
                    # Availability
                    r'relocate|relocation|willing.?to.?move': 'willing_to_relocate',
                    r'notice|availability|start.?date|available|earliest': 'start_date',
                    
                    # Salary
                    r'salary|compensation|pay|expected': 'salary_expectation',
                    
                    # Referral
                    r'hear|heard|source|referr|how.?did.?you': 'referral_source',
                }
                
                import re
                
                # Helper function to fill a field with React-compatible events
                async def fill_field_react_compatible(element, value, field_name):
                    """Fill a field using React-compatible event dispatching"""
                    try:
                        # Focus the element
                        await element.focus()
                        await asyncio.sleep(0.1)
                        
                        # Clear existing value
                        await element.evaluate('el => el.value = ""')
                        
                        # Type the value character by character for React compatibility
                        await element.type(str(value), delay=10)
                        
                        # Dispatch events to trigger React state updates
                        await element.evaluate('''el => {
                            el.dispatchEvent(new Event("input", { bubbles: true }));
                            el.dispatchEvent(new Event("change", { bubbles: true }));
                            el.dispatchEvent(new Event("blur", { bubbles: true }));
                        }''')
                        
                        logger.info(f"✅ Filled {field_name}: {str(value)[:30]}...")
                        return True
                    except Exception as e:
                        logger.error(f"❌ Error filling field {field_name}: {e}")
                        return False
                
                # Helper function to handle dropdown/select fields
                async def fill_dropdown(element, value, field_name):
                    """Fill a dropdown/select field by finding matching option"""
                    try:
                        # Get all options
                        options = await element.query_selector_all('option')
                        
                        value_lower = str(value).lower()
                        best_match = None
                        
                        for option in options:
                            option_text = await option.text_content()
                            option_value = await option.get_attribute('value')
                            
                            if option_text and value_lower in option_text.lower():
                                best_match = option_value or option_text
                                break
                            elif option_value and value_lower in option_value.lower():
                                best_match = option_value
                                break
                        
                        if best_match:
                            await element.select_option(value=best_match)
                            await element.evaluate('el => el.dispatchEvent(new Event("change", { bubbles: true }))')
                            logger.info(f"✅ Selected dropdown {field_name}: {best_match}")
                            return True
                        else:
                            # Try selecting by visible text
                            await element.select_option(label=str(value))
                            logger.info(f"✅ Selected dropdown {field_name}: {value}")
                            return True
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select dropdown {field_name}: {e}")
                        return False
                
                # Helper function to handle radio buttons
                async def fill_radio(page, field_name, value):
                    """Fill a radio button by finding the matching option"""
                    try:
                        value_lower = str(value).lower()
                        
                        # Find radio buttons with matching name and value/label
                        radio_selectors = [
                            f'input[type="radio"][value*="{value}" i]',
                            f'input[type="radio"][id*="{value}" i]',
                        ]
                        
                        for selector in radio_selectors:
                            radio = await page.query_selector(selector)
                            if radio:
                                await radio.click()
                                logger.info(f"✅ Selected radio {field_name}: {value}")
                                return True
                        
                        # Try finding by label text
                        labels = await page.query_selector_all('label')
                        for label in labels:
                            label_text = await label.text_content()
                            if label_text and value_lower in label_text.lower():
                                radio_input = await label.query_selector('input[type="radio"]')
                                if radio_input:
                                    await radio_input.click()
                                    logger.info(f"✅ Selected radio {field_name} via label: {value}")
                                    return True
                        
                        return False
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select radio {field_name}: {e}")
                        return False
                
                # Now fill fields using both detected required fields AND standard selectors
                filled_field_names = set()
                
                # First, try to fill detected required fields
                for rf in required_fields:
                    if not rf.get('isVisible'):
                        continue
                    
                    selector = rf.get('selector')
                    if not selector:
                        continue
                    
                    field_label = (rf.get('label', '') + ' ' + rf.get('name', '') + ' ' + rf.get('id', '') + ' ' + rf.get('placeholder', '')).lower()
                    
                    # Find matching data key
                    matched_key = None
                    for pattern, data_key in field_mapping.items():
                        if re.search(pattern, field_label, re.IGNORECASE):
                            matched_key = data_key
                            break
                    
                    if not matched_key:
                        continue
                    
                    value = auto_fill_data.get(matched_key)
                    if not value:
                        logger.warning(f"⚠️ Required field '{rf.get('label', selector)}' has no matching profile data for '{matched_key}'")
                        continue
                    
                    if matched_key in filled_field_names:
                        continue
                    
                    try:
                        element = await page.query_selector(selector)
                        if not element:
                            continue
                        
                        field_type = rf.get('type', 'input')
                        input_type = rf.get('inputType', 'text')
                        
                        if field_type == 'select':
                            if await fill_dropdown(element, value, matched_key):
                                fields_filled.append(matched_key)
                                filled_field_names.add(matched_key)
                        elif input_type == 'radio':
                            if await fill_radio(page, matched_key, value):
                                fields_filled.append(matched_key)
                                filled_field_names.add(matched_key)
                        elif input_type == 'checkbox':
                            # For checkboxes, click if value is truthy
                            if value and str(value).lower() in ['yes', 'true', '1']:
                                await element.click()
                                fields_filled.append(matched_key)
                                filled_field_names.add(matched_key)
                                logger.info(f"✅ Checked checkbox {matched_key}")
                        else:
                            # Text input or textarea
                            if await fill_field_react_compatible(element, value, matched_key):
                                fields_filled.append(matched_key)
                                filled_field_names.add(matched_key)
                    except Exception as e:
                        logger.error(f"❌ Error filling {matched_key}: {e}")
                        fields_failed.append(matched_key)
                
                # Second pass: Use standard selectors for any fields not yet filled
                for field_name, selectors in field_selectors.items():
                    if field_name in filled_field_names:
                        continue
                    
                    value = auto_fill_data.get(field_name)
                    if not value:
                        continue
                    
                    filled = False
                    for selector in selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                is_visible = await element.is_visible()
                                if is_visible:
                                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                                    
                                    if tag_name == 'select':
                                        filled = await fill_dropdown(element, value, field_name)
                                    else:
                                        filled = await fill_field_react_compatible(element, value, field_name)
                                    
                                    if filled:
                                        fields_filled.append(field_name)
                                        filled_field_names.add(field_name)
                                        break
                        except Exception as e:
                            continue
                    
                    if not filled and value:
                        fields_failed.append(field_name)
                
                # Handle cover letter textarea
                if auto_fill_data.get("cover_letter"):
                    cover_selectors = [
                        'textarea[name*="cover" i]',
                        'textarea[id*="cover" i]',
                        'textarea[placeholder*="cover" i]',
                        'textarea[aria-label*="cover" i]',
                    ]
                    for selector in cover_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.fill(auto_fill_data["cover_letter"])
                                fields_filled.append("cover_letter")
                                logger.info("✅ Filled cover letter")
                                break
                        except:
                            continue
                
                # Handle resume file upload
                if temp_resume_path and os.path.exists(temp_resume_path):
                    resume_selectors = [
                        'input[type="file"][name*="resume" i]',
                        'input[type="file"][id*="resume" i]',
                        'input[type="file"][name*="cv" i]',
                        'input[type="file"][id*="cv" i]',
                        'input[type="file"][accept*="pdf"]',
                        'input[type="file"][accept*="doc"]',
                        'input[type="file"]:not([name*="cover" i])',
                    ]
                    resume_uploaded = False
                    for selector in resume_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.set_input_files(temp_resume_path)
                                fields_filled.append("resume")
                                resume_uploaded = True
                                logger.info(f"✅ Resume uploaded via selector: {selector}")
                                break
                        except Exception as e:
                            logger.debug(f"Resume upload failed for {selector}: {e}")
                            continue
                    
                    if not resume_uploaded:
                        fields_failed.append("resume")
                        logger.warning("⚠️ Could not find resume file input")
                
                # ========================================
                # AUTO-SUBMIT: Find and click submit button
                # Only if submit_form=True (user confirmed)
                # ========================================
                submit_clicked = False
                submit_error = None
                
                if submit_form:
                    logger.info("🚀 submit_form=True - Attempting to submit application...")
                    
                    # Wait a moment for form validation
                    await asyncio.sleep(1)
                    
                    # Submit button selectors (common patterns across ATS platforms)
                    submit_selectors = [
                        # Standard submit buttons
                        'button[type="submit"]',
                        'input[type="submit"]',
                        # Text-based buttons
                        'button:has-text("Submit Application")',
                        'button:has-text("Submit")',
                        'button:has-text("Apply")',
                        'button:has-text("Apply Now")',
                        'button:has-text("Send Application")',
                        'button:has-text("Complete Application")',
                        # ID/class based
                        'button[id*="submit" i]',
                        'button[class*="submit" i]',
                        '#submit-btn',
                        '#submit_app',
                        '.submit-button',
                        '.apply-button',
                        # Greenhouse specific
                        'button[data-test="submit-application"]',
                        # Lever specific
                        'button.postings-btn-submit',
                        'button[data-qa="btn-submit"]',
                        # SmartRecruiters specific
                        'button[data-test="footer-submit"]',
                        # Generic fallbacks
                        'form button[type="submit"]',
                        'form input[type="submit"]',
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            submit_btn = await page.query_selector(selector)
                            if submit_btn:
                                is_visible = await submit_btn.is_visible()
                                is_enabled = await submit_btn.is_enabled()
                                
                                if is_visible and is_enabled:
                                    logger.info(f"🔘 Found submit button: {selector}")
                                    
                                    # Scroll to button
                                    await submit_btn.scroll_into_view_if_needed()
                                    await asyncio.sleep(0.5)
                                    
                                    # Click the submit button
                                    await submit_btn.click()
                                    submit_clicked = True
                                    logger.info("🚀 Clicked submit button!")
                                    
                                    # Wait for submission to process
                                    await asyncio.sleep(3)
                                    
                                    # Check for success indicators
                                    page_content = await page.content()
                                    page_content_lower = page_content.lower()
                                    final_url = page.url
                                    
                                    success_indicators = [
                                        'thank you',
                                        'application received',
                                        'application submitted',
                                        'successfully submitted',
                                        'we have received your application',
                                        'application complete',
                                        'thanks for applying',
                                        'thank you for applying',
                                    ]
                                    
                                    # Check URL for confirmation patterns
                                    url_success_patterns = [
                                        '/thank', '/success', '/confirm', '/complete', 
                                        '/submitted', '/received', '/done'
                                    ]
                                    url_indicates_success = any(pattern in final_url.lower() for pattern in url_success_patterns)
                                    
                                    submission_confirmed = any(ind in page_content_lower for ind in success_indicators) or url_indicates_success
                                    
                                    # Take a screenshot as evidence
                                    screenshot_base64 = None
                                    try:
                                        screenshot_bytes = await page.screenshot(type='jpeg', quality=50)
                                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                                        logger.info("📸 Captured confirmation screenshot")
                                    except Exception as e:
                                        logger.warning(f"Could not capture screenshot: {e}")
                                    
                                    if submission_confirmed:
                                        logger.info(f"✅ Application submission likely successful! Final URL: {final_url}")
                                    else:
                                        # Check if we're still on the form (might have validation errors)
                                        error_indicators = [
                                            'required field',
                                            'please fill',
                                            'this field is required',
                                            'error',
                                            'invalid',
                                        ]
                                        has_errors = any(err in page_content_lower for err in error_indicators)
                                        if has_errors:
                                            logger.warning("⚠️ Form may have validation errors")
                                            submit_error = "Form validation errors detected - check screenshot"
                                        else:
                                            logger.info(f"📝 Submit clicked but no confirmation detected. Final URL: {final_url}")
                                            submit_error = "Submit clicked but confirmation not detected - verify via email"
                                    
                                    break
                        except Exception as e:
                            logger.debug(f"Submit button {selector} not usable: {e}")
                            continue
                    
                    if not submit_clicked:
                        logger.warning("⚠️ Could not find or click submit button")
                        submit_error = "Submit button not found"
                        final_url = page.url
                        screenshot_base64 = None
                        submission_confirmed = False
                else:
                    # submit_form=False - Just fill, don't submit
                    logger.info("📝 Form filled (submit_form=False - no submission)")
                    final_url = page.url
                    screenshot_base64 = None
                    submission_confirmed = False
                
                await browser.close()
                
                # Cleanup temp file
                if temp_resume_path and os.path.exists(temp_resume_path):
                    try:
                        os.remove(temp_resume_path)
                    except:
                        pass
                
                return {
                    "success": len(fields_filled) > 0,
                    "submitted": submit_clicked,
                    "submission_confirmed": submission_confirmed if submit_form else None,
                    "final_url": final_url if submit_form else None,
                    "screenshot": screenshot_base64 if submit_form and submit_clicked else None,
                    "captcha_detected": False,
                    "fields_filled": fields_filled,
                    "fields_failed": fields_failed,
                    "submit_error": submit_error,
                    "error": None
                }
                
            except PlaywrightTimeout:
                await browser.close()
                # Cleanup temp file
                if temp_resume_path and os.path.exists(temp_resume_path):
                    try:
                        os.remove(temp_resume_path)
                    except:
                        pass
                return {
                    "success": False,
                    "captcha_detected": False,
                    "fields_filled": fields_filled,
                    "fields_failed": fields_failed,
                    "error": "Page load timeout"
                }
            except Exception as e:
                await browser.close()
                # Cleanup temp file
                if temp_resume_path and os.path.exists(temp_resume_path):
                    try:
                        os.remove(temp_resume_path)
                    except:
                        pass
                return {
                    "success": False,
                    "captcha_detected": False,
                    "fields_filled": fields_filled,
                    "fields_failed": fields_failed,
                    "error": str(e)
                }
                
    except Exception as e:
        logger.error(f"Playwright error: {str(e)}")
        # Cleanup temp file
        if temp_resume_path and os.path.exists(temp_resume_path):
            try:
                os.remove(temp_resume_path)
            except:
                pass
        return {
            "success": False,
            "captcha_detected": False,
            "fields_filled": [],
            "fields_failed": [],
            "error": str(e)
        }


def get_field_selectors(ats_type: str) -> dict:
    """Get field selectors based on ATS type."""
    
    # Common selectors that work across most ATS
    common = {
        "first_name": [
            'input[name="first_name"]', 'input[name="firstName"]',
            'input[id*="first_name"]', 'input[id*="firstName"]',
            'input[autocomplete="given-name"]',
            'input[placeholder*="First" i]',
        ],
        "last_name": [
            'input[name="last_name"]', 'input[name="lastName"]',
            'input[id*="last_name"]', 'input[id*="lastName"]',
            'input[autocomplete="family-name"]',
            'input[placeholder*="Last" i]',
        ],
        "full_name": [
            'input[name="name"]', 'input[name="fullName"]',
            'input[id*="name"]:not([id*="first"]):not([id*="last"])',
            'input[placeholder*="Full name" i]',
        ],
        "email": [
            'input[name="email"]', 'input[type="email"]',
            'input[id*="email"]', 'input[autocomplete="email"]',
        ],
        "phone": [
            'input[name="phone"]', 'input[type="tel"]',
            'input[id*="phone"]', 'input[autocomplete="tel"]',
            'input[placeholder*="phone" i]',
        ],
        "linkedin": [
            'input[name*="linkedin" i]', 'input[id*="linkedin" i]',
            'input[placeholder*="linkedin" i]',
        ],
        "github": [
            'input[name*="github" i]', 'input[id*="github" i]',
            'input[placeholder*="github" i]',
        ],
        "portfolio": [
            'input[name*="portfolio" i]', 'input[name*="website" i]',
            'input[id*="portfolio" i]', 'input[id*="website" i]',
            'input[placeholder*="portfolio" i]', 'input[placeholder*="website" i]',
        ],
        "city": [
            'input[name="city"]', 'input[id*="city"]',
            'input[autocomplete="address-level2"]',
        ],
        "state": [
            'input[name="state"]', 'input[name="province"]',
            'input[id*="state"]', 'input[id*="province"]',
        ],
        "current_company": [
            'input[name*="company" i]', 'input[name*="employer" i]',
            'input[id*="company" i]', 'input[placeholder*="company" i]',
        ],
    }
    
    # ATS-specific additions
    if ats_type == "greenhouse":
        # Greenhouse uses standard naming
        pass
    elif ats_type == "lever":
        # Lever sometimes uses full name instead of first/last
        common["full_name"].insert(0, 'input[name="name"]')
    elif ats_type == "ashby":
        # Ashby uses aria-labels
        for field in common:
            common[field].append(f'input[aria-label*="{field.replace("_", " ")}" i]')
    elif ats_type == "smartrecruiters":
        # SmartRecruiters uses data-test attributes and specific class names
        common["first_name"].extend([
            'input[data-test="first-name"]',
            'input[class*="firstName"]',
        ])
        common["last_name"].extend([
            'input[data-test="last-name"]',
            'input[class*="lastName"]',
        ])
        common["email"].extend([
            'input[data-test="email"]',
        ])
        common["phone"].extend([
            'input[data-test="phone"]',
        ])
    elif ats_type == "pinpoint":
        # Pinpoint uses standard naming with some variations
        common["first_name"].extend([
            'input[name="candidate[first_name]"]',
            'input[id="candidate_first_name"]',
        ])
        common["last_name"].extend([
            'input[name="candidate[last_name]"]',
            'input[id="candidate_last_name"]',
        ])
        common["email"].extend([
            'input[name="candidate[email]"]',
            'input[id="candidate_email"]',
        ])
        common["phone"].extend([
            'input[name="candidate[phone]"]',
            'input[id="candidate_phone"]',
        ])
    elif ats_type == "unknown":
        # For unknown ATS, add more generic selectors
        for field in common:
            common[field].append(f'input[name*="{field}" i]')
            common[field].append(f'input[id*="{field}" i]')
    
    return common

@router.put("/applications/{application_id}/reject")
async def reject_application(request: Request, application_id: str):
    """Reject/skip an application."""
    user = await get_current_user(request)
    
    await db.applications.update_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"$set": {"status": "rejected"}}
    )
    
    updated = await db.applications.find_one(
        {"application_id": application_id},
        {"_id": 0}
    )
    
    return updated

@router.delete("/applications/{application_id}")
async def delete_application(request: Request, application_id: str):
    """Delete an application."""
    user = await get_current_user(request)
    
    result = await db.applications.delete_one(
        {"application_id": application_id, "user_id": user.user_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application deleted"}

# ========================
# NEXT STEPS ("What to Do Next") ENDPOINTS
# ========================

def get_default_next_steps():
    """Return the default next steps structure for a new application."""
    return {
        "follow_company": {
            "completed": False,
            "title": "Follow the Company",
            "description": "Stay visible in their network. Recruiters often check who's engaging with their content — this puts your name on their radar before they even review applications.",
            "why_important": "85% of jobs are filled through networking. Following shows genuine interest."
        },
        "find_recruiter": {
            "completed": False,
            "title": "Find Recruiter/Hiring Manager",
            "description": "Most applicants never reach the decision-maker directly. Finding the right person lets you bypass the ATS black hole and get your application seen by someone who can actually hire you.",
            "why_important": "Direct outreach increases response rates by 40% compared to just applying."
        },
        "send_message": {
            "completed": False,
            "title": "Send a Message",
            "description": "A personalized message makes you memorable. While 98% of applicants stay silent, a thoughtful note can move you from 'maybe' to 'interview' pile.",
            "why_important": "Candidates who reach out are 3x more likely to get an interview.",
            "generated_content": None
        },
        "prep_interview": {
            "completed": False,
            "title": "Prep Interview Questions",
            "description": "Don't wait for the interview invite to prepare. The best candidates practice answers tailored to THIS role — so when you get the call, you're already ahead.",
            "why_important": "Prepared candidates score 50% higher in interviews than those who wing it.",
            "generated_questions": None
        },
        "track_outcome": {
            "completed": False,
            "title": "Track Outcome",
            "description": "Keep your job search organized. Knowing where each application stands helps you follow up strategically and learn what's working.",
            "why_important": "Organized job seekers land roles 2x faster than those who lose track.",
            "outcome": "pending"  # pending, interview_scheduled, rejected, offer
        },
        "follow_up": {
            "completed": False,
            "title": "Follow Up in 7 Days",
            "description": "Most candidates never follow up — and miss out. A polite check-in shows persistence and keeps you top-of-mind when hiring decisions are made.",
            "why_important": "Following up can increase your chances of a response by 30%.",
            "reminder_date": None
        }
    }

@router.get("/applications/{application_id}/next-steps")
async def get_next_steps(request: Request, application_id: str):
    """Get the next steps progress for an application."""
    user = await get_current_user(request)
    
    app = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Return existing progress or default
    next_steps = app.get("next_steps_progress") or get_default_next_steps()
    
    # Calculate progress
    completed_count = sum(1 for step in next_steps.values() if step.get("completed"))
    total_count = len(next_steps)
    
    return {
        "application_id": application_id,
        "job_title": app.get("job_title"),
        "company": app.get("company"),
        "status": app.get("status"),
        "next_steps": next_steps,
        "progress": {
            "completed": completed_count,
            "total": total_count,
            "percentage": round((completed_count / total_count) * 100) if total_count > 0 else 0
        }
    }

@router.put("/applications/{application_id}/next-steps")
async def update_next_step(request: Request, application_id: str, update: NextStepUpdate):
    """Update a single next step's completion status or data."""
    user = await get_current_user(request)
    
    app = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get existing or default next steps
    next_steps = app.get("next_steps_progress") or get_default_next_steps()
    
    # Validate step_id
    if update.step_id not in next_steps:
        raise HTTPException(status_code=400, detail=f"Invalid step_id: {update.step_id}")
    
    # Update the specific step
    if update.completed is not None:
        next_steps[update.step_id]["completed"] = update.completed
    
    if update.outcome is not None and update.step_id == "track_outcome":
        next_steps[update.step_id]["outcome"] = update.outcome
    
    if update.reminder_date is not None and update.step_id == "follow_up":
        next_steps[update.step_id]["reminder_date"] = update.reminder_date
    
    # Save to database
    await db.applications.update_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"$set": {"next_steps_progress": next_steps}}
    )
    
    # Calculate progress
    completed_count = sum(1 for step in next_steps.values() if step.get("completed"))
    total_count = len(next_steps)
    
    return {
        "success": True,
        "step_id": update.step_id,
        "next_steps": next_steps,
        "progress": {
            "completed": completed_count,
            "total": total_count,
            "percentage": round((completed_count / total_count) * 100) if total_count > 0 else 0
        }
    }

@router.post("/applications/{application_id}/next-steps/generate")
async def generate_next_step_content(request: Request, application_id: str, req: NextStepContentRequest):
    """Generate AI content for send_message or prep_interview steps."""
    user = await get_current_user(request)
    
    app = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get user profile for personalization
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if profile:
        profile = decrypt_sensitive_data(profile)
    
    # Get user info
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    user_name = user_doc.get("name", "Applicant") if user_doc else "Applicant"
    
    job_title = app.get("job_title", "the position")
    company = app.get("company", "the company")
    job_description = app.get("job_description", "")
    optimized_resume = app.get("optimized_resume", "")
    
    # Extract skills from profile
    skills = []
    if profile and profile.get("skills"):
        for skill in profile.get("skills", []):
            if isinstance(skill, dict):
                skills.append(skill.get("name", ""))
            else:
                skills.append(str(skill))
    skills_text = ", ".join(skills[:10]) if skills else "various relevant skills"
    
    # Generate content based on step_id
    if req.step_id == "send_message":
        content_type = req.content_type or "linkedin_message"
        generated_content = await generate_outreach_message(
            user_name, job_title, company, job_description, skills_text, optimized_resume, content_type
        )
        
        # Save to next_steps_progress
        next_steps = app.get("next_steps_progress") or get_default_next_steps()
        next_steps["send_message"]["generated_content"] = generated_content
        
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {"next_steps_progress": next_steps}}
        )
        
        return {
            "success": True,
            "step_id": "send_message",
            "content_type": content_type,
            "generated_content": generated_content
        }
    
    elif req.step_id == "prep_interview":
        generated_questions = await generate_interview_questions(
            user_name, job_title, company, job_description, skills_text, optimized_resume
        )
        
        # Save to next_steps_progress
        next_steps = app.get("next_steps_progress") or get_default_next_steps()
        next_steps["prep_interview"]["generated_questions"] = generated_questions
        
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {"next_steps_progress": next_steps}}
        )
        
        return {
            "success": True,
            "step_id": "prep_interview",
            "generated_questions": generated_questions
        }
    
    else:
        raise HTTPException(status_code=400, detail="Content generation only available for send_message and prep_interview steps")

async def generate_outreach_message(user_name: str, job_title: str, company: str, 
                                     job_description: str, skills: str, resume: str, 
                                     content_type: str) -> str:
    """Generate a personalized outreach message using AI."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    if content_type == "connection_request":
        prompt = f"""Write a brief LinkedIn connection request (under 300 characters) for someone who just applied to a {job_title} position at {company}.

Applicant name: {user_name}
Key skills: {skills}

Requirements:
- Be professional but friendly
- Mention the specific role applied for
- Keep it concise (LinkedIn has a 300 character limit for connection requests)
- Don't be overly formal or salesy
- Express genuine interest in connecting

Write ONLY the message text, no quotes or explanations."""
    
    elif content_type == "email":
        prompt = f"""Write a professional follow-up email for someone who applied to a {job_title} position at {company}.

Applicant name: {user_name}
Key skills: {skills}
Job description summary: {job_description[:500] if job_description else 'Not available'}
Resume highlights: {resume[:500] if resume else 'Not available'}

Requirements:
- Professional but personable tone
- Subject line included
- Reference specific skills/experience relevant to the role
- Express enthusiasm without being pushy
- Include a clear call-to-action
- Keep under 200 words

Format:
Subject: [subject line]

[email body]"""
    
    else:  # linkedin_message
        prompt = f"""Write a LinkedIn message to a recruiter/hiring manager after applying for a {job_title} position at {company}.

Applicant name: {user_name}
Key skills: {skills}
Job description summary: {job_description[:500] if job_description else 'Not available'}
Resume highlights: {resume[:500] if resume else 'Not available'}

Requirements:
- Professional but conversational tone
- Reference the specific position applied for
- Briefly highlight 1-2 relevant qualifications
- Express genuine interest in the company/role
- Include a soft call-to-action
- Keep under 150 words

Write ONLY the message text, no quotes or explanations."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"outreach_{uuid.uuid4().hex[:8]}",
            system_message="You are a professional career coach helping job applicants write effective outreach messages."
        )
        response = await chat.send_message(UserMessage(text=prompt))
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating outreach message: {e}")
        return f"Hi, I recently applied for the {job_title} position at {company} and wanted to connect. I believe my background in {skills} would be a great fit for this role. I'd love to learn more about the opportunity. Thank you!"

async def generate_interview_questions(user_name: str, job_title: str, company: str,
                                        job_description: str, skills: str, resume: str) -> str:
    """Generate personalized interview prep questions and answers using AI."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    prompt = f"""Generate 5 likely interview questions for a {job_title} position at {company}, along with personalized answer suggestions.

Candidate name: {user_name}
Key skills: {skills}
Job description: {job_description[:800] if job_description else 'Not available'}
Resume/background: {resume[:800] if resume else 'Not available'}

Requirements:
- Include a mix of behavioral and technical questions
- Tailor questions to the specific role and company
- Provide concise but strong answer suggestions
- Use STAR method hints for behavioral questions
- Keep answers professional and achievement-focused

Format each Q&A as:
**Q1: [Question]**
💡 Suggested Answer: [Answer suggestion in 2-3 sentences]

**Q2: [Question]**
💡 Suggested Answer: [Answer]

...and so on for all 5 questions."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"interview_{uuid.uuid4().hex[:8]}",
            system_message="You are an expert career coach helping candidates prepare for job interviews."
        )
        response = await chat.send_message(UserMessage(text=prompt))
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        return f"""**Q1: Tell me about yourself and why you're interested in this {job_title} role.**
💡 Suggested Answer: Focus on your relevant experience with {skills} and express genuine interest in {company}'s mission.

**Q2: What's your greatest strength relevant to this position?**
💡 Suggested Answer: Highlight a key skill from your background that directly applies to the role.

**Q3: Describe a challenging project you've worked on.**
💡 Suggested Answer: Use the STAR method - Situation, Task, Action, Result.

**Q4: Why do you want to work at {company}?**
💡 Suggested Answer: Research the company and mention specific things that attract you.

**Q5: Where do you see yourself in 5 years?**
💡 Suggested Answer: Show ambition while aligning with the company's growth trajectory."""

def create_docx_from_text(text: str, title: str = None) -> bytes:
    """Create a DOCX file from text content and return bytes."""
    doc = Document()
    
    # Add title if provided
    if title:
        doc.add_heading(title, 0)
    
    # Split text by newlines and add paragraphs
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para)
    
    # Save to BytesIO and return bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# Legacy downloads directory (kept for backwards compatibility)
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def cleanup_old_static_downloads(max_age_minutes: int = 30):
    """Remove files older than max_age_minutes from static downloads directory."""
    try:
        now = datetime.now()
        for filename in os.listdir(STATIC_DOWNLOADS_DIR):
            filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_age.total_seconds() > max_age_minutes * 60:
                    os.remove(filepath)
                    logger.info(f"Cleaned up old download: {filename}")
    except Exception as e:
        logger.error(f"Error cleaning up static downloads: {e}")

def generate_and_save_docx(text: str, user_id: str, job_id: str, doc_type: str) -> str:
    """
    Generate a DOCX file and save it to disk.
    Returns the file_id for downloading.
    """
    doc = Document()
    
    # Add content
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para)
    
    # Generate unique filename
    file_id = f"{doc_type}_{user_id}_{job_id}"
    filename = f"{file_id}.docx"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    # Save to disk
    doc.save(filepath)
    logger.info(f"Saved DOCX to: {filepath}")
    
    return file_id

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download a generated DOCX file.
    file_id format: {doc_type}_{user_id}_{job_id}
    """
    filename = f"{file_id}.docx"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine friendly filename
    parts = file_id.split('_', 1)
    doc_type = parts[0] if parts else "document"
    friendly_name = f"{doc_type}.docx"
    
    # Read file content
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Return as downloadable response
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{friendly_name}"',
            "Content-Length": str(len(content)),
            "Cache-Control": "no-cache"
        }
    )

@router.get("/download-page/{file_id}")
async def download_page(file_id: str):
    """
    Returns an HTML page that auto-triggers download.
    This is a fallback for browsers that block direct downloads.
    """
    filename = f"{file_id}.docx"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Read file and convert to base64
    import base64
    with open(filepath, 'rb') as f:
        content = f.read()
    
    b64_content = base64.b64encode(content).decode('utf-8')
    
    parts = file_id.split('_', 1)
    doc_type = parts[0] if parts else "document"
    friendly_name = f"{doc_type}.docx"
    
    # Return HTML page that triggers download
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Downloading {friendly_name}...</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a2e; color: white; }}
            .container {{ text-align: center; }}
            .spinner {{ width: 50px; height: 50px; border: 3px solid #333; border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            a {{ color: #6366f1; text-decoration: none; padding: 10px 20px; border: 1px solid #6366f1; border-radius: 5px; display: inline-block; margin-top: 20px; }}
            a:hover {{ background: #6366f1; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h2>Downloading {friendly_name}...</h2>
            <p>Your download should start automatically.</p>
            <p id="status"></p>
            <a href="#" id="manual-link" style="display:none;">Click here if download doesn't start</a>
        </div>
        <script>
            (function() {{
                var b64 = "{b64_content}";
                var filename = "{friendly_name}";
                
                // Convert base64 to blob
                var byteCharacters = atob(b64);
                var byteNumbers = new Array(byteCharacters.length);
                for (var i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                var byteArray = new Uint8Array(byteNumbers);
                var blob = new Blob([byteArray], {{type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}});
                
                // Create download link
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = filename;
                
                // Try to trigger download
                document.body.appendChild(a);
                a.click();
                
                // Show manual link after 2 seconds
                setTimeout(function() {{
                    var manualLink = document.getElementById('manual-link');
                    manualLink.href = url;
                    manualLink.download = filename;
                    manualLink.style.display = 'inline-block';
                    document.getElementById('status').textContent = 'If the download did not start, click the button below.';
                }}, 2000);
                
                // Cleanup
                setTimeout(function() {{
                    document.body.removeChild(a);
                }}, 100);
            }})();
        </script>
    </body>
    </html>
    """
    
    return Response(content=html, media_type="text/html")

@router.post("/applications/{application_id}/generate-resume-docx")
async def generate_resume_docx(request: Request, application_id: str):
    """Generate and save optimized resume as DOCX, return download URL."""
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("optimized_resume"):
        raise HTTPException(status_code=400, detail="No optimized resume found")
    
    try:
        file_id = generate_and_save_docx(
            text=app_doc["optimized_resume"],
            user_id=user.user_id,
            job_id=application_id,
            doc_type="resume"
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/api/download/{file_id}",
            "filename": f"Resume_{app_doc.get('company', 'Company')}_{app_doc.get('job_title', 'Position')}.docx"
        }
    except Exception as e:
        logger.error(f"Failed to generate resume DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate file: {str(e)}")

@router.post("/applications/{application_id}/generate-cover-letter-docx")
async def generate_cover_letter_docx(request: Request, application_id: str):
    """Generate and save cover letter as DOCX, return download URL."""
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("cover_letter"):
        raise HTTPException(status_code=400, detail="No cover letter found")
    
    try:
        file_id = generate_and_save_docx(
            text=app_doc["cover_letter"],
            user_id=user.user_id,
            job_id=application_id,
            doc_type="cover_letter"
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/api/download/{file_id}",
            "filename": f"CoverLetter_{app_doc.get('company', 'Company')}_{app_doc.get('job_title', 'Position')}.docx"
        }
    except Exception as e:
        logger.error(f"Failed to generate cover letter DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate file: {str(e)}")

@router.post("/applications/{application_id}/prepare-download/resume")
async def prepare_resume_download(request: Request, application_id: str):
    """
    Prepare resume download - generates file and returns public download URL.
    """
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("optimized_resume"):
        raise HTTPException(status_code=400, detail="No optimized resume found")
    
    # Create filename
    company = re.sub(r'[^\w\s-]', '', app_doc.get("company", "Company")).replace(" ", "_")
    job_title = re.sub(r'[^\w\s-]', '', app_doc.get("job_title", "Position")).replace(" ", "_")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"Resume_{company}_{job_title}_{unique_id}.docx"
    
    # Create and save DOCX
    docx_bytes = create_docx_from_text(app_doc["optimized_resume"])
    filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(docx_bytes)
    
    # Return the public download URL
    return {"download_url": f"/api/static-downloads/{filename}", "filename": filename}

@router.post("/applications/{application_id}/prepare-download/cover-letter")
async def prepare_cover_letter_download(request: Request, application_id: str):
    """
    Prepare cover letter download - generates file and returns public download URL.
    """
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("cover_letter"):
        raise HTTPException(status_code=400, detail="No cover letter found")
    
    # Create filename
    company = re.sub(r'[^\w\s-]', '', app_doc.get("company", "Company")).replace(" ", "_")
    job_title = re.sub(r'[^\w\s-]', '', app_doc.get("job_title", "Position")).replace(" ", "_")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"CoverLetter_{company}_{job_title}_{unique_id}.docx"
    
    # Create and save DOCX
    docx_bytes = create_docx_from_text(app_doc["cover_letter"])
    filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(docx_bytes)
    
    # Return the public download URL
    return {"download_url": f"/api/static-downloads/{filename}", "filename": filename}

@router.get("/applications/{application_id}/download/resume")
async def download_resume_docx(request: Request, application_id: str):
    """
    Download optimized resume as DOCX file.
    Saves to static directory and returns 302 redirect to static file URL.
    """
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("optimized_resume"):
        raise HTTPException(status_code=400, detail="No optimized resume found for this application")
    
    # Create DOCX file - sanitize filename
    company = re.sub(r'[^\w\s-]', '', app_doc.get("company", "Company")).replace(" ", "_")
    job_title = re.sub(r'[^\w\s-]', '', app_doc.get("job_title", "Position")).replace(" ", "_")
    
    # Generate unique filename to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    filename = f"Resume_{company}_{job_title}_{unique_id}.docx"
    
    # Create the DOCX content
    docx_bytes = create_docx_from_text(app_doc["optimized_resume"])
    
    # Save to static downloads directory
    filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(docx_bytes)
    
    logger.info(f"Saved resume to static: {filepath}")
    
    # Return 302 redirect to static file (same approach as test-download which works)
    return RedirectResponse(url=f"/api/static-downloads/{filename}", status_code=302)

@router.get("/applications/{application_id}/download/cover-letter")
async def download_cover_letter_docx(request: Request, application_id: str):
    """
    Download cover letter as DOCX file.
    """
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("cover_letter"):
        raise HTTPException(status_code=400, detail="No cover letter found for this application")
    
    # Create DOCX file - sanitize filename
    company = re.sub(r'[^\w\s-]', '', app_doc.get("company", "Company")).replace(" ", "_")
    job_title = re.sub(r'[^\w\s-]', '', app_doc.get("job_title", "Position")).replace(" ", "_")
    
    # Generate unique filename to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    filename = f"CoverLetter_{company}_{job_title}_{unique_id}.docx"
    
    # Create the DOCX content
    docx_bytes = create_docx_from_text(app_doc["cover_letter"])
    
    # Save to static downloads directory
    filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(docx_bytes)
    
    logger.info(f"Saved cover letter to static: {filepath}")
    
    # Return 302 redirect to static file (same approach as test-download which works)
    return RedirectResponse(url=f"/api/static-downloads/{filename}", status_code=302)

@router.get("/applications/{application_id}/autofill-script")
async def get_autofill_script(request: Request, application_id: str):
    """Generate a JavaScript auto-fill script for Greenhouse applications."""
    user = await get_current_user(request)
    
    # Get application data
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get user profile for contact info
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get user info
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Parse name
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    email = user_doc.get("email", "") if user_doc else ""
    
    # Get resume and cover letter
    resume_text = app_doc.get("optimized_resume") or profile.get("resume_text", "") if profile else ""
    cover_letter = app_doc.get("cover_letter", "")
    
    # Escape strings for JavaScript
    def js_escape(s):
        if not s:
            return ""
        return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    
    # Generate the auto-fill script
    script = f'''// MyCareerCoPilot - Greenhouse Auto-Fill Script
// Application: {js_escape(app_doc.get("job_title", ""))} at {js_escape(app_doc.get("company", ""))}
// Generated for: {js_escape(full_name)}

(function() {{
    const data = {{
        firstName: `{js_escape(first_name)}`,
        lastName: `{js_escape(last_name)}`,
        email: `{js_escape(email)}`,
        resume: `{js_escape(resume_text)}`,
        coverLetter: `{js_escape(cover_letter)}`
    }};

    // Helper to fill input fields
    function fillField(selectors, value) {{
        if (!value) return false;
        for (const selector of selectors) {{
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {{
                if (el && (el.offsetParent !== null || el.type === 'hidden')) {{
                    el.value = value;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log('✓ Filled:', selector);
                    return true;
                }}
            }}
        }}
        return false;
    }}

    // Helper to fill text areas
    function fillTextArea(selectors, value) {{
        if (!value) return false;
        for (const selector of selectors) {{
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {{
                if (el && el.offsetParent !== null) {{
                    el.value = value;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log('✓ Filled textarea:', selector);
                    return true;
                }}
            }}
        }}
        return false;
    }}

    console.log('🚀 MyCareerCoPilot Auto-Fill Starting...');
    console.log('Applying for:', '{js_escape(app_doc.get("job_title", ""))}');

    // Fill first name
    fillField([
        'input[name="first_name"]',
        'input[name="firstName"]',
        'input[id*="first_name"]',
        'input[id*="firstName"]',
        'input[autocomplete="given-name"]',
        'input[placeholder*="First"]'
    ], data.firstName);

    // Fill last name
    fillField([
        'input[name="last_name"]',
        'input[name="lastName"]',
        'input[id*="last_name"]',
        'input[id*="lastName"]',
        'input[autocomplete="family-name"]',
        'input[placeholder*="Last"]'
    ], data.lastName);

    // Fill email
    fillField([
        'input[name="email"]',
        'input[type="email"]',
        'input[id*="email"]',
        'input[autocomplete="email"]',
        'input[placeholder*="email"]'
    ], data.email);

    // Fill cover letter textarea
    fillTextArea([
        'textarea[name*="cover"]',
        'textarea[id*="cover"]',
        'textarea[placeholder*="cover"]',
        'textarea[placeholder*="Cover"]',
        'textarea[name*="letter"]',
        '#cover_letter',
        '.cover-letter textarea'
    ], data.coverLetter);

    // Try to fill resume text field if exists (some forms have text input)
    fillTextArea([
        'textarea[name*="resume"]',
        'textarea[id*="resume"]',
        '#resume_text',
        '.resume-text textarea'
    ], data.resume);

    // Handle file upload hint
    const fileInputs = document.querySelectorAll('input[type="file"]');
    if (fileInputs.length > 0) {{
        console.log('📎 File upload detected - please upload your resume .docx file manually');
    }}

    console.log('');
    console.log('✅ Auto-fill complete!');
    console.log('📋 Please review all fields before submitting.');
    console.log('📎 If there\\'s a file upload, use the downloaded .docx resume.');
    console.log('🔐 Complete any CAPTCHA if required.');
    
    alert('MyCareerCoPilot Auto-Fill Complete!\\n\\n✓ Fields have been filled\\n\\nPlease:\\n1. Review all information\\n2. Upload resume file if required\\n3. Complete any CAPTCHA\\n4. Click Submit');
}})();'''

    return {
        "script": script,
        "application": {
            "job_title": app_doc.get("job_title"),
            "company": app_doc.get("company"),
            "apply_link": app_doc.get("apply_link")
        },
        "user": {
            "name": full_name,
            "email": email
        }
    }

