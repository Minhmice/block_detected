"""Apply hot-reloadable config to a running WebcamEngine (testable helper)."""

from block_detected.runtime.config_schema import (
    RESTART_CAMERA_KEYS,
    RESTART_DETECTOR_KEYS,
    AppConfig,
)
from block_detected.runtime.engine import WebcamEngine

RESTART_LOG_LEVEL_KEY = "ui.log_level"


def config_changed_keys(current: AppConfig, baseline: AppConfig) -> set[str]:
    """Return dotted config keys that differ between two snapshots."""
    keys: set[str] = set()
    cam_a, cam_b = current.camera, baseline.camera
    if cam_a.index != cam_b.index:
        keys.add("camera.index")
    if cam_a.max_index != cam_b.max_index:
        keys.add("camera.max_index")
    if cam_a.width != cam_b.width:
        keys.add("camera.width")
    if cam_a.height != cam_b.height:
        keys.add("camera.height")

    inf_a, inf_b = current.inference, baseline.inference
    if inf_a.default_model_name != inf_b.default_model_name:
        keys.add("inference.default_model_name")

    if current.ui.log_level != baseline.ui.log_level:
        keys.add(RESTART_LOG_LEVEL_KEY)

    stab_a, stab_b = current.stability, baseline.stability
    if stab_a.enabled != stab_b.enabled:
        keys.add("stability.enabled")
    if stab_a.min_confidence != stab_b.min_confidence:
        keys.add("stability.min_confidence")
    if stab_a.min_box_area_px != stab_b.min_box_area_px:
        keys.add("stability.min_box_area_px")
    if stab_a.reject_edge_boxes != stab_b.reject_edge_boxes:
        keys.add("stability.reject_edge_boxes")
    if stab_a.duplicate_merge_iou != stab_b.duplicate_merge_iou:
        keys.add("stability.duplicate_merge_iou")
    if stab_a.temporal_window != stab_b.temporal_window:
        keys.add("stability.temporal_window")
    if stab_a.required_stable_votes != stab_b.required_stable_votes:
        keys.add("stability.required_stable_votes")
    return keys


def needs_runtime_restart(current: AppConfig, baseline: AppConfig) -> bool:
    changed = config_changed_keys(current, baseline)
    return (
        bool(changed & RESTART_CAMERA_KEYS)
        or bool(changed & RESTART_DETECTOR_KEYS)
        or RESTART_LOG_LEVEL_KEY in changed
    )


def apply_hot_runtime_settings(
    engine: WebcamEngine,
    config: AppConfig,
    *,
    confidence: float,
    eval_mode: bool,
) -> None:
    """Sync AppConfig and runtime state fields that do not require camera restart."""
    engine.apply_hot_config(config)
    engine.state.confidence = confidence
    engine.state.eval_mode = eval_mode
