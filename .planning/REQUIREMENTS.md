# Requirements

## REQ-01 — Webcam detection
Realtime YOLO inference from webcam with bounding boxes and interactive controls.

## REQ-02 — Package structure
Installable Python package under `src/block_detected/` with documented module boundaries.

## REQ-03 — CV expansion layout
Folder structure supports future: tracking, calibration, GUI config panel, without renaming the root package.

## REQ-04 — Runtime engine and typed config
WebcamEngine frame loop (read → infer → render → metrics), typed AppConfig with TOML load/save/validate, DetectorBackend protocol with YOLO loader, and hot-reload vs restart key classification for GUI consumption.
