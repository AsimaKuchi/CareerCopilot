// Regression test for the "Could not connect" bug where the user typed
// "mycareercopilot.ca" without a protocol. Extension now auto-prepends
// https://, validates via URL(), reflects the corrected URL back into the
// input, and shows a helpful error citing the hostname on network failure.

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { JSDOM } = require('jsdom');

function assert(cond, msg) { if (!cond) { console.error('FAIL:', msg); process.exit(1); } }

(async () => {
  const popupSrc = fs.readFileSync(path.join(__dirname, '..', 'popup.js'), 'utf8');
  const popupHtml = fs.readFileSync(path.join(__dirname, '..', 'popup.html'), 'utf8');

  const dom = new JSDOM(popupHtml, {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
    url: 'chrome-extension://fake/popup.html'
  });
  const { window } = dom;

  // Track fetches so we can assert on what URL was actually hit.
  const fetchCalls = [];
  const fetchImpl = async (url, opts) => {
    fetchCalls.push({ url, opts });
    // Emulate the real backend: 200 { status: 'healthy' } for /api/health on
    // valid https URLs, TypeError for anything malformed.
    if (typeof url !== 'string') throw new TypeError('Failed to fetch');
    if (!/^https?:\/\//.test(url)) throw new TypeError('Failed to fetch: invalid URL');
    if (/\/api\/health$/.test(url) && url.startsWith('https://mycareercopilot.ca')) {
      return {
        ok: true, status: 200,
        json: async () => ({ status: 'healthy' })
      };
    }
    if (/\/api\/health$/.test(url) && url.startsWith('https://')) {
      return { ok: true, status: 200, json: async () => ({ status: 'healthy' }) };
    }
    return { ok: false, status: 404 };
  };
  window.fetch = fetchImpl;

  // Chrome API stubs — background handler resolves immediately with
  // fake user data so we can reach the end of handleConnect().
  window.chrome = {
    storage: { local: {
      get: () => Promise.resolve({}),
      set: () => Promise.resolve(),
      remove: () => Promise.resolve()
    } },
    tabs: { query: async () => [{ id: 1, url: 'https://example.com' }], sendMessage: async () => ({}), create: () => {} },
    scripting: { executeScript: async () => [{ result: false }] },
    runtime: {
      sendMessage: (msg, cb) => {
        // Simulate FETCH_PROFILE succeeding
        if (msg?.action === 'FETCH_PROFILE') {
          setTimeout(() => cb({ data: { full_name: 'Test User', email: 't@x.com' } }), 5);
        }
      },
      lastError: null,
      onMessage: { addListener: () => {} }
    }
  };

  vm.runInContext(popupSrc, dom.getInternalVMContext());

  // Trigger DOMContentLoaded so popup wires up the elements + handlers.
  window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 30));

  const apiInput = window.document.getElementById('apiUrl');
  const connectBtn = window.document.getElementById('connectBtn');
  const loginError = window.document.getElementById('loginError');
  assert(apiInput, 'apiUrl input exists');
  assert(connectBtn, 'connectBtn exists');
  assert(loginError, 'loginError element exists');

  // ---- Test 1: bare domain "mycareercopilot.ca" — the exact user scenario
  fetchCalls.length = 0;
  apiInput.value = 'mycareercopilot.ca';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 200));

  const hit = fetchCalls.find(c => c.url.endsWith('/api/health'));
  assert(hit, `expected /api/health to be called, got: ${JSON.stringify(fetchCalls)}`);
  assert(
    hit.url === 'https://mycareercopilot.ca/api/health',
    `expected fetch to https://mycareercopilot.ca/api/health, got ${hit.url}`
  );
  assert(
    apiInput.value === 'https://mycareercopilot.ca',
    `expected input to be normalised to https://mycareercopilot.ca, got "${apiInput.value}"`
  );
  console.log('PASS: bare domain "mycareercopilot.ca" auto-prepends https:// and connects');

  // ---- Test 2: user pastes with trailing slash "https://mycareercopilot.ca/"
  fetchCalls.length = 0;
  apiInput.value = 'https://mycareercopilot.ca/';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 200));
  const hit2 = fetchCalls.find(c => c.url.endsWith('/api/health'));
  assert(hit2.url === 'https://mycareercopilot.ca/api/health', `trailing slash not stripped: ${hit2.url}`);
  console.log('PASS: trailing slash stripped correctly');

  // ---- Test 3: user pastes with "/api" root by mistake
  fetchCalls.length = 0;
  apiInput.value = 'https://mycareercopilot.ca/api';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 200));
  const hit3 = fetchCalls.find(c => c.url.endsWith('/api/health'));
  assert(hit3.url === 'https://mycareercopilot.ca/api/health', `/api suffix not stripped: ${hit3.url}`);
  console.log('PASS: trailing /api suffix stripped');

  // ---- Test 4: totally malformed URL — should error out cleanly without hitting fetch
  fetchCalls.length = 0;
  loginError.classList.remove('active');
  loginError.textContent = '';
  apiInput.value = 'not a url at all';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 200));
  const errShown = loginError.classList.contains('active') && loginError.textContent.length > 0;
  assert(errShown, `garbage input should show a visible error, got: active=${loginError.classList.contains('active')} text="${loginError.textContent}"`);
  console.log(`PASS: garbage input shows helpful error ("${loginError.textContent.slice(0, 80)}...")`);

  // ---- Test 5: pre-existing https:// URL is untouched (idempotent)
  fetchCalls.length = 0;
  apiInput.value = 'https://mycareercopilot.ca';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 200));
  assert(apiInput.value === 'https://mycareercopilot.ca', `normalised URL should be idempotent, got "${apiInput.value}"`);
  const hit5 = fetchCalls.find(c => c.url.endsWith('/api/health'));
  assert(hit5.url === 'https://mycareercopilot.ca/api/health', 'unchanged https URL should fetch as-is');
  console.log('PASS: already-normalised https URL is idempotent');

  // ---- Test 6: unreachable host produces a helpful error containing hostname
  fetchCalls.length = 0;
  // Override fetch to simulate a network failure
  window.fetch = async (url) => {
    fetchCalls.push({ url });
    throw new TypeError('Failed to fetch');
  };
  loginError.classList.remove('active');
  loginError.textContent = '';
  apiInput.value = 'typo-domain-that-does-not-exist.ca';
  connectBtn.click();
  await new Promise(r => setTimeout(r, 250));
  assert(
    loginError.classList.contains('active') && loginError.textContent.length > 0,
    'error message should be shown for unreachable host'
  );
  assert(
    /typo-domain-that-does-not-exist\.ca/.test(loginError.textContent),
    `error message should mention the hostname; got: "${loginError.textContent}"`
  );
  console.log('PASS: unreachable host error message includes the hostname');

  console.log('\n✅ All URL normalization tests passed.');
})().catch(e => { console.error('CRASH:', e); process.exit(1); });
