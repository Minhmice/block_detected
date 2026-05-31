"use client";

import { useEffect } from "react";

import {
  getHealth,
  getCameraConfig,
  getEimConfig,
  postDetectionStart,
  postDetectionStop,
} from "@/lib/api";
import { connectDetectionWs } from "@/lib/ws";
import { useVisionStore } from "@/stores/useVisionStore";

const STATUS_COLOR: Record<string, string> = {
  connected: "bg-secondary",
  connecting: "bg-yellow-400",
  disconnected: "bg-gray-500",
  error: "bg-error",
};

export function TopStatusBar() {
  const connectionStatus = useVisionStore((s) => s.connectionStatus);
  const fps = useVisionStore((s) => s.fps);
  const latencyMs = useVisionStore((s) => s.latencyMs);
  const mockCamera = useVisionStore((s) => s.mockCamera);
  const cameraRunning = useVisionStore((s) => s.cameraRunning);
  const eiModelLabel = useVisionStore((s) => s.eiModelLabel);
  const visionMockMode = useVisionStore((s) => s.visionMockMode);
  const setLogTerminalOpen = useVisionStore((s) => s.setLogTerminalOpen);
  const appendLog = useVisionStore((s) => s.appendLog);
  const setMockCamera = useVisionStore((s) => s.setMockCamera);
  const setCameraRunning = useVisionStore((s) => s.setCameraRunning);
  const setCameraIndex = useVisionStore((s) => s.setCameraIndex);
  const setAvailableCameraIndices = useVisionStore(
    (s) => s.setAvailableCameraIndices,
  );
  const setEiModelId = useVisionStore((s) => s.setEiModelId);
  const setEiModelLabel = useVisionStore((s) => s.setEiModelLabel);
  const setVisionMockMode = useVisionStore((s) => s.setVisionMockMode);

  useEffect(() => {
    connectDetectionWs();
  }, []);

  async function handleInitialize() {
    try {
      appendLog("API", "INITIALIZE — health check");
      const [health, camera, eim] = await Promise.all([
        getHealth(),
        getCameraConfig(),
        getEimConfig(),
      ]);
      setMockCamera(health.mockCamera);
      setCameraRunning(health.detectionRunning);
      setCameraIndex(camera.cameraIndex);
      setAvailableCameraIndices(camera.availableIndices);
      setVisionMockMode(eim.visionMockMode);
      setEiModelId(eim.selectedId);
      const selected = eim.models.find((m) => m.id === eim.selectedId);
      setEiModelLabel(selected?.label ?? health.eiModelLabel ?? "");
      connectDetectionWs();
      appendLog("API", `Health OK backend=${health.cameraBackend}`);
    } catch (err) {
      appendLog("ERR", `Initialize failed: ${String(err)}`);
    }
  }

  async function handleStart() {
    try {
      await postDetectionStart();
      setCameraRunning(true);
      appendLog("API", "Detection started");
    } catch (err) {
      appendLog("ERR", `Start failed: ${String(err)}`);
    }
  }

  async function handleStop() {
    try {
      await postDetectionStop();
      setCameraRunning(false);
      appendLog("API", "Detection stopped");
    } catch (err) {
      appendLog("ERR", `Stop failed: ${String(err)}`);
    }
  }

  async function handleEmergencyStop() {
    await handleStop();
    appendLog("ERR", "EMERGENCY STOP");
  }

  const disabled = connectionStatus === "disconnected";

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-gutter">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-bold tracking-tight text-primary">
          VISION_OS // BLOCK_DETECTOR_V2
        </h1>
        <div className="hidden items-center gap-2 md:flex">
          <span
            className={`h-2 w-2 rounded-full ${STATUS_COLOR[connectionStatus]}`}
          />
          <span className="label-caps text-secondary">
            {connectionStatus.toUpperCase()}
          </span>
        </div>
        {mockCamera && (
          <span className="label-caps rounded border border-primary/40 px-2 py-0.5 text-primary">
            MOCK_MODE
          </span>
        )}
        {!visionMockMode && eiModelLabel ? (
          <span className="label-caps rounded border border-secondary/40 px-2 py-0.5 text-secondary">
            EI: {eiModelLabel}
          </span>
        ) : null}
        {!mockCamera && !cameraRunning && (
          <span className="label-caps rounded border border-secondary/40 px-2 py-0.5 text-secondary">
            LIVE_CAMERA — RUN_DETECTION
          </span>
        )}
      </div>
      <div className="flex items-center gap-4 font-mono text-sm">
        <span>FPS {fps.toFixed(1)}</span>
        <span>{latencyMs.toFixed(0)} ms</span>
        <button
          type="button"
          className="rounded border border-outline-variant px-3 py-1 hover:border-primary"
          onClick={() => setLogTerminalOpen(true)}
        >
          LOG
        </button>
        <button
          type="button"
          className="rounded border border-outline-variant px-3 py-1 hover:border-primary"
          onClick={handleInitialize}
        >
          INITIALIZE
        </button>
        <button
          type="button"
          disabled={disabled && !mockCamera}
          className="rounded bg-primary px-3 py-1 text-surface disabled:opacity-40"
          onClick={handleStart}
        >
          RUN_DETECTION
        </button>
        <button
          type="button"
          disabled={disabled}
          className="rounded border border-outline-variant px-3 py-1 disabled:opacity-40"
          onClick={handleStop}
        >
          STOP
        </button>
        <button
          type="button"
          className="rounded bg-red-700 px-3 py-1 text-white"
          onClick={handleEmergencyStop}
        >
          E_STOP
        </button>
        {cameraRunning && (
          <span className="label-caps text-secondary">
            {mockCamera ? "LIVE" : "LIVE_CAMERA"}
          </span>
        )}
      </div>
    </header>
  );
}
