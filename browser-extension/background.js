// JobMatch AI - Background Service Worker

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
    chrome.storage.local.get(['jobmatch_api_url', 'jobmatch_user_data'], (result) => {
      sendResponse(result);
    });
    return true;
  }
  
  if (message.action === 'OPEN_OPTIONS') {
    chrome.runtime.openOptionsPage();
  }
});

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
