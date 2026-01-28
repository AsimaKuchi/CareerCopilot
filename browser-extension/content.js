// JobMatch AI Browser Extension - Content Script
// Runs on job application pages to handle auto-fill

console.log('JobMatch AI Auto-Fill Extension loaded');

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'autofill') {
    performAutoFill(message.data);
    sendResponse({ success: true });
  }
  return true;
});

// Main auto-fill function
function performAutoFill(data) {
  console.log('JobMatch AI: Starting auto-fill...');
  
  const results = {
    filled: [],
    failed: []
  };

  // Helper: Fill input field
  function fillInput(selectors, value, fieldName) {
    if (!value) return false;
    
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        if (el && isVisible(el)) {
          el.value = value;
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          el.dispatchEvent(new Event('blur', { bubbles: true }));
          results.filled.push(fieldName);
          console.log(`✓ Filled ${fieldName}:`, selector);
          return true;
        }
      }
    }
    return false;
  }

  // Helper: Fill textarea
  function fillTextArea(selectors, value, fieldName) {
    if (!value) return false;
    
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        if (el && isVisible(el)) {
          el.value = value;
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          results.filled.push(fieldName);
          console.log(`✓ Filled ${fieldName}:`, selector);
          return true;
        }
      }
    }
    return false;
  }

  // Helper: Check if element is visible
  function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  // Fill First Name
  fillInput([
    'input[name="first_name"]',
    'input[name="firstName"]',
    'input[id*="first_name" i]',
    'input[id*="firstname" i]',
    'input[autocomplete="given-name"]',
    'input[placeholder*="First" i]',
    'input[aria-label*="First" i]',
    '#first_name',
    '.first-name input'
  ], data.firstName, 'First Name');

  // Fill Last Name
  fillInput([
    'input[name="last_name"]',
    'input[name="lastName"]',
    'input[id*="last_name" i]',
    'input[id*="lastname" i]',
    'input[autocomplete="family-name"]',
    'input[placeholder*="Last" i]',
    'input[aria-label*="Last" i]',
    '#last_name',
    '.last-name input'
  ], data.lastName, 'Last Name');

  // Fill Email
  fillInput([
    'input[name="email"]',
    'input[type="email"]',
    'input[id*="email" i]',
    'input[autocomplete="email"]',
    'input[placeholder*="email" i]',
    'input[aria-label*="email" i]',
    '#email'
  ], data.email, 'Email');

  // Fill Phone
  fillInput([
    'input[name="phone"]',
    'input[type="tel"]',
    'input[id*="phone" i]',
    'input[autocomplete="tel"]',
    'input[placeholder*="phone" i]',
    'input[aria-label*="phone" i]',
    '#phone'
  ], data.phone, 'Phone');

  // Fill LinkedIn
  fillInput([
    'input[name*="linkedin" i]',
    'input[id*="linkedin" i]',
    'input[placeholder*="linkedin" i]',
    'input[aria-label*="linkedin" i]'
  ], data.linkedin, 'LinkedIn');

  // Fill Cover Letter
  fillTextArea([
    'textarea[name*="cover" i]',
    'textarea[id*="cover" i]',
    'textarea[placeholder*="cover" i]',
    'textarea[aria-label*="cover" i]',
    'textarea[name*="letter" i]',
    '#cover_letter',
    '.cover-letter textarea',
    'textarea[data-field="cover_letter"]'
  ], data.coverLetter, 'Cover Letter');

  // Fill Resume text (if there's a textarea for it)
  fillTextArea([
    'textarea[name*="resume" i]',
    'textarea[id*="resume" i]',
    'textarea[placeholder*="summary" i]',
    'textarea[aria-label*="summary" i]',
    '#resume_text'
  ], data.resume, 'Resume/Summary');

  // Try to detect and handle file upload for resume
  const fileInputs = document.querySelectorAll('input[type="file"]');
  if (fileInputs.length > 0) {
    console.log('📎 File upload field detected - please upload your resume .docx manually');
    showNotification('Please upload your resume file manually', 'info');
  }

  // Show completion notification
  const filledCount = results.filled.length;
  if (filledCount > 0) {
    showNotification(`Auto-fill complete! Filled ${filledCount} field(s)`, 'success');
    highlightFilledFields();
  } else {
    showNotification('Could not detect form fields. Please fill manually.', 'warning');
  }

  console.log('JobMatch AI: Auto-fill complete', results);
  return results;
}

// Show notification overlay
function showNotification(message, type = 'info') {
  // Remove existing notification
  const existing = document.getElementById('jobmatch-notification');
  if (existing) existing.remove();

  const notification = document.createElement('div');
  notification.id = 'jobmatch-notification';
  notification.className = `jobmatch-notification jobmatch-notification-${type}`;
  notification.innerHTML = `
    <div class="jobmatch-notification-content">
      <strong>JobMatch AI</strong>
      <p>${message}</p>
    </div>
    <button class="jobmatch-notification-close">&times;</button>
  `;

  document.body.appendChild(notification);

  // Close button
  notification.querySelector('.jobmatch-notification-close').onclick = () => {
    notification.remove();
  };

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.classList.add('jobmatch-notification-fade');
      setTimeout(() => notification.remove(), 300);
    }
  }, 5000);
}

// Briefly highlight filled fields
function highlightFilledFields() {
  const inputs = document.querySelectorAll('input, textarea');
  inputs.forEach(input => {
    if (input.value && input.value.length > 0) {
      input.style.transition = 'box-shadow 0.3s';
      input.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.5)';
      setTimeout(() => {
        input.style.boxShadow = '';
      }, 2000);
    }
  });
}

// Add floating button on supported pages
function addFloatingButton() {
  if (document.getElementById('jobmatch-float-btn')) return;

  const btn = document.createElement('button');
  btn.id = 'jobmatch-float-btn';
  btn.className = 'jobmatch-float-btn';
  btn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>
    <span>Auto-Fill</span>
  `;
  btn.title = 'JobMatch AI Auto-Fill';
  
  btn.onclick = async () => {
    btn.disabled = true;
    btn.innerHTML = '<span class="jobmatch-spinner"></span> Loading...';
    
    try {
      const response = await fetch('https://careerfit-30.preview.emergentagent.com/api/autofill/data?url=' + encodeURIComponent(window.location.href), {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        performAutoFill(data);
      } else if (response.status === 401) {
        showNotification('Please log in to JobMatch AI first', 'warning');
        window.open('https://careerfit-30.preview.emergentagent.com', '_blank');
      } else {
        showNotification('Could not load your data. Please try again.', 'error');
      }
    } catch (error) {
      console.error('JobMatch AI error:', error);
      showNotification('Connection error. Please try again.', 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
      </svg>
      <span>Auto-Fill</span>
    `;
  };

  document.body.appendChild(btn);
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addFloatingButton);
} else {
  addFloatingButton();
}
