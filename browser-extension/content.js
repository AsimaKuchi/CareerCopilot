// JobMatch AI - Content Script v3
// Debug version for Greenhouse react-select dropdowns

(function() {
  'use strict';

  const DEBUG = true;

  function log(...args) {
    console.log('[JobMatch AI]', ...args);
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
      log('=== AUTO-FILL STARTED (v3) ===');
      log('URL:', window.location.href);

      // Build profile from data
      const profile = buildProfile(data);
      log('Profile:', profile);

      // 1. Fill text fields first
      await fillTextFields(data, profile, results);

      // 2. Handle file uploads
      await handleFileUploads(data, results);

      // 3. Fill dropdowns - DIRECT APPROACH
      log('\n=== PROCESSING DROPDOWNS (Direct Approach) ===');
      
      // Find ALL elements with select__control class (the clickable part of react-select)
      const selectControls = document.querySelectorAll('.select__control');
      log(`Found ${selectControls.length} select controls on page`);

      for (let i = 0; i < selectControls.length; i++) {
        const control = selectControls[i];
        await processDropdownDirect(control, i, profile, results);
        await sleep(200);
      }

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

  // ============================
  // DIRECT DROPDOWN PROCESSING
  // ============================

  async function processDropdownDirect(control, index, profile, results) {
    // Find the label for this dropdown
    const container = control.closest('.select__container') || control.closest('.select');
    const label = findLabelText(container, control);
    
    log(`\n--- Dropdown #${index}: "${label || 'Unknown'}" ---`);

    if (!label) {
      log('Skipping - no label found');
      return;
    }

    // Skip EEO questions
    if (shouldSkipQuestion(label)) {
      log('Skipping - EEO/demographic question');
      results.skipped.push(`${label.substring(0, 30)} (EEO)`);
      return;
    }

    // Check if already has a value
    const singleValue = control.querySelector('.select__single-value');
    if (singleValue && singleValue.textContent && !singleValue.textContent.includes('Select')) {
      log('Already filled:', singleValue.textContent);
      return;
    }

    // Get the answer for this question
    const answer = getAnswerForQuestion(label.toLowerCase(), profile);
    if (!answer) {
      log('No answer found for this question');
      results.skipped.push(`${label.substring(0, 30)} (no match)`);
      return;
    }

    log('Answer to fill:', answer);

    // STEP 1: Click the control to open dropdown
    log('Step 1: Clicking control to open dropdown...');
    control.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    await sleep(50);
    control.click();
    await sleep(400);

    // STEP 2: Look for the menu that appeared
    log('Step 2: Looking for menu...');
    
    // Debug: Log all elements that might be menus
    const allMenus = document.querySelectorAll('[class*="menu"]');
    log(`Found ${allMenus.length} elements with "menu" in class`);
    
    // Try multiple selectors to find options
    let options = [];
    
    // Method 1: Standard react-select menu
    let menu = document.querySelector('.select__menu');
    if (menu) {
      log('Found .select__menu');
      const opts = menu.querySelectorAll('.select__option');
      log(`Found ${opts.length} .select__option elements`);
      opts.forEach(o => {
        if (isVisible(o)) {
          options.push({ el: o, text: o.textContent.trim() });
        }
      });
    }

    // Method 2: Any visible menu with options
    if (options.length === 0) {
      document.querySelectorAll('[class*="menu"]').forEach(m => {
        if (isVisible(m)) {
          m.querySelectorAll('[class*="option"]').forEach(o => {
            if (isVisible(o) && o.textContent.trim()) {
              options.push({ el: o, text: o.textContent.trim() });
            }
          });
        }
      });
    }

    // Method 3: Look in portal mount point
    if (options.length === 0) {
      const portal = document.getElementById('react-portal-mount-point');
      if (portal) {
        log('Checking portal mount point...');
        portal.querySelectorAll('[class*="option"]').forEach(o => {
          if (isVisible(o) && o.textContent.trim()) {
            options.push({ el: o, text: o.textContent.trim() });
          }
        });
      }
    }

    // Method 4: Any element with role="option"
    if (options.length === 0) {
      document.querySelectorAll('[role="option"]').forEach(o => {
        if (isVisible(o) && o.textContent.trim()) {
          options.push({ el: o, text: o.textContent.trim() });
        }
      });
    }

    // Method 5: Check if combobox input needs interaction
    if (options.length === 0) {
      log('No options found, trying to trigger via input...');
      const input = control.querySelector('input[role="combobox"]') || 
                    container?.querySelector('input[role="combobox"]');
      if (input) {
        log('Found combobox input, focusing and pressing arrow down...');
        input.focus();
        await sleep(100);
        
        // Try arrow down to open
        input.dispatchEvent(new KeyboardEvent('keydown', { 
          key: 'ArrowDown', 
          code: 'ArrowDown',
          keyCode: 40,
          bubbles: true 
        }));
        await sleep(400);
        
        // Look for options again
        document.querySelectorAll('[class*="option"], [role="option"]').forEach(o => {
          if (isVisible(o) && o.textContent.trim()) {
            options.push({ el: o, text: o.textContent.trim() });
          }
        });
      }
    }

    log(`Total options found: ${options.length}`);
    if (options.length > 0) {
      log('Options:', options.map(o => o.text));
    }

    if (options.length === 0) {
      log('FAILED: No options found');
      closeDropdown();
      results.failed.push(`${label.substring(0, 30)} (no options)`);
      return;
    }

    // STEP 3: Find and click the matching option
    log('Step 3: Finding matching option...');
    const bestOption = findBestOption(options, answer);
    
    if (!bestOption) {
      log('No matching option found');
      closeDropdown();
      results.failed.push(`${label.substring(0, 30)} (no match in options)`);
      return;
    }

    log('Clicking option:', bestOption.text);
    bestOption.el.click();
    await sleep(100);

    results.filled.push(`${label.substring(0, 30)} → ${bestOption.text}`);
    log('SUCCESS!');
  }

  function findLabelText(container, control) {
    // Try multiple ways to find the label
    
    // 1. Look for label in container
    if (container) {
      const label = container.querySelector('label, .label, .select__label');
      if (label) return label.textContent.replace(/\*/g, '').trim();
    }

    // 2. Check aria-labelledby on the input
    const input = control.querySelector('input');
    if (input) {
      const labelledBy = input.getAttribute('aria-labelledby');
      if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return labelEl.textContent.replace(/\*/g, '').trim();
      }
    }

    // 3. Look at parent elements
    let parent = control.parentElement;
    for (let i = 0; i < 5 && parent; i++) {
      const label = parent.querySelector('label');
      if (label) return label.textContent.replace(/\*/g, '').trim();
      parent = parent.parentElement;
    }

    return null;
  }

  function shouldSkipQuestion(label) {
    const lower = label.toLowerCase();
    return /gender|race|ethnicity|veteran|disability|hispanic|latino|eeo|demographic/i.test(lower);
  }

  function getAnswerForQuestion(q, profile) {
    // Employment agreements
    if (q.includes('employment agreement') || q.includes('post-employment') || q.includes('restriction')) {
      return 'No';
    }

    // Sponsorship
    if (q.includes('sponsorship') || (q.includes('visa') && q.includes('require'))) {
      return profile.requiresSponsorship ? 'Yes' : 'No';
    }

    // Previously worked
    if (q.includes('previously worked') || q.includes('consulted for')) {
      return 'No';
    }

    // Location US/Canada
    if (q.includes('located') && (q.includes('us') || q.includes('canada'))) {
      const loc = `${profile.city} ${profile.state} ${profile.country}`.toLowerCase();
      return (loc.includes('canada') || loc.includes('us') || profile.country === 'CA') ? 'Yes' : 'No';
    }

    // Country of residence
    if (q.includes('country') && q.includes('residence')) {
      return profile.countryFull || 'Canada';
    }

    // Years of experience
    if (q.includes('years') && q.includes('experience')) {
      return 'Yes'; // Assume yes if they're applying
    }

    return null;
  }

  function findBestOption(options, answer) {
    const answerLower = answer.toLowerCase().trim();
    
    // Exact match
    for (const opt of options) {
      if (opt.text.toLowerCase().trim() === answerLower) {
        return opt;
      }
    }

    // Starts with
    for (const opt of options) {
      if (opt.text.toLowerCase().startsWith(answerLower)) {
        return opt;
      }
    }

    // Contains
    for (const opt of options) {
      if (opt.text.toLowerCase().includes(answerLower) || 
          answerLower.includes(opt.text.toLowerCase())) {
        return opt;
      }
    }

    return null;
  }

  function closeDropdown() {
    document.body.click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 &&
           style.display !== 'none' && 
           style.visibility !== 'hidden';
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============================
  // PROFILE BUILDER
  // ============================

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
      noticePeriod: data.profile_context?.notice_period || '',
      workArrangement: data.profile_context?.work_arrangement || '',
      resumeText: data.profile_context?.resume_text || '',
    };
  }

  // ============================
  // TEXT FIELDS
  // ============================

  async function fillTextFields(data, profile, results) {
    const pi = data.personal_info || {};

    if (pi.first_name && await fillInput('#first_name', pi.first_name)) {
      results.filled.push('First Name');
    }
    if (pi.last_name && await fillInput('#last_name', pi.last_name)) {
      results.filled.push('Last Name');
    }
    if (pi.email && await fillInput('#email', pi.email)) {
      results.filled.push('Email');
    }
    if (pi.phone && await fillInput('#phone', pi.phone)) {
      results.filled.push('Phone');
    }
    if (pi.linkedin) {
      const linkedinInput = document.querySelector('input[id*="linkedin" i], input[name*="linkedin" i]');
      if (linkedinInput && await fillInput(linkedinInput, pi.linkedin)) {
        results.filled.push('LinkedIn Profile');
      }
    }

    // Preferred name question
    const labels = document.querySelectorAll('label');
    for (const label of labels) {
      if (label.textContent.toLowerCase().includes('prefer') && 
          label.textContent.toLowerCase().includes('name')) {
        const forId = label.getAttribute('for');
        if (forId) {
          const input = document.getElementById(forId);
          if (input && input.tagName === 'INPUT' && !input.value) {
            await fillInput(input, profile.firstName);
            results.filled.push("Preferred Name");
          }
        }
      }
    }
  }

  async function fillInput(selectorOrEl, value) {
    const el = typeof selectorOrEl === 'string' ? 
               document.querySelector(selectorOrEl) : selectorOrEl;
    if (!el || el.value) return false;

    el.focus();
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  // ============================
  // FILE UPLOADS
  // ============================

  async function handleFileUploads(data, results) {
    const resume = data.documents?.resume;
    if (resume?.file_data) {
      const input = document.querySelector('#resume');
      if (input) {
        try {
          const file = b64ToFile(resume.file_data, resume.filename, resume.mime_type);
          const dt = new DataTransfer();
          dt.items.add(file);
          input.files = dt.files;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Resume');
        } catch (e) { log('Resume error:', e); }
      }
    }

    const cover = data.documents?.cover_letter;
    if (cover?.file_data) {
      const input = document.querySelector('#cover_letter');
      if (input) {
        try {
          const file = b64ToFile(cover.file_data, cover.filename, cover.mime_type);
          const dt = new DataTransfer();
          dt.items.add(file);
          input.files = dt.files;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Cover Letter');
        } catch (e) { log('Cover letter error:', e); }
      }
    }
  }

  function b64ToFile(b64, name, type) {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    return new File([arr], name || 'file.pdf', { type: type || 'application/pdf' });
  }

  log('Content script v3 loaded - Ready!');
})();
