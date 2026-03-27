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
- **Professional Design System**: Clean light-theme SaaS design with Indigo primary, Inter font, shadcn/ui components (COMPLETE - Mar 12, 2026)

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

## Design System (Mar 12, 2026) - COMPLETE

### Design Tokens:
- **Primary**: Indigo #6366F1, **Secondary**: Green #10B981, **Accent**: Blue #3B82F6
- **Font**: Inter (400/500/600/700), JetBrains Mono for code
- **Backgrounds**: Gray-50 (#F9FAFB), White cards with border-gray-200
- **Shadows**: sm (subtle), md (card hover), lg (elevated)
- **Transitions**: 200ms on all interactive elements

### Pages Updated:
- index.css: CSS variables, Inter font, selection, scrollbar, surface utilities, animations
- App.css: Updated utility classes (prose, gradient borders, shimmer, card effects)
- Navbar: Clean white background, indigo active states, compact design
- LandingPage: Full rewrite with clean hero, metric cards, features, reviews
- Dashboard: Light-theme stat cards, quick actions, saved jobs
- Auth: Clean card-based login/signup with Google OAuth
- JobSearch: Updated badges, form inputs, source selector, match analysis
- InterviewPrep: Light-theme forms and tips
- Support: Full rewrite with clean form layout

### Test Results (iteration_23.json):
- Frontend: 100% - All 8 pages verified with correct design tokens

## Bento Grid Stats Redesign (Mar 12, 2026) - COMPLETE

### Layout:
- **Total Applications**: 2-col purple gradient card with sparkline SVG
- **Applied**: 1-col white card with emerald checkmark
- **Profile Complete**: 1-col white card with animated progress bar
- **Time Saved**: Full-width bottom row with contextual message

### Animations (framer-motion):
- AnimatedNumber: Count-up from 0 with requestAnimationFrame
- AnimatedBar: Progress fills 0→100% over 800ms with cubic easing
- Staggered card entrance: 50ms delay between each card

### Test Results (iteration_24.json):
- Frontend: 100% - All bento stats cards verified with proper styling and animations

## Security: Rate Limiting & Account Lockout (Mar 27, 2026) - COMPLETE

### Rate Limiting (in-memory sliding window):
- **Login**: 10 attempts/minute per IP (HTTP 429 when exceeded)
- **Signup**: 5 attempts/minute per IP
- **Password Reset**: 3 attempts/5 minutes per IP

### Account Lockout (MongoDB-persisted):
- Tracks `failed_login_attempts` per user in DB
- **Locks account after 5 failed attempts** for 15 minutes (HTTP 423)
- Shows remaining attempts on each failure
- Resets counter on successful login
- Lockout auto-expires after 15 minutes

### Files Modified:
- `backend/server.py`: Added `RateLimiter` class, `get_client_ip()`, rate limit + lockout logic on `/auth/login`, `/auth/signup`, `/auth/forgot-password`, `/auth/reset-password`

### Test Results (manual curl):
- Rate limiting: Blocks 6th signup ✓
- Account lockout: Locks after 5 failures, blocks even correct password ✓
- Lockout message shows remaining minutes ✓
- Successful login resets counter ✓

## Personalized Match Analysis (Mar 8, 2026) - COMPLETE

### Problem Solved:
- OLD: Generic statements like "Strong role alignment: Your target role matches this position"
- NEW: Specific, evidence-based insights using actual resume text

### Implementation:
- **Backend**: Enhanced `evaluate_job_match()` function in server.py
- **New Fields**:
  - `grounded_strengths[]`: Array with {strength_title, evidence, relevance}
  - `matched_skills[]`: List of specific skills that match job requirements
  - `evidence`: Actual achievement bullets from resume with metrics

### Bugs Fixed (Session Mar 8, 2026):
1. **Frontend field mismatch**: Was rendering `s.requirement`/`s.match_reason`, now uses `s.strength_title`/`s.relevance` matching backend output
2. **Streaming endpoint missing description**: `/api/jobs/greenhouse/search` was only passing job title+department to `evaluate_job_match`, now passes full description for proper skill matching
3. **Work experience parsing**: `extract_work_experience()` was incorrectly parsing `Title | Company | Date` format, setting company to the job title. Rewritten with proper part classification
4. **Duplicate strength titles**: Achievement-based strengths all got same category (e.g., "Technical Delivery"). Now uses diverse categories (Leadership, Cost Optimization, Business Impact, Technical Building, System Implementation, Quality & DevOps)

### Test Results (iteration_22.json):
- Backend: 100% (7/7 tests passed)
- Frontend: 100% - All grounded strengths displayed correctly
- All 4 bugs verified fixed

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
- `/app/backend/server.py` - Fixed streaming endpoint job_description, rewrote extract_work_experience(), improved grounded strength categorization, frontend field alignment
- `/app/frontend/src/pages/JobSearch.jsx` - Fixed grounded_strengths rendering to use strength_title/relevance instead of requirement/match_reason
- `/app/frontend/src/pages/InterviewPrep.jsx` - Q&A formatting
- `/app/frontend/src/utils/extractSalary.js` - Salary extraction utility
- `/app/frontend/src/utils/formatJobDescription.js` - Description formatting utility
- `/app/backend/tests/test_grounded_strengths.py` - Unit tests for grounded strengths feature
