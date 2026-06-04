# Graph Report - .  (2026-06-02)

## Corpus Check
- 56 files · ~2,709,015 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 300 nodes · 444 edges · 29 communities detected
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 98 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `MainWindow` - 34 edges
2. `WebcamEngine` - 29 edges
3. `AppConfig` - 24 edges
4. `DetectionPostProcessor` - 14 edges
5. `FrameThread` - 13 edges
6. `FrameResult` - 13 edges
7. `DetectorBackend` - 12 edges
8. `Detection` - 10 edges
9. `ProcessedFrame` - 9 edges
10. `RuntimeMetrics` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Ultralytics YOLO detector backend.` --uses--> `FrameResult`  [INFERRED]
  src\block_detected\detection\yolo\backend.py → src\block_detected\core\domain.py
- `Load, save, and validate AppConfig (TOML via stdlib tomllib).` --uses--> `AppConfig`  [INFERRED]
  src\block_detected\runtime\config_store.py → src\block_detected\runtime\config_schema.py
- `Tests for runtime config load/validate/save.` --uses--> `AppConfig`  [INFERRED]
  tests\test_config_store.py → src\block_detected\runtime\config_schema.py
- `FrameThread` --uses--> `AppConfig`  [INFERRED]
  src\block_detected\apps\gui\app.py → src\block_detected\runtime\config_schema.py
- `FrameThread` --uses--> `WebcamEngine`  [INFERRED]
  src\block_detected\apps\gui\app.py → src\block_detected\runtime\engine.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (7): _frame_to_qimage(), FrameThread, main(), MainWindow, _print_missing_qt(), PySide6 desktop GUI for webcam runtime tuning., _stylesheet()

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (22): extract_boxes(), parse_yolo_result(), Parse raw detector outputs into domain types., Legacy helper — prefer parse_yolo_result().detections., Draw domain detections on frames (no detection imports)., Detection, FrameResult, InferenceStats (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (14): AppConfig, CameraConfig, ClassicalPipelineConfig, InferenceConfig, Typed application configuration (dataclasses + TOML-friendly dicts)., Placeholder for future classical CV stages (blur, threshold, etc.)., UiDebugConfig, Apply fields that do not require camera/detector restart. (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (10): apply_hot_runtime_settings(), config_changed_keys(), needs_runtime_restart(), Apply hot-reloadable config to a running WebcamEngine (testable helper)., Return dotted config keys that differ between two snapshots., Sync AppConfig and runtime state fields that do not require camera restart., WebcamEngine, _FakeDetector (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.16
Nodes (13): Post-inference filtering and temporal stability., StabilityConfig, _detection_matches(), DetectionPostProcessor, filter_edge_boxes(), filter_min_area(), filter_min_confidence(), merge_duplicate_detections() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (8): get_log_lines(), LogBufferHandler, LoggingContext, Central logging setup for CLI and future GUI log panel., Ring buffer of recent log records for GUI consumption., Thread-safe copy of buffered log lines for UI display., Return a thread-safe snapshot of recent log lines., Thread-safe log buffer snapshot API.

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (8): _FakeBox, _FakeBoxes, _FakeResult, _FakeTensor, Tests for detection parse helpers., test_extract_boxes_one(), test_parse_yolo_result_detection_fields(), test_parse_yolo_result_empty()

### Community 7 - "Community 7"
Cohesion: 0.27
Nodes (8): _det(), test_detection_post_processor_disabled_passthrough(), test_detection_post_processor_full_pipeline(), test_filter_edge_boxes_rejects_partial_detections(), test_filter_min_area_rejects_small_boxes(), test_filter_min_confidence_rejects_low_scores(), test_merge_duplicate_detections_keeps_highest_confidence(), test_temporal_stability_requires_votes_across_window()

### Community 8 - "Community 8"
Cohesion: 0.2
Nodes (5): Ultralytics YOLO detector backend., YoloDetector, load_detector(), Load Ultralytics YOLO detector (project default and only backend)., Load a YOLO `.pt` model. Project uses Ultralytics only.

### Community 9 - "Community 9"
Cohesion: 0.25
Nodes (3): _FakeDetector, Tests for hot config application helper., test_apply_hot_runtime_settings_updates_state_and_config()

### Community 10 - "Community 10"
Cohesion: 0.28
Nodes (4): _FakeDetector, Tests for runtime engine behavior that does not require a real camera., test_switch_model_keeps_previous_detector_when_load_fails(), test_switch_model_swaps_and_closes_previous_detector()

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (1): Tests for runtime config load/validate/save.

### Community 12 - "Community 12"
Cohesion: 0.38
Nodes (4): _dict_to_toml(), Load, save, and validate AppConfig (TOML via stdlib tomllib)., save_config(), _toml_value()

### Community 13 - "Community 13"
Cohesion: 0.47
Nodes (4): box_area(), intersection_area(), iou(), Pure geometry helpers (no model dependencies).

### Community 14 - "Community 14"
Cohesion: 0.4
Nodes (1): YOLO model discovery and loading.

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (4): open_camera(), Webcam capture and source switching., Try the next available camera index. Returns (cap, new_index, switched)., switch_camera()

### Community 16 - "Community 16"
Cohesion: 0.4
Nodes (3): draw_model_switch_button(), On-screen UI widgets (status bar, buttons)., Draw clickable button; returns (x1, y1, x2, y2).

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (1): Tests for vision.geometry.

### Community 18 - "Community 18"
Cohesion: 0.5
Nodes (1): Tests for config.paths.

### Community 19 - "Community 19"
Cohesion: 0.67
Nodes (1): Evaluation-mode label drawing.

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (1): GUI entry should be importable (PySide6 required at runtime).

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (1): Tests for OpenCV drawing widget layout.

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Webcam capture settings.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Detection and inference thresholds.

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Filesystem paths for project assets.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): UI window, widget, and keyboard constants.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Shared primitive types (no third-party imports).

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Pytest configuration — ensure src/ is importable without pip install -e .

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **30 isolated node(s):** `Webcam capture settings.`, `Detection and inference thresholds.`, `Filesystem paths for project assets.`, `UI window, widget, and keyboard constants.`, `Domain types for detection and runtime (no OpenCV/YOLO imports).` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 22`** (2 nodes): `camera.py`, `Webcam capture settings.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `inference.py`, `Detection and inference thresholds.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `paths.py`, `Filesystem paths for project assets.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `ui.py`, `UI window, widget, and keyboard constants.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `types.py`, `Shared primitive types (no third-party imports).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `conftest.py`, `Pytest configuration — ensure src/ is importable without pip install -e .`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WebcamEngine` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.233) - this node is a cross-community bridge._
- **Why does `AppConfig` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 9`, `Community 10`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `Community 0` to `Community 2`, `Community 3`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `MainWindow` (e.g. with `AppConfig` and `WebcamEngine`) actually correct?**
  _`MainWindow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `WebcamEngine` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`WebcamEngine` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `AppConfig` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`AppConfig` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `DetectionPostProcessor` (e.g. with `ProcessedFrame` and `WebcamEngine`) actually correct?**
  _`DetectionPostProcessor` has 7 INFERRED edges - model-reasoned connections that need verification._