"""Evaluation-mode label drawing."""

import cv2


def draw_eval_boxes(frame, result) -> None:
    if result.boxes is None:
        return

    names = result.names
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        cv2.rectangle(frame, p1, p2, (0, 220, 255), 2)
        label = f"{names.get(cls_id, cls_id)} {conf * 100:.1f}%"
        label_y = max(p1[1] - 8, 0)
        cv2.putText(
            frame,
            label,
            (p1[0], label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )
