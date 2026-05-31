"""Pydantic wire schemas (camelCase JSON)."""

from .wire import (
    ClassificationScoresWire,
    DetectionParamsWire,
    DetectionResultWire,
    DetectionTelemetryWire,
    PointWire,
    SystemStatusWire,
)

__all__ = [
    "ClassificationScoresWire",
    "DetectionParamsWire",
    "DetectionResultWire",
    "DetectionTelemetryWire",
    "PointWire",
    "SystemStatusWire",
]
