import React, { createContext, useContext, useEffect, useState } from "react";
import api, { apiErr } from "./api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=checking, false=anon
  const [period, setPeriod] = useState(null);

  useEffect(() => {
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.access_token) localStorage.setItem("ao360_token", data.access_token);
    setUser(data);
    return data;
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch (e) {}
    localStorage.removeItem("ao360_token");
    setUser(false);
  };

  const refreshUser = async () => {
    const r = await api.get("/auth/me");
    setUser(r.data);
    return r.data;
  };

  return (
    <AuthCtx.Provider value={{ user, setUser, login, logout, refreshUser, period, setPeriod }}>
      {children}
    </AuthCtx.Provider>
  );
}
