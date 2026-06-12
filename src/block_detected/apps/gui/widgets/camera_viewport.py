"""Camera preview viewport with idle placeholder."""

from __future__ import annotations

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class CameraViewport(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("PreviewFrame")
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            container = QtWidgets.QWidget()
            inner = QtWidgets.QVBoxLayout(container)
            inner.setContentsMargins(0, 0, 0, 0)

            self.preview = QtWidgets.QLabel("Camera idle")
            self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.preview.setMinimumHeight(360)
            self.preview.setObjectName("Preview")
            inner.addWidget(self.preview, 1)

            self.preview_overlay = QtWidgets.QLabel("Model: — | Click NEXT MODEL or Start")
            self.preview_overlay.setObjectName("PreviewOverlay")
            inner.addWidget(self.preview_overlay, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

            layout.addWidget(container, 1)

else:
    CameraViewport = None  # type: ignore[misc, assignment]
