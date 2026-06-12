"""Top header bar with brand and action buttons."""

from __future__ import annotations

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class HeaderBar(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("HeaderBar")
            self.setFixedHeight(72)
            layout = QtWidgets.QHBoxLayout(self)
            layout.setContentsMargins(24, 12, 24, 12)

            self.brand = QtWidgets.QLabel("ROBO-VISION OS v2.4")
            self.brand.setObjectName("BrandTitle")
            layout.addWidget(self.brand)
            layout.addStretch(1)

            self.restart_hint_label = QtWidgets.QLabel("")
            self.restart_hint_label.setObjectName("RestartHint")
            layout.addWidget(self.restart_hint_label)

            self.camera_button = QtWidgets.QPushButton("NEXT CAMERA")
            self.camera_button.setObjectName("NavButton")
            self.model_button = QtWidgets.QPushButton("NEXT MODEL")
            self.model_button.setObjectName("NavButton")
            self.start_button = QtWidgets.QPushButton("▶ START")
            self.start_button.setObjectName("StartButton")
            self.start_button.setFixedWidth(130)

            layout.addWidget(self.camera_button)
            layout.addWidget(self.model_button)
            layout.addWidget(self.start_button)

else:
    HeaderBar = None  # type: ignore[misc, assignment]
