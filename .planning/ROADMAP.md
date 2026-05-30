# Roadmap: Block Detected

## Overview

Deliver a Pi-compatible vision pipeline that detects one of four colored cube blocks without ArUco markers, returning ordered square-face corners, block identity, and optional robot pickup pose. Phases follow the natural pipeline order: contract API → camera capture → preprocess/contours → geometry/warp → CNN classification → pose/calibration → reject/integration → test/evaluation.

## Phases

**Phase Numbering:**
- Integer phases (1–8): Planned milestone work
- Decimal phases (e.g., 2.1): Urgent insertions via `/gsd-insert-phase`

- [x] **Phase 1: Contract & Pipeline Skeleton** - Public `detect_block` API wired to existing `DetectionResult` contract
- [x] **Phase 2: Camera & Capture** - Stable 640×480 acquisition with debug frame saving
- [ ] **Phase 3: Preprocess & Contour Detection** - Grayscale/threshold/morphology chain and square-face candidate finding
- [ ] **Phase 4: Corner Ordering, Warp & Geometry** - TL/TR/BR/BL ordering, perspective warp, center and angle
- [ ] **Phase 5: CNN Classification** - TFLite INT8 4-class classifier with training pipeline
- [ ] **Phase 6: Pose & Calibration** - Pixel-to-mm homography and robot pickup pose
- [ ] **Phase 7: Reject Logic & Integration** - Full end-to-end pipeline with safety reject paths
- [ ] **Phase 8: Test & Evaluation** - Labeled test set, offline metrics, integration smoke test

## Phase Details

### Phase 1: Contract & Pipeline Skeleton
**Goal**: Integrators can call `detect_block(frame)` and receive validated `DetectionResult` objects (stub pipeline acceptable)
**Depends on**: Nothing (first phase)
**Requirements**: CONT-01, CONT-02, CONT-03
**Success Criteria** (what must be TRUE):
  1. Calling `detect_block(frame)` returns a `DetectionResult` that passes contract validation helpers
  2. Successful stub/synthetic detection populates `block_id`, `confidence`, `center_px`, `corners_px` (TL, TR, BR, BL), and `angle_deg`
  3. Rejected or ambiguous frames return the correct `status` with `debug.rejection_reason` and no fabricated corner geometry
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Wave 0: unittest scaffold
- [x] 01-02-PLAN.md — Wave 1: package + `detect_block` stub
- [x] 01-03-PLAN.md — Wave 2: `MULTIPLE_CANDIDATES` fix + full validation

**Progress (2026-05-31):** Phase 1 complete — `detect_block`, package layout, 10 unittest tests green.

### Phase 2: Camera & Capture
**Goal**: Pipeline receives stable 640×480 frames from Pi Camera or USB with reproducible capture settings
**Depends on**: Phase 1
**Requirements**: CAM-01, CAM-02, CAM-03
**Success Criteria** (what must be TRUE):
  1. System captures 640×480 frames from Pi Camera (CSI) or USB camera via a single backend abstraction
  2. Exposure and white balance are locked when the hardware supports it, producing consistent frames under fixed lighting
  3. Raw frames (and optional debug overlays) are saved to a debug directory with monotonic frame identifiers
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Wave 0: pytest scaffolding, CaptureFrame/FrameSource, ImageSequenceFrameSource
- [x] 02-02-PLAN.md — Wave 1: PiCamera2 + USB adapters, CAM-02 metadata, create_frame_source, camera_smoke
- [x] 02-03-PLAN.md — Wave 2: DebugFrameWriter path/retention, CAM-03

### Phase 3: Preprocess & Contour Detection
**Goal**: Input frames yield filtered square-face contour candidates ready for geometry
**Depends on**: Phase 2
**Requirements**: GEO-01, GEO-02
**Success Criteria** (what must be TRUE):
  1. Preprocess chain converts BGR input through grayscale, blur, adaptive threshold or Canny, and morphology open/close
  2. Contour pass identifies 4-vertex convex quads within configured area min/max and ~1:1 aspect ratio bounds
  3. On reference images with a visible block face, at least one valid square candidate is found
**Plans**: TBD

### Phase 4: Corner Ordering, Warp & Geometry
**Goal**: Each candidate yields consistently ordered corners, a canonical face warp, and pixel pose geometry
**Depends on**: Phase 3
**Requirements**: GEO-03, GEO-04, GEO-05
**Success Criteria** (what must be TRUE):
  1. Corners are output in consistent TL, TR, BR, BL order regardless of block rotation in the frame
  2. `warpPerspective` produces a canonical 128×128 (or 160×160) face crop suitable for classification
  3. `center_px` equals the mean of ordered corners and `angle_deg` matches top-edge orientation (TR − TL)
**Plans**: TBD

### Phase 5: CNN Classification
**Goal**: Warped face crops are classified into four block identities with documented confidence
**Depends on**: Phase 4
**Requirements**: CLS-01, CLS-02, CLS-03
**Success Criteria** (what must be TRUE):
  1. TFLite INT8 model classifies a warped face crop into one of four block classes on target Pi hardware
  2. Classification confidence is exposed and mapped to `DetectionResult.confidence` with a documented acceptance threshold
  3. Training pipeline collects warped crops, trains a small CNN, and exports a deployable INT8 `.tflite` model
**Plans**: TBD

### Phase 6: Pose & Calibration
**Goal**: When calibration is present, pixel geometry converts to robot-ready pickup coordinates
**Depends on**: Phase 5
**Requirements**: POSE-01, POSE-02, POSE-03
**Success Criteria** (what must be TRUE):
  1. Calibration artifacts (table homography, robot origin offset, gripper offset; optional intrinsics) load without error
  2. When calibration is present, detection populates `pickup_pose` with `x_mm`, `y_mm`, and `theta_deg` derived from pixel center and angle
  3. Calibration procedure is documented using checkerboard or known table landmarks (no ArUco on blocks)
**Plans**: TBD

### Phase 7: Reject Logic & Integration
**Goal**: Full pipeline runs end-to-end with robust rejection for ambiguous or unsafe detections
**Depends on**: Phase 6
**Requirements**: REJ-01, REJ-02, REJ-03, REJ-04, REJ-05
**Success Criteria** (what must be TRUE):
  1. Frames with no contour passing geometry filters return `no_detection` status
  2. Classification below threshold returns `low_confidence`; invalid/skewed quads return `invalid_geometry`
  3. Multiple overlapping candidates return `multiple_candidates`; face area below minimum returns rejection with documented reason
  4. Integrated `detect_block` runs capture → preprocess → contours → geometry → classify → pose → reject in a single call
**Plans**: TBD

### Phase 8: Test & Evaluation
**Goal**: Pipeline accuracy and integration are measured against a real-world labeled test set
**Depends on**: Phase 7
**Requirements**: TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. Labeled test set covers all 4 blocks across varied rotation, distance, lighting, pallet, and partial occlusion
  2. Offline evaluator reports per-class accuracy, corner error, and false reject rate on the test set
  3. Integration smoke test runs camera → `detect_block` → JSON result on sample frames without manual intervention
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Contract & Pipeline Skeleton | 0/2 | Planned | - |
| 2. Camera & Capture | 0/3 | Not started | - |
| 3. Preprocess & Contour Detection | 0/TBD | Not started | - |
| 4. Corner Ordering, Warp & Geometry | 0/TBD | Not started | - |
| 5. CNN Classification | 0/TBD | Not started | - |
| 6. Pose & Calibration | 0/TBD | Not started | - |
| 7. Reject Logic & Integration | 0/TBD | Not started | - |
| 8. Test & Evaluation | 0/TBD | Not started | - |

---
*Roadmap created: 2026-05-31*
*Granularity: standard (8 phases)*
