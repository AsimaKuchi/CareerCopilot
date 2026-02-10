// JobMatch AI - Content Script
// Robust dropdown auto-fill for Greenhouse/Lever/Ashby ATS forms

(function() {
  'use strict';

  // ============================
  // DEBUG FLAG
  // ============================
  const DEBUG_DROPDOWNS = true;

  function log(...args) {
    if (DEBUG_DROPDOWNS) console.log('[JobMatch AI]', ...args);
  }

  function logDebug(...args) {
    if (DEBUG_DROPDOWNS) console.log('[JobMatch AI DEBUG]', ...args);
  }

  let apiUrl = null;

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'AUTOFILL') {
      handleAutoFill(message.data).then(sendResponse);
      return true; // Keep channel open for async response
    }
    if (message.action === 'SET_API_URL') {
      apiUrl = message.url;
      sendResponse({ success: true });
      return true;
    }
  });

  // ============================
  // NORMALIZATION UTILITIES
  // ============================

  function normalize(str) {
    if (!str) return '';
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s]/g, ' ')  // Replace punctuation with spaces
      .replace(/\s+/g, ' ')      // Collapse multiple spaces
      .trim();
  }

  // Synonym mappings for common answer variations
  const SYNONYMS = {
    // Yes/No variations
    'yes': ['yes', 'true', 'y', 'i do', 'i am', 'i have', 'i will', 'affirmative', 'correct'],
    'no': ['no', 'false', 'n', 'i do not', 'i dont', 'i am not', 'i have not', 'i will not', 'negative', 'none'],
    
    // Country variations
    'canada': ['canada', 'ca', 'canadian', 'cdn'],
    'united states': ['united states', 'us', 'usa', 'u.s.', 'u.s.a', 'america', 'american'],
    
    // Work arrangement
    'remote': ['remote', 'work from home', 'wfh', 'fully remote', '100% remote', 'distributed'],
    'hybrid': ['hybrid', 'flexible', 'partially remote', 'mixed', 'part remote'],
    'onsite': ['onsite', 'on-site', 'on site', 'in office', 'in-office', 'office'],
    
    // Relocation
    'willing to relocate': ['yes', 'willing', 'open to relocate', 'yes - willing'],
    'not willing to relocate': ['no', 'not willing', 'no - not willing'],
    'open to discussion': ['open to discussion', 'maybe', 'depends', 'possibly', 'open'],
    
    // Notice period
    'immediately': ['immediately', 'immediate', 'now', 'asap', 'right away', 'available now', 'immediately available'],
    '2 weeks': ['2 weeks', 'two weeks', '14 days', '2-week', 'two-week'],
    '1 month': ['1 month', 'one month', '30 days', '4 weeks', 'four weeks'],
    '2 months': ['2 months', 'two months', '60 days', '8 weeks'],
    '3 months': ['3 months', 'three months', '90 days', '12 weeks'],
    '3+ months': ['3+ months', 'more than 3 months', 'over 3 months', '3 months or more'],
  };

  function expandSynonyms(answer) {
    const normalized = normalize(answer);
    const expanded = [answer, normalized];
    
    for (const [key, synonyms] of Object.entries(SYNONYMS)) {
      if (synonyms.some(s => normalize(s) === normalized || normalized.includes(normalize(s)))) {
        expanded.push(key, ...synonyms);
      }
    }
    
    return [...new Set(expanded)];
  }

  // ============================
  // DROPDOWN DETECTION
  // ============================

  function isDropdownElement(el) {
    if (!el) return false;
    
    const tag = el.tagName?.toLowerCase();
    const role = el.getAttribute('role');
    const ariaHasPopup = el.getAttribute('aria-haspopup');
    const ariaExpanded = el.getAttribute('aria-expanded');
    
    // Native select
    if (tag === 'select') return { type: 'native-select', el };
    
    // Combobox role
    if (role === 'combobox') return { type: 'combobox', el };
    
    // Listbox role on button/div
    if (role === 'listbox') return { type: 'listbox', el };
    
    // aria-haspopup="listbox" or "true"
    if (ariaHasPopup === 'listbox' || ariaHasPopup === 'true') return { type: 'aria-popup', el };
    
    // Has aria-expanded attribute (likely a dropdown trigger)
    if (ariaExpanded !== null) return { type: 'aria-expanded', el };
    
    // Check for common dropdown class patterns
    const classList = el.className || '';
    if (classList.includes('select') || classList.includes('dropdown') || classList.includes('combobox')) {
      return { type: 'class-pattern', el };
    }
    
    return false;
  }

  function findDropdownInContainer(container) {
    // First check if container itself is a dropdown
    const selfCheck = isDropdownElement(container);
    if (selfCheck) return selfCheck;
    
    // Look for common dropdown patterns within container
    const selectors = [
      'select',
      '[role="combobox"]',
      '[role="listbox"]',
      '[aria-haspopup="listbox"]',
      '[aria-haspopup="true"]',
      '[aria-expanded]',
      'button[class*="select"]',
      'div[class*="select"]',
      '[class*="Select"]',
      '[class*="dropdown"]',
      '[class*="Dropdown"]'
    ];
    
    for (const selector of selectors) {
      const el = container.querySelector(selector);
      if (el) {
        const check = isDropdownElement(el);
        if (check) return check;
        return { type: 'selector-match', el };
      }
    }
    
    return null;
  }

  // ============================
  // OPTION FINDING (CRITICAL)
  // ============================

  async function waitForOptions(maxWait = 2500) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWait) {
      const options = findVisibleOptions();
      if (options.length > 0) {
        return options;
      }
      await sleep(100);
    }
    
    return [];
  }

  function findVisibleOptions() {
    const options = [];
    const seen = new Set();
    
    // Priority 1: Standard listbox options
    const listboxOptions = document.querySelectorAll('[role="listbox"]:not([aria-hidden="true"]) [role="option"]');
    listboxOptions.forEach(opt => {
      if (isVisible(opt)) {
        const text = opt.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: opt, text, source: 'listbox-option' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 2: ul listbox li items
    const listItems = document.querySelectorAll('ul[role="listbox"] li');
    listItems.forEach(li => {
      if (isVisible(li)) {
        const text = li.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: li, text, source: 'ul-li' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 3: Radix UI popper content
    const radixOptions = document.querySelectorAll('[data-radix-popper-content-wrapper] [role="option"]');
    radixOptions.forEach(opt => {
      if (isVisible(opt)) {
        const text = opt.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: opt, text, source: 'radix-option' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 4: react-select menu options
    const reactSelectOptions = document.querySelectorAll('.select__menu [class*="option"], [class*="menu"] [class*="option"]');
    reactSelectOptions.forEach(opt => {
      if (isVisible(opt)) {
        const text = opt.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: opt, text, source: 'react-select' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 5: Generic visible menu items
    const menuItems = document.querySelectorAll('[role="menu"] [role="menuitem"], [role="menu"] li, .dropdown-menu li, .dropdown-menu a');
    menuItems.forEach(item => {
      if (isVisible(item)) {
        const text = item.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: item, text, source: 'menu-item' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 6: Greenhouse-specific custom select options
    const greenhouseOptions = document.querySelectorAll('[class*="custom-select"] [class*="option"], .select-dropdown li, [data-option]');
    greenhouseOptions.forEach(opt => {
      if (isVisible(opt)) {
        const text = opt.textContent?.trim();
        if (text && !seen.has(text)) {
          seen.add(text);
          options.push({ el: opt, text, source: 'greenhouse-custom' });
        }
      }
    });
    if (options.length > 0) return options;
    
    // Priority 7: Any visible divs that look like options in a newly opened popover
    const popovers = document.querySelectorAll('[role="dialog"], [data-state="open"], [class*="popover"], [class*="Popover"]');
    popovers.forEach(popover => {
      if (!isVisible(popover)) return;
      const children = popover.querySelectorAll('div, span, button');
      children.forEach(child => {
        if (isVisible(child) && child.textContent?.trim() && child.childElementCount === 0) {
          const text = child.textContent.trim();
          if (text.length < 100 && !seen.has(text)) {
            seen.add(text);
            options.push({ el: child, text, source: 'popover-child' });
          }
        }
      });
    });
    
    return options;
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      style.opacity !== '0' &&
      el.offsetParent !== null
    );
  }

  function filterPlaceholders(options) {
    const placeholders = ['select', 'choose', 'pick', 'loading', 'no options', 'no results', '--', '---'];
    return options.filter(opt => {
      const text = normalize(opt.text);
      if (!text || text.length < 1) return false;
      return !placeholders.some(p => text === p || text.startsWith(p + ' '));
    });
  }

  // ============================
  // ANSWER MATCHING
  // ============================

  function scoreMatch(optionText, answerVariants) {
    const optNorm = normalize(optionText);
    
    for (const variant of answerVariants) {
      const varNorm = normalize(variant);
      
      // Exact match (highest score)
      if (optNorm === varNorm) return { score: 100, type: 'exact' };
    }
    
    for (const variant of answerVariants) {
      const varNorm = normalize(variant);
      
      // Contains match
      if (optNorm.includes(varNorm) || varNorm.includes(optNorm)) {
        const lengthRatio = Math.min(optNorm.length, varNorm.length) / Math.max(optNorm.length, varNorm.length);
        return { score: 60 + (lengthRatio * 30), type: 'contains' };
      }
    }
    
    // Word overlap match
    for (const variant of answerVariants) {
      const varWords = normalize(variant).split(' ').filter(w => w.length > 2);
      const optWords = optNorm.split(' ').filter(w => w.length > 2);
      
      const overlap = varWords.filter(w => optWords.includes(w)).length;
      if (overlap > 0 && varWords.length > 0) {
        const overlapScore = (overlap / varWords.length) * 50;
        if (overlapScore > 20) return { score: overlapScore, type: 'word-overlap' };
      }
    }
    
    return { score: 0, type: 'none' };
  }

  function findBestMatchingOption(options, answer) {
    if (!options || options.length === 0 || !answer) return null;
    
    const answerVariants = expandSynonyms(answer);
    let bestMatch = null;
    let bestScore = 0;
    
    logDebug('Finding best match for answer:', answer);
    logDebug('Answer variants:', answerVariants.slice(0, 5));
    logDebug('Available options:', options.slice(0, 15).map(o => o.text));
    
    for (const opt of options) {
      const result = scoreMatch(opt.text, answerVariants);
      if (result.score > bestScore) {
        bestScore = result.score;
        bestMatch = { ...opt, matchScore: result.score, matchType: result.type };
      }
    }
    
    if (bestMatch && bestScore >= 20) {
      logDebug(`Best match: "${bestMatch.text}" (score: ${bestScore}, type: ${bestMatch.matchType})`);
      return bestMatch;
    }
    
    logDebug('No suitable match found');
    return null;
  }

  // Numeric bucket matching for years of experience questions
  function matchNumericBucket(options, yearsValue) {
    if (yearsValue === null || yearsValue === undefined) return null;
    
    const years = parseFloat(yearsValue);
    if (isNaN(years)) return null;
    
    logDebug(`Matching numeric bucket for ${years} years`);
    
    for (const opt of options) {
      const text = opt.text.toLowerCase();
      
      // Extract numbers from option text
      const numbers = text.match(/\d+/g);
      if (!numbers) continue;
      
      // Check for range patterns like "3-5", "3 to 5", "3–5"
      const rangeMatch = text.match(/(\d+)\s*[-–to]+\s*(\d+)/i);
      if (rangeMatch) {
        const min = parseInt(rangeMatch[1]);
        const max = parseInt(rangeMatch[2]);
        if (years >= min && years <= max) {
          logDebug(`Matched range ${min}-${max} for ${years} years`);
          return opt;
        }
      }
      
      // Check for "X+ years" pattern
      const plusMatch = text.match(/(\d+)\s*\+/);
      if (plusMatch) {
        const threshold = parseInt(plusMatch[1]);
        if (years >= threshold) {
          logDebug(`Matched ${threshold}+ for ${years} years`);
          return opt;
        }
      }
      
      // Check for single number match
      if (numbers.length === 1) {
        const num = parseInt(numbers[0]);
        if (num === Math.floor(years) || num === Math.ceil(years)) {
          return opt;
        }
      }
    }
    
    return null;
  }

  // ============================
  // DROPDOWN INTERACTION
  // ============================

  async function openDropdown(dropdownInfo) {
    const { type, el } = dropdownInfo;
    log(`Opening dropdown (type: ${type})`);
    
    // For native select, we don't need to "open" it
    if (type === 'native-select') {
      return true;
    }
    
    // Click to open
    try {
      el.scrollIntoView({ behavior: 'instant', block: 'center' });
      await sleep(50);
      
      // Try mousedown + click sequence (works better for some React components)
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
      await sleep(10);
      el.click();
      await sleep(100);
      
      // Check if aria-expanded changed
      const expanded = el.getAttribute('aria-expanded');
      if (expanded === 'true') {
        log('Dropdown opened (aria-expanded=true)');
        return true;
      }
      
      // Try focus + space key (for some accessibility-compliant dropdowns)
      el.focus();
      el.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
      await sleep(100);
      
      return true;
    } catch (e) {
      log('Error opening dropdown:', e);
      return false;
    }
  }

  async function selectDropdownValue(fieldEl, answer, questionLabel = '') {
    log('\n========== DROPDOWN FILL ==========');
    log('Question:', questionLabel);
    log('Answer to fill:', answer);
    
    // Find dropdown element
    const dropdownInfo = findDropdownInContainer(fieldEl) || isDropdownElement(fieldEl);
    
    if (!dropdownInfo) {
      log('No dropdown detected in container');
      return { success: false, reason: 'no_dropdown_found' };
    }
    
    log('Dropdown detected:', dropdownInfo.type);
    
    // Handle native select directly
    if (dropdownInfo.type === 'native-select') {
      return await handleNativeSelect(dropdownInfo.el, answer);
    }
    
    // Open the dropdown
    const opened = await openDropdown(dropdownInfo);
    if (!opened) {
      log('Failed to open dropdown');
      return { success: false, reason: 'failed_to_open' };
    }
    
    // Wait for options to appear
    await sleep(200);
    let options = await waitForOptions(2500);
    options = filterPlaceholders(options);
    
    log('Options found:', options.length);
    if (options.length > 0) {
      log('Option texts (first 15):', options.slice(0, 15).map(o => o.text));
    }
    
    if (options.length === 0) {
      log('No options found after opening dropdown');
      // Try to close the dropdown
      document.body.click();
      return { success: false, reason: 'no_options_found' };
    }
    
    // Find best matching option
    let bestMatch = findBestMatchingOption(options, answer);
    
    // If no match and answer looks numeric, try bucket matching
    if (!bestMatch && /^\d+(\.\d+)?$/.test(String(answer))) {
      bestMatch = matchNumericBucket(options, answer);
    }
    
    if (!bestMatch) {
      log('No matching option found');
      // Close dropdown
      document.body.click();
      await sleep(100);
      return { success: false, reason: 'no_match', availableOptions: options.slice(0, 10).map(o => o.text) };
    }
    
    // Click the option
    log(`Selecting option: "${bestMatch.text}"`);
    try {
      bestMatch.el.scrollIntoView({ behavior: 'instant', block: 'center' });
      await sleep(50);
      
      // Try multiple click methods
      bestMatch.el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      await sleep(10);
      bestMatch.el.click();
      await sleep(100);
      
      // Verify selection
      const verified = await verifySelection(dropdownInfo.el, bestMatch.text, answer);
      
      if (!verified) {
        log('Selection not verified, retrying...');
        // Retry once
        await openDropdown(dropdownInfo);
        await sleep(200);
        const retryOptions = await waitForOptions(1500);
        const retryMatch = retryOptions.find(o => o.text === bestMatch.text);
        if (retryMatch) {
          retryMatch.el.click();
          await sleep(100);
        }
      }
      
      log('Selection complete');
      log('=====================================\n');
      return { success: true, selected: bestMatch.text, matchType: bestMatch.matchType };
      
    } catch (e) {
      log('Error clicking option:', e);
      return { success: false, reason: 'click_error', error: e.message };
    }
  }

  async function handleNativeSelect(selectEl, answer) {
    log('Handling native <select> element');
    
    const options = Array.from(selectEl.options).map(opt => ({
      el: opt,
      text: opt.text?.trim() || opt.value,
      value: opt.value
    }));
    
    const filteredOptions = filterPlaceholders(options);
    log('Select options:', filteredOptions.map(o => o.text));
    
    const bestMatch = findBestMatchingOption(filteredOptions, answer);
    
    if (!bestMatch) {
      return { success: false, reason: 'no_match', availableOptions: filteredOptions.map(o => o.text) };
    }
    
    // Set value on native select
    selectEl.value = bestMatch.el.value;
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    selectEl.dispatchEvent(new Event('input', { bubbles: true }));
    
    log(`Selected: "${bestMatch.text}"`);
    return { success: true, selected: bestMatch.text };
  }

  async function verifySelection(dropdownEl, selectedText, originalAnswer) {
    await sleep(100);
    
    // Check if dropdown text changed
    const currentText = dropdownEl.textContent?.trim() || '';
    if (currentText.includes(selectedText)) {
      return true;
    }
    
    // Check aria-selected on options
    const selectedOption = document.querySelector('[role="option"][aria-selected="true"]');
    if (selectedOption && selectedOption.textContent?.includes(selectedText)) {
      return true;
    }
    
    // Check if aria-expanded is now false (dropdown closed after selection)
    if (dropdownEl.getAttribute('aria-expanded') === 'false') {
      return true;
    }
    
    // Check for hidden input value change
    const container = dropdownEl.closest('div, fieldset, section');
    if (container) {
      const hiddenInput = container.querySelector('input[type="hidden"]');
      if (hiddenInput && hiddenInput.value) {
        return true;
      }
    }
    
    return false;
  }

  // ============================
  // QUESTION DETECTION & SKIPPING
  // ============================

  const SKIP_PATTERNS = [
    // EEO / Demographics
    /gender/i, /race/i, /ethnicity/i, /veteran/i, /disability/i, /sex\b/i,
    /equal\s*opportunity/i, /eeo/i, /demographic/i, /diversity/i,
    /sexual\s*orientation/i, /pronouns/i,
    
    // Legal agreements (unless we have explicit answers)
    /terms\s*(and|&)\s*conditions/i, /privacy\s*policy/i, /acknowledge/i,
    /consent\s*to/i, /agree\s*to/i,
    
    // Accommodation requests
    /accommodation/i, /special\s*needs/i,
  ];

  function shouldSkipQuestion(questionText) {
    const normalized = normalize(questionText);
    return SKIP_PATTERNS.some(pattern => pattern.test(questionText) || pattern.test(normalized));
  }

  // ============================
  // FIELD FINDING
  // ============================

  function findAllFormFields() {
    const fields = [];
    const seen = new Set();
    
    // Method 1: Find labels and their associated inputs
    document.querySelectorAll('label').forEach(label => {
      const labelText = label.textContent?.trim() || '';
      if (labelText.length < 3 || seen.has(labelText)) return;
      
      // Find associated input
      let input = null;
      const forId = label.getAttribute('for');
      
      if (forId) {
        input = document.getElementById(forId);
      }
      
      if (!input) {
        input = label.querySelector('input, select, textarea');
      }
      
      if (!input) {
        const parent = label.closest('div, fieldset, section');
        if (parent) {
          input = parent.querySelector('input, select, textarea, [role="combobox"], [aria-haspopup]');
        }
      }
      
      if (input) {
        seen.add(labelText);
        fields.push({
          label: labelText,
          labelLower: labelText.toLowerCase(),
          element: input,
          container: label.closest('div, fieldset, section'),
          type: getFieldType(input),
          hasDropdown: !!findDropdownInContainer(input.closest('div, fieldset, section') || input)
        });
      }
    });
    
    // Method 2: Find aria-labeled elements
    document.querySelectorAll('[aria-label]').forEach(el => {
      const labelText = el.getAttribute('aria-label') || '';
      if (labelText.length < 3 || seen.has(labelText)) return;
      
      seen.add(labelText);
      fields.push({
        label: labelText,
        labelLower: labelText.toLowerCase(),
        element: el,
        container: el.closest('div, fieldset, section'),
        type: getFieldType(el),
        hasDropdown: !!findDropdownInContainer(el.closest('div, fieldset, section') || el)
      });
    });
    
    // Method 3: Find fieldsets with legends
    document.querySelectorAll('fieldset').forEach(fieldset => {
      const legend = fieldset.querySelector('legend');
      if (!legend) return;
      
      const labelText = legend.textContent?.trim() || '';
      if (labelText.length < 3 || seen.has(labelText)) return;
      
      const input = fieldset.querySelector('input, select, [role="combobox"]');
      if (input) {
        seen.add(labelText);
        fields.push({
          label: labelText,
          labelLower: labelText.toLowerCase(),
          element: input,
          container: fieldset,
          type: getFieldType(input),
          hasDropdown: !!findDropdownInContainer(fieldset)
        });
      }
    });
    
    return fields;
  }

  function getFieldType(el) {
    if (!el) return 'unknown';
    const tag = el.tagName?.toLowerCase();
    const type = el.type?.toLowerCase();
    const role = el.getAttribute('role');
    
    if (tag === 'select') return 'select';
    if (role === 'combobox' || el.getAttribute('aria-haspopup')) return 'dropdown';
    if (tag === 'textarea') return 'textarea';
    if (tag === 'input') {
      if (type === 'radio') return 'radio';
      if (type === 'checkbox') return 'checkbox';
      if (type === 'file') return 'file';
      return 'text';
    }
    return 'unknown';
  }

  // ============================
  // PROFILE ANSWER MAPPING
  // ============================

  function getAnswerFromProfile(field, profile) {
    const q = field.labelLower;
    
    // Skip sensitive/EEO questions
    if (shouldSkipQuestion(q)) {
      log(`Skipping question (sensitive/EEO): ${field.label.substring(0, 50)}`);
      return null;
    }
    
    // ===== WORK AUTHORIZATION =====
    if (q.includes('authorized to work') || q.includes('legally authorized') || q.includes('eligible to work') || q.includes('work authorization')) {
      const isAuthorized = profile.workAuthorizationStatus && 
        !['require_sponsorship', 'not_authorized', 'unknown'].includes(profile.workAuthorizationStatus);
      return isAuthorized ? 'Yes' : 'No';
    }
    
    // ===== SPONSORSHIP =====
    if (q.includes('sponsorship') || q.includes('visa support') || q.includes('require visa') || q.includes('immigration')) {
      const needsSponsorship = profile.requiresSponsorship === true;
      return needsSponsorship ? 'Yes' : 'No';
    }
    
    // ===== LOCATION QUESTIONS =====
    if (q.includes('country of residence') || q.includes('current country') || q.includes('what country')) {
      return profile.countryFull || profile.country || 'Canada';
    }
    
    if (q.includes('located in') || q.includes('based in') || q.includes('reside in')) {
      const locationStr = `${profile.city} ${profile.state} ${profile.country}`.toLowerCase();
      
      if (q.includes('us or canada') || q.includes('united states or canada') || q.includes('north america')) {
        const isUSCanada = locationStr.includes('canada') || locationStr.includes('us') || 
                          profile.country?.toUpperCase() === 'CA' || profile.country?.toUpperCase() === 'US';
        return isUSCanada ? 'Yes' : 'No';
      }
      if (q.includes('canada')) {
        return locationStr.includes('canada') || profile.country?.toUpperCase() === 'CA' ? 'Yes' : 'No';
      }
      if (q.includes('united states') || q.match(/\bus\b/)) {
        return locationStr.includes('united states') || profile.country?.toUpperCase() === 'US' ? 'Yes' : 'No';
      }
    }
    
    // ===== RELOCATION =====
    if (q.includes('relocat')) {
      const willing = profile.willingToRelocate;
      log('Relocation question, profile value:', willing);
      
      // Map normalized values to user-friendly dropdown options
      const relocateMap = {
        'yes': 'Yes - willing to relocate',
        'no': 'No - not willing to relocate',
        'open_to_discussion': 'Open to discussion'
      };
      
      return relocateMap[willing] || willing || null;
    }
    
    // ===== NOTICE PERIOD =====
    if (q.includes('notice period') || q.includes('how soon') || q.includes('when can you start') || q.includes('availability')) {
      const notice = profile.noticePeriod;
      log('Notice period question, profile value:', notice);
      
      // Map normalized values to user-friendly dropdown options
      const noticeMap = {
        'immediately': 'Immediately available',
        'one_week': '1 week',
        'two_weeks': '2 weeks',
        'three_weeks': '3 weeks', 
        'one_month': '1 month',
        'six_weeks': '6 weeks',
        'two_months': '2 months',
        'three_months': '3 months',
        'three_months_plus': '3+ months'
      };
      
      return noticeMap[notice] || notice || null;
    }
    
    // ===== WORK ARRANGEMENT =====
    if (q.includes('work arrangement') || q.includes('work preference') || q.includes('remote') && q.includes('hybrid') || q.includes('onsite')) {
      const arrangement = profile.workArrangement;
      log('Work arrangement question, profile value:', arrangement);
      
      const arrangementMap = {
        'remote': 'Remote',
        'hybrid': 'Hybrid',
        'onsite': 'On-site',
        'flexible': 'Flexible'
      };
      
      return arrangementMap[arrangement] || arrangement || null;
    }
    
    // "comfortable working remotely" / "open to remote work" (Yes/No)
    if (q.includes('remote') && (q.includes('comfortable') || q.includes('willing') || q.includes('open to'))) {
      const arrangement = profile.workArrangement;
      return arrangement === 'remote' || arrangement === 'hybrid' || arrangement === 'flexible' ? 'Yes' : 'No';
    }
    
    // ===== YEARS OF EXPERIENCE =====
    if (q.includes('years of experience') || q.includes('years experience')) {
      const years = profile.experienceYears;
      if (years !== null && years !== undefined) {
        return String(years);
      }
    }
    
    // Do you have X years of experience with Y?
    if ((q.includes('do you have') && q.includes('experience')) || q.includes('years') && q.includes('experience')) {
      // Extract skill/technology from question
      const skillMatch = q.match(/experience\s+(?:with|in|using)\s+([a-zA-Z0-9\s\+\#\.]+?)(?:\?|$|\s+years)/i);
      if (skillMatch && profile.skillsWithYears) {
        const targetSkill = normalize(skillMatch[1]);
        const matchingSkill = profile.skillsWithYears.find(s => 
          normalize(s.name).includes(targetSkill) || targetSkill.includes(normalize(s.name))
        );
        if (matchingSkill && matchingSkill.years) {
          return 'Yes';
        }
      }
      
      // Check resume for skill mention
      const resumeText = profile.resumeText?.toLowerCase() || '';
      if (skillMatch && resumeText.includes(normalize(skillMatch[1]))) {
        return 'Yes';
      }
    }
    
    // ===== EDUCATION =====
    if (q.includes('education') || q.includes('degree') || q.includes('highest level')) {
      const edu = profile.education;
      log('Education question, profile value:', edu);
      
      const eduMap = {
        'high_school': 'High School',
        'some_college': 'Some College',
        'associate': "Associate's Degree",
        'bachelor': "Bachelor's Degree",
        'master': "Master's Degree",
        'doctorate': 'Doctorate',
        'professional': 'Professional Degree',
        'bootcamp': 'Bootcamp',
        'certification': 'Certification'
      };
      
      return eduMap[edu] || edu || null;
    }
    
    // ===== COMMON YES/NO QUESTIONS =====
    if (q.includes('employment agreement') || q.includes('non-compete') || q.includes('employment restriction')) {
      return 'No';
    }
    
    if (q.includes('previously worked') || q.includes('worked at') || q.includes('employed by') || q.includes('consulted for')) {
      // Check resume for company mention
      const companyMatch = q.match(/(?:worked|employed|consulted)\s+(?:at|by|for)\s+([a-zA-Z0-9\s]+?)(?:\?|$|before)/i);
      if (companyMatch && profile.resumeText) {
        const company = normalize(companyMatch[1]);
        if (profile.resumeText.toLowerCase().includes(company)) {
          return 'Yes';
        }
      }
      return 'No';
    }
    
    if (q.includes('18 years') || q.includes('legal age') || q.includes('at least 18')) {
      return 'Yes';
    }
    
    if (q.includes('background check')) {
      return 'Yes';
    }
    
    // ===== HOW DID YOU HEAR =====
    if (q.includes('how did you hear') || q.includes('how did you find') || q.includes('referred by') || q.includes('source')) {
      return profile.referralSource || 'LinkedIn';
    }
    
    // ===== CONTACT INFO =====
    if (q.includes('linkedin') && !q.includes('url')) {
      return profile.linkedinUrl || null;
    }
    
    if (q.includes('github')) {
      return profile.githubUrl || null;
    }
    
    if (q.includes('portfolio') || q.includes('website') || q.includes('personal url')) {
      return profile.portfolioUrl || profile.websiteUrl || null;
    }
    
    if (q.includes('preferred name') || q.includes('name you') || q.includes('call you')) {
      return profile.firstName || null;
    }
    
    // ===== SALARY =====
    if (q.includes('salary') && (q.includes('expectation') || q.includes('requirement') || q.includes('desired'))) {
      if (profile.salaryMin && profile.salaryMax) {
        return `$${profile.salaryMin.toLocaleString()} - $${profile.salaryMax.toLocaleString()}`;
      } else if (profile.salaryMin) {
        return `$${profile.salaryMin.toLocaleString()}`;
      }
    }
    
    return null;
  }

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
      const url = window.location.href;
      const atsType = detectATSType(url);
      
      log('=== AUTO-FILL STARTED ===');
      log('ATS Type:', atsType);
      log('URL:', url);

      // Build comprehensive profile from data
      const profile = {
        firstName: data.personal_info?.first_name || '',
        lastName: data.personal_info?.last_name || '',
        fullName: data.personal_info?.full_name || '',
        email: data.personal_info?.email || '',
        phone: data.personal_info?.phone || '',
        linkedinUrl: data.personal_info?.linkedin || '',
        githubUrl: data.personal_info?.github || '',
        portfolioUrl: data.personal_info?.portfolio || '',
        websiteUrl: data.personal_info?.website || '',
        city: data.personal_info?.location?.city || '',
        state: data.personal_info?.location?.state || '',
        country: data.personal_info?.location?.country || '',
        countryFull: data.profile_context?.country || data.personal_info?.location?.country || '',
        
        // Work authorization
        workAuthorizationStatus: data.profile_context?.work_authorization || '',
        requiresSponsorship: data.profile_context?.requires_sponsorship,
        
        // Professional
        skills: data.profile_context?.skills || [],
        skillsWithYears: data.profile_context?.skills_with_years || [],
        experienceYears: data.profile_context?.experience_years,
        resumeText: data.profile_context?.resume_text || '',
        education: data.profile_context?.education || '',
        
        // Preferences
        willingToRelocate: data.profile_context?.willing_to_relocate || '',
        noticePeriod: data.profile_context?.notice_period || '',
        workArrangement: data.profile_context?.work_arrangement || '',
        referralSource: data.profile_context?.referral_source || 'LinkedIn',
        
        // Compensation
        salaryMin: data.profile_context?.salary_min,
        salaryMax: data.profile_context?.salary_max,
      };
      
      log('Profile loaded:', {
        name: profile.fullName,
        location: `${profile.city}, ${profile.state}, ${profile.country}`,
        workAuth: profile.workAuthorizationStatus,
        requiresSponsorship: profile.requiresSponsorship,
        willingToRelocate: profile.willingToRelocate,
        noticePeriod: profile.noticePeriod,
        education: profile.education,
        workArrangement: profile.workArrangement
      });

      // Fill standard personal info fields first
      await fillPersonalInfo(data, results);
      await fillContactInfo(data, results);
      await fillLinks(data, results);
      await fillLocation(data, results);
      
      // Handle resume upload
      await handleResumeUpload(data, results);
      
      // Handle cover letter
      await fillCoverLetter(data, results);
      
      // Fill screening questions / dropdowns
      log('\n=== PROCESSING SCREENING QUESTIONS ===');
      const allFields = findAllFormFields();
      log(`Found ${allFields.length} form fields`);
      
      for (const field of allFields) {
        // Skip if already filled
        if (field.type === 'text' && field.element.value) continue;
        
        const answer = getAnswerFromProfile(field, profile);
        
        if (answer) {
          log(`\nProcessing: "${field.label.substring(0, 50)}"`);
          log(`Answer: ${answer}`);
          log(`Field type: ${field.type}, Has dropdown: ${field.hasDropdown}`);
          
          if (field.type === 'select' || field.type === 'dropdown' || field.hasDropdown) {
            // Use robust dropdown selection
            const result = await selectDropdownValue(
              field.container || field.element,
              answer,
              field.label
            );
            
            if (result.success) {
              results.filled.push(`${field.label.substring(0, 40)} → ${result.selected}`);
            } else {
              results.failed.push(`${field.label.substring(0, 40)} (${result.reason})`);
            }
          } else {
            // Text/textarea field
            const filled = await setTextFieldValue(field.element, answer);
            if (filled) {
              results.filled.push(field.label.substring(0, 40));
            }
          }
        }
        
        // Small delay between fields
        await sleep(50);
      }

      results.success = results.filled.length > 0;
      results.filledCount = results.filled.length;
      
      log('\n=== AUTO-FILL COMPLETE ===');
      log('Filled:', results.filled.length);
      log('Failed:', results.failed.length);
      log('Skipped:', results.skipped.length);
      
    } catch (error) {
      log('Auto-fill error:', error);
      results.failed.push(`Error: ${error.message}`);
    }

    return results;
  }

  function detectATSType(url) {
    if (/greenhouse/i.test(url)) return 'greenhouse';
    if (/lever/i.test(url)) return 'lever';
    if (/ashby/i.test(url)) return 'ashby';
    if (/workable/i.test(url)) return 'workable';
    if (/smartrecruiters/i.test(url)) return 'smartrecruiters';
    return 'unknown';
  }

  // ============================
  // TEXT FIELD FILLING
  // ============================

  async function setTextFieldValue(element, value) {
    if (!element || !value) return false;
    
    try {
      // Check visibility
      const style = window.getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden' || element.disabled) {
        return false;
      }
      
      const tag = element.tagName?.toLowerCase();
      
      // Skip file inputs
      if (tag === 'input' && element.type === 'file') return false;
      
      // Handle contenteditable
      if (element.isContentEditable) {
        element.innerHTML = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        return true;
      }
      
      // Standard input/textarea
      element.focus();
      
      // Use native setter for React compatibility
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set;
      const nativeTextareaValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;
      
      if (tag === 'input' && nativeInputValueSetter) {
        nativeInputValueSetter.call(element, value);
      } else if (tag === 'textarea' && nativeTextareaValueSetter) {
        nativeTextareaValueSetter.call(element, value);
      } else {
        element.value = value;
      }
      
      // Dispatch events
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
      element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
      
      element.blur();
      
      return true;
      
    } catch (e) {
      log('Error setting text value:', e);
      return false;
    }
  }

  // ============================
  // PERSONAL INFO FILLING
  // ============================

  async function fillPersonalInfo(data, results) {
    const personalInfo = data.personal_info || {};
    
    // First Name
    if (personalInfo.first_name) {
      const selectors = [
        'input[name*="first_name" i]', 'input[name*="firstname" i]',
        'input[id*="first_name" i]', 'input[id*="firstname" i]',
        'input[autocomplete="given-name"]', 'input[placeholder*="first name" i]'
      ];
      if (await fillField(selectors, personalInfo.first_name)) {
        results.filled.push('First Name');
      }
    }

    // Last Name
    if (personalInfo.last_name) {
      const selectors = [
        'input[name*="last_name" i]', 'input[name*="lastname" i]',
        'input[id*="last_name" i]', 'input[id*="lastname" i]',
        'input[autocomplete="family-name"]', 'input[placeholder*="last name" i]'
      ];
      if (await fillField(selectors, personalInfo.last_name)) {
        results.filled.push('Last Name');
      }
    }

    // Full Name
    if (personalInfo.full_name) {
      const selectors = [
        'input[name*="full_name" i]', 'input[name*="fullname" i]',
        'input[autocomplete="name"]', 'input[placeholder*="full name" i]'
      ];
      if (await fillField(selectors, personalInfo.full_name)) {
        results.filled.push('Full Name');
      }
    }
  }

  async function fillContactInfo(data, results) {
    const personalInfo = data.personal_info || {};
    
    // Email
    if (personalInfo.email) {
      const selectors = [
        'input[type="email"]', 'input[name*="email" i]',
        'input[id*="email" i]', 'input[autocomplete="email"]'
      ];
      if (await fillField(selectors, personalInfo.email)) {
        results.filled.push('Email');
      }
    }

    // Phone
    if (personalInfo.phone) {
      const selectors = [
        'input[type="tel"]', 'input[name*="phone" i]',
        'input[id*="phone" i]', 'input[autocomplete="tel"]'
      ];
      if (await fillField(selectors, personalInfo.phone)) {
        results.filled.push('Phone');
      }
    }
  }

  async function fillLinks(data, results) {
    const personalInfo = data.personal_info || {};
    
    // LinkedIn
    if (personalInfo.linkedin) {
      const selectors = [
        'input[name*="linkedin" i]', 'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]'
      ];
      if (await fillField(selectors, personalInfo.linkedin)) {
        results.filled.push('LinkedIn');
      }
    }

    // GitHub
    if (personalInfo.github) {
      const selectors = [
        'input[name*="github" i]', 'input[id*="github" i]',
        'input[placeholder*="github" i]'
      ];
      if (await fillField(selectors, personalInfo.github)) {
        results.filled.push('GitHub');
      }
    }

    // Portfolio
    if (personalInfo.portfolio) {
      const selectors = [
        'input[name*="portfolio" i]', 'input[name*="website" i]',
        'input[type="url"]', 'input[placeholder*="portfolio" i]'
      ];
      if (await fillField(selectors, personalInfo.portfolio)) {
        results.filled.push('Portfolio');
      }
    }
  }

  async function fillLocation(data, results) {
    const location = data.personal_info?.location || {};
    
    // City
    if (location.city) {
      const selectors = [
        'input[name*="city" i]', 'input[id*="city" i]',
        'input[autocomplete="address-level2"]'
      ];
      if (await fillField(selectors, location.city)) {
        results.filled.push('City');
      }
    }

    // State/Province
    if (location.state) {
      const selectors = [
        'input[name*="state" i]', 'input[name*="province" i]',
        'input[autocomplete="address-level1"]',
        'select[name*="state" i]', 'select[id*="state" i]'
      ];
      if (await fillField(selectors, location.state)) {
        results.filled.push('State/Province');
      }
    }

    // Country
    if (location.country) {
      const selectors = [
        'select[name*="country" i]', 'select[id*="country" i]',
        'input[name*="country" i]', 'input[autocomplete="country"]'
      ];
      if (await fillField(selectors, location.country)) {
        results.filled.push('Country');
      }
    }
  }

  async function handleResumeUpload(data, results) {
    const resume = data.documents?.resume;
    if (!resume?.file_data) {
      results.skipped.push('Resume (no file data)');
      return;
    }

    const fileInputSelectors = [
      'input[type="file"][name*="resume" i]',
      'input[type="file"][id*="resume" i]',
      'input[type="file"][accept*="pdf"]',
      'input[type="file"]'
    ];

    for (const selector of fileInputSelectors) {
      const fileInput = document.querySelector(selector);
      if (fileInput) {
        try {
          const byteCharacters = atob(resume.file_data);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: resume.mime_type || 'application/pdf' });
          const file = new File([blob], resume.filename || 'resume.pdf', { 
            type: resume.mime_type || 'application/pdf' 
          });
          
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
          
          results.filled.push('Resume');
          log('Resume uploaded successfully');
          return;
        } catch (e) {
          log('Resume upload error:', e);
        }
      }
    }
    
    results.failed.push('Resume (file input not found)');
  }

  async function fillCoverLetter(data, results) {
    const coverLetter = data.documents?.cover_letter?.text;
    if (!coverLetter) {
      results.skipped.push('Cover Letter (not provided)');
      return;
    }

    const selectors = [
      'textarea[name*="cover" i]', 'textarea[id*="cover" i]',
      'textarea[placeholder*="cover letter" i]'
    ];

    if (await fillField(selectors, coverLetter)) {
      results.filled.push('Cover Letter');
    } else {
      results.skipped.push('Cover Letter (field not found)');
    }
  }

  // ============================
  // UTILITY FUNCTIONS
  // ============================

  async function fillField(selectors, value) {
    if (!value) return false;
    
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        if (await setTextFieldValue(element, value)) {
          return true;
        }
      }
    }
    return false;
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  log('Content script loaded - DEBUG_DROPDOWNS:', DEBUG_DROPDOWNS);
})();
