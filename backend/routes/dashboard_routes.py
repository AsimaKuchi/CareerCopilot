"""
routes/dashboard_routes.py - Dashboard and ATS statistics.

Endpoints (under /api):
  GET /dashboard/stats   -- Aggregate stats for the dashboard home page
  GET /admin/ats-stats   -- ATS scraping statistics (admin)

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Request

from core import (
    db,
    logger,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    CUSTOM_CAREER_COMPANIES,
    get_current_user,
    get_admin_user,
)
from ats_scrapers import SMARTRECRUITERS_COMPANIES, PINPOINT_COMPANIES

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics."""
    user = await get_current_user(request)
    
    # Count applications by status
    total = await db.applications.count_documents({"user_id": user.user_id})
    applied = await db.applications.count_documents({"user_id": user.user_id, "status": "applied"})
    pending = await db.applications.count_documents({"user_id": user.user_id, "status": "pending"})
    
    # Get recent applications
    recent = await db.applications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Get profile completeness
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    completeness = 0
    if profile:
        if profile.get("resume_text"): completeness += 40
        if profile.get("skills"): completeness += 20
        if profile.get("job_titles"): completeness += 20
        if profile.get("preferred_locations"): completeness += 10
        if profile.get("experience_years"): completeness += 10
    
    # Calculate time saved estimates
    # Average time per manual application: ~25 min
    # With autofill: ~5 min per application (saving ~20 min each)
    # Resume optimization: ~30 min saved per optimization
    # Cover letter generation: ~45 min saved per letter
    TIME_SAVED_PER_APPLICATION_MIN = 20
    TIME_SAVED_PER_RESUME_MIN = 30
    TIME_SAVED_PER_COVER_LETTER_MIN = 45

    resumes_generated = await db.applications.count_documents(
        {"user_id": user.user_id, "optimized_resume": {"$exists": True, "$ne": None, "$ne": ""}}
    )
    cover_letters_generated = await db.applications.count_documents(
        {"user_id": user.user_id, "cover_letter": {"$exists": True, "$ne": None, "$ne": ""}}
    )

    time_saved_min = (
        applied * TIME_SAVED_PER_APPLICATION_MIN
        + resumes_generated * TIME_SAVED_PER_RESUME_MIN
        + cover_letters_generated * TIME_SAVED_PER_COVER_LETTER_MIN
    )

    return {
        "total_applications": total,
        "applied": applied,
        "pending": pending,
        "recent_applications": recent,
        "profile_completeness": completeness,
        "time_saved": {
            "total_minutes": time_saved_min,
            "total_hours": round(time_saved_min / 60, 1),
            "applications_autofilled": applied,
            "resumes_generated": resumes_generated,
            "cover_letters_generated": cover_letters_generated,
            "breakdown": {
                "autofill_min": applied * TIME_SAVED_PER_APPLICATION_MIN,
                "resume_min": resumes_generated * TIME_SAVED_PER_RESUME_MIN,
                "cover_letter_min": cover_letters_generated * TIME_SAVED_PER_COVER_LETTER_MIN,
            },
        },
    }

# ========================
# ATS INGESTION STATS
# ========================

@router.get("/admin/ats-stats")
async def get_ats_stats(request: Request):
    """Get job ingestion statistics per ATS platform."""
    user = await get_current_user(request)
    
    # Get job counts per ATS from cache
    pipeline = [
        {"$unwind": "$jobs"},
        {"$group": {
            "_id": "$jobs.source",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    ats_counts = {}
    async for doc in db.job_cache.aggregate(pipeline):
        ats_counts[doc["_id"]] = doc["count"]
    
    # Also get from applications
    app_pipeline = [
        {"$group": {
            "_id": "$ats_type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    app_ats_counts = {}
    async for doc in db.applications.aggregate(app_pipeline):
        if doc["_id"]:
            app_ats_counts[doc["_id"]] = doc["count"]
    
    return {
        "jobs_by_ats": ats_counts,
        "applications_by_ats": app_ats_counts,
        "configured_companies": {
            "greenhouse": len(GREENHOUSE_COMPANIES),
            "lever": len(LEVER_COMPANIES),
            "smartrecruiters": len(SMARTRECRUITERS_COMPANIES),
            "pinpoint": len(PINPOINT_COMPANIES),
            "custom": len(CUSTOM_CAREER_COMPANIES),
        },
        "total_companies": len(GREENHOUSE_COMPANIES) + len(LEVER_COMPANIES) + len(SMARTRECRUITERS_COMPANIES) + len(PINPOINT_COMPANIES) + len(CUSTOM_CAREER_COMPANIES)
    }

# ========================
# HEALTH CHECK
# ========================

