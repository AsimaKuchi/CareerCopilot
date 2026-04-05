"""
Admin dashboard routes for MyCareerCopilot.
Handles overview stats, user management, security monitoring, audit logs, and support tools.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import csv
import io
import os
import logging

logger = logging.getLogger("server")

admin_router = APIRouter(prefix="/admin", tags=["admin"])

db = None
get_admin_user = None

def init_admin_routes(database, admin_user_func):
    global db, get_admin_user
    db = database
    get_admin_user = admin_user_func


async def log_admin_action(admin_email: str, action: str, target: str = "", details: str = ""):
    """Log an admin action to the audit_logs collection."""
    await db.audit_logs.insert_one({
        "type": "admin_action",
        "admin_email": admin_email,
        "action": action,
        "target": target,
        "details": details,
        "timestamp": datetime.now(timezone.utc),
    })


async def log_event(event_type: str, user_email: str = "", details: str = "", severity: str = "info"):
    """Log a system/user event to audit_logs."""
    await db.audit_logs.insert_one({
        "type": event_type,
        "user_email": user_email,
        "details": details,
        "severity": severity,
        "timestamp": datetime.now(timezone.utc),
    })


# ========================
# OVERVIEW
# ========================

@admin_router.get("/overview")
async def admin_overview(request: Request):
    """Real-time snapshot of platform health."""
    admin = await get_admin_user(request)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    last_hour = now - timedelta(hours=1)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # Total users
    total_users = await db.users.count_documents({})

    # Users by plan
    pro_users = await db.users.count_documents({"subscription_status": "active"})
    free_users = total_users - pro_users

    # Active users (last 24h) - users with sessions
    active_24h = await db.user_sessions.count_documents({
        "last_active": {"$gte": last_24h.isoformat()}
    })
    # Fallback: count by last_login
    if active_24h == 0:
        active_24h = await db.users.count_documents({
            "last_login": {"$gte": last_24h.isoformat()}
        })

    # Applications created today
    apps_today = await db.applications.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })

    # Failed login attempts (last 24h)
    failed_logins_24h = await db.audit_logs.count_documents({
        "type": "failed_login",
        "timestamp": {"$gte": last_24h}
    })

    # Locked accounts
    locked_accounts = await db.users.count_documents({
        "failed_login_attempts": {"$gte": 5}
    })

    # Recent signups
    signups_today = await db.users.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    signups_7d = await db.users.count_documents({
        "created_at": {"$gte": last_7d.isoformat()}
    })
    signups_30d = await db.users.count_documents({
        "created_at": {"$gte": last_30d.isoformat()}
    })

    # Total jobs indexed
    total_jobs = await db.stored_jobs.count_documents({})

    # MRR estimate (pro_users * $19.99)
    mrr = round(pro_users * 19.99, 2)

    # Usage stats for current month
    month_key = now.strftime("%Y-%m")
    usage_pipeline = [
        {"$match": {"month": month_key}},
        {"$group": {
            "_id": None,
            "total_resume_opts": {"$sum": "$resume_optimizations"},
            "total_cover_letters": {"$sum": "$cover_letters"},
            "total_interview_preps": {"$sum": "$interview_prep"},
            "total_career_paths": {"$sum": "$career_paths"},
            "total_job_apps": {"$sum": "$job_applications"},
            "total_extension_uses": {"$sum": "$extension_uses"},
        }}
    ]
    usage_agg = await db.usage_tracking.aggregate(usage_pipeline).to_list(1)
    usage_stats = usage_agg[0] if usage_agg else {}
    usage_stats.pop("_id", None)

    return {
        "total_users": total_users,
        "free_users": free_users,
        "pro_users": pro_users,
        "mrr": mrr,
        "active_users_24h": active_24h,
        "apps_today": apps_today,
        "failed_logins_24h": failed_logins_24h,
        "locked_accounts": locked_accounts,
        "signups_today": signups_today,
        "signups_7d": signups_7d,
        "signups_30d": signups_30d,
        "total_jobs_indexed": total_jobs,
        "usage_this_month": usage_stats,
    }


# ========================
# USER MANAGEMENT
# ========================

@admin_router.get("/users")
async def admin_list_users(
    request: Request,
    page: int = 1,
    limit: int = 20,
    search: str = "",
    plan: str = "",
    status: str = "",
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """List all users with search, filter, and pagination."""
    admin = await get_admin_user(request)

    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]
    if plan == "pro":
        query["subscription_status"] = "active"
    elif plan == "free":
        query["$or"] = query.get("$or", [])
        query.setdefault("subscription_status", {"$ne": "active"})
    if status == "banned":
        query["banned"] = True
    elif status == "locked":
        query["failed_login_attempts"] = {"$gte": 5}
    elif status == "active":
        query["banned"] = {"$ne": True}

    sort_dir = -1 if sort_order == "desc" else 1
    total = await db.users.count_documents(query)
    skip = (page - 1) * limit

    users = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0, "reset_token": 0, "verification_token": 0, "hashed_password": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)

    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
    }


@admin_router.get("/users/{user_id}")
async def admin_get_user_detail(user_id: str, request: Request):
    """Get detailed user information."""
    admin = await get_admin_user(request)

    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "password_hash": 0, "reset_token": 0, "verification_token": 0, "hashed_password": 0}
    )
    if not user:
        raise HTTPException(404, "User not found")

    # Get profile
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})

    # Get usage for current month
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    usage = await db.usage_tracking.find_one(
        {"user_id": user_id, "month": month_key},
        {"_id": 0}
    )

    # Get application count
    app_count = await db.applications.count_documents({"user_id": user_id})

    # Get saved jobs count
    saved_count = await db.user_saved_jobs.count_documents({"user_id": user_id})

    # Get recent audit logs for this user
    recent_logs = await db.audit_logs.find(
        {"$or": [{"user_email": user.get("email", "")}, {"target": user.get("email", "")}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)

    return {
        "user": user,
        "profile": profile,
        "usage": usage,
        "app_count": app_count,
        "saved_jobs_count": saved_count,
        "recent_activity": recent_logs,
    }


@admin_router.post("/users/{user_id}/ban")
async def admin_ban_user(user_id: str, request: Request):
    """Ban/suspend a user."""
    admin = await get_admin_user(request)
    body = await request.json()
    reason = body.get("reason", "")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1, "role": 1})
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("role") == "admin":
        raise HTTPException(400, "Cannot ban admin users")

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True, "banned_at": datetime.now(timezone.utc).isoformat(), "ban_reason": reason}},
    )

    # Delete their sessions
    await db.user_sessions.delete_many({"user_id": user_id})

    await log_admin_action(admin.email, "ban_user", user["email"], reason)
    return {"message": f"User {user['email']} has been banned"}


@admin_router.post("/users/{user_id}/unban")
async def admin_unban_user(user_id: str, request: Request):
    """Unban a user."""
    admin = await get_admin_user(request)

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
    if not user:
        raise HTTPException(404, "User not found")

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}, "$unset": {"ban_reason": "", "banned_at": ""}},
    )

    await log_admin_action(admin.email, "unban_user", user["email"])
    return {"message": f"User {user['email']} has been unbanned"}


@admin_router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, request: Request):
    """Force reset a user's password (generates a temp password)."""
    admin = await get_admin_user(request)
    import secrets
    from passlib.hash import bcrypt

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
    if not user:
        raise HTTPException(404, "User not found")

    temp_password = secrets.token_urlsafe(12)
    hashed = bcrypt.hash(temp_password)

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"hashed_password": hashed, "password_reset_required": True}},
    )

    await log_admin_action(admin.email, "reset_password", user["email"])
    return {"message": f"Password reset for {user['email']}", "temp_password": temp_password}


@admin_router.post("/users/{user_id}/subscription")
async def admin_override_subscription(user_id: str, request: Request):
    """Manually override a user's subscription status."""
    admin = await get_admin_user(request)
    body = await request.json()
    new_plan = body.get("plan")  # "free" or "pro"

    if new_plan not in ("free", "pro"):
        raise HTTPException(400, "Plan must be 'free' or 'pro'")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
    if not user:
        raise HTTPException(404, "User not found")

    if new_plan == "pro":
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "subscription_status": "active",
                "plan": "pro",
                "subscription_override": True,
                "subscription_override_by": admin.email,
                "subscription_override_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
    else:
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "subscription_status": "free",
                "plan": "free",
            }, "$unset": {"subscription_override": ""}},
        )

    await log_admin_action(admin.email, "subscription_override", user["email"], f"Set to {new_plan}")
    return {"message": f"Subscription set to {new_plan} for {user['email']}"}


@admin_router.get("/users/export/csv")
async def admin_export_users(request: Request):
    """Export all user data as CSV (GDPR compliance)."""
    admin = await get_admin_user(request)

    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0, "hashed_password": 0, "reset_token": 0, "verification_token": 0}
    ).to_list(None)

    output = io.StringIO()
    if not users:
        output.write("No users found")
    else:
        fields = ["user_id", "email", "name", "role", "subscription_status", "plan",
                   "email_verified", "created_at", "last_login", "banned", "failed_login_attempts"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for u in users:
            writer.writerow(u)

    output.seek(0)
    await log_admin_action(admin.email, "export_users", "", f"Exported {len(users)} users")

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=users_export_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"},
    )


@admin_router.post("/users/{user_id}/unlock")
async def admin_unlock_user_by_id(user_id: str, request: Request):
    """Unlock a locked user account."""
    admin = await get_admin_user(request)

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
    if not user:
        raise HTTPException(404, "User not found")

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"failed_login_attempts": 0}, "$unset": {"locked_until": "", "account_locked_until": ""}},
    )

    await log_admin_action(admin.email, "unlock_user", user["email"])
    return {"message": f"Account {user['email']} unlocked"}


# ========================
# SECURITY MONITORING
# ========================

@admin_router.get("/security/failed-logins")
async def admin_failed_logins(request: Request, page: int = 1, limit: int = 50):
    """Get recent failed login attempts."""
    admin = await get_admin_user(request)
    skip = (page - 1) * limit

    total = await db.audit_logs.count_documents({"type": "failed_login"})
    logs = await db.audit_logs.find(
        {"type": "failed_login"},
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)

    # Convert datetime objects to strings
    for log in logs:
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].isoformat()

    return {"logs": logs, "total": total, "page": page}


@admin_router.get("/security/lockouts")
async def admin_lockouts(request: Request):
    """Get currently locked accounts."""
    admin = await get_admin_user(request)

    locked = await db.users.find(
        {"failed_login_attempts": {"$gte": 5}},
        {"_id": 0, "user_id": 1, "email": 1, "name": 1, "failed_login_attempts": 1, "account_locked_until": 1}
    ).to_list(100)

    return {"locked_accounts": locked}


@admin_router.get("/security/summary")
async def admin_security_summary(request: Request):
    """Security summary for the dashboard."""
    admin = await get_admin_user(request)
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    failed_24h = await db.audit_logs.count_documents({"type": "failed_login", "timestamp": {"$gte": last_24h}})
    failed_7d = await db.audit_logs.count_documents({"type": "failed_login", "timestamp": {"$gte": last_7d}})
    locked_now = await db.users.count_documents({"failed_login_attempts": {"$gte": 5}})
    banned_total = await db.users.count_documents({"banned": True})

    # Top offending IPs (from audit logs)
    ip_pipeline = [
        {"$match": {"type": "failed_login", "timestamp": {"$gte": last_24h}}},
        {"$group": {"_id": "$ip_address", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_ips = await db.audit_logs.aggregate(ip_pipeline).to_list(10)

    return {
        "failed_logins_24h": failed_24h,
        "failed_logins_7d": failed_7d,
        "locked_accounts": locked_now,
        "banned_users": banned_total,
        "top_offending_ips": [{"ip": r["_id"], "count": r["count"]} for r in top_ips if r["_id"]],
    }


# ========================
# AUDIT LOGS
# ========================

@admin_router.get("/audit-logs")
async def admin_audit_logs(
    request: Request,
    page: int = 1,
    limit: int = 50,
    log_type: str = "",
    severity: str = "",
):
    """Get audit logs with filtering."""
    admin = await get_admin_user(request)
    skip = (page - 1) * limit

    query = {}
    if log_type:
        query["type"] = log_type
    if severity:
        query["severity"] = severity

    total = await db.audit_logs.count_documents(query)
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)

    # Serialize timestamps
    for log in logs:
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].isoformat()

    return {"logs": logs, "total": total, "page": page, "pages": max(1, (total + limit - 1) // limit)}


@admin_router.get("/audit-logs/types")
async def admin_audit_log_types(request: Request):
    """Get distinct audit log types for filtering."""
    admin = await get_admin_user(request)
    types = await db.audit_logs.distinct("type")
    return {"types": types}


# ========================
# SUPPORT TOOLS
# ========================

@admin_router.get("/support/search")
async def admin_support_search(request: Request, q: str = ""):
    """Search users by email or name for support purposes."""
    admin = await get_admin_user(request)

    if not q or len(q) < 2:
        return {"users": []}

    users = await db.users.find(
        {"$or": [
            {"email": {"$regex": q, "$options": "i"}},
            {"name": {"$regex": q, "$options": "i"}},
        ]},
        {"_id": 0, "user_id": 1, "email": 1, "name": 1, "role": 1, "subscription_status": 1,
         "created_at": 1, "last_login": 1, "banned": 1}
    ).limit(20).to_list(20)

    return {"users": users}


@admin_router.post("/support/send-notification")
async def admin_send_notification(request: Request):
    """Send a notification/message to a user (stored in DB)."""
    admin = await get_admin_user(request)
    body = await request.json()
    user_id = body.get("user_id")
    message = body.get("message")
    notif_type = body.get("type", "info")

    if not user_id or not message:
        raise HTTPException(400, "user_id and message are required")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email": 1})
    if not user:
        raise HTTPException(404, "User not found")

    await db.notifications.insert_one({
        "user_id": user_id,
        "message": message,
        "type": notif_type,
        "read": False,
        "sent_by": admin.email,
        "created_at": datetime.now(timezone.utc),
    })

    await log_admin_action(admin.email, "send_notification", user["email"], message[:100])
    return {"message": "Notification sent"}
