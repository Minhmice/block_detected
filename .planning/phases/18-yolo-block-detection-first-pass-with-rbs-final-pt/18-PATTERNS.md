# Phase 18 Patterns

## Analog map

| New / modified | Closest analog | Notes |
|----------------|----------------|-------|
| `yolo_detector.py` | Greenfield Ultralytics | Already written; no v1 analog |
| `roi_from_bbox()` | `extract_cluster_roi()` in `roi.py` | Same `ROIBox` output; rectangular mask not CC |
| `detect_hex_in_roi()` | Body of `detect_raw_hexagons()` | Extract inner loop for reuse |
| YOLO-first orchestration | `detect_raw_hexagons()` | Add branch at top |
| Config YOLO keys | `config.py` ROI/score block | Same flat constants style |
| Tests | `tests/test_block_detection_v2_roi.py` | Dataset dt50 smoke |

## `roi_from_bbox` pattern

```python
# roi.py — after ROIBox dataclass
def roi_from_bbox(
    x1: int, y1: int, x2: int, y2: int,
    frame_shape: FrameShape,
    *,
    block_mode: int | None = None,
    pad_frac: float | None = None,
) -> ROIBox:
    h, w = frame_shape
    mode = config.BLOCK_MODE if block_mode is None else block_mode
    pad = config.YOLO_PAD_FRAC if pad_frac is None else pad_frac
    # expand bbox by pad * width/height, clamp
    # if mode == 3: trim right 22% of bbox width
    # mask[y0:y1, x0:x1] = 255
    return ROIBox(...)
```

## Pipeline split pattern

```python
# pipeline.py
def _detect_hex_in_roi(color, gray, roi, lines, edges) -> tuple[HexagonDetection | None, dict]:
    """Fit + score inside one ROI; points in full-frame coords."""

def detect_raw_hexagons(color, gray, *, yolo_detector=None) -> ...:
    if config.USE_YOLO_ROI:
        boxes = (yolo_detector or _default_yolo()).detect(color)
        if boxes:
            dets, metas = [], []
            for box in boxes[:config.MAX_BLOCKS]:
                roi = roi_from_bbox(box.x1, box.y1, box.x2, box.y2, shape)
                det, meta = _detect_hex_in_roi(...)
                meta["yolo_conf"] = box.confidence
                meta["stage"] = "yolo_roi"
                ...
            return dets, merged_meta
    # existing edge-CC path; meta["stage"] = "edge_roi"
```

## Lazy YOLO singleton

```python
_yolo: YoloBlockDetector | None = None

def _default_yolo() -> YoloBlockDetector:
    global _yolo
    if _yolo is None:
        _yolo = YoloBlockDetector(model_path=config.YOLO_MODEL_PATH, conf=config.YOLO_CONF, ...)
    return _yolo
```

## main.py pattern

```python
# Remove TODO line 27; process_frame unchanged if pipeline owns YOLO
blocks, output = process_frame(frame, tracker)  # pipeline loads YOLO internally
```

## Renderer optional overlay

Draw orange rectangles for YOLO boxes when `meta` or `BlockResult` carries `yolo_xyxy` — optional in 18-04.

## Test pattern

```python
@pytest.mark.skipif(not MODEL.exists(), reason="model missing")
def test_yolo_detect_dt50():
    det = YoloBlockDetector()
    boxes = det.detect(cv2.imread(...))
    assert len(boxes) >= 1
    assert boxes[0].confidence > 0.5
```

Mock YOLO for pipeline unit tests:

```python
class FakeYolo:
    def detect(self, frame): return []
# assert fallback stage edge_roi
```
