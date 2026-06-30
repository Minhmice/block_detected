# Requirements — Milestone v2.0

## v2.0 Requirements

### Module isolation (ISO-01)

- [ ] **ISO-01**: `block_detection_v2` lives under `src/block_detection_v2/` with no imports from v1 or other project packages
- [ ] **ISO-02**: Only OpenCV + NumPy dependencies; no YOLO/Ultralytics in this milestone

### Pipeline (PIP-01)

- [ ] **PIP-01**: Camera/video capture → preprocess (resize, gray, CLAHE, blur) → Canny/morph → Hough/LSD
- [ ] **PIP-02**: Contour + approxPolyDP → validated 6-point hexagon A–F with ordering rules
- [ ] **PIP-03**: Front face A-B-E-F and right face B-C-D-E with W_front, W_right, yaw
- [ ] **PIP-04**: Homography warp per face, horizontal split → 4 block regions projected to source frame
- [ ] **PIP-05**: EMA tracker with jump reject and short hold on lost frames
- [ ] **PIP-06**: Renderer draws polygon, faces, block lines, labels, center, yaw, FPS, status
- [ ] **PIP-07**: Per-frame JSON-shaped dict output (detected, points, center, widths, yaw_deg)
- [ ] **PIP-08**: `python -m block_detection_v2.main` runs live loop; ESC exits
- [ ] **PIP-09**: TODO in main.py for future YOLO ROI integration

### Polygon validation (POL-01)

- [ ] **POL-01**: Min area, near-convex, valid top/bottom ordering, min face area, reject self-intersecting

### Image dataset viewer (V2-IMG)

- [ ] **V2-IMG-01**: Dedicated `image_source.py` reads `block_dataset/` with natural sort
- [ ] **V2-IMG-02**: Arrow left/right (and p/n) navigate images; overlay shows index and filename

### Multi-block (V2-MULTI)

- [ ] **V2-MULTI-01**: `find_hexagons` returns multiple non-overlapping blocks per frame
- [ ] **V2-MULTI-02**: `MultiTracker` + renderer + `blocks[]` in frame output

### Relaxed detection (V2-RELAX)

- [ ] **V2-RELAX-01**: `DETECTION_SCORE_MIN` and relaxed contour/face thresholds in config

### Spike integration — ROI / fit / score (SPIKE)

- [ ] **SPIKE-ROI-01**: `extract_cluster_roi()` isolates block cluster from pallet/background via edge CC + morph
- [ ] **SPIKE-ROI-02**: 3-block mode trims ~22% from ROI right edge (exclude outermost right block)
- [ ] **SPIKE-FIT-01**: `fit_hexagon_from_lines()` seeds A–F from ROI, refines with dominant-angle Hough lines + edge snap
- [ ] **SPIKE-FIT-02**: `main.py` passes Hough/LSD lines to fitter (not `_lines` discard)
- [ ] **SPIKE-SCORE-01**: Composite score: `area_ratio + edge_support + topology`; reject tiny labels
- [ ] **SPIKE-SCORE-02**: Accept threshold and weights in `config.py`; hard reject `hex_area < 3500` or `area_ratio < 0.12`
- [ ] **SPIKE-BENCH-01**: Benchmark script on `block_dataset/` dt1–dt108 with overlays + JSON stats

### YOLO first-pass (YOLO) — Phase 18

- [ ] **YOLO-01**: `yolo_detector.py` — Ultralytics wrapper, model path `models/rbs-final.pt`
- [ ] **YOLO-02**: `YoloBlockBox` dataclass + `detect()` / `crop()` API; conf/iou configurable
- [ ] **YOLO-03**: Wire YOLO bbox → classical pipeline ROI (detect block before hex fit)
- [ ] **YOLO-04**: Fallback to edge-CC ROI when YOLO returns no boxes; benchmark gate unchanged

## Future Requirements

- Integration with v1 runtime / GUI / web API (optional)

## Out of Scope

- Modifying existing `block_detected` v1 code
- Training or model files in v2
- Dependency injection, factories, heavy tracker frameworks

## Traceability

| Requirement | Phase |
|-------------|-------|
| ISO-01, ISO-02 | 15 |
| PIP-01 … PIP-09 | 15 |
| POL-01 | 15 |
| V2-IMG-01, V2-IMG-02 | 16 |
| V2-MULTI-01, V2-MULTI-02 | 16 |
| V2-RELAX-01 | 16 |
| SPIKE-ROI-01, SPIKE-ROI-02 | 17 |
| SPIKE-FIT-01, SPIKE-FIT-02 | 17 |
| SPIKE-SCORE-01, SPIKE-SCORE-02 | 17 |
| SPIKE-BENCH-01 | 17 |
| YOLO-01 … YOLO-04 | 18 |
