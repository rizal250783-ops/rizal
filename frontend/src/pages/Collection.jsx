import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api, { API, apiErr } from "../lib/api";
import { fmtShort, statusColor } from "../lib/utils";
import { Card, Button, Input, Select, Th, Td, Empty, Badge, SectionTitle } from "../components/ui";
import { Plus, MapPin, Camera, X, CheckCircle, XCircle, Image as ImageIcon } from "lucide-react";

const STATUS = ["Dikunjungi", "Berkomunikasi", "Janji Bayar", "Pembayaran Masuk", "Tidak Ditemui", "Restrukturisasi", "Eskalasi"];

function fileUrl(path) { const t = localStorage.getItem("ao360_token"); return `${API}/files/${path}?auth=${t}`; }

export default function Collection() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [gallery, setGallery] = useState(null);

  const load = () => api.get("/collection-activities").then((r) => setRows(r.data));
  useEffect(() => { load(); }, []);

  const review = async (id, action) => {
    await api.post(`/collection-activities/${id}/review?action=${action}`);
    load();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <SectionTitle sub="Dokumentasi aktivitas penagihan / kunjungan nasabah">Riwayat Dokumentasi</SectionTitle>
        {(user.role === "ao_lending" || user.role === "pic_remedial" || user.role === "admin") && (
          <Button variant="gold" onClick={() => setOpen(true)} data-testid="add-activity-btn"><Plus size={16} /> Aktivitas Penagihan</Button>
        )}
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr><Th>Tanggal</Th><Th>No. Kontrak</Th><Th>Nasabah</Th><Th className="text-right">Outstanding</Th><Th>PIC</Th><Th>Foto</Th><Th>Lokasi</Th><Th>Status</Th><Th>Validasi</Th><Th>Approval</Th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((a) => {
                const photo = a.photos?.[0];
                const hasLoc = photo && photo.latitude != null;
                return (
                  <tr key={a.id} data-testid={`activity-row-${a.id}`}>
                    <Td className="text-xs">{a.tanggal_aktivitas}<div className="text-slate-400">{a.jam_aktivitas}</div></Td>
                    <Td className="font-num text-xs">{a.nomor_kontrak}</Td>
                    <Td className="font-medium text-slate-900">{a.nama_nasabah}</Td>
                    <Td className="text-right font-num">{fmtShort(a.outstanding_pokok)}</Td>
                    <Td className="text-xs">{a.user_name}</Td>
                    <Td>
                      {a.photos?.length ? (
                        <button onClick={() => setGallery(a)} className="flex items-center gap-1 text-emerald-700 hover:underline text-sm" data-testid={`view-photos-${a.id}`}>
                          <ImageIcon size={16} /> {a.photos.length}
                        </button>
                      ) : <span className="text-slate-300 text-xs">-</span>}
                    </Td>
                    <Td>
                      {hasLoc ? (
                        <a href={`https://maps.google.com/?q=${photo.latitude},${photo.longitude}`} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-emerald-700 hover:underline text-sm" data-testid={`view-location-${a.id}`}>
                          <MapPin size={14} /> Lihat Lokasi
                        </a>
                      ) : <span className="text-xs text-slate-400">Lokasi tidak tersedia</span>}
                    </Td>
                    <Td><Badge className={statusColor(a.status_penagihan === "Pembayaran Masuk" ? "Good" : "N/A")}>{a.status_penagihan}</Badge></Td>
                    <Td><Badge className={a.status_validasi === "Valid" ? statusColor("Sehat") : statusColor("Need Attention")}>{a.status_validasi}</Badge></Td>
                    <Td>
                      {user.role === "admin" ? (
                        a.approval_status === "Pending" ? (
                          <div className="flex gap-1">
                            <button onClick={() => review(a.id, "approve")} className="text-emerald-600 hover:bg-emerald-50 rounded p-1" data-testid={`approve-${a.id}`}><CheckCircle size={18} /></button>
                            <button onClick={() => review(a.id, "reject")} className="text-red-600 hover:bg-red-50 rounded p-1" data-testid={`reject-${a.id}`}><XCircle size={18} /></button>
                          </div>
                        ) : <Badge className={statusColor(a.approval_status === "Approved" ? "Sehat" : "Critical")}>{a.approval_status}</Badge>
                      ) : <Badge className={statusColor(a.approval_status === "Approved" ? "Sehat" : a.approval_status === "Rejected" ? "Critical" : "N/A")}>{a.approval_status}</Badge>}
                    </Td>
                  </tr>
                );
              })}
              {rows.length === 0 && <tr><td colSpan={10}><Empty>Belum ada dokumentasi.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>

      {open && <ActivityModal onClose={() => { setOpen(false); load(); }} />}
      {gallery && <GalleryModal activity={gallery} onClose={() => setGallery(null)} />}
    </div>
  );
}

function ActivityModal({ onClose }) {
  const now = new Date();
  const [form, setForm] = useState({
    tanggal_aktivitas: now.toISOString().slice(0, 10),
    jam_aktivitas: now.toTimeString().slice(0, 5),
    nomor_kontrak: "", nama_nasabah: "", outstanding_pokok: "",
    status_penagihan: STATUS[0], catatan: "",
  });
  const [files, setFiles] = useState([]);
  const [gps, setGps] = useState({ lat: null, lon: null });
  const [gpsStatus, setGpsStatus] = useState("Meminta lokasi...");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => { setGps({ lat: pos.coords.latitude, lon: pos.coords.longitude }); setGpsStatus("Lokasi terdeteksi"); },
        () => setGpsStatus("Lokasi tidak tersedia (izin ditolak)"),
        { timeout: 8000 }
      );
    } else setGpsStatus("GPS tidak didukung perangkat");
  }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const onFiles = (e) => {
    const f = Array.from(e.target.files).slice(0, 5);
    setFiles(f);
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setSaving(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v || ""));
      if (gps.lat != null) { fd.append("latitude", gps.lat); fd.append("longitude", gps.lon); }
      files.forEach((f) => fd.append("files", f));
      await api.post("/collection-activities", fd, { headers: { "Content-Type": "multipart/form-data" } });
      onClose();
    } catch (e2) { setErr(apiErr(e2)); } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="card w-full max-w-lg max-h-[92vh] overflow-y-auto p-6" data-testid="activity-modal">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-lg font-bold text-slate-900">Aktivitas Penagihan</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs font-medium text-slate-600">Tanggal</label><Input type="date" value={form.tanggal_aktivitas} onChange={(e) => set("tanggal_aktivitas", e.target.value)} required data-testid="act-date" /></div>
            <div><label className="text-xs font-medium text-slate-600">Jam</label><Input type="time" value={form.jam_aktivitas} onChange={(e) => set("jam_aktivitas", e.target.value)} required data-testid="act-time" /></div>
          </div>
          <div><label className="text-xs font-medium text-slate-600">Nomor Kontrak</label><Input value={form.nomor_kontrak} onChange={(e) => set("nomor_kontrak", e.target.value)} required data-testid="act-kontrak" /></div>
          <div><label className="text-xs font-medium text-slate-600">Nama Nasabah</label><Input value={form.nama_nasabah} onChange={(e) => set("nama_nasabah", e.target.value)} required data-testid="act-nasabah" /></div>
          <div><label className="text-xs font-medium text-slate-600">Outstanding Pokok</label><Input type="number" value={form.outstanding_pokok} onChange={(e) => set("outstanding_pokok", e.target.value)} data-testid="act-outstanding" /></div>
          <div><label className="text-xs font-medium text-slate-600">Status Penagihan</label>
            <Select value={form.status_penagihan} onChange={(e) => set("status_penagihan", e.target.value)} data-testid="act-status">
              {STATUS.map((s) => <option key={s}>{s}</option>)}
            </Select>
          </div>
          <div><label className="text-xs font-medium text-slate-600">Catatan</label>
            <textarea className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus-ring" rows={2} value={form.catatan} onChange={(e) => set("catatan", e.target.value)} data-testid="act-note" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Foto (maks 5, watermark otomatis)</label>
            <label className="mt-1 flex items-center gap-2 rounded-lg border-2 border-dashed border-slate-300 px-4 py-3 cursor-pointer hover:bg-slate-50">
              <Camera size={18} className="text-emerald-700" />
              <span className="text-sm text-slate-600">{files.length ? `${files.length} foto dipilih` : "Pilih / ambil foto"}</span>
              <input type="file" accept="image/*" multiple capture="environment" className="hidden" onChange={onFiles} data-testid="act-photos" />
            </label>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <MapPin size={14} className={gps.lat ? "text-emerald-600" : "text-slate-400"} />
            <span className={gps.lat ? "text-emerald-700" : "text-slate-500"} data-testid="gps-status">{gpsStatus}{gps.lat ? `: ${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)}` : ""}</span>
          </div>
          {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">Batal</Button>
            <Button type="submit" disabled={saving} className="flex-1" data-testid="act-submit">{saving ? "Menyimpan..." : "Simpan Aktivitas"}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function GalleryModal({ activity, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div className="card w-full max-w-3xl max-h-[92vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()} data-testid="gallery-modal">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-lg font-bold">Dokumentasi Foto · {activity.nama_nasabah}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {activity.photos.map((p) => (
            <div key={p.id} className="rounded-lg overflow-hidden border border-slate-200">
              <img src={fileUrl(p.foto_url)} alt="Dokumentasi" className="w-full h-56 object-cover" />
              <div className="p-3 text-xs space-y-1">
                {p.waktu_upload_fallback && <div className="text-gold-700">Waktu foto berdasarkan waktu upload (metadata asli tidak tersedia)</div>}
                <div className="text-slate-500">{p.timestamp_foto?.slice(0, 19).replace("T", " ")}</div>
                {p.latitude != null ? (
                  <a href={`https://maps.google.com/?q=${p.latitude},${p.longitude}`} target="_blank" rel="noreferrer" className="text-emerald-700 hover:underline flex items-center gap-1"><MapPin size={12} /> {p.latitude}, {p.longitude}</a>
                ) : <div className="text-slate-400">Lokasi tidak tersedia</div>}
                <Badge className={p.status_validasi === "Valid" ? statusColor("Sehat") : statusColor("Need Attention")}>{p.status_validasi}</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
