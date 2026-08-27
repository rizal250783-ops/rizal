import { useEffect, useMemo, useState } from "react";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { ScrollText, Loader2, Search, X, Eye, Filter, ShieldAlert } from "lucide-react";

const ACTION_LABEL = {
  login: "Login", create_note: "Buat Nota", update_note: "Ubah Nota", submit_note: "Submit Nota",
  forward_note: "Forward Nota", approve_note: "Approve Nota", reject_note: "Reject Nota",
  revisi_note: "Revisi Nota", download_pdf: "Unduh PDF", risk_assessment: "Risk Assessment",
  create_user: "Buat User", update_user: "Ubah User", reset_password: "Reset Password",
  delete_user: "Hapus User", export_excel: "Ekspor Excel", export_notes_excel: "Ekspor Excel",
  create_preset: "Buat Preset", delete_preset: "Hapus Preset",
  add_holiday: "Tambah Hari Libur", delete_holiday: "Hapus Hari Libur",
  create_region: "Tambah Region", update_region: "Ubah Region", delete_region: "Hapus Region",
  create_area: "Tambah Area", update_area: "Ubah Area", delete_area: "Hapus Area",
  create_branch: "Tambah Cabang", update_branch: "Ubah Cabang", delete_branch: "Hapus Cabang",
  access_denied: "Akses Ditolak",
};

function fmtVal(v) {
  if (v === null || v === undefined || v === "") return "-";
  if (typeof v === "number") return v.toLocaleString("id-ID");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

export default function AuditTrail() {
  const [logs, setLogs] = useState(null);
  const [meta, setMeta] = useState({ actions: [], entities: [] });
  const [detail, setDetail] = useState(null);
  const [f, setF] = useState({ q: "", action: "", entity: "", date_from: "", date_to: "" });

  useEffect(() => { api.get("/audit/meta").then((r) => setMeta(r.data)).catch(() => {}); }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      const params = {};
      Object.entries(f).forEach(([k, v]) => { if (v) params[k] = v; });
      setLogs(null);
      api.get("/audit", { params }).then((r) => setLogs(r.data)).catch(() => setLogs([]));
    }, 350);
    return () => clearTimeout(t);
  }, [f]);

  const activeCount = useMemo(() => Object.values(f).filter(Boolean).length, [f]);
  const reset = () => setF({ q: "", action: "", entity: "", date_from: "", date_to: "" });
  const deniedActive = f.action === "access_denied";
  const toggleDenied = () => setF({ ...f, action: deniedActive ? "" : "access_denied" });
  const deniedCount = useMemo(() => (logs || []).filter((l) => l.action === "access_denied").length, [logs]);

  const selectCls = "px-3 py-2.5 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0] focus:ring-2 focus:ring-[#00A0A0]/20";

  const changedKeys = (log) => {
    const oldV = log.old_value || {}; const newV = log.new_value || {};
    return [...new Set([...Object.keys(oldV), ...Object.keys(newV)])].filter((k) => k !== "updated_at");
  };
  const hasDetail = (log) => (log.old_value && Object.keys(log.old_value).length) || (log.new_value && Object.keys(log.new_value).length);

  return (
    <div>
      <PageHeader title="Panel Audit Global" subtitle={logs ? `${logs.length} aktivitas` : "Memuat..."} icon={ScrollText} />

      <button onClick={toggleDenied} data-testid="audit-quick-denied"
        className={`mb-4 flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-semibold border transition-colors ${
          deniedActive ? "bg-red-600 text-white border-red-600" : "bg-red-50 text-red-700 border-red-200 hover:bg-red-100"
        }`}>
        <ShieldAlert size={16} />
        {deniedActive ? "Menampilkan: Percobaan Akses Ditolak" : "Sorot Percobaan Akses Ditolak"}
        {!deniedActive && deniedCount > 0 && (
          <span className="bg-red-600 text-white text-[11px] rounded-full px-2 py-0.5">{deniedCount}</span>
        )}
      </button>


      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 mb-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <label className="text-xs font-semibold text-slate-500">Pelaku (nama / NIP)</label>
            <Search size={16} className="absolute left-3 top-8 text-slate-400" />
            <input data-testid="audit-search" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} placeholder="Cari pelaku..."
              className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 block">Aktivitas</label>
            <select data-testid="audit-action" className={selectCls} value={f.action} onChange={(e) => setF({ ...f, action: e.target.value })}>
              <option value="">Semua</option>
              {meta.actions.map((a) => <option key={a} value={a}>{ACTION_LABEL[a] || a}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 block">Entity</label>
            <select data-testid="audit-entity" className={selectCls} value={f.entity} onChange={(e) => setF({ ...f, entity: e.target.value })}>
              <option value="">Semua</option>
              {meta.entities.map((e2) => <option key={e2} value={e2}>{e2}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 block">Dari Tanggal</label>
            <input type="date" data-testid="audit-from" className={selectCls} value={f.date_from} onChange={(e) => setF({ ...f, date_from: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 block">Sampai Tanggal</label>
            <input type="date" data-testid="audit-to" className={selectCls} value={f.date_to} onChange={(e) => setF({ ...f, date_to: e.target.value })} />
          </div>
          {activeCount > 0 && (
            <button data-testid="audit-reset" onClick={reset} className="flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-md border border-slate-300">
              <X size={15} /> Reset
            </button>
          )}
        </div>
        {activeCount > 0 && <div className="mt-2.5 flex items-center gap-2 text-xs text-slate-500"><Filter size={13} /> {activeCount} filter aktif</div>}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {!logs ? (
          <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>
        ) : (
          <div className="overflow-x-auto max-h-[68vh]">
            <table className="w-full text-sm">
              <thead className="sticky top-0"><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Waktu</th>
                <th className="text-left font-semibold px-4 py-3">Pelaku</th>
                <th className="text-left font-semibold px-4 py-3">NIP</th>
                <th className="text-left font-semibold px-4 py-3">Aktivitas</th>
                <th className="text-left font-semibold px-4 py-3">Entity</th>
                <th className="text-center font-semibold px-4 py-3">Detail</th>
              </tr></thead>
              <tbody data-testid="audit-table-body">
                {logs.length === 0 && <tr><td colSpan={6} className="text-center text-slate-400 py-10">Tidak ada aktivitas yang cocok</td></tr>}
                {logs.map((l) => (
                  <tr key={l.id} className={`border-b border-slate-100 ${l.action === "access_denied" ? "bg-red-50/70 hover:bg-red-50" : "hover:bg-slate-50/60"}`}>
                    <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">{new Date(l.created_at).toLocaleString("id-ID")}</td>
                    <td className="px-4 py-2.5 font-medium">{l.nama}</td>
                    <td className="px-4 py-2.5 text-slate-600">{l.nip}</td>
                    <td className="px-4 py-2.5"><span className={`text-xs px-2 py-0.5 rounded whitespace-nowrap ${l.action === "access_denied" ? "bg-red-600 text-white" : "bg-[#E6F6F6] text-[#00A0A0]"}`}>{ACTION_LABEL[l.action] || l.action}</span></td>
                    <td className="px-4 py-2.5 text-slate-500 text-xs">{l.entity}</td>
                    <td className="px-4 py-2.5 text-center">
                      {hasDetail(l) ? (
                        <button onClick={() => setDetail(l)} className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" data-testid={`audit-detail-${l.id}`}><Eye size={15} /></button>
                      ) : <span className="text-slate-300">-</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {detail && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setDetail(null)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()} data-testid="audit-detail-modal">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div>
                <h3 className="font-display font-bold text-lg">{ACTION_LABEL[detail.action] || detail.action}</h3>
                <p className="text-xs text-slate-500 mt-0.5">oleh {detail.nama} (NIP {detail.nip}) — {new Date(detail.created_at).toLocaleString("id-ID")}</p>
              </div>
              <button onClick={() => setDetail(null)}><X size={20} className="text-slate-400" /></button>
            </div>
            <div className="p-6 overflow-y-auto space-y-2">
              {changedKeys(detail).length === 0 ? (
                <div className="text-center text-slate-400 py-6">Tidak ada rincian tambahan</div>
              ) : changedKeys(detail).map((k) => {
                const o = (detail.old_value || {})[k];
                const n = (detail.new_value || {})[k];
                const changed = String(o ?? "") !== String(n ?? "");
                return (
                  <div key={k} className="text-sm bg-slate-50 rounded-md px-3 py-2 border border-slate-100">
                    <div className="text-xs font-semibold text-slate-600 mb-0.5">{k}</div>
                    {detail.action === "update_user" && changed ? (
                      <div>
                        <span className="text-red-500 line-through">{fmtVal(o)}</span>{" "}
                        <span className="text-slate-400">&rarr;</span>{" "}
                        <span className="text-emerald-600 font-medium">{fmtVal(n)}</span>
                      </div>
                    ) : (
                      <div className="text-slate-700">{fmtVal(n !== undefined ? n : o)}</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
