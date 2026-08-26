import { useEffect, useState, useCallback } from "react";
import api, { apiError, downloadBlob } from "@/lib/api";
import { rp, fmtDate, bulanDiff } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileDown } from "lucide-react";

const REPORT_TYPES = [
  { id: "semua", label: "Laporan Seluruh Perkara" },
  { id: "aktif", label: "Laporan Perkara Aktif" },
  { id: "kewajiban", label: "Laporan Nilai Kewajiban" },
  { id: "region", label: "Laporan per Region" },
  { id: "area", label: "Laporan per Area" },
  { id: "cabang", label: "Laporan per Cabang" },
  { id: "status", label: "Laporan Status Perkara" },
  { id: "aging", label: "Laporan Aging Perkara" },
  { id: "executive", label: "Executive Summary Management" },
];

const groupBy = (arr, field) => {
  const m = {};
  arr.forEach((c) => {
    const k = c[field] || "Lainnya";
    if (!m[k]) m[k] = { name: k, count: 0, total: 0 };
    m[k].count += 1;
    m[k].total += c.total_kewajiban || 0;
  });
  return Object.values(m).sort((a, b) => b.count - a.count);
};

const agingBucket = (c) => {
  const m = bulanDiff(c.tanggal_input);
  if (m < 3) return "0-3 bulan";
  if (m < 6) return "3-6 bulan";
  if (m < 12) return "6-12 bulan";
  return ">12 bulan";
};

export default function Reports() {
  const [type, setType] = useState("semua");
  const [cases, setCases] = useState([]);
  const [master, setMaster] = useState(null);
  const [filters, setFilters] = useState({ region: "all", area: "all", cabang: "all", status: "all", tahun: "all", risk_rating: "all" });

  useEffect(() => { api.get("/master-data").then((r) => setMaster(r.data)); }, []);

  const load = useCallback(() => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params[k] = v; });
    if (type === "aktif") params.aktif = "AKTIF";
    api.get("/cases", { params }).then((r) => setCases(r.data));
  }, [filters, type]);

  useEffect(() => { load(); }, [load]);

  const exportExcel = async () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params.set(k, v); });
    if (type === "aktif") params.set("aktif", "AKTIF");
    try {
      await downloadBlob(`/export/cases?${params.toString()}`, `laporan_${type}.xlsx`);
      toast.success("File Excel berhasil diunduh");
    } catch (e) { toast.error(apiError(e)); }
  };

  const areaOptions = filters.region !== "all" && master?.region_area_map?.[filters.region]
    ? master.region_area_map[filters.region]
    : [...new Set([...(master?.areas || []), ...Object.values(master?.region_area_map || {}).flat()])];

  const FS = ({ k, label, options }) => (
    <Select value={filters[k]} onValueChange={(v) => setFilters((f) => ({ ...f, [k]: v, ...(k === "region" ? { area: "all" } : {}) }))}>
      <SelectTrigger data-testid={`report-filter-${k}`} className="w-full bg-white"><SelectValue placeholder={label} /></SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Semua {label}</SelectItem>
        {(options || []).filter(Boolean).map((o) => <SelectItem key={o} value={String(o)}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  );

  const renderGroupTable = (field) => (
    <Table>
      <TableHeader><TableRow><TableHead>{field === "status_perkara" ? "Status" : field.charAt(0).toUpperCase() + field.slice(1)}</TableHead><TableHead>Jumlah Perkara</TableHead><TableHead>Total Kewajiban</TableHead></TableRow></TableHeader>
      <TableBody>
        {groupBy(cases, field).map((g) => (
          <TableRow key={g.name}><TableCell className="font-medium">{g.name}</TableCell><TableCell>{g.count}</TableCell><TableCell>{rp(g.total)}</TableCell></TableRow>
        ))}
      </TableBody>
    </Table>
  );

  const renderMain = () => {
    if (type === "region") return renderGroupTable("region");
    if (type === "area") return renderGroupTable("area");
    if (type === "cabang") return renderGroupTable("cabang");
    if (type === "status") return renderGroupTable("status_perkara");
    if (type === "aging") {
      const buckets = ["0-3 bulan", "3-6 bulan", "6-12 bulan", ">12 bulan"];
      return (
        <Table>
          <TableHeader><TableRow><TableHead>Kategori Aging</TableHead><TableHead>Jumlah Perkara</TableHead><TableHead>Total Kewajiban</TableHead></TableRow></TableHeader>
          <TableBody>
            {buckets.map((b) => {
              const list = cases.filter((c) => agingBucket(c) === b);
              return (
                <TableRow key={b} data-testid={`aging-${b}`}>
                  <TableCell className="font-medium">{b}</TableCell>
                  <TableCell>{list.length}</TableCell>
                  <TableCell>{rp(list.reduce((a, c) => a + (c.total_kewajiban || 0), 0))}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      );
    }
    if (type === "executive") {
      const aktif = cases.filter((c) => c.status_aktif === "AKTIF");
      const high = cases.filter((c) => c.risk_rating === "High Risk");
      return (
        <div className="p-6 space-y-4" data-testid="executive-summary">
          <p className="font-heading text-lg font-bold text-slate-900">Executive Summary Management</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-slate-200 rounded-md p-4"><p className="text-xs uppercase tracking-widest text-slate-500">Total Perkara</p><p className="font-heading text-2xl font-bold text-toska">{cases.length}</p></div>
            <div className="border border-slate-200 rounded-md p-4"><p className="text-xs uppercase tracking-widest text-slate-500">Perkara Aktif</p><p className="font-heading text-2xl font-bold text-toska">{aktif.length}</p></div>
            <div className="border border-slate-200 rounded-md p-4"><p className="text-xs uppercase tracking-widest text-slate-500">High Risk</p><p className="font-heading text-2xl font-bold text-red-500">{high.length}</p></div>
          </div>
          <div className="border border-slate-200 rounded-md p-4">
            <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">Total Nilai Kewajiban (Aktif)</p>
            <p className="font-heading text-3xl font-bold text-slate-900">{rp(aktif.reduce((a, c) => a + (c.total_kewajiban || 0), 0))}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500 mb-2">Perkara High Risk — Perlu Perhatian</p>
            {high.map((c) => (
              <div key={c.id} className="flex justify-between border-b border-slate-100 py-2 text-sm">
                <span className="font-medium text-slate-900">{c.nomor_perkara}</span>
                <span className="text-slate-500">{c.status_perkara}</span>
                <span className="font-medium">{rp(c.total_kewajiban)}</span>
              </div>
            ))}
            {high.length === 0 && <p className="text-sm text-slate-500">Tidak ada perkara high risk.</p>}
          </div>
        </div>
      );
    }
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nomor Perkara</TableHead><TableHead>Penggugat</TableHead><TableHead>Region</TableHead>
            <TableHead>Area</TableHead><TableHead>Cabang</TableHead><TableHead>Status</TableHead>
            <TableHead>Total Kewajiban</TableHead><TableHead>Keaktifan</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cases.map((c) => (
            <TableRow key={c.id}>
              <TableCell className="font-medium">{c.nomor_perkara}</TableCell>
              <TableCell className="text-sm">{(c.penggugat || []).join(", ")}</TableCell>
              <TableCell className="text-sm">{c.region}</TableCell>
              <TableCell className="text-sm">{c.area}</TableCell>
              <TableCell className="text-sm">{c.cabang}</TableCell>
              <TableCell><Badge variant="outline" className="border-toska text-toska-dark whitespace-nowrap">{c.status_perkara}</Badge></TableCell>
              <TableCell className="text-sm font-medium whitespace-nowrap">{rp(c.total_kewajiban)}</TableCell>
              <TableCell><Badge variant={c.status_aktif === "AKTIF" ? "default" : "secondary"} className={c.status_aktif === "AKTIF" ? "bg-toska hover:bg-toska" : ""}>{c.status_aktif}</Badge></TableCell>
            </TableRow>
          ))}
          {cases.length === 0 && <TableRow><TableCell colSpan={8} className="text-center text-sm text-slate-500 py-8">Tidak ada data.</TableCell></TableRow>}
        </TableBody>
      </Table>
    );
  };

  return (
    <div data-testid="reports-page" className="space-y-5">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Laporan</h1>
          <p className="text-sm text-slate-500 mt-1">{REPORT_TYPES.find((t) => t.id === type)?.label}</p>
        </div>
        <Button data-testid="report-export-button" variant="outline" onClick={exportExcel}>
          <FileDown className="h-4 w-4 mr-2" /> Export Excel
        </Button>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4 space-y-3">
        <Select value={type} onValueChange={setType}>
          <SelectTrigger data-testid="report-type-select" className="w-full md:w-96"><SelectValue /></SelectTrigger>
          <SelectContent>
            {REPORT_TYPES.map((t) => <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
          <FS k="region" label="Region" options={master?.regions} />
          <FS k="area" label="Area" options={areaOptions} />
          <FS k="cabang" label="Cabang" options={master?.cabangs} />
          <FS k="status" label="Status" options={master?.status_perkara} />
          <FS k="tahun" label="Tahun" options={master?.tahun} />
          <FS k="risk_rating" label="Risk" options={master?.risk_ratings} />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">{renderMain()}</div>
    </div>
  );
}
