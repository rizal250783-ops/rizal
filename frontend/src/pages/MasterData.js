import { useEffect, useState } from "react";
import api, { apiError } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Database, CalendarPlus, Trash2, Loader2, Search } from "lucide-react";
import { toast } from "sonner";

export default function MasterData() {
  const [tab, setTab] = useState("branches");
  return (
    <div>
      <PageHeader title="Master Data" subtitle="Kelola data cabang & hari libur" icon={Database} />
      <div className="flex gap-2 mb-4 border-b border-slate-200">
        {[["branches", "Cabang"], ["holidays", "Hari Libur"]].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} data-testid={`tab-${k}`}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${tab === k ? "border-[#00A0A0] text-[#00A0A0]" : "border-transparent text-slate-500"}`}>{l}</button>
        ))}
      </div>
      {tab === "branches" ? <Branches /> : <Holidays />}
    </div>
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

  useEffect(() => { api.get("/regions").then((r) => setRegions(r.data)); }, []);
  useEffect(() => { if (region) api.get("/areas", { params: { region } }).then((r) => setAreas(r.data)); else setAreas([]); setArea(""); }, [region]);
  useEffect(() => {
    if (!area) { setBranches([]); return; }
    setLoading(true);
    api.get("/branches", { params: { area } }).then((r) => setBranches(r.data)).finally(() => setLoading(false));
  }, [area]);

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
      </div>
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? <div className="flex justify-center py-16"><Loader2 className="animate-spin text-[#00A0A0]" /></div> : (
          <div className="overflow-x-auto max-h-[60vh]">
            <table className="w-full text-sm">
              <thead className="sticky top-0"><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Kode Outlet</th>
                <th className="text-left font-semibold px-4 py-3">Nama Cabang</th>
                <th className="text-left font-semibold px-4 py-3">Jenis</th>
              </tr></thead>
              <tbody>
                {!area && <tr><td colSpan={3} className="text-center text-slate-400 py-10">Pilih region & area untuk melihat cabang</td></tr>}
                {filtered.map((b) => (
                  <tr key={b.id} className="border-b border-slate-100 hover:bg-slate-50/60">
                    <td className="px-4 py-2.5 font-mono text-xs">{b.kode_outlet_bsi}</td>
                    <td className="px-4 py-2.5">{b.nama_cabang}</td>
                    <td className="px-4 py-2.5"><span className="text-xs bg-[#E6F6F6] text-[#00A0A0] px-2 py-0.5 rounded">{b.jenis_outlet}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Holidays() {
  const [holidays, setHolidays] = useState([]);
  const [form, setForm] = useState({ tanggal: "", keterangan: "" });
  const load = () => api.get("/holidays").then((r) => setHolidays(r.data));
  useEffect(() => { load(); }, []);

  const add = async (e) => {
    e.preventDefault();
    try { await api.post("/holidays", form); toast.success("Hari libur ditambahkan"); setForm({ tanggal: "", keterangan: "" }); load(); }
    catch (err) { toast.error(apiError(err)); }
  };
  const del = async (h) => { await api.delete(`/holidays/${h.id}`); load(); };
  const inp = "px-3 py-2 border border-slate-300 rounded-md text-sm outline-none focus:border-[#00A0A0]";

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <form onSubmit={add} className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-3 h-fit">
        <h3 className="font-display font-semibold">Tambah Hari Libur</h3>
        <div><label className="text-xs font-semibold text-slate-500">Tanggal</label><input type="date" className={inp + " w-full mt-1"} value={form.tanggal} onChange={(e) => setForm({ ...form, tanggal: e.target.value })} required data-testid="hf-date" /></div>
        <div><label className="text-xs font-semibold text-slate-500">Keterangan</label><input className={inp + " w-full mt-1"} value={form.keterangan} onChange={(e) => setForm({ ...form, keterangan: e.target.value })} required data-testid="hf-ket" /></div>
        <button className="w-full bg-[#00A0A0] text-white font-semibold py-2 rounded-md text-sm flex items-center justify-center gap-2" data-testid="hf-submit"><CalendarPlus size={16} /> Tambah</button>
        <p className="text-xs text-slate-400">Hari libur tidak dihitung dalam SLA approval.</p>
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
      </div>
    </div>
  );
}
