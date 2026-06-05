# Backend Gap Analysis — Robo-Vision OS v2.4 vs `block_detected`

> Generated: 2026-06-05  
> Reference UI: `example_ui/stitch_block_pickup_vision_console/code.html`  
> Reference spec: `html_data_requirements.md`  
> Codebase snapshot: `.planning/codebase/` (refreshed via `/gsd-map-codebase`)

Legend: **✅ Có** · **🟡 Một phần** (schema / UI cũ / hành vi tương đương nhưng chưa khớp spec) · **❌ Chưa có**

---

## Tóm tắt nhanh

| Nhóm | ✅ | 🟡 | ❌ |
|------|----|----|-----|
| 1. Camera | 3 | 4 | 5 |
| 2. YOLO inference | 2 | 5 | 6 |
| 3. Candidate / classical pipeline | 0 | 3 | 18 |
| 4. Test metrics (reject, stability, telemetry) | 6 | 6 | 12 |

**Backend hiện tại:** PySide6 GUI + `WebcamEngine` (OpenCV capture → Ultralytics YOLO `.pt` → postprocess stability → render/metrics).  
**Frontend mới cần:** Web console (Stitch HTML) với pipeline đầy đủ hơn (classical CV, ROI, overlay, kinematics, profile).

---

## 1. Camera

### 1.1 Config fields (target spec)

| Field | Trạng thái | Backend hiện tại | Ghi chú |
|-------|------------|------------------|---------|
| `cameraSource` (OBS / USB / Pi Camera) | ❌ | Chỉ `cv2.VideoCapture(index)` | `CameraConfig.index`, `io/camera/capture.py` — không phân loại nguồn |
| `resolution` 640×480 | 🟡 | `camera.width` / `camera.height` | Default **1280×720** trong `config_schema.py`; có set qua OpenCV props |
| `fpsTarget` 30 | ❌ | — | Không set `CAP_PROP_FPS`, không metric target FPS |
| `exposureLock` | ❌ | — | Không điều khiển exposure |
| `whiteBalanceLock` | ❌ | — | Không điều khiển WB |
| `frameWidth` / `frameHeight` | ✅ | `CameraConfig.width`, `.height` | TOML + GUI spinbox; restart camera khi đổi |
| `viewportWidth` / `viewportHeight` | ❌ | — | GUI preview scale theo widget, không có config riêng |
| `objectFit: contain` | 🟡 | `Qt.KeepAspectRatio` trong `apps/gui/app.py` | Chỉ PySide6 preview; chưa expose cho web UI |
| `coordDebug` (scale, offsetX, offsetY) | ❌ | — | Không map tọa độ frame ↔ viewport |

### 1.2 `html_data_requirements.md` — camera liên quan

| UI element | Trạng thái | Backend hiện tại |
|------------|------------|------------------|
| NEXT CAMERA | ✅ | `WebcamEngine.switch_camera()` + GUI button |
| Main camera feed (stream/img) | ✅ | Frame BGR → QImage preview (chưa MJPEG/base64 API cho web) |
| ROI X / Y / WIDTH / HEIGHT | ❌ | Không crop ROI trước infer |
| Camera width/height controls | ✅ | PySide6 Camera group (index, max, w, h) |

### 1.3 Việc cần làm (camera)

1. Enum `cameraSource` + adapter (USB index, OBS virtual cam, Pi libcamera).
2. `fpsTarget`, exposure/WB lock qua OpenCV / platform API.
3. Viewport model: `frame*` vs `viewport*`, `objectFit`, `coordDebug` cho overlay web.
4. ROI crop stage trước pipeline (config + engine hook).
5. Streaming API cho web UI (MJPEG hoặc WebSocket frames) thay vì chỉ Qt widget.

---

## 2. YOLO inference

### 2.1 Config fields (target spec)

| Field | Trạng thái | Backend hiện tại | Ghi chú |
|-------|------------|------------------|---------|
| `modelPath` → `best.onnx` | 🟡 | `models/*.pt` via Ultralytics | `detection/yolo/backend.py`; `.onnx` trong `.gitignore`, không backend ONNX |
| `imgsz` 640 | ❌ | — | `predict()` không truyền `imgsz` |
| `confThreshold` 0.35–0.70 | 🟡 | `RuntimeState.confidence` | Default **0.25**; hot-reload; range 0.001–0.95 |
| `iouThreshold` 0.45 | ❌ | — | Không truyền `iou` vào YOLO NMS |
| `maxDetections` 10 | ❌ | — | Không giới hạn |
| `device` / ExecutionProvider | ❌ | Ultralytics auto | Không chọn CPU/CUDA/ONNX EP |
| `classNames` BLOCK01–04 | 🟡 | Từ `result.names` trong model | Không map cố định 0–3; phụ thuộc weights |
| `multiDetectEnabled` | 🟡 | Nhiều box được parse | Không có flag bật/tắt |
| `showConfidencePerBox` | ✅ | `vision/drawing/detections.py` | Label `class confidence%` |

### 2.2 `html_data_requirements.md` — inference sidebar

| UI element | Trạng thái | Backend hiện tại |
|------------|------------|------------------|
| Confidence slider 0–1 | ✅ | GUI conf spin + slider; hot apply |
| NMS IoU slider | ❌ | Không có config/runtime |
| NEXT MODEL | ✅ | `switch_model()` cycle `models/*.pt` |
| START / STOP | ✅ | GUI engine thread |

### 2.3 Việc cần làm (YOLO)

1. Mở rộng `InferenceConfig`: `imgsz`, `iou`, `max_det`, `device`, `model_path` (pt/onnx).
2. Cập nhật `YoloDetector.predict()` truyền đủ tham số Ultralytics.
3. (Tuỳ chọn) `detection/onnx/` backend + loader — đã được nhắc trong phase-02 research.
4. `classNames` override trong config khi model không embed names.
5. REST/WebSocket endpoint để web UI chỉnh conf/IoU hot-reload.

---

## 3. Candidate / classical pipeline

> `ClassicalPipelineConfig` trong `config_schema.py` là **placeholder** (`enabled=False`); không có stage OpenCV nào chạy trong engine.

### 3.1 Config fields (target spec)

| Field | Trạng thái | Backend hiện tại |
|-------|------------|------------------|
| `preprocessMode` (canny / adaptive / hsv) | ❌ | — |
| `blurKernel` 3/5/7 | 🟡 | Field `classical.blur_kernel` (default 0), **không dùng** |
| `cannyLow` 50 | 🟡 | Field `classical.canny_low`, **không dùng** |
| `cannyHigh` 150 | 🟡 | Field `classical.canny_high`, **không dùng** |
| `contourRetrieval` RETR_EXTERNAL | ❌ | — |
| `minAreaPx` 1000 | ❌ | `stability.min_box_area_px` là post-YOLO, không phải contour |
| `maxAreaPx` 80000 | ❌ | — |
| `aspectRatioTolerance` 0.15 | ❌ | — |
| `approxPolyEpsilon` 0.02 | ❌ | — |
| `requireConvex` true | ❌ | — |
| `warpSize` 128/160 | ❌ | — |
| `rejectInternalContours` true | ❌ | — |

### 3.2 `html_data_requirements.md` — pre-processing & overlays

| UI element | Trạng thái | Backend hiện tại |
|------------|------------|------------------|
| Contrast 0–2 | ❌ | — |
| Brightness −100–100 | ❌ | — |
| Saturation 0–3 | ❌ | — |
| Blur kernel (sidebar Stability) | ❌ | Schema classical only; GUI không expose |
| Canny Low / High | ❌ | Schema only |
| Overlay: Contours | ❌ | — |
| Overlay: Corners | ❌ | — |
| Overlay: Warped Face | ❌ | — |

### 3.3 Việc cần làm (pipeline)

1. Module `vision/preprocess/` hoặc `runtime/classical.py`: blur → mode (canny/adaptive/hsv) → morphology.
2. `findContours` + filter (area, aspect, convex, approx) → candidate boxes.
3. Perspective warp + face patch (`warpSize`).
4. Wire `ClassicalPipelineConfig` vào engine (trước hoặc song song YOLO).
5. Overlay render layers toggled by UI flags.
6. GUI/web controls cho contrast/brightness/saturation (html spec).

---

## 4. Test metrics — reject, stability & telemetry

Nhóm này gom **reject/stability config**, **performance telemetry**, và **primary-target readouts** từ HTML mock.

### 4.1 Reject + stability config (target spec)

| Field | Trạng thái | Backend hiện tại | Ghi chú |
|-------|------------|------------------|---------|
| `minConf` 0.70 | 🟡 | `stability.min_confidence` | Default **0.0**; filter khi `stability.enabled` |
| `top1Top2Margin` 0.20 | ❌ | — | Không so sánh top-2 class scores |
| `unknownIfLowMargin` true | ❌ | — | Không emit class UNKNOWN |
| `temporalWindow` 7 | 🟡 | `stability.temporal_window` | Default **5**, configurable |
| `requiredStableVotes` 5 | 🟡 | `stability.required_stable_votes` | Default **3**, configurable |
| `duplicateMergeIoU` 0.50 | ✅ | `merge_duplicate_detections()` | Default 0.5, GUI + TOML |
| `rejectIfPartialBox` true | 🟡 | `reject_edge_boxes` | Tương đương partial-at-border; không generic partial occlusion |
| `rejectIfTooSmall` true | ✅ | `filter_min_area()` | `min_box_area_px` |

**Đã có thêm (ngoài spec):** `stability.enabled` master switch, `reject_edge_boxes` toggle, tests trong `tests/test_postprocess.py`.

### 4.2 Performance metrics (`html_data_requirements` §2)

| Metric | Trạng thái | Backend hiện tại |
|--------|------------|------------------|
| FPS | ✅ | `RuntimeMetrics` → `InferenceStats.fps` |
| Latency (ms) | 🟡 | `frame_read_ms` + `inference_ms` tách riêng; không field `latency` tổng |
| Render time (ms) | ✅ | `InferenceStats.render_ms` |
| Status bar / GUI hiển thị | ✅ | PySide6 status + OpenCV status bar |

### 4.3 Bottom telemetry — primary detect & kinematics (§4)

| Field | Trạng thái | Backend hiện tại |
|-------|------------|------------------|
| Object class (primary) | ❌ | Chỉ list detections; không chọn “primary target” |
| Confidence + bar chart | 🟡 | Per-box label khi vẽ; không telemetry struct cho UI |
| Target status (acquired/tracking/lost) | ❌ | — |
| Center (px) [X, Y] | ❌ | Không tính centroid primary |
| Angle (deg) | ❌ | — |
| Pose (mm) | ❌ | — |

### 4.4 System log & config profiles (§4.3, §6)

| Feature | Trạng thái | Backend hiện tại |
|---------|------------|------------------|
| Log entries (timestamp, level, message) | ✅ | `logging_setup.py` ring buffer; GUI `get_log_lines()` |
| Config profile dropdown | ❌ | Chỉ single `block_detected.toml` |
| SAVE CONFIG | 🟡 | `save_config()` → một file TOML |
| DELETE profile | ❌ | — |
| Temporal smoothing checkbox (html §5.3) | 🟡 | `stability.enabled` tương đương; không có control riêng “temporal smoothing” label |

### 4.5 Việc cần làm (test metrics / telemetry)

1. `RejectConfig`: `top1_top2_margin`, `unknown_if_low_margin`.
2. Domain type `PrimaryTarget` / `Kinematics` emitted mỗi frame.
3. Tracker state machine: acquired → tracking → lost.
4. Aggregate `latency_ms` cho web toolbar (hoặc document mapping từ stage metrics).
5. Named config profiles (load/save/delete nhiều TOML hoặc JSON).
6. JSON/WebSocket telemetry payload cho Stitch UI (FPS, latency, render, primary detect, log tail).

---

## Mapping nhanh: HTML sections → module backend

| HTML section | Module / file gần nhất | Gap chính |
|--------------|------------------------|-----------|
| Top nav (camera/model/start/stop) | `runtime/engine.py`, `apps/gui/app.py` | Web API; camera source enum |
| Viewport toolbar (overlays, FPS) | `runtime/metrics.py` | Overlays; web binding |
| Main feed | `apps/gui/app.py` preview | Stream endpoint |
| Telemetry panel | — | Primary target + kinematics chưa tồn tại |
| Sidebar pre-processing | `ClassicalPipelineConfig` (placeholder) | Toàn bộ pipeline |
| Sidebar inference | `detection/yolo/backend.py` | IoU, imgsz, device |
| Sidebar stability | `runtime/postprocess.py` | Margin/unknown; html blur/min-area khác layer |
| Sidebar edge / ROI | — | Chưa implement |
| Footer profiles | `runtime/config_store.py` | Multi-profile |

---

## Thứ tự đề xuất khi nối frontend mới

1. **Telemetry API** — FPS/latency/render + log tail + frame stream (unblock UI shell).
2. **Inference params** — conf, IoU, imgsz hot-reload (sidebar §5.2).
3. **Stability/reject** — align defaults (window=7, votes=5, minConf=0.70) + margin/unknown.
4. **Camera** — source types, ROI, coord mapping.
5. **Classical pipeline** — largest gap; có thể phase sau YOLO-only MVP.

---

## Files tham chiếu (đã có)

| Concern | Path |
|---------|------|
| Config schema | `src/block_detected/runtime/config_schema.py` |
| TOML load/save | `src/block_detected/runtime/config_store.py` |
| Engine loop | `src/block_detected/runtime/engine.py` |
| Post-process | `src/block_detected/runtime/postprocess.py` |
| YOLO backend | `src/block_detected/detection/yolo/backend.py` |
| Camera I/O | `src/block_detected/io/camera/capture.py` |
| Metrics | `src/block_detected/runtime/metrics.py` |
| PySide6 GUI (sẽ thay) | `src/block_detected/apps/gui/app.py` |
| Tests (stability) | `tests/test_postprocess.py`, `tests/test_metrics.py` |
