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
- **Job Data Source**: JSearch API + Greenhouse + Lever + SmartRecruiters + Pinpoint (real-time scraping)
- **Authentication**: Google Social Login (Emergent OAuth)
- **Design**: Light theme with glassmorphism

## Architecture

### Tech Stack
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via emergentintegrations
- **Job API**: JSearch (RapidAPI) + Greenhouse/Lever/SmartRecruiters/Pinpoint APIs
- **Auth**: Emergent Google OAuth
- **Automation**: Chrome Browser Extension (replaces server-side Playwright)

### Key Files
```
/app/backend/server.py          # Main API endpoints
/app/backend/profile_schema.py  # Profile v2 schema + migration logic
/app/backend/encryption.py      # AES encryption for sensitive data
/app/backend/ats_scrapers.py    # SmartRecruiters & Pinpoint scrapers
/app/browser-extension/         # Chrome extension for auto-filling (NEW)
/app/frontend/src/App.js        # Main React app with routing
/app/frontend/src/pages/        # All page components
/app/frontend/src/components/   # Shared components (Navbar)
```

## What's Been Implemented (February 11, 2025)

### Latest Updates ✅
- **File Naming Convention for Browser Extension Uploads (NEW - Feb 11, 2025)**:
  - Resume uploads now named: `FirstnameLastnameCV.docx` (e.g., `JohnSmithCV.docx`)
  - Cover letter uploads now named: `FirstnameLastnameCL.docx` (e.g., `JohnSmithCL.docx`)
  - Special characters and spaces are stripped from names for clean filenames
  - Backend endpoint `/api/extension/autofill-data` updated with new naming logic

- **Browser Extension Dropdown Auto-Fill (Feb 10, 2025)**:
  - Rebuilt content.js with robust dropdown detection and filling logic
  - Supports native `<select>`, `role="combobox"`, `aria-haspopup`, Radix UI, react-select
  - Opens dropdowns and waits for portal-rendered options (up to 2500ms)
  - Global option search: listbox options, ul/li, Radix popper, react-select menus
  - Answer matching: exact → contains → word-overlap → numeric bucket matching
  - Synonyms mapping for Yes/No, countries, work arrangements, relocation, notice periods
  - Filters placeholder options ("Select...", "Loading...", "No options")
  - Verification: checks aria-selected, hidden input values, dropdown text change
  - Retry mechanism for failed selections
  - Skips EEO/demographic/legal questions
  - DEBUG_DROPDOWNS flag for verbose logging
  - Backend mapping functions added to convert DB values to exact UI labels:
    - `_map_willing_to_relocate()`: "yes" → "Yes - willing to relocate"
    - `_map_notice_period()`: "two_weeks" → "2 weeks notice"
    - `_map_education()`: "bachelor" → "Bachelor's Degree"
    - `_map_work_arrangement()`: "remote" → "Remote"
  - Redesigned match analysis to be grounded in actual resume content
  - Each strength now includes: Job requirement → Resume evidence → Match reason
  - No more generic phrases like "Strong role alignment" or "Experience aligns well"
  - New `grounded_strengths` field with evidence-based analysis
  - New `/api/ai/detailed-match-analysis` endpoint for AI-powered deep analysis
  - Frontend updated to display structured evidence with visual hierarchy
  - Added matched skills display with badges
- **Fixed Cover Letter/Interview Prep Error (520)**: Updated skills handling for v2 schema
- **Added LinkedIn Job Source Button**: Dedicated filter for LinkedIn-only jobs
- **Comprehensive Location Filtering**:
  - Created `/app/backend/location_utils.py` with structured location parsing
  - Remote jobs now have proper scope: city, province, country, continent, or global
  - Canadian searches exclude Global/Worldwide remote jobs
  - Canadian searches exclude US-only remote jobs
  - Remote jobs display scope labels: "Remote (Canada)", "Remote (North America)", etc.
  - Hybrid jobs properly detected and labeled
  - All Canadian cities/provinces mapped for accurate detection
  - US states/cities mapped for exclusion
- **Fixed CAPTCHA False Positives**: Updated detection to check visible elements only, not raw HTML
- **SmartRecruiters Integration Fixed**:
  - Updated to use SmartRecruiters Public API
  - 36+ Canadian jobs now being fetched
  - Fixed location filter to exclude UK jobs (London, UK was matching London, ON)

### MVP Features ✅
- **Landing Page**: Hero section, features showcase, CTAs with light theme
- **Google Auth**: Full OAuth flow with session management
- **Dashboard**: 
  - Stats cards, quick actions, profile completion guide
  - "Your Saved Jobs" section showing jobs from last search
  - "NEW" star badge on jobs not seen before
  - "Find New Jobs" button to trigger fresh search
- **Profile Page**: 
  - Resume upload (PDF, DOCX, TXT)
  - Skills management
  - Job preferences
  - Salary expectations
  - Work Authorization (citizen, permanent_resident, work_permit, require_sponsorship)
  - Target Industries (max 3, with "open to any" option)
  - Seniority Level (entry, junior, mid, senior, lead, manager, director, executive)
- **Job Search**: 
  - Real-time search via JSearch API
  - Detailed match evaluation with:
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
  - Resume ATS optimization (GPT-5.2) - **NEW (Jan 28): One-page constraint enforced**
  - Cover letter generation (GPT-5.2)
  - Interview prep materials (GPT-5.2)
- **Document Handling**:
  - **NEW (Jan 28)**: "Download .docx" button in View modal - client-side generation with formatting preserved
  - "View & Copy" modal for optimized resume/cover letter
  - Download preserves headings (bold), bullet points (indented), and proper spacing

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
- ✅ Fallback search mechanism for multi-word queries (fixed Jan 25, 2025)
- ✅ **Profile v2 Schema Migration (Feb 1, 2025)**: Structured schema with normalized enums for work authorization, skills, education, phone (E.164), location. Auto-fill now uses normalized values.
- ✅ **Auto-Fill & Auto-Submit with User Confirmation (Feb 8, 2025)**: Implemented server-side Playwright automation that fills AND submits application forms. Users see a confirmation modal with 3 options: Cancel, Fill Only (no submit), Fill & Submit. Button renamed from "Auto-Fill" to "Auto-Apply".

### P1 - High Priority (Next)
- [ ] Add Google Jobs as a search source (user approved)
- [ ] Interview Tips & Prep feature completion
- [ ] Email notifications for new job matches
- [ ] Implement remaining ATS scrapers: Teamtailor, Jobvite, BambooHR

### P2 - Medium Priority
- [ ] Implement Playwright-based Ashby scraper (currently non-functional)
- [ ] Enhance Playwright reliability for SmartRecruiters and Pinpoint submissions
- [ ] Fetch full job descriptions for better AI analysis
- [ ] Saved job searches
- [ ] Multiple resume versions
- [ ] Application notes and reminders

### P3 - Nice to Have
- [ ] LinkedIn integration
- [ ] Company research panel
- [ ] Salary negotiation tips
- [ ] Video interview practice

## Test Results (Latest: February 8, 2025)
- **Backend**: 100% success rate (14/14 auto-fill tests passed)
- **Frontend**: All UI elements verified (confirmation modal, Auto-Apply button)
- **Profile v2 Schema**: All migration functions verified
- **API Endpoints**: GET/PUT /api/profile, GET /api/autofill/data all passing
- **Playwright Auto-Fill**: 4/4 tests passed (browser launch, navigation, CAPTCHA detection, field selectors)
- **Performance**: Job loading ~2s (parallel fetching)

## Recent Bug Fixes (February 8, 2025)
- **✅ Auto-Fill & Auto-Submit Feature Complete**: Implemented user-confirmed auto-submit functionality. Backend accepts `submit_form` parameter (defaults to False). When True, Playwright clicks submit button after filling fields.
- **✅ HTML Nesting Fix**: Fixed React hydration warning in confirmation modal by using `asChild` prop with div container instead of nested p tags.
- **✅ Submission Verification**: Added screenshot capture, final URL tracking, and honest messaging about submission confirmation status.
- **✅ Data Preview Modal**: Users can now preview all their data (personal info, resume, cover letter) before confirming auto-submit.
- **✅ Interview Prep Feature**: Added "Interview Prep" button to both JobSearch and Applications pages. Generates AI-powered interview materials tailored to each specific job.
- **✅ Browser Extension**: Created Chrome/Edge extension for auto-filling job applications directly in the browser. Much more reliable than server-side Playwright.

## Recent Bug Fixes (February 6, 2025)
- **✅ Fixed Playwright Executable Path Error**: The `BrowserType.launch: Executable doesn't exist` error was caused by a version mismatch between the Playwright Python package (v1.57.0, expecting browser build v1200) and the pre-installed browsers (build v1208). Fixed by running `playwright install chromium` to download the correct browser version.

## Database Schema

### users
- user_id: string
- email: string
- name: string
- picture: string (optional)
- created_at: datetime

### user_profiles (v2 Schema)
- user_id: string
- profile_version: int (1 or 2)
- migrated_at: datetime (when migrated to v2)
- resume_text: string (optional, encrypted)
- resume_filename: string (optional)
- resume_format: string (optional)
- skills: array[{name: string, years: number, level: string}]
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
- highest_education: string (optional)
- phone_number: string (optional, encrypted)
- email: string (optional)
- linkedin_url: string (optional, encrypted)
- github_url: string (optional, encrypted)
- portfolio_url: string (optional, encrypted)
- address_city: string (optional, encrypted)
- address_state: string (optional, encrypted)
- address_country: string (optional, encrypted)
- **structured**: object - Contains normalized values for auto-fill:
  - workAuthorization: {raw, normalized: {country, status, requiresSponsorship, expiryDate}}
  - seniorityLevel: {raw, normalized}
  - education: {raw, normalized}
  - skills: {items: [{name, years, level}]}
  - contact: {email, phone: {raw, normalized (E.164), formatted}, location: {raw, normalized}}
  - links: {linkedin, github, portfolio, website}
  - preferences: {desiredJobTitles, preferredLocations, workArrangement, jobTypes, willingToRelocate, noticePeriod}
  - compensation: {salaryExpectations: {min, max, currency}}
  - industries: {targetIndustries, openToAny}
  - applicationDefaults: {referralSource}
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
