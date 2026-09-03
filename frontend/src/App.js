import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/AuthContext";
import { currentPeriod } from "./lib/utils";
import Login from "./pages/Login";
import ChangePassword from "./pages/ChangePassword";
import Layout from "./components/Layout";
import Executive from "./pages/Executive";
import AdminHome from "./pages/AdminHome";
import MyDashboard from "./pages/MyDashboard";
import Leaderboard from "./pages/Leaderboard";
import Portfolio from "./pages/Portfolio";
import NPF from "./pages/NPF";
import Collection from "./pages/Collection";
import UsersPage from "./pages/Users";
import Targets from "./pages/Targets";
import PerfSettings from "./pages/PerfSettings";
import DataMgmt from "./pages/DataMgmt";
import Audit from "./pages/Audit";
import SystemSettings from "./pages/SystemSettings";

function Loading() {
  return <div className="min-h-screen flex items-center justify-center text-slate-400">Memuat AO-360...</div>;
}

function HomeRedirect() {
  const { user } = useAuth();
  const map = { direktur: "/executive", admin: "/admin", ao_lending: "/dashboard", ao_funding: "/dashboard", pic_remedial: "/dashboard" };
  return <Navigate to={map[user.role] || "/dashboard"} replace />;
}

function Protected({ children, roles }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (user === null) return <Loading />;
  if (user === false) return <Navigate to="/login" replace />;
  if (user.requires_password_reset && loc.pathname !== "/change-password")
    return <Navigate to="/change-password" replace />;
  if (roles && !roles.includes(user.role))
    return <div className="p-10 text-center text-slate-500">Akses ditolak untuk role Anda.</div>;
  return children;
}

function Page({ title, roles, children }) {
  return <Protected roles={roles}><Layout title={title}>{children}</Layout></Protected>;
}

function Shell() {
  const { user, period, setPeriod } = useAuth();
  useEffect(() => {
    if (user && !period) setPeriod(currentPeriod());
  }, [user, period, setPeriod]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/change-password" element={<Protected><ChangePassword /></Protected>} />
      <Route path="/" element={<Protected><HomeRedirect /></Protected>} />
      <Route path="/executive" element={<Page title="Executive Dashboard" roles={["direktur", "admin"]}><Executive /></Page>} />
      <Route path="/admin" element={<Page title="Admin Dashboard" roles={["admin"]}><AdminHome /></Page>} />
      <Route path="/dashboard" element={<Page title="Dashboard Saya" roles={["ao_lending", "ao_funding", "pic_remedial"]}><MyDashboard /></Page>} />
      <Route path="/leaderboard" element={<Page title="AO Performance Leaderboard" roles={["admin", "direktur"]}><Leaderboard /></Page>} />
      <Route path="/portfolio" element={<Page title="Portfolio Nasabah" roles={["admin", "direktur", "ao_lending"]}><Portfolio /></Page>} />
      <Route path="/npf" element={<Page title="Monitoring NPF" roles={["admin", "direktur", "pic_remedial"]}><NPF /></Page>} />
      <Route path="/collection" element={<Page title="Collection Activity" roles={["admin", "direktur", "ao_lending", "pic_remedial"]}><Collection /></Page>} />
      <Route path="/users" element={<Page title="Manajemen User" roles={["admin"]}><UsersPage /></Page>} />
      <Route path="/targets" element={<Page title="Target & Achievement" roles={["admin"]}><Targets /></Page>} />
      <Route path="/performance-settings" element={<Page title="Performance Setting & Weight Management" roles={["admin", "direktur"]}><PerfSettings /></Page>} />
      <Route path="/data" element={<Page title="Data Management" roles={["admin"]}><DataMgmt /></Page>} />
      <Route path="/audit" element={<Page title="Audit Log" roles={["admin", "direktur"]}><Audit /></Page>} />
      <Route path="/settings" element={<Page title="Pengaturan Sistem" roles={["admin"]}><SystemSettings /></Page>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </AuthProvider>
  );
}
