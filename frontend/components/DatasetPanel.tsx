"use client";

import { postDatasetSaveFrame } from "@/lib/api";
import { useVisionStore } from "@/stores/useVisionStore";

export function DatasetPanel() {
  const entries = useVisionStore((s) => s.datasetEntries);
  const appendLog = useVisionStore((s) => s.appendLog);
  const addDatasetEntry = useVisionStore((s) => s.addDatasetEntry);

  async function capture(label: string) {
    try {
      const res = await postDatasetSaveFrame({ reason: label });
      appendLog("API", `Dataset capture ${res.path ?? ""}`);
      if (res.path) {
        addDatasetEntry({ ts: Date.now(), path: res.path, reason: label });
      }
    } catch (err) {
      appendLog("ERR", `Dataset capture failed: ${String(err)}`);
    }
  }

  return (
    <div className="panel flex flex-col gap-4 p-container-padding">
      <h2 className="label-caps text-primary">Dataset</h2>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded border border-outline-variant px-3 py-1"
          onClick={() => capture("quick_capture")}
        >
          Quick Capture
        </button>
        <button
          type="button"
          className="rounded border border-outline-variant px-3 py-1"
          onClick={() => capture("failed_frame")}
        >
          Save Failed Frame
        </button>
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          NO FRAMES SAVED THIS SESSION
        </p>
      ) : (
        <ul className="font-mono text-xs space-y-1">
          {entries.map((e) => (
            <li key={e.ts}>{e.path}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
