# External Integrations

**Analysis Date:** 2026-06-30

## Network / Protocol Integrations

- **Raspberry Pi JPEG stream (custom TCP/UDP protocol)**
  - **UDP discovery**: server listens and replies with JSON metadata
    - Evidence: `src/stream/server.py` (`discovery_loop`, binds UDP port from `src/stream/protocol.py`)
    - Evidence: `src/stream/protocol.py` defines `UDP_PORT = 5001` and `DISCOVERY_MESSAGE = b"RASPI_CAM_DISCOVER_V1"`
  - **TCP streaming**: client sends a JSON “config” line, server ACKs JSON, then sends frames as `uint32_be length + jpeg_bytes`
    - Evidence: `src/stream/server.py` (`read_config`, `send_json_line`, `struct.pack("!I", len(data))`)
    - Evidence: `src/stream/protocol.py` (`send_json_line`, `recv_json_line`, `pack_frame`)
  - **Desktop viewer**: LAN discovery + TCP client + OpenCV window
    - Evidence: `src/stream/viewer.py` (`discover_server`, `socket.connect`, `cv2.imshow`)
  - **Operational note**: stream server introspects IP addresses via OS commands
    - Evidence: `src/stream/server.py` runs `ip -o -4 addr show up`
    - Evidence: `src/stream/viewer.py` runs `ipconfig /all` on Windows and `ip -o -4 ...` elsewhere

## ML / Model Integration

- **Ultralytics YOLO (local `.pt` weights)**
  - **Model discovery**: `.pt` files in `models/`
    - Evidence: `src/block_detected/detection/yolo/loader.py` (`MODELS_DIR.glob("*.pt")`)
  - **Model load + inference**:
    - Evidence: `src/block_detected/detection/yolo/backend.py` (`from ultralytics import YOLO`, `YOLO(str(model_path))`)
  - **No explicit remote model download APIs used** in application code (no Hub calls found in the YOLO backend modules above)

## Hardware / OS Integrations

- **Camera capture**
  - **Linux USB / V4L2**: opens `cv2.VideoCapture(..., cv2.CAP_V4L2)`
    - Evidence: `src/block_detected/io/camera/v4l2.py` (`open_v4l2`, `find_usb_camera`)
  - **Raspberry Pi Camera Module (CSI / libcamera)**
    - `picamera2` adapter
      - Evidence: `src/block_detected/io/camera/pi/picamera2.py` imports `Picamera2` and exposes `PiCameraCapture.read()`
    - `rpicam-vid` subprocess adapter (YUV420 → BGR via OpenCV)
      - Evidence: `src/block_detected/io/camera/pi/rpicam.py` runs `subprocess.Popen(["rpicam-vid", ...])` and converts via `cv2.cvtColor(...)`
  - **Source selection logic**:
    - Evidence: `src/block_detected/runtime/session.py` selects `usb` vs `libcamera`/`rpicam` based on config + `is_raspberry_pi()`
    - Evidence: `src/block_detected/io/camera/open.py` dispatches `source` string to the correct backend

## UI Integrations

- **OpenCV HighGUI window loop (desktop View app)**
  - Evidence: `src/view/app.py` uses `cv2.namedWindow`, `cv2.setMouseCallback`, `cv2.waitKeyEx`, `cv2.imshow`
- **Terminal UI (Textual + Rich)**
  - Evidence: `src/block_detected/tui/app.py` imports `textual.*` and `rich.*`
- **Desktop LAN viewer UI (tkinter + OpenCV)**
  - Evidence: `src/stream/viewer.py` uses `tkinter`/`ttk` for controls and `cv2.namedWindow/cv2.imshow` for frames
- **Optional/legacy PySide6 GUI modules exist**
  - Evidence: `src/block_detected/apps/gui/app.py` (PySide6 imports) and `tests/test_gui_controls.py` (`pytest.importorskip("PySide6")`)

## Storage Integrations

- **Local filesystem only**
  - **Config**: JSON stored in-package by default
    - Evidence: `src/block_detected/config/store.py` → `DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"`
    - Evidence: default shipped JSON: `src/block_detected/block_detected.json`
  - **Models**: `.pt` weights under `models/`
    - Evidence: `src/block_detected/config/paths.py` → `MODELS_DIR = PROJECT_ROOT / "models"`

## Observability

- **Stdlib logging (no external log shipping)**
  - Evidence: `src/block_detected/runtime/logging_setup.py` + `log_event` usage in `src/block_detected/runtime/engine.py`

## What is *not* integrated (as of code on disk)

- **No HTTP server / REST API in runtime**
  - Evidence: stream is raw sockets (`src/stream/*`); no `fastapi` package dependency in `pyproject.toml`
- **No database**
  - Evidence: no DB modules under `src/`; config + assets are file-based (see paths above)
