import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, pct, statusColor, KOLEK } from "../lib/utils";
import { KpiCard, Card, Badge, SectionTitle, Empty } from "../components/ui";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { TrendingUp, PiggyBank, RotateCcw, ShieldAlert, Wallet, Users2 } from "lucide-react";

export default function Executive() {
  const { period } = useAuth();
  const [d, setD] = useState(null);

  useEffect(() => {
    if (period) api.get(`/dashboard/executive?period=${period}`).then((r) => setD(r.data));
  }, [period]);

  if (!d) return <Empty>Memuat data...</Empty>;

  const kolData = [1, 2, 3, 4, 5].map((k) => ({ name: `Kol ${k}`, value: d.portfolio.kol[k], color: KOLEK[k].color }));
  const barData = [
    { name: "Lending", Target: d.lending.target_booking, Realisasi: d.lending.realisasi_booking },
    { name: "Funding", Target: d.funding.target_funding, Realisasi: d.funding.realisasi_funding },
    { name: "Recovery", Target: d.recovery.target_recovery, Realisasi: d.recovery.realisasi_recovery },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard testid="kpi-lending" label="Realisasi Lending" value={fmtShort(d.lending.realisasi_booking)}
          sub={`Achievement ${pct(d.lending.achievement.value)}`} icon={TrendingUp} tone="emerald" />
        <KpiCard testid="kpi-funding" label="Realisasi Funding" value={fmtShort(d.funding.realisasi_funding)}
          sub={`Achievement ${pct(d.funding.achievement.value)}`} icon={PiggyBank} tone="gold" />
        <KpiCard testid="kpi-recovery" label="Recovery WO" value={fmtShort(d.recovery.realisasi_recovery)}
          sub={`Achievement ${pct(d.recovery.achievement.value)}`} icon={RotateCcw} tone="slate" />
        <KpiCard testid="kpi-npf" label="NPF Ratio" value={d.npf.npf_ratio == null ? "N/A" : pct(d.npf.npf_ratio)}
          sub={`Status: ${d.npf.status}`} icon={ShieldAlert} tone={d.npf.status === "Sehat" ? "emerald" : "red"} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard testid="kpi-total-outstanding" label="Total Outstanding Portfolio" value={fmtShort(d.portfolio.total)} icon={Wallet} tone="emerald" />
        <KpiCard testid="kpi-npf-nominal" label="NPF Nominal (Kol 3-5)" value={fmtShort(d.portfolio.npf_out)} icon={ShieldAlert} tone="red" />
        <KpiCard testid="kpi-total-ao" label="Total AO Aktif" value={d.total_ao} icon={Users2} tone="slate" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="p-5 lg:col-span-7">
          <SectionTitle sub="Target vs Realisasi per segmen">Ringkasan Kinerja Bisnis</SectionTitle>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748B" }} />
              <YAxis tickFormatter={(v) => `${(v / 1e6).toFixed(0)}jt`} tick={{ fontSize: 11, fill: "#94A3B8" }} />
              <Tooltip formatter={(v) => fmtShort(v)} />
              <Legend />
              <Bar dataKey="Target" fill="#94A3B8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Realisasi" fill="#047857" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-5 lg:col-span-5">
          <SectionTitle sub="Distribusi Kolektibilitas 1-5">Kualitas Portfolio</SectionTitle>
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie data={kolData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2}>
                {kolData.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={(v) => fmtShort(v)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-5 gap-1 mt-2">
            {[1, 2, 3, 4, 5].map((k) => (
              <div key={k} className="text-center">
                <div className="h-2 rounded-full" style={{ background: KOLEK[k].color }} />
                <div className="text-[10px] text-slate-500 mt-1">Kol {k}</div>
                <div className="text-[10px] font-semibold text-slate-700">{d.portfolio.kol_count[k]}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <div className="flex items-center gap-3">
          <Badge className={statusColor(d.npf.status)} testid="exec-npf-status">NPF {d.npf.status}</Badge>
          <span className="text-sm text-slate-600">NPF Score: <b className="font-num">{pct(d.npf.npf_score)}</b> — konsep "Lower is Better" dikonversi ke skor sebanding.</span>
        </div>
      </Card>
    </div>
  );
}
