/**
 * Ashby ATS Mapper
 * 
 * Handles auto-filling for Ashby job application forms.
 * 
 * Ashby form structure:
 * - Forms are MULTI-STEP - need to detect and click "Next" buttons
 * - Fields have accessible labels - use getByLabel
 * - File upload inputs may be hidden
 * - Uses data-testid attributes for form elements
 */

const { BaseMapper } = require('./base');
const { logFilledField, logSkippedField, logError } = require('../utils/reporter');

class AshbyMapper extends BaseMapper {
  constructor() {
    super('Ashby');
    
    // Ashby-specific selectors
    this.selectors = {
      // Basic info
      firstName: [
        'input[name="firstName"]',
        'input[name="first_name"]',
        'input[data-testid*="first" i]',
        'input[aria-label*="first name" i]',
      ],
      lastName: [
        'input[name="lastName"]',
        'input[name="last_name"]',
        'input[data-testid*="last" i]',
        'input[aria-label*="last name" i]',
      ],
      email: [
        'input[name="email"]',
        'input[type="email"]',
        'input[data-testid*="email" i]',
        'input[aria-label*="email" i]',
      ],
      phone: [
        'input[name="phone"]',
        'input[type="tel"]',
        'input[data-testid*="phone" i]',
        'input[aria-label*="phone" i]',
      ],
      
      // Location
      city: [
        'input[name="city"]',
        'input[data-testid*="city" i]',
        'input[aria-label*="city" i]',
      ],
      state: [
        'input[name="state"]',
        'input[name="province"]',
        'select[name="state"]',
        'input[data-testid*="state" i]',
        'input[aria-label*="state" i]',
        'input[aria-label*="province" i]',
      ],
      country: [
        'select[name="country"]',
        'input[name="country"]',
        'select[data-testid*="country" i]',
        'input[aria-label*="country" i]',
      ],
      
      // Links
      linkedin: [
        'input[name*="linkedin" i]',
        'input[data-testid*="linkedin" i]',
        'input[aria-label*="linkedin" i]',
      ],
      github: [
        'input[name*="github" i]',
        'input[data-testid*="github" i]',
        'input[aria-label*="github" i]',
      ],
      portfolio: [
        'input[name*="portfolio" i]',
        'input[name*="website" i]',
        'input[data-testid*="portfolio" i]',
        'input[data-testid*="website" i]',
        'input[aria-label*="portfolio" i]',
        'input[aria-label*="website" i]',
      ],
      
      // Documents - Ashby often hides file inputs
      resume: [
        'input[type="file"][name*="resume" i]',
        'input[type="file"][data-testid*="resume" i]',
        'input[type="file"][accept*=".pdf"]',
        'input[type="file"]',
      ],
      coverLetter: [
        'textarea[name*="cover" i]',
        'textarea[data-testid*="cover" i]',
        'textarea[aria-label*="cover" i]',
        'input[type="file"][name*="cover" i]',
      ],
      
      // Navigation buttons
      nextButton: [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'button[data-testid*="next" i]',
        'button[type="button"]:has-text("Next")',
      ],
      submitButton: [
        'button:has-text("Submit")',
        'button[type="submit"]',
        'button[data-testid*="submit" i]',
      ],
    };
  }

  /**
   * Fill Ashby application form
   */
  async fill(page, payload, documents, options = {}) {
    const profile = payload.profile;
    
    // Wait for form to be ready
    await page.waitForSelector('form', { timeout: options.timeout || 30000 });
    await page.waitForTimeout(1500); // Ashby forms can be slow to hydrate

    // Track which step we're on
    let currentStep = 1;
    const maxSteps = 5; // Safety limit
    
    while (currentStep <= maxSteps) {
      console.log(`  Processing step ${currentStep}...`);
      
      // Fill all visible fields on current step
      await this.fillCurrentStep(page, payload, documents, options);
      
      // Check if there's a Next button
      const hasNext = await this.clickNextIfAvailable(page);
      
      if (!hasNext) {
        // No more steps
        break;
      }
      
      currentStep++;
      await page.waitForTimeout(1500); // Wait for next step to load
    }

    return this.getResults();
  }

  /**
   * Fill all visible fields on the current step
   */
  async fillCurrentStep(page, payload, documents, options) {
    const profile = payload.profile;

    // ═══════════════════════════════════════════════════════════
    // BASIC INFO (using getByLabel for accessibility)
    // ═══════════════════════════════════════════════════════════
    
    // First Name
    await this.fillByLabelAshby(page, ['First name', 'First Name', 'Given name'], profile.first_name, 'First Name');
    
    // Last Name
    await this.fillByLabelAshby(page, ['Last name', 'Last Name', 'Family name', 'Surname'], profile.last_name, 'Last Name');
    
    // Email
    await this.fillByLabelAshby(page, ['Email', 'Email address', 'E-mail'], profile.email, 'Email');
    
    // Phone
    await this.fillByLabelAshby(page, ['Phone', 'Phone number', 'Mobile', 'Telephone'], profile.phone_formatted || profile.phone, 'Phone');

    // Also try selector-based approach
    await this.trySelectors(page, this.selectors.firstName, profile.first_name, 'First Name (selector)');
    await this.trySelectors(page, this.selectors.lastName, profile.last_name, 'Last Name (selector)');
    await this.trySelectors(page, this.selectors.email, profile.email, 'Email (selector)');
    await this.trySelectors(page, this.selectors.phone, profile.phone_formatted || profile.phone, 'Phone (selector)');

    // ═══════════════════════════════════════════════════════════
    // LOCATION
    // ═══════════════════════════════════════════════════════════
    
    await this.fillByLabelAshby(page, ['City', 'Location'], profile.city, 'City');
    await this.fillByLabelAshby(page, ['State', 'Province', 'Region'], profile.state, 'State/Province');
    await this.fillByLabelAshby(page, ['Country'], profile.country_full || profile.country, 'Country');

    // ═══════════════════════════════════════════════════════════
    // LINKS
    // ═══════════════════════════════════════════════════════════
    
    await this.fillByLabelAshby(page, ['LinkedIn', 'LinkedIn URL', 'LinkedIn profile'], profile.linkedin_url, 'LinkedIn');
    await this.fillByLabelAshby(page, ['GitHub', 'GitHub URL', 'GitHub profile'], profile.github_url, 'GitHub');
    await this.fillByLabelAshby(page, ['Portfolio', 'Website', 'Personal website'], profile.portfolio_url || profile.website_url, 'Portfolio');

    // ═══════════════════════════════════════════════════════════
    // PROFESSIONAL INFO
    // ═══════════════════════════════════════════════════════════
    
    await this.fillByLabelAshby(page, ['Current company', 'Company', 'Employer'], profile.current_company, 'Current Company');
    await this.fillByLabelAshby(page, ['Years of experience', 'Experience'], profile.experience_years, 'Years of Experience');

    // ═══════════════════════════════════════════════════════════
    // DOCUMENTS
    // ═══════════════════════════════════════════════════════════
    
    // Resume Upload
    if (documents.resume.type === 'file' && documents.resume.filePath) {
      await this.tryUploadAshby(page, documents.resume.filePath, ['Resume', 'CV', 'Resume/CV'], 'Resume');
    }
    
    // Cover Letter
    if (documents.coverLetter.text) {
      await this.fillByLabelAshby(page, ['Cover letter', 'Cover Letter', 'Covering letter'], documents.coverLetter.text, 'Cover Letter');
    }

    // ═══════════════════════════════════════════════════════════
    // CUSTOM QUESTIONS (Label scanning)
    // ═══════════════════════════════════════════════════════════
    
    await this.fillCustomQuestions(page, payload, options);
  }

  /**
   * Fill field using Playwright's getByLabel (accessibility-first)
   */
  async fillByLabelAshby(page, labelTexts, value, fieldName) {
    if (!value) {
      return false;
    }

    for (const labelText of labelTexts) {
      try {
        const locator = page.getByLabel(labelText, { exact: false });
        const count = await locator.count();
        
        if (count > 0) {
          const element = locator.first();
          const isVisible = await element.isVisible();
          
          if (isVisible) {
            const tagName = await element.evaluate(el => el.tagName.toLowerCase());
            
            if (tagName === 'select') {
              // Handle select
              const options = await element.evaluate(el => 
                Array.from(el.options).map(o => ({ value: o.value, text: o.textContent.trim() }))
              );
              
              const normalizedValue = String(value).toLowerCase();
              const matchedOption = options.find(o =>
                o.text.toLowerCase().includes(normalizedValue) ||
                normalizedValue.includes(o.text.toLowerCase())
              );
              
              if (matchedOption) {
                await element.selectOption(matchedOption.value);
                this.filled.push(logFilledField(fieldName, matchedOption.text, `getByLabel("${labelText}")`));
                return true;
              }
            } else {
              // Handle input/textarea
              await element.click();
              await element.fill(String(value));
              this.filled.push(logFilledField(fieldName, value, `getByLabel("${labelText}")`));
              return true;
            }
          }
        }
      } catch (e) {
        continue;
      }
    }

    return false;
  }

  /**
   * Try multiple selectors until one works
   */
  async trySelectors(page, selectors, value, label) {
    if (!value) {
      return false;
    }

    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const isVisible = await element.isVisible();
          if (!isVisible) continue;
          
          const alreadyFilled = await element.inputValue().catch(() => '');
          if (alreadyFilled) continue; // Don't overwrite already filled fields
          
          await element.click();
          await element.fill(String(value));
          this.filled.push(logFilledField(label, value, selector));
          return true;
        }
      } catch (e) {
        continue;
      }
    }

    return false;
  }

  /**
   * Try to upload a file - Ashby often has hidden file inputs
   */
  async tryUploadAshby(page, filePath, labelTexts, fieldName) {
    // First, try to find file input by label
    for (const labelText of labelTexts) {
      try {
        // Click the label/button area to trigger file input
        const uploadButton = await page.$(`button:has-text("${labelText}"), [role="button"]:has-text("${labelText}"), label:has-text("${labelText}")`);
        
        if (uploadButton) {
          // Set up file chooser listener
          const [fileChooser] = await Promise.all([
            page.waitForEvent('filechooser', { timeout: 3000 }),
            uploadButton.click(),
          ]).catch(() => [null]);
          
          if (fileChooser) {
            await fileChooser.setFiles(filePath);
            this.filled.push(logFilledField(fieldName, filePath, `filechooser("${labelText}")`));
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }

    // Fallback: try direct file input
    for (const selector of this.selectors.resume) {
      try {
        const element = await page.$(selector);
        if (element) {
          await element.setInputFiles(filePath);
          this.filled.push(logFilledField(fieldName, filePath, selector));
          return true;
        }
      } catch (e) {
        continue;
      }
    }

    this.skipped.push(logSkippedField(fieldName, 'No file input found', null));
    return false;
  }

  /**
   * Click Next button if available
   */
  async clickNextIfAvailable(page) {
    for (const selector of this.selectors.nextButton) {
      try {
        const button = await page.$(selector);
        if (button) {
          const isVisible = await button.isVisible();
          const isEnabled = await button.isEnabled();
          
          if (isVisible && isEnabled) {
            // Make sure it's not the submit button
            const text = await button.textContent();
            if (text.toLowerCase().includes('submit')) {
              return false; // Don't click submit
            }
            
            await button.click();
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }
    
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
      // Find all visible labels
      const labels = await page.$$('label');
      
      for (const label of labels) {
        try {
          const isVisible = await label.isVisible();
          if (!isVisible) continue;
          
          const labelText = await label.textContent();
          const normalizedLabel = labelText.toLowerCase().trim();
          
          // Skip if already processed or empty
          if (!normalizedLabel || normalizedLabel.length < 3) continue;
          
          // Skip sensitive fields
          if (options.skipSensitive) {
            const isSensitive = sensitivePatterns.some(p => normalizedLabel.includes(p));
            if (isSensitive) {
              this.skipped.push(logSkippedField(labelText.trim(), 'Sensitive field - requires confirmation', null));
              continue;
            }
          }
          
          // Try to get associated input
          const forAttr = await label.getAttribute('for');
          let input = null;
          
          if (forAttr) {
            input = await page.$(`#${forAttr}`);
          }
          
          if (!input) {
            // Try sibling or child input
            input = await label.$('input, textarea, select');
            if (!input) {
              input = await label.evaluateHandle(el => el.nextElementSibling);
              const tagName = await input.evaluate(el => el?.tagName?.toLowerCase()).catch(() => null);
              if (!['input', 'textarea', 'select'].includes(tagName)) {
                input = null;
              }
            }
          }
          
          if (!input) continue;
          
          // Check if already has value
          const currentValue = await input.inputValue().catch(() => '');
          if (currentValue) continue;
          
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
          
          if (value) {
            const tagName = await input.evaluate(el => el.tagName.toLowerCase());
            const inputType = await input.getAttribute('type');
            
            if (inputType !== 'radio' && inputType !== 'checkbox' && inputType !== 'file') {
              await input.fill(String(value));
              this.filled.push(logFilledField(labelText.trim(), value, 'custom'));
            }
          }
          
        } catch (e) {
          // Skip this label
        }
      }
    } catch (e) {
      this.errors.push(logError('custom_questions', e.message, null));
    }
  }
}

module.exports = { AshbyMapper };
