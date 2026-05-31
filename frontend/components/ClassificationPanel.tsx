"use client";

import { useVisionStore } from "@/stores/useVisionStore";

export function ClassificationPanel() {
  const scores = useVisionStore((s) => s.classificationScores);
  const latestResult = useVisionStore((s) => s.latestResult);

  const entries: { label: string; score: number }[] = scores
    ? [
        { label: "block01", score: scores.block01 },
        { label: "block02", score: scores.block02 },
        { label: "block03", score: scores.block03 },
        { label: "block04", score: scores.block04 },
      ]
    : [];

  return (
    <div className="panel h-64 p-container-padding">
      <h2 className="label-caps mb-3 text-primary">Classification</h2>
      {entries.length === 0 ? (
        <p className="text-sm text-on-surface-variant">Awaiting telemetry…</p>
      ) : (
        <ul className="space-y-2 font-mono text-sm">
          {entries.map(({ label, score }) => (
            <li key={label} className="flex items-center gap-2">
              <span className="w-16 uppercase">{label}</span>
              <div className="h-2 flex-1 rounded bg-surface-container-high">
                <div
                  className="h-2 rounded bg-primary"
                  style={{ width: `${Math.round(score * 100)}%` }}
                />
              </div>
              <span>{(score * 100).toFixed(0)}%</span>
            </li>
          ))}
        </ul>
      )}
      {latestResult?.blockId != null && (
        <p className="mt-4 font-mono text-secondary">
          Active block: {latestResult.blockId}
        </p>
      )}
    </div>
  );
}
