# Requirements: Detect Only v4

**Defined:** 2026-07-03  
**Milestone:** v2.0  
**Core Value:** Từ camera Pi 5, tự động phát hiện model/camera phù hợp, chạy inference realtime với overlay và JSON chuẩn hóa

## v2.0 Requirements

### Core API & Types

- [ ] **CORE-01**: Module `src/detect_only_v4/` greenfield — không import từ `hex_detector`, `block_detected*`, hay legacy khác
- [ ] **CORE-02**: `DetectionResult` dataclass với fields: `class_id`, `class_name`, `confidence`, `xyxy`, `center_x`, `center_y`, `width`, `height`, `track_id=None`, `mask`, `keypoints`, `obb_points`, `angle`
- [ ] **CORE-03**: Public API exports: `load_model`, `inspect_model`, `discover_cameras`, `probe_camera`, `detect_frame`, `normalize_results`, `draw_overlay`
- [ ] **CORE-04**: `inspect_model(path)` trả family (YOLOv8/YOLO11/YOLO26/unknown), task (detect/segment/pose/obb/unknown), format, class names — ưu tiên `model.task` và metadata
- [ ] **CORE-05**: Task/family identification fallback: tên file → dry inference; trả `unknown` khi không đủ dữ liệu, không đoán
- [ ] **CORE-06**: Structured logging (stdlib) với per-stage timings và error taxonomy (skip vs fatal)

### Model Discovery & Loading

- [ ] **MODEL-01**: Tự quét `models/` — hỗ trợ `.pt`, `.onnx`, `.engine`, `.tflite`, thư mục NCNN (`*_ncnn_model/`)
- [ ] **MODEL-02**: `load_model(path)` lazy-load qua Ultralytics `YOLO(path)` với format backend phù hợp
- [ ] **MODEL-03**: Pi 5 backend priority: NCNN dir → OpenVINO dir → ONNX → TFLite → PT
- [ ] **MODEL-04**: `.engine` discover-only trên Pi — trả lỗi rõ ràng (requires CUDA), không crash
- [ ] **MODEL-05**: Model discovery cache với mtime invalidation; không scan mỗi HTTP request

### Task Adapters

- [ ] **ADPT-01**: Adapter layout: `detectors/detect/`, `detectors/segment/`, `detectors/pose/`, `detectors/obb/`
- [ ] **ADPT-02**: `normalize_results(results, task)` pure — map Ultralytics `Results` → `list[DetectionResult]`, JSON-serializable
- [ ] **ADPT-03**: Detect adapter: boxes xyxy, cls, conf, class names
- [ ] **ADPT-04**: Segment adapter: boxes + mask polygon/RLE JSON-safe
- [ ] **ADPT-05**: Pose adapter: boxes + keypoints `[{x,y,conf}, ...]`
- [ ] **ADPT-06**: OBB adapter: obb corners hoặc center/w/h/angle
- [ ] **ADPT-07**: Không tracking — luôn trả tất cả detections, `track_id` luôn None
- [ ] **ADPT-08**: `draw_overlay(frame, detections, config)` task-aware — mask/keypoints/angle theo task; copy-on-draw

### Camera

- [ ] **CAM-01**: `discover_cameras()` liệt kê V4L2 `/dev/video*`, Picamera2 (nếu Pi + importable)
- [ ] **CAM-02**: `probe_camera(camera_id)` trả actual width, height, fps, backend — không ép 640×480
- [ ] **CAM-03**: Camera backend auto-detect: Picamera2 (CSI Pi) → V4L2 (USB) → OpenCV fallback
- [ ] **CAM-04**: Cho phép đổi resolution runtime; fallback an toàn khi camera từ chối
- [ ] **CAM-05**: V4L2: `CAP_PROP_BUFFERSIZE=1`, prefer MJPEG; Picamera2: RGB→BGR conversion documented
- [ ] **CAM-06**: Warmup frames (5–10) sau camera start; log actual configuration

### Pipeline (Pi 5 Optimization)

- [ ] **PIPE-01**: Capture thread riêng — không block camera khi inference chậm
- [ ] **PIPE-02**: Inference thread riêng — một model instance per worker
- [ ] **PIPE-03**: Bounded queue `maxsize=1` (hoặc 2 max) với drop-old-frame policy
- [ ] **PIPE-04**: `LatestResult` snapshot với threading lock cho API consumers
- [ ] **PIPE-05**: Inference error → log + skip frame; không kill camera loop
- [ ] **PIPE-06**: Metrics: capture_fps, infer_fps, dropped_frames, infer_ms

### Web UI (FastAPI + WebSocket)

- [ ] **WEB-01**: FastAPI app với lifespan start/stop pipeline
- [ ] **WEB-02**: REST: `GET /health`, `GET /models`, `GET /cameras`, config endpoints
- [ ] **WEB-03**: WebSocket live stream: JPEG overlay + JSON detections realtime (~15–30 Hz cap)
- [ ] **WEB-04**: UI hiển thị family, task, format, resolution, FPS, latency
- [ ] **WEB-05**: Runtime config: model, camera, resolution, confidence, IoU, imgsz, class filter
- [ ] **WEB-06**: Model/camera switch: drain pipeline, reload, brief warming_up status
- [ ] **WEB-07**: Single uvicorn worker documented; CORS open for LAN dev
- [ ] **WEB-08**: Static HTML/JS client — mask/keypoints/angle render theo task

### Quality & Documentation

- [ ] **QA-01**: Type hints trên toàn bộ public API
- [ ] **QA-02**: Unit tests: adapters (golden fixtures), discovery, queue drop policy, inspect_model mocks
- [ ] **QA-03**: `tests/detect_only_v4/` — không yêu cầu camera/model thật trong CI
- [ ] **QA-04**: README: Pi 5 install (apt picamera2/opencv, venv --system-site-packages), NCNN export, chạy Web UI
- [ ] **QA-05**: `pyproject.toml` optional extra `[detect-only-v4]` và entry point `python -m detect_only_v4`

## Future Requirements (v2.x+)

### Integration

- **INTG-01**: Tích hợp hex_detector downstream (bbox → geometry) — milestone riêng
- **INTG-02**: Robot telemetry MQTT/ROS bridge

### Features

- **FEAT-01**: Model folder watch (inotify) for hot-add models
- **FEAT-02**: WebRTC low-latency stream thay JPEG WebSocket
- **FEAT-03**: Snapshot/clip recording endpoint

## Out of Scope

| Feature | Reason |
|---------|--------|
| YOLO training / fine-tune | Model đã có; document export only |
| Object tracking (ByteTrack, etc.) | Yêu cầu rõ: no tracking |
| Đọc/sửa code ngoài `detect_only_v4/` | Greenfield module |
| hex_detector merge | Separate milestone |
| CUDA / TensorRT on Pi | No NVIDIA GPU on Pi 5 |
| Multi-worker Uvicorn | Camera singleton conflict |
| Auth / multi-tenant | LAN lab tool |
| Classify / semantic seg tasks | Scope: detect/segment/pose/obb only |
| GPIO / robotic actuation | JSON output for downstream only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 3 | Pending |
| CORE-02 | Phase 3 | Pending |
| CORE-03 | Phase 3 | Pending |
| CORE-04 | Phase 3 | Pending |
| CORE-05 | Phase 3 | Pending |
| CORE-06 | Phase 3 | Pending |
| MODEL-01 | Phase 4 | Pending |
| MODEL-02 | Phase 4 | Pending |
| MODEL-03 | Phase 4 | Pending |
| MODEL-04 | Phase 4 | Pending |
| MODEL-05 | Phase 4 | Pending |
| ADPT-01 | Phase 5 | Pending |
| ADPT-02 | Phase 5 | Pending |
| ADPT-03 | Phase 5 | Pending |
| ADPT-04 | Phase 5 | Pending |
| ADPT-05 | Phase 5 | Pending |
| ADPT-06 | Phase 5 | Pending |
| ADPT-07 | Phase 5 | Pending |
| ADPT-08 | Phase 5 | Pending |
| CAM-01 | Phase 6 | Pending |
| CAM-02 | Phase 6 | Pending |
| CAM-03 | Phase 6 | Pending |
| CAM-04 | Phase 6 | Pending |
| CAM-05 | Phase 6 | Pending |
| CAM-06 | Phase 6 | Pending |
| PIPE-01 | Phase 7 | Pending |
| PIPE-02 | Phase 7 | Pending |
| PIPE-03 | Phase 7 | Pending |
| PIPE-04 | Phase 7 | Pending |
| PIPE-05 | Phase 7 | Pending |
| PIPE-06 | Phase 7 | Pending |
| WEB-01 | Phase 8 | Pending |
| WEB-02 | Phase 8 | Pending |
| WEB-03 | Phase 8 | Pending |
| WEB-04 | Phase 8 | Pending |
| WEB-05 | Phase 8 | Pending |
| WEB-06 | Phase 8 | Pending |
| WEB-07 | Phase 8 | Pending |
| WEB-08 | Phase 8 | Pending |
| QA-01 | Phase 9 | Pending |
| QA-02 | Phase 9 | Pending |
| QA-03 | Phase 9 | Pending |
| QA-04 | Phase 9 | Pending |
| QA-05 | Phase 9 | Pending |

**Coverage:**
- v2.0 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-03 for milestone v2.0*
