"use client";

import { useCallback, useEffect, useState } from "react";

import { getEimConfig, postEimConfig } from "@/lib/api";
import { useVisionStore } from "@/stores/useVisionStore";

export function ModelControls() {
  const eiModelId = useVisionStore((s) => s.eiModelId);
  const eiModelLabel = useVisionStore((s) => s.eiModelLabel);
  const visionMockMode = useVisionStore((s) => s.visionMockMode);
  const cameraRunning = useVisionStore((s) => s.cameraRunning);
  const setEiModelId = useVisionStore((s) => s.setEiModelId);
  const setEiModelLabel = useVisionStore((s) => s.setEiModelLabel);
  const setVisionMockMode = useVisionStore((s) => s.setVisionMockMode);
  const appendLog = useVisionStore((s) => s.appendLog);

  const [models, setModels] = useState<
    { id: string; label: string; executable: boolean }[]
  >([]);
  const [selectedId, setSelectedId] = useState("");
  const [busy, setBusy] = useState(false);

  const syncFromServer = useCallback(async () => {
    try {
      const config = await getEimConfig();
      setModels(config.models);
      setSelectedId(config.selectedId);
      setEiModelId(config.selectedId);
      setVisionMockMode(config.visionMockMode);
      const selected = config.models.find((m) => m.id === config.selectedId);
      setEiModelLabel(selected?.label ?? "");
    } catch (err) {
      appendLog("ERR", `EIM config load failed: ${String(err)}`);
    }
  }, [appendLog, setEiModelId, setEiModelLabel, setVisionMockMode]);

  useEffect(() => {
    void syncFromServer();
  }, [syncFromServer]);

  async function handleApply() {
    if (cameraRunning) {
      appendLog("ERR", "Stop detection before changing EIM model");
      return;
    }
    // #region agent log
    fetch("http://127.0.0.1:7800/ingest/4bf68a7c-eec8-41ad-8178-d40cbaef00f6", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "7b62f0",
      },
      body: JSON.stringify({
        sessionId: "7b62f0",
        location: "ModelControls.tsx:handleApply",
        message: "apply clicked",
        data: { selectedId, visionMockMode, cameraRunning },
        timestamp: Date.now(),
        hypothesisId: "C",
      }),
    }).catch(() => {});
    // #endregion
    setBusy(true);
    try {
      const config = await postEimConfig({ modelId: selectedId });
      setEiModelId(config.selectedId);
      const selected = config.models.find((m) => m.id === config.selectedId);
      setEiModelLabel(selected?.label ?? "");
      appendLog(
        "API",
        `EIM model: ${selected?.label ?? config.selectedId}${
          visionMockMode ? " (saved; live EI when mock off)" : ""
        }`,
      );
    } catch (err) {
      appendLog("ERR", `EIM model switch failed: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel mt-gutter flex flex-col gap-3 p-container-padding">
      <div className="flex items-center justify-between">
        <h2 className="label-caps text-primary">Edge Impulse Model</h2>
        {eiModelLabel ? (
          <span className="font-mono text-xs text-on-surface-variant">
            {eiModelLabel}
          </span>
        ) : null}
      </div>

      {visionMockMode ? (
        <p className="font-mono text-xs text-on-surface-variant">
          Mock vision active — selection is saved for Pi/live mode. Set
          VISION_MOCK_MODE=false to load EI at runtime.
        </p>
      ) : null}

      <label className="flex flex-col gap-1">
        <span className="label-caps">MODEL</span>
        <select
          className="data-input"
          value={selectedId}
          disabled={cameraRunning || busy}
          onChange={(e) => setSelectedId(e.target.value)}
        >
          {models.map((model) => (
            <option key={model.id} value={model.id} disabled={!model.executable}>
              {model.label}
              {!model.executable ? " (not executable)" : ""}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        className="rounded border border-primary px-3 py-2 label-caps text-primary disabled:opacity-40"
        disabled={cameraRunning || busy || !selectedId}
        onClick={handleApply}
      >
        APPLY MODEL
      </button>
    </div>
  );
}
