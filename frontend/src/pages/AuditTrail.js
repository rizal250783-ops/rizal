import { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { ScrollText, Loader2 } from "lucide-react";

export default function AuditTrail() {
  const [logs, setLogs] = useState(null);
  useEffect(() => { api.get("/audit").then((r) => setLogs(r.data)).catch(() => setLogs([])); }, []);
  if (!logs) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  return (
    <div>
      <PageHeader title="Audit Trail" subtitle={`${logs.length} aktivitas terakhir`} icon={ScrollText} />
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto max-h-[70vh]">
          <table className="w-full text-sm">
            <thead className="sticky top-0"><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
              <th className="text-left font-semibold px-4 py-3">Waktu</th>
              <th className="text-left font-semibold px-4 py-3">User</th>
              <th className="text-left font-semibold px-4 py-3">NIP</th>
              <th className="text-left font-semibold px-4 py-3">Aktivitas</th>
              <th className="text-left font-semibold px-4 py-3">Entity</th>
            </tr></thead>
            <tbody data-testid="audit-table-body">
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-slate-100 hover:bg-slate-50/60">
                  <td className="px-4 py-2.5 text-xs text-slate-500">{new Date(l.created_at).toLocaleString("id-ID")}</td>
                  <td className="px-4 py-2.5 font-medium">{l.nama}</td>
                  <td className="px-4 py-2.5 text-slate-600">{l.nip}</td>
                  <td className="px-4 py-2.5"><span className="text-xs bg-[#E6F6F6] text-[#00A0A0] px-2 py-0.5 rounded">{l.action}</span></td>
                  <td className="px-4 py-2.5 text-slate-500 text-xs">{l.entity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
