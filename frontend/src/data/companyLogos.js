/**
 * companyLogos.js
 *
 * Real company brand logos sourced from simpleicons.org CDN.
 * - simpleicons.org is MIT-licensed, CORS-enabled, served by Vercel CDN
 * - Each URL like https://cdn.simpleicons.org/google/4285F4 returns the
 *   official SVG glyph in the supplied hex color
 * - We pass each brand's primary brand color so the strip looks like
 *   a real "as seen on" section rather than monochrome dots
 *
 * If a logo ever fails to load, the <img onError> handler in LandingPage
 * falls back to a styled text wordmark.
 */

const sIcon = (slug, color) =>
  `https://cdn.simpleicons.org/${slug}/${color}`;

export const COMPANY_LOGOS = [
  { name: "Google", logo: sIcon("google", "4285F4") },
  { name: "Microsoft", logo: sIcon("microsoft", "5E5E5E") },
  { name: "Amazon", logo: sIcon("amazon", "FF9900") },
  { name: "Apple", logo: sIcon("apple", "000000") },
  { name: "Netflix", logo: sIcon("netflix", "E50914") },
  { name: "Uber", logo: sIcon("uber", "000000") },
  { name: "Airbnb", logo: sIcon("airbnb", "FF5A5F") },
  { name: "Shopify", logo: sIcon("shopify", "7AB55C") },
  { name: "Stripe", logo: sIcon("stripe", "635BFF") },
  { name: "Slack", logo: sIcon("slack", "4A154B") },
  { name: "Salesforce", logo: sIcon("salesforce", "00A1E0") },
  { name: "Adobe", logo: sIcon("adobe", "FF0000") },
  { name: "Meta", logo: sIcon("meta", "0467DF") },
  { name: "Nvidia", logo: sIcon("nvidia", "76B900") },
  { name: "Spotify", logo: sIcon("spotify", "1DB954") },
];
