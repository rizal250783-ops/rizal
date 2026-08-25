import { jsPDF } from "jspdf";
import { formatRupiah, formatBulan, formatTanggal } from "./utils";

// Build the kwitansi PDF and return a jsPDF instance
function buildReceipt(payment, settings) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const W = 210;
  const navy = [10, 25, 47];
  const gold = [212, 175, 55];
  const green = [16, 122, 74];

  // Header background
  doc.setFillColor(...navy);
  doc.rect(0, 0, W, 34, "F");

  // Logo
  if (settings?.logo) {
    try {
      doc.addImage(settings.logo, "PNG", 14, 6, 22, 22);
    } catch (e) { /* ignore */ }
  }

  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text("ROSADAH KOST", 42, 16);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...gold);
  doc.text("Nyaman  •  Aman  •  Bersih", 42, 23);

  // Gold line
  doc.setDrawColor(...gold);
  doc.setLineWidth(1.2);
  doc.line(14, 38, W - 14, 38);

  // Title
  doc.setTextColor(...navy);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("KWITANSI PEMBAYARAN KOST", W / 2, 50, { align: "center" });

  // Receipt number
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(90, 90, 90);
  doc.text(`No. Kwitansi: ${payment.nomor_kwitansi || "-"}`, W / 2, 57, { align: "center" });

  // Detail rows
  const periodeStr = (payment.tanggal_bayar && payment.tanggal_jatuh_tempo)
    ? `${formatTanggal(payment.tanggal_bayar)} s.d ${formatTanggal(payment.tanggal_jatuh_tempo)}`
    : formatBulan(payment.bulan);
  const rows = [
    ["Nama Penghuni", payment.nama],
    ["Lokasi Kost", payment.lokasi],
    ["Alamat Kost", payment.alamat],
    ["Nomor Kamar", payment.nomor_kamar],
    ["Periode Pembayaran", periodeStr],
    ["Tanggal Bayar", formatTanggal(payment.tanggal_bayar)],
  ];
  let y = 72;
  doc.setFontSize(11);
  rows.forEach(([label, val]) => {
    doc.setTextColor(110, 110, 110);
    doc.setFont("helvetica", "normal");
    doc.text(label, 18, y);
    doc.setTextColor(...navy);
    doc.setFont("helvetica", "bold");
    doc.text(":", 70, y);
    doc.text(String(val || "-"), 74, y);
    y += 10;
  });

  // Amount box
  y += 2;
  doc.setFillColor(245, 247, 250);
  doc.roundedRect(18, y, W - 36, 20, 2, 2, "F");
  doc.setTextColor(110, 110, 110);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.text("Jumlah Dibayar", 24, y + 8);
  doc.setTextColor(...navy);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text(formatRupiah(payment.jumlah), W - 24, y + 13, { align: "right" });

  // LUNAS stamp
  doc.saveGraphicsState();
  doc.setDrawColor(...green);
  doc.setTextColor(...green);
  doc.setLineWidth(1.5);
  const sx = 60, sy = y + 55;
  doc.roundedRect(sx, sy - 14, 90, 24, 3, 3, "S");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(34);
  doc.text("LUNAS", sx + 45, sy + 3, { align: "center", angle: 8 });
  doc.restoreGraphicsState();

  // Signature
  doc.setTextColor(...navy);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  const sigY = y + 95;
  doc.text("Hormat kami,", W - 55, sigY, { align: "center" });
  doc.setFont("helvetica", "bold");
  doc.text("ROSADAH KOST", W - 55, sigY + 22, { align: "center" });
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.3);
  doc.line(W - 80, sigY + 24, W - 30, sigY + 24);

  return doc;
}

export function downloadReceiptPDF(payment, settings) {
  const doc = buildReceipt(payment, settings);
  doc.save(`kwitansi-${payment.nomor_kwitansi || "rosadah"}.pdf`);
}

export async function shareReceiptPDF(payment, settings) {
  const doc = buildReceipt(payment, settings);
  const blob = doc.output("blob");
  const file = new File([blob], `kwitansi-${payment.nomor_kwitansi || "rosadah"}.pdf`, {
    type: "application/pdf",
  });
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({
        files: [file],
        title: "Kwitansi ROSADAH KOST",
        text: `Kwitansi pembayaran ${payment.nama}`,
      });
      return true;
    } catch (e) {
      return false;
    }
  }
  // fallback: download
  doc.save(`kwitansi-${payment.nomor_kwitansi || "rosadah"}.pdf`);
  return false;
}
