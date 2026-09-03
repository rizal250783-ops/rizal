import React, { useEffect, useState } from "react";
import api, { apiErr } from "../lib/api";
import { ROLE_LABEL } from "../lib/utils";
import { Card, Button, Input, Select, Th, Td, Empty, Badge, SectionTitle } from "../components/ui";
import { UserPlus, KeyRound, Power, Trash2, Repeat, X } from "lucide-react";

const ROLES = ["direktur", "admin", "ao_lending", "ao_funding", "pic_remedial"];

export default function Users() {
  const [rows, setRows] = useState([]);
  const [modal, setModal] = useState(null); // {type:'create'|'role', user}
  const [notice, setNotice] = useState("");

  const load = () => api.get("/users").then((r) => setRows(r.data));
  useEffect(() => { load(); }, []);

  const toggle = async (u) => { await api.post(`/users/${u.id}/status?active=${!u.is_active}`); load(); };
  const del = async (u) => { if (window.confirm(`Hapus user ${u.name}?`)) { await api.delete(`/users/${u.id}`); load(); } };
  const reset = async (u) => {
    const { data } = await api.post(`/users/${u.id}/reset-password`);
    setNotice(`Password sementara untuk ${u.name}: ${data.temp_password} (wajib ganti saat login)`);
    load();
  };

  return (
    <div className="space-y-5">
      {notice && <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-800 flex justify-between" data-testid="user-notice"><span>{notice}</span><button onClick={() => setNotice("")}><X size={16} /></button></div>}
      <div className="flex items-center justify-between">
        <SectionTitle sub="Tambah, edit, nonaktifkan, hapus, dan pindah jabatan">Manajemen User</SectionTitle>
        <Button onClick={() => setModal({ type: "create" })} data-testid="add-user-btn"><UserPlus size={16} /> Tambah User</Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200"><tr><Th>Nama</Th><Th>Email</Th><Th>Role</Th><Th>Status</Th><Th>Aksi</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((u) => (
                <tr key={u.id} data-testid={`user-row-${u.id}`}>
                  <Td className="font-medium text-slate-900">{u.name}</Td>
                  <Td className="text-xs text-slate-500">{u.email}</Td>
                  <Td><Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{ROLE_LABEL[u.role]}</Badge></Td>
                  <Td><Badge className={u.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-500 border-slate-200"}>{u.is_active ? "Aktif" : "Nonaktif"}</Badge></Td>
                  <Td>
                    <div className="flex gap-1">
                      <button title="Pindah jabatan" onClick={() => setModal({ type: "role", user: u })} className="text-slate-500 hover:bg-slate-100 rounded p-1.5" data-testid={`role-${u.id}`}><Repeat size={16} /></button>
                      <button title="Reset password" onClick={() => reset(u)} className="text-gold-600 hover:bg-gold-100 rounded p-1.5" data-testid={`reset-${u.id}`}><KeyRound size={16} /></button>
                      <button title={u.is_active ? "Nonaktifkan" : "Aktifkan"} onClick={() => toggle(u)} className="text-blue-600 hover:bg-blue-50 rounded p-1.5" data-testid={`toggle-${u.id}`}><Power size={16} /></button>
                      <button title="Hapus" onClick={() => del(u)} className="text-red-600 hover:bg-red-50 rounded p-1.5" data-testid={`delete-${u.id}`}><Trash2 size={16} /></button>
                    </div>
                  </Td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={5}><Empty>Belum ada user.</Empty></td></tr>}
            </tbody>
          </table>
        </div>
      </Card>

      {modal?.type === "create" && <CreateModal onClose={() => { setModal(null); load(); }} onTemp={setNotice} />}
      {modal?.type === "role" && <RoleModal user={modal.user} onClose={() => { setModal(null); load(); }} />}
    </div>
  );
}

function CreateModal({ onClose, onTemp }) {
  const [f, setF] = useState({ name: "", email: "", role: "ao_lending", password: "" });
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try {
      const body = { ...f };
      if (!body.password) delete body.password;
      const { data } = await api.post("/users", body);
      if (data.temp_password) onTemp(`Password sementara untuk ${data.name}: ${data.temp_password}`);
      onClose();
    } catch (e2) { setErr(apiErr(e2)); }
  };
  return (
    <Modal title="Tambah User" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Input placeholder="Nama lengkap" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required data-testid="nu-name" />
        <Input type="email" placeholder="Email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required data-testid="nu-email" />
        <Select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} data-testid="nu-role">
          {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
        </Select>
        <Input type="text" placeholder="Password (kosongkan = generate sementara)" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} data-testid="nu-password" />
        <p className="text-xs text-slate-400">Min 8 karakter, kombinasi huruf & angka.</p>
        {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
        <div className="flex gap-2"><Button type="button" variant="outline" onClick={onClose} className="flex-1">Batal</Button><Button type="submit" className="flex-1" data-testid="nu-submit">Simpan</Button></div>
      </form>
    </Modal>
  );
}

function RoleModal({ user, onClose }) {
  const [role, setRole] = useState(user.role);
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try { await api.post(`/users/${user.id}/change-role`, { new_role: role }); onClose(); }
    catch (e2) { setErr(apiErr(e2)); }
  };
  return (
    <Modal title={`Pindah Jabatan · ${user.name}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <div className="text-sm text-slate-600">Role saat ini: <b>{ROLE_LABEL[user.role]}</b></div>
        <Select value={role} onChange={(e) => setRole(e.target.value)} data-testid="cr-role">
          {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
        </Select>
        <p className="text-xs text-slate-400">Perubahan tersimpan sebagai histori (role lama, role baru, tanggal, admin pelaku).</p>
        {err && <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{err}</div>}
        <div className="flex gap-2"><Button type="button" variant="outline" onClick={onClose} className="flex-1">Batal</Button><Button type="submit" className="flex-1" data-testid="cr-submit">Simpan</Button></div>
      </form>
    </Modal>
  );
}

export function Modal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="card w-full max-w-md p-6" data-testid="modal">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-lg font-bold text-slate-900">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}
