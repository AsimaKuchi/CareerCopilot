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

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend, python-docx
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-5.2) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI), Amazon Jobs API
- **Auth**: Google OAuth + JWT for email/password

## Job Sources (12,570+ jobs)
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
- **Word document (.docx) download** for AI-optimized resumes and cover letters (Mar 4, 2026)

## .docx Download Feature (Mar 4, 2026)
- Backend endpoint: POST /api/ai/download-docx
- Formats: resume (section headers, bullet points, name, contact) and cover_letter (date, salutation, paragraphs, closing)
- Filename includes company + job title (e.g., Resume_Amazon_Senior_Engineer.docx)
- Available on both Job Search page (after optimization) and Applications page (for saved documents)
- Uses python-docx with Calibri font, proper margins, and professional formatting

## Key API Endpoints
- Auth: signup, login, verify-email, password-reset, session
- Jobs: /api/public/jobs, /api/public/sources, /api/public/jobs/ingest
- Search: /api/jobs/greenhouse/search, /api/jobs/search (both with company filter)
- AI: /api/ai/optimize-resume, /api/ai/cover-letter, /api/ai/download-docx, /api/ai/interview-prep
- Analytics: /api/analytics/company-search

## Prioritized Backlog
### P1: Refactor Monolithic Backend
### P2: Expand Canadian job coverage (Amazon/MS/Apple)
### P2: Enhance extension dropdown matching
### P3: Fine-tune extension for Lever/Ashby
### Future: Store company filter in user prefs, "Follow Company" feature
