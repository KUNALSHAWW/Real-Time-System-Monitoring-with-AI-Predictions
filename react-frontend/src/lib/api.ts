/**
 * Axios-based API client.
 *
 * - Automatically injects the JWT `Authorization` header
 * - Base URL defaults to the Next.js rewrite proxy (`/api/v1`)
 */

import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ---- request interceptor: attach JWT -----------------------------------
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ---- response interceptor: auto-logout on 401 --------------------------
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  },
);

export default api;
