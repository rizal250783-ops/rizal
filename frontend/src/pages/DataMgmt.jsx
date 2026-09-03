import React, { useEffect, useState } from "react";
import api, { API, apiErr } from "../lib/api";
import { Card, Button, Th, Td, Empty, SectionTitle, Badge } from "../components/ui";
import { Upload, Download, Database, RotateCcw, FileSpreadsheet } from "lucide-react";

export default function DataMgmt() {
  const [tab, setTab] = useState("import");
  return (
    <div className="space-y-5">
      <div className="flex gap-2 flex-wrap">
        {[["import", "Import Data", Upload], ["export", "Export Data", Download], ["backup", "Backup & Restore", Database], ["history", "Import History", FileSpreadsheet]].map(([k, label, Icon]) => (
          <Button key={k} variant={tab === k ? "primary" : "outline"} onClick={() => setTab(k)} data-testid={`dm-tab-${k}`}><Icon size={16} /> {label}</Button>
        ))}
      </div>
      {tab === "import" && <ImportPanel />}
      {tab === "export" && <ExportPanel />}
      {tab === "backup" && <BackupPanel />}
      {tab === "history" && <HistoryPanel />}
    </div>
  );
}

function ImportPanel() {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  const doPreview = async () => {
    setErr(""); setMsg("");
    if (!file) { setErr("Pilih file .xlsx"); return; }
    const fd = new FormData();
    fd.append("data_type", "portfolio");
    fd.append("file", file);
    try { const { data } = await api.post("/import/preview", fd, { headers: { "Content-Type": "multipart/form-data" } }); setPreview(data); }
    catch (e) { setErr(apiErr(e)); }
  };
  const confirm = async () => {
    try { const { data } = await api.post("/import/confirm", { data_type: "portfolio", filename: file?.name, records: preview.records }); setMsg(`Import selesai: ${data.success} berhasil, ${data.failed} gagal.`); setPreview(null); }
    catch (e) { setErr(apiErr(e)); }
  };

  return (
    <Card className="p-5">
      <SectionTitle sub="Upload → Validasi → Preview → Konfirmasi → Import (jenis: Portfolio)">Import Data Portfolio</SectionTitle>
      <div className="flex items-center gap-3">
        <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files[0])} data-testid="import-file" className="text-sm" />
        <Button variant="outline" onClick={doPreview} data-testid="import-preview-btn">Preview</Button>
      </div>
      <p className="text-xs text-slate-400 mt-2">Kolom: nomor_kontrak, nama_nasabah, produk, plafond, outstanding_pokok, tanggal_akad, tanggal_jatuh_tempo, kolektibilitas, dpd, ao_id</p>
      {err && <div className="mt-3 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
      {msg && <div className="mt-3 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      {preview && (
        <div className="mt-4">
          <div className="flex items-center gap-3 mb-2">
            <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{preview.valid_count} valid</Badge>
            <Badge className="bg-red-50 text-red-700 border-red-200">{preview.error_count} error</Badge>
          </div>
          {preview.errors.length > 0 && (
            <div className="rounded-lg bg-red-50 p-3 text-xs text-red-700 mb-3">
              {preview.errors.slice(0, 10).map((e, i) => <div key={i}>Baris {e.row}: {e.reason}</div>)}
            </div>
          )}
          <div className="overflow-x-auto max-h-64 border rounded-lg">
            <table className="w-full text-xs">
              <thead className="bg-slate-50"><tr>{preview.headers.map((h) => <Th key={h}>{h}</Th>)}</tr></thead>
              <tbody className="divide-y divide-slate-100">
                {preview.records.slice(0, 20).map((r, i) => (
                  <tr key={i}>{preview.headers.map((h) => <Td key={h}>{String(r.data[h] ?? "")}</Td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <Button className="mt-3" onClick={confirm} data-testid="import-confirm-btn">Konfirmasi & Import</Button>
        </div>
      )}
    </Card>
  );
}

function ExportPanel() {
  const dl = async (type) => {
    const token = localStorage.getItem("ao360_token");
    const res = await fetch(`${API}/export/${type}`, { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `${type}.xlsx`; a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <Card className="p-5">
      <SectionTitle sub="Format XLSX">Export Laporan</SectionTitle>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[["achievement", "Achievement Report"], ["portfolio", "Portfolio Report"], ["npf", "NPF Report"], ["collection", "Collection Report"]].map(([k, label]) => (
          <Button key={k} variant="outline" onClick={() => dl(k)} data-testid={`export-${k}`}><Download size={16} /> {label}</Button>
        ))}
      </div>
    </Card>
  );
}

function BackupPanel() {
  const [msg, setMsg] = useState("");
  const [restoreData, setRestoreData] = useState(null);
  const backup = async () => {
    const token = localStorage.getItem("ao360_token");
    const res = await fetch(`${API}/backup`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "ao360_backup.json"; a.click();
    setMsg("Backup berhasil diunduh. Catatan: password_hash tidak disertakan (aturan 72a).");
  };
  const onRestoreFile = (e) => {
    const f = e.target.files[0];
    const reader = new FileReader();
    reader.onload = () => { try { setRestoreData(JSON.parse(reader.result)); } catch { setMsg("File backup tidak valid"); } };
    reader.readAsText(f);
  };
  const confirmRestore = async () => {
    if (!window.confirm("Restore akan menimpa data & backup otomatis dibuat. Semua user wajib ganti password. Lanjutkan?")) return;
    const { data } = await api.post("/restore/confirm", restoreData);
    setMsg(`Restore selesai. ${data.restored_users.length} user wajib ganti password. ${data.note}`);
    setRestoreData(null);
  };
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <SectionTitle sub="Full backup tanpa password/credential (aturan 72a)">Backup Database</SectionTitle>
        <Button onClick={backup} data-testid="backup-btn"><Database size={16} /> Backup Sekarang</Button>
      </Card>
      <Card className="p-5">
        <SectionTitle sub="Upload backup → auto-backup → restore → user wajib ganti password">Restore Database</SectionTitle>
        <input type="file" accept=".json" onChange={onRestoreFile} data-testid="restore-file" className="text-sm" />
        {restoreData && <Button variant="danger" className="mt-3" onClick={confirmRestore} data-testid="restore-confirm-btn"><RotateCcw size={16} /> Konfirmasi Restore</Button>}
      </Card>
      {msg && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-800">{msg}</div>}
    </div>
  );
}

function HistoryPanel() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.get("/import-history").then((r) => setRows(r.data)); }, []);
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr><Th>File</Th><Th>Jenis</Th><Th>User</Th><Th className="text-right">Total</Th><Th className="text-right">Berhasil</Th><Th className="text-right">Gagal</Th><Th>Waktu</Th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((r) => (
              <tr key={r.id}><Td className="text-xs">{r.filename}</Td><Td>{r.data_type}</Td><Td className="text-xs">{r.user_name}</Td><Td className="text-right font-num">{r.total}</Td><Td className="text-right font-num text-emerald-700">{r.success}</Td><Td className="text-right font-num text-red-600">{r.failed}</Td><Td className="text-xs text-slate-400">{r.waktu?.slice(0, 19).replace("T", " ")}</Td></tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={7}><Empty>Belum ada riwayat import.</Empty></td></tr>}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
