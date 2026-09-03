import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, pct, statusColor, KOLEK } from "../lib/utils";
import { Card, Badge, KpiCard, SectionTitle, Empty, Th, Td } from "../components/ui";
import { ShieldAlert, TrendingDown, Users2 } from "lucide-react";

export default function NPF() {
  const { period } = useAuth();
  const [d, setD] = useState(null);
  const [rows, setRows] = useState([]);

  useEffect(() => {
    if (!period) return;
    api.get(`/npf?period=${period}`).then((r) => setD(r.data));
    api.get("/portfolio").then((r) => setRows(r.data.filter((x) => x.kolektibilitas >= 3)));
  }, [period]);

  if (!d) return <Empty>Memuat...</Empty>;
  const npf = d.npf;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard testid="npf-ratio" label="NPF Ratio Aktual" value={npf.npf_ratio == null ? "N/A" : pct(npf.npf_ratio)} sub={`Target maks ${pct(d.target_npf_ratio)}`} icon={ShieldAlert} tone={npf.status === "Sehat" ? "emerald" : "red"} />
        <KpiCard testid="npf-nominal" label="NPF Nominal (Kol 3-5)" value={fmtShort(d.portfolio.npf_out)} sub={`Target abs ${fmtShort(d.target_npf_absolute)}`} icon={TrendingDown} tone="red" />
        <KpiCard testid="npf-score" label="NPF Score" value={pct(npf.npf_score)} sub="Cap 150% · Lower is Better" icon={ShieldAlert} tone="gold" />
        <KpiCard testid="npf-accounts" label="Account Bermasalah" value={rows.length} sub="Kolektibilitas 3-5" icon={Users2} tone="slate" />
      </div>

      <Card className="p-5">
        <div className="flex items-center gap-3">
          <Badge className={statusColor(npf.status)} testid="npf-status">Status NPF: {npf.status}</Badge>
          <span className="text-sm text-slate-600">
            {npf.status === "Sehat" && `NPF ≤ Target (${pct(d.target_npf_ratio)}).`}
            {npf.status === "Perhatian" && `NPF di antara target dan target +1 poin.`}
            {npf.status === "Critical" && `NPF melebihi target +1 poin persentase.`}
            {npf.status === "N/A" && `Total outstanding 0.`}
          </span>
        </div>
      </Card>

      <Card className="p-5">
        <SectionTitle sub="Kolektibilitas 3, 4, 5">Monitoring Nasabah Bermasalah</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr><Th>No. Kontrak</Th><Th>Nasabah</Th><Th className="text-right">Outstanding</Th><Th>Kolek</Th><Th className="text-right">DPD</Th><Th>AO/PIC</Th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr key={r.id} data-testid={`npf-row-${r.id}`}>
                  <Td className="font-num text-xs">{r.nomor_kontrak}</Td>
                  <Td className="font-medium text-slate-900">{r.nama_nasabah}</Td>
                  <Td className="text-right font-num">{fmtShort(r.outstanding_pokok)}</Td>
                  <Td><Badge style={{ background: KOLEK[r.kolektibilitas]?.bg, color: KOLEK[r.kolektibilitas]?.color }} className="border">Kol {r.kolektibilitas}</Badge></Td>
                  <Td className="text-right font-num">{r.dpd}</Td>
                  <Td className="text-xs text-slate-500">{r.ao_name}</Td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={6}><Empty>Tidak ada nasabah bermasalah.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
