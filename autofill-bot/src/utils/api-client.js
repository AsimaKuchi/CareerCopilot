/**
 * API Client for AutoFill Bot
 * 
 * Handles all communication with the JobMatch API.
 */

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

const API_BASE_URL = process.env.API_BASE_URL || 'https://job-autofill-2.preview.emergentagent.com';
const SESSION_TOKEN = process.env.SESSION_TOKEN;

/**
 * Make an authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add auth if we have a token
  if (SESSION_TOKEN) {
    headers['Cookie'] = `session_token=${SESSION_TOKEN}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText}`);
  }

  return response.json();
}

/**
 * Fetch the autofill payload for an application
 * 
 * GET /api/applications/{application_id}/autofill-payload
 */
async function fetchAutofillPayload(applicationId) {
  if (!SESSION_TOKEN) {
    throw new Error('SESSION_TOKEN is required. Set it in .env file.');
  }

  return apiRequest(`/api/applications/${applicationId}/autofill-payload`);
}

/**
 * Prepare a document for download (generates DOCX on-demand)
 * 
 * POST /api/applications/{application_id}/prepare-download/{type}
 * type: 'resume' or 'cover-letter'
 */
async function prepareDocumentDownload(applicationId, type) {
  if (!SESSION_TOKEN) {
    throw new Error('SESSION_TOKEN is required for document download.');
  }

  return apiRequest(`/api/applications/${applicationId}/prepare-download/${type}`, {
    method: 'POST',
  });
}

/**
 * Download a file from the API
 * 
 * Some endpoints require auth (like /api/profile/resume/download/original)
 * Others are public (like /api/static-downloads/*)
 */
async function downloadFile(downloadUrl, filename) {
  // Create downloads directory
  const downloadsDir = path.join(__dirname, '..', '..', 'downloads');
  if (!fs.existsSync(downloadsDir)) {
    fs.mkdirSync(downloadsDir, { recursive: true });
  }

  // Full URL
  const fullUrl = downloadUrl.startsWith('http') 
    ? downloadUrl 
    : `${API_BASE_URL}${downloadUrl}`;

  // Build headers - include auth for API endpoints
  const headers = {};
  if (downloadUrl.includes('/api/') && !downloadUrl.includes('/static-downloads/')) {
    if (SESSION_TOKEN) {
      headers['Authorization'] = `Bearer ${SESSION_TOKEN}`;
      headers['Cookie'] = `session_token=${SESSION_TOKEN}`;
    }
  }

  const response = await fetch(fullUrl, { headers, redirect: 'follow' });
  
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }

  const buffer = await response.buffer();
  const filePath = path.join(downloadsDir, filename);
  
  fs.writeFileSync(filePath, buffer);
  
  return filePath;
}

/**
 * Update application status after fill
 * 
 * PUT /api/applications/{application_id}/status
 */
async function updateApplicationStatus(applicationId, status, metadata = {}) {
  return apiRequest(`/api/applications/${applicationId}/status`, {
    method: 'PUT',
    body: JSON.stringify({ status, ...metadata }),
  });
}

module.exports = {
  apiRequest,
  fetchAutofillPayload,
  prepareDocumentDownload,
  downloadFile,
  updateApplicationStatus,
  API_BASE_URL,
};
