"""
models.py - Pydantic schemas for MyCareerCopilot backend.

All request/response and document models are defined here so route
modules can import them without duplication. Refactored from
monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid

from pydantic import BaseModel, Field, ConfigDict, EmailStr


# ============================================================
# CORE USER & PROFILE MODELS
# ============================================================
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "user"  # "user" or "admin"
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
    skills: List[Any] = []  # List[str] or List[Skill]
    experience_years: int = 0
    job_titles: List[str] = []
    preferred_locations: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: List[str] = []  # full-time, part-time, contract, remote
    work_authorization: Optional[str] = None
    industries: List[str] = []
    open_to_any_industry: bool = False
    seniority_level: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    highest_education: Optional[str] = None
    current_company: Optional[str] = None
    willing_to_relocate: Optional[str] = None
    notice_period: Optional[str] = None
    referral_source: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    application_intensity: str = "balanced"
    daily_applications_count: int = 0
    last_application_date: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProfileUpdate(BaseModel):
    skills: Optional[List[Any]] = None
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
    current_company: Optional[str] = None
    willing_to_relocate: Optional[str] = None
    notice_period: Optional[str] = None
    referral_source: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    application_intensity: Optional[str] = None
    preferred_work_arrangement: Optional[str] = None


# ============================================================
# JOB APPLICATION MODELS
# ============================================================
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
    next_steps_progress: Optional[Dict[str, Any]] = None


class NextStepUpdate(BaseModel):
    """Update a single next step's completion status or data."""
    step_id: str  # follow_company, find_recruiter, send_message, prep_interview, track_outcome, follow_up
    completed: Optional[bool] = None
    outcome: Optional[str] = None
    reminder_date: Optional[str] = None


class NextStepContentRequest(BaseModel):
    """Request to generate AI content for a next step."""
    step_id: str  # send_message or prep_interview
    content_type: Optional[str] = None


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
    # Optional: list of previously-seen question texts so the AI can avoid
    # repeating them when the user regenerates for more variety.
    excluded_questions: Optional[List[str]] = None
    # Optional variation style: "default", "behavioral", "technical", "leadership",
    # "edge_cases" -- used to bias the regenerated batch towards a theme.
    variation: Optional[str] = None


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
    comparison_json: Dict[str, Any]
    personal_notes: Optional[str] = None
    status: str = "complete"
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


# ============================================================
# AUTH MODELS
# ============================================================
class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# ============================================================
# AI MODELS
# ============================================================
class DetailedMatchRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str


class DocxDownloadRequest(BaseModel):
    content: str
    doc_type: str  # "resume" or "cover_letter"
    job_title: Optional[str] = ""
    company: Optional[str] = ""


# ============================================================
# AUTOFILL / EXTENSION MODELS
# ============================================================
class AutoFillRequest(BaseModel):
    submit_form: bool = False


class ScreeningAnswersUpdate(BaseModel):
    answers: dict  # {question_id: answer_value}


class CustomQuestionAdd(BaseModel):
    question: str
    answer: str
    keywords: List[str] = []


class AnswerQuestionsRequest(BaseModel):
    questions: List[dict]  # [{question, options?}]
