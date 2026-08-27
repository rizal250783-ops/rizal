import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { formatRupiah } from "../lib/format";
import { FileText, FilePlus2, Eye, Search, Loader2, X, Filter } from "lucide-react";

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

  useEffect(() => { api.get("/notes").then((r) => setNotes(r.data)).catch(() => setNotes([])); }, []);

  // Keep the status filter in sync if the query param changes (e.g. navigating from Dashboard)
  useEffect(() => {
    const s = searchParams.get("status") || "";
    setStatusFilter(s);
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
    setQ("");
    setStatusFilter("");
    setRegionFilter("");
    setAreaFilter("");
    setCabangFilter("");
    setSearchParams({});
  };

  const selectCls = "px-3 py-2.5 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0] focus:ring-2 focus:ring-[#00A0A0]/20";

  return (
    <div>
      <PageHeader
        title={user.role === "RCO" ? "Nota Saya" : "Daftar Nota"}
        subtitle={`${filtered.length} dari ${notes.length} nota`}
        icon={FileText}
        action={user.role === "RCO" && (
          <button data-testid="new-note-btn" onClick={() => navigate("/notes/new")} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2">
            <FilePlus2 size={18} /> Buat Nota
          </button>
        )}
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

          {activeCount > 0 && (
            <button data-testid="reset-filters" onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-md border border-slate-300">
              <X size={15} /> Reset
            </button>
          )}
        </div>
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
