// JobMatch AI Browser Extension - Background Service Worker

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('JobMatch AI Extension installed');
    // Open welcome page
    chrome.tabs.create({
      url: 'https://careerwise-7.preview.emergentagent.com?extension=installed'
    });
  }
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'openJobMatch') {
    chrome.tabs.create({
      url: 'https://careerwise-7.preview.emergentagent.com'
    });
  }
  return true;
});
