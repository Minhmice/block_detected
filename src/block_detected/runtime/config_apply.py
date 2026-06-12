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
    if inf_a.last_model_name != inf_b.last_model_name:
        keys.add("inference.last_model_name")
    if inf_a.default_conf != inf_b.default_conf:
        keys.add("inference.default_conf")
    if inf_a.iou != inf_b.iou:
        keys.add("inference.iou")
    if inf_a.max_det != inf_b.max_det:
        keys.add("inference.max_det")
    if inf_a.agnostic_nms != inf_b.agnostic_nms:
        keys.add("inference.agnostic_nms")
    if inf_a.imgsz != inf_b.imgsz:
        keys.add("inference.imgsz")

    pp_a, pp_b = current.preprocess, baseline.preprocess
    if pp_a.contrast != pp_b.contrast:
        keys.add("preprocess.contrast")
    if pp_a.brightness != pp_b.brightness:
        keys.add("preprocess.brightness")
    if pp_a.saturation != pp_b.saturation:
        keys.add("preprocess.saturation")

    cl_a, cl_b = current.classical, baseline.classical
    if cl_a.enabled != cl_b.enabled:
        keys.add("classical.enabled")
    if cl_a.blur_kernel != cl_b.blur_kernel:
        keys.add("classical.blur_kernel")
    if cl_a.canny_low != cl_b.canny_low:
        keys.add("classical.canny_low")
    if cl_a.canny_high != cl_b.canny_high:
        keys.add("classical.canny_high")
    if cl_a.show_contours != cl_b.show_contours:
        keys.add("classical.show_contours")
    if cl_a.show_corners != cl_b.show_corners:
        keys.add("classical.show_corners")
    if cl_a.show_warped_face != cl_b.show_warped_face:
        keys.add("classical.show_warped_face")

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
