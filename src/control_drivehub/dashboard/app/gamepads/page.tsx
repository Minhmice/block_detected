"use client";

import { Card } from "@/components/ui";
import { useTelemetry } from "@/lib/ws";

function Stick({ x, y, label }: { x: number; y: number; label: string }) {
  const size = 160;
  const cx = size / 2 + x * (size / 2 - 12);
  const cy = size / 2 - y * (size / 2 - 12);
  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <svg width={size} height={size} className="rounded-full bg-slate-900">
        <circle cx={size / 2} cy={size / 2} r={size / 2 - 8} fill="none" stroke="#334155" strokeWidth="2" />
        <line x1={size / 2} y1={8} x2={size / 2} y2={size - 8} stroke="#334155" />
        <line x1={8} y1={size / 2} x2={size - 8} y2={size / 2} stroke="#334155" />
        <circle cx={cx} cy={cy} r={10} fill="#3b82f6" />
      </svg>
      <p className="font-mono text-xs text-slate-400">
        {x.toFixed(2)}, {y.toFixed(2)}
      </p>
    </div>
  );
}

function Buttons({ gp }: { gp: Record<string, boolean | number> }) {
  const keys = ["a", "b", "x", "y", "dpad_up", "dpad_down", "dpad_left", "dpad_right"];
  return (
    <div className="flex flex-wrap gap-2">
      {keys.map((k) => (
        <span
          key={k}
          className={`rounded px-2 py-1 text-xs font-mono ${gp[k] ? "bg-accent text-white" : "bg-slate-800 text-slate-500"}`}
        >
          {k}
        </span>
      ))}
    </div>
  );
}

export default function GamepadsPage() {
  const { frame } = useTelemetry();
  const gp1 = frame?.gamepad1;
  const gp2 = frame?.gamepad2;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Gamepad 1">
        {gp1 ? (
          <>
            <div className="flex justify-around py-4">
              <Stick x={gp1.left_stick_x} y={gp1.left_stick_y} label="Left" />
              <Stick x={gp1.right_stick_x} y={gp1.right_stick_y} label="Right" />
            </div>
            <p className="mb-2 text-xs text-slate-500">
              Triggers: L {gp1.left_trigger.toFixed(2)} / R {gp1.right_trigger.toFixed(2)}
            </p>
            <Buttons gp={gp1 as unknown as Record<string, boolean | number>} />
          </>
        ) : (
          <p className="text-slate-500">No data</p>
        )}
      </Card>
      <Card title="Gamepad 2">
        {gp2 ? (
          <>
            <div className="flex justify-around py-4">
              <Stick x={gp2.left_stick_x} y={gp2.left_stick_y} label="Left" />
              <Stick x={gp2.right_stick_x} y={gp2.right_stick_y} label="Right" />
            </div>
            <Buttons gp={gp2 as unknown as Record<string, boolean | number>} />
          </>
        ) : (
          <p className="text-slate-500">No data</p>
        )}
      </Card>
    </div>
  );
}
