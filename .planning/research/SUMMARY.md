# Research Summary — Detect Only v4 (Milestone v2.0)

**Synthesized:** 2026-07-03  
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md, PROJECT.md

---

## Executive Summary

Detect Only v4 is a **greenfield Python module** (`src/detect_only_v4/`) that provides library-first YOLO inference on Raspberry Pi 5 with a FastAPI/WebSocket control plane. The architecture centers on a normalized `DetectionResult` contract, task-specific adapters, format-aware model loading (NCNN priority on Pi), and a threaded capture/inference pipeline with drop-old-frame semantics.

**MVP slice:** Core types → `.pt` load + detect adapter → OpenCV camera → synchronous CLI → then threading → Web UI → Pi backends (NCNN, Picamera2) → remaining task adapters.

---

## Stack Additions

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Inference | ultralytics | ≥8.4.14, <9.0 | Single `YOLO(path)` for all formats |
| Pi runtime | NCNN export dir | via ultralytics | ~68 ms/im YOLO26n vs ~302 ms PyTorch |
| Fallback | OpenVINO / ONNX | via ultralytics | 71 ms / 130 ms on Pi 5 |
| Camera (Pi) | picamera2 (apt) | ≥0.3.19 | `--system-site-packages` venv |
| Camera (USB) | opencv (apt on Pi) | 4.6+ | V4L2, `CAP_PROP_BUFFERSIZE=1` |
| Web | fastapi + uvicorn | ≥0.115 / ≥0.30 | Single worker on Pi |
| Python | 3.11 (Pi Bookworm) | — | Avoid 3.13 on Pi |

**Backend priority on Pi:** NCNN dir → OpenVINO dir → ONNX → TFLite → PT. `.engine` discover-only, unsupported on Pi.

**Avoid:** pip opencv-python on Pi with Picamera2 (numpy 2.x clash); inference in async handlers; unbounded queues; tracking.

---

## Feature Table Stakes vs Differentiators

**Table stakes:** Model scan, load/detect API, task normalize, draw overlay, camera enumerate/probe, Web UI preview, runtime conf/IoU/imgsz, logging, type hints, unit tests.

**Differentiators:** Multi-format discovery with NCNN priority, auto family/task identify, unified `DetectionResult` across 4 tasks, library-first API, drop-old-frame pipeline, LAN WebSocket config.

**Anti-features (out of scope):** Tracking, training, hex_detector merge, CUDA on Pi, multi-worker Uvicorn, unbounded queue, auth.

---

## Architecture Highlights

```
FastAPI (async) → InferenceSession snapshot
CaptureThread → BoundedQueue(maxsize=1, drop-old) → InferenceWorker
  → TaskAdapter → DetectionResult → draw_overlay → SessionSnapshot
```

**Folder:** `src/detect_only_v4/` with `core/`, `models/`, `detectors/{detect,segment,pose,obb}/`, `cameras/`, `pipeline/`, `render/`, `api/`.

**Dependency rule:** `api` → `pipeline` → `{cameras, models, detectors, render}` → `core`.

**Public API:** `load_model`, `inspect_model`, `discover_cameras`, `probe_camera`, `detect_frame`, `normalize_results`, `draw_overlay`.

---

## Watch Out For (Top Pitfalls)

1. **Format interchangeability** — NCNN is a directory; `.engine` fails on Pi; task metadata required
2. **Guessing task/family** — Use `model.task` + metadata; refuse unknown; dry inference last resort only
3. **OpenCV VideoCapture(0) on Pi CSI** — Use Picamera2 for CSI; V4L2 for USB only
4. **Resolution negotiation** — Log actual dims after probe; warmup frames; BGR/RGB conversion once
5. **Single-threaded capture+infer** — Separate threads; queue maxsize=1; skip frame on error
6. **Blocking event loop** — Never predict/encode in async handlers; snapshot pattern
7. **NCNN always wins myth** — Prefer when available; benchmark and allow ONNX fallback

---

## Recommended Build Order (7 Phases)

| Phase | Focus | Key deliverable |
|-------|-------|-----------------|
| 3 | Core API & contracts | `DetectionResult`, `inspect_model`, logging |
| 4 | Model discovery & formats | Scan `models/`, NCNN/ONNX/PT backends |
| 5 | Task adapters & overlay | detect/segment/pose/obb + `draw_overlay` |
| 6 | Camera discovery & backends | V4L2, Picamera2, `probe_camera` |
| 7 | Threaded pipeline | Bounded queue, capture + infer threads |
| 8 | FastAPI WebSocket UI | REST list, live JPEG+JSON, runtime config |
| 9 | Pi optimization & hardening | NCNN priority, README, benchmarks, tests |

Phases 3–5 can partially parallelize after core types; camera (6) and pipeline (7) before full Web UI (8).

---

## Recommendations for Requirements

- REQ categories: CORE, MODEL, ADPT, CAM, PIPE, WEB, QA
- Every requirement maps to exactly one phase
- Pi-specific success criteria in phases 6, 7, 9
- `.engine` on Pi = discover + explicit unsupported error
- No tracking, no training, no legacy imports

---
*Synthesized for milestone v2.0 roadmap and requirements definition*
