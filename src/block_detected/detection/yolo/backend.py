"""Ultralytics YOLO detector backend."""

from pathlib import Path

from ultralytics import YOLO

from block_detected.core.domain import FrameResult
from block_detected.detection.boxes import parse_yolo_result


class YoloDetector:
    def __init__(self, model_path: Path) -> None:
        self._path = model_path
        self._model = YOLO(str(model_path))

    @property
    def model_name(self) -> str:
        return self._path.name

    def predict(self, frame, *, conf: float) -> FrameResult:
        results = self._model(frame, conf=conf, verbose=False)
        return parse_yolo_result(results[0])

    def close(self) -> None:
        self._model = None  # type: ignore[assignment]
