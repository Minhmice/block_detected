"use client";

import { useVisionStore } from "@/stores/useVisionStore";
import type { DetectionTelemetryWire } from "@/types/vision";

let socket: WebSocket | null = null;
let reconnectAttempt = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

function wsUrl(): string {
  const url = process.env.NEXT_PUBLIC_WS_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_WS_URL is not configured");
  }
  return url;
}

function scheduleReconnect(): void {
  if (reconnectTimer) return;
  const delay = Math.min(1000 * 2 ** reconnectAttempt, 8000);
  reconnectAttempt += 1;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectDetectionWs();
  }, delay);
}

export function connectDetectionWs(): WebSocket | null {
  const store = useVisionStore.getState();
  try {
    store.setConnection("connecting");
    store.appendLog("WS", "Connecting telemetry channel…");
    socket?.close();
    socket = new WebSocket(wsUrl());
  } catch (err) {
    store.setConnection("error");
    store.appendLog("ERR", `WS config error: ${String(err)}`);
    return null;
  }

  socket.onopen = () => {
    reconnectAttempt = 0;
    useVisionStore.getState().setConnection("connected");
    useVisionStore.getState().appendLog("WS", "Telemetry connected");
  };

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data as string) as DetectionTelemetryWire;
      useVisionStore.getState().applyTelemetry(payload);
    } catch {
      useVisionStore.getState().appendLog("ERR", "Malformed WS payload ignored");
    }
  };

  socket.onerror = () => {
    useVisionStore.getState().setConnection("error");
    useVisionStore.getState().appendLog("ERR", "WebSocket error");
  };

  socket.onclose = () => {
    useVisionStore.getState().setConnection("disconnected");
    useVisionStore.getState().appendLog("WS", "Telemetry disconnected — reconnecting");
    scheduleReconnect();
  };

  return socket;
}

export function disconnectDetectionWs(): void {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  socket?.close();
  socket = null;
}
