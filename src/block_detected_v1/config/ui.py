"""Re-export legacy UI constants from defaults."""

from block_detected.config.defaults import (
    BUTTON_HEIGHT,
    BUTTON_MARGIN,
    BUTTON_PAD_X,
    KEY_ARROW_DOWN,
    KEY_ARROW_UP,
    WINDOW_NAME,
)

__all__ = [
    "WINDOW_NAME",
    "BUTTON_MARGIN",
    "BUTTON_HEIGHT",
    "BUTTON_PAD_X",
    "KEY_ARROW_UP",
    "KEY_ARROW_DOWN",
]
