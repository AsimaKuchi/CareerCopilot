// MyCareerCoPilot - Content Script v4
// Fixed for Greenhouse react-select - using keyboard navigation

(function() {
  'use strict';

  function log(...args) {
    console.log('[MyCareerCoPilot]', ...args);
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'AUTOFILL') {
      handleAutoFill(message.data).then(sendResponse);
      return true;
    }
    if (message.action === 'SET_API_URL') {
      sendResponse({ success: true });
      return true;
    }
  });

  async function handleAutoFill(data) {
    const results = {
      success: false,
      filled: [],
      failed: [],
      skipped: [],
      filledCount: 0
    };

    try {
      log('=== AUTO-FILL STARTED (v4) ===');

      const profile = buildProfile(data);
      log('Profile:', profile);

      // Fill text fields
      await fillTextFields(data, profile, results);
      await handleFileUploads(data, results);

      // Fill dropdowns using INPUT-BASED approach
      log('\n=== PROCESSING DROPDOWNS ===');
      
      // Find all combobox inputs (the actual interactive element in react-select)
      const comboboxInputs = document.querySelectorAll('input[role="combobox"]');
      log(`Found ${comboboxInputs.length} combobox inputs`);

      for (const input of comboboxInputs) {
        await processCombobox(input, profile, results);
        await sleep(300);
      }

      results.success = results.filled.length > 0;
      results.filledCount = results.filled.length;

      log('\n=== COMPLETE ===');
      log('Filled:', results.filled);
      log('Failed:', results.failed);

    } catch (error) {
      log('Error:', error);
    }

    return results;
  }

  async function processCombobox(input, profile, results) {
    // Get the label for this combobox
    const labelId = input.getAttribute('aria-labelledby');
    const label = labelId ? document.getElementById(labelId)?.textContent?.replace(/\*/g, '').trim() : null;
    
    if (!label) {
      log('Skipping input without label');
      return;
    }

    log(`\n--- Processing: "${label}" ---`);

    // Skip EEO questions
    if (/gender|race|ethnicity|veteran|disability|hispanic|latino/i.test(label)) {
      log('Skipping EEO question');
      results.skipped.push(`${label.substring(0, 30)} (EEO)`);
      return;
    }

    // Check if already has value (look for single-value element)
    const control = input.closest('.select__control') || input.closest('[class*="control"]');
    const container = control?.parentElement;
    const singleValue = container?.querySelector('.select__single-value, [class*="singleValue"]');
    if (singleValue?.textContent && !singleValue.textContent.includes('Select')) {
      log('Already filled:', singleValue.textContent);
      return;
    }

    // Get answer
    const answer = getAnswerForQuestion(label.toLowerCase(), profile);
    if (!answer) {
      log('No answer for this question');
      results.skipped.push(`${label.substring(0, 30)} (no match)`);
      return;
    }

    log('Answer:', answer);

    // OPEN THE DROPDOWN using keyboard
    log('Opening dropdown...');
    
    // Focus the input
    input.focus();
    await sleep(100);

    // Check current state
    log('aria-expanded before:', input.getAttribute('aria-expanded'));

    // Method 1: Click the parent control area
    if (control) {
      control.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
      await sleep(50);
      control.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
      await sleep(50);
      control.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    }
    await sleep(200);

    // Method 2: Press Space key on input
    input.dispatchEvent(new KeyboardEvent('keydown', { 
      key: ' ', 
      code: 'Space', 
      keyCode: 32, 
      which: 32,
      bubbles: true,
      cancelable: true
    }));
    await sleep(200);

    // Method 3: Press ArrowDown
    input.dispatchEvent(new KeyboardEvent('keydown', { 
      key: 'ArrowDown', 
      code: 'ArrowDown', 
      keyCode: 40, 
      which: 40,
      bubbles: true,
      cancelable: true
    }));
    await sleep(300);

    log('aria-expanded after:', input.getAttribute('aria-expanded'));

    // Find options - look EVERYWHERE on the page
    let options = findAllVisibleOptions();
    log(`Found ${options.length} options`);
    
    if (options.length > 0) {
      log('Options:', options.slice(0, 5).map(o => o.text));
    }

    if (options.length === 0) {
      // Try typing to trigger autocomplete
      log('Trying to type answer...');
      await typeIntoInput(input, answer.substring(0, 3));
      await sleep(400);
      options = findAllVisibleOptions();
      log(`After typing, found ${options.length} options`);
    }

    if (options.length === 0) {
      log('FAILED: No options found');
      closeDropdown(input);
      results.failed.push(`${label.substring(0, 30)} (no options)`);
      return;
    }

    // Find matching option
    const match = findBestMatch(options, answer);
    if (!match) {
      log('No matching option');
      closeDropdown(input);
      results.failed.push(`${label.substring(0, 30)} (no match)`);
      return;
    }

    log('Selecting:', match.text);
    
    // Click the option
    match.el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    await sleep(50);
    match.el.click();
    await sleep(100);

    results.filled.push(`${label.substring(0, 30)} → ${match.text}`);
    log('SUCCESS');
  }

  function findAllVisibleOptions() {
    const options = [];
    const seen = new Set();

    // All possible option selectors
    const selectors = [
      '.select__option',
      '[class*="option"]',
      '[role="option"]',
      '[id*="option"]',
      '.select__menu-list > div',
      '[class*="menu"] > div',
      '[class*="Menu"] > div'
    ];

    for (const selector of selectors) {
      document.querySelectorAll(selector).forEach(el => {
        const text = el.textContent?.trim();
        if (text && !seen.has(text) && isVisible(el) && text.length < 200) {
          // Skip placeholder texts
          if (!/^select|^choose|^--/i.test(text) && text !== 'No options') {
            seen.add(text);
            options.push({ el, text });
          }
        }
      });
    }

    return options;
  }

  async function typeIntoInput(input, text) {
    input.focus();
    
    // Clear any existing value
    const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (nativeSetter) {
      nativeSetter.call(input, '');
    }
    input.dispatchEvent(new Event('input', { bubbles: true }));
    
    // Type each character
    for (const char of text) {
      if (nativeSetter) {
        nativeSetter.call(input, input.value + char);
      } else {
        input.value += char;
      }
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keydown', { key: char, bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keyup', { key: char, bubbles: true }));
      await sleep(50);
    }
  }

  function closeDropdown(input) {
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    document.body.click();
  }

  function findBestMatch(options, answer) {
    const answerLower = answer.toLowerCase().trim();
    
    // Exact
    for (const o of options) {
      if (o.text.toLowerCase().trim() === answerLower) return o;
    }
    
    // Starts with
    for (const o of options) {
      if (o.text.toLowerCase().startsWith(answerLower)) return o;
    }
    
    // Contains
    for (const o of options) {
      if (o.text.toLowerCase().includes(answerLower)) return o;
    }
    
    // Answer contains option
    for (const o of options) {
      if (answerLower.includes(o.text.toLowerCase())) return o;
    }

    return null;
  }

  function getAnswerForQuestion(q, profile) {
    if (q.includes('employment agreement') || q.includes('post-employment') || q.includes('restriction')) {
      return 'No';
    }
    if (q.includes('sponsorship') || (q.includes('visa') && q.includes('require'))) {
      return profile.requiresSponsorship ? 'Yes' : 'No';
    }
    if (q.includes('previously worked') || q.includes('consulted for')) {
      return 'No';
    }
    if (q.includes('located') && (q.includes('us') || q.includes('canada'))) {
      const loc = `${profile.city} ${profile.state} ${profile.country}`.toLowerCase();
      return (loc.includes('canada') || loc.includes('us') || profile.country === 'CA') ? 'Yes' : 'No';
    }
    if (q.includes('country') && q.includes('residence')) {
      return profile.countryFull || 'Canada';
    }
    if (q.includes('experience') && (q.includes('supporting') || q.includes('managing') || q.includes('working'))) {
      return 'Yes';
    }
    if (q.includes('google suite') || q.includes('calendar') || q.includes('timezone')) {
      return 'Yes';
    }
    return null;
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && 
           style.display !== 'none' && 
           style.visibility !== 'hidden' &&
           parseFloat(style.opacity) > 0;
  }

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  function buildProfile(data) {
    return {
      firstName: data.personal_info?.first_name || '',
      lastName: data.personal_info?.last_name || '',
      fullName: data.personal_info?.full_name || '',
      email: data.personal_info?.email || '',
      phone: data.personal_info?.phone || '',
      linkedinUrl: data.personal_info?.linkedin || '',
      city: data.personal_info?.location?.city || '',
      state: data.personal_info?.location?.state || '',
      country: data.personal_info?.location?.country || '',
      countryFull: data.profile_context?.country || '',
      requiresSponsorship: data.profile_context?.requires_sponsorship,
      willingToRelocate: data.profile_context?.willing_to_relocate || '',
      resumeText: data.profile_context?.resume_text || '',
    };
  }

  async function fillTextFields(data, profile, results) {
    const pi = data.personal_info || {};
    
    // ========================================
    // GENERIC FIELD FILLING - works on any site
    // ========================================
    
    // First Name - try multiple selectors and label patterns
    if (pi.first_name) {
      const filled = await fillFieldByPatterns(
        [
          '#first_name', 
          'input[name="first_name"]',
          'input[name="firstName"]',
          'input[name="fname"]',
          'input[id*="first" i][id*="name" i]',
          'input[name*="first" i][name*="name" i]',
          'input[autocomplete="given-name"]',
          'input[placeholder*="first name" i]'
        ],
        ['first name', 'given name', 'prénom'],
        pi.first_name
      );
      if (filled) results.filled.push('First Name');
    }
    
    // Last Name
    if (pi.last_name) {
      const filled = await fillFieldByPatterns(
        [
          '#last_name',
          'input[name="last_name"]',
          'input[name="lastName"]',
          'input[name="lname"]',
          'input[id*="last" i][id*="name" i]',
          'input[name*="last" i][name*="name" i]',
          'input[autocomplete="family-name"]',
          'input[placeholder*="last name" i]'
        ],
        ['last name', 'family name', 'surname', 'nom de famille'],
        pi.last_name
      );
      if (filled) results.filled.push('Last Name');
    }
    
    // Email
    if (pi.email) {
      const filled = await fillFieldByPatterns(
        [
          '#email',
          'input[type="email"]',
          'input[name="email"]',
          'input[name="emailAddress"]',
          'input[id*="email" i]',
          'input[autocomplete="email"]',
          'input[placeholder*="email" i]'
        ],
        ['email', 'e-mail', 'courriel'],
        pi.email
      );
      if (filled) results.filled.push('Email');
    }
    
    // Phone
    if (pi.phone) {
      const filled = await fillFieldByPatterns(
        [
          '#phone',
          'input[type="tel"]',
          'input[name="phone"]',
          'input[name="phoneNumber"]',
          'input[name="telephone"]',
          'input[id*="phone" i]',
          'input[autocomplete="tel"]',
          'input[placeholder*="phone" i]'
        ],
        ['phone', 'telephone', 'mobile', 'cell', 'téléphone'],
        pi.phone
      );
      if (filled) results.filled.push('Phone');
    }
    
    // LinkedIn
    if (pi.linkedin) {
      const filled = await fillFieldByPatterns(
        [
          'input[id*="linkedin" i]',
          'input[name*="linkedin" i]',
          'input[placeholder*="linkedin" i]'
        ],
        ['linkedin'],
        pi.linkedin
      );
      if (filled) results.filled.push('LinkedIn');
    }
    
    // GitHub
    if (pi.github) {
      const filled = await fillFieldByPatterns(
        [
          'input[id*="github" i]',
          'input[name*="github" i]',
          'input[placeholder*="github" i]'
        ],
        ['github'],
        pi.github
      );
      if (filled) results.filled.push('GitHub');
    }
    
    // Portfolio/Website
    if (pi.portfolio) {
      const filled = await fillFieldByPatterns(
        [
          'input[id*="portfolio" i]',
          'input[id*="website" i]',
          'input[name*="portfolio" i]',
          'input[name*="website" i]',
          'input[type="url"]'
        ],
        ['portfolio', 'website', 'personal site'],
        pi.portfolio
      );
      if (filled) results.filled.push('Portfolio/Website');
    }
    
    // Full Name (if site asks for combined name)
    if (pi.full_name || (pi.first_name && pi.last_name)) {
      const fullName = pi.full_name || `${pi.first_name} ${pi.last_name}`;
      const filled = await fillFieldByPatterns(
        [
          'input[name="full_name"]',
          'input[name="fullName"]',
          'input[name="name"]',
          'input[autocomplete="name"]'
        ],
        ['full name', 'your name', 'name'],
        fullName,
        true // exactLabelMatch to avoid matching "first name" or "last name"
      );
      if (filled) results.filled.push('Full Name');
    }
    
    // City
    if (profile.city) {
      const filled = await fillFieldByPatterns(
        [
          'input[name="city"]',
          'input[id*="city" i]',
          'input[autocomplete="address-level2"]'
        ],
        ['city', 'ville'],
        profile.city
      );
      if (filled) results.filled.push('City');
    }
    
    // Preferred name
    for (const label of document.querySelectorAll('label')) {
      if (/prefer.*name/i.test(label.textContent)) {
        const forId = label.getAttribute('for');
        if (forId) {
          const inp = document.getElementById(forId);
          if (inp?.tagName === 'INPUT' && !inp.value && inp.type !== 'password') {
            await fillInput(inp, profile.firstName);
            results.filled.push('Preferred Name');
          }
        }
      }
    }
  }
  
  // Helper to fill field by CSS selectors or label text
  async function fillFieldByPatterns(selectors, labelPatterns, value, exactLabelMatch = false) {
    if (!value) return false;
    
    // Try CSS selectors first
    for (const sel of selectors) {
      try {
        const el = document.querySelector(sel);
        if (el && !el.value && el.type !== 'password' && el.type !== 'hidden' && isVisible(el)) {
          log(`Filling ${sel} with value`);
          return await fillInput(el, value);
        }
      } catch (e) {
        // Invalid selector, skip
      }
    }
    
    // Try finding by label text
    for (const label of document.querySelectorAll('label')) {
      const labelText = label.textContent.toLowerCase().replace(/\*/g, '').trim();
      
      for (const pattern of labelPatterns) {
        const matches = exactLabelMatch 
          ? labelText === pattern.toLowerCase()
          : labelText.includes(pattern.toLowerCase());
          
        if (matches) {
          // Find associated input
          const forId = label.getAttribute('for');
          let input = forId ? document.getElementById(forId) : null;
          
          // If no "for" attribute, look for input inside or next to label
          if (!input) {
            input = label.querySelector('input:not([type="password"]):not([type="hidden"])');
          }
          if (!input) {
            input = label.parentElement?.querySelector('input:not([type="password"]):not([type="hidden"])');
          }
          if (!input) {
            // Check next sibling
            const next = label.nextElementSibling;
            if (next?.tagName === 'INPUT' && next.type !== 'password' && next.type !== 'hidden') {
              input = next;
            }
          }
          
          if (input && !input.value && input.type !== 'password' && isVisible(input)) {
            log(`Filling by label "${pattern}" with value`);
            return await fillInput(input, value);
          }
        }
      }
    }
    
    return false;
  }

  async function fillInput(sel, val) {
    const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
    if (!el || el.value) return false;
    el.focus();
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (setter) setter.call(el, val);
    else el.value = val;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  async function handleFileUploads(data, results) {
    const resume = data.documents?.resume;
    if (resume?.file_data) {
      log('Resume data found:', {
        filename: resume.filename,
        isOptimized: resume.is_optimized,
        hasFileData: !!resume.file_data,
        mimeType: resume.mime_type
      });
      
      // Try multiple selectors for resume file input
      const resumeSelectors = [
        '#resume',
        'input[type="file"][name*="resume" i]',
        'input[type="file"][id*="resume" i]',
        'input[type="file"][name*="cv" i]',
        'input[type="file"][id*="cv" i]',
        'input[type="file"][accept*="pdf"]',
        'input[type="file"][accept*="doc"]',
        'input[type="file"]:not([name*="cover" i]):not([name*="letter" i])'
      ];
      
      let inp = null;
      for (const sel of resumeSelectors) {
        inp = document.querySelector(sel);
        if (inp) {
          log(`Found resume input: ${sel}`);
          break;
        }
      }
      
      // Also try finding by label text
      if (!inp) {
        for (const label of document.querySelectorAll('label')) {
          const text = label.textContent.toLowerCase();
          if (text.includes('resume') || text.includes('cv') || text.includes('curriculum')) {
            const forId = label.getAttribute('for');
            if (forId) {
              inp = document.getElementById(forId);
              if (inp?.type === 'file') break;
            }
            // Check for input inside label
            const fileInput = label.querySelector('input[type="file"]');
            if (fileInput) {
              inp = fileInput;
              break;
            }
            // Check parent/siblings
            const parent = label.closest('div, fieldset, section');
            if (parent) {
              inp = parent.querySelector('input[type="file"]');
              if (inp) break;
            }
          }
        }
      }
      
      if (inp) {
        try {
          const f = b64ToFile(resume.file_data, resume.filename, resume.mime_type);
          const dt = new DataTransfer();
          dt.items.add(f);
          inp.files = dt.files;
          inp.dispatchEvent(new Event('change', { bubbles: true }));
          inp.dispatchEvent(new Event('input', { bubbles: true }));
          
          const label = resume.is_optimized ? 'Resume (Optimized for this job)' : 'Resume';
          results.filled.push(label);
          log(`Uploaded: ${label}`);
        } catch(e) {
          log('Resume upload error:', e);
          results.failed.push('Resume upload failed');
        }
      } else {
        log('Resume file input not found');
        results.skipped.push('Resume (no file input)');
      }
    } else {
      log('No resume file data available');
      results.skipped.push('Resume (no file data)');
    }
    
    const cover = data.documents?.cover_letter;
    if (cover?.file_data) {
      log('Cover letter data found:', {
        filename: cover.filename,
        isOptimized: cover.is_optimized,
        hasFileData: !!cover.file_data,
        mimeType: cover.mime_type
      });
      
      const inp = document.querySelector('#cover_letter');
      if (inp) {
        try {
          const f = b64ToFile(cover.file_data, cover.filename, cover.mime_type);
          const dt = new DataTransfer();
          dt.items.add(f);
          inp.files = dt.files;
          inp.dispatchEvent(new Event('change', { bubbles: true }));
          
          const label = cover.is_optimized ? 'Cover Letter (Optimized for this job)' : 'Cover Letter';
          results.filled.push(label);
          log(`Uploaded: ${label}`);
        } catch(e) {
          log('Cover letter upload error:', e);
          results.failed.push('Cover letter upload failed');
        }
      } else {
        log('Cover letter file input not found');
        results.skipped.push('Cover Letter (no file input)');
      }
    } else if (cover?.text) {
      // Try filling cover letter as text in a textarea
      log('Cover letter text found (no file data)');
      const textarea = document.querySelector('textarea[id*="cover" i], textarea[name*="cover" i]');
      if (textarea) {
        textarea.value = cover.text;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));
        const label = cover.is_optimized ? 'Cover Letter Text (Optimized)' : 'Cover Letter Text';
        results.filled.push(label);
      }
    }
  }

  function b64ToFile(b64, name, type) {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    return new File([arr], name || 'file.pdf', { type: type || 'application/pdf' });
  }

  // ========================================
  // SUBMISSION TRACKING
  // ========================================
  
  let submissionTracked = false; // Prevent duplicate tracking
  
  function extractJobInfo() {
    // Try to extract job title and company from the page
    let jobTitle = '';
    let company = '';
    
    // Common patterns for job title
    const titleSelectors = [
      'h1', // Most common
      '[data-testid="job-title"]',
      '.job-title',
      '.posting-headline h2',
      '[class*="JobTitle"]',
      '[class*="job-title"]'
    ];
    
    for (const selector of titleSelectors) {
      const el = document.querySelector(selector);
      if (el?.textContent?.trim()) {
        jobTitle = el.textContent.trim();
        break;
      }
    }
    
    // Common patterns for company name
    const companySelectors = [
      '[data-testid="company-name"]',
      '.company-name',
      '[class*="CompanyName"]',
      '[class*="company-name"]',
      '.posting-headline h1', // Greenhouse
      'meta[property="og:site_name"]'
    ];
    
    for (const selector of companySelectors) {
      const el = document.querySelector(selector);
      if (el) {
        company = el.getAttribute('content') || el.textContent?.trim() || '';
        if (company) break;
      }
    }
    
    // Fallback: try to get from page title
    if (!company && document.title) {
      const parts = document.title.split(/[|\-–]/);
      if (parts.length > 1) {
        company = parts[parts.length - 1].trim();
      }
    }
    
    return { jobTitle, company };
  }
  
  async function trackSubmission() {
    if (submissionTracked) {
      log('Submission already tracked, skipping');
      return;
    }
    
    submissionTracked = true;
    log('=== TRACKING SUBMISSION ===');
    
    const jobUrl = window.location.href;
    const { jobTitle, company } = extractJobInfo();
    
    log('Job URL:', jobUrl);
    log('Job Title:', jobTitle);
    log('Company:', company);
    
    // Send message to background script to make the API call
    // Background script has access to cookies for authentication
    chrome.runtime.sendMessage({
      action: 'TRACK_SUBMISSION',
      data: {
        job_url: jobUrl,
        job_title: jobTitle,
        company: company
      }
    }, (response) => {
      if (chrome.runtime.lastError) {
        log('Error sending to background:', chrome.runtime.lastError);
        return;
      }
      
      if (response?.success) {
        log('✅ Submission tracked successfully!');
        log('Application updated:', response.job_title, 'at', response.company);
        showSubmissionConfirmation(response);
      } else {
        log('⚠️ Could not track submission:', response?.message || 'Unknown error');
      }
    });
  }
  
  function showSubmissionConfirmation(data) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      max-width: 350px;
      animation: slideIn 0.3s ease-out;
    `;
    
    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 24px;">✓</div>
        <div>
          <div style="font-weight: 600; margin-bottom: 4px;">Application Submitted!</div>
          <div style="opacity: 0.9; font-size: 13px;">
            ${data.job_title ? `${data.job_title} at ` : ''}${data.company || 'Company'} - Tracked in MyCareerCoPilot
          </div>
        </div>
      </div>
    `;
    
    // Add animation keyframes
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }
  
  function setupSubmissionTracking() {
    log('Setting up submission tracking...');
    
    // Common submit button selectors for job applications
    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button[data-testid*="submit"]',
      'button[class*="submit"]',
      'button[class*="Submit"]',
      '#submit_app', // Greenhouse
      'button:contains("Submit")',
      'button:contains("Apply")',
      '[data-testid="submit-application"]',
      '.application-submit',
      // Greenhouse specific
      '#application_submit_button',
      'button[value="Submit Application"]',
      // Lever specific
      'button.postings-btn',
      // General patterns
      'button[type="submit"][class*="btn"]',
      'form button:last-of-type'
    ];
    
    // Find and attach listeners to submit buttons
    function attachSubmitListeners() {
      submitSelectors.forEach(selector => {
        try {
          const buttons = document.querySelectorAll(selector);
          buttons.forEach(button => {
            if (button.dataset.jobmatchTracked) return; // Already tracked
            
            const buttonText = (button.textContent || button.value || '').toLowerCase();
            // Only track buttons that look like submit buttons
            if (buttonText.includes('submit') || buttonText.includes('apply') || buttonText.includes('send')) {
              button.dataset.jobmatchTracked = 'true';
              
              button.addEventListener('click', (e) => {
                log('Submit button clicked:', buttonText);
                // Track after a short delay to allow form submission to complete
                setTimeout(() => trackSubmission(), 1500);
              });
              
              log('Attached listener to submit button:', buttonText);
            }
          });
        } catch (e) {
          // Selector might not be valid, ignore
        }
      });
    }
    
    // Also listen for form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form.tagName === 'FORM') {
        log('Form submitted');
        setTimeout(() => trackSubmission(), 1500);
      }
    }, true);
    
    // Run initially
    attachSubmitListeners();
    
    // Re-run when DOM changes (for SPAs)
    const observer = new MutationObserver(() => {
      attachSubmitListeners();
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    log('Submission tracking setup complete');
  }
  
  // Initialize submission tracking when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupSubmissionTracking);
  } else {
    setupSubmissionTracking();
  }

  log('Content script v4 loaded!');
})();
