import { useEffect, useState } from "react";
import api, { apiError } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Database, CalendarPlus, Trash2, Loader2, Search, Plus, Pencil, X, History, MapPin, Building2 } from "lucide-react";
import { toast } from "sonner";

const inp = "px-3 py-2 border border-slate-300 rounded-md text-sm outline-none focus:border-[#00A0A0]";
const btnPrimary = "bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold rounded-md text-sm flex items-center justify-center gap-2";

export default function MasterData() {
  const [tab, setTab] = useState("regions");
  return (
    <div>
      <PageHeader title="Master Data" subtitle="Kelola region, area, cabang & hari libur" icon={Database} />
      <div className="flex gap-2 mb-4 border-b border-slate-200">
        {[["regions", "Region & Area"], ["branches", "Cabang"], ["holidays", "Hari Libur"]].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} data-testid={`tab-${k}`}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${tab === k ? "border-[#00A0A0] text-[#00A0A0]" : "border-transparent text-slate-500"}`}>{l}</button>
        ))}
      </div>
      {tab === "regions" && <RegionsAreas />}
      {tab === "branches" && <Branches />}
      {tab === "holidays" && <Holidays />}
    </div>
  );
}

function Modal({ title, children, onClose, onSave }) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md" onClick={(e) => e.stopPropagation()} data-testid="md-modal">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h3 className="font-display font-bold">{title}</h3>
          <button onClick={onClose}><X size={20} className="text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-1">{children}</div>
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-100">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md">Batal</button>
          <button onClick={onSave} className={btnPrimary + " px-4 py-2"} data-testid="md-save">Simpan</button>
        </div>
      </div>
    </div>
  );
}

function RegionsAreas() {
  const [regions, setRegions] = useState([]);
  const [areas, setAreas] = useState([]);
  const [rName, setRName] = useState("");
  const [aName, setAName] = useState("");
  const [aRegion, setARegion] = useState("");
  const [editR, setEditR] = useState(null);
  const [editA, setEditA] = useState(null);

  const load = () => {
    api.get("/regions").then((r) => setRegions(r.data)).catch(() => {});
    api.get("/areas").then((r) => setAreas(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const addRegion = async (e) => { e.preventDefault(); try { await api.post("/regions", { nama: rName }); toast.success("Region ditambahkan"); setRName(""); load(); } catch (err) { toast.error(apiError(err)); } };
  const delRegion = async (r) => { if (!window.confirm(`Hapus region "${r.nama}"?`)) return; try { await api.delete(`/regions/${r.id}`); toast.success("Region dihapus"); load(); } catch (err) { toast.error(apiError(err)); } };
  const saveRegion = async () => { try { await api.put(`/regions/${editR.id}`, { nama: editR.nama }); toast.success("Region diperbarui"); setEditR(null); load(); } catch (err) { toast.error(apiError(err)); } };

  const addArea = async (e) => { e.preventDefault(); if (!aRegion) { toast.error("Pilih region dulu"); return; } try { await api.post("/areas", { nama: aName, region: aRegion }); toast.success("Area ditambahkan"); setAName(""); load(); } catch (err) { toast.error(apiError(err)); } };
  const delArea = async (a) => { if (!window.confirm(`Hapus area "${a.nama}"?`)) return; try { await api.delete(`/areas/${a.id}`); toast.success("Area dihapus"); load(); } catch (err) { toast.error(apiError(err)); } };
  const saveArea = async () => { try { await api.put(`/areas/${editA.id}`, { nama: editA.nama, region: editA.region }); toast.success("Area diperbarui"); setEditA(null); load(); } catch (err) { toast.error(apiError(err)); } };

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
        <h3 className="font-display font-semibold flex items-center gap-2 mb-3"><MapPin size={16} className="text-[#00A0A0]" /> Region ({regions.length})</h3>
        <form onSubmit={addRegion} className="flex gap-2 mb-3">
          <input className={inp + " flex-1"} placeholder="Nama region baru" value={rName} onChange={(e) => setRName(e.target.value)} required data-testid="region-name" />
          <button className={btnPrimary + " px-3"} data-testid="region-add"><Plus size={16} /></button>
        </form>
        <div className="max-h-[50vh] overflow-y-auto divide-y divide-slate-100">
          {regions.length === 0 && <div className="text-center text-slate-400 py-6 text-sm">Belum ada region</div>}
          {regions.map((r) => (
            <div key={r.id} className="flex items-center justify-between py-2" data-testid={`region-row-${r.nama}`}>
              <span className="text-sm">{r.nama}</span>
              <div className="flex gap-1">
                <button onClick={() => setEditR({ id: r.id, nama: r.nama })} className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" title="Edit"><Pencil size={14} /></button>
                <button onClick={() => delRegion(r)} className="text-red-500 hover:bg-red-50 p-1.5 rounded" title="Hapus"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
        <h3 className="font-display font-semibold flex items-center gap-2 mb-3"><Building2 size={16} className="text-[#00A0A0]" /> Area ({areas.length})</h3>
        <form onSubmit={addArea} className="flex flex-wrap gap-2 mb-3">
          <select className={inp} value={aRegion} onChange={(e) => setARegion(e.target.value)} data-testid="area-region">
            <option value="">Pilih Region</option>{regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
          </select>
          <input className={inp + " flex-1 min-w-[140px]"} placeholder="Nama area baru" value={aName} onChange={(e) => setAName(e.target.value)} required data-testid="area-name" />
          <button className={btnPrimary + " px-3"} data-testid="area-add"><Plus size={16} /></button>
        </form>
        <div className="max-h-[50vh] overflow-y-auto divide-y divide-slate-100">
          {areas.length === 0 && <div className="text-center text-slate-400 py-6 text-sm">Belum ada area</div>}
          {areas.map((a) => (
            <div key={a.id} className="flex items-center justify-between py-2" data-testid={`area-row-${a.nama}`}>
              <span className="text-sm">{a.nama} <span className="text-xs text-slate-400">• {a.region}</span></span>
              <div className="flex gap-1">
                <button onClick={() => setEditA({ id: a.id, nama: a.nama, region: a.region })} className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" title="Edit"><Pencil size={14} /></button>
                <button onClick={() => delArea(a)} className="text-red-500 hover:bg-red-50 p-1.5 rounded" title="Hapus"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {editR && (
        <Modal title="Ubah Region" onClose={() => setEditR(null)} onSave={saveRegion}>
          <label className="text-xs font-semibold text-slate-500">Nama Region</label>
          <input className={inp + " w-full mt-1"} value={editR.nama} onChange={(e) => setEditR({ ...editR, nama: e.target.value })} data-testid="region-edit-name" />
        </Modal>
      )}
      {editA && (
        <Modal title="Ubah Area" onClose={() => setEditA(null)} onSave={saveArea}>
          <label className="text-xs font-semibold text-slate-500">Region</label>
          <select className={inp + " w-full mt-1 mb-2"} value={editA.region} onChange={(e) => setEditA({ ...editA, region: e.target.value })} data-testid="area-edit-region">
            {regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
          </select>
          <label className="text-xs font-semibold text-slate-500">Nama Area</label>
          <input className={inp + " w-full mt-1"} value={editA.nama} onChange={(e) => setEditA({ ...editA, nama: e.target.value })} data-testid="area-edit-name" />
        </Modal>
      )}
    </div>
  );
}

function BranchModal({ regions, initial, onClose, onSaved }) {
  const isEdit = initial.mode === "edit";
  const [form, setForm] = useState(initial.data);
  const [region, setRegion] = useState(initial.data.region || "");
  const [areas, setAreas] = useState([]);

  useEffect(() => {
    if (region) api.get("/areas", { params: { region } }).then((r) => setAreas(r.data)).catch(() => setAreas([]));
    else setAreas([]);
  }, [region]);

  const save = async () => {
    try {
      const payload = { kode_outlet_bsi: form.kode_outlet_bsi, nama_cabang: form.nama_cabang, jenis_outlet: form.jenis_outlet, area: form.area, status: "aktif" };
      if (isEdit) await api.put(`/branches/${initial.data.id}`, payload);
      else await api.post("/branches", payload);
      toast.success(isEdit ? "Cabang diperbarui" : "Cabang ditambahkan");
      onSaved();
    } catch (err) { toast.error(apiError(err)); }
  };

  return (
    <Modal title={isEdit ? "Ubah Cabang" : "Tambah Cabang"} onClose={onClose} onSave={save}>
      <label className="text-xs font-semibold text-slate-500">Region</label>
      <select className={inp + " w-full mt-1 mb-2"} value={region} onChange={(e) => { setRegion(e.target.value); setForm({ ...form, area: "" }); }} data-testid="branch-region">
        <option value="">Pilih Region</option>{regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
      </select>
      <label className="text-xs font-semibold text-slate-500">Area</label>
      <select className={inp + " w-full mt-1 mb-2"} value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} data-testid="branch-area">
        <option value="">Pilih Area</option>{areas.map((a) => <option key={a.id} value={a.nama}>{a.nama}</option>)}
      </select>
      <label className="text-xs font-semibold text-slate-500">Kode Outlet</label>
      <input className={inp + " w-full mt-1 mb-2"} value={form.kode_outlet_bsi} onChange={(e) => setForm({ ...form, kode_outlet_bsi: e.target.value })} data-testid="branch-kode" />
      <label className="text-xs font-semibold text-slate-500">Nama Cabang</label>
      <input className={inp + " w-full mt-1 mb-2"} value={form.nama_cabang} onChange={(e) => setForm({ ...form, nama_cabang: e.target.value })} data-testid="branch-nama" />
      <label className="text-xs font-semibold text-slate-500">Jenis Outlet</label>
      <select className={inp + " w-full mt-1"} value={form.jenis_outlet} onChange={(e) => setForm({ ...form, jenis_outlet: e.target.value })} data-testid="branch-jenis">
        {["KC", "KCP", "KK", "KLS"].map((j) => <option key={j} value={j}>{j}</option>)}
      </select>
    </Modal>
  );
}

function Branches() {
  const [branches, setBranches] = useState([]);
  const [regions, setRegions] = useState([]);
  const [areas, setAreas] = useState([]);
  const [region, setRegion] = useState("");
  const [area, setArea] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(null);

  useEffect(() => { api.get("/regions").then((r) => setRegions(r.data)); }, []);
  useEffect(() => { if (region) api.get("/areas", { params: { region } }).then((r) => setAreas(r.data)); else setAreas([]); setArea(""); }, [region]);
  const loadBranches = () => {
    if (!area) { setBranches([]); return; }
    setLoading(true);
    api.get("/branches", { params: { area } }).then((r) => setBranches(r.data)).finally(() => setLoading(false));
  };
  useEffect(() => { loadBranches(); }, [area]);

  const del = async (b) => { if (!window.confirm(`Hapus cabang "${b.nama_cabang}"?`)) return; try { await api.delete(`/branches/${b.id}`); toast.success("Cabang dihapus"); loadBranches(); } catch (err) { toast.error(apiError(err)); } };

  const sel = "px-3 py-2 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]";
  const filtered = branches.filter((b) => !q || b.nama_cabang.toLowerCase().includes(q.toLowerCase()) || b.kode_outlet_bsi.toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <div className="flex flex-wrap gap-3 mb-4">
        <select className={sel} data-testid="mb-region" value={region} onChange={(e) => setRegion(e.target.value)}>
          <option value="">Pilih Region</option>{regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
        </select>
        <select className={sel} data-testid="mb-area" value={area} onChange={(e) => setArea(e.target.value)}>
          <option value="">Pilih Area</option>{areas.map((a) => <option key={a.id} value={a.nama}>{a.nama}</option>)}
        </select>
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm outline-none focus:border-[#00A0A0]" placeholder="Cari cabang..." value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <button data-testid="branch-add" onClick={() => setModal({ mode: "new", data: { kode_outlet_bsi: "", nama_cabang: "", jenis_outlet: "KC", area: area || "", region: region || "" } })} className={btnPrimary + " px-4 py-2"}><Plus size={16} /> Tambah Cabang</button>
      </div>
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? <div className="flex justify-center py-16"><Loader2 className="animate-spin text-[#00A0A0]" /></div> : (
          <div className="overflow-x-auto max-h-[60vh]">
            <table className="w-full text-sm">
              <thead className="sticky top-0"><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Kode Outlet</th>
                <th className="text-left font-semibold px-4 py-3">Nama Cabang</th>
                <th className="text-left font-semibold px-4 py-3">Jenis</th>
                <th className="text-right font-semibold px-4 py-3">Aksi</th>
              </tr></thead>
              <tbody>
                {!area && <tr><td colSpan={4} className="text-center text-slate-400 py-10">Pilih region & area untuk melihat cabang</td></tr>}
                {area && filtered.length === 0 && !loading && <tr><td colSpan={4} className="text-center text-slate-400 py-10">Tidak ada cabang</td></tr>}
                {filtered.map((b) => (
                  <tr key={b.id} className="border-b border-slate-100 hover:bg-slate-50/60">
                    <td className="px-4 py-2.5 font-mono text-xs">{b.kode_outlet_bsi}</td>
                    <td className="px-4 py-2.5">{b.nama_cabang}</td>
                    <td className="px-4 py-2.5"><span className="text-xs bg-[#E6F6F6] text-[#00A0A0] px-2 py-0.5 rounded">{b.jenis_outlet}</span></td>
                    <td className="px-4 py-2.5 text-right">
                      <button onClick={() => setModal({ mode: "edit", data: { id: b.id, kode_outlet_bsi: b.kode_outlet_bsi, nama_cabang: b.nama_cabang, jenis_outlet: b.jenis_outlet, area: b.area, region: b.region } })} className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" title="Edit"><Pencil size={15} /></button>
                      <button onClick={() => del(b)} className="text-red-500 hover:bg-red-50 p-1.5 rounded ml-1" title="Hapus"><Trash2 size={15} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {modal && <BranchModal regions={regions} initial={modal} onClose={() => setModal(null)} onSaved={() => { setModal(null); loadBranches(); }} />}
    </div>
  );
}

function Holidays() {
  const [holidays, setHolidays] = useState([]);
  const [form, setForm] = useState({ tanggal: "", keterangan: "" });
  const [showHist, setShowHist] = useState(false);
  const [hist, setHist] = useState([]);

  const load = () => api.get("/holidays").then((r) => setHolidays(r.data));
  const loadHist = () => api.get("/holidays/history").then((r) => setHist(r.data)).catch(() => setHist([]));
  useEffect(() => { load(); }, []);
  useEffect(() => { if (showHist) loadHist(); }, [showHist]);

  const add = async (e) => {
    e.preventDefault();
    try { await api.post("/holidays", form); toast.success("Hari libur ditambahkan"); setForm({ tanggal: "", keterangan: "" }); load(); if (showHist) loadHist(); }
    catch (err) { toast.error(apiError(err)); }
  };
  const del = async (h) => {
    try { await api.delete(`/holidays/${h.id}`); toast.success("Hari libur dihapus"); load(); if (showHist) loadHist(); }
    catch (err) { toast.error(apiError(err)); }
  };

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <form onSubmit={add} className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-3 h-fit">
        <h3 className="font-display font-semibold">Tambah Hari Libur</h3>
        <div><label className="text-xs font-semibold text-slate-500">Tanggal</label><input type="date" className={inp + " w-full mt-1"} value={form.tanggal} onChange={(e) => setForm({ ...form, tanggal: e.target.value })} required data-testid="hf-date" /></div>
        <div><label className="text-xs font-semibold text-slate-500">Keterangan</label><input className={inp + " w-full mt-1"} value={form.keterangan} onChange={(e) => setForm({ ...form, keterangan: e.target.value })} required data-testid="hf-ket" /></div>
        <button className={btnPrimary + " w-full py-2"} data-testid="hf-submit"><CalendarPlus size={16} /> Tambah</button>
        <p className="text-xs text-slate-400">Hari libur tidak dihitung dalam SLA approval.</p>
        <button type="button" onClick={() => setShowHist((s) => !s)} data-testid="holiday-history-toggle" className="w-full flex items-center justify-center gap-2 text-sm font-medium text-[#00A0A0] hover:bg-[#E6F6F6] py-2 rounded-md border border-[#00A0A0]/30">
          <History size={15} /> {showHist ? "Sembunyikan Riwayat" : "Lihat Riwayat"}
        </button>
      </form>
      <div className="md:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
            <th className="text-left font-semibold px-4 py-3">Tanggal</th><th className="text-left font-semibold px-4 py-3">Keterangan</th><th className="px-4 py-3"></th>
          </tr></thead>
          <tbody>
            {holidays.length === 0 && <tr><td colSpan={3} className="text-center text-slate-400 py-10">Belum ada hari libur</td></tr>}
            {holidays.map((h) => (
              <tr key={h.id} className="border-b border-slate-100">
                <td className="px-4 py-2.5">{h.tanggal}</td><td className="px-4 py-2.5">{h.keterangan}</td>
                <td className="px-4 py-2.5 text-right"><button onClick={() => del(h)} className="text-red-500 hover:bg-red-50 p-1.5 rounded"><Trash2 size={15} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {showHist && (
          <div className="border-t border-slate-200 p-4" data-testid="holiday-history-panel">
            <h4 className="font-display font-semibold text-sm mb-2 flex items-center gap-2"><History size={15} className="text-[#00A0A0]" /> Riwayat Perubahan Hari Libur</h4>
            {hist.length === 0 ? <div className="text-center text-slate-400 py-6 text-sm">Belum ada riwayat</div> : (
              <div className="space-y-2 max-h-[40vh] overflow-y-auto">
                {hist.map((h) => {
                  const v = h.new_value || h.old_value || {};
                  const added = h.action === "add_holiday";
                  return (
                    <div key={h.id} className="flex items-start gap-2 text-sm bg-slate-50 rounded-md px-3 py-2 border border-slate-100">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded whitespace-nowrap ${added ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{added ? "Ditambahkan" : "Dihapus"}</span>
                      <div className="flex-1">
                        <div className="text-slate-700">{v.tanggal || "-"} — {v.keterangan || "-"}</div>
                        <div className="text-xs text-slate-400">oleh {h.nama} (NIP {h.nip}) • {new Date(h.created_at).toLocaleString("id-ID")}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
