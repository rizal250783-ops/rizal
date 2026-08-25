import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Wallet, BedDouble, DoorOpen, AlertTriangle, UserX, PieChart, TrendingUp, CalendarPlus } from "lucide-react";
import { toast } from "sonner";
import api from "../api";
import { formatRupiah, formatBulan, downloadAllICS } from "../utils";

function StatCard({ icon: Icon, label, value, sub, tint, testid }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-5 flex flex-col justify-between fade-up" data-testid={testid}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</span>
        <span className={`w-9 h-9 rounded-xl flex items-center justify-center ${tint}`}><Icon size={18} /></span>
      </div>
      <div className="text-2xl font-heading font-extrabold text-navy">{value}</div>
      {sub ? <div className="text-xs text-slate-400 mt-1">{sub}</div> : null}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  const load = () => api.get("/dashboard").then((r) => setData(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const exportCalendar = async () => {
    const tid = toast.loading("Menyiapkan file kalender...");
    try {
      const res = await api.get("/tenants");
      const tenants = (res.data || []).filter((t) => t.tanggal_jatuh_tempo);
      if (tenants.length === 0) {
        toast.error("Belum ada penghuni dengan tanggal jatuh tempo.", { id: tid });
        return;
      }
      const count = downloadAllICS(tenants);
      if (count > 0) {
        toast.success(`File kalender ${count} penghuni diunduh. Buka file-nya di HP lalu simpan ke Google Calendar.`, { id: tid, duration: 6000 });
      } else {
        toast.error("Tidak ada jatuh tempo yang bisa diekspor.", { id: tid });
      }
    } catch (e) {
      toast.error("Gagal membuat file kalender", { id: tid });
    }
  };

  if (!data) return <div className="page-container text-slate-500">Memuat...</div>;

  return (
    <div className="page-container">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-heading font-extrabold text-navy">Beranda</h1>
          <p className="text-slate-500">Ringkasan periode {formatBulan(data.periode)}</p>
        </div>
        <button
          onClick={exportCalendar}
          data-testid="export-calendar-btn"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-navy text-white hover:bg-navy-light transition-colors duration-200 self-start sm:self-auto"
          title="Unduh file kalender berisi jatuh tempo semua penghuni (pengingat bulanan otomatis di HP)"
        >
          <CalendarPlus size={17} /> Ekspor Kalender
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-5">
        {/* Hero */}
        <div className="md:col-span-3 lg:col-span-2 bg-navy rounded-2xl p-7 text-white relative overflow-hidden fade-up" data-testid="hero-pemasukan-card">
          <div className="absolute -right-8 -top-8 w-40 h-40 rounded-full bg-gold/10" />
          <div className="absolute right-6 bottom-6 text-gold/20"><TrendingUp size={90} /></div>
          <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gold mb-3">
            <Wallet size={16} /> Total Pemasukan Bulan Ini
          </span>
          <div className="text-4xl lg:text-5xl font-heading font-extrabold" data-testid="total-pemasukan-value">
            {formatRupiah(data.total_pemasukan_bulan_ini)}
          </div>
          <p className="text-slate-300 text-sm mt-2">Dari pembayaran berstatus Lunas periode {formatBulan(data.periode)}</p>
        </div>

        <StatCard testid="stat-kamar-terisi" icon={BedDouble} label="Kamar Terisi" tint="bg-emerald-100 text-emerald-700"
          value={`${data.kamar_terisi} / ${data.kamar_total}`} sub="Kamar dihuni" />
        <StatCard testid="stat-kamar-kosong" icon={DoorOpen} label="Kamar Kosong" tint="bg-slate-100 text-slate-600"
          value={data.kamar_kosong} sub="Tersedia" />
        <StatCard testid="stat-tunggakan" icon={AlertTriangle} label="Total Tunggakan" tint="bg-rose-100 text-rose-700"
          value={formatRupiah(data.total_tunggakan)} sub="Belum lunas" />
        <StatCard testid="stat-belum-bayar" icon={UserX} label="Belum Bayar" tint="bg-amber-100 text-amber-700"
          value={`${data.jumlah_penghuni_belum_bayar} orang`} sub="Penghuni menunggak" />
        <StatCard testid="stat-hunian" icon={PieChart} label="Persentase Hunian" tint="bg-gold/15 text-gold-dark"
          value={`${data.persentase_hunian}%`} sub="Tingkat okupansi" />
      </div>

      {/* Perlu Perhatian */}
      <div className="mt-8 bg-white rounded-2xl border border-slate-200 shadow-card overflow-hidden" data-testid="perlu-perhatian-section">
        <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-100">
          <AlertTriangle size={18} className="text-rose-500" />
          <h2 className="font-heading font-bold text-navy text-lg">Perlu Perhatian</h2>
          <span className="ml-auto text-sm text-slate-500">{data.perlu_perhatian.length} penghuni menunggak</span>
        </div>
        {data.perlu_perhatian.length === 0 ? (
          <div className="px-6 py-10 text-center text-slate-400" data-testid="perlu-perhatian-empty">
            Tidak ada tunggakan pada periode ini.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {data.perlu_perhatian.map((p) => (
              <div key={p.tenant_id + p.bulan} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 transition-colors duration-200" data-testid={`perhatian-row-${p.tenant_id}`}>
                <div className="w-11 h-11 rounded-full bg-navy text-gold flex items-center justify-center font-bold flex-shrink-0">
                  {p.nama?.[0]?.toUpperCase() || "?"}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-navy truncate">{p.nama}</div>
                  <div className="text-sm text-slate-500 truncate">Kamar {p.nomor_kamar} • {p.lokasi}</div>
                </div>
                <div className="text-right">
                  <div className="font-heading font-bold text-rose-600">{formatRupiah(p.jumlah)}</div>
                  <div className="text-xs text-slate-400">Tunggakan</div>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="px-6 py-4 border-t border-slate-100">
          <button onClick={() => navigate("/pembayaran")} className="text-sm font-semibold text-gold-dark hover:underline" data-testid="goto-pembayaran-btn">
            Kelola Pembayaran →
          </button>
        </div>
      </div>
    </div>
  );
}
