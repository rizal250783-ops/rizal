export function PageHeader({ title, subtitle, icon: Icon, action }) {
  return (
    <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="w-10 h-10 rounded-lg bg-[#E6F6F6] flex items-center justify-center">
            <Icon size={20} className="text-[#00A0A0]" />
          </div>
        )}
        <div>
          <h1 className="font-display font-bold text-xl md:text-2xl text-slate-900 tracking-tight">{title}</h1>
          {subtitle && <p className="text-slate-500 text-sm mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}
