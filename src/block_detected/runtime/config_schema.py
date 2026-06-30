"""Re-export from block_detected.config (deprecated path)."""

from block_detected.config.schema import *  # noqa: F403
from block_detected.config.schema import (
    AppConfig,
    CameraConfig,
    ClassicalPipelineConfig,
    InferenceConfig,
    PreprocessConfig,
    RESTART_CAMERA_KEYS,
    RESTART_DETECTOR_KEYS,
    StabilityConfig,
    UiDebugConfig,
)

__all__ = [
    "AppConfig",
    "CameraConfig",
    "InferenceConfig",
    "PreprocessConfig",
    "ClassicalPipelineConfig",
    "StabilityConfig",
    "UiDebugConfig",
    "RESTART_CAMERA_KEYS",
    "RESTART_DETECTOR_KEYS",
]
