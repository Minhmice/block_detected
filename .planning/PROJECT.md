# Hex Detector — Block Face Geometry on Raspberry Pi 5

## What This Is

MVP thư viện CPU-only (OpenCV + NumPy) chạy trên Raspberry Pi 5, nhận bbox YOLO tracking cho cụm 4 block trên pallet và trích xuất 6 điểm A–F mô tả hai mặt front/right của block. Không train model, không sửa YOLO tracker hiện tại.

## Core Value

Từ mỗi bbox YOLO đã track, ổn định và chính xác trả về topology hex A–F (hoặc rectangle A,B,E,F khi mặt right quá hẹp) để điều khiển robot/lấy tọa độ mặt block.

## Requirements

### Validated

- [x] Front-first rectangle/hex detection with typed contracts (Phase 1 — 01-01)
- [x] Guarded temporal hold with score decay + basic/verbose debug rendering (Phase 1 — 01-02)

### Active

(None — Phase 1 delivered complete MVP)

### Out of Scope

- Train / fine-tune YOLO — model đã có
- YOLO Pose — chỉ dùng bbox + track_id
- Sửa YOLO tracker hiện tại — hex_detector là layer độc lập
- GPU / CUDA — CPU-only cho Pi 5
- FastAPI / web telemetry — MVP local

## Context

- Ultralytics YOLO tracking trả `track_id`, `bbox`, `confidence` cho cụm 4 block.
- Topology: front = A-B-E-F, right = B-C-D-E, polygon ngoài A→B→C→D→E→F, cạnh chung B-E.
- Module độc lập `src/hex_detector/` — không phụ thuộc block_detected.
- 31/31 tests pass, 14/14 must-have truths verified.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Front-first architecture | Detect rectangle before hex; never synthesize C/D | ✓ Good |
| Bounded candidates in config | Prevents combinatorial CPU explosion | ✓ Good |
| Stable RejectReason codes | Machine-readable rejection telemetry | ✓ Good |
| Single hold age counter | No double-aging between hold_or_clear and prune_missing | ✓ Good |
| Float geometry, int render | Precision preserved throughout pipeline | ✓ Good |

---
*Last updated: 2026-06-30 after Phase 1 completion*
