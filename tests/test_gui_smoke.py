"""Optional offscreen GUI smoke test when PySide6 is installed."""

import os

import pytest

from block_detected.runtime.config_schema import AppConfig


def test_mainwindow_instantiates_offscreen_when_pyside_available():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6 import QtWidgets

    from block_detected.apps.gui.app import MainWindow

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    window = MainWindow(AppConfig.defaults())
    assert window.frame_thread is None
    assert window.start_button.isEnabled()
    window.close()


def test_refresh_logs_updates_log_view_from_get_log_lines():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6 import QtWidgets

    from block_detected.apps.gui.app import MainWindow

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    window = MainWindow(AppConfig.defaults())
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "block_detected.apps.gui.app.get_log_lines",
            lambda: ["INFO test line"],
        )
        window._refresh_logs()
    assert "test line" in window.log_view.toPlainText()
    window.close()
