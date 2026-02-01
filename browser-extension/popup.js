// JobMatch AI Browser Extension - Popup Script

const API_BASE = 'https://quality-jobs.preview.emergentagent.com/api';

// Check connection status and load application data
async function init() {
  const statusEl = document.getElementById('status');
  const appInfoEl = document.getElementById('app-info');
  const jobTitleEl = document.getElementById('job-title');
  const companyEl = document.getElementById('company-name');
  const autofillBtn = document.getElementById('autofill-btn');
  const settingsBtn = document.getElementById('settings-btn');

  // Get current tab URL
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const currentUrl = tab?.url || '';

  // Check if on a supported job application page
  const isJobPage = currentUrl.includes('greenhouse.io') || 
                    currentUrl.includes('lever.co') ||
                    currentUrl.includes('workday.com');

  if (!isJobPage) {
    statusEl.className = 'status disconnected';
    statusEl.innerHTML = '⚠️ Not on a job application page';
    autofillBtn.disabled = true;
    return;
  }

  // Try to fetch user data from JobMatch AI
  try {
    const response = await fetch(`${API_BASE}/autofill/data?url=${encodeURIComponent(currentUrl)}`, {
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      
      statusEl.className = 'status connected';
      statusEl.innerHTML = '✓ Connected to JobMatch AI';
      
      if (data.hasApplication) {
        appInfoEl.classList.remove('hidden');
        jobTitleEl.textContent = data.jobTitle || 'Application Ready';
        companyEl.textContent = data.company || 'Tailored resume & cover letter loaded';
      }
      
      autofillBtn.disabled = false;
      autofillBtn.onclick = () => triggerAutoFill(tab.id, data);
      
    } else if (response.status === 401) {
      statusEl.className = 'status disconnected';
      statusEl.innerHTML = '🔒 Please log in to JobMatch AI first';
      autofillBtn.textContent = 'Open JobMatch AI';
      autofillBtn.disabled = false;
      autofillBtn.onclick = () => {
        chrome.tabs.create({ url: 'https://quality-jobs.preview.emergentagent.com' });
      };
    } else {
      throw new Error('Failed to fetch data');
    }
  } catch (error) {
    console.error('Error:', error);
    statusEl.className = 'status disconnected';
    statusEl.innerHTML = '❌ Could not connect to JobMatch AI';
    autofillBtn.disabled = true;
  }

  // Settings button
  settingsBtn.onclick = () => {
    chrome.tabs.create({ url: 'https://quality-jobs.preview.emergentagent.com/profile' });
  };
}

// Trigger auto-fill on the current page
async function triggerAutoFill(tabId, data) {
  const autofillBtn = document.getElementById('autofill-btn');
  autofillBtn.disabled = true;
  autofillBtn.innerHTML = '<span class="spinner"></span> Filling...';

  try {
    // Send message to content script to fill the form
    await chrome.tabs.sendMessage(tabId, {
      action: 'autofill',
      data: data
    });

    autofillBtn.innerHTML = '✓ Form Filled!';
    autofillBtn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
    
    setTimeout(() => {
      window.close();
    }, 1500);
    
  } catch (error) {
    console.error('Auto-fill error:', error);
    autofillBtn.innerHTML = '❌ Fill Failed - Try Manual';
    autofillBtn.disabled = false;
    
    setTimeout(() => {
      autofillBtn.innerHTML = 'Auto-Fill Application';
      autofillBtn.style.background = '';
    }, 2000);
  }
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', init);
