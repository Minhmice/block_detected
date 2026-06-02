"""Draw domain detections on frames (no detection imports)."""

import cv2

from block_detected.core.domain import Detection


def draw_detection_boxes(
    frame,
    detections: list[Detection],
    *,
    color: tuple[int, int, int] = (0, 220, 120),
    thickness: int = 2,
    show_labels: bool = True,
) -> None:
    for detection in detections:
        x1, y1, x2, y2 = detection.box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        if not show_labels:
            continue
        label = f"{detection.class_name} {detection.confidence * 100:.1f}%"
        label_y = max(y1 - 8, 0)
        cv2.putText(
            frame,
            label,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
