# Technology Stack

**Analysis Date:** 2026-06-30

## Languages

- **Python** (primary): library + apps (`src/block_detected/`, `src/view/`, `src/stream/`, `main.py`)
  - Evidence: `pyproject.toml` → `requires-python = ">=3.10"`
- **HTML/CSS/JS** (reference only): static spec/mockups under `example_ui/` (not executed by runtime)

## Packaging & Build

- **Build system**: setuptools (`pyproject.toml` → `[build-system] build-backend = "setuptools.build_meta"`)
- **Layout**: `src/`-layout packages (`pyproject.toml` → `[tool.setuptools.packages.find] where = ["src"]`)
- **Install**: pip / editable (`README.md` shows `pip install -e ...`; `bootstrap.py` runs `python -m pip ...`)
- **Lockfiles**: none detected (no `poetry.lock`, `uv.lock`, `requirements.lock`, etc.)

## Runtime Apps (entrypoints)

- **Launcher / device-aware picker**: `main.py` + `bootstrap.py`
  - Routes to:
    - **View (OpenCV window)**: `src/view/app.py`
    - **TUI (Textual dashboard)**: `src/block_detected/tui/app.py`
    - **Stream (Pi JPEG server + desktop viewer)**: `src/stream/server.py`, `src/stream/viewer.py`
- **Console scripts** (packaged): `pyproject.toml` → `[project.scripts]`
  - `block-detected = "main:main"`
  - `block-detected-view = "view.app:main"`
  - `block-detected-tui = "block_detected.tui.app:main"`
  - `block-detected-stream = "stream.__main__:main"`
- **`python -m block_detected`**: `src/block_detected/__main__.py` delegates to repo `main.py`

## Core Libraries

### ML / CV

- **Ultralytics** (YOLO inference): `pyproject.toml` → `ultralytics>=8.4.0`
  - Evidence: `src/block_detected/detection/yolo/backend.py` uses `from ultralytics import YOLO`
- **OpenCV**:
  - Default/core dependency is **headless**: `pyproject.toml` → `opencv-python-headless>=4.8.0`
  - View / viewer require **HighGUI**: `pyproject.toml` → extras `view = ["opencv-python>=4.8.0"]`, `viewer = ["opencv-python>=4.8.0"]`
  - Evidence: `src/view/app.py` uses `cv2.namedWindow`, `cv2.imshow`; `main.py` checks `hasattr(cv2, "imshow")`
- **NumPy** (transitive, also used directly): used in stream viewer + Pi camera adapters
  - Evidence: `src/stream/viewer.py` imports `numpy as np`; `src/block_detected/io/camera/pi/rpicam.py` imports `numpy as np`

### Terminal UI

- **Textual + Rich**: `pyproject.toml` → `textual>=8.0`, `rich>=13.7`
  - Evidence: `src/block_detected/tui/app.py` imports `textual.*` and `rich.*`

### GUI (optional / legacy module still present)

- **PySide6 (Qt)** code exists but is not part of default deps in `pyproject.toml`
  - Evidence (code): `src/block_detected/apps/gui/app.py` and `src/block_detected/apps/gui/widgets/*.py` import `PySide6`
  - Evidence (tests): `tests/test_gui_optional.py`, `tests/test_gui_controls.py` use `pytest.importorskip("PySide6")`

## Configuration & Assets

- **Primary config format**: JSON
  - Default location is **inside the package**: `src/block_detected/block_detected.json`
    - Evidence: `src/block_detected/config/store.py` → `DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"`
- **Typed config schema**: dataclasses in `src/block_detected/config/schema.py` (e.g., `AppConfig`, `CameraConfig`, `InferenceConfig`)
- **Model weights**: local `.pt` files under `models/`
  - Evidence: `src/block_detected/config/paths.py` → `MODELS_DIR = PROJECT_ROOT / "models"`
  - Evidence: `src/block_detected/detection/yolo/loader.py` globs `MODELS_DIR.glob("*.pt")`

## Platform / Hardware Notes

- **Raspberry Pi detection**:
  - Evidence: `src/block_detected/runtime/platform.py` reads `/proc/device-tree/model` and `/proc/cpuinfo`
- **Camera backends**:
  - USB / V4L2 path (Linux): `src/block_detected/io/camera/v4l2.py` uses `cv2.CAP_V4L2`
  - Pi Camera Module (CSI / libcamera):
    - `picamera2` adapter: `src/block_detected/io/camera/pi/picamera2.py`
    - `rpicam-vid` subprocess fallback: `src/block_detected/io/camera/pi/rpicam.py`

## Testing

- **pytest**: `pyproject.toml` → optional `dev = ["pytest>=8.0", "httpx>=0.27"]`
  - Evidence: tests live in `tests/` (e.g., `tests/test_tui_app.py`, `tests/test_bootstrap.py`)

## Notable Standard-Library Usage

- **Sockets & threading**: stream server/client
  - Evidence: `src/stream/server.py`, `src/stream/protocol.py`, `src/stream/viewer.py`
- **Subprocess**: network introspection helpers
  - Evidence: `src/stream/server.py` calls `ip ...`; `src/stream/viewer.py` calls `ipconfig` / `ip`
