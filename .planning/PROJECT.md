# Block Detected — Non-ArUco Cube Block Detection

## What This Is

A Raspberry Pi / edge vision pipeline that detects one of four colored cube blocks on a work table from a fixed camera (640×480), without ArUco markers. It returns precise square-face geometry (four ordered corners, center, rotation) plus block identity and optional robot pickup pose for a pick-and-place arm.

## Core Value

For every valid frame, the system must reliably output **which block (1–4)** with **correctly ordered four corners and angle** so the robot can pick — not just a bounding box.

## Requirements

### Validated

- ✓ **Output contract + public API (Phase 1)** — `detect_block`, contract validation, package layout. *(Phase 1, 2026-05-31)*
- ✓ **Camera capture (Phase 2)** — `FrameSource` (image_sequence, picamera2, usb), 640×480 BGR, CAM-02 metadata, `DebugFrameWriter`, `scripts/camera_smoke.py`. 20 pytest tests green. *(Phase 2, 2026-05-31)*

### Active

- [ ] Camera capture at 640×480 with stable exposure/WB and debug frame saving
- [ ] Preprocess pipeline: grayscale → blur → adaptive threshold/Canny → morphology
- [ ] Square-face detection via OpenCV contours (4-sided, area, aspect ratio, convex)
- [ ] Corner ordering: TL, TR, BR, BL
- [ ] Perspective warp to canonical face (128×128 or 160×160)
- [ ] Block classification: Mode B tiny CNN (TFLite INT8, 4 classes) — recommended path
- [ ] Pose: center, angle_deg, pixel→mm via table homography + calibration
- [ ] Confidence and reject logic (low geom/class confidence, tiny area, skew, overlap)
- [ ] Real-world test set and evaluation across angles, distance, lighting, occlusion

### Out of Scope

- **ArUco / AprilTag fiducials** — explicit project constraint; use contour + warp + CNN instead
- **YOLO-only detection** — does not deliver ordered corners + rotation required for grasp
- **Mode A template matching as primary** — optional fallback only; not default for v1
- **Multi-block simultaneous pick planning** — v1 targets single best candidate per frame; overlap → reject/multiple_candidates
- **Cloud inference** — on-device Pi inference required

## Context

- **Brownfield:** Repo already contains `detection_contract.py` with a richer contract than the minimal TS sketch (includes `status`, `bbox_px`, `face_area_px`, `label`, `debug`).
- **Target pipeline:** Contour → Warp → Tiny CNN → Corners/Pose → Pickup command.
- **Hardware:** Pi Camera or USB camera; robot needs mm pose from calibrated homography.
- **Blocks:** 4 distinct cube blocks; square top face visible; scenarios include rotation, distance, glare, pallet, partial occlusion.
- **References:** OpenCV contour/shape analysis; PyImageSearch corner ordering; LearnOpenCV document scanner homography; TensorFlow Lite image classifier workflow.

## Constraints

- **Tech**: Python 3, OpenCV, TensorFlow Lite (INT8), Pi-compatible — no ArUco dependency
- **Resolution**: 640×480 locked where possible
- **Latency**: Suitable for robot pick cycle (classify on 128×128 warp, not full-frame heavy models)
- **Accuracy**: Must beat template matching under lighting/view change; CNN is default
- **Output**: Must conform to existing `DetectionResult` contract in `detection_contract.py`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| No ArUco | User requirement; fiducials not on blocks | — Pending |
| Contour + warp + CNN over YOLO bbox | Robot needs 4 corners + θ, not axis-aligned box only | — Pending |
| Mode B (TFLite INT8 CNN) as v1 classifier | Robust to lighting/view vs template matching | — Pending |
| Warp size 128×128 (or 160×160) | Matches tiny CNN input; tradeoff TBD in Phase 4 | — Pending |
| Stdlib-only contract (no Pydantic) | Pi-friendly, zero extra deps at boundary | ✓ Good (Task 1) |
| Extend existing Python contract | Integration boundary for all pipeline stages | ✓ Good (Task 1) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-31 after Task 1 (output contract)*
