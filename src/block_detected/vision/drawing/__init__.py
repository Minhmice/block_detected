"""Frame annotation drawing primitives."""

from block_detected.vision.drawing.eval import draw_eval_boxes
from block_detected.vision.drawing.widgets import draw_model_switch_button, draw_status_bar

__all__ = [
    "draw_eval_boxes",
    "draw_model_switch_button",
    "draw_status_bar",
]
