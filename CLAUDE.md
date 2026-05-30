<!-- GSD:project-start source:PROJECT.md -->
## Project

**Block Detected — Non-ArUco Cube Block Detection**

A Raspberry Pi / edge vision pipeline that detects one of four colored cube blocks on a work table from a fixed camera (640×480), without ArUco markers. It returns precise square-face geometry (four ordered corners, center, rotation) plus block identity and optional robot pickup pose for a pick-and-place arm.

**Core Value:** For every valid frame, the system must reliably output **which block (1–4)** with **correctly ordered four corners and angle** so the robot can pick — not just a bounding box.

### Constraints

- **Tech**: Python 3, OpenCV, TensorFlow Lite (INT8), Pi-compatible — no ArUco dependency
- **Resolution**: 640×480 locked where possible
- **Latency**: Suitable for robot pick cycle (classify on 128×128 warp, not full-frame heavy models)
- **Accuracy**: Must beat template matching under lighting/view change; CNN is default
- **Output**: Must conform to existing `DetectionResult` contract in `detection_contract.py`
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11.x | Runtime on Pi and dev machines | Raspberry Pi OS Bookworm ships 3.11.2; PEP 668 requires venv for pip installs. Matches `tflite-runtime` and `ai-edge-litert` cp311 aarch64 wheels (verified PyPI 2026-05-31). |
| OpenCV (`opencv-python`) | 4.11.0.86 – 4.12.x (pin one) | Contour detection, morphology, perspective warp, homography | Standard stack for square-face geometry pipelines. Pi Forum confirms 4.11.0.86 + numpy 2.x on Pi 5 Bookworm. Avoid apt/pip OpenCV mixing. |
| NumPy | ≥1.26.4, <2.3 (pin in lockfile) | Array ops, corner ordering, warp buffers | Required by OpenCV Python bindings and TFLite I/O. Pin with OpenCV — numpy 2.x works with opencv-python ≥4.10; apt `python3-opencv` 4.6.0 needs numpy 1.24.x. |
| TFLite runtime (`tflite-runtime`) | 2.14.0 | On-device INT8 CNN inference on Pi | Official lightweight inference package (~15 MB vs 600 MB+ full TF). cp311 `manylinux_2_34_aarch64` wheel exists on PyPI. `num_threads=4` on Pi 4/5. |
| TensorFlow (dev only) | 2.15 – 2.17 on x86_64 | Train tiny 4-class CNN, export INT8 `.tflite` | Full TF/Keras belongs on a dev laptop/CI machine, not the Pi. Use `TFLiteConverter` + representative dataset for INT8. |
| pytest | ≥8.0 (latest 9.x OK) | Contract tests, geometry unit tests, offline frame regression | Standard Python test runner; no special vision framework required for v1. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| picamera2 | ≥0.3.36 (apt preferred) | Pi Camera Module capture via libcamera | **Required** when using Raspberry Pi Camera on Pi 4/5. OpenCV `VideoCapture` does not drive libcamera on Pi 5. |
| Pillow | ≥10.0 | Save debug JPEG/PNG frames | Optional but useful for field tuning and eval harness artifact export. |
| scipy | ≥1.11 | Euclidean distance in robust corner ordering | Optional — pure-numpy `order_points` is sufficient; add only if using imutils-style robust ordering. |
| pytest-cov | ≥5.0 | Coverage reporting | CI / quality gate on contract and geometry modules. |
| pytest-image-snapshot | ≥0.4.5 | Visual regression on warp/threshold outputs | Optional Phase 4+ when golden frames exist; not needed for contract-only tests. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `python3 -m venv` | Isolated Pi/dev environments | **Mandatory** on Bookworm (PEP 668). Use `python3 -m venv .venv && source .venv/bin/activate`. |
| `requirements.txt` + lock pins | Reproducible Pi deploy | Pin opencv-python, numpy, tflite-runtime together; document Pi OS version. |
| `libcamera-hello` / `libcamera-still` | Camera hardware smoke test | Run before debugging Python pipeline. |
| `v4l2-ctl` | USB camera exposure/format control | When using USB webcam instead of Pi Camera. |
| Git LFS (optional) | Store labeled eval images | Keep test fixtures out of main blob history if large. |
## Installation
### Raspberry Pi (inference runtime)
# System deps (Bookworm 64-bit)
# Pi Camera path — install picamera2 from apt (pulls libcamera stack)
# Project venv
# Core inference stack (pin exact versions in requirements.txt)
# Verify
### Dev machine (train + export INT8 model)
# After training — export (representative images must match warp preprocessing)
# See Training Export Pattern below
### Training Export Pattern (INT8 full-integer)
### Pi inference pattern
# Quantize warp to input scale/zero_point before set_tensor(...)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `tflite-runtime==2.14.0` | `ai-edge-litert>=2.1.5` | Google’s successor runtime; cp311/linux_aarch64 wheels on PyPI (2.1.5 verified). Use when migrating to Python 3.12+ or when `tflite-runtime` wheels disappear. API: `import ai_edge_litert.interpreter as tflite`. |
| picamera2 + numpy arrays | OpenCV `VideoCapture(0)` | USB UVC webcam on any Pi; simpler, works with standard V4L2. **Do not use VideoCapture for Pi Camera Module on Pi 5.** |
| pip `opencv-python` in venv | apt `python3-opencv` 4.6.0 | Offline/minimal-SD installs. Create venv with `--system-site-packages` and pin `numpy` to apt version (1.24.x). Trade-off: older OpenCV, fewer bugs from mixed installs. |
| Contour + warp + tiny CNN | ONNX Runtime on Pi | Faster ecosystem momentum in 2026 blogs, but **project constraint is TFLite INT8**. Only switch if requirements change. |
| Inline `order_points` (numpy) | `imutils` | imutils adds dependency for one function; PyImageSearch algorithm is 15 lines — copy into repo. |
| Train on x86 with TF/Keras | Train on Pi | Pi training is slow and pulls huge deps. Always train/export off-device, deploy `.tflite` only. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **ArUco / AprilTag / `opencv-contrib` aruco module** | Explicit project constraint; requires fiducials on blocks | Contour → `approxPolyDP` → corner order → warp |
| **YOLO / Ultralytics as primary detector** | Axis-aligned bbox only; no guaranteed TL/TR/BR/BL order or rotation for grasp | Contour quadrilateral + warp; CNN classifies warped face only |
| **Cloud vision APIs** (Google Vision, Rekognition, Roboflow hosted inference) | Latency, offline requirement, cost, privacy | On-device `tflite-runtime` |
| **Full `tensorflow` on Pi** | 600 MB+, slow install, no training on edge needed | `tflite-runtime` inference only |
| **Legacy `picamera` library** | Deprecated; incompatible with libcamera stack | `picamera2` |
| **`cv2.VideoCapture` for Pi Camera on Pi 5** | libcamera not exposed through OpenCV V4L backend on Pi 5 (open issue since 2022) | picamera2 `capture_array()` → OpenCV processing |
| **Mixed apt + pip OpenCV** | Import/version conflicts, numpy ABI breaks | One source: either all pip in venv or apt + `--system-site-packages` with pinned numpy |
| **Template matching (Mode A) as v1 default** | Lighting/view fragile vs CNN | TFLite INT8 CNN on 128×128 warp |
| **Float32 TFLite on Pi** | 3–4× slower than INT8 on ARM NEON; larger model | Post-training full-integer quantization |
| **End-to-end giant classifier on full 640×480 frame** | Wastes compute; harder to debug geometry failures | Detect square cheaply, classify small warp |
| **Hardcoded `pip install --break-system-packages` on Pi** | Breaks PEP 668 guarantees, corrupts OS Python | Always use venv |
## Stack Patterns by Variant
- Install `python3-picamera2` via apt.
- Configure `create_video_configuration(main={"size": (640, 480), "format": "RGB888"})` or `XRGB8888` with BGRA→BGR conversion.
- Loop: `frame = picam2.capture_array()` → OpenCV pipeline.
- Lock exposure/WB via `libcamera` controls (`AeEnable`, `AwbEnable`, manual exposure when tuned).
- Include `cv2.waitKey(1)` if displaying preview (OpenCV quirk on Pi).
- Skip picamera2 entirely.
- `cap = cv2.VideoCapture(0)` + `cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)` + `cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)`.
- Use `v4l2-ctl` to fix exposure/white balance when autoconfig drifts.
- Run pipeline on recorded 640×480 frames or USB webcam.
- Same OpenCV + TFLite code paths; swap camera backend via a thin `FrameSource` protocol.
- Train/export on x86; copy `.tflite` to Pi.
- Switch inference import to `ai-edge-litert>=2.1.5` (cp312 aarch64 wheels verified on PyPI).
- Keep export toolchain on TF 2.15+; `.tflite` format unchanged.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.11 (Bookworm) | `tflite-runtime==2.14.0` | cp311 manylinux aarch64 wheel confirmed PyPI 2026-05-31. **HIGH confidence.** |
| Python 3.11 (Bookworm) | `ai-edge-litert==2.1.5` | cp311 manylinux aarch64 wheel confirmed. **HIGH confidence.** |
| `opencv-python==4.11.0.86` | `numpy>=2.0,<2.3` | Pi 5 Bookworm forum-verified combo. **MEDIUM confidence** — pin and test on target hardware. |
| apt `python3-opencv` 4.6.0 | `python3-numpy` 1.24.x (Debian bookworm) | Do not pip-upgrade numpy in `--system-site-packages` venv without upgrading OpenCV. **HIGH confidence.** |
| `tflite-runtime` / TFLite export | Same preprocess + input dtype | Representative dataset must match warp normalization or INT8 accuracy collapses. **HIGH confidence** (Google docs). |
| picamera2 0.3.x | Raspberry Pi OS Bookworm/64-bit | Pi 5 requires libcamera stack; legacy `start_x=1` does not apply. **HIGH confidence.** |
| Full TensorFlow 2.15+ (x86) | Exported `.tflite` → `tflite-runtime 2.14` | Ops must be TFLITE_BUILTINS_INT8 compatible; keep model tiny (MobileNetV2-scale or custom 3–5 conv blocks). **MEDIUM confidence** — validate with `interpreter.get_tensor_details()`. |
### Recommended `requirements.txt` (Pi inference)
# block_detected — Pi inference (Python 3.11, aarch64, Bookworm)
# picamera2: install via apt (python3-picamera2), not pip, when using Pi Camera
### Recommended `requirements-train.txt` (dev machine)
## Architecture-Relevant Stack Boundaries
| Layer | Stack | Runs On |
|-------|-------|---------|
| Contract / types | stdlib `dataclasses`, `enum` | Pi + dev |
| Capture | picamera2 **or** OpenCV VideoCapture | Pi |
| Geometry | OpenCV imgproc + numpy | Pi |
| Classify | TFLite INT8 | Pi |
| Train / quantize | TensorFlow Keras | Dev machine only |
| Test | pytest + numpy.testing | Dev + CI (Pi optional HW tests) |
## Sources
| Source | What Verified | Confidence |
|--------|---------------|------------|
| [TensorFlow Lite Python guide](https://www.tensorflow.org/lite/guide/python) | `tflite-runtime` install, aarch64 wheel support, `Interpreter` API | HIGH |
| [Post-training quantization](https://www.tensorflow.org/lite/performance/post_training_quantization) | Full INT8 export, representative dataset, input/output types | HIGH |
| [PyPI tflite-runtime 2.14.0](https://pypi.org/project/tflite-runtime/2.14.0/) | cp311 linux_aarch64 wheel availability | HIGH |
| [PyPI ai-edge-litert 2.1.5](https://pypi.org/project/ai-edge-litert/2.1.5/) | Successor runtime, cp311 aarch64 wheels | HIGH |
| [Raspberry Pi OS docs — Python/venv](https://www.raspberrypi.com/documentation/computers/os.html) | PEP 668, venv requirement on Bookworm+ | HIGH |
| [picamera2 PyPI 0.3.36](https://pypi.org/project/picamera2/) | libcamera Python API, OpenCV integration examples | HIGH |
| [OpenCV findContours docs](https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html) | Contour-based shape detection pattern | HIGH |
| [PyImageSearch order_points](https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/) | TL/TR/BR/BL ordering algorithm | HIGH |
| Raspberry Pi Forums (Pi 5 + OpenCV VideoCapture, picamera2+waitKey) | VideoCapture empty on Pi Camera; picamera2 integration quirks | MEDIUM |
| Pi Forum: opencv-python 4.11 + numpy 2.2 on Pi 5 Bookworm | Version pin guidance | MEDIUM |
| GitHub tensorflow#62003, google-ai-edge/LiteRT#5 | `tflite-runtime` → `ai-edge-litert` migration | MEDIUM |
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
