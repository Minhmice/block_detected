# Codebase Concerns

**Analysis Date:** 2026-06-30

This document lists *high-impact risk areas* (tech debt, fragility, drift) in the current repo state, with concrete file-path evidence.

## Repo Knowledge-Graph Drift (Graphify)

**`graphify-out/` is not present in this workspace checkout.**
- **Evidence**: `.gitignore` excludes `graphify-out/` (`.gitignore`).
- **Impact**: Any process that expects `graphify-out/GRAPH_REPORT.md` as a source of truth will fail in a fresh clone / CI.
- **Mitigation**: Treat Graphify output as optional; ensure docs remain accurate without it.

## Configuration & Persistence Risks

**Config format and location may surprise contributors (package JSON + legacy migration).**
- **Evidence**: Default config path is inside the package at `src/block_detected/block_detected.json` (referenced by `README.md`; implemented in `src/block_detected/config/store.py` as `DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"`).
- **Legacy migration**: `src/block_detected/config/store.py` migrates root-level `block_detected.json` or `block_detected.toml` into the package JSON on first load (`_migrate_legacy_config_if_needed`).
- **Impact**:
  - Editing `block_detected.toml` / root JSON may “stop working” after migration.
  - Editable installs may put the package config under a different site-packages location than expected, making “where did my config go?” a recurring issue.
- **Mitigation ideas**:
  - Consider making repo-root config the canonical runtime path (and keep package JSON as defaults only), or surface the resolved config path in app UIs/logs.

**Runtime config wrappers can obscure the real implementation.**
- **Evidence**: `src/block_detected/runtime/config_schema.py` and `src/block_detected/runtime/config_store.py` are *deprecated re-exports* to `block_detected.config.*`.
- **Impact**: Readers may edit the runtime wrapper files instead of the real `src/block_detected/config/schema.py` / `src/block_detected/config/store.py`.
- **Mitigation**: Clearly mark wrappers as “do not edit” in docs, or remove wrappers once callers are migrated.

## Entry Points & App Surface Area Drift

**Two “frontends” exist (OpenCV View + PySide6 GUI code) but the launcher path is not unified.**
- **Evidence**:
  - OpenCV View entry: `src/view/app.py` (used by `main.py` for `--view`; script `block-detected-view` in `pyproject.toml`).
  - PySide6 GUI code exists: `src/block_detected/apps/gui/app.py`, `src/block_detected/apps/gui/robo_window.py`, and widgets under `src/block_detected/apps/gui/widgets/`.
  - `README.md` states View is the primary desktop UI (“OpenCV detection preview — replaces PySide6 GUI.” in `src/view/app.py`).
- **Impact**: Contributor confusion about which UI is “real”, and duplicated maintenance cost across two presentation layers.
- **Mitigation**: Decide whether PySide6 GUI is supported:
  - If **not supported**: remove/archival-move `src/block_detected/apps/gui/` and update planning docs.
  - If **supported**: expose a `--gui` mode consistently in `main.py` and optional deps in `pyproject.toml`.

## Pipeline Wiring Gaps (Config Fields vs Behavior)

**`classical.enabled` does not gate classical behavior; blur is applied regardless.**
- **Evidence**: `src/block_detected/runtime/frame_loop.py` always passes `cl.blur_kernel` into `apply_preprocess(...)` without checking `cl.enabled`.
- **Impact**: Turning classical “off” may still blur frames if `blur_kernel` is non-zero, contradicting expectations.
- **Mitigation**: Either:
  - Gate *all* classical knobs behind `classical.enabled`, or
  - Remove `classical.enabled` and treat each knob as independent.

**“Warped face” overlay is declared but appears intentionally unimplemented.**
- **Evidence**:
  - Schema includes `classical.show_warped_face` (`src/block_detected/config/schema.py`).
  - GUI disables it with a “future phase” tooltip (`src/block_detected/apps/gui/widgets/camera_toolbar.py`).
- **Impact**: Planning/UAT can drift into assuming it exists (it’s a visible knob in schema).
- **Mitigation**: Keep the field but mark it explicitly “reserved” in planning docs, or remove from schema until implemented.

## Failure Handling & Robustness

**A single inference exception stops the entire frame loop.**
- **Evidence**: In `src/block_detected/runtime/frame_loop.py`, inference exceptions `return None`, and the caller loop exits (`src/view/app.py` breaks when `processed is None`).
- **Impact**: Transient GPU/Ultralytics errors or a single corrupt frame can kill the session instead of degrading gracefully.
- **Mitigation**: Differentiate fatal vs recoverable errors:
  - On inference exception, log + skip frame (keep camera open), optionally backoff/retry detector.
  - On camera read failure, consider retrying reopen depending on source type.

## Hot-Reload Semantics (Config Apply)

**Hot-apply is “replace config” without merge semantics.**
- **Evidence**: `src/block_detected/runtime/engine.py` sets `self.config = config` in `apply_hot_config`, no “preserve non-hot keys” merging.
- **Impact**: UI code that updates only part of config must be careful to send a full coherent config snapshot, otherwise fields can unintentionally reset.
- **Mitigation**: Introduce a merge helper (or enforce “always full config snapshot” contracts at UI boundaries).

## Dependencies at Risk

**Ultralytics + PyTorch stack remains a volatility hotspot.**
- **Evidence**: `src/block_detected/detection/yolo/backend.py` uses Ultralytics `YOLO(...)`; `pyproject.toml` uses `ultralytics>=8.4.0`.
- **Impact**: Upstream API changes or platform-specific install failures can break the entire app surface.
- **Mitigation**: Pin upper bounds (or lock), and keep tests that cover the `DetectorBackend.predict(...)` contract.

**OpenCV backend differences across OSes and camera sources.**
- **Evidence**: Desktop uses `cv2.VideoCapture` and Pi uses alternate capture types (`src/block_detected/runtime/engine.py` imports `PiCameraCapture`, `RpicamCapture`; open/switch lives in `src/block_detected/runtime/session.py`).
- **Impact**: “Works on my machine” camera behavior is likely; driver/property quirks are common.
- **Mitigation**: Expand mocked camera tests and log actual negotiated resolution/source at startup.

## Repository Complexity / Legacy Code

**Parallel legacy implementation tree (`src/block_detection_v2/`) can distract and drift.**
- **Evidence**: Many files under `src/block_detection_v2/` including a separate YOLO detector and pipeline (`src/block_detection_v2/yolo_detector.py`, `src/block_detection_v2/pipeline.py`).
- **Impact**: New contributors may copy patterns from v2 that aren’t used by v1, or misunderstand which pipeline is production.
- **Mitigation**: Mark as “archive/prototype” in docs, or move to `experiments/` with a clear README.

## Planning & Documentation Drift

**Planning artifacts can easily go stale vs active code.**
- **Evidence**: The repo contains a large `.planning/phases/` tree and multiple app surfaces (`src/view/`, `src/stream/`, `src/block_detected/apps/tui/`, plus optional GUI code).
- **Impact**: UAT/verification steps can reference removed or unshipped UI (e.g., GUI-only behaviors) and create false “incomplete” signals.
- **Mitigation**: Regularly sync `.planning/` documents to the actual entry points defined in `pyproject.toml` + `main.py` + `README.md`.

---

*Concerns audit: 2026-06-30*
