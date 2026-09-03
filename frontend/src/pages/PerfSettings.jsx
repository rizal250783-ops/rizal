import React, { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import api, { apiErr } from "../lib/api";
import { Card, Button, Input, SectionTitle, Empty, Badge } from "../components/ui";
import { Save, History } from "lucide-react";

export default function PerfSettings() {
  const { user } = useAuth();
  const readOnly = user.role === "direktur";
  const [s, setS] = useState(null);
  const [hist, setHist] = useState([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = () => {
    api.get("/performance-settings").then((r) => setS(r.data));
    api.get("/performance-settings/history").then((r) => setHist(r.data));
  };
  useEffect(() => { load(); }, []);
  if (!s) return <Empty>Memuat...</Empty>;

  const saveWeights = async (role, weights) => {
    setErr(""); setMsg("");
    const total = Object.values(weights).reduce((a, b) => a + Number(b), 0);
    if (Math.abs(total - 100) > 0.01) { setErr(`Total bobot ${role} harus 100% (sekarang ${total}%)`); return; }
    if (!window.confirm(`Simpan bobot baru untuk ${role}? Versi baru akan dibuat.`)) return;
    try { await api.post("/performance-settings", { role, weights }); setMsg("Bobot tersimpan sebagai versi baru."); load(); }
    catch (e) { setErr(apiErr(e)); }
  };

  const saveParam = async (key, value) => {
    try { await api.post("/performance-settings/parameter", { parameter_key: key, parameter_value: Number(value) }); setMsg("Parameter tersimpan."); load(); }
    catch (e) { setErr(apiErr(e)); }
  };

  return (
    <div className="space-y-6">
      {msg && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2.5 text-sm text-emerald-800">{msg}</div>}
      {err && <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">{err}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <WeightCard title="AO Lending" role="ao_lending" weights={s.ao_lending} fields={[["lending", "New Booking Lending"], ["funding", "New Funding Acquisition"]]} readOnly={readOnly} onSave={saveWeights} />
        <WeightCard title="AO Funding" role="ao_funding" weights={s.ao_funding} fields={[["funding", "New Funding Acquisition"]]} readOnly={readOnly} onSave={saveWeights} />
        <WeightCard title="PIC Remedial" role="pic_remedial" weights={s.pic_remedial} fields={[["recovery", "Recovery WO"], ["npf", "NPF Position"]]} readOnly={readOnly} onSave={saveWeights} />
      </div>

      <Card className="p-5">
        <SectionTitle sub="Parameter non-bobot (dapat dikonfigurasi, tidak hardcoded)">Parameter NPF</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <ParamRow label="NPF Score Cap (%)" k="npf_score_cap" value={s.parameters.npf_score_cap} readOnly={readOnly} onSave={saveParam} />
          <ParamRow label="Ambang Status NPF (+poin %)" k="npf_status_threshold" value={s.parameters.npf_status_threshold} readOnly={readOnly} onSave={saveParam} />
        </div>
      </Card>

      <Card className="p-5">
        <SectionTitle sub="Setiap perubahan membuat versi baru (tidak menimpa)"><span className="inline-flex items-center gap-2"><History size={18} /> Versioning Performance Setting</span></SectionTitle>
        <div className="space-y-2 max-h-72 overflow-y-auto">
          {hist.map((h) => (
            <div key={h.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-2 text-sm">
              <div><b>{h.type === "weight" ? h.role : h.parameter_key}</b> v{h.version} <span className="text-slate-400">· {h.created_by}</span></div>
              <div className="font-num text-xs text-slate-600">{h.type === "weight" ? JSON.stringify(h.weights) : h.parameter_value}</div>
            </div>
          ))}
          {hist.length === 0 && <Empty>Belum ada riwayat.</Empty>}
        </div>
      </Card>
    </div>
  );
}

function WeightCard({ title, role, weights, fields, readOnly, onSave }) {
  const [w, setW] = useState(weights);
  const total = Object.values(w).reduce((a, b) => a + Number(b), 0);
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading font-semibold text-slate-900">{title}</h3>
        <Badge className={Math.abs(total - 100) < 0.01 ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"}>Total {total}%</Badge>
      </div>
      <div className="space-y-3">
        {fields.map(([k, label]) => (
          <div key={k}>
            <label className="text-xs font-medium text-slate-600">{label}</label>
            <div className="flex items-center gap-2">
              <Input type="number" value={w[k] ?? 0} disabled={readOnly} onChange={(e) => setW({ ...w, [k]: Number(e.target.value) })} data-testid={`w-${role}-${k}`} />
              <span className="text-sm text-slate-400">%</span>
            </div>
          </div>
        ))}
      </div>
      {!readOnly && <Button className="w-full mt-4" onClick={() => onSave(role, w)} data-testid={`save-${role}`}><Save size={16} /> Simpan Bobot</Button>}
    </Card>
  );
}

function ParamRow({ label, k, value, readOnly, onSave }) {
  const [v, setV] = useState(value);
  return (
    <div>
      <label className="text-xs font-medium text-slate-600">{label}</label>
      <div className="flex gap-2">
        <Input type="number" value={v} disabled={readOnly} onChange={(e) => setV(e.target.value)} data-testid={`param-${k}`} />
        {!readOnly && <Button variant="outline" onClick={() => onSave(k, v)} data-testid={`save-param-${k}`}><Save size={16} /></Button>}
      </div>
    </div>
  );
}
