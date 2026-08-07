"""Ultralytics YOLO detector backend."""

from pathlib import Path

from block_detected.core.domain import FrameResult
from block_detected.detection.boxes import parse_yolo_result
from block_detected.detection.yolo.loader import load_yolo


class YoloDetector:
    def __init__(self, model_path: Path) -> None:
        self._path = model_path
        self._model = load_yolo(model_path)

    @property
    def model_name(self) -> str:
        return self._path.name

    def predict(
        self,
        frame,
        *,
        conf: float,
        iou: float = 0.45,
        imgsz: int = 640,
        max_det: int = 100,
        agnostic_nms: bool = False,
    ) -> FrameResult:
        results = self._model(
            frame,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            max_det=max_det,
            agnostic_nms=agnostic_nms,
            verbose=False,
        )
        return parse_yolo_result(results[0])

    def close(self) -> None:
        self._model = None  # type: ignore[assignment]
