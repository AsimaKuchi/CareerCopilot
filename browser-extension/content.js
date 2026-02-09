// JobMatch AI - Content Script
// Injected into job application pages to handle auto-filling

(function() {
  'use strict';

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'AUTOFILL') {
      handleAutoFill(message.data).then(sendResponse);
      return true; // Keep channel open for async response
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
      
      // Fill custom questions
      await fillCustomQuestions(data, results);

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
