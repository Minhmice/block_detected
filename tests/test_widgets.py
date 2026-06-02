"""Tests for OpenCV drawing widget layout."""

import numpy as np

from block_detected.vision.drawing.widgets import draw_model_switch_button


def test_model_button_uses_passed_layout_values():
    frame = np.zeros((120, 240, 3), dtype=np.uint8)

    x1, _y1, _x2, y2 = draw_model_switch_button(
        frame,
        "model.pt",
        button_margin=9,
        button_height=30,
        button_pad_x=4,
    )

    assert x1 == 9
    assert y2 == 111
