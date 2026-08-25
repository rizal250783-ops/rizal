import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Landmark, Loader2 } from "lucide-react";

const BG = "https://images.pexels.com/photos/32327756/pexels-photo-32327756.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div
        className="hidden lg:flex flex-1 relative bg-cover bg-center"
        style={{ backgroundImage: `url(${BG})` }}
      >
        <div className="absolute inset-0 bg-toska-dark/85" />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <p className="text-xs uppercase tracking-widest text-gold mb-3">PT. Bank Syariah Indonesia, Tbk</p>
          <h1 className="font-heading text-4xl font-bold tracking-tight mb-3">CASEWISE LEGAL PERDATA</h1>
          <p className="text-sm text-white/80 max-w-md leading-relaxed">
            Legal Case Management System untuk monitoring, pengelolaan, approval, dan dokumentasi
            perkara gugatan perdata oleh Legal Group (LGG).
          </p>
        </div>
      </div>

      <div className="flex-1 lg:max-w-xl flex items-center justify-center bg-white p-6">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-12 w-12 bg-toska rounded-md flex items-center justify-center">
              <Landmark className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="font-heading font-bold text-xl text-slate-900 tracking-tight">CASEWISE</p>
              <p className="text-xs uppercase tracking-widest text-slate-500">Legal Perdata — BSI</p>
            </div>
          </div>

          <h2 className="font-heading text-2xl font-semibold text-slate-900 mb-1">Masuk Aplikasi</h2>
          <p className="text-sm text-slate-500 mb-6">Gunakan username dan password Anda.</p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                data-testid="login-username-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Masukkan username"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                data-testid="login-password-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password"
                autoComplete="current-password"
                required
              />
            </div>
            {error && (
              <div data-testid="login-error-message" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                {error}
              </div>
            )}
            <Button
              data-testid="login-submit-button"
              type="submit"
              disabled={loading}
              className="w-full bg-toska hover:bg-toska-hover text-white"
            >
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Masuk
            </Button>
          </form>

          <p className="text-xs text-slate-400 mt-8 text-center">
            Internal Use Only — Legal Group (LGG) PT. Bank Syariah Indonesia, Tbk
          </p>
        </div>
      </div>
    </div>
  );
}
