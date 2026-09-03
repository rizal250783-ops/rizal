import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api, { apiErr } from "../lib/api";
import { fmtShort, ROLE_LABEL } from "../lib/utils";
import { Card, Button, Input, Th, Td, Empty, SectionTitle, Badge } from "../components/ui";
import { Modal } from "./Users";
import { Pencil } from "lucide-react";

export default function Targets() {
  const { period } = useAuth();
  const [users, setUsers] = useState([]);
  const [targets, setTargets] = useState({});
  const [achs, setAchs] = useState({});
  const [edit, setEdit] = useState(null);

  const load = () => {
    api.get("/users").then((r) => setUsers(r.data.filter((u) => ["ao_lending", "ao_funding", "pic_remedial"].includes(u.role))));
    api.get(`/targets?period=${period}`).then((r) => setTargets(Object.fromEntries(r.data.map((t) => [t.ao_id, t]))));
    api.get(`/achievements?period=${period}`).then((r) => setAchs(Object.fromEntries(r.data.map((a) => [a.ao_id, a]))));
  };
  useEffect(() => { if (period) load(); }, [period]);

  return (
    <div className="space-y-5">
      <SectionTitle sub={`Target & realisasi per AO — periode ${period}`}>Target & Achievement</SectionTitle>
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200"><tr><Th>Nama AO</Th><Th>Role</Th><Th className="text-right">Target</Th><Th className="text-right">Realisasi</Th><Th>Aksi</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => {
                const t = targets[u.id] || {};
                const a = achs[u.id] || {};
                const key = u.role === "ao_lending" ? ["target_booking", "realisasi_booking"] : u.role === "ao_funding" ? ["target_funding", "realisasi_funding"] : ["target_recovery_wo", "realisasi_recovery_wo"];
                return (
                  <tr key={u.id} data-testid={`target-row-${u.id}`}>
                    <Td className="font-medium text-slate-900">{u.name}</Td>
                    <Td><Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{ROLE_LABEL[u.role]}</Badge></Td>
                    <Td className="text-right font-num">{fmtShort(t[key[0]])}</Td>
                    <Td className="text-right font-num">{fmtShort(a[key[1]])}</Td>
                    <Td><button onClick={() => setEdit({ u, t, a })} className="text-emerald-700 hover:bg-emerald-50 rounded p-1.5" data-testid={`edit-target-${u.id}`}><Pencil size={16} /></button></Td>
                  </tr>
                );
              })}
              {users.length === 0 && <tr><td colSpan={5}><Empty>Belum ada AO.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
      {edit && <EditModal period={period} data={edit} onClose={() => { setEdit(null); load(); }} />}
    </div>
  );
}

function EditModal({ period, data, onClose }) {
  const { u, t, a } = data;
  const [f, setF] = useState({
    target_booking: t.target_booking || 0, target_funding: t.target_funding || 0,
    target_recovery_wo: t.target_recovery_wo || 0, target_npf_ratio: t.target_npf_ratio || 0,
    target_npf_absolute: t.target_npf_absolute || 0,
    realisasi_booking: a.realisasi_booking || 0, realisasi_funding: a.realisasi_funding || 0,
    realisasi_recovery_wo: a.realisasi_recovery_wo || 0,
  });
  const [err, setErr] = useState("");
  const set = (k, v) => setF({ ...f, [k]: parseFloat(v) || 0 });

  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try {
      await api.post("/targets", { ao_id: u.id, period, target_booking: f.target_booking, target_funding: f.target_funding, target_recovery_wo: f.target_recovery_wo, target_npf_ratio: f.target_npf_ratio, target_npf_absolute: f.target_npf_absolute });
      await api.post("/achievements", { ao_id: u.id, period, realisasi_booking: f.realisasi_booking, realisasi_funding: f.realisasi_funding, realisasi_recovery_wo: f.realisasi_recovery_wo });
      onClose();
    } catch (e2) { setErr(apiErr(e2)); }
  };

  const Field = ({ k, label }) => (
    <div><label className="text-xs font-medium text-slate-600">{label}</label><Input type="number" defaultValue={f[k]} onChange={(e) => set(k, e.target.value)} data-testid={`f-${k}`} /></div>
  );

  return (
    <Modal title={`Target & Achievement · ${u.name}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3 max-h-[70vh] overflow-y-auto">
        {u.role === "ao_lending" && <><Field k="target_booking" label="Target Booking Baru" /><Field k="realisasi_booking" label="Realisasi Booking" /><Field k="target_funding" label="Target Funding Baru" /><Field k="realisasi_funding" label="Realisasi Funding" /></>}
        {u.role === "ao_funding" && <><Field k="target_funding" label="Target Funding Baru" /><Field k="realisasi_funding" label="Realisasi Funding" /></>}
        {u.role === "pic_remedial" && <><Field k="target_recovery_wo" label="Target Recovery WO" /><Field k="realisasi_recovery_wo" label="Realisasi Recovery WO" /><Field k="target_npf_ratio" label="Target NPF Ratio (%)" /><Field k="target_npf_absolute" label="Target NPF Absolute (Rp)" /></>}
        {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
        <div className="flex gap-2"><Button type="button" variant="outline" onClick={onClose} className="flex-1">Batal</Button><Button type="submit" className="flex-1" data-testid="target-submit">Simpan</Button></div>
      </form>
    </Modal>
  );
}
