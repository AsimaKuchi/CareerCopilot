from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import base64
import io
import asyncio
import re
from bs4 import BeautifulSoup

# Set Playwright browsers path before importing
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import resend

# Document parsing imports
from docx import Document
from PyPDF2 import PdfReader

# Encryption for sensitive data
from encryption import encrypt_sensitive_data, decrypt_sensitive_data, encrypt_field

# Profile schema migration
from profile_schema import (
    migrate_profile_to_v2,
    get_autofill_data,
    get_normalized_value,
    normalize_skills,
    get_skill_names,
)

# ATS Scrapers for SmartRecruiters, Pinpoint, etc.
from ats_scrapers import (
    fetch_all_new_ats_jobs_flat,
    fetch_all_smartrecruiters_jobs,
    fetch_all_pinpoint_jobs,
    SMARTRECRUITERS_COMPANIES,
    PINPOINT_COMPANIES,
)

# Location parsing utilities
from location_utils import (
    parse_location,
    is_job_valid_for_canadian_search,
    get_remote_label_for_display,
    CANADIAN_CITIES,
    CANADIAN_PROVINCES,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'Fuzail.abukhari@gmail.com')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')

# VERIFIED Greenhouse company boards (tested and working - no 404s)
# These companies have active Greenhouse job boards as of Jan 2025
GREENHOUSE_COMPANIES = [
    # Verified Working - Tested Jan 2025
    "airbnb", "stripe", "figma", "dropbox", "discord", 
    "instacart", "coinbase", "affirm", "brex", "gusto", 
    "lattice", "carta", "gitlab", "datadog", "databricks",
    "anthropic", "postman", "launchdarkly", "mixpanel", "amplitude",
    "marqeta", "adyen", "asana", "intercom", "oscar",
    "faire", "headway", "coursera", "duolingo", "gemini",
    "zocdoc", "alchemy",
    # Canadian-focused & companies with strong Canadian presence - Added Feb 2026
    "hootsuite", "d2l", "ritual", "grammarly", "lyft",
    "elastic", "cloudflare", "okta", "zscaler", "twitch",
    "airtable", "webflow", "vercel", "fivetran", "pagerduty",
    "reddit", "pinterest", "toast", "robinhood", "sofi",
    "roblox", "chime", "opendoor", "nextdoor", "scopely",
    "tulip", "ecobee", "squarespace",
]

# VERIFIED Lever company boards (tested and working)
LEVER_COMPANIES = [
    # Verified Working
    "lever", "attentive", "medium",
    # Canadian-focused & companies with Canadian presence - Added Feb 2026
    "wealthsimple", "plaid", "spotify", "pointclickcare",
    "clearco", "koho", "nuvei",
]

# VERIFIED Ashby company boards - SKIP for now (requires Playwright)
ASHBY_COMPANIES = []

# Job cache settings
JOB_CACHE_TTL_MINUTES = 30  # Cache jobs for 30 minutes
PARALLEL_BATCH_SIZE = 20    # Fetch 20 companies in parallel

# Non-English words/patterns to filter out (common in French, Spanish, Portuguese, German job titles)
NON_ENGLISH_PATTERNS = [
    # French
    "analyste", "développeur", "ingénieur", "responsable", "directeur", "gestionnaire",
    "conseiller", "coordonnateur", "spécialiste", "technicien", "adjoint", "chargé",
    " de la ", " du ", " des ", " sur ", " aux ", " pour ", " et ", " ou ",
    "qualité", "données", "affaires", "services", "ressources", "humaines",
    # Spanish  
    "analista", "desarrollador", "ingeniero", "gerente", "director", "especialista",
    "coordinador", "técnico", "asistente", " de ", " del ", " los ", " las ", " para ",
    # Portuguese
    "portugais", "português", "portuguese", "analista", "desenvolvedor", "engenheiro",
    # German
    "entwickler", "ingenieur", "leiter", "berater", "spezialist", "projektleiter",
    " und ", " für ", " mit ",
    # Common non-English indicators in titles
    "(français)", "(french)", "(francais)", "(portugais)", "(portuguese)", "(español)", 
    "(spanish)", "(deutsch)", "(german)", "(italien)", "(italian)",
    "bilingue", "bilingual", "francophone"
]

def is_english_job(title: str) -> bool:
    """Check if a job title appears to be in English."""
    title_lower = title.lower()
    for pattern in NON_ENGLISH_PATTERNS:
        if pattern in title_lower:
            return False
    return True


# ========================
# QUERY SYNONYM EXPANSION
# ========================
# Maps common search phrases to expanded variants for broader matching
QUERY_SYNONYMS = {
    "business analyst": ["business analyst", "business systems analyst", "business intelligence analyst", "ba ", "business analysis", "business operations analyst"],
    "data analyst": ["data analyst", "data analytics", "analytics analyst", "bi analyst", "business intelligence analyst", "data analysis"],
    "software engineer": ["software engineer", "software developer", "swe", "backend engineer", "frontend engineer", "full stack engineer", "fullstack engineer"],
    "product manager": ["product manager", "product lead", "pm ", "product owner", "product management"],
    "project manager": ["project manager", "project lead", "pmo", "project management", "scrum master"],
    "data scientist": ["data scientist", "data science", "ml engineer", "machine learning engineer", "applied scientist"],
    "ux designer": ["ux designer", "ui designer", "product designer", "ux/ui", "ui/ux", "user experience"],
    "devops": ["devops", "site reliability", "sre", "platform engineer", "infrastructure engineer", "cloud engineer"],
    "qa": ["qa engineer", "quality assurance", "test engineer", "sdet", "qa analyst"],
    "marketing": ["marketing manager", "growth marketing", "digital marketing", "marketing analyst", "marketing coordinator"],
    "financial analyst": ["financial analyst", "finance analyst", "fp&a", "financial planning"],
    "hr": ["human resources", "hr manager", "hr business partner", "people operations", "talent acquisition", "recruiter"],
    "accountant": ["accountant", "accounting", "cpa", "bookkeeper", "accounts payable", "accounts receivable"],
    "consultant": ["consultant", "consulting", "advisory", "strategy consultant", "management consultant"],
    "operations": ["operations manager", "operations analyst", "ops manager", "business operations"],
}

def expand_query(query: str) -> list:
    """Expand a search query with synonyms for broader matching."""
    query_lower = query.lower().strip()
    expanded = [query_lower]
    for key, synonyms in QUERY_SYNONYMS.items():
        if key in query_lower or query_lower in key:
            expanded.extend(synonyms)
    return list(set(expanded))

# Static downloads directory - files served directly by FastAPI static mount
STATIC_DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "static_downloads")
os.makedirs(STATIC_DOWNLOADS_DIR, exist_ok=True)

# Create the main app
app = FastAPI()

# Mount static downloads under /api/static-downloads so it goes through the backend
# (Kubernetes ingress routes /api/* to backend)
from fastapi.staticfiles import StaticFiles
app.mount("/api/static-downloads", StaticFiles(directory=STATIC_DOWNLOADS_DIR), name="static_downloads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# SALARY PARSING HELPER
# ========================

def parse_salary_from_description(description: str) -> Optional[str]:
    """
    Parse salary information from job description text.
    Returns a formatted salary string or None if not found.
    Does NOT hallucinate values - only returns what's explicitly stated.
    """
    if not description:
        return None
    
    text = description.lower()
    
    # Common salary patterns
    patterns = [
        # $XX,XXX - $XX,XXX or $XXk - $XXk
        r'\$[\d,]+(?:k)?\s*[-–to]+\s*\$[\d,]+(?:k)?(?:\s*(?:per\s+)?(?:year|annual|yr|/yr|/year))?',
        # $XX,XXX/year or $XXk/year
        r'\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?\s*(?:per\s+)?(?:year|annual|annually|yr|/yr|/year)',
        # $XX - $XX per hour
        r'\$[\d,.]+\s*[-–to]+\s*\$[\d,.]+\s*(?:per\s+)?(?:hour|hr|/hr|/hour|hourly)',
        # Salary: $XX,XXX
        r'salary[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
        # Compensation: $XX,XXX
        r'compensation[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
        # XX,XXX - XX,XXX USD/CAD
        r'[\d,]+\s*[-–to]+\s*[\d,]+\s*(?:usd|cad|gbp|eur)(?:\s*(?:per\s+)?(?:year|annual))?',
        # Base salary: $XXX,XXX
        r'base\s+salary[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            salary_text = match.group(0).strip()
            # Clean up and format
            salary_text = salary_text.replace('salary:', '').replace('compensation:', '').replace('base salary:', '').strip()
            # Capitalize currency codes
            for code in ['usd', 'cad', 'gbp', 'eur']:
                salary_text = re.sub(code, code.upper(), salary_text, flags=re.IGNORECASE)
            return salary_text.strip()
    
    return None

def format_salary_range(min_salary: Optional[int], max_salary: Optional[int], description: str = "") -> str:
    """
    Format salary range from structured data or parse from description.
    Returns 'Salary not listed' if no salary information is available.
    """
    # First try structured salary fields
    if min_salary and max_salary:
        return f"${min_salary:,} - ${max_salary:,}/year"
    elif min_salary:
        return f"${min_salary:,}+/year"
    elif max_salary:
        return f"Up to ${max_salary:,}/year"
    
    # Try parsing from description
    parsed = parse_salary_from_description(description)
    if parsed:
        return parsed
    
    return "Salary not listed"

# NOTE: normalize_skills and get_skill_names are imported from profile_schema.py

# ========================
# PYDANTIC MODELS
# ========================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Skill(BaseModel):
    """Skill with optional years of experience."""
    name: str
    years: Optional[str] = None  # "<1", "1–2", "3–5", "5+"

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    resume_text: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_format: Optional[str] = None
    skills: List[Any] = []  # Can be List[str] or List[Skill] for backwards compatibility
    experience_years: int = 0
    job_titles: List[str] = []
    preferred_locations: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: List[str] = []  # full-time, part-time, contract, remote
    # New fields for quality-first matching
    work_authorization: Optional[str] = None  # canadian_citizen, permanent_resident, work_permit, require_sponsorship
    industries: List[str] = []  # max 3 industries
    open_to_any_industry: bool = False
    seniority_level: Optional[str] = None  # entry, junior, mid, senior, lead, manager, director, executive
    # Contact information for auto-fill
    email: Optional[str] = None  # User's preferred contact email
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    # Education
    highest_education: Optional[str] = None  # high_school, associate, bachelor, master, doctorate, other
    # Auto-application fields
    current_company: Optional[str] = None
    willing_to_relocate: Optional[str] = None  # yes, no, open_to_discussion
    notice_period: Optional[str] = None  # immediately, two_weeks, one_month, two_months, three_months_plus
    referral_source: Optional[str] = None  # Default answer for "How did you hear about us?"
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    # Address fields
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None  # State/Province
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    # Application intensity and tracking
    application_intensity: str = "balanced"  # conservative, balanced, ambitious
    daily_applications_count: int = 0
    last_application_date: Optional[str] = None  # ISO date string
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfileUpdate(BaseModel):
    skills: Optional[List[Any]] = None  # Can be List[str] or List[Skill dict]
    experience_years: Optional[int] = None
    job_titles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[List[str]] = None
    work_authorization: Optional[str] = None
    industries: Optional[List[str]] = None
    open_to_any_industry: Optional[bool] = None
    seniority_level: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    highest_education: Optional[str] = None
    # New auto-application fields
    current_company: Optional[str] = None
    willing_to_relocate: Optional[str] = None
    notice_period: Optional[str] = None
    referral_source: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    # Address fields
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    application_intensity: Optional[str] = None
    # Work arrangement
    preferred_work_arrangement: Optional[str] = None

class JobApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_id: str = Field(default_factory=lambda: f"app_{uuid.uuid4().hex[:12]}")
    user_id: str
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    job_description: Optional[str] = None
    salary_range: Optional[str] = None
    optimized_resume: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = "pending"  # pending, approved, applied, rejected
    match_score: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied_at: Optional[datetime] = None
    next_steps_progress: Optional[Dict[str, Any]] = None  # Track "What to do next" progress

class NextStepUpdate(BaseModel):
    """Update a single next step's completion status or data."""
    step_id: str  # follow_company, find_recruiter, send_message, prep_interview, track_outcome, follow_up
    completed: Optional[bool] = None
    outcome: Optional[str] = None  # For track_outcome step
    reminder_date: Optional[str] = None  # For follow_up step (ISO date string)

class NextStepContentRequest(BaseModel):
    """Request to generate AI content for a next step."""
    step_id: str  # send_message or prep_interview
    content_type: Optional[str] = None  # For send_message: "linkedin_message", "email", "connection_request"

class ApplyRequest(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    job_description: str
    apply_link: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    optimized_resume: Optional[str] = None
    cover_letter: Optional[str] = None

class GenerateCoverLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str

class OptimizeResumeRequest(BaseModel):
    job_description: str

class InterviewPrepRequest(BaseModel):
    job_title: str
    company: str
    job_description: str

class JobComparisonRequest(BaseModel):
    job_id: str
    job_title: str
    company: str
    job_description: str
    apply_link: Optional[str] = None

class JobComparison(BaseModel):
    model_config = ConfigDict(extra="ignore")
    comparison_id: str = Field(default_factory=lambda: f"cmp_{uuid.uuid4().hex[:12]}")
    user_id: str
    job_id: str
    job_title: str
    company: str
    comparison_json: Dict[str, Any]  # The full analysis result
    personal_notes: Optional[str] = None
    status: str = "complete"  # pending, complete, error
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupportRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    reason: str
    description: str

class JobSearchQuery(BaseModel):
    query: str
    location: Optional[str] = None
    page: int = 1
    num_pages: int = 1
    employment_types: Optional[str] = None  # FULLTIME, PARTTIME, CONTRACTOR, INTERN

# ========================
# PUBLIC JOBS API (Phase 1)
# For Lovable Frontend Integration
# ========================

public_router = APIRouter(prefix="/public", tags=["Public Jobs API"])

@public_router.get("/health")
async def public_health():
    """Health check endpoint."""
    job_count = await db.stored_jobs.count_documents({})
    
    # Get next scheduled run time
    next_run = None
    job = scheduler.get_job("job_ingestion")
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()
    
    return {
        "status": "healthy",
        "service": "JobMatch API",
        "version": "1.0.0",
        "jobs_in_database": job_count,
        "auto_refresh": {
            "enabled": True,
            "interval": "every 2 hours",
            "next_refresh": next_run
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@public_router.post("/support")
async def submit_support_request(request: SupportRequest):
    """Submit a support request - sends email to support team."""
    try:
        # Create HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">New Support Request</h1>
            </div>
            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <h2 style="color: #374151; margin-top: 0;">Contact Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280; width: 120px;"><strong>Name:</strong></td>
                        <td style="padding: 8px 0; color: #111827;">{request.first_name} {request.last_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Email:</strong></td>
                        <td style="padding: 8px 0; color: #111827;"><a href="mailto:{request.email}" style="color: #6366f1;">{request.email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Reason:</strong></td>
                        <td style="padding: 8px 0; color: #111827;">{request.reason}</td>
                    </tr>
                </table>
                
                <h2 style="color: #374151; margin-top: 24px;">Description</h2>
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <p style="color: #374151; margin: 0; white-space: pre-wrap; line-height: 1.6;">{request.description}</p>
                </div>
                
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                        Sent from JobMatch AI Support Form • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email via Resend
        params = {
            "from": SENDER_EMAIL,
            "to": [SUPPORT_EMAIL],
            "subject": f"[Support] {request.reason} - {request.first_name} {request.last_name}",
            "html": html_content,
            "reply_to": request.email
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        # Store in database for tracking
        support_doc = {
            "support_id": str(uuid.uuid4()),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "reason": request.reason,
            "description": request.description,
            "email_id": email_result.get("id") if email_result else None,
            "status": "sent",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.support_requests.insert_one(support_doc)
        
        logger.info(f"Support request submitted by {request.email}: {request.reason}")
        
        return {
            "success": True,
            "message": "Your support request has been submitted. We'll get back to you soon!"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit support request: {str(e)}")
        
        # Still store it even if email fails
        support_doc = {
            "support_id": str(uuid.uuid4()),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "reason": request.reason,
            "description": request.description,
            "email_id": None,
            "status": "email_failed",
            "error": str(e),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.support_requests.insert_one(support_doc)
        
        return {
            "success": True,
            "message": "Your request has been received. We'll get back to you soon!"
        }

@public_router.get("/jobs")
async def get_jobs(
    page: int = 1,
    limit: int = 20,
    query: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,  # greenhouse, lever, jsearch
    remote_only: bool = False,
    posted_after: Optional[str] = None,  # ISO date string
    sort_by: str = "posted_at",  # posted_at, company, title
    sort_order: str = "desc"  # asc, desc
):
    """
    Get paginated list of jobs with filtering.
    Returns UI-ready JSON.
    """
    # Build filter
    filter_query = {}
    
    if query:
        # Search in title and description
        filter_query["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"company": {"$regex": query, "$options": "i"}}
        ]
    
    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}
    
    if company:
        filter_query["company"] = {"$regex": company, "$options": "i"}
    
    if source:
        filter_query["source"] = source
    
    if remote_only:
        filter_query["is_remote"] = True
    
    if posted_after:
        try:
            posted_date = datetime.fromisoformat(posted_after.replace('Z', '+00:00'))
            filter_query["posted_at"] = {"$gte": posted_date}
        except:
            pass
    
    # Pagination
    skip = (page - 1) * limit
    limit = min(limit, 100)  # Max 100 per page
    
    # Sort
    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by if sort_by in ["posted_at", "company", "title"] else "posted_at"
    
    # Get total count
    total = await db.stored_jobs.count_documents(filter_query)
    
    # Get jobs
    cursor = db.stored_jobs.find(filter_query, {"_id": 0}).sort(sort_field, sort_direction).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    
    # Format for UI
    formatted_jobs = []
    for job in jobs:
        # Handle posted_at which might be string or datetime
        posted_at = job.get("posted_at")
        if posted_at:
            if hasattr(posted_at, 'isoformat'):
                posted_at = posted_at.isoformat()
            # else it's already a string
        
        formatted_jobs.append({
            "id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "description_preview": (job.get("description", "")[:300] + "...") if job.get("description") else None,
            "apply_url": job.get("apply_link"),
            "source": job.get("source"),
            "is_remote": job.get("is_remote", False),
            "posted_at": posted_at,
            "department": job.get("department"),
            "employment_type": job.get("employment_type")
        })
    
    return {
        "jobs": formatted_jobs,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "has_next": skip + limit < total,
            "has_prev": page > 1
        },
        "filters_applied": {
            "query": query,
            "location": location,
            "company": company,
            "source": source,
            "remote_only": remote_only
        }
    }

@public_router.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """
    Get full job details by ID.
    Returns complete job data including full description.
    """
    job = await db.stored_jobs.find_one({"job_id": job_id}, {"_id": 0})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Helper to safely format dates
    def format_date(d):
        if d is None:
            return None
        if hasattr(d, 'isoformat'):
            return d.isoformat()
        return str(d)
    
    return {
        "id": job.get("job_id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "description": job.get("description"),
        "apply_url": job.get("apply_link"),
        "source": job.get("source"),
        "source_url": job.get("source_url"),
        "is_remote": job.get("is_remote", False),
        "posted_at": format_date(job.get("posted_at")),
        "department": job.get("department"),
        "employment_type": job.get("employment_type"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "requirements": job.get("requirements", []),
        "benefits": job.get("benefits", []),
        "metadata": {
            "ingested_at": format_date(job.get("ingested_at")),
            "last_updated": format_date(job.get("last_updated"))
        }
    }

@public_router.post("/jobs/ingest")
async def trigger_job_ingestion(background: bool = True):
    """
    Trigger job ingestion from all sources.
    This fetches jobs from Greenhouse/Lever and stores them in the database.
    """
    if background:
        # Run in background
        asyncio.create_task(ingest_all_jobs())
        return {"status": "started", "message": "Job ingestion started in background"}
    else:
        # Run synchronously (may take a while)
        result = await ingest_all_jobs()
        return result

async def ingest_all_jobs():
    """Fetch jobs from all sources and store in database."""
    logger.info("Starting job ingestion...")
    total_ingested = 0
    errors = []
    
    # Ingest from Greenhouse
    for company in GREENHOUSE_COMPANIES:
        try:
            jobs = await fetch_greenhouse_company_jobs(company)
            for job in jobs:
                # Add metadata
                job["ingested_at"] = datetime.now(timezone.utc)
                job["last_updated"] = datetime.now(timezone.utc)
                job["is_remote"] = "remote" in job.get("location", "").lower()
                
                # Upsert job
                await db.stored_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": job},
                    upsert=True
                )
                total_ingested += 1
        except Exception as e:
            errors.append(f"Greenhouse/{company}: {str(e)}")
    
    # Ingest from Lever
    for company in LEVER_COMPANIES:
        try:
            jobs = await fetch_lever_company_jobs(company)
            for job in jobs:
                job["ingested_at"] = datetime.now(timezone.utc)
                job["last_updated"] = datetime.now(timezone.utc)
                job["is_remote"] = "remote" in job.get("location", "").lower()
                
                await db.stored_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": job},
                    upsert=True
                )
                total_ingested += 1
        except Exception as e:
            errors.append(f"Lever/{company}: {str(e)}")
    
    logger.info(f"Job ingestion complete: {total_ingested} jobs")
    
    return {
        "status": "complete",
        "jobs_ingested": total_ingested,
        "errors": errors if errors else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@public_router.get("/sources")
async def get_job_sources():
    """Get list of available job sources and their job counts."""
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    results = await db.stored_jobs.aggregate(pipeline).to_list(length=100)
    
    sources = [{"source": r["_id"], "job_count": r["count"]} for r in results]
    
    return {
        "sources": sources,
        "total_jobs": sum(s["job_count"] for s in sources)
    }

@public_router.get("/companies")
async def get_companies(limit: int = 50):
    """Get list of companies with job counts."""
    pipeline = [
        {"$group": {"_id": "$company", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    results = await db.stored_jobs.aggregate(pipeline).to_list(length=limit)
    
    return {
        "companies": [{"name": r["_id"], "job_count": r["count"]} for r in results]
    }

# ========================
# AUTH HELPERS
# ========================

async def get_current_user(request: Request) -> User:
    """Get current user from session token in cookies or Authorization header."""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

# ========================
# AUTH ROUTES
# ========================

@api_router.post("/auth/session")
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
        # Create new user
        new_user = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
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
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Remove old sessions for this user
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user."""
    user = await get_current_user(request)
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session."""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ========================
# PROFILE ROUTES
# ========================

@api_router.get("/profile")
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

@api_router.put("/profile")
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

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file while preserving structure and formatting."""
    try:
        doc = Document(io.BytesIO(content))
        lines = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Check for bullet points or list items
                if para.style and para.style.name:
                    style = para.style.name.lower()
                    if 'heading' in style or 'title' in style:
                        # Add spacing before headings
                        if lines:
                            lines.append('')
                        lines.append(text.upper())
                        lines.append('')
                    elif 'list' in style or 'bullet' in style:
                        lines.append(f"• {text}")
                    else:
                        lines.append(text)
                else:
                    # Check if paragraph has bullet formatting
                    if para._element.pPr is not None:
                        numPr = para._element.pPr.numPr
                        if numPr is not None:
                            lines.append(f"• {text}")
                        else:
                            lines.append(text)
                    else:
                        lines.append(text)
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    lines.append(row_text)
        
        return '\n'.join(lines)
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {str(e)}")
        return ""

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return ""

# ========================
# GREENHOUSE JOB SCRAPER
# ========================

async def fetch_greenhouse_company_jobs(company: str) -> List[Dict]:
    """Fetch all jobs from a company's Greenhouse board using their API."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Greenhouse has a public API for job listings
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                for job in data.get("jobs", []):
                    jobs.append({
                        "job_id": f"gh_{company}_{job.get('id')}",
                        "greenhouse_id": job.get("id"),
                        "title": job.get("title"),
                        "company": company.replace("-", " ").title(),
                        "company_slug": company,
                        "location": job.get("location", {}).get("name", ""),
                        "department": job.get("departments", [{}])[0].get("name", "") if job.get("departments") else "",
                        "employment_type": job.get("employment_type", "FULLTIME"),
                        "apply_link": job.get("absolute_url"),
                        "posted_at": job.get("updated_at"),
                        "source": "greenhouse"
                    })
            else:
                logger.debug(f"Greenhouse API returned {response.status_code} for {company}")
                
    except Exception as e:
        logger.error(f"Error fetching Greenhouse jobs for {company}: {str(e)}")
    
    return jobs

async def fetch_greenhouse_job_details(company: str, job_id: int) -> Optional[Dict]:
    """Fetch detailed job description from Greenhouse."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                # Parse HTML content to plain text
                content_html = data.get("content", "")
                if content_html:
                    soup = BeautifulSoup(content_html, 'html.parser')
                    description = soup.get_text(separator='\n', strip=True)
                else:
                    description = ""
                
                return {
                    "description": description,
                    "full_description": description,
                    "requirements": data.get("requirements", ""),
                    "departments": [d.get("name") for d in data.get("departments", [])],
                    "offices": [o.get("name") for o in data.get("offices", [])],
                    "metadata": data.get("metadata", [])
                }
    except Exception as e:
        logger.error(f"Error fetching Greenhouse job details: {str(e)}")
    
    return None

async def fetch_lever_company_jobs(company: str) -> List[Dict]:
    """Fetch job listings from a Lever company board."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Lever API endpoint
            api_url = f"https://api.lever.co/v0/postings/{company}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                for job in data:
                    jobs.append({
                        "job_id": f"lv_{company}_{job.get('id')}",
                        "lever_id": job.get("id"),
                        "title": job.get("text"),
                        "company": company.replace("-", " ").title(),
                        "company_slug": company,
                        "location": job.get("categories", {}).get("location", ""),
                        "department": job.get("categories", {}).get("team", ""),
                        "employment_type": job.get("categories", {}).get("commitment", "Full-time"),
                        "apply_link": job.get("hostedUrl") or job.get("applyUrl"),
                        "posted_at": job.get("createdAt"),
                        "source": "lever"
                    })
            else:
                logger.debug(f"Lever API returned {response.status_code} for {company}")
                
    except httpx.TimeoutException:
        logger.debug(f"Timeout fetching Lever jobs for {company}")
    except Exception as e:
        logger.debug(f"Error fetching Lever jobs for {company}: {type(e).__name__}")
    
    return jobs

async def fetch_ashby_company_jobs(company: str) -> List[Dict]:
    """Fetch job listings from an Ashby company board."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Ashby uses jobs.ashbyhq.com/{company}
            api_url = f"https://jobs.ashbyhq.com/{company}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                # Ashby embeds job data in the HTML page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all job postings (Ashby uses specific class names)
                job_elements = soup.find_all('a', class_='ashby-job-posting-brief-list__list-item')
                
                for job_elem in job_elements:
                    try:
                        title = job_elem.find('h3').get_text(strip=True) if job_elem.find('h3') else ""
                        location_elem = job_elem.find('div', class_='ashby-job-posting-brief-list__list-item-location')
                        location = location_elem.get_text(strip=True) if location_elem else ""
                        job_link = job_elem.get('href', '')
                        
                        if not job_link.startswith('http'):
                            job_link = f"https://jobs.ashbyhq.com{job_link}"
                        
                        # Extract job ID from URL
                        job_id = job_link.split('/')[-1] if job_link else ""
                        
                        jobs.append({
                            "job_id": f"ab_{company}_{job_id}",
                            "ashby_id": job_id,
                            "title": title,
                            "company": company.replace("-", " ").title(),
                            "company_slug": company,
                            "location": location,
                            "department": "",
                            "employment_type": "FULLTIME",
                            "apply_link": job_link,
                            "posted_at": "",
                            "source": "ashby"
                        })
                    except Exception as e:
                        logger.debug(f"Error parsing Ashby job element: {e}")
                        continue
            else:
                logger.debug(f"Ashby returned {response.status_code} for {company}")
                
    except Exception as e:
        logger.error(f"Error fetching Ashby jobs for {company}: {str(e)}")
    
    return jobs

# ========================
# PARALLEL BATCH FETCHING & CACHING
# ========================

async def fetch_all_jobs_parallel() -> List[Dict]:
    """Fetch jobs from all platforms in parallel batches for speed."""
    all_jobs = []
    
    # Prepare all fetch tasks for Greenhouse and Lever
    tasks = []
    for company in GREENHOUSE_COMPANIES:
        tasks.append(("greenhouse", company, fetch_greenhouse_company_jobs(company)))
    for company in LEVER_COMPANIES:
        tasks.append(("lever", company, fetch_lever_company_jobs(company)))
    # Skip Ashby for now - requires Playwright
    
    logger.info(f"Fetching from {len(tasks)} Greenhouse/Lever companies in parallel...")
    start_time = datetime.now(timezone.utc)
    
    # Process Greenhouse/Lever in batches for controlled parallelism
    batch_size = PARALLEL_BATCH_SIZE
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        batch_coros = [t[2] for t in batch]
        
        results = await asyncio.gather(*batch_coros, return_exceptions=True)
        
        for j, result in enumerate(results):
            platform, company, _ = batch[j]
            if isinstance(result, list) and result:
                all_jobs.extend(result)
                logger.debug(f"  {platform}/{company}: {len(result)} jobs")
            elif isinstance(result, Exception):
                logger.debug(f"  {platform}/{company}: error - {type(result).__name__}")
    
    # Fetch from new ATS platforms (SmartRecruiters, Pinpoint)
    try:
        logger.info("Fetching from SmartRecruiters and Pinpoint...")
        new_ats_jobs = await fetch_all_new_ats_jobs_flat()
        if new_ats_jobs:
            all_jobs.extend(new_ats_jobs)
            logger.info(f"Added {len(new_ats_jobs)} jobs from SmartRecruiters/Pinpoint")
    except Exception as e:
        logger.error(f"Error fetching from new ATS platforms: {e}")
    
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"Parallel fetch complete: {len(all_jobs)} jobs in {elapsed:.1f}s")
    
    return all_jobs

async def get_cached_jobs(user_id: str) -> Optional[Dict]:
    """Get cached jobs for a user if still valid."""
    cache = await db.job_cache.find_one({"user_id": user_id})
    if cache:
        cached_at = cache.get("cached_at")
        if cached_at:
            age_minutes = (datetime.now(timezone.utc) - cached_at).total_seconds() / 60
            if age_minutes < JOB_CACHE_TTL_MINUTES:
                return cache
    return None

async def save_jobs_to_cache(user_id: str, jobs: List[Dict], query: str, location: str):
    """Save fetched jobs to user's cache."""
    # Get existing job IDs to detect new jobs later
    existing_cache = await db.job_cache.find_one({"user_id": user_id})
    existing_job_ids = set()
    if existing_cache:
        existing_job_ids = set(j.get("job_id") for j in existing_cache.get("jobs", []))
    
    # Mark new jobs
    for job in jobs:
        job["is_new_for_user"] = job.get("job_id") not in existing_job_ids
    
    await db.job_cache.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "jobs": jobs,
                "query": query,
                "location": location,
                "cached_at": datetime.now(timezone.utc),
                "total_jobs": len(jobs)
            }
        },
        upsert=True
    )
    
    # Also save to user's saved jobs collection for dashboard
    await db.user_saved_jobs.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "jobs": jobs[:50],  # Keep top 50 for dashboard
                "last_search_query": query,
                "last_search_location": location,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    new_count = sum(1 for j in jobs if j.get("is_new_for_user"))
    logger.info(f"Saved {len(jobs)} jobs to cache for user {user_id} ({new_count} new)")

async def search_greenhouse_jobs(query: str = "", location: str = "", limit: int = 50) -> List[Dict]:
    """Search for jobs across multiple Greenhouse company boards."""
    all_jobs = []
    query_words = query.lower().split() if query else []
    location_lower = location.lower() if location else ""
    
    logger.info(f"Searching Greenhouse: query_words={query_words}, location={location_lower}")
    
    # Fetch jobs from multiple companies in parallel
    tasks = [fetch_greenhouse_company_jobs(company) for company in GREENHOUSE_COMPANIES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = 0
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
            success_count += 1
        elif isinstance(result, Exception):
            logger.debug(f"Greenhouse fetch error: {result}")
    
    logger.info(f"Greenhouse: fetched from {success_count} companies, total {len(all_jobs)} jobs")
    
    # Filter by query and location with synonym expansion
    expanded_phrases = expand_query(query) if query else []
    filtered_jobs = []
    for job in all_jobs:
        job_title = (job.get("title") or "").lower()
        job_company = (job.get("company") or "").lower()
        job_dept = (job.get("department") or "").lower()
        job_location = (job.get("location") or "").lower()
        search_text = f"{job_title} {job_company} {job_dept}"
        
        # Match query - any word must match title, company, or department + synonym expansion
        query_match = not query_words or any(
            word in job_title or word in job_company or word in job_dept
            for word in query_words
        ) or any(syn in job_title for syn in expanded_phrases)
        
        # Match location
        location_match = not location_lower or location_lower in job_location
        
        if query_match and location_match:
            filtered_jobs.append(job)
    
    # Sort by posted date (most recent first)
    filtered_jobs.sort(key=lambda x: x.get("posted_at", ""), reverse=True)
    
    return filtered_jobs[:limit]

async def enrich_greenhouse_job(job: Dict, profile: Optional[Dict]) -> Dict:
    """Enrich a Greenhouse job with full description and match scoring."""
    # Fetch full job details
    if job.get("greenhouse_id") and job.get("company_slug"):
        details = await fetch_greenhouse_job_details(job["company_slug"], job["greenhouse_id"])
        if details:
            job["description"] = details.get("description", "")[:500] + "..."
            job["full_description"] = details.get("description", "")
    
    # Calculate match score
    if profile:
        # Create a job dict compatible with evaluate_job_match
        job_for_match = {
            "job_title": job.get("title"),
            "employer_name": job.get("company"),
            "job_description": job.get("full_description", job.get("description", "")),
            "job_city": job.get("location", "").split(",")[0].strip() if job.get("location") else "",
            "job_state": job.get("location", "").split(",")[-1].strip() if "," in job.get("location", "") else "",
            "job_is_remote": "remote" in job.get("location", "").lower(),
            "job_min_salary": None,
            "job_max_salary": None
        }
        match_eval = evaluate_job_match(job_for_match, profile)
        job.update({
            "match_score": match_eval["score"],
            "match_recommendation": match_eval["recommendation"],
            "match_strengths": match_eval["strengths"],
            "match_gaps": match_eval["gaps"],
            "match_reasoning": match_eval["match_reasoning"],
            "skip_reason": match_eval["skip_reason"]
        })
    else:
        job.update({
            "match_score": 50,
            "match_recommendation": "review",
            "match_strengths": [],
            "match_gaps": ["Complete your profile for better matching"],
            "match_reasoning": "Profile incomplete",
            "skip_reason": None
        })
    
    return job

@api_router.post("/jobs/greenhouse/search")
async def search_greenhouse(request: Request):
    """Search for jobs from Greenhouse, Lever, and Ashby-powered career pages with streaming."""
    logger.info("=== GREENHOUSE SEARCH ENDPOINT CALLED ===")
    user = await get_current_user(request)
    logger.info(f"User authenticated: {user.user_id}")
    
    body = await request.json()
    query = body.get("query", "")
    location = body.get("location", "")
    is_fallback = body.get("fallback_search", False)
    
    logger.info(f"Multi-platform job search (streaming): query='{query}', location='{location}', fallback={is_fallback}")
    
    # Get user profile for matching and intensity filtering
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get application intensity setting (default: balanced)
    intensity = profile.get("application_intensity", "balanced") if profile else "balanced"
    
    # ALL PROFILE-BASED FILTERING DISABLED
    # We only filter by title/location search terms
    # Match scores are calculated for ranking but NOT used to filter
    # User decides which jobs to apply to based on match scores displayed
    min_match_score = 0
    
    logger.info(f"Search mode: Show ALL jobs matching query/location. Match scoring enabled for ranking (no filtering).")
    
    # Get applied job IDs to filter duplicates
    existing_applications = await db.applications.find(
        {"user_id": user.user_id},
        {"job_id": 1, "_id": 0}
    ).to_list(500)
    applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
    
    async def stream_multi_platform_jobs():
        """Generator function that streams jobs from all platforms using parallel fetching."""
        logger.info("=== STREAMING FUNCTION STARTED (PARALLEL MODE) ===")
        import json
        
        # Send immediate heartbeat so frontend knows we're alive
        yield f"data: {json.dumps({'heartbeat': True, 'message': 'Search started - fetching from quality sources...'})}\n\n"
        
        query_words = query.lower().split() if query else []
        location_lower = location.lower() if location else ""
        is_fallback_search = body.get("fallback_search", False)
        
        jobs_found = 0
        matched_jobs = []
        
        # PARALLEL FETCH: Get all jobs at once (much faster than sequential)
        total_companies = len(GREENHOUSE_COMPANIES) + len(LEVER_COMPANIES)
        yield f"data: {json.dumps({'progress': True, 'message': f'Scanning {total_companies} companies...', 'checked': 0, 'found': 0})}\n\n"
        
        # Fetch all jobs in parallel batches
        all_raw_jobs = await fetch_all_jobs_parallel()
        
        yield f"data: {json.dumps({'progress': True, 'message': f'Found {len(all_raw_jobs)} total jobs, filtering...', 'checked': total_companies, 'found': len(all_raw_jobs)})}\n\n"
        
        # Get existing job IDs from user's previous search (to mark new jobs)
        existing_cache = await db.job_cache.find_one({"user_id": user.user_id})
        existing_job_ids = set()
        if existing_cache:
            existing_job_ids = set(j.get("job_id") for j in existing_cache.get("jobs", []))
        
        # Filter and process jobs
        skipped_non_english = 0
        skipped_applied = 0
        skipped_query = 0
        skipped_location = 0
        expanded_phrases = expand_query(query) if query else []
        logger.info(f"Expanded query phrases: {expanded_phrases}")
        
        for job in all_raw_jobs:
            # Skip already applied jobs
            if job.get("job_id") in applied_job_ids:
                skipped_applied += 1
                continue
            
            # Skip non-English job postings
            if not is_english_job(job.get("title", "")):
                skipped_non_english += 1
                continue
            
            job_title = (job.get("title") or "").lower()
            job_company = (job.get("company") or "").lower()
            job_dept = (job.get("department") or "").lower()
            job_location = (job.get("location") or "").lower()
            search_text = f"{job_title} {job_company} {job_dept}"
            
            # Query match logic with synonym expansion
            query_match = True
            if query_words:
                if len(query_words) >= 2:
                    if is_fallback_search:
                        # FALLBACK MODE: Any keyword match
                        query_match = any(word in search_text for word in query_words)
                    else:
                        # STRICT MODE: Phrase matching + synonym expansion
                        query_phrase = query.lower()
                        query_match = (
                            query_phrase in job_title or
                            all(word in job_title for word in query_words) or
                            query_phrase in search_text or
                            sum(1 for word in query_words if word in search_text) >= 2 or
                            any(syn in job_title for syn in expanded_phrases)
                        )
                else:
                    # Single word - broad matching
                    query_match = any(word in search_text for word in query_words)
            
            if not query_match:
                skipped_query += 1
                continue
            
            # Location match logic using comprehensive location parsing
            location_match = True
            if location_lower:
                # Extract user's city and province from search
                user_city = None
                user_province = None
                for city, prov in CANADIAN_CITIES.items():
                    if city in location_lower:
                        user_city = city
                        user_province = prov
                        break
                if not user_province:
                    for prov_name, prov_code in CANADIAN_PROVINCES.items():
                        if len(prov_name) > 2 and prov_name in location_lower:
                            user_province = prov_code
                            break
                
                # Check if this is a Canadian search
                is_canada_search = user_city or user_province or "canada" in location_lower
                
                if is_canada_search:
                    # Parse the job location
                    parsed = parse_location(job.get("location", ""))
                    
                    # Check if valid for Canadian search
                    is_valid, reason = is_job_valid_for_canadian_search(
                        parsed,
                        user_city=user_city,
                        user_province=user_province
                    )
                    
                    location_match = is_valid
                    
                    if is_valid:
                        # Add parsed location info to job
                        job["parsed_location"] = parsed
                        job["remote_label"] = get_remote_label_for_display(parsed)
                        job["location_filter_reason"] = reason
                else:
                    # Non-Canadian search - use simple keyword matching
                    location_words = location_lower.replace(",", " ").split()
                    location_keywords = [w for w in location_words if w not in ["area", "greater", "the", "of", "in"]]
                    location_match = any(keyword in job_location for keyword in location_keywords) if location_keywords else True
            
            if not location_match:
                skipped_location += 1
                continue
            
            # Mark if this is a NEW job for the user
            job["is_new_for_user"] = job.get("job_id") not in existing_job_ids
            
            # Calculate match score
            if profile:
                job_for_match = {
                    "job_title": job.get("title"),
                    "employer_name": job.get("company"),
                    "job_description": job.get("title", "") + " " + job.get("department", ""),
                    "job_city": job.get("location", "").split(",")[0].strip() if job.get("location") else "",
                    "job_state": job.get("location", "").split(",")[-1].strip() if "," in job.get("location", "") else "",
                    "job_is_remote": "remote" in job.get("location", "").lower(),
                    "job_min_salary": None,
                    "job_max_salary": None
                }
                match_eval = evaluate_job_match(job_for_match, profile)
                job.update({
                    "match_score": match_eval["score"],
                    "match_recommendation": match_eval["recommendation"],
                    "match_strengths": match_eval["strengths"],
                    "match_gaps": match_eval["gaps"],
                    "match_reasoning": match_eval["match_reasoning"],
                    "skip_reason": match_eval["skip_reason"]
                })
            else:
                job.update({
                    "match_score": 50,
                    "match_recommendation": "review",
                    "match_strengths": [],
                    "match_gaps": ["Complete your profile for better matching"],
                    "match_reasoning": "Profile incomplete",
                    "skip_reason": None
                })
            
            # Add description
            job["description"] = f"{job.get('title', '')} position at {job.get('company', '')} in {job.get('location', 'Unknown location')}"
            job["full_description"] = ""
            
            # Mark as new if posted in last 24 hours
            job_posted_date = job.get("posted_at")
            is_new = False
            if job_posted_date:
                try:
                    posted_dt = datetime.fromisoformat(job_posted_date.replace('Z', '+00:00'))
                    hours_ago = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
                    is_new = hours_ago <= 24
                except:
                    is_new = False
            job["is_new"] = is_new
            
            matched_jobs.append(job)
            jobs_found += 1
            
            # Limit to 100 jobs
            if jobs_found >= 100:
                break
        
        logger.info(f"Search filter stats: total={len(all_raw_jobs)}, skipped_non_english={skipped_non_english}, skipped_applied={skipped_applied}, skipped_query={skipped_query}, skipped_location={skipped_location}, matched={jobs_found}")
        
        # Sort jobs: new jobs (is_new_for_user) first, then by posted date
        matched_jobs.sort(key=lambda x: (
            not x.get("is_new_for_user", False),  # New jobs first (False sorts before True, so we negate)
            not x.get("is_new", False),            # Recently posted second
            x.get("posted_at", "") or ""           # Then by date
        ), reverse=False)
        
        # Re-sort the first group by posted_at descending
        matched_jobs.sort(key=lambda x: (
            0 if x.get("is_new_for_user", False) else 1,  # New for user first
            x.get("posted_at", "") or ""
        ), reverse=True)
        
        # Now stream the sorted jobs
        for job in matched_jobs:
            yield f"data: {json.dumps(job)}\n\n"
        
        # Save jobs to cache for dashboard
        if matched_jobs:
            await save_jobs_to_cache(user.user_id, matched_jobs, query, location)
        
        # Send completion message
        completion_data = {'done': True, 'total': jobs_found}
        
        # Count new jobs
        new_jobs_count = sum(1 for j in matched_jobs if j.get("is_new_for_user"))
        completion_data['new_jobs_count'] = new_jobs_count
        
        # If 0 results for a multi-word query, suggest fallback
        if jobs_found == 0 and len(query_words) >= 2 and not is_fallback_search:
            completion_data['suggest_fallback'] = True
            completion_data['fallback_message'] = f"No exact '{query}' jobs found in {location or 'your area'}. Try showing related roles?"
            completion_data['original_query'] = query
        
        yield f"data: {json.dumps(completion_data)}\n\n"
    
    return StreamingResponse(
        stream_multi_platform_jobs(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@api_router.get("/jobs/saved")
async def get_saved_jobs(request: Request):
    """Get user's saved jobs from their last search (for dashboard display)."""
    user = await get_current_user(request)
    
    saved = await db.user_saved_jobs.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not saved:
        return {
            "jobs": [],
            "last_search_query": None,
            "last_search_location": None,
            "updated_at": None,
            "total": 0
        }
    
    # Sort jobs with new ones first
    jobs = saved.get("jobs", [])
    jobs.sort(key=lambda x: (
        0 if x.get("is_new_for_user", False) else 1,
        x.get("posted_at", "") or ""
    ), reverse=True)
    
    return {
        "jobs": jobs,
        "last_search_query": saved.get("last_search_query"),
        "last_search_location": saved.get("last_search_location"),
        "updated_at": saved.get("updated_at").isoformat() if saved.get("updated_at") else None,
        "total": len(jobs)
    }

@api_router.get("/jobs/greenhouse/companies")
async def get_greenhouse_companies(request: Request):
    """Get list of known Greenhouse company boards."""
    await get_current_user(request)
    return {"companies": GREENHOUSE_COMPANIES}

@api_router.post("/jobs/greenhouse/add-company")
async def add_greenhouse_company(request: Request):
    """Add a new company to the Greenhouse search list."""
    await get_current_user(request)
    body = await request.json()
    company = body.get("company", "").lower().strip()
    
    if not company:
        raise HTTPException(status_code=400, detail="Company name required")
    
    # Validate that the company has a Greenhouse board
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            response = await client.get(api_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"No Greenhouse board found for '{company}'")
            
            data = response.json()
            job_count = len(data.get("jobs", []))
            
            if company not in GREENHOUSE_COMPANIES:
                GREENHOUSE_COMPANIES.append(company)
            
            return {
                "message": f"Added {company} with {job_count} jobs",
                "company": company,
                "job_count": job_count
            }
        except httpx.RequestError:
            raise HTTPException(status_code=400, detail=f"Could not verify Greenhouse board for '{company}'")

@api_router.post("/profile/resume")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    """Upload and parse resume from DOCX, PDF, or TXT files."""
    try:
        user = await get_current_user(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Auth error in resume upload: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    try:
        content = await file.read()
        
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        filename = file.filename.lower() if file.filename else ""
        resume_text = ""
        resume_format = "text"
        
        # Parse based on file type
        if filename.endswith('.docx'):
            resume_text = extract_text_from_docx(content)
            resume_format = "docx"
            if not resume_text:
                raise HTTPException(status_code=400, detail="Could not extract text from DOCX file")
        elif filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(content)
            resume_format = "pdf"
            if not resume_text:
                raise HTTPException(status_code=400, detail="Could not extract text from PDF file")
        elif filename.endswith('.doc'):
            # .doc files are not directly supported, store as base64
            resume_text = "[Legacy .doc format - please convert to .docx for full text extraction]"
            resume_format = "doc"
        else:
            # Try to decode as text
            try:
                resume_text = content.decode('utf-8')
                resume_format = "text"
            except UnicodeDecodeError:
                resume_text = base64.b64encode(content).decode('utf-8')
                resume_format = "binary"
        
        # Store the raw content as base64 for potential future use
        raw_content_b64 = base64.b64encode(content).decode('utf-8')
        
        await db.user_profiles.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "resume_text": encrypt_field(resume_text),
                "resume_raw": encrypt_field(raw_content_b64),
                "resume_filename": file.filename,
                "resume_format": resume_format,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        logger.info(f"Resume uploaded for user {user.user_id}: {file.filename} (format: {resume_format}, encrypted: yes)")
        return {
            "message": "Resume uploaded and encrypted successfully", 
            "filename": file.filename,
            "format": resume_format,
            "text_extracted": len(resume_text) > 0,
            "encrypted": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")

@api_router.post("/profile/resume/reparse")
async def reparse_resume(request: Request):
    """Re-extract text from stored resume raw content."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found")
    
    # Check for raw content in resume_raw or base64 in resume_text
    raw_content = None
    
    if profile.get("resume_raw"):
        # Normal case: raw content stored separately
        try:
            raw_content = base64.b64decode(profile["resume_raw"])
        except Exception as e:
            logger.error(f"Failed to decode resume_raw: {e}")
    
    if not raw_content and profile.get("resume_text"):
        # Check if resume_text contains base64 data (starts with PK signature for DOCX/ZIP)
        resume_text = profile.get("resume_text", "")
        if resume_text.startswith("UEsDB"):  # Base64 of "PK" (ZIP/DOCX signature)
            try:
                raw_content = base64.b64decode(resume_text)
                logger.info("Decoded base64 from resume_text field")
            except Exception as e:
                logger.error(f"Failed to decode resume_text as base64: {e}")
    
    if not raw_content:
        raise HTTPException(status_code=400, detail="No resume raw content found to reparse")
    
    try:
        filename = profile.get("resume_filename", "").lower()
        resume_text = ""
        resume_format = ""
        
        # Try to extract based on filename extension
        if filename.endswith('.docx'):
            resume_text = extract_text_from_docx(raw_content)
            resume_format = "docx"
        elif filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(raw_content)
            resume_format = "pdf"
        else:
            # Try DOCX first (most common), then PDF, then text
            resume_text = extract_text_from_docx(raw_content)
            if resume_text:
                resume_format = "docx"
            else:
                resume_text = extract_text_from_pdf(raw_content)
                if resume_text:
                    resume_format = "pdf"
                else:
                    try:
                        resume_text = raw_content.decode('utf-8')
                        resume_format = "text"
                    except UnicodeDecodeError:
                        pass
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume. Please re-upload.")
        
        # Update the profile with extracted text and store raw content properly
        raw_b64 = base64.b64encode(raw_content).decode('utf-8')
        
        await db.user_profiles.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "resume_text": resume_text,
                "resume_raw": raw_b64,
                "resume_format": resume_format,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Resume reparsed for user {user.user_id}: {len(resume_text)} chars extracted")
        return {
            "message": "Resume text re-extracted successfully",
            "text_length": len(resume_text),
            "format": resume_format
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume reparse error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reparse resume: {str(e)}")

@api_router.get("/profile/resume/download/original")
async def download_original_resume(request: Request):
    """
    Download the user's original resume file (preserves original format and formatting).
    Returns the file in its original format (PDF, DOCX, etc.)
    """
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "resume_raw": 1, "resume_filename": 1, "resume_format": 1}
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    resume_raw = profile.get("resume_raw")
    if not resume_raw:
        raise HTTPException(status_code=404, detail="No original resume file stored")
    
    # Decrypt if encrypted
    if isinstance(resume_raw, str) and resume_raw.startswith("gAAAAA"):
        resume_raw = decrypt_field(resume_raw)
    
    try:
        # Decode base64 to bytes
        file_content = base64.b64decode(resume_raw)
    except Exception as e:
        logger.error(f"Failed to decode resume_raw: {e}")
        raise HTTPException(status_code=500, detail="Failed to decode resume file")
    
    # Determine content type
    resume_format = profile.get("resume_format", "").lower()
    filename = profile.get("resume_filename", "resume")
    
    if resume_format == "pdf" or filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif resume_format == "docx" or filename.endswith(".docx"):
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif resume_format == "doc" or filename.endswith(".doc"):
        content_type = "application/msword"
    else:
        content_type = "application/octet-stream"
    
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

# ========================
# JOB SEARCH ROUTES
# ========================

@api_router.post("/jobs/search")
async def search_jobs(request: Request):
    """Search for jobs using JSearch API - includes LinkedIn, Indeed, Glassdoor, etc."""
    user = await get_current_user(request)
    
    body = await request.json()
    query = body.get("query", "")
    location = body.get("location", "")
    linkedin_only = body.get("linkedin_only", False)
    
    # Get user profile to determine country preference
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Determine country code from user's location preference or search location
    country_code = None
    location_lower = location.lower() if location else ""
    
    # Map common location terms to country codes
    canada_keywords = ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "edmonton", "ontario", "bc", "quebec", "alberta"]
    us_keywords = ["usa", "united states", "new york", "california", "texas", "florida", "seattle", "san francisco", "los angeles", "chicago"]
    uk_keywords = ["uk", "united kingdom", "london", "manchester", "birmingham", "england", "scotland"]
    
    if any(kw in location_lower for kw in canada_keywords):
        country_code = "CA"
    elif any(kw in location_lower for kw in us_keywords):
        country_code = "US"
    elif any(kw in location_lower for kw in uk_keywords):
        country_code = "GB"
    elif profile:
        # Fallback to user's profile location preference
        preferred_locations = profile.get("preferred_locations", [])
        for loc in preferred_locations:
            loc_lower = loc.lower()
            if any(kw in loc_lower for kw in canada_keywords):
                country_code = "CA"
                break
            elif any(kw in loc_lower for kw in us_keywords):
                country_code = "US"
                break
            elif any(kw in loc_lower for kw in uk_keywords):
                country_code = "GB"
                break
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": f"{query} {location}".strip(),
                "num_pages": "3" if country_code else ("2" if linkedin_only else "1"),  # Fetch more to compensate for country filtering
                "page": "1"
            }
            
            # Add country filter if we determined a country
            if country_code:
                params["country"] = country_code
                logger.info(f"JSearch filtering by country: {country_code}")
            
            response = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"JSearch API error: {response.status_code}")
                return {"jobs": [], "total": 0}
            
            data = response.json()
            jobs = data.get("data", [])
            
            # Filter out Bebee jobs (poor quality spam)
            jobs = [job for job in jobs if "bebee.com" not in job.get("job_apply_link", "").lower()]
            
            # Extract user's city and province for location filtering
            user_city = None
            user_province = None
            if location_lower:
                # Parse the search location to get city/province
                for city, prov in CANADIAN_CITIES.items():
                    if city in location_lower:
                        user_city = city
                        user_province = prov
                        break
                if not user_province:
                    for prov_name, prov_code in CANADIAN_PROVINCES.items():
                        if len(prov_name) > 2 and prov_name in location_lower:
                            user_province = prov_code
                            break
            
            # Filter jobs using comprehensive location parsing
            if country_code == "CA":
                filtered_jobs = []
                
                for job in jobs:
                    job_location = job.get("job_city", "") or ""
                    if job.get("job_state"):
                        job_location += f", {job.get('job_state')}"
                    if job.get("job_country"):
                        job_location += f", {job.get('job_country')}"
                    
                    # Also check the job employment type for remote indicators
                    is_remote = job.get("job_is_remote", False)
                    if is_remote:
                        job_location = f"Remote - {job_location}" if job_location else "Remote"
                    
                    # Parse the location
                    parsed = parse_location(
                        job_location,
                        job_country=job.get("job_country", ""),
                        job_state=job.get("job_state", ""),
                        job_city=job.get("job_city", "")
                    )
                    
                    # Check if valid for Canadian search
                    is_valid, reason = is_job_valid_for_canadian_search(
                        parsed, 
                        user_city=user_city,
                        user_province=user_province
                    )
                    
                    if is_valid:
                        # Add parsed location info to job
                        job["parsed_location"] = parsed
                        job["remote_label"] = get_remote_label_for_display(parsed)
                        job["location_filter_reason"] = reason
                        filtered_jobs.append(job)
                    else:
                        logger.debug(f"Filtered out job: {job.get('job_title')} - {reason}")
                
                logger.info(f"Location filter: {len(jobs)} -> {len(filtered_jobs)} jobs for {user_city or user_province or 'Canada'}")
                jobs = filtered_jobs
            
            # Filter for LinkedIn only if requested
            if linkedin_only:
                jobs = [job for job in jobs if "linkedin.com" in job.get("job_apply_link", "").lower()]
                logger.info(f"Filtered to {len(jobs)} LinkedIn jobs")
            else:
                logger.info(f"Filtered to {len(jobs)} jobs")
            
            # Get applied job IDs to filter duplicates
            existing_applications = await db.applications.find(
                {"user_id": user.user_id},
                {"job_id": 1, "_id": 0}
            ).to_list(500)
            applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
            
            # Filter out already applied jobs (KEEP LinkedIn this time)
            jobs = [job for job in jobs if job.get("job_id") not in applied_job_ids]
            
            # Enrich jobs with match evaluation
            enriched_jobs = []
            for job in jobs[:30]:
                if profile:
                    match_eval = evaluate_job_match(job, profile)
                    job.update({
                        "match_score": match_eval["score"],
                        "match_recommendation": match_eval["recommendation"],
                        "match_strengths": match_eval["strengths"],
                        "match_gaps": match_eval["gaps"],
                        "match_reasoning": match_eval["match_reasoning"],
                        "skip_reason": match_eval["skip_reason"]
                    })
                else:
                    job.update({
                        "match_score": 50,
                        "match_recommendation": "review",
                        "match_strengths": [],
                        "match_gaps": ["Complete your profile for better matching"],
                        "match_reasoning": "Profile incomplete",
                        "skip_reason": None
                    })
                
                # Transform to match our format
                job_posted_date = job.get("job_posted_at_datetime_utc")
                is_new = False
                if job_posted_date:
                    try:
                        from datetime import datetime, timezone
                        posted_dt = datetime.fromisoformat(job_posted_date.replace('Z', '+00:00'))
                        hours_ago = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
                        is_new = hours_ago <= 24  # New if posted in last 24 hours
                    except:
                        is_new = False
                
                enriched_jobs.append({
                    "job_id": job.get("job_id"),
                    "title": job.get("job_title"),
                    "company": job.get("employer_name"),
                    "location": f"{job.get('job_city', '')}, {job.get('job_state', '')}".strip(", "),
                    "employment_type": job.get("job_employment_type"),
                    "description": job.get("job_description", "")[:500] + "..." if job.get("job_description") else "",
                    "apply_link": job.get("job_apply_link"),
                    "posted_at": job_posted_date,
                    "is_new": is_new,
                    "source": "aggregator",
                    "is_linkedin": "linkedin.com" in job.get("job_apply_link", "").lower(),
                    "requires_login": "linkedin.com" in job.get("job_apply_link", "").lower(),
                    "match_score": job.get("match_score"),
                    "match_recommendation": job.get("match_recommendation"),
                    "match_strengths": job.get("match_strengths"),
                    "match_gaps": job.get("match_gaps"),
                    "match_reasoning": job.get("match_reasoning"),
                    "skip_reason": job.get("skip_reason")
                })
            
            # Sort by match score
            enriched_jobs.sort(key=lambda x: (0 if x.get("match_recommendation") == "skip" else 1, x.get("match_score", 0)), reverse=True)
            
            return {
                "jobs": enriched_jobs,
                "total": len(enriched_jobs)
            }
    except Exception as e:
        logger.error(f"JSearch error: {str(e)}")
        return {"jobs": [], "total": 0}

def evaluate_job_match(job: Dict, profile: Optional[Dict]) -> Dict:
    """
    Evaluate job match to help user decide whether to apply.
    Returns match score, decision summary, strengths, risks, confidence, and recommendation.
    Focus: Guide decision-making with honesty and clarity, not hype.
    """
    if not profile:
        return {
            "score": 50,
            "recommendation": "review",
            "confidence": "low",
            "risk": "high",
            "decision_summary": "Complete your profile for personalized match analysis",
            "strengths": [],
            "gaps": ["Complete your profile and upload resume for accurate matching"],
            "match_reasoning": "Profile incomplete - unable to provide detailed analysis",
            "skip_reason": None,
            "auto_apply_blocked": True,
            "auto_apply_reason": "Insufficient profile data"
        }
    
    # Extract job details
    job_title = (job.get("job_title") or "").lower()
    job_desc = (job.get("job_description") or "").lower()
    job_title_display = job.get("job_title") or "this role"
    company_name = job.get("employer_name") or "this company"
    job_city = job.get("job_city") or ""
    job_state = job.get("job_state") or ""
    job_location = (job_city + " " + job_state).lower().strip()
    is_remote = job.get("job_is_remote", False)
    
    # Extract profile details
    resume_text = (profile.get("resume_text") or "").lower()
    has_resume = len(resume_text) > 100
    target_roles = [r.lower() for r in profile.get("job_titles", [])]
    profile_skills = get_skill_names(profile.get("skills", []))  # Use helper for backwards compatibility
    user_years = profile.get("experience_years", 0)
    user_seniority = profile.get("seniority_level", "").lower()
    
    # Initialize scoring
    score = 0
    strengths = []
    risks = []
    gaps = []
    auto_apply_blocked = False
    auto_apply_reason = None
    
    # ============================================================================
    # CATEGORY 1: CORE FIT (60 points) - Should I apply?
    # ============================================================================
    
    # 1.1 ROLE ALIGNMENT (20 points) - Title synonym mapping
    role_score = 0
    role_matched = False
    
    # Define title synonyms and related roles
    title_synonyms = {
        "business analyst": ["systems analyst", "data analyst", "business systems analyst", "process analyst", 
                            "functional analyst", "requirements analyst", "workday analyst", "analyst"],
        "data analyst": ["business intelligence analyst", "analytics analyst", "reporting analyst", 
                        "business analyst", "data specialist"],
        "software engineer": ["software developer", "engineer", "developer", "programmer", "sde"],
        "product manager": ["product owner", "pm", "product lead", "product specialist"],
        "project manager": ["program manager", "project lead", "delivery manager", "scrum master"],
        "accountant": ["accounting analyst", "financial analyst", "accounting specialist"],
        "marketing": ["marketing specialist", "marketing coordinator", "digital marketing", "marketing analyst"]
    }
    
    # Check target roles against job title
    for target_role in target_roles:
        # Direct match
        if target_role in job_title or any(word in job_title for word in target_role.split()):
            role_score = 20
            role_matched = True
            strengths.append(f"Strong role alignment: Your target role '{target_role.title()}' directly matches this position")
            break
        
        # Synonym match
        for category, synonyms in title_synonyms.items():
            if target_role in synonyms or category == target_role:
                if any(syn in job_title for syn in synonyms):
                    role_score = 18
                    role_matched = True
                    strengths.append(f"Related role match: This position aligns with your '{target_role.title()}' career path")
                    break
        
        if role_matched:
            break
    
    if not role_matched and target_roles:
        role_score = 5  # Minimal points for no match
        risks.append("Role title doesn't align with your target positions - may require explanation in cover letter")
    
    score += role_score
    
    # 2. Skills Match (max +20 points) - Enhanced with resume analysis
    skills = profile.get("skills", [])
    matched_skills = []
    
    # 1.2 SKILL OVERLAP (20 points) - Required vs Preferred skills
    skill_score = 0
    matched_skills = []
    resume_skills = []
    
    # Common technical and business skills to check
    skill_library = [
        "python", "javascript", "java", "sql", "excel", "tableau", "power bi",
        "aws", "azure", "docker", "kubernetes", "react", "node", "angular",
        "machine learning", "data analysis", "project management", "agile",
        "salesforce", "sap", "oracle", "mongodb", "postgresql", "git",
        "financial modeling", "budgeting", "forecasting", "reporting",
        "leadership", "stakeholder management", "workday", "peoplesoft"
    ]
    
    # Check profile skills
    for skill in profile_skills:
        if skill in job_desc or skill in job_title:
            matched_skills.append(skill)
    
    # Check resume for additional skills
    if has_resume:
        for skill in skill_library:
            if skill in job_desc and skill in resume_text:
                if skill not in matched_skills:
                    resume_skills.append(skill)
    
    all_skills = matched_skills + resume_skills
    
    if all_skills:
        # Weight: more skills = higher score, cap at 20
        skill_ratio = min(len(all_skills) / 5, 1.0)  # 5+ skills = full points
        skill_score = int(skill_ratio * 20)
        
        if len(all_skills) >= 3:
            strengths.append(f"Strong skill match: {', '.join(all_skills[:4])} align with job requirements")
        elif len(all_skills) >= 1:
            strengths.append(f"Key skills match: {', '.join(all_skills[:2])} mentioned in requirements")
    else:
        skill_score = 3  # Minimal points
        if profile_skills or has_resume:
            risks.append("Limited skill overlap detected - may need to highlight transferable skills")
    
    score += skill_score
    
    # 1.3 EXPERIENCE SCOPE (20 points) - Seniority based on scope, not just years
    exp_score = 0
    seniority_gap = 0
    
    # Detect job seniority from title
    job_seniority_level = 2  # Default: mid
    job_seniority_name = "mid"
    
    if any(word in job_title for word in ["ceo", "cto", "cfo", "vp", "chief"]):
        job_seniority_level = 6
        job_seniority_name = "executive"
    elif any(word in job_title for word in ["director", "head of"]):
        job_seniority_level = 5
        job_seniority_name = "director"
    elif any(word in job_title for word in ["senior", "sr.", "lead", "principal", "staff"]):
        job_seniority_level = 3
        job_seniority_name = "senior"
    elif any(word in job_title for word in ["junior", "jr.", "entry", "associate", "graduate", "intern"]):
        job_seniority_level = 1
        job_seniority_name = "junior"
    elif any(word in job_title for word in ["manager"]):
        job_seniority_level = 4
        job_seniority_name = "manager"
    
    # Determine user seniority
    seniority_map = {"entry": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4, "manager": 4, "director": 5, "executive": 6}
    user_seniority_level = seniority_map.get(user_seniority, None)
    
    # Infer from years if not set
    if user_seniority_level is None:
        if user_years <= 2:
            user_seniority_level = 1
            user_seniority = "junior"
        elif user_years <= 5:
            user_seniority_level = 2
            user_seniority = "mid"
        elif user_years <= 8:
            user_seniority_level = 3
            user_seniority = "senior"
        else:
            user_seniority_level = 4
            user_seniority = "lead"
    
    seniority_gap = job_seniority_level - user_seniority_level
    
    # Scoring based on seniority alignment
    if seniority_gap == 0:
        exp_score = 20
        strengths.append(f"Experience aligns well: Your {user_seniority}-level background matches this {job_seniority_name} position")
    elif seniority_gap == 1:
        exp_score = 15
        risks.append(f"One level stretch: This {job_seniority_name} role is one level above your {user_seniority} position - achievable with strong application")
    elif seniority_gap == -1:
        exp_score = 18
        strengths.append(f"Solid fit: Your {user_seniority}-level experience exceeds this {job_seniority_name} position")
    elif seniority_gap >= 2:
        exp_score = 5
        risks.append(f"Significant stretch: This {job_seniority_name} role is {seniority_gap} levels above your current {user_seniority} level - high risk")
        auto_apply_blocked = True
        auto_apply_reason = "Seniority gap exceeds one level"
    elif seniority_gap <= -2:
        exp_score = 10
        risks.append(f"Overqualified: This {job_seniority_name} role may be below your {user_seniority}-level experience")
    
    # Resume evidence boost
    if has_resume and user_years > 0:
        leadership_keywords = ["led", "managed", "directed", "owned", "coordinated", "supervised"]
        if any(kw in resume_text for kw in leadership_keywords):
            exp_score = min(exp_score + 2, 20)
    
    score += exp_score

    
    # ============================================================================
    # CATEGORY 2: CONSTRAINTS & PRACTICALITY (25 points) - Can I apply?
    # ============================================================================
    
    # 2.1 LOCATION / REMOTE FIT (10 points)
    location_score = 0
    preferred_locations = [loc.lower() for loc in profile.get("preferred_locations", [])]
    
    if is_remote:
        location_score = 10
        strengths.append("Remote position offers location flexibility")
    elif preferred_locations and any(loc in job_location for loc in preferred_locations):
        location_score = 10
        strengths.append(f"Location matches your preferences")
    elif preferred_locations:
        location_score = 3
        gaps.append("Location may not match your preferences - consider if relocation is feasible")
    else:
        location_score = 7  # No preference set, give partial credit
    
    score += location_score
    
    # 2.2 INDUSTRY ALIGNMENT (5 points)
    industry_score = 0
    industries = [ind.lower() for ind in profile.get("industries", [])]
    open_to_any = profile.get("open_to_any_industry", False)
    
    if open_to_any:
        industry_score = 5
    elif industries:
        # Simplified industry check
        industry_matched = False
        for ind in industries:
            if ind in company_name.lower() or ind in job_desc:
                industry_score = 5
                industry_matched = True
                break
        
        if not industry_matched:
            industry_score = 2
            gaps.append("Industry alignment unclear - may require additional research on company")
    else:
        industry_score = 4  # No preference, neutral
    
    score += industry_score
    
    # 2.3 SALARY ALIGNMENT (5 points) - Don't penalize heavily if missing
    salary_score = 4  # Default: assume okay if not specified
    job_min_salary = job.get("job_min_salary")
    user_min_salary = profile.get("salary_min")
    
    if job_min_salary and user_min_salary:
        if job_min_salary >= user_min_salary:
            salary_score = 5
            strengths.append(f"Salary (${job_min_salary:,}+) meets your requirements")
        else:
            salary_score = 1
            risks.append("Salary may be below your minimum - negotiate or clarify compensation")
    
    score += salary_score
    
    # 2.4 WORK AUTHORIZATION / ELIGIBILITY (5 points) - CRITICAL
    auth_score = 5  # Default: assume eligible
    work_auth = profile.get("work_authorization", "")
    
    if work_auth == "require_sponsorship":
        blockers = ["no sponsorship", "must be authorized", "no visa", "pr only"]
        if any(blocker in job_desc.lower() for blocker in blockers):
            auth_score = 0
            auto_apply_blocked = True
            auto_apply_reason = "Work authorization requirement not met"
            risks.append("CRITICAL: Role does not offer sponsorship - not eligible to apply")
    
    score += auth_score
    
    # ============================================================================
    # CATEGORY 3: CONFIDENCE & RISK ADJUSTERS (15 points) - How risky is this?
    # ============================================================================
    
    # 3.1 RESUME EVIDENCE STRENGTH (5 points)
    resume_score = 0
    if has_resume:
        # Check for substantive content
        if len(resume_text) > 500:
            resume_score = 5
        elif len(resume_text) > 200:
            resume_score = 3
        else:
            resume_score = 1
            auto_apply_blocked = True
            auto_apply_reason = "Weak resume evidence"
    else:
        resume_score = 0
        gaps.append("Upload resume for stronger application and better match analysis")
        auto_apply_blocked = True
        auto_apply_reason = "No resume uploaded"
    
    score += resume_score
    
    # 3.2 ATS COMPATIBILITY (5 points)
    ats_score = 5  # Bonus for Greenhouse/Lever/Ashby
    source = job.get("source", "")
    if source in ["greenhouse", "lever", "ashby"]:
        ats_score = 5  # Full points - these are friendly ATS
    elif source == "aggregator":
        ats_score = 3  # Neutral for other sources
    
    score += ats_score
    
    # 3.3 SENIORITY STRETCH INDICATOR (5 points)
    stretch_score = 0
    if seniority_gap == 0:
        stretch_score = 5
    elif abs(seniority_gap) == 1:
        stretch_score = 3
    else:
        stretch_score = 1
    
    score += stretch_score
    
    # Contextual bonuses (capped at +5 total)
    bonus = 0
    if has_resume and company_name.lower() in resume_text:
        bonus += 2
        strengths.append(f"Previous exposure to {company_name} strengthens your application")
    
    score = min(score + bonus, 92)  # Cap at 92, never show above 92%
    
    # ============================================================================
    # DETERMINE MATCH LABEL, CONFIDENCE, RISK
    # ============================================================================
    
    if score >= 85:
        recommendation = "strong_match"
        match_label = "Strong Match"
    elif score >= 70:
        recommendation = "good_match"
        match_label = "Good Match"
    elif score > 65:
        recommendation = "review"
        match_label = "Review"
    else:
        # 65% or below is "Not Recommended"
        recommendation = "not_recommended"
        match_label = "Not Recommended"
    
    # Confidence level
    if has_resume and len(all_skills) >= 3 and role_matched:
        confidence = "high"
    elif has_resume or (len(all_skills) >= 2 and role_matched):
        confidence = "medium"
    else:
        confidence = "low"
    
    # Risk level
    if auto_apply_blocked or seniority_gap >= 2 or auth_score == 0:
        risk = "high"
        risk_explanation = "Significant barriers or misalignment detected"
    elif seniority_gap == 1 or len(all_skills) < 2:
        risk = "moderate"
        risk_explanation = "Some stretch or skill gaps present"
    else:
        risk = "low"
        risk_explanation = "Strong alignment across key factors"
    
    # ============================================================================
    # DECISION SUMMARY (REQUIRED)
    # ============================================================================
    
    if recommendation == "strong_match":
        decision_summary = f"Strong alignment with {company_name}'s needs. {risk_explanation}. Highly recommended to apply."
    elif recommendation == "good_match":
        decision_summary = f"Solid match with {company_name}. {risk_explanation}. Worth applying with tailored application."
    elif recommendation == "review":
        decision_summary = f"Potential fit at {company_name}. {risk_explanation}. Review carefully before applying."
    else:
        # not_recommended (65% or below)
        decision_summary = f"Limited alignment with requirements. {risk_explanation}. Not recommended - consider focusing on better-fit opportunities."
    
    # ============================================================================
    # OPTIONAL VALUE ADD (for matches ≥70%)
    # ============================================================================
    
    value_add = None
    if score >= 70:
        value_add = f"This role at {company_name} offers career leverage through {job_seniority_name}-level responsibilities and skill development in {', '.join(all_skills[:2]) if all_skills else 'key areas'}."
    
    # Match reasoning (user-facing explanation)
    if score >= 70:
        match_reasoning = f"{match_label}: Your background aligns well with this {job_title_display} position. {', '.join(strengths[:2]) if strengths else 'Core requirements match your profile'}."
    else:
        match_reasoning = f"{match_label}: {', '.join(risks[:2]) if risks else 'Significant gaps detected'}. {decision_summary}"
    
    # Build resume-grounded strengths for detailed analysis
    grounded_strengths = []
    
    # Extract specific resume evidence for each strength
    if has_resume:
        # Find specific metrics and achievements from resume
        resume_lines = profile.get("resume_text", "").split('\n')
        resume_bullets = [line.strip() for line in resume_lines if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or any(char.isdigit() for char in line))]
        
        # Skill-based grounded strengths
        for skill in all_skills[:3]:
            # Find resume evidence for this skill
            skill_evidence = None
            for bullet in resume_bullets:
                if skill.lower() in bullet.lower():
                    skill_evidence = bullet[:150] + "..." if len(bullet) > 150 else bullet
                    break
            
            if skill_evidence:
                grounded_strengths.append({
                    "requirement": f"Job requires {skill}",
                    "evidence": skill_evidence,
                    "match_reason": f"Your resume demonstrates hands-on experience with {skill}"
                })
            else:
                grounded_strengths.append({
                    "requirement": f"Job requires {skill}",
                    "evidence": f"{skill.title()} listed in your skills profile",
                    "match_reason": f"Direct skill alignment with position requirements"
                })
        
        # Experience/seniority grounded strength
        if exp_score >= 15:
            years_text = f"{user_years}+ years" if user_years else "relevant experience"
            grounded_strengths.append({
                "requirement": f"Position targets {job_seniority_name}-level candidates",
                "evidence": f"Your profile indicates {years_text} of experience",
                "match_reason": f"Your seniority level ({user_seniority or 'mid'}) aligns with this {job_seniority_name} role"
            })
        
        # Role alignment grounded strength
        if role_matched and target_roles:
            grounded_strengths.append({
                "requirement": f"Hiring for {job_title_display}",
                "evidence": f"Your target role: {target_roles[0].title()}",
                "match_reason": "Direct alignment between your career goals and this position"
            })
    
    return {
        "score": score,
        "recommendation": recommendation,
        "match_label": match_label,
        "confidence": confidence,
        "risk": risk,
        "decision_summary": decision_summary,
        "strengths": strengths[:3],  # Max 3 (legacy format)
        "grounded_strengths": grounded_strengths[:5],  # New: resume-grounded strengths
        "gaps": (risks + gaps)[:2],  # Max 2, prioritize risks
        "match_reasoning": match_reasoning,
        "value_add": value_add,
        "skip_reason": None if score >= 55 else "Below recommended match threshold",
        "auto_apply_blocked": auto_apply_blocked,
        "auto_apply_reason": auto_apply_reason,
        "matched_skills": all_skills[:5],  # Expose matched skills
        "job_seniority": job_seniority_name,
        "user_seniority": user_seniority or "not specified",
    }


def calculate_match_score(job: Dict, profile: Optional[Dict]) -> int:
    """Legacy function - returns just the score for backward compatibility."""
    result = evaluate_job_match(job, profile)
    return result["score"]

# ========================
# AI ROUTES
# ========================

@api_router.post("/ai/optimize-resume")
async def optimize_resume(request: Request, req: OptimizeResumeRequest):
    """Optimize resume for ATS based on job description while preserving original format."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile or not profile.get("resume_text"):
        raise HTTPException(status_code=400, detail="Please upload your resume first")
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    resume_format = profile.get("resume_format", "text")
    original_resume = profile.get("resume_text", "")
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"resume_opt_{user.user_id}_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert ATS (Applicant Tracking System) resume optimizer.

**CRITICAL: ONE PAGE MAXIMUM**
The final resume MUST fit on ONE SINGLE PAGE when pasted into a Word document with standard margins (1 inch) and 11pt font. This is NON-NEGOTIABLE. Be concise and prioritize the most impactful content.

PAGE LENGTH GUIDELINES:
- Maximum ~450-500 words total
- 3-4 bullet points per role (not 5-6)
- Keep bullet points to 1-2 lines max
- Trim older/less relevant experience if needed to fit
- Summary/objective should be 2-3 lines max

FORMATTING RULES:
1. Preserve the original resume's structure and section order
2. Keep section headers in the same format
3. Use bullet points (•) or dashes (-) consistently
4. Maintain clear spacing between sections
5. Keep date formats consistent (e.g., "Jan 2020 - Present")
6. Do NOT add new sections or reorganize

OPTIMIZATION FOCUS:
- Inject relevant keywords from the job description naturally
- Strengthen action verbs
- Include quantifiable metrics where possible
- Mirror terminology from the job description
- PRIORITIZE recent and most relevant experience
- CUT less impactful content to fit one page

OUTPUT FORMAT:
Return the optimized resume as CONCISE plain text that fits on ONE PAGE."""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Optimize this resume for the following job. The output MUST FIT ON ONE SINGLE PAGE in a Word document.

JOB DESCRIPTION:
{req.job_description}

ORIGINAL RESUME:
{original_resume}

CRITICAL REQUIREMENTS:
1. **ONE PAGE ONLY** - This is the most important rule. Be concise!
2. Keep section headers and overall structure
3. Use consistent bullet points (• or -)
4. Limit each role to 3-4 impactful bullet points (1-2 lines each)
5. Enhance content with keywords from the job description
6. Cut less relevant content if needed to fit one page
7. Maximum ~450-500 words total

Return the concise, one-page optimized resume now:"""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"optimized_resume": response, "original_format": resume_format}
    except Exception as e:
        logger.error(f"Resume optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to optimize resume")


class DetailedMatchRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str


@api_router.post("/ai/detailed-match-analysis")
async def generate_detailed_match_analysis(request: Request, req: DetailedMatchRequest):
    """
    Generate resume-grounded match analysis.
    Every strength must reference specific resume evidence and job requirements.
    """
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your profile first")
    
    resume_text = profile.get("resume_text", "")
    if not resume_text or len(resume_text) < 100:
        raise HTTPException(status_code=400, detail="Please upload your resume for detailed analysis")
    
    # Get skills with years for context
    skills = profile.get("skills", [])
    skills_text = ""
    if skills:
        if isinstance(skills[0], dict):
            skills_text = ", ".join([f"{s.get('name', '')} ({s.get('years', 0)} years)" for s in skills])
        else:
            skills_text = ", ".join(skills)
    
    experience_years = profile.get("experience_years", 0)
    target_roles = profile.get("job_titles", [])
    seniority = profile.get("seniority_level", "mid")
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"match_analysis_{user.user_id}_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert career analyst who provides evidence-based job match analysis.

CRITICAL RULES:
1. Every strength MUST reference specific evidence from the resume
2. Every strength MUST reference a specific job requirement
3. NO generic phrases like "Strong role alignment", "Experience aligns well", "Good fit"
4. If resume evidence is weak or missing for a requirement, say so explicitly
5. Do NOT fabricate or assume experience not in the resume
6. Prefer fewer, higher-quality bullets over generic coverage

FORMAT for each strength bullet:
[Job requirement] → [Resume evidence] → [Why it matters]

Example of GOOD analysis:
"SQL-based analysis required → Resume shows 'Built SQL queries for performance reporting and trend analysis' → Direct skill match for analytical requirements"

Example of BAD analysis (DO NOT DO THIS):
"Strong role alignment: Your experience aligns well with this position" 
"""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Analyze this job match based on the candidate's ACTUAL resume content.

JOB DETAILS:
- Title: {req.job_title}
- Company: {req.company_name}
- Description: {req.job_description}

CANDIDATE PROFILE:
- Experience: {experience_years} years
- Seniority Level: {seniority}
- Target Roles: {', '.join(target_roles) if target_roles else 'Not specified'}
- Skills: {skills_text if skills_text else 'Not specified'}

CANDIDATE RESUME (use this as evidence):
{resume_text}

GENERATE A RESUME-GROUNDED MATCH ANALYSIS:

1. **Match Summary** (1-2 sentences)
   Explain why this role fits based on SPECIFIC resume evidence, not generic statements.

2. **Strengths** (3-5 bullets, ONLY if evidence exists)
   Each bullet MUST follow this format:
   [Specific job requirement] → [Specific resume bullet/experience] → [Why this matters for the role]
   
   Focus on:
   - Tools/technologies mentioned in both job and resume
   - Metrics/outcomes from resume that match job needs
   - Domain experience that aligns
   - Relevant certifications or education

3. **Gaps/Concerns** (1-3 bullets, be honest)
   List requirements from the job description where:
   - Resume evidence is weak or missing
   - Experience level may not match
   - Skills need development

4. **Recommendation**
   Should the candidate apply? Why or why not based on evidence?

IMPORTANT: Be specific and honest. Reference actual text from the resume. If you can't find evidence for something, say "Resume does not demonstrate..." rather than making assumptions."""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {
            "detailed_analysis": response,
            "job_title": req.job_title,
            "company": req.company_name,
            "skills_analyzed": skills_text,
            "experience_years": experience_years
        }
    except Exception as e:
        logger.error(f"Detailed match analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate detailed analysis")


@api_router.post("/ai/cover-letter")
async def generate_cover_letter(request: Request, req: GenerateCoverLetterRequest):
    """Generate personalized cover letter."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"cover_{user.user_id}_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert ATS-optimized cover letter writer. Write concise, professional cover letters that directly align candidate experience to job requirements.

STRICT RULES:
- 1 page max (300-450 words)
- Simple formatting (no tables, no columns, no emojis)
- No fluff or generic enthusiasm
- Use keywords directly from the job description
- Align experience clearly to role requirements
- Professional, confident tone (not desperate or salesy)
- No company clichés or buzzwords
- AVOID phrases like "I am passionate", "I am excited", "I would love to", "I am thrilled"

REQUIRED STRUCTURE:
1. Opening paragraph: State the role title and company. Briefly summarize why the candidate's background fits the role.
2. Middle paragraphs (1-2): Match experience directly to key job requirements. Use metrics or outcomes where possible. Mirror terminology used in the job description.
3. Closing paragraph: Reiterate fit. Express interest in discussing the role. Thank the reader.

Output only the cover letter text, no additional commentary."""
    ).with_model("openai", "gpt-5.2")
    
    # Handle v2 skills format (list of dicts with name, years, level)
    raw_skills = profile.get("skills", []) if profile else []
    skill_names = get_skill_names(raw_skills)
    skills = ", ".join(skill_names) if skill_names else "Not specified"
    experience = profile.get("experience_years", 0) if profile else 0
    resume = profile.get("resume_text", "") if profile else ""
    job_titles = ", ".join(profile.get("job_titles", [])) if profile else "Not specified"
    
    prompt = f"""Write an ATS-friendly cover letter using these inputs:

JOB TITLE: {req.job_title}
COMPANY: {req.company}

JOB DESCRIPTION:
{req.job_description}

CANDIDATE INFORMATION:
- Name: {user_doc['name']}
- Years of Experience: {experience}
- Key Skills: {skills}
- Target Roles: {job_titles}

RESUME CONTENT:
{resume[:2000] if resume else 'Not provided'}

Generate a professional, ATS-optimized cover letter following the strict rules and structure provided. Use keywords from the job description and align the candidate's experience directly to the role requirements."""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"cover_letter": response}
    except Exception as e:
        logger.error(f"Cover letter generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate cover letter")

@api_router.post("/ai/interview-prep")
async def get_interview_prep(request: Request, req: InterviewPrepRequest):
    """Generate interview preparation materials."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"interview_{user.user_id}_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert career coach and interview preparation specialist.
Provide comprehensive interview preparation including common questions, 
STAR method examples, company research tips, and confidence-building advice."""
    ).with_model("openai", "gpt-5.2")
    
    # Handle v2 skills format (list of dicts with name, years, level)
    raw_skills = profile.get("skills", []) if profile else []
    skill_names = get_skill_names(raw_skills)
    skills = ", ".join(skill_names) if skill_names else "Not specified"
    
    prompt = f"""You are an expert interview coach creating a professional interview preparation document for a FAANG / enterprise role.

POSITION: {req.job_title} at {req.company}
JOB DESCRIPTION:
{req.job_description}
CANDIDATE SKILLS: {skills}

FORMATTING RULES (must follow exactly):

1. Use clean, professional Markdown
2. Use numbered, ALL-CAPS section headers (e.g., 1. COMMON INTERVIEW QUESTIONS)
3. Separate major sections with a horizontal rule (---)
4. Format each interview question using this exact structure:
   - Question as a level-4 header (####)
   - Suggested approach on one line (NO asterisks, NO italics)
   - Sample answer as a blockquote (>)
5. Keep sample answers concise: 4–6 sentences max
6. Use clear whitespace between questions
7. Do NOT use asterisks or italics
8. Do NOT use emojis or casual language
9. Make everything bold and easy to read

REQUIRED SECTIONS (in this exact order):

1. COMMON INTERVIEW QUESTIONS
- 5 common questions every interviewer asks
- Each with: #### Question, Suggested approach, > Sample answer

---

2. BEHAVIORAL QUESTIONS
- 5 behavioral questions using STAR method
- Each with: #### Question, STAR framework guidance, > Sample answer

---

3. TECHNICAL QUESTIONS
- 5 technical questions specific to {req.job_title}
- Each with: #### Question, Approach guidance, > Sample answer

---

4. INTERVIEW TIPS
- 5-7 tactical tips (numbered list)
- Focus on: preparation, body language, follow-up, negotiation

---

5. QUESTIONS TO ASK THE INTERVIEWER
- 5 intelligent questions (numbered list)
- Categories: role scope, team dynamics, growth, company direction

ANSWER STYLE:
- Professional, direct, data-driven
- Emphasize measurable impact and collaboration
- Use concrete examples
- Avoid generic phrases

Generate interview prep for {req.job_title} at {req.company} following this structure exactly."""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"prep_materials": response}
    except Exception as e:
        logger.error(f"Interview prep error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate interview prep")


# ========================
# JOB COMPARISON / ANALYZE MATCH ROUTES
# ========================

@api_router.post("/jobs/{job_id}/compare")
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

@api_router.get("/jobs/{job_id}/compare")
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

@api_router.put("/jobs/{job_id}/compare/notes")
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

@api_router.post("/applications")
async def create_application(request: Request, req: ApplyRequest):
    """Create a new job application (pending approval)."""
    user = await get_current_user(request)
    
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
    
    return application

@api_router.get("/applications")
async def get_applications(request: Request):
    """Get all applications for current user."""
    user = await get_current_user(request)
    
    applications = await db.applications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"applications": applications}

@api_router.put("/applications/{application_id}/approve")
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

@api_router.get("/applications/{application_id}/autofill-payload")
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

class AutoFillRequest(BaseModel):
    submit_form: bool = False  # If True, will attempt to click submit after filling

@api_router.post("/applications/{application_id}/auto-fill")
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

@api_router.put("/applications/{application_id}/reject")
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

@api_router.delete("/applications/{application_id}")
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

@api_router.get("/applications/{application_id}/next-steps")
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

@api_router.put("/applications/{application_id}/next-steps")
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

@api_router.post("/applications/{application_id}/next-steps/generate")
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

@api_router.get("/download/{file_id}")
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

@api_router.get("/download-page/{file_id}")
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

@api_router.post("/applications/{application_id}/generate-resume-docx")
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

@api_router.post("/applications/{application_id}/generate-cover-letter-docx")
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

@api_router.post("/applications/{application_id}/prepare-download/resume")
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

@api_router.post("/applications/{application_id}/prepare-download/cover-letter")
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

@api_router.get("/applications/{application_id}/download/resume")
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

@api_router.get("/applications/{application_id}/download/cover-letter")
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

@api_router.get("/applications/{application_id}/autofill-script")
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
    script = f'''// JobMatch AI - Greenhouse Auto-Fill Script
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

    console.log('🚀 JobMatch AI Auto-Fill Starting...');
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
    
    alert('JobMatch AI Auto-Fill Complete!\\n\\n✓ Fields have been filled\\n\\nPlease:\\n1. Review all information\\n2. Upload resume file if required\\n3. Complete any CAPTCHA\\n4. Click Submit');
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

@api_router.get("/autofill/data")
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

@api_router.get("/extension/autofill-data")
async def get_extension_autofill_data(request: Request, job_url: str = None):
    """
    Get structured autofill data for the browser extension.
    Returns all user profile data including resume and cover letter.
    If job_url is provided, tries to match to a saved application for optimized content.
    """
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
    
    # Check if we have a matching saved application with optimized content
    optimized_resume = None
    optimized_cover_letter = None
    matched_application = None
    
    if job_url:
        # Try to find a matching application
        matched_application = await db.applications.find_one(
            {
                "user_id": user.user_id,
                "$or": [
                    {"apply_link": {"$regex": job_url.split("?")[0], "$options": "i"}},
                    {"job_url": {"$regex": job_url.split("?")[0], "$options": "i"}}
                ]
            },
            {"_id": 0}
        )
        
        if matched_application:
            optimized_resume = matched_application.get("optimized_resume")
            optimized_cover_letter = matched_application.get("cover_letter")
            logger.info(f"Found matching application for URL: {job_url}")
    
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


@api_router.post("/extension/track-submission")
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
    
    # Try to find the matching application by URL
    # Strip query params for matching
    base_url = job_url.split("?")[0]
    
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


@api_router.get("/screening-questions/templates")
async def get_screening_question_templates(request: Request):
    """Get the list of common screening questions with templates."""
    await get_current_user(request)  # Ensure authenticated
    return {"questions": COMMON_SCREENING_QUESTIONS}


@api_router.get("/screening-questions/answers")
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


class ScreeningAnswersUpdate(BaseModel):
    answers: dict  # {question_id: answer_value}


@api_router.put("/screening-questions/answers")
async def update_screening_answers(request: Request, data: ScreeningAnswersUpdate):
    """Update user's screening question answers."""
    user = await get_current_user(request)
    
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {"$set": {"screening_answers": data.answers}},
        upsert=True
    )
    
    return {"success": True, "message": "Screening answers saved"}


class CustomQuestionAdd(BaseModel):
    question: str
    answer: str
    keywords: List[str] = []


@api_router.post("/screening-questions/custom")
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


class AnswerQuestionsRequest(BaseModel):
    questions: List[dict]  # List of {question: str, options: List[str] (optional)}

@api_router.post("/extension/answer-questions")
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

@api_router.get("/dashboard/stats")
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
    
    return {
        "total_applications": total,
        "applied": applied,
        "pending": pending,
        "recent_applications": recent,
        "profile_completeness": completeness
    }

# ========================
# ATS INGESTION STATS
# ========================

@api_router.get("/admin/ats-stats")
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
        },
        "total_companies": len(GREENHOUSE_COMPANIES) + len(LEVER_COMPANIES) + len(SMARTRECRUITERS_COMPANIES) + len(PINPOINT_COMPANIES)
    }

# ========================
# HEALTH CHECK
# ========================

@api_router.get("/")
async def root():
    return {"message": "JobMatch AI API", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

@api_router.get("/test-download")
async def test_download():
    """Test endpoint - downloads a simple DOCX file without authentication."""
    from docx import Document
    import io
    
    # Create a simple test document
    doc = Document()
    doc.add_heading('Test Download', 0)
    doc.add_paragraph('If you can read this, downloads are working!')
    doc.add_paragraph('Generated at: ' + datetime.now().isoformat())
    
    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    docx_bytes = buffer.getvalue()
    
    # Save to static downloads
    filename = f"test_download_{uuid.uuid4().hex[:8]}.docx"
    filepath = os.path.join(STATIC_DOWNLOADS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(docx_bytes)
    
    # Redirect to static file
    return RedirectResponse(url=f"/api/static-downloads/{filename}", status_code=302)

# Test form for autofill bot testing
@api_router.get("/test-form")
async def serve_test_form():
    """Serve a test application form for bot testing."""
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Application Form</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        .field { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; box-sizing: border-box; }
        textarea { height: 100px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Test Job Application Form</h1>
    <form id="application-form">
        <div class="field">
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name">
        </div>
        <div class="field">
            <label for="last_name">Last Name</label>
            <input type="text" id="last_name" name="last_name">
        </div>
        <div class="field">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email">
        </div>
        <div class="field">
            <label for="phone">Phone Number</label>
            <input type="tel" id="phone" name="phone">
        </div>
        <div class="field">
            <label for="city">City</label>
            <input type="text" id="city" name="city">
        </div>
        <div class="field">
            <label for="linkedin">LinkedIn URL</label>
            <input type="url" id="linkedin" name="linkedin" placeholder="https://linkedin.com/in/...">
        </div>
        <div class="field">
            <label for="github">GitHub URL</label>
            <input type="url" id="github" name="github" placeholder="https://github.com/...">
        </div>
        <div class="field">
            <label for="portfolio">Portfolio / Website</label>
            <input type="url" id="portfolio" name="portfolio" placeholder="https://...">
        </div>
        <div class="field">
            <label for="resume">Resume/CV</label>
            <input type="file" id="resume" name="resume" accept=".pdf,.docx">
        </div>
        <div class="field">
            <label for="cover_letter">Cover Letter</label>
            <textarea id="cover_letter" name="cover_letter" placeholder="Write your cover letter..."></textarea>
        </div>
        <button type="submit">Submit Application</button>
    </form>
</body>
</html>"""
    return HTMLResponse(content=html)

# Include the routers
app.include_router(api_router)
app.include_router(public_router, prefix="/api")  # Public Jobs API at /api/public/*

# Get frontend URL for CORS - allow Lovable domains
FRONTEND_URL = os.environ.get('CORS_ORIGINS', '')
origins = [origin.strip() for origin in FRONTEND_URL.split(',') if origin.strip()]

# Add common Lovable domains for Phase 1 integration
lovable_origins = [
    "https://*.lovable.app",
    "https://*.lovableproject.com", 
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080"
]
origins.extend(lovable_origins)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow all origins for public API
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ========================
# SCHEDULED JOB INGESTION
# Automatically refresh jobs every 2 hours
# ========================

scheduler = AsyncIOScheduler()

async def scheduled_job_ingestion():
    """Background task to refresh jobs every 2 hours."""
    logger.info("🔄 Starting scheduled job ingestion...")
    try:
        result = await ingest_all_jobs()
        logger.info(f"✅ Scheduled ingestion complete: {result.get('jobs_ingested', 0)} jobs")
    except Exception as e:
        logger.error(f"❌ Scheduled ingestion failed: {e}")

@app.on_event("startup")
async def start_scheduler():
    """Start the job scheduler on app startup."""
    
    # Ensure Playwright browsers are installed
    await ensure_playwright_browsers()
    
    # Run job ingestion every 2 hours
    scheduler.add_job(
        scheduled_job_ingestion,
        trigger=IntervalTrigger(hours=2),
        id="job_ingestion",
        name="Refresh jobs from Greenhouse/Lever",
        replace_existing=True
    )
    scheduler.start()
    logger.info("📅 Job scheduler started - jobs will refresh every 2 hours")
    
    # Run initial ingestion if database is empty
    job_count = await db.stored_jobs.count_documents({})
    if job_count == 0:
        logger.info("Database empty - running initial job ingestion...")
        asyncio.create_task(ingest_all_jobs())


async def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed. Auto-install if missing."""
    import subprocess
    import sys
    
    browser_path = "/pw-browsers/chromium-1200"
    headless_shell_path = "/pw-browsers/chromium_headless_shell-1200"
    
    # Check if browsers exist
    browsers_exist = os.path.exists(browser_path) or os.path.exists(headless_shell_path)
    
    if not browsers_exist:
        logger.info("🔧 Playwright browsers not found. Installing...")
        try:
            # Set environment variable
            env = os.environ.copy()
            env['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'
            
            # Install chromium using python -m playwright
            result = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                env=env,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                logger.info("✅ Playwright browsers installed successfully")
            else:
                logger.error(f"❌ Playwright browser installation failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("❌ Playwright browser installation timed out")
        except Exception as e:
            logger.error(f"❌ Playwright browser installation error: {e}")
    else:
        logger.info("✅ Playwright browsers already installed")

@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown scheduler and database on app shutdown."""
    scheduler.shutdown()
    client.close()
    logger.info("Scheduler and database connection closed")
