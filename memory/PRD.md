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
- **Salary Extraction**: Automatically extracts salary from job descriptions when not in structured fields (COMPLETE - Mar 8, 2026)

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
- Full Job Descriptions Feature (expandable on Dashboard and Job Search)
- Formatted Job Descriptions (section headers, bullets, spacing)
- **Salary Extraction from Descriptions** (Mar 8, 2026) - COMPLETE

## Salary Extraction Feature (Mar 8, 2026) - COMPLETE

### Implementation Details:
- **Utility**: `/app/frontend/src/utils/extractSalary.js`
  - `extractSalaryFromDescription()` - Parses salary from text
  - `getDisplaySalary()` - Priority: structured fields > text field > description extraction
  
### Supported Salary Patterns:
- Currency with symbol: `$95,000 CAD`, `$90,000 USD`, `€80,000`
- Salary ranges: `$90,000 - $120,000`, `$90,000—$120,000` (em-dash supported)
- K notation: `$80K - $100K`, `$95K`
- Hourly rates: `$40/hr`, `$40 per hour`
- Prefix patterns: `Base pay: $90,000`, `Salary: $100K+`

### Currency Support:
- USD ($), CAD (CA$), EUR (€), GBP (£), AUD (A$)

### UI Display:
- Extracted salaries display in **emerald green** (`text-emerald-400`)
- Falls back to "Salary not listed" when no salary found
- Sanity checks: annual $10K-$10M, hourly <$500

### Test Results (iteration_18.json):
- Backend: 100% (5/5 tests passed)
- Bug fixed: Em-dash (—) character not recognized in range patterns

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs (returns jobs with description), /api/public/sources
- Search: /api/jobs/greenhouse/search (fixed to preserve descriptions)
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx
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
- **OpenAI (GPT-4o, GPT-4o-mini)**: Uses Emergent LLM Key
- **JSearch API (RapidAPI)**: Requires User API Key
- **Resend**: Transactional emails
- **Google OAuth**: Authentication
- **python-docx**: Document generation
- **BeautifulSoup4**: HTML parsing
- **python-dateutil**: Date parsing

## Files Added (Mar 8, 2026)
- `/app/frontend/src/utils/formatJobDescription.js` - Description formatting utility
- `/app/frontend/src/components/FormattedJobDescription.jsx` - Formatted description component
- `/app/frontend/src/utils/extractSalary.js` - Salary extraction utility
- `/app/backend/tests/test_salary_extraction.py` - Salary extraction tests
