import clsx from "clsx";

export function Badge({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: "ok" | "warn" | "danger" | "neutral";
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        tone === "ok" && "bg-emerald-500/20 text-emerald-300",
        tone === "warn" && "bg-amber-500/20 text-amber-300",
        tone === "danger" && "bg-red-500/20 text-red-300",
        tone === "neutral" && "bg-slate-500/20 text-slate-300",
      )}
    >
      {label}
    </span>
  );
}

export function Card({
  title,
  children,
  className,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("rounded-xl border border-slate-700/60 bg-panel p-4 shadow-lg", className)}>
      {title ? <h3 className="mb-3 text-sm font-medium text-slate-300">{title}</h3> : null}
      {children}
    </div>
  );
}

export function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white"
    >
      {label}
    </a>
  );
}
