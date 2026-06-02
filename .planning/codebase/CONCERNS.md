# Codebase Concerns

**Analysis Date:** 2026-06-02

## Tech Debt

**Duplicated inference logic across scripts:**
- Issue: `run_yolo_webcam.py` and `batch_detect_square.py` each load Ultralytics `YOLO`, parse `result.boxes`, and draw annotations independently. Box drawing differs (webcam: `result.plot()` + optional history overlay; batch: square boxes via `draw_square_box`). No shared package or module.
- Files: `run_yolo_webcam.py`, `batch_detect_square.py`
- Impact: Bug fixes and API changes (e.g. unified square boxes on webcam) require editing two files; behavior drifts between realtime and batch.
- Fix approach: Extract a small `detection/` or `lib/` module with `load_model()`, `run_inference()`, and optional `draw_boxes(mode="rect"|"square")`; keep scripts as thin CLIs.

**Inconsistent configuration style:**
- Issue: Webcam uses module-level constants (`CAMERA_INDEX`, `CONF_MIN`, `DEFAULT_MODEL_NAME`, etc. in `run_yolo_webcam.py`); batch uses `argparse` (`batch_detect_square.py`). README tells users to edit source for webcam settings but flags for batch.
- Files: `run_yolo_webcam.py`, `batch_detect_square.py`, `README.md`
- Impact: Harder to script, deploy, or document one set of runtime options.
- Fix approach: Add `argparse` (or env vars) to webcam for model dir, camera index, resolution, default conf; align defaults with batch (`--conf 0.01` vs webcam default `0.25`).

**Hardcoded platform-specific keyboard codes:**
- Issue: Confidence adjustment uses magic `cv2.waitKeyEx` return values `2490368` (up) and `2621440` (down) in `run_yolo_webcam.py`.
- Files: `run_yolo_webcam.py` (lines ~260–271)
- Impact: Arrow keys may not adjust confidence on macOS/Linux or with different OpenCV builds; README documents arrows as working everywhere.
- Fix approach: Use `cv2.waitKey` with `ord` for `+`/`-` or `w`/`s`, or map keys via a small lookup table per platform; document portable keys in `README.md`.

**Full model reload on every switch:**
- Issue: `switch_model()` constructs a new `YOLO(str(current_path))` on each switch instead of caching loaded models.
- Files: `run_yolo_webcam.py` (`switch_model` nested function)
- Impact: Noticeable pause and memory churn when cycling multiple `.pt` files during live capture.
- Fix approach: Preload all discovered models into a `dict[Path, YOLO]` at startup, or lazy-cache on first use.

**Models excluded from version control:**
- Issue: `.gitignore` ignores `models/*.pt`; only `models/.gitkeep` is tracked. README lists several example weights (`train-2.pt`, `yolo26n.pt`, etc.) that are not in the repo.
- Files: `.gitignore`, `models/.gitkeep`, `README.md`
- Impact: Fresh clone fails until weights are copied manually; docs over-promise available models.
- Fix approach: Document a single download/setup step; optional Git LFS or release asset for default `train-3.pt`; trim README model list to what is actually shipped or linked.

**No project tooling for quality:**
- Issue: No `pyproject.toml`, `ruff`, `mypy`, `pytest`, pre-commit, or CI workflow. `.gitignore` references `.ruff_cache/` and `.pytest_cache/` but no configs exist.
- Files: `.gitignore`, repo root
- Impact: Style and regressions are unchecked; Python 3.14 venv in workspace vs README “3.10+” is untested in automation.
- Fix approach: Add minimal `ruff` + `pytest` smoke tests and optional GitHub Actions on push.

## Known Bugs

**Model switch failure desyncs UI and weights:**
- Symptoms: After a failed load, on-screen status and button show the new `current_path.name`, but inference still uses the previous `model` object.
- Files: `run_yolo_webcam.py` (`switch_model`: increments `model_index` / `current_path` before `try`, only assigns `model` on success)
- Trigger: Place a corrupt or incompatible `.pt` in `models/`, cycle models with `v` or the UI button until load throws.
- Workaround: Restart script; remove bad `.pt` from `models/`.

**Batch output can overwrite inputs:**
- Symptoms: If `--output` equals `--input` (or user points both at `images/`), `cv2.imwrite` overwrites source files in place.
- Files: `batch_detect_square.py` (`out_path = output_dir / image_path.name`, `cv2.imwrite`)
- Trigger: `python batch_detect_square.py --input images --output images`
- Workaround: Always use separate dirs (default `images_out/`); add a guard rejecting `output_dir.resolve() == input_dir.resolve()`.

**Webcam exits on single bad frame or inference error:**
- Symptoms: One failed `cap.read()` or one inference exception breaks the entire loop instead of retrying.
- Files: `run_yolo_webcam.py` (main loop `break` on read failure and on inference `except`)
- Trigger: Brief camera glitch or transient GPU OOM.
- Workaround: Restart script; reduce resolution constants.

## Security Considerations

**Trusted model binaries (PyTorch pickle):**
- Risk: `.pt` weights are loaded via Ultralytics/PyTorch; malicious weights can execute code on load.
- Files: `run_yolo_webcam.py`, `batch_detect_square.py`, `models/*.pt` (local only, gitignored)
- Current mitigation: None in code; operator must trust model source.
- Recommendations: Only load weights from known training runs; document provenance; avoid loading arbitrary downloaded `.pt` on shared machines.

**No network surface in application code:**
- Risk: Low for these scripts; Ultralytics may download assets on first use depending on version/settings.
- Files: N/A in repo scripts
- Current mitigation: Offline inference once dependencies and weights are local.
- Recommendations: Run in offline/air-gapped mode when auditing; pin `ultralytics` version.

**Environment files ignored but unused:**
- Risk: Low today; `.env` is gitignored (`.gitignore`) but no code reads env vars.
- Files: `.gitignore`
- Current mitigation: No secrets in repo scripts.
- Recommendations: If env-based config is added later, provide `.env.example` without secrets (pattern already in `.gitignore`: `!.env.example`).

## Performance Bottlenecks

**Per-frame full-resolution YOLO on webcam:**
- Problem: Every captured frame at up to 1280×720 runs through the model with no skipping or ROI.
- Files: `run_yolo_webcam.py` (`CAMERA_WIDTH`, `CAMERA_HEIGHT`, main loop `model(frame, ...)`)
- Cause: Synchronous inference in the display loop; no threading or frame decimation.
- Improvement path: Lower resolution; process every Nth frame; run inference in a worker thread and show latest result; use TensorRT/exported engine if GPU available.

**Redundant work in normal webcam mode:**
- Problem: Code calls `extract_boxes(result)` and also `result.plot()`, then optionally draws history on top of the plotted image.
- Files: `run_yolo_webcam.py` (`extract_boxes`, `result.plot`, `draw_overlay_history`)
- Cause: History overlay needs raw boxes; plot already draws boxes.
- Improvement path: Single render path: either custom draw from boxes only, or disable built-in plot boxes when overlay is on.

**Batch processing is strictly sequential:**
- Problem: Images processed one-by-one in a Python loop; no DataLoader batching or parallel I/O.
- Files: `batch_detect_square.py` (`for idx, image_path in enumerate(image_paths)`)
- Cause: Simple script design.
- Improvement path: `model.predict(source=input_dir, stream=True)` Ultralytics batch API; optional multiprocessing for I/O.

**Default confidence thresholds encourage noisy detections:**
- Problem: Batch default `--conf 0.01` and webcam eval mode `EVAL_CONF = 0.01` surface many low-confidence boxes.
- Files: `batch_detect_square.py`, `run_yolo_webcam.py`
- Cause: Tuned for inspection/debug, not production filtering.
- Improvement path: Document production defaults (e.g. 0.25–0.5); separate `--debug` flag for low conf.

## Fragile Areas

**OpenCV GUI and camera portability:**
- Files: `run_yolo_webcam.py`, `batch_detect_square.py` (`cv2.imshow`, `VideoCapture`, `waitKeyEx`)
- Why fragile: Behavior varies by OS, headless servers, and display backend; camera indices 0–5 are probed heuristically.
- Safe modification: Test on target OS; guard GUI with `--headless` for batch-only servers; use `CAP_DSHOW` / `CAP_AVFOUNDATION` only behind platform checks if needed.
- Test coverage: None.

**Ultralytics API coupling:**
- Files: `run_yolo_webcam.py` (`model(frame, ...)`), `batch_detect_square.py` (`model.predict(source=img, ...)`)
- Why fragile: Minor version bumps can change result object shape or kwargs.
- Safe modification: Pin `ultralytics` in `requirements.txt` to exact version after validation; wrap inference in one function.
- Test coverage: None.

**Mouse callback and mutable `ui_state` dict:**
- Files: `run_yolo_webcam.py` (`on_mouse`, `ui_state`, `cv2.setMouseCallback`)
- Why fragile: Relies on closure `switch_model` and `button_rect` updated every frame; race-free only because single-threaded loop.
- Safe modification: Keep all UI mutations on main thread; avoid refactoring to async without revisiting callback design.
- Test coverage: None.

## Scaling Limits

**Single-process desktop scripts:**
- Current capacity: One webcam stream or one batch folder per process; no queue, API, or multi-camera fusion.
- Limit: Cannot serve multiple clients or edge devices from this codebase as-is.
- Scaling path: Wrap inference in FastAPI/gRPC, or export to ONNX/TensorRT for embedded deployment; out of current repo scope.

**Repository size from sample images:**
- Current capacity: ~62 MB of PNG fixtures under `images/` committed to git.
- Limit: Clone and CI artifact size grow with each added sample image.
- Scaling path: Move fixtures to Git LFS, external dataset URL, or a small `images/sample/` subset for docs only.

## Dependencies at Risk

**Loose version pins:**
- Risk: `ultralytics>=8.4.0` and `opencv-python>=4.8.0` in `requirements.txt` allow breaking upgrades on fresh `pip install`.
- Impact: Reproducible builds and CUDA/torch pairing documented in README may break silently.
- Migration plan: Pin exact versions after a known-good matrix (Python 3.11 + torch + ultralytics); optional `requirements-lock.txt` or `uv lock`.

**Transitive PyTorch stack not declared:**
- Risk: `requirements.txt` does not list `torch`; Ultralytics installs a default torch build which may be CPU-only or wrong CUDA version.
- Impact: README troubleshooting section required for GPU users; performance surprises.
- Migration plan: Document two requirement files (`requirements-cpu.txt`, `requirements-cu124.txt`) or install torch first per PyTorch matrix.

**Python 3.14 / bleeding-edge interpreters:**
- Risk: Local `venv/` may use Python 3.14 while README recommends 3.10–3.13; ultralytics/torch wheels may lag newest Python.
- Impact: Install failures or runtime bugs on newest Python.
- Migration plan: Add `.python-version` or document tested versions; CI on 3.11 and 3.12.

## Missing Critical Features

**No training or evaluation pipeline in repo:**
- Problem: Only inference scripts exist; no `train.py`, dataset YAML, or metrics export despite YOLO training being the natural complement.
- Blocks: Retraining or fine-tuning from this repo alone; operators must use external Ultralytics CLI/notebooks.

**No automated tests:**
- Problem: Zero `test_*.py`, `pytest`, or CI.
- Blocks: Safe refactors of box drawing, model switch logic, and CLI validation.

**No headless / export path:**
- Problem: Webcam and batch preview depend on OpenCV windows.
- Blocks: Running on servers without display without code changes.

## Test Coverage Gaps

**Square box geometry (`draw_square_box`):**
- What's not tested: Clamping at image edges, square side from rectangular YOLO boxes, degenerate boxes.
- Files: `batch_detect_square.py`
- Risk: Silent off-by-one or empty squares on edge cases.
- Priority: Medium

**Model discovery and default selection:**
- What's not tested: `discover_model_paths()`, `default_model_index()` when `train-3.pt` missing.
- Files: `run_yolo_webcam.py`
- Risk: Wrong default model or empty list handling regressions.
- Priority: Medium

**Model switch failure handling:**
- What's not tested: Failed load keeps previous weights but updates `current_path` (known bug).
- Files: `run_yolo_webcam.py`
- Risk: User trusts wrong label on screen during demo.
- Priority: High

**Batch CLI validation:**
- What's not tested: Missing model, empty input dir, equal input/output paths, invalid `--conf`.
- Files: `batch_detect_square.py`
- Risk: Data loss (overwrite) or confusing exit codes.
- Priority: High

---

*Concerns audit: 2026-06-02*
