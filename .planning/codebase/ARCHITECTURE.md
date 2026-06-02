# Architecture

**Analysis Date:** 2026-06-02

## Pattern Overview

**Overall:** Dual-entry-point script architecture (no installable package, no shared internal library)

**Key Characteristics:**
- Two standalone Python scripts at the repository root, each runnable via `python <script>.py`
- All application logic lives inside those scripts; there is no `src/` package or importable project module
- Ultralytics YOLO handles model loading and inference; OpenCV handles I/O, drawing, and UI
- Configuration is module-level constants (webcam) or `argparse` CLI flags (batch), not environment files or config YAML

## Layers

**Configuration (constants / CLI):**
- Purpose: Paths, thresholds, camera settings, UI tuning
- Location: Top of `run_yolo_webcam.py` (lines 8–23); `parse_args()` in `batch_detect_square.py` (lines 11–22)
- Contains: `BASE_DIR`, `MODELS_DIR`, `DEFAULT_MODEL_NAME`, camera resolution, confidence bounds, button layout; batch `--model`, `--input`, `--output`, `--conf`, `--show`
- Depends on: `pathlib.Path`, `argparse` (batch only)
- Used by: Same file’s `main()` and helpers

**Model discovery & loading:**
- Purpose: Resolve `.pt` weights and construct `YOLO` instances
- Location: `discover_model_paths()`, `default_model_index()`, `switch_model()` in `run_yolo_webcam.py`; explicit `Path(args.model)` check in `batch_detect_square.py`
- Contains: Glob `models/*.pt`, prefer `train-3.pt`, reload on hot-swap (webcam)
- Depends on: `ultralytics.YOLO`, filesystem under `models/`
- Used by: Inference loops in both entry points

**Inference:**
- Purpose: Run detection on frames or still images
- Location: `run_yolo_webcam.py` (`model(frame, conf=..., verbose=False)`); `batch_detect_square.py` (`model.predict(source=img, conf=..., verbose=False)`)
- Contains: Ultralytics `Results` objects; access via `result.boxes`, `result.names`
- Depends on: Loaded `YOLO` model, NumPy/OpenCV image buffers (implicit via Ultralytics + `cv2.imread`)
- Used by: Visualization / export layers below

**Visualization & annotation:**
- Purpose: Draw boxes and labels on images for display or save
- Location: `extract_boxes`, `draw_overlay_history`, `draw_eval_boxes`, `draw_model_switch_button` in `run_yolo_webcam.py`; `draw_square_box` + `cv2.putText` in `batch_detect_square.py`
- Contains: Normal mode uses `result.plot()` plus optional multi-frame overlay; eval mode uses custom cyan boxes with percentage labels; batch uses axis-aligned **square** boxes centered on detections
- Depends on: OpenCV (`cv2`)
- Used by: `cv2.imshow` (webcam and optional batch preview) or `cv2.imwrite` (batch)

**I/O & device loop:**
- Purpose: Acquire frames or read/write files; handle keyboard/mouse
- Location: `open_camera`, main `while True` loop, `on_mouse` in `run_yolo_webcam.py`; sorted `input_dir.iterdir()`, `cv2.imread` / `cv2.imwrite` in `batch_detect_square.py`
- Contains: `cv2.VideoCapture`, `cap.read()`, `cv2.waitKeyEx` / `waitKey`, mouse callback for model button
- Depends on: OpenCV, OS webcam drivers, local filesystem
- Used by: User-facing runtime only

## Data Flow

**Webcam realtime (`run_yolo_webcam.py`):**

1. `discover_model_paths()` scans `models/*.pt`; `YOLO(str(path))` loads default or user-selected weights
2. `open_camera(CAMERA_INDEX)` opens device, sets `CAMERA_WIDTH` × `CAMERA_HEIGHT`
3. Loop: `cap.read()` → BGR `frame`
4. `model(frame, conf=active_conf, verbose=False)` → `results[0]`; `extract_boxes(result)` for overlay history
5. Branch on `eval_mode`: custom `draw_eval_boxes` on copy, or `result.plot()` + optional `draw_overlay_history`
6. Status text + `draw_model_switch_button` → `cv2.imshow`
7. Keys/mouse adjust conf, overlay, eval mode, camera index, or model; `q` exits; `finally` releases camera and destroys windows

**Batch still images (`batch_detect_square.py`):**

1. `parse_args()` resolves model path, input dir (`images/`), output dir (`images_out/`), confidence
2. Validate model file and input directory; collect sorted images by extension (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`)
3. `output_dir.mkdir(parents=True, exist_ok=True)`; `YOLO(str(model_path))` once per run
4. Per image: `cv2.imread` → `model.predict(source=img, conf=args.conf)` → iterate `result.boxes`
5. For each box: `draw_square_box` (square circumscribing max side of bbox) + class/conf label via `cv2.putText`
6. `cv2.imwrite` to `images_out/<same filename>`; optional `--show` preview with `waitKey`

**State Management:**
- Webcam: In-memory only — `conf`, `overlay_enabled`, `eval_mode`, `box_history` (`deque`), `model` / `model_index` / `current_path`, `ui_state` dict for mouse callback and button rect; no persistence across runs
- Batch: Stateless per image; no cross-image aggregation; model loaded once and reused in the loop

## Key Abstractions

**Ultralytics `YOLO` model handle:**
- Purpose: Single object encapsulating weights and inference API
- Examples: `run_yolo_webcam.py` (`model = YOLO(str(current_path))`), `batch_detect_square.py` (`model = YOLO(str(model_path))`)
- Pattern: Construct at startup (or on hot-swap); call callable / `.predict()` with `conf` and `verbose=False`

**Detection result (`results[0]`):**
- Purpose: One frame/image worth of detections
- Examples: Used in both scripts after inference
- Pattern: Guard `result.boxes is None`; iterate boxes; read `box.xyxy`, `box.cls`, `box.conf`; class names via `result.names`

**Bounding box coordinates:**
- Purpose: Pixel rectangles `(x1, y1, x2, y2)` as ints or floats from tensor `.tolist()`
- Examples: `extract_boxes()` in `run_yolo_webcam.py`; loop in `batch_detect_square.py` lines 87–91
- Pattern: Webcam stores int tuples for overlay; batch passes floats into `draw_square_box` which recomputes square corners

**Project-relative paths:**
- Purpose: Scripts work regardless of cwd when paths are anchored to repo root
- Examples: `BASE_DIR = Path(__file__).resolve().parent` in both files; `MODELS_DIR = BASE_DIR / "models"`
- Pattern: Always resolve paths from `__file__`, not from `os.getcwd()`

## Entry Points

**Webcam inference:**
- Location: `run_yolo_webcam.py` — `main()` via `if __name__ == "__main__": raise SystemExit(main())`
- Triggers: `python run_yolo_webcam.py` (no CLI args)
- Responsibilities: Model discovery, camera capture, realtime inference, interactive UI (keyboard + model switch button), graceful shutdown

**Batch image processing:**
- Location: `batch_detect_square.py` — `main()` via `if __name__ == "__main__": raise SystemExit(main())`
- Triggers: `python batch_detect_square.py` with optional `--model`, `--input`, `--output`, `--conf`, `--show`
- Responsibilities: Validate paths, batch inference, square-box annotation, write `images_out/`, optional interactive preview

## Error Handling

**Strategy:** Fail fast at startup with exit code `1` and `[ERROR]` logs; tolerate per-frame/per-file failures where loop can continue

**Patterns:**
- Missing models / invalid input dir / empty image list → print `[ERROR]`, `return 1` before main loop (`batch_detect_square.py` lines 55–66; `run_yolo_webcam.py` lines 137–139, 147–149, 153–155)
- Model load failure → caught `Exception`, message printed, exit or skip switch (`run_yolo_webcam.py` lines 147–149, 180–181)
- Unreadable batch image → `[WARN] Skip`, `continue` next file (`batch_detect_square.py` lines 77–79)
- Inference exception in webcam loop → `[ERROR]`, `break` loop (`run_yolo_webcam.py` lines 200–202)
- Camera read failure → `[WARN]`, break loop (`run_yolo_webcam.py` lines 191–193)
- Resource cleanup → `try` / `finally` releases `VideoCapture` and destroys OpenCV windows (`run_yolo_webcam.py` lines 278–281)

## Cross-Cutting Concerns

**Logging:** `print()` with prefixed tags `[INFO]`, `[WARN]`, `[ERROR]` — no structured logging library

**Validation:** Filesystem checks (`exists()`, `is_dir()`), non-empty model glob, image extension whitelist; no schema validation for images beyond `cv2.imread` returning non-`None`

**Authentication:** Not applicable — local offline scripts only

**Shared code between scripts:** None — duplicate `BASE_DIR` pattern only; drawing and inference invocation differ (callable vs `.predict`, `result.plot()` vs square boxes)

---

*Architecture analysis: 2026-06-02*
