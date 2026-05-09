"""
core.py - Shared infrastructure for MyCareerCopilot backend.

This module centralizes all shared state, configuration, helpers, and
dependencies used across the modular route files. Importing from this
single module avoids circular imports and ensures every router uses
the same database client, logger, rate limiter and auth dependency.

Refactored from monolithic server.py (Feb 2026).
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import os
import logging
import collections
import time
import secrets

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import resend

# --- Environment & Paths ----------------------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://job-match-ai-62.preview.emergentagent.com')

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'Fuzail.abukhari@gmail.com')

# API keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')

# --- MongoDB ----------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# --- Logging ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backend")

# --- Static downloads dir --------------------------------------------------
STATIC_DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "static_downloads")
os.makedirs(STATIC_DOWNLOADS_DIR, exist_ok=True)

# --- Password hashing ------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets strength requirements: 8+ chars, uppercase, number, special char."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    return True, ""

# --- Rate limiter ----------------------------------------------------------
class RateLimiter:
    """Sliding-window rate limiter keyed by IP."""
    def __init__(self):
        self._hits = collections.defaultdict(list)

    def _cleanup(self, key, window):
        cutoff = time.monotonic() - window
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

    def is_limited(self, key: str, max_hits: int, window_seconds: int) -> bool:
        self._cleanup(key, window_seconds)
        if len(self._hits[key]) >= max_hits:
            return True
        self._hits[key].append(time.monotonic())
        return False

    def remaining(self, key: str, max_hits: int, window_seconds: int) -> int:
        self._cleanup(key, window_seconds)
        return max(0, max_hits - len(self._hits[key]))

rate_limiter = RateLimiter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# Rate limits: (max_attempts, window_seconds)
RATE_LOGIN  = (10, 60)    # 10 per minute per IP
RATE_SIGNUP = (5, 60)     # 5 per minute per IP
RATE_RESET  = (3, 300)    # 3 per 5 minutes per IP

# Account lockout
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# --- ATS company lists -----------------------------------------------------
GREENHOUSE_COMPANIES = [
    "airbnb", "stripe", "figma", "dropbox", "discord",
    "instacart", "coinbase", "affirm", "brex", "gusto",
    "lattice", "carta", "gitlab", "datadog", "databricks",
    "anthropic", "postman", "launchdarkly", "mixpanel", "amplitude",
    "marqeta", "adyen", "asana", "intercom", "oscar",
    "faire", "headway", "coursera", "duolingo", "gemini",
    "zocdoc", "alchemy",
    "hootsuite", "d2l", "ritual", "grammarly", "lyft",
    "elastic", "cloudflare", "okta", "zscaler", "twitch",
    "airtable", "webflow", "vercel", "fivetran", "pagerduty",
    "reddit", "pinterest", "toast", "robinhood", "sofi",
    "roblox", "chime", "opendoor", "nextdoor", "scopely",
    "tulip", "ecobee", "squarespace",
]

LEVER_COMPANIES = [
    "lever", "attentive", "medium",
    "wealthsimple", "plaid", "spotify", "pointclickcare",
    "clearco", "koho", "nuvei",
    "netflix",
]

CUSTOM_CAREER_COMPANIES = ["amazon", "microsoft", "apple"]
ASHBY_COMPANIES = []

# Job cache settings
JOB_CACHE_TTL_MINUTES = 30
PARALLEL_BATCH_SIZE = 20

# --- Non-English filter ----------------------------------------------------
NON_ENGLISH_PATTERNS = [
    "analyste", "développeur", "ingénieur", "responsable", "directeur", "gestionnaire",
    "conseiller", "coordonnateur", "spécialiste", "technicien", "adjoint", "chargé",
    " de la ", " du ", " des ", " sur ", " aux ", " pour ", " et ", " ou ",
    "qualité", "données", "affaires", "services", "ressources", "humaines",
    "analista", "desarrollador", "ingeniero", "gerente", "director", "especialista",
    "coordinador", "técnico", "asistente", " de ", " del ", " los ", " las ", " para ",
    "portugais", "português", "portuguese", "analista", "desenvolvedor", "engenheiro",
    "entwickler", "ingenieur", "leiter", "berater", "spezialist", "projektleiter",
    " und ", " für ", " mit ",
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

def normalize_posted_date(posted_at, fallback=None):
    """Normalize various posted_at formats to a proper UTC datetime."""
    from dateutil import parser as dateparser

    if posted_at is None:
        return fallback or datetime.now(timezone.utc)
    if isinstance(posted_at, datetime):
        if posted_at.tzinfo is None:
            return posted_at.replace(tzinfo=timezone.utc)
        return posted_at
    if isinstance(posted_at, (int, float)):
        try:
            return datetime.fromtimestamp(posted_at / 1000, tz=timezone.utc)
        except Exception:
            return fallback or datetime.now(timezone.utc)
    if isinstance(posted_at, str):
        try:
            dt = dateparser.parse(posted_at)
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return fallback or datetime.now(timezone.utc)
    return fallback or datetime.now(timezone.utc)

# --- Query expansion -------------------------------------------------------
QUERY_SYNONYMS = {
    "business analyst": ["business analyst", "business systems analyst", "business intelligence analyst", "business analysis", "business operations analyst", "data analyst", "operations analyst", "strategy analyst", "systems analyst", "process analyst", "requirements analyst"],
    "data analyst": ["data analyst", "data analytics", "analytics analyst", "bi analyst", "business intelligence analyst", "data analysis", "business analyst", "insights analyst"],
    "software engineer": ["software engineer", "software developer", "swe", "backend engineer", "frontend engineer", "full stack engineer", "fullstack engineer", "web developer"],
    "product manager": ["product manager", "product lead", "pm ", "product owner", "product management", "program manager"],
    "project manager": ["project manager", "project lead", "pmo", "project management", "scrum master", "program manager"],
    "data scientist": ["data scientist", "data science", "ml engineer", "machine learning engineer", "applied scientist"],
    "ux designer": ["ux designer", "ui designer", "product designer", "ux/ui", "ui/ux", "user experience"],
    "devops": ["devops", "site reliability", "sre", "platform engineer", "infrastructure engineer", "cloud engineer"],
    "qa": ["qa engineer", "quality assurance", "test engineer", "sdet", "qa analyst"],
    "marketing": ["marketing manager", "growth marketing", "digital marketing", "marketing analyst", "marketing coordinator"],
    "financial analyst": ["financial analyst", "finance analyst", "fp&a", "financial planning", "business analyst"],
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

# --- Salary parsing helpers ------------------------------------------------
import re as _re

def parse_salary_from_description(description: str) -> Optional[str]:
    """
    Parse salary information from job description text.
    Returns a formatted salary string or None if not found.
    Does NOT hallucinate values - only returns what's explicitly stated.
    """
    if not description:
        return None
    text = description.lower()
    patterns = [
        r'\$[\d,]+(?:k)?\s*[-–to]+\s*\$[\d,]+(?:k)?(?:\s*(?:per\s+)?(?:year|annual|yr|/yr|/year))?',
        r'\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?\s*(?:per\s+)?(?:year|annual|annually|yr|/yr|/year)',
        r'\$[\d,.]+\s*[-–to]+\s*\$[\d,.]+\s*(?:per\s+)?(?:hour|hr|/hr|/hour|hourly)',
        r'salary[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
        r'compensation[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
        r'[\d,]+\s*[-–to]+\s*[\d,]+\s*(?:usd|cad|gbp|eur)(?:\s*(?:per\s+)?(?:year|annual))?',
        r'base\s+salary[:\s]+\$[\d,]+(?:k)?(?:\s*[-–]\s*\$[\d,]+(?:k)?)?',
    ]
    for pattern in patterns:
        match = _re.search(pattern, text, _re.IGNORECASE)
        if match:
            salary_text = match.group(0).strip()
            salary_text = salary_text.replace('salary:', '').replace('compensation:', '').replace('base salary:', '').strip()
            for code in ['usd', 'cad', 'gbp', 'eur']:
                salary_text = _re.sub(code, code.upper(), salary_text, flags=_re.IGNORECASE)
            return salary_text.strip()
    return None

def format_salary_range(min_salary: Optional[int], max_salary: Optional[int], description: str = "") -> str:
    """
    Format salary range from structured data or parse from description.
    Returns 'Salary not listed' if no salary information is available.
    """
    if min_salary and max_salary:
        return f"${min_salary:,} - ${max_salary:,}/year"
    elif min_salary:
        return f"${min_salary:,}+/year"
    elif max_salary:
        return f"Up to ${max_salary:,}/year"
    parsed = parse_salary_from_description(description)
    if parsed:
        return parsed
    return "Salary not listed"

# --- Auth dependency -------------------------------------------------------
async def get_current_user(request: Request):
    """Get current user from session token in cookies or Authorization header."""
    from models import User  # local import to avoid circular dependency

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

async def get_admin_user(request: Request):
    """Verify the current user has admin role."""
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
