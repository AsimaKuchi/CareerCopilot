// Verify popup.js aggregateFrameResults handles multi-frame scenarios correctly.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Load popup.js source and evaluate only the aggregation function.
const popupSrc = fs.readFileSync(path.join(__dirname, '..', 'popup.js'), 'utf8');

// Extract aggregateFrameResults + updateProgress by executing in a sandbox
// that mocks document/chrome so top-level code doesn't crash.
const sandbox = {
  document: { addEventListener: () => {}, getElementById: () => ({ addEventListener: () => {} }) },
  chrome: { storage: { local: { get: () => Promise.resolve({}), set: () => {} } }, tabs: {}, scripting: {}, runtime: {} },
  console
};
vm.createContext(sandbox);
try {
  vm.runInContext(popupSrc, sandbox);
} catch (e) {
  // top-level errors are fine as long as aggregateFrameResults gets defined
}

const agg = sandbox.aggregateFrameResults;
if (typeof agg !== 'function') {
  console.error('aggregateFrameResults not defined');
  process.exit(1);
}

// Scenario 1: Two frames — top has no form, iframe has form and successfully filled
const scenario1 = agg([
  { result: { frameHadForm: false, filled: [], failed: [], skipped: [] } }, // top frame (Lyft careers)
  { result: { frameHadForm: true, filled: ['First Name', 'Email', 'Resume (Optimized for this job)'], failed: [], skipped: [] } } // greenhouse iframe
]);

console.log('Scenario 1 (Lyft outer + Greenhouse iframe):');
console.log('  filled:', scenario1.filled);
console.log('  skipped:', scenario1.skipped);
console.log('  failed:', scenario1.failed);
console.log('  success:', scenario1.success);

if (scenario1.filled.length !== 3) { console.error('FAIL: expected 3 filled'); process.exit(1); }
if (scenario1.skipped.length !== 0) { console.error('FAIL: expected 0 skipped'); process.exit(1); }
if (!scenario1.success) { console.error('FAIL: expected success=true'); process.exit(1); }
console.log('  ✓ PASS');

// Scenario 2: File uploaded in one frame; another frame reports "no file input" -> suppressed
const scenario2 = agg([
  { result: { frameHadForm: true, filled: ['Resume (Optimized for this job)'], failed: [], skipped: ['Cover Letter (no file input)'] } },
  { result: { frameHadForm: true, filled: ['Cover Letter (Optimized for this job)'], failed: [], skipped: ['Resume (no file input)'] } }
]);

console.log('\nScenario 2 (split frames — file uploads across):');
console.log('  filled:', scenario2.filled);
console.log('  skipped:', scenario2.skipped);

// Both resume and cover letter were filled somewhere, skipped duplicates should be suppressed
if (scenario2.skipped.length !== 0) {
  console.error(`FAIL: expected skipped to be empty (suppressed by filled), got ${JSON.stringify(scenario2.skipped)}`);
  process.exit(1);
}
console.log('  ✓ PASS (redundant "no file input" skipped entries suppressed)');

// Scenario 3: No frame has a form -> "No form fields detected"
const scenario3 = agg([
  { result: { frameHadForm: false, filled: [], failed: [], skipped: [] } }
]);
console.log('\nScenario 3 (no frame has form):');
console.log('  failed:', scenario3.failed);
if (!scenario3.failed.includes('No form fields detected on this page')) {
  console.error('FAIL: expected "No form fields detected" message');
  process.exit(1);
}
console.log('  ✓ PASS');

// Scenario 4: Frames returning null (executeScript can return null for restricted frames)
const scenario4 = agg([
  { result: null },
  { result: { frameHadForm: true, filled: ['First Name'], failed: [], skipped: [] } }
]);
console.log('\nScenario 4 (null frame + valid frame):');
console.log('  filled:', scenario4.filled);
if (scenario4.filled.length !== 1 || !scenario4.success) {
  console.error('FAIL: null frames should be ignored');
  process.exit(1);
}
console.log('  ✓ PASS');

console.log('\n✅ All aggregation tests passed.');
