# MyCareerCoPilot - Product Requirements Document

## Original Problem Statement
Build a browser extension that auto-fills job application forms using a central user profile. Evolved into a full-featured web application for career management named "MyCareerCoPilot".

## Core Features

### Browser Extension
- Autofill forms universally on any job site (Manifest V3, `<all_urls>`)
- Automatically track application submissions

### Web Application
- **Dashboard**: Track applications, show stats like "Time Saved"
- **Profile Management**: Multi-select skills, AI resume-to-profile pre-fill
- **Job Search**: Find jobs from multiple sources with company filter
- **Authentication**: Google OAuth + email/password with verification/reset
- **AI Career Paths**: Analyze profile/resume, suggest career paths, find matching jobs
- **AI Documents**: Optimized resume + cover letter with .docx download
- **Welcome Email**: Sends onboarding email via Resend on signup
- **Full Job Descriptions**: Expandable job descriptions on dashboard (NEW - Mar 7, 2026)

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend, python-docx, python-dateutil, BeautifulSoup4
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API, Greenhouse API, Lever API
- **Auth**: Google OAuth + JWT for email/password

## Job Sources (~12,989 jobs)
| Source | Method | Count |
|--------|--------|-------|
| Greenhouse | Direct API | ~11,957 |
| Lever | Direct API | ~463 |
| Amazon | amazon.jobs JSON API | ~120 |
| Microsoft | JSearch API | ~16 |
| Apple | JSearch API | ~21 |
| Netflix | Lever | 0 (currently) |

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
- **Full Job Descriptions on Dashboard** (Mar 7, 2026) - COMPLETE

## Full Job Description Feature (Mar 7, 2026) - COMPLETE
- Backend: GET /api/public/jobs returns clean, plain-text job descriptions
- All 4 sources (Greenhouse, Lever, Amazon, JSearch) fetch full descriptions
- HTML tags properly stripped using BeautifulSoup
- Jobs sorted by posted_at_dt descending (newest first)
- description_preview field truncated to 300 chars with "..." suffix
- Frontend: Expandable "View Description" button on each job card
- Test Results: 100% pass rate (15/15 tests) - all tests passing

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs, /api/public/sources, /api/public/jobs/ingest
- Search: /api/jobs/greenhouse/search, /api/jobs/search (both with company filter)
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx, /api/ai/interview-prep
- Analytics: /api/analytics/company-search

## Database Schema
- **stored_jobs**: Contains `description` (full plain text) and `posted_at_dt` (standardized datetime for sorting)
- **user_saved_jobs**: User's saved job results from searches
- **search_analytics**: Tracks company filter usage

## Prioritized Backlog

### P0: Refactor Monolithic Backend (URGENT)
- `backend/server.py` is 8736+ lines and becoming unmanageable
- Must break into structured FastAPI application:
  - routes/ (API routers by domain)
  - models/ (Pydantic models)
  - services/ (business logic)
  - utils/ (helpers)
- Critical for maintainability and scalability

### P1: Expand Canadian Job Coverage
- Add Canada as target region for Amazon, Microsoft, Apple jobs
- Update JSearch queries to include Canadian locations

### P2: Enhance Extension Dropdown Matching
- Improve universal extension logic for complex dropdown scenarios

### P3: Fine-tune Extension for Lever/Ashby
- Add platform-specific logic for better reliability

### Future
- "Follow Company" feature
- Store company filter in user preferences
- Persist last-used company filter

## 3rd Party Integrations
- **OpenAI (GPT-4o, GPT-4o-mini)**: Uses Emergent LLM Key
- **JSearch API (RapidAPI)**: Requires User API Key
- **Resend**: Transactional emails
- **Google OAuth**: Authentication
- **python-docx**: Document generation
- **BeautifulSoup4**: HTML parsing
- **python-dateutil**: Date parsing
