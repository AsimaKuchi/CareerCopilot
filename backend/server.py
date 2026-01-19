from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, UploadFile, File
from fastapi.responses import JSONResponse
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
    
    # 3. Experience Level (max +15 points)
    user_years = profile.get("experience_years", 0)
    user_seniority = profile.get("seniority_level", "").lower()
    
    # Detect job seniority from title/description
    job_seniority = "mid"
    if any(word in job_title for word in ["senior", "sr.", "lead", "principal"]):
        job_seniority = "senior"
    elif any(word in job_title for word in ["junior", "jr.", "entry", "associate", "graduate"]):
        job_seniority = "junior"
    elif any(word in job_title for word in ["director", "head", "vp", "chief", "manager"]):
        job_seniority = "director"
    
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
    elif job_seniority == "director" and user_years >= 8:
        seniority_match = True
        strengths.append(f"With {user_years}+ years in the field, you have the leadership experience required for this {job_title_display} position")
        score += 15
    
    if not seniority_match:
        if job_seniority == "senior" and user_years < 5:
            gaps.append(f"Role requires more experience ({job_seniority} level)")
            if user_years < 3:
                skip_reasons.append("Role is significantly above your experience level")
        elif job_seniority == "director" and user_years < 8:
            gaps.append("This is a leadership role requiring extensive experience")
            skip_reasons.append("Role requires leadership experience you may not have")
    
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
    
    # 5. Industry Match (max +10 points)
    industries = [ind.lower() for ind in profile.get("industries", [])]
    open_to_any = profile.get("open_to_any_industry", False)
    
    if open_to_any:
        score += 10
    elif industries:
        industry_keywords = {
            "technology": ["tech", "software", "saas", "startup", "digital"],
            "finance": ["bank", "financial", "fintech", "investment", "insurance"],
            "healthcare": ["health", "medical", "pharma", "biotech", "hospital"],
            "retail": ["retail", "ecommerce", "consumer", "shopping"],
            "manufacturing": ["manufacturing", "industrial", "production"],
            "consulting": ["consulting", "advisory", "professional services"],
        }
        
        for ind in industries:
            keywords = industry_keywords.get(ind, [ind])
            if any(kw in job_desc for kw in keywords):
                strengths.append(f"Industry aligns with your preference: {ind}")
                score += 10
                break
        else:
            if industries:
                gaps.append("Industry may not match your selected preferences")
    
    # 6. Work Authorization Check (Canada-focused)
    work_auth = profile.get("work_authorization", "")
    if work_auth == "require_sponsorship":
        # Check if job mentions no sponsorship available
        sponsorship_blockers = [
            "no sponsorship", "must be authorized", "no visa", 
            "canadian citizen", "permanent resident only", "pr only",
            "must have valid work permit", "no lmia"
        ]
        if any(blocker in job_desc for blocker in sponsorship_blockers):
            skip_reasons.append("Role does not offer work permit sponsorship")
    
    # 7. Salary Check (max +5 points)
    job_min_salary = job.get("job_min_salary")
    job_max_salary = job.get("job_max_salary")
    user_min_salary = profile.get("salary_min")
    
    if job_min_salary and user_min_salary:
        if job_min_salary >= user_min_salary:
            strengths.append("Salary range meets your minimum")
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
        match_reasoning = "Strong match - aligns well with your profile"
    elif score >= 60:
        recommendation = "good_match"
        match_reasoning = "Good match - worth reviewing"
    elif score >= 45:
        recommendation = "review"
        match_reasoning = "Potential match - review carefully for fit"
    else:
        recommendation = "weak_match"
        match_reasoning = "Weak match - may not align with your goals"
    
    return {
        "score": score,
        "recommendation": recommendation,
        "strengths": strengths[:4],  # Limit to top 4
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
