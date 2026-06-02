"""PySide6 desktop GUI for webcam runtime tuning."""

from __future__ import annotations

import copy
import logging
import sys
import threading
from pathlib import Path
from typing import Any

import cv2

from block_detected.runtime.config_apply import apply_hot_runtime_settings, needs_runtime_restart
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import DEFAULT_CONFIG_PATH, load_config, save_config, validate_config
from block_detected.runtime.engine import WebcamEngine
from block_detected.runtime.logging_setup import get_log_lines, setup_logging

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

    class FrameThread(QtCore.QThread):
        frame_ready = QtCore.Signal(object, object)
        error = QtCore.Signal(str)

        def __init__(self, config: AppConfig, generation: int) -> None:
            super().__init__()
            self.generation = generation
            self._config = copy.deepcopy(config)
            self._stop = threading.Event()
            self._lock = threading.Lock()
            self._pending_conf: float | None = None
            self._pending_overlay: bool | None = None
            self._pending_eval: bool | None = None
            self._pending_hot_config: AppConfig | None = None
            self._switch_model_requested = False
            self._switch_camera_requested = False

        def run(self) -> None:
            engine, create_error = WebcamEngine.try_create(self._config)
            if engine is None:
                self.error.emit(create_error or "Failed to create webcam engine.")
                return
            started, start_error = engine.try_start()
            if not started:
                self.error.emit(start_error or "Failed to open camera source.")
                engine.shutdown(destroy_cv_windows=False)
                return

            try:
                while not self._stop.is_set():
                    self._apply_pending(engine)
                    processed = engine.process_frame()
                    if processed is None:
                        break
                    self.frame_ready.emit(_frame_to_qimage(processed.annotated), processed.status)
                    self.msleep(1)
            finally:
                engine.shutdown(destroy_cv_windows=False)

        def stop(self) -> None:
            self._stop.set()

        def set_confidence(self, value: float) -> None:
            with self._lock:
                self._pending_conf = value

        def set_overlay_enabled(self, value: bool) -> None:
            with self._lock:
                self._pending_overlay = value

        def set_eval_mode(self, value: bool) -> None:
            with self._lock:
                self._pending_eval = value

        def apply_hot_config(self, config: AppConfig) -> None:
            with self._lock:
                self._pending_hot_config = copy.deepcopy(config)

        def request_switch_model(self) -> None:
            with self._lock:
                self._switch_model_requested = True

        def request_switch_camera(self) -> None:
            with self._lock:
                self._switch_camera_requested = True

        def _apply_pending(self, engine: WebcamEngine) -> None:
            with self._lock:
                conf = self._pending_conf
                overlay = self._pending_overlay
                eval_mode = self._pending_eval
                hot_config = self._pending_hot_config
                switch_model_requested = self._switch_model_requested
                switch_camera_requested = self._switch_camera_requested
                self._pending_conf = None
                self._pending_overlay = None
                self._pending_eval = None
                self._pending_hot_config = None
                self._switch_model_requested = False
                self._switch_camera_requested = False

            if hot_config is not None or conf is not None or overlay is not None or eval_mode is not None:
                apply_hot_runtime_settings(
                    engine,
                    hot_config if hot_config is not None else engine.config,
                    confidence=conf if conf is not None else engine.state.confidence,
                    eval_mode=eval_mode if eval_mode is not None else engine.state.eval_mode,
                    overlay_enabled=overlay if overlay is not None else engine.state.overlay_enabled,
                )
            if switch_model_requested:
                engine.switch_model()
            if switch_camera_requested:
                engine.switch_camera()


    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, config: AppConfig) -> None:
            super().__init__()
            self.config = copy.deepcopy(config)
            self.frame_thread: FrameThread | None = None
            self._run_generation = 0
            self._stopping = False
            self._current_pixmap: QtGui.QPixmap | None = None
            self._last_log_text = ""
            self._syncing_conf = False
            self._restart_widgets: list[Any] = []

            self.setWindowTitle("Block Detected Control")
            self.resize(1280, 820)
            self._build_ui()
            self._load_controls(self.config)
            self._wire_events()
            self._apply_running_state(False)

            self.log_timer = QtCore.QTimer(self)
            self.log_timer.timeout.connect(self._refresh_logs)
            self.log_timer.start(500)

        def closeEvent(self, event) -> None:
            self._stop_engine()
            super().closeEvent(event)

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            self._update_preview_pixmap()

        def _build_ui(self) -> None:
            root = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(root)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(10)

            header = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel("Block Detected")
            title.setObjectName("Title")
            self.status_label = QtWidgets.QLabel("Idle")
            self.status_label.setObjectName("Status")
            self.restart_hint_label = QtWidgets.QLabel("")
            self.restart_hint_label.setObjectName("RestartHint")
            header.addWidget(title)
            header.addStretch(1)
            header_col = QtWidgets.QVBoxLayout()
            header_col.addWidget(self.status_label, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
            header_col.addWidget(self.restart_hint_label, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
            header.addLayout(header_col)
            layout.addLayout(header)

            splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            self.preview = QtWidgets.QLabel("Preview idle")
            self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.preview.setMinimumSize(720, 420)
            self.preview.setObjectName("Preview")
            splitter.addWidget(self.preview)
            splitter.addWidget(self._build_controls())
            splitter.setSizes([860, 360])
            layout.addWidget(splitter, 1)

            self.log_view = QtWidgets.QPlainTextEdit()
            self.log_view.setReadOnly(True)
            self.log_view.setMaximumBlockCount(500)
            self.log_view.setMinimumHeight(150)
            self.log_view.setObjectName("LogView")
            layout.addWidget(self.log_view)

            self.setCentralWidget(root)
            self.setStyleSheet(_stylesheet())

        def _build_controls(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QWidget()
            panel.setObjectName("Inspector")
            layout = QtWidgets.QVBoxLayout(panel)
            layout.setContentsMargins(10, 0, 0, 0)
            layout.setSpacing(12)

            runtime = QtWidgets.QGroupBox("Runtime")
            runtime_layout = QtWidgets.QGridLayout(runtime)
            self.start_button = QtWidgets.QPushButton("Start")
            self.stop_button = QtWidgets.QPushButton("Stop")
            self.model_button = QtWidgets.QPushButton("Next model")
            self.camera_button = QtWidgets.QPushButton("Next camera")
            runtime_layout.addWidget(self.start_button, 0, 0)
            runtime_layout.addWidget(self.stop_button, 0, 1)
            runtime_layout.addWidget(self.model_button, 1, 0)
            runtime_layout.addWidget(self.camera_button, 1, 1)
            layout.addWidget(runtime)

            inference = QtWidgets.QGroupBox("Inference")
            inf_layout = QtWidgets.QFormLayout(inference)
            self.conf_spin = QtWidgets.QDoubleSpinBox()
            self.conf_spin.setDecimals(3)
            self.conf_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.eval_check = QtWidgets.QCheckBox("Eval mode")
            self.overlay_check = QtWidgets.QCheckBox("Overlay trail")
            self.overlay_history_spin = QtWidgets.QSpinBox()
            self.overlay_history_spin.setRange(1, 120)
            self.show_fps_check = QtWidgets.QCheckBox("Show FPS in preview")
            inf_layout.addRow("Confidence", self.conf_spin)
            inf_layout.addRow("", self.conf_slider)
            inf_layout.addRow(self.eval_check)
            inf_layout.addRow(self.overlay_check)
            inf_layout.addRow("Trail frames", self.overlay_history_spin)
            inf_layout.addRow(self.show_fps_check)
            layout.addWidget(inference)

            stability = QtWidgets.QGroupBox("Stability")
            stab_layout = QtWidgets.QFormLayout(stability)
            self.stability_enabled_check = QtWidgets.QCheckBox("Enable stability")
            self.stability_min_conf_spin = QtWidgets.QDoubleSpinBox()
            self.stability_min_conf_spin.setDecimals(3)
            self.stability_min_conf_spin.setRange(0.0, 1.0)
            self.stability_min_conf_spin.setSingleStep(0.05)
            self.stability_min_area_spin = QtWidgets.QSpinBox()
            self.stability_min_area_spin.setRange(0, 2_000_000)
            self.stability_reject_edge_check = QtWidgets.QCheckBox("Reject edge boxes")
            self.stability_dup_iou_spin = QtWidgets.QDoubleSpinBox()
            self.stability_dup_iou_spin.setDecimals(2)
            self.stability_dup_iou_spin.setRange(0.01, 1.0)
            self.stability_dup_iou_spin.setSingleStep(0.05)
            self.stability_window_spin = QtWidgets.QSpinBox()
            self.stability_window_spin.setRange(1, 120)
            self.stability_votes_spin = QtWidgets.QSpinBox()
            self.stability_votes_spin.setRange(1, 120)
            stab_layout.addRow(self.stability_enabled_check)
            stab_layout.addRow("Min confidence", self.stability_min_conf_spin)
            stab_layout.addRow("Min area (px²)", self.stability_min_area_spin)
            stab_layout.addRow(self.stability_reject_edge_check)
            stab_layout.addRow("Duplicate IoU", self.stability_dup_iou_spin)
            stab_layout.addRow("Temporal window", self.stability_window_spin)
            stab_layout.addRow("Required votes", self.stability_votes_spin)
            layout.addWidget(stability)

            camera = QtWidgets.QGroupBox("Camera")
            camera_layout = QtWidgets.QFormLayout(camera)
            self.camera_index_spin = QtWidgets.QSpinBox()
            self.camera_index_spin.setRange(0, 32)
            self.camera_max_spin = QtWidgets.QSpinBox()
            self.camera_max_spin.setRange(0, 32)
            self.width_spin = QtWidgets.QSpinBox()
            self.width_spin.setRange(1, 7680)
            self.height_spin = QtWidgets.QSpinBox()
            self.height_spin.setRange(1, 4320)
            camera_layout.addRow("Index", self.camera_index_spin)
            camera_layout.addRow("Max index", self.camera_max_spin)
            camera_layout.addRow("Width", self.width_spin)
            camera_layout.addRow("Height", self.height_spin)
            layout.addWidget(camera)

            config_box = QtWidgets.QGroupBox("Config")
            config_layout = QtWidgets.QFormLayout(config_box)
            self.model_name_edit = QtWidgets.QLineEdit()
            self.detector_label = QtWidgets.QLabel("YOLO (Ultralytics)")
            self.detector_label.setObjectName("DetectorLabel")
            self.log_level_combo = QtWidgets.QComboBox()
            self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            self.apply_button = QtWidgets.QPushButton("Apply hot config")
            self.save_button = QtWidgets.QPushButton("Save TOML")
            config_layout.addRow("Default model", self.model_name_edit)
            config_layout.addRow("Detector", self.detector_label)
            config_layout.addRow("Log level", self.log_level_combo)
            config_layout.addRow(self.apply_button)
            config_layout.addRow(self.save_button)
            layout.addWidget(config_box)

            self._restart_widgets = [
                self.camera_index_spin,
                self.camera_max_spin,
                self.width_spin,
                self.height_spin,
                self.model_name_edit,
                self.log_level_combo,
            ]
            layout.addStretch(1)
            return panel

        def _wire_events(self) -> None:
            self.start_button.clicked.connect(self._start_engine)
            self.stop_button.clicked.connect(self._stop_engine)
            self.model_button.clicked.connect(self._request_switch_model)
            self.camera_button.clicked.connect(self._request_switch_camera)
            self.apply_button.clicked.connect(self._apply_hot_config)
            self.save_button.clicked.connect(self._save_config)
            self.conf_spin.valueChanged.connect(self._on_conf_spin_changed)
            self.conf_slider.valueChanged.connect(self._on_conf_slider_changed)
            self.eval_check.toggled.connect(self._on_eval_changed)
            self.overlay_check.toggled.connect(self._on_overlay_changed)
            self.show_fps_check.toggled.connect(lambda _checked: self._apply_hot_config())
            self.overlay_history_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            self.stability_enabled_check.toggled.connect(lambda _checked: self._apply_hot_config())
            self.stability_min_conf_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            self.stability_min_area_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            self.stability_reject_edge_check.toggled.connect(lambda _checked: self._apply_hot_config())
            self.stability_dup_iou_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            self.stability_window_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            self.stability_votes_spin.valueChanged.connect(lambda _value: self._apply_hot_config())
            for widget in self._restart_widgets:
                if isinstance(widget, QtWidgets.QAbstractSpinBox):
                    widget.valueChanged.connect(self._update_restart_hint)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    widget.textChanged.connect(self._update_restart_hint)
                elif isinstance(widget, QtWidgets.QComboBox):
                    widget.currentTextChanged.connect(self._update_restart_hint)

        def _load_controls(self, config: AppConfig) -> None:
            inf = config.inference
            self.conf_spin.setRange(inf.conf_min, inf.conf_max)
            self.conf_spin.setSingleStep(inf.conf_step)
            self.conf_spin.setValue(inf.default_conf)
            self.conf_slider.setRange(int(inf.conf_min * 1000), int(inf.conf_max * 1000))
            self.conf_slider.setValue(int(inf.default_conf * 1000))
            self.eval_check.setChecked(False)
            self.overlay_check.setChecked(True)
            self.overlay_history_spin.setValue(inf.overlay_history)
            self.show_fps_check.setChecked(config.ui.show_fps_in_status)
            self.camera_index_spin.setValue(config.camera.index)
            self.camera_max_spin.setValue(config.camera.max_index)
            self.width_spin.setValue(config.camera.width)
            self.height_spin.setValue(config.camera.height)
            self.model_name_edit.setText(config.inference.default_model_name)
            self.log_level_combo.setCurrentText(config.ui.log_level.upper())
            stab = config.stability
            self.stability_enabled_check.setChecked(stab.enabled)
            self.stability_min_conf_spin.setValue(stab.min_confidence)
            self.stability_min_area_spin.setValue(stab.min_box_area_px)
            self.stability_reject_edge_check.setChecked(stab.reject_edge_boxes)
            self.stability_dup_iou_spin.setValue(stab.duplicate_merge_iou)
            self.stability_window_spin.setValue(stab.temporal_window)
            self.stability_votes_spin.setValue(stab.required_stable_votes)

        def _apply_stability_from_controls(self, config: AppConfig) -> None:
            stab = config.stability
            stab.enabled = self.stability_enabled_check.isChecked()
            stab.min_confidence = self.stability_min_conf_spin.value()
            stab.min_box_area_px = self.stability_min_area_spin.value()
            stab.reject_edge_boxes = self.stability_reject_edge_check.isChecked()
            stab.duplicate_merge_iou = self.stability_dup_iou_spin.value()
            stab.temporal_window = self.stability_window_spin.value()
            stab.required_stable_votes = min(
                self.stability_votes_spin.value(),
                self.stability_window_spin.value(),
            )

        def _config_from_controls(self) -> AppConfig:
            config = copy.deepcopy(self.config)
            config.camera.index = self.camera_index_spin.value()
            config.camera.max_index = self.camera_max_spin.value()
            config.camera.width = self.width_spin.value()
            config.camera.height = self.height_spin.value()
            config.inference.default_conf = self.conf_spin.value()
            config.inference.overlay_history = self.overlay_history_spin.value()
            config.inference.default_model_name = self.model_name_edit.text().strip()
            config.ui.show_fps_in_status = self.show_fps_check.isChecked()
            config.ui.log_level = self.log_level_combo.currentText()
            self._apply_stability_from_controls(config)
            return config

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
                lambda image, status, gen=generation: self._on_frame_ready(image, status, gen)
            )
            thread.error.connect(lambda message, gen=generation: self._on_worker_error(message, gen))
            thread.finished.connect(self._on_worker_finished)
            self.frame_thread = thread
            self._stopping = False
            thread.start()
            self._apply_running_state(True)
            self._update_restart_hint()
            self.status_label.setText("Starting")

        def _stop_engine(self) -> None:
            if self.frame_thread is None:
                return
            if self._stopping:
                return
            self._stopping = True
            self._apply_stopping_state()
            thread = self.frame_thread
            thread.stop()
            if not thread.wait(5000):
                self.status_label.setText("Stop pending — wait before Start")
                return
            if thread.isFinished():
                self._finalize_worker_stop(thread)

        def _apply_stopping_state(self) -> None:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.model_button.setEnabled(False)
            self.camera_button.setEnabled(False)
            self.status_label.setText("Stopping…")

        def _finalize_worker_stop(self, thread: FrameThread) -> None:
            if thread is not self.frame_thread:
                return
            self.frame_thread = None
            self._stopping = False
            self._current_pixmap = None
            self.preview.setText("Preview idle")
            self._apply_running_state(False)
            self._update_restart_hint()
            self.status_label.setText("Stopped")

        def _apply_running_state(self, running: bool) -> None:
            stopping = self._stopping
            can_start = not running and not stopping and (
                self.frame_thread is None or not self.frame_thread.isRunning()
            )
            self.start_button.setEnabled(can_start)
            self.stop_button.setEnabled(running or stopping)
            self.model_button.setEnabled(running and not stopping)
            self.camera_button.setEnabled(running and not stopping)
            for widget in self._restart_widgets:
                widget.setEnabled(not running and not stopping)
            restart_hint = " (restart required)" if running else ""
            self.camera_index_spin.setToolTip(f"Camera index{restart_hint}")
            self.camera_max_spin.setToolTip(f"Max camera index to scan{restart_hint}")
            self.width_spin.setToolTip(f"Resolution width{restart_hint}")
            self.height_spin.setToolTip(f"Resolution height{restart_hint}")
            self.model_name_edit.setToolTip(f"Default model on next Start{restart_hint}")
            self.log_level_combo.setToolTip(f"Log level (restart required while running){restart_hint}")

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
            self.status_label.setText("Error")
            QtWidgets.QMessageBox.critical(self, "Runtime error", message)
            if self.frame_thread is not None:
                self.frame_thread.stop()

        def _on_frame_ready(self, image: Any, status: Any, generation: int) -> None:
            if generation != self._run_generation:
                return
            self._current_pixmap = QtGui.QPixmap.fromImage(image)
            self._update_preview_pixmap()
            stats = status.stats
            self.status_label.setText(
                f"model {status.model_name} | cam {status.camera_index} | "
                f"conf {status.confidence:.3f} | eval {'on' if status.eval_mode else 'off'} | "
                f"overlay {'on' if status.overlay_enabled else 'off'} | "
                f"stab {'on' if status.stability_enabled else 'off'} | "
                f"dets {status.detection_count} | "
                f"fps {stats.fps:.1f} | read {stats.frame_read_ms:.1f}ms | "
                f"infer {stats.inference_ms:.1f}ms | render {stats.render_ms:.1f}ms"
            )

        def _update_preview_pixmap(self) -> None:
            if self._current_pixmap is None:
                return
            scaled = self._current_pixmap.scaled(
                self.preview.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.preview.setPixmap(scaled)

        def _on_conf_spin_changed(self, value: float) -> None:
            if self._syncing_conf:
                return
            self._syncing_conf = True
            self.conf_slider.setValue(int(value * 1000))
            self._syncing_conf = False
            if self.frame_thread is not None:
                self.frame_thread.set_confidence(value)

        def _on_conf_slider_changed(self, value: int) -> None:
            if self._syncing_conf:
                return
            conf = value / 1000.0
            self._syncing_conf = True
            self.conf_spin.setValue(conf)
            self._syncing_conf = False
            if self.frame_thread is not None:
                self.frame_thread.set_confidence(conf)

        def _on_eval_changed(self, checked: bool) -> None:
            if self.frame_thread is not None:
                self.frame_thread.set_eval_mode(checked)

        def _on_overlay_changed(self, checked: bool) -> None:
            if self.frame_thread is not None:
                self.frame_thread.set_overlay_enabled(checked)

        def _hot_config_from_controls(self) -> AppConfig:
            config = copy.deepcopy(self.config)
            config.inference.overlay_history = self.overlay_history_spin.value()
            config.ui.show_fps_in_status = self.show_fps_check.isChecked()
            self._apply_stability_from_controls(config)
            return config

        def _apply_hot_config(self) -> None:
            config = self._hot_config_from_controls()
            errors = validate_config(config)
            if errors:
                self._show_errors(errors)
                return
            self.config.inference.overlay_history = config.inference.overlay_history
            self.config.ui.show_fps_in_status = config.ui.show_fps_in_status
            self.config.stability = copy.deepcopy(config.stability)
            if self.frame_thread is not None:
                self.frame_thread.apply_hot_config(config)
                self.frame_thread.set_confidence(self.conf_spin.value())
                self.frame_thread.set_eval_mode(self.eval_check.isChecked())
                self.frame_thread.set_overlay_enabled(self.overlay_check.isChecked())
            logger.info(
                "Applied hot config (confidence, eval, overlay, trail, FPS, stability)."
            )

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
                    "Camera and default model fields apply on the next Start.",
                )
            self._update_restart_hint()

        def _update_restart_hint(self) -> None:
            if self.frame_thread is None or not self.frame_thread.isRunning():
                self.restart_hint_label.setText("")
                return
            current = self._config_from_controls()
            needs_restart = needs_runtime_restart(current, self.config)
            if needs_restart:
                self.restart_hint_label.setText("Restart required for camera/model changes")
            else:
                self.restart_hint_label.setText("")

        def _request_switch_model(self) -> None:
            if self.frame_thread is not None:
                self.frame_thread.request_switch_model()

        def _request_switch_camera(self) -> None:
            if self.frame_thread is not None:
                self.frame_thread.request_switch_camera()

        def _refresh_logs(self) -> None:
            text = "\n".join(get_log_lines())
            if text == self._last_log_text:
                return
            self._last_log_text = text
            self.log_view.setPlainText(text)
            self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

        def _show_errors(self, errors: list[str]) -> None:
            QtWidgets.QMessageBox.warning(self, "Invalid config", "\n".join(errors))


def _stylesheet() -> str:
    return """
    QWidget {
        background: #101214;
        color: #e6e8eb;
        font-family: "Inter", "SF Pro Text", Arial, sans-serif;
        font-size: 13px;
    }
    QLabel#Title {
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#Status {
        color: #9aa4b2;
        font-size: 11px;
    }
    QLabel#RestartHint {
        color: #e8a84a;
        font-size: 11px;
    }
    QLabel#DetectorLabel {
        color: #cfd5dd;
        padding: 4px 0;
    }
    QLabel#Preview {
        background: #050607;
        border: 1px solid #242a31;
        border-radius: 6px;
        color: #667085;
    }
    QWidget#Inspector {
        background: #101214;
    }
    QGroupBox {
        border: 1px solid #252b33;
        border-radius: 6px;
        margin-top: 10px;
        padding: 10px 8px 8px 8px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #cfd5dd;
    }
    QPushButton {
        background: #1b222a;
        border: 1px solid #303945;
        border-radius: 5px;
        padding: 7px 10px;
    }
    QPushButton:hover {
        background: #26313c;
    }
    QPushButton:disabled {
        color: #606a75;
        background: #15191e;
    }
    QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
        background: #0b0d10;
        border: 1px solid #2b333d;
        border-radius: 4px;
        padding: 5px;
        min-height: 24px;
    }
    QCheckBox {
        spacing: 8px;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #2a313a;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 14px;
        margin: -5px 0;
        border-radius: 7px;
        background: #36c28f;
    }
    QPlainTextEdit#LogView {
        background: #07090b;
        border: 1px solid #242a31;
        border-radius: 6px;
        color: #b9c0c9;
        font-family: "SF Mono", Menlo, Consolas, monospace;
        font-size: 12px;
    }
    """


def _print_missing_qt() -> int:
    print("[ERROR] PySide6 is not installed.")
    print('[INFO] Install GUI dependencies with: pip install -e ".[gui]"')
    return 1


def main() -> int:
    if QtWidgets is None:
        return _print_missing_qt()

    config = load_config()
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"[ERROR] Config: {error}")
        return 1

    setup_logging(config.ui.log_level)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
