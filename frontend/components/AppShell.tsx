"use client";

import type { ReactNode } from "react";

import { Sidebar } from "@/components/Sidebar";
import { TopStatusBar } from "@/components/TopStatusBar";
import { LogTerminal } from "@/components/LogTerminal";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-surface-dim">
      <TopStatusBar />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-h-0 flex-1 overflow-auto p-gutter">{children}</main>
      </div>
      <LogTerminal />
    </div>
  );
}
