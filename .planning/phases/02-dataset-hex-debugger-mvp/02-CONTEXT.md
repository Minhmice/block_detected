# Phase 2: Dataset Hex Debugger MVP - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Create one MVP script, `scripts/debug_hex_dataset.py`, that naturally iterates images in `block_dataset/`, runs `models/son-down.pt`, converts every YOLO box into the existing typed `src/hex_detector` API, creates a fresh detector per image, and provides keyboard-driven OpenCV inspection plus lightweight/full debug exports. The phase may add only the minimum instrumentation fields needed in the existing detector debug payload; it must not alter detector decisions, scoring, geometry, or result schema.

Out of scope: complex GUI, video tracking, ground-truth annotation, HTML reports, detector algorithm changes, or new application architecture.

</domain>

<decisions>
## Implementation Decisions

### Script and CLI contract
- **D-01:** Add exactly one new source file: `scripts/debug_hex_dataset.py`. Minimal edits to existing `src/hex_detector` files are allowed only to expose missing debug instrumentation; do not create additional source modules or new dataclasses when existing models suffice.
- **D-02:** Support the exact CLI options `--images`, `--model`, `--conf`, `--iou`, `--imgsz`, `--device`, `--output`, `--start-index`, and `--debug-level 0|1|2|3`. The documented baseline command uses `block_dataset`, `models/son-down.pt`, confidence `0.35`, device `cpu`, and output `runs/debug_hex`.
- **D-03:** Sort dataset images naturally (`dt1.jpg`, `dt2.jpg`, `dt10.jpg`), not lexicographically. Handle unreadable images, empty boxes, and images with no YOLO detections.
- **D-04:** For each image, run `load → YOLO predict → list[YoloDetection] → new HexDetector → detect_frame → render → cv2.imshow`. Assign fake `track_id` values from box order. Construct a new detector for every image so hold and EMA never leak across dataset images.

### Debug levels
- **D-05:** Level 0 shows the original image plus YOLO bbox, confidence, fake track ID, result mode/status/total score, and reject reason.
- **D-06:** Level 1 adds effective ROI bbox, winning/selected lines, A-F point labels, rectangle/hex polygon, and the existing six-field score breakdown.
- **D-07:** Level 2 adds raw Hough lines, filtered/pre-merge information needed to explain grouping, merged `vertical`/`front_horizontal`/`right_diagonal` groups with counts, and a separate Canny edge-map window.
- **D-08:** Level 3 adds top candidates when supported, validation PASS/FAIL and reason, candidate score/intersections, selected-line angle and length, and per-stage timing. Candidate collections must remain bounded by existing config limits.

### Instrumentation source
- **D-09:** The detector is the single source of truth for debug data. Do not rerun preprocessing, Hough, grouping, candidate generation, or scoring inside the script; replaying would risk result divergence and roughly double CPU cost.
- **D-10:** Extend the existing debug payload only with the minimum data/timing required by levels 2-3 (for example edges, raw/filtered lines, pre-merge/merged groups, bounded candidate summaries, validation outcome, and stage timings). Instrumentation must observe the actual selected run.
- **D-11:** Instrumentation must not change `DetectionResult`, mode/status/reject semantics, scoring weights, thresholds, candidate selection, geometry, or temporal behavior. Heavy debug data stays in the non-serialized `debug` payload unless the script explicitly sanitizes it for a full snapshot.

### Persistence and controls
- **D-12:** Automatically write a lightweight JSON record for every processed image. It includes image metadata, YOLO boxes, each `DetectionResult.to_dict()` value, A-F points, mode/status/reject reason, score breakdown, line/group counts, and timings; it must omit heavyweight image arrays and raw object graphs.
- **D-13:** `J` writes a full debug snapshot and also saves the current overlay and edge map. `S` saves the overlay, and `E` saves the edge map independently.
- **D-14:** Use output layout `runs/debug_hex/overlays/`, `runs/debug_hex/edges/`, `runs/debug_hex/debug_json/`, plus `runs/debug_hex/debug.log`. File names must be deterministic per source image and safe to overwrite when rerunning that image.
- **D-15:** Keyboard controls are fixed: Right/D next, Left/A previous, 0-3 switch debug level, R rerun current image, S overlay, E edge map, J full snapshot, Q/ESC exit.

### Config reload and state
- **D-16:** Use `debug_config.json` for tuning. Pressing `R` rereads the JSON, validates/builds a fresh `HexDetectorConfig`, creates a new `HexDetector`, reruns YOLO + hex detection for the current image, and refreshes outputs.
- **D-17:** Never use `importlib` to reload `config.py`. A config parse/validation failure prints and logs the full traceback and keeps the last valid interactive session state; initial config failure is fatal.

### Error and logging policy
- **D-18:** Per-image load, YOLO inference, detector, render, or export errors print and log a full traceback, mark the image as failed, and allow navigation to continue. Import failure, model initialization failure, or initial config initialization failure terminates the program with a nonzero exit.
- **D-19:** Print a clear block per image covering image name, YOLO box count/details, result mode/status/score/rejection, raw/filtered/grouped/merged counts, six score components, and YOLO/hex/total timing. Mirror console diagnostics to `debug.log`; do not suppress exceptions.
- **D-20:** After implementation, run syntax and import checks and document an exact Windows PowerShell command. The handoff must list the created file, run command, actual APIs used, and any minimal `hex_detector` instrumentation changes.

### the agent's Discretion
- Choose the default location and bootstrap behavior for `debug_config.json` (project root versus output root), provided `R` uses that same documented path and no extra Python source file is introduced.
- Choose a JSON-safe representation for `LineSegment`, `LineGroups`, NumPy scalars, and bounded candidates; arrays such as the Canny image are saved as image artifacts rather than embedded in lightweight JSON.
- Choose OpenCV window names, resize-to-fit behavior, overlay colors, and layout while preserving full-resolution saved artifacts and the fixed information hierarchy per debug level.
- Choose the bounded top-candidate count and minimal candidate summary fields when current detector internals can expose them without changing selection logic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and prior-phase contracts
- `.planning/PROJECT.md` — CPU-only Pi 5 constraints, greenfield module boundary, and project core value.
- `.planning/phases/01-core-cv-pipeline/01-CONTEXT.md` — Locked detector API, output, score, debug, and temporal decisions.
- `.planning/phases/01-core-cv-pipeline/01-02-SUMMARY.md` — Actual Phase 1 implementation outcome and changed debug/config behavior.

No external specifications or ADRs were referenced.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/hex_detector/detector.py`: `HexDetector(config=None)` and `detect_frame(frame, detections: Sequence[YoloDetection]) -> list[DetectionResult]`; `detect_roi()` already drives the real ROI pipeline.
- `src/hex_detector/models.py`: `BBox`, `YoloDetection(track_id, bbox, confidence)`, `DetectionResult`, `ScoreBreakdown`, `LineSegment`, and `LineGroups` are reusable; `HexResult` is a compatibility alias.
- `src/hex_detector/config.py`: `HexDetectorConfig` already centralizes detector and debug settings, including `debug_mode="basic"|"verbose"` and bounded candidate/config limits.
- `src/hex_detector/renderer.py`: `render_debug(frame, results, cfg)` already renders bbox, winning geometry, status, score, points, rejection, and verbose merged groups.
- `scripts/batch_hex_son_down.py`: Proven model import, YOLO `boxes.xyxy/conf` conversion into `BBox`/`YoloDetection`, fresh-detector-per-image call, and overlay flow.

### Established Patterns
- `DetectionResult.to_dict()` serializes track ID, mode, points, score, ROI bbox, reject reason, status, and score breakdown, but intentionally excludes the heterogeneous `debug` payload.
- Basic detector debug currently contains `winning_lines` and `roi_size`; verbose additionally contains merged `groups`. It does not currently expose raw/filtered lines, Canny edges, top candidates, validation history, or stage timing.
- Score breakdown already exposes `edge_support`, `parallelism`, `topology`, `area_position`, `temporal`, and `total`; the script must consume it rather than recompute scoring.
- Existing batch script uses ordinary `sorted()`, fixed inference arguments, and noninteractive saving; the new script must add natural sort, full CLI control, navigation, runtime config, and tiered diagnostics.

### Integration Points
- Use the same `ROOT/src` import setup and `YOLO` construction pattern as `scripts/batch_hex_son_down.py`.
- Convert each Ultralytics box to `YoloDetection(track_id=i+1, bbox=BBox(...), confidence=...)` using actual float `xyxy` values.
- Feed the returned typed results directly to `render_debug`; use `to_dict()` as the lightweight JSON base and separately sanitize `result.debug` only for full snapshots.
- Add instrumentation at the existing `detect_roi()` stage boundaries so timing/debug data reflects the exact winning run.

</code_context>

<specifics>
## Specific Ideas

Baseline command:

```powershell
python scripts/debug_hex_dataset.py `
  --images block_dataset `
  --model models/son-down.pt `
  --conf 0.35 `
  --device cpu `
  --output runs/debug_hex
```

Console output should preserve the requested IMAGE / YOLO boxes / BOX / RESULT / REJECT / LINES / GROUPS / MERGED / SCORE / TIMING sections so a developer can compare images quickly while tuning.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within the single-script dataset-debugger boundary.

</deferred>

---

*Phase: 2-Dataset Hex Debugger MVP*
*Context gathered: 2026-07-01*
