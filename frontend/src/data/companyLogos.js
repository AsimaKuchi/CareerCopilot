/**
 * companyLogos.js
 *
 * Real company brand logos served from two free, CORS-enabled CDNs:
 *
 *   1. simpleicons.org/<slug>/<hex>  -- official MIT-licensed brand SVGs
 *      Works for: Google, Apple, Netflix, Uber, Airbnb, Shopify, Stripe,
 *                Meta, Nvidia, Spotify.
 *      Does NOT serve: Microsoft, Amazon, Slack, Salesforce, Adobe
 *      (those brands requested removal from simpleicons).
 *
 *   2. unavatar.io/<domain>  -- generic favicon/logo proxy
 *      Used as the fallback for the brands simpleicons no longer hosts.
 *
 * The <img onError> handler in LandingPage.jsx replaces any broken image
 * with a styled text wordmark, so the marquee row never shows a broken
 * icon even if a CDN has a temporary outage.
 */

const si = (slug, color) => `https://cdn.simpleicons.org/${slug}/${color}`;
const ua = (domain) => `https://unavatar.io/${domain}`;

export const COMPANY_LOGOS = [
  { name: "Google", logo: si("google", "4285F4") },
  { name: "Microsoft", logo: ua("microsoft.com") },
  { name: "Amazon", logo: ua("amazon.com") },
  { name: "Apple", logo: si("apple", "000000") },
  { name: "Netflix", logo: si("netflix", "E50914") },
  { name: "Uber", logo: si("uber", "000000") },
  { name: "Airbnb", logo: si("airbnb", "FF5A5F") },
  { name: "Shopify", logo: si("shopify", "7AB55C") },
  { name: "Stripe", logo: si("stripe", "635BFF") },
  { name: "Slack", logo: ua("slack.com") },
  { name: "Salesforce", logo: ua("salesforce.com") },
  { name: "Meta", logo: si("meta", "0467DF") },
  { name: "Nvidia", logo: si("nvidia", "76B900") },
  { name: "Spotify", logo: si("spotify", "1DB954") },
];
