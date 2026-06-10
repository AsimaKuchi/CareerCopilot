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

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
