import "./globals.css";
import { NavLink } from "@/components/ui";
import { EmergencyStopButton } from "@/components/EmergencyStopButton";

export const metadata = {
  title: "Control DriveHub Monitor",
  description: "REV Control Hub / Driver Hub realtime telemetry",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-surface text-slate-100 antialiased">
        <header className="border-b border-slate-800 bg-panel/80 backdrop-blur">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">FTC Pi Monitor</p>
              <h1 className="text-xl font-semibold">Control DriveHub</h1>
            </div>
            <nav className="flex flex-wrap items-center gap-1">
              <NavLink href="/" label="Overview" />
              <NavLink href="/motors" label="Motors" />
              <NavLink href="/gamepads" label="Gamepads" />
              <NavLink href="/logs" label="Logs" />
            </nav>
            <EmergencyStopButton />
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
