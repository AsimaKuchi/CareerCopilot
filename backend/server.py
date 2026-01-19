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
    skills: List[str] = []
    experience_years: int = 0
    job_titles: List[str] = []
    preferred_locations: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: List[str] = []  # full-time, part-time, contract, remote
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfileUpdate(BaseModel):
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    job_titles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[List[str]] = None

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
        
        # Get user profile for matching
        profile = await db.user_profiles.find_one(
            {"user_id": user.user_id},
            {"_id": 0}
        )
        
        # Calculate match scores
        enriched_jobs = []
        for job in jobs:
            match_score = calculate_match_score(job, profile)
            enriched_jobs.append({
                "job_id": job.get("job_id"),
                "title": job.get("job_title"),
                "company": job.get("employer_name"),
                "company_logo": job.get("employer_logo"),
                "location": job.get("job_city", "") + (", " + job.get("job_state", "") if job.get("job_state") else ""),
                "employment_type": job.get("job_employment_type"),
                "description": job.get("job_description", "")[:500] + "...",
                "full_description": job.get("job_description"),
                "apply_link": job.get("job_apply_link"),
                "posted_at": job.get("job_posted_at_datetime_utc"),
                "salary_min": job.get("job_min_salary"),
                "salary_max": job.get("job_max_salary"),
                "salary_currency": job.get("job_salary_currency"),
                "is_remote": job.get("job_is_remote"),
                "match_score": match_score,
                "highlights": job.get("job_highlights", {})
            })
        
        # Sort by match score
        enriched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "jobs": enriched_jobs,
            "total": len(enriched_jobs)
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Job search timed out")
    except Exception as e:
        logger.error(f"Job search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_match_score(job: Dict, profile: Optional[Dict]) -> int:
    """Calculate job match score based on user profile."""
    if not profile:
        return 50  # Default score
    
    score = 50  # Base score
    
    job_title = job.get("job_title", "").lower()
    job_desc = job.get("job_description", "").lower()
    
    # Match job titles
    for title in profile.get("job_titles", []):
        if title.lower() in job_title:
            score += 20
            break
    
    # Match skills
    skills = profile.get("skills", [])
    matched_skills = 0
    for skill in skills:
        if skill.lower() in job_desc:
            matched_skills += 1
    
    if skills:
        skill_match_ratio = matched_skills / len(skills)
        score += int(skill_match_ratio * 20)
    
    # Match location
    job_location = (job.get("job_city", "") + " " + job.get("job_state", "")).lower()
    for loc in profile.get("preferred_locations", []):
        if loc.lower() in job_location:
            score += 10
            break
    
    # Remote preference
    if job.get("job_is_remote") and "remote" in profile.get("job_type", []):
        score += 10
    
    return min(score, 100)

# ========================
# AI ROUTES
# ========================

@api_router.post("/ai/optimize-resume")
async def optimize_resume(request: Request, req: OptimizeResumeRequest):
    """Optimize resume for ATS based on job description."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile or not profile.get("resume_text"):
        raise HTTPException(status_code=400, detail="Please upload your resume first")
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"resume_opt_{user.user_id}_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert ATS (Applicant Tracking System) resume optimizer. 
Your job is to optimize resumes to pass ATS scans while maintaining authenticity.
Focus on:
1. Keyword optimization from the job description
2. Proper formatting for ATS parsing
3. Quantifiable achievements
4. Action verbs
5. Relevant skills alignment
Return the optimized resume in a clean, ATS-friendly format."""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Please optimize this resume for the following job:

JOB DESCRIPTION:
{req.job_description}

CURRENT RESUME:
{profile['resume_text']}

Provide the optimized resume with:
1. ATS-optimized keywords
2. Relevant skills highlighted
3. Achievements quantified where possible
4. Clean, parseable format"""
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"optimized_resume": response}
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
        "optimized_resume": None,
        "cover_letter": None,
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

# Get frontend URL for CORS
FRONTEND_URL = os.environ.get('CORS_ORIGINS', 'https://job-match-pilot.preview.emergentagent.com')
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
