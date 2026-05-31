export type ConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export interface PointPx {
  x: number;
  y: number;
}

export interface CornersPx {
  tl: PointPx;
  tr: PointPx;
  br: PointPx;
  bl: PointPx;
}

export interface PickupPoseMm {
  xMm: number;
  yMm: number;
  thetaDeg: number;
}

export interface DetectionResultWire {
  blockId: number | null;
  confidence: number;
  status: string;
  centerPx: PointPx | null;
  cornersPx: CornersPx | null;
  angleDeg: number | null;
  pickupPoseMm: PickupPoseMm | null;
}

export interface ClassificationScoresWire {
  block01: number;
  block02: number;
  block03: number;
  block04: number;
}

export interface DetectionTelemetryWire {
  type: "telemetry";
  fps: number;
  latencyMs: number;
  valid: boolean;
  rejectReason: string | null;
  detection: DetectionResultWire | null;
  classificationScores: ClassificationScoresWire | null;
}

export interface DetectionParamsWire {
  blurKernel: number;
  adaptiveBlockSize: number;
  adaptiveC: number;
  cannyLow: number;
  cannyHigh: number;
  minAreaPx: number;
  maxAreaPx: number;
  aspectMin: number;
  aspectMax: number;
  confidenceThreshold: number;
}

export interface SystemStatusWire {
  status: string;
  mockCamera: boolean;
  detectionRunning: boolean;
  cameraBackend: string;
  cameraIndex: number;
  visionMockMode?: boolean;
  eiModelPath?: string;
  eiModelLoaded?: boolean;
  eiModelExecutable?: boolean;
  eiModelError?: string | null;
  eiModelId?: string;
  eiModelLabel?: string;
}

export interface EimModelWire {
  id: string;
  label: string;
  path: string;
  executable: boolean;
}

export interface EimConfigWire {
  models: EimModelWire[];
  selectedId: string;
  selectedPath: string;
  selectedExecutable: boolean;
  visionMockMode: boolean;
}

export interface CameraDeviceWire {
  index: number;
  label: string;
}

export interface CameraConfigWire {
  mockCamera: boolean;
  cameraIndex: number;
  availableIndices: number[];
}
