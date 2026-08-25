import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Building2, Users, Wallet, Image as ImageIcon, Upload } from "lucide-react";
import { Toaster, toast } from "sonner";
import api from "./api";
import { Modal, Field } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import LokasiKamar from "./pages/LokasiKamar";
import Penghuni from "./pages/Penghuni";
import Pembayaran from "./pages/Pembayaran";
import "./App.css";

const SettingsContext = createContext(null);
export const useSettings = () => useContext(SettingsContext);

const NAV = [
  { to: "/", label: "Beranda", icon: LayoutDashboard, end: true },
  { to: "/lokasi", label: "Lokasi & Kamar", icon: Building2 },
  { to: "/penghuni", label: "Penghuni", icon: Users },
  { to: "/pembayaran", label: "Pembayaran", icon: Wallet },
];

function Logo({ logo, size = 44 }) {
  if (logo) {
    return (
      <img
        src={logo}
        alt="ROSADAH KOST"
        style={{ width: size, height: size }}
        className="rounded-full object-cover bg-white"
        data-testid="app-logo"
      />
    );
  }
  return (
    <div
      style={{ width: size, height: size }}
      className="rounded-full bg-gold flex items-center justify-center text-navy font-heading font-extrabold"
      data-testid="app-logo-placeholder"
    >
      RK
    </div>
  );
}

function Sidebar({ settings, onOpenLogo }) {
  return (
    <aside className="hidden lg:flex flex-col w-72 bg-navy text-white fixed inset-y-0 left-0 z-30">
      <div className="flex items-center gap-3 px-6 py-6 border-b border-white/10">
        <Logo logo={settings?.logo} />
        <div>
          <div className="font-heading font-extrabold text-lg leading-tight text-white">ROSADAH KOST</div>
          <div className="text-[11px] text-gold tracking-wider">Nyaman • Aman • Bersih</div>
        </div>
      </div>
      <nav className="flex-1 px-4 py-6 space-y-1.5">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            data-testid={`nav-${item.label.toLowerCase().replace(/[^a-z]/g, "-").replace(/-+/g, "-")}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200 ${
                isActive
                  ? "bg-white/10 text-gold border-l-4 border-gold"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <item.icon size={20} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-5 border-t border-white/10">
        <button
          onClick={onOpenLogo}
          data-testid="open-logo-settings-btn"
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors duration-200"
        >
          <ImageIcon size={18} /> Pengaturan Logo
        </button>
      </div>
    </aside>
  );
}

function MobileHeader({ settings, onOpenLogo }) {
  return (
    <header className="lg:hidden sticky top-0 z-30 bg-navy text-white px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <Logo logo={settings?.logo} size={38} />
        <div>
          <div className="font-heading font-extrabold text-base leading-tight">ROSADAH KOST</div>
          <div className="text-[10px] text-gold tracking-wider">Nyaman • Aman • Bersih</div>
        </div>
      </div>
      <button onClick={onOpenLogo} data-testid="mobile-open-logo-btn" className="p-2 rounded-full hover:bg-white/10">
        <ImageIcon size={20} />
      </button>
    </header>
  );
}

function BottomNav() {
  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-slate-200 flex">
      {NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          data-testid={`bottomnav-${item.label.toLowerCase().replace(/[^a-z]/g, "-").replace(/-+/g, "-")}`}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center py-2.5 gap-0.5 text-[10px] font-medium transition-colors duration-200 ${
              isActive ? "text-gold-dark" : "text-slate-400"
            }`
          }
        >
          <item.icon size={20} />
          {item.label.split(" ")[0]}
        </NavLink>
      ))}
    </nav>
  );
}

function LogoModal({ open, onClose }) {
  const { settings, refreshSettings } = useSettings();
  const [preview, setPreview] = useState(settings?.logo || "");
  const [saving, setSaving] = useState(false);

  useEffect(() => { setPreview(settings?.logo || ""); }, [settings, open]);

  const onFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 3 * 1024 * 1024) {
      toast.error("Ukuran gambar maksimal 3MB");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result);
    reader.readAsDataURL(file);
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/settings/logo", { logo: preview });
      await refreshSettings();
      toast.success("Logo berhasil disimpan");
      onClose();
    } catch (e) {
      toast.error("Gagal menyimpan logo");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Pengaturan Logo" testid="logo-modal">
      <div className="flex flex-col items-center">
        <div className="w-32 h-32 rounded-full bg-slate-100 flex items-center justify-center overflow-hidden border-4 border-gold/30 mb-4">
          {preview ? (
            <img src={preview} alt="preview" className="w-full h-full object-cover" data-testid="logo-preview" />
          ) : (
            <span className="text-slate-400 text-sm">Belum ada logo</span>
          )}
        </div>
        <Field label="Unggah Logo (PNG/JPG)">
          <label className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 border-dashed border-slate-300 text-slate-500 cursor-pointer hover:border-gold hover:text-gold-dark transition-colors duration-200">
            <Upload size={18} /> Pilih Gambar
            <input type="file" accept="image/*" className="hidden" onChange={onFile} data-testid="logo-file-input" />
          </label>
        </Field>
      </div>
      <div className="flex gap-3 mt-2">
        <button onClick={onClose} className="flex-1 py-3 rounded-xl border border-slate-300 text-slate-600 font-semibold hover:bg-slate-50 transition-colors duration-200" data-testid="logo-cancel-btn">
          Batal
        </button>
        <button onClick={save} disabled={saving} className="flex-1 py-3 rounded-xl bg-navy text-white font-semibold hover:bg-navy-light disabled:opacity-60 transition-colors duration-200" data-testid="logo-save-btn">
          {saving ? "Menyimpan..." : "Simpan Logo"}
        </button>
      </div>
    </Modal>
  );
}

function Shell() {
  const [settings, setSettings] = useState(null);
  const [logoOpen, setLogoOpen] = useState(false);

  const refreshSettings = useCallback(async () => {
    try {
      const res = await api.get("/settings");
      setSettings(res.data);
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => { refreshSettings(); }, [refreshSettings]);

  return (
    <SettingsContext.Provider value={{ settings, refreshSettings }}>
      <div className="min-h-screen bg-slate-50">
        <Sidebar settings={settings} onOpenLogo={() => setLogoOpen(true)} />
        <MobileHeader settings={settings} onOpenLogo={() => setLogoOpen(true)} />
        <main className="lg:ml-72 pb-24 lg:pb-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/lokasi" element={<LokasiKamar />} />
            <Route path="/penghuni" element={<Penghuni />} />
            <Route path="/pembayaran" element={<Pembayaran />} />
          </Routes>
        </main>
        <BottomNav />
        <LogoModal open={logoOpen} onClose={() => setLogoOpen(false)} />
      </div>
    </SettingsContext.Provider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" richColors />
      <Shell />
    </BrowserRouter>
  );
}
