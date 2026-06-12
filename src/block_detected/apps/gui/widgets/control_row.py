"""Slider + numeric input control row."""

from __future__ import annotations

from typing import Any, Callable

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class ControlRow(QtWidgets.QWidget):
        def __init__(
            self,
            label: str,
            *,
            spin: QtWidgets.QAbstractSpinBox,
            slider: QtWidgets.QSlider | None = None,
            parent=None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("ControlRow")
            layout = QtWidgets.QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            name = QtWidgets.QLabel(label)
            name.setObjectName("MetricMuted")
            name.setMinimumWidth(80)
            name.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Preferred,
                QtWidgets.QSizePolicy.Policy.Preferred,
            )
            layout.addWidget(name)
            self.slider = slider
            if slider is not None:
                slider.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding,
                    QtWidgets.QSizePolicy.Policy.Fixed,
                )
                layout.addWidget(slider, 1)
            self.spin = spin
            self.spin.setMinimumWidth(48)
            self.spin.setMaximumWidth(72)
            layout.addWidget(self.spin)

    def bind_slider_spin(
        slider: QtWidgets.QSlider,
        spin: QtWidgets.QAbstractSpinBox,
        *,
        scale: int = 1000,
        on_change: Callable[[], None] | None = None,
    ) -> tuple[Callable[[], None], Callable[[], None]]:
        """Two-way sync between slider integer steps and spin value."""
        syncing = {"active": False}

        def from_spin(value: float) -> None:
            if syncing["active"]:
                return
            syncing["active"] = True
            slider.setValue(int(value * scale))
            syncing["active"] = False
            if on_change:
                on_change()

        def from_slider(value: int) -> None:
            if syncing["active"]:
                return
            syncing["active"] = True
            spin.setValue(value / scale)
            syncing["active"] = False
            if on_change:
                on_change()

        spin.valueChanged.connect(from_spin)
        slider.valueChanged.connect(from_slider)
        return from_spin, from_slider

else:
    ControlRow = None  # type: ignore[misc, assignment]

    def bind_slider_spin(*_args: Any, **_kwargs: Any):
        raise RuntimeError("PySide6 required")
