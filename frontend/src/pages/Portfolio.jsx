import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api from "../lib/api";
import { fmtShort, KOLEK } from "../lib/utils";
import { Card, Th, Td, Empty, Badge, KpiCard, SectionTitle, Input } from "../components/ui";
import { Wallet, Layers } from "lucide-react";

export default function Portfolio() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState(null);
  const [q, setQ] = useState("");
  const [kolek, setKolek] = useState(0);

  useEffect(() => {
    api.get("/portfolio").then((r) => setRows(r.data));
    api.get("/portfolio/summary").then((r) => setSummary(r.data));
  }, []);

  const filtered = rows.filter((r) =>
    (kolek === 0 || r.kolektibilitas === kolek) &&
    (r.nama_nasabah?.toLowerCase().includes(q.toLowerCase()) || r.nomor_kontrak?.toLowerCase().includes(q.toLowerCase())));

  return (
    <div className="space-y-6">
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <KpiCard testid="kpi-total" label="Total Outstanding" value={fmtShort(summary.total)} icon={Wallet} tone="emerald" />
          {[1, 2, 3, 4, 5].map((k) => (
            <div key={k} className="card p-4" data-testid={`kolek-card-${k}`}>
              <div className="text-[10px] font-semibold uppercase" style={{ color: KOLEK[k].color }}>Kol {k} · {KOLEK[k].label}</div>
              <div className="font-num font-bold text-slate-900 mt-1 text-sm">{fmtShort(summary.kol[k])}</div>
              <div className="text-[11px] text-slate-500">{summary.kol_count[k]} nasabah</div>
            </div>
          ))}
        </div>
      )}

      <Card className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <SectionTitle sub="Detail portfolio nasabah kelolaan">Portfolio Nasabah</SectionTitle>
          <div className="flex gap-2">
            <Input placeholder="Cari nama / kontrak..." value={q} onChange={(e) => setQ(e.target.value)} className="w-48" data-testid="portfolio-search" />
            <select className="rounded-lg border border-slate-300 px-3 text-sm" value={kolek} onChange={(e) => setKolek(parseInt(e.target.value))} data-testid="portfolio-kolek-filter">
              <option value={0}>Semua Kolek</option>
              {[1, 2, 3, 4, 5].map((k) => <option key={k} value={k}>Kol {k}</option>)}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr><Th>No. Kontrak</Th><Th>Nasabah</Th><Th>Produk</Th><Th className="text-right">Plafond</Th><Th className="text-right">Outstanding</Th><Th>Kolek</Th><Th className="text-right">DPD</Th><Th>AO</Th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r) => (
                <tr key={r.id} data-testid={`portfolio-row-${r.id}`}>
                  <Td className="font-num text-xs">{r.nomor_kontrak}</Td>
                  <Td className="font-medium text-slate-900">{r.nama_nasabah}</Td>
                  <Td className="text-xs">{r.produk}</Td>
                  <Td className="text-right font-num">{fmtShort(r.plafond)}</Td>
                  <Td className="text-right font-num">{fmtShort(r.outstanding_pokok)}</Td>
                  <Td><Badge className={`border`} style={{ background: KOLEK[r.kolektibilitas]?.bg, color: KOLEK[r.kolektibilitas]?.color }}>Kol {r.kolektibilitas}</Badge></Td>
                  <Td className="text-right font-num">{r.dpd}</Td>
                  <Td className="text-xs text-slate-500">{r.ao_name}</Td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={8}><Empty>Tidak ada data portfolio.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
