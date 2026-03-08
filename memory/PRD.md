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
- **Interview Prep**: AI-generated interview prep with consistent Q&A formatting (UPDATED - Mar 8, 2026)

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend, python-docx, python-dateutil, BeautifulSoup4
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-5.2, GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API, Greenhouse API, Lever API
- **Auth**: Google OAuth + JWT for email/password

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
- **Interview Prep Q&A Formatting** (Mar 8, 2026) - COMPLETE

## Interview Prep Q&A Formatting (Mar 8, 2026) - COMPLETE

### Issue Fixed:
- OLD: Inconsistent formatting with cream/amber tip boxes, lightbulb icons, numbered headers
- NEW: Clean, professional Q&A format matching the desired design

### New Format:
- **Questions**: Light slate background (`bg-slate-50`) with indigo "Q" badge (`bg-indigo-500`)
- **Answers**: White background with green "A" badge (`bg-emerald-500`)
- **Suggested approach**: Highlighted in answers with medium font weight
- **Section headers**: Numbered badges in indigo circles with uppercase titles

### Code Changes:
- Rewrote parsing logic in InterviewPrep.jsx (lines 206-330)
- Removed amber/cream tip boxes and lightbulb icons from generated content
- Added detection for "Suggested approach:" lines
- Grouped Q&A items by section

### Test Results (iteration_19.json):
- Frontend: 100% (6/6 formatting requirements verified)
- 11-12 Q&A items rendered consistently per generation

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs, /api/public/sources
- Search: /api/jobs/greenhouse/search
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx, /api/ai/interview-prep
- Analytics: /api/analytics/company-search

## Database Schema
- **stored_jobs**: Contains `description` (full plain text) and `posted_at_dt` (standardized datetime)
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
- **OpenAI (GPT-5.2, GPT-4o, GPT-4o-mini)**: Uses Emergent LLM Key
- **JSearch API (RapidAPI)**: Requires User API Key
- **Resend**: Transactional emails
- **Google OAuth**: Authentication
- **python-docx**: Document generation
- **BeautifulSoup4**: HTML parsing
- **python-dateutil**: Date parsing

## Files Modified (Mar 8, 2026)
- `/app/frontend/src/pages/InterviewPrep.jsx` - Complete rewrite of Q&A parsing and rendering
- `/app/frontend/src/utils/extractSalary.js` - Salary extraction utility (new)
- `/app/frontend/src/utils/formatJobDescription.js` - Description formatting utility
- `/app/frontend/src/components/FormattedJobDescription.jsx` - Formatted description component
