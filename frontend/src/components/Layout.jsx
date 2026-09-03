import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Users, Target, Trophy, Wallet, AlertTriangle,
  Camera, SlidersHorizontal, Database, ScrollText, LogOut, Menu, X, Settings,
} from "lucide-react";
import { useAuth } from "../lib/AuthContext";
import { LOGO, ROLE_LABEL, periodLabel } from "../lib/utils";
import { Select } from "./ui";

const MENUS = {
  direktur: [
    ["/executive", "Executive Dashboard", LayoutDashboard],
    ["/leaderboard", "Ranking AO", Trophy],
    ["/portfolio", "Portfolio Summary", Wallet],
    ["/npf", "Monitoring NPF", AlertTriangle],
    ["/collection", "Dokumentasi Penagihan", Camera],
    ["/performance-settings", "Performance Setting", SlidersHorizontal],
    ["/audit", "Audit Log", ScrollText],
  ],
  admin: [
    ["/admin", "Admin Dashboard", LayoutDashboard],
    ["/users", "Manajemen User", Users],
    ["/targets", "Target & Achievement", Target],
    ["/leaderboard", "Leaderboard", Trophy],
    ["/portfolio", "Portfolio", Wallet],
    ["/npf", "Monitoring NPF", AlertTriangle],
    ["/collection", "Collection Activity", Camera],
    ["/performance-settings", "Performance Setting", SlidersHorizontal],
    ["/data", "Data Management", Database],
    ["/audit", "Audit Log", ScrollText],
    ["/settings", "Pengaturan Sistem", Settings],
  ],
  ao_lending: [
    ["/dashboard", "Dashboard Saya", LayoutDashboard],
    ["/portfolio", "Portfolio Kelolaan", Wallet],
    ["/collection", "Collection Activity", Camera],
  ],
  ao_funding: [
    ["/dashboard", "Dashboard Saya", LayoutDashboard],
  ],
  pic_remedial: [
    ["/dashboard", "Dashboard Remedial", LayoutDashboard],
    ["/npf", "Nasabah Bermasalah & NPF", AlertTriangle],
    ["/collection", "Collection Activity", Camera],
  ],
};

export default function Layout({ children, title }) {
  const { user, logout, period, setPeriod } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const menu = MENUS[user.role] || [];

  const now = new Date();
  const months = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
  const [py, pm] = (period || `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`).split("-");

  const setP = (m, y) => setPeriod(`${y}-${String(m).padStart(2, "0")}`);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className={`fixed lg:static z-40 h-screen w-64 bg-emerald-900 text-emerald-50 flex flex-col transition-transform ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="flex items-center gap-3 px-5 py-5 border-b border-emerald-800">
          <img src={LOGO} alt="BPRS Haji Miskin" className="h-10 w-10 rounded-full bg-white p-1 object-contain" />
          <div>
            <div className="font-heading font-extrabold text-lg tracking-tight text-white">AO-360</div>
            <div className="text-[10px] text-emerald-300 uppercase tracking-wider">Achievement Dashboard</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {menu.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} data-testid={`nav-${to.slice(1)}`}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-emerald-700 text-white" : "text-emerald-100 hover:bg-emerald-800"
                }`
              }>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-emerald-800 px-3 py-3">
          <div className="px-2 pb-2">
            <div className="text-sm font-semibold text-white truncate">{user.name}</div>
            <div className="text-[11px] text-gold-500 font-semibold">{ROLE_LABEL[user.role]}</div>
          </div>
          <button onClick={() => { logout(); nav("/login"); }} data-testid="logout-btn"
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-800 transition-colors">
            <LogOut size={16} /> Keluar
          </button>
        </div>
      </aside>

      {open && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-4 border-b border-slate-200 bg-white/80 backdrop-blur px-4 sm:px-6 py-3">
          <button className="lg:hidden text-slate-600" onClick={() => setOpen(!open)} data-testid="menu-toggle">
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
          <div className="min-w-0">
            <h1 className="truncate text-base sm:text-xl font-bold text-slate-900 font-heading">{title}</h1>
            <div className="text-xs text-slate-500">PT BPRS Haji Miskin · Periode {periodLabel(period)}</div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Select value={parseInt(pm)} onChange={(e) => setP(e.target.value, py)} className="w-36 py-1.5" data-testid="filter-month">
              {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </Select>
            <Select value={py} onChange={(e) => setP(pm, e.target.value)} className="w-24 py-1.5" data-testid="filter-year">
              {[now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2].map((y) => <option key={y} value={y}>{y}</option>)}
            </Select>
          </div>
        </header>
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-[1400px] w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
