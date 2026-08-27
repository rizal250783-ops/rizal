import { createContext, useContext, useEffect, useState } from "react";
import api from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("rcg_token");
    if (!token) { setLoading(false); return; }
    api.get("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem("rcg_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (nip, password) => {
    const { data } = await api.post("/auth/login", { nip, password });
    localStorage.setItem("rcg_token", data.token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("rcg_token");
    setUser(null);
    window.location.href = "/login";
  };

  const refreshUser = async () => {
    const r = await api.get("/auth/me");
    setUser(r.data);
    return r.data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
