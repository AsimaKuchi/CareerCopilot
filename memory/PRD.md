# MyCareerCoPilot - Product Requirements Document

## Original Problem Statement
Build a browser extension that auto-fills job application forms using a central user profile. Evolved into a full-featured web application for career management named "MyCareerCoPilot".

## Core Features

### Browser Extension
- Autofill forms universally on any job site (Manifest V3, `<all_urls>`)
- Automatically track application submissions

### Web Application
- **Dashboard**: Track applications, show stats, display saved jobs with formatted descriptions and extracted salaries
- **Profile Management**: Multi-select skills, AI resume-to-profile pre-fill
- **Job Search**: Find jobs from multiple sources with company filter and formatted descriptions
- **Authentication**: Google OAuth + email/password with verification/reset
- **AI Career Paths**: Analyze profile/resume, suggest career paths, find matching jobs
- **AI Documents**: Optimized resume + cover letter with .docx download
- **Welcome Email**: Sends onboarding email via Resend on signup
- **Formatted Job Descriptions**: Scannable, well-structured job descriptions with headers and bullets
- **Salary Extraction**: Automatically extracts salary from job descriptions when not in structured fields
- **Interview Prep**: AI-generated interview prep with consistent Q&A formatting
- **Canadian Job Coverage**: Jobs from USA and Canada for all major sources
- **Personalized Match Analysis**: AI-powered matching with actual resume evidence (COMPLETE - Mar 8, 2026)

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend, python-docx, python-dateutil, BeautifulSoup4
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-5.2, GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API, Greenhouse API, Lever API
- **Auth**: Google OAuth + JWT for email/password

## Job Sources (~13,094 jobs)
| Source | Method | USA | Canada | Total |
|--------|--------|-----|--------|-------|
| Greenhouse | Direct API | ~11,000 | ~964 | ~11,957 |
| Lever | Direct API | ~406 | ~57 | ~463 |
| Amazon | amazon.jobs API | ~241 | ~105 | ~346 |
| Microsoft | JSearch API | ~16 | 0* | ~16 |
| Apple | JSearch API | ~21 | 0* | ~21 |

## What's Been Implemented
- Full authentication system (Google OAuth + email/password)
- Universal Chrome extension for any job site
- Dashboard with prioritized job listings
- Profile page with resume-to-profile AI pre-fill
- AI Career Paths page
- Job search with company filter (13 top companies)
- Landing page with company logo carousel
- Welcome email via Resend
- Custom CSS logo "MyCareer CoPilot"
- Branding unified to "MyCareerCoPilot"
- Job sources: Amazon, Microsoft, Apple, Netflix
- Expired job cleanup + auto refresh scheduler
- Company filter with analytics tracking
- Word document (.docx) download for AI-optimized resumes and cover letters
- Full Job Descriptions Feature (expandable on Dashboard and Job Search)
- Formatted Job Descriptions (section headers, bullets, spacing)
- Salary Extraction from Descriptions
- Interview Prep Q&A Formatting
- Canadian Job Coverage
- **Personalized Match Analysis** (Mar 8, 2026) - COMPLETE

## Personalized Match Analysis (Mar 8, 2026) - COMPLETE

### Problem Solved:
- OLD: Generic statements like "Strong role alignment: Your target role matches this position"
- NEW: Specific, evidence-based insights using actual resume text

### Implementation:
- **Backend**: Enhanced `evaluate_job_match()` function in server.py
- **New Fields**:
  - `grounded_strengths[]`: Array with {requirement, evidence, match_reason}
  - `matched_skills[]`: List of specific skills that match job requirements
  - `evidence`: Actual snippets from user's resume (10-word context around matched keywords)

### Example Output:
```json
{
  "grounded_strengths": [
    {
      "requirement": "Requires SQL",
      "evidence": "Developed SQL queries and Python scripts to automate monthly reporting, saving 40 hours per month",
      "match_reason": "Your resume demonstrates hands-on experience with SQL"
    },
    {
      "requirement": "Job requires Python",
      "evidence": "Created 15+ Tableau dashboards and Python automation scripts for executive leadership",
      "match_reason": "Your Python experience matches job requirements"
    }
  ],
  "matched_skills": ["SQL", "Python", "Tableau", "Data Analysis", "Project Management"],
  "score": 76
}
```

### Test Results (iteration_21.json):
- Backend: 100% (9/9 tests passed)
- Frontend: 100% - Analyze Match dialog displays personalized insights
- Bug fixed: grounded_strengths was computed but not passed through to job responses (fixed in 4 locations)

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs, /api/public/sources, /api/public/jobs/ingest
- Search: /api/jobs/greenhouse/search (includes match analysis)
- Match: /api/jobs/{job_id}/compare (GPT-powered detailed analysis)
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx, /api/ai/interview-prep
- Analytics: /api/analytics/company-search

## Database Schema
- **stored_jobs**: Contains `description`, `posted_at_dt`, `location`
- **user_saved_jobs**: User's saved job results with descriptions
- **user_profiles**: Resume text, skills, job titles, experience years
- **search_analytics**: Tracks company filter usage

## Prioritized Backlog

### P0: Refactor Monolithic Backend (URGENT)
- `backend/server.py` is 8842+ lines and becoming unmanageable
- Must break into structured FastAPI application:
  - routes/ (API routers by domain)
  - models/ (Pydantic models)
  - services/ (business logic)
  - utils/ (helpers)
- Critical for maintainability and scalability

### P2: Enhance Extension Dropdown Matching
- Improve universal extension logic for complex dropdown scenarios

### P3: Fine-tune Extension for Lever/Ashby
- Add platform-specific logic for better reliability

### Future
- "Follow Company" feature
- Store company filter in user preferences
- Persist last-used company filter
- Save Interview Prep Materials

## 3rd Party Integrations
- **OpenAI (GPT-5.2, GPT-4o, GPT-4o-mini)**: Uses Emergent LLM Key
- **JSearch API (RapidAPI)**: Requires User API Key
- **Resend**: Transactional emails
- **Google OAuth**: Authentication
- **python-docx**: Document generation
- **BeautifulSoup4**: HTML parsing
- **python-dateutil**: Date parsing

## Files Modified (Mar 8, 2026)
- `/app/backend/server.py` - evaluate_job_match() enhanced with grounded_strengths, find_resume_evidence() helper
- `/app/frontend/src/pages/JobSearch.jsx` - Added data-testid to Analyze Match button
- `/app/frontend/src/pages/InterviewPrep.jsx` - Q&A formatting
- `/app/frontend/src/utils/extractSalary.js` - Salary extraction utility
- `/app/frontend/src/utils/formatJobDescription.js` - Description formatting utility
