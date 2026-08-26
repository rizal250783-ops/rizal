import { useEffect, useState } from "react";
import api, { apiError, downloadBlob } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileDown, Upload, HardDrive, Loader2, FileSpreadsheet } from "lucide-react";

export default function Database() {
  const [master, setMaster] = useState(null);
  const [lastExport, setLastExport] = useState(null);
  const [filters, setFilters] = useState({ tahun: "all", region: "all", area: "all", cabang: "all", status: "all", risk_rating: "all", aktif: "all" });
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/master-data").then((r) => setMaster(r.data));
    api.get("/export/last").then((r) => setLastExport(r.data)).catch(() => {});
  }, []);

  const doExport = async () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params.set(k, v); });
    setBusy(true);
    try {
      await downloadBlob(`/export/database?${params.toString()}`, "casewise_database_export.xlsx");
      toast.success("Database berhasil diexport");
      api.get("/export/last").then((r) => setLastExport(r.data)).catch(() => {});
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const doPreview = async () => {
    if (!file) { toast.error("Pilih file Excel terlebih dahulu"); return; }
    const fd = new FormData();
    fd.append("file", file);
    setBusy(true);
    try {
      const { data } = await api.post("/import/preview", fd);
      setPreview(data);
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const doImport = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/import/execute", { staging_id: preview.staging_id });
      toast.success(`Import selesai: ${data.imported} data diproses`);
      setPreview(null);
      setFile(null);
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const areaOptions = filters.region !== "all" && master?.region_area_map?.[filters.region]
    ? master.region_area_map[filters.region]
    : [...new Set([...(master?.areas || []), ...Object.values(master?.region_area_map || {}).flat()])];

  const FS = ({ k, label, options }) => (
    <Select value={filters[k]} onValueChange={(v) => setFilters((f) => ({ ...f, [k]: v, ...(k === "region" ? { area: "all" } : {}) }))}>
      <SelectTrigger data-testid={`db-filter-${k}`} className="w-full bg-white"><SelectValue placeholder={label} /></SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Semua {label}</SelectItem>
        {(options || []).filter(Boolean).map((o) => <SelectItem key={o} value={String(o)}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  );

  return (
    <div data-testid="database-page" className="space-y-5 max-w-5xl">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Database Management</h1>
        <p className="text-sm text-slate-500 mt-1">Export, import, dan backup manual database — khusus Dept Head Legal Perdata</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <div className="flex items-center gap-2">
          <HardDrive className="h-4 w-4 text-toska" />
          <p className="font-heading font-semibold text-slate-900">A. Export Database / Backup Manual</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          <FS k="tahun" label="Tahun" options={master?.tahun} />
          <FS k="region" label="Region" options={master?.regions} />
          <FS k="area" label="Area" options={areaOptions} />
          <FS k="cabang" label="Cabang" options={master?.cabangs} />
          <FS k="status" label="Status" options={master?.status_perkara} />
          <FS k="risk_rating" label="Risk" options={master?.risk_ratings} />
          <FS k="aktif" label="Keaktifan" options={["AKTIF", "TIDAK AKTIF"]} />
        </div>
        <Button data-testid="export-database-button" className="bg-toska hover:bg-toska-hover text-white" disabled={busy} onClick={doExport}>
          {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}
          EXPORT DATABASE
        </Button>
        <div className="bg-slate-50 border border-slate-200 rounded-md p-4 text-sm" data-testid="last-backup-info">
          <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-2">Informasi Backup Terakhir</p>
          {lastExport ? (
            <div className="flex flex-wrap gap-6">
              <span className="text-slate-600">Tanggal: <span className="font-medium text-slate-900">{fmtDate(lastExport.tanggal)}</span></span>
              <span className="text-slate-600">User: <span className="font-medium text-slate-900">{lastExport.user}</span></span>
              <span className="text-slate-600">Jumlah data: <span className="font-medium text-slate-900">{lastExport.jumlah} perkara</span></span>
            </div>
          ) : (
            <p className="text-slate-500">Belum pernah dilakukan export database.</p>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Upload className="h-4 w-4 text-toska" />
          <p className="font-heading font-semibold text-slate-900">B. Import Database</p>
        </div>
        <p className="text-sm text-slate-500">
          Format: Excel (.xlsx) sesuai template. Sistem memvalidasi format, duplikasi nomor perkara, dan field wajib sebelum import.
        </p>
        <Button data-testid="download-template-button" variant="outline" onClick={() => downloadBlob("/export/template", "template_import_casewise.xlsx")}>
          <FileSpreadsheet className="h-4 w-4 mr-2" /> Download Template Import
        </Button>
        <div className="flex flex-col md:flex-row gap-3 md:items-end">
          <div className="flex-1">
            <Label>File Excel (.xlsx)</Label>
            <Input data-testid="import-file-input" type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files[0])} />
          </div>
          <Button data-testid="preview-import-button" variant="outline" disabled={busy || !file} onClick={doPreview}>
            {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Validasi & Preview
          </Button>
        </div>
      </div>

      <Dialog open={!!preview} onOpenChange={() => setPreview(null)}>
        <DialogContent data-testid="import-preview-dialog" className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Konfirmasi Import Database</DialogTitle>
          </DialogHeader>
          {preview && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="border border-toska/40 bg-toska-light rounded-md p-3 text-center">
                  <p className="font-heading text-2xl font-bold text-toska-dark" data-testid="import-count-baru">{preview.baru}</p>
                  <p className="text-xs text-slate-500">Data Baru</p>
                </div>
                <div className="border border-gold/50 bg-gold-light rounded-md p-3 text-center">
                  <p className="font-heading text-2xl font-bold text-gold-hover" data-testid="import-count-update">{preview.update}</p>
                  <p className="text-xs text-slate-500">Data Update</p>
                </div>
                <div className="border border-red-300 bg-red-50 rounded-md p-3 text-center">
                  <p className="font-heading text-2xl font-bold text-red-500" data-testid="import-count-gagal">{preview.errors.length}</p>
                  <p className="text-xs text-slate-500">Error / Gagal</p>
                </div>
              </div>
              {preview.errors.length > 0 && (
                <div className="max-h-56 overflow-y-auto border border-slate-200 rounded-md">
                  <Table>
                    <TableHeader>
                      <TableRow><TableHead>Sheet</TableHead><TableHead>Baris</TableHead><TableHead>Kolom</TableHead><TableHead>Keterangan</TableHead></TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.errors.map((e, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-sm">{e.sheet}</TableCell>
                          <TableCell className="text-sm">{e.baris}</TableCell>
                          <TableCell className="text-sm">{e.kolom}</TableCell>
                          <TableCell className="text-sm text-red-600">{e.keterangan}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              <p className="text-xs text-slate-500">Baris dengan error akan dilewati. Lanjutkan hanya jika hasil validasi sudah sesuai.</p>
            </div>
          )}
          <DialogFooter>
            <Button data-testid="cancel-import-button" variant="outline" onClick={() => setPreview(null)}>BATALKAN</Button>
            <Button data-testid="execute-import-button" className="bg-toska hover:bg-toska-hover text-white" disabled={busy} onClick={doImport}>
              {busy && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              LANJUTKAN IMPORT
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
