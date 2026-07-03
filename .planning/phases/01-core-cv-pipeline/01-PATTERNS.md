# Phase 1 Pattern Map — Core CV Pipeline

**Scope inspected:** `src/hex_detector/` only
**Generated:** 2026-06-30

## Data Flow

`HexDetector.detect_frame()` → padded/smoothed bbox → cropped ROI → preprocessed edges → raw/filtered/grouped lines → front-face candidates → optional right-face upgrade → topology validation → score breakdown → temporal state → typed result → debug renderer.

## File Roles and Closest Existing Patterns

| File | Current role | Pattern to preserve | Required evolution |
|---|---|---|---|
| `src/hex_detector/models.py` | Dataclasses for bbox, lines, points, and results | Typed values cross module boundaries | Add typed status, rejection codes, score breakdown, and debug payload; keep geometry as float |
| `src/hex_detector/config.py` | Single source of tunable constants | No detector magic numbers | Add hold guards, score decay, edge-support floor, debug mode, and verbose candidate limit |
| `src/hex_detector/preprocessing.py` | ROI extraction and fixed OpenCV preprocessing chain | Small pure functions with empty-input guards | Reuse unchanged unless result typing requires a narrow signature update |
| `src/hex_detector/lines.py` | Hough detection, filtering, grouping, merge, combinations | Group-specific line classification and bounded candidate search | Split front combinations from optional right-face combinations; bound both searches deterministically |
| `src/hex_detector/geometry.py` | Intersections, validation, scoring | Pure geometry/scoring helpers | Add front quadrilateral construction/validation and return component score breakdown instead of total-only scoring |
| `src/hex_detector/detector.py` | Pipeline orchestration | Public batch entry point delegates one ROI at a time | Expose internal `detect_roi`; run front-first branch, optional hex upgrade, stable rejection mapping, and present-track hold fallback |
| `src/hex_detector/tracker.py` | Per-track EMA and last-good storage | One `_TrackState` per `track_id` | Store last-good bbox/result and advance hold age exactly once per frame with IoU/jump/conflict guards |
| `src/hex_detector/renderer.py` | OpenCV overlay | Convert float coordinates to int only at draw time | Basic draws winner only; verbose adds grouped lines and top candidates |
| `src/hex_detector/__init__.py` | Public exports | Narrow package API | Export typed result/status/rejection/score contracts with compatibility naming if retained |

## Reusable Assets

- `BBox.pad()`, `BBox.clamp()`, and current bbox EMA are the correct place to keep ROI coordinates bounded.
- `LineGroups` and `merge_line_groups()` already provide bounded classified inputs for two-stage candidate generation.
- `line_intersection()`, `is_convex_polygon()`, and `polygon_area()` are reusable for both four-point and six-point validation.
- Existing component functions (`edge_support_score`, `parallelism_score`, `topology_score`, `area_position_score`, `temporal_similarity_score`) provide the score breakdown inputs.
- `DetectionResult.to_dict()` is the serialization boundary; internal detector/tracker/renderer communication remains typed.

## Landmines to Address

- `pick_line_combinations()` currently requires 3 vertical + 2 front-horizontal + 2 diagonal lines, so a genuine rectangle with no right-face support can never become a candidate.
- `validate_hex_points()` permits `right_too_narrow` to continue, but this still depends on synthesized C,D intersections; it is not an independent rectangle path.
- `score_candidate()` returns only the weighted total and its topology helper constructs a fresh config, which can diverge from the active config.
- `hold_or_clear()` and `prune_missing()` both advance `miss_frames`; hold age must have a single owner.
- Present-track CV failure currently returns `not_detected` immediately instead of consulting last-good state.
- Renderer currently treats every grouped line as selected, which makes default overlays noisy.

## Plan Boundaries

- **01-01:** typed result contract plus front-first rectangle and optional hex upgrade; proves a real `detect_frame()` path.
- **01-02:** guarded temporal hold, stable rejection behavior, score/debug observability, and Pi-friendly rendering; depends on 01-01 result types.
