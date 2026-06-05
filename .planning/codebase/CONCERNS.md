# Codebase Concerns

**Analysis Date:** 2026-06-05

## Tech Debt

**Legacy config modules vs `AppConfig`:**
- Issue: `config/camera.py`, `config/inference.py`, and `config/ui.py` hold module-level constants that are re-imported into `AppConfig` defaults in `runtime/config_schema.py`. Two sources of truth for the same values.
- Files: `src/block_detected/config/camera.py`, `src/block_detected/config/inference.py`, `src/block_detected/config/ui.py`, `src/block_detected/runtime/config_schema.py`, `src/block_detected/config/__init__.py`
- Impact: Changing a default in one place without updating the other causes silent drift between TOML defaults, GUI spin ranges, and legacy re-exports.
- Fix approach: Derive legacy constants from `AppConfig.defaults()` once, or mark legacy modules deprecated and stop importing them from `config_schema.py`.

**`ClassicalPipelineConfig` placeholder never wired:**
- Issue: `ClassicalPipelineConfig` is validated, serialized to TOML, and saved from the GUI schema path, but no engine stage reads `config.classical`.
- Files: `src/block_detected/runtime/config_schema.py`, `src/block_detected/runtime/engine.py`
- Impact: Config fields (`enabled`, `blur_kernel`, `canny_low`, `canny_high`) suggest behavior that does not exist; Stitch UI spec expects pre-processing and edge detection that cannot run.
- Fix approach: Wire a classical stage in `WebcamEngine.process_frame()` before inference, or remove/hide from TOML until implemented and document as reserved in `AGENTS.md`.

**Dead OpenCV keyboard/mouse UI layer:**
- Issue: `ui/input/handlers.py` implements `waitKeyEx` / mouse callbacks for an OpenCV window loop, but no entry point calls `handle_key` or `on_mouse`. `main.py`, `__main__.py`, and the `block-detected` console script all launch the PySide6 GUI only.
- Files: `src/block_detected/ui/input/handlers.py`, `src/block_detected/ui/__init__.py`, `main.py`, `src/block_detected/apps/gui/app.py`
- Impact: Orphan code with platform-specific arrow-key assumptions; misleads readers into thinking a CLI OpenCV path still exists.
- Fix approach: Remove or relocate to an explicit `apps/cli/` entry if needed; stop re-exporting from `ui/__init__.py` until wired.

**Monolithic GUI module:**
- Issue: `MainWindow`, `FrameThread`, stylesheet, and all control wiring live in a single 620+ line file.
- Files: `src/block_detected/apps/gui/app.py`
- Impact: High merge conflict risk; hard to unit-test widget logic in isolation; any UI change touches the god node of the graph.
- Fix approach: Split into `frame_thread.py`, `controls_panel.py`, and `preview.py` when adding Stitch/web-console parity.

**Custom TOML writer without escaping:**
- Issue: `save_config()` uses hand-rolled `_dict_to_toml()` with naive string quoting (`f'"{value}"'`).
- Files: `src/block_detected/runtime/config_store.py`
- Impact: Model names or paths containing `"`, `\`, or newlines can produce invalid TOML on save.
- Fix approach: Use a proper TOML library for write (e.g. `tomli-w`) or escape strings per TOML spec.

**Planning docs out of sync with code:**
- Issue: `.planning/STATE.md` still says "Phase 4 in progress" and references `block-detected-gui` / optional GUI extra. `.planning/ROADMAP.md` marks phases 3–6 as unplanned TBD while phase directories and code for runtime, GUI, hardening, and stability exist. `.planning/codebase/TESTING.md` references `test_runtime_state.py` and overlay history tests that do not exist. `.planning/codebase/INTEGRATIONS.md` references `ui.show_fps_in_status` which is not in `config_schema.py`.
- Files: `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/phases/05-gui-and-runtime-hardening-for-production-uat/05-UAT.md`
- Impact: GSD planners and executors load stale assumptions (missing features treated as done, wrong install commands).
- Fix approach: Refresh planning artifacts via `/gsd-map-codebase` and milestone sync; align UAT checklists with implemented controls only.

**Phase 5 UAT references unimplemented features:**
- Issue: `05-UAT.md` lists "Overlay trail on/off and trail frame count" and "Show FPS flag updates status bar in preview". No `trail`, `overlay`, or `show_fps` symbols exist in Python source.
- Files: `.planning/phases/05-gui-and-runtime-hardening-for-production-uat/05-UAT.md`, `src/block_detected/apps/gui/app.py`, `src/block_detected/runtime/config_schema.py`
- Impact: UAT appears incomplete even when core GUI works; confuses verification scope.
- Fix approach: Remove or re-scope checklist items; implement features in a dedicated phase if still required.

**Pyproject vs UAT install instructions:**
- Issue: UAT says `pip install -e ".[dev,gui]"` and `block-detected-gui`, but `pyproject.toml` defines only `[dev]` optional deps and a single script `block-detected` → GUI `main`.
- Files: `pyproject.toml`, `.planning/phases/05-gui-and-runtime-hardening-for-production-uat/05-UAT.md`
- Impact: Copy-paste setup fails for new contributors.
- Fix approach: Update UAT to `pip install -e ".[dev]"` and `python main.py` / `block-detected`.

## Known Bugs

**Single inference/camera failure stops entire preview loop:**
- Symptoms: Preview freezes or worker exits after one bad frame or inference exception.
- Files: `src/block_detected/runtime/engine.py` (`process_frame` returns `None` on read failure or inference exception), `src/block_detected/apps/gui/app.py` (`FrameThread.run` breaks on `processed is None`)
- Trigger: Camera disconnect mid-session, corrupt frame, or transient Ultralytics error.
- Workaround: Stop and Start the engine.
- Fix approach: Distinguish fatal vs recoverable errors; skip frame and log on inference failure; optionally retry camera open.

**Stop timeout leaves worker referenced:**
- Symptoms: After Stop with a hung worker (`thread.wait(5000)` timeout), Start stays disabled and status shows "Stop pending — wait before Start".
- Files: `src/block_detected/apps/gui/app.py` (`_stop_engine`)
- Trigger: Slow YOLO shutdown or blocked `VideoCapture.read()`.
- Workaround: Close the window or wait for `finished` signal.
- Fix approach: Document behavior; consider forced terminate only as last resort; disable Stop spam.

**Log level change does not apply at runtime:**
- Symptoms: User changes log level in GUI while running; log panel verbosity unchanged until full restart.
- Files: `src/block_detected/apps/gui/app.py` (log level in `_restart_widgets`), `src/block_detected/runtime/logging_setup.py` (`setup_logging` called once in `main()`)
- Trigger: Edit log level combo while engine is running.
- Workaround: Stop app and relaunch after Save TOML.
- Fix approach: Call `setup_logging` on hot apply or document as restart-only consistently in UI tooltips.

**Camera resolution request not verified:**
- Symptoms: Config shows 1280×720 but actual capture may differ; postprocess edge filter uses `frame.shape`, not requested config.
- Files: `src/block_detected/io/camera/capture.py` (sets props, never reads back), `src/block_detected/runtime/postprocess.py` (`filter_edge_boxes`)
- Trigger: Drivers that ignore `CAP_PROP_FRAME_WIDTH` / `HEIGHT`.
- Fix approach: After `open_camera`, read back dimensions and log warning if mismatch.

## Security Considerations

**Local-only desktop app:**
- Risk: No network attack surface in runtime code; no auth, webhooks, or remote APIs.
- Files: Entire `src/block_detected/` tree
- Current mitigation: N/A — offline webcam processing.
- Recommendations: Keep it that way unless adding a web console; then add explicit bind address, CORS, and auth before exposing streams.

**Model weights and config on disk:**
- Risk: Large `.pt` files in `models/` may contain training data fingerprints; TOML may hold paths.
- Files: `models/*.pt`, `block_detected.toml`, `src/block_detected/config/paths.py`
- Current mitigation: `models/*.pt` excluded from agent edits per `AGENTS.md`.
- Recommendations: Do not commit private weights; `.gitignore` env/credential files (no `.env` detected in repo).

**No secrets in repo:**
- Risk: Low — no API keys or cloud credentials in source.
- Recommendations: Continue avoiding `.env` commits; note existence only in audits.

## Performance Bottlenecks

**Per-frame full buffer copies (render path):**
- Problem: `frame.copy()` on every frame when eval mode or stability is enabled; additional copy in `_frame_to_qimage()` via `.copy()` on `QImage`.
- Files: `src/block_detected/runtime/engine.py` (`_render`), `src/block_detected/apps/gui/app.py` (`_frame_to_qimage`)
- Cause: Custom drawing requires writable buffer; Qt needs owned image data.
- Improvement path: Reuse pre-allocated numpy buffer; use `QImage` constructor with copy-on-write only when necessary; profile on 720p+ targets.

**Tight worker polling loop:**
- Problem: `FrameThread` calls `msleep(1)` after every frame with no back-pressure when inference is faster than display need.
- Files: `src/block_detected/apps/gui/app.py` (`FrameThread.run`)
- Cause: No frame pacing or vsync; loop runs as fast as camera + YOLO allow.
- Improvement path: Sleep to target FPS or block on latest-frame queue with drop-old policy.

**Temporal stability vote cost:**
- Problem: `TemporalStabilityTracker.update()` is O(current_detections × window × detections_per_history_frame) with nested IoU checks.
- Files: `src/block_detected/runtime/postprocess.py`
- Cause: Naive vote counting without spatial indexing.
- Improvement path: Acceptable at low detection counts; add grid/hash bucketing if multi-detect scenes grow.

**YOLO model reload on switch:**
- Problem: Each `switch_model()` loads a full new Ultralytics model from disk.
- Files: `src/block_detected/runtime/engine.py`, `src/block_detected/detection/yolo/backend.py`
- Cause: By design — only one active model.
- Improvement path: LRU cache of loaded models if rapid cycling is a UX requirement.

**Ultralytics `result.plot()` in normal mode (stability off):**
- Problem: Delegates rendering to Ultralytics; harder to customize and may allocate internally.
- Files: `src/block_detected/runtime/engine.py` (`_render`)
- Improvement path: Always use `draw_detection_boxes` on a copy for consistent path and colors.

## Fragile Areas

**Import-time Ultralytics dependency:**
- Files: `src/block_detected/detection/yolo/loader.py`, `src/block_detected/detection/yolo/backend.py`, `src/block_detected/runtime/detector_loader.py`, `src/block_detected/runtime/engine.py`
- Why fragile: Importing `WebcamEngine` pulls `ultralytics` immediately via `detector_loader` → `YoloDetector` → `loader.py`. Tests that only need engine logic fail collection without the full ML stack installed.
- Safe modification: Lazy-import YOLO inside `load_detector()` / `YoloDetector.__init__`; avoid re-export side effects in `detection/yolo/__init__.py`.
- Test coverage: Partial — pure tests pass without ultralytics; `test_engine.py`, `test_engine_create.py`, `test_config_apply.py` require it.

**OpenCV arrow key codes (unused but configured):**
- Files: `src/block_detected/config/ui.py`, `src/block_detected/runtime/config_schema.py` (`UiDebugConfig.key_arrow_up/down`)
- Why fragile: Comments say macOS/Linux `waitKeyEx` codes; Windows codes differ. Handlers are unused today but constants remain in TOML schema.
- Safe modification: Remove from active config or gate behind CLI-only profile.

**GUI ↔ worker threading contract:**
- Files: `src/block_detected/apps/gui/app.py` (`FrameThread`, generation guards, `_stop_engine`)
- Why fragile: Stale `frame_ready` / `error` signals must be ignored via `_run_generation`; violating `AGENTS.md` rule (clearing `frame_thread` before `finished`) causes use-after-free symptoms.
- Safe modification: Always match patterns in existing `_on_frame_ready`, `_on_worker_error`, `_finalize_worker_stop`.
- Test coverage: Smoke only (`tests/test_gui_smoke.py`); no FrameThread lifecycle tests.

**Ultralytics result shape in eval drawing:**
- Files: `src/block_detected/vision/drawing/eval.py`, `src/block_detected/detection/boxes.py`
- Why fragile: `draw_eval_boxes` reads raw Ultralytics tensors directly; stability-on eval path uses domain `Detection` drawing instead — two code paths for labels.
- Safe modification: Prefer domain types everywhere; keep `raw` for parity testing only.

**Stability config hot-reload vs tracker state:**
- Files: `src/block_detected/runtime/postprocess.py` (`DetectionPostProcessor.update_config`), `src/block_detected/apps/gui/app.py` (auto `_apply_hot_config` on every stability widget change)
- Why fragile: Tracker rebuilds when window/votes/IoU change; disabling stability clears history but rapid toggles during motion can cause visible flicker.
- Safe modification: Debounce GUI stability applies or batch into explicit Apply button.

## Scaling Limits

**Single camera, single model, single thread:**
- Current capacity: One `VideoCapture`, one `YoloDetector`, one `FrameThread` loop.
- Limit: No multi-camera fusion, no async inference queue, no batching.
- Scaling path: Separate capture and infer threads with a bounded queue; optional second backend via `DetectorBackend` protocol in `src/block_detected/core/protocols.py`.

**Detection count and temporal window:**
- Current capacity: Default temporal window 5, votes 3; GUI allows up to 120.
- Limit: Large windows increase memory (`deque` of detection lists) and vote-loop CPU.
- Scaling path: Cap window in validation to practical FPS-derived maximum.

**Log ring buffer:**
- Current capacity: 500 lines in `LogBufferHandler`, 500 blocks in GUI `QPlainTextEdit`.
- Limit: Very chatty DEBUG on long runs drops older lines (by design).

## Dependencies at Risk

**Ultralytics + PyTorch stack:**
- Risk: Heavy install, GPU/CUDA variability, upstream API changes to `result.plot()`, `boxes`, and `predict()` kwargs.
- Impact: Breaks inference, parsing (`detection/boxes.py`), and normal-mode render.
- Migration plan: Pin versions in CI; add contract tests with fakes (`tests/test_boxes.py` pattern); consider ONNX backend stub already noted in phase-02 research.

**OpenCV `opencv-python`:**
- Risk: Camera backend differences across Windows/macOS/Linux; property set/get not guaranteed.
- Impact: Wrong resolution, failed open, or different color format.
- Migration plan: Platform-specific camera tests where feasible; document tested indices.

**PySide6:**
- Risk: Required for default entry; optional import guard exists but app exits without it.
- Impact: Headless/CI must use `pytest.importorskip("PySide6")` pattern from `tests/test_gui_smoke.py`.
- Migration plan: Keep lazy import in `apps/gui/app.py` per `AGENTS.md`.

**Unpinned lower-bound versions:**
- Risk: `pyproject.toml` and `requirements.txt` use `>=` only (e.g. `ultralytics>=8.4.0`).
- Impact: Non-reproducible installs across machines and time.
- Migration plan: Add lockfile or upper pins when CI is introduced.

## Missing Critical Features

**Stitch / Robo-Vision web console backend (large gap):**
- Problem: `example_ui/stitch_block_pickup_vision_console/html_data_requirements.md` expects NMS IoU, pre-processing sliders, ROI crop, kinematics telemetry, contour/corner overlays, MJPEG/base64 stream, and config profiles. None are implemented in runtime.
- Blocks: Embedding the HTML UI without a new API layer and pipeline stages.
- Reference: `example_ui/stitch_block_pickup_vision_console/BACKEND_GAP_ANALYSIS.md`

**YOLO inference parameters:**
- Problem: No `imgsz`, NMS `iou`, `max_det`, or `device` in `InferenceConfig` or `YoloDetector.predict()`.
- Files: `src/block_detected/runtime/config_schema.py`, `src/block_detected/detection/yolo/backend.py`
- Blocks: Matching training-time inference settings from the Stitch sidebar.

**Overlay trail (Phase 6 verification item):**
- Problem: `06-VERIFICATION.md` manual check "Overlay trail uses filtered boxes when stability on" — no trail/history overlay drawing exists.
- Files: `.planning/phases/06-detection-post-processing-reject-rules-and-temporal-stabilit/06-VERIFICATION.md`, `src/block_detected/vision/drawing/`
- Blocks: Closing Phase 6 UAT as written.

**Web streaming API:**
- Problem: Frames only go to Qt preview; no HTTP/WebSocket feed for external UI.
- Files: `src/block_detected/apps/gui/app.py`
- Blocks: Browser-based console without rewriting capture path.

**CI pipeline:**
- Problem: No `.github/workflows` or other automated test runner detected.
- Blocks: Regression safety on dependency upgrades and PR review.

## Test Coverage Gaps

**`WebcamEngine.process_frame` end-to-end:**
- What's not tested: Read → infer → postprocess → render branches (eval, stability on/off, `plot()` path).
- Files: `src/block_detected/runtime/engine.py`, `tests/` (no dedicated test file)
- Risk: Render/regression bugs in `_render()` unnoticed.
- Priority: High — add fake detector + synthetic `numpy` frame test.

**FrameThread lifecycle and generation guards:**
- What's not tested: Stop timeout, stale signal rejection, rapid Start/Stop.
- Files: `src/block_detected/apps/gui/app.py`
- Risk: Threading regressions called out in Phase 5 UAT.
- Priority: Medium — Qt offscreen tests with mocked engine.

**Camera I/O:**
- What's not tested: `open_camera`, `switch_camera`, resolution readback.
- Files: `src/block_detected/io/camera/capture.py`
- Risk: Platform-specific capture failures.
- Priority: Medium — mock `cv2.VideoCapture`.

**Live Ultralytics and webcam:**
- What's not tested: Real `.pt` inference and hardware camera (acceptable omission).
- Files: `models/*.pt`, `detection/yolo/backend.py`
- Risk: Integration issues only found manually.
- Priority: Low for unit suite; document manual UAT in phase verification.

**Docs vs tests mismatch:**
- What's not tested: `test_runtime_state.py` and overlay history deque cited in `.planning/codebase/TESTING.md` do not exist.
- Files: `.planning/codebase/TESTING.md`
- Risk: Planners assume coverage that is absent.
- Priority: Low — fix TESTING.md or add the missing tests.

**Phase 6 manual UAT:**
- What's not tested: All items in `06-VERIFICATION.md` remain unchecked (webcam noise reduction, edge reject, temporal votes, TOML persist, overlay trail).
- Files: `.planning/phases/06-detection-post-processing-reject-rules-and-temporal-stabilit/06-VERIFICATION.md`
- Risk: Stability feature quality unvalidated on real hardware.
- Priority: High before marking Phase 6 complete.

**Collection dependency on ultralytics:**
- What's not tested: Engine-related tests cannot collect without `ultralytics` installed (verified: `pytest` errors on import in a minimal env).
- Files: `tests/test_engine.py`, `tests/test_engine_create.py`, `tests/test_config_apply.py`
- Risk: CI or dev installs with only `[dev]` fail confusingly.
- Priority: Medium — lazy imports or pytest marker `requires_ultralytics`.

---

*Concerns audit: 2026-06-05*
