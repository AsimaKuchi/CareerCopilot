// MyCareerCoPilot - Browser Extension Popup Script

const STORAGE_KEYS = {
  API_URL: 'jobmatch_api_url',
  USER_DATA: 'jobmatch_user_data',
  AUTH_TOKEN: 'jobmatch_auth_token'
};

// DOM Elements
let elements = {};

document.addEventListener('DOMContentLoaded', async () => {
  // Cache DOM elements
  elements = {
    loginSection: document.getElementById('loginSection'),
    mainSection: document.getElementById('mainSection'),
    loginError: document.getElementById('loginError'),
    apiUrl: document.getElementById('apiUrl'),
    connectBtn: document.getElementById('connectBtn'),
    userName: document.getElementById('userName'),
    userEmail: document.getElementById('userEmail'),
    statusCard: document.getElementById('statusCard'),
    statusIcon: document.getElementById('statusIcon'),
    statusTitle: document.getElementById('statusTitle'),
    statusText: document.getElementById('statusText'),
    autoFillBtn: document.getElementById('autoFillBtn'),
    progressContainer: document.getElementById('progressContainer'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    results: document.getElementById('results'),
    resultsList: document.getElementById('resultsList'),
    successMsg: document.getElementById('successMsg'),
    errorMsg: document.getElementById('errorMsg'),
    openDashboard: document.getElementById('openDashboard'),
    disconnectBtn: document.getElementById('disconnectBtn')
  };

  // Check if already connected
  const stored = await chrome.storage.local.get([STORAGE_KEYS.API_URL, STORAGE_KEYS.USER_DATA]);
  
  if (stored[STORAGE_KEYS.API_URL] && stored[STORAGE_KEYS.USER_DATA]) {
    showMainSection(stored[STORAGE_KEYS.USER_DATA], stored[STORAGE_KEYS.API_URL]);
  } else if (stored[STORAGE_KEYS.API_URL]) {
    elements.apiUrl.value = stored[STORAGE_KEYS.API_URL];
  }

  // Event Listeners
  elements.connectBtn.addEventListener('click', handleConnect);
  elements.autoFillBtn.addEventListener('click', handleAutoFill);
  elements.disconnectBtn.addEventListener('click', handleDisconnect);
  elements.openDashboard.addEventListener('click', handleOpenDashboard);
});

async function handleConnect() {
  const apiUrl = elements.apiUrl.value.trim();
  
  if (!apiUrl) {
    showError(elements.loginError, 'Please enter your CareerCopilot AI URL');
    return;
  }

  // Clean up URL
  const cleanUrl = apiUrl.replace(/\/$/, '');
  
  elements.connectBtn.innerHTML = '<div class="spinner"></div><span>Connecting...</span>';
  elements.connectBtn.disabled = true;
  hideError(elements.loginError);

  try {
    // Step 1: Check if the API is reachable (non-credentialed health check)
    try {
      const healthResponse = await fetch(`${cleanUrl}/api/health`, {
        method: 'GET',
        credentials: 'omit' // No credentials for initial check
      });
      
      if (!healthResponse.ok) {
        throw new Error('Could not reach CareerCopilot AI. Please check the URL and try again.');
      }
    } catch (healthError) {
      // Network error or API unreachable
      throw new Error('Could not connect to CareerCopilot AI. Please check the URL is correct.');
    }
    
    // Step 2: Now try to fetch profile using a different approach
    // Since CORS with credentials from extensions is tricky, we use background script
    const userData = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'FETCH_PROFILE', apiUrl: cleanUrl },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error('Extension error. Please reload and try again.'));
            return;
          }
          if (response.error) {
            reject(new Error(response.error));
            return;
          }
          resolve(response.data);
        }
      );
    });
    
    // Store connection info
    await chrome.storage.local.set({
      [STORAGE_KEYS.API_URL]: cleanUrl,
      [STORAGE_KEYS.USER_DATA]: userData
    });

    showMainSection(userData, cleanUrl);
    
  } catch (error) {
    showError(elements.loginError, error.message);
  } finally {
    elements.connectBtn.innerHTML = '<span>Connect Account</span>';
    elements.connectBtn.disabled = false;
  }
}

function showMainSection(userData, apiUrl) {
  elements.loginSection.classList.remove('active');
  elements.mainSection.classList.add('active');
  
  // Display user info
  const name = userData.full_name || userData.name || 'User';
  const email = userData.email || '';
  
  elements.userName.textContent = name;
  elements.userEmail.textContent = email;
  elements.openDashboard.href = apiUrl;
  
  // Store API URL in a format content script can access
  chrome.storage.local.set({
    apiUrl: apiUrl,
    sessionToken: '' // Will be set from cookies
  });
  
  // Check current page
  checkCurrentPage();
}

async function checkCurrentPage() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab?.url || '';
    
    const atsInfo = detectATS(url);
    const hasForm = await checkForApplicationForm(tab.id);
    
    if (atsInfo.supported) {
      // Known ATS - high confidence
      elements.statusCard.className = 'status-card supported';
      elements.statusIcon.textContent = '✅';
      elements.statusTitle.textContent = `${atsInfo.name} Detected`;
      elements.statusText.textContent = 'This page is supported! Click below to auto-fill your application.';
      elements.autoFillBtn.style.display = 'flex';
    } else if (hasForm) {
      // Unknown site but has form fields - can try to fill
      elements.statusCard.className = 'status-card supported';
      elements.statusIcon.textContent = '📝';
      elements.statusTitle.textContent = 'Application Form Detected';
      elements.statusText.textContent = 'Found form fields on this page. Click below to auto-fill.';
      elements.autoFillBtn.style.display = 'flex';
    } else {
      // No form detected - but still allow manual attempt
      elements.statusCard.className = 'status-card unsupported';
      elements.statusIcon.textContent = '🔍';
      elements.statusTitle.textContent = 'No Form Detected';
      elements.statusText.textContent = 'No application form found, but you can still try to auto-fill.';
      elements.autoFillBtn.style.display = 'flex';
      elements.autoFillBtn.innerHTML = '<span>Try Auto-Fill Anyway</span>';
    }
  } catch (error) {
    console.error('Error checking page:', error);
    // Still show button on error
    elements.autoFillBtn.style.display = 'flex';
  }
}

async function checkForApplicationForm(tabId) {
  try {
    // Check ALL frames (top + iframes). Many ATS forms (Lyft/Greenhouse
    // job-boards) live inside an iframe on the careers page.
    const results = await chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      func: () => {
        // Check for common job application form indicators
        const indicators = [
          'input[type="email"]',
          'input[name*="name" i]',
          'input[name*="phone" i]',
          'input[type="file"]',
          'input[name*="resume" i]',
          'input[name*="cv" i]',
          'textarea[name*="cover" i]',
          'form'
        ];
        
        for (const sel of indicators) {
          if (document.querySelector(sel)) return true;
        }
        
        // Check for job-related keywords in page text
        const pageText = document.body?.innerText?.toLowerCase() || '';
        const jobKeywords = ['apply', 'application', 'resume', 'cv', 'cover letter', 'experience', 'qualifications'];
        const hasJobKeywords = jobKeywords.some(kw => pageText.includes(kw));
        
        return hasJobKeywords;
      }
    });
    
    // Return true if ANY frame reports a form
    return (results || []).some(r => r?.result === true);
  } catch (e) {
    console.log('Could not check for form:', e);
    return false;
  }
}

function detectATS(url) {
  const atsPatterns = [
    { pattern: /boards\.greenhouse\.io|jobs\.greenhouse\.io/i, name: 'Greenhouse' },
    { pattern: /jobs\.lever\.co/i, name: 'Lever' },
    { pattern: /jobs\.ashbyhq\.com/i, name: 'Ashby' },
    { pattern: /apply\.workable\.com/i, name: 'Workable' },
    { pattern: /careers\.smartrecruiters\.com/i, name: 'SmartRecruiters' },
    { pattern: /\.pinpointhq\.com/i, name: 'Pinpoint' },
    { pattern: /\.bamboohr\.com/i, name: 'BambooHR' },
    { pattern: /\.teamtailor\.com/i, name: 'Teamtailor' },
    { pattern: /\.jobvite\.com/i, name: 'Jobvite' },
    { pattern: /\.myworkdayjobs\.com/i, name: 'Workday' },
    { pattern: /\.taleo\.net/i, name: 'Taleo' },
    { pattern: /\.icims\.com/i, name: 'iCIMS' },
    { pattern: /\.randstad\.ca|\.randstad\.com|www\.randstad\./i, name: 'Randstad' }
  ];

  for (const ats of atsPatterns) {
    if (ats.pattern.test(url)) {
      return { supported: true, name: ats.name };
    }
  }

  return { supported: false, name: null };
}

async function handleAutoFill() {
  elements.autoFillBtn.style.display = 'none';
  elements.progressContainer.classList.add('active');
  elements.results.classList.remove('active');
  hideError(elements.errorMsg);
  hideSuccess(elements.successMsg);
  
  try {
    // Get current tab URL for job matching
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentUrl = tab?.url || '';
    
    // Step 1: Fetch autofill data via background script (which has cookie access)
    updateProgress(20, 'Fetching your profile data...');
    
    const stored = await chrome.storage.local.get([STORAGE_KEYS.API_URL]);
    const apiUrl = stored[STORAGE_KEYS.API_URL];
    
    const autofillData = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'FETCH_AUTOFILL', apiUrl, jobUrl: currentUrl },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error('Extension error. Please reload and try again.'));
            return;
          }
          if (response.error) {
            reject(new Error(response.error));
            return;
          }
          resolve(response.data);
        }
      );
    });
    
    // Store API URL and current job URL for submission tracking
    // The content script will use these to track submissions
    await chrome.storage.local.set({
      apiUrl: apiUrl,
      currentJobUrl: currentUrl
    });
    
    // Show if we matched a saved application
    if (autofillData.matched_job) {
      updateProgress(40, `Found saved application: ${autofillData.matched_job}`);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Step 2: Fill form fields
    updateProgress(50, 'Filling form fields...');

    // Inject the content script into ALL frames (top + iframes). Many ATS
    // forms (Lyft/Greenhouse job-boards) are embedded via iframe, so filling
    // only the top frame silently skips every field. The manifest also
    // declares content.js at all_frames, but explicit injection ensures the
    // handler is loaded even on pages that had it stripped or blocked.
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id, allFrames: true },
        files: ['content.js']
      });
    } catch (injectError) {
      console.log('Content script may already be loaded:', injectError);
    }

    // Small delay to let script initialize
    await new Promise(resolve => setTimeout(resolve, 250));

    // Execute the autofill in EVERY frame. Frames without form fields exit
    // early inside content.js so we only get real results.
    let result;
    try {
      const execResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id, allFrames: true },
        func: async (payload) => {
          // Runs inside each frame's isolated world.
          if (typeof window.__mccHandleAutoFill === 'function') {
            try {
              return await window.__mccHandleAutoFill(payload);
            } catch (e) {
              return { success: false, filled: [], failed: [`Error: ${e.message}`], skipped: [], frameHadForm: false };
            }
          }
          return null;
        },
        args: [autofillData]
      });

      // Aggregate results from all frames. Only include frames that reported
      // frameHadForm=true so we don't show spurious "skipped" from empty frames.
      result = aggregateFrameResults(execResults);
    } catch (msgError) {
      console.log('executeScript failed, falling back to direct exec:', msgError);
      const execResult = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: executeAutoFillDirect,
        args: [autofillData]
      });
      result = execResult[0]?.result || { success: false, filled: [], failed: ['Could not fill form'], skipped: [] };
    }

    updateProgress(100, 'Complete!');
    
    // Show results
    setTimeout(() => {
      elements.progressContainer.classList.remove('active');
      showResults(result);
    }, 500);
    
  } catch (error) {
    console.error('Auto-fill error:', error);
    elements.progressContainer.classList.remove('active');
    showError(elements.errorMsg, error.message);
    elements.autoFillBtn.style.display = 'flex';
  }
}

function updateProgress(percent, text) {
  elements.progressFill.style.width = `${percent}%`;
  elements.progressText.textContent = text;
}

// Combine autofill results returned from each frame into a single result set.
// - Only counts frames that had a form (frameHadForm=true).
// - De-duplicates identical filled/failed/skipped entries.
// - Suppresses "skipped" entries whose base name matches something already
//   filled (e.g. hides "Resume (no file input)" if resume was uploaded in
//   another frame).
function aggregateFrameResults(execResults) {
  const combined = { success: false, filled: [], failed: [], skipped: [], entries: [], filledCount: 0 };
  const filledSet = new Set();
  const failedSet = new Set();
  const skippedSet = new Set();
  const entryKeys = new Set();
  let anyFrameHadForm = false;

  for (const entry of execResults || []) {
    const r = entry?.result;
    if (!r || !r.frameHadForm) continue;
    anyFrameHadForm = true;
    (r.filled || []).forEach(f => filledSet.add(f));
    (r.failed || []).forEach(f => failedSet.add(f));
    (r.skipped || []).forEach(f => skippedSet.add(f));
    (r.entries || []).forEach(e => {
      // Dedupe by (name + status) key across frames
      const key = `${(e.name || '').toLowerCase()}|${e.status}`;
      if (!entryKeys.has(key)) {
        entryKeys.add(key);
        combined.entries.push(e);
      }
    });
  }

  combined.filled = Array.from(filledSet);
  combined.failed = Array.from(failedSet);

  // Suppress redundant skipped entries. If Resume was filled, don't show
  // "Resume (no file input) (skipped)".
  const filledBaseNames = combined.filled.map(f => f.toLowerCase().split(' (')[0]);
  combined.skipped = Array.from(skippedSet).filter(s => {
    const base = s.toLowerCase().split(' (')[0];
    return !filledBaseNames.includes(base);
  });

  // Same for entries: if a document was filled in one frame, suppress
  // 'attention/failed' entries for the same doc from other frames.
  const filledEntryBaseNames = combined.entries
    .filter(e => e.status === 'filled')
    .map(e => baseName(e.name));
  combined.entries = combined.entries.filter(e => {
    if (e.status === 'filled') return true;
    return !filledEntryBaseNames.includes(baseName(e.name));
  });

  combined.filledCount = combined.filled.length;
  combined.success = combined.filledCount > 0;

  if (!anyFrameHadForm) {
    combined.failed.push('No form fields detected on this page');
  }

  return combined;
}

// Extract the base field name so "Resume (optimized for this job)" and
// "Resume" are treated as the same field for de-dup purposes.
function baseName(name) {
  return String(name || '').toLowerCase().replace(/\s*\(.*?\)\s*/g, '').trim();
}

function showResults(result) {
  elements.results.classList.add('active');

  // If we have structured entries, render the Field Coverage Report.
  // Otherwise fall back to the legacy flat list (defensive).
  if (result.entries && result.entries.length > 0) {
    renderCoverageReport(result);
  } else {
    renderLegacyList(result);
  }

  // Show auto-fill button again for retry
  elements.autoFillBtn.style.display = 'flex';
  elements.autoFillBtn.innerHTML = '<span>Fill Again</span>';
}

function renderCoverageReport(result) {
  const entries = result.entries || [];
  const filled = entries.filter(e => e.status === 'filled');
  const needsAttention = entries.filter(e => e.status !== 'filled');
  const total = entries.length;
  const pct = total > 0 ? Math.round((filled.length / total) * 100) : 0;

  if (result.success) {
    showSuccess(elements.successMsg, `Filled ${filled.length} of ${total} fields · ${pct}% coverage`);
  } else {
    showError(elements.errorMsg, needsAttention.length > 0
      ? `${needsAttention.length} field${needsAttention.length === 1 ? '' : 's'} need your attention`
      : 'No fields were filled — try clicking directly on the form first');
  }

  const groups = {
    personal_info: { title: 'Personal Info', entries: [] },
    documents: { title: 'Documents', entries: [] },
    screening: { title: 'Screening Questions', entries: [] },
    other: { title: 'Other', entries: [] }
  };
  for (const e of entries) {
    const g = groups[e.category] || groups.other;
    g.entries.push(e);
  }

  const iconFor = (status) => {
    if (status === 'filled') return '<span class="fc-icon fc-filled" data-testid="fc-icon-filled">✓</span>';
    if (status === 'failed') return '<span class="fc-icon fc-failed" data-testid="fc-icon-failed">!</span>';
    return '<span class="fc-icon fc-attention" data-testid="fc-icon-attention">?</span>';
  };

  let html = `
    <div class="coverage-summary" data-testid="coverage-summary">
      <div class="coverage-header">
        <span class="coverage-count" data-testid="coverage-count">${filled.length} / ${total} filled</span>
        <span class="coverage-pct" data-testid="coverage-pct">${pct}%</span>
      </div>
      <div class="coverage-bar"><div class="coverage-bar-fill" style="width: ${pct}%"></div></div>
      ${needsAttention.length > 0
        ? `<div class="coverage-attention" data-testid="coverage-attention">${needsAttention.length} field${needsAttention.length === 1 ? ' needs' : 's need'} your attention below</div>`
        : ''}
    </div>
  `;

  const order = ['personal_info', 'documents', 'screening', 'other'];
  for (const key of order) {
    const g = groups[key];
    if (!g.entries.length) continue;
    html += `
      <div class="fc-group" data-testid="fc-group-${key}">
        <div class="fc-group-title">${g.title}</div>
        ${g.entries.map(e => `
          <div class="fc-row fc-row-${e.status}" data-testid="fc-row-${e.status}">
            ${iconFor(e.status)}
            <div class="fc-row-body">
              <div class="fc-row-name">${escapeHtml(e.name)}</div>
              ${e.hint ? `<div class="fc-row-hint">${escapeHtml(e.hint)}</div>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  elements.resultsList.innerHTML = html;
}

function renderLegacyList(result) {
  if (result.success) {
    showSuccess(elements.successMsg, `Successfully filled ${result.filledCount} fields!`);
  }
  let html = '';
  (result.filled || []).forEach(field => {
    html += `<div class="result-item"><span class="result-icon success">✓</span><span>${escapeHtml(field)}</span></div>`;
  });
  (result.failed || []).forEach(field => {
    html += `<div class="result-item"><span class="result-icon error">✗</span><span>${escapeHtml(field)}</span></div>`;
  });
  (result.skipped || []).forEach(field => {
    html += `<div class="result-item"><span class="result-icon" style="color: #fbbf24;">–</span><span>${escapeHtml(field)} (skipped)</span></div>`;
  });
  elements.resultsList.innerHTML = html || '<p style="color: rgba(255,255,255,0.6); font-size: 13px;">No fields were filled.</p>';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function handleDisconnect() {
  await chrome.storage.local.remove([STORAGE_KEYS.API_URL, STORAGE_KEYS.USER_DATA, STORAGE_KEYS.AUTH_TOKEN]);
  
  elements.mainSection.classList.remove('active');
  elements.loginSection.classList.add('active');
  elements.results.classList.remove('active');
  elements.progressContainer.classList.remove('active');
  hideError(elements.errorMsg);
  hideSuccess(elements.successMsg);
}

function handleOpenDashboard(e) {
  e.preventDefault();
  chrome.storage.local.get([STORAGE_KEYS.API_URL], (stored) => {
    if (stored[STORAGE_KEYS.API_URL]) {
      chrome.tabs.create({ url: stored[STORAGE_KEYS.API_URL] });
    }
  });
}

function showError(element, message) {
  element.textContent = message;
  element.classList.add('active');
}

function hideError(element) {
  element.classList.remove('active');
}

function showSuccess(element, message) {
  element.textContent = message;
  element.classList.add('active');
}

function hideSuccess(element) {
  element.classList.remove('active');
}

// Direct autofill function that runs in page context
function executeAutoFillDirect(data) {
  const results = {
    success: false,
    filled: [],
    failed: [],
    skipped: [],
    filledCount: 0
  };

  function fillField(selectors, value) {
    if (!value) return false;
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        try {
          const style = window.getComputedStyle(el);
          if (style.display === 'none' || style.visibility === 'hidden' || el.disabled) continue;
          
          if (el.tagName === 'SELECT') {
            const options = Array.from(el.options);
            const match = options.find(opt => 
              opt.text.toLowerCase().includes(value.toLowerCase()) ||
              value.toLowerCase().includes(opt.text.toLowerCase())
            );
            if (match) {
              el.value = match.value;
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
          } else {
            el.focus();
            el.value = value;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
            return true;
          }
        } catch (e) { continue; }
      }
    }
    return false;
  }

  const p = data.personal_info || {};
  
  // First Name
  if (p.first_name && fillField(['input[name*="first" i]', 'input[id*="first" i]', 'input[autocomplete="given-name"]'], p.first_name)) {
    results.filled.push('First Name');
  }
  
  // Last Name
  if (p.last_name && fillField(['input[name*="last" i]', 'input[id*="last" i]', 'input[autocomplete="family-name"]'], p.last_name)) {
    results.filled.push('Last Name');
  }
  
  // Email
  if (p.email && fillField(['input[type="email"]', 'input[name*="email" i]', 'input[autocomplete="email"]'], p.email)) {
    results.filled.push('Email');
  }
  
  // Phone
  if (p.phone && fillField(['input[type="tel"]', 'input[name*="phone" i]', 'input[autocomplete="tel"]'], p.phone)) {
    results.filled.push('Phone');
  }
  
  // LinkedIn
  if (p.linkedin && fillField(['input[name*="linkedin" i]', 'input[id*="linkedin" i]'], p.linkedin)) {
    results.filled.push('LinkedIn');
  }
  
  // GitHub
  if (p.github && fillField(['input[name*="github" i]', 'input[id*="github" i]'], p.github)) {
    results.filled.push('GitHub');
  }
  
  // Portfolio
  if (p.portfolio && fillField(['input[name*="portfolio" i]', 'input[name*="website" i]', 'input[type="url"]'], p.portfolio)) {
    results.filled.push('Portfolio');
  }
  
  // City
  if (p.location?.city && fillField(['input[name*="city" i]', 'input[autocomplete="address-level2"]'], p.location.city)) {
    results.filled.push('City');
  }

  results.success = results.filled.length > 0;
  results.filledCount = results.filled.length;
  
  return results;
}

