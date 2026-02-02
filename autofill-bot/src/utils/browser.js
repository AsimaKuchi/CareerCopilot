/**
 * Browser Utilities for AutoFill Bot
 * 
 * Handles browser creation and ATS detection.
 */

const { chromium } = require('playwright');

/**
 * Create and configure browser instance
 */
async function createBrowser(config = {}) {
  // Force headless in server environments without display
  const isHeadless = config.headless !== false;
  
  const browser = await chromium.launch({
    headless: true,  // Always true for server environment
    slowMo: config.slowMo ?? 100,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--single-process',
      '--no-zygote',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    acceptDownloads: true,
  });

  const page = await context.newPage();
  page.setDefaultTimeout(config.timeout ?? 30000);

  return { browser, context, page };
}

/**
 * Detect ATS type from page structure
 */
async function detectATSType(page, url) {
  const urlLower = url.toLowerCase();
  
  // High confidence: URL-based detection
  if (urlLower.includes('greenhouse.io') || urlLower.includes('boards.greenhouse')) {
    return { type: 'greenhouse', confidence: 'high', source: 'url' };
  }
  if (urlLower.includes('lever.co') || urlLower.includes('jobs.lever')) {
    return { type: 'lever', confidence: 'high', source: 'url' };
  }
  if (urlLower.includes('ashbyhq.com') || urlLower.includes('jobs.ashby')) {
    return { type: 'ashby', confidence: 'high', source: 'url' };
  }
  if (urlLower.includes('myworkdayjobs.com') || urlLower.includes('workday.com')) {
    return { type: 'workday', confidence: 'high', source: 'url' };
  }

  // Medium confidence: Page structure detection
  try {
    // Check for Greenhouse markers
    const isGreenhouse = await page.evaluate(() => {
      return !!(
        document.querySelector('form#application-form') ||
        document.querySelector('[data-controller="application-form"]') ||
        document.querySelector('.application-page') ||
        document.querySelector('#grnhse_app') ||
        window.Greenhouse !== undefined
      );
    });
    if (isGreenhouse) {
      return { type: 'greenhouse', confidence: 'medium', source: 'page_structure' };
    }

    // Check for Lever markers
    const isLever = await page.evaluate(() => {
      return !!(
        document.querySelector('.application-form') ||
        document.querySelector('[data-qa="application-form"]') ||
        document.querySelector('.lever-job-application') ||
        document.querySelector('form[action*="lever"]')
      );
    });
    if (isLever) {
      return { type: 'lever', confidence: 'medium', source: 'page_structure' };
    }

    // Check for Ashby markers
    const isAshby = await page.evaluate(() => {
      return !!(
        document.querySelector('[data-testid="application-form"]') ||
        document.querySelector('.ashby-application') ||
        document.querySelector('form[data-ashby]') ||
        window.__ASHBY__ !== undefined
      );
    });
    if (isAshby) {
      return { type: 'ashby', confidence: 'medium', source: 'page_structure' };
    }

  } catch (e) {
    // Page evaluation failed
  }

  // Low confidence: Generic
  return { type: 'unknown', confidence: 'low', source: 'fallback' };
}

/**
 * Wait for page to be ready for interaction
 */
async function waitForPageReady(page, timeout = 10000) {
  try {
    // Wait for network to be idle
    await page.waitForLoadState('networkidle', { timeout });
    
    // Wait a bit for any lazy-loaded content
    await page.waitForTimeout(1000);
    
    // Check if there's a loading indicator
    const loadingSelectors = [
      '.loading',
      '[data-loading]',
      '.spinner',
      '[aria-busy="true"]',
    ];
    
    for (const selector of loadingSelectors) {
      const loading = await page.$(selector);
      if (loading) {
        await page.waitForSelector(selector, { state: 'hidden', timeout: 5000 }).catch(() => {});
      }
    }
    
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Scroll element into view
 */
async function scrollToElement(page, selector) {
  const element = await page.$(selector);
  if (element) {
    await element.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
  }
}

module.exports = {
  createBrowser,
  detectATSType,
  waitForPageReady,
  scrollToElement,
};
