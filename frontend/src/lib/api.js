import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("rcg_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.includes("/login")) {
      localStorage.removeItem("rcg_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function apiError(e) {
  const d = e.response?.data?.detail;
  if (d == null) return e.message || "Terjadi kesalahan";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => (typeof x === "string" ? x : x.msg || JSON.stringify(x))).join(" • ");
  if (d.msg) return d.msg;
  return String(d);
}

export default api;
