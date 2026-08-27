import { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { Bell, Check, CheckCheck, Loader2 } from "lucide-react";

export default function Notifications() {
  const [data, setData] = useState(null);

  const load = () => api.get("/notifications").then((r) => setData(r.data)).catch(() => setData({ items: [], unread: 0 }));
  useEffect(() => { load(); }, []);

  const markRead = async (id) => { await api.post(`/notifications/${id}/read`); load(); };
  const markAll = async () => { await api.post("/notifications/read-all"); load(); };

  if (!data) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  return (
    <div>
      <PageHeader title="Notifikasi" subtitle={`${data.unread} belum dibaca`} icon={Bell}
        action={data.unread > 0 && <button onClick={markAll} data-testid="mark-all-read" className="text-sm text-[#00A0A0] font-medium flex items-center gap-1 hover:underline"><CheckCheck size={16} /> Tandai semua dibaca</button>} />
      <div className="space-y-2 max-w-3xl" data-testid="notifications-list">
        {data.items.length === 0 && <div className="text-center text-slate-400 py-16 bg-white rounded-lg border border-slate-200">Tidak ada notifikasi</div>}
        {data.items.map((n) => (
          <div key={n.id} data-testid={`notif-${n.id}`} className={`bg-white rounded-lg border p-4 flex items-start gap-3 ${n.is_read ? "border-slate-200" : "border-[#F0B43C] bg-[#FDF7EB]/40"}`}>
            <div className={`w-2 h-2 rounded-full mt-2 ${n.is_read ? "bg-slate-300" : "bg-[#F0B43C]"}`} />
            <div className="flex-1">
              <p className="text-sm text-slate-800">{n.message}</p>
              <div className="text-xs text-slate-500 mt-1">{n.nomor_nota} • {n.nama_nasabah} • {n.tanggal} {n.jam}</div>
            </div>
            {!n.is_read && <button onClick={() => markRead(n.id)} className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" title="Tandai dibaca"><Check size={16} /></button>}
          </div>
        ))}
      </div>
    </div>
  );
}
