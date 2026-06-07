"""Offscreen GUI control wiring tests (PySide6 required at runtime)."""

import copy
import os

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


def _mainwindow(config: AppConfig | None = None):
    from block_detected.apps.gui.app import MainWindow

    return MainWindow(config or AppConfig.defaults())


def test_mainwindow_defaults_idle_offscreen():
    _qapp()
    window = _mainwindow()
    assert window.frame_thread is None
    assert window.start_button.isEnabled()
    window.close()


def test_config_from_controls_round_trip():
    _qapp()
    window = _mainwindow()
    window.camera_index_spin.setValue(2)
    window.width_spin.setValue(1280)
    window.height_spin.setValue(720)
    window.conf_spin.setValue(0.42)
    window.stability_enabled_check.setChecked(True)
    window.stability_min_conf_spin.setValue(0.55)
    window.stability_window_spin.setValue(7)
    window.stability_votes_spin.setValue(4)

    config = window._config_from_controls()

    assert config.camera.index == 2
    assert config.camera.width == 1280
    assert config.camera.height == 720
    assert config.inference.default_conf == pytest.approx(0.42)
    assert config.stability.enabled is True
    assert config.stability.min_confidence == pytest.approx(0.55)
    assert config.stability.temporal_window == 7
    assert config.stability.required_stable_votes == 4
    window.close()


def test_hot_config_from_controls_stability_only():
    _qapp()
    window = _mainwindow()
    baseline = copy.deepcopy(window.config)
    window.camera_index_spin.setValue(baseline.camera.index + 1)
    window.stability_enabled_check.setChecked(True)
    window.stability_min_area_spin.setValue(500)

    hot = window._hot_config_from_controls()

    assert hot.camera.index == baseline.camera.index
    assert hot.stability.enabled is True
    assert hot.stability.min_box_area_px == 500
    window.close()


def test_restart_widgets_include_camera_model_log_level():
    _qapp()
    window = _mainwindow()
    names = {w.objectName() or type(w).__name__ for w in window._restart_widgets}
    assert window.camera_index_spin in window._restart_widgets
    assert window.model_name_edit in window._restart_widgets
    assert window.log_level_combo in window._restart_widgets
    assert len(window._restart_widgets) >= 6
    assert "QSpinBox" in names or window.camera_index_spin in window._restart_widgets
    window.close()
