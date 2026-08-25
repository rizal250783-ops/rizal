import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "../api";
import { Field, inputClass } from "./ui";
import { formatRupiah, maskDate, ddmmyyyyToISO } from "../utils";

export default function AddTenantForm({ fixedRoom, onDone }) {
  const [locations, setLocations] = useState([]);
  const [locationId, setLocationId] = useState("");
  const [rooms, setRooms] = useState([]);
  const [roomId, setRoomId] = useState(fixedRoom?.id || "");
  const [nama, setNama] = useState("");
  const [nomorHp, setNomorHp] = useState("");
  const [harga, setHarga] = useState("");
  const [jatuhTempo, setJatuhTempo] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (fixedRoom) return;
    api.get("/locations").then((r) => setLocations(r.data)).catch(() => {});
  }, [fixedRoom]);

  useEffect(() => {
    if (fixedRoom || !locationId) return;
    setRoomId("");
    api.get(`/locations/${locationId}/rooms`).then((r) => {
      setRooms(r.data.rooms.filter((x) => x.status === "kosong"));
    }).catch(() => {});
  }, [locationId, fixedRoom]);

  const submit = async (e) => {
    e.preventDefault();
    if (!roomId) { toast.error("Pilih kamar terlebih dahulu"); return; }
    if (!nama.trim()) { toast.error("Nama penghuni wajib diisi"); return; }
    let isoJatuhTempo = "";
    if (jatuhTempo) {
      isoJatuhTempo = ddmmyyyyToISO(jatuhTempo);
      if (!isoJatuhTempo) { toast.error("Tanggal jatuh tempo harus format dd/mm/yyyy"); return; }
    }
    setSaving(true);
    try {
      await api.post("/tenants", {
        room_id: roomId,
        nama: nama.trim(),
        nomor_hp: nomorHp.trim(),
        harga_sewa: Number(harga) || 0,
        tanggal_jatuh_tempo: isoJatuhTempo,
      });
      toast.success("Penghuni berhasil ditambahkan");
      onDone?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal menambah penghuni");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} data-testid="add-tenant-form">
      {fixedRoom ? (
        <div className="mb-4 px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm text-navy">
          Kamar <span className="font-bold">No. {fixedRoom.nomor_kamar}</span> — {fixedRoom.lokasi}
        </div>
      ) : (
        <>
          <Field label="Lokasi Kost">
            <select className={inputClass} value={locationId} onChange={(e) => setLocationId(e.target.value)} data-testid="tenant-location-select">
              <option value="">Pilih lokasi</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>{l.nama} ({l.kamar_kosong} kosong)</option>
              ))}
            </select>
          </Field>
          <Field label="Kamar Kosong">
            <select className={inputClass} value={roomId} onChange={(e) => setRoomId(e.target.value)} disabled={!locationId} data-testid="tenant-room-select">
              <option value="">{locationId ? "Pilih kamar" : "Pilih lokasi dulu"}</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>Kamar No. {r.nomor_kamar}</option>
              ))}
            </select>
          </Field>
        </>
      )}
      <Field label="Nama Penghuni">
        <input className={inputClass} value={nama} onChange={(e) => setNama(e.target.value)} placeholder="Nama lengkap" data-testid="tenant-nama-input" />
      </Field>
      <Field label="Nomor WhatsApp / Telepon">
        <input className={inputClass} value={nomorHp} onChange={(e) => setNomorHp(e.target.value)} placeholder="08xxxxxxxxxx" data-testid="tenant-hp-input" />
      </Field>
      <Field label="Harga Sewa per Bulan">
        <input type="number" className={inputClass} value={harga} onChange={(e) => setHarga(e.target.value)} placeholder="0" data-testid="tenant-harga-input" />
        {harga ? <span className="text-xs text-gold-dark font-semibold mt-1 block">{formatRupiah(harga)}</span> : null}
      </Field>
      <Field label="Tanggal Jatuh Tempo Bulan Berikutnya">
        <input type="text" inputMode="numeric" className={inputClass} value={jatuhTempo} onChange={(e) => setJatuhTempo(maskDate(e.target.value))} placeholder="dd/mm/yyyy" maxLength={10} data-testid="tenant-jatuhtempo-input" />
      </Field>
      <button type="submit" disabled={saving} className="w-full py-3 rounded-xl bg-navy text-white font-semibold hover:bg-navy-light disabled:opacity-60 transition-colors duration-200 active:scale-95" data-testid="tenant-save-btn">
        {saving ? "Menyimpan..." : "Simpan Penghuni"}
      </button>
    </form>
  );
}
