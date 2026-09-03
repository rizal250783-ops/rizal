import React from "react";

export function Card({ children, className = "", ...rest }) {
  return <div className={`card ${className}`} {...rest}>{children}</div>;
}

export function KpiCard({ label, value, sub, icon: Icon, tone = "emerald", testid }) {
  const tones = {
    emerald: "text-emerald-700 bg-emerald-50",
    gold: "text-gold-700 bg-gold-100",
    slate: "text-slate-700 bg-slate-100",
    red: "text-red-700 bg-red-50",
  };
  return (
    <div className="card p-5 fade-up" data-testid={testid}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</div>
          <div className="mt-2 text-2xl font-bold font-num tracking-tight text-slate-900">{value}</div>
          {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
        </div>
        {Icon && <div className={`rounded-lg p-2.5 ${tones[tone]}`}><Icon size={20} /></div>}
      </div>
    </div>
  );
}

export function Badge({ children, className = "", testid }) {
  return (
    <span data-testid={testid}
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}

export function Button({ children, variant = "primary", className = "", ...rest }) {
  const v = {
    primary: "bg-emerald-700 hover:bg-emerald-800 text-white",
    gold: "bg-gold-600 hover:bg-gold-700 text-white",
    outline: "border border-slate-300 bg-white hover:bg-slate-50 text-slate-700",
    ghost: "hover:bg-slate-100 text-slate-600",
    danger: "bg-red-600 hover:bg-red-700 text-white",
  };
  return (
    <button className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors focus-ring disabled:opacity-50 ${v[variant]} ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function Input({ className = "", ...rest }) {
  return <input className={`w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus-ring placeholder:text-slate-400 ${className}`} {...rest} />;
}

export function Select({ className = "", children, ...rest }) {
  return <select className={`w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus-ring ${className}`} {...rest}>{children}</select>;
}

export function Th({ children, className = "" }) {
  return <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 ${className}`}>{children}</th>;
}
export function Td({ children, className = "" }) {
  return <td className={`px-4 py-3 text-sm text-slate-700 ${className}`}>{children}</td>;
}

export function SectionTitle({ children, sub }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold text-slate-900 font-heading">{children}</h2>
      {sub && <p className="text-sm text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export function Empty({ children }) {
  return <div className="py-10 text-center text-sm text-slate-400">{children}</div>;
}
