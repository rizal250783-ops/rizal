import { useEffect, useState } from "react";
import api from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

export default function TimelinePage() {
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    api.get("/cases").then((r) => {
      setCases(r.data);
      if (r.data.length) setSelected(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (selected) api.get(`/cases/${selected}`).then((r) => setDetail(r.data));
  }, [selected]);

  const timeline = detail ? [...(detail.timeline || [])].sort((a, b) => (a.tanggal < b.tanggal ? 1 : -1)) : [];

  return (
    <div data-testid="timeline-page" className="space-y-5 max-w-4xl">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Timeline Perkara</h1>
        <p className="text-sm text-slate-500 mt-1">Perjalanan perkara dari registrasi hingga Inkracht / Eksekusi / Settlement</p>
      </div>

      <Select value={selected} onValueChange={setSelected}>
        <SelectTrigger data-testid="timeline-case-select" className="w-full md:w-96 bg-white">
          <SelectValue placeholder="Pilih perkara" />
        </SelectTrigger>
        <SelectContent>
          {cases.map((c) => <SelectItem key={c.id} value={c.id}>{c.nomor_perkara}</SelectItem>)}
        </SelectContent>
      </Select>

      {detail && (
        <div className="bg-white border border-slate-200 rounded-md p-6">
          <div className="flex flex-wrap items-center gap-2 mb-6">
            <p className="font-heading font-semibold text-slate-900">{detail.nomor_perkara}</p>
            <Badge variant="outline" className="border-toska text-toska-dark">{detail.status_perkara}</Badge>
            <Badge className={detail.status_aktif === "AKTIF" ? "bg-toska hover:bg-toska" : ""} variant={detail.status_aktif === "AKTIF" ? "default" : "secondary"}>{detail.status_aktif}</Badge>
          </div>
          <div className="border-l-2 border-slate-200 ml-2 space-y-6" data-testid="timeline-events">
            {timeline.map((t) => (
              <div key={t.id} className="relative pl-6">
                <span className={`absolute -left-[7px] top-1 h-3 w-3 rounded-full ${t.type === "dokumen" ? "bg-gold" : t.type === "agenda" ? "bg-slate-400" : "bg-toska"}`} />
                <p className="text-xs text-slate-400">{fmtDate(t.tanggal)}</p>
                <p className="text-sm font-semibold text-slate-900">{t.judul}</p>
                <p className="text-sm text-slate-500">{t.keterangan}</p>
              </div>
            ))}
            {timeline.length === 0 && <p className="text-sm text-slate-500 pl-6">Belum ada timeline.</p>}
          </div>
          <div className="flex gap-4 mt-6 pt-4 border-t border-slate-200 text-xs text-slate-500">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-toska inline-block" /> Status/Perkara</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-slate-400 inline-block" /> Agenda Sidang</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-gold inline-block" /> Dokumen</span>
          </div>
        </div>
      )}
    </div>
  );
}
