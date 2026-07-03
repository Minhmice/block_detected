# Hex Detector — Block Face Geometry on Raspberry Pi 5

## What This Is

MVP thư viện CPU-only (OpenCV + NumPy) chạy trên Raspberry Pi 5, nhận bbox YOLO tracking cho cụm 4 block trên pallet và trích xuất 6 điểm A–F mô tả hai mặt front/right của block. Kèm script debug dataset tương tác. Không train model, không sửa YOLO tracker hiện tại.

## Core Value

Từ mỗi bbox YOLO đã track, ổn định và chính xác trả về topology hex A–F (hoặc rectangle A,B,E,F khi mặt right quá hẹp) để điều khiển robot/lấy tọa độ mặt block.

## Current State (v1.0 shipped 2026-07-03)

- **Module:** `src/hex_detector/` — front-first rectangle/hex detection, temporal hold, debug rendering
- **Debugger:** `scripts/debug_hex_dataset.py` — tiered diagnostics 0–3, keyboard navigation, config reload
- **Tests:** 32+ automated tests passing; 20/20 Phase 2 must-haves verified
- **Git range:** `28cdd11` → `90e8a85` (2026-06-30 → 2026-07-01)
- **Known gaps:** Pi 5 CPU profiling and OpenCV GUI keyboard behavior require human verification (`human_needed` on phase VERIFICATION.md)

## Next Milestone Goals

- Pi 5 on-device performance validation and memory profiling
- Production integration with live YOLO tracker (beyond dataset debugger)
- Extended temporal tracking across video frames
- Ground-truth evaluation harness for dataset accuracy metrics

## Requirements

### Validated

- [x] Front-first rectangle/hex detection with typed contracts (Phase 1 — 01-01) — v1.0
- [x] Guarded temporal hold with score decay + basic/verbose debug rendering (Phase 1 — 01-02) — v1.0
- [x] Interactive dataset debugger with tiered diagnostics 0–3 (Phase 2 — 02-01) — v1.0
- [x] Per-stage detector instrumentation, observational only (Phase 2 — 02-01) — v1.0

### Active

(None — v1.0 milestone complete; define via `/gsd:new-milestone`)

### Out of Scope

- Train / fine-tune YOLO — model đã có
- YOLO Pose — chỉ dùng bbox + track_id
- Sửa YOLO tracker hiện tại — hex_detector là layer độc lập
- GPU / CUDA — CPU-only cho Pi 5
- FastAPI / web telemetry — MVP local
- Complex GUI, video tracking, ground-truth annotation, HTML reports

## Context

- Ultralytics YOLO tracking trả `track_id`, `bbox`, `confidence` cho cụm 4 block.
- Topology: front = A-B-E-F, right = B-C-D-E, polygon ngoài A→B→C→D→E→F, cạnh chung B-E.
- Module độc lập `src/hex_detector/` — không phụ thuộc block_detected.
- Greenfield pivot from Block Detected v1.x on 2026-06-30.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Front-first architecture | Detect rectangle before hex; never synthesize C/D | ✓ Good |
| Bounded candidates in config | Prevents combinatorial CPU explosion | ✓ Good |
| Stable RejectReason codes | Machine-readable rejection telemetry | ✓ Good |
| Single hold age counter | No double-aging between hold_or_clear and prune_missing | ✓ Good |
| Float geometry, int render | Precision preserved throughout pipeline | ✓ Good |
| Fresh HexDetector per image | Prevents EMA/hold leakage across dataset images | ✓ Good |
| Observational instrumentation only | Debugger must not alter detector decisions | ✓ Good |
| Split line-stage timings | hough/filter/group/merge for diagnostic clarity | ✓ Good |

---
*Last updated: 2026-07-03 after v1.0 milestone*
