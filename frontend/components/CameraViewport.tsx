"use client";

import { useEffect, useRef, useState } from "react";

import { postDatasetSaveFrame } from "@/lib/api";
import { useVisionStore } from "@/stores/useVisionStore";
import { VisionOverlay } from "@/components/VisionOverlay";

const STREAM_URL = process.env.NEXT_PUBLIC_STREAM_URL;

export function CameraViewport() {
  const imgRef = useRef<HTMLImageElement>(null);
  const latestValid = useVisionStore((s) => s.latestValid);
  const rejectReason = useVisionStore((s) => s.rejectReason);
  const overlayFlags = useVisionStore((s) => s.overlayFlags);
  const cameraRunning = useVisionStore((s) => s.cameraRunning);
  const mockCamera = useVisionStore((s) => s.mockCamera);
  const cameraIndex = useVisionStore((s) => s.cameraIndex);
  const setOverlayFlag = useVisionStore((s) => s.setOverlayFlag);
  const appendLog = useVisionStore((s) => s.appendLog);
  const addDatasetEntry = useVisionStore((s) => s.addDatasetEntry);
  const [streamKey, setStreamKey] = useState(0);

  useEffect(() => {
    if (cameraRunning) {
      setStreamKey((k) => k + 1);
    }
  }, [cameraRunning, cameraIndex, mockCamera]);

  async function saveFrame(reason: string) {
    try {
      const res = await postDatasetSaveFrame({ reason });
      appendLog("API", `Saved frame ${res.path ?? ""}`);
      if (res.path) {
        addDatasetEntry({ ts: Date.now(), path: res.path, reason });
      }
    } catch (err) {
      appendLog("ERR", `Save frame failed: ${String(err)}`);
    }
  }

  if (!STREAM_URL) {
    return (
      <div className="panel flex h-full min-h-[360px] items-center justify-center p-6 text-on-surface-variant">
        Configure NEXT_PUBLIC_STREAM_URL to view the camera feed.
      </div>
    );
  }

  return (
    <div className="panel flex min-h-[360px] flex-col overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant p-2">
        <span className="label-caps text-secondary">
          {mockCamera
            ? "MOCK FEED"
            : `LIVE · Camera ${cameraIndex}`}
          {cameraRunning ? " · STREAMING" : " · IDLE"}
        </span>
        <div className="flex flex-wrap gap-2">
        {(Object.keys(overlayFlags) as (keyof typeof overlayFlags)[]).map(
          (key) => (
            <button
              key={key}
              type="button"
              className={`label-caps rounded px-2 py-1 ${
                overlayFlags[key]
                  ? "bg-primary/20 text-primary"
                  : "bg-surface-container-high"
              }`}
              onClick={() => setOverlayFlag(key, !overlayFlags[key])}
            >
              {key}
            </button>
          ),
        )}
        </div>
      </div>
      <div className="relative flex-1 bg-black">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          ref={imgRef}
          src={
            cameraRunning && STREAM_URL
              ? `${STREAM_URL}?v=${streamKey}`
              : undefined
          }
          alt="Live detection stream"
          className="h-full w-full object-contain"
        />
        {!cameraRunning && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 p-4 text-center text-sm text-on-surface-variant">
            No stream — apply camera source or press RUN_DETECTION
          </div>
        )}
        <VisionOverlay imgRef={imgRef} />
      </div>
      <div className="flex items-center justify-between border-t border-outline-variant p-2">
        <span
          className={`label-caps ${latestValid ? "text-secondary" : "text-error"}`}
        >
          {latestValid ? "VALID" : "INVALID"}
          {rejectReason ? ` — ${rejectReason}` : ""}
        </span>
        <button
          type="button"
          className="label-caps rounded border border-outline-variant px-3 py-1 hover:border-primary"
          onClick={() => saveFrame("manual_save")}
        >
          Save Failed Frame
        </button>
      </div>
    </div>
  );
}
