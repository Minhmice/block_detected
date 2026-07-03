"use client";

import { Badge, Card } from "@/components/ui";
import { Sparkline } from "@/components/Sparkline";
import { useTelemetry } from "@/lib/ws";

function stateTone(state: string | undefined): "ok" | "warn" | "danger" | "neutral" {
  if (state === "RUNNING") return "ok";
  if (state === "INIT") return "warn";
  if (state === "STOPPED") return "danger";
  return "neutral";
}

export default function OverviewPage() {
  const { frame, stale, connected, history } = useTelemetry();
  const latencyData = history.map((h, i) => ({ i, latency: h.latency }));
  const loopData = history.map((h, i) => ({ i, loop: h.loop }));

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card title="Robot state" className="lg:col-span-1">
        <div className="flex flex-wrap gap-2">
          <Badge label={frame?.robot_state ?? "NO DATA"} tone={stateTone(frame?.robot_state)} />
          <Badge
            label={frame?.driver_hub_connected ? "Driver Hub OK" : "Driver Hub ?"}
            tone={frame?.driver_hub_connected ? "ok" : "warn"}
          />
          <Badge label={connected ? "Dashboard WS" : "Dashboard WS down"} tone={connected ? "ok" : "danger"} />
          <Badge label={stale ? "STALE" : "LIVE"} tone={stale ? "danger" : "ok"} />
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-slate-500">Seq</dt>
            <dd className="font-mono text-lg">{frame?.seq ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Latency</dt>
            <dd className="font-mono text-lg">{frame?.latency_ms?.toFixed(1) ?? "—"} ms</dd>
          </div>
          <div>
            <dt className="text-slate-500">Loop</dt>
            <dd className="font-mono text-lg">{frame?.loop_time_ms?.toFixed(1) ?? "—"} ms</dd>
          </div>
          <div>
            <dt className="text-slate-500">Battery</dt>
            <dd className="font-mono text-lg">{frame?.battery_v?.toFixed(2) ?? "—"} V</dd>
          </div>
        </dl>
      </Card>

      <Card title="Latency (ms)" className="lg:col-span-1">
        <Sparkline data={latencyData} dataKey="latency" color="#3b82f6" />
      </Card>

      <Card title="Loop time (ms)" className="lg:col-span-1">
        <Sparkline data={loopData} dataKey="loop" color="#22c55e" />
      </Card>

      <Card title="IMU" className="lg:col-span-3">
        <div className="grid grid-cols-3 gap-4 text-center">
          {(["yaw", "pitch", "roll"] as const).map((k) => (
            <div key={k} className="rounded-lg bg-slate-900/60 p-4">
              <p className="text-xs uppercase text-slate-500">{k}</p>
              <p className="font-mono text-2xl">{frame?.imu?.[k]?.toFixed(1) ?? "—"}°</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
