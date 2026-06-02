"""Typed application configuration (dataclasses + TOML-friendly dicts)."""

from dataclasses import asdict, dataclass, field
from typing import Any

from block_detected.config.inference import (
    CONF_MAX,
    CONF_MIN,
    CONF_STEP,
    DEFAULT_CONF,
    DEFAULT_MODEL_NAME,
    EVAL_CONF,
    OVERLAY_HISTORY,
)
from block_detected.config.ui import (
    BUTTON_HEIGHT,
    BUTTON_MARGIN,
    BUTTON_PAD_X,
    KEY_ARROW_DOWN,
    KEY_ARROW_UP,
    WINDOW_NAME,
)


# Keys that require reopening camera or reloading detector when changed at runtime.
RESTART_CAMERA_KEYS = frozenset({"camera.index", "camera.width", "camera.height", "camera.max_index"})
RESTART_DETECTOR_KEYS = frozenset({"inference.default_model_name"})


@dataclass
class CameraConfig:
    index: int = 0
    max_index: int = 5
    width: int = 1280
    height: int = 720


@dataclass
class InferenceConfig:
    default_model_name: str = DEFAULT_MODEL_NAME
    conf_min: float = CONF_MIN
    conf_max: float = CONF_MAX
    conf_step: float = CONF_STEP
    default_conf: float = DEFAULT_CONF
    eval_conf: float = EVAL_CONF
    overlay_history: int = OVERLAY_HISTORY


@dataclass
class ClassicalPipelineConfig:
    """Placeholder for future classical CV stages (blur, threshold, etc.)."""

    enabled: bool = False
    blur_kernel: int = 0
    canny_low: int = 50
    canny_high: int = 150


@dataclass
class StabilityConfig:
    """Post-inference filtering and temporal stability."""

    enabled: bool = False
    min_confidence: float = 0.0
    min_box_area_px: int = 0
    reject_edge_boxes: bool = False
    duplicate_merge_iou: float = 0.5
    temporal_window: int = 5
    required_stable_votes: int = 3


@dataclass
class UiDebugConfig:
    window_name: str = WINDOW_NAME
    button_margin: int = BUTTON_MARGIN
    button_height: int = BUTTON_HEIGHT
    button_pad_x: int = BUTTON_PAD_X
    key_arrow_up: int = KEY_ARROW_UP
    key_arrow_down: int = KEY_ARROW_DOWN
    log_level: str = "INFO"
    show_fps_in_status: bool = True


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    classical: ClassicalPipelineConfig = field(default_factory=ClassicalPipelineConfig)
    stability: StabilityConfig = field(default_factory=StabilityConfig)
    ui: UiDebugConfig = field(default_factory=UiDebugConfig)

    @classmethod
    def defaults(cls) -> "AppConfig":
        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        def section(name: str, dc_type: type):
            raw = data.get(name, {})
            if not isinstance(raw, dict):
                return dc_type()
            fields = {f.name for f in dc_type.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return dc_type(**{k: v for k, v in raw.items() if k in fields})

        return cls(
            camera=section("camera", CameraConfig),
            inference=section("inference", InferenceConfig),
            classical=section("classical", ClassicalPipelineConfig),
            stability=section("stability", StabilityConfig),
            ui=section("ui", UiDebugConfig),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera": asdict(self.camera),
            "inference": asdict(self.inference),
            "classical": asdict(self.classical),
            "stability": asdict(self.stability),
            "ui": asdict(self.ui),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        inf = self.inference

        def require_number(path: str, value: Any) -> bool:
            if isinstance(value, bool) or not isinstance(value, int | float):
                errors.append(f"{path} must be a number")
                return False
            return True

        def require_int(path: str, value: Any) -> bool:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{path} must be an integer")
                return False
            return True

        def require_bool(path: str, value: Any) -> bool:
            if not isinstance(value, bool):
                errors.append(f"{path} must be true or false")
                return False
            return True

        def require_str(path: str, value: Any) -> bool:
            if not isinstance(value, str):
                errors.append(f"{path} must be a string")
                return False
            return True

        conf_fields_valid = all(
            (
                require_number("inference.conf_min", inf.conf_min),
                require_number("inference.conf_max", inf.conf_max),
                require_number("inference.conf_step", inf.conf_step),
                require_number("inference.default_conf", inf.default_conf),
                require_number("inference.eval_conf", inf.eval_conf),
            )
        )
        require_int("inference.overlay_history", inf.overlay_history)
        require_str("inference.default_model_name", inf.default_model_name)

        camera_fields_valid = all(
            (
                require_int("camera.index", self.camera.index),
                require_int("camera.max_index", self.camera.max_index),
                require_int("camera.width", self.camera.width),
                require_int("camera.height", self.camera.height),
            )
        )

        require_bool("classical.enabled", self.classical.enabled)
        require_int("classical.blur_kernel", self.classical.blur_kernel)
        require_int("classical.canny_low", self.classical.canny_low)
        require_int("classical.canny_high", self.classical.canny_high)
        require_bool("stability.enabled", self.stability.enabled)
        require_number("stability.min_confidence", self.stability.min_confidence)
        require_int("stability.min_box_area_px", self.stability.min_box_area_px)
        require_bool("stability.reject_edge_boxes", self.stability.reject_edge_boxes)
        stability_iou_valid = require_number(
            "stability.duplicate_merge_iou",
            self.stability.duplicate_merge_iou,
        )
        stability_window_valid = require_int("stability.temporal_window", self.stability.temporal_window)
        stability_votes_valid = require_int(
            "stability.required_stable_votes",
            self.stability.required_stable_votes,
        )
        require_str("ui.window_name", self.ui.window_name)
        require_int("ui.button_margin", self.ui.button_margin)
        require_int("ui.button_height", self.ui.button_height)
        require_int("ui.button_pad_x", self.ui.button_pad_x)
        require_int("ui.key_arrow_up", self.ui.key_arrow_up)
        require_int("ui.key_arrow_down", self.ui.key_arrow_down)
        log_level_valid = require_str("ui.log_level", self.ui.log_level)
        require_bool("ui.show_fps_in_status", self.ui.show_fps_in_status)

        if conf_fields_valid and not inf.conf_min <= inf.default_conf <= inf.conf_max:
            errors.append("inference.default_conf must be within [conf_min, conf_max]")
        if conf_fields_valid and (inf.eval_conf < inf.conf_min or inf.eval_conf > inf.conf_max):
            errors.append("inference.eval_conf must be within [conf_min, conf_max]")
        if isinstance(inf.overlay_history, int) and not isinstance(inf.overlay_history, bool) and inf.overlay_history < 1:
            errors.append("inference.overlay_history must be >= 1")
        if camera_fields_valid and (self.camera.width < 1 or self.camera.height < 1):
            errors.append("camera width/height must be positive")
        if log_level_valid and self.ui.log_level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("ui.log_level must be a valid logging level name")
        stab = self.stability
        if stability_iou_valid and not 0 < stab.duplicate_merge_iou <= 1:
            errors.append("stability.duplicate_merge_iou must be in (0, 1]")
        if stability_window_valid and stab.temporal_window < 1:
            errors.append("stability.temporal_window must be >= 1")
        if stability_votes_valid and stab.required_stable_votes < 1:
            errors.append("stability.required_stable_votes must be >= 1")
        if (
            stability_window_valid
            and stability_votes_valid
            and stab.required_stable_votes > stab.temporal_window
        ):
            errors.append("stability.required_stable_votes must be <= temporal_window")
        if stab.min_confidence < 0 or stab.min_confidence > 1:
            errors.append("stability.min_confidence must be within [0, 1]")
        return errors

    @staticmethod
    def needs_camera_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_CAMERA_KEYS)

    @staticmethod
    def needs_detector_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_DETECTOR_KEYS)
