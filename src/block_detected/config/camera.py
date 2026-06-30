"""Re-export legacy constants from defaults."""

from block_detected.config.defaults import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    MAX_CAMERA_INDEX,
)

__all__ = ["CAMERA_INDEX", "MAX_CAMERA_INDEX", "CAMERA_WIDTH", "CAMERA_HEIGHT"]
