# JobMatch AI - Browser Extension

Auto-fill job applications with your optimized resume and cover letter from JobMatch AI.

## Features

- **One-Click Auto-Fill**: Fill job application forms instantly with your profile data
- **Smart Field Detection**: Automatically detects and fills common form fields
- **Resume Upload**: Uploads your resume file directly
- **Cover Letter**: Pastes your customized cover letter
- **Work Authorization**: Fills sponsorship and authorization questions
- **Multi-ATS Support**: Works with Greenhouse, Lever, Ashby, Workable, SmartRecruiters, and more

## Supported ATS Platforms

- Greenhouse
- Lever
- Ashby
- Workable
- SmartRecruiters
- Pinpoint
- BambooHR
- Teamtailor
- Jobvite
- Workday
- Taleo
- iCIMS

## Installation (Chrome/Edge)

1. **Download the extension folder**
   - Download or clone this `/browser-extension` folder to your computer

2. **Open Chrome Extensions**
   - Go to `chrome://extensions/` in Chrome
   - Or `edge://extensions/` in Microsoft Edge

3. **Enable Developer Mode**
   - Toggle "Developer mode" switch in the top right corner

4. **Load the Extension**
   - Click "Load unpacked"
   - Select the `browser-extension` folder

5. **Pin the Extension**
   - Click the puzzle piece icon in your toolbar
   - Pin "JobMatch AI - Auto-Fill" for easy access

## Usage

1. **Connect Your Account**
   - Click the JobMatch AI extension icon
   - Enter your JobMatch AI URL (e.g., `https://your-app.emergentagent.com`)
   - Make sure you're logged in to JobMatch AI website
   - Click "Connect Account"

2. **Auto-Fill Applications**
   - Navigate to any job application page (Greenhouse, Lever, etc.)
   - Click the JobMatch AI extension icon
   - You'll see "✅ [ATS Name] Detected"
   - Click "Auto-Fill Application"
   - Review the filled fields and submit!

## What Gets Filled

| Field | Source |
|-------|--------|
| First Name | Profile |
| Last Name | Profile |
| Email | Profile |
| Phone | Profile (E.164 format) |
| LinkedIn | Profile |
| GitHub | Profile |
| Portfolio | Profile |
| City, State, Country | Profile |
| Work Authorization | Profile |
| Resume | Uploaded file |
| Cover Letter | Generated text |

## Troubleshooting

### "Please log in to JobMatch AI website first"
- Open JobMatch AI in a new tab and sign in
- Then try connecting again

### Fields not filling
- Some ATS platforms use non-standard field names
- You may need to manually fill some fields
- Check the results list in the extension popup

### Resume not uploading
- Make sure you have a resume file uploaded to your profile
- Some file upload fields may require manual upload

## Privacy & Security

- Your data is fetched directly from your JobMatch AI account
- No data is stored in the extension beyond your API URL
- The extension only runs on supported ATS domains
- All communication uses HTTPS

## Development

The extension is built with:
- Manifest V3
- Vanilla JavaScript
- Chrome Extension APIs

### File Structure
```
browser-extension/
├── manifest.json      # Extension configuration
├── popup.html         # Extension popup UI
├── popup.js           # Popup logic
├── content.js         # Content script for form filling
├── content.css        # Visual feedback styles
├── background.js      # Service worker
└── icons/             # Extension icons
```

## Support

If you encounter issues, check the browser console for error messages prefixed with `[JobMatch AI]`.
