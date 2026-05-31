"use client";

import { useCallback, useRef } from "react";

import { ParamLabel, ParamTooltip } from "@/components/ParamTooltip";
import { postDetectionParams } from "@/lib/api";
import {
  DETECTION_PANEL_FOOTER_TIP,
  DETECTION_PARAM_TOOLTIPS,
  type ParamTooltipContent,
} from "@/lib/detectionParamTooltips";
import { useVisionStore } from "@/stores/useVisionStore";

const DEBOUNCE_MS = 400;

export function DetectionControls() {
  const params = useVisionStore((s) => s.params);
  const setParams = useVisionStore((s) => s.setParams);
  const resetParams = useVisionStore((s) => s.resetParams);
  const appendLog = useVisionStore((s) => s.appendLog);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pushParams = useCallback(
    (next: typeof params) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(async () => {
        try {
          await postDetectionParams({
            blurKernel: next.blurKernel,
            adaptiveBlockSize: next.adaptiveBlockSize,
            adaptiveC: next.adaptiveC,
            cannyLow: next.cannyLow,
            cannyHigh: next.cannyHigh,
            minAreaPx: next.minAreaPx,
            maxAreaPx: next.maxAreaPx,
            aspectMin: next.aspectMin,
            aspectMax: next.aspectMax,
            confidenceThreshold: next.confidenceThreshold,
          });
          appendLog("API", "Params synced");
        } catch (err) {
          appendLog("ERR", `Params sync failed: ${String(err)}`);
        }
      }, DEBOUNCE_MS);
    },
    [appendLog],
  );

  function update<K extends keyof typeof params>(key: K, value: (typeof params)[K]) {
    const next = { ...params, [key]: value };
    setParams({ [key]: value });
    pushParams(next);
  }

  async function handleReset() {
    resetParams();
    const fresh = useVisionStore.getState().params;
    pushParams(fresh);
    appendLog("API", "RESET DEFAULTS");
  }

  return (
    <div className="panel flex flex-col gap-4 p-container-padding">
      <div className="flex items-center justify-between">
        <h2 className="label-caps text-primary">Detection Parameters</h2>
        <span className="inline-flex items-center gap-1">
          <button
            type="button"
            className="label-caps text-xs text-primary underline"
            onClick={handleReset}
          >
            RESET DEFAULTS
          </button>
          <ParamTooltip content={DETECTION_PARAM_TOOLTIPS.resetDefaults} />
        </span>
      </div>

      <label className="flex flex-col gap-1">
        <span className="label-caps">
          <ParamLabel tooltip={DETECTION_PARAM_TOOLTIPS.thresholdMode}>
            THRESHOLD_MODE
          </ParamLabel>
        </span>
        <select
          className="data-input"
          value={params.thresholdMode}
          onChange={(e) => update("thresholdMode", e.target.value)}
        >
          <option value="canny">canny</option>
          <option value="adaptive">adaptive</option>
          <option value="hsv">hsv</option>
        </select>
      </label>

      <Slider
        label="blurKernel"
        tooltip={DETECTION_PARAM_TOOLTIPS.blurKernel}
        value={params.blurKernel}
        min={1}
        max={15}
        step={2}
        onChange={(v) => update("blurKernel", v)}
      />
      <Slider
        label="cannyLow"
        tooltip={DETECTION_PARAM_TOOLTIPS.cannyLow}
        value={params.cannyLow}
        min={0}
        max={255}
        onChange={(v) => update("cannyLow", v)}
      />
      <Slider
        label="cannyHigh"
        tooltip={DETECTION_PARAM_TOOLTIPS.cannyHigh}
        value={params.cannyHigh}
        min={0}
        max={255}
        onChange={(v) => update("cannyHigh", v)}
      />
      <Slider
        label="minAreaPx"
        tooltip={DETECTION_PARAM_TOOLTIPS.minAreaPx}
        value={params.minAreaPx}
        min={100}
        max={50000}
        onChange={(v) => update("minAreaPx", v)}
      />
      <Slider
        label="maxAreaPx"
        tooltip={DETECTION_PARAM_TOOLTIPS.maxAreaPx}
        value={params.maxAreaPx}
        min={1000}
        max={200000}
        onChange={(v) => update("maxAreaPx", v)}
      />
      <Slider
        label="confidenceThresh"
        tooltip={DETECTION_PARAM_TOOLTIPS.confidenceThresh}
        value={params.confidenceThreshold}
        min={0}
        max={1}
        step={0.01}
        onChange={(v) => update("confidenceThreshold", v)}
      />

      <p className="border-t border-outline-variant pt-3 font-mono text-xs text-on-surface-variant">
        {DETECTION_PANEL_FOOTER_TIP}
      </p>
    </div>
  );
}

function Slider({
  label,
  tooltip,
  value,
  min,
  max,
  step = 1,
  onChange,
}: {
  label: string;
  tooltip: ParamTooltipContent;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <div className="flex justify-between label-caps">
        <ParamLabel tooltip={tooltip}>{label}</ParamLabel>
        <span className="font-mono">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-primary"
      />
    </label>
  );
}
