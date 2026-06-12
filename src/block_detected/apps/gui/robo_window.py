"""Robo-Vision OS desktop shell — composed widget layout."""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import cv2

from block_detected.apps.gui.theme import ROBO_VISION_QSS
from block_detected.apps.gui.widgets import (
    CameraToolbar,
    CameraViewport,
    DetectionCard,
    HeaderBar,
    KinematicsCard,
    PipelineSidebar,
    SystemLogCard,
    bind_slider_spin,
)
from block_detected.apps.gui.worker import create_frame_thread
from block_detected.runtime.config_apply import apply_hot_runtime_settings, needs_runtime_restart
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import DEFAULT_CONFIG_PATH, load_config, save_config, validate_config
from block_detected.runtime.logging_setup import get_log_lines

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _frame_to_qimage(frame: Any) -> Any:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    return QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888).copy()


if QtCore is not None:
    FrameThread = create_frame_thread(QtCore)

    class RoboVisionWindow(QtWidgets.QMainWindow):
        """Desktop GUI matching Stitch Robo-Vision OS v2.4."""

        def __init__(self, config: AppConfig) -> None:
            super().__init__()
            self.config = copy.deepcopy(config)
            self.frame_thread: FrameThread | None = None
            self._run_generation = 0
            self._stopping = False
            self._running = False
            self._current_pixmap: QtGui.QPixmap | None = None
            self._last_log_count = 0
            self._syncing_conf = False

            self.setWindowTitle("ROBO-VISION OS v2.4")
            self.resize(1440, 900)
            self._build_ui()
            self._bind_slider_sync()
            self._load_controls(self.config)
            self._wire_events()
            self._apply_running_state(False)

            self.log_timer = QtCore.QTimer(self)
            self.log_timer.timeout.connect(self._refresh_logs)
            self.log_timer.start(400)

        def closeEvent(self, event) -> None:
            self._stop_engine()
            super().closeEvent(event)

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            self._update_preview_pixmap()
            sidebar_width = max(300, min(440, int(self.width() * 0.28)))
            self.sidebar.setFixedWidth(sidebar_width)

        # --- Public attrs used by tests ---
        @property
        def fps_label(self):
            return self.toolbar.fps_label

        @property
        def latency_label(self):
            return self.toolbar.latency_label

        @property
        def render_label(self):
            return self.toolbar.render_label

        @property
        def start_button(self):
            return self.header.start_button

        @property
        def camera_button(self):
            return self.header.camera_button

        @property
        def model_button(self):
            return self.header.model_button

        @property
        def restart_hint_label(self):
            return self.header.restart_hint_label

        @property
        def preview(self):
            return self.viewport.preview

        @property
        def preview_overlay(self):
            return self.viewport.preview_overlay

        @property
        def primary_name(self):
            return self.detection_card.primary_name

        @property
        def primary_conf(self):
            return self.detection_card.primary_conf

        @property
        def primary_bar(self):
            return self.detection_card.primary_bar

        @property
        def apply_button(self):
            return self.sidebar.apply_button

        @property
        def save_button(self):
            return self.sidebar.save_button

        @property
        def contours_check(self):
            return self.toolbar.contours_check

        @property
        def conf_spin(self):
            return self.sidebar.conf_spin

        @property
        def conf_slider(self):
            return self.sidebar.conf_slider

        @property
        def eval_check(self):
            return self.sidebar.eval_check

        @property
        def stability_enabled_check(self):
            return self.sidebar.stability_enabled_check

        @property
        def stability_min_conf_spin(self):
            return self.sidebar.stability_min_conf_spin

        @property
        def stability_min_area_spin(self):
            return self.sidebar.stability_min_area_spin

        @property
        def stability_dup_iou_spin(self):
            return self.sidebar.stability_dup_iou_spin

        @property
        def stability_window_spin(self):
            return self.sidebar.stability_window_spin

        @property
        def stability_votes_spin(self):
            return self.sidebar.stability_votes_spin

        @property
        def camera_index_spin(self):
            return self.sidebar.camera_index_spin

        @property
        def camera_max_spin(self):
            return self.sidebar.camera_max_spin

        @property
        def width_spin(self):
            return self.sidebar.width_spin

        @property
        def height_spin(self):
            return self.sidebar.height_spin

        @property
        def log_level_combo(self):
            return self.sidebar.log_level_combo

        @property
        def _restart_widgets(self):
            return [
                self.sidebar.camera_index_spin,
                self.sidebar.camera_max_spin,
                self.sidebar.width_spin,
                self.sidebar.height_spin,
                self.sidebar.log_level_combo,
                self.sidebar.imgsz_spin,
            ]

        def _build_ui(self) -> None:
            root = QtWidgets.QWidget()
            outer = QtWidgets.QVBoxLayout(root)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)

            self.header = HeaderBar()
            outer.addWidget(self.header)

            body = QtWidgets.QHBoxLayout()
            body.setContentsMargins(8, 8, 8, 8)
            body.setSpacing(8)

            left_col = QtWidgets.QVBoxLayout()
            left_col.setSpacing(8)

            preview_frame = QtWidgets.QWidget()
            preview_layout = QtWidgets.QVBoxLayout(preview_frame)
            preview_layout.setContentsMargins(0, 0, 0, 0)
            preview_layout.setSpacing(0)

            self.toolbar = CameraToolbar()
            preview_layout.addWidget(self.toolbar)
            self.viewport = CameraViewport()
            preview_layout.addWidget(self.viewport, 1)
            left_col.addWidget(preview_frame, 1)

            bottom = QtWidgets.QHBoxLayout()
            bottom.setSpacing(8)
            self.detection_card = DetectionCard()
            self.kinematics_card = KinematicsCard()
            self.log_card = SystemLogCard()
            bottom.addWidget(self.detection_card, 1)
            bottom.addWidget(self.kinematics_card, 1)
            bottom.addWidget(self.log_card, 1)
            left_col.addLayout(bottom)

            body.addLayout(left_col, 1)
            self.sidebar = PipelineSidebar()
            body.addWidget(self.sidebar)
            outer.addLayout(body, 1)

            self.setCentralWidget(root)
            self.setStyleSheet(ROBO_VISION_QSS)

        def _bind_slider_sync(self) -> None:
            sb = self.sidebar
            bind_slider_spin(sb.contrast_slider, sb.contrast_spin, scale=1000)
            bind_slider_spin(sb.brightness_slider, sb.brightness_spin, scale=1)
            bind_slider_spin(sb.saturation_slider, sb.saturation_spin, scale=1000)
            bind_slider_spin(
                sb.conf_slider,
                sb.conf_spin,
                scale=1000,
                on_change=lambda: self._on_conf_hot(),
            )
            bind_slider_spin(sb.nms_iou_slider, sb.nms_iou_spin, scale=100)
            bind_slider_spin(sb.imgsz_slider, sb.imgsz_spin, scale=1)
            bind_slider_spin(sb.max_det_slider, sb.max_det_spin, scale=1)
            bind_slider_spin(sb.canny_low_slider, sb.canny_low_spin, scale=1)
            bind_slider_spin(sb.canny_high_slider, sb.canny_high_spin, scale=1)
            bind_slider_spin(sb.stability_min_area_slider, sb.stability_min_area_spin, scale=1)
            bind_slider_spin(sb.stability_min_conf_slider, sb.stability_min_conf_spin, scale=1000)
            bind_slider_spin(sb.stability_dup_iou_slider, sb.stability_dup_iou_spin, scale=100)
            bind_slider_spin(sb.stability_window_slider, sb.stability_window_spin, scale=1)
            bind_slider_spin(sb.stability_votes_slider, sb.stability_votes_spin, scale=1)

        def _wire_events(self) -> None:
            self.header.start_button.clicked.connect(self._toggle_runtime)
            self.header.camera_button.clicked.connect(self._request_switch_camera)
            self.header.model_button.clicked.connect(self._request_switch_model)
            self.sidebar.apply_button.clicked.connect(self._apply_hot_config)
            self.sidebar.save_button.clicked.connect(self._save_config)
            self.sidebar.delete_button.clicked.connect(self._delete_config)

            self.toolbar.contours_check.toggled.connect(self._on_overlay_toggled)
            self.toolbar.corners_check.toggled.connect(self._on_overlay_toggled)
            self.sidebar.eval_check.toggled.connect(self._on_eval_changed)

            hot_widgets = [
                self.sidebar.contrast_spin,
                self.sidebar.brightness_spin,
                self.sidebar.saturation_spin,
                self.sidebar.nms_iou_spin,
                self.sidebar.max_det_spin,
                self.sidebar.agnostic_nms_check,
                self.sidebar.stability_enabled_check,
                self.sidebar.stability_min_conf_spin,
                self.sidebar.stability_min_area_spin,
                self.sidebar.stability_dup_iou_spin,
                self.sidebar.stability_window_spin,
                self.sidebar.stability_votes_spin,
                self.sidebar.blur_kernel_spin,
                self.sidebar.canny_low_spin,
                self.sidebar.canny_high_spin,
            ]
            for widget in hot_widgets:
                if isinstance(widget, QtWidgets.QAbstractSpinBox):
                    widget.valueChanged.connect(lambda _v: self._apply_hot_config())
                elif isinstance(widget, QtWidgets.QCheckBox):
                    widget.toggled.connect(lambda _c: self._apply_hot_config())

            for widget in self._restart_widgets:
                if isinstance(widget, QtWidgets.QAbstractSpinBox):
                    widget.valueChanged.connect(self._update_restart_hint)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    widget.textChanged.connect(self._update_restart_hint)
                elif isinstance(widget, QtWidgets.QComboBox):
                    widget.currentTextChanged.connect(self._update_restart_hint)

        def _load_controls(self, config: AppConfig) -> None:
            inf = config.inference
            self.sidebar.conf_spin.setRange(inf.conf_min, inf.conf_max)
            self.sidebar.conf_spin.setSingleStep(inf.conf_step)
            self.sidebar.conf_spin.setValue(inf.default_conf)
            self.sidebar.conf_slider.setRange(int(inf.conf_min * 1000), int(inf.conf_max * 1000))
            self.sidebar.conf_slider.setValue(int(inf.default_conf * 1000))
            self.sidebar.nms_iou_spin.setValue(inf.iou)
            self.sidebar.nms_iou_slider.setValue(int(inf.iou * 100))
            self.sidebar.imgsz_spin.setValue(inf.imgsz)
            self.sidebar.imgsz_slider.setValue(inf.imgsz)
            self.sidebar.max_det_spin.setValue(inf.max_det)
            self.sidebar.max_det_slider.setValue(inf.max_det)
            self.sidebar.agnostic_nms_check.setChecked(inf.agnostic_nms)
            self.sidebar.eval_check.setChecked(False)

            pp = config.preprocess
            self.sidebar.contrast_spin.setValue(pp.contrast)
            self.sidebar.contrast_slider.setValue(int(pp.contrast * 1000))
            self.sidebar.brightness_spin.setValue(pp.brightness)
            self.sidebar.brightness_slider.setValue(pp.brightness)
            self.sidebar.saturation_spin.setValue(pp.saturation)
            self.sidebar.saturation_slider.setValue(int(pp.saturation * 1000))

            cl = config.classical
            self.sidebar.blur_kernel_spin.setValue(cl.blur_kernel)
            self.sidebar.canny_low_spin.setValue(cl.canny_low)
            self.sidebar.canny_low_slider.setValue(cl.canny_low)
            self.sidebar.canny_high_spin.setValue(cl.canny_high)
            self.sidebar.canny_high_slider.setValue(cl.canny_high)
            self.toolbar.contours_check.setChecked(cl.show_contours)
            self.toolbar.corners_check.setChecked(cl.show_corners)

            self.sidebar.camera_index_spin.setValue(config.camera.index)
            self.sidebar.camera_max_spin.setValue(config.camera.max_index)
            self.sidebar.width_spin.setValue(config.camera.width)
            self.sidebar.height_spin.setValue(config.camera.height)
            self.sidebar.log_level_combo.setCurrentText(config.ui.log_level.upper())

            stab = config.stability
            self.sidebar.stability_enabled_check.setChecked(stab.enabled)
            self.sidebar.stability_min_conf_spin.setValue(stab.min_confidence)
            self.sidebar.stability_min_conf_slider.setValue(int(stab.min_confidence * 1000))
            self.sidebar.stability_min_area_spin.setValue(stab.min_box_area_px)
            self.sidebar.stability_min_area_slider.setValue(
                min(stab.min_box_area_px, self.sidebar.stability_min_area_slider.maximum())
            )
            self.sidebar.stability_dup_iou_spin.setValue(stab.duplicate_merge_iou)
            self.sidebar.stability_dup_iou_slider.setValue(int(stab.duplicate_merge_iou * 100))
            self.sidebar.stability_window_spin.setValue(stab.temporal_window)
            self.sidebar.stability_window_slider.setValue(stab.temporal_window)
            self.sidebar.stability_votes_spin.setValue(stab.required_stable_votes)
            self.sidebar.stability_votes_slider.setValue(stab.required_stable_votes)

        def _apply_preprocess_from_controls(self, config: AppConfig) -> None:
            pp = config.preprocess
            pp.contrast = self.sidebar.contrast_spin.value()
            pp.brightness = self.sidebar.brightness_spin.value()
            pp.saturation = self.sidebar.saturation_spin.value()

        def _apply_inference_from_controls(self, config: AppConfig) -> None:
            inf = config.inference
            inf.default_conf = self.sidebar.conf_spin.value()
            inf.iou = self.sidebar.nms_iou_spin.value()
            inf.imgsz = self.sidebar.imgsz_spin.value()
            inf.max_det = self.sidebar.max_det_spin.value()
            inf.agnostic_nms = self.sidebar.agnostic_nms_check.isChecked()

        def _apply_classical_from_controls(self, config: AppConfig) -> None:
            cl = config.classical
            cl.blur_kernel = self.sidebar.blur_kernel_spin.value()
            cl.canny_low = self.sidebar.canny_low_spin.value()
            cl.canny_high = self.sidebar.canny_high_spin.value()
            cl.show_contours = self.toolbar.contours_check.isChecked()
            cl.show_corners = self.toolbar.corners_check.isChecked()

        def _apply_stability_from_controls(self, config: AppConfig) -> None:
            stab = config.stability
            stab.enabled = self.sidebar.stability_enabled_check.isChecked()
            stab.min_confidence = self.sidebar.stability_min_conf_spin.value()
            stab.min_box_area_px = self.sidebar.stability_min_area_spin.value()
            stab.duplicate_merge_iou = self.sidebar.stability_dup_iou_spin.value()
            stab.temporal_window = self.sidebar.stability_window_spin.value()
            stab.required_stable_votes = min(
                self.sidebar.stability_votes_spin.value(),
                self.sidebar.stability_window_spin.value(),
            )

        def _config_from_controls(self) -> AppConfig:
            config = copy.deepcopy(self.config)
            config.camera.index = self.sidebar.camera_index_spin.value()
            config.camera.max_index = self.sidebar.camera_max_spin.value()
            config.camera.width = self.sidebar.width_spin.value()
            config.camera.height = self.sidebar.height_spin.value()
            config.ui.log_level = self.sidebar.log_level_combo.currentText()
            self._apply_inference_from_controls(config)
            self._apply_preprocess_from_controls(config)
            self._apply_classical_from_controls(config)
            self._apply_stability_from_controls(config)
            return config

        def _hot_config_from_controls(self) -> AppConfig:
            config = copy.deepcopy(self.config)
            self._apply_inference_from_controls(config)
            self._apply_preprocess_from_controls(config)
            self._apply_classical_from_controls(config)
            self._apply_stability_from_controls(config)
            return config

        def _toggle_runtime(self) -> None:
            if self._running or self._stopping:
                self._stop_engine()
            else:
                self._start_engine()

        def _start_engine(self) -> None:
            if self._stopping:
                return
            if self.frame_thread is not None and self.frame_thread.isRunning():
                return
            config = self._config_from_controls()
            errors = validate_config(config)
            if errors:
                self._show_errors(errors)
                return
            self.config = config
            self._run_generation += 1
            generation = self._run_generation
            thread = FrameThread(config, generation)
            thread.frame_ready.connect(
                lambda frame, status, gen=generation: self._on_frame_ready(frame, status, gen)
            )
            thread.error.connect(lambda message, gen=generation: self._on_worker_error(message, gen))
            thread.finished.connect(self._on_worker_finished)
            self.frame_thread = thread
            self._stopping = False
            thread.start()
            self._apply_running_state(True)
            self._update_restart_hint()

        def _stop_engine(self) -> None:
            if self.frame_thread is None:
                self._apply_running_state(False)
                return
            if self._stopping:
                return
            self._stopping = True
            self._apply_stopping_state()
            thread = self.frame_thread
            thread.stop()
            if not thread.wait(5000):
                self.restart_hint_label.setText("Stop pending — wait before Start")
                return
            if thread.isFinished():
                self._finalize_worker_stop(thread)

        def _apply_stopping_state(self) -> None:
            self.start_button.setEnabled(False)
            self.camera_button.setEnabled(False)
            self.model_button.setEnabled(False)

        def _finalize_worker_stop(self, thread: FrameThread) -> None:
            if thread is not self.frame_thread:
                return
            self.frame_thread = None
            self._stopping = False
            self._current_pixmap = None
            self.preview.setText("Camera idle")
            self._apply_running_state(False)
            self._update_restart_hint()
            self._reset_metrics()
            self.log_card.set_live(False)

        def _apply_running_state(self, running: bool) -> None:
            self._running = running and not self._stopping
            stopping = self._stopping
            can_start = not running and not stopping and (
                self.frame_thread is None or not self.frame_thread.isRunning()
            )
            if running and not stopping:
                self.start_button.setText("■ STOP")
                self.start_button.setObjectName("StopButton")
                self.start_button.setStyleSheet("")
                self.start_button.setEnabled(True)
            else:
                self.start_button.setText("▶ START")
                self.start_button.setObjectName("StartButton")
                self.start_button.setStyleSheet("")
                self.start_button.setEnabled(can_start)
            self.camera_button.setEnabled(running and not stopping)
            self.model_button.setEnabled(running and not stopping)
            for widget in self._restart_widgets:
                widget.setEnabled(not running and not stopping)
            self.log_card.set_live(running and not stopping)
            self.setStyleSheet(ROBO_VISION_QSS)

        def _on_worker_finished(self) -> None:
            thread = self.sender()
            if not isinstance(thread, FrameThread):
                return
            if thread is not self.frame_thread:
                return
            self._finalize_worker_stop(thread)

        def _on_worker_error(self, message: str, generation: int) -> None:
            if generation != self._run_generation:
                return
            logger.error("%s", message)
            QtWidgets.QMessageBox.critical(self, "Runtime error", message)
            if self.frame_thread is not None:
                self.frame_thread.stop()

        def _on_frame_ready(self, frame: Any, status: Any, generation: int) -> None:
            if generation != self._run_generation:
                return
            self._current_pixmap = QtGui.QPixmap.fromImage(_frame_to_qimage(frame))
            self._update_preview_pixmap()
            stats = status.stats
            latency = stats.frame_read_ms + stats.inference_ms
            self.fps_label.setText(f"{stats.fps:.1f}")
            self.latency_label.setText(f"{latency:.1f}ms")
            self.render_label.setText(f"{stats.render_ms:.1f}ms")
            self.preview_overlay.setText(
                f"Model: {status.model_name} | cam {status.camera_index} | "
                f"conf {status.confidence:.3f} | dets {status.detection_count}"
            )
            self.detection_card.update_detections(list(status.detections))

        def _reset_metrics(self) -> None:
            self.fps_label.setText("—")
            self.latency_label.setText("—")
            self.render_label.setText("—")
            self.preview_overlay.setText("Model: — | Click NEXT MODEL or Start")
            self.detection_card.update_detections([])

        def _update_preview_pixmap(self) -> None:
            if self._current_pixmap is None:
                return
            scaled = self._current_pixmap.scaled(
                self.preview.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.preview.setPixmap(scaled)

        def _on_conf_hot(self) -> None:
            if self.frame_thread is not None:
                self.frame_thread.set_confidence(self.sidebar.conf_spin.value())

        def _on_eval_changed(self, checked: bool) -> None:
            if self.frame_thread is not None:
                self.frame_thread.set_eval_mode(checked)

        def _on_overlay_toggled(self, _checked: bool) -> None:
            self._apply_hot_config()

        def _apply_hot_config(self) -> None:
            config = self._hot_config_from_controls()
            errors = validate_config(config)
            if errors:
                self._show_errors(errors)
                return
            self.config.inference.default_conf = config.inference.default_conf
            self.config.inference.iou = config.inference.iou
            self.config.inference.max_det = config.inference.max_det
            self.config.inference.agnostic_nms = config.inference.agnostic_nms
            self.config.preprocess = copy.deepcopy(config.preprocess)
            self.config.classical = copy.deepcopy(config.classical)
            self.config.stability = copy.deepcopy(config.stability)
            if self.frame_thread is not None:
                self.frame_thread.apply_hot_config(config)
                self.frame_thread.set_confidence(self.sidebar.conf_spin.value())
                self.frame_thread.set_eval_mode(self.sidebar.eval_check.isChecked())
            logger.info("Applied vision pipeline hot config.")

        def _save_config(self) -> None:
            config = self._config_from_controls()
            errors = validate_config(config)
            if errors:
                self._show_errors(errors)
                return
            previous = copy.deepcopy(self.config)
            self.config = config
            save_config(config)
            logger.info("Saved config: %s", DEFAULT_CONFIG_PATH)
            running = self.frame_thread is not None and self.frame_thread.isRunning()
            if running and needs_runtime_restart(config, previous):
                QtWidgets.QMessageBox.information(
                    self,
                    "Config saved",
                    f"Saved to {DEFAULT_CONFIG_PATH}.\n\n"
                    "Camera, image size, and default model apply on the next Start.",
                )
            self._update_restart_hint()

        def _delete_config(self) -> None:
            answer = QtWidgets.QMessageBox.question(
                self,
                "Delete config",
                "Reset all settings to defaults and remove block_detected.toml?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            if Path(DEFAULT_CONFIG_PATH).exists():
                Path(DEFAULT_CONFIG_PATH).unlink()
            self.config = AppConfig.defaults()
            self._load_controls(self.config)
            if self.frame_thread is not None and self.frame_thread.isRunning():
                self.frame_thread.apply_hot_config(self._hot_config_from_controls())
            logger.info("Config reset to defaults.")

        def _update_restart_hint(self) -> None:
            if self.frame_thread is None or not self.frame_thread.isRunning():
                self.restart_hint_label.setText("")
                return
            current = self._config_from_controls()
            if needs_runtime_restart(current, self.config):
                self.restart_hint_label.setText("Restart required for camera/model/imgsz changes")
            else:
                self.restart_hint_label.setText("")

        def _request_switch_model(self) -> None:
            if self.frame_thread is not None:
                self.frame_thread.request_switch_model()

        def _request_switch_camera(self) -> None:
            if self.frame_thread is not None:
                self.frame_thread.request_switch_camera()

        def _refresh_logs(self) -> None:
            lines = get_log_lines()
            if len(lines) == self._last_log_count:
                return
            self._last_log_count = len(lines)
            self.log_card.update_lines(lines)

        def _show_errors(self, errors: list[str]) -> None:
            QtWidgets.QMessageBox.warning(self, "Invalid config", "\n".join(errors))

    MainWindow = RoboVisionWindow
else:
    RoboVisionWindow = None  # type: ignore[misc, assignment]
    MainWindow = None  # type: ignore[misc, assignment]
