import React, { useEffect, useState, useCallback } from "react";
import { Search, Plus, Trash2, Archive, MapPin, DoorClosed } from "lucide-react";
import { toast } from "sonner";
import api from "../api";
import { Modal, inputClass } from "../components/ui";
import AddTenantForm from "../components/AddTenantForm";
import { formatRupiah, initials } from "../utils";

export default function Penghuni() {
  const [tenants, setTenants] = useState([]);
  const [locations, setLocations] = useState([]);
  const [search, setSearch] = useState("");
  const [locFilter, setLocFilter] = useState("");
  const [addOpen, setAddOpen] = useState(false);

  const load = useCallback(() => {
    const params = {};
    if (search) params.search = search;
    if (locFilter) params.location_id = locFilter;
    api.get("/tenants", { params }).then((r) => setTenants(r.data)).catch(() => {});
  }, [search, locFilter]);

  useEffect(() => { api.get("/locations").then((r) => setLocations(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  const removeTenant = async (id, mode) => {
    const ok = window.confirm(
      mode === "delete"
        ? "Hapus penghuni ini secara permanen beserta data pembayarannya?"
        : "Arsipkan penghuni ini? Kamar akan dikosongkan."
    );
    if (!ok) return;
    try {
      if (mode === "delete") await api.delete(`/tenants/${id}`);
      else await api.post(`/tenants/${id}/archive`);
      toast.success(mode === "delete" ? "Penghuni dihapus" : "Penghuni diarsipkan");
      load();
    } catch (e) { toast.error("Gagal memproses"); }
  };

  return (
    <div className="page-container">
      <div className="flex items-center justify-between gap-3 mb-6 flex-wrap">
        <div>
          <h1 className="text-3xl font-heading font-extrabold text-navy">Penghuni</h1>
          <p className="text-slate-500">Daftar seluruh penghuni kost</p>
        </div>
        <button onClick={() => setAddOpen(true)} className="flex items-center gap-2 px-5 py-3 rounded-xl bg-navy text-white font-semibold hover:bg-navy-light transition-colors duration-200 active:scale-95" data-testid="tambah-penghuni-btn">
          <Plus size={18} /> Tambah Penghuni
        </button>
      </div>

      <div className="flex gap-3 mb-6 flex-col sm:flex-row">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className={`${inputClass} pl-11`} placeholder="Cari nama penghuni..." value={search} onChange={(e) => setSearch(e.target.value)} data-testid="penghuni-search-input" />
        </div>
        <select className={`${inputClass} sm:max-w-xs`} value={locFilter} onChange={(e) => setLocFilter(e.target.value)} data-testid="penghuni-location-filter">
          <option value="">Semua Lokasi</option>
          {locations.map((l) => <option key={l.id} value={l.id}>{l.nama}</option>)}
        </select>
      </div>

      {tenants.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400" data-testid="penghuni-empty">
          Belum ada penghuni. Klik "Tambah Penghuni" untuk mulai.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="penghuni-grid">
          {tenants.map((t) => (
            <div key={t.id} className="bg-white rounded-2xl border border-slate-200 shadow-card p-5 hover:-translate-y-1 hover:shadow-md transition-all duration-200 fade-up" data-testid={`penghuni-card-${t.id}`}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-full bg-navy text-gold flex items-center justify-center font-heading font-bold">
                  {initials(t.nama)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-heading font-bold text-navy truncate">{t.nama}</div>
                  <div className="text-sm text-slate-500">{t.nomor_hp || "-"}</div>
                </div>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex items-center gap-2 text-slate-600"><DoorClosed size={15} className="text-slate-400" /> Kamar {t.nomor_kamar || "-"}</div>
                <div className="flex items-center gap-2 text-slate-600"><MapPin size={15} className="text-slate-400" /> {t.lokasi}</div>
              </div>
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                <span className="font-heading font-bold text-gold-dark">{formatRupiah(t.harga_sewa)}<span className="text-xs font-normal text-slate-400">/bln</span></span>
                <div className="flex gap-2">
                  <button onClick={() => removeTenant(t.id, "archive")} title="Arsipkan" className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors duration-200" data-testid={`arsip-btn-${t.id}`}><Archive size={16} /></button>
                  <button onClick={() => removeTenant(t.id, "delete")} title="Hapus" className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 transition-colors duration-200" data-testid={`hapus-btn-${t.id}`}><Trash2 size={16} /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Tambah Penghuni" testid="penghuni-add-modal">
        <AddTenantForm onDone={() => { setAddOpen(false); load(); }} />
      </Modal>
    </div>
  );
}
