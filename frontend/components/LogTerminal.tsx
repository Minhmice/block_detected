"use client";

import { useEffect, useRef } from "react";

import { useVisionStore } from "@/stores/useVisionStore";

const LEVEL_CLASS: Record<string, string> = {
  WS: "text-primary",
  API: "text-secondary",
  ERR: "text-error",
};

export function LogTerminal() {
  const open = useVisionStore((s) => s.logTerminalOpen);
  const setOpen = useVisionStore((s) => s.setLogTerminalOpen);
  const logs = useVisionStore((s) => s.logs);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs, open]);

  if (!open) return null;

  return (
    <div className="fixed bottom-0 right-0 z-50 flex h-48 w-full flex-col border-t border-outline-variant bg-surface-container-lowest lg:w-96">
      <div className="flex items-center justify-between border-b border-outline-variant px-3 py-1">
        <span className="label-caps">Event Log</span>
        <button type="button" onClick={() => setOpen(false)}>
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 font-mono text-xs">
        {logs.length === 0 ? (
          <p className="text-on-surface-variant">
            &gt; Log terminal ready — waiting for events
          </p>
        ) : (
          logs.map((line) => (
            <div
              key={line.id}
              className={LEVEL_CLASS[line.level] ?? "text-on-surface"}
            >
              [{line.level}] {line.message}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
