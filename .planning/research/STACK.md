# Stack Research

**Domain:** Raspberry Pi vision — OpenCV geometry + on-device TFLite classification
**Researched:** 2026-05-31
**Confidence:** HIGH (core stack), MEDIUM (exact Pi OS package pins)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime | Pi OS standard; dataclass contract already in repo |
| OpenCV | 4.8+ (`opencv-python-headless` on Pi) | Capture, preprocess, contours, warp | Industry default for contour→homography pipelines |
| NumPy | 1.26+ | Array ops | OpenCV native dependency |
| TensorFlow Lite | 2.14+ (`tflite-runtime` on Pi) | INT8 4-class CNN inference | Official on-device path; fits 128×128 tiny models |
| picamera2 | latest (Pi Camera) | Stable 640×480 capture | libcamera stack; exposure/WB controls |
| OpenCV VideoCapture | 4.x | USB camera fallback | Same pipeline code path |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| TensorFlow (dev machine) | 2.15+ | Train + export TFLite | Not on Pi — train on PC, deploy `.tflite` |
| Pillow | 10+ | Debug frame save | Optional if not using `cv2.imwrite` |
| pytest | 8+ | Contract + geometry unit tests | CI and laptop dev |
| scipy / sklearn | optional | Eval metrics | Offline test harness only |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `requirements.txt` + optional `requirements-pi.txt` | Repro installs | Split heavy TF (train) vs `tflite-runtime` (deploy) |
| `ruff` or `black` | Lint/format | Match team preference |
| `scripts/capture_dataset.py` | Labeled warp crops | Feeds CNN training |

## Installation

```bash
# Dev / train (laptop)
python -m venv .venv && source .venv/bin/activate
pip install opencv-python numpy tensorflow pytest

# Pi deploy
pip install opencv-python-headless numpy tflite-runtime picamera2 pytest
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| TFLite INT8 CNN | ONNX Runtime + quantized model | If team already standardized on ONNX export |
| picamera2 | legacy `picamera` | Never on Bookworm — libcamera only |
| Contour pipeline | ArUco | **Rejected** — user constraint |
| Tiny CNN | `cv2.matchTemplate` Mode A | Quick prototype only; not production default |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `opencv-contrib` ArUco module | Out of scope | Contour + warp |
| YOLOv8 bbox-only as primary | No ordered corners | Contour quad + warp |
| Full TensorFlow on Pi | Slow, large | `tflite-runtime` |
| Cloud vision APIs | Latency, offline requirement | Local CNN |
| `opencv-python` GUI on headless Pi | Pulls GUI deps | `opencv-python-headless` |

## Stack Patterns by Variant

**If Pi Camera:**
- Use `picamera2` with fixed `main` size 640×480, disable auto exposure after warmup
- Because USB and CSI need different backends

**If USB camera only:**
- `cv2.VideoCapture(0)` + `CAP_PROP_FRAME_WIDTH/HEIGHT`
- Lock WB/exposure via V4L2 if supported

**If training data scarce:**
- Start MobileNetV2-0.35 width or custom 3–4 layer CNN on 128×128
- Because full ImageNet models are overkill

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `tflite-runtime` 2.14 | TFLite export from TF 2.14–2.16 | Re-export if op mismatch |
| OpenCV 4.8+ | NumPy 1.26+ | Standard wheel pairing on aarch64 |

## Sources

- OpenCV contours / `approxPolyDP` — https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html
- TensorFlow Lite converter — https://www.tensorflow.org/lite/models/image_classification/overview
- picamera2 manual — Raspberry Pi documentation

---
*Stack research for: non-ArUco cube block detection on Raspberry Pi*
*Researched: 2026-05-31*
