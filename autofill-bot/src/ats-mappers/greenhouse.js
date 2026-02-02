/**
 * Greenhouse ATS Mapper
 * 
 * Handles auto-filling for Greenhouse job application forms.
 * 
 * Greenhouse form structure:
 * - Uses input[name='first_name'], input[name='last_name'], etc.
 * - Resume is usually input[type='file'] near "Resume/CV" label
 * - Cover letter can be textarea or file upload
 * - Custom questions in fieldsets with label-based matching
 */

const { BaseMapper } = require('./base');
const { logFilledField, logSkippedField, logError } = require('../utils/reporter');

class GreenhouseMapper extends BaseMapper {
  constructor() {
    super('Greenhouse');
    
    // Greenhouse-specific selectors
    this.selectors = {
      // Basic info
      firstName: [
        'input[name="first_name"]',
        'input[name="firstName"]',
        'input[id*="first_name"]',
        'input[autocomplete="given-name"]',
      ],
      lastName: [
        'input[name="last_name"]',
        'input[name="lastName"]',
        'input[id*="last_name"]',
        'input[autocomplete="family-name"]',
      ],
      email: [
        'input[name="email"]',
        'input[type="email"]',
        'input[id*="email"]',
        'input[autocomplete="email"]',
      ],
      phone: [
        'input[name="phone"]',
        'input[type="tel"]',
        'input[id*="phone"]',
        'input[autocomplete="tel"]',
      ],
      
      // Location
      city: [
        'input[name="city"]',
        'input[id*="city"]',
        'input[autocomplete="address-level2"]',
      ],
      state: [
        'input[name="state"]',
        'input[name="province"]',
        'input[id*="state"]',
        'input[id*="province"]',
        'select[name="state"]',
        'select[id*="state"]',
      ],
      country: [
        'select[name="country"]',
        'input[name="country"]',
        'select[id*="country"]',
      ],
      
      // Links
      linkedin: [
        'input[name*="linkedin" i]',
        'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]',
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
      ],
      
      // Documents
      resume: [
        'input[type="file"][name*="resume" i]',
        'input[type="file"][id*="resume" i]',
        'input[type="file"][accept*="pdf"]',
        'input[type="file"]:first-of-type',
      ],
      coverLetter: [
        'input[type="file"][name*="cover" i]',
        'input[type="file"][id*="cover" i]',
        'textarea[name*="cover" i]',
        'textarea[id*="cover" i]',
      ],
      coverLetterText: [
        'textarea[name*="cover" i]',
        'textarea[id*="cover" i]',
        'textarea[placeholder*="cover" i]',
      ],
      
      // Submit button (for reference, we don't click it)
      submit: [
        'button[type="submit"]',
        'input[type="submit"]',
        '#submit_app',
        'button:has-text("Submit")',
      ],
    };
  }

  /**
   * Fill Greenhouse application form
   */
  async fill(page, payload, documents, options = {}) {
    const profile = payload.profile;
    
    // Wait for form to be ready
    await page.waitForSelector('form', { timeout: options.timeout || 30000 });
    await page.waitForTimeout(1000);

    // ═══════════════════════════════════════════════════════════
    // BASIC INFO
    // ═══════════════════════════════════════════════════════════
    
    // First Name
    await this.trySelectors(page, this.selectors.firstName, profile.first_name, 'First Name');
    
    // Last Name
    await this.trySelectors(page, this.selectors.lastName, profile.last_name, 'Last Name');
    
    // Email
    await this.trySelectors(page, this.selectors.email, profile.email, 'Email');
    
    // Phone
    await this.trySelectors(page, this.selectors.phone, profile.phone_formatted || profile.phone, 'Phone');

    // ═══════════════════════════════════════════════════════════
    // LOCATION
    // ═══════════════════════════════════════════════════════════
    
    // City
    await this.trySelectors(page, this.selectors.city, profile.city, 'City');
    
    // State/Province
    await this.trySelectors(page, this.selectors.state, profile.state, 'State/Province');
    
    // Country
    await this.trySelectorsSelect(page, this.selectors.country, profile.country_full || profile.country, 'Country');

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
    // PROFESSIONAL INFO (Label-based matching)
    // ═══════════════════════════════════════════════════════════
    
    // Current Company
    await this.fillByLabel(page, payload, 'current_company', options);
    
    // Years of Experience
    await this.fillByLabel(page, payload, 'years_experience', options);
    
    // Education
    await this.fillByLabel(page, payload, 'education', options);

    // ═══════════════════════════════════════════════════════════
    // DOCUMENTS
    // ═══════════════════════════════════════════════════════════
    
    // Resume Upload
    if (documents.resume.type === 'file' && documents.resume.filePath) {
      await this.tryUpload(page, this.selectors.resume, documents.resume.filePath, 'Resume');
    } else if (documents.resume.type === 'text' && documents.resume.text) {
      // Try to find a textarea for resume
      this.skipped.push(logSkippedField('Resume', 'File input only - no textarea available', null));
    }
    
    // Cover Letter
    if (documents.coverLetter.type === 'file' && documents.coverLetter.filePath) {
      // Try file upload first
      const uploaded = await this.tryUpload(page, this.selectors.coverLetter, documents.coverLetter.filePath, 'Cover Letter');
      if (!uploaded && documents.coverLetter.text) {
        // Fall back to textarea
        await this.trySelectors(page, this.selectors.coverLetterText, documents.coverLetter.text, 'Cover Letter', true);
      }
    } else if (documents.coverLetter.text) {
      // Use textarea
      await this.trySelectors(page, this.selectors.coverLetterText, documents.coverLetter.text, 'Cover Letter', true);
    }

    // ═══════════════════════════════════════════════════════════
    // CUSTOM QUESTIONS (Skip sensitive)
    // ═══════════════════════════════════════════════════════════
    
    await this.fillCustomQuestions(page, payload, options);

    return this.getResults();
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
            await element.click();
            await element.fill('');
            await element.fill(String(value));
            this.filled.push(logFilledField(label, value, selector));
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
   * Try selectors for select elements
   */
  async trySelectorsSelect(page, selectors, value, label) {
    if (!value) {
      this.skipped.push(logSkippedField(label, 'No value available', null));
      return false;
    }

    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const tagName = await element.evaluate(el => el.tagName.toLowerCase());
          
          if (tagName === 'select') {
            // Get options and try to match
            const options = await page.$$eval(`${selector} option`, opts =>
              opts.map(o => ({ value: o.value, text: o.textContent.trim() }))
            );
            
            // Find matching option
            const normalizedValue = String(value).toLowerCase();
            const matchedOption = options.find(o => 
              o.text.toLowerCase().includes(normalizedValue) ||
              o.value.toLowerCase().includes(normalizedValue) ||
              normalizedValue.includes(o.text.toLowerCase())
            );
            
            if (matchedOption) {
              await page.selectOption(selector, matchedOption.value);
              this.filled.push(logFilledField(label, matchedOption.text, selector));
              return true;
            }
          } else if (tagName === 'input') {
            // It's an input, not a select
            await element.click();
            await element.fill(String(value));
            this.filled.push(logFilledField(label, value, selector));
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
      // Find all fieldsets or question containers
      const containers = await page.$$('fieldset, .field, .question, [class*="question"], [class*="field"]');
      
      for (const container of containers) {
        try {
          // Get label text
          const labelElement = await container.$('label, legend, .label');
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
          
          // Try to fill based on label
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
          }
          
          if (value) {
            if (tagName === 'select') {
              await this.fillSelect(page, input, value, labelText.trim());
            } else if (inputType !== 'radio' && inputType !== 'checkbox') {
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
}

module.exports = { GreenhouseMapper };
