"""Draw domain detections on frames (no detection imports)."""

import cv2

from block_detected.core.domain import Detection
from block_detected.vision.geometry import (
    box_center,
    box_to_xywh,
)


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


def draw_detection_centers(
    frame,
    detections: list[Detection],
    *,
    color: tuple[int, int, int] = (0, 0, 255),  # BGR: Red
    radius: int = 5,
    thickness: int = 2,
    show_coords: bool = True,
) -> None:
    """Draw center point and XYWH coordinates for each detection.
    
    Args:
        frame: Image to draw on
        detections: List of Detection objects
        color: BGR color tuple (default red)
        radius: Radius of center circle
        thickness: Thickness of circle outline
        show_coords: Whether to show XYWH text coordinates
    """
    for detection in detections:
        cx, cy = box_center(detection.box)
        center_point = (int(cx), int(cy))
        
        # Draw center circle
        cv2.circle(frame, center_point, radius, color, thickness)
        
        if show_coords:
            # Get XYWH coordinates
            x, y, w, h = box_to_xywh(detection.box)
            
            # Format coordinate text
            coord_text = f"x:{int(x)} y:{int(y)} w:{int(w)} h:{int(h)}"
            
            # Draw text above the center point
            text_y = int(cy) - 15
            cv2.putText(
                frame,
                coord_text,
                (int(cx) - 40, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
                cv2.LINE_AA,
            )


def draw_camera_center(
    frame,
    *,
    color: tuple[int, int, int] = (200, 0, 200),  # BGR: Purple/Magenta
    radius: int = 8,
    thickness: int = 2,
    show_coords: bool = True,
) -> None:
    """Draw camera center point with crosshair and XYWH coordinates.
    
    Args:
        frame: Image to draw on
        color: BGR color tuple (default purple/magenta)
        radius: Radius of center circle
        thickness: Thickness of lines
        show_coords: Whether to show XYWH text coordinates
    """
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    center_point = (cx, cy)
    
    # Draw center circle
    cv2.circle(frame, center_point, radius, color, thickness)
    
    # Draw crosshair
    crosshair_size = radius * 3
    cv2.line(frame, (cx - crosshair_size, cy), (cx + crosshair_size, cy), color, 1)
    cv2.line(frame, (cx, cy - crosshair_size), (cx, cy + crosshair_size), color, 1)
    
    if show_coords:
        # Camera center XYWH format
        coord_text = f"camera: x:{cx} y:{cy} w:{w} h:{h}"
        
        # Draw text above the center point
        cv2.putText(
            frame,
            coord_text,
            (cx - 70, cy - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
            cv2.LINE_AA,
        )
