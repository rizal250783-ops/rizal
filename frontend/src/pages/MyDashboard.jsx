import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, pct, statusColor, KOLEK } from "../lib/utils";
import { KpiCard, Card, Badge, SectionTitle, Empty } from "../components/ui";
import { PieChart, Pie, Cell, ResponsiveContainer, RadialBarChart, RadialBar } from "recharts";
import { Target, TrendingUp, PiggyBank, RotateCcw, ShieldAlert, Gauge } from "lucide-react";

function Gap({ target, realisasi }) {
  const gap = (target || 0) - (realisasi || 0);
  return <span className={gap <= 0 ? "text-emerald-700" : "text-red-600"}>{gap <= 0 ? "Tercapai +" : "Kurang "}{fmtShort(Math.abs(gap))}</span>;
}

function ScoreGauge({ score }) {
  const val = score == null ? 0 : Math.min(score, 150);
  const data = [{ value: val, fill: score >= 100 ? "#047857" : score >= 85 ? "#2563EB" : score >= 70 ? "#D97706" : "#DC2626" }];
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={180}>
        <RadialBarChart innerRadius="70%" outerRadius="100%" data={data} startAngle={220} endAngle={-40}>
          <RadialBar background dataKey="value" cornerRadius={10} max={150} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-3xl font-bold font-num text-slate-900">{pct(score)}</div>
        <div className="text-xs text-slate-500">Performance Score</div>
      </div>
    </div>
  );
}

export default function MyDashboard() {
  const { user, period } = useAuth();
  const [d, setD] = useState(null);

  useEffect(() => {
    if (period) api.get(`/dashboard/me?period=${period}`).then((r) => setD(r.data));
  }, [period]);

  if (!d) return <Empty>Memuat data...</Empty>;
  const ps = d.performance || {};

  return (
    <div className="space-y-6">
      {ps.partial && <div className="rounded-lg bg-gold-100 border border-amber-200 px-4 py-2.5 text-sm text-gold-800" data-testid="partial-note">{ps.note}</div>}

      {user.role === "ao_lending" && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard testid="kpi-target-booking" label="Target Booking Baru" value={fmtShort(d.target_booking)} icon={Target} tone="slate" />
            <KpiCard testid="kpi-realisasi-booking" label="Realisasi Booking" value={fmtShort(d.realisasi_booking)} icon={TrendingUp} tone="emerald" />
            <KpiCard testid="kpi-ach-lending" label="Achievement Lending" value={d.ach_lending.label} sub={<Gap target={d.target_booking} realisasi={d.realisasi_booking} />} icon={Gauge} tone="gold" />
            <KpiCard testid="kpi-ach-funding" label="Achievement Funding" value={d.ach_funding.label} sub={`Realisasi ${fmtShort(d.realisasi_funding)}`} icon={PiggyBank} tone="emerald" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-5 flex flex-col items-center justify-center">
              <ScoreGauge score={ps.value} />
              <Badge className={statusColor(ps.status) + " mt-2"} testid="my-status">{ps.status}</Badge>
            </Card>
            <Card className="p-5 lg:col-span-2">
              <SectionTitle sub="Kualitas portfolio nasabah kelolaan">Portfolio Saya</SectionTitle>
              {d.portfolio && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <KpiCard testid="kpi-portfolio-total" label="Total Outstanding" value={fmtShort(d.portfolio.total)} tone="emerald" />
                  {[1, 2].map((k) => (
                    <div key={k} className="rounded-lg p-4" style={{ background: KOLEK[k].bg }}>
                      <div className="text-xs font-semibold uppercase" style={{ color: KOLEK[k].color }}>Kol {k} · {KOLEK[k].label}</div>
                      <div className="mt-1 font-num font-bold text-slate-900">{fmtShort(d.portfolio.kol[k])}</div>
                      <div className="text-xs text-slate-500">{d.portfolio.kol_count[k]} nasabah</div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}

      {user.role === "ao_funding" && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard testid="kpi-target-funding" label="Target Funding Baru" value={fmtShort(d.target_funding)} icon={Target} tone="slate" />
            <KpiCard testid="kpi-realisasi-funding" label="Realisasi Funding Baru" value={fmtShort(d.realisasi_funding)} icon={PiggyBank} tone="emerald" />
            <KpiCard testid="kpi-ach-funding" label="Achievement Funding" value={d.ach_funding.label} sub={<Gap target={d.target_funding} realisasi={d.realisasi_funding} />} icon={Gauge} tone="gold" />
            <KpiCard testid="kpi-score" label="Performance Score" value={pct(ps.value)} sub={ps.status} icon={TrendingUp} tone="emerald" />
          </div>
          <Card className="p-5 flex flex-col items-center">
            <ScoreGauge score={ps.value} />
            <Badge className={statusColor(ps.status) + " mt-2"} testid="my-status">{ps.status}</Badge>
          </Card>
        </>
      )}

      {user.role === "pic_remedial" && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard testid="kpi-target-recovery" label="Target Recovery WO" value={fmtShort(d.target_recovery)} icon={Target} tone="slate" />
            <KpiCard testid="kpi-realisasi-recovery" label="Realisasi Recovery WO" value={fmtShort(d.realisasi_recovery)} icon={RotateCcw} tone="emerald" />
            <KpiCard testid="kpi-ach-recovery" label="Achievement Recovery" value={d.ach_recovery.label} sub={<Gap target={d.target_recovery} realisasi={d.realisasi_recovery} />} icon={Gauge} tone="gold" />
            <KpiCard testid="kpi-npf" label="NPF Ratio" value={d.npf.npf_ratio == null ? "N/A" : pct(d.npf.npf_ratio)} sub={`Status ${d.npf.status}`} icon={ShieldAlert} tone={d.npf.status === "Sehat" ? "emerald" : "red"} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-5 flex flex-col items-center justify-center">
              <ScoreGauge score={ps.value} />
              <Badge className={statusColor(ps.status) + " mt-2"} testid="my-status">{ps.status}</Badge>
            </Card>
            <Card className="p-5 lg:col-span-2">
              <SectionTitle sub="Recovery WO 70% + NPF Position 30%">Rincian Remedial Score</SectionTitle>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-emerald-50 p-4"><div className="text-xs text-emerald-700 font-semibold">Recovery Achievement</div><div className="font-num font-bold text-xl mt-1">{d.ach_recovery.label}</div></div>
                <div className="rounded-lg bg-gold-100 p-4"><div className="text-xs text-gold-800 font-semibold">NPF Score</div><div className="font-num font-bold text-xl mt-1">{pct(d.npf.npf_score)}</div><div className="text-xs text-slate-500 mt-0.5">NPF {pct(d.npf.npf_ratio)} vs target {pct(d.npf.target_npf_ratio)}</div></div>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
