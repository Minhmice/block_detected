"""KINEMATICS panel — displays target center and camera reference."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from block_detected.core.domain import RuntimeStatus

if QtWidgets is not None:

    class KinematicsCard(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("Panel")
            self.setMinimumHeight(192)

            layout = QtWidgets.QVBoxLayout(self)
            caps = QtWidgets.QLabel("KINEMATICS")
            caps.setObjectName("CapsLabel")
            layout.addWidget(caps)

            content = QtWidgets.QWidget()
            content_layout = QtWidgets.QVBoxLayout(content)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(4)

            # Target status
            self.target_status_label = QtWidgets.QLabel("target_status: idle")
            self.target_status_label.setObjectName("MetricMuted")
            content_layout.addWidget(self.target_status_label)

            # Center coordinates
            self.center_px_label = QtWidgets.QLabel("center_px: [—, —]")
            self.center_px_label.setObjectName("MetricMuted")
            content_layout.addWidget(self.center_px_label)

            # Distance (optional future use)
            self.distance_label = QtWidgets.QLabel("distance_px: —")
            self.distance_label.setObjectName("MetricMuted")
            content_layout.addWidget(self.distance_label)

            # Camera center
            self.camera_center_label = QtWidgets.QLabel("camera_center_px: [—, —]")
            self.camera_center_label.setObjectName("MetricMuted")
            content_layout.addWidget(self.camera_center_label)

            content_layout.addStretch(1)
            layout.addWidget(content)

        def update_status(self, status: RuntimeStatus) -> None:
            """Update kinematic display with runtime status."""
            if status.primary_detection is None:
                self.target_status_label.setText("target_status: idle")
                self.center_px_label.setText("center_px: [—, —]")
                self.distance_label.setText("distance_px: —")
                if status.camera_center_px:
                    cx, cy = status.camera_center_px
                    self.camera_center_label.setText(f"camera_center_px: [{cx}, {cy}]")
            else:
                self.target_status_label.setText("target_status: acquired")
                
                # Update center coordinates
                if status.primary_center_px:
                    cx, cy = status.primary_center_px
                    self.center_px_label.setText(f"center_px: [{int(cx)}, {int(cy)}]")
                
                # Update camera center
                if status.camera_center_px:
                    cam_cx, cam_cy = status.camera_center_px
                    self.camera_center_label.setText(f"camera_center_px: [{cam_cx}, {cam_cy}]")
                
                # Optionally calculate distance
                if status.primary_center_px and status.camera_center_px:
                    from block_detected.vision.geometry import distance_between_points
                    dist = distance_between_points(
                        status.camera_center_px,
                        status.primary_center_px,
                    )
                    self.distance_label.setText(f"distance_px: {dist:.1f}")

else:
    KinematicsCard = None  # type: ignore[misc, assignment]
