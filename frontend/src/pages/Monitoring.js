import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api, { API } from "../lib/api";
import { PageHeader } from "../components/PageHeader";
import { formatRupiah, formatRupiahShort } from "../lib/format";
import { BarChart3, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend } from "recharts";

const COLORS = ["#00A0A0", "#F0B43C"];

export default function Monitoring() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [regions, setRegions] = useState([]);
  const [areas, setAreas] = useState([]);
  const [filters, setFilters] = useState({ region: "", area: "", segmen: "", produk: "", kolektibilitas: "", status: "" });
  const [ref, setRef] = useState(null);

  const load = () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    api.get("/monitoring", { params }).then((r) => setData(r.data)).catch(() => {});
  };

  useEffect(() => {
    api.get("/reference").then((r) => setRef(r.data));
    if (user.role === "RCG") api.get("/regions").then((r) => setRegions(r.data));
  }, []);
  useEffect(() => { load(); }, [filters]);
  useEffect(() => {
    if (filters.region) api.get("/areas", { params: { region: filters.region } }).then((r) => setAreas(r.data));
    else if (user.role === "RCG") setAreas([]);
  }, [filters.region]);

  const exportExcel = async () => {
    try {
      const token = localStorage.getItem("rcg_token");
      const p = new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString();
      const res = await fetch(`${API}/export/excel?${p}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Gagal export");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "Export_Nota_RCG.xlsx"; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { toast.error(e.message); }
  };

  const sel = "px-3 py-2 border border-slate-300 rounded-md text-sm bg-white outline-none focus:border-[#00A0A0]";

  return (
    <div>
      <PageHeader title="Monitoring Segmen & Produk" subtitle={user.role === "RCG" ? "Data Nasional" : `Region ${user.region}`} icon={BarChart3}
        action={<button onClick={exportExcel} data-testid="export-excel" className="bg-[#F0B43C] hover:bg-[#D9A236] text-white font-semibold px-4 py-2.5 rounded-md text-sm flex items-center gap-2"><Download size={16} /> Export Excel</button>} />

      {/* Filters */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 mb-4 flex flex-wrap gap-3">
        {user.role === "RCG" && (
          <select className={sel} data-testid="mon-region" value={filters.region} onChange={(e) => setFilters({ ...filters, region: e.target.value, area: "" })}>
            <option value="">Semua Region</option>
            {regions.map((r) => <option key={r.id} value={r.nama}>{r.nama}</option>)}
          </select>
        )}
        <select className={sel} data-testid="mon-area" value={filters.area} onChange={(e) => setFilters({ ...filters, area: e.target.value })}>
          <option value="">Semua Area</option>
          {areas.map((a) => <option key={a.id} value={a.nama}>{a.nama}</option>)}
        </select>
        <select className={sel} data-testid="mon-segmen" value={filters.segmen} onChange={(e) => setFilters({ ...filters, segmen: e.target.value, produk: "" })}>
          <option value="">Semua Segmen</option>
          {ref?.segmen.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className={sel} value={filters.produk} onChange={(e) => setFilters({ ...filters, produk: e.target.value })}>
          <option value="">Semua Produk</option>
          {filters.segmen && ref?.produk[filters.segmen]?.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select className={sel} value={filters.kolektibilitas} onChange={(e) => setFilters({ ...filters, kolektibilitas: e.target.value })}>
          <option value="">Semua Kol</option>
          {ref?.kolektibilitas.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
      </div>

      {!data ? <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#00A0A0]" size={30} /></div> : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
              <h3 className="font-display font-semibold text-slate-800 mb-4">Jumlah Loan per Segmen</h3>
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={data.per_segmen} dataKey="loan" nameKey="segmen" cx="50%" cy="50%" outerRadius={90} label>
                      {data.per_segmen.map((e, i) => <Cell key={i} fill={COLORS[i % 2]} />)}
                    </Pie>
                    <Tooltip /><Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
              <h3 className="font-display font-semibold text-slate-800 mb-4">Total Kewajiban per Produk</h3>
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={data.per_produk}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="produk" tick={{ fontSize: 10 }} />
                    <YAxis tickFormatter={formatRupiahShort} tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(v) => formatRupiah(v)} />
                    <Bar dataKey="kewajiban" fill="#00A0A0" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <MonTable title="Monitoring per Segmen" rows={data.per_segmen} keyCol="segmen" testid="table-segmen" />
          <MonTable title="Monitoring per Produk" rows={data.per_produk} keyCol="produk" extra="segmen" testid="table-produk" />
        </>
      )}
    </div>
  );
}

function MonTable({ title, rows, keyCol, extra, testid }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 mb-4" data-testid={testid}>
      <h3 className="font-display font-semibold text-slate-800 mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
              {extra && <th className="text-left font-semibold px-3 py-2">Segmen</th>}
              <th className="text-left font-semibold px-3 py-2">{keyCol}</th>
              <th className="text-right font-semibold px-3 py-2">Nota</th>
              <th className="text-right font-semibold px-3 py-2">Loan</th>
              <th className="text-right font-semibold px-3 py-2">OS Pokok</th>
              <th className="text-right font-semibold px-3 py-2">OS Margin</th>
              <th className="text-right font-semibold px-3 py-2">Penalty</th>
              <th className="text-right font-semibold px-3 py-2">Kewajiban</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/60">
                {extra && <td className="px-3 py-2 text-slate-500">{r[extra]}</td>}
                <td className="px-3 py-2 font-medium capitalize">{r[keyCol]}</td>
                <td className="px-3 py-2 text-right">{r.nota}</td>
                <td className="px-3 py-2 text-right">{r.loan}</td>
                <td className="px-3 py-2 text-right tabular-nums">{formatRupiah(r.os_pokok)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{formatRupiah(r.os_margin)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{formatRupiah(r.penalty)}</td>
                <td className="px-3 py-2 text-right tabular-nums font-medium">{formatRupiah(r.kewajiban)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
