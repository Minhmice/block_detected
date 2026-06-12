"""SYSTEM LOG panel with LIVE badge and tagged rows."""

from __future__ import annotations

import re

from block_detected.apps.gui.theme import COLORS

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:
    _TAG_COLORS = {
        "SYS": COLORS["text_muted"],
        "CAM": COLORS["secondary"],
        "INIT": COLORS["primary"],
        "OK": COLORS["secondary"],
        "DET": COLORS["primary"],
        "ERR": COLORS["error"],
    }
    _LOG_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+\[([A-Z]+)\]\s+(.*)$")

    class SystemLogCard(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("Panel")
            self.setMinimumHeight(192)
            layout = QtWidgets.QVBoxLayout(self)

            header = QtWidgets.QHBoxLayout()
            caps = QtWidgets.QLabel("SYSTEM LOG")
            caps.setObjectName("CapsLabel")
            header.addWidget(caps)
            header.addStretch(1)
            self.live_badge = QtWidgets.QLabel("● LIVE")
            self.live_badge.setObjectName("LiveBadge")
            self.live_badge.setVisible(False)
            header.addWidget(self.live_badge)
            layout.addLayout(header)

            self.log_list = QtWidgets.QListWidget()
            self.log_list.setObjectName("SystemLog")
            self.log_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            self.log_list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
            layout.addWidget(self.log_list)

            self._last_count = 0

        def set_live(self, active: bool) -> None:
            self.live_badge.setVisible(active)

        def update_lines(self, lines: list[str]) -> None:
            if len(lines) == self._last_count and lines:
                return
            self.log_list.clear()
            for line in lines[-200:]:
                item = QtWidgets.QListWidgetItem()
                widget = self._row_widget(line)
                item.setSizeHint(widget.sizeHint())
                self.log_list.addItem(item)
                self.log_list.setItemWidget(item, widget)
            self._last_count = len(lines)
            if self.log_list.count():
                self.log_list.scrollToBottom()

        def _row_widget(self, line: str) -> QtWidgets.QWidget:
            row = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(row)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(8)

            match = _LOG_RE.match(line)
            if match:
                stamp, tag, message = match.groups()
                time_lbl = QtWidgets.QLabel(stamp)
                time_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-family: monospace; font-size: 10px;")
                tag_lbl = QtWidgets.QLabel(tag)
                color = _TAG_COLORS.get(tag, COLORS["text_muted"])
                tag_lbl.setStyleSheet(
                    f"color: {color}; font-size: 9px; font-weight: 700; "
                    f"border: 1px solid {COLORS['outline']}; padding: 1px 4px; border-radius: 3px;"
                )
                msg_lbl = QtWidgets.QLabel(message)
                msg_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
                msg_lbl.setWordWrap(True)
                layout.addWidget(time_lbl, 0)
                layout.addWidget(tag_lbl, 0)
                layout.addWidget(msg_lbl, 1)
            else:
                plain = QtWidgets.QLabel(line)
                plain.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: monospace; font-size: 10px;")
                plain.setWordWrap(True)
                layout.addWidget(plain, 1)
            return row

else:
    SystemLogCard = None  # type: ignore[misc, assignment]
