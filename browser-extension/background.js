// JobMatch AI - Background Service Worker

const STORAGE_KEYS = {
  API_URL: 'jobmatch_api_url',
  USER_DATA: 'jobmatch_user_data'
};

// Handle installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[JobMatch AI] Extension installed');
  } else if (details.reason === 'update') {
    console.log('[JobMatch AI] Extension updated');
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
    // First, check if we have any cookies for this domain
    const url = new URL(apiUrl);
    const cookies = await chrome.cookies.getAll({ domain: url.hostname });
    
    console.log('[CareerCopilot AI] Found cookies:', cookies.length);
    
    // Make API call with credentials (cookies)
    const response = await fetch(`${apiUrl}/api/profile`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        return { 
          error: 'Please sign in to CareerCopilot AI website first (use "Sign in with Google"), then try connecting again.' 
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
    
    // Provide helpful error messages based on error type
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return { 
        error: 'Could not reach CareerCopilot AI. Please check the URL and your internet connection.' 
      };
    }
    
    return { error: error.message || 'Connection failed. Please try again.' };
  }
}

// Track submission API call (runs in background with cookie access)
async function handleTrackSubmission(data) {
  console.log('[JobMatch AI] Tracking submission:', data);
  
  try {
    // Get stored API URL
    const stored = await chrome.storage.local.get([STORAGE_KEYS.API_URL]);
    const apiUrl = stored[STORAGE_KEYS.API_URL];
    
    if (!apiUrl) {
      console.log('[JobMatch AI] No API URL stored');
      return { success: false, message: 'Not connected to JobMatch AI' };
    }
    
    // Make API call with credentials (cookies)
    const response = await fetch(`${apiUrl}/api/extension/track-submission`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        job_url: data.job_url,
        job_title: data.job_title,
        company: data.company
      })
    });
    
    if (!response.ok) {
      console.log('[JobMatch AI] API returned error:', response.status);
      return { success: false, message: 'Failed to track submission' };
    }
    
    const result = await response.json();
    console.log('[JobMatch AI] Track submission result:', result);
    return result;
    
  } catch (error) {
    console.error('[JobMatch AI] Error tracking submission:', error);
    return { success: false, message: error.message };
  }
}

// Update badge when on supported pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const isSupported = checkIfSupported(tab.url);
    
    if (isSupported) {
      chrome.action.setBadgeText({ tabId, text: '✓' });
      chrome.action.setBadgeBackgroundColor({ tabId, color: '#10b981' });
    } else {
      chrome.action.setBadgeText({ tabId, text: '' });
    }
  }
});

function checkIfSupported(url) {
  const supportedPatterns = [
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
    /\.icims\.com/i
  ];
  
  return supportedPatterns.some(pattern => pattern.test(url));
}

console.log('[JobMatch AI] Background service worker loaded');
