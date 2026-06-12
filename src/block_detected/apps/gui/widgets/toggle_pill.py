"""Toggle pill widget for viewport toolbar."""

from __future__ import annotations

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class TogglePill(QtWidgets.QCheckBox):
        def __init__(self, label: str, parent=None) -> None:
            super().__init__(label, parent)
            self.setObjectName("TogglePill")

else:
    TogglePill = None  # type: ignore[misc, assignment]
