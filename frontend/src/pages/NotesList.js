import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { formatRupiah } from "../lib/format";
import { FileText, FilePlus2, Eye, Search, Loader2, X, Filter, Download, BookmarkPlus, Bookmark } from "lucide-react";
import { toast } from "sonner";

export default function NotesList() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [notes, setNotes] = useState(null);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "");
  const [regionFilter, setRegionFilter] = useState(searchParams.get("region") || "");
  const [areaFilter, setAreaFilter] = useState(searchParams.get("area") || "");
  const [cabangFilter, setCabangFilter] = useState(searchParams.get("cabang") || "");

  const PRESET_KEY = `rcg_note_presets_${user?.nip || "anon"}`;
  const [presets, setPresets] = useState([]);

  useEffect(() => { api.get("/notes").then((r) => setNotes(r.data)).catch(() => setNotes([])); }, []);

  useEffect(() => {
    try { const s = localStorage.getItem(PRESET_KEY); if (s) setPresets(JSON.parse(s)); } catch { /* ignore */ }
  }, [PRESET_KEY]);

  // Keep filters in sync when navigating from Dashboard (query params)
  useEffect(() => {
    setStatusFilter(searchParams.get("status") || "");
    setRegionFilter(searchParams.get("region") || "");
    setAreaFilter(searchParams.get("area") || "");
    setCabangFilter(searchParams.get("cabang") || "");
  }, [searchParams]);

  const options = useMemo(() => {
    const list = notes || [];
    const uniq = (arr) => [...new Set(arr.filter(Boolean))].sort();
    return {
      statuses: uniq(list.map((n) => n.status)),
      regions: uniq(list.map((n) => n.region)),
      areas: uniq(list.map((n) => n.area)),
      cabangs: uniq(list.flatMap((n) => (n.facilities || []).map((f) => f.nama_cabang))),
    };
  }, [notes]);

  if (!notes) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  const cabangOf = (n) => (n.facilities || []).map((f) => f.nama_cabang || "").join(" ");

  const filtered = notes.filter((n) => {
    const term = q.trim().toLowerCase();
    const okQ = !term
      || (n.customer?.nama || "").toLowerCase().includes(term)
      || (n.nomor_nota || "").toLowerCase().includes(term)
      || cabangOf(n).toLowerCase().includes(term);
    const okS = !statusFilter || n.status === statusFilter;
    const okR = !regionFilter || n.region === regionFilter;
    const okA = !areaFilter || n.area === areaFilter;
    const okC = !cabangFilter || (n.facilities || []).some((f) => f.nama_cabang === cabangFilter);
    return okQ && okS && okR && okA && okC;
  });

  const activeCount = [statusFilter, regionFilter, areaFilter, cabangFilter].filter(Boolean).length + (q.trim() ? 1 : 0);

  const resetFilters = () => {
    setQ(""); setStatusFilter(""); setRegionFilter(""); setAreaFilter(""); setCabangFilter("");
    setSearchParams({});
  };

  const persistPresets = (arr) => {
    setPresets(arr);
    try { localStorage.setItem(PRESET_KEY, JSON.stringify(arr)); } catch { /* ignore */ }
  };

  const savePreset = () => {
    if (activeCount === 0) { toast.error("Atur minimal satu filter dulu sebelum menyimpan preset"); return; }
    const name = window.prompt("Beri nama preset filter ini:");
    if (!name || !name.trim()) return;
    const p = { name: name.trim(), q, statusFilter, regionFilter, areaFilter, cabangFilter };
    persistPresets([...presets.filter((x) => x.name !== p.name), p]);
    toast.success(`Preset "${p.name}" disimpan`);
  };

  const applyPreset = (p) => {
    setQ(p.q || ""); setStatusFilter(p.statusFilter || ""); setRegionFilter(p.regionFilter || "");
    setAreaFilter(p.areaFilter || ""); setCabangFilter(p.cabangFilter || "");
    setSearchParams({});
  };

  const deletePreset = (name) => { persistPresets(presets.filter((x) => x.name !== name)); };

  const exportCsv = () => {
    const headers = ["Nomor Nota", "Nasabah", "Cabang", "Area", "Region", "Nilai Kewenangan", "Total Kewajiban", "Status"];
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = filtered.map((n) => [
      n.nomor_nota || "Draft",
      n.customer?.nama || "",
      (n.facilities || []).map((f) => f.nama_cabang).filter(Boolean).join("; "),
      n.area || "",
      n.region || "",
      Math.round(Number(n.nilai_kewenangan_pemutus || 0)),
      Math.round(Number(n.total_kewajiban || 0)),
      n.status || "",
    ]);
    const csv = "\ufeff" + [headers, ...rows].map((r) => r.map(esc).join(",")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Daftar_Nota_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`${filtered.length} nota diekspor ke CSV`);
  };

  const selectCls = "px-3 py-2.5 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0] focus:ring-2 focus:ring-[#00A0A0]/20";

  return (
    <div>
      <PageHeader
        title={user.role === "RCO" ? "Nota Saya" : "Daftar Nota"}
        subtitle={`${filtered.length} dari ${notes.length} nota`}
        icon={FileText}
        action={
          <div className="flex items-center gap-2">
            <button data-testid="export-csv-btn" onClick={exportCsv} disabled={filtered.length === 0}
              className="bg-white border border-slate-300 hover:border-[#00A0A0] hover:text-[#00A0A0] text-slate-600 font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
              <Download size={17} /> Unduh CSV
            </button>
            {user.role === "RCO" && (
              <button data-testid="new-note-btn" onClick={() => navigate("/notes/new")} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2">
                <FilePlus2 size={18} /> Buat Nota
              </button>
            )}
          </div>
        }
      />

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 mb-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search size={16} className="absolute left-3 top-3 text-slate-400" />
            <input data-testid="search-notes" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nomor nota / nama nasabah / cabang..."
              className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none" />
          </div>

          <select data-testid="filter-status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            <option value="">Semua Status</option>
            {options.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>

          {user.role === "RCG" && (
            <select data-testid="filter-region" value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)} className={selectCls}>
              <option value="">Semua Region</option>
              {options.regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          )}

          {(user.role === "RCG" || user.role === "RCRM") && (
            <select data-testid="filter-area" value={areaFilter} onChange={(e) => setAreaFilter(e.target.value)} className={selectCls}>
              <option value="">Semua Area</option>
              {options.areas.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          )}

          <select data-testid="filter-cabang" value={cabangFilter} onChange={(e) => setCabangFilter(e.target.value)} className={selectCls}>
            <option value="">Semua Cabang</option>
            {options.cabangs.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>

          <button data-testid="save-preset" onClick={savePreset}
            className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-[#00A0A0] hover:bg-[#E6F6F6] rounded-md border border-[#00A0A0]/40">
            <BookmarkPlus size={15} /> Simpan Preset
          </button>

          {activeCount > 0 && (
            <button data-testid="reset-filters" onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-md border border-slate-300">
              <X size={15} /> Reset
            </button>
          )}
        </div>

        {presets.length > 0 && (
          <div className="mt-3 flex items-center gap-2 flex-wrap" data-testid="preset-list">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1"><Bookmark size={13} /> Preset:</span>
            {presets.map((p) => (
              <span key={p.name} className="inline-flex items-center gap-1 bg-slate-100 hover:bg-[#E6F6F6] rounded-full pl-3 pr-1 py-1 text-xs">
                <button onClick={() => applyPreset(p)} data-testid={`preset-${p.name}`} className="font-medium text-slate-700 hover:text-[#00A0A0]">{p.name}</button>
                <button onClick={() => deletePreset(p.name)} title="Hapus preset" className="text-slate-400 hover:text-red-500 rounded-full p-0.5"><X size={12} /></button>
              </span>
            ))}
          </div>
        )}

        {activeCount > 0 && (
          <div className="mt-2.5 flex items-center gap-2 text-xs text-slate-500">
            <Filter size={13} /> {activeCount} filter aktif
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Nomor Nota</th>
                <th className="text-left font-semibold px-4 py-3">Nasabah</th>
                <th className="text-left font-semibold px-4 py-3">Cabang</th>
                {user.role !== "RCO" && <th className="text-left font-semibold px-4 py-3">Area</th>}
                <th className="text-right font-semibold px-4 py-3">Nilai Kewenangan</th>
                <th className="text-right font-semibold px-4 py-3">Total Kewajiban</th>
                <th className="text-left font-semibold px-4 py-3">Status</th>
                <th className="text-center font-semibold px-4 py-3">Aksi</th>
              </tr>
            </thead>
            <tbody data-testid="notes-table-body">
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="text-center text-slate-400 py-10">Tidak ada nota yang cocok dengan pencarian/filter</td></tr>
              )}
              {filtered.map((n) => (
                <tr key={n.id} className="border-b border-slate-100 hover:bg-slate-50/60 cursor-pointer" onClick={() => navigate(`/notes/${n.id}`)} data-testid={`note-row-${n.id}`}>
                  <td className="px-4 py-3 font-medium text-slate-800">{n.nomor_nota || <span className="text-slate-400 italic">Draft</span>}</td>
                  <td className="px-4 py-3">{n.customer?.nama || "-"}</td>
                  <td className="px-4 py-3 text-slate-600">{(n.facilities || []).map((f) => f.nama_cabang).filter(Boolean)[0] || "-"}</td>
                  {user.role !== "RCO" && <td className="px-4 py-3 text-slate-600">{n.area}</td>}
                  <td className="px-4 py-3 text-right tabular-nums">{formatRupiah(n.nilai_kewenangan_pemutus)}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{formatRupiah(n.total_kewajiban)}</td>
                  <td className="px-4 py-3"><StatusBadge status={n.status} /></td>
                  <td className="px-4 py-3 text-center">
                    <button className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" onClick={(e) => { e.stopPropagation(); navigate(`/notes/${n.id}`); }}>
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
