import type { DetectionParamsWire } from "@/types/vision";
import type {
  CameraConfigWire,
  CameraDeviceWire,
  EimConfigWire,
  SystemStatusWire,
} from "@/types/vision";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
  }
  return base.replace(/\/$/, "");
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<SystemStatusWire> {
  const res = await fetch(`${apiBase()}/health`);
  return parseJson<SystemStatusWire>(res);
}

export async function postDetectionStart(): Promise<{ started: boolean }> {
  const res = await fetch(`${apiBase()}/api/detection/start`, { method: "POST" });
  return parseJson(res);
}

export async function postDetectionStop(): Promise<{ started: boolean }> {
  const res = await fetch(`${apiBase()}/api/detection/stop`, { method: "POST" });
  return parseJson(res);
}

export async function postDetectionParams(
  params: DetectionParamsWire,
): Promise<{ ok: boolean }> {
  const res = await fetch(`${apiBase()}/api/detection/params`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return parseJson(res);
}

export async function postCalibrationSave(body: unknown): Promise<{ ok: boolean }> {
  const res = await fetch(`${apiBase()}/api/calibration/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

export async function postDatasetSaveFrame(body?: {
  reason?: string;
}): Promise<{ ok: boolean; path?: string }> {
  const res = await fetch(`${apiBase()}/api/dataset/save-frame`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  return parseJson(res);
}

export async function getCameraConfig(): Promise<CameraConfigWire> {
  const res = await fetch(`${apiBase()}/api/camera/config`);
  return parseJson<CameraConfigWire>(res);
}

export async function getEimConfig(): Promise<EimConfigWire> {
  const res = await fetch(`${apiBase()}/api/eim/config`);
  return parseJson<EimConfigWire>(res);
}

export async function postEimConfig(body: {
  modelId: string;
}): Promise<EimConfigWire> {
  const res = await fetch(`${apiBase()}/api/eim/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<EimConfigWire>(res);
}

export async function getCameraDevices(): Promise<CameraDeviceWire[]> {
  const res = await fetch(`${apiBase()}/api/camera/devices`);
  return parseJson(res);
}

export async function postCameraConfig(body: {
  mockCamera?: boolean;
  cameraIndex?: number;
}): Promise<CameraConfigWire> {
  const res = await fetch(`${apiBase()}/api/camera/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<CameraConfigWire>(res);
}
