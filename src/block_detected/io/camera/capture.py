"""Webcam capture and source switching."""

import cv2


def open_camera(
    index: int,
    *,
    width: int,
    height: int,
) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def switch_camera(
    cap: cv2.VideoCapture,
    current_camera: int,
    *,
    max_index: int,
    width: int,
    height: int,
) -> tuple[cv2.VideoCapture, int, bool]:
    """Try the next available camera index. Returns (cap, new_index, switched)."""
    next_camera = (current_camera + 1) % (max_index + 1)

    for _ in range(max_index + 1):
        new_cap = open_camera(next_camera, width=width, height=height)
        if new_cap is not None:
            cap.release()
            return new_cap, next_camera, True
        next_camera = (next_camera + 1) % (max_index + 1)

    return cap, current_camera, False
