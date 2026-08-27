import { useEffect, useState } from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import {
  LayoutDashboard, FileText, FilePlus2, CheckCircle2, Bell, BarChart3,
  Users, Database, ShieldCheck, ScrollText, KeyRound, LogOut, Menu, X, ChevronDown, ShieldAlert
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { BsiLogo, Marquee } from "./Brand";
import api from "../lib/api";

const TAGLINE = "Solusi cerdas menuju pembiayaan berkelanjutan";

function menuFor(user) {
  const role = user.role;
  const items = [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "menu-dashboard" }];
  if (role === "RCO") {
    items.push({ to: "/notes/new", label: "Buat Nota", icon: FilePlus2, testid: "menu-new-note" });
    items.push({ to: "/notes", label: "Nota Saya", icon: FileText, testid: "menu-notes" });
  } else {
    items.push({ to: "/notes", label: "Daftar Nota", icon: FileText, testid: "menu-notes" });
  }
  items.push({ to: "/approved", label: "Nota Approved", icon: CheckCircle2, testid: "menu-approved" });
  if (role === "RCRM" || role === "RCG") {
    items.push({ to: "/monitoring", label: "Monitoring Segmen & Produk", icon: BarChart3, testid: "menu-monitoring" });
  }
  if (role === "RCG") {
    items.push({ to: "/risk-assessment", label: "Risk Assessment", icon: ShieldAlert, testid: "menu-ra" });
    items.push({ to: "/users", label: "Manajemen User", icon: Users, testid: "menu-users" });
    items.push({ to: "/master", label: "Master Data", icon: Database, testid: "menu-master" });
    items.push({ to: "/audit", label: "Panel Audit Global", icon: ScrollText, testid: "menu-audit" });
  }
  items.push({ to: "/notifications", label: "Notifikasi", icon: Bell, testid: "menu-notifications" });
  items.push({ to: "/change-password", label: "Ganti Password", icon: KeyRound, testid: "menu-change-password" });
  return items;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const load = () => api.get("/notifications").then((r) => setUnread(r.data.unread)).catch(() => {});
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  const items = menuFor(user);

  return (
    <div className="min-h-screen flex bg-[#F8FAFC]">
      {/* Sidebar */}
      <aside className={`fixed lg:static z-40 h-screen w-64 bg-white border-r border-slate-200 flex flex-col transition-transform ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100">
          <BsiLogo size="sm" />
          <span className="font-display font-bold text-[#00A0A0] text-sm">RCG</span>
          <button className="lg:hidden" onClick={() => setOpen(false)} data-testid="sidebar-close"><X size={20} /></button>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {items.map((it) => {
            const Icon = it.icon;
            return (
              <NavLink
                key={it.to}
                to={it.to}
                onClick={() => setOpen(false)}
                data-testid={it.testid}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors relative ${
                    isActive ? "bg-[#E6F6F6] text-[#00A0A0] border-l-4 border-[#00A0A0] pl-2" : "text-slate-600 hover:bg-slate-50"
                  }`
                }
              >
                <Icon size={18} />
                <span className="flex-1">{it.label}</span>
                {it.to === "/notifications" && unread > 0 && (
                  <span className="bg-[#F0B43C] text-white text-[10px] rounded-full px-1.5 py-0.5 min-w-[18px] text-center" data-testid="unread-count">{unread}</span>
                )}
              </NavLink>
            );
          })}
        </nav>
        <div className="p-3 border-t border-slate-100">
          <div className="text-xs text-slate-500 mb-1">Masuk sebagai</div>
          <div className="text-sm font-semibold text-slate-800 truncate">{user.nama}</div>
          <div className="text-xs text-[#00A0A0] font-medium">{user.role} • {user.nip}</div>
        </div>
      </aside>

      {open && <div className="fixed inset-0 bg-black/30 z-30 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center gap-3 px-4 sticky top-0 z-20">
          <button className="lg:hidden" onClick={() => setOpen(true)} data-testid="sidebar-open"><Menu size={22} /></button>
          <div className="flex-1 hidden md:block">
            <Marquee text={TAGLINE} className="bg-[#E6F6F6] text-[#00A0A0] py-1.5 rounded-md text-sm font-medium max-w-2xl" />
          </div>
          <button onClick={() => navigate("/notifications")} className="relative p-2 rounded-md hover:bg-slate-100" data-testid="header-bell">
            <Bell size={20} className="text-slate-600" />
            {unread > 0 && <span className="absolute top-1 right-1 w-2 h-2 bg-[#F0B43C] rounded-full" />}
          </button>
          <div className="w-9 h-9 rounded-full bg-[#00A0A0] text-white flex items-center justify-center font-semibold text-sm">
            {user.nama?.[0]}
          </div>
          <button onClick={logout} className="p-2 rounded-md hover:bg-slate-100 text-slate-600" data-testid="logout-btn" title="Keluar">
            <LogOut size={18} />
          </button>
        </header>
        <main className="flex-1 p-4 md:p-6 overflow-x-hidden fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
