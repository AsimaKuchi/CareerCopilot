# MyCareerCopilot — PRD

## Original Problem Statement
Comprehensive career management application ("MyCareerCopilot") + universal browser extension for autofilling job applications. Premium SaaS UI (React/Tailwind/shadcn), FastAPI + MongoDB backend, strong security (CSRF, rate limiting, sessions, audit logs), Stripe monetization (Free/Pro tiers), AI career features (resume/cover letter optimization, streaming interview prep, career coach, career paths).

## Architecture
- Frontend: React (CRA), Tailwind, shadcn/ui, React.lazy code-splitting — `/app/frontend`
- Backend: FastAPI + Motor (MongoDB) — `/app/backend` (routes in `/app/backend/routes/`)
- Extension: Manifest V3 Chrome extension — `/app/browser-extension`
- Integrations: Emergent LLM key (OpenAI/Anthropic via emergentintegrations), Stripe, Resend, JSearch (RapidAPI), Emergent-managed Google Auth
- Deployed by user to production (mycareercopilot.ca); dev work stays in preview

## Branding / Logo (June 2026)
- Website logo: "MyCareer" (gray-900) + plane glyph (gray-400, rotated 45° pointing up-right) / "CoPilot" (indigo-500) with a continuous indigo stream flowing OUT of the plane's tail, sweeping under "MyCareer" and curling before "CoPilot". Implemented in `Navbar.jsx`, `LandingPage.jsx`, `HowItWorks.jsx` (absolute overlay SVG, viewBox 0 0 100 40).
- Extension icon (FINAL): just the plane glyph in indigo-500 (#6366f1) on white rounded tile, pointing up-right. Generator: `/app/scripts/generate_logo_final.py`, outputs `/app/scripts/logo_output/final/` (icon16/48/128/1024 + store tile 440x280).
- Icons copied to `/app/browser-extension/icons/`, zip rebuilt.

## Extension distribution
- ZIP: `/app/scripts/dist/mycareer-copilot-extension.zip` copied to `/app/frontend/public/downloads/mycareer-copilot-extension.zip` (and `/app/frontend/public/browser-extension.zip`)
- Store assets in `/app/frontend/public/downloads/`: `icon128.png`, `store_tile_440x280.png`
- Privacy policy at `/privacy` (`/app/frontend/src/pages/legal/PrivacyPolicy.jsx`) — now includes section 2.3.1 explaining Chrome permissions (activeTab/scripting, storage, cookies, host permissions) + Limited Use compliance statement. Terms at `/terms`, refund policy also exist.
- NOTE: manifest.json extension name is still "CareerCopilot AI - Auto-Fill" — user may want rename to "MyCareerCopilot".

## Completed (this session, June 2026)
- Website logo: stream now leads out of the plane's tail; plane flipped to point up-right (Navbar, Landing, HowItWorks)
- Final extension icon: indigo plane matching site branding; zip rebuilt & hosted for download
- Store promo tile (440x280) generated
- Privacy policy enhanced with Chrome permission explanations (verified via screenshot)
- Chrome Web Store upload instructions provided to user

## Completed (earlier sessions)
- Full app: auth (JWT sessions + Google via Emergent), profile with completion tracker, job search (JSearch hybrid cache), applications tracker, AI interview prep (streaming, fixed markdown renderer), career coach, career paths, Stripe free/pro, admin dashboard, audit logging, CSRF, per-user rate limits, resume upload with magic-byte validation, React.lazy code splitting.

## Backlog
- P1: Extension improvements — complex dropdowns, ATS-specific logic (Lever, Ashby)
- P2: Rename extension in manifest.json to "MyCareerCopilot" (pending user confirmation)
- P3: Deep /api/health check (MongoDB, Stripe, OpenAI status)
- P4: Maintenance mode admin toggle
- P5: "Follow Company" feature
- P6: Persist company filter in preferences
- Known: Resend account in sandbox mode (user must verify custom domain); minor ruff F811 lint in resume_routes.py line ~551

## Credentials
- See /app/memory/test_credentials.md (user: refactor_test@example.com / test; admin: fuzailbukhari@gmail.com)
