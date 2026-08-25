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

// Generate & download an .ics calendar file for a due date
export function downloadICS({ nama, lokasi, kamar, jumlah, tanggal, ownerEmail }) {
  const dt = tanggal ? new Date(tanggal) : new Date();
  const pad = (x) => String(x).padStart(2, "0");
  const dateStr = `${dt.getFullYear()}${pad(dt.getMonth() + 1)}${pad(dt.getDate())}`;
  const stamp = new Date();
  const dtstamp = `${stamp.getFullYear()}${pad(stamp.getMonth() + 1)}${pad(stamp.getDate())}T${pad(stamp.getHours())}${pad(stamp.getMinutes())}${pad(stamp.getSeconds())}`;
  const uid = `rosadah-${Date.now()}@rosadahkost`;
  const desc = `Penghuni: ${nama}\\nLokasi: ${lokasi}\\nKamar: ${kamar}\\nSewa: Rp${Number(jumlah || 0).toLocaleString("id-ID")}`;
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//ROSADAH KOST//ID",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART;VALUE=DATE:${dateStr}`,
    `SUMMARY:Jatuh Tempo Pembayaran Kost - ${nama}`,
    `DESCRIPTION:${desc}`,
    ownerEmail ? `ORGANIZER;CN=ROSADAH KOST:mailto:${ownerEmail}` : "",
    "BEGIN:VALARM",
    "TRIGGER:-P1D",
    "ACTION:DISPLAY",
    `DESCRIPTION:Pengingat jatuh tempo pembayaran kost - ${nama}`,
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ].filter(Boolean).join("\r\n");

  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `jatuh-tempo-${nama.replace(/\s+/g, "-").toLowerCase()}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
