export function Marquee({ text, className = "" }) {
  return (
    <div className={`marquee ${className}`} data-testid="tagline-marquee" aria-label={text}>
      <div className="marquee__inner">
        <span className="mx-8">✦ {text}</span>
        <span className="mx-8">✦ {text}</span>
        <span className="mx-8">✦ {text}</span>
      </div>
    </div>
  );
}

export function BsiLogo({ size = "md", inverse = false }) {
  const dim = size === "lg" ? "text-3xl" : size === "sm" ? "text-lg" : "text-2xl";
  return (
    <div className="flex items-center gap-2 select-none">
      <div className="relative">
        <span className={`font-display font-extrabold tracking-tight ${dim} ${inverse ? "text-white" : "text-[#00A0A0]"}`}>
          BSI
        </span>
        <span className="absolute -top-1.5 -right-2 text-[#F0B43C] text-xs">✦</span>
      </div>
      {size !== "sm" && (
        <div className={`leading-none ${inverse ? "text-white/90" : "text-slate-500"}`}>
          <div className="text-[10px] font-semibold tracking-wider">BANK SYARIAH</div>
          <div className="text-[10px] font-semibold tracking-wider">INDONESIA</div>
        </div>
      )}
    </div>
  );
}
