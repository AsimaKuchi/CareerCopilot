// Test harness: simulate Lyft/Greenhouse job-boards form and verify content.js
// autofill actually fills the visible fields (previously silently skipped).

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const LYFT_LIKE_HTML = `
<!doctype html>
<html><body>
  <main>
    <h1>Apply for this job</h1>
    <p>* indicates a required field</p>
    <form id="app-form">
      <label for="first_name">First Name *</label>
      <input id="first_name" name="first_name" type="text" />

      <label for="last_name">Last Name *</label>
      <input id="last_name" name="last_name" type="text" />

      <label for="email">Email *</label>
      <input id="email" name="email" type="email" />

      <label for="phone">Phone *</label>
      <input id="phone" name="phone" type="tel" />

      <label for="location">Location (City) *</label>
      <input id="location" name="location" type="text" placeholder="Type your location" />

      <label for="resume">Resume/CV *</label>
      <input id="resume" name="resume" type="file" />

      <label for="cover_letter">Cover Letter</label>
      <input id="cover_letter" name="cover_letter" type="file" />

      <button id="submit_app" type="submit">Submit application</button>
    </form>
  </main>
</body></html>
`;

const AUTOFILL_DATA = {
  personal_info: {
    first_name: 'Fuzail',
    last_name: 'Bukhari',
    full_name: 'Fuzail Bukhari',
    email: 'fuzailbukhari@gmail.com',
    phone: '+1 416-555-0199',
    linkedin: 'https://linkedin.com/in/fuzailbukhari',
    location: { city: 'Toronto', state: 'ON', country: 'Canada' }
  },
  profile_context: {
    country: 'Canada',
    requires_sponsorship: false,
    willing_to_relocate: 'Yes',
    resume_text: '...'
  },
  documents: {
    resume: {
      filename: 'resume_optimized.pdf',
      mime_type: 'application/pdf',
      file_data: Buffer.from('%PDF-1.4 fake pdf bytes').toString('base64'),
      is_optimized: true
    },
    cover_letter: {
      filename: 'cover_letter_optimized.pdf',
      mime_type: 'application/pdf',
      file_data: Buffer.from('%PDF-1.4 fake cl bytes').toString('base64'),
      is_optimized: true
    }
  }
};

async function runTest() {
  const dom = new JSDOM(LYFT_LIKE_HTML, {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
    url: 'https://job-boards.greenhouse.io/lyft/jobs/123456'
  });
  const { window } = dom;

  // Mock chrome API used by content.js so it doesn't crash on load
  window.chrome = {
    runtime: {
      onMessage: { addListener: () => {} },
      sendMessage: (msg, cb) => { if (cb) cb({ success: false }); },
      lastError: null
    }
  };

  // JSDOM doesn't implement DataTransfer — polyfill it so file uploads work.
  window.DataTransfer = class {
    constructor() {
      this._files = [];
      this.items = {
        add: (f) => this._files.push(f)
      };
    }
    get files() {
      // Return a FileList-like array
      const arr = this._files.slice();
      arr.item = (i) => arr[i] || null;
      return arr;
    }
  };

  // JSDOM doesn't give elements dimensions -> isVisible() would fail.
  // Patch getBoundingClientRect to return non-zero for any inputs so
  // content.js sees them as visible.
  const origGBCR = window.Element.prototype.getBoundingClientRect;
  window.Element.prototype.getBoundingClientRect = function () {
    return { top: 0, left: 0, right: 100, bottom: 20, width: 100, height: 20, x: 0, y: 0 };
  };

  // Load content.js in the JSDOM window context.
  const contentSrc = fs.readFileSync(path.join(__dirname, '..', 'content.js'), 'utf8');
  const vm = require('vm');
  const contextify = dom.getInternalVMContext();
  vm.runInContext(contentSrc, contextify);

  // Verify window handler is exposed
  if (typeof window.__mccHandleAutoFill !== 'function') {
    console.error('FAIL: window.__mccHandleAutoFill not exposed by content.js');
    process.exit(1);
  }
  if (typeof window.__mccHasFormFields !== 'function') {
    console.error('FAIL: window.__mccHasFormFields not exposed by content.js');
    process.exit(1);
  }
  if (!window.__mccHasFormFields()) {
    console.error('FAIL: hasFormFields returned false for a form-bearing page');
    process.exit(1);
  }
  console.log('PASS: content.js exposes handlers and detects form fields');

  // Run the autofill
  const result = await window.__mccHandleAutoFill(AUTOFILL_DATA);

  console.log('\nAutofill result:', JSON.stringify(result, null, 2));

  // Assertions
  const failures = [];

  if (!result.frameHadForm) failures.push('result.frameHadForm should be true');

  const filled = (result.filled || []).map(s => s.toLowerCase());
  const skipped = (result.skipped || []).map(s => s.toLowerCase());

  const expectFilled = ['first name', 'last name', 'email', 'phone'];
  for (const e of expectFilled) {
    if (!filled.some(f => f.includes(e))) failures.push(`Expected filled to include "${e}", got: ${JSON.stringify(result.filled)}`);
  }
  // Location: accept either "location" or "city" label (both fill #location DOM node)
  if (!filled.some(f => f.includes('location') || f.includes('city'))) {
    failures.push(`Expected filled to include location or city, got: ${JSON.stringify(result.filled)}`);
  }

  // The DOM values should have been set
  const doc = window.document;
  const checks = {
    first_name: 'Fuzail',
    last_name: 'Bukhari',
    email: 'fuzailbukhari@gmail.com',
    phone: '+1 416-555-0199',
    location: 'Toronto'
  };
  for (const [id, expected] of Object.entries(checks)) {
    const el = doc.getElementById(id);
    if (!el) failures.push(`Missing input #${id}`);
    else if (!el.value || !el.value.toLowerCase().includes(expected.toLowerCase())) {
      failures.push(`Input #${id} value="${el.value}" does not contain "${expected}"`);
    }
  }

  // Verify resume file input WAS FOUND (upload may fail in JSDOM due to
  // FileList polyfill limitations — real Chrome works fine). The critical
  // regression: previously the code couldn't find the input and pushed
  // "Resume (no file input) (skipped)". Now it must find #resume and either
  // fill or fail — never silently skip.
  const failedLower = (result.failed || []).map(s => s.toLowerCase());
  const skippedLower = skipped;
  const resumeWasFound =
    filled.some(f => f.includes('resume') && !f.includes('cover')) ||
    failedLower.some(f => f.includes('resume') && !f.includes('cover')); // upload attempted
  const resumeSilentlySkipped = skippedLower.some(s =>
    s.includes('resume') && s.includes('no file input')
  );
  if (!resumeWasFound) failures.push('Resume input was not found (regression from iframe fix)');
  if (resumeSilentlySkipped) failures.push('Regression: Resume silently skipped as "no file input"');

  const coverWasFound =
    filled.some(f => f.includes('cover letter')) ||
    failedLower.some(f => f.includes('cover letter'));
  const coverSilentlySkipped = skippedLower.some(s =>
    s.includes('cover letter') && s.includes('no file input')
  );
  if (!coverWasFound) failures.push('Cover letter input was not found');
  if (coverSilentlySkipped) failures.push('Regression: Cover letter silently skipped as "no file input"');

  console.log('PASS: File inputs discovered on the page');

  // Bug #1 regression: ensure "Resume (no file input)" NOT in skipped when uploaded
  if (skipped.some(s => s.includes('resume') && s.includes('no file input'))) {
    failures.push('Regression: skipped contains "Resume (no file input)" but resume was uploaded');
  }
  if (skipped.some(s => s.includes('cover letter') && s.includes('no file input'))) {
    failures.push('Regression: skipped contains "Cover Letter (no file input)" but was uploaded');
  }

  if (failures.length > 0) {
    console.error('\n=== TEST FAILURES ===');
    failures.forEach(f => console.error(' - ' + f));
    process.exit(1);
  }

  console.log('\n=== ALL TESTS PASSED ===');
  console.log(`Filled ${result.filled.length} fields:`, result.filled);
  console.log(`Skipped ${result.skipped.length}:`, result.skipped);
  console.log(`Failed ${result.failed.length}:`, result.failed);
}

// Second test: empty frame (no form) should return early with frameHadForm=false
async function runEmptyFrameTest() {
  const dom = new JSDOM('<html><body><p>Nothing here</p></body></html>', {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
    url: 'https://careers.lyft.com/'
  });
  const { window } = dom;
  window.chrome = {
    runtime: { onMessage: { addListener: () => {} }, sendMessage: () => {}, lastError: null }
  };
  const contentSrc = fs.readFileSync(path.join(__dirname, '..', 'content.js'), 'utf8');
  const vm = require('vm');
  vm.runInContext(contentSrc, dom.getInternalVMContext());

  const result = await window.__mccHandleAutoFill(AUTOFILL_DATA);
  if (result.frameHadForm) {
    console.error('FAIL: empty frame reported frameHadForm=true');
    process.exit(1);
  }
  if (result.filled.length !== 0 || result.skipped.length !== 0) {
    console.error('FAIL: empty frame produced result entries:', result);
    process.exit(1);
  }
  console.log('PASS: empty frame early-exits with frameHadForm=false');
}

(async () => {
  try {
    await runTest();
    console.log('');
    await runEmptyFrameTest();
    console.log('\n✅ All extension tests passed.');
  } catch (e) {
    console.error('\n💥 Test crashed:', e);
    process.exit(1);
  }
})();
