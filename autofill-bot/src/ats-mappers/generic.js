/**
 * Generic ATS Mapper
 * 
 * Fallback mapper for unknown ATS systems.
 * Uses label-based heuristics to fill forms.
 */

const { BaseMapper } = require('./base');
const { matchLabelToField, getValueFromPath, formatValueForInput, FIELD_MAPPINGS } = require('../utils/field-matcher');
const { logFilledField, logSkippedField, logError } = require('../utils/reporter');

class GenericMapper extends BaseMapper {
  constructor() {
    super('Generic');
  }

  /**
   * Fill form using generic label matching
   */
  async fill(page, payload, documents, options = {}) {
    const profile = payload.profile;
    
    // Wait for form
    try {
      await page.waitForSelector('form', { timeout: options.timeout || 30000 });
    } catch (e) {
      // No form found, try to fill anyway
    }
    
    await page.waitForTimeout(1500);

    // ═══════════════════════════════════════════════════════════
    // PHASE 1: Scan all labels and match to profile fields
    // ═══════════════════════════════════════════════════════════
    
    console.log('  Scanning page for fillable fields...');
    
    const labels = await page.$$('label');
    const processedInputIds = new Set();
    
    for (const label of labels) {
      try {
        const isVisible = await label.isVisible();
        if (!isVisible) continue;
        
        const labelText = await label.textContent();
        if (!labelText || labelText.trim().length < 2) continue;
        
        // Match label to profile field
        const match = matchLabelToField(labelText);
        if (!match) continue;
        
        // Skip sensitive fields
        if (match.mapping.sensitive && options.skipSensitive) {
          this.skipped.push(logSkippedField(labelText.trim(), 'Sensitive field - requires confirmation', null));
          continue;
        }
        
        // Find associated input
        const input = await this.findInputForLabel(page, label);
        if (!input) continue;
        
        // Check if already processed
        const inputId = await input.evaluate(el => el.id || el.name || Math.random().toString());
        if (processedInputIds.has(inputId)) continue;
        processedInputIds.add(inputId);
        
        // Get value from payload
        let value = getValueFromPath(payload, match.mapping.profilePath);
        if (!value && match.mapping.altPath) {
          value = getValueFromPath(payload, match.mapping.altPath);
        }
        
        if (!value) {
          this.skipped.push(logSkippedField(match.fieldKey, 'No value in profile', labelText.trim()));
          continue;
        }
        
        // Fill the field
        const filled = await this.fillField(input, value, labelText.trim());
        if (filled) {
          this.filled.push(logFilledField(labelText.trim(), value, match.fieldKey));
        }
        
      } catch (e) {
        // Continue with next label
      }
    }

    // ═══════════════════════════════════════════════════════════
    // PHASE 2: Try common selectors for basic fields
    // ═══════════════════════════════════════════════════════════
    
    console.log('  Trying common selectors...');
    
    await this.tryCommonSelectors(page, profile);

    // ═══════════════════════════════════════════════════════════
    // PHASE 3: Handle documents
    // ═══════════════════════════════════════════════════════════
    
    console.log('  Handling documents...');
    
    // Resume
    if (documents.resume.type === 'file' && documents.resume.filePath) {
      await this.tryFileUpload(page, documents.resume.filePath, ['resume', 'cv'], 'Resume');
    } else if (documents.resume.text) {
      await this.tryTextarea(page, documents.resume.text, ['resume', 'cv'], 'Resume');
    }
    
    // Cover Letter
    if (documents.coverLetter.text) {
      const uploadedCL = documents.coverLetter.filePath 
        ? await this.tryFileUpload(page, documents.coverLetter.filePath, ['cover'], 'Cover Letter')
        : false;
      
      if (!uploadedCL) {
        await this.tryTextarea(page, documents.coverLetter.text, ['cover'], 'Cover Letter');
      }
    }

    return this.getResults();
  }

  /**
   * Find input element associated with a label
   */
  async findInputForLabel(page, label) {
    try {
      // Try for attribute
      const forAttr = await label.getAttribute('for');
      if (forAttr) {
        const input = await page.$(`#${forAttr}`);
        if (input) return input;
      }
      
      // Try child input
      const childInput = await label.$('input, textarea, select');
      if (childInput) return childInput;
      
      // Try next sibling
      const sibling = await label.evaluateHandle(el => {
        const next = el.nextElementSibling;
        if (next && ['INPUT', 'TEXTAREA', 'SELECT'].includes(next.tagName)) {
          return next;
        }
        // Try parent's next child
        const parent = el.parentElement;
        if (parent) {
          const inputs = parent.querySelectorAll('input, textarea, select');
          if (inputs.length > 0) return inputs[0];
        }
        return null;
      });
      
      const tagName = await sibling.evaluate(el => el?.tagName).catch(() => null);
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tagName)) {
        return sibling;
      }
      
    } catch (e) {
      // Ignore
    }
    
    return null;
  }

  /**
   * Fill a field based on its type
   */
  async fillField(element, value, label) {
    try {
      const tagName = await element.evaluate(el => el.tagName.toLowerCase());
      const inputType = await element.getAttribute('type');
      
      // Skip certain types
      if (['file', 'hidden', 'submit', 'button', 'image'].includes(inputType)) {
        return false;
      }
      
      // Check if already has value
      const currentValue = await element.inputValue().catch(() => '');
      if (currentValue && currentValue.length > 0) {
        return false;
      }
      
      // Check visibility
      const isVisible = await element.isVisible();
      if (!isVisible) return false;
      
      if (tagName === 'select') {
        return await this.fillSelect(element, value, label);
      } else if (inputType === 'radio' || inputType === 'checkbox') {
        return await this.fillCheckboxRadio(element, value);
      } else {
        await element.click();
        await element.fill(String(value));
        return true;
      }
    } catch (e) {
      this.errors.push(logError('fill_field', e.message, label));
      return false;
    }
  }

  /**
   * Fill a select element
   */
  async fillSelect(element, value, label) {
    try {
      const options = await element.evaluate(el => 
        Array.from(el.options).map(o => ({ value: o.value, text: o.textContent.trim() }))
      );
      
      const normalizedValue = String(value).toLowerCase();
      const matchedOption = options.find(o =>
        o.text.toLowerCase().includes(normalizedValue) ||
        o.value.toLowerCase().includes(normalizedValue) ||
        normalizedValue.includes(o.text.toLowerCase())
      );
      
      if (matchedOption) {
        await element.selectOption(matchedOption.value);
        return true;
      }
    } catch (e) {
      this.errors.push(logError('fill_select', e.message, label));
    }
    return false;
  }

  /**
   * Fill checkbox or radio button
   */
  async fillCheckboxRadio(element, value) {
    try {
      const stringValue = String(value).toLowerCase();
      const shouldCheck = ['yes', 'true', '1', 'y'].includes(stringValue);
      
      const isChecked = await element.isChecked();
      if (shouldCheck && !isChecked) {
        await element.check();
        return true;
      } else if (!shouldCheck && isChecked) {
        await element.uncheck();
        return true;
      }
    } catch (e) {
      // Ignore checkbox errors
    }
    return false;
  }

  /**
   * Try common selectors for basic fields
   */
  async tryCommonSelectors(page, profile) {
    const commonFields = [
      // Name fields
      { selectors: ['input[name="first_name"]', 'input[name="firstName"]', 'input[autocomplete="given-name"]'], value: profile.first_name, label: 'First Name' },
      { selectors: ['input[name="last_name"]', 'input[name="lastName"]', 'input[autocomplete="family-name"]'], value: profile.last_name, label: 'Last Name' },
      { selectors: ['input[name="name"]', 'input[name="fullName"]'], value: profile.full_name, label: 'Full Name' },
      
      // Contact
      { selectors: ['input[type="email"]', 'input[name="email"]', 'input[autocomplete="email"]'], value: profile.email, label: 'Email' },
      { selectors: ['input[type="tel"]', 'input[name="phone"]', 'input[autocomplete="tel"]'], value: profile.phone_formatted || profile.phone, label: 'Phone' },
      
      // Location
      { selectors: ['input[name="city"]', 'input[autocomplete="address-level2"]'], value: profile.city, label: 'City' },
      { selectors: ['input[name="state"]', 'input[name="province"]', 'input[autocomplete="address-level1"]'], value: profile.state, label: 'State' },
      
      // Links
      { selectors: ['input[name*="linkedin" i]', 'input[placeholder*="linkedin" i]'], value: profile.linkedin_url, label: 'LinkedIn' },
      { selectors: ['input[name*="github" i]', 'input[placeholder*="github" i]'], value: profile.github_url, label: 'GitHub' },
      { selectors: ['input[name*="portfolio" i]', 'input[name*="website" i]'], value: profile.portfolio_url || profile.website_url, label: 'Portfolio' },
    ];

    for (const field of commonFields) {
      if (!field.value) continue;
      
      for (const selector of field.selectors) {
        try {
          const element = await page.$(selector);
          if (element) {
            const isVisible = await element.isVisible();
            const currentValue = await element.inputValue().catch(() => '');
            
            if (isVisible && !currentValue) {
              await element.click();
              await element.fill(String(field.value));
              this.filled.push(logFilledField(field.label, field.value, selector));
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }
    }
  }

  /**
   * Try to upload a file
   */
  async tryFileUpload(page, filePath, labelHints, fieldName) {
    // Build selectors from hints
    const selectors = [];
    for (const hint of labelHints) {
      selectors.push(
        `input[type="file"][name*="${hint}" i]`,
        `input[type="file"][id*="${hint}" i]`,
        `input[type="file"][accept*="pdf"]`
      );
    }
    
    for (const selector of selectors) {
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

    // Try clicking upload buttons
    for (const hint of labelHints) {
      try {
        const button = await page.$(`button:has-text("${hint}"), [role="button"]:has-text("${hint}")`);
        if (button) {
          const [fileChooser] = await Promise.all([
            page.waitForEvent('filechooser', { timeout: 3000 }),
            button.click(),
          ]).catch(() => [null]);
          
          if (fileChooser) {
            await fileChooser.setFiles(filePath);
            this.filled.push(logFilledField(fieldName, filePath, 'filechooser'));
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
   * Try to fill a textarea with text
   */
  async tryTextarea(page, text, labelHints, fieldName) {
    // Build selectors from hints
    const selectors = [];
    for (const hint of labelHints) {
      selectors.push(
        `textarea[name*="${hint}" i]`,
        `textarea[id*="${hint}" i]`,
        `textarea[placeholder*="${hint}" i]`,
        `textarea[aria-label*="${hint}" i]`
      );
    }
    
    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          const isVisible = await element.isVisible();
          if (isVisible) {
            await element.click();
            await element.fill(text);
            this.filled.push(logFilledField(fieldName, text.substring(0, 50) + '...', selector));
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }

    return false;
  }
}

module.exports = { GenericMapper };
