# Requirements: Block Detected (Non-ArUco)

**Defined:** 2026-05-31
**Core Value:** Reliable block ID plus four ordered corners and angle for robot pickup

## v1 Requirements

### Contract & Integration

- [x] **CONT-01**: Public `detect_block(frame)` returns validated `DetectionResult` matching `detection_contract.py` — Phase 1 *(2026-05-31)*
- [x] **CONT-02**: Successful detection populates `block_id`, `confidence`, `center_px`, `corners_px` (TL, TR, BR, BL), `angle_deg` — validated via contract samples + `validate_detection_result()` *(Task 1, 2026-05-31)*
- [x] **CONT-03**: Rejected/ambiguous frames return appropriate `status` with `debug.rejection_reason` (no fake geometry) — `SAMPLE_LOW_CONFIDENCE`, `SAMPLE_NO_DETECTION`, mismatch guard *(Task 1, 2026-05-31)*

### Camera & Capture

- [x] **CAM-01**: Capture 640×480 from Pi Camera or USB via stable backend abstraction — Phase 2 *(2026-05-31)*
- [x] **CAM-02**: Lock exposure and white balance when hardware supports it — Phase 2 *(2026-05-31)*
- [x] **CAM-03**: Save raw frames (and optional overlay) to debug directory with frame id — Phase 2 *(2026-05-31)*

### Preprocess & Geometry

- [x] **GEO-01**: Preprocess chain: BGR→gray, light blur, adaptive threshold or Canny, morphology open/close
- [x] **GEO-02**: Find square-face candidates via contours + `approxPolyDP` (4 vertices, convex, area min/max, aspect ~1:1)
- [x] **GEO-03**: Order corners consistently: top-left, top-right, bottom-right, bottom-left
- [x] **GEO-04**: `warpPerspective` face to canonical 128×128 (or 160×160) for classification
- [x] **GEO-05**: Compute `center_px` as mean of corners and `angle_deg` from top edge (e.g. atan2 TR−TL)

### Classification

- [x] **CLS-01**: Classify warped face into 4 block classes using TFLite INT8 CNN (Mode B default) — stub + optional `TfliteFaceClassifier` when model present
- [x] **CLS-02**: Expose classification confidence; map to `DetectionResult.confidence` with documented threshold
- [x] **CLS-03**: Training pipeline: collect warped crops, train small CNN, export TFLite INT8 for Pi — scaffold (`scripts/train_classifier.md`, `models/`)

### Pose & Calibration

- [x] **POSE-01**: Load calibration artifacts: camera intrinsics (optional), table homography, robot origin offset, gripper offset
- [x] **POSE-02**: Convert pixel center + `angle_deg` to `pickup_pose` (x_mm, y_mm, theta_deg) when calibration present
- [x] **POSE-03**: Document calibration procedure (checkerboard or known table landmarks — not ArUco on blocks) — `config/calibration.example.json`

### Reject & Safety

- [x] **REJ-01**: Reject when no contour passes geometry filters → `no_detection`
- [x] **REJ-02**: Reject when classification confidence below threshold → `low_confidence`
- [x] **REJ-03**: Reject invalid/skewed quads (corner angle/area heuristics) → `invalid_geometry`
- [x] **REJ-04**: Reject multiple overlapping candidates → `multiple_candidates`
- [x] **REJ-05**: Reject face area below minimum pixel threshold

### Test & Evaluation

- [x] **TEST-01**: Labeled test set: 4 blocks × varied rotation, distance, lighting, pallet, partial occlusion — fixture layout + README
- [x] **TEST-02**: Offline evaluator reports per-class accuracy, corner error, false reject rate — `scripts/eval_offline.py` scaffold
- [x] **TEST-03**: Integration smoke test: camera → detect → JSON result on sample frames

## v2 Requirements

### Classification

- **CLS-04**: Mode A template matching fallback when CNN uncertain (guarded, not primary)

### Runtime

- **RUN-01**: Multi-block scene graph (detect all, rank best pick)
- **RUN-02**: Temporal filtering / tracking across frames

### Ops

- **OPS-01**: Live tuning UI for threshold and reject parameters

## Out of Scope

| Feature | Reason |
|---------|--------|
| ArUco / AprilTag on blocks | Explicit project constraint |
| YOLO as primary detector | Bbox-only; insufficient for corner-ordered grasp |
| Cloud inference API | On-device Pi requirement |
| Template matching as v1 default | Fails under lighting/view change per user spec |
| Simultaneous multi-pick planning | v1 single best candidate per frame |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONT-01 | Phase 1 | Complete |
| CONT-02 | Phase 1 | Complete |
| CONT-03 | Phase 1 | Complete |
| CAM-01 | Phase 2 | Complete |
| CAM-02 | Phase 2 | Complete |
| CAM-03 | Phase 2 | Complete |
| GEO-01 | Phase 3 | Complete |
| GEO-02 | Phase 3 | Complete |
| GEO-03 | Phase 4 | Complete |
| GEO-04 | Phase 4 | Complete |
| GEO-05 | Phase 4 | Complete |
| CLS-01 | Phase 5 | Complete |
| CLS-02 | Phase 5 | Complete |
| CLS-03 | Phase 5 | Complete (scaffold) |
| POSE-01 | Phase 6 | Complete |
| POSE-02 | Phase 6 | Complete |
| POSE-03 | Phase 6 | Complete |
| REJ-01 | Phase 7 | Complete |
| REJ-02 | Phase 7 | Complete |
| REJ-03 | Phase 7 | Complete |
| REJ-04 | Phase 7 | Complete |
| REJ-05 | Phase 7 | Complete |
| TEST-01 | Phase 8 | Complete (scaffold) |
| TEST-02 | Phase 8 | Complete (scaffold) |
| TEST-03 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-31*
*Last updated: 2026-05-31 after Task 1 (CONT-02, CONT-03 complete)*
