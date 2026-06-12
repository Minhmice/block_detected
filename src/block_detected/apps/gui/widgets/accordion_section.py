"""Collapsible accordion section for pipeline sidebar."""

from __future__ import annotations

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class AccordionSection(QtWidgets.QFrame):
        def __init__(self, title: str, parent=None, *, expanded: bool = True) -> None:
            super().__init__(parent)
            self.setObjectName("AccordionSection")
            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)

            self.toggle = QtWidgets.QPushButton(f"  {title}")
            self.toggle.setObjectName("AccordionToggle")
            self.toggle.setCheckable(True)
            self.toggle.setChecked(expanded)
            self.toggle.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            outer.addWidget(self.toggle)

            self.body = QtWidgets.QFrame()
            self.body.setObjectName("AccordionBody")
            self.body_layout = QtWidgets.QVBoxLayout(self.body)
            self.body_layout.setContentsMargins(12, 12, 12, 12)
            self.body_layout.setSpacing(10)
            outer.addWidget(self.body)
            self.body.setVisible(expanded)
            self.toggle.toggled.connect(self.body.setVisible)

        def add_widget(self, widget: QtWidgets.QWidget) -> None:
            self.body_layout.addWidget(widget)

        def add_layout(self, layout: QtWidgets.QLayout) -> None:
            self.body_layout.addLayout(layout)

else:
    AccordionSection = None  # type: ignore[misc, assignment]
