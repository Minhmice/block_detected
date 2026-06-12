"""PRIMARY DETECT panel — multi-detection scroll list."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from block_detected.core.domain import Detection

if QtWidgets is not None:

    class DetectionRow(QtWidgets.QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 6)
            layout.setSpacing(4)

            row = QtWidgets.QHBoxLayout()
            self.name_label = QtWidgets.QLabel("—")
            self.name_label.setObjectName("PrimaryDetectName")
            self.conf_label = QtWidgets.QLabel("—")
            self.conf_label.setObjectName("PrimaryDetectConf")
            row.addWidget(self.name_label)
            row.addStretch(1)
            row.addWidget(self.conf_label)
            layout.addLayout(row)

            self.bar = QtWidgets.QProgressBar()
            self.bar.setRange(0, 100)
            self.bar.setValue(0)
            self.bar.setTextVisible(False)
            self.bar.setFixedHeight(8)
            layout.addWidget(self.bar)

        def set_detection(self, detection: Any) -> None:
            name = detection.class_name.upper().replace(" ", "_")
            conf_pct = min(100, int(detection.confidence * 100))
            self.name_label.setText(name)
            self.conf_label.setText(f"{detection.confidence * 100:.1f}%")
            self.bar.setValue(conf_pct)

        def set_empty(self, message: str = "NO TARGET") -> None:
            self.name_label.setText(message)
            self.conf_label.setText("—")
            self.bar.setValue(0)

    class DetectionCard(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("Panel")
            self.setMinimumHeight(192)
            outer = QtWidgets.QVBoxLayout(self)
            outer.setSpacing(6)

            header = QtWidgets.QHBoxLayout()
            caps = QtWidgets.QLabel("PRIMARY DETECT")
            caps.setObjectName("CapsLabel")
            header.addWidget(caps)
            header.addStretch(1)
            self.count_badge = QtWidgets.QLabel("")
            self.count_badge.setObjectName("MetricMuted")
            header.addWidget(self.count_badge)
            outer.addLayout(header)

            self.scroll = QtWidgets.QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.list_host = QtWidgets.QWidget()
            self.list_layout = QtWidgets.QVBoxLayout(self.list_host)
            self.list_layout.setContentsMargins(0, 0, 4, 0)
            self.list_layout.setSpacing(2)
            self.list_layout.addStretch(1)
            self.scroll.setWidget(self.list_host)
            outer.addWidget(self.scroll, 1)

            self._rows: list[DetectionRow] = []
            self._first_row = DetectionRow()
            self.primary_name = self._first_row.name_label
            self.primary_conf = self._first_row.conf_label
            self.primary_bar = self._first_row.bar

        def update_detections(self, detections: list[Any]) -> None:
            while self.list_layout.count() > 1:
                item = self.list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._rows.clear()

            if not detections:
                self.count_badge.setText("")
                row = DetectionRow()
                row.set_empty()
                self.list_layout.insertWidget(0, row)
                self._rows.append(row)
                self.primary_name = row.name_label
                self.primary_conf = row.conf_label
                self.primary_bar = row.bar
                return

            count = len(detections)
            self.count_badge.setText(f"{count} target{'s' if count != 1 else ''}")
            for index, detection in enumerate(detections):
                row = DetectionRow()
                row.set_detection(detection)
                self.list_layout.insertWidget(index, row)
                self._rows.append(row)

            first = self._rows[0]
            self.primary_name = first.name_label
            self.primary_conf = first.conf_label
            self.primary_bar = first.bar

else:
    DetectionCard = None  # type: ignore[misc, assignment]
