export const LOGO = "https://customer-assets-eiarnc6j.emergentagent.net/job_cdbb0a0e-bca9-4af7-824e-9ab49c408de5/artifacts/uxgzo9e5_Logo%20BPRS%20Haji%20Miskin.png";

export const ROLE_LABEL = {
  direktur: "Direktur",
  admin: "Admin",
  ao_lending: "AO Lending",
  ao_funding: "AO Funding",
  pic_remedial: "PIC Remedial",
};

export function fmtRp(n) {
  if (n == null || isNaN(n)) return "Rp 0";
  return "Rp " + Math.round(n).toLocaleString("id-ID");
}

export function fmtShort(n) {
  if (n == null || isNaN(n)) return "-";
  const abs = Math.abs(n);
  if (abs >= 1e9) return "Rp " + (n / 1e9).toFixed(2).replace(".", ",") + " M";
  if (abs >= 1e6) return "Rp " + (n / 1e6).toFixed(0) + " jt";
  return fmtRp(n);
}

export function pct(v) {
  if (v == null) return "N/A";
  return v.toFixed(1).replace(".", ",") + "%";
}

export function statusColor(status) {
  const map = {
    Excellent: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Good: "bg-blue-50 text-blue-700 border-blue-200",
    "Need Attention": "bg-gold-100 text-gold-800 border-amber-200",
    Critical: "bg-red-50 text-red-700 border-red-200",
    "N/A": "bg-slate-100 text-slate-500 border-slate-200",
    Sehat: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Perhatian: "bg-gold-100 text-gold-800 border-amber-200",
  };
  return map[status] || "bg-slate-100 text-slate-600 border-slate-200";
}

export const KOLEK = {
  1: { label: "Lancar", color: "#059669", bg: "#ECFDF5", text: "text-emerald-700" },
  2: { label: "DPK", color: "#D97706", bg: "#FEF3C7", text: "text-gold-800" },
  3: { label: "Kurang Lancar", color: "#EA580C", bg: "#FFEDD5", text: "text-orange-700" },
  4: { label: "Diragukan", color: "#DC2626", bg: "#FEE2E2", text: "text-red-700" },
  5: { label: "Macet", color: "#991B1B", bg: "#FEF2F2", text: "text-red-900" },
};

export function currentPeriod() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function periodLabel(p) {
  if (!p) return "";
  const [y, m] = p.split("-");
  const names = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
  return `${names[parseInt(m) - 1]} ${y}`;
}
