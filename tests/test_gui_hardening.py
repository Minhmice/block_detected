"""GUI worker lifecycle, generation guards, and restart-hint tests."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from block_detected.runtime.config_schema import AppConfig


def _qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6 import QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def _mainwindow():
    from block_detected.apps.gui.app import MainWindow

    return MainWindow(AppConfig.defaults())


def test_stale_frame_ready_ignored():
    _qapp()
    from PySide6 import QtGui

    window = _mainwindow()
    window._run_generation = 2
    before = window.fps_label.text()
    image = QtGui.QImage(4, 4, QtGui.QImage.Format.Format_RGB888)
    status = MagicMock(
        stats=MagicMock(fps=0.0, frame_read_ms=0.0, inference_ms=0.0, render_ms=0.0),
        model_name="fake.pt",
        camera_index=0,
        confidence=0.5,
        eval_mode=False,
        stability_enabled=False,
        detection_count=0,
    )
    window._on_frame_ready(image, status, generation=1)
    assert window.fps_label.text() == before
    assert window._current_pixmap is None
    window.close()


def test_stale_worker_error_does_not_show_dialog():
    _qapp()
    from PySide6 import QtWidgets

    window = _mainwindow()
    window._run_generation = 1
    with patch.object(QtWidgets.QMessageBox, "critical") as critical:
        window._on_worker_error("fail", generation=0)
        critical.assert_not_called()
    window.close()


def test_stop_pending_disables_start():
    _qapp()
    window = _mainwindow()
    window._stopping = True
    window.frame_thread = MagicMock(isRunning=lambda: True)
    window._apply_running_state(False)
    assert not window.start_button.isEnabled()
    window.close()


def test_finalize_worker_stop_clears_thread_and_status():
    _qapp()
    window = _mainwindow()
    thread = MagicMock()
    window.frame_thread = thread
    window._stopping = True
    window._finalize_worker_stop(thread)
    assert window.frame_thread is None
    assert window._stopping is False
    assert window.start_button.text() == "▶ START"
    window.close()


def test_finalize_worker_stop_ignores_non_current_thread():
    _qapp()
    window = _mainwindow()
    current = MagicMock()
    other = MagicMock()
    window.frame_thread = current
    window._finalize_worker_stop(other)
    assert window.frame_thread is current
    window.close()


def test_restart_hint_when_camera_index_differs_while_running():
    _qapp()
    window = _mainwindow()
    window.config.camera.index = 0
    window.frame_thread = MagicMock(isRunning=lambda: True)
    window.camera_index_spin.setValue(1)
    window._update_restart_hint()
    assert window.restart_hint_label.text() != ""
    window.close()


def test_frame_thread_shutdown_uses_destroy_cv_windows_false():
    source = Path(__file__).resolve().parents[1] / "src" / "block_detected" / "apps" / "gui" / "worker.py"
    text = source.read_text(encoding="utf-8")
    assert "destroy_cv_windows=False" in text
