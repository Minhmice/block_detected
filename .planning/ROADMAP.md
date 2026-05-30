# Roadmap: Block Detected

## Overview

Deliver a Pi-compatible vision pipeline that detects one of four colored cube blocks without ArUco markers, returning ordered square-face corners, block identity, and optional robot pickup pose. Phases follow the natural pipeline order: contract API → camera capture → preprocess/contours → geometry/warp → CNN classification → pose/calibration → reject/integration → test/evaluation.

## Phases

**Phase Numbering:**
- Integer phases (1–8): Planned milestone work
- Decimal phases (e.g., 2.1): Urgent insertions via `/gsd-insert-phase`

- [x] **Phase 1: Contract & Pipeline Skeleton** - Public `detect_block` API wired to existing `DetectionResult` contract
- [x] **Phase 2: Camera & Capture** - Stable 640×480 acquisition with debug frame saving
- [x] **Phase 3: Preprocess & Contour Detection** - Grayscale/threshold/morphology chain and square-face candidate finding
- [x] **Phase 4: Corner Ordering, Warp & Geometry** - TL/TR/BR/BL ordering, perspective warp, center and angle
- [x] **Phase 5: CNN Classification** - TFLite INT8 4-class classifier with training pipeline
- [x] **Phase 6: Pose & Calibration** - Pixel-to-mm homography and robot pickup pose
- [x] **Phase 7: Reject Logic & Integration** - Full end-to-end pipeline with safety reject paths
- [x] **Phase 8: Test & Evaluation** - Labeled test set, offline metrics, integration smoke test
- [ ] **Phase 9: Next.js + FastAPI detection console UI** - WebSocket telemetry, MJPEG stream, Docker Compose
- [ ] **Phase 10: Real camera on dev machine** - Live USB/Pi camera feed without mock mode

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
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Wave 0: `preprocess.py`, GEO-01 masks, `vision.example.json`, `test_preprocess.py`
- [x] 03-02-PLAN.md — Wave 1: `detector.py`, GEO-02 square candidates, `test_detector.py`
- [x] 03-03-PLAN.md — Wave 2: `vision.py` frame helper + overlay, `square_face.png` fixture, integration tests

**Progress (2026-05-31):** Phase 3 complete — preprocess, detector, vision helper; 37 pytest tests green.

### Phase 4: Corner Ordering, Warp & Geometry
**Goal**: Each candidate yields consistently ordered corners, a canonical face warp, and pixel pose geometry
**Depends on**: Phase 3
**Requirements**: GEO-03, GEO-04, GEO-05
**Success Criteria** (what must be TRUE):
  1. Corners are output in consistent TL, TR, BR, BL order regardless of block rotation in the frame
  2. `warpPerspective` produces a canonical 128×128 (or 160×160) face crop suitable for classification
  3. `center_px` equals the mean of ordered corners and `angle_deg` matches top-edge orientation (TR − TL)
**Plans**: executed (autonomous)

**Progress (2026-05-31):** `geometry.py` — order_corners, warp 128×128, center/angle.

### Phase 5: CNN Classification
**Goal**: Warped face crops are classified into four block identities with documented confidence
**Depends on**: Phase 4
**Requirements**: CLS-01, CLS-02, CLS-03
**Success Criteria** (what must be TRUE):
  1. TFLite INT8 model classifies a warped face crop into one of four block classes on target Pi hardware
  2. Classification confidence is exposed and mapped to `DetectionResult.confidence` with a documented acceptance threshold
  3. Training pipeline collects warped crops, trains a small CNN, and exports a deployable INT8 `.tflite` model
**Plans**: executed (autonomous)

**Progress (2026-05-31):** `classifier.py` — stub + optional TFLite; `train_classifier.md` scaffold.

### Phase 6: Pose & Calibration
**Goal**: When calibration is present, pixel geometry converts to robot-ready pickup coordinates
**Depends on**: Phase 5
**Requirements**: POSE-01, POSE-02, POSE-03
**Success Criteria** (what must be TRUE):
  1. Calibration artifacts (table homography, robot origin offset, gripper offset; optional intrinsics) load without error
  2. When calibration is present, detection populates `pickup_pose` with `x_mm`, `y_mm`, and `theta_deg` derived from pixel center and angle
  3. Calibration procedure is documented using checkerboard or known table landmarks (no ArUco on blocks)
**Plans**: executed (autonomous)

**Progress (2026-05-31):** `calibration.py`, `calibration.example.json`.

### Phase 7: Reject Logic & Integration
**Goal**: Full pipeline runs end-to-end with robust rejection for ambiguous or unsafe detections
**Depends on**: Phase 6
**Requirements**: REJ-01, REJ-02, REJ-03, REJ-04, REJ-05
**Success Criteria** (what must be TRUE):
  1. Frames with no contour passing geometry filters return `no_detection` status
  2. Classification below threshold returns `low_confidence`; invalid/skewed quads return `invalid_geometry`
  3. Multiple overlapping candidates return `multiple_candidates`; face area below minimum returns rejection with documented reason
  4. Integrated `detect_block` runs capture → preprocess → contours → geometry → classify → pose → reject in a single call
**Plans**: executed (autonomous)

**Progress (2026-05-31):** Full `detect_block` pipeline with all reject paths.

### Phase 8: Test & Evaluation
**Goal**: Pipeline accuracy and integration are measured against a real-world labeled test set
**Depends on**: Phase 7
**Requirements**: TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. Labeled test set covers all 4 blocks across varied rotation, distance, lighting, pallet, and partial occlusion
  2. Offline evaluator reports per-class accuracy, corner error, and false reject rate on the test set
  3. Integration smoke test runs camera → `detect_block` → JSON result on sample frames without manual intervention
**Plans**: executed (autonomous)

**Progress (2026-05-31):** `eval_offline.py`, integration tests; 50 pytest tests green.

### Phase 9: Next.js + FastAPI detection console UI with WebSocket telemetry, MJPEG stream, and Docker Compose

**Goal:** Operators run a Next.js cyber-console against a FastAPI wrapper that streams MJPEG, pushes WebSocket telemetry, and controls the existing `detect_block` pipeline (mock mode on dev, real camera on Pi).
**Depends on:** Phase 8
**Requirements**: UI-09-01, UI-09-02, UI-09-03, UI-09-04, UI-09-05, UI-09-06, UI-09-07, UI-09-08
**Success Criteria** (what must be TRUE):
  1. Browser shows live 640×480 MJPEG feed and Canvas overlay aligned to detection corners
  2. WebSocket delivers FPS, latency, and camelCase detection JSON matching TypeScript types
  3. All console buttons call real REST endpoints (start/stop/params/calibration/dataset save)
  4. `MOCK_CAMERA=true` runs full UI without USB/Pi camera
  5. `npm run dev:all` and `docker compose up` documented and working
**Plans:** 7 plans

Plans:
- [ ] 09-01-PLAN.md — Wave 0: wire golden fixture, API test scaffold, dev:all, .env.example
- [ ] 09-02-PLAN.md — Wave 1: Pydantic wire schemas, mock frame factory, /health + CORS
- [ ] 09-03-PLAN.md — Wave 2: detection loop, MJPEG, WebSocket, REST routes
- [ ] 09-04-PLAN.md — Wave 3: Next.js scaffold, Tailwind tokens, Zustand, api/ws libs
- [ ] 09-05-PLAN.md — Wave 4: AppShell, camera, overlay, detection controls
- [ ] 09-06-PLAN.md — Wave 4: classification, telemetry, calibration/dataset, log terminal
- [ ] 09-07-PLAN.md — Wave 5: Docker Compose, README, integration UAT checkpoint

### Phase 10: Real camera capture on dev machine (no mock — USB/Pi camera live feed)

**Goal:** Dev machine runs live camera capture (USB or built-in) end-to-end through the console — no `MOCK_CAMERA`, no image sequence fallback
**Depends on:** Phase 9
**Requirements**: TBD (CAM-10-xx to be defined in plan)
**Success Criteria** (what must be TRUE):
  1. TBD (run `/gsd-plan-phase 10`)
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 10 to break down)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → … → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Contract & Pipeline Skeleton | 3/3 | Complete | 2026-05-31 |
| 2. Camera & Capture | 3/3 | Complete | 2026-05-31 |
| 3. Preprocess & Contour Detection | 3/3 | Complete | 2026-05-31 |
| 4. Corner Ordering, Warp & Geometry | 1/1 | Complete | 2026-05-31 |
| 5. CNN Classification | 1/1 | Complete | 2026-05-31 |
| 6. Pose & Calibration | 1/1 | Complete | 2026-05-31 |
| 7. Reject Logic & Integration | 1/1 | Complete | 2026-05-31 |
| 8. Test & Evaluation | 1/1 | Complete | 2026-05-31 |
| 9. Next.js + FastAPI detection console UI | 0/7 | In progress | — |
| 10. Real camera on dev machine | 0/0 | Not planned | — |

---
*Roadmap created: 2026-05-31*
*Granularity: standard (8 phases)*
