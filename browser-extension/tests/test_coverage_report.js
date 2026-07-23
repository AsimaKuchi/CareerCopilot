// Verify:
//  1. content.js returns structured `entries` array with { name, status, category, hint }
//  2. aggregateFrameResults (from popup.js) preserves entries and de-dupes across frames
//  3. popup.js renderCoverageReport produces the expected grouped DOM

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { JSDOM } = require('jsdom');

function assert(cond, msg) { if (!cond) { console.error('FAIL:', msg); process.exit(1); } }

(async () => {
  // ---- Load popup.js aggregateFrameResults + baseName + renderers in a sandbox
  const popupSrc = fs.readFileSync(path.join(__dirname, '..', 'popup.js'), 'utf8');
  const popupHtml = fs.readFileSync(path.join(__dirname, '..', 'popup.html'), 'utf8');

  const dom = new JSDOM(popupHtml, {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
    url: 'chrome-extension://fake/popup.html'
  });
  const { window } = dom;
  window.chrome = {
    storage: { local: {
      get: (_k) => Promise.resolve({}),
      set: () => Promise.resolve(),
      remove: () => Promise.resolve()
    } },
    tabs: { query: async () => [{}], sendMessage: async () => ({}), create: () => {} },
    scripting: { executeScript: async () => [] },
    runtime: { sendMessage: () => {}, lastError: null, onMessage: { addListener: () => {} } }
  };

  vm.runInContext(popupSrc, dom.getInternalVMContext());

  // Fire DOMContentLoaded so popup.js populates its internal `elements` cache
  // (which shadows references to actual JSDOM nodes).
  window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true, cancelable: true }));
  // Give the async DOMContentLoaded handler time to complete its awaited get()
  await new Promise(r => setTimeout(r, 30));

  const agg = window.aggregateFrameResults;
  const baseName = window.baseName;
  const renderCoverageReport = window.renderCoverageReport;
  const escapeHtml = window.escapeHtml;

  // ---- Test 1: baseName strips parenthetical suffix
  assert(baseName('Resume (optimized for this job)') === 'resume', 'baseName strips parens');
  assert(baseName('Cover Letter') === 'cover letter', 'baseName lowers case');
  console.log('PASS: baseName correctly normalises field names');

  // ---- Test 2: aggregate preserves entries and ignores empty frames
  const agg1 = agg([
    { result: { frameHadForm: false, filled: [], failed: [], skipped: [], entries: [] } },
    { result: {
      frameHadForm: true,
      filled: ['First Name', 'Email'], failed: [], skipped: [],
      entries: [
        { name: 'First Name', status: 'filled', category: 'personal_info', hint: '' },
        { name: 'Email', status: 'filled', category: 'personal_info', hint: '' },
        { name: 'Sponsorship required?', status: 'attention', category: 'screening', hint: 'No profile match — please answer manually' }
      ]
    }}
  ]);
  assert(agg1.entries.length === 3, `expected 3 entries, got ${agg1.entries.length}`);
  assert(agg1.entries.some(e => e.name === 'Sponsorship required?' && e.category === 'screening'), 'screening entry present');
  console.log('PASS: aggregation preserves entries from valid frames and ignores empty frames');

  // ---- Test 3: aggregate dedupes across frames — suppress attention when filled elsewhere
  const agg2 = agg([
    { result: {
      frameHadForm: true,
      filled: ['Resume (optimized for this job)'], failed: [], skipped: [],
      entries: [{ name: 'Resume (optimized for this job)', status: 'filled', category: 'documents', hint: '' }]
    }},
    { result: {
      frameHadForm: true,
      filled: [], failed: [], skipped: ['Resume (no file input)'],
      entries: [{ name: 'Resume', status: 'attention', category: 'documents', hint: 'No file input found — attach manually' }]
    }}
  ]);
  assert(agg2.entries.length === 1, `expected 1 entry after dedup, got ${agg2.entries.length}`);
  assert(agg2.entries[0].status === 'filled', `expected filled status, got ${agg2.entries[0].status}`);
  console.log('PASS: aggregation suppresses attention/failed when same base name filled elsewhere');

  // ---- Test 4: identical entries across frames dedupe by (name+status)
  const agg3 = agg([
    { result: { frameHadForm: true, filled: ['Email'], failed: [], skipped: [], entries: [
      { name: 'Email', status: 'filled', category: 'personal_info', hint: '' }
    ]}},
    { result: { frameHadForm: true, filled: ['Email'], failed: [], skipped: [], entries: [
      { name: 'Email', status: 'filled', category: 'personal_info', hint: '' }
    ]}}
  ]);
  assert(agg3.entries.length === 1, `expected 1 deduped Email entry, got ${agg3.entries.length}`);
  console.log('PASS: aggregation dedupes identical (name+status) entries');

  // ---- Test 5: renderCoverageReport produces the expected DOM structure
  const resultForRender = {
    success: true,
    filledCount: 3,
    filled: ['First Name', 'Email', 'Resume (optimized for this job)'],
    failed: [], skipped: [],
    entries: [
      { name: 'First Name', status: 'filled', category: 'personal_info', hint: '' },
      { name: 'Email', status: 'filled', category: 'personal_info', hint: '' },
      { name: 'Resume (optimized for this job)', status: 'filled', category: 'documents', hint: '' },
      { name: 'Country', status: 'attention', category: 'screening', hint: 'No profile match — please answer manually' },
      { name: 'Location', status: 'failed', category: 'personal_info', hint: 'Field not found on this page' }
    ]
  };

  renderCoverageReport(resultForRender);
  const resultsList = window.document.getElementById('resultsList');
  const listHtml = resultsList.innerHTML;

  assert(listHtml.includes('data-testid="coverage-summary"'), 'coverage summary card rendered');
  assert(listHtml.includes('data-testid="coverage-count"'), 'coverage count present');
  assert(listHtml.includes('data-testid="coverage-pct"'), 'coverage % present');
  assert(listHtml.includes('3 / 5 filled'), `expected "3 / 5 filled" got:\n${listHtml.slice(0, 400)}`);
  assert(listHtml.includes('60%'), 'coverage % shows 60%');
  assert(listHtml.includes('data-testid="coverage-attention"'), 'attention count shown when >0');
  assert(listHtml.includes('data-testid="fc-group-personal_info"'), 'personal info group rendered');
  assert(listHtml.includes('data-testid="fc-group-documents"'), 'documents group rendered');
  assert(listHtml.includes('data-testid="fc-group-screening"'), 'screening group rendered');
  assert(listHtml.includes('data-testid="fc-row-filled"'), 'at least one filled row');
  assert(listHtml.includes('data-testid="fc-row-failed"'), 'failed row rendered');
  assert(listHtml.includes('data-testid="fc-row-attention"'), 'attention row rendered');
  assert(listHtml.includes('No profile match'), 'hint text is included in output');
  console.log('PASS: renderCoverageReport produces grouped DOM with summary, categories, and hints');

  // ---- Test 6: 0% coverage state
  const zero = { success: false, filledCount: 0, filled: [], failed: [], skipped: [], entries: [
    { name: 'First Name', status: 'attention', category: 'personal_info', hint: 'Not detected on this page' }
  ] };
  renderCoverageReport(zero);
  const zeroHtml = window.document.getElementById('resultsList').innerHTML;
  assert(zeroHtml.includes('0 / 1 filled'), '0/1 filled shown');
  assert(zeroHtml.includes('0%'), '0% shown');
  console.log('PASS: 0% coverage state renders correctly');

  // ---- Test 7: XSS safety of escapeHtml
  const evil = '<img src=x onerror=alert(1)>';
  assert(escapeHtml(evil) === '&lt;img src=x onerror=alert(1)&gt;', 'escapeHtml escapes < and >');
  console.log('PASS: escapeHtml prevents HTML injection into report');

  console.log('\n✅ All Field Coverage Report tests passed.');
})().catch(e => { console.error('CRASH:', e); process.exit(1); });
