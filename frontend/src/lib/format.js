export function formatRupiah(v) {
  const n = Number(v || 0);
  return "Rp" + Math.round(n).toLocaleString("id-ID");
}

export function formatRupiahShort(v) {
  const n = Number(v || 0);
  if (n >= 1e12) return "Rp" + (n / 1e12).toFixed(2) + " T";
  if (n >= 1e9) return "Rp" + (n / 1e9).toFixed(2) + " M";
  if (n >= 1e6) return "Rp" + (n / 1e6).toFixed(1) + " Jt";
  return formatRupiah(n);
}

export function parseNumber(str) {
  if (typeof str === "number") return str;
  const cleaned = String(str || "").replace(/[^\d]/g, "");
  return cleaned ? Number(cleaned) : 0;
}

export function formatNumberInput(v) {
  const n = parseNumber(v);
  return n ? n.toLocaleString("id-ID") : "";
}

export function todayDDMMYYYY() {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

export const STATUS_COLORS = {
  "Draft": "bg-slate-100 text-slate-600 border-slate-300",
  "Final Approved": "bg-emerald-50 text-emerald-600 border-emerald-300",
};

export function statusColor(status) {
  if (!status) return "bg-slate-100 text-slate-600 border-slate-300";
  if (status === "Final Approved") return "bg-emerald-50 text-emerald-700 border-emerald-300";
  if (status === "Draft") return "bg-slate-100 text-slate-600 border-slate-300";
  if (status.startsWith("Menunggu")) return "bg-[#FDF7EB] text-[#B4842A] border-[#F0B43C]";
  if (status.startsWith("Revisi")) return "bg-amber-50 text-amber-700 border-amber-300";
  if (status.startsWith("Reject")) return "bg-red-50 text-red-600 border-red-300";
  if (status.startsWith("Memerlukan")) return "bg-red-50 text-red-700 border-red-400";
  return "bg-slate-100 text-slate-600 border-slate-300";
}
