import { useEffect, useState, useCallback } from "react";
import api, { apiError } from "@/lib/api";
import { rp, fmtDate } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Check, X } from "lucide-react";

const TYPE_LABEL = {
  CREATE: "Input Perkara Baru",
  EDIT: "Edit Data Perkara",
  DELETE_NONAKTIF: "Nonaktifkan Perkara",
  DELETE_PERMANENT: "Hapus Permanen",
};

const statusBadge = (s) =>
  s === "MENUNGGU" ? <Badge className="bg-gold text-slate-900 hover:bg-gold">Menunggu Approval</Badge>
    : s === "APPROVED" ? <Badge className="bg-toska hover:bg-toska">Approved</Badge>
    : <Badge variant="destructive">Rejected</Badge>;

export default function Approvals() {
  const { isDeptHead } = useAuth();
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("MENUNGGU");
  const [target, setTarget] = useState(null);
  const [action, setAction] = useState(null);
  const [catatan, setCatatan] = useState("");
  const [alasan, setAlasan] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    const params = tab === "SEMUA" ? {} : { status: tab };
    api.get("/approvals", { params }).then((r) => setItems(r.data));
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  const doApprove = async () => {
    setBusy(true);
    try {
      await api.post(`/approvals/${target.id}/approve`, { catatan });
      toast.success("Request disetujui");
      setTarget(null); setAction(null); setCatatan("");
      load();
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const doReject = async () => {
    if (!alasan.trim()) { toast.error("Alasan reject wajib diisi"); return; }
    setBusy(true);
    try {
      await api.post(`/approvals/${target.id}/reject`, { alasan_reject: alasan });
      toast.success("Request ditolak");
      setTarget(null); setAction(null); setAlasan("");
      load();
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const payloadSummary = (r) => {
    if (!r.payload || !Object.keys(r.payload).length) return null;
    const p = r.payload;
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm mt-3 bg-slate-50 border border-slate-200 rounded-md p-3">
        <div><span className="text-slate-500">Region/Area/Cabang:</span><br />{p.region} / {p.area} / {p.cabang}</div>
        <div><span className="text-slate-500">Penggugat:</span><br />{(p.penggugat || []).join(", ") || "-"}</div>
        <div><span className="text-slate-500">Status Perkara:</span><br />{p.status_perkara}</div>
        <div><span className="text-slate-500">Total Kewajiban:</span><br />{rp(p.total_kewajiban)}</div>
      </div>
    );
  };

  return (
    <div data-testid="approval-page" className="space-y-5">
      <div>
        <h1 className="font-heading text-3xl font-bold text-slate-900 tracking-tight">Approval Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          {isDeptHead ? "Review dan proses seluruh perubahan data (maker-checker)" : "Status request perubahan yang Anda ajukan"}
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger data-testid="approval-tab-menunggu" value="MENUNGGU">Menunggu</TabsTrigger>
          <TabsTrigger data-testid="approval-tab-approved" value="APPROVED">Approved</TabsTrigger>
          <TabsTrigger data-testid="approval-tab-rejected" value="REJECTED">Rejected</TabsTrigger>
          <TabsTrigger data-testid="approval-tab-semua" value="SEMUA">Semua</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tipe Request</TableHead><TableHead>Nomor Perkara</TableHead>
              <TableHead>Diajukan Oleh</TableHead><TableHead>Tanggal</TableHead>
              <TableHead>Status</TableHead><TableHead>Approver</TableHead>
              {isDeptHead && <TableHead className="text-right">Aksi</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((r) => (
              <TableRow key={r.id} data-testid={`approval-row-${r.id}`}>
                <TableCell>
                  <Badge variant="outline" className={r.type.startsWith("DELETE") ? "border-red-400 text-red-600" : "border-toska text-toska-dark"}>
                    {TYPE_LABEL[r.type] || r.type}
                  </Badge>
                  {r.reason && <p className="text-xs text-slate-500 mt-1">Alasan: {r.reason}</p>}
                </TableCell>
                <TableCell className="font-medium text-slate-900">{r.case_nomor}</TableCell>
                <TableCell className="text-sm">{r.requested_by_nama}</TableCell>
                <TableCell className="text-sm">{fmtDate(r.requested_at)}</TableCell>
                <TableCell>
                  {statusBadge(r.status)}
                  {r.status === "REJECTED" && r.alasan_reject && (
                    <p className="text-xs text-red-600 mt-1">Alasan: {r.alasan_reject}</p>
                  )}
                  {r.status === "APPROVED" && r.catatan_approval && (
                    <p className="text-xs text-slate-500 mt-1">Catatan: {r.catatan_approval}</p>
                  )}
                </TableCell>
                <TableCell className="text-sm">
                  {r.approver || "-"}
                  {r.approved_at && <p className="text-xs text-slate-400">{fmtDate(r.approved_at)}</p>}
                </TableCell>
                {isDeptHead && (
                  <TableCell className="text-right whitespace-nowrap">
                    {r.status === "MENUNGGU" && (
                      <>
                        <Button data-testid={`approve-btn-${r.id}`} size="sm" className="bg-toska hover:bg-toska-hover text-white mr-2"
                          onClick={() => { setTarget(r); setAction("approve"); setCatatan(""); }}>
                          <Check className="h-4 w-4 mr-1" /> Approve
                        </Button>
                        <Button data-testid={`reject-btn-${r.id}`} size="sm" variant="outline" className="border-red-300 text-red-600 hover:bg-red-50"
                          onClick={() => { setTarget(r); setAction("reject"); setAlasan(""); }}>
                          <X className="h-4 w-4 mr-1" /> Reject
                        </Button>
                      </>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
            {items.length === 0 && (
              <TableRow><TableCell colSpan={isDeptHead ? 7 : 6} className="text-center text-sm text-slate-500 py-8">Tidak ada request.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!target} onOpenChange={() => { setTarget(null); setAction(null); }}>
        <DialogContent data-testid="approval-action-dialog">
          <DialogHeader>
            <DialogTitle>
              {action === "approve" ? "Approve Request" : "Reject Request"} — {target && TYPE_LABEL[target.type]}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-slate-600">Nomor Perkara: <span className="font-semibold text-slate-900">{target?.case_nomor}</span></p>
            {target?.reason && <p className="text-sm text-slate-600">Alasan pengajuan: {target.reason}</p>}
            {target && payloadSummary(target)}
            {action === "approve" ? (
              <div>
                <Label>Catatan Approval (opsional)</Label>
                <Textarea data-testid="approval-catatan-input" rows={3} value={catatan} onChange={(e) => setCatatan(e.target.value)} />
              </div>
            ) : (
              <div>
                <Label>Alasan Reject <span className="text-red-500">*</span></Label>
                <Textarea data-testid="reject-alasan-input" rows={3} value={alasan} onChange={(e) => setAlasan(e.target.value)} />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setTarget(null); setAction(null); }}>Batal</Button>
            {action === "approve" ? (
              <Button data-testid="confirm-approve-button" className="bg-toska hover:bg-toska-hover text-white" disabled={busy} onClick={doApprove}>Approve</Button>
            ) : (
              <Button data-testid="confirm-reject-button" variant="destructive" disabled={busy} onClick={doReject}>Reject</Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
