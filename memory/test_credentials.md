# Test Credentials

## Active accounts (Feb 2026 refactor verified)

| Type | Email | Password | Notes |
|------|-------|----------|-------|
| User | `refactor_test@example.com` | `TestPass123!` | Created during refactor testing, email verified |
| Admin | `fuzailbukhari@gmail.com` | _(Google OAuth - admin role in DB)_ | Bypasses Stripe usage limits |

## Sign-up flow note

Email service runs in TEST mode locally. Signup returns a `verification_url` in the response body that
must be POSTed back to `/api/auth/verify-email` with `{"token": ...}` before login is allowed.
