"""KINEMATICS panel with COMING SOON overlay."""

from __future__ import annotations

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

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
            faded = QtWidgets.QLabel(
                "target_status: acquired\ncenter_px: [640, 480]\nangle_deg: 45.2°\npose_mm: -12.5"
            )
            faded.setObjectName("MetricMuted")
            content_layout.addWidget(faded)
            layout.addWidget(content)

            overlay = QtWidgets.QLabel("COMING SOON")
            overlay.setObjectName("ComingSoon")
            overlay.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            overlay.setParent(self)
            self._overlay = overlay

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            self._overlay.setGeometry(self.rect())
            self._overlay.raise_()

else:
    KinematicsCard = None  # type: ignore[misc, assignment]
