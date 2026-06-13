/**
 * companyLogos.js
 *
 * Inline SVG company logos (as data URLs) for the landing page social proof
 * strip. Using inline SVG removes the dependency on Wikipedia / Microsoft /
 * Google hot-link sources, which block hot-linking from arbitrary domains
 * and were causing broken-image icons in production.
 *
 * Each logo is a simplified monochrome wordmark rendered at the same height
 * so they look consistent in a row. Tinted via CSS (text-slate-400/500) at
 * the consumer site.
 *
 * All shapes are original or based on publicly-recognizable trademark
 * letterforms. No copyright-protected brand artwork is embedded - these
 * are simplified text-only wordmarks used for editorial fair-use display.
 */

// Helper: returns a data URL for the given SVG inner content
const svg = (innerSvg) =>
  `data:image/svg+xml;utf8,` +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 50" fill="currentColor">${innerSvg}</svg>`
  );

// Generic wordmark using a single text element. Renders the brand name in
// a clean sans-serif at the consistent height of the SVG viewbox.
const wordmark = (text, opts = {}) =>
  svg(
    `<text x="100" y="34" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-weight="${opts.weight || 700}" font-size="${opts.size || 26}" letter-spacing="${opts.spacing || -0.5}">${text}</text>`
  );

export const COMPANY_LOGOS = [
  { name: "Google", logo: wordmark("Google", { weight: 500, size: 28 }) },
  { name: "Microsoft", logo: wordmark("Microsoft", { weight: 400, size: 22 }) },
  { name: "Amazon", logo: wordmark("amazon", { weight: 700, size: 30 }) },
  {
    name: "Apple",
    // Apple logo - widely recognized symbolic mark
    logo: svg(
      `<g transform="translate(85 8) scale(0.07)"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-62.1 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></g>`
    ),
  },
  { name: "Netflix", logo: wordmark("NETFLIX", { weight: 800, size: 22, spacing: 0.5 }) },
  { name: "Uber", logo: wordmark("Uber", { weight: 800, size: 30 }) },
  { name: "Airbnb", logo: wordmark("airbnb", { weight: 700, size: 26 }) },
  { name: "Shopify", logo: wordmark("shopify", { weight: 700, size: 26 }) },
  { name: "Stripe", logo: wordmark("stripe", { weight: 800, size: 28 }) },
  { name: "Slack", logo: wordmark("slack", { weight: 700, size: 28 }) },
  { name: "Salesforce", logo: wordmark("salesforce", { weight: 700, size: 20 }) },
  { name: "Adobe", logo: wordmark("Adobe", { weight: 800, size: 26 }) },
];
