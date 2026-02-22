// JobMatch AI - Browser Extension Popup Script

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
    
    if (atsInfo.supported) {
      elements.statusCard.className = 'status-card supported';
      elements.statusIcon.textContent = '✅';
      elements.statusTitle.textContent = `${atsInfo.name} Detected`;
      elements.statusText.textContent = 'This page is supported! Click below to auto-fill your application.';
      elements.autoFillBtn.style.display = 'flex';
    } else {
      elements.statusCard.className = 'status-card unsupported';
      elements.statusIcon.textContent = '📋';
      elements.statusTitle.textContent = 'Not an Application Page';
      elements.statusText.textContent = 'Navigate to a job application page on Greenhouse, Lever, Ashby, or other supported ATS to auto-fill.';
      elements.autoFillBtn.style.display = 'none';
    }
  } catch (error) {
    console.error('Error checking page:', error);
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
    
    // Step 1: Fetch autofill data (pass job URL for optimized content matching)
    updateProgress(20, 'Fetching your profile data...');
    
    const stored = await chrome.storage.local.get([STORAGE_KEYS.API_URL]);
    const apiUrl = stored[STORAGE_KEYS.API_URL];
    
    const response = await fetch(`${apiUrl}/api/extension/autofill-data?job_url=${encodeURIComponent(currentUrl)}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch profile data. Please log in to JobMatch AI.');
    }

    const autofillData = await response.json();
    
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
    
    // First, try to inject the content script programmatically
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
    } catch (injectError) {
      console.log('Content script may already be loaded:', injectError);
    }
    
    // Small delay to let script initialize
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Send data to content script
    let result;
    try {
      result = await chrome.tabs.sendMessage(tab.id, {
        action: 'AUTOFILL',
        data: autofillData
      });
    } catch (msgError) {
      // If message fails, try executing autofill directly
      console.log('Message failed, trying direct execution:', msgError);
      
      const execResult = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: executeAutoFillDirect,
        args: [autofillData]
      });
      
      result = execResult[0]?.result || { success: false, filled: [], failed: ['Could not fill form'] };
    }
    
    // Add info about optimized content
    if (autofillData.documents?.resume?.is_optimized) {
      result.filled = result.filled || [];
      result.filled.push('Resume (Optimized for this job)');
    }
    if (autofillData.documents?.cover_letter?.is_optimized) {
      result.filled = result.filled || [];
      result.filled.push('Cover Letter (Optimized for this job)');
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

function showResults(result) {
  elements.results.classList.add('active');
  
  if (result.success) {
    showSuccess(elements.successMsg, `Successfully filled ${result.filledCount} fields!`);
  }
  
  let html = '';
  
  if (result.filled && result.filled.length > 0) {
    result.filled.forEach(field => {
      html += `
        <div class="result-item">
          <span class="result-icon success">✓</span>
          <span>${field}</span>
        </div>
      `;
    });
  }
  
  if (result.failed && result.failed.length > 0) {
    result.failed.forEach(field => {
      html += `
        <div class="result-item">
          <span class="result-icon error">✗</span>
          <span>${field}</span>
        </div>
      `;
    });
  }
  
  if (result.skipped && result.skipped.length > 0) {
    result.skipped.forEach(field => {
      html += `
        <div class="result-item">
          <span class="result-icon" style="color: #fbbf24;">–</span>
          <span>${field} (skipped)</span>
        </div>
      `;
    });
  }
  
  elements.resultsList.innerHTML = html || '<p style="color: rgba(255,255,255,0.6); font-size: 13px;">No fields were filled.</p>';
  
  // Show auto-fill button again for retry
  elements.autoFillBtn.style.display = 'flex';
  elements.autoFillBtn.innerHTML = '<span>Fill Again</span>';
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

