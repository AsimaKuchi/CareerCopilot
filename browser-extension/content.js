// JobMatch AI - Content Script v4
// Fixed for Greenhouse react-select - using keyboard navigation

(function() {
  'use strict';

  function log(...args) {
    console.log('[JobMatch AI]', ...args);
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
    if (pi.first_name) await fillInput('#first_name', pi.first_name) && results.filled.push('First Name');
    if (pi.last_name) await fillInput('#last_name', pi.last_name) && results.filled.push('Last Name');
    if (pi.email) await fillInput('#email', pi.email) && results.filled.push('Email');
    if (pi.phone) await fillInput('#phone', pi.phone) && results.filled.push('Phone');
    
    // LinkedIn
    const li = document.querySelector('input[id*="linkedin" i]');
    if (li && pi.linkedin) await fillInput(li, pi.linkedin) && results.filled.push('LinkedIn');
    
    // Preferred name
    for (const label of document.querySelectorAll('label')) {
      if (/prefer.*name/i.test(label.textContent)) {
        const forId = label.getAttribute('for');
        if (forId) {
          const inp = document.getElementById(forId);
          if (inp?.tagName === 'INPUT' && !inp.value) {
            await fillInput(inp, profile.firstName);
            results.filled.push('Preferred Name');
          }
        }
      }
    }
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
      const inp = document.querySelector('#resume');
      if (inp) {
        try {
          const f = b64ToFile(resume.file_data, resume.filename, resume.mime_type);
          const dt = new DataTransfer();
          dt.items.add(f);
          inp.files = dt.files;
          inp.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Resume');
        } catch(e) {}
      }
    }
    const cover = data.documents?.cover_letter;
    if (cover?.file_data) {
      const inp = document.querySelector('#cover_letter');
      if (inp) {
        try {
          const f = b64ToFile(cover.file_data, cover.filename, cover.mime_type);
          const dt = new DataTransfer();
          dt.items.add(f);
          inp.files = dt.files;
          inp.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push('Cover Letter');
        } catch(e) {}
      }
    }
  }

  function b64ToFile(b64, name, type) {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    return new File([arr], name || 'file.pdf', { type: type || 'application/pdf' });
  }

  log('Content script v4 loaded!');
})();
