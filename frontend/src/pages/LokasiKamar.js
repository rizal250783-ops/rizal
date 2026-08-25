import React, { useEffect, useState } from "react";
import { MapPin, DoorOpen, Plus, Trash2, Archive } from "lucide-react";
import { toast } from "sonner";
import api from "../api";
import { Modal, Badge, inputClass } from "../components/ui";
import AddTenantForm from "../components/AddTenantForm";
import { formatRupiah } from "../utils";

export default function LokasiKamar() {
  const [locations, setLocations] = useState([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState(null);
  const [addRoom, setAddRoom] = useState(null);
  const [viewTenant, setViewTenant] = useState(null);
  const [err, setErr] = useState("");

  const loadLocations = () => api.get("/locations").then((r) => {
    setLocations(r.data);
    setSelected((prev) => prev || (r.data.length ? r.data[0].id : ""));
  }).catch(() => {});

  const loadDetail = (id) => {
    if (!id) { setDetail(null); return; }
    setErr("");
    api.get(`/locations/${id}/rooms`).then((r) => setDetail(r.data)).catch(() => {
      setErr("Gagal memuat data kamar. Silakan coba lagi.");
    });
  };

  useEffect(() => { loadLocations(); }, []);
  useEffect(() => { loadDetail(selected); }, [selected]);

  const refresh = () => { loadDetail(selected); loadLocations(); };

  const openRoom = (room) => {
    if (room.status === "kosong") {
      setAddRoom({ ...room, lokasi: detail.lokasi.nama });
    } else {
      setViewTenant(room);
    }
  };

  const vacate = async (room) => {
    if (!window.confirm("Kosongkan kamar ini? Penghuni akan dilepas dari kamar.")) return;
    try {
      await api.post(`/rooms/${room.id}/vacate`);
      toast.success("Kamar berhasil dikosongkan");
      setViewTenant(null);
      refresh();
    } catch (e) { toast.error("Gagal mengosongkan kamar"); }
  };

  const removeTenant = async (tenantId, mode) => {
    const ok = window.confirm(
      mode === "delete"
        ? "Hapus penghuni ini secara permanen beserta data pembayarannya?"
        : "Arsipkan penghuni ini?"
    );
    if (!ok) return;
    try {
      if (mode === "delete") await api.delete(`/tenants/${tenantId}`);
      else await api.post(`/tenants/${tenantId}/archive`);
      toast.success(mode === "delete" ? "Penghuni dihapus" : "Penghuni diarsipkan");
      setViewTenant(null);
      refresh();
    } catch (e) { toast.error("Gagal memproses"); }
  };

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="text-3xl font-heading font-extrabold text-navy">Lokasi & Kamar</h1>
        <p className="text-slate-500">Kelola kamar di 4 lokasi kost</p>
      </div>

      <select className={`${inputClass} max-w-md mb-6`} value={selected} onChange={(e) => setSelected(e.target.value)} data-testid="lokasi-filter-select">
        {locations.map((l) => (
          <option key={l.id} value={l.id}>{l.nama}</option>
        ))}
      </select>

      {err && (
        <div className="text-rose-600 text-sm break-all" data-testid="lokasi-error">{err}</div>
      )}

      {!detail && !err && (
        <div className="text-slate-500" data-testid="lokasi-loading">Memuat kamar...</div>
      )}

      {detail && (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-6 mb-6" data-testid="lokasi-summary">
            <div className="flex items-start gap-3">
              <span className="w-11 h-11 rounded-xl bg-navy text-gold flex items-center justify-center flex-shrink-0"><MapPin size={20} /></span>
              <div className="flex-1">
                <h2 className="font-heading font-bold text-xl text-navy">{detail.lokasi.nama}</h2>
                <p className="text-slate-500 text-sm">{detail.lokasi.alamat}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-5">
              <div className="text-center bg-slate-50 rounded-xl py-3">
                <div className="text-2xl font-heading font-extrabold text-navy">{detail.total_kamar}</div>
                <div className="text-xs text-slate-500">Total Kamar</div>
              </div>
              <div className="text-center bg-emerald-50 rounded-xl py-3">
                <div className="text-2xl font-heading font-extrabold text-emerald-700">{detail.kamar_terisi}</div>
                <div className="text-xs text-slate-500">Terisi</div>
              </div>
              <div className="text-center bg-slate-50 rounded-xl py-3">
                <div className="text-2xl font-heading font-extrabold text-slate-500">{detail.kamar_kosong}</div>
                <div className="text-xs text-slate-500">Kosong</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="kamar-grid">
            {detail.rooms.map((room) => (
              <button
                key={room.id}
                onClick={() => openRoom(room)}
                data-testid={`kamar-card-${room.nomor_kamar}`}
                className={`rounded-2xl border p-4 text-left transition-all duration-200 hover:-translate-y-1 hover:shadow-md ${
                  room.status === "terisi"
                    ? "bg-white border-emerald-200"
                    : "bg-slate-50 border-slate-200 border-dashed"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-400 font-semibold">KAMAR</span>
                  {room.status === "terisi" ? <Badge variant="success">Terisi</Badge> : <Badge variant="neutral">Kosong</Badge>}
                </div>
                <div className="font-heading font-extrabold text-2xl text-navy">{room.nomor_kamar}</div>
                {room.tenant ? (
                  <div className="text-xs text-slate-500 truncate mt-1">{room.tenant.nama}</div>
                ) : (
                  <div className="text-xs text-gold-dark font-semibold mt-1 flex items-center gap-1"><Plus size={12} /> Tambah penghuni</div>
                )}
              </button>
            ))}
          </div>
        </>
      )}

      {/* Add tenant to empty room */}
      <Modal open={!!addRoom} onClose={() => setAddRoom(null)} title="Tambah Penghuni" testid="add-tenant-modal">
        {addRoom && <AddTenantForm fixedRoom={addRoom} onDone={() => { setAddRoom(null); refresh(); }} />}
      </Modal>

      {/* Filled room detail */}
      <Modal open={!!viewTenant} onClose={() => setViewTenant(null)} title={`Detail Kamar ${viewTenant?.nomor_kamar || ""}`} testid="room-detail-modal">
        {viewTenant?.tenant && (
          <div>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-14 h-14 rounded-full bg-navy text-gold flex items-center justify-center font-heading font-bold text-xl">
                {viewTenant.tenant.nama?.[0]?.toUpperCase()}
              </div>
              <div>
                <div className="font-heading font-bold text-lg text-navy">{viewTenant.tenant.nama}</div>
                <div className="text-sm text-slate-500">{viewTenant.tenant.nomor_hp || "-"}</div>
              </div>
            </div>
            <dl className="space-y-3 text-sm">
              <Row label="Harga Sewa" value={formatRupiah(viewTenant.tenant.harga_sewa)} />
              <Row label="Lokasi" value={detail?.lokasi?.nama} />
              <Row label="Nomor Kamar" value={viewTenant.nomor_kamar} />
              <Row label="Status Pembayaran" value={
                viewTenant.tenant.status_pembayaran === "lunas"
                  ? <Badge variant="success">Lunas</Badge>
                  : <Badge variant="danger">Tunggakan</Badge>
              } />
            </dl>
            <button onClick={() => vacate(viewTenant)} className="w-full mt-6 py-3 rounded-xl bg-amber-500 text-white font-semibold hover:bg-amber-600 transition-colors duration-200 flex items-center justify-center gap-2" data-testid="kosongkan-kamar-btn">
              <DoorOpen size={18} /> Kosongkan Kamar
            </button>
            <div className="flex gap-3 mt-3">
              <button onClick={() => removeTenant(viewTenant.tenant.id, "archive")} className="flex-1 py-2.5 rounded-xl border border-slate-300 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition-colors duration-200 flex items-center justify-center gap-2" data-testid="arsip-penghuni-btn">
                <Archive size={16} /> Arsipkan
              </button>
              <button onClick={() => removeTenant(viewTenant.tenant.id, "delete")} className="flex-1 py-2.5 rounded-xl border border-rose-300 text-rose-600 text-sm font-semibold hover:bg-rose-50 transition-colors duration-200 flex items-center justify-center gap-2" data-testid="hapus-penghuni-btn">
                <Trash2 size={16} /> Hapus
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-100">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-semibold text-navy">{value}</dd>
    </div>
  );
}
