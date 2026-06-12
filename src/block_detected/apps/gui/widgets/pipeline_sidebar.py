"""Right sidebar with vision pipeline accordions and action buttons."""

from __future__ import annotations

from block_detected.apps.gui.widgets.accordion_section import AccordionSection
from block_detected.apps.gui.widgets.control_row import ControlRow

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = QtWidgets = None  # type: ignore[assignment]

if QtWidgets is not None:

    class PipelineSidebar(QtWidgets.QFrame):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("Sidebar")
            self.setMinimumWidth(300)
            self.setMaximumWidth(440)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Preferred,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)

            header = QtWidgets.QLabel("VISION PIPELINE")
            header.setObjectName("CapsLabel")
            header.setContentsMargins(16, 14, 16, 10)
            outer.addWidget(header)

            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_content = QtWidgets.QWidget()
            scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(8)
            scroll_layout.setContentsMargins(8, 0, 8, 8)

            # PRE-PROCESSING (open)
            self.preprocess_section = AccordionSection("PRE-PROCESSING", expanded=True)
            self.contrast_spin = QtWidgets.QDoubleSpinBox()
            self.contrast_spin.setRange(0.0, 2.0)
            self.contrast_spin.setSingleStep(0.1)
            self.contrast_spin.setDecimals(1)
            self.contrast_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.contrast_slider.setRange(0, 2000)
            self.preprocess_section.add_widget(
                ControlRow("Contrast", spin=self.contrast_spin, slider=self.contrast_slider)
            )
            self.brightness_spin = QtWidgets.QSpinBox()
            self.brightness_spin.setRange(-100, 100)
            self.brightness_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.brightness_slider.setRange(-100, 100)
            self.preprocess_section.add_widget(
                ControlRow("Brightness", spin=self.brightness_spin, slider=self.brightness_slider)
            )
            self.saturation_spin = QtWidgets.QDoubleSpinBox()
            self.saturation_spin.setRange(0.0, 2.0)
            self.saturation_spin.setSingleStep(0.1)
            self.saturation_spin.setDecimals(1)
            self.saturation_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.saturation_slider.setRange(0, 2000)
            self.preprocess_section.add_widget(
                ControlRow("Saturation", spin=self.saturation_spin, slider=self.saturation_slider)
            )
            scroll_layout.addWidget(self.preprocess_section)

            # INFERENCE (open)
            self.inference_section = AccordionSection("INFERENCE", expanded=True)
            self.conf_spin = QtWidgets.QDoubleSpinBox()
            self.conf_spin.setDecimals(3)
            self.conf_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.inference_section.add_widget(
                ControlRow("Confidence", spin=self.conf_spin, slider=self.conf_slider)
            )
            self.nms_iou_spin = QtWidgets.QDoubleSpinBox()
            self.nms_iou_spin.setDecimals(2)
            self.nms_iou_spin.setRange(0.01, 1.0)
            self.nms_iou_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.nms_iou_slider.setRange(1, 100)
            self.inference_section.add_widget(
                ControlRow("NMS IoU", spin=self.nms_iou_spin, slider=self.nms_iou_slider)
            )
            self.imgsz_spin = QtWidgets.QSpinBox()
            self.imgsz_spin.setRange(320, 1280)
            self.imgsz_spin.setSingleStep(32)
            self.imgsz_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.imgsz_slider.setRange(320, 1280)
            self.imgsz_slider.setSingleStep(32)
            self.inference_section.add_widget(
                ControlRow("Image Size", spin=self.imgsz_spin, slider=self.imgsz_slider)
            )
            self.max_det_spin = QtWidgets.QSpinBox()
            self.max_det_spin.setRange(1, 300)
            self.max_det_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.max_det_slider.setRange(1, 300)
            self.inference_section.add_widget(
                ControlRow("Max Det.", spin=self.max_det_spin, slider=self.max_det_slider)
            )
            agnostic_row = QtWidgets.QHBoxLayout()
            agnostic_lbl = QtWidgets.QLabel("Agnostic NMS")
            agnostic_lbl.setObjectName("MetricMuted")
            self.agnostic_nms_check = QtWidgets.QCheckBox("")
            agnostic_row.addWidget(agnostic_lbl)
            agnostic_row.addStretch(1)
            agnostic_row.addWidget(self.agnostic_nms_check)
            agnostic_wrap = QtWidgets.QWidget()
            agnostic_wrap.setLayout(agnostic_row)
            self.inference_section.add_widget(agnostic_wrap)
            self.eval_check = QtWidgets.QCheckBox("Eval mode")
            self.inference_section.add_widget(self.eval_check)
            scroll_layout.addWidget(self.inference_section)

            # STABILITY (collapsed)
            self.stability_section = AccordionSection("STABILITY", expanded=False)
            self.blur_kernel_spin = QtWidgets.QSpinBox()
            self.blur_kernel_spin.setRange(0, 31)
            self.blur_kernel_spin.setSingleStep(2)
            self.stability_section.add_widget(
                ControlRow("Blur Kernel", spin=self.blur_kernel_spin, slider=None)
            )
            self.stability_min_area_spin = QtWidgets.QSpinBox()
            self.stability_min_area_spin.setRange(0, 2_000_000)
            self.stability_min_area_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.stability_min_area_slider.setRange(0, 500_000)
            self.stability_section.add_widget(
                ControlRow(
                    "Min Area",
                    spin=self.stability_min_area_spin,
                    slider=self.stability_min_area_slider,
                )
            )
            smooth_row = QtWidgets.QHBoxLayout()
            smooth_lbl = QtWidgets.QLabel("Temporal smoothing")
            smooth_lbl.setObjectName("MetricMuted")
            self.stability_enabled_check = QtWidgets.QCheckBox("")
            smooth_row.addWidget(smooth_lbl)
            smooth_row.addStretch(1)
            smooth_row.addWidget(self.stability_enabled_check)
            smooth_wrap = QtWidgets.QWidget()
            smooth_wrap.setLayout(smooth_row)
            self.stability_section.add_widget(smooth_wrap)
            self.stability_min_conf_spin = QtWidgets.QDoubleSpinBox()
            self.stability_min_conf_spin.setDecimals(3)
            self.stability_min_conf_spin.setRange(0.0, 1.0)
            self.stability_min_conf_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.stability_min_conf_slider.setRange(0, 1000)
            self.stability_section.add_widget(
                ControlRow(
                    "Min conf",
                    spin=self.stability_min_conf_spin,
                    slider=self.stability_min_conf_slider,
                )
            )
            self.stability_dup_iou_spin = QtWidgets.QDoubleSpinBox()
            self.stability_dup_iou_spin.setDecimals(2)
            self.stability_dup_iou_spin.setRange(0.01, 1.0)
            self.stability_dup_iou_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.stability_dup_iou_slider.setRange(1, 100)
            self.stability_section.add_widget(
                ControlRow(
                    "Dup IoU",
                    spin=self.stability_dup_iou_spin,
                    slider=self.stability_dup_iou_slider,
                )
            )
            self.stability_window_spin = QtWidgets.QSpinBox()
            self.stability_window_spin.setRange(1, 120)
            self.stability_window_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.stability_window_slider.setRange(1, 120)
            self.stability_section.add_widget(
                ControlRow(
                    "Window",
                    spin=self.stability_window_spin,
                    slider=self.stability_window_slider,
                )
            )
            self.stability_votes_spin = QtWidgets.QSpinBox()
            self.stability_votes_spin.setRange(1, 120)
            self.stability_votes_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.stability_votes_slider.setRange(1, 120)
            self.stability_section.add_widget(
                ControlRow(
                    "Votes",
                    spin=self.stability_votes_spin,
                    slider=self.stability_votes_slider,
                )
            )
            scroll_layout.addWidget(self.stability_section)

            # EDGE DETECTION (collapsed)
            self.edge_section = AccordionSection("EDGE DETECTION", expanded=False)
            self.canny_low_spin = QtWidgets.QSpinBox()
            self.canny_low_spin.setRange(0, 255)
            self.canny_low_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.canny_low_slider.setRange(0, 255)
            self.edge_section.add_widget(
                ControlRow("Canny Low", spin=self.canny_low_spin, slider=self.canny_low_slider)
            )
            self.canny_high_spin = QtWidgets.QSpinBox()
            self.canny_high_spin.setRange(0, 255)
            self.canny_high_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.canny_high_slider.setRange(0, 255)
            self.edge_section.add_widget(
                ControlRow("Canny High", spin=self.canny_high_spin, slider=self.canny_high_slider)
            )
            scroll_layout.addWidget(self.edge_section)

            # ROI (disabled, collapsed)
            self.roi_section = AccordionSection("ROI SELECTION", expanded=False)
            roi_lbl = QtWidgets.QLabel("Coming in Phase 11")
            roi_lbl.setObjectName("MetricMuted")
            self.roi_section.add_widget(roi_lbl)
            self.roi_section.setEnabled(False)
            self.roi_section.setToolTip("ROI crop stage — Phase 11")
            scroll_layout.addWidget(self.roi_section)

            # DEFAULT CONFIG (collapsed, no default model field)
            self.default_section = AccordionSection("DEFAULT CONFIG", expanded=False)
            default_form = QtWidgets.QFormLayout()
            self.camera_index_spin = QtWidgets.QSpinBox()
            self.camera_index_spin.setRange(0, 32)
            self.camera_max_spin = QtWidgets.QSpinBox()
            self.camera_max_spin.setRange(0, 32)
            self.width_spin = QtWidgets.QSpinBox()
            self.width_spin.setRange(1, 7680)
            self.height_spin = QtWidgets.QSpinBox()
            self.height_spin.setRange(1, 4320)
            self.log_level_combo = QtWidgets.QComboBox()
            self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            default_form.addRow("Index", self.camera_index_spin)
            default_form.addRow("Max index", self.camera_max_spin)
            default_form.addRow("Width", self.width_spin)
            default_form.addRow("Height", self.height_spin)
            default_form.addRow("Log level", self.log_level_combo)
            default_wrap = QtWidgets.QWidget()
            default_wrap.setLayout(default_form)
            self.default_section.add_widget(default_wrap)
            scroll_layout.addWidget(self.default_section)

            scroll_layout.addStretch(1)
            scroll.setWidget(scroll_content)
            outer.addWidget(scroll, 1)

            footer = QtWidgets.QWidget()
            footer_layout = QtWidgets.QVBoxLayout(footer)
            footer_layout.setContentsMargins(12, 8, 12, 12)
            footer_layout.setSpacing(8)
            self.apply_button = QtWidgets.QPushButton("APPLY")
            self.apply_button.setObjectName("ApplyButton")
            self.save_button = QtWidgets.QPushButton("SAVE CONFIG")
            self.save_button.setObjectName("SaveButton")
            self.delete_button = QtWidgets.QPushButton("DELETE")
            self.delete_button.setObjectName("DeleteButton")
            footer_layout.addWidget(self.apply_button)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.save_button)
            row.addWidget(self.delete_button)
            footer_layout.addLayout(row)
            outer.addWidget(footer)

else:
    PipelineSidebar = None  # type: ignore[misc, assignment]
