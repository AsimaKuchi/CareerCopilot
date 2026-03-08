/**
 * Extracts salary information from job description text
 * when structured salary data is not available
 */

// Common salary patterns to detect
const SALARY_PATTERNS = [
  // Currency with range: $90,000 - $120,000 USD
  /\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(?:-|to|–)\s*\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(USD|CAD|EUR|GBP|AUD)?(?:\s*(?:per\s+)?(?:year|annually|yr|pa|p\.a\.))?/gi,
  
  // Single salary with currency: $95,000 CAD
  /\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(USD|CAD|EUR|GBP|AUD)?(?:\s*(?:per\s+)?(?:year|annually|yr|pa|p\.a\.))?/gi,
  
  // Base pay / Salary prefix
  /(?:base\s+(?:pay|salary)|salary|compensation|pay)\s*(?:range)?[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(?:-|to|–)?\s*\$?\s*([\d,]+(?:\.\d{2})?)?\s*(?:k|K)?\s*(USD|CAD|EUR|GBP|AUD)?/gi,
  
  // Hourly rates: $40/hour or $40 per hour
  /\$\s*([\d,]+(?:\.\d{2})?)\s*(?:\/|\s+per\s+)(?:hour|hr|h)\b/gi,
  
  // Range with K notation: $80K - $100K
  /\$\s*([\d]+)\s*[kK]\s*(?:-|to|–)\s*\$?\s*([\d]+)\s*[kK]/gi,
  
  // Up to / Starting at patterns
  /(?:up\s+to|starting\s+at|from)\s+\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(USD|CAD|EUR|GBP|AUD)?/gi,
  
  // Annual salary mentions
  /([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(USD|CAD|EUR|GBP|AUD)\s*(?:per\s+)?(?:year|annually|yr|pa|p\.a\.)/gi,
];

/**
 * Parse a salary string and normalize it
 * @param {string} value - The salary value (e.g., "95000", "95,000", "95K")
 * @returns {number} - Normalized salary as a number
 */
const parseSalaryValue = (value) => {
  if (!value) return 0;
  
  let normalized = value.toString().replace(/,/g, '').trim();
  
  // Handle K notation
  if (/k$/i.test(normalized)) {
    normalized = parseFloat(normalized.replace(/k$/i, '')) * 1000;
  } else {
    normalized = parseFloat(normalized);
  }
  
  return isNaN(normalized) ? 0 : normalized;
};

/**
 * Format salary for display
 * @param {number} min - Minimum salary
 * @param {number} max - Maximum salary (optional)
 * @param {string} currency - Currency code (optional)
 * @param {boolean} isHourly - Whether this is an hourly rate
 * @returns {string} - Formatted salary string
 */
const formatSalary = (min, max, currency = 'USD', isHourly = false) => {
  const currencySymbol = currency === 'CAD' ? 'CA$' : 
                         currency === 'EUR' ? '€' :
                         currency === 'GBP' ? '£' :
                         currency === 'AUD' ? 'A$' : '$';
  
  const formatNumber = (num) => {
    if (num >= 1000) {
      return `${Math.round(num / 1000)}K`;
    }
    return num.toLocaleString();
  };
  
  if (isHourly) {
    return `${currencySymbol}${min}/hr`;
  }
  
  if (max && max > min) {
    return `${currencySymbol}${formatNumber(min)} - ${currencySymbol}${formatNumber(max)}`;
  }
  
  return `${currencySymbol}${formatNumber(min)}`;
};

/**
 * Extract salary information from job description text
 * @param {string} description - The job description text
 * @returns {object|null} - Extracted salary info or null if not found
 */
export const extractSalaryFromDescription = (description) => {
  if (!description) return null;
  
  // Check for hourly rates first
  const hourlyMatch = description.match(/\$\s*([\d,]+(?:\.\d{2})?)\s*(?:\/|\s+per\s+)(?:hour|hr|h)\b/i);
  if (hourlyMatch) {
    const hourlyRate = parseSalaryValue(hourlyMatch[1]);
    if (hourlyRate > 0 && hourlyRate < 500) { // Sanity check for hourly rates
      return {
        min: hourlyRate,
        max: null,
        currency: 'USD',
        isHourly: true,
        display: formatSalary(hourlyRate, null, 'USD', true),
        raw: hourlyMatch[0]
      };
    }
  }
  
  // Check for salary ranges with K notation
  const kRangeMatch = description.match(/\$\s*([\d]+)\s*[kK]\s*(?:-|to|–)\s*\$?\s*([\d]+)\s*[kK]/i);
  if (kRangeMatch) {
    const min = parseSalaryValue(kRangeMatch[1] + 'K');
    const max = parseSalaryValue(kRangeMatch[2] + 'K');
    if (min > 0) {
      return {
        min,
        max,
        currency: 'USD',
        isHourly: false,
        display: formatSalary(min, max, 'USD'),
        raw: kRangeMatch[0]
      };
    }
  }
  
  // Check for currency-specific salaries (CAD, USD, etc.)
  // Note: Support em-dash (—), en-dash (–), hyphen (-), and newlines in ranges
  const currencyMatch = description.match(/\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(?:[-–—]|to)?\s*\$?\s*([\d,]+(?:\.\d{2})?)?\s*(?:k|K)?\s*(CAD|USD|EUR|GBP|AUD)/i);
  if (currencyMatch) {
    const min = parseSalaryValue(currencyMatch[1]);
    const max = currencyMatch[2] ? parseSalaryValue(currencyMatch[2]) : null;
    const currency = currencyMatch[3]?.toUpperCase() || 'USD';
    
    // Sanity check - salary should be at least $10K and less than $10M
    if (min >= 10000 && min < 10000000) {
      return {
        min,
        max: max && max > min ? max : null,
        currency,
        isHourly: false,
        display: formatSalary(min, max && max > min ? max : null, currency),
        raw: currencyMatch[0]
      };
    }
  }
  
  // Check for salary ranges: $90,000 - $120,000
  // Note: Support em-dash (—), en-dash (–), hyphen (-), and newlines in ranges
  const rangeMatch = description.match(/\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?\s*(?:[-–—]|to)\s*\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?/i);
  if (rangeMatch) {
    const min = parseSalaryValue(rangeMatch[1]);
    const max = parseSalaryValue(rangeMatch[2]);
    
    if (min >= 10000 && min < 10000000) {
      return {
        min,
        max: max > min ? max : null,
        currency: 'USD',
        isHourly: false,
        display: formatSalary(min, max > min ? max : null, 'USD'),
        raw: rangeMatch[0]
      };
    }
  }
  
  // Check for base pay / salary prefix patterns
  const baseSalaryMatch = description.match(/(?:base\s+(?:pay|salary)|salary|compensation)\s*(?:range)?[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?/i);
  if (baseSalaryMatch) {
    const min = parseSalaryValue(baseSalaryMatch[1]);
    if (min >= 10000 && min < 10000000) {
      return {
        min,
        max: null,
        currency: 'USD',
        isHourly: false,
        display: formatSalary(min, null, 'USD'),
        raw: baseSalaryMatch[0]
      };
    }
  }
  
  // Check for simple dollar amounts that look like salaries
  const simpleMatch = description.match(/\$\s*([\d,]+)\s*(?:k|K)?(?:\s+(?:per\s+)?(?:year|annually|yr))?/i);
  if (simpleMatch) {
    const value = parseSalaryValue(simpleMatch[1]);
    // Only consider it a salary if it's in a reasonable range
    if (value >= 30000 && value < 1000000) {
      return {
        min: value,
        max: null,
        currency: 'USD',
        isHourly: false,
        display: formatSalary(value, null, 'USD'),
        raw: simpleMatch[0]
      };
    }
  }
  
  return null;
};

/**
 * Get display salary - either from structured field or extracted from description
 * @param {object} job - Job object with salary and description fields
 * @returns {string} - Salary display string or "Salary not listed"
 */
export const getDisplaySalary = (job) => {
  // First check structured salary fields (various naming conventions)
  const minSalary = job.job_min_salary || job.salary_min;
  const maxSalary = job.job_max_salary || job.salary_max;
  
  if (minSalary) {
    if (maxSalary && maxSalary > minSalary) {
      return `$${minSalary.toLocaleString()} - $${maxSalary.toLocaleString()}`;
    }
    return `$${minSalary.toLocaleString()}+`;
  }
  
  // Check if there's a text salary field
  if (job.salary && job.salary !== 'Salary not listed' && job.salary !== 'Not specified') {
    return job.salary;
  }
  
  // Try to extract from description
  const description = job.description || job.full_description || job.description_preview;
  const extracted = extractSalaryFromDescription(description);
  
  if (extracted) {
    return extracted.display;
  }
  
  return 'Salary not listed';
};

export default { extractSalaryFromDescription, getDisplaySalary };
