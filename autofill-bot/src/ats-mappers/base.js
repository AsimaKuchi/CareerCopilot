/**
 * Base ATS Mapper
 * 
 * Provides common functionality for all ATS mappers.
 */

const { matchLabelToField, getValueFromPath, formatValueForInput, matchSelectOption, FIELD_MAPPINGS } = require('../utils/field-matcher');
const { logFilledField, logSkippedField, logError } = require('../utils/reporter');

class BaseMapper {
  constructor(name) {
    this.name = name;
    this.filled = [];
    this.skipped = [];
    this.errors = [];
  }

  /**
   * Main fill method - to be overridden by subclasses
   */
  async fill(page, payload, documents, options = {}) {
    throw new Error('fill() must be implemented by subclass');
  }

  /**
   * Try to fill an input field
   */
  async fillInput(page, selector, value, label = null) {
    if (!value) {
      this.skipped.push(logSkippedField(label || selector, 'No value available', selector));
      return false;
    }

    try {
      const element = await page.$(selector);
      if (!element) {
        this.skipped.push(logSkippedField(label || selector, 'Element not found', selector));
        return false;
      }

      // Clear existing value
      await element.click();
      await element.fill('');
      await element.fill(String(value));
      
      this.filled.push(logFilledField(label || selector, value, selector));
      return true;
    } catch (e) {
      this.errors.push(logError('fill_input', e.message, selector));
      return false;
    }
  }

  /**
   * Try to fill a textarea
   */
  async fillTextarea(page, selector, value, label = null) {
    if (!value) {
      this.skipped.push(logSkippedField(label || selector, 'No value available', selector));
      return false;
    }

    try {
      const element = await page.$(selector);
      if (!element) {
        this.skipped.push(logSkippedField(label || selector, 'Element not found', selector));
        return false;
      }

      await element.click();
      await element.fill('');
      await element.fill(String(value));
      
      this.filled.push(logFilledField(label || selector, value.substring(0, 50) + '...', selector));
      return true;
    } catch (e) {
      this.errors.push(logError('fill_textarea', e.message, selector));
      return false;
    }
  }

  /**
   * Try to select from dropdown
   */
  async fillSelect(page, selector, value, label = null) {
    if (!value) {
      this.skipped.push(logSkippedField(label || selector, 'No value available', selector));
      return false;
    }

    try {
      const element = await page.$(selector);
      if (!element) {
        this.skipped.push(logSkippedField(label || selector, 'Element not found', selector));
        return false;
      }

      // Get options
      const options = await page.$$eval(`${selector} option`, opts => 
        opts.map(o => ({ value: o.value, text: o.textContent.trim() }))
      );

      // Match option
      const matchedValue = matchSelectOption(options, value);
      if (!matchedValue) {
        this.skipped.push(logSkippedField(label || selector, `No matching option for "${value}"`, selector));
        return false;
      }

      await page.selectOption(selector, matchedValue);
      this.filled.push(logFilledField(label || selector, matchedValue, selector));
      return true;
    } catch (e) {
      this.errors.push(logError('fill_select', e.message, selector));
      return false;
    }
  }

  /**
   * Try to click a radio button
   */
  async clickRadio(page, selector, label = null) {
    try {
      const element = await page.$(selector);
      if (!element) {
        return false;
      }

      await element.click();
      this.filled.push(logFilledField(label || selector, 'clicked', selector));
      return true;
    } catch (e) {
      this.errors.push(logError('click_radio', e.message, selector));
      return false;
    }
  }

  /**
   * Try to upload a file
   */
  async uploadFile(page, selector, filePath, label = null) {
    if (!filePath) {
      this.skipped.push(logSkippedField(label || selector, 'No file available', selector));
      return false;
    }

    try {
      const element = await page.$(selector);
      if (!element) {
        this.skipped.push(logSkippedField(label || selector, 'File input not found', selector));
        return false;
      }

      await element.setInputFiles(filePath);
      this.filled.push(logFilledField(label || selector, filePath, selector));
      return true;
    } catch (e) {
      this.errors.push(logError('upload_file', e.message, selector));
      return false;
    }
  }

  /**
   * Find field by label text
   */
  async findFieldByLabel(page, labelPatterns, inputTypes = ['input', 'textarea', 'select']) {
    for (const pattern of labelPatterns) {
      try {
        // Try label[for] + input
        const labelElement = await page.$(`label:has-text("${pattern}")`);
        if (labelElement) {
          const forAttr = await labelElement.getAttribute('for');
          if (forAttr) {
            const input = await page.$(`#${forAttr}`);
            if (input) return { element: input, selector: `#${forAttr}`, label: pattern };
          }
          
          // Try sibling/child input
          for (const inputType of inputTypes) {
            const siblingInput = await page.$(`label:has-text("${pattern}") + ${inputType}, label:has-text("${pattern}") ${inputType}`);
            if (siblingInput) return { element: siblingInput, selector: `label:has-text("${pattern}") + ${inputType}`, label: pattern };
          }
        }

        // Try aria-label
        for (const inputType of inputTypes) {
          const ariaInput = await page.$(`${inputType}[aria-label*="${pattern}" i]`);
          if (ariaInput) return { element: ariaInput, selector: `${inputType}[aria-label*="${pattern}" i]`, label: pattern };
        }

        // Try placeholder
        for (const inputType of inputTypes) {
          const placeholderInput = await page.$(`${inputType}[placeholder*="${pattern}" i]`);
          if (placeholderInput) return { element: placeholderInput, selector: `${inputType}[placeholder*="${pattern}" i]`, label: pattern };
        }

      } catch (e) {
        // Continue trying other patterns
      }
    }

    return null;
  }

  /**
   * Fill field by label matching
   */
  async fillByLabel(page, payload, fieldKey, options = {}) {
    const mapping = FIELD_MAPPINGS[fieldKey];
    if (!mapping) return false;

    // Skip sensitive fields if configured
    if (mapping.sensitive && options.skipSensitive) {
      this.skipped.push(logSkippedField(fieldKey, 'Sensitive field - requires confirmation', null));
      return false;
    }

    // Get value from payload
    let value = getValueFromPath(payload, mapping.profilePath);
    if (!value && mapping.altPath) {
      value = getValueFromPath(payload, mapping.altPath);
    }

    if (!value) {
      this.skipped.push(logSkippedField(fieldKey, 'No value in profile', null));
      return false;
    }

    // Find the field
    const field = await this.findFieldByLabel(page, mapping.patterns);
    if (!field) {
      this.skipped.push(logSkippedField(fieldKey, 'Field not found on page', null));
      return false;
    }

    // Format value
    const formattedValue = formatValueForInput(value, fieldKey);

    // Fill based on element type
    const tagName = await field.element.evaluate(el => el.tagName.toLowerCase());
    
    switch (tagName) {
      case 'input':
        const inputType = await field.element.getAttribute('type');
        if (inputType === 'file') {
          return false; // Handle files separately
        }
        return await this.fillInput(page, field.selector, formattedValue, field.label);
      
      case 'textarea':
        return await this.fillTextarea(page, field.selector, formattedValue, field.label);
      
      case 'select':
        return await this.fillSelect(page, field.selector, formattedValue, field.label);
      
      default:
        return false;
    }
  }

  /**
   * Get fill results
   */
  getResults() {
    return {
      filled: this.filled,
      skipped: this.skipped,
      errors: this.errors,
    };
  }
}

module.exports = { BaseMapper };
