# CareerCopilot AI - Product Requirements Document

## Original Problem Statement
Build a browser extension that auto-fills job application forms on Greenhouse, Lever, and Ashby using a central user profile. Evolved into a full-featured web application for career management named "CareerCopilot AI".

## Core Features

### Browser Extension
- Autofill forms universally on any job site
- Automatically track application submissions
- Manifest V3 with `<all_urls>` permission

### Web Application
- **Dashboard**: Track applications, show stats like "Time Saved"
- **Profile Management**: Multi-select skills, AI resume-to-profile pre-fill
- **Job Search**: Find jobs from various sources, prioritize key ATS platforms
- **Authentication**: Google OAuth + email/password with verification/reset
- **AI Career Paths**: Analyze profile/resume, suggest career paths, find matching jobs
- **Welcome Email**: Sends onboarding email via Resend on signup

### Branding
- Custom logo with "Career" (dark navy) and "CoPilot" (indigo) with airplane icon
- Logo placed on landing page header and dashboard navbar

## Tech Stack
- **Backend**: Python (FastAPI), MongoDB, passlib[bcrypt], Resend
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Browser Extension**: Manifest V3, universal field detection
- **AI**: OpenAI (GPT-4o, GPT-4o-mini) via Emergent LLM Key
- **Jobs API**: JSearch (RapidAPI)
- **Auth**: Google OAuth + JWT for email/password

## What's Been Implemented
- Full authentication system (Google OAuth + email/password)
- Universal Chrome extension for any job site
- Dashboard with prioritized job listings
- Profile page with resume-to-profile AI pre-fill
- AI Career Paths page
- Job search feature
- Landing page with company logo carousel
- Welcome email via Resend (tested, working)
- Custom logo integration on landing page + dashboard navbar (Feb 23, 2026)

## Key API Endpoints
- `POST /api/auth/signup` - Email registration
- `POST /api/auth/login` - Email/password login (returns JWT)
- `GET /api/auth/verify-email/{token}` - Email verification + welcome email
- `POST /api/auth/request-password-reset` - Password reset initiation
- `POST /api/auth/reset-password` - Password reset completion
- `GET /api/auth/session` - Google OAuth (triggers welcome email for new users)

## DB Schema
- **users**: Extended with hashed_password, is_verified, verification_token, reset_token

## Prioritized Backlog

### P1: Refactor Monolithic Backend
- Break `backend/server.py` into structured app with APIRouters, models, services

### P2: Enhance Extension Dropdown Matching
- Handle numeric ranges, synonym lists for dropdown options

### P3: Fine-tune Extension for Key ATS
- Add specific logic for Lever, Ashby unique form structures

## Known Limitations
- Resend is in test mode: emails only delivered to verified account email
- To send to all users: verify a custom domain at resend.com/domains

## 3rd Party Integrations
- OpenAI (GPT-4o, GPT-4o-mini) via Emergent LLM Key
- JSearch API (RapidAPI)
- Resend (transactional emails)
- Google OAuth (authentication)
