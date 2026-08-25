import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api, { apiError, downloadBlob, previewBlob } from "@/lib/api";
import { rp, fmtDate } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Pencil, Upload, Eye, FileDown, Trash2, Plus, FileText } from "lucide-react";

function Info({ label, value }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500 font-medium">{label}</p>
      <p className="text-sm text-slate-900 mt-1 whitespace-pre-wrap">{value || "-"}</p>
    </div>
  );
}

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [c, setC] = useState(null);
  const [docs, setDocs] = useState([]);
  const [master, setMaster] = useState(null);
  const [agenda, setAgenda] = useState({ tanggal: "", agenda: "", keterangan: "" });
  const [upload, setUpload] = useState({ kategori: "", nomor: "", tanggal: "", file: null });
  const [opStatus, setOpStatus] = useState("");
  const [opRisk, setOpRisk] = useState("");
  const [opRek, setOpRek] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.get(`/cases/${id}`).then((r) => {
      setC(r.data);
      setOpStatus(r.data.status_perkara);
      setOpRisk(r.data.risk_rating || "");
      setOpRek(r.data.rekomendasi_tindakan || "");
    }).catch((e) => toast.error(apiError(e)));
    api.get("/documents", { params: { case_id: id } }).then((r) => setDocs(r.data));
  }, [id]);

  useEffect(() => {
    load();
    api.get("/master-data").then((r) => setMaster(r.data));
  }, [load]);

  const saveOperasional = async () => {
    setBusy(true);
    try {
      await api.patch(`/cases/${id}/operasional`, {
        status_perkara: opStatus, risk_rating: opRisk || undefined, rekomendasi_tindakan: opRek,
        mediasi: c.mediasi, kesimpulan_mediasi: c.kesimpulan_mediasi,
      });
      toast.success("Data operasional diperbarui");
      load();
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setBusy(false);
    }
  };

  const addAgenda = async () => {
    if (!agenda.tanggal || !agenda.agenda) {
      toast.error("Tanggal dan agenda wajib diisi");
      return;
    }
    try {
      await api.post(`/cases/${id}/agenda`, agenda);
      toast.success("Agenda sidang ditambahkan ke timeline");
      setAgenda({ tanggal: "", agenda: "", keterangan: "" });
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const doUpload = async () => {
    if (!upload.file || !upload.kategori) {
      toast.error("Kategori dan file PDF wajib diisi");
      return;
    }
    const fd = new FormData();
    fd.append("file", upload.file);
    fd.append("kategori", upload.kategori);
    fd.append("nomor", upload.nomor);
    fd.append("tanggal", upload.tanggal);
    setBusy(true);
    try {
      await api.post(`/cases/${id}/documents`, fd);
      toast.success("Dokumen berhasil diunggah");
      setUpload({ kategori: "", nomor: "", tanggal: "", file: null });
      load();
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setBusy(false);
    }
  };

  const deleteDoc = async (docId) => {
    try {
      await api.delete(`/documents/${docId}`);
      toast.success("Dokumen dihapus");
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  if (!c) return <p className="text-sm text-slate-500">Memuat data perkara...</p>;

  const timeline = [...(c.timeline || [])].sort((a, b) => (a.tanggal < b.tanggal ? 1 : -1));

  return (
    <div data-testid="case-detail-page" className="space-y-5">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
        <div className="flex items-start gap-3">
          <Button variant="outline" size="icon" onClick={() => navigate("/perkara")} data-testid="back-to-cases">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">{c.nomor_perkara}</h1>
            <p className="text-sm text-slate-500 mt-1">{c.nama_pn} • {c.cabang}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline" className="border-toska text-toska-dark">{c.status_perkara}</Badge>
              {c.risk_rating && <Badge variant={c.risk_rating === "High Risk" ? "destructive" : c.risk_rating === "Medium Risk" ? "default" : "secondary"}>{c.risk_rating}</Badge>}
              <Badge className={c.status_aktif === "AKTIF" ? "bg-toska hover:bg-toska" : ""} variant={c.status_aktif === "AKTIF" ? "default" : "secondary"}>{c.status_aktif}</Badge>
            </div>
          </div>
        </div>
        <Link to={`/perkara/${id}/edit`}>
          <Button data-testid="edit-case-button" variant="outline"><Pencil className="h-4 w-4 mr-2" /> Edit Data</Button>
        </Link>
      </div>

      {c.status_aktif === "TIDAK AKTIF" && (
        <div className="bg-slate-100 border border-slate-300 rounded-md p-4 text-sm text-slate-700">
          <span className="font-semibold">Alasan penghentian: </span>{c.alasan_nonaktif}
        </div>
      )}

      <Tabs defaultValue="detail" className="bg-white border border-slate-200 rounded-md">
        <TabsList className="w-full justify-start flex-wrap h-auto border-b border-slate-200 rounded-none bg-transparent p-2">
          <TabsTrigger data-testid="tab-detail" value="detail">Detail</TabsTrigger>
          <TabsTrigger data-testid="tab-agenda" value="agenda">Agenda Sidang</TabsTrigger>
          <TabsTrigger data-testid="tab-dokumen" value="dokumen">Dokumen ({docs.length})</TabsTrigger>
          <TabsTrigger data-testid="tab-timeline" value="timeline">Timeline</TabsTrigger>
          <TabsTrigger data-testid="tab-status" value="status">Status & Risk</TabsTrigger>
        </TabsList>

        <TabsContent value="detail" className="p-6 space-y-8">
          <section>
            <p className="text-xs uppercase tracking-widest text-toska font-semibold mb-3">A. Informasi Perkara</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Info label="Jenis Penggugat" value={c.jenis_penggugat} />
              <Info label="Tahun" value={c.tahun} />
              <Info label="Penggugat" value={(c.penggugat || []).join("; ")} />
              <Info label="Tergugat" value={(c.tergugat || []).join("; ")} />
            </div>
            <div className="mt-4"><Info label="Materi Gugatan" value={c.materi_gugatan} /></div>
          </section>

          <section>
            <p className="text-xs uppercase tracking-widest text-toska font-semibold mb-3">B. Organisasi BSI</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Info label="Region" value={c.region} />
              <Info label="Area" value={c.area} />
              <Info label="Cabang" value={c.cabang} />
              <Info label="PIC" value={c.pic} />
              <Info label="Kontak PIC" value={c.kontak_pic} />
            </div>
          </section>

          <section>
            <p className="text-xs uppercase tracking-widest text-toska font-semibold mb-3">C. Data CIF & Loan</p>
            {(c.cif_list || []).map((cif, ci) => (
              <div key={ci} className="border border-slate-200 rounded-md mb-3">
                <p className="px-4 py-2 bg-slate-50 border-b border-slate-200 text-sm font-semibold">CIF: {cif.nomor_cif}</p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nomor Loan</TableHead><TableHead>OS Pokok</TableHead>
                      <TableHead>OS Margin</TableHead><TableHead>Penalti</TableHead><TableHead>Subtotal</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(cif.loans || []).map((l, li) => (
                      <TableRow key={li}>
                        <TableCell>{l.nomor_loan}</TableCell>
                        <TableCell>{rp(l.os_pokok)}</TableCell>
                        <TableCell>{rp(l.os_margin)}</TableCell>
                        <TableCell>{rp(l.penalti)}</TableCell>
                        <TableCell className="font-medium">{rp((l.os_pokok || 0) + (l.os_margin || 0) + (l.penalti || 0))}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ))}
            <div className="bg-toska-light border border-toska/30 rounded-md p-4 flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">TOTAL KEWAJIBAN</p>
              <p data-testid="detail-total-kewajiban" className="font-heading text-xl font-bold text-toska-dark">{rp(c.total_kewajiban)}</p>
            </div>
          </section>

          <section>
            <p className="text-xs uppercase tracking-widest text-toska font-semibold mb-3">D. Jaminan</p>
            {(c.jaminan || []).length === 0 && <p className="text-sm text-slate-500">Tidak ada data jaminan.</p>}
            {(c.jaminan || []).map((j, i) => (
              <div key={i} className="border border-slate-200 rounded-md p-4 mb-3">
                <p className="font-semibold text-slate-900">{j.jenis || "Jaminan"}</p>
                <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{j.deskripsi}</p>
                <div className="flex gap-6 mt-2 text-sm">
                  <span className="text-slate-500">Nilai: <span className="font-medium text-slate-900">{rp(j.nilai)}</span></span>
                  <span className="text-slate-500">Pengikatan: <span className="font-medium text-slate-900">{j.status_pengikatan || "-"}</span></span>
                </div>
              </div>
            ))}
          </section>

          <section>
            <p className="text-xs uppercase tracking-widest text-toska font-semibold mb-3">Mediasi</p>
            {(c.mediasi || []).length === 0 && <p className="text-sm text-slate-500">Belum ada data mediasi.</p>}
            {(c.mediasi || []).map((m, i) => (
              <div key={i} className="flex gap-4 text-sm border-b border-slate-100 py-2">
                <span className="font-medium w-24">Mediasi {i + 1}</span>
                <span className="text-slate-500 w-32">{fmtDate(m.tanggal)}</span>
                <span className="text-slate-900">{m.hasil}</span>
              </div>
            ))}
            {c.kesimpulan_mediasi && <div className="mt-3"><Info label="Kesimpulan Hasil Mediasi" value={c.kesimpulan_mediasi} /></div>}
          </section>
        </TabsContent>

        <TabsContent value="agenda" className="p-6 space-y-5">
          <div className="border border-slate-200 rounded-md p-4 grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
            <div>
              <Label className="text-xs uppercase tracking-widest text-slate-500">Tanggal Sidang</Label>
              <Input data-testid="agenda-tanggal-input" type="date" value={agenda.tanggal} onChange={(e) => setAgenda((a) => ({ ...a, tanggal: e.target.value }))} />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest text-slate-500">Agenda</Label>
              <Select value={agenda.agenda} onValueChange={(v) => setAgenda((a) => ({ ...a, agenda: v }))}>
                <SelectTrigger data-testid="agenda-select"><SelectValue placeholder="Pilih agenda" /></SelectTrigger>
                <SelectContent>
                  {(master?.agenda_list || []).map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest text-slate-500">Keterangan</Label>
              <Input data-testid="agenda-keterangan-input" value={agenda.keterangan} onChange={(e) => setAgenda((a) => ({ ...a, keterangan: e.target.value }))} />
            </div>
            <Button data-testid="add-agenda-button" className="bg-toska hover:bg-toska-hover text-white" onClick={addAgenda}>
              <Plus className="h-4 w-4 mr-1" /> Tambah Agenda
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Tanggal</TableHead><TableHead>Agenda</TableHead><TableHead>Keterangan</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {[...(c.agenda_sidang || [])].sort((a, b) => (a.tanggal < b.tanggal ? 1 : -1)).map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{fmtDate(a.tanggal)}</TableCell>
                  <TableCell><Badge variant="outline" className="border-toska text-toska-dark">{a.agenda}</Badge></TableCell>
                  <TableCell className="text-sm">{a.keterangan}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={async () => { await api.delete(`/cases/${id}/agenda/${a.id}`); load(); }}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {(c.agenda_sidang || []).length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center text-sm text-slate-500 py-6">Belum ada agenda sidang.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="dokumen" className="p-6 space-y-5">
          <div className="border border-slate-200 rounded-md p-4 space-y-3">
            <p className="text-sm font-semibold text-slate-900">Upload Dokumen (PDF only)</p>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <div>
                <Label className="text-xs uppercase tracking-widest text-slate-500">Kategori Dokumen</Label>
                <Select value={upload.kategori} onValueChange={(v) => setUpload((u) => ({ ...u, kategori: v }))}>
                  <SelectTrigger data-testid="doc-kategori-select"><SelectValue placeholder="Pilih kategori" /></SelectTrigger>
                  <SelectContent>
                    {(master?.dokumen_kategori || []).map((k) => <SelectItem key={k} value={k}>{k}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs uppercase tracking-widest text-slate-500">Nomor (opsional)</Label>
                <Input data-testid="doc-nomor-input" value={upload.nomor} onChange={(e) => setUpload((u) => ({ ...u, nomor: e.target.value }))} />
              </div>
              <div>
                <Label className="text-xs uppercase tracking-widest text-slate-500">Tanggal (opsional)</Label>
                <Input data-testid="doc-tanggal-input" type="date" value={upload.tanggal} onChange={(e) => setUpload((u) => ({ ...u, tanggal: e.target.value }))} />
              </div>
              <div>
                <Input data-testid="doc-file-input" type="file" accept="application/pdf" onChange={(e) => setUpload((u) => ({ ...u, file: e.target.files[0] }))} />
              </div>
            </div>
            <Button data-testid="upload-doc-button" className="bg-toska hover:bg-toska-hover text-white" disabled={busy} onClick={doUpload}>
              <Upload className="h-4 w-4 mr-2" /> Upload PDF
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow><TableHead>Kategori</TableHead><TableHead>File</TableHead><TableHead>Nomor/Tanggal</TableHead><TableHead>Diunggah</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {docs.map((d) => (
                <TableRow key={d.id} data-testid={`doc-row-${d.id}`}>
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
              {docs.length === 0 && (
                <TableRow><TableCell colSpan={5} className="text-center text-sm text-slate-500 py-6">Belum ada dokumen.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="timeline" className="p-6">
          <div className="border-l-2 border-slate-200 ml-2 space-y-6" data-testid="case-timeline">
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
        </TabsContent>

        <TabsContent value="status" className="p-6 space-y-4 max-w-2xl">
          <div>
            <Label className="text-xs uppercase tracking-widest text-slate-500">Status Perkara (18 Tahapan)</Label>
            <Select value={opStatus} onValueChange={setOpStatus}>
              <SelectTrigger data-testid="op-status-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {(master?.status_perkara || []).map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-widest text-slate-500">Risk Rating</Label>
            <Select value={opRisk || "none"} onValueChange={(v) => setOpRisk(v === "none" ? "" : v)}>
              <SelectTrigger data-testid="op-risk-select"><SelectValue placeholder="Pilih risk rating" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Belum ditentukan</SelectItem>
                <SelectItem value="High Risk">High Risk</SelectItem>
                <SelectItem value="Medium Risk">Medium Risk</SelectItem>
                <SelectItem value="Low Risk">Low Risk</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-widest text-slate-500">Rekomendasi Tindakan</Label>
            <Textarea data-testid="op-rekomendasi-input" rows={4} value={opRek} onChange={(e) => setOpRek(e.target.value)} />
          </div>
          <Button data-testid="save-operasional-button" className="bg-toska hover:bg-toska-hover text-white" disabled={busy} onClick={saveOperasional}>
            Simpan Perubahan
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
}
