import React, { useEffect, useState, useCallback } from "react";
import { CheckCircle2, XCircle, FileDown, Share2, Send, CalendarPlus, Mail } from "lucide-react";
import { toast } from "sonner";
import api from "../api";
import { useSettings } from "../App";
import { Badge } from "../components/ui";
import { formatRupiah, formatBulan, waLink, downloadICS } from "../utils";
import { downloadReceiptPDF, shareReceiptPDF } from "../pdf";

const FILTERS = [
  { key: "semua", label: "Semua" },
  { key: "lunas", label: "Lunas" },
  { key: "tunggakan", label: "Tunggakan" },
];

export default function Pembayaran() {
  const { settings } = useSettings();
  const [data, setData] = useState({ payments: [], total_lunas: 0, total_tunggakan: 0 });
  const [filter, setFilter] = useState("semua");

  const load = useCallback(() => {
    api.get("/payments").then((r) => setData(r.data)).catch(() => {});
  }, []);
  useEffect(() => { load(); }, [load]);

  const toggle = async (p) => {
    try {
      await api.post(`/payments/${p.id}/toggle`);
      load();
    } catch (e) { toast.error("Gagal mengubah status"); }
  };

  const share = async (p) => {
    const ok = await shareReceiptPDF(p, settings);
    if (!ok) toast.info("Kwitansi diunduh (berbagi tidak didukung perangkat ini)");
  };

  const sendReminder = async (p) => {
    const tid = toast.loading("Mengirim email pengingat...");
    try {
      const res = await api.post("/reminders/send", null, { params: { payment_id: p.id } });
      toast.success(`Email pengingat terkirim ke ${res.data.tujuan}`, { id: tid });
    } catch (e) {
      toast.error(e.response?.data?.detail || "Gagal mengirim email", { id: tid });
    }
  };

  const ownerWa = settings?.owner_whatsapp || "6281313841255";
  const shown = data.payments.filter((p) => filter === "semua" || p.status === filter);

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="text-3xl font-heading font-extrabold text-navy">Pembayaran</h1>
        <p className="text-slate-500">Kelola status pembayaran & kwitansi</p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5" data-testid="summary-lunas">
          <div className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1">Total Lunas</div>
          <div className="text-2xl font-heading font-extrabold text-emerald-800">{formatRupiah(data.total_lunas)}</div>
        </div>
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5" data-testid="summary-tunggakan">
          <div className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-1">Total Tunggakan</div>
          <div className="text-2xl font-heading font-extrabold text-rose-800">{formatRupiah(data.total_tunggakan)}</div>
        </div>
      </div>

      <div className="flex gap-2 mb-5">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            data-testid={`filter-${f.key}`}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-colors duration-200 ${
              filter === f.key ? "bg-navy text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {shown.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400" data-testid="pembayaran-empty">
          Tidak ada data pembayaran.
        </div>
      ) : (
        <div className="space-y-3" data-testid="pembayaran-list">
          {shown.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl border border-slate-200 shadow-card p-5 fade-up" data-testid={`pembayaran-card-${p.id}`}>
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-full bg-navy text-gold flex items-center justify-center font-bold flex-shrink-0">
                  {p.nama?.[0]?.toUpperCase() || "?"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-heading font-bold text-navy">{p.nama}</span>
                    {p.status === "lunas" ? <Badge variant="success" testid={`badge-${p.id}`}>Lunas</Badge> : <Badge variant="danger" testid={`badge-${p.id}`}>Tunggakan</Badge>}
                  </div>
                  <div className="text-sm text-slate-500">Kamar {p.nomor_kamar} • {p.lokasi}</div>
                  <div className="text-sm text-slate-400">Periode {formatBulan(p.bulan)}</div>
                </div>
                <div className="text-right">
                  <div className="font-heading font-extrabold text-navy">{formatRupiah(p.jumlah)}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-100">
                <button
                  onClick={() => toggle(p)}
                  data-testid={`toggle-btn-${p.id}`}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-colors duration-200 ${
                    p.status === "lunas"
                      ? "bg-rose-50 text-rose-600 hover:bg-rose-100"
                      : "bg-emerald-500 text-white hover:bg-emerald-600"
                  }`}
                >
                  {p.status === "lunas" ? <><XCircle size={16} /> Batalkan Lunas</> : <><CheckCircle2 size={16} /> Tandai Lunas</>}
                </button>

                {p.status === "tunggakan" && (
                  <button onClick={() => sendReminder(p)} className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors duration-200" data-testid={`email-reminder-btn-${p.id}`}>
                    <Mail size={16} /> Email Pengingat
                  </button>
                )}

                {p.status === "lunas" && (
                  <>
                    <button onClick={() => downloadReceiptPDF(p, settings)} className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-navy text-white hover:bg-navy-light transition-colors duration-200" data-testid={`kwitansi-btn-${p.id}`}>
                      <FileDown size={16} /> Kwitansi
                    </button>
                    <button onClick={() => share(p)} className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors duration-200" data-testid={`share-btn-${p.id}`}>
                      <Share2 size={16} /> Bagikan
                    </button>
                    <a href={waLink(ownerWa, { nama: p.nama, kamar: p.nomor_kamar, bulan: p.bulan, jumlah: p.jumlah })} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-[#25D366] text-white hover:opacity-90 transition-opacity duration-200" data-testid={`wa-btn-${p.id}`}>
                      <Send size={16} /> WhatsApp
                    </a>
                  </>
                )}

                <button
                  onClick={() => downloadICS({ nama: p.nama, lokasi: p.lokasi, kamar: p.nomor_kamar, jumlah: p.jumlah, tanggal: null, ownerEmail: settings?.owner_email })}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors duration-200"
                  data-testid={`ics-btn-${p.id}`}
                >
                  <CalendarPlus size={16} /> Kalender
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
