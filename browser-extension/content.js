// JobMatch AI - Content Script
// Optimized for Greenhouse react-select dropdowns

(function() {
  'use strict';

  const DEBUG = true;

  function log(...args) {
    if (DEBUG) console.log('[JobMatch AI]', ...args);
  }

  // Listen for messages from popup
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

  // ============================
  // MAIN AUTO-FILL HANDLER
  // ============================

  async function handleAutoFill(data) {
    const results = {
      success: false,
      filled: [],
      failed: [],
      skipped: [],
      filledCount: 0
    };

    try {
      log('=== AUTO-FILL STARTED ===');
      log('URL:', window.location.href);

      // Build profile from data
      const profile = buildProfile(data);
      log('Profile loaded:', {
        name: profile.fullName,
        location: `${profile.city}, ${profile.state}, ${profile.country}`,
        requiresSponsorship: profile.requiresSponsorship,
        willingToRelocate: profile.willingToRelocate,
        noticePeriod: profile.noticePeriod,
      });

      // 1. Fill text fields first
      await fillTextFields(data, profile, results);

      // 2. Handle file uploads
      await handleFileUploads(data, results);

      // 3. Fill react-select dropdowns (Greenhouse custom questions)
      log('\n=== PROCESSING DROPDOWN QUESTIONS ===');
      await fillReactSelectDropdowns(profile, results);

      results.success = results.filled.length > 0;
      results.filledCount = results.filled.length;

      log('\n=== AUTO-FILL COMPLETE ===');
      log('Filled:', results.filled);
      log('Failed:', results.failed);
      log('Skipped:', results.skipped);

    } catch (error) {
      log('Auto-fill error:', error);
      results.failed.push(`Error: ${error.message}`);
    }

    return results;
  }

  function buildProfile(data) {
    return {
      firstName: data.personal_info?.first_name || '',
      lastName: data.personal_info?.last_name || '',
      fullName: data.personal_info?.full_name || '',
      email: data.personal_info?.email || '',
      phone: data.personal_info?.phone || '',
      linkedinUrl: data.personal_info?.linkedin || '',
      githubUrl: data.personal_info?.github || '',
      portfolioUrl: data.personal_info?.portfolio || '',
      city: data.personal_info?.location?.city || '',
      state: data.personal_info?.location?.state || '',
      country: data.personal_info?.location?.country || '',
      countryFull: data.profile_context?.country || data.personal_info?.location?.country || '',
      workAuthorizationStatus: data.profile_context?.work_authorization || '',
      requiresSponsorship: data.profile_context?.requires_sponsorship,
      skills: data.profile_context?.skills || [],
      skillsWithYears: data.profile_context?.skills_with_years || [],
      experienceYears: data.profile_context?.experience_years,
      resumeText: data.profile_context?.resume_text || '',
      education: data.profile_context?.education || '',
      willingToRelocate: data.profile_context?.willing_to_relocate || '',
      noticePeriod: data.profile_context?.notice_period || '',
      workArrangement: data.profile_context?.work_arrangement || '',
      referralSource: data.profile_context?.referral_source || 'LinkedIn',
      salaryMin: data.profile_context?.salary_min,
      salaryMax: data.profile_context?.salary_max,
    };
  }

  // ============================
  // REACT-SELECT DROPDOWN HANDLER
  // ============================

  async function fillReactSelectDropdowns(profile, results) {
    // Find all react-select containers (Greenhouse uses .select-shell or .select__container)
    const selectContainers = document.querySelectorAll('.select__container, .select-shell');
    log(`Found ${selectContainers.length} react-select dropdowns`);

    for (const container of selectContainers) {
      await processReactSelect(container, profile, results);
      await sleep(100); // Small delay between dropdowns
    }
  }

  async function processReactSelect(container, profile, results) {
    // Find the label
    const label = findLabelForContainer(container);
    if (!label) {
      return;
    }

    const questionText = label.toLowerCase();
    
    // Skip EEO/demographic questions
    if (shouldSkipQuestion(questionText)) {
      log(`Skipping (EEO/demographic): ${label.substring(0, 40)}`);
      results.skipped.push(`${label.substring(0, 40)} (EEO)`);
      return;
    }

    // Check if already filled
    const placeholder = container.querySelector('.select__placeholder');
    const singleValue = container.querySelector('.select__single-value');
    if (singleValue && singleValue.textContent && !singleValue.textContent.includes('Select')) {
      log(`Already filled: ${label.substring(0, 40)}`);
      return;
    }

    // Determine the answer based on question
    const answer = getAnswerForQuestion(questionText, profile);
    if (!answer) {
      log(`No answer for: ${label.substring(0, 40)}`);
      results.skipped.push(`${label.substring(0, 40)} (no profile match)`);
      return;
    }

    log(`\n--- Processing: "${label.substring(0, 50)}" ---`);
    log(`Answer to fill: "${answer}"`);

    // Find the combobox input element
    const combobox = container.querySelector('input[role="combobox"]');
    if (!combobox) {
      log('No combobox found');
      results.failed.push(`${label.substring(0, 40)} (no combobox)`);
      return;
    }

    // Click the control to open the dropdown
    const control = container.querySelector('.select__control');
    if (control) {
      control.click();
      await sleep(300);
    }

    // Wait for menu to appear and find options
    let options = [];
    for (let attempt = 0; attempt < 5; attempt++) {
      await sleep(200);
      options = findReactSelectOptions();
      if (options.length > 0) break;
    }

    log(`Options found: ${options.length}`);
    if (options.length > 0) {
      log(`Available options:`, options.slice(0, 10).map(o => o.text));
    }

    if (options.length === 0) {
      // Try typing to filter/trigger options
      combobox.focus();
      await simulateTyping(combobox, answer.substring(0, 3));
      await sleep(300);
      options = findReactSelectOptions();
      log(`Options after typing: ${options.length}`);
    }

    if (options.length === 0) {
      log('No options found');
      closeDropdown();
      results.failed.push(`${label.substring(0, 40)} (no options)`);
      return;
    }

    // Find best matching option
    const bestOption = findBestOption(options, answer);
    if (!bestOption) {
      log(`No match for answer "${answer}"`);
      closeDropdown();
      results.failed.push(`${label.substring(0, 40)} (no match)`);
      return;
    }

    log(`Selecting: "${bestOption.text}"`);
    
    // Click the option
    bestOption.el.click();
    await sleep(100);

    results.filled.push(`${label.substring(0, 40)} → ${bestOption.text}`);
  }

  function findReactSelectOptions() {
    const options = [];
    
    // React-select renders menu in a portal or as sibling - look globally
    const selectors = [
      '.select__menu .select__option',
      '[class*="menu"] [class*="option"]',
      '.remix-css-1nmdiq5-menu [class*="option"]', // Greenhouse specific
      '[id*="react-select"][id*="option"]',
    ];

    for (const selector of selectors) {
      document.querySelectorAll(selector).forEach(el => {
        if (isVisible(el)) {
          const text = el.textContent?.trim();
          if (text && text.length > 0 && !text.toLowerCase().includes('no options')) {
            options.push({ el, text });
          }
        }
      });
      if (options.length > 0) break;
    }

    // Also check for portal-rendered menus
    if (options.length === 0) {
      const portalMount = document.getElementById('react-portal-mount-point');
      if (portalMount) {
        portalMount.querySelectorAll('[class*="option"]').forEach(el => {
          if (isVisible(el)) {
            const text = el.textContent?.trim();
            if (text && text.length > 0) {
              options.push({ el, text });
            }
          }
        });
      }
    }

    return options;
  }

  function findLabelForContainer(container) {
    // Check for associated label
    const labelEl = container.querySelector('.select__label, label');
    if (labelEl) {
      return labelEl.textContent?.replace('*', '').trim();
    }

    // Check parent for label
    const parent = container.closest('.select');
    if (parent) {
      const label = parent.querySelector('label');
      if (label) return label.textContent?.replace('*', '').trim();
    }

    // Check aria-labelledby
    const combobox = container.querySelector('input[role="combobox"]');
    if (combobox) {
      const labelledBy = combobox.getAttribute('aria-labelledby');
      if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return labelEl.textContent?.replace('*', '').trim();
      }
    }

    return null;
  }

  function shouldSkipQuestion(questionText) {
    const skipPatterns = [
      /gender/i, /race/i, /ethnicity/i, /veteran/i, /disability/i,
      /hispanic/i, /latino/i, /equal.?opportunity/i, /eeo/i,
      /demographic/i, /diversity/i, /orientation/i, /pronouns/i
    ];
    return skipPatterns.some(pattern => pattern.test(questionText));
  }

  // ============================
  // ANSWER MATCHING
  // ============================

  function getAnswerForQuestion(questionText, profile) {
    const q = questionText.toLowerCase();

    // Employment agreements / non-compete
    if (q.includes('employment agreement') || q.includes('post-employment') || q.includes('restriction') || q.includes('non-compete')) {
      return 'No';
    }

    // Sponsorship
    if (q.includes('sponsorship') || q.includes('visa') && (q.includes('require') || q.includes('need'))) {
      return profile.requiresSponsorship ? 'Yes' : 'No';
    }

    // Previously worked at company
    if (q.includes('previously worked') || q.includes('consulted for') || q.includes('worked at')) {
      return 'No';
    }

    // Years of experience with specific skill
    if (q.includes('years') && q.includes('experience')) {
      // Check for skill-specific questions
      const skillMatch = q.match(/experience (?:with|in|using|working with) ([a-zA-Z0-9\s]+)/i);
      if (skillMatch) {
        const skill = skillMatch[1].trim().toLowerCase();
        // Check if user has this skill
        if (profile.resumeText?.toLowerCase().includes(skill) || 
            profile.skills?.some(s => s.toLowerCase().includes(skill))) {
          return 'Yes';
        }
        return 'No';
      }
      // General experience question
      return profile.experienceYears ? 'Yes' : 'No';
    }

    // B2B SaaS / technology company experience
    if (q.includes('b2b') || q.includes('saas') || q.includes('technology company')) {
      const techKeywords = ['saas', 'software', 'technology', 'tech', 'b2b', 'startup'];
      const hasExperience = techKeywords.some(kw => 
        profile.resumeText?.toLowerCase().includes(kw)
      );
      return hasExperience ? 'Yes' : 'No';
    }

    // Location - US or Canada
    if ((q.includes('located') || q.includes('reside')) && (q.includes('us') || q.includes('canada') || q.includes('united states'))) {
      const loc = `${profile.city} ${profile.state} ${profile.country} ${profile.countryFull}`.toLowerCase();
      const isUSCanada = loc.includes('canada') || loc.includes('us') || 
                        loc.includes('united states') || loc.includes('america') ||
                        profile.country?.toUpperCase() === 'CA' || 
                        profile.country?.toUpperCase() === 'US';
      return isUSCanada ? 'Yes' : 'No';
    }

    // Country of residence
    if (q.includes('country of residence') || q.includes('current country') || q.includes('what country')) {
      return profile.countryFull || profile.country || 'Canada';
    }

    // Relocation
    if (q.includes('relocat')) {
      return profile.willingToRelocate || 'No';
    }

    // Notice period / availability
    if (q.includes('notice period') || q.includes('availability') || q.includes('how soon') || q.includes('when can you start')) {
      return profile.noticePeriod || 'Immediately available';
    }

    // Work arrangement (remote/hybrid/onsite)
    if (q.includes('work arrangement') || q.includes('work preference') || (q.includes('remote') && q.includes('hybrid'))) {
      return profile.workArrangement || 'Remote';
    }

    // Comfortable working remotely
    if (q.includes('remote') && (q.includes('comfortable') || q.includes('open to'))) {
      const arr = profile.workArrangement?.toLowerCase();
      return ['remote', 'hybrid', 'flexible'].includes(arr) ? 'Yes' : 'No';
    }

    // Education
    if (q.includes('education') || q.includes('degree')) {
      return profile.education || null;
    }

    // Age 18+
    if (q.includes('18 years') || q.includes('legal age')) {
      return 'Yes';
    }

    // Background check
    if (q.includes('background check')) {
      return 'Yes';
    }

    // How did you hear
    if (q.includes('how did you hear') || q.includes('how did you find') || q.includes('source')) {
      return profile.referralSource || 'LinkedIn';
    }

    // Preferred name
    if (q.includes('preferred name') || q.includes("name you'd prefer") || q.includes('call you')) {
      return profile.firstName || null;
    }

    return null;
  }

  function findBestOption(options, answer) {
    if (!answer || !options.length) return null;

    const answerLower = answer.toLowerCase().trim();
    const answerNormalized = normalize(answerLower);

    // Exact match
    for (const opt of options) {
      if (opt.text.toLowerCase().trim() === answerLower) {
        return opt;
      }
    }

    // Normalized exact match
    for (const opt of options) {
      if (normalize(opt.text.toLowerCase()) === answerNormalized) {
        return opt;
      }
    }

    // Contains match
    for (const opt of options) {
      const optLower = opt.text.toLowerCase();
      if (optLower.includes(answerLower) || answerLower.includes(optLower)) {
        return opt;
      }
    }

    // Yes/No synonym matching
    if (['yes', 'no'].includes(answerLower)) {
      const yesSynonyms = ['yes', 'true', 'i do', 'i have', 'i will', 'i am'];
      const noSynonyms = ['no', 'false', 'i do not', 'i don\'t', 'i have not', 'i will not', 'i am not', 'none'];
      
      const synonyms = answerLower === 'yes' ? yesSynonyms : noSynonyms;
      
      for (const opt of options) {
        const optLower = opt.text.toLowerCase();
        if (synonyms.some(syn => optLower === syn || optLower.startsWith(syn + ' ') || optLower.includes(syn))) {
          return opt;
        }
      }
    }

    // Country matching
    if (answerLower === 'canada' || answerLower === 'ca') {
      for (const opt of options) {
        if (opt.text.toLowerCase().includes('canada')) return opt;
      }
    }
    if (answerLower === 'united states' || answerLower === 'us' || answerLower === 'usa') {
      for (const opt of options) {
        if (opt.text.toLowerCase().includes('united states') || opt.text === 'US') return opt;
      }
    }

    return null;
  }

  function normalize(str) {
    return str.replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
  }

  // ============================
  // TEXT FIELD FILLING
  // ============================

  async function fillTextFields(data, profile, results) {
    const personalInfo = data.personal_info || {};

    // First name
    if (personalInfo.first_name) {
      if (await fillInput(['#first_name', 'input[name*="first_name"]', 'input[autocomplete="given-name"]'], personalInfo.first_name)) {
        results.filled.push('First Name');
      }
    }

    // Last name
    if (personalInfo.last_name) {
      if (await fillInput(['#last_name', 'input[name*="last_name"]', 'input[autocomplete="family-name"]'], personalInfo.last_name)) {
        results.filled.push('Last Name');
      }
    }

    // Email
    if (personalInfo.email) {
      if (await fillInput(['#email', 'input[type="email"]', 'input[name*="email"]'], personalInfo.email)) {
        results.filled.push('Email');
      }
    }

    // Phone
    if (personalInfo.phone) {
      if (await fillInput(['#phone', 'input[type="tel"]', 'input[name*="phone"]'], personalInfo.phone)) {
        results.filled.push('Phone');
      }
    }

    // LinkedIn
    if (personalInfo.linkedin) {
      if (await fillInput(['input[name*="linkedin" i]', 'input[id*="linkedin" i]', 'input[placeholder*="linkedin" i]'], personalInfo.linkedin)) {
        results.filled.push('LinkedIn Profile');
      }
    }

    // City
    if (personalInfo.location?.city) {
      if (await fillInput(['input[name*="city"]', 'input[id*="city"]'], personalInfo.location.city)) {
        results.filled.push('City');
      }
    }

    // Custom text questions - preferred name
    const preferredNameSelectors = Array.from(document.querySelectorAll('label')).filter(l => 
      l.textContent?.toLowerCase().includes('prefer') && l.textContent?.toLowerCase().includes('name')
    );
    for (const label of preferredNameSelectors) {
      const forId = label.getAttribute('for');
      if (forId) {
        const input = document.getElementById(forId);
        if (input && input.tagName === 'INPUT' && !input.value) {
          await fillInput([`#${forId}`], profile.firstName);
          results.filled.push("What's the name you'd prefer us to use");
        }
      }
    }
  }

  async function fillInput(selectors, value) {
    if (!value) return false;

    for (const selector of selectors) {
      try {
        const element = document.querySelector(selector);
        if (element && !element.value) {
          element.focus();
          
          // Use native setter for React compatibility
          const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          )?.set;
          
          if (nativeSetter) {
            nativeSetter.call(element, value);
          } else {
            element.value = value;
          }
          
          element.dispatchEvent(new Event('input', { bubbles: true }));
          element.dispatchEvent(new Event('change', { bubbles: true }));
          element.blur();
          
          return true;
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    return false;
  }

  // ============================
  // FILE UPLOAD HANDLING
  // ============================

  async function handleFileUploads(data, results) {
    // Resume
    const resume = data.documents?.resume;
    if (resume?.file_data) {
      try {
        const fileInput = document.querySelector('#resume, input[type="file"][id*="resume"]');
        if (fileInput) {
          const file = base64ToFile(resume.file_data, resume.filename || 'resume.pdf', resume.mime_type || 'application/pdf');
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Resume (Optimized for this job)');
        }
      } catch (e) {
        log('Resume upload error:', e);
        results.failed.push('Resume upload');
      }
    }

    // Cover letter
    const coverLetter = data.documents?.cover_letter;
    if (coverLetter?.file_data) {
      try {
        const fileInput = document.querySelector('#cover_letter, input[type="file"][id*="cover_letter"]');
        if (fileInput) {
          const file = base64ToFile(coverLetter.file_data, coverLetter.filename || 'cover_letter.pdf', coverLetter.mime_type || 'application/pdf');
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Cover Letter (Optimized for this job)');
        }
      } catch (e) {
        log('Cover letter upload error:', e);
      }
    }
  }

  function base64ToFile(base64, filename, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mimeType });
    return new File([blob], filename, { type: mimeType });
  }

  // ============================
  // UTILITIES
  // ============================

  async function simulateTyping(element, text) {
    element.focus();
    for (const char of text) {
      element.dispatchEvent(new KeyboardEvent('keydown', { key: char, bubbles: true }));
      
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set;
      
      if (nativeSetter) {
        nativeSetter.call(element, element.value + char);
      } else {
        element.value += char;
      }
      
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new KeyboardEvent('keyup', { key: char, bubbles: true }));
      await sleep(30);
    }
  }

  function closeDropdown() {
    // Press Escape or click body to close
    document.body.click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 &&
           style.display !== 'none' && 
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  log('Content script loaded - Ready for Greenhouse forms');
})();
