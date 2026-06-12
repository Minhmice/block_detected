"""Reusable Robo-Vision GUI components."""

from block_detected.apps.gui.widgets.accordion_section import AccordionSection
from block_detected.apps.gui.widgets.camera_toolbar import CameraToolbar
from block_detected.apps.gui.widgets.camera_viewport import CameraViewport
from block_detected.apps.gui.widgets.control_row import ControlRow, bind_slider_spin
from block_detected.apps.gui.widgets.detection_card import DetectionCard
from block_detected.apps.gui.widgets.header_bar import HeaderBar
from block_detected.apps.gui.widgets.kinematics_card import KinematicsCard
from block_detected.apps.gui.widgets.metric_badge import MetricBadge
from block_detected.apps.gui.widgets.pipeline_sidebar import PipelineSidebar
from block_detected.apps.gui.widgets.system_log_card import SystemLogCard
from block_detected.apps.gui.widgets.toggle_pill import TogglePill

__all__ = [
    "AccordionSection",
    "CameraToolbar",
    "CameraViewport",
    "ControlRow",
    "DetectionCard",
    "HeaderBar",
    "KinematicsCard",
    "MetricBadge",
    "PipelineSidebar",
    "SystemLogCard",
    "TogglePill",
    "bind_slider_spin",
]
