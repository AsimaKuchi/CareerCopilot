/**
 * Field Matcher Utilities
 * 
 * Maps form labels to profile fields using fuzzy matching.
 */

/**
 * Field mapping configuration
 * Maps label patterns to profile field paths
 */
const FIELD_MAPPINGS = {
  // Identity
  first_name: {
    patterns: ['first name', 'given name', 'first', 'nombre', 'prénom'],
    profilePath: 'profile.first_name',
    sensitive: false,
  },
  last_name: {
    patterns: ['last name', 'surname', 'family name', 'last', 'apellido', 'nom'],
    profilePath: 'profile.last_name',
    sensitive: false,
  },
  full_name: {
    patterns: ['full name', 'name', 'your name', 'applicant name'],
    profilePath: 'profile.full_name',
    sensitive: false,
  },
  email: {
    patterns: ['email', 'e-mail', 'email address', 'your email', 'correo'],
    profilePath: 'profile.email',
    sensitive: false,
  },
  phone: {
    patterns: ['phone', 'telephone', 'mobile', 'cell', 'phone number', 'contact number', 'teléfono'],
    profilePath: 'profile.phone',
    altPath: 'profile.phone_formatted',
    sensitive: false,
  },

  // Location
  city: {
    patterns: ['city', 'ciudad', 'ville', 'town'],
    profilePath: 'profile.city',
    sensitive: false,
  },
  state: {
    patterns: ['state', 'province', 'region', 'estado', 'provincia'],
    profilePath: 'profile.state',
    sensitive: false,
  },
  country: {
    patterns: ['country', 'país', 'nation'],
    profilePath: 'profile.country_full',
    altPath: 'profile.country',
    sensitive: false,
  },
  address: {
    patterns: ['address', 'street address', 'street', 'dirección'],
    profilePath: 'profile.address',
    sensitive: false,
  },
  postal_code: {
    patterns: ['postal code', 'zip code', 'zip', 'postcode', 'código postal'],
    profilePath: 'profile.postal_code',
    sensitive: false,
  },

  // Links
  linkedin: {
    patterns: ['linkedin', 'linkedin url', 'linkedin profile', 'linkedin.com'],
    profilePath: 'profile.linkedin_url',
    sensitive: false,
  },
  github: {
    patterns: ['github', 'github url', 'github profile', 'github.com'],
    profilePath: 'profile.github_url',
    sensitive: false,
  },
  portfolio: {
    patterns: ['portfolio', 'portfolio url', 'personal website', 'website', 'personal site'],
    profilePath: 'profile.portfolio_url',
    altPath: 'profile.website_url',
    sensitive: false,
  },

  // Professional
  current_company: {
    patterns: ['current company', 'current employer', 'company', 'employer', 'organization'],
    profilePath: 'profile.current_company',
    sensitive: false,
  },
  current_title: {
    patterns: ['current title', 'job title', 'current position', 'title', 'role'],
    profilePath: 'profile.desired_job_titles[0]',
    sensitive: false,
  },
  years_experience: {
    patterns: ['years of experience', 'years experience', 'experience years', 'total experience', 'years'],
    profilePath: 'profile.experience_years',
    sensitive: false,
  },

  // Education
  education: {
    patterns: ['education', 'highest education', 'degree', 'educational background'],
    profilePath: 'profile.education',
    sensitive: false,
  },
  school: {
    patterns: ['school', 'university', 'college', 'institution', 'alma mater'],
    profilePath: 'profile.school',
    sensitive: false,
  },

  // Sensitive fields - require confirmation
  work_authorization: {
    patterns: ['work authorization', 'authorized to work', 'legal right to work', 'legally authorized', 'eligibility to work'],
    profilePath: 'profile.work_authorization.status',
    sensitive: true,
  },
  sponsorship: {
    patterns: ['sponsorship', 'require sponsorship', 'visa sponsorship', 'need sponsorship', 'immigration sponsorship'],
    profilePath: 'profile.work_authorization.requires_sponsorship',
    sensitive: true,
  },
  salary: {
    patterns: ['salary', 'expected salary', 'salary expectation', 'compensation', 'desired salary', 'pay expectation'],
    profilePath: 'profile.salary_min',
    sensitive: true,
  },
  salary_min: {
    patterns: ['minimum salary', 'salary minimum', 'min salary'],
    profilePath: 'profile.salary_min',
    sensitive: true,
  },
  salary_max: {
    patterns: ['maximum salary', 'salary maximum', 'max salary'],
    profilePath: 'profile.salary_max',
    sensitive: true,
  },
  relocate: {
    patterns: ['relocate', 'relocation', 'willing to relocate', 'open to relocation', 'move'],
    profilePath: 'profile.willing_to_relocate',
    sensitive: true,
  },
  notice_period: {
    patterns: ['notice period', 'notice', 'when can you start', 'start date', 'availability', 'earliest start'],
    profilePath: 'profile.notice_period',
    sensitive: true,
  },
  referral_source: {
    patterns: ['how did you hear', 'referral', 'source', 'where did you hear', 'how did you find', 'heard about us'],
    profilePath: 'profile.referral_source',
    sensitive: true,
  },

  // Documents
  resume: {
    patterns: ['resume', 'cv', 'curriculum vitae', 'résumé'],
    profilePath: 'documents.resume',
    isDocument: true,
    sensitive: false,
  },
  cover_letter: {
    patterns: ['cover letter', 'covering letter', 'letter of interest', 'motivation letter'],
    profilePath: 'documents.cover_letter',
    isDocument: true,
    sensitive: false,
  },
};

/**
 * Work authorization value mappings for Canada and US
 */
const WORK_AUTH_VALUES = {
  // Canadian statuses
  canadian_citizen: ['citizen', 'canadian citizen', 'yes', 'authorized'],
  permanent_resident: ['permanent resident', 'pr', 'landed immigrant', 'yes', 'authorized'],
  work_permit: ['work permit', 'open work permit', 'pgwp', 'yes - with restrictions'],
  require_sponsorship: ['require sponsorship', 'no', 'lmia required', 'need sponsorship'],
  
  // US statuses
  us_citizen: ['citizen', 'us citizen', 'american citizen', 'yes', 'authorized'],
  green_card: ['green card', 'permanent resident', 'lawful permanent resident', 'yes', 'authorized'],
  h1b: ['h-1b', 'h1b', 'yes - visa holder', 'work visa'],
  tn_visa: ['tn', 'tn visa', 'nafta', 'yes - tn'],
  opt: ['opt', 'optional practical training', 'f-1 opt'],
  require_sponsorship_us: ['require sponsorship', 'no', 'need h-1b', 'need sponsorship'],
};

/**
 * Yes/No value mappings
 */
const YES_NO_VALUES = {
  yes: ['yes', 'true', '1', 'y', 'oui', 'sí'],
  no: ['no', 'false', '0', 'n', 'non'],
};

/**
 * Normalize text for comparison
 */
function normalizeText(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Calculate similarity between two strings
 */
function similarity(str1, str2) {
  const s1 = normalizeText(str1);
  const s2 = normalizeText(str2);
  
  if (s1 === s2) return 1;
  if (s1.includes(s2) || s2.includes(s1)) return 0.8;
  
  // Word overlap
  const words1 = s1.split(' ');
  const words2 = s2.split(' ');
  const overlap = words1.filter(w => words2.includes(w)).length;
  const maxWords = Math.max(words1.length, words2.length);
  
  return overlap / maxWords;
}

/**
 * Match a label to a profile field
 * Returns { fieldKey, mapping, confidence } or null
 */
function matchLabelToField(label) {
  const normalizedLabel = normalizeText(label);
  let bestMatch = null;
  let bestScore = 0;

  for (const [fieldKey, mapping] of Object.entries(FIELD_MAPPINGS)) {
    for (const pattern of mapping.patterns) {
      const score = similarity(normalizedLabel, pattern);
      if (score > bestScore && score >= 0.5) {
        bestScore = score;
        bestMatch = {
          fieldKey,
          mapping,
          confidence: score >= 0.8 ? 'high' : score >= 0.6 ? 'medium' : 'low',
          matchedPattern: pattern,
        };
      }
    }
  }

  return bestMatch;
}

/**
 * Get value from payload using dot notation path
 */
function getValueFromPath(payload, path) {
  const parts = path.split('.');
  let value = payload;

  for (const part of parts) {
    // Handle array notation like [0]
    const arrayMatch = part.match(/^(\w+)\[(\d+)\]$/);
    if (arrayMatch) {
      const [, key, index] = arrayMatch;
      value = value?.[key]?.[parseInt(index)];
    } else {
      value = value?.[part];
    }
    
    if (value === undefined || value === null) break;
  }

  return value;
}

/**
 * Format value for form input
 */
function formatValueForInput(value, fieldKey) {
  if (value === null || value === undefined) return null;
  
  // Handle booleans
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  
  // Handle numbers
  if (typeof value === 'number') {
    // Salary formatting
    if (fieldKey.includes('salary')) {
      return value.toLocaleString();
    }
    return value.toString();
  }
  
  // Handle arrays
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  
  return String(value);
}

/**
 * Match select option to value
 */
function matchSelectOption(options, targetValue) {
  const normalizedTarget = normalizeText(String(targetValue));
  
  for (const option of options) {
    const normalizedOption = normalizeText(option.text || option.value || '');
    if (normalizedOption === normalizedTarget || 
        normalizedOption.includes(normalizedTarget) ||
        normalizedTarget.includes(normalizedOption)) {
      return option.value;
    }
  }
  
  // Try work auth mappings
  for (const [key, values] of Object.entries(WORK_AUTH_VALUES)) {
    if (normalizedTarget.includes(normalizeText(key))) {
      for (const option of options) {
        const optText = normalizeText(option.text || option.value || '');
        for (const val of values) {
          if (optText.includes(normalizeText(val))) {
            return option.value;
          }
        }
      }
    }
  }
  
  return null;
}

module.exports = {
  FIELD_MAPPINGS,
  WORK_AUTH_VALUES,
  YES_NO_VALUES,
  normalizeText,
  similarity,
  matchLabelToField,
  getValueFromPath,
  formatValueForInput,
  matchSelectOption,
};
