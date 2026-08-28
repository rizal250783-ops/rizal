import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api, { apiError, API } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { formatRupiah } from "../lib/format";
import { FileText, FilePlus2, Eye, Search, Loader2, X, Filter, Download, FileSpreadsheet, BookmarkPlus, Bookmark, Share2, Users2 } from "lucide-react";
import { toast } from "sonner";

const ROLE_TABS = {
  RCO: [
    { key: "draft", label: "Draft Nota" },
    { key: "sent_reviewer", label: "Sent to Reviewer" },
    { key: "sent_committee", label: "Sent to Committee" },
    { key: "approved", label: "Nota Approved" },
    { key: "correction", label: "Nota Correction" },
    { key: "rejected", label: "Nota Rejected" },
  ],
  ACRM: [
    { key: "committee", label: "Nota Committee" },
    { key: "review", label: "Nota Review" },
    { key: "approved", label: "Nota Approved" },
    { key: "correction", label: "Nota Correction" },
    { key: "rejected", label: "Nota Rejected" },
  ],
  RCRM: [
    { key: "committee", label: "Nota Committee" },
    { key: "review", label: "Nota Review" },
    { key: "approved", label: "Nota Approved" },
    { key: "correction", label: "Nota Correction" },
    { key: "rejected", label: "Nota Rejected" },
  ],
  RCG: [
    { key: "committee", label: "Nota Committee" },
    { key: "approved", label: "Nota Approved" },
    { key: "correction", label: "Nota Correction" },
    { key: "rejected", label: "Nota Rejected" },
  ],
};

const lastActivity = (n) => {
  const aps = n.approvals || [];
  const last = aps[aps.length - 1];
  if (!last) return { text: "-", when: "" };
  const text = (n.disposisi_pemutus && n.status === "Final Approved" ? n.disposisi_pemutus : (last.disposisi || last.catatan)) || last.keputusan || "-";
  return { text, when: `${last.date || ""} ${last.time || ""}`.trim() };
};

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
  const [sharedPresets, setSharedPresets] = useState([]);
  const [shareModal, setShareModal] = useState(false);
  const [shareForm, setShareForm] = useState({ name: "", scope: "region", region: "" });

  const isAdmin = user?.is_user_admin;
  const tabs = ROLE_TABS[user?.role] || ROLE_TABS.RCG;
  const [activeTab, setActiveTab] = useState(tabs[0]?.key);

  useEffect(() => { api.get("/notes").then((r) => setNotes(r.data)).catch(() => setNotes([])); }, []);
  useEffect(() => { api.get("/presets").then((r) => setSharedPresets(r.data)).catch(() => setSharedPresets([])); }, []);

  useEffect(() => {
    try { const s = localStorage.getItem(PRESET_KEY); if (s) setPresets(JSON.parse(s)); } catch { /* ignore */ }
  }, [PRESET_KEY]);

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

  const tabCounts = tabs.reduce((acc, t) => {
    acc[t.key] = notes.filter((n) => n.category === t.key).length;
    return acc;
  }, {});
  const tabActionNeeded = tabs.reduce((acc, t) => {
    acc[t.key] = notes.some((n) => n.category === t.key && n.action_required);
    return acc;
  }, {});

  const filtered = notes.filter((n) => {
    const term = q.trim().toLowerCase();
    const okQ = !term
      || (n.customer?.nama || "").toLowerCase().includes(term)
      || (n.nomor_nota || "").toLowerCase().includes(term)
      || cabangOf(n).toLowerCase().includes(term);
    const okTab = n.category === activeTab;
    const okS = !statusFilter || n.status === statusFilter;
    const okR = !regionFilter || n.region === regionFilter;
    const okA = !areaFilter || n.area === areaFilter;
    const okC = !cabangFilter || (n.facilities || []).some((f) => f.nama_cabang === cabangFilter);
    return okQ && okTab && okS && okR && okA && okC;
  });

  const activeCount = [statusFilter, regionFilter, areaFilter, cabangFilter].filter(Boolean).length + (q.trim() ? 1 : 0);
  const currentFilters = () => ({ q: q.trim(), status: statusFilter, region: regionFilter, area: areaFilter, cabang: cabangFilter });

  const resetFilters = () => {
    setQ(""); setStatusFilter(""); setRegionFilter(""); setAreaFilter(""); setCabangFilter("");
    setSearchParams({});
  };

  const applyFilters = (fl) => {
    setQ(fl.q || ""); setStatusFilter(fl.status || ""); setRegionFilter(fl.region || "");
    setAreaFilter(fl.area || ""); setCabangFilter(fl.cabang || "");
    setSearchParams({});
  };

  // ---- Local presets ----
  const persistPresets = (arr) => {
    setPresets(arr);
    try { localStorage.setItem(PRESET_KEY, JSON.stringify(arr)); } catch { /* ignore */ }
  };
  const savePreset = () => {
    if (activeCount === 0) { toast.error("Atur minimal satu filter dulu sebelum menyimpan preset"); return; }
    const name = window.prompt("Beri nama preset filter ini:");
    if (!name || !name.trim()) return;
    const p = { name: name.trim(), ...currentFilters() };
    persistPresets([...presets.filter((x) => x.name !== p.name), p]);
    toast.success(`Preset "${p.name}" disimpan`);
  };
  const deletePreset = (name) => { persistPresets(presets.filter((x) => x.name !== name)); };

  // ---- Shared presets ----
  const openShare = () => {
    if (activeCount === 0) { toast.error("Atur minimal satu filter dulu sebelum membagikan preset"); return; }
    setShareForm({ name: "", scope: "region", region: options.regions[0] || "" });
    setShareModal(true);
  };
  const submitShare = async (e) => {
    e.preventDefault();
    try {
      await api.post("/presets", {
        name: shareForm.name.trim(),
        scope: shareForm.scope,
        region: shareForm.scope === "region" ? shareForm.region : null,
        filters: currentFilters(),
      });
      toast.success("Preset berhasil dibagikan");
      setShareModal(false);
      const r = await api.get("/presets"); setSharedPresets(r.data);
    } catch (err) { toast.error(apiError(err)); }
  };
  const deleteShared = async (id) => {
    try { await api.delete(`/presets/${id}`); setSharedPresets(sharedPresets.filter((x) => x.id !== id)); toast.success("Preset bersama dihapus"); }
    catch (err) { toast.error(apiError(err)); }
  };

  // ---- Exports ----
  const exportCsv = () => {
    const headers = ["Nomor Nota", "Nasabah", "Cabang", "Area", "Region", "Nilai Kewenangan", "Total Kewajiban", "Status"];
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = filtered.map((n) => [
      n.nomor_nota || "Draft", n.customer?.nama || "",
      (n.facilities || []).map((f) => f.nama_cabang).filter(Boolean).join("; "),
      n.area || "", n.region || "",
      Math.round(Number(n.nilai_kewenangan_pemutus || 0)), Math.round(Number(n.total_kewajiban || 0)), n.status || "",
    ]);
    const csv = "\ufeff" + [headers, ...rows].map((r) => r.map(esc).join(",")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `Daftar_Nota_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`${filtered.length} nota diekspor ke CSV`);
  };

  const exportExcel = async () => {
    try {
      const token = localStorage.getItem("rcg_token");
      const params = new URLSearchParams();
      const fl = currentFilters();
      Object.entries(fl).forEach(([k, v]) => { if (v) params.set(k, v); });
      if (activeTab) params.set("category", activeTab);
      const res = await fetch(`${API}/export/notes-excel?${params.toString()}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Gagal ekspor Excel");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const tabLabel = (tabs.find((t) => t.key === activeTab)?.label || "Daftar").replace(/\s+/g, "_");
      a.href = url; a.download = `Rekap_${tabLabel}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Rekap tab "${tabs.find((t) => t.key === activeTab)?.label}" diunduh`);
    } catch { toast.error("Gagal mengunduh Excel"); }
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
              className="bg-white border border-slate-300 hover:border-[#00A0A0] hover:text-[#00A0A0] text-slate-600 font-semibold px-3.5 py-2.5 rounded-md text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
              <Download size={16} /> CSV
            </button>
            <button data-testid="export-excel-btn" onClick={exportExcel} disabled={filtered.length === 0}
              className="bg-[#0F766E] hover:bg-[#0b5f58] text-white font-semibold px-3.5 py-2.5 rounded-md text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
              <FileSpreadsheet size={16} /> Rekap Tab
            </button>
            {user.role === "RCO" && (
              <button data-testid="new-note-btn" onClick={() => navigate("/notes/new")} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2">
                <FilePlus2 size={18} /> Buat Nota
              </button>
            )}
          </div>
        }
      />

      <div className="flex flex-wrap gap-1.5 mb-4 border-b border-slate-200" data-testid="note-tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            data-testid={`tab-${t.key}`}
            onClick={() => setActiveTab(t.key)}
            className={`relative px-4 py-2.5 text-sm font-semibold rounded-t-md -mb-px border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === t.key
                ? "border-[#00A0A0] text-[#00A0A0] bg-white"
                : "border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50"
            }`}
          >
            {tabActionNeeded[t.key] && (
              <span data-testid={`tab-alert-${t.key}`} title="Ada nota yang menunggu tindakan Anda" className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
              </span>
            )}
            {t.label}
            <span className={`text-[11px] px-1.5 py-0.5 rounded-full ${activeTab === t.key ? "bg-[#00A0A0] text-white" : "bg-slate-200 text-slate-600"}`}>
              {tabCounts[t.key] || 0}
            </span>
          </button>
        ))}
      </div>

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

          {isAdmin && (
            <button data-testid="share-preset" onClick={openShare}
              className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-[#B4842A] hover:bg-[#FDF7EB] rounded-md border border-[#F0B43C]/60">
              <Share2 size={15} /> Bagikan Preset
            </button>
          )}

          {activeCount > 0 && (
            <button data-testid="reset-filters" onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-md border border-slate-300">
              <X size={15} /> Reset
            </button>
          )}
        </div>

        {sharedPresets.length > 0 && (
          <div className="mt-3 flex items-center gap-2 flex-wrap" data-testid="shared-preset-list">
            <span className="text-xs font-semibold text-[#B4842A] flex items-center gap-1"><Users2 size={13} /> Preset Bersama:</span>
            {sharedPresets.map((p) => (
              <span key={p.id} className="inline-flex items-center gap-1 bg-[#FDF7EB] border border-[#F0B43C]/50 rounded-full pl-3 pr-1 py-1 text-xs" title={p.scope === "global" ? "Semua region" : p.region}>
                <button onClick={() => applyFilters(p.filters || {})} data-testid={`shared-preset-${p.name}`} className="font-medium text-[#8a6216] hover:text-[#B4842A]">
                  {p.name}<span className="ml-1 text-[10px] text-[#B4842A]/70">{p.scope === "global" ? "· Global" : `· ${(p.region || "").replace("RO ", "")}`}</span>
                </button>
                {isAdmin && <button onClick={() => deleteShared(p.id)} title="Hapus preset bersama" className="text-[#B4842A]/60 hover:text-red-500 rounded-full p-0.5"><X size={12} /></button>}
              </span>
            ))}
          </div>
        )}

        {presets.length > 0 && (
          <div className="mt-3 flex items-center gap-2 flex-wrap" data-testid="preset-list">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1"><Bookmark size={13} /> Preset Saya:</span>
            {presets.map((p) => (
              <span key={p.name} className="inline-flex items-center gap-1 bg-slate-100 hover:bg-[#E6F6F6] rounded-full pl-3 pr-1 py-1 text-xs">
                <button onClick={() => applyFilters(p)} data-testid={`preset-${p.name}`} className="font-medium text-slate-700 hover:text-[#00A0A0]">{p.name}</button>
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
                <th className="text-left font-semibold px-4 py-3">Disposisi / Catatan</th>
                <th className="text-left font-semibold px-4 py-3">Update (Tgl &amp; Jam)</th>
                <th className="text-left font-semibold px-4 py-3">Status</th>
                <th className="text-center font-semibold px-4 py-3">Aksi</th>
              </tr>
            </thead>
            <tbody data-testid="notes-table-body">
              {filtered.length === 0 && (
                <tr><td colSpan={10} className="text-center text-slate-400 py-10">Tidak ada nota pada kategori ini</td></tr>
              )}
              {filtered.map((n) => {
                const act = lastActivity(n);
                return (
                <tr key={n.id} className="border-b border-slate-100 hover:bg-slate-50/60 cursor-pointer" onClick={() => navigate(`/notes/${n.id}`)} data-testid={`note-row-${n.id}`}>
                  <td className="px-4 py-3 font-medium text-slate-800">{n.nomor_nota || <span className="text-slate-400 italic">Draft</span>}</td>
                  <td className="px-4 py-3">{n.customer?.nama || "-"}</td>
                  <td className="px-4 py-3 text-slate-600">{(n.facilities || []).map((f) => f.nama_cabang).filter(Boolean)[0] || "-"}</td>
                  {user.role !== "RCO" && <td className="px-4 py-3 text-slate-600">{n.area}</td>}
                  <td className="px-4 py-3 text-right tabular-nums">{formatRupiah(n.nilai_kewenangan_pemutus)}</td>
                  <td className="px-4 py-3 text-slate-600 max-w-[220px]"><span className="line-clamp-2" title={act.text}>{act.text}</span></td>
                  <td className="px-4 py-3 text-slate-500 whitespace-nowrap text-xs">{act.when || "-"}</td>
                  <td className="px-4 py-3"><StatusBadge status={n.status} /></td>
                  <td className="px-4 py-3 text-center">
                    <button className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" onClick={(e) => { e.stopPropagation(); navigate(`/notes/${n.id}`); }}>
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {shareModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShareModal(false)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md" onClick={(e) => e.stopPropagation()} data-testid="share-modal">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-display font-bold text-lg flex items-center gap-2"><Share2 size={18} className="text-[#B4842A]" /> Bagikan Preset</h3>
              <button onClick={() => setShareModal(false)}><X size={20} className="text-slate-400" /></button>
            </div>
            <form onSubmit={submitShare} className="p-6 space-y-3">
              <p className="text-xs text-slate-500">Preset ini akan tampil untuk pengguna sesuai cakupan yang dipilih, menggunakan kombinasi filter yang aktif saat ini.</p>
              <div>
                <label className="text-xs font-semibold text-slate-500">Nama Preset</label>
                <input className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none" value={shareForm.name} onChange={(e) => setShareForm({ ...shareForm, name: e.target.value })} required data-testid="share-name" />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-500">Cakupan</label>
                <select className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]" value={shareForm.scope} onChange={(e) => setShareForm({ ...shareForm, scope: e.target.value })} data-testid="share-scope">
                  <option value="region">Region tertentu</option>
                  <option value="global">Semua region (Global)</option>
                </select>
              </div>
              {shareForm.scope === "region" && (
                <div>
                  <label className="text-xs font-semibold text-slate-500">Region</label>
                  <select className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]" value={shareForm.region} onChange={(e) => setShareForm({ ...shareForm, region: e.target.value })} required data-testid="share-region">
                    <option value="">Pilih Region</option>
                    {options.regions.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              )}
              <button className="w-full bg-[#B4842A] hover:bg-[#96701f] text-white font-semibold py-2.5 rounded-md text-sm mt-2" data-testid="share-submit">Bagikan Preset</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
