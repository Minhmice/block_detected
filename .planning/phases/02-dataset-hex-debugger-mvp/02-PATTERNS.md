# Phase 2 Pattern Map — Dataset Hex Debugger MVP

**Scope:** one new script plus minimum observational edits to the existing detector
**Generated:** 2026-07-01

## Data Flow

CLI → natural image list → image decode → one YOLO predict call → `BBox`/`YoloDetection` conversion → fresh configured `HexDetector` → `detect_frame()` → `render_debug()` → level-specific overlay/windows → console/log → lightweight JSON; keys navigate, rerun, or save full artifacts.

## Existing Analogs

| Target | Closest existing code | Reuse exactly | Extend carefully |
|---|---|---|---|
| `scripts/debug_hex_dataset.py` | `scripts/batch_hex_son_down.py` | ROOT/src import setup, `YOLO` load, `boxes.xyxy/conf` conversion, fake IDs, fresh detector, renderer call | argparse, natural sort, navigation loop, level overlays, logging, JSON/config reload |
| Detector instrumentation | `src/hex_detector/detector.py` | actual crop/preprocess/Hough/filter/group/merge/candidate flow and `_build_debug_payload()` | capture existing intermediate values/timings without extra CV calls or selection changes |
| JSON result | `src/hex_detector/models.py` | `DetectionResult.to_dict()`, score-breakdown serialization, line dataclasses | script-local sanitizer for debug-only objects; no new model/dataclass |
| Base visualization | `src/hex_detector/renderer.py` | bbox, status, total score, reject reason, winning lines, polygon/points, score components | script overlays confidence/counts/selected-line metrics and controls extra edge window |
| Runtime tuning | `src/hex_detector/config.py` | dataclass defaults and `validate()` | whitelist JSON keys with `dataclasses.fields`, instantiate a fresh config, never reload module |

## Exact API Links

- `YOLO(str(model_path)).predict(frame, conf=conf, iou=iou, imgsz=imgsz, device=device, verbose=False)` → first `Results` item.
- `YoloDetection(track_id=i + 1, bbox=BBox(float(x1), float(y1), float(x2), float(y2)), confidence=float(conf))`.
- `HexDetector(config).detect_frame(frame, detections)` → `list[DetectionResult]`.
- `render_debug(frame, results, config)` → copied overlay image.
- `DetectionResult.to_dict()` → lightweight JSON base; `result.debug` remains separate.

## Instrumentation Boundaries

- Add `perf_counter()` and debug assignments around existing statements; do not call stage functions twice.
- Keep current basic payload stable (`winning_lines`, `roi_size`).
- Under verbose mode add edges, raw/filtered lines, pre-merge groups, merged groups, bounded candidate summaries, validation, and timings.
- Attach partial debug to rejection paths using only values produced before the rejection.
- Do not touch scoring weights, comparison operators, candidate ordering, returned mode/status, point smoothing, or result fields.

## Landmines

- Ordinary `sorted(Path.glob())` puts `dt10.jpg` before `dt2.jpg`; use a numeric token key.
- `waitKeyEx` codes vary by backend; support D/A plus known arrow codes.
- `DetectionResult.to_dict()` excludes debug by design; full J snapshots must sanitize it explicitly.
- NumPy arrays and `LineSegment`/`LineGroups` are not JSON serializable without conversion.
- One `HexDetector` reused across images would activate EMA/hold and invalidate independent dataset evaluation.
- Reloading `config.py` with `importlib` leaves mixed module/class state; rebuild from validated JSON instead.

## Plan Shape

One plan, three tasks:

1. Add non-invasive verbose instrumentation to `detector.py` and prove Phase 1 tests remain green.
2. Create the single interactive script with CLI, navigation, exports, logging, and JSON config reload.
3. Run syntax/import/help/regression checks and document the PowerShell smoke command.
