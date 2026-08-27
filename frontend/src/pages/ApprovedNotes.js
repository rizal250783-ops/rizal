import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatRupiah } from "../lib/format";
import { CheckCircle2, Download, Eye, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API } from "../lib/api";

export default function ApprovedNotes() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notes, setNotes] = useState(null);

  useEffect(() => {
    api.get("/notes", { params: { status: "Final Approved" } }).then((r) => setNotes(r.data)).catch(() => setNotes([]));
  }, []);

  const download = async (n) => {
    try {
      const token = localStorage.getItem("rcg_token");
      const res = await fetch(`${API}/notes/${n.id}/pdf`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Gagal unduh"); }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `Nota_${n.nomor_nota.replace(/[/ ]/g, "_")}.pdf`;
      a.click(); URL.revokeObjectURL(url);
    } catch (e) { toast.error(e.message); }
  };

  if (!notes) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  return (
    <div>
      <PageHeader title="Nota Telah Approved" subtitle={`${notes.length} nota final approved`} icon={CheckCircle2} />
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Nomor Nota</th>
                <th className="text-left font-semibold px-4 py-3">Nasabah</th>
                <th className="text-left font-semibold px-4 py-3">Area / Region</th>
                <th className="text-left font-semibold px-4 py-3">Pemutus</th>
                <th className="text-left font-semibold px-4 py-3">Tgl Approved</th>
                <th className="text-right font-semibold px-4 py-3">Nilai Kewenangan</th>
                <th className="text-center font-semibold px-4 py-3">Aksi</th>
              </tr>
            </thead>
            <tbody data-testid="approved-table-body">
              {notes.length === 0 && <tr><td colSpan={7} className="text-center text-slate-400 py-10">Belum ada nota approved</td></tr>}
              {notes.map((n) => (
                <tr key={n.id} className="border-b border-slate-100 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">{n.nomor_nota}</td>
                  <td className="px-4 py-3">{n.customer?.nama}</td>
                  <td className="px-4 py-3 text-slate-600">{n.area}<br /><span className="text-xs text-slate-400">{n.region}</span></td>
                  <td className="px-4 py-3">{n.final_approver_nama}<br /><span className="text-xs text-[#00A0A0]">{n.final_approver_level}</span></td>
                  <td className="px-4 py-3 text-slate-600">{n.approved_date}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatRupiah(n.nilai_kewenangan_pemutus)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" onClick={() => navigate(`/notes/${n.id}`)} data-testid={`view-${n.id}`}><Eye size={16} /></button>
                      <button className="text-[#B4842A] hover:bg-[#FDF7EB] p-1.5 rounded" onClick={() => download(n)} data-testid={`download-${n.id}`}><Download size={16} /></button>
                    </div>
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
