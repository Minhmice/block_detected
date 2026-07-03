# Detect Only v4 — Modular YOLO Inference on Raspberry Pi 5

## What This Is

Ứng dụng Python modular chạy trên Raspberry Pi 5, đọc camera và inference model Ultralytics YOLO với Web UI FastAPI/WebSocket. Greenfield module `src/detect_only_v4/` — không phụ thuộc hex_detector, block_detected, hay code legacy khác.

## Core Value

Từ camera Pi 5, tự động phát hiện model/camera phù hợp, chạy inference realtime với overlay và JSON chuẩn hóa — sẵn sàng tích hợp robot/telemetry mà không cần viết lại pipeline YOLO.

## Current Milestone: v2.0 Detect Only v4

**Goal:** Xây dựng platform inference YOLO modular trên Pi 5 với discovery model/camera, task adapters, và Web UI điều khiển realtime.

**Target features:**
- Model discovery: `.pt`, `.onnx`, `.engine`, `.tflite`, thư mục NCNN
- Auto-identify model family (YOLOv8/11/26) và task (detect/segment/pose/OBB)
- Task adapters chuẩn hóa `DetectionResult` (detect/segment/pose/obb)
- Core API: `load_model`, `inspect_model`, `discover_cameras`, `probe_camera`, `detect_frame`, `normalize_results`, `draw_overlay`
- Camera auto-detect: OpenCV/V4L2, USB webcam, Picamera2 — native resolution/FPS
- FastAPI + WebSocket UI: list camera/model, live overlay + JSON, runtime config
- Pi 5 optimization: bounded queue, drop-old-frame, inference thread, NCNN priority
- Type hints, dataclass, logging, unit tests, README

## Current State (v1.0 shipped 2026-07-03)

- **Module:** `src/hex_detector/` — CPU-only block face geometry (separate milestone, unchanged)
- **Debugger:** `scripts/debug_hex_dataset.py`
- **Tests:** 32+ automated tests passing

## Requirements

### Validated (v1.0 — hex_detector)

- [x] Front-first rectangle/hex detection with typed contracts (Phase 1 — 01-01) — v1.0
- [x] Guarded temporal hold with score decay + basic/verbose debug rendering (Phase 1 — 01-02) — v1.0
- [x] Interactive dataset debugger with tiered diagnostics 0–3 (Phase 2 — 02-01) — v1.0
- [x] Per-stage detector instrumentation, observational only (Phase 2 — 02-01) — v1.0

### Active

(Define via milestone v2.0 — see `.planning/REQUIREMENTS.md`)

### Out of Scope

- Train / fine-tune YOLO — model đã có
- Object tracking — không dùng tracker, luôn trả tất cả detections
- Đọc/sửa code ngoài `src/detect_only_v4/` — greenfield module
- hex_detector integration — milestone riêng, không merge logic
- GPU / CUDA trên Pi — ưu tiên NCNN/CPU
- Complex desktop GUI — Web UI FastAPI là surface chính

## Context

- Folder code: `src/detect_only_v4/` (greenfield)
- Models: quét `models/` tại repo root
- Pi 5 target: bounded queue, inference thread riêng, không block camera
- Ultralytics YOLO: hỗ trợ detect, segment, pose, OBB qua task adapters

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Greenfield `detect_only_v4/` | Tách biệt hoàn toàn khỏi hex_detector và legacy | Pending |
| Task adapter pattern | Chuẩn hóa mọi output thành `DetectionResult` | Pending |
| NCNN priority on Pi | Tối ưu inference CPU trên Pi 5 | Pending |
| No tracking | Yêu cầu rõ ràng — trả tất cả detections | Pending |
| Web UI via FastAPI/WebSocket | Remote config + preview trên LAN | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-03 — Milestone v2.0 started*
