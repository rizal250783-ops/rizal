import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { apiError, downloadBlob } from "@/lib/api";
import { rp, fmtDate } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Search, FileDown, Eye, Pencil, Trash2 } from "lucide-react";

export const riskBadge = (r) =>
  r === "High Risk" ? "destructive" : r === "Medium Risk" ? "default" : "secondary";

export default function Cases() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [master, setMaster] = useState(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ region: "all", area: "all", cabang: "all", status: "all", tahun: "all", risk_rating: "all", aktif: "all" });
  const [delTarget, setDelTarget] = useState(null);
  const [delMode, setDelMode] = useState("NONAKTIF");
  const [delAlasan, setDelAlasan] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.get("/master-data").then((r) => setMaster(r.data)); }, []);

  const load = useCallback(() => {
    const params = {};
    if (search) params.search = search;
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params[k] = v; });
    api.get("/cases", { params }).then((r) => setCases(r.data));
  }, [search, filters]);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [load]);

  const submitDelete = async () => {
    if (!delAlasan.trim()) {
      toast.error("Alasan wajib diisi");
      return;
    }
    setLoading(true);
    try {
      await api.post(`/cases/${delTarget.id}/delete-request`, { mode: delMode, alasan: delAlasan });
      toast.success("Request penghapusan dikirim, menunggu approval Dept Head");
      setDelTarget(null);
      setDelAlasan("");
      load();
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setLoading(false);
    }
  };

  const exportExcel = async () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params.set(k, v); });
    try {
      await downloadBlob(`/export/cases?${params.toString()}`, "laporan_perkara.xlsx");
      toast.success("File Excel berhasil diunduh");
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const areaOptions = filters.region !== "all" && master?.region_area_map?.[filters.region]
    ? master.region_area_map[filters.region]
    : [...new Set([...(master?.areas || []), ...Object.values(master?.region_area_map || {}).flat()])];

  const FS = ({ k, label, options }) => (
    <Select value={filters[k]} onValueChange={(v) => setFilters((f) => ({ ...f, [k]: v, ...(k === "region" ? { area: "all" } : {}) }))}>
      <SelectTrigger data-testid={`case-filter-${k}`} className="w-full bg-white">
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Semua {label}</SelectItem>
        {(options || []).filter(Boolean).map((o) => <SelectItem key={o} value={String(o)}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  );

  return (
    <div data-testid="cases-page" className="space-y-5">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Data Perkara</h1>
          <p className="text-sm text-slate-500 mt-1">{cases.length} perkara ditemukan</p>
        </div>
        <div className="flex gap-2">
          <Button data-testid="export-excel-button" variant="outline" onClick={exportExcel}>
            <FileDown className="h-4 w-4 mr-2" /> Export Excel
          </Button>
          <Button data-testid="add-case-button" className="bg-toska hover:bg-toska-hover text-white" onClick={() => navigate("/perkara/baru")}>
            <Plus className="h-4 w-4 mr-2" /> Input Perkara Baru
          </Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            data-testid="case-search-input"
            className="pl-9"
            placeholder="Cari nomor perkara, penggugat, tergugat, CIF, atau loan..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          <FS k="region" label="Region" options={master?.regions} />
          <FS k="area" label="Area" options={areaOptions} />
          <FS k="cabang" label="Cabang" options={master?.cabangs} />
          <FS k="status" label="Status" options={master?.status_perkara} />
          <FS k="tahun" label="Tahun" options={master?.tahun} />
          <FS k="risk_rating" label="Risk" options={master?.risk_ratings} />
          <FS k="aktif" label="Keaktifan" options={["AKTIF", "TIDAK AKTIF"]} />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nomor Perkara</TableHead>
              <TableHead>Penggugat</TableHead>
              <TableHead>Cabang</TableHead>
              <TableHead>Status Perkara</TableHead>
              <TableHead>Total Kewajiban</TableHead>
              <TableHead>Risk</TableHead>
              <TableHead>Keaktifan</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cases.map((c) => (
              <TableRow key={c.id} data-testid={`case-row-${c.nomor_perkara}`} className="hover:bg-slate-50">
                <TableCell>
                  <p className="font-medium text-slate-900">{c.nomor_perkara}</p>
                  <p className="text-xs text-slate-500">{c.nama_pn}</p>
                </TableCell>
                <TableCell className="text-sm">{(c.penggugat || []).join(", ")}</TableCell>
                <TableCell className="text-sm">{c.cabang}</TableCell>
                <TableCell><Badge variant="outline" className="border-toska text-toska-dark whitespace-nowrap">{c.status_perkara}</Badge></TableCell>
                <TableCell className="text-sm font-medium whitespace-nowrap">{rp(c.total_kewajiban)}</TableCell>
                <TableCell>{c.risk_rating ? <Badge variant={riskBadge(c.risk_rating)}>{c.risk_rating}</Badge> : "-"}</TableCell>
                <TableCell>
                  <Badge variant={c.status_aktif === "AKTIF" ? "default" : "secondary"}
                    className={c.status_aktif === "AKTIF" ? "bg-toska hover:bg-toska" : ""}>
                    {c.status_aktif}
                  </Badge>
                </TableCell>
                <TableCell className="text-right whitespace-nowrap">
                  <Button data-testid={`view-case-${c.id}`} variant="ghost" size="icon" onClick={() => navigate(`/perkara/${c.id}`)}>
                    <Eye className="h-4 w-4 text-toska" />
                  </Button>
                  <Button data-testid={`edit-case-${c.id}`} variant="ghost" size="icon" onClick={() => navigate(`/perkara/${c.id}/edit`)}>
                    <Pencil className="h-4 w-4 text-slate-600" />
                  </Button>
                  <Button data-testid={`delete-case-${c.id}`} variant="ghost" size="icon" onClick={() => { setDelTarget(c); setDelMode("NONAKTIF"); setDelAlasan(""); }}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {cases.length === 0 && (
              <TableRow><TableCell colSpan={8} className="text-center text-sm text-slate-500 py-8">Tidak ada data perkara.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!delTarget} onOpenChange={() => setDelTarget(null)}>
        <DialogContent data-testid="delete-case-dialog">
          <DialogHeader>
            <DialogTitle>Hapus Perkara — {delTarget?.nomor_perkara}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <RadioGroup value={delMode} onValueChange={setDelMode}>
              <div className="flex items-start gap-3 border border-slate-200 rounded-md p-3">
                <RadioGroupItem data-testid="delete-mode-nonaktif" value="NONAKTIF" id="m1" className="mt-1" />
                <Label htmlFor="m1" className="cursor-pointer">
                  <span className="font-semibold text-slate-900">Status Perkara: TIDAK AKTIF</span>
                  <p className="text-xs text-slate-500 mt-1">Perkara dihentikan namun data tetap tersimpan.</p>
                </Label>
              </div>
              <div className="flex items-start gap-3 border border-slate-200 rounded-md p-3">
                <RadioGroupItem data-testid="delete-mode-permanent" value="PERMANENT" id="m2" className="mt-1" />
                <Label htmlFor="m2" className="cursor-pointer">
                  <span className="font-semibold text-red-600">Hapus Perkara Permanen</span>
                  <p className="text-xs text-slate-500 mt-1">Data perkara dan dokumen dihapus permanen.</p>
                </Label>
              </div>
            </RadioGroup>
            <div>
              <Label>{delMode === "NONAKTIF" ? "Alasan penghentian perkara" : "Alasan penghapusan perkara"} *</Label>
              <Textarea data-testid="delete-reason-input" value={delAlasan} onChange={(e) => setDelAlasan(e.target.value)} rows={3} />
            </div>
            <p className="text-xs text-slate-500">Kedua pilihan wajib melalui approval Dept Head Legal Perdata.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDelTarget(null)}>Batal</Button>
            <Button data-testid="delete-submit-button" variant="destructive" disabled={loading} onClick={submitDelete}>
              Ajukan Penghapusan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
