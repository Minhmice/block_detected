"""Core shared types and protocols."""

from block_detected.core.domain import Detection, FrameResult, InferenceStats, RuntimeStatus
from block_detected.core.types import Box

__all__ = ["Box", "Detection", "FrameResult", "InferenceStats", "RuntimeStatus"]
