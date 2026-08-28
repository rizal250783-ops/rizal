import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { PageHeader } from "../components/PageHeader";
import { formatNumberInput, parseNumber, formatRupiah } from "../lib/format";
import { FilePlus2, Plus, Trash2, Save, Eye, Send, Upload, Check, Loader2, AlertTriangle, X } from "lucide-react";
import { toast } from "sonner";

const emptyLoan = () => ({ nama_cabang: "", cif: "", nomor_loan: "", kolektibilitas: "", segmen: "", produk: "", akad: "", os_pokok: 0, os_margin: 0, penalty: 0, tgl_mulai: "", tgl_akhir: "" });
const emptyCollateral = () => ({ jenis: "", nilai_pasar: 0, nilai_likuidasi: 0, tanggal_penilaian: "", penilai: "", nama_kjpp: "", nomor_laporan: "" });

const inp = "w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none";
const lbl = "text-xs font-semibold text-slate-500";
const STANDARD_DOC_KEYS = ["foto_ots", "surat_permohonan_ktp", "laporan_agunan", "bi_checking"];

function Section({ title, children, num }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 mb-4">
      <h3 className="font-display font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <span className="w-6 h-6 rounded-full bg-[#00A0A0] text-white text-xs flex items-center justify-center">{num}</span>{title}
      </h3>
      {children}
    </div>
  );
}

export default function NoteForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ref, setRef] = useState(null);
  const [branches, setBranches] = useState([]);
  const [noteId, setNoteId] = useState(id || null);
  const [saving, setSaving] = useState(false);
  const [confirmSubmit, setConfirmSubmit] = useState(false);

  const [header, setHeader] = useState({ nomor_manual: "", kepada: "", reff_tanggal: "" });
  const [customer, setCustomer] = useState({ nama: "", alamat: "", no_kontak: "", restrukturisasi_ke: "1" });
  const [facilities, setFacilities] = useState([emptyLoan()]);
  const [hasFixAsset, setHasFixAsset] = useState(false);
  const [collaterals, setCollaterals] = useState([]);
  const [rac, setRac] = useState([]);
  const [analysis, setAnalysis] = useState({ kemampuan_bayar: "", penyebab_bermasalah: "" });
  const [documents, setDocuments] = useState({});
  const [customDocs, setCustomDocs] = useState([]); // [{id, label, uploaded}]
  const [progress, setProgress] = useState({}); // key -> percent (0-100) while uploading

  // Opsi Pemutus (label header) diturunkan dari area/region pembuat nota
  const pemutusOptions = [];
  if (user?.area) pemutusOptions.push(`ACRM ${String(user.area).replace(/^Area\s+/i, "")}`);
  if (user?.region) pemutusOptions.push(`RCRM ${user.region}`);
  pemutusOptions.push("Group Head RCG");

  useEffect(() => {
    api.get("/reference").then((r) => setRef(r.data));
    api.get("/branches").then((r) => setBranches(r.data));
  }, []);

  useEffect(() => {
    if (!id) return;
    api.get(`/notes/${id}`).then((r) => {
      const n = r.data;
      setHeader({ nomor_manual: n.nomor_manual || "", kepada: n.kepada || "", reff_tanggal: n.reff_tanggal || "" });
      setCustomer({ nama: "", alamat: "", no_kontak: "", restrukturisasi_ke: "1", ...n.customer });
      setFacilities((n.facilities || []).length ? n.facilities.map((f) => ({ ...emptyLoan(), ...f })) : [emptyLoan()]);
      setHasFixAsset(!!n.has_fix_asset);
      setCollaterals(n.collaterals || []);
      setRac(n.rac || []);
      setAnalysis({ kemampuan_bayar: n.analysis?.kemampuan_bayar || "", penyebab_bermasalah: n.analysis?.penyebab_bermasalah || "" });
      const docs = {};
      const custom = [];
      (n.documents || []).forEach((d) => {
        if (STANDARD_DOC_KEYS.includes(d.document_type)) {
          docs[d.document_type] = d;
        } else if (d.file_path) {
          custom.push({ id: d.document_type, label: d.label || d.filename || "Dokumen tambahan", uploaded: d });
        }
      });
      setDocuments(docs);
      setCustomDocs(custom);
    }).catch(() => toast.error("Gagal memuat nota"));
  }, [id]);

  // Recompute RAC when segments change
  const syncRac = useCallback(() => {
    if (!ref) return;
    const segs = new Set(facilities.map((f) => f.segmen).filter(Boolean));
    const items = [];
    if (segs.has("KONSUMER")) ref.rac_konsumer.forEach((p) => items.push({ segment: "KONSUMER", parameter: p }));
    if (segs.has("RETAIL")) ref.rac_retail.forEach((p) => items.push({ segment: "RETAIL", parameter: p }));
    setRac((prev) => items.map((it) => {
      const existing = prev.find((x) => x.parameter === it.parameter && x.segment === it.segment);
      return existing || { ...it, status: "Terpenuhi", keterangan: "" };
    }));
  }, [facilities, ref]);

  useEffect(() => { syncRac(); }, [facilities.map((f) => f.segmen).join(","), ref]); // eslint-disable-line

  const setLoan = (i, patch) => setFacilities((f) => f.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const changeSegmen = (i, seg) => setLoan(i, { segmen: seg, produk: "", akad: "" });

  const loanTotal = (f) => parseNumber(f.os_pokok) + parseNumber(f.os_margin) + parseNumber(f.penalty);
  const nilaiKewenangan = facilities.reduce((s, f) => s + parseNumber(f.os_pokok), 0);
  const totalKewajiban = facilities.reduce((s, f) => s + loanTotal(f), 0);

  const buildPayload = () => {
    const proposals = facilities.map((f) => ({
      jenis_fasilitas: f.segmen, akad: f.akad, tujuan: f.produk,
      os_pokok: parseNumber(f.os_pokok), os_margin: parseNumber(f.os_margin), penalty: parseNumber(f.penalty),
      tgl_mulai: f.tgl_mulai, tgl_akhir: f.tgl_akhir,
    }));
    return {
      nomor_manual: header.nomor_manual, kepada: header.kepada, reff_tanggal: header.reff_tanggal,
      customer,
      facilities: facilities.map((f) => ({
        nama_cabang: f.nama_cabang, cif: f.cif, nomor_loan: f.nomor_loan, kolektibilitas: f.kolektibilitas,
        segmen: f.segmen, produk: f.produk, akad: f.akad,
        os_pokok: parseNumber(f.os_pokok), os_margin: parseNumber(f.os_margin), penalty: parseNumber(f.penalty),
        tgl_mulai: f.tgl_mulai, tgl_akhir: f.tgl_akhir,
      })),
      has_fix_asset: hasFixAsset,
      collaterals: hasFixAsset ? collaterals.map((c) => ({ ...c, nilai_pasar: parseNumber(c.nilai_pasar), nilai_likuidasi: parseNumber(c.nilai_likuidasi) })) : [],
      rac,
      analysis: { kemampuan_bayar: analysis.kemampuan_bayar, penyebab_bermasalah: analysis.penyebab_bermasalah },
      proposals,
      documents: [
        ...Object.entries(documents).map(([k, v]) => ({ document_type: k, filename: v.original, file_path: v.file_path })),
        ...customDocs.filter((c) => c.uploaded).map((c) => ({ document_type: c.id, label: c.label, filename: c.uploaded.original, file_path: c.uploaded.file_path })),
      ],
    };
  };

  const save = async (silent = false) => {
    setSaving(true);
    try {
      const payload = buildPayload();
      let nid = noteId;
      if (nid) { await api.put(`/notes/${nid}`, payload); }
      else { const { data } = await api.post("/notes", payload); nid = data.id; setNoteId(nid); }
      if (!silent) toast.success("Draft tersimpan");
      return nid;
    } catch (e) { toast.error(apiError(e)); return null; }
    finally { setSaving(false); }
  };

  const doSubmit = async () => {
    setConfirmSubmit(false);
    const nid = await save(true);
    if (!nid) return;
    try {
      await api.post(`/notes/${nid}/submit`);
      toast.success("Nota berhasil dikirim");
      navigate(`/notes/${nid}`);
    } catch (e) { toast.error(apiError(e)); }
  };

  const uploadWithProgress = async (progressKey, file) => {
    const fd = new FormData(); fd.append("file", file);
    setProgress((p) => ({ ...p, [progressKey]: 1 }));
    try {
      const { data } = await api.post("/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (evt) => {
          const pct = evt.total ? Math.round((evt.loaded * 100) / evt.total) : 0;
          setProgress((p) => ({ ...p, [progressKey]: Math.max(1, pct) }));
        },
      });
      return data;
    } finally {
      setProgress((p) => { const c = { ...p }; delete c[progressKey]; return c; });
    }
  };

  const uploadDoc = async (key, file) => {
    try {
      const data = await uploadWithProgress(key, file);
      setDocuments((d) => ({ ...d, [key]: data }));
      toast.success("Dokumen terupload");
    } catch (e) { toast.error(apiError(e)); }
  };

  const addCustomDoc = () => setCustomDocs((c) => [...c, { id: `custom_${Date.now()}`, label: "", uploaded: null }]);
  const setCustomLabel = (id, label) => setCustomDocs((c) => c.map((x) => (x.id === id ? { ...x, label } : x)));
  const removeCustomDoc = (id) => setCustomDocs((c) => c.filter((x) => x.id !== id));
  const uploadCustomDoc = async (id, file) => {
    try {
      const data = await uploadWithProgress(id, file);
      setCustomDocs((c) => c.map((x) => (x.id === id ? { ...x, uploaded: data } : x)));
      toast.success("Dokumen terupload");
    } catch (e) { toast.error(apiError(e)); }
  };

  if (!ref) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  return (
    <div className="max-w-5xl">
      <PageHeader title={id ? "Edit Nota Restruktur" : "Buat Nota Restruktur"} subtitle="Lengkapi seluruh data wajib sebelum mengirim" icon={FilePlus2} />

      {/* Header */}
      <Section num={1} title="Header Nota">
        <div className="grid md:grid-cols-3 gap-4">
          <div><label className={lbl}>Nomor Manual (maks 5 digit)</label>
            <input className={inp + " mt-1"} maxLength={5} value={header.nomor_manual} onChange={(e) => setHeader({ ...header, nomor_manual: e.target.value.replace(/\D/g, "") })} data-testid="nf-nomor" placeholder="12345" />
            <p className="text-xs text-slate-400 mt-1">Format: 06/{header.nomor_manual || "xxxxx"}-2/ACR ...</p>
          </div>
          <div><label className={lbl}>Pemutus</label>
            <select className={inp + " mt-1"} value={header.kepada} onChange={(e) => setHeader({ ...header, kepada: e.target.value })} data-testid="nf-kepada">
              <option value="">Pilih Pemutus</option>{pemutusOptions.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <div><label className={lbl}>Tanggal Surat Reff (Permohonan Nasabah)</label>
            <input type="date" className={inp + " mt-1"} value={isoFromDDMM(header.reff_tanggal)} onChange={(e) => setHeader({ ...header, reff_tanggal: ddmmFromIso(e.target.value) })} data-testid="nf-reff" />
          </div>
        </div>
      </Section>

      {/* Customer */}
      <Section num={2} title="Informasi Nasabah">
        <div className="grid md:grid-cols-2 gap-4">
          <div><label className={lbl}>Nama Nasabah</label><input className={inp + " mt-1"} value={customer.nama} onChange={(e) => setCustomer({ ...customer, nama: e.target.value })} data-testid="nf-nama" /></div>
          <div><label className={lbl}>No. Kontak</label><input className={inp + " mt-1"} value={customer.no_kontak} onChange={(e) => setCustomer({ ...customer, no_kontak: e.target.value.replace(/\D/g, "") })} data-testid="nf-kontak" /></div>
          <div className="md:col-span-2"><label className={lbl}>Alamat</label><textarea className={inp + " mt-1"} rows={2} value={customer.alamat} onChange={(e) => setCustomer({ ...customer, alamat: e.target.value })} data-testid="nf-alamat" /></div>
          <div><label className={lbl}>Restrukturisasi ke</label>
            <select className={inp + " mt-1"} value={customer.restrukturisasi_ke} onChange={(e) => setCustomer({ ...customer, restrukturisasi_ke: e.target.value })} data-testid="nf-restruk-ke">
              {ref.restrukturisasi_ke.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>
      </Section>

      {/* Facilities */}
      <Section num={3} title="Fasilitas Pembiayaan Existing (Multi Loan)">
        {facilities.map((f, i) => (
          <div key={i} className="border border-slate-200 rounded-lg p-4 mb-3 bg-slate-50/40" data-testid={`loan-${i}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold text-sm text-[#00A0A0]">Loan #{i + 1}</span>
              {facilities.length > 1 && <button onClick={() => setFacilities((x) => x.filter((_, j) => j !== i))} className="text-red-500 hover:bg-red-50 p-1 rounded" data-testid={`remove-loan-${i}`}><Trash2 size={15} /></button>}
            </div>
            <div className="grid md:grid-cols-3 gap-3">
              <div><label className={lbl}>Nama Cabang</label>
                <select className={inp + " mt-1"} value={f.nama_cabang} onChange={(e) => setLoan(i, { nama_cabang: e.target.value })} data-testid={`loan-cabang-${i}`}>
                  <option value="">Pilih Cabang</option>{branches.map((b) => <option key={b.id} value={b.nama_cabang}>{b.nama_cabang}</option>)}
                </select>
              </div>
              <div><label className={lbl}>Nomor CIF</label><input className={inp + " mt-1"} value={f.cif} onChange={(e) => setLoan(i, { cif: e.target.value })} data-testid={`loan-cif-${i}`} /></div>
              <div><label className={lbl}>Nomor Loan</label><input className={inp + " mt-1"} value={f.nomor_loan} onChange={(e) => setLoan(i, { nomor_loan: e.target.value })} data-testid={`loan-nomor-${i}`} /></div>
              <div><label className={lbl}>Kolektibilitas (PPAP)</label>
                <select className={inp + " mt-1"} value={f.kolektibilitas} onChange={(e) => setLoan(i, { kolektibilitas: e.target.value })} data-testid={`loan-kol-${i}`}>
                  <option value="">Pilih</option>{ref.kolektibilitas.map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
              </div>
              <div><label className={lbl}>Segmen</label>
                <select className={inp + " mt-1"} value={f.segmen} onChange={(e) => changeSegmen(i, e.target.value)} data-testid={`loan-segmen-${i}`}>
                  <option value="">Pilih Segmen</option>{ref.segmen.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div><label className={lbl}>Produk</label>
                <select className={inp + " mt-1"} value={f.produk} onChange={(e) => setLoan(i, { produk: e.target.value })} disabled={!f.segmen} data-testid={`loan-produk-${i}`}>
                  <option value="">{f.segmen ? "Pilih Produk" : "Pilih segmen dulu"}</option>{f.segmen && ref.produk[f.segmen].map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div><label className={lbl}>Skim / Akad</label>
                <select className={inp + " mt-1"} value={f.akad} onChange={(e) => setLoan(i, { akad: e.target.value })} disabled={!f.segmen} data-testid={`loan-akad-${i}`}>
                  <option value="">{f.segmen ? "Pilih Akad" : "Pilih segmen dulu"}</option>{f.segmen && ref.akad[f.segmen].map((a) => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
              <div><label className={lbl}>OS Pokok + Tunggakan Pokok</label><input className={inp + " mt-1"} value={formatNumberInput(f.os_pokok)} onChange={(e) => setLoan(i, { os_pokok: parseNumber(e.target.value) })} data-testid={`loan-ospokok-${i}`} /></div>
              <div><label className={lbl}>OS Margin + Tunggakan Margin</label><input className={inp + " mt-1"} value={formatNumberInput(f.os_margin)} onChange={(e) => setLoan(i, { os_margin: parseNumber(e.target.value) })} data-testid={`loan-osmargin-${i}`} /></div>
              <div><label className={lbl}>Penalty (opsional)</label><input className={inp + " mt-1"} value={formatNumberInput(f.penalty)} onChange={(e) => setLoan(i, { penalty: parseNumber(e.target.value) })} data-testid={`loan-penalty-${i}`} /></div>
              <div className="md:col-span-3 flex items-center justify-between bg-white rounded-md px-3 py-2 border border-slate-200">
                <span className="text-xs font-semibold text-slate-500">Total Kewajiban Loan</span>
                <span className="font-semibold text-[#00A0A0]">{formatRupiah(loanTotal(f))}</span>
              </div>
              <div><label className={lbl}>Jangka Waktu Mulai</label><input type="date" className={inp + " mt-1"} value={isoFromDDMM(f.tgl_mulai)} onChange={(e) => setLoan(i, { tgl_mulai: ddmmFromIso(e.target.value) })} data-testid={`loan-mulai-${i}`} /></div>
              <div><label className={lbl}>Jangka Waktu Akhir</label><input type="date" className={inp + " mt-1"} value={isoFromDDMM(f.tgl_akhir)} onChange={(e) => setLoan(i, { tgl_akhir: ddmmFromIso(e.target.value) })} data-testid={`loan-akhir-${i}`} /></div>
            </div>
          </div>
        ))}
        <button onClick={() => setFacilities((f) => [...f, emptyLoan()])} className="text-sm text-[#00A0A0] font-medium flex items-center gap-1 hover:underline" data-testid="add-loan"><Plus size={16} /> Tambah Loan</button>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-100">
          <Sum label="Nilai Kewenangan Pemutus" value={nilaiKewenangan} highlight />
          <Sum label="Total Kewajiban" value={totalKewajiban} />
        </div>
      </Section>

      {/* Collateral */}
      <Section num={4} title="Agunan / Jaminan">
        <div className="flex items-center gap-4 mb-4">
          <label className="flex items-center gap-2 text-sm"><input type="radio" checked={!hasFixAsset} onChange={() => setHasFixAsset(false)} data-testid="no-fixasset" /> Tidak ada jaminan fix asset</label>
          <label className="flex items-center gap-2 text-sm"><input type="radio" checked={hasFixAsset} onChange={() => { setHasFixAsset(true); if (!collaterals.length) setCollaterals([emptyCollateral()]); }} data-testid="has-fixasset" /> Ada jaminan fix asset</label>
        </div>
        {hasFixAsset && collaterals.map((c, i) => (
          <div key={i} className="border border-slate-200 rounded-lg p-4 mb-3 bg-slate-50/40" data-testid={`collateral-${i}`}>
            <div className="flex items-center justify-between mb-3"><span className="font-semibold text-sm text-[#00A0A0]">Jaminan #{i + 1}</span>
              {collaterals.length > 1 && <button onClick={() => setCollaterals((x) => x.filter((_, j) => j !== i))} className="text-red-500 p-1"><Trash2 size={15} /></button>}</div>
            <div className="grid md:grid-cols-3 gap-3">
              <div><label className={lbl}>Jenis Jaminan</label><input className={inp + " mt-1"} value={c.jenis} onChange={(e) => setCol(setCollaterals, i, { jenis: e.target.value })} data-testid={`col-jenis-${i}`} /></div>
              <div><label className={lbl}>Nilai Pasar</label><input className={inp + " mt-1"} value={formatNumberInput(c.nilai_pasar)} onChange={(e) => setCol(setCollaterals, i, { nilai_pasar: parseNumber(e.target.value) })} data-testid={`col-pasar-${i}`} /></div>
              <div><label className={lbl}>Nilai Likuidasi</label><input className={inp + " mt-1"} value={formatNumberInput(c.nilai_likuidasi)} onChange={(e) => setCol(setCollaterals, i, { nilai_likuidasi: parseNumber(e.target.value) })} data-testid={`col-likuidasi-${i}`} /></div>
              <div><label className={lbl}>Tanggal Penilaian</label><input type="date" className={inp + " mt-1"} value={isoFromDDMM(c.tanggal_penilaian)} onChange={(e) => setCol(setCollaterals, i, { tanggal_penilaian: ddmmFromIso(e.target.value) })} /></div>
              <div><label className={lbl}>Penilaian Jaminan</label>
                <select className={inp + " mt-1"} value={c.penilai} onChange={(e) => setCol(setCollaterals, i, { penilai: e.target.value })} data-testid={`col-penilai-${i}`}>
                  <option value="">Pilih</option>{ref.penilai_jaminan.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              {c.penilai === "KJPP" && <div><label className={lbl}>Nama KJPP</label><input className={inp + " mt-1"} value={c.nama_kjpp} onChange={(e) => setCol(setCollaterals, i, { nama_kjpp: e.target.value })} /></div>}
              <div><label className={lbl}>Nomor Laporan Penilaian</label><input className={inp + " mt-1"} value={c.nomor_laporan} onChange={(e) => setCol(setCollaterals, i, { nomor_laporan: e.target.value })} /></div>
              <div className="md:col-span-3 grid grid-cols-2 gap-3">
                <div className="bg-white rounded-md px-3 py-2 border border-slate-200 text-sm flex justify-between"><span className="text-slate-500">CCR Pasar</span><b>{totalKewajiban ? ((parseNumber(c.nilai_pasar) / totalKewajiban) * 100).toFixed(1) : 0}%</b></div>
                <div className="bg-white rounded-md px-3 py-2 border border-slate-200 text-sm flex justify-between"><span className="text-slate-500">CCR Likuidasi</span><b>{totalKewajiban ? ((parseNumber(c.nilai_likuidasi) / totalKewajiban) * 100).toFixed(1) : 0}%</b></div>
              </div>
            </div>
          </div>
        ))}
        {hasFixAsset && <button onClick={() => setCollaterals((c) => [...c, emptyCollateral()])} className="text-sm text-[#00A0A0] font-medium flex items-center gap-1 hover:underline"><Plus size={16} /> Tambah Jaminan</button>}
      </Section>

      {/* RAC */}
      <Section num={5} title="Risk Acceptance Criteria (RAC)">
        {rac.length === 0 && <p className="text-sm text-slate-400">Pilih segmen pada loan untuk memunculkan RAC.</p>}
        {["KONSUMER", "RETAIL"].map((seg) => {
          const items = rac.filter((r) => r.segment === seg);
          if (!items.length) return null;
          return (
            <div key={seg} className="mb-4">
              <div className="text-xs font-bold text-[#B4842A] uppercase mb-2">RAC {seg}</div>
              {items.map((r) => {
                const idx = rac.indexOf(r);
                return (
                  <div key={r.parameter} className="border border-slate-200 rounded-md p-3 mb-2" data-testid={`rac-${idx}`}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm text-slate-700 flex-1">{r.parameter}</p>
                      <select className="px-2 py-1 border border-slate-300 rounded text-xs bg-white" value={r.status} onChange={(e) => setRac((x) => x.map((y, j) => j === idx ? { ...y, status: e.target.value } : y))} data-testid={`rac-status-${idx}`}>
                        <option>Terpenuhi</option><option>Tidak Terpenuhi</option>
                      </select>
                    </div>
                    {r.status === "Tidak Terpenuhi" && (
                      <input className={inp + " mt-2"} placeholder="Keterangan (wajib)" value={r.keterangan} onChange={(e) => setRac((x) => x.map((y, j) => j === idx ? { ...y, keterangan: e.target.value } : y))} data-testid={`rac-ket-${idx}`} />
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
        {rac.some((r) => r.status === "Tidak Terpenuhi") && (
          <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
            <AlertTriangle size={16} /> Ada RAC tidak terpenuhi → pemutus naik 1 level & wajib Risk Assessment.
          </div>
        )}
      </Section>

      {/* Analysis */}
      <Section num={6} title="Analisa">
        <div className="space-y-3">
          <div className="text-sm bg-slate-50 rounded-md p-3 border border-slate-100"><b>Profil / Karakter:</b> otomatis terisi pada nota final.</div>
          <div><label className={lbl}>Jelaskan Penyebab Nasabah Bermasalah</label>
            <textarea className={inp + " mt-1"} rows={3} value={analysis.penyebab_bermasalah} onChange={(e) => setAnalysis({ ...analysis, penyebab_bermasalah: e.target.value })} data-testid="nf-penyebab" placeholder="Uraikan penyebab nasabah mengalami permasalahan pembiayaan..." />
          </div>
          <div><label className={lbl}>Kemampuan Bayar / Repayment Capacity</label>
            <select className={inp + " mt-1"} value={analysis.kemampuan_bayar} onChange={(e) => setAnalysis({ ...analysis, kemampuan_bayar: e.target.value })} data-testid="nf-kemampuan">
              <option value="">Pilih</option>{ref.kemampuan_bayar.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>
      </Section>

      {/* Documents */}
      <Section num={7} title="Upload Dokumen">
        <div className="grid md:grid-cols-2 gap-3">
          {ref.document_types.map((dt) => {
            const uploaded = documents[dt.key];
            const required = dt.required || (dt.required_if_fix_asset && hasFixAsset);
            const pct = progress[dt.key];
            return (
              <div key={dt.key} className="border border-slate-200 rounded-md p-3 flex items-center justify-between gap-3" data-testid={`doc-${dt.key}`}>
                <div className="text-sm flex-1 min-w-0">
                  <div className="text-slate-700">{dt.label} {required && <span className="text-red-500">*</span>}</div>
                  {uploaded && !pct && <div className="text-xs text-emerald-600 flex items-center gap-1 mt-0.5"><Check size={12} /> {uploaded.original}</div>}
                  {pct != null && (
                    <div className="mt-1.5" data-testid={`doc-progress-${dt.key}`}>
                      <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden"><div className="h-full bg-[#00A0A0] transition-all" style={{ width: `${pct}%` }} /></div>
                      <div className="text-[10px] text-slate-400 mt-0.5">Mengupload... {pct}%</div>
                    </div>
                  )}
                </div>
                <label className="text-xs bg-[#E6F6F6] text-[#00A0A0] rounded-md px-3 py-1.5 cursor-pointer flex items-center gap-1 whitespace-nowrap">
                  <Upload size={13} /> {uploaded ? "Ganti" : "Upload"}
                  <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => e.target.files[0] && uploadDoc(dt.key, e.target.files[0])} data-testid={`doc-input-${dt.key}`} />
                </label>
              </div>
            );
          })}
        </div>

        {/* Dokumen tambahan dinamis */}
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold text-slate-500">Dokumen Tambahan</div>
          {customDocs.map((c) => {
            const pct = progress[c.id];
            return (
              <div key={c.id} className="border border-slate-200 rounded-md p-3 flex items-center gap-3" data-testid={`custom-doc-${c.id}`}>
                <div className="flex-1 min-w-0">
                  <input className={inp} placeholder="Nama dokumen (mis. Rekening Koran, Sertifikat, dll)" value={c.label} onChange={(e) => setCustomLabel(c.id, e.target.value)} data-testid={`custom-doc-label-${c.id}`} />
                  {c.uploaded && !pct && <div className="text-xs text-emerald-600 flex items-center gap-1 mt-1"><Check size={12} /> {c.uploaded.original}</div>}
                  {pct != null && (
                    <div className="mt-1.5">
                      <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden"><div className="h-full bg-[#00A0A0] transition-all" style={{ width: `${pct}%` }} /></div>
                      <div className="text-[10px] text-slate-400 mt-0.5">Mengupload... {pct}%</div>
                    </div>
                  )}
                </div>
                <label className="text-xs bg-[#E6F6F6] text-[#00A0A0] rounded-md px-3 py-1.5 cursor-pointer flex items-center gap-1 whitespace-nowrap">
                  <Upload size={13} /> {c.uploaded ? "Ganti" : "Upload"}
                  <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => e.target.files[0] && uploadCustomDoc(c.id, e.target.files[0])} data-testid={`custom-doc-input-${c.id}`} />
                </label>
                <button type="button" onClick={() => removeCustomDoc(c.id)} className="text-red-500 hover:bg-red-50 p-1.5 rounded" title="Hapus dokumen"><X size={15} /></button>
              </div>
            );
          })}
          <button type="button" onClick={addCustomDoc} data-testid="add-custom-doc" className="text-sm text-[#00A0A0] font-medium flex items-center gap-1 hover:underline"><Plus size={16} /> Tambah Dokumen Upload</button>
        </div>
      </Section>

      {/* Actions */}
      <div className="sticky bottom-0 bg-white border border-slate-200 rounded-lg shadow-lg p-4 flex items-center justify-between gap-3 flex-wrap">
        <div className="text-sm text-slate-500">Nilai Kewenangan Pemutus: <b className="text-[#00A0A0]">{formatRupiah(nilaiKewenangan)}</b></div>
        <div className="flex gap-2">
          <button onClick={() => save(false)} disabled={saving} className="border border-slate-300 text-slate-700 font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2 hover:bg-slate-50 disabled:opacity-60" data-testid="save-draft">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} Simpan Draft
          </button>
          <button onClick={async () => { const nid = await save(true); if (nid) navigate(`/notes/${nid}`); }} className="border border-[#00A0A0] text-[#00A0A0] font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2 hover:bg-[#E6F6F6]" data-testid="preview-btn">
            <Eye size={16} /> Preview
          </button>
          <button onClick={() => setConfirmSubmit(true)} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2" data-testid="submit-btn">
            <Send size={16} /> Kirim Nota
          </button>
        </div>
      </div>

      {confirmSubmit && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6 text-center" data-testid="confirm-submit-dialog">
            <div className="w-12 h-12 rounded-full bg-[#FDF7EB] flex items-center justify-center mx-auto mb-3"><Send className="text-[#F0B43C]" /></div>
            <h3 className="font-display font-bold text-lg mb-1">Kirim Nota?</h3>
            <p className="text-sm text-slate-500 mb-5">Pastikan data yang anda input sudah benar.</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmSubmit(false)} className="flex-1 border border-slate-300 rounded-md py-2.5 text-sm font-semibold" data-testid="cancel-submit">Kembali Edit</button>
              <button onClick={doSubmit} className="flex-1 bg-[#00A0A0] text-white rounded-md py-2.5 text-sm font-semibold" data-testid="confirm-submit">Kirim Nota</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Sum({ label, value, highlight }) {
  return (
    <div className={`rounded-md px-3 py-2.5 border ${highlight ? "bg-[#E6F6F6] border-[#00A0A0]" : "bg-slate-50 border-slate-200"}`}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`font-display font-bold ${highlight ? "text-[#00A0A0]" : "text-slate-800"}`}>{formatRupiah(value)}</div>
    </div>
  );
}

const setCol = (setter, i, patch) => setter((c) => c.map((x, j) => (j === i ? { ...x, ...patch } : x)));

function isoFromDDMM(s) {
  if (!s || !s.includes("/")) return "";
  const [d, m, y] = s.split("/");
  return `${y}-${m}-${d}`;
}
function ddmmFromIso(s) {
  if (!s) return "";
  const [y, m, d] = s.split("-");
  return `${d}/${m}/${y}`;
}
