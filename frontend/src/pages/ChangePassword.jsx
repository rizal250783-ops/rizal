import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import api, { apiErr } from "../lib/api";
import { LOGO } from "../lib/utils";
import { Button, Input } from "../components/ui";

export default function ChangePassword() {
  const { refreshUser } = useAuth();
  const nav = useNavigate();
  const [cur, setCur] = useState("");
  const [np, setNp] = useState("");
  const [np2, setNp2] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    if (np !== np2) { setErr("Konfirmasi password tidak cocok"); return; }
    try {
      await api.post("/auth/change-password", { current_password: cur, new_password: np });
      setOk(true);
      await refreshUser();
      setTimeout(() => nav("/"), 1000);
    } catch (e2) { setErr(apiErr(e2)); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-6 justify-center">
          <img src={LOGO} alt="Logo" className="h-12 w-12 rounded-full bg-white border p-1 object-contain" />
          <div className="font-heading text-xl font-extrabold text-emerald-900">AO-360</div>
        </div>
        <div className="card p-8">
          <h1 className="font-heading text-xl font-bold text-slate-900">Ganti Password</h1>
          <p className="text-sm text-slate-500 mt-1 mb-5">Anda wajib mengganti password sebelum melanjutkan. Minimal 8 karakter, kombinasi huruf & angka.</p>
          <form onSubmit={submit} className="space-y-4">
            <Input type="password" placeholder="Password saat ini / sementara" value={cur} onChange={(e) => setCur(e.target.value)} required data-testid="cp-current" />
            <Input type="password" placeholder="Password baru" value={np} onChange={(e) => setNp(e.target.value)} required data-testid="cp-new" />
            <Input type="password" placeholder="Ulangi password baru" value={np2} onChange={(e) => setNp2(e.target.value)} required data-testid="cp-confirm" />
            {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
            {ok && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">Password berhasil diubah. Mengalihkan...</div>}
            <Button type="submit" className="w-full" data-testid="cp-submit">Simpan Password</Button>
          </form>
        </div>
      </div>
    </div>
  );
}
