"""Pydantic response models for web API (no OpenCV imports)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from block_detected.core.domain import RuntimeStatus


class TelemetryResponse(BaseModel):
    """Viewport toolbar metrics.

    ``latency_ms`` is the aggregate of frame read and inference stages
    (``frame_read_ms + inference_ms``), not including render time.
    """

    fps: float = 0.0
    latency_ms: float = 0.0
    render_ms: float = 0.0
    frame_read_ms: float | None = None
    inference_ms: float | None = None
    model_name: str | None = None
    camera_index: int | None = None
    running: bool = False
    detection_count: int = 0


class LogsResponse(BaseModel):
    lines: list[str] = Field(default_factory=list)
    count: int = 0


class ControlResponse(BaseModel):
    ok: bool
    message: str | None = None


class EngineStateResponse(BaseModel):
    running: bool
    model_name: str | None = None
    camera_index: int | None = None
    error: str | None = None


def telemetry_from_status(status: RuntimeStatus | None, *, running: bool) -> TelemetryResponse:
    if status is None:
        return TelemetryResponse(running=running)

    stats = status.stats
    return TelemetryResponse(
        fps=stats.fps,
        latency_ms=stats.frame_read_ms + stats.inference_ms,
        render_ms=stats.render_ms,
        frame_read_ms=stats.frame_read_ms,
        inference_ms=stats.inference_ms,
        model_name=status.model_name or stats.model_name,
        camera_index=status.camera_index,
        running=running,
        detection_count=status.detection_count,
    )
