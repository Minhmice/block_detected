"""Viewport toolbar with overlay toggles and metrics."""

from __future__ import annotations

from block_detected.apps.gui.widgets.metric_badge import MetricBadge
from block_detected.apps.gui.widgets.toggle_pill import TogglePill

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class CameraToolbar(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("ViewportToolbar")
            self.setFixedHeight(48)
            layout = QtWidgets.QHBoxLayout(self)
            layout.setContentsMargins(12, 6, 12, 6)

            self.contours_check = TogglePill("Contours")
            self.corners_check = TogglePill("Corners")
            self.warped_check = TogglePill("Warped Face")
            self.warped_check.setEnabled(False)
            self.warped_check.setToolTip("Warped face overlay — future phase")

            for toggle in (self.contours_check, self.corners_check, self.warped_check):
                layout.addWidget(toggle)
            layout.addStretch(1)

            self.fps_badge = MetricBadge("FPS:", "MetricPrimary")
            self.latency_badge = MetricBadge("Latency:", "MetricSecondary")
            self.render_badge = MetricBadge("render", "MetricRender")
            layout.addWidget(self.fps_badge)
            layout.addWidget(self.latency_badge)
            layout.addWidget(self.render_badge)

        @property
        def fps_label(self):
            return self.fps_badge.value_label

        @property
        def latency_label(self):
            return self.latency_badge.value_label

        @property
        def render_label(self):
            return self.render_badge.value_label

else:
    CameraToolbar = None  # type: ignore[misc, assignment]
