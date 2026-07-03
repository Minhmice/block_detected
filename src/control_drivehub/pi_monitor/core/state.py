"""Shared telemetry state and connection tracking."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

from pi_monitor.core.schema import DashboardEnvelope, RobotState, TelemetryFrame


@dataclass
class TelemetryState:
    stale_timeout_sec: float = 1.0
    latest: TelemetryFrame | None = None
    last_received_at_ms: int | None = None
    hub_connected: bool = False
    dashboard_clients: set[Any] = field(default_factory=set)
    hub_socket: Any | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def is_stale(self, now_ms: int | None = None) -> bool:
        if self.last_received_at_ms is None:
            return True
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        return (now - self.last_received_at_ms) > int(self.stale_timeout_sec * 1000)

    async def ingest(self, payload: dict[str, Any]) -> TelemetryFrame:
        async with self._lock:
            received_at = int(time.time() * 1000)
            hub_ts = int(payload.get("ts_hub_ms", 0))
            latency_ms = None
            if hub_ts > 0:
                latency_ms = max(0.0, float(received_at - hub_ts))

            payload = dict(payload)
            payload["latency_ms"] = latency_ms
            payload["pi_connected"] = True
            frame = TelemetryFrame.model_validate(payload)
            self.latest = frame
            self.last_received_at_ms = received_at
            return frame

    def status_dict(self) -> dict[str, Any]:
        stale = self.is_stale()
        frame = self.latest
        return {
            "hub_connected": self.hub_connected,
            "dashboard_clients": len(self.dashboard_clients),
            "stale": stale,
            "last_seq": frame.seq if frame else None,
            "last_ts_hub_ms": frame.ts_hub_ms if frame else None,
            "latency_ms": frame.latency_ms if frame else None,
            "robot_state": frame.robot_state.value if frame else None,
            "driver_hub_connected": frame.driver_hub_connected if frame else None,
            "received_at_ms": self.last_received_at_ms,
        }

    def dashboard_envelope(self) -> DashboardEnvelope:
        return DashboardEnvelope(
            stale=self.is_stale(),
            received_at_ms=self.last_received_at_ms or 0,
            frame=self.latest,
        )

    async def broadcast_dashboard(self) -> None:
        envelope = self.dashboard_envelope()
        message = envelope.model_dump_json()
        dead: list[Any] = []
        for ws in list(self.dashboard_clients):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.dashboard_clients.discard(ws)

    async def send_command_to_hub(self, command: dict[str, Any]) -> bool:
        if self.hub_socket is None:
            return False
        try:
            await self.hub_socket.send_text(json.dumps(command, separators=(",", ":")))
            return True
        except Exception:
            return False
