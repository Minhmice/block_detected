"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Real-time Detection" },
  { href: "/calibration", label: "Calibration" },
  { href: "/datasets", label: "Datasets" },
  { href: "/analysis", label: "Analysis" },
  { href: "/system", label: "System" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-outline-variant bg-surface-container-lowest md:flex">
      <nav className="flex flex-col gap-1 p-3">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded px-3 py-2 text-sm ${
                active
                  ? "border-l-4 border-primary bg-surface-container pl-2 text-primary"
                  : "text-on-surface-variant hover:bg-surface-container"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
