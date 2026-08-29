import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api, { apiError, API } from "../lib/api";
import { StatusBadge } from "../components/StatusBadge";
import { formatRupiah } from "../lib/format";
import {
  ArrowLeft, Edit, Send, Check, X, RotateCcw, Download, Loader2, CheckCircle2, ShieldCheck, FileText, Eye
} from "lucide-react";
import { toast } from "sonner";

const IMMADHA_NIP = "2175007386";

export default function NoteDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [actionModal, setActionModal] = useState(null); // {decision}
  const [catatan, setCatatan] = useState("");
  const [disposisi, setDisposisi] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api.get(`/notes/${id}`).then((r) => setNote(r.data)).catch((e) => { toast.error(apiError(e)); navigate("/notes"); });
  useEffect(() => { load(); }, [id]);

  if (!note) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  const stage = (note.stages || [])[note.stage_index];
  const isDraftLike = note.status === "Draft" || note.status?.startsWith("Revisi") || note.status?.startsWith("Reject");
  const isOwner = note.creator_id === user.id;
  const isApproved = note.status === "Final Approved";

  // Can the current user act at the current stage?
  let canAct = false, isDecide = false;
  if (stage && !isApproved) {
    const [level, act] = stage;
    isDecide = act === "decide";
    if (level === "ACRM") canAct = user.role === "ACRM" && user.area === note.area;
    else if (level === "RCRM") canAct = user.role === "RCRM" && user.region === note.region;
    else if (level === "RCG") canAct = user.nip === (note.rcg_pemutus_nip || IMMADHA_NIP);
  }

  const submitNote = async () => {
    setBusy(true);
    try { await api.post(`/notes/${id}/submit`); toast.success("Nota dikirim"); load(); }
    catch (e) { toast.error(apiError(e)); }
    finally { setBusy(false); }
  };

  const doAction = async () => {
    setBusy(true);
    try {
      await api.post(`/notes/${id}/action`, { decision: actionModal.decision, catatan, disposisi });
      toast.success("Aksi berhasil");
      setActionModal(null); setCatatan(""); setDisposisi(""); load();
    } catch (e) { toast.error(apiError(e)); }
    finally { setBusy(false); }
  };

  const download = async () => {
    try {
      const token = localStorage.getItem("rcg_token");
      const res = await fetch(`${API}/notes/${id}/pdf`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Gagal unduh"); }
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `Nota_${(note.nomor_nota || "draft").replace(/[/ ]/g, "_")}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-slate-500 text-sm hover:text-slate-800"><ArrowLeft size={16} /> Kembali</button>
        <div className="flex items-center gap-2 flex-wrap">
          <StatusBadge status={note.status} testid="detail-status" />
          {note.can_download && <button onClick={download} className="bg-[#F0B43C] hover:bg-[#D9A236] text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="detail-download"><Download size={15} /> Download PDF</button>}
          {isOwner && isDraftLike && (
            <>
              <button onClick={() => navigate(`/notes/${id}/edit`)} className="border border-slate-300 font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5 hover:bg-slate-50" data-testid="detail-edit"><Edit size={15} /> Edit</button>
              {note.status === "Draft" && <button onClick={submitNote} disabled={busy} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="detail-submit"><Send size={15} /> Kirim</button>}
            </>
          )}
        </div>
      </div>

      {/* Approver action bar */}
      {canAct && (
        <div className="bg-[#E6F6F6] border border-[#00A0A0]/30 rounded-lg p-4 mb-4 flex items-center justify-between flex-wrap gap-3" data-testid="action-bar">
          <div className="text-sm text-slate-700">
            <b>Tindakan Anda diperlukan</b> — Anda berperan sebagai {isDecide ? "Pemutus" : "Pengusul/Reviewer"} pada nota ini.
          </div>
          <div className="flex gap-2">
            {isDecide
              ? <button onClick={() => setActionModal({ decision: "approve" })} className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="act-approve"><Check size={15} /> Approve</button>
              : <button onClick={() => setActionModal({ decision: "forward" })} className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="act-forward"><Send size={15} /> Teruskan</button>}
            <button onClick={() => setActionModal({ decision: "revisi" })} className="bg-amber-500 hover:bg-amber-600 text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="act-revisi"><RotateCcw size={15} /> Revisi</button>
            <button onClick={() => setActionModal({ decision: "reject" })} className="bg-red-500 hover:bg-red-600 text-white font-semibold px-3 py-2 rounded-md text-sm flex items-center gap-1.5" data-testid="act-reject"><X size={15} /> Reject</button>
          </div>
        </div>
      )}

      {note.final_approver_level === "ABOVE_RCG" && !isApproved && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-sm text-red-700 flex items-center gap-2" data-testid="escalation-banner">
          <ShieldCheck size={18} /> Nilai kewenangan melebihi Rp30 Miliar. Nota memerlukan eskalasi komite di atas RCG dan tidak dapat di-approve oleh IMMADHA.
        </div>
      )}

      {/* Document preview */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden" data-testid="note-preview">
        <div className="bg-[#00A0A0] text-white px-6 py-4 flex items-center justify-between">
          <div className="font-display font-bold text-lg">NOTA ANALISA RESTRUKTUR PEMBIAYAAN</div>
          <div className="text-xs opacity-80">BSI • RCG</div>
        </div>

        {isApproved && (
          <div className="bg-emerald-500 text-white px-6 py-3 flex items-center justify-between" data-testid="approved-stamp">
            <div className="flex items-center gap-2 font-display font-bold text-xl"><CheckCircle2 /> APPROVED</div>
            <div className="text-sm">Tanggal Approved: {note.approved_date} {note.approved_time}</div>
          </div>
        )}

        <div className="p-6 space-y-5 text-sm">
          <KV rows={[
            ["Nomor Nota", note.nomor_nota || "-"],
            ["Dari", note.dari],
            ["Tanggal", note.tanggal_nota],
            ["Pemutus", note.kepada || "-"],
            ["Reff", `Surat Permohonan Nasabah tanggal ${note.reff_tanggal || "-"}`],
            ["Perihal", note.perihal],
          ]} />

          <Block title="Informasi Nasabah">
            <KV rows={[
              ["Nama Nasabah", note.customer?.nama],
              ["Alamat", note.customer?.alamat],
              ["No. Kontak", note.customer?.no_kontak],
              ["Restrukturisasi ke", note.customer?.restrukturisasi_ke],
            ]} />
          </Block>

          <Block title="Fasilitas Pembiayaan Existing">
            <Table head={["Cabang", "CIF", "No Loan", "Kol", "Segmen/Produk", "Akad", "OS Pokok", "OS Margin", "Penalty", "Total"]}
              rows={(note.facilities || []).map((f) => [f.nama_cabang, f.cif, f.nomor_loan, f.kolektibilitas, `${f.segmen}/${f.produk}`, f.akad, formatRupiah(f.os_pokok), formatRupiah(f.os_margin), formatRupiah(f.penalty), formatRupiah(f.total_kewajiban)])} />
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3">
              <Mini label="Total OS Pokok" value={note.total_os_pokok} />
              <Mini label="Total OS Margin" value={note.total_os_margin} />
              <Mini label="Total Penalty" value={note.total_penalty} />
              <Mini label="Total Kewajiban" value={note.total_kewajiban} />
            </div>
          </Block>

          <Block title="Agunan / Jaminan">
            {note.has_fix_asset && note.collaterals?.length
              ? <Table head={["Jenis", "Nilai Pasar", "Nilai Likuidasi", "CCR Pasar", "CCR Likuidasi", "Penilai"]}
                  rows={note.collaterals.map((c) => [c.jenis, formatRupiah(c.nilai_pasar), formatRupiah(c.nilai_likuidasi), `${c.ccr_pasar}%`, `${c.ccr_likuidasi}%`, c.penilai === "KJPP" && c.nama_kjpp ? `KJPP - ${c.nama_kjpp}` : c.penilai])} />
              : <p className="text-slate-500">Tidak ada jaminan fix asset</p>}
          </Block>

          <Block title="Risk Acceptance Criteria (RAC)">
            <Table head={["Parameter", "Status", "Keterangan"]}
              rows={(note.rac || []).map((r) => [r.parameter, r.status, r.keterangan || "-"])} />
          </Block>

          {note.ra_required && (
            <Block title="Risk Assessment (FRA Unit)">
              <KV rows={[["Status", note.risk_assessment?.status || "Belum dilakukan"]]} />
            </Block>
          )}

          <Block title="Analisa">
            <KV rows={[
              ["Profil / Kondisi Usaha", note.analysis?.profil],
              ["Karakter", note.analysis?.karakter],
              ["Penyebab Nasabah Bermasalah", note.analysis?.penyebab_bermasalah],
              ["Kemampuan Bayar", note.analysis?.kemampuan_bayar],
              ["Informasi Jaminan & CCR", note.analysis?.informasi_jaminan],
              ["TBO", note.analysis?.tbo],
            ]} />
          </Block>

          <Block title="Usulan Restrukturisasi">
            <p className="text-slate-600 mb-3 italic">{note.usulan_kalimat}</p>
            <Table head={["Jenis Fasilitas", "Akad", "Tujuan", "OS Pokok", "OS Margin", "Jangka Waktu"]}
              rows={(note.proposals || []).map((p) => [p.jenis_fasilitas, p.akad, p.tujuan, formatRupiah(p.os_pokok), formatRupiah(p.os_margin), `${p.tgl_mulai || "-"} s/d ${p.tgl_akhir || "-"} ${p.durasi ? `(${p.durasi})` : ""}`])} />
          </Block>

          {(note.documents || []).length > 0 && (
            <Block title="Dokumen Pendukung (Upload RCO)">
              <div className="space-y-2" data-testid="note-documents">
                {(note.documents || []).map((d, i) => {
                  const fileUrl = `${API}/files/${d.file_path}`;
                  const isImg = /\.(png|jpe?g|webp)$/i.test(d.file_path || "");
                  return (
                    <div key={i} className="flex items-center justify-between gap-3 border border-slate-200 rounded-md px-3 py-2 bg-slate-50" data-testid={`doc-row-${i}`}>
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText size={16} className="text-[#00A0A0] shrink-0" />
                        <div className="min-w-0">
                          <div className="text-slate-800 font-medium truncate">{d.label || d.filename || d.document_type}</div>
                          <div className="text-xs text-slate-400">{d.document_type}{isImg ? " · gambar" : (d.file_path?.toLowerCase().endsWith(".pdf") ? " · PDF" : "")}</div>
                        </div>
                      </div>
                      {d.file_path && (
                        <div className="flex items-center gap-2 shrink-0">
                          <a href={fileUrl} target="_blank" rel="noopener noreferrer" className="text-[#00A0A0] hover:bg-[#E6F6F6] border border-[#00A0A0]/40 rounded-md px-2.5 py-1.5 text-xs font-semibold flex items-center gap-1" data-testid={`doc-preview-${i}`}><Eye size={13} /> Preview</a>
                          <a href={fileUrl} download className="text-slate-600 hover:bg-slate-100 border border-slate-300 rounded-md px-2.5 py-1.5 text-xs font-semibold flex items-center gap-1" data-testid={`doc-download-${i}`}><Download size={13} /> Download</a>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Block>
          )}

          {note.disposisi_pemutus && (
            <Block title="Disposisi Pemutus">
              <p className="text-slate-800 whitespace-pre-line" data-testid="disposisi-pemutus">{note.disposisi_pemutus}</p>
            </Block>
          )}

          <Block title="Riwayat Persetujuan">
            <Table head={["User", "Role", "Fungsi", "Keputusan", "Catatan", "Waktu"]}
              rows={(note.approvals || []).map((a) => [a.nama, a.role, a.fungsi, a.keputusan, a.catatan || "-", `${a.date} ${a.time}`])} />
          </Block>

          {isApproved && (
            <>
              <Block title="Informasi Pengusul & Pemutus">
                <KV rows={[
                  ["Pengusul", `${note.creator_nama} — NIP ${note.creator_nip}`],
                  ["Pemutus", `${note.final_approver_nama} — NIP ${note.final_approver_nip}`],
                  ["Jabatan Pemutus", note.final_approver_jabatan],
                  ["Level Pemutus", note.final_approver_level],
                  ["Limit Pemutus Digunakan", formatRupiah(note.limit_pemutus_used)],
                  ["Tanggal & Jam Approved", `${note.approved_date} ${note.approved_time}`],
                ]} />
              </Block>
              <div className="bg-slate-50 border border-slate-200 rounded-md p-4 text-xs text-slate-500 italic" data-testid="approved-keterangan">
                {note.approved_keterangan}
              </div>
            </>
          )}
        </div>
      </div>

      {actionModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => { setActionModal(null); setCatatan(""); setDisposisi(""); }}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6" onClick={(e) => e.stopPropagation()} data-testid="action-modal">
            <h3 className="font-display font-bold text-lg mb-1 capitalize">
              {{ approve: "Disposisi Pemutus", forward: "Teruskan Nota", revisi: "Kembalikan untuk Revisi", reject: "Tolak Nota" }[actionModal.decision]}
            </h3>
            {actionModal.decision === "approve" ? (
              <>
                <p className="text-sm text-slate-500 mb-4">Isi Disposisi Pemutus <b>(wajib)</b>. Disposisi akan tercatat otomatis pada nota.</p>
                <textarea className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm mb-4 outline-none focus:border-[#00A0A0]" rows={4} value={disposisi} onChange={(e) => setDisposisi(e.target.value)} placeholder="Tuliskan disposisi/keputusan pemutus..." data-testid="action-disposisi" />
              </>
            ) : (
              <>
                <p className="text-sm text-slate-500 mb-4">Tambahkan catatan {actionModal.decision === "forward" ? "(opsional)" : "(wajib)"}.</p>
                <textarea className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm mb-4 outline-none focus:border-[#00A0A0]" rows={3} value={catatan} onChange={(e) => setCatatan(e.target.value)} data-testid="action-catatan" />
              </>
            )}
            <div className="flex gap-2">
              <button onClick={() => { setActionModal(null); setCatatan(""); setDisposisi(""); }} className="flex-1 border border-slate-300 rounded-md py-2.5 text-sm font-semibold">Batal</button>
              <button onClick={doAction} disabled={busy || (actionModal.decision === "approve" && !disposisi.trim()) || ((actionModal.decision === "revisi" || actionModal.decision === "reject") && !catatan)} className="flex-1 bg-[#00A0A0] text-white rounded-md py-2.5 text-sm font-semibold disabled:opacity-50 flex items-center justify-center gap-1.5" data-testid="action-confirm">
                {busy && <Loader2 size={15} className="animate-spin" />} Konfirmasi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Block({ title, children }) {
  return (
    <div>
      <div className="bg-[#00A0A0] text-white text-xs font-semibold uppercase tracking-wide px-3 py-1.5 rounded-t-md">{title}</div>
      <div className="border border-t-0 border-slate-200 rounded-b-md p-3">{children}</div>
    </div>
  );
}

function KV({ rows }) {
  return (
    <table className="w-full text-sm">
      <tbody>
        {rows.map(([k, v], i) => (
          <tr key={i} className="border-b border-slate-100 last:border-0">
            <td className="py-1.5 pr-4 font-semibold text-slate-500 align-top w-52">{k}</td>
            <td className="py-1.5 text-slate-800">{v || "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Table({ head, rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead><tr className="bg-slate-50 text-slate-500 uppercase tracking-wider">
          {head.map((h) => <th key={h} className="text-left font-semibold px-2 py-1.5 whitespace-nowrap">{h}</th>)}
        </tr></thead>
        <tbody>
          {rows.length === 0 && <tr><td colSpan={head.length} className="text-center text-slate-400 py-4">-</td></tr>}
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-slate-100">
              {r.map((c, j) => <td key={j} className="px-2 py-1.5 text-slate-700">{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Mini({ label, value, highlight }) {
  return (
    <div className={`rounded-md px-3 py-2 border ${highlight ? "bg-[#E6F6F6] border-[#00A0A0]" : "bg-slate-50 border-slate-200"}`}>
      <div className="text-[10px] text-slate-500 uppercase">{label}</div>
      <div className={`font-semibold text-sm ${highlight ? "text-[#00A0A0]" : "text-slate-800"}`}>{formatRupiah(value)}</div>
    </div>
  );
}
