"""Protocols for pluggable backends (stdlib typing only)."""

from typing import Any, Protocol, runtime_checkable

from block_detected.core.domain import FrameResult


@runtime_checkable
class DetectorBackend(Protocol):
    """Object detector — Ultralytics YOLO implementation."""

    @property
    def model_name(self) -> str:
        ...

    def predict(
        self,
        frame: Any,
        *,
        conf: float,
        iou: float = 0.45,
        imgsz: int = 640,
        max_det: int = 100,
        agnostic_nms: bool = False,
    ) -> FrameResult:
        ...

    def close(self) -> None:
        ...
