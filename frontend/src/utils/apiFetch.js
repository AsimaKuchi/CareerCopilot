/**
 * Returns the CSRF token from the cookie.
 */
export function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : "";
}

/**
 * Wrapper around fetch that automatically injects the CSRF token header
 * on state-changing requests (POST, PUT, PATCH, DELETE).
 * Drop-in replacement: apiFetch(url, options)
 */
export async function apiFetch(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const token = getCsrfToken();
    if (token) {
      options.headers = {
        ...options.headers,
        "X-CSRF-Token": token,
      };
    }
  }
  // Ensure credentials are always included
  options.credentials = "include";
  return fetch(url, options);
}
