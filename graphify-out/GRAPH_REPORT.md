# Graph Report - .  (2026-06-07)

## Corpus Check
- 63 files · ~92,863 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 415 nodes · 647 edges · 33 communities detected
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 119 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `MainWindow` - 36 edges
2. `WebcamEngine` - 32 edges
3. `AppConfig` - 30 edges
4. `FrameResult` - 18 edges
5. `DetectorBackend` - 14 edges
6. `DetectionPostProcessor` - 14 edges
7. `FrameThread` - 13 edges
8. `Detection` - 13 edges
9. `StreamViewer` - 12 edges
10. `_det()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Load, save, and validate AppConfig (TOML via stdlib tomllib).` --uses--> `AppConfig`  [INFERRED]
  src\block_detected\runtime\config_store.py → src\block_detected\runtime\config_schema.py
- `Unit tests for AppConfig schema, validation, and restart key classification.` --uses--> `AppConfig`  [INFERRED]
  tests\test_config_schema.py → src\block_detected\runtime\config_schema.py
- `Tests for runtime config load/validate/save.` --uses--> `AppConfig`  [INFERRED]
  tests\test_config_store.py → src\block_detected\runtime\config_schema.py
- `Frame annotation drawing primitives.` --uses--> `RuntimeStatus`  [INFERRED]
  src\block_detected\vision\drawing\__init__.py → src\block_detected\core\domain.py
- `FrameThread` --uses--> `AppConfig`  [INFERRED]
  src\block_detected\apps\gui\app.py → src\block_detected\runtime\config_schema.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (32): apply_hot_runtime_settings(), config_changed_keys(), needs_runtime_restart(), Apply hot-reloadable config to a running WebcamEngine (testable helper)., Return dotted config keys that differ between two snapshots., Sync AppConfig and runtime state fields that do not require camera restart., AppConfig, CameraConfig (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (25): Ultralytics YOLO detector backend., YoloDetector, extract_boxes(), parse_yolo_result(), Parse raw detector outputs into domain types., Legacy helper — prefer parse_yolo_result().detections., Draw domain detections on frames (no detection imports)., load_detector() (+17 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (7): _frame_to_qimage(), FrameThread, main(), MainWindow, _print_missing_qt(), PySide6 desktop GUI for webcam runtime tuning., _stylesheet()

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (22): TimeoutError, discover_server(), DiscoveryCandidate, DiscoveryError, get_network_interfaces(), _interface_priority(), _interfaces_from_ip_command(), _interfaces_from_ipconfig() (+14 more)

### Community 4 - "Community 4"
Cohesion: 0.16
Nodes (13): Post-inference filtering and temporal stability., StabilityConfig, _detection_matches(), DetectionPostProcessor, filter_edge_boxes(), filter_min_area(), filter_min_confidence(), merge_duplicate_detections() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (8): get_log_lines(), LogBufferHandler, LoggingContext, Central logging setup for CLI and future GUI log panel., Ring buffer of recent log records for GUI consumption., Thread-safe copy of buffered log lines for UI display., Return a thread-safe snapshot of recent log lines., Thread-safe log buffer snapshot API.

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (10): _engine_with_cap(), _FakeCap, _FakeDetector, _sample_detections(), test_apply_hot_config_min_confidence_filters_more_detections(), test_apply_hot_config_updates_stability_without_touching_cap(), test_process_frame_applies_postprocess_min_confidence(), test_process_frame_returns_none_on_inference_exception() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.19
Nodes (8): _FakeBox, _FakeBoxes, _FakeResult, _FakeTensor, Tests for detection parse helpers., test_extract_boxes_one(), test_parse_yolo_result_detection_fields(), test_parse_yolo_result_empty()

### Community 8 - "Community 8"
Cohesion: 0.21
Nodes (11): _det(), test_detection_post_processor_disabled_passthrough(), test_detection_post_processor_full_pipeline(), test_filter_edge_boxes_rejects_partial_detections(), test_filter_min_area_rejects_small_boxes(), test_filter_min_confidence_rejects_low_scores(), test_merge_duplicate_detections_keeps_highest_confidence(), test_temporal_stability_requires_votes_across_window() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.3
Nodes (11): discovery_loop(), discovery_response(), get_local_ipv4_addresses(), handle_client(), main(), open_camera(), read_actual(), read_config() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.2
Nodes (4): _FakeDetector, Tests for hot config application helper., test_apply_hot_runtime_settings_updates_stability_config(), test_apply_hot_runtime_settings_updates_state_and_config()

### Community 11 - "Community 11"
Cohesion: 0.4
Nodes (9): _mainwindow(), _qapp(), GUI worker lifecycle, generation guards, and restart-hint tests., test_finalize_worker_stop_clears_thread_and_status(), test_finalize_worker_stop_ignores_non_current_thread(), test_restart_hint_when_camera_index_differs_while_running(), test_stale_frame_ready_ignored(), test_stale_worker_error_does_not_show_dialog() (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (1): Tests for runtime config load/validate/save.

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (3): _FakeDetector, Engine create/start error messages without camera or weights., test_try_start_reports_camera_index()

### Community 14 - "Community 14"
Cohesion: 0.25
Nodes (1): Unit tests for AppConfig schema, validation, and restart key classification.

### Community 15 - "Community 15"
Cohesion: 0.54
Nodes (7): _mainwindow(), _qapp(), Offscreen GUI control wiring tests (PySide6 required at runtime)., test_config_from_controls_round_trip(), test_hot_config_from_controls_stability_only(), test_mainwindow_defaults_idle_offscreen(), test_restart_widgets_include_camera_model_log_level()

### Community 16 - "Community 16"
Cohesion: 0.38
Nodes (4): _dict_to_toml(), Load, save, and validate AppConfig (TOML via stdlib tomllib)., save_config(), _toml_value()

### Community 17 - "Community 17"
Cohesion: 0.47
Nodes (4): box_area(), intersection_area(), iou(), Pure geometry helpers (no model dependencies).

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (1): GUI entry should be importable (PySide6 required at runtime).

### Community 19 - "Community 19"
Cohesion: 0.4
Nodes (1): YOLO model discovery and loading.

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (4): open_camera(), Webcam capture and source switching., Try the next available camera index. Returns (cap, new_index, switched)., switch_camera()

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (3): draw_model_switch_button(), On-screen UI widgets (status bar, buttons)., Draw clickable button; returns (x1, y1, x2, y2).

### Community 22 - "Community 22"
Cohesion: 0.4
Nodes (1): Tests for vision.geometry.

### Community 23 - "Community 23"
Cohesion: 0.5
Nodes (1): Tests for config.paths.

### Community 24 - "Community 24"
Cohesion: 0.67
Nodes (1): Evaluation-mode label drawing.

### Community 25 - "Community 25"
Cohesion: 0.67
Nodes (1): Tests for OpenCV drawing widget layout.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Webcam capture settings.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Detection and inference thresholds.

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Filesystem paths for project assets.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): UI window, widget, and keyboard constants.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Shared primitive types (no third-party imports).

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Pytest configuration — ensure src/ is importable without pip install -e .

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **30 isolated node(s):** `Webcam capture settings.`, `Detection and inference thresholds.`, `Filesystem paths for project assets.`, `UI window, widget, and keyboard constants.`, `Domain types for detection and runtime (no OpenCV/YOLO imports).` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 26`** (2 nodes): `camera.py`, `Webcam capture settings.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `inference.py`, `Detection and inference thresholds.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `paths.py`, `Filesystem paths for project assets.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `ui.py`, `UI window, widget, and keyboard constants.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `types.py`, `Shared primitive types (no third-party imports).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `conftest.py`, `Pytest configuration — ensure src/ is importable without pip install -e .`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppConfig` connect `Community 0` to `Community 1`, `Community 2`, `Community 6`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Why does `WebcamEngine` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 10`, `Community 13`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `Community 2` to `Community 0`, `Community 11`, `Community 15`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `MainWindow` (e.g. with `AppConfig` and `WebcamEngine`) actually correct?**
  _`MainWindow` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `WebcamEngine` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`WebcamEngine` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `AppConfig` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`AppConfig` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `FrameResult` (e.g. with `DetectorBackend` and `Protocols for pluggable backends (stdlib typing only).`) actually correct?**
  _`FrameResult` has 17 INFERRED edges - model-reasoned connections that need verification._