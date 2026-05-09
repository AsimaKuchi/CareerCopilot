"""
server.py - MyCareerCopilot FastAPI application entry point.

This module is intentionally thin. Responsibilities:
  * create the FastAPI app
  * mount the static-downloads directory
  * wire shared dependencies into helper modules (Stripe, Admin)
  * register every router from /app/backend/routes/*
  * register the CORS, security-headers and CSRF middleware
  * start the APScheduler-driven background ingestion + cleanup jobs

Domain logic lives in:
  - core.py                  -> shared infra (db, logger, helpers, auth deps)
  - models.py                -> Pydantic schemas
  - routes/*.py              -> per-feature routers
  - stripe_routes.py         -> Stripe subscription routes (existing)
  - admin_routes.py          -> Admin dashboard routes (existing)
  - ats_scrapers.py          -> SmartRecruiters / Pinpoint scrapers
  - profile_schema.py        -> profile migration helpers
  - location_utils.py        -> Canadian location utilities
  - encryption.py            -> encrypt/decrypt sensitive fields

Refactored from a 9446-line monolith on Feb 2026 (branch: refactor/backend-split).
The previous monolith is preserved as ``server_old.py`` for at least one week
as a rollback safety-net.
"""
import os
import asyncio

# Set Playwright browsers path before any playwright imports happen anywhere.
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Shared infrastructure
from core import (
    db,
    client,
    logger,
    STATIC_DOWNLOADS_DIR,
    get_current_user,
    get_admin_user,
)

# Existing standalone routers
from stripe_routes import stripe_router, init_stripe_routes
from admin_routes import admin_router, init_admin_routes

# Modular routers extracted from the old monolith
from routes.auth_routes import router as auth_router
from routes.profile_routes import router as profile_router
from routes.resume_routes import router as resume_router
from routes.job_routes import router as job_router
from routes.ai_routes import router as ai_router
from routes.comparison_routes import router as comparison_router
from routes.application_routes import router as application_router
from routes.extension_routes import router as extension_router
from routes.dashboard_routes import router as dashboard_router
from routes.misc_routes import router as misc_router
from routes.public_routes import router as public_router

# Helpers used by the scheduler
from routes.public_routes import ingest_all_jobs
from routes.job_routes import cleanup_expired_jobs


# ============================================================
# WIRE SHARED DEPENDENCIES INTO HELPER MODULES
# ============================================================
init_stripe_routes(db, get_current_user)
init_admin_routes(db, get_admin_user)


# ============================================================
# FASTAPI APP + STATIC FILES
# ============================================================
app = FastAPI(title="MyCareerCopilot API")

# Static downloads served via /api/static-downloads/* (Kubernetes ingress
# routes /api/* to the backend).
app.mount(
    "/api/static-downloads",
    StaticFiles(directory=STATIC_DOWNLOADS_DIR),
    name="static_downloads",
)


# ============================================================
# REGISTER ROUTERS UNDER /api PREFIX
# ============================================================
# All feature routers (ones that originally registered against ``api_router``)
# are mounted via a single APIRouter with the /api prefix so paths stay
# identical to the pre-refactor URLs.
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(resume_router)
api_router.include_router(job_router)
api_router.include_router(ai_router)
api_router.include_router(comparison_router)
api_router.include_router(application_router)
api_router.include_router(extension_router)
api_router.include_router(dashboard_router)
api_router.include_router(misc_router)
app.include_router(api_router)

# Public Jobs API: router has its own ``/public`` prefix; final paths
# resolve to /api/public/*.
app.include_router(public_router, prefix="/api")

# Stripe + Admin routers (already prefix-less internally).
app.include_router(stripe_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# ============================================================
# CUSTOM CORS MIDDLEWARE
# ============================================================
class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware that properly handles chrome-extension origins with credentials."""

    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin", "")

        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
        ]

        is_allowed = (
            origin.startswith("chrome-extension://")
            or origin in allowed_origins
            or "lovable.app" in origin
            or "lovableproject.com" in origin
            or "emergentagent.com" in origin
            or "preview.emergentagent.com" in origin
        )

        if is_allowed and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"

        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin, X-CSRF-Token"
        response.headers["Access-Control-Expose-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"

        return response


app.add_middleware(CustomCORSMiddleware)


# ============================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://auth.emergentagent.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https: wss:; "
        "frame-ancestors 'none'"
    )
    return response


# ============================================================
# CSRF PROTECTION MIDDLEWARE
# ============================================================
CSRF_EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/signup",
    "/api/auth/google",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/auth/verify-email",
    "/api/public/",
    "/api/downloads/",
    "/api/health",
    "/api/webhook/",
)


@app.middleware("http")
async def csrf_protection_middleware(request: Request, call_next):
    """Validate the X-CSRF-Token header for state-changing requests with a session.

    Hardened (Feb 2026): if a session_token cookie is present and the path is
    not in CSRF_EXEMPT_PREFIXES, the X-CSRF-Token header is REQUIRED and must
    match the session's stored csrf_token. Previously this middleware only
    validated when the header was provided, allowing a CSRF bypass by simply
    omitting the header.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        path = request.url.path
        if not any(path.startswith(prefix) for prefix in CSRF_EXEMPT_PREFIXES):
            session_token = request.cookies.get("session_token")
            if session_token:
                csrf_header = request.headers.get("x-csrf-token", "")
                if not csrf_header:
                    return Response(
                        content='{"detail":"CSRF token missing"}',
                        status_code=403,
                        media_type="application/json",
                    )
                session = await db.user_sessions.find_one(
                    {"session_token": session_token},
                    {"_id": 0, "csrf_token": 1},
                )
                if not session or session.get("csrf_token") != csrf_header:
                    return Response(
                        content='{"detail":"CSRF token invalid"}',
                        status_code=403,
                        media_type="application/json",
                    )
    return await call_next(request)


# ============================================================
# SCHEDULED JOB INGESTION (every 2 hours) + cleanup (daily)
# ============================================================
scheduler = AsyncIOScheduler()


async def scheduled_job_ingestion():
    """Background task to refresh jobs every 2 hours."""
    logger.info("Starting scheduled job ingestion...")
    try:
        result = await ingest_all_jobs()
        logger.info(f"Scheduled ingestion complete: {result.get('jobs_ingested', 0)} jobs")
    except Exception as e:
        logger.error(f"Scheduled ingestion failed: {e}")


async def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed; auto-install if missing."""
    import subprocess
    import sys

    browser_path = "/pw-browsers/chromium-1200"
    headless_shell_path = "/pw-browsers/chromium_headless_shell-1200"

    browsers_exist = os.path.exists(browser_path) or os.path.exists(headless_shell_path)
    if browsers_exist:
        logger.info("Playwright browsers already installed")
        return

    logger.info("Playwright browsers not found. Installing...")
    try:
        env = os.environ.copy()
        env['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'
        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            logger.info("Playwright browsers installed successfully")
        else:
            logger.error(f"Playwright browser installation failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Playwright browser installation timed out")
    except Exception as e:
        logger.error(f"Playwright browser installation error: {e}")


@app.on_event("startup")
async def start_scheduler():
    """Start the job scheduler on app startup."""
    await ensure_playwright_browsers()

    scheduler.add_job(
        scheduled_job_ingestion,
        trigger=IntervalTrigger(hours=2),
        id="job_ingestion",
        name="Refresh jobs from all sources",
        replace_existing=True,
    )

    scheduler.add_job(
        cleanup_expired_jobs,
        trigger=IntervalTrigger(hours=24),
        id="job_cleanup",
        name="Remove expired job listings",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Job scheduler started - ingestion every 2h, cleanup every 24h")

    # Run initial ingestion if database is empty
    job_count = await db.stored_jobs.count_documents({})
    if job_count == 0:
        logger.info("Database empty - running initial job ingestion...")
        asyncio.create_task(ingest_all_jobs())


@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown scheduler and database on app shutdown."""
    scheduler.shutdown()
    client.close()
    logger.info("Scheduler and database connection closed")
