# Graph Report - .  (2026-06-07)

## Corpus Check
- 78 files · ~95,853 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 515 nodes · 831 edges · 34 communities detected
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 172 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `AppConfig` - 42 edges
2. `WebcamEngine` - 41 edges
3. `MainWindow` - 36 edges
4. `RuntimeStatus` - 25 edges
5. `EngineService` - 20 edges
6. `FrameResult` - 18 edges
7. `DetectorBackend` - 14 edges
8. `DetectionPostProcessor` - 14 edges
9. `FrameThread` - 13 edges
10. `Detection` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Runtime timing metrics (FPS and stage latencies).` --uses--> `InferenceStats`  [INFERRED]
  src\block_detected\runtime\metrics.py → src\block_detected\core\domain.py
- `Load, save, and validate AppConfig (TOML via stdlib tomllib).` --uses--> `AppConfig`  [INFERRED]
  src\block_detected\runtime\config_store.py → src\block_detected\runtime\config_schema.py
- `Unit tests for AppConfig schema, validation, and restart key classification.` --uses--> `AppConfig`  [INFERRED]
  tests\test_config_schema.py → src\block_detected\runtime\config_schema.py
- `Tests for runtime config load/validate/save.` --uses--> `AppConfig`  [INFERRED]
  tests\test_config_store.py → src\block_detected\runtime\config_schema.py
- `Frame annotation drawing primitives.` --uses--> `RuntimeStatus`  [INFERRED]
  src\block_detected\vision\drawing\__init__.py → src\block_detected\core\domain.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (26): DetectionStateTracker, DetectionTransition, Tracks DETECTED/CLEAR transitions without logging every frame., apply_hot_runtime_settings(), config_changed_keys(), needs_runtime_restart(), Apply hot-reloadable config to a running WebcamEngine (testable helper)., Return dotted config keys that differ between two snapshots. (+18 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (24): Ultralytics YOLO detector backend., YoloDetector, extract_boxes(), parse_yolo_result(), Parse raw detector outputs into domain types., Legacy helper — prefer parse_yolo_result().detections., Draw domain detections on frames (no detection imports)., load_detector() (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (4): _frame_to_qimage(), FrameThread, MainWindow, Optional offscreen GUI smoke test when PySide6 is installed.

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (19): BaseModel, Engine control REST endpoints., FastAPI dependencies for runtime API routes., RuntimeStatus, ControlResponse, EngineStateResponse, LogsResponse, Pydantic response models for web API (no OpenCV imports). (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (22): TimeoutError, discover_server(), DiscoveryCandidate, DiscoveryError, get_network_interfaces(), _interface_priority(), _interfaces_from_ip_command(), _interfaces_from_ipconfig() (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (18): build_parser(), CliArgs, config_from_args(), _draw(), format_status_lines(), _import_curses(), log_transition(), main() (+10 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (6): _dict_to_toml(), Load, save, and validate AppConfig (TOML via stdlib tomllib)., save_config(), _toml_value(), Unit tests for AppConfig schema, validation, and restart key classification., Tests for runtime config load/validate/save.

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (13): Post-inference filtering and temporal stability., StabilityConfig, _detection_matches(), DetectionPostProcessor, filter_edge_boxes(), filter_min_area(), filter_min_confidence(), merge_duplicate_detections() (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (9): _FakeEngine, Tests for the curses-free parts of the TUI app., _status(), test_detection_tracker_only_reports_transitions(), test_format_status_lines_reports_detected_and_metrics(), test_tui_runtime_returns_error_when_start_fails(), test_tui_runtime_sets_error_when_frame_loop_ends(), test_tui_runtime_start_process_and_stop_without_real_camera() (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (11): CameraConfig, ClassicalPipelineConfig, InferenceConfig, Typed application configuration (dataclasses + TOML-friendly dicts)., Placeholder for future classical CV stages (blur, threshold, etc.)., UiDebugConfig, handle_key(), Keyboard and mouse input for the webcam UI. (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (8): get_log_lines(), LogBufferHandler, LoggingContext, Central logging setup for CLI and future GUI log panel., Ring buffer of recent log records for GUI consumption., Thread-safe copy of buffered log lines for UI display., Return a thread-safe snapshot of recent log lines., Thread-safe log buffer snapshot API.

### Community 11 - "Community 11"
Cohesion: 0.19
Nodes (10): _engine_with_cap(), _FakeCap, _FakeDetector, _sample_detections(), test_apply_hot_config_min_confidence_filters_more_detections(), test_apply_hot_config_updates_stability_without_touching_cap(), test_process_frame_applies_postprocess_min_confidence(), test_process_frame_returns_none_on_inference_exception() (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.19
Nodes (8): _FakeBox, _FakeBoxes, _FakeResult, _FakeTensor, Tests for detection parse helpers., test_extract_boxes_one(), test_parse_yolo_result_detection_fields(), test_parse_yolo_result_empty()

### Community 13 - "Community 13"
Cohesion: 0.21
Nodes (11): _det(), test_detection_post_processor_disabled_passthrough(), test_detection_post_processor_full_pipeline(), test_filter_edge_boxes_rejects_partial_detections(), test_filter_min_area_rejects_small_boxes(), test_filter_min_confidence_rejects_low_scores(), test_merge_duplicate_detections_keeps_highest_confidence(), test_temporal_stability_requires_votes_across_window() (+3 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (1): FastAPI TestClient coverage for the web API (no camera hardware).

### Community 15 - "Community 15"
Cohesion: 0.3
Nodes (11): discovery_loop(), discovery_response(), get_local_ipv4_addresses(), handle_client(), main(), open_camera(), read_actual(), read_config() (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.2
Nodes (4): _FakeDetector, Tests for hot config application helper., test_apply_hot_runtime_settings_updates_stability_config(), test_apply_hot_runtime_settings_updates_state_and_config()

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (9): _mainwindow(), _qapp(), GUI worker lifecycle, generation guards, and restart-hint tests., test_finalize_worker_stop_clears_thread_and_status(), test_finalize_worker_stop_ignores_non_current_thread(), test_restart_hint_when_camera_index_differs_while_running(), test_stale_frame_ready_ignored(), test_stale_worker_error_does_not_show_dialog() (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.54
Nodes (7): _mainwindow(), _qapp(), Offscreen GUI control wiring tests (PySide6 required at runtime)., test_config_from_controls_round_trip(), test_hot_config_from_controls_stability_only(), test_mainwindow_defaults_idle_offscreen(), test_restart_widgets_include_camera_model_log_level()

### Community 19 - "Community 19"
Cohesion: 0.47
Nodes (4): box_area(), intersection_area(), iou(), Pure geometry helpers (no model dependencies).

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (1): GUI entry should be importable (PySide6 required at runtime).

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (1): YOLO model discovery and loading.

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (4): open_camera(), Webcam capture and source switching., Try the next available camera index. Returns (cap, new_index, switched)., switch_camera()

### Community 23 - "Community 23"
Cohesion: 0.4
Nodes (3): draw_model_switch_button(), On-screen UI widgets (status bar, buttons)., Draw clickable button; returns (x1, y1, x2, y2).

### Community 24 - "Community 24"
Cohesion: 0.4
Nodes (1): Tests for vision.geometry.

### Community 25 - "Community 25"
Cohesion: 0.5
Nodes (1): Tests for config.paths.

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (1): Evaluation-mode label drawing.

### Community 27 - "Community 27"
Cohesion: 0.67
Nodes (1): Tests for OpenCV drawing widget layout.

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): ``python -m block_detected.apps.web`` entry point.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Webcam capture settings.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Detection and inference thresholds.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Filesystem paths for project assets.

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): UI window, widget, and keyboard constants.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Pytest configuration — ensure src/ is importable without pip install -e .

## Knowledge Gaps
- **31 isolated node(s):** ```python -m block_detected.apps.web`` entry point.`, `Webcam capture settings.`, `Detection and inference thresholds.`, `Filesystem paths for project assets.`, `UI window, widget, and keyboard constants.` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 28`** (2 nodes): `__main__.py`, ```python -m block_detected.apps.web`` entry point.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `camera.py`, `Webcam capture settings.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `inference.py`, `Detection and inference thresholds.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `paths.py`, `Filesystem paths for project assets.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `ui.py`, `UI window, widget, and keyboard constants.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `conftest.py`, `Pytest configuration — ensure src/ is importable without pip install -e .`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppConfig` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 11`, `Community 16`, `Community 17`, `Community 18`?**
  _High betweenness centrality (0.225) - this node is a cross-community bridge._
- **Why does `WebcamEngine` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 9`, `Community 11`, `Community 16`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `Community 2` to `Community 0`, `Community 17`, `Community 18`, `Community 5`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `AppConfig` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`AppConfig` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `WebcamEngine` (e.g. with `FrameThread` and `MainWindow`) actually correct?**
  _`WebcamEngine` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `MainWindow` (e.g. with `AppConfig` and `WebcamEngine`) actually correct?**
  _`MainWindow` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `RuntimeStatus` (e.g. with `CliArgs` and `DetectionTransition`) actually correct?**
  _`RuntimeStatus` has 24 INFERRED edges - model-reasoned connections that need verification._