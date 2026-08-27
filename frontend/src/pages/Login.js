import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../lib/api";
import { BsiLogo, Marquee } from "../components/Brand";
import { Loader2, Lock, User } from "lucide-react";

const TAGLINE = "Solusi cerdas menuju pembiayaan berkelanjutan";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [nip, setNip] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(nip.trim(), password);
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left brand panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#00A0A0] relative overflow-hidden flex-col justify-between p-12">
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, #fff 1px, transparent 1px)", backgroundSize: "28px 28px" }} />
        <div className="relative z-10"><BsiLogo size="md" inverse /></div>
        <div className="relative z-10">
          <div className="text-[#F0B43C] text-sm font-semibold tracking-widest mb-3">APLIKASI INTERNAL</div>
          <h1 className="text-white font-display font-extrabold text-4xl leading-tight mb-4">
            RCG DIGITAL<br />RESTRUCTURING
          </h1>
          <p className="text-white/80 max-w-md leading-relaxed">
            Digitalisasi Nota Analisa Restruktur Pembiayaan — Retail Collection, Restructuring & Recovery Group.
          </p>
        </div>
        <div className="relative z-10">
          <Marquee text={TAGLINE} className="text-[#F0B43C] text-base font-medium" />
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-white">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8 flex justify-center"><BsiLogo size="lg" /></div>
          <h2 className="font-display font-bold text-2xl text-slate-900 mb-1">Masuk ke Akun</h2>
          <p className="text-slate-500 text-sm mb-8">Gunakan NIP dan password Anda</p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">NIP</label>
              <div className="relative mt-1.5">
                <User size={18} className="absolute left-3 top-3 text-slate-400" />
                <input
                  data-testid="login-nip"
                  value={nip}
                  onChange={(e) => setNip(e.target.value)}
                  placeholder="Masukkan NIP"
                  className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Password</label>
              <div className="relative mt-1.5">
                <Lock size={18} className="absolute left-3 top-3 text-slate-400" />
                <input
                  data-testid="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Masukkan password"
                  className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none"
                />
              </div>
            </div>
            {error && <div data-testid="login-error" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</div>}
            <button
              type="submit"
              disabled={loading}
              data-testid="login-submit"
              className="w-full bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold py-2.5 rounded-md transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading && <Loader2 size={18} className="animate-spin" />} Masuk
            </button>
          </form>
          <p className="text-xs text-slate-400 mt-8 text-center">© PT. Bank Syariah Indonesia, Tbk — Internal Use Only</p>
        </div>
      </div>
    </div>
  );
}
