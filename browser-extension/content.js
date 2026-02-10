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
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  // Synonym mappings for common answer variations
  const SYNONYMS = {
    'yes': ['yes', 'true', 'y', 'i do', 'i am', 'i have', 'i will', 'affirmative', 'correct'],
    'no': ['no', 'false', 'n', 'i do not', 'i dont', 'i am not', 'i have not', 'i will not', 'negative', 'none'],
    'canada': ['canada', 'ca', 'canadian', 'cdn'],
    'united states': ['united states', 'us', 'usa', 'u.s.', 'u.s.a', 'america', 'american'],
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
      log('=== AUTO-FILL STARTED ===');
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
      
      log('Profile loaded:', {
        name: profile.fullName,
        location: `${profile.city}, ${profile.state}, ${profile.country}`,
        workAuth: profile.workAuthorizationStatus,
        requiresSponsorship: profile.requiresSponsorship,
        willingToRelocate: profile.willingToRelocate,
        noticePeriod: profile.noticePeriod,
        education: profile.education,
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
      
      // =====================================================
      // SCREENING QUESTIONS - Find and fill ALL select dropdowns
      // =====================================================
      log('\n=== PROCESSING SCREENING QUESTIONS (DROPDOWNS) ===');
      
      // Find all select elements on the page
      const allSelects = document.querySelectorAll('select');
      log(`Found ${allSelects.length} <select> elements on page`);
      
      for (const selectEl of allSelects) {
        await processSelectDropdown(selectEl, profile, results);
      }
      
      // Also find custom dropdowns (div-based with role="listbox" or similar)
      const customDropdowns = document.querySelectorAll('[role="combobox"], [role="listbox"], [aria-haspopup="listbox"]');
      log(`Found ${customDropdowns.length} custom dropdown elements`);
      
      for (const dropdown of customDropdowns) {
        await processCustomDropdown(dropdown, profile, results);
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

  // ============================
  // PROCESS NATIVE <SELECT> DROPDOWN
  // ============================

  async function processSelectDropdown(selectEl, profile, results) {
    // Skip if already filled or hidden
    if (selectEl.value && selectEl.value !== '' && !selectEl.value.toLowerCase().includes('select')) {
      return;
    }
    
    const style = window.getComputedStyle(selectEl);
    if (style.display === 'none' || style.visibility === 'hidden') {
      return;
    }

    // Get the question label
    const label = findLabelForElement(selectEl);
    if (!label) {
      logDebug('Skipping select without label');
      return;
    }
    
    const questionText = label.toLowerCase();
    log(`\n--- Processing Select: "${label.substring(0, 50)}..." ---`);
    
    // Get all options
    const options = Array.from(selectEl.options)
      .map(opt => ({ value: opt.value, text: opt.text?.trim() || opt.value }))
      .filter(opt => opt.value && opt.text && !opt.text.toLowerCase().includes('select'));
    
    log('Available options:', options.map(o => o.text));
    
    if (options.length === 0) {
      log('No valid options found');
      results.failed.push(`${label.substring(0, 40)} (no options)`);
      return;
    }
    
    // Determine the answer based on the question
    const answer = getAnswerForQuestion(questionText, profile, options);
    
    if (!answer) {
      log('No answer determined for this question');
      results.skipped.push(`${label.substring(0, 40)} (no profile match)`);
      return;
    }
    
    log('Answer to fill:', answer);
    
    // Find best matching option
    const bestOption = findBestOption(options, answer);
    
    if (!bestOption) {
      log('No matching option found');
      results.failed.push(`${label.substring(0, 40)} (no match)`);
      return;
    }
    
    // Set the value
    log(`Selecting: "${bestOption.text}" (value: ${bestOption.value})`);
    selectEl.value = bestOption.value;
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    selectEl.dispatchEvent(new Event('input', { bubbles: true }));
    
    results.filled.push(`${label.substring(0, 40)} → ${bestOption.text}`);
  }

  // ============================
  // PROCESS CUSTOM DROPDOWN (DIV-BASED)
  // ============================

  async function processCustomDropdown(dropdownEl, profile, results) {
    // Skip if already processed or hidden
    const style = window.getComputedStyle(dropdownEl);
    if (style.display === 'none' || style.visibility === 'hidden') {
      return;
    }

    const label = findLabelForElement(dropdownEl);
    if (!label) {
      return;
    }
    
    const questionText = label.toLowerCase();
    log(`\n--- Processing Custom Dropdown: "${label.substring(0, 50)}..." ---`);
    
    // Click to open the dropdown
    dropdownEl.click();
    await sleep(300);
    
    // Find options that appeared
    let options = findVisibleOptions();
    log('Options found after click:', options.length);
    
    if (options.length === 0) {
      // Try clicking again or finding a button within
      const btn = dropdownEl.querySelector('button, [role="button"]');
      if (btn) {
        btn.click();
        await sleep(300);
        options = findVisibleOptions();
      }
    }
    
    if (options.length === 0) {
      log('No options found');
      // Close by clicking elsewhere
      document.body.click();
      return;
    }
    
    log('Available options:', options.slice(0, 10).map(o => o.text));
    
    // Determine answer
    const answer = getAnswerForQuestion(questionText, profile, options.map(o => ({ value: o.text, text: o.text })));
    
    if (!answer) {
      document.body.click();
      return;
    }
    
    // Find and click matching option
    const bestOption = options.find(o => 
      normalize(o.text) === normalize(answer) ||
      normalize(o.text).includes(normalize(answer)) ||
      normalize(answer).includes(normalize(o.text))
    );
    
    if (bestOption) {
      log(`Clicking option: "${bestOption.text}"`);
      bestOption.el.click();
      results.filled.push(`${label.substring(0, 40)} → ${bestOption.text}`);
    } else {
      document.body.click();
    }
    
    await sleep(100);
  }

  function findVisibleOptions() {
    const options = [];
    const selectors = [
      '[role="option"]',
      '[role="listbox"] li',
      '[data-radix-popper-content-wrapper] [role="option"]',
      '.select__option',
      '[class*="option"]',
      '[class*="menu"] li',
      '[class*="dropdown"] li'
    ];
    
    for (const selector of selectors) {
      document.querySelectorAll(selector).forEach(el => {
        if (isVisible(el) && el.textContent?.trim()) {
          options.push({ el, text: el.textContent.trim() });
        }
      });
      if (options.length > 0) break;
    }
    
    return options;
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && 
           style.display !== 'none' && style.visibility !== 'hidden';
  }

  // ============================
  // FIND LABEL FOR ELEMENT
  // ============================

  function findLabelForElement(el) {
    // Method 1: Check for associated label via 'for' attribute
    const id = el.id;
    if (id) {
      const label = document.querySelector(`label[for="${id}"]`);
      if (label) return label.textContent?.trim();
    }
    
    // Method 2: Check parent label
    const parentLabel = el.closest('label');
    if (parentLabel) return parentLabel.textContent?.trim();
    
    // Method 3: Look for label in parent container
    const container = el.closest('.field, .form-group, .form-field, div');
    if (container) {
      const label = container.querySelector('label, .label, legend');
      if (label) return label.textContent?.trim();
    }
    
    // Method 4: Check aria-label
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel;
    
    // Method 5: Check aria-labelledby
    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
      const labelEl = document.getElementById(labelledBy);
      if (labelEl) return labelEl.textContent?.trim();
    }
    
    // Method 6: Check previous sibling
    const prevSibling = el.previousElementSibling;
    if (prevSibling && (prevSibling.tagName === 'LABEL' || prevSibling.classList.contains('label'))) {
      return prevSibling.textContent?.trim();
    }
    
    return null;
  }

  // ============================
  // GET ANSWER FOR QUESTION
  // ============================

  function getAnswerForQuestion(questionText, profile, options) {
    const q = questionText.toLowerCase();
    
    // Skip EEO/demographic questions
    if (/gender|race|ethnicity|veteran|disability|sex\b|equal.?opportunity|eeo|demographic|diversity|orientation|pronouns/i.test(q)) {
      log('Skipping EEO/demographic question');
      return null;
    }
    
    // ===== WORK AUTHORIZATION =====
    if (q.includes('authorized to work') || q.includes('legally authorized') || q.includes('eligible to work')) {
      const isAuthorized = profile.workAuthorizationStatus && 
        !['require_sponsorship', 'not_authorized', 'unknown'].includes(profile.workAuthorizationStatus.toLowerCase());
      return isAuthorized !== false ? 'Yes' : 'No';
    }
    
    // ===== SPONSORSHIP =====
    if (q.includes('sponsorship') || q.includes('visa support') || q.includes('require visa') || q.includes('immigration')) {
      const needsSponsorship = profile.requiresSponsorship === true;
      return needsSponsorship ? 'Yes' : 'No';
    }
    
    // ===== EMPLOYMENT AGREEMENTS =====
    if (q.includes('employment agreement') || q.includes('non-compete') || q.includes('employment restriction') || q.includes('subject to any')) {
      return 'No';
    }
    
    // ===== PREVIOUSLY WORKED =====
    if (q.includes('previously worked') || q.includes('worked at') || q.includes('consulted for') || q.includes('employed by')) {
      // Check resume for company mention
      const companyMatch = q.match(/(?:worked|employed|consulted).+?(?:at|by|for)\s+([a-zA-Z0-9\s]+?)(?:\?|$|before)/i);
      if (companyMatch && profile.resumeText) {
        const company = normalize(companyMatch[1]);
        if (profile.resumeText.toLowerCase().includes(company)) {
          return 'Yes';
        }
      }
      return 'No';
    }
    
    // ===== LOCATION - US OR CANADA =====
    if (q.includes('located in') && (q.includes('us or canada') || q.includes('united states or canada') || q.includes('north america'))) {
      const locationStr = `${profile.city} ${profile.state} ${profile.country} ${profile.countryFull}`.toLowerCase();
      const isUSCanada = locationStr.includes('canada') || locationStr.includes('united states') || 
                        locationStr.includes('usa') || locationStr.includes('us') ||
                        profile.country?.toUpperCase() === 'CA' || profile.country?.toUpperCase() === 'US';
      return isUSCanada ? 'Yes' : 'No';
    }
    
    // ===== LOCATION - CANADA =====
    if (q.includes('located in') && q.includes('canada')) {
      const locationStr = `${profile.city} ${profile.state} ${profile.country} ${profile.countryFull}`.toLowerCase();
      return locationStr.includes('canada') || profile.country?.toUpperCase() === 'CA' ? 'Yes' : 'No';
    }
    
    // ===== COUNTRY OF RESIDENCE =====
    if (q.includes('country of residence') || q.includes('current country') || q.includes('what country')) {
      return profile.countryFull || profile.country || 'Canada';
    }
    
    // ===== YEARS OF EXPERIENCE =====
    if (q.includes('years of experience') || q.includes('years experience')) {
      // Check for specific skill/technology
      const skillMatch = q.match(/(\d+)\+?\s*years.+?(?:experience|with|in)\s+([a-zA-Z0-9\s\+\#\.]+)/i);
      if (skillMatch) {
        const requiredYears = parseInt(skillMatch[1]);
        const targetSkill = normalize(skillMatch[2]);
        
        // Check skills with years
        if (profile.skillsWithYears) {
          const matchingSkill = profile.skillsWithYears.find(s => 
            normalize(s.name || '').includes(targetSkill) || targetSkill.includes(normalize(s.name || ''))
          );
          if (matchingSkill && matchingSkill.years >= requiredYears) {
            return 'Yes';
          }
        }
        
        // Check resume
        if (profile.resumeText && profile.resumeText.toLowerCase().includes(targetSkill)) {
          // If in resume, assume they might have experience
          return profile.experienceYears >= requiredYears ? 'Yes' : 'No';
        }
        
        return 'No';
      }
      
      // General years of experience
      if (profile.experienceYears !== null && profile.experienceYears !== undefined) {
        return String(profile.experienceYears);
      }
    }
    
    // ===== DO YOU HAVE EXPERIENCE =====
    if ((q.includes('do you have') || q.includes('experience')) && (q.includes('working') || q.includes('experience'))) {
      // Working for public/SaaS company
      if (q.includes('public') || q.includes('saas') || q.includes('technology company')) {
        // Check resume for relevant companies
        const techCompanyKeywords = ['saas', 'software', 'technology', 'tech', 'startup', 'inc', 'corp'];
        const hasExperience = techCompanyKeywords.some(kw => profile.resumeText?.toLowerCase().includes(kw));
        return hasExperience ? 'Yes' : 'No';
      }
    }
    
    // ===== RELOCATION =====
    if (q.includes('relocat')) {
      const willing = profile.willingToRelocate;
      log('Relocation profile value:', willing);
      
      // Backend sends human-readable labels
      if (willing) {
        // If it looks like already formatted label, return as-is
        if (willing.includes('willing') || willing.includes('discussion') || willing.includes('Yes') || willing.includes('No')) {
          return willing;
        }
        // Map normalized to readable
        const map = {
          'yes': 'Yes - willing to relocate',
          'no': 'No - not willing to relocate',
          'open_to_discussion': 'Open to discussion'
        };
        return map[willing.toLowerCase()] || willing;
      }
      return null;
    }
    
    // ===== NOTICE PERIOD =====
    if (q.includes('notice period') || q.includes('how soon') || q.includes('when can you start') || q.includes('availability')) {
      const notice = profile.noticePeriod;
      log('Notice period profile value:', notice);
      
      if (notice) {
        // Already formatted from backend
        if (notice.includes('available') || notice.includes('notice') || notice.includes('week') || notice.includes('month')) {
          return notice;
        }
        const map = {
          'immediately': 'Immediately available',
          'two_weeks': '2 weeks notice',
          'one_month': '1 month notice',
          'two_months': '2 months notice',
          'three_months_plus': '3+ months notice'
        };
        return map[notice.toLowerCase()] || notice;
      }
      return null;
    }
    
    // ===== WORK ARRANGEMENT =====
    if (q.includes('work arrangement') || q.includes('work preference') || (q.includes('remote') && q.includes('hybrid'))) {
      const arrangement = profile.workArrangement;
      if (arrangement) {
        if (['Remote', 'Hybrid', 'On-site', 'Flexible'].includes(arrangement)) {
          return arrangement;
        }
        const map = { 'remote': 'Remote', 'hybrid': 'Hybrid', 'onsite': 'On-site', 'flexible': 'Flexible' };
        return map[arrangement.toLowerCase()] || arrangement;
      }
      return null;
    }
    
    // ===== COMFORTABLE WORKING REMOTELY =====
    if (q.includes('remote') && (q.includes('comfortable') || q.includes('willing') || q.includes('open to'))) {
      const arr = profile.workArrangement?.toLowerCase();
      return ['remote', 'hybrid', 'flexible'].includes(arr) ? 'Yes' : 'No';
    }
    
    // ===== EDUCATION =====
    if (q.includes('education') || q.includes('degree') || q.includes('highest level')) {
      const edu = profile.education;
      if (edu) {
        if (edu.includes('Degree') || edu.includes('Diploma') || edu.includes('College')) {
          return edu;
        }
        const map = {
          'high_school': 'High School Diploma / GED',
          'some_college': 'Some College (No Degree)',
          'associate': 'Associate Degree',
          'bachelor': "Bachelor's Degree",
          'master': "Master's Degree",
          'doctorate': 'Doctorate (PhD, MD, JD, etc.)',
          'professional': 'Professional Certification'
        };
        return map[edu.toLowerCase()] || edu;
      }
      return null;
    }
    
    // ===== AGE 18+ =====
    if (q.includes('18 years') || q.includes('legal age') || q.includes('at least 18')) {
      return 'Yes';
    }
    
    // ===== BACKGROUND CHECK =====
    if (q.includes('background check')) {
      return 'Yes';
    }
    
    // ===== HOW DID YOU HEAR =====
    if (q.includes('how did you hear') || q.includes('how did you find') || q.includes('source')) {
      return profile.referralSource || 'LinkedIn';
    }
    
    // ===== PREFERRED NAME =====
    if (q.includes('preferred name') || q.includes('call you') || q.includes('name you')) {
      return profile.firstName || null;
    }
    
    // ===== LINKEDIN =====
    if (q.includes('linkedin')) {
      return profile.linkedinUrl || null;
    }
    
    // ===== GITHUB =====
    if (q.includes('github')) {
      return profile.githubUrl || null;
    }
    
    // ===== PORTFOLIO/WEBSITE =====
    if (q.includes('portfolio') || q.includes('website') || q.includes('personal url')) {
      return profile.portfolioUrl || null;
    }
    
    return null;
  }

  // ============================
  // FIND BEST MATCHING OPTION
  // ============================

  function findBestOption(options, answer) {
    if (!answer || !options || options.length === 0) return null;
    
    const answerNorm = normalize(answer);
    const answerVariants = expandSynonyms(answer);
    
    // Exact match
    for (const opt of options) {
      if (normalize(opt.text) === answerNorm) {
        return opt;
      }
    }
    
    // Contains match
    for (const opt of options) {
      const optNorm = normalize(opt.text);
      if (optNorm.includes(answerNorm) || answerNorm.includes(optNorm)) {
        return opt;
      }
    }
    
    // Synonym match
    for (const variant of answerVariants) {
      const varNorm = normalize(variant);
      for (const opt of options) {
        const optNorm = normalize(opt.text);
        if (optNorm === varNorm || optNorm.includes(varNorm) || varNorm.includes(optNorm)) {
          return opt;
        }
      }
    }
    
    // Word overlap
    const answerWords = answerNorm.split(' ').filter(w => w.length > 2);
    for (const opt of options) {
      const optWords = normalize(opt.text).split(' ').filter(w => w.length > 2);
      const overlap = answerWords.filter(w => optWords.includes(w)).length;
      if (overlap >= 1 && overlap / answerWords.length >= 0.5) {
        return opt;
      }
    }
    
    return null;
  }

  // ============================
  // PERSONAL INFO FILLING
  // ============================

  async function fillPersonalInfo(data, results) {
    const personalInfo = data.personal_info || {};
    
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
    
    if (personalInfo.email) {
      const selectors = [
        'input[type="email"]', 'input[name*="email" i]',
        'input[id*="email" i]', 'input[autocomplete="email"]'
      ];
      if (await fillField(selectors, personalInfo.email)) {
        results.filled.push('Email');
      }
    }

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
    
    if (personalInfo.linkedin) {
      const selectors = [
        'input[name*="linkedin" i]', 'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]'
      ];
      if (await fillField(selectors, personalInfo.linkedin)) {
        results.filled.push('LinkedIn');
      }
    }

    if (personalInfo.github) {
      const selectors = [
        'input[name*="github" i]', 'input[id*="github" i]',
        'input[placeholder*="github" i]'
      ];
      if (await fillField(selectors, personalInfo.github)) {
        results.filled.push('GitHub');
      }
    }

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
    
    if (location.city) {
      const selectors = [
        'input[name*="city" i]', 'input[id*="city" i]',
        'input[autocomplete="address-level2"]'
      ];
      if (await fillField(selectors, location.city)) {
        results.filled.push('City');
      }
    }

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
        if (await setFieldValue(element, value)) {
          return true;
        }
      }
    }
    return false;
  }

  async function setFieldValue(element, value) {
    if (!element || !value) return false;
    
    try {
      const style = window.getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden' || element.disabled) {
        return false;
      }

      const tag = element.tagName?.toLowerCase();
      
      if (tag === 'select') {
        const options = Array.from(element.options);
        const match = options.find(opt => 
          opt.text?.toLowerCase().includes(value.toLowerCase()) ||
          value.toLowerCase().includes(opt.text?.toLowerCase())
        );
        if (match) {
          element.value = match.value;
          element.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
        return false;
      }
      
      if (tag === 'input' && element.type === 'file') return false;
      
      if (element.isContentEditable) {
        element.innerHTML = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        return true;
      }
      
      element.focus();
      
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
      
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
      element.blur();
      
      return true;
      
    } catch (e) {
      log('Error setting field value:', e);
      return false;
    }
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  log('Content script loaded - DEBUG_DROPDOWNS:', DEBUG_DROPDOWNS);
})();
