import { useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { KeyRound } from "lucide-react";

export default function ChangePassword() {
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm_password: "" });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (form.new_password !== form.confirm_password) return toast.error("Konfirmasi password tidak cocok");
    setLoading(true);
    try {
      await api.post("/auth/change-password", form);
      toast.success("Password berhasil diubah");
      setForm({ old_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  const inp = "w-full px-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none";

  return (
    <div>
      <PageHeader title="Ganti Password" subtitle="Perbarui password akun Anda (maksimal 8 karakter)" icon={KeyRound} />
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 max-w-md">
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Password Lama</label>
            <input type="password" data-testid="cp-old" className={inp + " mt-1.5"} value={form.old_password} onChange={(e) => setForm({ ...form, old_password: e.target.value })} required />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Password Baru</label>
            <input type="password" maxLength={8} data-testid="cp-new" className={inp + " mt-1.5"} value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} required />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Konfirmasi Password Baru</label>
            <input type="password" maxLength={8} data-testid="cp-confirm" className={inp + " mt-1.5"} value={form.confirm_password} onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} required />
          </div>
          <button disabled={loading} data-testid="cp-submit" className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-5 py-2.5 rounded-md text-sm disabled:opacity-60">
            Simpan Perubahan
          </button>
        </form>
      </div>
    </div>
  );
}
