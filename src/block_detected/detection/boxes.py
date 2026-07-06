"""Parse raw detector outputs into domain types."""

from block_detected.core.domain import Detection, FrameResult
from block_detected.core.types import Box


def parse_yolo_result(result) -> FrameResult:
    """Parse Ultralytics result — handles detection (boxes) and OBB (obb)."""
    detections: list[Detection] = []
    names = result.names

    # OBB model → result.obb
    if hasattr(result, "obb") and result.obb is not None:
        for obb in result.obb:
            xc, yc, w, h, angle_rad = obb.xywhr[0].tolist()
            cls_id = int(obb.cls[0].item())
            conf = float(obb.conf[0].item())
            # xywhr → x1y1x2y2 for axis-aligned box
            x1 = int(xc - w / 2)
            y1 = int(yc - h / 2)
            x2 = int(xc + w / 2)
            y2 = int(yc + h / 2)
            detections.append(
                Detection(
                    box=(x1, y1, x2, y2),
                    class_id=cls_id,
                    class_name=str(names.get(cls_id, cls_id)),
                    confidence=conf,
                    angle=angle_rad,
                )
            )
        return FrameResult(detections=detections, raw=result)

    # Detection model → result.boxes
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            detections.append(
                Detection(
                    box=(int(x1), int(y1), int(x2), int(y2)),
                    class_id=cls_id,
                    class_name=str(names.get(cls_id, cls_id)),
                    confidence=conf,
                )
            )
    return FrameResult(detections=detections, raw=result)


def extract_boxes(result) -> list[Box]:
    """Legacy helper — prefer parse_yolo_result().detections."""
    return [d.box for d in parse_yolo_result(result).detections]


def boxes_from_detections(detections: list[Detection]) -> list[Box]:
    return [d.box for d in detections]
