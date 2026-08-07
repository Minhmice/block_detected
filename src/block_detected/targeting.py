"""Headless model compatibility checks and bounding-box targeting."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, TextIO

from block_detected.config.paths import MODELS_DIR, PACKAGE_ROOT
from block_detected.config.store import load_config
from block_detected.core.domain import Detection
from block_detected.detection.yolo.loader import discover_model_paths
from block_detected.runtime.detector_loader import load_detector
from block_detected.runtime.preprocess import apply_preprocess
from block_detected.runtime.session import try_open_camera
from block_detected.runtime.state import RuntimeState
from block_detected.vision.geometry import box_center

PI_USB_CONFIG_PATH = PACKAGE_ROOT / "block_detected-pi-usb.json"
SPATIAL_TASKS = frozenset({"detect", "pose", "segment", "obb"})


@dataclass(frozen=True, slots=True)
class TargetResult:
    box: tuple[int, int, int, int]
    class_id: int
    class_name: str
    confidence: float
    angle: float
    center_px: tuple[float, float]
    error_px: tuple[float, float]
    center_norm: tuple[float, float]
    error_norm: tuple[float, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def select_target(
    detections: list[Detection],
    *,
    frame_width: int,
    frame_height: int,
    class_filter: str | int | None = None,
) -> TargetResult | None:
    """Select highest-confidence matching box and calculate aim error."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be positive")

    candidates = detections
    if isinstance(class_filter, int):
        candidates = [item for item in candidates if item.class_id == class_filter]
    elif class_filter is not None:
        wanted = class_filter.casefold()
        candidates = [item for item in candidates if item.class_name.casefold() == wanted]
    if not candidates:
        return None

    detection = max(candidates, key=lambda item: item.confidence)
    center_x, center_y = box_center(detection.box)
    camera_x, camera_y = frame_width / 2.0, frame_height / 2.0
    return TargetResult(
        box=detection.box,
        class_id=detection.class_id,
        class_name=detection.class_name,
        confidence=detection.confidence,
        angle=detection.angle,
        center_px=(center_x, center_y),
        error_px=(center_x - camera_x, center_y - camera_y),
        center_norm=(center_x / frame_width, center_y / frame_height),
        error_norm=(2.0 * center_x / frame_width - 1.0, 2.0 * center_y / frame_height - 1.0),
    )


def parse_class_filter(value: str | None) -> str | int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def resolve_model_path(name: str, models_dir: Path = MODELS_DIR) -> Path:
    path = Path(name).expanduser()
    if path.is_file():
        return path.resolve()
    candidate = models_dir / name
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"model not found: {name}")


def resolve_imgsz(model_path: Path, requested: int) -> int:
    """Use fixed square ONNX input dimensions when the graph requires them."""
    if model_path.suffix.lower() != ".onnx":
        return requested
    try:
        import onnx

        model = onnx.load(str(model_path), load_external_data=False)
        dimensions = model.graph.input[0].type.tensor_type.shape.dim
        height = dimensions[-2].dim_value
        width = dimensions[-1].dim_value
        if height > 0 and height == width:
            return int(height)
    except Exception:
        pass
    return requested


def detector_task(detector: Any) -> str:
    return str(getattr(detector, "task", "detect") or "detect").lower()


def _read_frame(capture: Any, attempts: int = 3) -> Any | None:
    for _ in range(attempts):
        ok, frame = capture.read()
        if ok and frame is not None:
            return frame
    return None


def _prepare_frame(frame: Any, config: Any) -> Any:
    return apply_preprocess(
        frame,
        contrast=config.preprocess.contrast,
        brightness=config.preprocess.brightness,
        saturation=config.preprocess.saturation,
        blur_kernel=config.classical.blur_kernel,
    )


def _predict(detector: Any, frame: Any, config: Any, imgsz: int) -> Any:
    return detector.predict(
        frame,
        conf=config.inference.default_conf,
        iou=config.inference.iou,
        imgsz=imgsz,
        max_det=config.inference.max_det,
        agnostic_nms=config.inference.agnostic_nms,
    )


def _write_json(payload: dict[str, Any], output: TextIO) -> None:
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True), file=output, flush=True)


def _target_payload(
    *,
    model_name: str,
    task: str,
    frame_number: int,
    elapsed_ms: float,
    detections: list[Detection],
    frame: Any,
    class_filter: str | int | None,
) -> dict[str, Any]:
    height, width = frame.shape[:2]
    target = select_target(
        detections,
        frame_width=int(width),
        frame_height=int(height),
        class_filter=class_filter,
    )
    return {
        "model": model_name,
        "task": task,
        "frame": frame_number,
        "latency_ms": round(elapsed_ms, 3),
        "detections": len(detections),
        "target": None if target is None else target.to_dict(),
    }


def run_single(
    args: argparse.Namespace,
    config: Any,
    capture: Any,
    *,
    output: TextIO = sys.stdout,
) -> int:
    model_name = args.model or config.inference.last_model_name
    detector = None
    class_filter = parse_class_filter(args.class_filter)
    try:
        model_path = resolve_model_path(model_name)
        imgsz = resolve_imgsz(model_path, config.inference.imgsz)
        with contextlib.redirect_stdout(sys.stderr):
            detector = load_detector(model_path)
        task = detector_task(detector)
        if task not in SPATIAL_TASKS:
            _write_json({"model": model_path.name, "task": task, "status": "unsupported"}, output)
            return 2

        warmup_frame = _read_frame(capture)
        if warmup_frame is None:
            raise RuntimeError("camera frame read failed")
        warmup_frame = _prepare_frame(warmup_frame, config)
        for _ in range(args.warmup):
            with contextlib.redirect_stdout(sys.stderr):
                _predict(detector, warmup_frame, config, imgsz)

        frame_number = 0
        while args.frames == 0 or frame_number < args.frames:
            frame = _read_frame(capture)
            if frame is None:
                raise RuntimeError("camera frame read failed")
            frame = _prepare_frame(frame, config)
            started = perf_counter()
            with contextlib.redirect_stdout(sys.stderr):
                result = _predict(detector, frame, config, imgsz)
            elapsed_ms = (perf_counter() - started) * 1000.0
            frame_number += 1
            _write_json(
                _target_payload(
                    model_name=model_path.name,
                    task=task,
                    frame_number=frame_number,
                    elapsed_ms=elapsed_ms,
                    detections=result.detections,
                    frame=frame,
                    class_filter=class_filter,
                ),
                output,
            )
        return 0
    except Exception as exc:
        _write_json({"model": Path(model_name).name, "status": "error", "error": str(exc)}, output)
        return 1
    finally:
        if detector is not None:
            detector.close()


def check_all_models(
    args: argparse.Namespace,
    config: Any,
    frame: Any,
    *,
    output: TextIO = sys.stdout,
    models_dir: Path = MODELS_DIR,
) -> int:
    model_paths = discover_model_paths(models_dir)
    if not model_paths:
        _write_json({"status": "error", "error": f"no models found in {models_dir}"}, output)
        return 1

    failed = False
    frame = _prepare_frame(frame, config)
    class_filter = parse_class_filter(args.class_filter)
    for model_path in model_paths:
        detector = None
        try:
            imgsz = resolve_imgsz(model_path, config.inference.imgsz)
            with contextlib.redirect_stdout(sys.stderr):
                detector = load_detector(model_path)
            task = detector_task(detector)
            if task not in SPATIAL_TASKS:
                _write_json(
                    {"model": model_path.name, "task": task, "imgsz": imgsz, "status": "unsupported"},
                    output,
                )
                continue
            for _ in range(args.warmup):
                with contextlib.redirect_stdout(sys.stderr):
                    _predict(detector, frame, config, imgsz)
            started = perf_counter()
            with contextlib.redirect_stdout(sys.stderr):
                result = _predict(detector, frame, config, imgsz)
            elapsed_ms = (perf_counter() - started) * 1000.0
            payload = _target_payload(
                model_name=model_path.name,
                task=task,
                frame_number=1,
                elapsed_ms=elapsed_ms,
                detections=result.detections,
                frame=frame,
                class_filter=class_filter,
            )
            payload.update({"status": "ok", "imgsz": imgsz})
            _write_json(payload, output)
        except Exception as exc:
            failed = True
            _write_json({"model": model_path.name, "status": "error", "error": str(exc)}, output)
        finally:
            if detector is not None:
                detector.close()
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Headless Pi targeting with JSONL output")
    parser.add_argument("--model", help="model filename under models/ or path")
    parser.add_argument("--check-all", action="store_true", help="test every discovered model on one frame")
    parser.add_argument("--config", type=Path, default=PI_USB_CONFIG_PATH)
    parser.add_argument("--camera-index", type=int)
    parser.add_argument("--imgsz", type=int)
    parser.add_argument("--conf", type=float)
    parser.add_argument("--class", dest="class_filter")
    parser.add_argument("--frames", type=int, default=0, help="0 runs until interrupted")
    parser.add_argument("--warmup", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.frames < 0 or args.warmup < 0:
        raise SystemExit("--frames and --warmup must be non-negative")
    if args.imgsz is not None and (not 320 <= args.imgsz <= 1280 or args.imgsz % 32):
        raise SystemExit("--imgsz must be a multiple of 32 within [320, 1280]")
    if args.conf is not None and not 0 <= args.conf <= 1:
        raise SystemExit("--conf must be within [0, 1]")

    config = load_config(args.config)
    if args.camera_index is not None:
        config.camera.index = args.camera_index
    if args.imgsz is not None:
        config.inference.imgsz = args.imgsz
    if args.conf is not None:
        config.inference.default_conf = args.conf
    errors = config.validate()
    if errors:
        for error in errors:
            _write_json({"status": "error", "error": error}, sys.stdout)
        return 2

    state = RuntimeState(confidence=config.inference.default_conf, camera_index=config.camera.index)
    capture, _source, error = try_open_camera(config, state)
    if capture is None:
        _write_json({"status": "error", "error": error or "camera open failed"}, sys.stdout)
        return 1
    try:
        if args.check_all:
            frame = _read_frame(capture)
            if frame is None:
                _write_json({"status": "error", "error": "camera frame read failed"}, sys.stdout)
                return 1
            return check_all_models(args, config, frame)
        return run_single(args, config, capture)
    except KeyboardInterrupt:
        return 130
    finally:
        capture.release()


if __name__ == "__main__":
    raise SystemExit(main())
