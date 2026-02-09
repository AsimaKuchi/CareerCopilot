// JobMatch AI - Content Script
// Injected into job application pages to handle auto-filling

(function() {
  'use strict';

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
      
      console.log('[JobMatch AI] Starting auto-fill for:', atsType);
      console.log('[JobMatch AI] Data received:', Object.keys(data));

      // Fill personal information
      await fillPersonalInfo(data, results);
      
      // Fill contact information
      await fillContactInfo(data, results);
      
      // Fill links (LinkedIn, GitHub, Portfolio)
      await fillLinks(data, results);
      
      // Fill work authorization
      await fillWorkAuthorization(data, results);
      
      // Fill location
      await fillLocation(data, results);
      
      // Handle resume upload
      await handleResumeUpload(data, results);
      
      // Handle cover letter
      await fillCoverLetter(data, results);
      
      // Fill custom screening questions using AI
      await fillCustomScreeningQuestions(data, results);

      results.success = results.filled.length > 0;
      results.filledCount = results.filled.length;
      
      console.log('[JobMatch AI] Auto-fill complete:', results);
      
    } catch (error) {
      console.error('[JobMatch AI] Auto-fill error:', error);
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
    if (/pinpoint/i.test(url)) return 'pinpoint';
    if (/bamboohr/i.test(url)) return 'bamboohr';
    if (/teamtailor/i.test(url)) return 'teamtailor';
    if (/jobvite/i.test(url)) return 'jobvite';
    if (/workday/i.test(url)) return 'workday';
    if (/taleo/i.test(url)) return 'taleo';
    if (/icims/i.test(url)) return 'icims';
    return 'unknown';
  }

  // ==========================================
  // CUSTOM SCREENING QUESTIONS (PROFILE-BASED)
  // ==========================================
  
  async function fillCustomScreeningQuestions(data, results) {
    console.log('[JobMatch AI] Looking for custom screening questions...');
    
    // Build a comprehensive profile context from existing data
    const profile = {
      firstName: data.personal_info?.first_name || '',
      lastName: data.personal_info?.last_name || '',
      fullName: data.personal_info?.full_name || '',
      email: data.personal_info?.email || '',
      phone: data.personal_info?.phone || '',
      linkedin: data.personal_info?.linkedin || '',
      github: data.personal_info?.github || '',
      portfolio: data.personal_info?.portfolio || '',
      city: data.personal_info?.location?.city || '',
      state: data.personal_info?.location?.state || '',
      country: data.personal_info?.location?.country || '',
      workAuth: data.profile_context?.work_authorization || '',
      requiresSponsorship: data.profile_context?.requires_sponsorship,
      skills: data.profile_context?.skills || [],
      skillsWithYears: data.profile_context?.skills_with_years || [],
      yearsExperience: data.profile_context?.experience_years || '',
      resumeText: (data.profile_context?.resume_text || '').toLowerCase(),
      willingToRelocate: data.profile_context?.willing_to_relocate,  // "yes", "no", "open_to_discussion"
      salaryMin: data.profile_context?.salary_min,
      salaryMax: data.profile_context?.salary_max,
      noticePeriod: data.profile_context?.notice_period,  // "immediate", "2_weeks", "1_month", etc
      availabilityDate: data.profile_context?.availability_date,
      education: data.profile_context?.education,  // "bachelors", "masters", etc
      workArrangement: data.profile_context?.work_arrangement,  // "remote", "hybrid", "onsite"
      referralSource: data.profile_context?.referral_source,
    };
    
    console.log('[JobMatch AI] Profile context:', {
      name: profile.fullName,
      location: `${profile.city}, ${profile.state}, ${profile.country}`,
      skills: profile.skills.length,
      hasResume: profile.resumeText.length > 0
    });
    
    // Find all form fields that might be screening questions
    const allFields = findAllFormFields();
    console.log(`[JobMatch AI] Found ${allFields.length} potential fields to fill`);
    
    for (const field of allFields) {
      const answer = getAnswerFromProfile(field, profile);
      if (answer) {
        const filled = await setFieldAnswer(field, answer);
        if (filled) {
          results.filled.push(field.label.substring(0, 40) + (field.label.length > 40 ? '...' : ''));
        }
      }
    }
  }
  
  function findAllFormFields() {
    const fields = [];
    
    // Find all labeled inputs, selects, and textareas
    document.querySelectorAll('label').forEach(label => {
      const labelText = label.textContent?.trim() || '';
      if (labelText.length < 5) return;
      
      // Find associated input
      const forId = label.getAttribute('for');
      let input = forId ? document.getElementById(forId) : null;
      
      // If no for attribute, look for input inside label
      if (!input) {
        input = label.querySelector('input, select, textarea');
      }
      
      // If still no input, look for adjacent sibling
      if (!input) {
        const parent = label.parentElement;
        input = parent?.querySelector('input, select, textarea');
      }
      
      if (input && !input.value) {
        const options = [];
        if (input.tagName === 'SELECT') {
          Array.from(input.options).forEach(opt => {
            if (opt.value && !opt.text.toLowerCase().includes('select')) {
              options.push({ value: opt.value, text: opt.text.trim() });
            }
          });
        }
        
        // Check for radio buttons
        const radios = label.closest('fieldset, div, form')?.querySelectorAll(`input[type="radio"][name="${input.name || ''}"]`);
        
        fields.push({
          label: labelText,
          labelLower: labelText.toLowerCase(),
          element: input,
          type: input.tagName.toLowerCase(),
          inputType: input.type || 'text',
          options: options,
          radios: radios?.length > 1 ? Array.from(radios) : null
        });
      }
    });
    
    // Also look for aria-label fields
    document.querySelectorAll('input[aria-label], select[aria-label], textarea[aria-label]').forEach(input => {
      const labelText = input.getAttribute('aria-label') || '';
      if (labelText.length < 5 || input.value) return;
      
      const options = [];
      if (input.tagName === 'SELECT') {
        Array.from(input.options).forEach(opt => {
          if (opt.value && !opt.text.toLowerCase().includes('select')) {
            options.push({ value: opt.value, text: opt.text.trim() });
          }
        });
      }
      
      fields.push({
        label: labelText,
        labelLower: labelText.toLowerCase(),
        element: input,
        type: input.tagName.toLowerCase(),
        inputType: input.type || 'text',
        options: options,
        radios: null
      });
    });
    
    return fields;
  }
  
  function getAnswerFromProfile(field, profile) {
    const q = field.labelLower;
    const opts = field.options.map(o => o.text.toLowerCase());
    
    // ===== NAME QUESTIONS =====
    if (q.includes('preferred name') || q.includes('name you') || q.includes('call you')) {
      return profile.firstName;
    }
    if (q.includes('full name') && !q.includes('company')) {
      return profile.fullName;
    }
    
    // ===== CONTACT QUESTIONS =====
    if (q.includes('linkedin')) {
      return profile.linkedin;
    }
    if (q.includes('github')) {
      return profile.github;
    }
    if (q.includes('portfolio') || q.includes('website') || q.includes('personal url')) {
      return profile.portfolio;
    }
    
    // ===== LOCATION QUESTIONS =====
    if (q.includes('country of residence') || q.includes('current country') || q.includes('what country')) {
      if (field.options.length > 0) {
        return findBestOption(field.options, [profile.country]);
      }
      return profile.country;
    }
    if (q.includes('city')) {
      return profile.city;
    }
    if (q.includes('state') || q.includes('province')) {
      if (field.options.length > 0) {
        return findBestOption(field.options, [profile.state]);
      }
      return profile.state;
    }
    
    // Location check questions (Yes/No)
    if (q.includes('located in') || q.includes('based in') || q.includes('reside in')) {
      const locationLower = `${profile.city} ${profile.state} ${profile.country}`.toLowerCase();
      
      if (q.includes('us or canada') || q.includes('united states or canada') || q.includes('north america')) {
        const isUSCanada = locationLower.includes('canada') || locationLower.includes('united states') || 
                          locationLower.includes('usa') || profile.country.toLowerCase() === 'us';
        return findYesNoOption(field.options, isUSCanada);
      }
      if (q.includes('canada')) {
        return findYesNoOption(field.options, locationLower.includes('canada'));
      }
      if (q.includes('united states') || q.includes('us ')) {
        const isUS = locationLower.includes('united states') || locationLower.includes('usa') || profile.country.toLowerCase() === 'us';
        return findYesNoOption(field.options, isUS);
      }
    }
    
    // Timezone questions
    if (q.includes('timezone') || q.includes('time zone')) {
      const cityLower = profile.city.toLowerCase();
      const stateLower = profile.state.toLowerCase();
      
      // EST timezone cities/states
      const estLocations = ['toronto', 'montreal', 'ottawa', 'new york', 'boston', 'miami', 'atlanta', 'ontario', 'quebec', 'florida', 'georgia', 'new jersey', 'pennsylvania', 'virginia', 'north carolina'];
      // PST timezone
      const pstLocations = ['vancouver', 'seattle', 'los angeles', 'san francisco', 'portland', 'british columbia', 'california', 'washington', 'oregon'];
      // CST timezone
      const cstLocations = ['chicago', 'houston', 'dallas', 'austin', 'winnipeg', 'manitoba', 'texas', 'illinois'];
      
      const isEST = estLocations.some(loc => cityLower.includes(loc) || stateLower.includes(loc));
      const isPST = pstLocations.some(loc => cityLower.includes(loc) || stateLower.includes(loc));
      const isCST = cstLocations.some(loc => cityLower.includes(loc) || stateLower.includes(loc));
      
      if (q.includes('est') || q.includes('eastern')) {
        return findYesNoOption(field.options, isEST);
      }
      if (q.includes('pst') || q.includes('pacific')) {
        return findYesNoOption(field.options, isPST);
      }
      if (q.includes('cst') || q.includes('central')) {
        return findYesNoOption(field.options, isCST);
      }
    }
    
    // ===== WORK AUTHORIZATION =====
    if (q.includes('authorized to work') || q.includes('legally authorized') || q.includes('eligible to work') || q.includes('work authorization')) {
      const isAuthorized = profile.workAuth && 
        (profile.workAuth.toLowerCase().includes('citizen') || 
         profile.workAuth.toLowerCase().includes('permanent') ||
         profile.workAuth.toLowerCase().includes('authorized') ||
         profile.workAuth.toLowerCase().includes('green card'));
      return findYesNoOption(field.options, isAuthorized !== false);
    }
    
    if (q.includes('sponsorship') || q.includes('visa support') || q.includes('require visa')) {
      const needsSponsorship = profile.requiresSponsorship === true;
      // Note: question usually asks "will you REQUIRE sponsorship" so Yes = needs, No = doesn't need
      return findYesNoOption(field.options, needsSponsorship);
    }
    
    // ===== EXPERIENCE QUESTIONS =====
    if (q.includes('years of experience') || q.includes('years experience')) {
      if (q.includes('total') || (!q.includes('with') && !q.includes('in '))) {
        // Total years of experience
        if (profile.yearsExperience) {
          if (field.options.length > 0) {
            return findBestOption(field.options, [profile.yearsExperience.toString(), `${profile.yearsExperience}+`, `${profile.yearsExperience} years`]);
          }
          return profile.yearsExperience.toString();
        }
      } else {
        // Years with specific skill - check resume and skills
        const skillMatch = q.match(/(?:with|in|using)\s+([a-zA-Z0-9\s\+\#\.]+?)(?:\?|$|\s+years|\s+experience)/i);
        if (skillMatch) {
          const skill = skillMatch[1].trim().toLowerCase();
          const hasSkill = profile.skills.some(s => s.toLowerCase().includes(skill)) || 
                          profile.resumeText.includes(skill);
          if (hasSkill) {
            return findYesNoOption(field.options, true) || findBestOption(field.options, ['yes', '2+', '3+', '1+', '2-3', '3-5']);
          } else {
            return findYesNoOption(field.options, false) || findBestOption(field.options, ['no', '0', 'none', 'less than']);
          }
        }
      }
    }
    
    // Do you have experience with X?
    if (q.includes('do you have') && (q.includes('experience') || q.includes('knowledge') || q.includes('proficiency'))) {
      const skillMatch = q.match(/(?:experience|knowledge|proficiency)\s+(?:with|in|of|using)\s+([a-zA-Z0-9\s\+\#\.]+?)(?:\?|$)/i);
      if (skillMatch) {
        const skill = skillMatch[1].trim().toLowerCase();
        const hasSkill = profile.skills.some(s => s.toLowerCase().includes(skill)) || 
                        profile.resumeText.includes(skill);
        return findYesNoOption(field.options, hasSkill);
      }
    }
    
    // ===== COMMON YES/NO QUESTIONS =====
    if (q.includes('employment agreement') || q.includes('non-compete') || q.includes('employment restriction')) {
      return findYesNoOption(field.options, false); // Default: No restrictions
    }
    
    if (q.includes('previously worked') || q.includes('worked at') || q.includes('employed by') || q.includes('consulted for')) {
      // Check if company name is in resume
      const companyMatch = q.match(/(?:worked|employed|consulted)\s+(?:at|by|for)\s+([a-zA-Z0-9\s]+?)(?:\?|$|before)/i);
      if (companyMatch) {
        const company = companyMatch[1].trim().toLowerCase();
        const workedThere = profile.resumeText.includes(company);
        return findYesNoOption(field.options, workedThere);
      }
      return findYesNoOption(field.options, false); // Default: No
    }
    
    if (q.includes('18 years') || q.includes('legal age') || q.includes('at least 18')) {
      return findYesNoOption(field.options, true);
    }
    
    if (q.includes('background check')) {
      return findYesNoOption(field.options, true);
    }
    
    if (q.includes('drug test') || q.includes('drug screen')) {
      return findYesNoOption(field.options, true);
    }
    
    if (q.includes('remote') && (q.includes('comfortable') || q.includes('willing') || q.includes('open to'))) {
      return findYesNoOption(field.options, true);
    }
    
    if (q.includes('relocate') || q.includes('relocation')) {
      // Use actual profile setting - values: "yes", "no", "open_to_discussion", "unknown"
      const willRelocate = profile.willingToRelocate;
      console.log('[JobMatch AI] Relocation setting:', willRelocate);
      if (willRelocate === 'yes') {
        return findYesNoOption(field.options, true);
      } else if (willRelocate === 'no') {
        return findYesNoOption(field.options, false);
      } else if (willRelocate === 'open_to_discussion') {
        return findBestOption(field.options, ['maybe', 'open', 'depends', 'possibly']) || findYesNoOption(field.options, true);
      }
      // If unknown or not set, don't answer
      return null;
    }
    
    // ===== REMOTE WORK =====
    if (q.includes('remote') && (q.includes('comfortable') || q.includes('willing') || q.includes('open to') || q.includes('work remotely'))) {
      // Values: "remote", "hybrid", "onsite"
      const workArrangement = profile.workArrangement;
      console.log('[JobMatch AI] Work arrangement:', workArrangement);
      if (workArrangement === 'remote') {
        return findYesNoOption(field.options, true);
      } else if (workArrangement === 'onsite') {
        return findYesNoOption(field.options, false);
      } else if (workArrangement === 'hybrid') {
        return findYesNoOption(field.options, true); // Hybrid usually OK with remote
      }
      return null;
    }
    
    // ===== SALARY EXPECTATION =====
    if (q.includes('salary') && (q.includes('expectation') || q.includes('requirement') || q.includes('desired') || q.includes('range'))) {
      if (profile.salaryMin && profile.salaryMax) {
        return `$${profile.salaryMin.toLocaleString()} - $${profile.salaryMax.toLocaleString()}`;
      } else if (profile.salaryMin) {
        return `$${profile.salaryMin.toLocaleString()}+`;
      } else if (profile.salaryMax) {
        return `Up to $${profile.salaryMax.toLocaleString()}`;
      }
      return null;
    }
    
    // ===== NOTICE PERIOD =====
    if (q.includes('notice period') || q.includes('current notice') || q.includes('how soon')) {
      // Values: "immediate", "2_weeks", "1_month", "2_months", "3_months"
      const notice = profile.noticePeriod;
      console.log('[JobMatch AI] Notice period:', notice);
      if (notice && notice !== 'unknown') {
        const noticeMap = {
          'immediate': 'Immediately',
          '2_weeks': '2 weeks',
          '1_month': '1 month',
          '2_months': '2 months',
          '3_months': '3 months',
          '3_months_plus': '3+ months'
        };
        const displayValue = noticeMap[notice] || notice;
        if (field.options.length > 0) {
          return findBestOption(field.options, [displayValue, notice]);
        }
        return displayValue;
      }
      return null;
    }
    
    // ===== START DATE =====
    if (q.includes('start date') || q.includes('when can you start') || q.includes('available to start')) {
      if (profile.availabilityDate) {
        return profile.availabilityDate;
      }
      // Use notice period as fallback
      if (profile.noticePeriod && profile.noticePeriod !== 'unknown') {
        const noticeMap = {
          'immediate': 'Immediately',
          '2_weeks': 'In 2 weeks',
          '1_month': 'In 1 month',
          '2_months': 'In 2 months',
          '3_months': 'In 3 months'
        };
        return noticeMap[profile.noticePeriod] || null;
      }
      return null;
    }
    
    // ===== EDUCATION =====
    if (q.includes('education') || q.includes('degree') || q.includes('highest level')) {
      // Values: "high_school", "associates", "bachelors", "masters", "phd", etc
      const edu = profile.education;
      console.log('[JobMatch AI] Education:', edu);
      if (edu && edu !== 'unknown') {
        const eduMap = {
          'high_school': "High School",
          'associates': "Associate's Degree",
          'bachelors': "Bachelor's Degree",
          'masters': "Master's Degree",
          'phd': "PhD",
          'doctorate': "Doctorate"
        };
        const displayValue = eduMap[edu] || edu;
        if (field.options.length > 0) {
          return findBestOption(field.options, [displayValue, edu, "Bachelor", "Master", "PhD"]);
        }
        return displayValue;
      }
      return null;
    }
    
    // ===== HOW DID YOU HEAR =====
    if (q.includes('how did you hear') || q.includes('how did you find') || q.includes('referred by') || q.includes('source')) {
      const source = profile.referralSource;
      if (source) {
        if (field.options.length > 0) {
          return findBestOption(field.options, [source, source.toLowerCase(), 'linkedin', 'job board', 'online']);
        }
        return source;
      }
      return findBestOption(field.options, ['linkedin', 'job board', 'online', 'website']) || 'LinkedIn';
    }
    
    return null;
  }
  
  function findYesNoOption(options, isYes) {
    if (options.length === 0) return isYes ? 'Yes' : 'No';
    
    const yesWords = ['yes', 'true', 'i am', 'i do', 'i have', 'i will'];
    const noWords = ['no', 'false', 'i am not', "i don't", 'i have not', 'i will not'];
    
    const searchWords = isYes ? yesWords : noWords;
    
    for (const opt of options) {
      const optLower = opt.text.toLowerCase();
      if (searchWords.some(w => optLower.includes(w) || optLower === w)) {
        return opt.text;
      }
    }
    
    // Fallback
    return isYes ? 'Yes' : 'No';
  }
  
  function findBestOption(options, searchTerms) {
    for (const term of searchTerms) {
      for (const opt of options) {
        if (opt.text.toLowerCase().includes(term.toLowerCase())) {
          return opt.text;
        }
      }
    }
    return null;
  }
  
  async function setFieldAnswer(field, answer) {
    try {
      if (field.type === 'select' && field.element) {
        const options = Array.from(field.element.options);
        const matchingOption = options.find(opt => 
          opt.text.toLowerCase() === answer.toLowerCase() ||
          opt.text.toLowerCase().includes(answer.toLowerCase()) ||
          answer.toLowerCase().includes(opt.text.toLowerCase())
        );
        
        if (matchingOption) {
          field.element.value = matchingOption.value;
          field.element.dispatchEvent(new Event('change', { bubbles: true }));
          console.log(`[JobMatch AI] ✓ ${field.label.substring(0, 30)}... = ${matchingOption.text}`);
          return true;
        }
      }
      
      if (field.radios) {
        for (const radio of field.radios) {
          const radioLabel = radio.closest('label')?.textContent?.trim() || radio.value;
          if (radioLabel.toLowerCase().includes(answer.toLowerCase()) ||
              answer.toLowerCase().includes(radioLabel.toLowerCase())) {
            radio.click();
            console.log(`[JobMatch AI] ✓ ${field.label.substring(0, 30)}... = ${radioLabel}`);
            return true;
          }
        }
      }
      
      if ((field.type === 'input' || field.type === 'textarea') && field.element) {
        if (field.inputType === 'radio' || field.inputType === 'checkbox') {
          return false;
        }
        
        field.element.focus();
        field.element.value = answer;
        field.element.dispatchEvent(new Event('input', { bubbles: true }));
        field.element.dispatchEvent(new Event('change', { bubbles: true }));
        field.element.blur();
        console.log(`[JobMatch AI] ✓ ${field.label.substring(0, 30)}... = ${answer}`);
        return true;
      }
    } catch (error) {
      console.error('[JobMatch AI] Error setting answer:', error);
    }
    
    return false;
  }

  // ==========================================
  // FIELD FILLING FUNCTIONS
  // ==========================================

  async function fillPersonalInfo(data, results) {
    const personalInfo = data.personal_info || {};
    
    // First Name
    const firstNameSelectors = [
      'input[name*="first_name" i]',
      'input[name*="firstname" i]',
      'input[id*="first_name" i]',
      'input[id*="firstname" i]',
      'input[autocomplete="given-name"]',
      'input[placeholder*="first name" i]',
      'input[aria-label*="first name" i]',
      '#first_name',
      '#firstName'
    ];
    
    if (personalInfo.first_name) {
      if (await fillField(firstNameSelectors, personalInfo.first_name)) {
        results.filled.push('First Name');
      } else {
        results.failed.push('First Name');
      }
    }

    // Last Name
    const lastNameSelectors = [
      'input[name*="last_name" i]',
      'input[name*="lastname" i]',
      'input[id*="last_name" i]',
      'input[id*="lastname" i]',
      'input[autocomplete="family-name"]',
      'input[placeholder*="last name" i]',
      'input[aria-label*="last name" i]',
      '#last_name',
      '#lastName'
    ];
    
    if (personalInfo.last_name) {
      if (await fillField(lastNameSelectors, personalInfo.last_name)) {
        results.filled.push('Last Name');
      } else {
        results.failed.push('Last Name');
      }
    }

    // Full Name (some forms use this instead)
    const fullNameSelectors = [
      'input[name*="full_name" i]',
      'input[name*="fullname" i]',
      'input[id*="full_name" i]',
      'input[autocomplete="name"]',
      'input[placeholder*="full name" i]',
      'input[aria-label*="full name" i]'
    ];
    
    if (personalInfo.full_name) {
      if (await fillField(fullNameSelectors, personalInfo.full_name)) {
        results.filled.push('Full Name');
      }
    }
  }

  async function fillContactInfo(data, results) {
    const personalInfo = data.personal_info || {};
    
    // Email
    const emailSelectors = [
      'input[type="email"]',
      'input[name*="email" i]',
      'input[id*="email" i]',
      'input[autocomplete="email"]',
      'input[placeholder*="email" i]',
      'input[aria-label*="email" i]'
    ];
    
    if (personalInfo.email) {
      if (await fillField(emailSelectors, personalInfo.email)) {
        results.filled.push('Email');
      } else {
        results.failed.push('Email');
      }
    }

    // Phone
    const phoneSelectors = [
      'input[type="tel"]',
      'input[name*="phone" i]',
      'input[id*="phone" i]',
      'input[autocomplete="tel"]',
      'input[placeholder*="phone" i]',
      'input[aria-label*="phone" i]',
      'input[name*="mobile" i]'
    ];
    
    if (personalInfo.phone) {
      if (await fillField(phoneSelectors, personalInfo.phone)) {
        results.filled.push('Phone');
      } else {
        results.failed.push('Phone');
      }
    }
  }

  async function fillLinks(data, results) {
    const personalInfo = data.personal_info || {};
    
    // LinkedIn
    const linkedinSelectors = [
      'input[name*="linkedin" i]',
      'input[id*="linkedin" i]',
      'input[placeholder*="linkedin" i]',
      'input[aria-label*="linkedin" i]'
    ];
    
    if (personalInfo.linkedin) {
      if (await fillField(linkedinSelectors, personalInfo.linkedin)) {
        results.filled.push('LinkedIn');
      }
    }

    // GitHub
    const githubSelectors = [
      'input[name*="github" i]',
      'input[id*="github" i]',
      'input[placeholder*="github" i]',
      'input[aria-label*="github" i]'
    ];
    
    if (personalInfo.github) {
      if (await fillField(githubSelectors, personalInfo.github)) {
        results.filled.push('GitHub');
      }
    }

    // Portfolio/Website
    const portfolioSelectors = [
      'input[name*="portfolio" i]',
      'input[name*="website" i]',
      'input[name*="personal_url" i]',
      'input[id*="portfolio" i]',
      'input[id*="website" i]',
      'input[type="url"]',
      'input[placeholder*="portfolio" i]',
      'input[placeholder*="website" i]'
    ];
    
    if (personalInfo.portfolio || personalInfo.website) {
      if (await fillField(portfolioSelectors, personalInfo.portfolio || personalInfo.website)) {
        results.filled.push('Portfolio/Website');
      }
    }
  }

  async function fillLocation(data, results) {
    const location = data.personal_info?.location || {};
    
    // City
    const citySelectors = [
      'input[name*="city" i]',
      'input[id*="city" i]',
      'input[autocomplete="address-level2"]',
      'input[placeholder*="city" i]'
    ];
    
    if (location.city) {
      if (await fillField(citySelectors, location.city)) {
        results.filled.push('City');
      }
    }

    // State/Province
    const stateSelectors = [
      'input[name*="state" i]',
      'input[name*="province" i]',
      'input[id*="state" i]',
      'input[autocomplete="address-level1"]',
      'select[name*="state" i]',
      'select[id*="state" i]'
    ];
    
    if (location.state) {
      if (await fillField(stateSelectors, location.state)) {
        results.filled.push('State/Province');
      }
    }

    // Country
    const countrySelectors = [
      'select[name*="country" i]',
      'select[id*="country" i]',
      'input[name*="country" i]',
      'input[autocomplete="country"]'
    ];
    
    if (location.country) {
      if (await fillField(countrySelectors, location.country)) {
        results.filled.push('Country');
      }
    }

    // Address (combined)
    const addressSelectors = [
      'input[name*="address" i]',
      'input[id*="address" i]',
      'input[autocomplete="street-address"]',
      'textarea[name*="address" i]'
    ];
    
    const fullAddress = [location.city, location.state, location.country].filter(Boolean).join(', ');
    if (fullAddress) {
      await fillField(addressSelectors, fullAddress);
    }
  }

  async function fillWorkAuthorization(data, results) {
    const questions = data.questions || [];
    
    // Find work authorization questions
    const workAuthQuestion = questions.find(q => 
      q.field_type === 'work_authorization' || 
      q.question?.toLowerCase().includes('authorized') ||
      q.question?.toLowerCase().includes('sponsorship') ||
      q.question?.toLowerCase().includes('work permit')
    );
    
    if (!workAuthQuestion) return;
    
    // Try to find and fill work authorization fields
    const workAuthSelectors = [
      'select[name*="authorized" i]',
      'select[name*="work_auth" i]',
      'select[name*="sponsorship" i]',
      'input[name*="authorized" i]',
      'input[name*="sponsorship" i]'
    ];
    
    // Also look for radio buttons
    const radioSelectors = [
      'input[type="radio"][name*="authorized" i]',
      'input[type="radio"][name*="sponsorship" i]',
      'input[type="radio"][name*="legally" i]'
    ];
    
    const value = workAuthQuestion.current_value;
    
    // Try dropdown first
    let filled = await fillField(workAuthSelectors, value);
    
    // Try radio buttons
    if (!filled) {
      const radios = document.querySelectorAll(radioSelectors.join(', '));
      for (const radio of radios) {
        const label = radio.closest('label')?.textContent || radio.getAttribute('value') || '';
        if (label.toLowerCase().includes('yes') && value?.toLowerCase().includes('yes')) {
          radio.click();
          filled = true;
          break;
        } else if (label.toLowerCase().includes('no') && value?.toLowerCase().includes('no')) {
          radio.click();
          filled = true;
          break;
        }
      }
    }
    
    if (filled) {
      results.filled.push('Work Authorization');
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
      'input[type="file"][accept*=".doc"]',
      'input[type="file"]'
    ];

    for (const selector of fileInputSelectors) {
      const fileInput = document.querySelector(selector);
      if (fileInput) {
        try {
          // Convert base64 to blob
          const byteCharacters = atob(resume.file_data);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: resume.mime_type || 'application/pdf' });
          
          // Create file from blob
          const file = new File([blob], resume.filename || 'resume.pdf', { 
            type: resume.mime_type || 'application/pdf' 
          });
          
          // Create DataTransfer to set files
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;
          
          // Trigger change event
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
          
          results.filled.push('Resume');
          console.log('[JobMatch AI] Resume uploaded successfully');
          return;
        } catch (error) {
          console.error('[JobMatch AI] Resume upload error:', error);
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

    const coverLetterSelectors = [
      'textarea[name*="cover" i]',
      'textarea[id*="cover" i]',
      'textarea[placeholder*="cover letter" i]',
      'textarea[aria-label*="cover letter" i]',
      'div[contenteditable="true"][aria-label*="cover" i]'
    ];

    if (await fillField(coverLetterSelectors, coverLetter, true)) {
      results.filled.push('Cover Letter');
    } else {
      // Try to find cover letter file upload
      const fileInputSelectors = [
        'input[type="file"][name*="cover" i]',
        'input[type="file"][id*="cover" i]'
      ];
      
      for (const selector of fileInputSelectors) {
        const input = document.querySelector(selector);
        if (input) {
          results.skipped.push('Cover Letter (file upload field - paste manually)');
          return;
        }
      }
      
      results.skipped.push('Cover Letter (field not found)');
    }
  }

  async function fillCustomQuestions(data, results) {
    const questions = data.questions || [];
    
    for (const q of questions) {
      if (q.field_type === 'work_authorization') continue; // Already handled
      
      const value = q.current_value;
      if (!value) continue;
      
      // Try to find matching field by question text
      const questionText = q.question?.toLowerCase() || '';
      
      // Look for labels that match the question
      const labels = document.querySelectorAll('label');
      for (const label of labels) {
        const labelText = label.textContent?.toLowerCase() || '';
        if (labelText.includes(questionText.substring(0, 20)) || questionText.includes(labelText.substring(0, 20))) {
          const forId = label.getAttribute('for');
          if (forId) {
            const input = document.getElementById(forId);
            if (input && await setFieldValue(input, value)) {
              results.filled.push(q.question?.substring(0, 30) + '...');
              break;
            }
          }
          
          // Check for input inside label
          const inputInLabel = label.querySelector('input, textarea, select');
          if (inputInLabel && await setFieldValue(inputInLabel, value)) {
            results.filled.push(q.question?.substring(0, 30) + '...');
            break;
          }
        }
      }
    }
  }

  // ==========================================
  // UTILITY FUNCTIONS
  // ==========================================

  async function fillField(selectors, value, isTextarea = false) {
    if (!value) return false;
    
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        if (await setFieldValue(element, value, isTextarea)) {
          return true;
        }
      }
    }
    return false;
  }

  async function setFieldValue(element, value, isTextarea = false) {
    if (!element || !value) return false;
    
    try {
      // Check if element is visible and not disabled
      const style = window.getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden' || element.disabled) {
        return false;
      }

      const tagName = element.tagName.toLowerCase();
      
      if (tagName === 'select') {
        // Handle dropdown
        const options = Array.from(element.options);
        const matchingOption = options.find(opt => 
          opt.text.toLowerCase().includes(value.toLowerCase()) ||
          opt.value.toLowerCase().includes(value.toLowerCase()) ||
          value.toLowerCase().includes(opt.text.toLowerCase())
        );
        
        if (matchingOption) {
          element.value = matchingOption.value;
          element.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
        return false;
      }
      
      if (tagName === 'input') {
        const inputType = element.type?.toLowerCase();
        
        if (inputType === 'radio' || inputType === 'checkbox') {
          // Handle radio/checkbox
          const label = element.closest('label')?.textContent || element.value || '';
          if (label.toLowerCase().includes(value.toLowerCase()) || value.toLowerCase().includes(label.toLowerCase())) {
            element.click();
            return true;
          }
          return false;
        }
        
        if (inputType === 'file') {
          return false; // Handled separately
        }
      }
      
      // Handle text input, textarea, or contenteditable
      if (element.isContentEditable) {
        element.innerHTML = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        return true;
      }
      
      // Standard input/textarea
      element.focus();
      element.value = value;
      
      // Dispatch events to trigger React/Vue/Angular change detection
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
      element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
      
      // For React controlled components
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set;
      const nativeTextareaValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;
      
      if (tagName === 'input' && nativeInputValueSetter) {
        nativeInputValueSetter.call(element, value);
        element.dispatchEvent(new Event('input', { bubbles: true }));
      } else if (tagName === 'textarea' && nativeTextareaValueSetter) {
        nativeTextareaValueSetter.call(element, value);
        element.dispatchEvent(new Event('input', { bubbles: true }));
      }
      
      element.blur();
      
      return true;
      
    } catch (error) {
      console.error('[JobMatch AI] Error setting field value:', error);
      return false;
    }
  }

  // Add small delay helper
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  console.log('[JobMatch AI] Content script loaded');
})();
