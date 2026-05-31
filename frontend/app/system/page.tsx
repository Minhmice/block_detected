"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { getHealth } from "@/lib/api";
import type { SystemStatusWire } from "@/types/vision";

export default function SystemPage() {
  const [health, setHealth] = useState<SystemStatusWire | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <AppShell>
      <div className="panel space-y-2 p-6 font-mono text-sm">
        <h2 className="label-caps text-primary">System Status</h2>
        {!health ? (
          <p className="text-on-surface-variant">Unable to reach backend</p>
        ) : (
          Object.entries(health).map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4">
              <span className="label-caps">{k}</span>
              <span>{String(v)}</span>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
