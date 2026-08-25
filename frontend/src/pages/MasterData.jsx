import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Badge } from "@/components/ui/badge";

function Section({ title, items, testid }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5" data-testid={testid}>
      <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-3">{title}</p>
      <div className="flex flex-wrap gap-2">
        {(items || []).filter(Boolean).map((s) => (
          <Badge key={s} variant="outline" className="border-toska text-toska-dark">{s}</Badge>
        ))}
        {(!items || items.filter(Boolean).length === 0) && <p className="text-sm text-slate-400">Belum ada data.</p>}
      </div>
    </div>
  );
}

export default function MasterData() {
  const [master, setMaster] = useState(null);

  useEffect(() => { api.get("/master-data").then((r) => setMaster(r.data)); }, []);

  if (!master) return <p className="text-sm text-slate-500">Memuat master data...</p>;

  return (
    <div data-testid="master-data-page" className="space-y-5">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Master Data</h1>
        <p className="text-sm text-slate-500 mt-1">Referensi data dan daftar nilai standar aplikasi</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Status Perkara (18 Tahapan)" items={master.status_perkara} testid="master-status" />
        <Section title="Agenda Sidang" items={master.agenda_list} testid="master-agenda" />
        <Section title="Kategori Dokumen" items={master.dokumen_kategori} testid="master-dokumen" />
        <Section title="Risk Rating" items={master.risk_ratings} testid="master-risk" />
        <Section title="Region Terdaftar" items={master.regions} testid="master-region" />
        <Section title="Area Terdaftar" items={master.areas} testid="master-area" />
        <Section title="Cabang Terdaftar" items={master.cabangs} testid="master-cabang" />
        <Section title="Tahun Perkara" items={master.tahun} testid="master-tahun" />
      </div>
    </div>
  );
}
