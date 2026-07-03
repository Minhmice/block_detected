---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Detect Only v4
status: planning
last_updated: "2026-07-03T05:15:00.000Z"
last_activity: 2026-07-03 — Milestone v2.0 roadmap approved
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Detect Only v4

**Last updated:** 2026-07-03

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-07-03)

**Core value:** Từ camera Pi 5, tự động phát hiện model/camera, inference YOLO realtime với overlay và JSON chuẩn hóa  
**Current focus:** Milestone v2.0 — ready to plan Phase 3

## Progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Core CV Pipeline (v1.0) | Complete | `src/hex_detector/` |
| 2 Dataset Hex Debugger (v1.0) | Complete | `scripts/debug_hex_dataset.py` |
| 3 Core API & Contracts | Pending | `src/detect_only_v4/core/` |
| 4 Model Discovery & Formats | Pending | `src/detect_only_v4/models/` |
| 5 Task Adapters & Overlay | Pending | `src/detect_only_v4/detectors/` |
| 6 Camera Discovery & Backends | Pending | `src/detect_only_v4/cameras/` |
| 7 Threaded Pipeline | Pending | `src/detect_only_v4/pipeline/` |
| 8 FastAPI WebSocket UI | Pending | `src/detect_only_v4/api/` |
| 9 Pi Optimization & Hardening | Pending | tests + README |

## Decisions Log

- v2.0 greenfield `src/detect_only_v4/` — không đọc/sửa legacy code
- NCNN priority on Pi 5; `.engine` unsupported on Pi
- No tracking — all detections per frame
- Task adapters chuẩn hóa DetectionResult
- Bounded queue maxsize=1, drop-old-frame

## Blockers

None

## Current Position

Phase: 3 — Core API & Contracts (not started)
Plan: —
Status: Roadmap approved — ready for `/gsd:plan-phase 3`
Last activity: 2026-07-03 — Milestone v2.0 requirements + roadmap complete

## Operator Next Steps

- `/gsd:discuss-phase 3` — gather context for Core API & Contracts
- `/gsd:plan-phase 3` — create executable plan for Phase 3

---
*Initialized: 2026-06-30 | v2.0 started: 2026-07-03*
