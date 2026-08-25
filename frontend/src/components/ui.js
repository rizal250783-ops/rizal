import React, { useEffect } from "react";
import { X } from "lucide-react";

export function Modal({ open, onClose, title, children, testid }) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
      const onKey = (e) => { if (e.key === "Escape") onClose?.(); };
      window.addEventListener("keydown", onKey);
      return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      data-testid={testid || "modal"}
    >
      <div
        className="absolute inset-0 bg-navy/60 backdrop-blur-sm"
        onClick={onClose}
        data-testid="modal-overlay"
      />
      <div className="relative z-10 w-full sm:max-w-lg bg-white rounded-t-3xl sm:rounded-2xl shadow-xl max-h-[92vh] overflow-y-auto fade-up">
        <div className="sticky top-0 flex items-center justify-between px-6 py-4 bg-white border-b border-slate-100">
          <h3 className="text-lg font-heading font-bold text-navy">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-slate-100 text-slate-500 transition-colors duration-200"
            data-testid="modal-close-btn"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

export function Badge({ variant = "neutral", children, testid }) {
  const styles = {
    success: "bg-emerald-100 text-emerald-800 border border-emerald-300",
    danger: "bg-rose-100 text-rose-800 border border-rose-300",
    neutral: "bg-slate-100 text-slate-600 border border-slate-200",
    gold: "bg-gold/15 text-gold-dark border border-gold/40",
  };
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${styles[variant]}`}
    >
      {children}
    </span>
  );
}

export function Field({ label, children }) {
  return (
    <label className="block mb-4">
      <span className="block mb-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-navy focus:outline-none focus:ring-2 focus:ring-gold focus:border-transparent transition-all duration-200";
