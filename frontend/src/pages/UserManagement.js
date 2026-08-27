import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api, { apiError } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatRupiah, parseNumber, formatNumberInput } from "../lib/format";
import { Users, UserPlus, KeyRound, Trash2, Loader2, X, Pencil, History } from "lucide-react";
import { toast } from "sonner";

const EMPTY_FORM = { nama: "", nip: "", role: "RCO", jabatan: "", region: "", area: "", limit_pemutus: 0, status: "aktif" };

export default function UserManagement() {
  const { user } = useAuth();
  const [users, setUsers] = useState(null);
  const [regions, setRegions] = useState([]);
  const [areas, setAreas] = useState([]);
  const [roleFilter, setRoleFilter] = useState("");
  const [modal, setModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [genPw, setGenPw] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [histUser, setHistUser] = useState(null);
  const [histData, setHistData] = useState(null);

  const load = () => api.get("/users", { params: roleFilter ? { role: roleFilter } : {} }).then((r) => setUsers(r.data)).catch(() => setUsers([]));
  useEffect(() => { load(); }, [roleFilter]);
  useEffect(() => { api.get("/regions").then((r) => setRegions(r.data)); }, []);
  useEffect(() => {
    if (form.region) api.get("/areas", { params: { region: form.region } }).then((r) => setAreas(r.data));
    else setAreas([]);
  }, [form.region]);

  const openNew = () => { setForm({ ...EMPTY_FORM }); setEditingId(null); setGenPw(null); setModal(true); };
  const openEdit = (u) => {
    setForm({
      nama: u.nama || "", nip: u.nip || "", role: u.role, jabatan: u.jabatan || "",
      region: u.region || "", area: u.area || "", limit_pemutus: u.limit_pemutus || 0, status: u.status || "aktif",
    });
    setEditingId(u.id); setGenPw(null); setModal(true);
  };

  const submit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/users/${editingId}`, form);
        toast.success("Perubahan user tersimpan");
        setModal(false);
        load();
      } else {
        const { data } = await api.post("/users", form);
        setGenPw(data.generated_password);
        toast.success("User berhasil dibuat");
        load();
      }
    } catch (err) { toast.error(apiError(err)); }
  };

  const resetPw = async (u) => {
    try { const { data } = await api.post(`/users/${u.id}/reset-password`); toast.success(`Password baru: ${data.generated_password}`, { duration: 10000 }); }
    catch (err) { toast.error(apiError(err)); }
  };

  const del = async (u) => {
    if (!window.confirm(`Hapus user ${u.nama}?`)) return;
    try { await api.delete(`/users/${u.id}`); toast.success("User dihapus"); load(); }
    catch (err) { toast.error(apiError(err)); }
  };

  const openHistory = async (u) => {
    setHistUser(u); setHistData(null);
    try { const { data } = await api.get(`/users/${u.id}/history`); setHistData(data); }
    catch (err) { toast.error(apiError(err)); setHistData([]); }
  };

  const ACTION_LABEL = { create_user: "Dibuat", update_user: "Diubah", reset_password: "Reset Password", delete_user: "Dihapus" };
  const FIELD_LABEL = { limit_pemutus: "Limit Pemutus", area: "Area", region: "Region", status: "Status", nama: "Nama", jabatan: "Jabatan" };
  const fmtVal = (k, v) => {
    if (v === null || v === undefined || v === "") return "-";
    if (k === "limit_pemutus") return formatRupiah(v);
    return String(v);
  };
  const changeList = (log) => {
    if (log.action !== "update_user") return [];
    const oldV = log.old_value || {}; const newV = log.new_value || {};
    return Object.keys(FIELD_LABEL)
      .filter((k) => k in newV && String(oldV[k] ?? "") !== String(newV[k] ?? ""))
      .map((k) => ({ field: FIELD_LABEL[k], from: fmtVal(k, oldV[k]), to: fmtVal(k, newV[k]) }));
  };
  const fmtDate = (iso) => { try { return new Date(iso).toLocaleString("id-ID"); } catch { return iso; } };

  if (!users) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div>;

  const isAdmin = user.is_user_admin;
  const sel = "px-3 py-2 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]";
  const inp = "w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-[#00A0A0]/20 focus:border-[#00A0A0] outline-none";
  const roleOptions = editingId ? [form.role] : ["RCO", "ACRM", "RCRM", "RCG"];

  return (
    <div>
      <PageHeader title="Manajemen User" subtitle={isAdmin ? "Anda dapat menambah, mengubah (limit & area/region), reset password & menghapus user" : "Mode lihat & reset password (penambahan/perubahan/penghapusan hanya oleh SYAMSU RIZAL)"} icon={Users}
        action={isAdmin && <button onClick={openNew} data-testid="add-user-btn" className="bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2"><UserPlus size={18} /> Tambah User</button>} />

      <div className="flex gap-3 mb-4">
        <select className={sel} data-testid="filter-role" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
          <option value="">Semua Role</option>
          {["RCO", "ACRM", "RCRM", "RCG"].map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left font-semibold px-4 py-3">Nama</th>
                <th className="text-left font-semibold px-4 py-3">NIP</th>
                <th className="text-left font-semibold px-4 py-3">Role</th>
                <th className="text-left font-semibold px-4 py-3">Area / Region</th>
                <th className="text-right font-semibold px-4 py-3">Limit</th>
                <th className="text-center font-semibold px-4 py-3">Status</th>
                <th className="text-center font-semibold px-4 py-3">Aksi</th>
              </tr>
            </thead>
            <tbody data-testid="users-table-body">
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">{u.nama}{u.can_approve && <span className="ml-2 text-[10px] bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded-full border border-emerald-200">Pemutus RCG</span>}</td>
                  <td className="px-4 py-3 text-slate-600">{u.nip}</td>
                  <td className="px-4 py-3"><span className="text-xs font-semibold text-[#00A0A0]">{u.role}</span></td>
                  <td className="px-4 py-3 text-slate-600 text-xs">{u.area || "-"}<br />{u.region || ""}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-xs">{u.limit_pemutus ? formatRupiah(u.limit_pemutus) : "-"}</td>
                  <td className="px-4 py-3 text-center"><span className={`text-xs px-2 py-0.5 rounded-full ${u.status === "aktif" ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-500"}`}>{u.status}</span></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      {isAdmin && <button className="text-[#00A0A0] hover:bg-[#E6F6F6] p-1.5 rounded" onClick={() => openEdit(u)} title="Edit User" data-testid={`edit-${u.nip}`}><Pencil size={15} /></button>}
                      <button className="text-slate-500 hover:bg-slate-100 p-1.5 rounded" onClick={() => openHistory(u)} title="Riwayat Perubahan" data-testid={`history-${u.nip}`}><History size={15} /></button>
                      <button className="text-[#B4842A] hover:bg-[#FDF7EB] p-1.5 rounded" onClick={() => resetPw(u)} title="Reset Password" data-testid={`reset-${u.nip}`}><KeyRound size={15} /></button>
                      {isAdmin && u.nip !== "2175007386" && <button className="text-red-500 hover:bg-red-50 p-1.5 rounded" onClick={() => del(u)} title="Hapus" data-testid={`delete-${u.nip}`}><Trash2 size={15} /></button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setModal(false)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg" onClick={(e) => e.stopPropagation()} data-testid="user-modal">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-display font-bold text-lg">{editingId ? "Edit User" : "Tambah User"}</h3>
              <button onClick={() => setModal(false)}><X size={20} className="text-slate-400" /></button>
            </div>
            {genPw ? (
              <div className="p-6 text-center">
                <div className="text-slate-600 mb-2">User berhasil dibuat. Password otomatis:</div>
                <div className="font-mono text-2xl font-bold text-[#00A0A0] bg-[#E6F6F6] rounded-md py-3" data-testid="generated-password">{genPw}</div>
                <p className="text-xs text-slate-400 mt-3">Catat password ini dan sampaikan kepada user.</p>
                <button onClick={() => setModal(false)} className="mt-4 bg-[#00A0A0] text-white px-5 py-2 rounded-md text-sm">Selesai</button>
              </div>
            ) : (
              <form onSubmit={submit} className="p-6 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-xs font-semibold text-slate-500">Nama</label><input className={inp} value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} required data-testid="uf-nama" /></div>
                  <div><label className="text-xs font-semibold text-slate-500">NIP</label><input className={`${inp} ${editingId ? "bg-slate-100 text-slate-500" : ""}`} value={form.nip} onChange={(e) => setForm({ ...form, nip: e.target.value })} required disabled={!!editingId} data-testid="uf-nip" /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-xs font-semibold text-slate-500">Role</label>
                    <select className={`${inp} ${editingId ? "bg-slate-100 text-slate-500" : ""}`} value={form.role} disabled={!!editingId} onChange={(e) => setForm({ ...form, role: e.target.value, area: "", region: "", limit_pemutus: 0 })} data-testid="uf-role">
                      {roleOptions.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                  <div><label className="text-xs font-semibold text-slate-500">Jabatan (opsional)</label><input className={inp} value={form.jabatan} onChange={(e) => setForm({ ...form, jabatan: e.target.value })} /></div>
                </div>

                {form.role === "RCRM" && (
                  <div><label className="text-xs font-semibold text-slate-500">Region</label>
                    <select className={inp} value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} required data-testid="uf-region">
                      <option value="">Pilih Region</option>{regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
                    </select>
                  </div>
                )}
                {(form.role === "RCO" || form.role === "ACRM") && (
                  <div className="grid grid-cols-2 gap-3">
                    <div><label className="text-xs font-semibold text-slate-500">Region</label>
                      <select className={inp} value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value, area: "" })} required data-testid="uf-region">
                        <option value="">Pilih Region</option>{regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
                      </select>
                    </div>
                    <div><label className="text-xs font-semibold text-slate-500">Area</label>
                      <select className={inp} value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} required data-testid="uf-area">
                        <option value="">Pilih Area</option>{areas.map((a) => <option key={a.id} value={a.nama}>{a.nama}</option>)}
                      </select>
                    </div>
                  </div>
                )}
                {(form.role === "ACRM" || form.role === "RCRM") && (
                  <div><label className="text-xs font-semibold text-slate-500">Limit Kewenangan Pemutus (Rp)</label>
                    <input className={inp} value={formatNumberInput(form.limit_pemutus)} onChange={(e) => setForm({ ...form, limit_pemutus: parseNumber(e.target.value) })} required data-testid="uf-limit" />
                  </div>
                )}
                {editingId && (
                  <div><label className="text-xs font-semibold text-slate-500">Status</label>
                    <select className={inp} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} data-testid="uf-status">
                      <option value="aktif">Aktif</option>
                      <option value="nonaktif">Nonaktif</option>
                    </select>
                  </div>
                )}
                <button className="w-full bg-[#00A0A0] hover:bg-[#008888] text-white font-semibold py-2.5 rounded-md text-sm mt-2" data-testid="uf-submit">{editingId ? "Simpan Perubahan" : "Simpan User"}</button>
              </form>
            )}
          </div>
        </div>
      )}

      {histUser && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setHistUser(null)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()} data-testid="history-modal">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div>
                <h3 className="font-display font-bold text-lg flex items-center gap-2"><History size={18} className="text-[#00A0A0]" /> Riwayat Perubahan</h3>
                <p className="text-xs text-slate-500 mt-0.5">{histUser.nama} — NIP {histUser.nip}</p>
              </div>
              <button onClick={() => setHistUser(null)}><X size={20} className="text-slate-400" /></button>
            </div>
            <div className="p-6 overflow-y-auto">
              {histData === null ? (
                <div className="flex justify-center py-10"><Loader2 className="animate-spin text-[#00A0A0]" size={26} /></div>
              ) : histData.length === 0 ? (
                <div className="text-center text-slate-400 py-10">Belum ada riwayat perubahan untuk user ini</div>
              ) : (
                <ol className="relative border-l-2 border-slate-100 ml-2">
                  {histData.map((log) => {
                    const changes = changeList(log);
                    return (
                      <li key={log.id} className="mb-5 ml-4" data-testid="history-item">
                        <span className="absolute -left-[7px] w-3 h-3 rounded-full bg-[#00A0A0] border-2 border-white" />
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#E6F6F6] text-[#00A0A0]">{ACTION_LABEL[log.action] || log.action}</span>
                          <span className="text-xs text-slate-400">{fmtDate(log.created_at)}</span>
                        </div>
                        <div className="text-sm text-slate-700 mt-1">oleh <span className="font-medium">{log.nama}</span> <span className="text-slate-400">(NIP {log.nip})</span></div>
                        {log.action === "update_user" && (
                          changes.length > 0 ? (
                            <div className="mt-2 space-y-1">
                              {changes.map((c, i) => (
                                <div key={i} className="text-xs bg-slate-50 rounded-md px-3 py-1.5 border border-slate-100">
                                  <span className="font-semibold text-slate-600">{c.field}:</span>{" "}
                                  <span className="text-red-500 line-through">{c.from}</span>{" "}
                                  <span className="text-slate-400">&rarr;</span>{" "}
                                  <span className="text-emerald-600 font-medium">{c.to}</span>
                                </div>
                              ))}
                            </div>
                          ) : <div className="mt-1 text-xs text-slate-400 italic">Tidak ada perubahan field yang tercatat</div>
                        )}
                      </li>
                    );
                  })}
                </ol>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
