import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { formatRupiah } from "../lib/format";
import { FileText, FilePlus2, Eye, Search, Loader2 } from "lucide-react";

export default function NotesList() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notes, setNotes] = useState(null);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => { api.get("/notes").then((r) => setNotes(r.data)).catch(() => setNotes([])); }, []);

  if (!notes) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  const statuses = [...new Set(notes.map((n) => n.status))];
  const filtered = notes.filter((n) => {
    const okQ = !q || (n.customer?.nama || "").toLowerCase().includes(q.toLowerCase()) || (n.nomor_nota || "").toLowerCase().includes(q.toLowerCase());
    const okS = !statusFilter || n.status === statusFilter;
    return okQ && okS;
  });

  return (
    <div>
      <PageHeader
        title={user.role === "RCO" ? "Nota Saya" : "Daftar Nota"}
        subtitle={`${filtered.length} nota ditemukan`}
        icon={FileText}
        action={user.role === "RCO" && (
          <button data-testid="new-note-btn" onClick={() => navigate("/notes/new")} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2">
            <FilePlus2 size={18} /> Buat Nota
          </button>
        )}
      />

      <div className="flex gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input data-testid="search-notes" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nomor nota / nama nasabah..."
            className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none" />
        </div>
        <select data-testid="filter-status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]">
          <option value="">Semua Status</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Nomor Nota</th>
                <th className="text-left font-semibold px-4 py-3">Nasabah</th>
                {user.role !== "RCO" && <th className="text-left font-semibold px-4 py-3">Area</th>}
                <th className="text-right font-semibold px-4 py-3">Nilai Kewenangan</th>
                <th className="text-right font-semibold px-4 py-3">Total Kewajiban</th>
                <th className="text-left font-semibold px-4 py-3">Status</th>
                <th className="text-center font-semibold px-4 py-3">Aksi</th>
              </tr>
            </thead>
            <tbody data-testid="notes-table-body">
              {filtered.length === 0 && (
                <tr><td colSpan={7} className="text-center text-slate-400 py-10">Belum ada nota</td></tr>
              )}
              {filtered.map((n) => (
                <tr key={n.id} className="border-b border-slate-100 hover:bg-slate-50/60 cursor-pointer" onClick={() => navigate(`/notes/${n.id}`)} data-testid={`note-row-${n.id}`}>
                  <td className="px-4 py-3 font-medium text-slate-800">{n.nomor_nota || <span className="text-slate-400 italic">Draft</span>}</td>
                  <td className="px-4 py-3">{n.customer?.nama || "-"}</td>
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
