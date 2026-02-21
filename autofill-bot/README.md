# JobMatch AutoFill Bot

A Playwright-based auto-fill bot for job applications on Greenhouse, Lever, and Ashby ATS platforms.

## Features

- ✅ **Multi-ATS Support**: Greenhouse, Lever, Ashby, and generic fallback
- ✅ **Smart Field Matching**: Uses label text, placeholders, aria-labels, and name attributes
- ✅ **Document Handling**: Uploads resume/cover letter files or pastes text into textareas
- ✅ **Sensitive Field Protection**: Never auto-fills salary, work authorization, sponsorship without confirmation
- ✅ **Human-in-the-Loop**: Never auto-submits - always stops for human review
- ✅ **Detailed Reports**: Logs all filled, skipped, and error fields
- ✅ **Screenshot Capture**: Before/after screenshots for verification

## Installation

```bash
cd /app/autofill-bot

# Install dependencies
yarn install

# Install Playwright browsers
yarn install-browsers
```

## Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# API Configuration
API_BASE_URL=https://copilot-ai-7.preview.emergentagent.com

# Session token from browser (required!)
# Get this from your browser cookies after logging in
SESSION_TOKEN=your_session_token_here

# Bot Behavior
HEADLESS=false
SLOW_MO=100
SCREENSHOT_DIR=./screenshots
TIMEOUT=30000
```

### Getting Your Session Token

1. Log into the JobMatch website
2. Open browser DevTools (F12)
3. Go to Application → Cookies
4. Find `session_token` cookie
5. Copy the value to your `.env` file

## Usage

### Basic Usage

```bash
# Run autofill for a specific application
npm run autofill -- --application_id app_abc123def

# Or with yarn
yarn autofill --application_id app_abc123def
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--application_id <id>` | Application ID to fill (required) | - |
| `--headful` | Run browser in visible mode | `true` |
| `--headless` | Run browser in headless mode | `false` |
| `--slow-mo <ms>` | Slow down actions by milliseconds | `100` |
| `--timeout <ms>` | Timeout for operations | `30000` |
| `--skip-screenshots` | Skip taking screenshots | `false` |
| `--debug` | Enable debug logging | `false` |

### Examples

```bash
# Run in headless mode (no visible browser)
yarn autofill --application_id app_abc123 --headless

# Run with slower actions for debugging
yarn autofill --application_id app_abc123 --slow-mo 500

# Run with debug logging
yarn autofill --application_id app_abc123 --debug

# Run without screenshots
yarn autofill --application_id app_abc123 --skip-screenshots
```

## How It Works

### 1. Fetch Autofill Payload

The bot fetches the complete autofill payload from the API:

```
GET /api/applications/{application_id}/autofill-payload
```

This includes:
- Application metadata (job title, company, ATS type)
- User's structured profile (v2 schema)
- Resume and cover letter (text + file URLs)
- Fields requiring confirmation

### 2. Prepare Documents

If file upload is needed:
1. Calls `POST /api/applications/{id}/prepare-download/resume` to generate DOCX
2. Downloads the file from the returned public URL
3. Stores locally for upload

### 3. Navigate & Detect ATS

- Opens the application URL
- Verifies ATS type from page structure
- Selects appropriate mapper (Greenhouse, Lever, Ashby, or Generic)

### 4. Auto-Fill Form

Each ATS mapper handles platform-specific quirks:

**Greenhouse:**
- Uses `input[name="first_name"]` style selectors
- File inputs for resume
- Cover letter can be textarea or file

**Lever:**
- Often uses single "Full Name" field
- Cover letter is usually textarea
- Uses `data-qa` attributes

**Ashby:**
- Multi-step forms (handles "Next" buttons)
- Uses accessibility labels (`getByLabel`)
- File inputs may be hidden

### 5. Handle Sensitive Fields

The following fields are **never auto-filled** without user confirmation:
- Work authorization / sponsorship
- Salary expectations
- Willing to relocate
- Notice period / start date
- Referral source ("How did you hear about us?")

These are highlighted with a red border for manual review.

### 6. Stop for Review

The bot **never submits** automatically. It:
1. Takes an "after" screenshot
2. Highlights fields needing confirmation
3. Keeps browser open for human review
4. Generates a detailed report

## Report Output

Reports are saved to `./reports/`:

```
reports/
├── autofill_app_abc123_2025-02-01T12-34-56.json
└── autofill_app_abc123_2025-02-01T12-34-56.txt
```

### JSON Report Structure

```json
{
  "applicationId": "app_abc123",
  "startedAt": "2025-02-01T12:34:56.789Z",
  "duration": 15234,
  "status": "ready_for_review",
  "atsType": "greenhouse",
  "atsConfidence": "high",
  "filledFields": [
    { "field": "First Name", "value": "John", "selector": "input[name=\"first_name\"]" },
    { "field": "Email", "value": "john@example.com", "selector": "input[type=\"email\"]" }
  ],
  "skippedFields": [
    { "field": "salary", "reason": "Sensitive field - requires confirmation" }
  ],
  "confirmRequired": [
    { "field": "work_authorization", "reason": "Legal implications", "current_value": "citizen" }
  ],
  "errors": [],
  "screenshots": [
    { "stage": "before", "path": "./screenshots/app_abc123_before_1706789000000.png" },
    { "stage": "after", "path": "./screenshots/app_abc123_after_1706789015000.png" }
  ]
}
```

## Architecture

```
autofill-bot/
├── src/
│   ├── index.js              # Main entry point & CLI
│   ├── ats-mappers/
│   │   ├── base.js           # Base mapper class
│   │   ├── greenhouse.js     # Greenhouse-specific logic
│   │   ├── lever.js          # Lever-specific logic
│   │   ├── ashby.js          # Ashby-specific logic
│   │   └── generic.js        # Fallback for unknown ATS
│   └── utils/
│       ├── api-client.js     # API communication
│       ├── browser.js        # Browser/page utilities
│       ├── field-matcher.js  # Label-to-field matching
│       └── reporter.js       # Report generation
├── downloads/                # Downloaded document files
├── reports/                  # Generated reports
├── screenshots/              # Captured screenshots
├── package.json
├── .env.example
└── README.md
```

## Field Mapping

The bot matches form labels to profile fields using fuzzy matching:

| Label Patterns | Profile Field |
|---------------|---------------|
| "First name", "Given name" | `profile.first_name` |
| "Last name", "Surname", "Family name" | `profile.last_name` |
| "Email", "Email address" | `profile.email` |
| "Phone", "Mobile", "Telephone" | `profile.phone` |
| "City", "Location" | `profile.city` |
| "State", "Province" | `profile.state` |
| "LinkedIn", "LinkedIn URL" | `profile.linkedin_url` |
| "GitHub", "GitHub URL" | `profile.github_url` |
| "Portfolio", "Website" | `profile.portfolio_url` |
| "Resume", "CV" | `documents.resume` |
| "Cover letter" | `documents.cover_letter` |

## Design Principles

1. **Transparency over full automation**: The bot logs everything it does
2. **Human-in-the-loop**: Never submits without user review
3. **No credential scraping**: Only uses data from our API
4. **No CAPTCHA bypassing**: Fails gracefully if CAPTCHA detected
5. **No terms-of-service violations**: Respects rate limits and doesn't spam

## Troubleshooting

### "SESSION_TOKEN is required"

You need to set your session token in `.env`. Log into the website and copy the `session_token` cookie value.

### "Application not found"

The application ID doesn't exist or doesn't belong to your account. Verify the ID in the JobMatch dashboard.

### Form fields not being filled

1. Check the report for skipped fields and reasons
2. Try running with `--debug` flag for more logging
3. The ATS may have changed their form structure

### Browser not opening

1. Make sure Playwright browsers are installed: `yarn install-browsers`
2. Try running with `--headless` to see if it's a display issue

### File upload failing

1. Check that the document was generated successfully
2. Verify the file exists in `./downloads/`
3. Some ATS use hidden file inputs - the bot tries multiple approaches

## Contributing

When adding support for a new ATS:

1. Create a new mapper in `src/ats-mappers/`
2. Extend `BaseMapper` class
3. Implement the `fill()` method
4. Add ATS detection logic in `src/utils/browser.js`
5. Update this README

## License

MIT
