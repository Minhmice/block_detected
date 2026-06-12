"""Metric label with colored value."""

from __future__ import annotations

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class MetricBadge(QtWidgets.QWidget):
        def __init__(self, prefix: str, accent: str = "MetricMuted", parent=None) -> None:
            super().__init__(parent)
            layout = QtWidgets.QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            self.prefix_label = QtWidgets.QLabel(prefix)
            self.prefix_label.setObjectName("MetricMuted")
            self.value_label = QtWidgets.QLabel("—")
            self.value_label.setObjectName(accent)
            layout.addWidget(self.prefix_label)
            layout.addWidget(self.value_label)

        def set_value(self, text: str, accent: str | None = None) -> None:
            self.value_label.setText(text)
            if accent:
                self.value_label.setObjectName(accent)

else:
    MetricBadge = None  # type: ignore[misc, assignment]
