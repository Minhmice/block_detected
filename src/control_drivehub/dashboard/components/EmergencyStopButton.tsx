"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/types";

export function EmergencyStopButton() {
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/config`)
      .then((r) => r.json())
      .then((c) => setEnabled(Boolean(c?.commands?.enabled)))
      .catch(() => setEnabled(false));
  }, []);

  if (!enabled) return null;

  async function trigger() {
    setBusy(true);
    setMsg("");
    try {
      const res = await fetch(`${API_BASE}/api/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Command-Token": "change-me",
        },
        body: JSON.stringify({
          v: 1,
          type: "emergency_stop",
          token: "change-me",
          ts: Date.now(),
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        setMsg(err.detail || "failed");
      } else {
        setMsg("sent");
      }
    } catch {
      setMsg("network error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        disabled={busy}
        onClick={trigger}
        className="rounded-xl bg-red-600 px-6 py-3 text-sm font-bold uppercase tracking-wider text-white shadow-lg shadow-red-900/40 transition hover:bg-red-500 disabled:opacity-50"
      >
        Emergency Stop
      </button>
      {msg ? <span className="text-xs text-slate-400">{msg}</span> : null}
    </div>
  );
}
