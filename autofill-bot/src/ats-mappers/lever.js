/**
 * Lever ATS Mapper
 * 
 * Handles auto-filling for Lever job application forms.
 * 
 * Lever form structure:
 * - Uses input[name='name'], input[name='email'], input[name='phone']
 * - Often has combined "Full Name" field instead of first/last
 * - Resume is input[type='file']
 * - Cover letter is usually a textarea
 * - Custom questions use label-based matching
 */

const { BaseMapper } = require('./base');
const { logFilledField, logSkippedField, logError } = require('../utils/reporter');

class LeverMapper extends BaseMapper {
  constructor() {
    super('Lever');
    
    // Lever-specific selectors
    this.selectors = {
      // Basic info - Lever often uses "name" for full name
      fullName: [
        'input[name="name"]',
        'input[name="fullName"]',
        'input[name="full_name"]',
        'input[id*="name"]:not([id*="first"]):not([id*="last"])',
        'input[placeholder*="full name" i]',
        'input[placeholder*="your name" i]',
      ],
      firstName: [
        'input[name="first_name"]',
        'input[name="firstName"]',
        'input[id*="first"]',
      ],
      lastName: [
        'input[name="last_name"]',
        'input[name="lastName"]',
        'input[id*="last"]',
      ],
      email: [
        'input[name="email"]',
        'input[type="email"]',
        'input[id*="email"]',
        'input[placeholder*="email" i]',
      ],
      phone: [
        'input[name="phone"]',
        'input[type="tel"]',
        'input[id*="phone"]',
        'input[placeholder*="phone" i]',
      ],
      
      // Location
      location: [
        'input[name="location"]',
        'input[name="city"]',
        'input[id*="location"]',
        'input[placeholder*="location" i]',
        'input[placeholder*="city" i]',
      ],
      
      // Links
      linkedin: [
        'input[name*="linkedin" i]',
        'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]',
        'input[aria-label*="linkedin" i]',
      ],
      github: [
        'input[name*="github" i]',
        'input[id*="github" i]',
        'input[placeholder*="github" i]',
      ],
      portfolio: [
        'input[name*="portfolio" i]',
        'input[name*="website" i]',
        'input[id*="portfolio" i]',
        'input[id*="website" i]',
        'input[placeholder*="portfolio" i]',
        'input[placeholder*="website" i]',
      ],
      
      // Documents
      resume: [
        'input[type="file"][name*="resume" i]',
        'input[type="file"][id*="resume" i]',
        'input[type="file"][data-qa*="resume" i]',
        'input[type="file"]:not([name*="cover" i])',
      ],
      coverLetter: [
        'textarea[name*="cover" i]',
        'textarea[id*="cover" i]',
        'textarea[placeholder*="cover" i]',
        'textarea[aria-label*="cover" i]',
        'div[data-placeholder*="cover" i]', // Lever uses contenteditable divs sometimes
      ],
      
      // Current company/employer
      currentCompany: [
        'input[name*="company" i]',
        'input[name*="employer" i]',
        'input[id*="company" i]',
        'input[placeholder*="company" i]',
        'input[placeholder*="employer" i]',
      ],
      
      // Additional info textarea
      additionalInfo: [
        'textarea[name*="additional" i]',
        'textarea[id*="additional" i]',
        'textarea:not([name*="cover" i])',
      ],
    };
  }

  /**
   * Fill Lever application form
   */
  async fill(page, payload, documents, options = {}) {
    const profile = payload.profile;
    
    // Wait for form to be ready
    await page.waitForSelector('form', { timeout: options.timeout || 30000 });
    await page.waitForTimeout(1000);

    // ═══════════════════════════════════════════════════════════
    // BASIC INFO
    // ═══════════════════════════════════════════════════════════
    
    // Check if there's a full name field vs first/last
    const hasFullName = await this.hasSelector(page, this.selectors.fullName);
    const hasFirstName = await this.hasSelector(page, this.selectors.firstName);
    
    if (hasFullName && !hasFirstName) {
      // Use full name field
      await this.trySelectors(page, this.selectors.fullName, profile.full_name, 'Full Name');
    } else {
      // Use first/last name fields
      await this.trySelectors(page, this.selectors.firstName, profile.first_name, 'First Name');
      await this.trySelectors(page, this.selectors.lastName, profile.last_name, 'Last Name');
    }
    
    // Email
    await this.trySelectors(page, this.selectors.email, profile.email, 'Email');
    
    // Phone
    await this.trySelectors(page, this.selectors.phone, profile.phone_formatted || profile.phone, 'Phone');

    // ═══════════════════════════════════════════════════════════
    // LOCATION
    // ═══════════════════════════════════════════════════════════
    
    // Lever often has a single location field
    const locationValue = [profile.city, profile.state, profile.country_full]
      .filter(Boolean)
      .join(', ');
    await this.trySelectors(page, this.selectors.location, locationValue || profile.city, 'Location');

    // ═══════════════════════════════════════════════════════════
    // LINKS
    // ═══════════════════════════════════════════════════════════
    
    // LinkedIn
    await this.trySelectors(page, this.selectors.linkedin, profile.linkedin_url, 'LinkedIn');
    
    // GitHub
    await this.trySelectors(page, this.selectors.github, profile.github_url, 'GitHub');
    
    // Portfolio
    await this.trySelectors(page, this.selectors.portfolio, profile.portfolio_url || profile.website_url, 'Portfolio');

    // ═══════════════════════════════════════════════════════════
    // PROFESSIONAL INFO
    // ═══════════════════════════════════════════════════════════
    
    // Current Company
    await this.trySelectors(page, this.selectors.currentCompany, profile.current_company, 'Current Company');

    // ═══════════════════════════════════════════════════════════
    // DOCUMENTS
    // ═══════════════════════════════════════════════════════════
    
    // Resume Upload
    if (documents.resume.type === 'file' && documents.resume.filePath) {
      await this.tryUpload(page, this.selectors.resume, documents.resume.filePath, 'Resume');
    }
    
    // Cover Letter (Lever usually uses textarea)
    if (documents.coverLetter.text) {
      const filled = await this.trySelectors(page, this.selectors.coverLetter, documents.coverLetter.text, 'Cover Letter', true);
      
      // If standard selectors didn't work, try contenteditable div
      if (!filled) {
        await this.tryContentEditable(page, 'cover', documents.coverLetter.text, 'Cover Letter');
      }
    }

    // ═══════════════════════════════════════════════════════════
    // CUSTOM QUESTIONS
    // ═══════════════════════════════════════════════════════════
    
    await this.fillCustomQuestions(page, payload, options);

    return this.getResults();
  }

  /**
   * Check if any selector exists
   */
  async hasSelector(page, selectors) {
    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) return true;
      } catch (e) {
        continue;
      }
    }
    return false;
  }

  /**
   * Try multiple selectors until one works
   */
  async trySelectors(page, selectors, value, label, isTextarea = false) {
    if (!value) {
      this.skipped.push(logSkippedField(label, 'No value available', null));
      return false;
    }

    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const tagName = await element.evaluate(el => el.tagName.toLowerCase());
          
          if (tagName === 'input' || tagName === 'textarea') {
            // Check if visible
            const isVisible = await element.isVisible();
            if (!isVisible) continue;
            
            await element.click();
            await element.fill('');
            await element.fill(String(value));
            this.filled.push(logFilledField(label, isTextarea ? value.substring(0, 50) + '...' : value, selector));
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }

    this.skipped.push(logSkippedField(label, 'No matching element found', selectors[0]));
    return false;
  }

  /**
   * Try to fill a contenteditable div (Lever uses these sometimes)
   */
  async tryContentEditable(page, labelHint, value, label) {
    try {
      const editables = await page.$$('[contenteditable="true"]');
      
      for (const editable of editables) {
        const placeholder = await editable.getAttribute('data-placeholder') || '';
        const ariaLabel = await editable.getAttribute('aria-label') || '';
        
        if (placeholder.toLowerCase().includes(labelHint) || ariaLabel.toLowerCase().includes(labelHint)) {
          await editable.click();
          await editable.fill(String(value));
          this.filled.push(logFilledField(label, value.substring(0, 50) + '...', 'contenteditable'));
          return true;
        }
      }
    } catch (e) {
      // Ignore
    }
    
    return false;
  }

  /**
   * Try to upload a file
   */
  async tryUpload(page, selectors, filePath, label) {
    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const type = await element.getAttribute('type');
          if (type === 'file') {
            await element.setInputFiles(filePath);
            this.filled.push(logFilledField(label, filePath, selector));
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }

    this.skipped.push(logSkippedField(label, 'No file input found', selectors[0]));
    return false;
  }

  /**
   * Fill custom questions using label matching
   */
  async fillCustomQuestions(page, payload, options) {
    const profile = payload.profile;
    
    // Sensitive fields we should skip
    const sensitivePatterns = [
      'salary', 'compensation', 'pay',
      'authorization', 'authorized', 'legally',
      'sponsorship', 'visa', 'work permit',
      'relocate', 'relocation',
      'notice', 'start date', 'availability',
      'how did you hear', 'referral', 'source',
    ];

    try {
      // Lever uses data-qa attributes for question containers
      const containers = await page.$$('[data-qa="question"], .question, .field-wrapper, [class*="question"]');
      
      for (const container of containers) {
        try {
          const labelElement = await container.$('label, .label, [data-qa="label"]');
          if (!labelElement) continue;
          
          const labelText = await labelElement.textContent();
          const normalizedLabel = labelText.toLowerCase().trim();
          
          // Skip sensitive fields
          if (options.skipSensitive) {
            const isSensitive = sensitivePatterns.some(p => normalizedLabel.includes(p));
            if (isSensitive) {
              this.skipped.push(logSkippedField(labelText.trim(), 'Sensitive field - requires confirmation', null));
              continue;
            }
          }
          
          const input = await container.$('input:not([type="hidden"]):not([type="file"]), textarea, select');
          if (!input) continue;
          
          const tagName = await input.evaluate(el => el.tagName.toLowerCase());
          const inputType = await input.getAttribute('type');
          
          // Match and fill
          let value = null;
          
          if (normalizedLabel.includes('experience') && normalizedLabel.includes('year')) {
            value = profile.experience_years;
          } else if (normalizedLabel.includes('company') || normalizedLabel.includes('employer')) {
            value = profile.current_company;
          } else if (normalizedLabel.includes('linkedin')) {
            value = profile.linkedin_url;
          } else if (normalizedLabel.includes('github')) {
            value = profile.github_url;
          } else if (normalizedLabel.includes('portfolio') || normalizedLabel.includes('website')) {
            value = profile.portfolio_url || profile.website_url;
          } else if (normalizedLabel.includes('education') || normalizedLabel.includes('degree')) {
            value = profile.education;
          }
          
          if (value && inputType !== 'radio' && inputType !== 'checkbox') {
            if (tagName === 'select') {
              await this.fillSelectByElement(page, input, value, labelText.trim());
            } else {
              await input.fill(String(value));
              this.filled.push(logFilledField(labelText.trim(), value, 'custom'));
            }
          }
          
        } catch (e) {
          // Skip this container
        }
      }
    } catch (e) {
      this.errors.push(logError('custom_questions', e.message, null));
    }
  }

  /**
   * Fill a select element by element handle
   */
  async fillSelectByElement(page, element, value, label) {
    try {
      const options = await element.$$eval('option', opts =>
        opts.map(o => ({ value: o.value, text: o.textContent.trim() }))
      );
      
      const normalizedValue = String(value).toLowerCase();
      const matchedOption = options.find(o =>
        o.text.toLowerCase().includes(normalizedValue) ||
        o.value.toLowerCase().includes(normalizedValue)
      );
      
      if (matchedOption) {
        await element.selectOption(matchedOption.value);
        this.filled.push(logFilledField(label, matchedOption.text, 'select'));
        return true;
      }
    } catch (e) {
      this.errors.push(logError('fill_select', e.message, label));
    }
    return false;
  }
}

module.exports = { LeverMapper };
