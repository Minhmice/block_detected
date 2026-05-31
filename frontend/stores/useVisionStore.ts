"use client";

import { create } from "zustand";

import type {
  ConnectionStatus,
  DetectionParamsWire,
  DetectionTelemetryWire,
  DetectionResultWire,
} from "@/types/vision";

export interface OverlayFlags {
  grid: boolean;
  squareCorners: boolean;
  center: boolean;
  angle: boolean;
  pickup: boolean;
  bbox: boolean;
}

export interface LogEntry {
  id: number;
  ts: number;
  level: string;
  message: string;
}

export interface DatasetEntry {
  ts: number;
  path: string;
  reason?: string | null;
}

export interface VisionParams extends DetectionParamsWire {
  thresholdMode: string;
  rejectLowConfidence: boolean;
  rejectInvalidGeometry: boolean;
}

const DEFAULT_PARAMS: VisionParams = {
  blurKernel: 5,
  adaptiveBlockSize: 31,
  adaptiveC: 5,
  cannyLow: 50,
  cannyHigh: 150,
  minAreaPx: 1000,
  maxAreaPx: 80000,
  aspectMin: 0.75,
  aspectMax: 1.33,
  confidenceThreshold: 0.55,
  thresholdMode: "adaptive",
  rejectLowConfidence: true,
  rejectInvalidGeometry: true,
};

interface VisionState {
  connectionStatus: ConnectionStatus;
  fps: number;
  latencyMs: number;
  detectionMode: string;
  cameraRunning: boolean;
  mockCamera: boolean;
  cameraIndex: number;
  availableCameraIndices: number[];
  eiModelId: string;
  eiModelLabel: string;
  visionMockMode: boolean;
  params: VisionParams;
  latestResult: DetectionResultWire | null;
  latestValid: boolean;
  rejectReason: string | null;
  classificationScores: DetectionTelemetryWire["classificationScores"];
  overlayFlags: OverlayFlags;
  logs: LogEntry[];
  logTerminalOpen: boolean;
  datasetEntries: DatasetEntry[];
  setConnection: (status: ConnectionStatus) => void;
  setTransportMetrics: (fps: number, latencyMs: number) => void;
  setCameraRunning: (running: boolean) => void;
  setMockCamera: (mock: boolean) => void;
  setCameraIndex: (index: number) => void;
  setAvailableCameraIndices: (indices: number[]) => void;
  setEiModelId: (id: string) => void;
  setEiModelLabel: (label: string) => void;
  setVisionMockMode: (mock: boolean) => void;
  setParams: (partial: Partial<VisionParams>) => void;
  resetParams: () => void;
  applyTelemetry: (msg: DetectionTelemetryWire) => void;
  appendLog: (level: string, message: string) => void;
  setLogTerminalOpen: (open: boolean) => void;
  setOverlayFlag: (key: keyof OverlayFlags, value: boolean) => void;
  addDatasetEntry: (entry: DatasetEntry) => void;
}

const MAX_LOGS = 500;
let nextLogId = 1;

export const useVisionStore = create<VisionState>((set, get) => ({
  connectionStatus: "disconnected",
  fps: 0,
  latencyMs: 0,
  detectionMode: "live",
  cameraRunning: false,
  mockCamera: false,
  cameraIndex: 0,
  availableCameraIndices: [],
  eiModelId: "",
  eiModelLabel: "",
  visionMockMode: true,
  params: DEFAULT_PARAMS,
  latestResult: null,
  latestValid: false,
  rejectReason: null,
  classificationScores: null,
  overlayFlags: {
    grid: true,
    squareCorners: true,
    center: true,
    angle: true,
    pickup: true,
    bbox: true,
  },
  logs: [],
  logTerminalOpen: false,
  datasetEntries: [],
  setConnection: (connectionStatus) => set({ connectionStatus }),
  setTransportMetrics: (fps, latencyMs) => set({ fps, latencyMs }),
  setCameraRunning: (cameraRunning) => set({ cameraRunning }),
  setMockCamera: (mockCamera) => set({ mockCamera }),
  setCameraIndex: (cameraIndex) => set({ cameraIndex }),
  setAvailableCameraIndices: (availableCameraIndices) =>
    set({ availableCameraIndices }),
  setEiModelId: (eiModelId) => set({ eiModelId }),
  setEiModelLabel: (eiModelLabel) => set({ eiModelLabel }),
  setVisionMockMode: (visionMockMode) => set({ visionMockMode }),
  setParams: (partial) =>
    set({ params: { ...get().params, ...partial } }),
  resetParams: () => set({ params: { ...DEFAULT_PARAMS } }),
  applyTelemetry: (msg) =>
    set({
      fps: msg.fps,
      latencyMs: msg.latencyMs,
      latestValid: msg.valid,
      rejectReason: msg.rejectReason,
      latestResult: msg.detection,
      classificationScores: msg.classificationScores,
    }),
  appendLog: (level, message) => {
    const entry: LogEntry = {
      id: nextLogId++,
      ts: Date.now(),
      level,
      message,
    };
    const logs = [...get().logs, entry].slice(-MAX_LOGS);
    set({ logs });
  },
  setLogTerminalOpen: (logTerminalOpen) => set({ logTerminalOpen }),
  setOverlayFlag: (key, value) =>
    set({ overlayFlags: { ...get().overlayFlags, [key]: value } }),
  addDatasetEntry: (entry) =>
    set({
      datasetEntries: [entry, ...get().datasetEntries].slice(0, 10),
    }),
}));
