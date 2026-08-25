import { useEffect, useState } from "react";
import api, { apiError } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { UserPlus, Loader2 } from "lucide-react";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ username: "", password: "", nama: "" });
  const [loading, setLoading] = useState(false);

  const load = () => api.get("/users").then((r) => setUsers(r.data));
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/users", form);
      toast.success(`User ${form.username} berhasil dibuat`);
      setForm({ username: "", password: "", nama: "" });
      load();
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  const toggle = async (u, aktif) => {
    try {
      await api.patch(`/users/${u.id}/status`, { aktif });
      toast.success(`User ${u.username} ${aktif ? "diaktifkan" : "dinonaktifkan"}`);
      load();
    } catch (err) {
      toast.error(apiError(err));
    }
  };

  return (
    <div data-testid="users-page" className="space-y-5 max-w-5xl">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">User Management</h1>
        <p className="text-sm text-slate-500 mt-1">Kelola user Admin Legal — khusus Dept Head Legal Perdata</p>
      </div>

      <form onSubmit={submit} className="bg-white border border-slate-200 rounded-md p-5">
        <p className="text-xs uppercase tracking-widest text-slate-500 font-medium mb-4">Tambah User Admin Legal</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div>
            <Label>Username</Label>
            <Input data-testid="new-user-username" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
          </div>
          <div>
            <Label>Password</Label>
            <Input data-testid="new-user-password" type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required />
          </div>
          <div>
            <Label>Nama User</Label>
            <Input data-testid="new-user-nama" value={form.nama} onChange={(e) => setForm((f) => ({ ...f, nama: e.target.value }))} required />
          </div>
          <Button data-testid="add-user-button" type="submit" className="bg-toska hover:bg-toska-hover text-white" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UserPlus className="h-4 w-4 mr-2" />}
            Tambah User
          </Button>
        </div>
      </form>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Username</TableHead><TableHead>Nama</TableHead><TableHead>Role</TableHead>
              <TableHead>Status</TableHead><TableHead>Dibuat</TableHead><TableHead className="text-right">Aktif / Non Aktif</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} data-testid={`user-row-${u.username}`}>
                <TableCell className="font-medium text-slate-900">{u.username}</TableCell>
                <TableCell className="text-sm">{u.nama}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={u.role === "dept_head" ? "border-gold text-gold-hover" : "border-toska text-toska-dark"}>
                    {u.role === "dept_head" ? "Dept Head" : "Admin Legal"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={u.aktif ? "default" : "secondary"} className={u.aktif ? "bg-toska hover:bg-toska" : ""}>
                    {u.aktif ? "Aktif" : "Non Aktif"}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">{fmtDate(u.created_at)}</TableCell>
                <TableCell className="text-right">
                  {u.role !== "dept_head" && (
                    <Switch data-testid={`toggle-user-${u.username}`} checked={u.aktif} onCheckedChange={(v) => toggle(u, v)} />
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
