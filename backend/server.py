from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import base64
import io
import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Document parsing imports
from docx import Document
from PyPDF2 import PdfReader

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')

# Known Greenhouse company boards (will be expanded dynamically)
GREENHOUSE_COMPANIES = [
    "airbnb", "stripe", "figma", "notion", "airtable", "dropbox", "slack",
    "twitch", "discord", "spotify", "pinterest", "lyft", "doordash",
    "instacart", "robinhood", "coinbase", "plaid", "affirm", "chime",
    "brex", "ramp", "rippling", "gusto", "lattice", "carta", "deel",
    "remote", "gitlab", "datadog", "mongodb", "elastic", "snowflake",
    "databricks", "confluent", "hashicorp", "cockroachlabs", "planetscale",
    "vercel", "netlify", "render", "railway", "supabase", "neon",
    "openai", "anthropic", "cohere", "huggingface", "scale", "labelbox",
    "weights-and-biases", "mlflow", "prefect", "dagster", "airbyte",
    "fivetran", "dbt-labs", "looker", "metabase", "preset", "hex",
    "retool", "airplane", "appsmith", "budibase", "tooljet"
]

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    resume_text: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_format: Optional[str] = None
    skills: List[str] = []
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
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfileUpdate(BaseModel):
    skills: Optional[List[str]] = None
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
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None

class JobApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_id: str = Field(default_factory=lambda: f"app_{uuid.uuid4().hex[:12]}")
    user_id: str
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    optimized_resume: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = "pending"  # pending, approved, applied, rejected
    match_score: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied_at: Optional[datetime] = None

class ApplyRequest(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    job_description: str
    apply_link: Optional[str] = None
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

class JobSearchQuery(BaseModel):
    query: str
    location: Optional[str] = None
    page: int = 1
    num_pages: int = 1
    employment_types: Optional[str] = None  # FULLTIME, PARTTIME, CONTRACTOR, INTERN

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
    """Get user profile."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        # Create default profile
        profile = {
            "user_id": user.user_id,
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
    
    return profile

@api_router.put("/profile")
async def update_profile(request: Request, update: ProfileUpdate):
    """Update user profile."""
    user = await get_current_user(request)
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.user_profiles.update_one(
        {"user_id": user.user_id},
        {"$set": update_data},
        upsert=True
    )
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    return profile

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file while preserving structure."""
    try:
        doc = Document(io.BytesIO(content))
        lines = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Preserve formatting hints
                if para.style and para.style.name:
                    style = para.style.name.lower()
                    if 'heading' in style or 'title' in style:
                        lines.append(f"\n{text.upper()}\n{'=' * len(text)}")
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
    
    # Filter by query and location
    filtered_jobs = []
    for job in all_jobs:
        job_title = job.get("title", "").lower()
        job_company = job.get("company", "").lower()
        job_dept = job.get("department", "").lower()
        job_location = job.get("location", "").lower()
        
        # Match query - any word must match title, company, or department
        query_match = not query_words or any(
            word in job_title or word in job_company or word in job_dept
            for word in query_words
        )
        
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
    """Search for jobs from Greenhouse-powered career pages with streaming."""
    user = await get_current_user(request)
    
    body = await request.json()
    query = body.get("query", "")
    location = body.get("location", "")
    
    logger.info(f"Greenhouse search (streaming): query='{query}', location='{location}'")
    
    # Get user profile for matching
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get applied job IDs to filter duplicates
    existing_applications = await db.applications.find(
        {"user_id": user.user_id},
        {"job_id": 1, "_id": 0}
    ).to_list(500)
    applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
    
    async def stream_greenhouse_jobs():
        """Generator function that streams jobs as they're found."""
        import json
        
        query_words = query.lower().split() if query else []
        location_lower = location.lower() if location else ""
        
        jobs_found = 0
        
        # Process companies one by one and stream results
        for company in GREENHOUSE_COMPANIES:
            try:
                # Fetch jobs from this company
                company_jobs = await fetch_greenhouse_company_jobs(company)
                
                if not company_jobs:
                    continue
                
                # Filter and enrich jobs from this company
                for job in company_jobs:
                    # Skip already applied jobs
                    if job.get("job_id") in applied_job_ids:
                        continue
                    
                    # Filter by query
                    job_title = job.get("title", "").lower()
                    job_company = job.get("company", "").lower()
                    job_dept = job.get("department", "").lower()
                    job_location = job.get("location", "").lower()
                    
                    query_match = not query_words or any(
                        word in job_title or word in job_company or word in job_dept
                        for word in query_words
                    )
                    
                    location_match = not location_lower or location_lower in job_location
                    
                    if not (query_match and location_match):
                        continue
                    
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
                    
                    # Stream this job immediately
                    jobs_found += 1
                    yield f"data: {json.dumps(job)}\n\n"
                    
                    # Limit to 30 jobs
                    if jobs_found >= 30:
                        break
                
                if jobs_found >= 30:
                    break
                    
            except Exception as e:
                logger.debug(f"Error fetching from {company}: {e}")
                continue
        
        # Send completion message
        yield f"data: {json.dumps({'done': True, 'total': jobs_found})}\n\n"
    
    return StreamingResponse(
        stream_greenhouse_jobs(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

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
                "resume_text": resume_text,
                "resume_raw": raw_content_b64,
                "resume_filename": file.filename,
                "resume_format": resume_format,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        logger.info(f"Resume uploaded for user {user.user_id}: {file.filename} (format: {resume_format})")
        return {
            "message": "Resume uploaded successfully", 
            "filename": file.filename,
            "format": resume_format,
            "text_extracted": len(resume_text) > 0
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

# ========================
# JOB SEARCH ROUTES
# ========================

@api_router.post("/jobs/search")
async def search_jobs(request: Request, query: JobSearchQuery):
    """Search for jobs using JSearch API."""
    user = await get_current_user(request)
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
        "query": query.query,
        "page": str(query.page),
        "num_pages": str(query.num_pages)
    }
    
    if query.location:
        params["query"] = f"{query.query} in {query.location}"
    
    if query.employment_types:
        params["employment_types"] = query.employment_types
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                headers=headers,
                params=params,
                timeout=30.0
            )
        
        if response.status_code != 200:
            logger.error(f"JSearch API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to fetch jobs")
        
        data = response.json()
        jobs = data.get("data", [])
        
        # Filter out LinkedIn jobs - only keep jobs with direct company URLs
        filtered_jobs = []
        for job in jobs:
            apply_link = job.get("job_apply_link", "") or ""
            # Skip LinkedIn jobs
            if "linkedin.com" in apply_link.lower():
                continue
            filtered_jobs.append(job)
        
        jobs = filtered_jobs
        logger.info(f"Filtered to {len(jobs)} non-LinkedIn jobs")
        
        # Get user's existing applications to filter out duplicates
        existing_applications = await db.applications.find(
            {"user_id": user.user_id},
            {"job_id": 1, "_id": 0}
        ).to_list(500)
        applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
        
        # Filter out jobs user has already applied to
        jobs = [job for job in jobs if job.get("job_id") not in applied_job_ids]
        logger.info(f"After removing applied jobs: {len(jobs)} jobs remaining")
        
        # Get user profile for matching
        profile = await db.user_profiles.find_one(
            {"user_id": user.user_id},
            {"_id": 0}
        )
        
        # Calculate match scores with detailed evaluation
        enriched_jobs = []
        for job in jobs:
            match_eval = evaluate_job_match(job, profile)
            enriched_jobs.append({
                "job_id": job.get("job_id"),
                "title": job.get("job_title"),
                "company": job.get("employer_name"),
                "company_logo": job.get("employer_logo"),
                "location": (job.get("job_city") or "") + (", " + job.get("job_state") if job.get("job_state") else ""),
                "employment_type": job.get("job_employment_type"),
                "description": job.get("job_description", "")[:500] + "...",
                "full_description": job.get("job_description"),
                "apply_link": job.get("job_apply_link"),
                "posted_at": job.get("job_posted_at_datetime_utc"),
                "salary_min": job.get("job_min_salary"),
                "salary_max": job.get("job_max_salary"),
                "salary_currency": job.get("job_salary_currency"),
                "is_remote": job.get("job_is_remote"),
                "match_score": match_eval["score"],
                "match_recommendation": match_eval["recommendation"],
                "match_strengths": match_eval["strengths"],
                "match_gaps": match_eval["gaps"],
                "match_reasoning": match_eval["match_reasoning"],
                "skip_reason": match_eval["skip_reason"],
                "highlights": job.get("job_highlights", {}),
                "source": "jsearch"
            })
        
        # Sort by match score, but put "skip" recommendations at the end
        enriched_jobs.sort(key=lambda x: (0 if x["match_recommendation"] == "skip" else 1, x["match_score"]), reverse=True)
        
        return {
            "jobs": enriched_jobs,
            "total": len(enriched_jobs)
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Job search timed out")
    except Exception as e:
        logger.error(f"Job search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def evaluate_job_match(job: Dict, profile: Optional[Dict]) -> Dict:
    """
    Intelligently evaluate job match with detailed reasoning.
    Returns match score, strengths, gaps, recommendation, and skip reason if applicable.
    """
    if not profile:
        return {
            "score": 50,
            "recommendation": "review",
            "strengths": [],
            "gaps": ["Complete your profile for better matching"],
            "match_reasoning": "Profile incomplete - unable to provide detailed analysis",
            "skip_reason": None
        }
    
    strengths = []
    gaps = []
    skip_reasons = []
    score = 40  # Base score
    
    job_title = (job.get("job_title") or "").lower()
    job_desc = (job.get("job_description") or "").lower()
    job_title_display = job.get("job_title") or "this role"
    company_name = job.get("employer_name") or "this company"
    job_city = job.get("job_city") or ""
    job_state = job.get("job_state") or ""
    job_location = (job_city + " " + job_state).lower().strip()
    is_remote = job.get("job_is_remote", False)
    
    # 1. Role Relevance (max +25 points)
    role_match = False
    matched_title = None
    for title in profile.get("job_titles", []):
        if title.lower() in job_title or any(word in job_title for word in title.lower().split()):
            matched_title = title
            score += 25
            role_match = True
            break
    
    if role_match and matched_title:
        strengths.append(f"Your target role '{matched_title}' directly aligns with this {job_title_display} position at {company_name}")
    
    if not role_match:
        gaps.append("Role title doesn't match your target positions")
        # Check if it's completely misaligned
        if profile.get("job_titles"):
            target_keywords = set()
            for t in profile.get("job_titles", []):
                target_keywords.update(t.lower().split())
            job_keywords = set(job_title.split())
            if not target_keywords.intersection(job_keywords):
                skip_reasons.append("Role is misaligned with your target positions")
    
    # 2. Skills Match (max +20 points)
    skills = profile.get("skills", [])
    matched_skills = []
    missing_skills = []
    
    for skill in skills:
        if skill.lower() in job_desc:
            matched_skills.append(skill)
    
    if skills:
        skill_ratio = len(matched_skills) / len(skills)
        score += int(skill_ratio * 20)
        
        if matched_skills:
            # Create detailed skill match explanation
            if len(matched_skills) >= 3:
                strengths.append(f"Strong technical alignment: Your expertise in {', '.join(matched_skills[:3])} directly matches key requirements in this job description")
            elif len(matched_skills) >= 1:
                strengths.append(f"Your {', '.join(matched_skills)} skills are specifically mentioned in the job requirements")
            
            # Add context about how skills apply to the role
            if any(s.lower() in ['python', 'javascript', 'java', 'sql', 'react', 'node'] for s in matched_skills):
                tech_matches = [s for s in matched_skills if s.lower() in ['python', 'javascript', 'java', 'sql', 'react', 'node', 'aws', 'docker', 'kubernetes']]
                if tech_matches:
                    strengths.append(f"Your technical stack ({', '.join(tech_matches[:4])}) is well-suited for the technology requirements at {company_name}")
        
        # Check for required skills in job that user doesn't have
        common_required = ["python", "javascript", "java", "sql", "react", "aws", "docker"]
        for req_skill in common_required:
            if req_skill in job_desc and req_skill.lower() not in [s.lower() for s in skills]:
                if "required" in job_desc[max(0, job_desc.find(req_skill)-50):job_desc.find(req_skill)+50]:
                    missing_skills.append(req_skill)
        
        if missing_skills:
            gaps.append(f"May need: {', '.join(missing_skills[:3])}")
    
    # 3. Experience Level & Seniority (max +15 points)
    user_years = profile.get("experience_years", 0)
    user_seniority = profile.get("seniority_level", "").lower()
    
    # Define seniority hierarchy
    seniority_levels = {
        "entry": 0,
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "manager": 4,
        "director": 5,
        "executive": 6
    }
    
    # Detect job seniority from title/description
    job_seniority = "mid"
    job_seniority_level = 2
    
    if any(word in job_title for word in ["ceo", "cto", "cfo", "vp", "vice president", "chief"]):
        job_seniority = "executive"
        job_seniority_level = 6
    elif any(word in job_title for word in ["director", "head of"]):
        job_seniority = "director"
        job_seniority_level = 5
    elif any(word in job_title for word in ["senior", "sr.", "lead", "principal", "staff"]):
        job_seniority = "senior"
        job_seniority_level = 3
    elif any(word in job_title for word in ["junior", "jr.", "entry", "associate", "graduate"]):
        job_seniority = "junior"
        job_seniority_level = 1
    elif any(word in job_title for word in ["manager", "engineering manager"]):
        job_seniority = "manager"
        job_seniority_level = 4
    
    # Get user's seniority level (default to mid if not set)
    user_seniority_level = seniority_levels.get(user_seniority, None)
    if user_seniority_level is None:
        # Infer from years of experience if seniority not set
        if user_years <= 2:
            user_seniority_level = 1  # junior
        elif user_years <= 5:
            user_seniority_level = 2  # mid
        elif user_years <= 8:
            user_seniority_level = 3  # senior
        else:
            user_seniority_level = 4  # lead/manager
    
    # STRICT RULE: Skip if job is >1 level above user's seniority
    level_gap = job_seniority_level - user_seniority_level
    
    if level_gap > 1:
        skip_reasons.append(f"Role is {job_seniority} level - significantly above your current {user_seniority or 'mid'}-level position ({level_gap} levels above)")
    
    # Check experience alignment
    seniority_match = False
    if job_seniority == "junior" and user_years <= 3:
        seniority_match = True
        strengths.append(f"With {user_years} years of experience, you're well-positioned for this entry-level opportunity to grow your career")
        score += 15
    elif job_seniority == "mid" and 2 <= user_years <= 7:
        seniority_match = True
        strengths.append(f"Your {user_years} years of experience positions you as an ideal mid-level candidate for this role")
        score += 15
    elif job_seniority == "senior" and user_years >= 5:
        seniority_match = True
        strengths.append(f"Your {user_years} years of experience demonstrates the seniority level {company_name} is seeking")
        score += 15
    elif job_seniority == "manager" and user_years >= 6:
        seniority_match = True
        strengths.append(f"Your {user_years}+ years provide the team management experience required for this role")
        score += 15
    elif job_seniority == "director" and user_years >= 8:
        seniority_match = True
        strengths.append(f"With {user_years}+ years in the field, you have the leadership experience required for this {job_title_display} position")
        score += 15
    elif job_seniority == "executive" and user_years >= 12:
        seniority_match = True
        strengths.append(f"Your extensive {user_years}+ years positions you for this executive-level opportunity")
        score += 15
    
    if not seniority_match:
        if level_gap == 1:
            gaps.append(f"Role is one level above your current position ({job_seniority} vs {user_seniority or 'mid'}) - stretch opportunity")
        elif job_seniority == "senior" and user_years < 5:
            gaps.append(f"Role requires more experience ({job_seniority} level, typically 5+ years)")
        elif job_seniority in ["director", "manager"] and user_years < 8:
            gaps.append("This leadership role requires extensive experience and team management background")
    
    # 4. Location Match (max +15 points)
    location_match = False
    preferred_locations = [loc.lower() for loc in profile.get("preferred_locations", [])]
    job_city_display = job.get("job_city") or ""
    job_state_display = job.get("job_state") or ""
    location_display = f"{job_city_display}, {job_state_display}".strip(", ")
    
    if is_remote and "remote" in preferred_locations:
        strengths.append(f"This is a remote position, perfectly matching your work location preference")
        score += 15
        location_match = True
    elif any(loc in job_location for loc in preferred_locations):
        matched_loc = next((loc for loc in preferred_locations if loc in job_location), "")
        strengths.append(f"Job located in {location_display or matched_loc.title()} aligns with your preferred work locations")
        score += 15
        location_match = True
    elif is_remote:
        strengths.append(f"Remote work option available, offering flexibility regardless of your location")
        score += 10
        location_match = True
    
    if not location_match and preferred_locations:
        gaps.append("Location may not match your preferences")
    
    # 5. Industry Match (max +10 points) - STRICT FILTERING
    industries = [ind.lower() for ind in profile.get("industries", [])]
    open_to_any = profile.get("open_to_any_industry", False)
    
    if open_to_any:
        score += 10
        strengths.append(f"Your openness to various industries makes {company_name} a viable opportunity")
    elif industries:
        industry_keywords = {
            "technology": ["tech", "software", "saas", "startup", "digital", "app", "platform", "cloud"],
            "finance": ["bank", "financial", "fintech", "investment", "insurance", "trading", "asset management"],
            "healthcare": ["health", "medical", "pharma", "biotech", "hospital", "clinical", "diagnostic"],
            "retail": ["retail", "ecommerce", "consumer", "shopping", "marketplace"],
            "manufacturing": ["manufacturing", "industrial", "production", "supply chain"],
            "consulting": ["consulting", "advisory", "professional services"],
            "education": ["education", "edtech", "learning", "university", "school"],
            "media": ["media", "entertainment", "content", "streaming", "publishing"],
            "energy": ["energy", "oil", "gas", "renewable", "utilities"],
            "real estate": ["real estate", "property", "housing", "construction"],
        }
        
        industry_display_names = {
            "technology": "Technology/Software",
            "finance": "Finance/Banking", 
            "healthcare": "Healthcare/Medical",
            "retail": "Retail/E-commerce",
            "manufacturing": "Manufacturing",
            "consulting": "Consulting/Professional Services",
            "education": "Education/EdTech",
            "media": "Media/Entertainment",
            "energy": "Energy/Utilities",
            "real estate": "Real Estate/Construction",
        }
        
        industry_matched = False
        for ind in industries:
            keywords = industry_keywords.get(ind, [ind])
            if any(kw in job_desc or kw in company_name.lower() for kw in keywords):
                display_name = industry_display_names.get(ind, ind.title())
                strengths.append(f"{company_name} operates in the {display_name} sector, matching your target industry preference")
                score += 10
                industry_matched = True
                break
        
        # STRICT RULE: Skip if industry doesn't match (unless user has <3 industries selected)
        if not industry_matched:
            if len(industries) >= 1:  # If user has selected specific industries
                gaps.append("Industry does not match your selected preferences")
                # Skip if no industry match found
                skip_reasons.append(f"Company industry doesn't align with your selected focus areas: {', '.join([industry_display_names.get(i, i.title()) for i in industries])}")
    
    # 6. Work Authorization Check (STRICT)
    work_auth = profile.get("work_authorization", "")
    if work_auth == "require_sponsorship":
        # Check if job mentions no sponsorship available
        sponsorship_blockers = [
            "no sponsorship", "must be authorized", "no visa", 
            "canadian citizen", "permanent resident only", "pr only",
            "must have valid work permit", "no lmia", "no work visa",
            "us citizen", "authorized to work", "must be eligible"
        ]
        if any(blocker in job_desc.lower() for blocker in sponsorship_blockers):
            skip_reasons.append("Role does not offer work permit/visa sponsorship - requires existing work authorization")
    
    # Check if job is in a location that doesn't match user's work authorization
    if work_auth in ["canadian_citizen", "permanent_resident"] and job_location:
        # If user is Canada-authorized but job is clearly US-only
        us_only_indicators = ["us only", "united states only", "must be located in us", "no remote", "must be in usa"]
        if any(indicator in job_desc.lower() for indicator in us_only_indicators) and "canada" not in job_location:
            skip_reasons.append("Role requires US work authorization - not available for Canadian residents")
    
    # 7. Salary Check (max +5 points)
    job_min_salary = job.get("job_min_salary")
    job_max_salary = job.get("job_max_salary")
    user_min_salary = profile.get("salary_min")
    
    if job_min_salary and user_min_salary:
        if job_min_salary >= user_min_salary:
            salary_str = f"${job_min_salary:,}"
            if job_max_salary:
                salary_str += f" - ${job_max_salary:,}"
            strengths.append(f"Compensation ({salary_str}) meets or exceeds your minimum salary requirement")
            score += 5
        else:
            gaps.append("Salary may be below your minimum requirement")
    
    # Determine recommendation
    score = min(score, 100)
    
    if skip_reasons:
        recommendation = "skip"
        match_reasoning = f"Not recommended: {skip_reasons[0]}"
    elif score >= 75:
        recommendation = "strong_match"
        match_reasoning = f"Strong match for {job_title_display} - your experience and skills align well with what {company_name} is seeking"
    elif score >= 60:
        recommendation = "good_match"
        match_reasoning = f"Good potential fit - your background has relevant overlap with this {job_title_display} role"
    elif score >= 45:
        recommendation = "review"
        match_reasoning = f"Worth considering - review the job requirements carefully to assess fit"
    else:
        recommendation = "weak_match"
        match_reasoning = f"Limited alignment with your profile - may require significant adaptation"
    
    return {
        "score": score,
        "recommendation": recommendation,
        "strengths": strengths[:5],  # Limit to top 5 for more detail
        "gaps": gaps[:3],  # Limit to top 3
        "match_reasoning": match_reasoning,
        "skip_reason": skip_reasons[0] if skip_reasons else None
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

CRITICAL RULES:
1. PRESERVE the exact same structure, sections, and formatting as the original resume
2. Keep all section headers in the same order (e.g., Summary, Experience, Education, Skills)
3. Maintain the same layout style (bullet points, dates, company names format)
4. Only modify the CONTENT to add relevant keywords and optimize for ATS
5. Do NOT add new sections that weren't in the original
6. Do NOT remove any sections from the original
7. Do NOT change the overall visual structure

OPTIMIZATION FOCUS:
- Inject relevant keywords from the job description naturally
- Strengthen action verbs
- Add quantifiable metrics where appropriate
- Ensure skills mentioned in the job description appear in the resume
- Make sure job titles and experience align with the target role

OUTPUT:
Return the optimized resume maintaining the EXACT SAME FORMAT as the original."""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Optimize this resume for the following job while STRICTLY PRESERVING the original format and structure.

JOB DESCRIPTION:
{req.job_description}

ORIGINAL RESUME FORMAT TYPE: {resume_format}

ORIGINAL RESUME CONTENT:
{original_resume}

INSTRUCTIONS:
1. Keep the EXACT same section order and structure
2. Preserve all formatting (headers, bullet points, date formats)
3. Only modify content to add relevant keywords from the job description
4. Strengthen action verbs and add metrics where possible
5. Ensure the optimized resume looks structurally identical to the original

Return the optimized resume in the same format as the original."""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"optimized_resume": response, "original_format": resume_format}
    except Exception as e:
        logger.error(f"Resume optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to optimize resume")

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
    
    skills = ", ".join(profile.get("skills", [])) if profile else "Not specified"
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
    
    skills = ", ".join(profile.get("skills", [])) if profile else "Not specified"
    
    prompt = f"""Create comprehensive interview preparation for:

POSITION: {req.job_title} at {req.company}

JOB DESCRIPTION:
{req.job_description}

CANDIDATE SKILLS: {skills}

Please provide:
1. **Common Interview Questions** (10 questions with suggested answers)
2. **Technical Questions** (if applicable, based on job description)
3. **Behavioral Questions** (with STAR method examples)
4. **Questions to Ask the Interviewer** (5 thoughtful questions)
5. **Company Research Tips** (what to research about {req.company})
6. **Quick Tips** (confidence boosters, body language, etc.)

Format as clear sections with bullet points."""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"prep_materials": response}
    except Exception as e:
        logger.error(f"Interview prep error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate interview prep")

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
    
    application = {
        "application_id": f"app_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "job_id": req.job_id,
        "job_title": req.job_title,
        "company": req.company,
        "location": req.location,
        "job_description": req.job_description,
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

async def auto_submit_greenhouse(app_data: Dict, user_data: Dict, profile_data: Dict) -> Dict:
    """
    Use Playwright to auto-submit a Greenhouse application.
    Returns dict with 'success', 'message', and optional 'error' keys.
    """
    apply_link = app_data.get("apply_link", "")
    
    if not apply_link or "greenhouse.io" not in apply_link.lower():
        return {"success": False, "message": "Not a Greenhouse application link"}
    
    # Parse user data
    full_name = user_data.get("name", "")
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    email = user_data.get("email", "")
    
    # Get contact info from profile
    phone = profile_data.get("phone_number", "")
    linkedin = profile_data.get("linkedin_url", "")
    
    # Get resume and cover letter
    resume_text = app_data.get("optimized_resume") or profile_data.get("resume_text", "")
    cover_letter = app_data.get("cover_letter", "")
    
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to application page
                await page.goto(apply_link, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # Wait for form to load
                
                # Check for CAPTCHA or login requirement
                page_content = await page.content()
                if "captcha" in page_content.lower() or "recaptcha" in page_content.lower():
                    await browser.close()
                    return {
                        "success": False,
                        "message": "CAPTCHA detected - please apply manually",
                        "error": "CAPTCHA_REQUIRED"
                    }
                
                if "sign in" in page_content.lower() or "log in" in page_content.lower():
                    await browser.close()
                    return {
                        "success": False,
                        "message": "Login required - please apply manually",
                        "error": "LOGIN_REQUIRED"
                    }
                
                # Fill first name
                first_name_selectors = [
                    'input[name="first_name"]',
                    'input[name="firstName"]',
                    'input[id*="first_name"]',
                    'input[autocomplete="given-name"]'
                ]
                filled_first_name = False
                for selector in first_name_selectors:
                    try:
                        await page.fill(selector, first_name, timeout=2000)
                        filled_first_name = True
                        break
                    except:
                        continue
                
                # Fill last name
                last_name_selectors = [
                    'input[name="last_name"]',
                    'input[name="lastName"]',
                    'input[id*="last_name"]',
                    'input[autocomplete="family-name"]'
                ]
                filled_last_name = False
                for selector in last_name_selectors:
                    try:
                        await page.fill(selector, last_name, timeout=2000)
                        filled_last_name = True
                        break
                    except:
                        continue
                
                # Fill email
                email_selectors = [
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[id*="email"]',
                    'input[autocomplete="email"]'
                ]
                filled_email = False
                for selector in email_selectors:
                    try:
                        await page.fill(selector, email, timeout=2000)
                        filled_email = True
                        break
                    except:
                        continue
                
                # Fill phone number (if provided)
                if phone:
                    phone_selectors = [
                        'input[name="phone"]',
                        'input[type="tel"]',
                        'input[id*="phone"]',
                        'input[autocomplete="tel"]'
                    ]
                    for selector in phone_selectors:
                        try:
                            await page.fill(selector, phone, timeout=2000)
                            break
                        except:
                            continue
                
                # Fill LinkedIn URL (if provided)
                if linkedin:
                    linkedin_selectors = [
                        'input[name="linkedin"]',
                        'input[name="linkedin_url"]',
                        'input[id*="linkedin"]',
                        'input[placeholder*="linkedin" i]'
                    ]
                    for selector in linkedin_selectors:
                        try:
                            await page.fill(selector, linkedin, timeout=2000)
                            break
                        except:
                            continue
                
                # Fill resume/cover letter if there are textareas
                textarea_count = await page.locator('textarea').count()
                if textarea_count > 0 and (resume_text or cover_letter):
                    # Try to fill the first textarea with cover letter or resume
                    try:
                        content_to_fill = cover_letter if cover_letter else resume_text[:2000]
                        await page.locator('textarea').first.fill(content_to_fill, timeout=2000)
                    except:
                        pass
                
                # Check if basic fields were filled
                if not (filled_first_name and filled_last_name and filled_email):
                    await browser.close()
                    return {
                        "success": False,
                        "message": "Could not find required form fields - form structure may have changed",
                        "error": "FORM_NOT_FOUND"
                    }
                
                # Take screenshot before submission for debugging
                await page.screenshot(path="/tmp/before_submit.png")
                
                # Look for submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Submit Application")',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    '#submit_app'
                ]
                
                clicked_submit = False
                for selector in submit_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        clicked_submit = True
                        break
                    except:
                        continue
                
                if not clicked_submit:
                    await browser.close()
                    return {
                        "success": False,
                        "message": "Could not find submit button - please complete manually",
                        "error": "SUBMIT_BUTTON_NOT_FOUND"
                    }
                
                # Wait for navigation or success message
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(2)
                    
                    # Check for success indicators
                    page_content = await page.content()
                    success_keywords = ["thank you", "success", "submitted", "received your application"]
                    
                    is_success = any(keyword in page_content.lower() for keyword in success_keywords)
                    
                    if is_success:
                        await browser.close()
                        return {
                            "success": True,
                            "message": "Application submitted successfully via automation"
                        }
                    else:
                        await browser.close()
                        return {
                            "success": False,
                            "message": "Submission may have failed - please verify manually",
                            "error": "UNCERTAIN_STATUS"
                        }
                
                except PlaywrightTimeout:
                    await browser.close()
                    return {
                        "success": False,
                        "message": "Submission timed out - please verify manually",
                        "error": "TIMEOUT"
                    }
            
            finally:
                await browser.close()
    
    except Exception as e:
        logger.error(f"Playwright automation error: {str(e)}")
        return {
            "success": False,
            "message": f"Automation error: {str(e)}",
            "error": "PLAYWRIGHT_ERROR"
        }

@api_router.post("/applications/{application_id}/auto-submit")
async def auto_submit_application(request: Request, application_id: str):
    """
    Automatically submit an approved application using Playwright.
    Only works for Greenhouse applications.
    """
    user = await get_current_user(request)
    
    # Get application
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if already submitted
    if app_doc.get("status") == "applied":
        return {
            "success": False,
            "message": "Application already submitted"
        }
    
    # Check rate limiting (1 submission per 5 minutes per user)
    recent_submissions = await db.applications.count_documents({
        "user_id": user.user_id,
        "status": "applied",
        "applied_at": {"$gte": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()}
    })
    
    if recent_submissions >= 1:
        raise HTTPException(
            status_code=429,
            detail="Rate limit: Please wait 5 minutes between automated submissions"
        )
    
    # Get user profile and data
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Attempt auto-submission
    result = await auto_submit_greenhouse(app_doc, user_doc, profile or {})
    
    if result["success"]:
        # Update status to applied
        await db.applications.update_one(
            {"application_id": application_id},
            {"$set": {
                "status": "applied",
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "auto_submitted": True
            }}
        )
        
        updated = await db.applications.find_one(
            {"application_id": application_id},
            {"_id": 0}
        )
        
        return {
            "success": True,
            "message": result["message"],
            "application": updated
        }
    else:
        # Return error with fallback link
        return {
            "success": False,
            "message": result["message"],
            "error": result.get("error"),
            "fallback_link": app_doc.get("apply_link")
        }

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

def create_docx_from_text(text: str, title: str = None) -> io.BytesIO:
    """Create a DOCX file from text content."""
    doc = Document()
    
    # Add title if provided
    if title:
        doc.add_heading(title, 0)
    
    # Split text by newlines and add paragraphs
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para)
    
    # Save to BytesIO
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

@api_router.get("/applications/{application_id}/download/resume")
async def download_resume_docx(request: Request, application_id: str):
    """Download optimized resume as DOCX file."""
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("optimized_resume"):
        raise HTTPException(status_code=400, detail="No optimized resume found for this application")
    
    # Create DOCX file
    company = app_doc.get("company", "Company").replace(" ", "_")
    job_title = app_doc.get("job_title", "Position").replace(" ", "_")
    filename = f"Resume_{company}_{job_title}.docx"
    
    buffer = create_docx_from_text(app_doc["optimized_resume"])
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/applications/{application_id}/download/cover-letter")
async def download_cover_letter_docx(request: Request, application_id: str):
    """Download cover letter as DOCX file."""
    user = await get_current_user(request)
    
    app_doc = await db.applications.find_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app_doc.get("cover_letter"):
        raise HTTPException(status_code=400, detail="No cover letter found for this application")
    
    # Create DOCX file
    company = app_doc.get("company", "Company").replace(" ", "_")
    job_title = app_doc.get("job_title", "Position").replace(" ", "_")
    filename = f"Cover_Letter_{company}_{job_title}.docx"
    
    buffer = create_docx_from_text(app_doc["cover_letter"])
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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
async def get_autofill_data(request: Request, url: str = None):
    """Get user data for bookmarklet auto-fill. Matches by job URL or returns latest approved application."""
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
    
    # Parse name
    full_name = user_doc.get("name", "") if user_doc else ""
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    email = user_doc.get("email", "") if user_doc else ""
    phone = profile.get("phone", "") if profile else ""
    linkedin = profile.get("linkedin", "") if profile else ""
    
    # Try to find matching application by URL
    app_doc = None
    if url:
        # Try to match by apply_link
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
        "linkedin": linkedin,
        "resume": resume_text,
        "coverLetter": cover_letter,
        "jobTitle": job_title,
        "company": company,
        "hasApplication": app_doc is not None
    }

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
# HEALTH CHECK
# ========================

@api_router.get("/")
async def root():
    return {"message": "JobMatch AI API", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include the router
app.include_router(api_router)

# Get frontend URL for CORS - no hardcoded fallback for production safety
FRONTEND_URL = os.environ.get('CORS_ORIGINS')
if not FRONTEND_URL:
    raise ValueError("CORS_ORIGINS environment variable is required")
origins = [origin.strip() for origin in FRONTEND_URL.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
