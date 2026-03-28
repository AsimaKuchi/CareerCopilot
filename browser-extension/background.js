// MyCareerCoPilot - Background Service Worker

const STORAGE_KEYS = {
  API_URL: 'jobmatch_api_url',
  USER_DATA: 'jobmatch_user_data'
};

// Handle installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[MyCareerCoPilot] Extension installed');
  } else if (details.reason === 'update') {
    console.log('[MyCareerCoPilot] Extension updated');
  }
});

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'GET_AUTH') {
    // Return stored auth info
    chrome.storage.local.get([STORAGE_KEYS.API_URL, STORAGE_KEYS.USER_DATA], (result) => {
      sendResponse(result);
    });
    return true;
  }
  
  if (message.action === 'OPEN_OPTIONS') {
    chrome.runtime.openOptionsPage();
  }
  
  // Handle profile fetch from popup (with proper cookie handling)
  if (message.action === 'FETCH_PROFILE') {
    handleFetchProfile(message.apiUrl).then(sendResponse);
    return true; // Keep channel open for async response
  }
  
  // Handle autofill data fetch from popup
  if (message.action === 'FETCH_AUTOFILL') {
    handleFetchAutofill(message.apiUrl, message.jobUrl).then(sendResponse);
    return true;
  }
  
  // Handle submission tracking from content script
  if (message.action === 'TRACK_SUBMISSION') {
    handleTrackSubmission(message.data).then(sendResponse);
    return true; // Keep channel open for async response
  }
});

// Fetch user profile with cookies (runs in background service worker)
async function handleFetchProfile(apiUrl) {
  console.log('[CareerCopilot AI] Fetching profile from:', apiUrl);
  
  try {
    const url = new URL(apiUrl);
    
    // Get the session cookie using the cookies API
    const sessionCookie = await chrome.cookies.get({
      url: apiUrl,
      name: 'session_token'
    });
    
    if (!sessionCookie) {
      return { 
        error: 'Not logged in. Please sign in to CareerCopilot AI website first, then try connecting again.' 
      };
    }
    
    console.log('[CareerCopilot AI] Found session cookie');
    
    // Make API call with cookie header manually set
    const response = await fetch(`${apiUrl}/api/profile`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': `session_token=${sessionCookie.value}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        return { 
          error: 'Session expired. Please sign in to CareerCopilot AI website again, then reconnect.' 
        };
      }
      return { 
        error: `Connection failed (${response.status}). Please check the URL and try again.` 
      };
    }
    
    const userData = await response.json();
    console.log('[CareerCopilot AI] Profile fetched successfully');
    return { data: userData };
    
  } catch (error) {
    console.error('[CareerCopilot AI] Error fetching profile:', error);
    
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return { 
        error: 'Could not reach CareerCopilot AI. Please check the URL and your internet connection.' 
      };
    }
    
    return { error: error.message || 'Connection failed. Please try again.' };
  }
}

// Track submission API call (runs in background with cookie access)
async function handleFetchAutofill(apiUrl, jobUrl) {
  try {
    const sessionCookie = await chrome.cookies.get({
      url: apiUrl,
      name: 'session_token'
    });
    
    if (!sessionCookie) {
      return { error: 'Session expired. Please sign in to CareerCopilot AI and reconnect.' };
    }
    
    const response = await fetch(`${apiUrl}/api/extension/autofill-data?job_url=${encodeURIComponent(jobUrl || '')}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': `session_token=${sessionCookie.value}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        return { error: 'Session expired. Please sign in to CareerCopilot AI and reconnect.' };
      }
      return { error: `Failed to fetch profile data (${response.status}).` };
    }
    
    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error.message || 'Failed to fetch profile data.' };
  }
}

// Track submission API call (runs in background with cookie access)
async function handleTrackSubmission(data) {
  console.log('[CareerCopilot AI] Tracking submission:', data);
  
  try {
    const stored = await chrome.storage.local.get([STORAGE_KEYS.API_URL]);
    const apiUrl = stored[STORAGE_KEYS.API_URL];
    
    if (!apiUrl) {
      return { success: false, message: 'Not connected to CareerCopilot AI' };
    }
    
    // Get session cookie
    const sessionCookie = await chrome.cookies.get({
      url: apiUrl,
      name: 'session_token'
    });
    
    if (!sessionCookie) {
      return { success: false, message: 'Session expired. Please reconnect.' };
    }
    
    const response = await fetch(`${apiUrl}/api/extension/track-submission`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_token=${sessionCookie.value}`
      },
      body: JSON.stringify({
        job_url: data.job_url,
        job_title: data.job_title,
        company: data.company
      })
    });
    
    if (!response.ok) {
      return { success: false, message: 'Failed to track submission' };
    }
    
    const result = await response.json();
    return result;
    
  } catch (error) {
    console.error('[CareerCopilot AI] Error tracking submission:', error);
    return { success: false, message: error.message };
  }
}

// Update badge when on pages with forms
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Skip chrome:// and other internal pages
    if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || tab.url.startsWith('about:')) {
      chrome.action.setBadgeText({ tabId, text: '' });
      return;
    }
    
    const isKnownATS = checkIfKnownATS(tab.url);
    
    if (isKnownATS) {
      // Known ATS - green checkmark
      chrome.action.setBadgeText({ tabId, text: '✓' });
      chrome.action.setBadgeBackgroundColor({ tabId, color: '#10b981' });
    } else {
      // For other sites, check if there's a form
      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId },
          func: () => {
            const hasForm = document.querySelector('form, input[type="email"], input[type="file"]');
            return !!hasForm;
          }
        });
        
        if (results?.[0]?.result) {
          // Has form - show blue dot
          chrome.action.setBadgeText({ tabId, text: '●' });
          chrome.action.setBadgeBackgroundColor({ tabId, color: '#6366f1' });
        } else {
          chrome.action.setBadgeText({ tabId, text: '' });
        }
      } catch (e) {
        // Can't inject script (e.g., restricted page)
        chrome.action.setBadgeText({ tabId, text: '' });
      }
    }
  }
});

function checkIfKnownATS(url) {
  const knownPatterns = [
    /boards\.greenhouse\.io/i,
    /jobs\.greenhouse\.io/i,
    /jobs\.lever\.co/i,
    /jobs\.ashbyhq\.com/i,
    /apply\.workable\.com/i,
    /careers\.smartrecruiters\.com/i,
    /\.pinpointhq\.com/i,
    /\.bamboohr\.com/i,
    /\.teamtailor\.com/i,
    /\.jobvite\.com/i,
    /\.myworkdayjobs\.com/i,
    /\.taleo\.net/i,
    /\.icims\.com/i,
    /\.randstad\.ca/i,
    /\.randstad\.com/i
  ];
  
  return knownPatterns.some(pattern => pattern.test(url));
}

console.log('[MyCareerCoPilot] Background service worker loaded');
