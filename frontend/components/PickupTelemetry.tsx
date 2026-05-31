"use client";

import { useVisionStore } from "@/stores/useVisionStore";

export function PickupTelemetry() {
  const latestResult = useVisionStore((s) => s.latestResult);
  const pose = latestResult?.pickupPoseMm;

  return (
    <div className="panel h-64 p-container-padding font-mono text-sm">
      <h2 className="label-caps mb-3 text-primary">PICKUP_TELEMETRY</h2>
      {!pose ? (
        <p className="text-on-surface-variant">DRY-RUN — no pickup pose</p>
      ) : (
        <dl className="grid grid-cols-2 gap-2">
          <dt className="label-caps">X_MM</dt>
          <dd>{pose.xMm.toFixed(2)}</dd>
          <dt className="label-caps">Y_MM</dt>
          <dd>{pose.yMm.toFixed(2)}</dd>
          <dt className="label-caps">THETA</dt>
          <dd>{pose.thetaDeg.toFixed(2)}°</dd>
        </dl>
      )}
    </div>
  );
}
