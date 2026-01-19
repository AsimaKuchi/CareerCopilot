# JobMatch AI - Product Requirements Document

## Original Problem Statement
Build a website that helps users find jobs best suited for them based on what info they provide and automatically applies to them based off their approval. Also optimizes resumes to ATS standard based off each job, using their resume. Make a cover letter for each job and interview tips and prep.

## User Choices
- **AI Provider**: OpenAI GPT-5.2 (via Emergent Universal Key)
- **Job Data Source**: JSearch API (RapidAPI)
- **Authentication**: Google Social Login (Emergent OAuth)
- **Design**: Eye-catching dark theme with glassmorphism

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

## User Personas
1. **Job Seekers** - Entry to mid-career professionals looking to streamline their job search
2. **Career Changers** - People transitioning to new industries
3. **Busy Professionals** - Those who need efficient application management

## Core Requirements (Static)
1. ✅ User authentication via Google OAuth
2. ✅ Profile management with resume upload
3. ✅ AI-powered job matching from real job listings
4. ✅ ATS resume optimization
5. ✅ AI cover letter generation
6. ✅ Interview preparation materials
7. ✅ Application tracking with approval workflow

## What's Been Implemented (January 19, 2025)

### MVP Features ✅
- **Landing Page**: Hero section, features showcase, CTAs with dark glassmorphism design
- **Google Auth**: Full OAuth flow with session management
- **Dashboard**: Stats cards, quick actions, profile completion guide
- **Profile Page**: Resume upload, skills management, job preferences, salary expectations
- **Job Search**: Real-time search via JSearch API with AI match scores
- **Applications**: Create, approve, reject, delete applications with status tracking
- **AI Features**:
  - Resume ATS optimization (GPT-5.2)
  - Cover letter generation (GPT-5.2)
  - Interview prep materials (GPT-5.2)

### Backend API Endpoints
- `POST /api/auth/session` - Exchange session_id for session_token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user
- `GET/PUT /api/profile` - Profile management
- `POST /api/profile/resume` - Resume upload
- `POST /api/jobs/search` - Search jobs with match scoring
- `POST /api/ai/optimize-resume` - ATS optimization
- `POST /api/ai/cover-letter` - Generate cover letter
- `POST /api/ai/interview-prep` - Generate interview prep
- `GET/POST /api/applications` - Application CRUD
- `PUT /api/applications/{id}/approve` - Approve application
- `PUT /api/applications/{id}/reject` - Reject application
- `GET /api/dashboard/stats` - Dashboard statistics

## Prioritized Backlog

### P0 - Critical (Blocking)
- None currently

### P1 - High Priority
- [ ] Auto-apply integration (submit applications programmatically)
- [ ] PDF resume parsing
- [ ] Email notifications for new job matches

### P2 - Medium Priority
- [ ] Saved job searches
- [ ] Multiple resume versions
- [ ] Application notes and reminders
- [ ] Job alerts/notifications

### P3 - Nice to Have
- [ ] LinkedIn integration
- [ ] Company research panel
- [ ] Salary negotiation tips
- [ ] Video interview practice

## Next Tasks
1. Add PDF resume parsing for better resume extraction
2. Implement email notifications for job matches
3. Add saved searches functionality
4. Consider actual auto-apply integration with job boards

## Test Results
- Backend: 92.3% success rate
- Frontend: All pages loading correctly
- AI Features: Cover letter, interview prep, resume optimization all working
- Job Search: Real-time results from JSearch API with match scoring
