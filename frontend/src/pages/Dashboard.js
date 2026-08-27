import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatRupiahShort, formatRupiah, statusColor } from "../lib/format";
import {
  LayoutDashboard, FileText, FileClock, RotateCcw, CheckCircle2, ShieldAlert, Layers, Loader2
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid, Legend
} from "recharts";

const COLORS = ["#00A0A0", "#F0B43C", "#0F766E", "#EAB308", "#14B8A6", "#F59E0B"];

function Stat({ icon: Icon, label, value, tone = "teal", testid }) {
  const tones = {
    teal: "bg-[#E6F6F6] text-[#00A0A0]",
    gold: "bg-[#FDF7EB] text-[#B4842A]",
    slate: "bg-slate-100 text-slate-600",
    green: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-600",
  };
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5" data-testid={testid}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${tones[tone]}`}><Icon size={18} /></div>
      </div>
      <div className="mt-3 font-display font-bold text-2xl text-slate-900">{value}</div>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
      <h3 className="font-display font-semibold text-slate-800 mb-4">{title}</h3>
      <div style={{ height: 280 }}>{children}</div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => { api.get("/dashboard").then((r) => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  const s = data.summary;
  const c = data.cards;

  return (
    <div>
      <PageHeader title={`Dashboard ${user.role}`} subtitle={`Selamat datang, ${user.nama}`} icon={LayoutDashboard} />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-4">
        <Stat icon={FileText} label="Total Nota" value={s.total_nota} testid="stat-total-nota" />
        <Stat icon={Layers} label="Total Loan" value={s.total_loan} tone="gold" testid="stat-total-loan" />
        <Stat icon={FileClock} label="Menunggu" value={c.menunggu} tone="gold" testid="stat-menunggu" />
        <Stat icon={RotateCcw} label="Revisi / Reject" value={c.revisi_reject} tone="red" testid="stat-revisi" />
        {user.role === "RCO" && <Stat icon={FileText} label="Draft" value={c.draft} tone="slate" testid="stat-draft" />}
        <Stat icon={CheckCircle2} label="Final Approved" value={c.approved} tone="green" testid="stat-approved" />
        {c.eskalasi > 0 && <Stat icon={ShieldAlert} label="Eskalasi > RCG" value={c.eskalasi} tone="red" testid="stat-eskalasi" />}
      </div>

      {user.role !== "RCO" && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Stat icon={FileText} label="Total OS Pokok" value={formatRupiahShort(s.total_os_pokok)} testid="stat-os-pokok" />
          <Stat icon={FileText} label="Total OS Margin" value={formatRupiahShort(s.total_os_margin)} tone="gold" testid="stat-os-margin" />
          <Stat icon={FileText} label="Total Penalty" value={formatRupiahShort(s.total_penalty)} tone="slate" testid="stat-penalty" />
          <Stat icon={FileText} label="Total Kewajiban" value={formatRupiahShort(s.total_kewajiban)} tone="teal" testid="stat-kewajiban" />
        </div>
      )}

      {/* Ringkasan Status - klik untuk lihat daftar nota */}
      {data.by_status && Object.keys(data.by_status).length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 mb-6" data-testid="status-summary">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-display font-semibold text-slate-800">Ringkasan Status Nota</h3>
            <button onClick={() => navigate("/notes")} className="text-xs font-semibold text-[#00A0A0] hover:underline" data-testid="view-all-notes">
              Lihat semua nota &rarr;
            </button>
          </div>
          <div className="flex flex-wrap gap-2.5">
            {Object.entries(data.by_status)
              .sort((a, b) => b[1] - a[1])
              .map(([status, count]) => (
                <button
                  key={status}
                  data-testid={`status-chip-${status}`}
                  onClick={() => navigate(`/notes?status=${encodeURIComponent(status)}`)}
                  className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border text-sm font-medium transition hover:shadow-sm hover:-translate-y-0.5 ${statusColor(status)}`}
                >
                  <span>{status}</span>
                  <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 rounded-full bg-white/70 text-slate-800 text-xs font-bold">{count}</span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <ChartCard title="Nota per Status">
          <ResponsiveContainer>
            <BarChart data={Object.entries(data.by_status).map(([k, v]) => ({ status: k.replace("Menunggu ", "").slice(0, 14), nota: v }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="status" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="nota" fill="#00A0A0" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {data.by_region && (
          <ChartCard title="Total Kewajiban per Region">
            <ResponsiveContainer>
              <BarChart data={data.by_region.map((r) => ({ region: r.region.replace("RO ", ""), kewajiban: r.kewajiban }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="region" tick={{ fontSize: 9 }} interval={0} angle={-30} textAnchor="end" height={70} />
                <YAxis tickFormatter={formatRupiahShort} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => formatRupiah(v)} />
                <Bar dataKey="kewajiban" fill="#F0B43C" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {data.by_area && !data.by_region && (
          <ChartCard title="Outstanding Pokok per Area">
            <ResponsiveContainer>
              <BarChart data={data.by_area.map((r) => ({ area: r.area.replace("Area ", ""), os: r.os_pokok }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="area" tick={{ fontSize: 9 }} interval={0} angle={-30} textAnchor="end" height={70} />
                <YAxis tickFormatter={formatRupiahShort} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => formatRupiah(v)} />
                <Bar dataKey="os" fill="#F0B43C" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {data.by_rco && (
          <ChartCard title="Nota per RCO">
            <ResponsiveContainer>
              <BarChart data={data.by_rco} layout="vertical">
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="rco" tick={{ fontSize: 10 }} width={110} />
                <Tooltip />
                <Bar dataKey="nota" fill="#00A0A0" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {data.by_month && (
          <ChartCard title="Jumlah Nota per Bulan">
            <ResponsiveContainer>
              <BarChart data={data.by_month}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="bulan" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="nota" fill="#00A0A0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </div>

      {/* Breakdown tables */}
      {data.by_region && (
        <BreakdownTable title="Breakdown per Region" cols={["Region", "Nota", "Loan", "OS Pokok", "OS Margin", "Penalty", "Kewajiban"]}
          rows={data.by_region.map((r) => [r.region, r.nota, r.loan, r.os_pokok, r.os_margin, r.penalty, r.kewajiban])} testid="table-region" />
      )}
      {data.by_area && (
        <BreakdownTable title="Breakdown per Area" cols={["Area", "Nota", "Loan", "OS Pokok", "OS Margin", "Penalty", "Kewajiban"]}
          rows={data.by_area.map((r) => [r.area, r.nota, r.loan, r.os_pokok, r.os_margin, r.penalty, r.kewajiban])} testid="table-area" />
      )}
    </div>
  );
}

function BreakdownTable({ title, cols, rows, testid }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 mb-6" data-testid={testid}>
      <h3 className="font-display font-semibold text-slate-800 mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
              {cols.map((c) => <th key={c} className="text-left font-semibold px-3 py-2 whitespace-nowrap">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/60">
                {r.map((cell, j) => (
                  <td key={j} className="px-3 py-2 whitespace-nowrap">
                    {j >= 3 ? formatRupiah(cell) : cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
