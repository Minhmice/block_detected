# Roadmap: Block Detected

## Overview

v1: YOLO webcam + runtime + GUI + web API (phases 1–14).
v2.0: Standalone classical CV hexagon detector in `block_detection_v2`.

## Phases (v2.0 milestone)

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 15 | block_detection_v2 classical CV module | Runnable OpenCV-only hexagon pipeline | ISO-*, PIP-*, POL-* | ✓ |
| 16 | Relaxed multi-block + image folder viewer | block_dataset UAT, arrow nav, multi-block | V2-IMG-*, V2-MULTI-*, V2-RELAX-* | ✓ |
| 17 | ROI-fit-score detection pipeline | Integrate spike-validated ROI → line fit → scoring | SPIKE-ROI-*, SPIKE-FIT-*, SPIKE-SCORE-*, SPIKE-BENCH-* | ✓ |
| 18 | YOLO block detection first pass | YOLO `rbs-final.pt` detects blocks first; CV hex on crop | YOLO-01 … YOLO-04 | ✓ |

### Phase 15: block_detection_v2 classical CV module

**Goal:** Deliver isolated `src/block_detection_v2/` package runnable via `python -m block_detection_v2.main`.

**Depends on:** Nothing (greenfield module; no v1 coupling)

**Requirements:** ISO-01, ISO-02, PIP-01 … PIP-09, POL-01

**Success criteria:**

1. All 11 module files exist per schema; no imports outside `block_detection_v2`
2. Live loop shows FPS, hexagon A–F, front/right faces, block split lines, center, yaw
3. Tracker smooths points; rejects large jumps; holds last pose ≤4 frames when lost
4. Frame dict matches specified output shape
5. `PYTHONPATH=src python -m block_detection_v2.main` starts without import errors

**Plans:**

- [x] 15-01-PLAN.md — module scaffold, pipeline, entry smoke test

### Phase 16: Relaxed multi-block detection and image folder viewer

**Goal:** Dataset-driven UAT on `block_dataset/`: relaxed detection score, multi-block, `image_source.py` with arrow navigation.

**Depends on:** Phase 15

**Requirements:** V2-IMG-01, V2-IMG-02, V2-MULTI-01, V2-MULTI-02, V2-RELAX-01

**Success criteria:**

1. `image_source.py` serves 108 images from `block_dataset/` with natural sort
2. Left/right arrows change image; overlay shows `[n/N] filename`
3. Multiple blocks detected and tracked when present in frame
4. `DETECTION_SCORE_MIN` tunable in config for looser matching

**Plans:**

- [x] 16-01-PLAN.md — image source, multi-block, relaxed thresholds

### Phase 17: ROI-fit-score detection pipeline

**Goal:** Replace contour-only hexagon detection with spike-validated pipeline: ROI cluster mask → Hough-assisted A–F fit → composite scoring; maintain dt1–dt108 benchmark.

**Depends on:** Phase 16

**Requirements:** SPIKE-ROI-01, SPIKE-ROI-02, SPIKE-FIT-01, SPIKE-FIT-02, SPIKE-SCORE-01, SPIKE-SCORE-02, SPIKE-BENCH-01

**Success criteria:**

1. `main.py` uses ROI + line fit + scoring; Hough lines no longer discarded
2. 3-block silhouette (right trim); label/logo false positives rejected vs legacy contour path
3. Benchmark harness runs on 108 images; accept rate ≥ 80% (baseline spike: 84%)
4. `find_hexagons` demoted to fallback; primary path is ROI-fit-score

**Plans:** 4 plans

Plans:

- [x] 17-01-PLAN.md — ROI module + config constants
- [x] 17-02-PLAN.md — fit.py + wire Hough lines
- [x] 17-03-PLAN.md — score.py + full pipeline
- [x] 17-04-PLAN.md — benchmark harness

### Phase 18: YOLO block detection first pass with rbs-final.pt

**Goal:** Add YOLO first-pass block detection in `block_detection_v2` using `models/rbs-final.pt`. Pipeline becomes: **YOLO finds block bbox(s) first** → classical CV (ROI/fit/score) runs on each crop instead of full-frame edge CC.

**Depends on:** Phase 17

**Requirements:** YOLO-01, YOLO-02, YOLO-03, YOLO-04

**Success criteria:**

1. `yolo_detector.py` loads `models/rbs-final.pt` via Ultralytics; no imports from v1 `block_detected`
2. `detect()` returns sorted `YoloBlockBox` list (xyxy, conf, class)
3. `pipeline.py` uses YOLO bbox as primary ROI seed; edge-CC ROI is fallback when YOLO misses
4. `main.py` TODO removed; benchmark still ≥80% accept on `block_dataset/`

**Plans:** 4 plans
Plans:
**Wave 1**

- [x] 18-01-PLAN.md — YOLO config + yolo_detector tests (YOLO-01/02)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 18-02-PLAN.md — roi_from_bbox from YOLO xyxy

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 18-03-PLAN.md — pipeline YOLO-first + edge-CC fallback

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 18-04-PLAN.md — main cleanup, benchmark meta, docs, ≥80% gate

---

## Archived v1 phases (1–14)

See prior ROADMAP sections in git history. Phases 1–7 complete; 8–14 deferred on v1.x track.
