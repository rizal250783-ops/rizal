import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { Card, Th, Td, Empty, SectionTitle, Input, Badge } from "../components/ui";

export default function Audit() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  useEffect(() => { api.get("/audit-logs").then((r) => setRows(r.data)); }, []);
  const filtered = rows.filter((r) => (r.aktivitas + r.user_name).toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <SectionTitle sub="Catatan seluruh aktivitas sistem">Audit Log</SectionTitle>
        <Input placeholder="Cari aktivitas / user..." value={q} onChange={(e) => setQ(e.target.value)} className="w-56" data-testid="audit-search" />
      </div>
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200"><tr><Th>Waktu</Th><Th>User</Th><Th>Role</Th><Th>Aktivitas</Th><Th>Detail</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r) => (
                <tr key={r.id} data-testid={`audit-row-${r.id}`}>
                  <Td className="text-xs text-slate-400">{r.waktu?.slice(0, 19).replace("T", " ")}</Td>
                  <Td className="font-medium text-slate-900">{r.user_name}</Td>
                  <Td className="text-xs">{r.role || "-"}</Td>
                  <Td><Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{r.aktivitas}</Badge></Td>
                  <Td className="text-xs text-slate-500 max-w-xs truncate">{r.data_sesudah ? JSON.stringify(r.data_sesudah) : "-"}</Td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={5}><Empty>Tidak ada log.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
