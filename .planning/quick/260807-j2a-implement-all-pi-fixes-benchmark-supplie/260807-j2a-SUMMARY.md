---
status: complete
quick_task: 260807-j2a-implement-all-pi-fixes-benchmark-supplie
completed: 2026-08-07
commits:
  - be0754784009f7585d6be7284e81c1d9dad82f1f
  - dede95a5c8d65be427704aa0091c87c0c1ce5fc3
---

# Pi hardening, model selection, and deployment summary

## Delivered

- Added explicit `onnx` dependency to Pi install profiles.
- Fixed root `block_dataset/` discovery and OpenCV 5 `HoughLinesP` shape handling with regressions.
- Preserved supplied LFS changes: deleted `pose11.onnx`, added `pose11-fp16.onnx` and `pose11-int8.onnx` byte-identically.
- Selected Pi-only config: `pose11-fp16.onnx`, `imgsz=320`, `max_det=8`.
- Shipped missing default `src/block_detected/block_detected.json` and made camera-label tests OS-independent.

## Model evidence

- `pose11-fp16.onnx`: valid dynamic pose ONNX. Dataset at 320 retained 108/108 detection images and 186 detections, equal to its 640 result.
- `pose11-int8.onnx`: rejected by ONNX checker because graph is not topologically sorted.
- `rbs-final_int8.onnx`: rejected for production because it produced 0 detections across 108 images.
- Local full matrix: `/tmp/block-detected-model-benchmark.json`.
- Pi full matrix: `/tmp/block-detected-model-benchmark.json` on `/home/son/block_detected`.

## Verification

- Local project suite: 209 passed.
- Local classical quality: 94/108 accepted (87.04%).
- Pi focused suite: 14 passed.
- Pi full project suite on final deployed SHA: 209 passed in 335.52 seconds.
- Pi classical quality on final SHA: 94/108 accepted (87.04%) in 165.92 seconds.
- Pi final SHA equals pushed `origin/main`: `dede95a5c8d65be427704aa0091c87c0c1ce5fc3`.

## Final Pi USB benchmark

- Model/config: `pose11-fp16.onnx`, 320, `max_det=8`.
- 300/300 processed frames; zero camera or inference errors.
- 14.05 end-to-end FPS; mean 71.13 ms; p50 67.54 ms; p95 76.09 ms.
- 170 frames with detections; 306 total detections.
- Peak RSS 449.66 MB.
- Temperature 42.2°C to 57.1°C; `throttled=0x0` before and after.
- Earlier cold/camera-scene run reached 25.07 FPS; final uncontended acceptance result above is retained as conservative production evidence.

## Notes

Full repository-wide collection outside `tests/` still requires optional `control-drivehub` dependencies. Pi production profile intentionally excludes them. Main project suite and deployed Pi runtime are green.
