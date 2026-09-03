import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL;
export const API = `${BASE}/api`;

const api = axios.create({ baseURL: API, withCredentials: true });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ao360_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

export function apiErr(e) {
  const d = e?.response?.data?.detail;
  if (d == null) return e?.message || "Terjadi kesalahan";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x?.msg || JSON.stringify(x)).join(" ");
  if (d?.msg) return d.msg;
  return String(d);
}
