const BULAN_ID = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];

export function formatRupiah(value) {
  const n = Number(value || 0);
  return "Rp" + n.toLocaleString("id-ID");
}

export function formatBulan(str) {
  if (!str) return "-";
  const [y, m] = str.split("-");
  const idx = parseInt(m, 10) - 1;
  return `${BULAN_ID[idx] || m} ${y}`;
}

export function formatTanggal(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return `${d.getDate()} ${BULAN_ID[d.getMonth()]} ${d.getFullYear()}`;
}

export function initials(nama) {
  if (!nama) return "?";
  const parts = nama.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Mask raw input into dd/mm/yyyy as the user types
export function maskDate(value) {
  const digits = String(value).replace(/\D/g, "").slice(0, 8);
  const parts = [];
  if (digits.length >= 2) {
    parts.push(digits.slice(0, 2));
    if (digits.length >= 4) {
      parts.push(digits.slice(2, 4));
      if (digits.length > 4) parts.push(digits.slice(4, 8));
    } else {
      parts.push(digits.slice(2));
    }
  } else {
    parts.push(digits);
  }
  return parts.join("/");
}

// "dd/mm/yyyy" -> "yyyy-mm-dd" (ISO); returns "" if incomplete/invalid
export function ddmmyyyyToISO(str) {
  const m = String(str).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return "";
  const [, dd, mm, yyyy] = m;
  const d = new Date(`${yyyy}-${mm}-${dd}T00:00:00`);
  if (isNaN(d.getTime()) || d.getDate() !== Number(dd) || d.getMonth() + 1 !== Number(mm)) return "";
  return `${yyyy}-${mm}-${dd}`;
}

// "yyyy-mm-dd" (or ISO) -> "dd/mm/yyyy"
export function isoToDdmmyyyy(iso) {
  if (!iso) return "";
  const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return "";
  const [, yyyy, mm, dd] = m;
  return `${dd}/${mm}/${yyyy}`;
}

// WhatsApp link to owner number
export function waLink(ownerNumber, { nama, kamar, bulan, jumlah }) {
  const pesan = `Pembayaran kost ROSADAH KOST telah diterima.

Nama:
${nama}

Kamar:
${kamar}

Periode:
${formatBulan(bulan)}

Jumlah:
${formatRupiah(jumlah)}

Status:
LUNAS

Terima kasih.`;
  return `https://wa.me/${ownerNumber}?text=${encodeURIComponent(pesan)}`;
}

const _pad = (x) => String(x).padStart(2, "0");

// Escape special chars per RFC 5545 for text values
function _icsEscape(text) {
  return String(text || "")
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\n/g, "\\n");
}

// Build a single VEVENT block for a rent due date.
// Timed event 09:00 (floating local time = HP owner timezone), recurring MONTHLY,
// with two alarms: H-1 (09:00 hari sebelumnya) & tepat di hari jatuh tempo.
function _buildVevent({ nama, lokasi, kamar, jumlah, tanggal, index = 0 }) {
  const dt = tanggal ? new Date(`${String(tanggal).slice(0, 10)}T09:00:00`) : new Date();
  if (isNaN(dt.getTime())) return "";
  const y = dt.getFullYear();
  const m = _pad(dt.getMonth() + 1);
  const d = _pad(dt.getDate());
  const dtStart = `${y}${m}${d}T090000`;
  const dtEnd = `${y}${m}${d}T093000`;
  const stamp = new Date();
  const dtstamp = `${stamp.getUTCFullYear()}${_pad(stamp.getUTCMonth() + 1)}${_pad(stamp.getUTCDate())}T${_pad(stamp.getUTCHours())}${_pad(stamp.getUTCMinutes())}${_pad(stamp.getUTCSeconds())}Z`;
  const uid = `rosadah-${y}${m}${d}-${index}-${Math.random().toString(36).slice(2, 8)}@rosadahkost`;
  const desc = `Penghuni: ${nama}\\nLokasi: ${lokasi || "-"}\\nKamar: ${kamar || "-"}\\nSewa: Rp${Number(jumlah || 0).toLocaleString("id-ID")}\\n\\nPengingat pembayaran sewa kost ROSADAH KOST.`;
  return [
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART:${dtStart}`,
    `DTEND:${dtEnd}`,
    "RRULE:FREQ=MONTHLY",
    `SUMMARY:${_icsEscape(`Jatuh Tempo Sewa - ${nama} (Kamar ${kamar || "-"})`)}`,
    `DESCRIPTION:${desc}`,
    `LOCATION:${_icsEscape(lokasi || "")}`,
    "BEGIN:VALARM",
    "TRIGGER:-P1D",
    "ACTION:DISPLAY",
    `DESCRIPTION:${_icsEscape(`Besok jatuh tempo sewa - ${nama}`)}`,
    "END:VALARM",
    "BEGIN:VALARM",
    "TRIGGER:PT0S",
    "ACTION:DISPLAY",
    `DESCRIPTION:${_icsEscape(`Hari ini jatuh tempo sewa - ${nama}`)}`,
    "END:VALARM",
    "END:VEVENT",
  ].join("\r\n");
}

function _downloadIcsFile(veventBlocks, filename) {
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//ROSADAH KOST//Manajemen Kost//ID",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    ...veventBlocks,
    "END:VCALENDAR",
  ].join("\r\n");
  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Generate & download an .ics calendar file for ONE tenant's due date (monthly recurring).
export function downloadICS({ nama, lokasi, kamar, jumlah, tanggal }) {
  const vevent = _buildVevent({ nama, lokasi, kamar, jumlah, tanggal, index: 0 });
  if (!vevent) return false;
  const safe = String(nama || "penghuni").replace(/\s+/g, "-").toLowerCase();
  _downloadIcsFile([vevent], `jatuh-tempo-${safe}.ics`);
  return true;
}

// Generate & download ONE .ics containing due-date reminders for ALL tenants.
// `items` = array of { nama, lokasi, nomor_kamar, harga_sewa, tanggal_jatuh_tempo }
// Returns the number of events written (0 if none have a valid due date).
export function downloadAllICS(items) {
  const list = Array.isArray(items) ? items : [];
  const blocks = [];
  list.forEach((it, i) => {
    const tanggal = it.tanggal_jatuh_tempo || it.tanggal;
    if (!tanggal) return;
    const vevent = _buildVevent({
      nama: it.nama,
      lokasi: it.lokasi,
      kamar: it.nomor_kamar || it.kamar,
      jumlah: it.harga_sewa != null ? it.harga_sewa : it.jumlah,
      tanggal,
      index: i,
    });
    if (vevent) blocks.push(vevent);
  });
  if (blocks.length === 0) return 0;
  const stamp = new Date();
  const fname = `jatuh-tempo-kost-${stamp.getFullYear()}${_pad(stamp.getMonth() + 1)}${_pad(stamp.getDate())}.ics`;
  _downloadIcsFile(blocks, fname);
  return blocks.length;
}
