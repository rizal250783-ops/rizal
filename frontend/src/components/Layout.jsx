import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard, Scale, CheckSquare, History, FileText, BarChart3,
  ListTree, Users, HardDrive, LogOut, Menu,
} from "lucide-react";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

const MENU = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/perkara", label: "Data Perkara", icon: Scale },
  { to: "/approval", label: "Approval Center", icon: CheckSquare },
  { to: "/timeline", label: "Timeline Perkara", icon: History },
  { to: "/dokumen", label: "Dokumen Perkara", icon: FileText },
  { to: "/laporan", label: "Laporan", icon: BarChart3 },
  { to: "/master-data", label: "Master Data", icon: ListTree },
  { to: "/users", label: "User Management", icon: Users, deptOnly: true },
  { to: "/database", label: "Database Management", icon: HardDrive, deptOnly: true },
];

function NavItems({ onNavigate }) {
  const { isDeptHead } = useAuth();
  return (
    <nav className="flex flex-col gap-1 px-3">
      {MENU.filter((m) => !m.deptOnly || isDeptHead).map((m) => (
        <NavLink
          key={m.to}
          to={m.to}
          end={m.to === "/"}
          onClick={onNavigate}
          data-testid={`nav-${m.label.toLowerCase().replace(/\s+/g, "-")}`}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-colors ${
              isActive ? "bg-toska text-white" : "text-slate-600 hover:bg-toska-light hover:text-toska-dark"
            }`
          }
        >
          <m.icon className="h-4 w-4 shrink-0" />
          {m.label}
        </NavLink>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <div className="flex flex-col gap-3 px-5 py-5 border-b border-slate-200">
      <img src="/bsi-logo.png" alt="Bank Syariah Indonesia" data-testid="sidebar-bsi-logo" className="h-9 w-auto object-contain self-start" />
      <div className="leading-tight">
        <p className="font-heading font-bold text-slate-900 tracking-tight">CASEWISE</p>
        <p className="text-[10px] uppercase tracking-widest text-slate-500">Legal Perdata — BSI</p>
      </div>
    </div>
  );
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <aside className="hidden lg:flex flex-col fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200 z-30">
        <Brand />
        <div className="flex-1 overflow-y-auto py-4">
          <NavItems />
        </div>
        <div className="border-t border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-900" data-testid="sidebar-user-name">{user?.nama}</p>
          <p className="text-xs text-slate-500 mb-3">
            {user?.role === "dept_head" ? "Legal Litigation & Advice Manager" : "Legal Litigation & Advice Officer"}
          </p>
          <Button data-testid="logout-button" variant="outline" size="sm" className="w-full" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" /> Keluar
          </Button>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="lg:hidden sticky top-0 z-20 bg-white border-b border-slate-200 flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <img src="/bsi-logo.png" alt="Bank Syariah Indonesia" className="h-7 w-auto object-contain" />
            <p className="font-heading font-bold text-slate-900">CASEWISE</p>
          </div>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button data-testid="mobile-menu-button" variant="outline" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetTitle className="sr-only">Menu Navigasi</SheetTitle>
              <Brand />
              <div className="py-4">
                <NavItems onNavigate={() => setOpen(false)} />
              </div>
              <div className="border-t border-slate-200 p-4">
                <p className="text-sm font-semibold text-slate-900">{user?.nama}</p>
                <p className="text-xs text-slate-500 mb-3">
                  {user?.role === "dept_head" ? "Legal Litigation & Advice Manager" : "Legal Litigation & Advice Officer"}
                </p>
                <Button data-testid="logout-button-mobile" variant="outline" size="sm" className="w-full" onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" /> Keluar
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </header>
        <main className="p-4 md:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
