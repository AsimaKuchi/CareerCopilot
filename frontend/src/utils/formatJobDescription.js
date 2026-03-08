/**
 * Formats job descriptions for better readability
 * - Detects and highlights section headers
 * - Converts lists to bullet points
 * - Adds proper spacing and visual hierarchy
 */

// Common section headers to detect (case-insensitive)
const SECTION_HEADERS = [
  // About sections
  'about the role', 'about us', 'about the position', 'about the team', 
  'about the company', 'about this role', 'about', 'company description',
  'who we are', 'the opportunity', 'overview', 'summary', 'introduction',
  'role description', 'position overview', 'job summary',
  
  // Community/Team
  'the community you will join', 'the team', 'your team', 'meet the team',
  
  // Responsibilities
  'responsibilities', 'what you\'ll do', 'what you will do', 'your responsibilities',
  'the role', 'key responsibilities', 'job responsibilities', 'duties',
  'what you\'ll be doing', 'day to day', 'in this role you will',
  'your day-to-day', 'you will', 'your role', 'a typical day',
  'the difference you will make', 'your impact', 'what you\'ll work on',
  
  // Requirements
  'requirements', 'qualifications', 'what we\'re looking for', 
  'what we are looking for', 'must have', 'required qualifications',
  'minimum qualifications', 'basic qualifications', 'required skills',
  'what you need', 'you should have', 'who you are', 'ideal candidate',
  'required experience', 'experience required', 'your expertise',
  'your background', 'your experience',
  
  // Skills
  'skills', 'technical skills', 'required skills', 'key skills',
  'core competencies', 'technical requirements', 'tools and technologies',
  
  // Nice to have
  'nice to have', 'preferred qualifications', 'bonus', 'preferred',
  'plus', 'nice to haves', 'desired qualifications', 'additional qualifications',
  'it\'s a plus if', 'bonus points', 'extra credit',
  
  // Benefits
  'benefits', 'what we offer', 'perks', 'compensation', 'why join us',
  'why work here', 'our offer', 'what\'s in it for you', 'total rewards',
  'compensation and benefits', 'employee benefits', 'our benefits',
  
  // Other
  'how to apply', 'next steps', 'equal opportunity', 'diversity',
  'location', 'work arrangement', 'remote work', 'hybrid',
  'our commitment', 'additional information'
];

// Action verbs that often start list items
const ACTION_VERBS = [
  'design', 'develop', 'create', 'build', 'implement', 'manage', 'lead',
  'analyze', 'collaborate', 'work', 'drive', 'own', 'support', 'maintain',
  'write', 'review', 'test', 'deploy', 'optimize', 'scale', 'architect',
  'communicate', 'partner', 'coordinate', 'ensure', 'deliver', 'define',
  'establish', 'evaluate', 'execute', 'facilitate', 'gather', 'identify',
  'improve', 'investigate', 'mentor', 'monitor', 'participate', 'perform',
  'plan', 'prepare', 'present', 'provide', 'research', 'resolve', 'track',
  'transform', 'understand', 'utilize', 'validate', 'help', 'assist',
  'contribute', 'engage', 'influence'
];

/**
 * Check if a line is likely a section header
 */
const isSectionHeader = (line) => {
  const trimmed = line.trim().toLowerCase();
  // Remove trailing colons and check
  const cleaned = trimmed.replace(/:$/, '').trim();
  
  // Direct match with section headers
  if (SECTION_HEADERS.some(header => cleaned === header || cleaned.startsWith(header + ' '))) {
    return true;
  }
  
  // Short lines ending with colon that look like headers (not too short)
  if (line.trim().endsWith(':') && line.trim().length < 60 && line.trim().length > 5 && !line.includes('.')) {
    return true;
  }
  
  // ALL CAPS short lines (likely headers)
  if (line === line.toUpperCase() && line.trim().length < 50 && line.trim().length > 3 && /[A-Z]/.test(line)) {
    return true;
  }
  
  return false;
};

/**
 * Check if a line looks like a list item
 */
const isListItem = (line) => {
  const trimmed = line.trim();
  
  // Already has bullet or dash
  if (/^[-•●○◦▪▸►◆★✓✔→]\s/.test(trimmed)) return true;
  
  // Numbered list (1. or 1) or a. or a))
  if (/^(\d+[\.\):]|\w[\.\)])\s/.test(trimmed)) return true;
  
  // Starts with action verb (common in job descriptions) and is reasonably short
  const firstWord = trimmed.split(/\s+/)[0]?.toLowerCase().replace(/[^a-z]/g, '');
  if (ACTION_VERBS.includes(firstWord) && trimmed.length < 250 && trimmed.length > 10) return true;
  
  return false;
};

/**
 * Clean and normalize a line
 */
const cleanLine = (line) => {
  return line
    .replace(/^[-•●○◦▪▸►◆★✓✔→]\s*/, '') // Remove existing bullets
    .replace(/^(\d+[\.\):]|\w[\.\)])\s*/, '') // Remove numbering
    .trim();
};

/**
 * Pre-process description to add newlines before section headers
 */
const preprocessDescription = (description) => {
  let processed = description;
  
  // Add newlines before common section header patterns that appear inline
  const headerPatterns = SECTION_HEADERS.map(h => h.replace(/'/g, "['']?"));
  
  for (const header of SECTION_HEADERS) {
    // Pattern: Header followed by colon (case insensitive)
    const regex = new RegExp(`([.!?]\\s*)(?=${header}\\s*:)`, 'gi');
    processed = processed.replace(regex, '$1\n\n');
    
    // Also add newline before the header itself if not already there
    const headerRegex = new RegExp(`([^\\n])\\s*(${header}\\s*:)`, 'gi');
    processed = processed.replace(headerRegex, '$1\n\n$2');
  }
  
  return processed;
};

/**
 * Format job description for display
 * Returns an array of formatted elements with type information
 */
export const parseJobDescription = (description) => {
  if (!description) return [];
  
  // Pre-process to add structure
  const processed = preprocessDescription(description);
  
  // Split by newlines, preserving structure
  const lines = processed.split(/\n+/);
  const elements = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    if (isSectionHeader(line)) {
      // Format as section header
      const headerText = line.replace(/:$/, '').trim();
      elements.push({
        type: 'header',
        content: headerText
      });
    } else if (isListItem(line)) {
      // Format as bullet point
      elements.push({
        type: 'bullet',
        content: cleanLine(line)
      });
    } else {
      // Regular paragraph - check if it's a short sentence that could be a bullet
      if (line.length < 200 && line.split(' ').length > 3 && line.split(' ').length < 30) {
        const firstWord = line.split(/\s+/)[0]?.toLowerCase().replace(/[^a-z]/g, '');
        if (ACTION_VERBS.includes(firstWord)) {
          elements.push({
            type: 'bullet',
            content: cleanLine(line)
          });
          continue;
        }
      }
      
      elements.push({
        type: 'paragraph',
        content: line
      });
    }
  }
  
  return elements;
};

/**
 * Format description as React elements
 */
export const formatJobDescription = (description) => {
  const elements = parseJobDescription(description);
  
  return elements.map((el, idx) => {
    switch (el.type) {
      case 'header':
        return {
          key: idx,
          type: 'header',
          content: el.content
        };
      case 'bullet':
        return {
          key: idx,
          type: 'bullet',
          content: el.content
        };
      default:
        return {
          key: idx,
          type: 'paragraph',
          content: el.content
        };
    }
  });
};

export default formatJobDescription;
