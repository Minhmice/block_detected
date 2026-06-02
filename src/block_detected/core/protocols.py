"""Protocols for pluggable backends (stdlib typing only)."""

from typing import Any, Protocol, runtime_checkable

from block_detected.core.domain import FrameResult


@runtime_checkable
class DetectorBackend(Protocol):
    """Object detector — Ultralytics YOLO implementation."""

    @property
    def model_name(self) -> str:
        ...

    def predict(self, frame: Any, *, conf: float) -> FrameResult:
        ...

    def close(self) -> None:
        ...
