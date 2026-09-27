import axios from "axios";

/**
 * api/client.js — single axios instance for the whole SPA.
 *
 *  * attaches the JWT as a Bearer header on every request
 *  * on 401, clears the stale session and bounces to /login
 *
 * In development, vite proxies /api to http://localhost:8000.
 * In production, set VITE_API_BASE to the Render API URL.
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("dp_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes("/auth/login")) {
      localStorage.removeItem("dp_token");
      localStorage.removeItem("dp_user");
      if (window.location.pathname !== "/login") window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function apiError(err, fallback = "Something went wrong") {
  return err.response?.data?.detail || fallback;
}

export default client;
