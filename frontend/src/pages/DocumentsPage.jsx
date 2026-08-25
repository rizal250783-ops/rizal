import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import api, { apiError, downloadBlob, previewBlob } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Eye, FileDown, Trash2, FileText } from "lucide-react";

export default function DocumentsPage() {
  const [docs, setDocs] = useState([]);
  const [cases, setCases] = useState([]);
  const [master, setMaster] = useState(null);
  const [caseFilter, setCaseFilter] = useState("all");
  const [katFilter, setKatFilter] = useState("all");

  useEffect(() => {
    api.get("/cases").then((r) => setCases(r.data));
    api.get("/master-data").then((r) => setMaster(r.data));
  }, []);

  const load = useCallback(() => {
    const params = caseFilter !== "all" ? { case_id: caseFilter } : {};
    api.get("/documents", { params }).then((r) => setDocs(r.data));
  }, [caseFilter]);

  useEffect(() => { load(); }, [load]);

  const filtered = docs.filter((d) => katFilter === "all" || d.kategori === katFilter);

  const deleteDoc = async (id) => {
    try {
      await api.delete(`/documents/${id}`);
      toast.success("Dokumen dihapus");
      load();
    } catch (e) { toast.error(apiError(e)); }
  };

  return (
    <div data-testid="documents-page" className="space-y-5">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Dokumen Perkara</h1>
        <p className="text-sm text-slate-500 mt-1">Seluruh dokumen PDF perkara — upload dilakukan dari halaman detail perkara</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Select value={caseFilter} onValueChange={setCaseFilter}>
          <SelectTrigger data-testid="doc-filter-case" className="w-full md:w-80 bg-white"><SelectValue placeholder="Semua Perkara" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Perkara</SelectItem>
            {cases.map((c) => <SelectItem key={c.id} value={c.id}>{c.nomor_perkara}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={katFilter} onValueChange={setKatFilter}>
          <SelectTrigger data-testid="doc-filter-kategori" className="w-full md:w-72 bg-white"><SelectValue placeholder="Semua Kategori" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Kategori</SelectItem>
            {(master?.dokumen_kategori || []).map((k) => <SelectItem key={k} value={k}>{k}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nomor Perkara</TableHead><TableHead>Kategori</TableHead><TableHead>File</TableHead>
              <TableHead>Nomor/Tanggal</TableHead><TableHead>Diunggah Oleh</TableHead><TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((d) => (
              <TableRow key={d.id} data-testid={`doc-row-${d.id}`}>
                <TableCell>
                  <Link to={`/perkara/${d.case_id}`} className="text-toska-dark font-medium hover:underline">{d.case_nomor}</Link>
                </TableCell>
                <TableCell><Badge variant="outline" className="border-toska text-toska-dark whitespace-nowrap">{d.kategori}</Badge></TableCell>
                <TableCell className="text-sm"><FileText className="h-3.5 w-3.5 inline mr-1 text-slate-400" />{d.original_name}</TableCell>
                <TableCell className="text-sm">{d.nomor || "-"} {d.tanggal ? `• ${fmtDate(d.tanggal)}` : ""}</TableCell>
                <TableCell className="text-sm">{d.uploaded_by}<br /><span className="text-xs text-slate-400">{fmtDate(d.uploaded_at)}</span></TableCell>
                <TableCell className="text-right whitespace-nowrap">
                  <Button data-testid={`preview-doc-${d.id}`} variant="ghost" size="icon" onClick={() => previewBlob(`/documents/${d.id}/download`)}><Eye className="h-4 w-4 text-toska" /></Button>
                  <Button data-testid={`download-doc-${d.id}`} variant="ghost" size="icon" onClick={() => downloadBlob(`/documents/${d.id}/download`, d.original_name)}><FileDown className="h-4 w-4 text-slate-600" /></Button>
                  <Button data-testid={`delete-doc-${d.id}`} variant="ghost" size="icon" onClick={() => deleteDoc(d.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                </TableCell>
              </TableRow>
            ))}
            {filtered.length === 0 && (
              <TableRow><TableCell colSpan={6} className="text-center text-sm text-slate-500 py-8">Belum ada dokumen.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
