# Codebase Concerns

**Analysis Date:** 2026-06-02

## Tech Debt

**Batch application not implemented:**
- Issue: `apps/batch/__init__.py` is a docstring stub only; deleted legacy `batch_detect_square.py` not replaced
- Files: `src/block_detected/apps/batch/__init__.py`, `.planning/ROADMAP.md` Phase 3 plans (`03-01` through `03-03`)
- Impact: No CLI batch inference; `io/images/iter_image_paths` unused in production code
- Fix approach: Implement `apps/batch/app.py`, square-box module under `vision/drawing/`, register `block-detected-batch` in `pyproject.toml`

**No linting or formatting toolchain:**
- Issue: `.gitignore` references `.ruff_cache/` and `.mypy_cache/` but no `ruff`, `mypy`, or formatter config in `pyproject.toml`
- Files: `.gitignore`, `pyproject.toml`
- Impact: Style and import-order drift across contributors
- Fix approach: Add `[tool.ruff]` with minimal rules; optional pre-commit

**Unpinned dependencies:**
- Issue: `requirements.txt` and `pyproject.toml` use lower bounds only (`>=8.4.0`, `>=4.8.0`)
- Files: `pyproject.toml`, `requirements.txt`
- Impact: Non-reproducible installs across machines/CI
- Fix approach: Lock file (`uv.lock` / `pip-tools`) or upper bounds after validation

**Print-based logging:**
- Issue: All operational feedback via `print("[INFO|WARN|ERROR] ...")`
- Files: `src/block_detected/apps/webcam/app.py`, `src/block_detected/ui/input/handlers.py`
- Impact: No log levels, rotation, or structured fields for debugging production issues
- Fix approach: Introduce `logging` module with single config in `config/` or small `core/logging.py`

## Known Bugs

**Arrow key codes platform-specific:**
- Symptoms: Confidence adjust keys may not work on all platforms
- Files: `src/block_detected/config/ui.py` (`KEY_ARROW_UP`, `KEY_ARROW_DOWN`)
- Trigger: Run on OS where `waitKeyEx` codes differ from macOS/Linux values documented
- Workaround: Use mouse UI or document platform-specific constants

**`handle_key` returns unused `switch_model_requested`:**
- Symptoms: Fifth tuple element always `False` in return type docstring vs actual usage
- Files: `src/block_detected/ui/input/handlers.py`
- Trigger: Code review / type checker strictness
- Workaround: None functional — cosmetic API debt

## Security Considerations

**Local-only attack surface:**
- Risk: Low — no network listeners; reads local camera and `models/*.pt`
- Files: entire `src/block_detected/`
- Current mitigation: No remote code execution paths; weights supplied by user
- Recommendations: Do not commit `.pt` from untrusted sources; validate paths if adding user-supplied `--input` in batch CLI (path traversal under user control is acceptable for local tool)

**Secrets:**
- Risk: None required today; `.env` gitignored but unused
- Files: `.gitignore`
- Recommendations: Keep secrets out of `config/*.py` if cloud APIs added later

## Performance Bottlenecks

**Per-frame YOLO inference on full resolution:**
- Problem: Webcam loop runs `model(frame)` every frame at `CAMERA_WIDTH`×`CAMERA_HEIGHT` (1280×720 default)
- Files: `src/block_detected/apps/webcam/app.py`, `src/block_detected/config/camera.py`
- Cause: No frame skipping or async inference queue
- Improvement path: Lower resolution in `camera.py`, smaller model (`yolo26n.pt`), or throttle inference FPS in app loop

**Overlay history copies boxes each frame:**
- Problem: `deque` stores up to `OVERLAY_HISTORY` box lists; `draw_overlay_history` redraws trails
- Files: `src/block_detected/apps/webcam/app.py`, `src/block_detected/vision/drawing/overlays.py`
- Cause: Intentional visual feature
- Improvement path: Cap history or disable by default on low-end hardware

## Fragile Areas

**Webcam main loop monolith:**
- Files: `src/block_detected/apps/webcam/app.py` (~140 lines, nested `switch_model`, shared `ui_state`)
- Why fragile: Mixes inference, rendering mode switch, camera switch, and input in one function
- Safe modification: Extract frame processing to `_process_frame(...)` without changing layer imports; keep cv2 calls out of new modules except `vision`/`io`
- Test coverage: **none** — manual only

**Ultralytics API coupling:**
- Files: `src/block_detected/detection/boxes.py`, `apps/webcam/app.py` (`result.plot()`, `result.boxes`)
- Why fragile: Ultralytics result object shape changes across versions
- Safe modification: Keep all `result.*` access in `detection/` layer; extend fakes in `tests/test_boxes.py`
- Test coverage: partial (`extract_boxes` only)

**PROJECT_ROOT depth assumption:**
- Files: `src/block_detected/config/paths.py` (`parents[3]`)
- Why fragile: Moving `config/paths.py` breaks root resolution
- Safe modification: Add test if path layout changes; consider `importlib.resources` or env override
- Test coverage: `tests/test_config_paths.py` asserts `pyproject.toml` exists under root

## Scaling Limits

**Single webcam session:**
- Current capacity: One OpenCV window, one model loaded, one camera stream
- Limit: No multi-camera or distributed inference
- Scaling path: New `apps/` entry points and `io/video/` for RTSP/files per `AGENTS.md`

**Model discovery linear scan:**
- Current capacity: All `models/*.pt` loaded into list; switch reloads full YOLO each time
- Limit: Many large weights → slow switch and memory pressure
- Scaling path: Lazy load, keep one model hot, or ONNX runtime backend

## Dependencies at Risk

**Ultralytics + PyTorch stack:**
- Risk: Heavy transitive deps; version skew between `ultralytics` and `torch`
- Impact: Install failures or inference errors after `pip install -U`
- Migration plan: Pin versions after CI added; consider ONNX path in `detection/onnx/`

**OpenCV `waitKeyEx` key codes:**
- Risk: Platform-specific constants in `config/ui.py`
- Impact: Broken keyboard shortcuts
- Migration plan: Centralize platform detection or use `ord()`-only keys where possible

## Missing Critical Features

**Batch inference CLI:**
- Problem: Phase 3 planned but not built
- Blocks: Folder-based detection workflow, square-box export to `images_out/`

**CI pipeline:**
- Problem: No automated test run on push
- Blocks: Regression safety for Phase 3+ refactors

**Integration tests for webcam:**
- Problem: No headless or mocked `VideoCapture` tests
- Blocks: Safe refactor of `apps/webcam/app.py`

## Test Coverage Gaps

**`apps/webcam/app.py` main loop:**
- What's not tested: Camera loop, model switching, eval mode, OpenCV window lifecycle
- Files: `src/block_detected/apps/webcam/app.py`
- Risk: Regressions only caught manually
- Priority: Medium (high user visibility)

**`detection/yolo/loader.py`:**
- What's not tested: `discover_model_paths`, `load_yolo`, `default_model_index`
- Files: `src/block_detected/detection/yolo/loader.py`
- Risk: Broken model discovery after path changes
- Priority: Medium

**Vision drawing modules:**
- What's not tested: `overlays.py`, `eval.py`, `widgets.py` pixel output
- Files: `src/block_detected/vision/drawing/*`
- Risk: Visual regressions in UI overlays
- Priority: Low–Medium (Phase 3 square-box tests will add drawing coverage)

**`io/camera/capture.py`:**
- What's not tested: `open_camera`, `switch_camera` (requires hardware or heavy cv2 mock)
- Files: `src/block_detected/io/camera/capture.py`
- Risk: Camera switch edge cases on different OS
- Priority: Low for unit tests; manual QA

## Removed Legacy Code

**Deleted root scripts:**
- `run_yolo_webcam.py` and `batch_detect_square.py` removed in favor of package layout
- Risk: External docs or habits referencing old filenames
- Mitigation: `main.py` + README + `AGENTS.md` document new entry points

---

*Concerns audit: 2026-06-02*
