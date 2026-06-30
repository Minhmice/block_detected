from __future__ import annotations

import time
from typing import List

import cv2

from . import config
from .geometry import compute_geometry
from .image_source import (
    KEY_ESC,
    ImageFolder,
    is_next_key,
    is_prev_key,
    navigation_hint,
    open_image_source,
    wait_key,
)
from .models import BlockResult
from .pipeline import detect_raw_hexagons
from .preprocessing import preprocess
from .renderer import frame_output, render
from .tracker import MultiTracker


def process_frame(frame, tracker: MultiTracker) -> tuple[List[BlockResult], dict, dict]:
    """Run detection + tracking. YOLO-first when USE_YOLO_ROI (see pipeline)."""
    color, gray = preprocess(frame)
    raw, meta = detect_raw_hexagons(color, gray)
    stable = tracker.update(raw)

    blocks: List[BlockResult] = []
    for det in stable:
        geo = compute_geometry(det.points)
        blocks.append(
            BlockResult(
                points=det.points,
                center=geo.center,
                front_width=geo.front_width,
                right_width=geo.right_width,
                yaw_deg=geo.yaw_deg,
                score=det.score,
                geometry=geo,
            )
        )

    output = frame_output(blocks)
    return blocks, output, meta


def main() -> None:
    src: ImageFolder = open_image_source()
    tracker = MultiTracker()
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)

    prev_t = time.perf_counter()
    fps = 0.0

    try:
        while True:
            ok, frame = src.read()
            if not ok or frame is None:
                break

            blocks, output, meta = process_frame(frame, tracker)

            now = time.perf_counter()
            dt = now - prev_t
            prev_t = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            yolo_boxes = meta.get("yolo_boxes") if config.DEBUG_YOLO else None
            vis = render(
                frame,
                blocks,
                fps,
                output["detected"],
                navigation_hint(src),
                yolo_boxes=yolo_boxes,
            )
            cv2.imshow(config.WINDOW_NAME, vis)

            key = wait_key(config.IMAGE_PAUSE_MS)
            if key == KEY_ESC or (key & 0xFF) == KEY_ESC:
                break
            if is_prev_key(key):
                src.prev_image()
            elif is_next_key(key):
                src.next_image()
    finally:
        src.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
