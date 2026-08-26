import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { rp, fmtDate } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, CartesianGrid, Legend,
} from "recharts";
import { Scale, Banknote, MapPin, Building2, GitBranch, AlarmClock, CheckSquare } from "lucide-react";

const TAHAP = ["Gugatan", "Mediasi", "Jawaban", "Replik", "Duplik", "Pembuktian", "Putusan",
  "Banding", "Kasasi", "PK", "Inkracht", "Eksekusi", "Settlement"];

const TAHAP_MAP = {
  "Gugatan": ["Gugatan Terdaftar", "Pemanggilan Relaas"],
  "Mediasi": ["Mediasi"],
  "Jawaban": ["Jawaban Tergugat"],
  "Replik": ["Replik"],
  "Duplik": ["Duplik"],
  "Pembuktian": ["Pembuktian", "Kesimpulan"],
  "Putusan": ["Putusan", "Pemberitahuan Putusan"],
  "Banding": ["Banding", "Putusan Banding"],
  "Kasasi": ["Kasasi", "Putusan Kasasi"],
  "PK": ["Peninjauan Kembali"],
  "Inkracht": ["Inkracht"],
  "Eksekusi": ["Eksekusi Jaminan"],
  "Settlement": ["Settlement / Perdamaian"],
};

const PIE_COLORS = ["#00a0a0", "#f0b43c", "#64748b", "#10b981", "#ef4444", "#0ea5e9"];

function KpiCard({ icon: Icon, label, value, sub, testid }) {
  return (
    <div data-testid={testid} className="bg-white border border-slate-200 rounded-md p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500 font-medium">{label}</p>
        <div className="h-8 w-8 bg-toska-light rounded-md flex items-center justify-center">
          <Icon className="h-4 w-4 text-toska" />
        </div>
      </div>
      <p className="font-heading text-2xl font-bold text-slate-900 tracking-tight">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function Dashboard() {
  const { isDeptHead } = useAuth();
  const [stats, setStats] = useState(null);
  const [master, setMaster] = useState(null);
  const [filters, setFilters] = useState({ tahun: "all", region: "all", area: "all", cabang: "all", status: "all" });

  useEffect(() => {
    api.get("/master-data").then((r) => setMaster(r.data));
  }, []);

  const load = useCallback(() => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v !== "all") params[k] = v; });
    api.get("/dashboard/stats", { params }).then((r) => setStats(r.data));
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const setF = (k) => (v) => setFilters((f) => ({ ...f, [k]: v, ...(k === "region" ? { area: "all" } : {}) }));

  const areaOptions = filters.region !== "all" && master?.region_area_map?.[filters.region]
    ? master.region_area_map[filters.region]
    : [...new Set([...(master?.areas || []), ...Object.values(master?.region_area_map || {}).flat()])];

  const tahapCount = (t) => {
    if (!stats) return 0;
    const statuses = TAHAP_MAP[t] || [];
    return stats.per_status.filter((s) => statuses.includes(s.name)).reduce((a, b) => a + b.value, 0);
  };

  const FilterSelect = ({ k, label, options }) => (
    <Select value={filters[k]} onValueChange={setF(k)}>
      <SelectTrigger data-testid={`filter-${k}`} className="w-full md:w-44 bg-white">
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Semua {label}</SelectItem>
        {(options || []).filter(Boolean).map((o) => (
          <SelectItem key={o} value={String(o)}>{o}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  return (
    <div data-testid="dashboard-page" className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Dashboard Monitoring</h1>
          <p className="text-sm text-slate-500 mt-1">Monitoring perkara gugatan perdata — Retail Collection, Restructuring & Recovery Group (RCG)</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <FilterSelect k="tahun" label="Tahun" options={master?.tahun} />
          <FilterSelect k="region" label="Region" options={master?.regions} />
          <FilterSelect k="area" label="Area" options={areaOptions} />
          <FilterSelect k="cabang" label="Cabang" options={master?.cabangs} />
          <FilterSelect k="status" label="Status" options={master?.status_perkara} />
        </div>
      </div>

      {!stats ? (
        <p className="text-sm text-slate-500">Memuat data...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <KpiCard icon={Scale} label="Perkara Aktif" value={stats.total_aktif} sub={`dari ${stats.total_perkara} total perkara`} testid="kpi-perkara-aktif" />
            <KpiCard icon={Banknote} label="Total Nilai Kewajiban" value={rp(stats.total_kewajiban)} sub="Perkara aktif" testid="kpi-total-kewajiban" />
            <KpiCard icon={MapPin} label="Region" value={stats.per_region.length} sub={`${stats.per_area.length} Area • ${stats.per_cabang.length} Cabang`} testid="kpi-region" />
            {isDeptHead ? (
              <Link to="/approval" data-testid="kpi-pending-approval">
                <div className="bg-gold-light border border-gold rounded-md p-5 h-full hover:bg-gold/10 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs uppercase tracking-widest text-slate-600 font-medium">Menunggu Approval</p>
                    <CheckSquare className="h-4 w-4 text-gold-hover" />
                  </div>
                  <p className="font-heading text-2xl font-bold text-slate-900">{stats.pending_approvals}</p>
                  <p className="text-xs text-slate-600 mt-1">Klik untuk review</p>
                </div>
              </Link>
            ) : (
              <KpiCard icon={CheckSquare} label="Menunggu Approval" value={stats.pending_approvals} sub="Request dalam antrian" testid="kpi-pending-approval" />
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-md p-5">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-4">Perkara Berdasarkan Tahap Proses</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {TAHAP.map((t) => (
                <div key={t} data-testid={`tahap-${t.toLowerCase()}`} className="border border-slate-200 rounded-md p-3 text-center">
                  <p className="font-heading text-xl font-bold text-toska">{tahapCount(t)}</p>
                  <p className="text-xs text-slate-500 mt-1">{t}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-md p-5">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-4">Jumlah Perkara per Region</p>
              <div className="h-72">
                <ResponsiveContainer>
                  <BarChart data={stats.per_region} layout="vertical" margin={{ left: 20, right: 20 }}>
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#00a0a0" radius={[0, 4, 4, 0]} name="Perkara" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-md p-5">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-4">Status Perkara</p>
              <div className="h-72">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={stats.per_status} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85} paddingAngle={2}>
                      {stats.per_status.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-md p-5">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-4">Perjalanan Perkara (Registrasi per Bulan)</p>
              <div className="h-64">
                <ResponsiveContainer>
                  <AreaChart data={stats.timeline_chart} margin={{ left: 0, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Area type="monotone" dataKey="value" stroke="#00a0a0" fill="#00a0a0" fillOpacity={0.15} name="Perkara" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-gold-light border border-gold/60 rounded-md p-5">
              <div className="flex items-center gap-2 mb-4">
                <AlarmClock className="h-4 w-4 text-gold-hover" />
                <p className="text-xs uppercase tracking-widest text-slate-600 font-medium">Reminder & Tenggat</p>
              </div>
              <div className="space-y-3 max-h-64 overflow-y-auto" data-testid="reminder-list">
                {stats.reminders.length === 0 && (
                  <p className="text-sm text-slate-500">Tidak ada tenggat dalam 60 hari ke depan.</p>
                )}
                {stats.reminders.map((r, i) => (
                  <Link to={`/perkara/${r.case_id}`} key={i} className="block bg-white border border-gold/50 rounded-md p-3 hover:border-gold transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-900">{r.agenda}</p>
                      <Badge variant={r.hari < 0 ? "destructive" : r.hari <= 7 ? "default" : "secondary"}
                        className={r.hari >= 0 && r.hari <= 7 ? "bg-gold text-slate-900 hover:bg-gold" : ""}>
                        {r.hari < 0 ? `Terlewat ${-r.hari} hari` : `${r.hari} hari lagi`}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{r.nomor_perkara}</p>
                    <p className="text-xs text-slate-400">{fmtDate(r.tanggal)}</p>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
