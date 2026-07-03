"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { API_BASE } from "@/lib/types";

export default function LogsPage() {
  const [lines, setLines] = useState<string[]>([]);
  const [file, setFile] = useState("");

  useEffect(() => {
    const load = () => {
      fetch(`${API_BASE}/api/history?lines=80`)
        .then((r) => r.json())
        .then((d) => {
          setLines(d.lines || []);
          setFile(d.file || "");
        })
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <Card title={`JSONL tail ${file ? `— ${file}` : ""}`}>
      <pre className="max-h-[70vh] overflow-auto rounded-lg bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-300">
        {lines.length ? lines.join("\n") : "No log lines yet. Start PiMonitor with simulator or connect Control Hub."}
      </pre>
    </Card>
  );
}
