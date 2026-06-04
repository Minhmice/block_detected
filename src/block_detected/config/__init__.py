"""Configuration — paths, camera, inference, and UI defaults."""

from block_detected.config.camera import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    MAX_CAMERA_INDEX,
)
from block_detected.config.inference import (
    CONF_MAX,
    CONF_MIN,
    CONF_STEP,
    DEFAULT_CONF,
    DEFAULT_MODEL_NAME,
    EVAL_CONF,
)
from block_detected.config.paths import MODELS_DIR, PROJECT_ROOT
from block_detected.config.ui import (
    BUTTON_HEIGHT,
    BUTTON_MARGIN,
    BUTTON_PAD_X,
    KEY_ARROW_DOWN,
    KEY_ARROW_UP,
    WINDOW_NAME,
)

__all__ = [
    "PROJECT_ROOT",
    "MODELS_DIR",
    "DEFAULT_MODEL_NAME",
    "CAMERA_INDEX",
    "MAX_CAMERA_INDEX",
    "CAMERA_WIDTH",
    "CAMERA_HEIGHT",
    "WINDOW_NAME",
    "CONF_MIN",
    "CONF_MAX",
    "CONF_STEP",
    "DEFAULT_CONF",
    "EVAL_CONF",
    "BUTTON_MARGIN",
    "BUTTON_HEIGHT",
    "BUTTON_PAD_X",
    "KEY_ARROW_UP",
    "KEY_ARROW_DOWN",
]
