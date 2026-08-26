import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { rp } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Trash2, Loader2, ArrowLeft } from "lucide-react";

const emptyLoan = { nomor_loan: "", os_pokok: "", os_margin: "", penalti: "" };
const emptyForm = {
  nomor_perkara: "", nama_pn: "", materi_gugatan: "", jenis_penggugat: "Nasabah",
  penggugat: [""], tergugat: [""],
  region: "", area: "", cabang: "", pic: "", kontak_pic: "",
  cif_list: [{ nomor_cif: "", loans: [{ ...emptyLoan }] }],
  jaminan: [{ jenis: "", deskripsi: "", nilai: "", status_pengikatan: "" }],
  mediasi: [{ tanggal: "", hasil: "" }],
  kesimpulan_mediasi: "",
  status_perkara: "Gugatan Terdaftar", risk_rating: "", rekomendasi_tindakan: "",
};

function Field({ label, children, required }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs uppercase tracking-widest text-slate-500 font-medium">
        {label} {required && <span className="text-red-500">*</span>}
      </Label>
      {children}
    </div>
  );
}

export default function CaseForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [master, setMaster] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/master-data").then((r) => setMaster(r.data));
    if (isEdit) {
      api.get(`/cases/${id}`).then((r) => {
        const c = r.data;
        setForm({
          ...emptyForm, ...c,
          penggugat: c.penggugat?.length ? c.penggugat : [""],
          tergugat: c.tergugat?.length ? c.tergugat : [""],
          cif_list: c.cif_list?.length ? c.cif_list : [{ nomor_cif: "", loans: [{ ...emptyLoan }] }],
          jaminan: c.jaminan?.length ? c.jaminan : [],
          mediasi: c.mediasi?.length ? c.mediasi : [{ tanggal: "", hasil: "" }],
        });
      }).catch((e) => toast.error(apiError(e)));
    }
  }, [id, isEdit]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target ? e.target.value : e }));

  const setArr = (key, i, val) => setForm((f) => {
    const arr = [...f[key]];
    arr[i] = val;
    return { ...f, [key]: arr };
  });

  const setCif = (ci, key, val) => setForm((f) => {
    const cifs = [...f.cif_list];
    cifs[ci] = { ...cifs[ci], [key]: val };
    return { ...f, cif_list: cifs };
  });

  const setLoan = (ci, li, key, val) => setForm((f) => {
    const cifs = [...f.cif_list];
    const loans = [...cifs[ci].loans];
    loans[li] = { ...loans[li], [key]: val };
    cifs[ci] = { ...cifs[ci], loans };
    return { ...f, cif_list: cifs };
  });

  const setJaminan = (i, key, val) => setForm((f) => {
    const arr = [...f.jaminan];
    arr[i] = { ...arr[i], [key]: val };
    return { ...f, jaminan: arr };
  });

  const setMediasi = (i, key, val) => setForm((f) => {
    const arr = [...f.mediasi];
    arr[i] = { ...arr[i], [key]: val };
    return { ...f, mediasi: arr };
  });

  const total = form.cif_list.reduce(
    (a, c) => a + c.loans.reduce((b, l) => b + (parseFloat(l.os_pokok) || 0) + (parseFloat(l.os_margin) || 0) + (parseFloat(l.penalti) || 0), 0), 0);

  const regionMap = master?.region_area_map || {};
  const regionOptions = [...new Set([...Object.keys(regionMap), ...(form.region ? [form.region] : [])])];
  const areaOptions = regionMap[form.region] || (form.area ? [form.area] : []);

  const submit = async () => {
    if (!form.nomor_perkara.trim()) {
      toast.error("Nomor Perkara wajib diisi");
      return;
    }
    setLoading(true);
    const payload = {
      ...form,
      penggugat: form.penggugat.filter(Boolean),
      tergugat: form.tergugat.filter(Boolean),
      cif_list: form.cif_list.filter((c) => c.nomor_cif).map((c) => ({
        ...c,
        loans: c.loans.filter((l) => l.nomor_loan).map((l) => ({
          ...l, os_pokok: parseFloat(l.os_pokok) || 0, os_margin: parseFloat(l.os_margin) || 0, penalti: parseFloat(l.penalti) || 0,
        })),
      })),
      jaminan: form.jaminan.filter((j) => j.jenis || j.deskripsi).map((j) => ({ ...j, nilai: parseFloat(j.nilai) || 0 })),
      mediasi: form.mediasi.filter((m) => m.tanggal || m.hasil),
    };
    try {
      if (isEdit) {
        await api.put(`/cases/${id}`, payload);
        toast.success("Perubahan dikirim, menunggu approval Manager");
      } else {
        await api.post("/cases", payload);
        toast.success("Perkara baru dikirim, menunggu approval Manager");
      }
      navigate("/perkara");
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="case-form-page" className="space-y-5 max-w-5xl">
      <div className="flex items-center gap-3">
        <Button variant="outline" size="icon" onClick={() => navigate(-1)} data-testid="back-button">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">
            {isEdit ? "Edit Data Perkara" : "Input Perkara Baru"}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {isEdit ? "Perubahan wajib melalui approval Legal Litigation & Advice Manager" : "Status: Draft → Menunggu Approval → Approved"}
          </p>
        </div>
      </div>

      <Tabs defaultValue="informasi" className="bg-white border border-slate-200 rounded-md">
        <TabsList className="w-full justify-start flex-wrap h-auto border-b border-slate-200 rounded-none bg-transparent p-2">
          <TabsTrigger data-testid="tab-informasi" value="informasi">A. Informasi Perkara</TabsTrigger>
          <TabsTrigger data-testid="tab-organisasi" value="organisasi">B. Organisasi BSI</TabsTrigger>
          <TabsTrigger data-testid="tab-cif" value="cif">C. CIF & Loan</TabsTrigger>
          <TabsTrigger data-testid="tab-jaminan" value="jaminan">D. Jaminan</TabsTrigger>
          <TabsTrigger data-testid="tab-mediasi" value="mediasi">Mediasi</TabsTrigger>
          <TabsTrigger data-testid="tab-risk" value="risk">Risk Rating</TabsTrigger>
        </TabsList>

        <TabsContent value="informasi" className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nomor Perkara" required>
              <Input data-testid="input-nomor-perkara" value={form.nomor_perkara} onChange={set("nomor_perkara")} placeholder="cth: 123/Pdt.G/2025/PN.Jkt.Sel" />
            </Field>
            <Field label="Nama PN/PA">
              <Input data-testid="input-nama-pn" value={form.nama_pn} onChange={set("nama_pn")} placeholder="cth: PN Jakarta Selatan" />
            </Field>
          </div>
          <Field label="Materi Gugatan">
            <Textarea data-testid="input-materi-gugatan" rows={4} value={form.materi_gugatan} onChange={set("materi_gugatan")} />
          </Field>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Jenis Penggugat">
              <Select value={form.jenis_penggugat} onValueChange={set("jenis_penggugat")}>
                <SelectTrigger data-testid="select-jenis-penggugat"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Nasabah">Nasabah</SelectItem>
                  <SelectItem value="Pihak Ketiga">Pihak Ketiga</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Status Perkara">
              <Select value={form.status_perkara} onValueChange={set("status_perkara")}>
                <SelectTrigger data-testid="select-status-perkara"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(master?.status_perkara || []).map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <div className="space-y-2">
            <Label className="text-xs uppercase tracking-widest text-slate-500 font-medium">Nama Penggugat</Label>
            {form.penggugat.map((p, i) => (
              <div key={i} className="flex gap-2">
                <Input data-testid={`input-penggugat-${i}`} value={p} onChange={(e) => setArr("penggugat", i, e.target.value)} placeholder={`Penggugat ${i + 1}`} />
                {form.penggugat.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => setForm((f) => ({ ...f, penggugat: f.penggugat.filter((_, x) => x !== i) }))}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                )}
              </div>
            ))}
            <Button data-testid="add-penggugat-button" variant="outline" size="sm" onClick={() => setForm((f) => ({ ...f, penggugat: [...f.penggugat, ""] }))}>
              <Plus className="h-4 w-4 mr-1" /> Tambah Penggugat
            </Button>
          </div>

          <div className="space-y-2">
            <Label className="text-xs uppercase tracking-widest text-slate-500 font-medium">Daftar Tergugat</Label>
            {form.tergugat.map((t, i) => (
              <div key={i} className="flex gap-2">
                <Input data-testid={`input-tergugat-${i}`} value={t} onChange={(e) => setArr("tergugat", i, e.target.value)} placeholder={`Tergugat ${i + 1}`} />
                {form.tergugat.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => setForm((f) => ({ ...f, tergugat: f.tergugat.filter((_, x) => x !== i) }))}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                )}
              </div>
            ))}
            <Button data-testid="add-tergugat-button" variant="outline" size="sm" onClick={() => setForm((f) => ({ ...f, tergugat: [...f.tergugat, ""] }))}>
              <Plus className="h-4 w-4 mr-1" /> Tambah Tergugat
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="organisasi" className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nama Region">
              <Select value={form.region || "none"} onValueChange={(v) => setForm((f) => ({ ...f, region: v === "none" ? "" : v, area: "" }))}>
                <SelectTrigger data-testid="select-region"><SelectValue placeholder="Pilih region" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Pilih Region</SelectItem>
                  {regionOptions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Nama Area">
              <Select value={form.area || "none"} onValueChange={(v) => set("area")(v === "none" ? "" : v)} disabled={!form.region}>
                <SelectTrigger data-testid="select-area"><SelectValue placeholder={form.region ? "Pilih area" : "Pilih region terlebih dahulu"} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Pilih Area</SelectItem>
                  {areaOptions.map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Nama Cabang"><Input data-testid="input-cabang" value={form.cabang} onChange={set("cabang")} placeholder="cth: KC Jakarta Tebet" /></Field>
            <Field label="Nama PIC"><Input data-testid="input-pic" value={form.pic} onChange={set("pic")} /></Field>
            <Field label="Kontak PIC"><Input data-testid="input-kontak-pic" value={form.kontak_pic} onChange={set("kontak_pic")} placeholder="cth: 0812-xxxx-xxxx" /></Field>
          </div>
        </TabsContent>

        <TabsContent value="cif" className="p-6 space-y-6">
          {form.cif_list.map((cif, ci) => (
            <div key={ci} className="border border-slate-200 rounded-md p-4 space-y-4">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-900">CIF {ci + 1}</p>
                {form.cif_list.length > 1 && (
                  <Button variant="ghost" size="sm" onClick={() => setForm((f) => ({ ...f, cif_list: f.cif_list.filter((_, x) => x !== ci) }))}>
                    <Trash2 className="h-4 w-4 text-red-500 mr-1" /> Hapus CIF
                  </Button>
                )}
              </div>
              <Field label="Nomor CIF">
                <Input data-testid={`input-cif-${ci}`} value={cif.nomor_cif} onChange={(e) => setCif(ci, "nomor_cif", e.target.value)} placeholder="cth: CIF001234" />
              </Field>
              {cif.loans.map((loan, li) => (
                <div key={li} className="bg-slate-50 border border-slate-200 rounded-md p-4">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-medium text-slate-700">Loan {li + 1}</p>
                    {cif.loans.length > 1 && (
                      <Button variant="ghost" size="icon" onClick={() => setCif(ci, "loans", cif.loans.filter((_, x) => x !== li))}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <Field label="Nomor Loan"><Input data-testid={`input-loan-${ci}-${li}`} value={loan.nomor_loan} onChange={(e) => setLoan(ci, li, "nomor_loan", e.target.value)} /></Field>
                    <Field label="OS Pokok"><Input data-testid={`input-os-pokok-${ci}-${li}`} type="number" value={loan.os_pokok} onChange={(e) => setLoan(ci, li, "os_pokok", e.target.value)} /></Field>
                    <Field label="OS Margin"><Input data-testid={`input-os-margin-${ci}-${li}`} type="number" value={loan.os_margin} onChange={(e) => setLoan(ci, li, "os_margin", e.target.value)} /></Field>
                    <Field label="Penalti"><Input data-testid={`input-penalti-${ci}-${li}`} type="number" value={loan.penalti} onChange={(e) => setLoan(ci, li, "penalti", e.target.value)} /></Field>
                  </div>
                </div>
              ))}
              <Button data-testid={`add-loan-${ci}`} variant="outline" size="sm" onClick={() => setCif(ci, "loans", [...cif.loans, { ...emptyLoan }])}>
                <Plus className="h-4 w-4 mr-1" /> Tambah Loan
              </Button>
            </div>
          ))}
          <Button data-testid="add-cif-button" variant="outline" onClick={() => setForm((f) => ({ ...f, cif_list: [...f.cif_list, { nomor_cif: "", loans: [{ ...emptyLoan }] }] }))}>
            <Plus className="h-4 w-4 mr-1" /> Tambah CIF
          </Button>
          <div className="bg-toska-light border border-toska/30 rounded-md p-4 flex items-center justify-between">
            <p className="text-sm font-medium text-slate-700">TOTAL KEWAJIBAN (OS Pokok + OS Margin + Penalti)</p>
            <p data-testid="total-kewajiban-display" className="font-heading text-xl font-bold text-toska-dark">{rp(total)}</p>
          </div>
        </TabsContent>

        <TabsContent value="jaminan" className="p-6 space-y-4">
          {form.jaminan.map((j, i) => (
            <div key={i} className="border border-slate-200 rounded-md p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-900">Jaminan {i + 1}</p>
                <Button variant="ghost" size="icon" onClick={() => setForm((f) => ({ ...f, jaminan: f.jaminan.filter((_, x) => x !== i) }))}>
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Field label="Jenis Jaminan">
                  <Input data-testid={`input-jaminan-jenis-${i}`} value={j.jenis} onChange={(e) => setJaminan(i, "jenis", e.target.value)} placeholder="cth: Tanah dan Bangunan (Rumah Tinggal)" list="jenis-jaminan" />
                  <datalist id="jenis-jaminan">
                    <option value="Tanah dan Bangunan (Rumah Tinggal)" />
                    <option value="Tanah dan Bangunan (Ruko)" />
                    <option value="Tanah (Kebun)" />
                    <option value="Kendaraan Bermotor" />
                    <option value="Deposito" />
                  </datalist>
                </Field>
                <Field label="Nilai Jaminan (Rp)"><Input type="number" value={j.nilai} onChange={(e) => setJaminan(i, "nilai", e.target.value)} /></Field>
              </div>
              <Field label="Deskripsi Jaminan">
                <Textarea rows={3} value={j.deskripsi} onChange={(e) => setJaminan(i, "deskripsi", e.target.value)} placeholder="cth: SHM No.15, Luas tanah 100 M2, Luas bangunan 90 M2, Lokasi: ..." />
              </Field>
              <Field label="Status Pengikatan">
                <Input value={j.status_pengikatan} onChange={(e) => setJaminan(i, "status_pengikatan", e.target.value)} placeholder="cth: APHT / SKMHT / Fidusia" list="status-pengikatan" />
                <datalist id="status-pengikatan">
                  <option value="APHT" /><option value="SKMHT" /><option value="Fidusia" /><option value="Belum Diikat" />
                </datalist>
              </Field>
            </div>
          ))}
          <Button data-testid="add-jaminan-button" variant="outline" onClick={() => setForm((f) => ({ ...f, jaminan: [...f.jaminan, { jenis: "", deskripsi: "", nilai: "", status_pengikatan: "" }] }))}>
            <Plus className="h-4 w-4 mr-1" /> Tambah Jaminan
          </Button>
        </TabsContent>

        <TabsContent value="mediasi" className="p-6 space-y-4">
          {form.mediasi.map((m, i) => (
            <div key={i} className="border border-slate-200 rounded-md p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="font-semibold text-slate-900">Mediasi {i + 1}</p>
                {form.mediasi.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => setForm((f) => ({ ...f, mediasi: f.mediasi.filter((_, x) => x !== i) }))}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Field label="Tanggal"><Input data-testid={`input-mediasi-tanggal-${i}`} type="date" value={m.tanggal} onChange={(e) => setMediasi(i, "tanggal", e.target.value)} /></Field>
                <Field label="Hasil"><Input data-testid={`input-mediasi-hasil-${i}`} value={m.hasil} onChange={(e) => setMediasi(i, "hasil", e.target.value)} placeholder="cth: Belum tercapai kesepakatan" /></Field>
              </div>
            </div>
          ))}
          {form.mediasi.length < 5 && (
            <Button data-testid="add-mediasi-button" variant="outline" onClick={() => setForm((f) => ({ ...f, mediasi: [...f.mediasi, { tanggal: "", hasil: "" }] }))}>
              <Plus className="h-4 w-4 mr-1" /> Tambah Mediasi
            </Button>
          )}
          <Field label="Kesimpulan Hasil Mediasi">
            <Textarea data-testid="input-kesimpulan-mediasi" rows={3} value={form.kesimpulan_mediasi} onChange={set("kesimpulan_mediasi")} />
          </Field>
        </TabsContent>

        <TabsContent value="risk" className="p-6 space-y-4">
          <Field label="Risk Rating">
            <Select value={form.risk_rating || "none"} onValueChange={(v) => set("risk_rating")(v === "none" ? "" : v)}>
              <SelectTrigger data-testid="select-risk-rating" className="md:w-72"><SelectValue placeholder="Pilih risk rating" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Belum ditentukan</SelectItem>
                <SelectItem value="High Risk">High Risk</SelectItem>
                <SelectItem value="Medium Risk">Medium Risk</SelectItem>
                <SelectItem value="Low Risk">Low Risk</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field label="Rekomendasi Tindakan">
            <Textarea data-testid="input-rekomendasi" rows={4} value={form.rekomendasi_tindakan} onChange={set("rekomendasi_tindakan")} />
          </Field>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => navigate("/perkara")}>Batal</Button>
        <Button data-testid="submit-case-button" className="bg-toska hover:bg-toska-hover text-white" disabled={loading} onClick={submit}>
          {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {isEdit ? "Ajukan Perubahan" : "Ajukan Perkara Baru"}
        </Button>
      </div>
    </div>
  );
}
