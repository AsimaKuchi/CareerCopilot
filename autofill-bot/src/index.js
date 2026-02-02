/**
 * JobMatch AutoFill Bot
 * 
 * Playwright-based bot for auto-filling job applications on Greenhouse, Lever, and Ashby.
 * Fetches user profile from API and fills form fields with human-in-the-loop confirmation.
 */

const { program } = require('commander');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const { fetchAutofillPayload, prepareDocumentDownload, downloadFile } = require('./utils/api-client');
const { createBrowser, detectATSType } = require('./utils/browser');
const { generateReport, saveReport } = require('./utils/reporter');
const { GreenhouseMapper } = require('./ats-mappers/greenhouse');
const { LeverMapper } = require('./ats-mappers/lever');
const { AshbyMapper } = require('./ats-mappers/ashby');
const { GenericMapper } = require('./ats-mappers/generic');

// CLI Setup
program
  .name('autofill')
  .description('Auto-fill job applications using your saved profile')
  .version('1.0.0')
  .requiredOption('--application_id <id>', 'Application ID to fill')
  .option('--headful', 'Run browser in visible mode (default: true)', true)
  .option('--headless', 'Run browser in headless mode', false)
  .option('--slow-mo <ms>', 'Slow down actions by milliseconds', '100')
  .option('--timeout <ms>', 'Timeout for operations', '30000')
  .option('--skip-screenshots', 'Skip taking screenshots', false)
  .option('--auto-submit', 'Auto-submit after filling (dangerous!)', false)
  .option('--debug', 'Enable debug logging', false)
  .parse(process.argv);

const options = program.opts();

// Logging helpers
const log = {
  info: (msg) => console.log(chalk.blue('ℹ'), msg),
  success: (msg) => console.log(chalk.green('✓'), msg),
  warn: (msg) => console.log(chalk.yellow('⚠'), msg),
  error: (msg) => console.log(chalk.red('✗'), msg),
  debug: (msg) => options.debug && console.log(chalk.gray('⚙'), msg),
  step: (num, msg) => console.log(chalk.cyan(`[${num}]`), msg),
};

// Main execution
async function main() {
  const startTime = Date.now();
  const report = {
    applicationId: options.application_id,
    startedAt: new Date().toISOString(),
    atsType: null,
    atsConfidence: null,
    filledFields: [],
    skippedFields: [],
    confirmRequired: [],
    errors: [],
    screenshots: [],
    duration: null,
    status: 'pending',
  };

  let browser = null;
  let page = null;

  try {
    // Step 1: Fetch autofill payload
    log.step(1, 'Fetching autofill payload from API...');
    const payload = await fetchAutofillPayload(options.application_id);
    
    if (!payload) {
      throw new Error('Failed to fetch autofill payload');
    }

    report.atsType = payload.application.ats_type;
    report.atsConfidence = payload.application.ats_confidence;
    report.confirmRequired = payload.confirm_required || [];

    log.success(`Loaded application: ${payload.application.job_title} at ${payload.application.company}`);
    log.info(`ATS Type: ${payload.application.ats_type} (confidence: ${payload.application.ats_confidence})`);
    log.info(`Apply URL: ${payload.application.apply_url}`);

    // Step 2: Prepare document files if needed
    log.step(2, 'Preparing document files...');
    const documents = await prepareDocuments(payload);
    log.success(`Resume: ${documents.resume.type} | Cover Letter: ${documents.coverLetter.type}`);

    // Step 3: Launch browser
    log.step(3, 'Launching browser...');
    const browserConfig = {
      headless: options.headless && !options.headful,
      slowMo: parseInt(options.slow_mo),
      timeout: parseInt(options.timeout),
    };
    
    const browserResult = await createBrowser(browserConfig);
    browser = browserResult.browser;
    page = browserResult.page;
    log.success('Browser launched');

    // Step 4: Navigate to application URL
    log.step(4, `Navigating to ${payload.application.apply_url}...`);
    await page.goto(payload.application.apply_url, { 
      waitUntil: 'networkidle',
      timeout: parseInt(options.timeout) 
    });
    await page.waitForTimeout(2000); // Wait for dynamic content
    log.success('Page loaded');

    // Take before screenshot
    if (!options.skip_screenshots) {
      const beforeScreenshot = await takeScreenshot(page, 'before-fill');
      report.screenshots.push({ stage: 'before', path: beforeScreenshot });
    }

    // Step 5: Detect ATS type from page (verify API detection)
    log.step(5, 'Verifying ATS type from page structure...');
    const detectedATS = await detectATSType(page, payload.application.apply_url);
    
    if (detectedATS.type !== payload.application.ats_type && detectedATS.confidence === 'high') {
      log.warn(`ATS mismatch: API said ${payload.application.ats_type}, page looks like ${detectedATS.type}`);
      report.atsType = detectedATS.type;
    }
    log.success(`Confirmed ATS: ${report.atsType}`);

    // Step 6: Select appropriate mapper
    log.step(6, 'Selecting ATS mapper...');
    const mapper = selectMapper(report.atsType);
    log.success(`Using ${mapper.name} mapper`);

    // Step 7: Auto-fill the form
    log.step(7, 'Auto-filling form fields...');
    const fillResult = await mapper.fill(page, payload, documents, {
      skipSensitive: true,
      debug: options.debug,
      timeout: parseInt(options.timeout),
    });

    report.filledFields = fillResult.filled;
    report.skippedFields = fillResult.skipped;
    report.errors = fillResult.errors;

    log.success(`Filled ${fillResult.filled.length} fields`);
    if (fillResult.skipped.length > 0) {
      log.warn(`Skipped ${fillResult.skipped.length} fields`);
    }
    if (fillResult.errors.length > 0) {
      log.error(`Encountered ${fillResult.errors.length} errors`);
    }

    // Take after screenshot
    if (!options.skip_screenshots) {
      const afterScreenshot = await takeScreenshot(page, 'after-fill');
      report.screenshots.push({ stage: 'after', path: afterScreenshot });
    }

    // Step 8: Highlight sensitive fields
    log.step(8, 'Highlighting fields requiring confirmation...');
    await highlightSensitiveFields(page, report.confirmRequired);

    // Step 9: Handle submission
    if (options.auto_submit) {
      log.warn('AUTO-SUBMIT enabled - this is dangerous!');
      // We still don't actually submit - just warn
      log.info('Auto-submit is disabled for safety. Please review and submit manually.');
    }

    // Final status
    report.status = 'ready_for_review';
    report.duration = Date.now() - startTime;

    log.success('');
    log.success('═══════════════════════════════════════════════════════════');
    log.success('  AUTO-FILL COMPLETE - READY FOR HUMAN REVIEW');
    log.success('═══════════════════════════════════════════════════════════');
    log.info('');
    log.info(`  Filled: ${report.filledFields.length} fields`);
    log.info(`  Skipped: ${report.skippedFields.length} fields`);
    log.info(`  Needs Confirmation: ${report.confirmRequired.length} fields`);
    log.info(`  Duration: ${(report.duration / 1000).toFixed(2)}s`);
    log.info('');
    log.warn('  ⚠️  Please review all fields before submitting!');
    log.warn('  ⚠️  Check highlighted fields that need your confirmation.');
    log.info('');

    // Save report
    const reportPath = await saveReport(report, options.application_id);
    log.info(`Report saved: ${reportPath}`);

    // Keep browser open for review
    log.info('Browser will stay open for review. Press Ctrl+C to close.');
    
    // Wait indefinitely (user closes manually)
    await new Promise(() => {});

  } catch (error) {
    report.status = 'error';
    report.errors.push({
      type: 'fatal',
      message: error.message,
      stack: error.stack,
    });
    report.duration = Date.now() - startTime;

    log.error(`Fatal error: ${error.message}`);
    if (options.debug) {
      console.error(error.stack);
    }

    // Save error report
    await saveReport(report, options.application_id);

    // Take error screenshot if possible
    if (page && !options.skip_screenshots) {
      try {
        await takeScreenshot(page, 'error');
      } catch (e) {
        // Ignore screenshot errors
      }
    }

    process.exit(1);
  }
}

/**
 * Prepare document files for upload
 */
async function prepareDocuments(payload) {
  const result = {
    resume: { type: 'none', text: null, filePath: null },
    coverLetter: { type: 'none', text: null, filePath: null },
  };

  // Resume
  if (payload.documents?.resume?.text) {
    result.resume.text = payload.documents.resume.text;
    result.resume.type = 'text';
  }

  if (payload.documents?.resume?.file_available) {
    try {
      log.debug('Generating resume DOCX...');
      const prepared = await prepareDocumentDownload(options.application_id, 'resume');
      if (prepared?.download_url) {
        const filePath = await downloadFile(prepared.download_url, prepared.filename);
        result.resume.filePath = filePath;
        result.resume.type = 'file';
        log.debug(`Resume downloaded: ${filePath}`);
      }
    } catch (e) {
      log.warn(`Could not prepare resume file: ${e.message}`);
      // Fall back to text
      result.resume.type = result.resume.text ? 'text' : 'none';
    }
  }

  // Cover Letter
  if (payload.documents?.cover_letter?.text) {
    result.coverLetter.text = payload.documents.cover_letter.text;
    result.coverLetter.type = 'text';
  }

  if (payload.documents?.cover_letter?.file_available) {
    try {
      log.debug('Generating cover letter DOCX...');
      const prepared = await prepareDocumentDownload(options.application_id, 'cover-letter');
      if (prepared?.download_url) {
        const filePath = await downloadFile(prepared.download_url, prepared.filename);
        result.coverLetter.filePath = filePath;
        result.coverLetter.type = 'file';
        log.debug(`Cover letter downloaded: ${filePath}`);
      }
    } catch (e) {
      log.warn(`Could not prepare cover letter file: ${e.message}`);
      result.coverLetter.type = result.coverLetter.text ? 'text' : 'none';
    }
  }

  return result;
}

/**
 * Select the appropriate ATS mapper
 */
function selectMapper(atsType) {
  switch (atsType) {
    case 'greenhouse':
      return new GreenhouseMapper();
    case 'lever':
      return new LeverMapper();
    case 'ashby':
      return new AshbyMapper();
    default:
      log.warn(`Unknown ATS type: ${atsType}, using generic mapper`);
      return new GenericMapper();
  }
}

/**
 * Take a screenshot
 */
async function takeScreenshot(page, name) {
  const screenshotDir = process.env.SCREENSHOT_DIR || './screenshots';
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const filename = `${options.application_id}_${name}_${Date.now()}.png`;
  const filepath = path.join(screenshotDir, filename);
  
  await page.screenshot({ 
    path: filepath, 
    fullPage: true 
  });
  
  return filepath;
}

/**
 * Highlight sensitive fields that need confirmation
 */
async function highlightSensitiveFields(page, confirmRequired) {
  for (const field of confirmRequired) {
    try {
      // Try to find and highlight the field
      const selectors = getFieldSelectors(field.field);
      for (const selector of selectors) {
        const element = await page.$(selector);
        if (element) {
          await page.evaluate((el) => {
            el.style.outline = '3px solid #ff6b6b';
            el.style.backgroundColor = '#fff3f3';
            
            // Add warning label
            const label = document.createElement('div');
            label.textContent = '⚠️ Confirm this field';
            label.style.cssText = 'background:#ff6b6b;color:white;padding:2px 8px;font-size:12px;position:absolute;z-index:9999;';
            el.parentElement.style.position = 'relative';
            el.parentElement.insertBefore(label, el);
          }, element);
          break;
        }
      }
    } catch (e) {
      // Ignore highlight errors
    }
  }
}

/**
 * Get selectors for a field type
 */
function getFieldSelectors(fieldType) {
  const selectorMap = {
    work_authorization: [
      '[name*="authorization" i]',
      '[name*="legal" i]',
      '[id*="authorization" i]',
      'label:has-text("authorized") + input',
      'label:has-text("authorization") + input',
    ],
    salary: [
      '[name*="salary" i]',
      '[name*="compensation" i]',
      '[id*="salary" i]',
      'label:has-text("salary") + input',
    ],
    willing_to_relocate: [
      '[name*="relocate" i]',
      '[name*="relocation" i]',
      '[id*="relocate" i]',
      'label:has-text("relocate") + input',
    ],
    notice_period: [
      '[name*="notice" i]',
      '[name*="start" i]',
      '[name*="available" i]',
      '[id*="notice" i]',
      'label:has-text("notice") + input',
      'label:has-text("start date") + input',
    ],
    referral_source: [
      '[name*="source" i]',
      '[name*="referral" i]',
      '[name*="hear" i]',
      '[id*="source" i]',
      'label:has-text("hear about") + input',
      'label:has-text("how did you") + input',
    ],
    requires_sponsorship: [
      '[name*="sponsor" i]',
      '[name*="visa" i]',
      '[id*="sponsor" i]',
      'label:has-text("sponsor") + input',
      'label:has-text("visa") + input',
    ],
  };

  return selectorMap[fieldType] || [];
}

// Run
main();
