import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { apiError } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { ShieldAlert, Loader2, Upload } from "lucide-react";
import { toast } from "sonner";
import { formatRupiah } from "../lib/format";

export default function RiskAssessment() {
  const navigate = useNavigate();
  const [notes, setNotes] = useState(null);

  const load = () => api.get("/notes").then((r) => setNotes(r.data.filter((n) => n.ra_required))).catch(() => setNotes([]));
  useEffect(() => { load(); }, []);

  const update = async (n, status, file_path) => {
    try { await api.post(`/notes/${n.id}/risk-assessment`, { status, file_path }); toast.success("Status Risk Assessment diperbarui"); load(); }
    catch (err) { toast.error(apiError(err)); }
  };

  const uploadAndSet = async (n, e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    try {
      const { data } = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await update(n, "Selesai", data.file_path);
    } catch (err) { toast.error(apiError(err)); }
  };

  if (!notes) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  return (
    <div>
      <PageHeader title="Risk Assessment (FRA Unit)" subtitle="Nota dengan RAC tidak sepenuhnya terpenuhi wajib melalui Risk Assessment" icon={ShieldAlert} />
      <div className="space-y-3" data-testid="ra-list">
        {notes.length === 0 && <div className="text-center text-slate-400 py-16 bg-white rounded-lg border border-slate-200">Tidak ada nota yang memerlukan Risk Assessment</div>}
        {notes.map((n) => {
          const ra = n.risk_assessment || {};
          return (
            <div key={n.id} className="bg-white rounded-lg border border-slate-200 shadow-sm p-5" data-testid={`ra-${n.id}`}>
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                  <div className="font-medium text-slate-800">{n.nomor_nota || "Draft"} — {n.customer?.nama}</div>
                  <div className="text-xs text-slate-500 mt-1">{n.area} • {n.region} • Nilai {formatRupiah(n.nilai_kewenangan_pemutus)}</div>
                  <div className="mt-2 flex items-center gap-2"><StatusBadge status={n.status} /><span className="text-xs text-slate-500">RA: {ra.status || "Belum dilakukan"}</span></div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => navigate(`/notes/${n.id}`)} className="text-sm border border-slate-300 rounded-md px-3 py-1.5 hover:bg-slate-50">Detail</button>
                  <select className="px-3 py-1.5 border border-slate-300 rounded-md text-sm bg-white" value={ra.status || "Belum dilakukan"} onChange={(e) => update(n, e.target.value)} data-testid={`ra-status-${n.id}`}>
                    {["Belum dilakukan", "Dalam proses", "Selesai"].map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <label className="text-sm bg-[#F0B43C] hover:bg-[#D9A236] text-white rounded-md px-3 py-1.5 cursor-pointer flex items-center gap-1">
                    <Upload size={14} /> Upload & Selesai
                    <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => uploadAndSet(n, e)} data-testid={`ra-upload-${n.id}`} />
                  </label>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
