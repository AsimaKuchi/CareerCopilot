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
- **Stripe Subscription**: Freemium model with Free ($0) and Pro ($19.99/month) tiers (COMPLETE - Apr 5, 2026)
  - Free tier: Monthly usage limits (3 applications, 2 resumes, 2 cover letters, 1 interview prep, 1 career path, 3 extension uses)
  - Pro tier: Unlimited everything + advanced analytics + priority support + premium templates
  - Stripe Checkout for payments, webhook handling for subscription lifecycle
  - In-app billing management (cancel, reactivate, update payment, view invoices)
  - Inline upgrade modals when free users hit limits (HTTP 402 responses)
  - /pricing page (public) and /billing page (authenticated)
- **Admin Dashboard**: Full admin panel at /admin with dark theme (COMPLETE - Apr 5, 2026)
  - Overview: Total users, MRR, active users, failed logins, signups, jobs indexed, feature usage
  - User Management: Search/filter/paginate, view details, ban/unban, unlock, reset password, subscription override, CSV export
  - Security Monitoring: Failed login tracking, locked accounts, top offending IPs, banned users
  - Audit Logs: Filterable event log of all admin actions and critical user events
  - Support Tools: User search, send notifications, quick action links
  - Access restricted to admin-role users only (403 for non-admin)
- **Backend Modular Architecture**: Refactored 9446-line monolith into 11 route modules (COMPLETE - Feb 9, 2026, branch `refactor/backend-split`)
  - `core.py` (shared infra), `models.py` (Pydantic schemas), `routes/*.py` (per-feature routers)
  - Thin `server.py` (~330 lines) handles app, middleware, scheduler, router includes
  - `server_old.py` retained as rollback backup
  - Validated by testing agent: 26/27 endpoint tests pass (96%)
- **CSRF Hardening**: Closed CSRF bypass — middleware now requires X-CSRF-Token header on all authenticated state-changing requests (COMPLETE - Feb 9, 2026)
- **Job-search performance**: 58× speedup via cache-first hybrid (29s -> 0.5s); auto-refresh when cache > 15 min stale (COMPLETE - Feb 9, 2026)
- **Scheduler hardening**: Startup catch-up + `scheduler_meta` tracking; admin health endpoint at `/api/admin/scheduler-health` (COMPLETE - Feb 9, 2026)
- **Canonical job-URL matching**: Browser extension now matches optimized resume across variant ATS URLs (Greenhouse gh_jid, Lever uuid, LinkedIn id, etc.); 54 existing apps backfilled (COMPLETE - Feb 9, 2026)
- **Interview Prep**: Streaming responses (40ms to first content), gpt-5.2 -> gpt-4o-mini, regeneration with `excluded_questions` + 4 theme variations, parser fix that supports statement-style questions (COMPLETE - Feb 9, 2026)
- **Interview Prep autocomplete**: Generic dropdown of ~130 job titles + ~200 popular companies on both inputs (COMPLETE - Feb 9, 2026)
- **Pre-launch usage bypass** (TEMPORARY): `get_user_plan()` and `check_usage_limit()` in `stripe_routes.py` force `plan="pro"` for all users so preview-link testers don't hit paywalls. Original Free Tier logic preserved as commented code for easy revert. (COMPLETE - Feb 13, 2026)
- **`/api/stripe/usage` endpoint**: New GET endpoint returns `{plan, usage}` mirroring `/api/subscription` usage portion — resolves spec drift flagged in iteration_30 test report. (COMPLETE - Feb 13, 2026)
- **bcrypt warning fix**: Pinned `bcrypt==4.0.1` to silence passlib `bcrypt.__about__` warning spam. (COMPLETE - Feb 13, 2026)
- **Personal Career Coach (Brutal Mentor)**: Multi-turn AI coach with discovery flow for users who don't know where to go next. Dual-entry on `/career-paths`: 'I know what I want' vs 'I'm not sure where to go'. After ~6-8 messages, synthesizes the conversation into 3 personalized paths that render in the existing analysis view (COMPLETE - Feb 9, 2026)


## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend, python-docx, python-dateutil, BeautifulSoup4, stripe
- **Frontend**: React, Tailwind CSS, Shadcn/UI, framer-motion
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-5.2, GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API, Greenhouse API, Lever API
- **Auth**: Google OAuth + JWT for email/password
- **Payments**: Stripe (test mode), subscription billing

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

## Session Idle Timeout (Mar 27, 2026) - COMPLETE

### Implementation:
- `IdleTimeout` component mounted in `ProtectedRoute` (all authenticated pages)
- Tracks: mousedown, keydown, scroll, touchstart, mousemove events
- **55 min inactivity**: Warning dialog with live countdown (MM:SS)
- **60 min inactivity**: Auto-logout via `/api/auth/logout`, redirect to `/auth`
- **"Stay Logged In" button**: Resets all timers
- **"Log out now" button**: Immediate logout

### Files:
- `frontend/src/components/IdleTimeout.jsx`: Self-contained component with AlertDialog
- `frontend/src/App.js`: IdleTimeout rendered inside ProtectedRoute wrapper

### Test Results (manual curl):
- Rate limiting: Blocks 6th signup ✓
- Account lockout: Locks after 5 failures, blocks even correct password ✓
- Lockout message shows remaining minutes ✓
- Successful login resets counter ✓

## Security: Headers, Admin Roles, CSRF (Mar 27, 2026) - COMPLETE

### Security Headers (middleware on every response):
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; script/style/img/connect policies`

### Admin Role System:
- `role` field on User model ("user" | "admin")
- `get_admin_user()` dependency returns 403 for non-admins
- Endpoints: GET `/admin/users`, GET `/admin/stats`, PUT `/admin/users/{id}/role`, POST `/admin/unlock-user`
- Admin: fuzailbukhari@gmail.com

### CSRF Protection:
- Token generated on login, stored in session + non-httponly cookie
- Frontend `apiFetch.js` reads cookie and sends `X-CSRF-Token` header on POST/PUT/PATCH/DELETE
- Middleware validates token on state-changing requests (exempt: auth, public endpoints)
- All authenticated pages updated to use `apiFetch` wrapper

### Test Results (iteration_25.json):
- Backend: 100% (12/12 tests passed)
- Frontend: 100% - Login, navigation, CSRF all working

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

## Job Search Date Sorting (Apr 5, 2026) - COMPLETE

### Problem:
- Jobs were sorted by match_score, not by date
- User requested strict newest-first ordering

### Fix:
- **Backend** (`server.py`): Replaced broken string-based sort with `normalize_posted_date()` to parse all date formats (ISO strings, Unix timestamps, etc.) then sort descending
- **Frontend** (`JobSearch.jsx`): Changed all 3 sort functions (streaming, fallback, final combine) from match_score to date-based sorting
- **Non-streaming endpoint** (`/api/jobs/search`): Also updated to sort by posted_at descending

### Test Results (iteration_26.json):
- Backend: 100% (3/3 tests passed)
- Streaming: 100 jobs, 0 sort violations
- Non-streaming: 17 jobs, 0 sort violations


## Audit Logging & Session Revocation (Apr 5, 2026) - COMPLETE

### Comprehensive Audit Logging:
- Logs: login_success, failed_login (with IP), signup, forgot_password, password_reset, profile_update, subscription_upgrade/cancel/reactivate, revoke_all_sessions, all admin_actions
- Stored in `audit_logs` collection with timestamp, user_email, severity, details
- Viewable and filterable in Admin Dashboard > Audit Logs

### Session Revocation:
- GET /api/auth/sessions - Lists active sessions with device info (IP, user agent, last active)
- POST /api/auth/revoke-all-sessions - Logout from all devices except current
- Multi-session support (login no longer kills other sessions)
- SessionManagement component on Profile page shows active sessions with "This device" badge
- "Logout All Devices" button when multiple sessions exist

### Test Results (iteration_29.json):
- Backend: 100% (13/13 tests passed)
- Frontend: 100% (all UI tests passed)

## Prioritized Backlog

### P0: Refactor Monolithic Backend (URGENT)
- `backend/server.py` is 9,380+ lines and becoming unmanageable
- Must break into structured FastAPI application:
  - routes/ (API routers by domain)
  - models/ (Pydantic models)
  - services/ (business logic)
  - utils/ (helpers)
- Critical for maintainability and scalability
- Note: `stripe_routes.py` and `admin_routes.py` already started the pattern

### P1: Admin Dashboard Phase 2 (Revenue)
- Revenue dashboard with Stripe data (daily/monthly/yearly)
- Conversion funnel (signups -> free -> pro)
- Churn rate, LTV metrics
- Stripe webhook event tracking

### P2: Speed up "Find Jobs" load times
- Instantly load cached DB results while streaming live results in the background

### P3: Enhance Extension Dropdown Matching
- Improve universal extension logic for complex dropdown scenarios

### P4: Fine-tune Extension for Lever/Ashby
- Add platform-specific logic for better reliability

### Future
- Admin Dashboard Phase 2 (Revenue metrics from Stripe)
- Analytics Dashboard (admin)
- Maintenance Mode toggle
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
