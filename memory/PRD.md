# JobMatch AI - Product Requirements Document

## Original Problem Statement
Build a website that helps users find jobs best suited for them based on what info they provide and automatically applies to them based off their approval. Also optimizes resumes to ATS standard based off each job, using their resume. Make a cover letter for each job and interview tips and prep.

## Core Principles (Quality-First)
- **Quality over volume**: Focus on high-quality, relevant job matches
- **Human-in-the-loop**: Users must review and approve every application before it's sent
- **Transparency**: System explains why jobs are recommended or skipped
- **Intelligent evaluation**: Roles evaluated based on relevance, industry, seniority, location, work authorization, and skill overlap

## User Choices
- **AI Provider**: OpenAI GPT-5.2 (via Emergent Universal Key)
- **Job Data Source**: JSearch API (RapidAPI) + Greenhouse (planned)
- **Authentication**: Google Social Login (Emergent OAuth)
- **Design**: Light theme with glassmorphism

## Architecture

### Tech Stack
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via emergentintegrations
- **Job API**: JSearch (RapidAPI)
- **Auth**: Emergent Google OAuth

### Key Files
```
/app/backend/server.py          # Main API endpoints
/app/frontend/src/App.js        # Main React app with routing
/app/frontend/src/pages/        # All page components
/app/frontend/src/components/   # Shared components (Navbar)
```

## What's Been Implemented (January 19, 2025)

### MVP Features ✅
- **Landing Page**: Hero section, features showcase, CTAs with light theme
- **Google Auth**: Full OAuth flow with session management
- **Dashboard**: Stats cards, quick actions, profile completion guide
- **Profile Page**: 
  - Resume upload (PDF, DOCX, TXT)
  - Skills management
  - Job preferences
  - Salary expectations
  - **NEW**: Work Authorization (citizen, permanent_resident, work_permit, require_sponsorship)
  - **NEW**: Target Industries (max 3, with "open to any" option)
  - **NEW**: Seniority Level (entry, junior, mid, senior, lead, manager, director, executive)
- **Job Search**: 
  - Real-time search via JSearch API
  - **NEW**: Detailed match evaluation with:
    - Match score (0-100%)
    - Match recommendation (strong_match, good_match, review, weak_match, skip)
    - Strengths list
    - Gaps list
    - Match reasoning explanation
    - Skip reason (for not recommended jobs)
  - Expandable match analysis on job cards
  - Grayed out "skip" recommended jobs with disabled apply button
- **Applications**: Create, approve, reject, delete with status tracking
- **AI Features**:
  - Resume ATS optimization (GPT-5.2)
  - Cover letter generation (GPT-5.2)
  - Interview prep materials (GPT-5.2)

### Backend API Endpoints
- `POST /api/auth/session` - Exchange session_id for session_token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user
- `GET/PUT /api/profile` - Profile management (includes new fields)
- `POST /api/profile/resume` - Resume upload
- `POST /api/jobs/search` - Search jobs with detailed match evaluation
- `POST /api/ai/optimize-resume` - ATS optimization
- `POST /api/ai/cover-letter` - Generate cover letter
- `POST /api/ai/interview-prep` - Generate interview prep
- `GET/POST /api/applications` - Application CRUD
- `PUT /api/applications/{id}/approve` - Approve application
- `PUT /api/applications/{id}/reject` - Reject application
- `GET /api/dashboard/stats` - Dashboard statistics

## Match Evaluation Algorithm
The job matching evaluates candidates against jobs using:
1. **Role Relevance** (+25 points): Title alignment with target positions
2. **Skills Match** (+20 points): Ratio of matching skills in job description
3. **Experience Level** (+15 points): Seniority alignment (junior/mid/senior/director)
4. **Location Match** (+15 points): Preferred locations or remote availability
5. **Industry Match** (+10 points): Target industries or "open to any"
6. **Work Authorization Check**: Filters jobs requiring sponsorship if user needs it
7. **Salary Check** (+5 points): Salary range meets minimum requirement

## Prioritized Backlog

### P0 - Critical (Completed ✅)
- ✅ Quality-First job matching with detailed evaluation
- ✅ Work authorization filter
- ✅ Industry and seniority matching

### P1 - High Priority (Next)
- [ ] Greenhouse job sourcing (scrape job-boards.greenhouse.io)
- [ ] Interview Tips & Prep feature completion
- [ ] Email notifications for new job matches

### P2 - Medium Priority
- [ ] Auto-apply integration (submit to Greenhouse after approval)
- [ ] Saved job searches
- [ ] Multiple resume versions
- [ ] Application notes and reminders

### P3 - Nice to Have
- [ ] LinkedIn integration
- [ ] Company research panel
- [ ] Salary negotiation tips
- [ ] Video interview practice

## Test Results (Latest: iteration_3.json - January 25, 2025)
- **Backend**: 100% success rate (8/8 tests passed)
- **Frontend**: All UI flows verified
- **Fixed P0 Bug**: "Business analyst" in "Toronto" search returning 0 results on Quality Sources
  - Root cause: `performFallbackSearch` function in JobSearch.jsx was calling `/api/jobs/search` (JSearch aggregator) instead of `/api/jobs/greenhouse/search` (streaming Greenhouse/Lever endpoint)
  - Fix: Changed line 259 in JobSearch.jsx to use correct endpoint
  - Verification: Fallback now correctly returns 16+ related analyst jobs when strict search returns 0

## Database Schema

### users
- user_id: string
- email: string
- name: string
- picture: string (optional)
- created_at: datetime

### user_profiles
- user_id: string
- resume_text: string (optional)
- resume_filename: string (optional)
- resume_format: string (optional)
- skills: array[string]
- experience_years: int
- job_titles: array[string]
- preferred_locations: array[string]
- salary_min: int (optional)
- salary_max: int (optional)
- job_type: array[string]
- work_authorization: string (optional) - citizen, permanent_resident, work_permit, require_sponsorship
- industries: array[string] - max 3
- open_to_any_industry: boolean
- seniority_level: string (optional) - entry, junior, mid, senior, lead, manager, director, executive
- updated_at: datetime

### applications
- application_id: string
- user_id: string
- job_id: string
- job_title: string
- company: string
- location: string (optional)
- job_description: string
- optimized_resume: string (optional)
- cover_letter: string (optional)
- status: string - pending, approved, applied, rejected
- match_score: int
- created_at: datetime
- applied_at: datetime (optional)
