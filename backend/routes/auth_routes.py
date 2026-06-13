"""
routes/auth_routes.py - Authentication routes.

Endpoints (under /api):
  POST /auth/session              -- Exchange Google OAuth session_id for session_token
  GET  /auth/me                   -- Current user info
  POST /auth/logout               -- Logout (revoke single session)
  GET  /auth/sessions             -- List active sessions for current user
  POST /auth/revoke-all-sessions  -- Logout from all devices
  POST /auth/signup               -- Email/password signup
  POST /auth/verify-email         -- Verify email via token
  POST /auth/resend-verification  -- Resend verification email
  POST /auth/login                -- Email/password login
  POST /auth/forgot-password      -- Request password reset email
  POST /auth/reset-password       -- Reset password using token

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Request, Response
import httpx
import resend

from core import (
    db,
    logger,
    FRONTEND_URL,
    SENDER_EMAIL,
    hash_password,
    verify_password,
    generate_token,
    validate_password_strength,
    rate_limiter,
    get_client_ip,
    RATE_LOGIN,
    RATE_SIGNUP,
    RATE_RESET,
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_MINUTES,
    get_current_user,
)
from models import (
    User,
    EmailSignupRequest,
    EmailLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
)
from admin_routes import log_event

router = APIRouter()


@router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token after Google OAuth."""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent auth API
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    
    auth_data = auth_response.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    session_token = auth_data.get("session_token")
    is_new_user = False
    
    # Check if user exists
    existing_user = await db.users.find_one(
        {"email": auth_data["email"]},
        {"_id": 0}
    )
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": auth_data["name"],
                "picture": auth_data.get("picture")
            }}
        )
    else:
        is_new_user = True
        # Create new user
        new_user = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
            "auth_type": "google",
            "email_verified": True,  # Google accounts are pre-verified
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
        
        # Create default profile
        default_profile = {
            "user_id": user_id,
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
        await db.user_profiles.insert_one(default_profile)
    
    # Create session
    csrf_token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "csrf_token": csrf_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
        "ip_address": request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown"),
        "user_agent": (request.headers.get("user-agent", "")[:200]),
    }
    
    # Keep existing sessions, clean expired
    await db.user_sessions.delete_many({
        "user_id": user_id,
        "expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookies
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    # Send welcome email for new Google OAuth users
    if is_new_user:
        first_name = auth_data.get("name", "there").split()[0] if auth_data.get("name") else "there"
        await send_welcome_email(auth_data.get("email"), first_name)
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user."""
    user = await get_current_user(request)
    data = user.model_dump()
    # Fetch csrf_token from session
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0, "csrf_token": 1})
        if session:
            data["csrf_token"] = session.get("csrf_token")
    return data

@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session."""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    response.delete_cookie(key="csrf_token", path="/")
    return {"message": "Logged out successfully"}


@router.get("/auth/sessions")
async def list_sessions(request: Request):
    """List all active sessions for the current user."""
    user = await get_current_user(request)
    current_token = request.cookies.get("session_token")
    
    sessions = await db.user_sessions.find(
        {"user_id": user.user_id},
        {"_id": 0, "csrf_token": 0}
    ).sort("last_active", -1).to_list(50)
    
    result = []
    for s in sessions:
        is_current = (s.get("session_token", "") == current_token)
        result.append({
            "created_at": s.get("created_at", ""),
            "last_active": s.get("last_active", s.get("created_at", "")),
            "ip_address": s.get("ip_address", "Unknown"),
            "user_agent": s.get("user_agent", "Unknown"),
            "is_current": is_current,
        })
    
    return {"sessions": result, "total": len(result)}


@router.post("/auth/revoke-all-sessions")
async def revoke_all_sessions(request: Request, response: Response):
    """Logout from all devices except the current session."""
    user = await get_current_user(request)
    current_token = request.cookies.get("session_token")
    
    # Delete all sessions except current
    if current_token:
        result = await db.user_sessions.delete_many({
            "user_id": user.user_id,
            "session_token": {"$ne": current_token}
        })
    else:
        result = await db.user_sessions.delete_many({"user_id": user.user_id})
    
    await log_event("revoke_all_sessions", user.email, f"Revoked {result.deleted_count} sessions", "info")
    
    return {"message": f"Logged out from {result.deleted_count} other device(s)", "revoked": result.deleted_count}

# ========================
# EMAIL AUTHENTICATION
# ========================
async def send_verification_email(email: str, token: str, name: str):
    """Send email verification link."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #6366f1; margin: 0;">MyCareerCoPilot</h1>
        </div>
        <h2 style="color: #1f2937;">Welcome, {name}!</h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
            Thanks for signing up for MyCareerCoPilot. Please verify your email address by clicking the button below:
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="background-color: #6366f1; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">
                Verify Email Address
            </a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">
            Or copy and paste this link into your browser:<br>
            <a href="{verify_url}" style="color: #6366f1;">{verify_url}</a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            This link will expire in 24 hours.
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">
            If you didn't create an account, you can safely ignore this email.
        </p>
    </div>
    """
    
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Verify your MyCareerCoPilot account",
        "html": html_content
    }
    
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.warning(f"Failed to send verification email to {email}: {e}")
        return False

async def send_password_reset_email(email: str, token: str, name: str):
    """Send password reset link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #6366f1; margin: 0;">MyCareerCoPilot</h1>
        </div>
        <h2 style="color: #1f2937;">Reset Your Password</h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
            Hi {name}, we received a request to reset your password. Click the button below to create a new password:
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #6366f1; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_url}" style="color: #6366f1;">{reset_url}</a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            This link will expire in 1 hour.
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">
            If you didn't request a password reset, you can safely ignore this email.
        </p>
    </div>
    """
    
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Reset your MyCareerCoPilot password",
        "html": html_content
    }
    
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.warning(f"Failed to send password reset email to {email}: {e}")
        return False

async def send_welcome_email(email: str, first_name: str):
    """Send welcome email to new users after successful signup/verification."""
    dashboard_url = f"{FRONTEND_URL}/dashboard"
    support_url = f"{FRONTEND_URL}/support"
    
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #6366f1; margin: 0; font-size: 28px;">MyCareerCoPilot</h1>
        </div>
        
        <h2 style="color: #1f2937; margin-bottom: 10px;">Hi {first_name},</h2>
        
        <p style="color: #1f2937; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
            Welcome to MyCareerCoPilot! 🎉
        </p>
        
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
            Thank you for signing up. You've just taken the first step toward a smarter, more efficient job search that prioritizes quality over quantity.
        </p>
        
        <div style="background-color: #f8fafc; border-radius: 12px; padding: 24px; margin: 24px 0;">
            <h3 style="color: #1f2937; margin-top: 0; margin-bottom: 16px; font-size: 18px;">Here's what to do next:</h3>
            
            <div style="margin-bottom: 16px;">
                <p style="color: #4b5563; font-size: 15px; margin: 0; line-height: 1.6;">
                    <strong style="color: #6366f1;">1. Complete your profile</strong> - Add your skills, experience, and job preferences so we can find the best-fit roles for you
                </p>
            </div>
            
            <div style="margin-bottom: 16px;">
                <p style="color: #4b5563; font-size: 15px; margin: 0; line-height: 1.6;">
                    <strong style="color: #6366f1;">2. Upload your resume</strong> - Our AI will auto-fill your profile to save you time
                </p>
            </div>
            
            <div style="margin-bottom: 16px;">
                <p style="color: #4b5563; font-size: 15px; margin: 0; line-height: 1.6;">
                    <strong style="color: #6366f1;">3. Install the Chrome extension</strong> - Auto-fill applications in seconds on any job site
                </p>
            </div>
            
            <div>
                <p style="color: #4b5563; font-size: 15px; margin: 0; line-height: 1.6;">
                    <strong style="color: #6366f1;">4. Start your job search</strong> - Find roles that actually match your background
                </p>
            </div>
        </div>
        
        <div style="background-color: #eef2ff; border-radius: 12px; padding: 24px; margin: 24px 0;">
            <h3 style="color: #4338ca; margin-top: 0; margin-bottom: 16px; font-size: 18px;">Why you'll love MyCareerCoPilot:</h3>
            <ul style="color: #4b5563; font-size: 15px; line-height: 1.8; margin: 0; padding-left: 20px;">
                <li>Save 25+ minutes per application with smart auto-fill</li>
                <li>Apply to fewer jobs, get more interviews</li>
                <li>AI-powered cover letters and resume optimization</li>
                <li>Track all your applications in one place</li>
            </ul>
        </div>
        
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
            We're here to help you land your next great role - not just apply to hundreds of jobs.
        </p>
        
        <div style="text-align: center; margin: 32px 0;">
            <a href="{dashboard_url}" style="background-color: #6366f1; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">
                Get Started Now →
            </a>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
            Need help? Just reply to this email or visit our <a href="{support_url}" style="color: #6366f1; text-decoration: none;">Support page</a>.
        </p>
        
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin-top: 24px;">
            Best of luck on your job search!<br>
            <strong>The MyCareerCoPilot Team</strong>
        </p>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <p style="color: #9ca3af; font-size: 13px; text-align: center; font-style: italic;">
            💡 Pro tip: Complete your profile 100% to get the most accurate job matches!
        </p>
    </div>
    """
    
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Welcome to MyCareerCoPilot! 🚀",
        "html": html_content
    }
    
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {email}: {e}")
        return False

@router.post("/auth/signup")
async def email_signup(data: EmailSignupRequest, request: Request):
    """Sign up with email and password."""
    # --- Rate limit by IP ---
    ip = get_client_ip(request)
    if rate_limiter.is_limited(f"signup:{ip}", *RATE_SIGNUP):
        raise HTTPException(status_code=429, detail="Too many signup attempts. Please wait a minute and try again.")

    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": data.email.lower()})
    if existing_user:
        if existing_user.get("email_verified", False):
            raise HTTPException(status_code=400, detail="An account with this email already exists")
        else:
            # User exists but not verified - update and resend verification
            verification_token = generate_token()
            await db.users.update_one(
                {"email": data.email.lower()},
                {"$set": {
                    "name": data.name,
                    "password_hash": hash_password(data.password),
                    "verification_token": verification_token,
                    "verification_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
                }}
            )
            await send_verification_email(data.email.lower(), verification_token, data.name)
            return {"message": "Verification email sent. Please check your inbox."}
    
    # Create new user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    verification_token = generate_token()
    
    new_user = {
        "user_id": user_id,
        "email": data.email.lower(),
        "name": data.name,
        "password_hash": hash_password(data.password),
        "auth_type": "email",
        "email_verified": False,
        "verification_token": verification_token,
        "verification_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    # Create default profile
    default_profile = {
        "user_id": user_id,
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
    await db.user_profiles.insert_one(default_profile)
    
    # Send verification email
    email_sent = await send_verification_email(data.email.lower(), verification_token, data.name)
    
    await log_event("signup", data.email.lower(), "New account created", "info")
    
    if email_sent:
        return {"message": "Account created! Please check your email to verify your account."}
    else:
        # Email failed but account was created - provide verification link directly for testing
        return {
            "message": "Account created! Email service is in test mode. Use the verification link below.",
            "verification_url": f"{FRONTEND_URL}/verify-email?token={verification_token}"
        }

@router.post("/auth/verify-email")
async def verify_email(request: Request):
    """Verify email address with token."""
    body = await request.json()
    token = body.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Verification token required")
    
    user = await db.users.find_one({"verification_token": token})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    
    # Check if token expired
    expires_at = datetime.fromisoformat(user.get("verification_expires", "2000-01-01T00:00:00"))
    if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Verification link has expired. Please request a new one.")
    
    # Mark email as verified
    await db.users.update_one(
        {"verification_token": token},
        {
            "$set": {"email_verified": True},
            "$unset": {"verification_token": "", "verification_expires": ""}
        }
    )
    
    # Send welcome email after successful verification
    first_name = user.get("name", "there").split()[0] if user.get("name") else "there"
    await send_welcome_email(user.get("email"), first_name)
    
    return {"message": "Email verified successfully! You can now log in."}

@router.post("/auth/resend-verification")
async def resend_verification(data: ResendVerificationRequest):
    """Resend verification email."""
    user = await db.users.find_one({"email": data.email.lower()})
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If an account exists with this email, a verification link will be sent."}
    
    if user.get("email_verified", False):
        raise HTTPException(status_code=400, detail="Email is already verified")
    
    # Generate new token
    verification_token = generate_token()
    await db.users.update_one(
        {"email": data.email.lower()},
        {"$set": {
            "verification_token": verification_token,
            "verification_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }}
    )
    
    await send_verification_email(data.email.lower(), verification_token, user.get("name", "there"))
    
    return {"message": "If an account exists with this email, a verification link will be sent."}

@router.post("/auth/login")
async def email_login(data: EmailLoginRequest, request: Request, response: Response):
    """Login with email and password."""
    # --- Rate limit by IP ---
    ip = get_client_ip(request)
    if rate_limiter.is_limited(f"login:{ip}", *RATE_LOGIN):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait a minute and try again.")

    user = await db.users.find_one({"email": data.email.lower()})

    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # --- Account lockout check ---
    lockout_until = user.get("locked_until")
    if lockout_until:
        lock_dt = datetime.fromisoformat(lockout_until)
        if lock_dt.tzinfo is None:
            lock_dt = lock_dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < lock_dt:
            remaining = int((lock_dt - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=423,
                detail=f"Account locked due to too many failed attempts. Try again in {remaining} minute{'s' if remaining != 1 else ''}."
            )
        # Lockout expired — reset
        await db.users.update_one(
            {"email": data.email.lower()},
            {"$set": {"failed_login_attempts": 0}, "$unset": {"locked_until": ""}}
        )

    if not verify_password(data.password, user["password_hash"]):
        # --- Increment failed attempts ---
        failed = user.get("failed_login_attempts", 0) + 1
        update = {"$set": {"failed_login_attempts": failed}}
        
        # Log failed attempt for admin security monitoring
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        await log_event("failed_login", data.email.lower(), f"Failed attempt #{failed}", "warning")
        await db.audit_logs.update_one(
            {"type": "failed_login", "user_email": data.email.lower(), "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(seconds=1)}},
            {"$set": {"ip_address": client_ip}},
        )
        
        if failed >= MAX_FAILED_ATTEMPTS:
            lock_until = (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
            update["$set"]["locked_until"] = lock_until
            await db.users.update_one({"email": data.email.lower()}, update)
            raise HTTPException(
                status_code=423,
                detail=f"Account locked after {MAX_FAILED_ATTEMPTS} failed attempts. Try again in {LOCKOUT_MINUTES} minutes."
            )
        await db.users.update_one({"email": data.email.lower()}, update)
        remaining = MAX_FAILED_ATTEMPTS - failed
        raise HTTPException(status_code=401, detail=f"Invalid email or password. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")

    if not user.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Please verify your email before logging in")

    # --- Successful login: reset failed attempts ---
    await db.users.update_one(
        {"email": data.email.lower()},
        {"$set": {"failed_login_attempts": 0, "last_login": datetime.now(timezone.utc).isoformat()}, "$unset": {"locked_until": ""}}
    )
    
    await log_event("login_success", data.email.lower(), "User logged in", "info")
    
    # Create session
    session_token = generate_token()
    csrf_token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user["user_id"],
        "session_token": session_token,
        "csrf_token": csrf_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
        "ip_address": request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown"),
        "user_agent": (request.headers.get("user-agent", "")[:200]),
    }
    
    # Keep existing sessions (allow multi-device), just clean expired ones
    await db.user_sessions.delete_many({
        "user_id": user["user_id"],
        "expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookies
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # JS must read this
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name"),
        "picture": user.get("picture"),
        "role": user.get("role", "user"),
        "csrf_token": csrf_token
    }

@router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, request: Request):
    """Request password reset email."""
    # --- Rate limit by IP ---
    ip = get_client_ip(request)
    if rate_limiter.is_limited(f"reset:{ip}", *RATE_RESET):
        raise HTTPException(status_code=429, detail="Too many reset requests. Please wait a few minutes and try again.")

    user = await db.users.find_one({"email": data.email.lower()})
    
    # Always return same message to prevent email enumeration
    if not user or user.get("auth_type") != "email":
        return {"message": "If an account exists with this email, a password reset link will be sent."}
    
    # Generate reset token
    reset_token = generate_token()
    await db.users.update_one(
        {"email": data.email.lower()},
        {"$set": {
            "reset_token": reset_token,
            "reset_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }}
    )
    
    await send_password_reset_email(data.email.lower(), reset_token, user.get("name", "there"))
    
    await log_event("forgot_password", data.email.lower(), "Password reset requested", "info")
    
    return {"message": "If an account exists with this email, a password reset link will be sent."}

@router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest, request: Request):
    """Reset password with token."""
    # --- Rate limit by IP ---
    ip = get_client_ip(request)
    if rate_limiter.is_limited(f"reset:{ip}", *RATE_RESET):
        raise HTTPException(status_code=429, detail="Too many reset attempts. Please wait a few minutes and try again.")

    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    user = await db.users.find_one({"reset_token": data.token})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Check if token expired
    expires_at = datetime.fromisoformat(user.get("reset_expires", "2000-01-01T00:00:00"))
    if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    
    # Update password and clear reset token
    await db.users.update_one(
        {"reset_token": data.token},
        {
            "$set": {"password_hash": hash_password(data.password)},
            "$unset": {"reset_token": "", "reset_expires": ""}
        }
    )
    
    # Clear all sessions for this user (force re-login)
    await db.user_sessions.delete_many({"user_id": user["user_id"]})
    
    await log_event("password_reset", user.get("email", ""), "Password reset via email link", "info")
    
    return {"message": "Password reset successfully! You can now log in with your new password."}

