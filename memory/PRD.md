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
- **Job Search**: Find jobs from multiple sources with matching algorithm
- **Authentication**: Google OAuth + email/password with verification/reset
- **AI Career Paths**: Analyze profile/resume, suggest career paths, find matching jobs
- **Welcome Email**: Sends onboarding email via Resend on signup

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API
- **Auth**: Google OAuth + JWT for email/password

## Job Sources (12,570+ jobs)
| Source | Method | Count |
|--------|--------|-------|
| Greenhouse | Direct API | ~11,957 |
| Lever | Direct API | ~463 |
| Amazon | amazon.jobs JSON API | ~120 |
| Microsoft | JSearch API | ~14 |
| Apple | JSearch API | ~16 |
| Netflix | Lever (added, currently 0 open) | 0 |

### Job Ingestion Pipeline
- Scheduler: Ingestion every 2 hours, cleanup every 24 hours
- Expired jobs (>30 days old) automatically removed
- Indeed and Talent.com filtered out (require separate login)
- Non-English jobs filtered via pattern matching

## What's Been Implemented
- Full authentication system (Google OAuth + email/password)
- Universal Chrome extension for any job site
- Dashboard with prioritized job listings
- Profile page with resume-to-profile AI pre-fill
- AI Career Paths page
- Job search feature
- Landing page with company logo carousel
- Welcome email via Resend (tested, working)
- Custom CSS logo "MyCareer CoPilot" with airplane icon (Feb 23, 2026)
- Branding unified to "MyCareerCoPilot" across entire app (Feb 23, 2026)
- Job sources: Amazon, Microsoft, Apple, Netflix integrated (Feb 24, 2026)
- Expired job cleanup + automatic refresh scheduler (Feb 24, 2026)
- Landing page feature text updated (Feb 23, 2026)
- How It Works page condensed for scannability (Feb 23, 2026)

## Key API Endpoints
- `POST /api/auth/signup` - Email registration
- `POST /api/auth/login` - Email/password login (returns JWT)
- `GET /api/auth/verify-email/{token}` - Email verification + welcome email
- `POST /api/auth/request-password-reset` - Password reset initiation
- `POST /api/auth/reset-password` - Password reset completion
- `GET /api/auth/session` - Google OAuth
- `GET /api/public/jobs` - Browse jobs with filters
- `GET /api/public/sources` - Job source counts
- `POST /api/public/jobs/ingest` - Trigger job ingestion

## Prioritized Backlog

### P1: Refactor Monolithic Backend
- Break `backend/server.py` into structured app with APIRouters, models, services

### P2: Enhance Extension Dropdown Matching
- Handle numeric ranges, synonym lists for dropdown options

### P3: Fine-tune Extension for Key ATS
- Add specific logic for Lever, Ashby unique form structures

## Known Limitations
- Resend is in test mode: emails only delivered to verified account email
- Netflix Lever board has 0 open positions currently
- Microsoft & Apple job counts depend on JSearch API quota
