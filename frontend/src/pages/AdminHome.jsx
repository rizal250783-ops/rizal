import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, pct, ROLE_LABEL } from "../lib/utils";
import { KpiCard, Card, SectionTitle, Empty, Th, Td, Badge } from "../components/ui";
import { statusColor } from "../lib/utils";
import { Users2, TrendingUp, PiggyBank, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

export default function AdminHome() {
  const { period } = useAuth();
  const [exec, setExec] = useState(null);
  const [users, setUsers] = useState([]);
  const [rank, setRank] = useState([]);

  useEffect(() => {
    if (!period) return;
    api.get(`/dashboard/executive?period=${period}`).then((r) => setExec(r.data));
    api.get("/users").then((r) => setUsers(r.data));
    api.get(`/ranking?type=lending&period=${period}`).then((r) => setRank(r.data.entries));
  }, [period]);

  if (!exec) return <Empty>Memuat data...</Empty>;
  const activeUsers = users.filter((u) => u.is_active).length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard testid="kpi-users" label="Total User" value={`${activeUsers}/${users.length}`} sub="Aktif / Total" icon={Users2} tone="emerald" />
        <KpiCard testid="kpi-lending" label="Realisasi Lending" value={fmtShort(exec.lending.realisasi_booking)} sub={`Ach ${pct(exec.lending.achievement.value)}`} icon={TrendingUp} tone="emerald" />
        <KpiCard testid="kpi-funding" label="Realisasi Funding" value={fmtShort(exec.funding.realisasi_funding)} sub={`Ach ${pct(exec.funding.achievement.value)}`} icon={PiggyBank} tone="gold" />
        <KpiCard testid="kpi-npf" label="NPF Ratio" value={exec.npf.npf_ratio == null ? "N/A" : pct(exec.npf.npf_ratio)} sub={exec.npf.status} icon={ShieldAlert} tone={exec.npf.status === "Sehat" ? "emerald" : "red"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <SectionTitle sub="Ringkasan komposisi tim">Struktur User per Role</SectionTitle>
          <div className="space-y-2">
            {Object.keys(ROLE_LABEL).map((role) => {
              const c = users.filter((u) => u.role === role).length;
              return (
                <div key={role} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-2.5">
                  <span className="text-sm font-medium text-slate-700">{ROLE_LABEL[role]}</span>
                  <span className="font-num font-semibold text-slate-900">{c}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <SectionTitle sub="Top AO Lending periode ini">Ranking Teratas</SectionTitle>
            <Link to="/leaderboard" className="text-sm font-semibold text-emerald-700 hover:underline">Lihat semua</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-200"><tr><Th>#</Th><Th>Nama</Th><Th>Score</Th><Th>Status</Th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {rank.slice(0, 5).map((e) => (
                  <tr key={e.ao_id}><Td>{e.rank || "-"}</Td><Td className="font-medium text-slate-900">{e.name}</Td>
                    <Td className="font-num">{pct(e.performance_score)}</Td>
                    <Td><Badge className={statusColor(e.status)}>{e.status}</Badge></Td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
