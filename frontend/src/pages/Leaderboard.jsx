import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, pct, statusColor, ROLE_LABEL } from "../lib/utils";
import { Card, Badge, Th, Td, Empty, Button } from "../components/ui";
import { Trophy, Medal } from "lucide-react";

const TABS = [["lending", "AO Lending"], ["funding", "AO Funding"], ["remedial", "PIC Remedial"]];

export default function Leaderboard() {
  const { period } = useAuth();
  const [type, setType] = useState("lending");
  const [data, setData] = useState(null);

  useEffect(() => {
    if (period) api.get(`/ranking?type=${type}&period=${period}`).then((r) => setData(r.data));
  }, [type, period]);

  return (
    <div className="space-y-5">
      <div className="flex gap-2">
        {TABS.map(([k, label]) => (
          <Button key={k} variant={type === k ? "primary" : "outline"} onClick={() => setType(k)} data-testid={`tab-${k}`}>{label}</Button>
        ))}
      </div>

      {!data ? <Empty>Memuat...</Empty> : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr><Th>Rank</Th><Th>Nama AO</Th><Th>Role</Th><Th className="text-right">Target</Th><Th className="text-right">Realisasi</Th><Th className="text-right">Achievement</Th><Th className="text-right">Score</Th><Th>Status</Th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.entries.map((e) => (
                  <tr key={e.ao_id} data-testid={`rank-row-${e.ao_id}`} className={e.rank && e.rank <= 3 ? "bg-emerald-50/40" : ""}>
                    <Td>
                      {e.rank == null ? <Badge className="bg-slate-100 text-slate-500 border-slate-200">N/A</Badge> :
                        e.rank <= 3 ? <span className="inline-flex items-center gap-1 font-bold text-gold-700"><Medal size={16} />{e.rank}</span> :
                        <span className="font-num font-semibold text-slate-600">{e.rank}</span>}
                    </Td>
                    <Td className="font-medium text-slate-900">{e.name}</Td>
                    <Td className="text-xs text-slate-500">{ROLE_LABEL[e.role]}</Td>
                    <Td className="text-right font-num">{fmtShort(e.detail.target_booking || e.detail.target_funding || e.detail.target_recovery)}</Td>
                    <Td className="text-right font-num">{fmtShort(e.realisasi)}</Td>
                    <Td className="text-right font-num">{pct(e.achievement_value)}</Td>
                    <Td className="text-right font-num font-bold">{pct(e.performance_score)}</Td>
                    <Td><Badge className={statusColor(e.status)}>{e.status}</Badge></Td>
                  </tr>
                ))}
                {data.entries.length === 0 && <tr><td colSpan={8}><Empty>Belum ada data.</Empty></td></tr>}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
