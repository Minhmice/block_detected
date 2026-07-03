"use client";

import { Card } from "@/components/ui";
import { useTelemetry } from "@/lib/ws";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function MotorsPage() {
  const { frame } = useTelemetry();
  const motors = frame?.motors ?? [];

  return (
    <div className="grid gap-4">
      <Card title="Motor power">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={motors}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis domain={[-1, 1]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#1a2332", border: "1px solid #334155" }} />
            <Bar dataKey="power" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {motors.map((m) => (
          <Card key={m.name} title={m.name}>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <div><dt className="text-slate-500">Encoder</dt><dd className="font-mono">{m.encoder}</dd></div>
              <div><dt className="text-slate-500">Velocity</dt><dd className="font-mono">{m.velocity.toFixed(1)}</dd></div>
              <div><dt className="text-slate-500">Current</dt><dd className="font-mono">{m.current.toFixed(2)} A</dd></div>
              <div><dt className="text-slate-500">Mode</dt><dd className="font-mono text-xs">{m.mode}</dd></div>
            </dl>
          </Card>
        ))}
      </div>
    </div>
  );
}
