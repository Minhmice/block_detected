"""On-screen UI widgets (status bar, buttons)."""

from typing import TYPE_CHECKING

import cv2

from block_detected.config.ui import BUTTON_HEIGHT, BUTTON_MARGIN, BUTTON_PAD_X

if TYPE_CHECKING:
    from block_detected.core.domain import InferenceStats


def draw_model_switch_button(
    frame,
    model_name: str,
    *,
    button_margin: int = BUTTON_MARGIN,
    button_height: int = BUTTON_HEIGHT,
    button_pad_x: int = BUTTON_PAD_X,
) -> tuple[int, int, int, int]:
    """Draw clickable button; returns (x1, y1, x2, y2)."""
    label = f"  Model: {model_name}  |  Click or [V] next  "
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, scale, thickness)
    h, w = frame.shape[:2]

    btn_w = text_w + button_pad_x * 2
    btn_h = max(button_height, text_h + baseline + 12)
    x1 = button_margin
    y2 = h - button_margin
    y1 = y2 - btn_h
    x2 = min(x1 + btn_w, w - 1)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 40, 40), -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 120), 2)
    text_x = x1 + button_pad_x
    text_y = y1 + (btn_h + text_h) // 2 - baseline
    cv2.putText(frame, label, (text_x, text_y), font, scale, (240, 240, 240), thickness, cv2.LINE_AA)
    return x1, y1, x2, y2


def draw_status_bar(
    frame,
    *,
    eval_mode: bool,
    conf: float,
    eval_conf: float,
    overlay_enabled: bool,
    model_name: str,
    stats: "InferenceStats | None" = None,
) -> None:
    if eval_mode:
        status = f"mode: eval | conf: {eval_conf:.3f} | model: {model_name}"
    else:
        status = (
            f"mode: normal | conf: {conf:.3f} | overlay: {'on' if overlay_enabled else 'off'}"
            f" | model: {model_name}"
        )
    if stats is not None:
        status += (
            f" | fps: {stats.fps:.1f}"
            f" | read: {stats.frame_read_ms:.1f}ms"
            f" | infer: {stats.inference_ms:.1f}ms"
            f" | render: {stats.render_ms:.1f}ms"
        )
    cv2.putText(
        frame,
        status,
        (12, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
