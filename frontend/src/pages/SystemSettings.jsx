import React, { useEffect, useState } from "react";
import api, { apiErr } from "../lib/api";
import { Card, Button, Input, Select, SectionTitle } from "../components/ui";
import { Save } from "lucide-react";

export default function SystemSettings() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => { api.get("/settings").then((r) => setS(r.data)); }, []);
  if (!s) return null;

  const months = ["01","02","03","04","05","06","07","08","09","10","11","12"];
  const [py, pm] = (s.active_period || "").split("-");
  const now = new Date();

  const save = async () => {
    setErr(""); setMsg("");
    try { await api.put("/settings", s); setMsg("Pengaturan tersimpan. Perubahan periode aktif tercatat di Audit Log."); }
    catch (e) { setErr(apiErr(e)); }
  };

  return (
    <div className="space-y-5 max-w-2xl">
      {msg && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2.5 text-sm text-emerald-800">{msg}</div>}
      {err && <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">{err}</div>}
      <Card className="p-5">
        <SectionTitle sub="Periode aktif dipakai Ranking Engine & notifikasi (aturan 19a)">Periode Aktif Sistem</SectionTitle>
        <div className="grid grid-cols-2 gap-3">
          <Select value={pm} onChange={(e) => setS({ ...s, active_period: `${py}-${e.target.value}` })} data-testid="setting-month">
            {months.map((m, i) => <option key={m} value={m}>{["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"][i]}</option>)}
          </Select>
          <Select value={py} onChange={(e) => setS({ ...s, active_period: `${e.target.value}-${pm}` })} data-testid="setting-year">
            {[now.getFullYear(), now.getFullYear() - 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </Select>
        </div>
      </Card>
      <Card className="p-5">
        <SectionTitle sub="Sesi berakhir otomatis setelah tidak aktif (aturan 14a)">Session Timeout</SectionTitle>
        <div className="flex items-center gap-2">
          <Input type="number" value={s.session_timeout_minutes} onChange={(e) => setS({ ...s, session_timeout_minutes: parseInt(e.target.value) || 60 })} className="w-40" data-testid="setting-timeout" />
          <span className="text-sm text-slate-500">menit</span>
        </div>
      </Card>
      <Button onClick={save} data-testid="settings-save"><Save size={16} /> Simpan Pengaturan</Button>
    </div>
  );
}
