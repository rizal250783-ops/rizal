import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import { apiErr } from "../lib/api";
import { LOGO } from "../lib/utils";
import { Button, Input } from "../components/ui";
import { ShieldCheck, TrendingUp } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setLoading(true);
    try {
      const u = await login(email, password);
      if (u.requires_password_reset) nav("/change-password");
      else nav("/");
    } catch (e2) {
      setErr(apiErr(e2));
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="hidden lg:flex flex-col justify-between bg-emerald-900 text-white p-12 relative overflow-hidden">
        <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-emerald-800/50" />
        <div className="absolute -left-16 bottom-10 h-64 w-64 rounded-full bg-emerald-800/40" />
        <div className="relative flex items-center gap-4">
          <img src={LOGO} alt="Logo" className="h-16 w-16 rounded-full bg-white p-1.5 object-contain" />
          <div>
            <div className="font-heading text-3xl font-extrabold">AO-360</div>
            <div className="text-emerald-300 text-sm tracking-wide">AO Achievement Dashboard</div>
          </div>
        </div>
        <div className="relative">
          <h2 className="font-heading text-4xl font-bold leading-tight">Mengukur.<br/>Mengevaluasi.<br/><span className="text-gold-500">Meningkatkan.</span></h2>
          <p className="mt-4 text-emerald-200 max-w-md">Pusat monitoring kinerja Account Officer PT BPRS Haji Miskin — pencapaian target, kualitas portfolio, dan dokumentasi penagihan dalam satu dashboard.</p>
        </div>
        <div className="relative flex gap-6 text-sm text-emerald-200">
          <div className="flex items-center gap-2"><ShieldCheck size={18} className="text-gold-500"/> Role-based Access</div>
          <div className="flex items-center gap-2"><TrendingUp size={18} className="text-gold-500"/> Real-time KPI</div>
        </div>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center p-6 sm:p-12 bg-slate-50">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <img src={LOGO} alt="Logo" className="h-14 w-14 rounded-full bg-white border border-slate-200 p-1 object-contain" />
            <div>
              <div className="font-heading text-2xl font-extrabold text-emerald-900">AO-360</div>
              <div className="text-xs text-slate-500">AO Achievement Dashboard</div>
            </div>
          </div>
          <div className="card p-8">
            <h1 className="font-heading text-2xl font-bold text-slate-900">Masuk</h1>
            <p className="text-sm text-slate-500 mt-1 mb-6">PT BPRS Haji Miskin</p>
            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Email</label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  placeholder="nama@hajimiskin.co.id" className="mt-1" data-testid="login-email" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Password</label>
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                  placeholder="••••••••" className="mt-1" data-testid="login-password" />
              </div>
              {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700" data-testid="login-error">{err}</div>}
              <Button type="submit" disabled={loading} className="w-full" data-testid="login-submit">
                {loading ? "Memproses..." : "Masuk"}
              </Button>
            </form>
          </div>
          <p className="text-center text-xs text-slate-400 mt-6">© {new Date().getFullYear()} PT BPRS Haji Miskin · Direktur: HENDRI KAMAL</p>
        </div>
      </div>
    </div>
  );
}
