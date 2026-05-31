"use client";

import { useCallback, useEffect, useState } from "react";

import {
  getCameraConfig,
  getCameraDevices,
  postCameraConfig,
  postDetectionStart,
} from "@/lib/api";
import { useVisionStore } from "@/stores/useVisionStore";

export function CameraControls() {
  const mockCamera = useVisionStore((s) => s.mockCamera);
  const cameraIndex = useVisionStore((s) => s.cameraIndex);
  const availableCameraIndices = useVisionStore((s) => s.availableCameraIndices);
  const cameraRunning = useVisionStore((s) => s.cameraRunning);
  const setMockCamera = useVisionStore((s) => s.setMockCamera);
  const setCameraIndex = useVisionStore((s) => s.setCameraIndex);
  const setAvailableCameraIndices = useVisionStore(
    (s) => s.setAvailableCameraIndices,
  );
  const setCameraRunning = useVisionStore((s) => s.setCameraRunning);
  const appendLog = useVisionStore((s) => s.appendLog);

  const [sourceMode, setSourceMode] = useState<"mock" | "live">("mock");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [busy, setBusy] = useState(false);

  const syncFromServer = useCallback(async () => {
    try {
      const config = await getCameraConfig();
      setMockCamera(config.mockCamera);
      setCameraIndex(config.cameraIndex);
      setAvailableCameraIndices(config.availableIndices);
      setSourceMode(config.mockCamera ? "mock" : "live");
      setSelectedIndex(config.cameraIndex);
    } catch (err) {
      appendLog("ERR", `Camera config load failed: ${String(err)}`);
    }
  }, [
    appendLog,
    setAvailableCameraIndices,
    setCameraIndex,
    setMockCamera,
  ]);

  useEffect(() => {
    void syncFromServer();
  }, [syncFromServer]);

  async function handleRefreshDevices() {
    setBusy(true);
    try {
      const { devices } = await getCameraDevices();
      const indices = devices.map((d) => d.index);
      setAvailableCameraIndices(indices);
      appendLog("API", `Found ${indices.length} camera(s)`);
      if (indices.length > 0 && !indices.includes(selectedIndex)) {
        setSelectedIndex(indices[0]);
      }
    } catch (err) {
      appendLog("ERR", `Device scan failed: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleApply() {
    if (cameraRunning) {
      appendLog("ERR", "Stop detection before changing camera");
      return;
    }
    setBusy(true);
    try {
      const config = await postCameraConfig({
        mockCamera: sourceMode === "mock",
        cameraIndex: sourceMode === "live" ? selectedIndex : undefined,
      });
      setMockCamera(config.mockCamera);
      setCameraIndex(config.cameraIndex);
      setAvailableCameraIndices(config.availableIndices);
      setCameraRunning(false);
      appendLog(
        "API",
        config.mockCamera
          ? "Source: mock image sequence"
          : `Source: live camera ${config.cameraIndex}`,
      );
      try {
        await postDetectionStart();
        setCameraRunning(true);
        appendLog("API", "Detection started — MJPEG stream active");
      } catch (startErr) {
        appendLog("ERR", `Auto-start failed: ${String(startErr)}`);
      }
    } catch (err) {
      appendLog("ERR", `Camera apply failed: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  const deviceOptions =
    availableCameraIndices.length > 0
      ? availableCameraIndices
      : [cameraIndex];

  return (
    <div className="panel mb-gutter flex flex-col gap-4 p-container-padding">
      <div className="flex items-center justify-between">
        <h2 className="label-caps text-primary">Camera Source</h2>
        <button
          type="button"
          className="label-caps text-xs text-primary underline disabled:opacity-40"
          disabled={busy}
          onClick={() => void handleRefreshDevices()}
        >
          SCAN
        </button>
      </div>

      <label className="flex flex-col gap-1">
        <span className="label-caps">SOURCE</span>
        <select
          className="data-input"
          value={sourceMode}
          disabled={cameraRunning || busy}
          onChange={(e) =>
            setSourceMode(e.target.value as "mock" | "live")
          }
        >
          <option value="mock">Mock — images/*.jpg</option>
          <option value="live">Live — USB / built-in</option>
        </select>
      </label>

      {sourceMode === "live" && (
        <label className="flex flex-col gap-1">
          <span className="label-caps">DEVICE</span>
          <select
            className="data-input"
            value={selectedIndex}
            disabled={cameraRunning || busy}
            onChange={(e) => setSelectedIndex(Number(e.target.value))}
          >
            {deviceOptions.map((idx) => (
              <option key={idx} value={idx}>
                Camera {idx}
              </option>
            ))}
          </select>
          {availableCameraIndices.length === 0 && (
            <span className="text-xs text-on-surface-variant">
              No devices found — click SCAN or check macOS camera permission
            </span>
          )}
        </label>
      )}

      <button
        type="button"
        className="rounded bg-primary px-3 py-2 text-sm text-surface disabled:opacity-40"
        disabled={cameraRunning || busy}
        onClick={() => void handleApply()}
      >
        APPLY CAMERA
      </button>

      {mockCamera ? (
        <p className="text-xs text-on-surface-variant">
          Active: mock sequence. RUN_DETECTION auto-starts on backend boot when
          mock is active.
        </p>
      ) : (
        <p className="text-xs text-on-surface-variant">
          Active: live camera {cameraIndex}. Stream starts automatically after
          APPLY.
        </p>
      )}
    </div>
  );
}
