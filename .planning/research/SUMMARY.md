# Research Summary

**Project:** Block Detected — non-ArUco cube detection for robot pick
**Synthesized:** 2026-05-31

## Executive Summary

Build a **modular OpenCV geometry pipeline** on Raspberry Pi with a **TFLite INT8 4-class CNN** on perspective-warped square faces. Existing `detection_contract.py` is the integration boundary — do not duplicate types. v1 prioritizes ordered corners + angle over bbox detectors.

## Stack (decisions)

- **Python 3.11+, OpenCV 4.8+, NumPy, tflite-runtime on Pi**
- **picamera2** for CSI; **VideoCapture** for USB
- **Train on PC (TensorFlow)** → deploy **INT8 `.tflite`**
- **Avoid:** ArUco, YOLO-primary, full TF on Pi, template matching as default

## Table Stakes

Capture 640×480 → preprocess → square contours → order corners → warp 128×128 → classify → pose (if calibrated) → reject → `DetectionResult`.

## Architecture

Package under `src/block_detected/` with stages: `camera`, `preprocess`, `detector`, `geometry`, `classifier`, `pose`, `reject`, `pipeline.detect_block`.

Build order: contract → camera → geometry without ML → dataset + CNN → pose → reject + eval.

## Top Risks

1. Corner order bugs (warp/classification)
2. Lighting/threshold fragility
3. CNN confusion between similar blocks
4. Calibration drift
5. Multi-contour ambiguity

## Recommended Roadmap Shape

~8 phases aligned to requirement groups: Contract/API → Camera → Preprocess/Contours → Warp/Geometry → CNN → Pose → Reject/Integration → Test/Eval.

---
*Summary for: block_detected*
*Synthesized: 2026-05-31*
