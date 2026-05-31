"use client";

import { useState } from "react";

import { postCalibrationSave } from "@/lib/api";
import { useVisionStore } from "@/stores/useVisionStore";

export function CalibrationPanel() {
  const appendLog = useVisionStore((s) => s.appendLog);
  const [preview, setPreview] = useState<string>("");

  async function handleSave() {
    if (!preview) return;
    try {
      const body = JSON.parse(preview);
      await postCalibrationSave(body);
      appendLog("API", "Calibration saved");
    } catch (err) {
      appendLog("ERR", `Calibration save failed: ${String(err)}`);
    }
  }

  return (
    <div className="panel flex flex-col gap-4 p-container-padding">
      <h2 className="label-caps text-primary">Calibration</h2>
      <label className="label-caps">
        LOAD FROM FILE
        <input
          type="file"
          accept="application/json"
          className="mt-1 block w-full text-sm"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            const text = await file.text();
            setPreview(text);
          }}
        />
      </label>
      <textarea
        className="data-input min-h-[200px] w-full"
        value={preview}
        onChange={(e) => setPreview(e.target.value)}
        placeholder="Paste or load calibration JSON"
      />
      <button
        type="button"
        className="rounded bg-primary px-4 py-2 text-surface"
        onClick={handleSave}
      >
        SAVE CALIBRATION
      </button>
    </div>
  );
}
