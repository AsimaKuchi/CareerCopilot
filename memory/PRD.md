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
- **Canadian Job Coverage**: Jobs from USA and Canada for all major sources (COMPLETE - Mar 8, 2026)

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

*JSearch API rate limits prevent Canadian job fetch - code is ready but depends on API availability

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
- **Canadian Job Coverage** (Mar 8, 2026) - COMPLETE

## Canadian Job Coverage (Mar 8, 2026) - COMPLETE

### Implementation:
- **Amazon Jobs API**: Updated `fetch_amazon_jobs()` to fetch from both `"USA"` and `"CAN"` countries
- **JSearch API**: Updated `fetch_company_jobs_via_jsearch()` to query both `"US"` and `"CA"` countries
- JSearch queries include Canada-specific search terms (`"Microsoft jobs Canada"`)

### Results:
- **Total Jobs**: 13,094 (increased from ~12,989)
- **Canadian Jobs**: 1,126 total
  - Amazon: 105 Canadian jobs
  - Greenhouse: 964 Canadian jobs
  - Lever: 57 Canadian jobs
- **Canadian Cities Covered**: Toronto (424 jobs), Vancouver (141 jobs), and more

### Test Results (iteration_20.json):
- Backend: 100% (15/15 tests passed)
- Amazon correctly fetches from both USA and CAN
- Canadian jobs stored with location format: `CA, ON, Toronto`

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs, /api/public/sources, /api/public/jobs/ingest
- Search: /api/jobs/greenhouse/search
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx, /api/ai/interview-prep
- Analytics: /api/analytics/company-search

## Database Schema
- **stored_jobs**: Contains `description`, `posted_at_dt`, `location` (supports Canadian cities)
- **user_saved_jobs**: User's saved job results with descriptions
- **search_analytics**: Tracks company filter usage

## Prioritized Backlog

### P0: Refactor Monolithic Backend (URGENT)
- `backend/server.py` is 8738+ lines and becoming unmanageable
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
- **JSearch API (RapidAPI)**: Requires User API Key - rate limited on free tier
- **Resend**: Transactional emails
- **Google OAuth**: Authentication
- **python-docx**: Document generation
- **BeautifulSoup4**: HTML parsing
- **python-dateutil**: Date parsing

## Files Modified (Mar 8, 2026)
- `/app/backend/server.py` - Updated `fetch_amazon_jobs()` and `fetch_company_jobs_via_jsearch()` for Canada
- `/app/frontend/src/pages/InterviewPrep.jsx` - Q&A formatting
- `/app/frontend/src/utils/extractSalary.js` - Salary extraction utility
- `/app/frontend/src/utils/formatJobDescription.js` - Description formatting utility
- `/app/frontend/src/components/FormattedJobDescription.jsx` - Formatted description component
