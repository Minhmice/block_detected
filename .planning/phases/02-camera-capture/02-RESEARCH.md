# Phase 2: Camera & Capture - Research

**Researched:** 2026-05-31 [VERIFIED: local date context]
**Domain:** Raspberry Pi CSI and USB camera acquisition for a 640x480 OpenCV vision pipeline [VERIFIED: .planning/ROADMAP.md]
**Confidence:** MEDIUM [VERIFIED: local environment probes; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html]

<user_constraints>
## User Constraints

No phase `CONTEXT.md` exists for Phase 2, so there are no additional locked decisions from `/gsd-discuss-phase`. [VERIFIED: `gsd-tools.cjs init phase-op 2` returned `has_context=false`]

### Locked Decisions

- Phase 2 goal is stable 640x480 frames from Pi Camera or USB with reproducible capture settings. [VERIFIED: .planning/ROADMAP.md]
- Phase 2 must keep Pi Camera and USB paths abstracted behind one frame source interface. [VERIFIED: user prompt]
- Phase 2 must address CAM-01, CAM-02, and CAM-03. [VERIFIED: user prompt; VERIFIED: .planning/REQUIREMENTS.md]
- Project v1 forbids ArUco and AprilTag fiducials on blocks. [VERIFIED: .planning/PROJECT.md]
- Project output must conform to the existing `DetectionResult` contract in `detection_contract.py`. [VERIFIED: .planning/PROJECT.md; VERIFIED: detection_contract.py]

### Claude's Discretion

- The exact module split, class names, and debug file naming scheme are not locked. [VERIFIED: no Phase 2 CONTEXT.md; VERIFIED: .planning/research/ARCHITECTURE.md]
- Exposure and white balance lock values are not locked and must be configurable per camera and lighting setup. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]

### Deferred Ideas (OUT OF SCOPE)

- Classification, contour detection, corner ordering, pose mapping, reject policy, and test-set evaluation are later phases. [VERIFIED: .planning/ROADMAP.md]
- Multi-block scene graph, temporal tracking, and live tuning UI are v2 requirements. [VERIFIED: .planning/REQUIREMENTS.md]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAM-01 | Capture 640x480 from Pi Camera or USB via stable backend abstraction. [VERIFIED: .planning/REQUIREMENTS.md] | Use a `FrameSource` protocol plus `PiCamera2FrameSource` and `UsbVideoCaptureFrameSource`; Picamera2 supports configured stream sizes and OpenCV supports `VideoCapture` device capture and width/height properties. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html] |
| CAM-02 | Lock exposure and white balance when hardware supports it. [VERIFIED: .planning/REQUIREMENTS.md] | For Pi Camera, use Picamera2 controls such as `AeEnable`, `AwbEnable`, `ExposureTime`, `AnalogueGain`, and `ColourGains`; for USB, probe V4L2 controls and degrade gracefully because OpenCV property behavior depends on backend, driver, and hardware. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html; CITED: https://www.kernel.org/doc/html/v4.8/media/uapi/v4l/control.html] |
| CAM-03 | Save raw frames and optional overlays to debug directory with frame id. [VERIFIED: .planning/REQUIREMENTS.md] | Use a dedicated debug sink that names files from the monotonic `frame_id`; use OpenCV `imwrite` and check its boolean return. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html] |
</phase_requirements>

## Summary

Phase 2 should build only the capture boundary: one source-neutral `FrameSource` interface, concrete CSI and USB adapters, manual-control application, and a debug artifact sink. [VERIFIED: .planning/ROADMAP.md; VERIFIED: user prompt] The implementation should normalize every successful frame to the same in-memory shape and color convention before later pipeline phases see it. [VERIFIED: .planning/research/ARCHITECTURE.md; CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html]

The CSI path should use Picamera2 rather than `cv2.VideoCapture`, because the project stack notes identify Picamera2 as the Pi Camera path and Picamera2 exposes libcamera controls needed for reproducible exposure/WB. [VERIFIED: .planning/research/STACK.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] The USB path should use OpenCV `VideoCapture` for frame reads and V4L2 controls for hardware settings where available, because OpenCV documents USB-style device capture while also warning that property behavior depends on backend, driver, and hardware. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html]

**Primary recommendation:** Plan a `camera.py` module with `FrameSource`, `CaptureFrame`, `CameraSettings`, `PiCamera2FrameSource`, `UsbVideoCaptureFrameSource`, `ImageSequenceFrameSource`, and `DebugFrameWriter`; use fake/image-sequence sources for local tests and target-hardware smoke tests for real camera controls. [VERIFIED: .planning/research/ARCHITECTURE.md; VERIFIED: local environment probes; ASSUMED]

## Project Constraints (from CLAUDE.md)

- The project is a Raspberry Pi edge vision pipeline for detecting one of four cube blocks at fixed 640x480 camera resolution. [VERIFIED: CLAUDE.md]
- The project must not use ArUco or AprilTag markers on blocks. [VERIFIED: CLAUDE.md]
- The technical stack is Python 3, OpenCV, TensorFlow Lite INT8, and Pi-compatible runtime components. [VERIFIED: CLAUDE.md]
- The public output must conform to `detection_contract.py`. [VERIFIED: CLAUDE.md; VERIFIED: detection_contract.py]
- Before file-changing work, GSD workflow artifacts must stay in sync; this research phase is being written under the GSD research workflow. [VERIFIED: CLAUDE.md; VERIFIED: user prompt]
- No project-local skills were found under `.claude/skills/` or `.agents/skills/`. [VERIFIED: local `find .claude/skills .agents/skills -name SKILL.md`]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | Target Pi: Python 3.11.x; local dev host currently Python 3.14.4. [VERIFIED: .planning/research/STACK.md; VERIFIED: local `python3 --version`] | Runtime and test execution. [VERIFIED: CLAUDE.md] | Project constraints specify Python 3 and Pi compatibility. [VERIFIED: CLAUDE.md] |
| OpenCV Python (`opencv-python`) | 4.13.0.92, published 2026-02-05. [VERIFIED: PyPI JSON 2026-05-31] | USB `VideoCapture`, BGR image arrays, debug image saves, and later OpenCV processing. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html] | OpenCV exposes camera backends, frame properties, and image write APIs used by CAM-01 and CAM-03. [CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html; CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html] |
| NumPy | 2.4.6, published 2026-05-18. [VERIFIED: PyPI JSON 2026-05-31] | Frame arrays and test fixtures. [VERIFIED: .planning/research/STACK.md] | Picamera2 and OpenCV Python operate on array-like image buffers in the project stack. [VERIFIED: .planning/research/STACK.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] |
| Picamera2 | 0.3.36, published 2026-05-06. [VERIFIED: PyPI JSON 2026-05-31] | Raspberry Pi CSI camera capture and libcamera controls. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] | Picamera2 documents stream sizing, `capture_array()` support, metadata, and controls for exposure/WB. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| pytest | 9.0.3, published 2026-04-07. [VERIFIED: PyPI JSON 2026-05-31] | Unit tests for frame source protocol, config parsing, debug filename monotonicity, and fake source behavior. [ASSUMED] | Use in Wave 0 because no test infrastructure exists yet. [VERIFIED: local file scan] |
| Pillow | 12.2.0, published 2026-04-01. [VERIFIED: PyPI JSON 2026-05-31] | Optional image inspection or fallback debug writes. [ASSUMED] | Prefer OpenCV `imwrite`; add Pillow only if the implementation needs non-OpenCV image utilities. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html; ASSUMED] |
| `v4l2-ctl` / v4l-utils | Target version not probed on Pi. [VERIFIED: local `v4l2-ctl` probe missing; ASSUMED] | List and set USB camera controls. [CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html] | Use for Linux USB cameras when OpenCV property set/readback is insufficient. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html] |
| `rpicam-hello` or `libcamera-hello` | Target version not probed on Pi. [VERIFIED: local `rpicam-hello` and `libcamera-hello` probes missing; ASSUMED] | Hardware smoke test before Python capture debugging. [CITED: https://www.raspberrypi.com/documentation/computers/camera_software.html] | Use only on target Raspberry Pi hardware. [ASSUMED] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Picamera2 for CSI | OpenCV `VideoCapture` for Pi Camera | Do not make this the standard path; Phase 2 needs exposure/WB control and the project stack already selects Picamera2 for CSI. [VERIFIED: .planning/research/STACK.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] |
| OpenCV `VideoCapture` for USB | Picamera2 USB support | Picamera2 documentation notes support for non-Pi cameras is limited, so USB should remain an OpenCV/V4L2 adapter. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; ASSUMED] |
| OpenCV `imwrite` for debug images | Custom PNG/JPEG encoder | Do not hand-roll image encoding; OpenCV already saves images based on filename extension and returns success/failure. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html] |

**Installation:**

```bash
# Development/test dependencies for Phase 2. [VERIFIED: PyPI JSON 2026-05-31]
python3 -m venv .venv
. .venv/bin/activate
python -m pip install "opencv-python==4.13.0.92" "numpy>=2,<3" "pytest==9.0.3"

# Target Raspberry Pi CSI dependencies are expected to include Picamera2/libcamera packages. [ASSUMED]
# Confirm exact apt package names on the target image before locking the plan. [ASSUMED]
```

**Version verification:** `python3 -m pip index versions` reported `opencv-python 4.13.0.92`, `numpy 2.4.6`, `picamera2 0.3.36`, `pytest 9.0.3`, and `pillow 12.2.0` on 2026-05-31. [VERIFIED: local command; VERIFIED: PyPI JSON 2026-05-31]

## Architecture Patterns

### Recommended Project Structure

```text
src/block_detected/
  camera.py          # FrameSource protocol, settings, CSI/USB/image-sequence adapters. [ASSUMED]
  debug.py           # DebugFrameWriter for raw/overlay artifacts. [ASSUMED]
  pipeline.py        # Later phase integration point for detect_block(frame). [VERIFIED: .planning/research/ARCHITECTURE.md]
tests/
  test_camera_source.py  # fake/image-sequence source tests. [ASSUMED]
  test_debug_writer.py   # frame id and debug artifact tests. [ASSUMED]
config/
  camera.example.json    # capture size and manual-control profile. [ASSUMED]
debug_frames/            # gitignored runtime artifacts. [ASSUMED]
```

### Pattern 1: FrameSource Protocol

**What:** Define a source-neutral interface that returns a `CaptureFrame` with `frame_id`, `image_bgr`, monotonic timestamp, backend name, and optional camera metadata. [ASSUMED]

**When to use:** Use for every capture backend so later phases never branch on CSI versus USB. [VERIFIED: user prompt; VERIFIED: .planning/research/ARCHITECTURE.md]

**Example:**

```python
# Source basis: project architecture requires a camera abstraction, and OpenCV/Picamera2 both return frame arrays. [VERIFIED: .planning/research/ARCHITECTURE.md; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]
from dataclasses import dataclass
from typing import Mapping, Protocol

import numpy as np


@dataclass(frozen=True)
class CaptureFrame:
    frame_id: str
    image_bgr: np.ndarray
    timestamp_ns: int
    source: str
    metadata: Mapping[str, object]


class FrameSource(Protocol):
    def start(self) -> None: ...
    def read(self) -> CaptureFrame: ...
    def stop(self) -> None: ...
```

### Pattern 2: Two-Step Camera Stabilization and Lock

**What:** Start camera auto controls, capture/read metadata after warmup, then apply manual exposure/gain/WB controls when supported. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]

**When to use:** Use for CAM-02 under fixed lighting; skip unsupported controls with explicit metadata and logs. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html]

**Example:**

```python
# Source basis: Picamera2 exposes AeEnable, AwbEnable, ExposureTime, AnalogueGain, ColourGains, and capture metadata. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

metadata = picam2.capture_metadata()
picam2.set_controls({
    "AeEnable": False,
    "AwbEnable": False,
    "ExposureTime": metadata["ExposureTime"],
    "AnalogueGain": metadata["AnalogueGain"],
    "ColourGains": metadata["ColourGains"],
})
frame = picam2.capture_array()
```

### Pattern 3: Debug Sink Outside Capture Backend

**What:** Capture backends should produce frames; a separate writer should persist raw and overlay artifacts. [ASSUMED]

**When to use:** Use for CAM-03 so debug writes can be enabled, disabled, or throttled without changing camera code. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED]

**Example:**

```python
# Source basis: OpenCV imwrite saves images by extension and returns a success boolean. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html]
from pathlib import Path
import cv2 as cv


def write_debug_frame(debug_dir: Path, frame_id: str, image_bgr, overlay_bgr=None) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    raw_path = debug_dir / f"{frame_id}_raw.png"
    if not cv.imwrite(str(raw_path), image_bgr):
        raise OSError(f"failed to write debug frame: {raw_path}")
    if overlay_bgr is not None:
        overlay_path = debug_dir / f"{frame_id}_overlay.png"
        if not cv.imwrite(str(overlay_path), overlay_bgr):
            raise OSError(f"failed to write debug overlay: {overlay_path}")
```

### Anti-Patterns to Avoid

- **Backend-specific frame objects leaking downstream:** Later pipeline stages should receive a normalized array and metadata, not Picamera2 request objects or raw `VideoCapture` handles. [VERIFIED: user prompt; ASSUMED]
- **Assuming `cap.set()` succeeded:** OpenCV states that property read/write behavior depends on backend, OS, driver, and hardware, so the USB adapter must read back properties and capture a test frame. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html]
- **Writing debug files inside the frame acquisition hot path unconditionally:** Debug I/O can dominate latency on small computers, so make it configurable and preferably sample-based outside production loops. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSI camera driver and ISP controls | Custom libcamera bindings | Picamera2 | Picamera2 already exposes camera configuration, arrays, metadata, and controls. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] |
| USB camera capture loop primitives | Raw V4L2 ioctl frame buffering | OpenCV `VideoCapture` | OpenCV already opens camera indices, checks `isOpened()`, reads frames, and reports failures. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html] |
| USB exposure/WB control database | Hardcoded per-webcam magic values only | V4L2 control probing plus optional profile overrides | V4L2 exposes auto/manual exposure and white balance controls, but exact device support varies. [CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html; CITED: https://www.kernel.org/doc/html/v4.8/media/uapi/v4l/control.html; ASSUMED] |
| PNG/JPEG encoding | Custom image encoders | OpenCV `imwrite` | OpenCV writes images by extension and documents supported image formats. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html] |

**Key insight:** The hard part of Phase 2 is not reading a frame; it is making each backend prove that the returned frame is exactly 640x480, consistently colored, traceable by `frame_id`, and accompanied by honest metadata about which controls were actually locked. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; ASSUMED]

## Common Pitfalls

### Pitfall 1: Camera Property Writes Are Best-Effort

**What goes wrong:** USB code calls `cap.set(CAP_PROP_FRAME_WIDTH, 640)` or `cap.set(CAP_PROP_AUTO_WB, 0)` and assumes the camera accepted it. [CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html]

**Why it happens:** OpenCV property behavior passes through backend, OS, driver, and hardware layers. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html]

**How to avoid:** Read back width/height and capture one validation frame; store `settings_applied` and `settings_verified` in metadata. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; ASSUMED]

**Warning signs:** `cap.get()` returns 0, the first frame shape is not `(480, 640, 3)`, or exposure visibly changes across frames under fixed lighting. [ASSUMED]

### Pitfall 2: Color Order Drift Between Backends

**What goes wrong:** Pi frames and USB frames reach detection with different RGB/BGR channel order. [ASSUMED]

**Why it happens:** OpenCV uses BGR-style image conventions, while Picamera2 has specific stream format behavior that needs explicit normalization. [CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]

**How to avoid:** Make `image_bgr` the interface invariant and add a hardware smoke test with a known red/blue object. [ASSUMED]

**Warning signs:** A blue block appears red in saved raw debug frames or later classifier data collection. [ASSUMED]

### Pitfall 3: Locking Auto Controls Too Early

**What goes wrong:** Manual exposure/WB locks a bad startup value before the auto algorithms settle. [ASSUMED]

**Why it happens:** Pi camera controls and metadata are tied to active capture requests, and auto algorithms need frames to converge. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; CITED: https://www.raspberrypi.com/documentation/computers/camera_software.html]

**How to avoid:** Warm up for a configurable number of frames, capture metadata, then set explicit manual values. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; ASSUMED]

**Warning signs:** First saved frames are much darker or more color shifted than later frames. [ASSUMED]

### Pitfall 4: Debug Directory Grows Without Bound

**What goes wrong:** Field runs fill storage with raw and overlay images. [ASSUMED]

**Why it happens:** CAM-03 requires debug saves, but no retention policy is specified. [VERIFIED: .planning/REQUIREMENTS.md]

**How to avoid:** Plan `enabled`, `every_n_frames`, and `max_files` or `max_bytes` settings, with default debug output disabled for production loops. [ASSUMED]

**Warning signs:** Robot cycle slows down or Pi disk usage grows during long runs. [ASSUMED]

## Code Examples

Verified patterns from official sources:

### USB VideoCapture Source Skeleton

```python
# Source basis: OpenCV VideoCapture opens camera indexes, reads frames, and exposes width/height properties. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html]
import itertools
import time
import cv2 as cv


class UsbVideoCaptureFrameSource:
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._ids = itertools.count(1)
        self._cap = None

    def start(self) -> None:
        self._cap = cv.VideoCapture(self.camera_index, cv.CAP_V4L2)
        if not self._cap.isOpened():
            raise RuntimeError(f"USB camera {self.camera_index} did not open")
        self._cap.set(cv.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> CaptureFrame:
        ok, image_bgr = self._cap.read()
        if not ok or image_bgr is None or image_bgr.shape[:2] != (480, 640):
            raise RuntimeError("USB camera did not return a 640x480 frame")
        frame_id = f"frame_{next(self._ids):06d}"
        return CaptureFrame(frame_id, image_bgr, time.monotonic_ns(), "usb-opencv", {})

    def stop(self) -> None:
        if self._cap is not None:
            self._cap.release()
```

### V4L2 Control Probe Shape

```python
# Source basis: Linux V4L2 defines auto/manual exposure and white-balance controls; exact devices vary. [CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html; CITED: https://www.kernel.org/doc/html/v4.8/media/uapi/v4l/control.html; ASSUMED]
import subprocess


def list_v4l2_controls(device: str = "/dev/video0") -> str:
    return subprocess.check_output(
        ["v4l2-ctl", "--device", device, "--list-ctrls-menus"],
        text=True,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Use one OpenCV `VideoCapture(0)` path for every camera. [ASSUMED] | Use Picamera2 for Raspberry Pi CSI and OpenCV/V4L2 for USB, behind one project interface. [VERIFIED: .planning/research/STACK.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] | Current project research dated 2026-05-31 already selected this split. [VERIFIED: .planning/research/STACK.md] | The plan must test both adapters but keep downstream pipeline code backend-agnostic. [VERIFIED: user prompt; ASSUMED] |
| Let auto exposure and auto white balance run continuously. [ASSUMED] | Warm up, then lock manual values when hardware supports them. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf] | Required by CAM-02 in this roadmap. [VERIFIED: .planning/REQUIREMENTS.md] | Later geometry/classification phases see more reproducible frames under fixed lighting. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] |
| Save ad hoc screenshots with inconsistent names. [ASSUMED] | Central debug sink writes raw and optional overlay files named by monotonic frame id. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] | Required by CAM-03 in this roadmap. [VERIFIED: .planning/REQUIREMENTS.md] | Field failures become traceable to a specific capture. [ASSUMED] |

**Deprecated/outdated:**

- Legacy `picamera` should not be the Phase 2 standard because current project stack notes select Picamera2/libcamera for Pi Camera. [VERIFIED: .planning/research/STACK.md; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]
- A single full-frame detector path is out of scope for Phase 2 because this phase stops at capture and debug persistence. [VERIFIED: .planning/ROADMAP.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Target Raspberry Pi setup uses a recent Raspberry Pi OS image with Picamera2/libcamera available. | Standard Stack | Planner may need an OS/package bootstrap task before camera work. |
| A2 | `python3-picamera2`, `v4l-utils`, and `rpicam-apps` package names are available on the target image. | Standard Stack | Planner may need to replace package names after target apt verification. |
| A3 | Monotonic `frame_id` only needs to be monotonic within one process/run unless the user later requests persistence across restarts. | Architecture Patterns | Debug file names could collide across runs unless the writer includes a run id or timestamp. |
| A4 | Local automated tests should use fake/image-sequence sources because no target camera tools are installed on this dev host. | Environment Availability | Hardware issues could appear only during target Pi smoke tests. |
| A5 | Common USB camera control names will be discoverable through V4L2 on the target device. | Don't Hand-Roll | Some webcams may not expose manual exposure/WB; CAM-02 must then report unsupported controls honestly. |
| A6 | Debug retention should be configurable but is not yet specified by project requirements. | Common Pitfalls | Long field runs may produce too much data if retention is omitted. |

## Open Questions

1. **Which exact target hardware will run CAM-02?** [ASSUMED]
   - What we know: The project supports Pi Camera CSI and USB camera paths. [VERIFIED: .planning/ROADMAP.md]
   - What's unclear: Camera model, Raspberry Pi model, OS image, and USB camera V4L2 control support are not recorded. [VERIFIED: local project scan]
   - Recommendation: Planner should include a target-hardware smoke task that records `rpicam-hello --list-cameras` or `v4l2-ctl --list-ctrls-menus` output. [ASSUMED]

2. **What does "raw frame" mean for CAM-03?** [VERIFIED: .planning/REQUIREMENTS.md]
   - What we know: CAM-03 requires raw frames and optional overlays in a debug directory. [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: The requirement does not specify raw sensor Bayer data versus unmodified captured BGR frames. [VERIFIED: .planning/REQUIREMENTS.md]
   - Recommendation: Treat "raw frame" as the unmodified normalized 640x480 pipeline input image, not sensor RAW, unless the user changes the requirement. [ASSUMED]

3. **Should frame ids persist across process restarts?** [VERIFIED: .planning/REQUIREMENTS.md]
   - What we know: CAM-03 requires monotonic frame identifiers. [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: The requirement does not define process-local versus persistent monotonicity. [VERIFIED: .planning/REQUIREMENTS.md]
   - Recommendation: Use `run_id/frame_000001` directories for collision resistance and process-local monotonicity. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Unit tests and implementation | yes | 3.14.4 local | Target Pi Python version still must be probed. [VERIFIED: local `python3 --version`; ASSUMED] |
| pip | Dependency install | yes | 26.1 local | Use project venv. [VERIFIED: local `python3 -m pip --version`] |
| Node/npm | GSD tooling | yes | Node 24.14.0, npm 11.9.0 local | None needed. [VERIFIED: local `node -v && npm -v`] |
| OpenCV (`cv2`) | USB source and debug saves | no | none local | Install Wave 0 dev dependency or mock writer in unit tests. [VERIFIED: local import probe] |
| NumPy | Frame arrays | no | none local | Install Wave 0 dev dependency. [VERIFIED: local import probe] |
| pytest | Validation architecture | no | none local | Install Wave 0 dev dependency. [VERIFIED: local import probe] |
| Picamera2 | CSI source | no | none local | Target Pi only; use fake/image-sequence source locally. [VERIFIED: local import probe; ASSUMED] |
| `rpicam-hello` / `libcamera-hello` | Pi camera hardware smoke | no | none local | Run on target Pi. [VERIFIED: local command probes; ASSUMED] |
| `v4l2-ctl` | USB camera control probe | no | none local | Run on target Linux/Pi; local macOS cannot validate V4L2. [VERIFIED: local command probe; ASSUMED] |

**Missing dependencies with no fallback:**

- None for research writing. [VERIFIED: file created in repo]
- Real CAM-02 hardware verification is blocked until running on target Pi or Linux USB camera host. [VERIFIED: local command probes; ASSUMED]

**Missing dependencies with fallback:**

- OpenCV, NumPy, and pytest are missing locally; install in Wave 0 for automated tests. [VERIFIED: local import probe; VERIFIED: PyPI JSON 2026-05-31]
- Picamera2 and V4L2 tooling are missing locally; use fake/image-sequence tests locally and target-hardware smoke tests on Pi. [VERIFIED: local command probes; ASSUMED]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 current on PyPI. [VERIFIED: PyPI JSON 2026-05-31] |
| Config file | none. [VERIFIED: local file scan] |
| Quick run command | `python -m pytest tests/test_camera_source.py tests/test_debug_writer.py -q` after Wave 0 creates tests. [ASSUMED] |
| Full suite command | `python -m pytest -q` after Wave 0 creates test infrastructure. [ASSUMED] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CAM-01 | `FrameSource` fake/image-sequence source returns `CaptureFrame` with `(480, 640, 3)` image shape and monotonically increasing `frame_id`. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] | unit | `python -m pytest tests/test_camera_source.py::test_fake_source_returns_640x480_bgr -q` [ASSUMED] | no, Wave 0. [VERIFIED: local file scan] |
| CAM-01 | USB and Pi adapters fail clearly when backend cannot open or returns wrong shape. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html] | unit with mocks plus hardware smoke | `python -m pytest tests/test_camera_source.py::test_backend_open_failure_is_explicit -q` [ASSUMED] | no, Wave 0. [VERIFIED: local file scan] |
| CAM-02 | Settings application records which exposure/WB controls were requested, applied, verified, or unsupported. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] | unit with mocks plus hardware smoke | `python -m pytest tests/test_camera_source.py::test_manual_control_metadata_records_support -q` [ASSUMED] | no, Wave 0. [VERIFIED: local file scan] |
| CAM-03 | Debug writer saves raw and overlay files using the same monotonic frame id. [VERIFIED: .planning/REQUIREMENTS.md] | unit | `python -m pytest tests/test_debug_writer.py::test_debug_writer_uses_monotonic_frame_ids -q` [ASSUMED] | no, Wave 0. [VERIFIED: local file scan] |

### Sampling Rate

- **Per task commit:** run camera/debug unit tests after dependencies are installed. [ASSUMED]
- **Per wave merge:** run `python -m pytest -q` after Wave 0 test scaffolding exists. [ASSUMED]
- **Phase gate:** run full tests plus one target-hardware capture smoke for CSI or USB before `/gsd-verify-work`. [ASSUMED]

### Wave 0 Gaps

- [ ] `pyproject.toml` or `requirements-dev.txt` for pytest/OpenCV/NumPy test dependencies. [VERIFIED: local file scan]
- [ ] `tests/test_camera_source.py` covering CAM-01 and CAM-02 adapter behavior with fakes/mocks. [VERIFIED: local file scan]
- [ ] `tests/test_debug_writer.py` covering CAM-03 filenames and write failures. [VERIFIED: local file scan]
- [ ] `config/camera.example.json` documenting CSI/USB settings fields and debug options. [ASSUMED]
- [ ] Hardware smoke script or documented command for target Pi/USB validation. [ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No network or user authentication surface is planned in Phase 2. [VERIFIED: .planning/ROADMAP.md; CITED: https://github.com/OWASP/ASVS] |
| V3 Session Management | no | No session state is planned in Phase 2. [VERIFIED: .planning/ROADMAP.md; CITED: https://github.com/OWASP/ASVS] |
| V4 Access Control | limited | Restrict debug directory writes to configured local paths; do not accept arbitrary unvalidated paths from external users. [ASSUMED; CITED: https://github.com/OWASP/ASVS] |
| V5 Input Validation | yes | Validate camera indexes, device paths, frame dimensions, debug directory, and image shape before use. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED; CITED: https://github.com/OWASP/ASVS] |
| V6 Cryptography | no | Phase 2 does not add cryptographic operations. [VERIFIED: .planning/ROADMAP.md; CITED: https://github.com/OWASP/ASVS] |

### Known Threat Patterns for Camera Capture

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal or accidental overwrite through debug directory configuration. [ASSUMED] | Tampering | Resolve debug path under a configured project/output root and reject paths outside it. [ASSUMED] |
| Disk exhaustion from unlimited debug image saving. [ASSUMED] | Denial of Service | Add sampling and retention limits. [ASSUMED] |
| Sensitive scene data stored in debug frames. [ASSUMED] | Information Disclosure | Keep debug directory gitignored and document retention/deletion expectations. [ASSUMED] |
| OS command injection if `v4l2-ctl` receives shell-formatted strings. [ASSUMED] | Tampering | Use `subprocess.run([...], shell=False)` with validated device paths and numeric settings. [ASSUMED; CITED: https://github.com/OWASP/ASVS] |

## Sources

### Primary (HIGH Confidence)

- `.planning/ROADMAP.md` - Phase 2 goal, dependencies, success criteria, and phase boundaries. [VERIFIED: local read]
- `.planning/REQUIREMENTS.md` - CAM-01, CAM-02, CAM-03 requirement definitions. [VERIFIED: local read]
- `detection_contract.py` - Existing contract boundary and debug `frame_id` field. [VERIFIED: local read]
- `CLAUDE.md` - Project constraints and GSD workflow directives. [VERIFIED: local read]
- Picamera2 manual PDF - stream configuration, `RGB888`, `capture_array`, metadata, and controls. [CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf]
- OpenCV `VideoCapture` docs - camera opening, `read()`, `isOpened()`, `get()`, `set()`, and backend caveats. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html]
- OpenCV video I/O flags docs - frame width/height, exposure, auto white balance, and backend identifiers. [CITED: https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html]
- OpenCV imgcodecs docs - `imwrite` behavior. [CITED: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html]
- Linux kernel V4L2 camera/user controls - exposure and white balance controls. [CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html; CITED: https://www.kernel.org/doc/html/v4.8/media/uapi/v4l/control.html]

### Secondary (MEDIUM Confidence)

- PyPI JSON and `pip index versions` - current package versions and upload dates for OpenCV, NumPy, Picamera2, pytest, and Pillow. [VERIFIED: PyPI JSON 2026-05-31; VERIFIED: local command]
- Raspberry Pi camera software docs - rpicam command behavior and exposure/WB examples. [CITED: https://www.raspberrypi.com/documentation/computers/camera_software.html]
- OWASP ASVS repository - security category reference. [CITED: https://github.com/OWASP/ASVS]

### Tertiary (LOW Confidence)

- Assumptions in this document about target OS package names, exact camera hardware, debug retention defaults, and frame-id persistence scope require planner or user confirmation. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH for Python package versions and documented APIs; MEDIUM for target Pi apt package names because the target Pi was not probed. [VERIFIED: PyPI JSON 2026-05-31; CITED: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf; ASSUMED]
- Architecture: HIGH for the required backend abstraction and debug saving requirement; MEDIUM for exact module names because no package structure exists yet. [VERIFIED: user prompt; VERIFIED: .planning/REQUIREMENTS.md; ASSUMED]
- Pitfalls: HIGH for OpenCV property caveats and V4L2 control variability; MEDIUM for debug I/O and retention risks because they are operational assumptions. [CITED: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html; CITED: https://www.kernel.org/doc/html/v5.7/media/uapi/v4l/ext-ctrls-camera.html; ASSUMED]

**Research date:** 2026-05-31 [VERIFIED: local date context]
**Valid until:** 2026-06-30 for package versions and camera API guidance; re-check PyPI and target Pi package versions before implementation. [ASSUMED]
