# Phase 2 Research — Dataset Hex Debugger MVP

**Researched:** 2026-07-01
**Question:** What is needed to plan a correct one-file interactive dataset debugger around the existing YOLO and `hex_detector` APIs?

## Recommendation

Build one orchestration script around the proven flow in `scripts/batch_hex_son_down.py`, and add observational instrumentation only at existing `HexDetector.detect_roi()` stage boundaries. Do not duplicate preprocessing/scoring in the script. Use the typed result as the lightweight record and separately sanitize the heterogeneous debug payload for full snapshots.

## Confirmed External APIs

### Ultralytics prediction

Official predict-mode documentation confirms:

- `model.predict(source, conf=..., iou=..., imgsz=..., device=..., verbose=False)` is the correct inference surface.
- Defaults are `conf=0.25`, `iou=0.7`, and `imgsz=640`; this phase intentionally overrides confidence to `0.35` while retaining explicit CLI control.
- A predict call returns a list of `Results`; detection boxes expose `boxes.xyxy` as `(N,4)` pixel coordinates and `boxes.conf` as `(N,)` confidence values.
- Moving only the box tensors to CPU before NumPy conversion is valid; the existing repository pattern (`boxes.xyxy[i].cpu().numpy()` and `boxes.conf[i].item()`) is already correct.

Source: [Ultralytics Predict mode](https://docs.ultralytics.com/modes/predict)

### OpenCV HighGUI input

Official HighGUI documentation confirms:

- `cv2.imshow()` needs periodic `waitKey`, `waitKeyEx`, or `pollKey` calls for GUI event processing.
- `cv2.waitKeyEx(0)` is appropriate for blocking image-by-image navigation and returns the full key code.
- Arrow-key codes are backend-specific (Win32/QT/GTK), so portable navigation must accept D/A and a small documented set of backend arrow codes rather than assuming one universal integer.
- Window-close detection can use `cv2.getWindowProperty()` where the backend supports it; Q/ESC remains the reliable primary exit path.

Source: [OpenCV HighGUI reference](https://docs.opencv.org/master/d7/dfc/group__highgui.html)

### Dataclass-backed JSON config

Python documentation confirms `dataclasses.fields(HexDetectorConfig)` is the supported way to enumerate real config fields. This enables strict whitelisting of JSON keys before calling `HexDetectorConfig(**values)`. `dataclasses.asdict()` recursively deep-copies nested structures, so it is reasonable for the small config object but should not be used blindly on debug payloads containing NumPy edge arrays.

Source: [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)

## Confirmed Repository Contracts

- `HexDetector(config: HexDetectorConfig | None = None)` validates config at construction.
- `detect_frame(frame, detections: Sequence[YoloDetection]) -> list[DetectionResult]` is the public batch entry point.
- `YoloDetection` contains `track_id: int`, `bbox: BBox`, and `confidence: float`; `BBox` uses float `x1,y1,x2,y2`.
- `DetectionResult.to_dict()` already serializes track ID, mode, points, score, ROI bbox, rejection, status, and score breakdown.
- The six score fields already exist: edge support, parallelism, topology, area position, temporal, total.
- Basic debug currently contains `winning_lines` and `roi_size`; verbose additionally contains merged `groups`.
- Missing for requested levels 2-3: Canny edges, raw/filtered lines, pre-merge groups, bounded candidate summaries, validation history, and per-stage timing.
- `render_debug()` already handles the stable base overlay; the script should layer level-specific diagnostics around it rather than replace it.

## Instrumentation Design

Add timing and debug capture inside the existing run, not as a second pipeline:

1. Capture `perf_counter()` deltas for crop, preprocess, Hough, filter, group, merge, candidates/scoring, and detector total.
2. Preserve `raw_groups = group_lines(filtered, cfg)` before calling `merge_line_groups(raw_groups, ...)`.
3. In verbose mode attach `edges`, `raw_lines`, `filtered_lines`, `raw_groups`, merged `groups`, bounded candidate summaries, validation outcome/reason, and `timing_ms`.
4. Candidate summaries are observational records produced while the current loops already validate/score; sorting copies for debug must never change the candidate chosen by detector logic.
5. Basic mode retains the current lean payload and result schema.

Early rejects need a debug payload containing whatever stage data exists so the debugger can explain `ROI_EMPTY`, `NO_LINES`, or `NO_FRONT_FACE` without rerunning anything.

## Script State Model

Keep simple local variables in one script:

- model loaded once at startup;
- natural-sorted image list and current index;
- last valid `HexDetectorConfig` values;
- current frame, YOLO detections, results, overlay, edge view, timings, and error;
- debug level 0-3.

Every processing call constructs a fresh `HexDetector`. R reloads JSON config, then reruns YOLO and detector for the same image. Navigation performs the same processing for the target index. No tracker state crosses images or reruns.

## Serialization and Output

- Lightweight per-image JSON uses `DetectionResult.to_dict()`, YOLO box dictionaries, line/group counts, and timing dictionaries.
- Full J snapshots recursively sanitize dataclasses, tuples/lists/dicts, NumPy scalars, and small arrays; Canny pixels should be stored in the edge PNG and referenced by path rather than embedded.
- Deterministic names such as `{stem}.json`, `{stem}.full.json`, `{stem}.overlay.jpg`, and `{stem}.edges.png` make R/J idempotent.
- Log to console and `debug.log`; use `logger.exception()` or `traceback.print_exc()` for full stack traces.

## Failure Policy

- Fatal before loop: imports, model construction, initial config parsing/validation.
- Recoverable per image/action: image decoding, inference, detector, rendering, or artifact writing. Log traceback, create a lightweight failure record when possible, and keep navigation alive.
- R with invalid updated config is recoverable: retain the last valid state/visualization and report the validation traceback.

## Validation Architecture

- Run existing Phase 1 detector tests to prove instrumentation did not change results.
- Run `python -m py_compile scripts/debug_hex_dataset.py`.
- Run an import-only check that executes the module without entering `main()`.
- Run `python scripts/debug_hex_dataset.py --help` to verify all required flags and defaults without loading a model.
- Perform a manual smoke run with the documented PowerShell command because HighGUI keyboard/window behavior cannot be fully validated headlessly.

## Risks

- Backend-specific arrow codes: D/A are mandatory fallbacks.
- Debug payload memory: capture heavy arrays only in verbose mode and release state when moving images.
- PyTorch model loading: treat the supplied local `.pt` file as trusted; do not download or discover models dynamically.
- `asdict()` deep copies: safe for config, avoid for edge/debug object graphs.

