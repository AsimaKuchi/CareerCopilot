"""
routes/profile_routes.py - User profile CRUD.

Endpoints (under /api):
  GET /profile -- Get current user's profile (creates default if missing)
  PUT /profile -- Update profile fields

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core import db, logger, get_current_user
from models import UserProfile, ProfileUpdate
from profile_schema import (
    migrate_profile_to_v2,
    normalize_skills,
    get_skill_names,
)
from encryption import encrypt_field, encrypt_sensitive_data, decrypt_sensitive_data
from admin_routes import log_event

router = APIRouter()


@router.get("/profile")
async def get_profile(request: Request):
    """Get user profile with decrypted sensitive data and structured schema."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        # Create default profile with v2 schema
        profile = {
            "user_id": user.user_id,
            "profile_version": 2,
            "resume_text": None,
            "resume_filename": None,
            "skills": [],
            "experience_years": 0,
            "job_titles": [],
            "preferred_locations": [],
            "salary_min": None,
            "salary_max": None,
            "job_type": [],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_profiles.insert_one(profile)
        profile.pop("_id", None)
    
    # Decrypt sensitive fields before returning
    profile = decrypt_sensitive_data(profile)
    
    # Migrate to v2 structured schema if needed
    if profile.get("profile_version") != 2:
        profile = migrate_profile_to_v2(profile)
        # Save migrated profile
        await db.user_profiles.update_one(
            {"user_id": user.user_id},
            {"$set": {"profile_version": 2, "structured": profile.get("structured", {})}}
        )
    
    # Also normalize skills for frontend compatibility
    raw_skills = profile.get("skills", [])
    normalized_skills = []
    for skill in raw_skills:
        if isinstance(skill, str):
            normalized_skills.append({"name": skill, "years": None})
        elif isinstance(skill, dict):
            normalized_skills.append({
                "name": skill.get("name", ""),
                "years": skill.get("years")
            })
    profile["skills"] = normalized_skills
    
    return profile

@router.put("/profile")
async def update_profile(request: Request, update: ProfileUpdate):
    """Update user profile with encryption and structured schema migration."""
    user = await get_current_user(request)
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["profile_version"] = 2
    
    # Encrypt sensitive fields before storing
    update_data = encrypt_sensitive_data(update_data)
    
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {"$set": update_data},
        upsert=True
    )
    
    await log_event("profile_update", user.email, f"Profile updated: {', '.join(update_data.keys())}", "info")
    
    # Fetch updated profile
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Decrypt before processing
    profile = decrypt_sensitive_data(profile)
    
    # Re-migrate to v2 to regenerate structured data with updated fields
    profile = migrate_profile_to_v2(profile)
    
    # Save the regenerated structured data
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {"$set": {"structured": profile.get("structured", {}), "migrated_at": profile.get("migrated_at")}}
    )
    
    # Normalize skills for frontend compatibility
    raw_skills = profile.get("skills", [])
    normalized_skills = []
    for skill in raw_skills:
        if isinstance(skill, str):
            normalized_skills.append({"name": skill, "years": None})
        elif isinstance(skill, dict):
            normalized_skills.append({
                "name": skill.get("name", ""),
                "years": skill.get("years")
            })
    profile["skills"] = normalized_skills
    
    return profile

