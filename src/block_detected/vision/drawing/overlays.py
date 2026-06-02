"""Temporal detection overlay trails."""

import cv2

from block_detected.core.types import Box


def draw_overlay_history(frame, history: list[list[Box]]) -> None:
    if not history:
        return

    for age, boxes in enumerate(reversed(history), start=1):
        weight = age / len(history)
        color = (0, int(255 * weight), int(255 * (1.0 - weight)))
        thickness = 1 if age < len(history) else 2
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
