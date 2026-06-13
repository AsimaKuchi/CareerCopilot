import React from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "@/index.css";
import App from "@/App";
import { getCsrfToken } from "@/utils/apiFetch";

// Global axios interceptor: always send cookies and inject X-CSRF-Token on
// state-changing requests. Keeps every page (incl. ones using raw axios)
// compatible with the hardened backend CSRF middleware.
axios.defaults.withCredentials = true;
axios.interceptors.request.use((config) => {
  const method = (config.method || "get").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const token = getCsrfToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers["X-CSRF-Token"] = token;
    }
  }
  return config;
});

// Global fetch wrapper: same protection for any raw `fetch(...)` call across
// the codebase. Adds credentials and X-CSRF-Token on state-changing requests
// when the URL points at our API. Safe for external URLs (no header added if
// the cookie is missing).
const _origFetch = window.fetch.bind(window);
window.fetch = (input, init = {}) => {
  const method = (init.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const token = getCsrfToken();
    if (token) {
      init.headers = { ...(init.headers || {}), "X-CSRF-Token": token };
    }
  }
  if (init.credentials === undefined) init.credentials = "include";
  return _origFetch(input, init);
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
