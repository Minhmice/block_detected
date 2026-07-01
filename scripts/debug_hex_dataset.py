#!/usr/bin/env python3
"""Interactive YOLO + hex-detector dataset debugger with tiered diagnostics.

Run::

    python scripts/debug_hex_dataset.py `
      --images block_dataset `
      --model models/son-down.pt `
      --conf 0.35 `
      --device cpu `
      --output runs/debug_hex

Controls::

    Right / D  — next image
    Left  / A  — previous image
    0-3        — switch debug level
    R          — reload debug_config.json, rerun YOLO + hex for current image
    S          — save {stem}.overlay.jpg to overlays/
    E          — save {stem}.edges.png to edges/
    J          — save overlay, edges, and {stem}.full.json (full debug snapshot)
    Q / ESC    — exit
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hex_detector import (  # noqa: E402
    BBox,
    HexDetector,
    HexDetectorConfig,
    HexPoints,
    LineSegment,
    ScoreBreakdown,
    YoloDetection,
)
from hex_detector.renderer import render_debug  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logger = logging.getLogger("debug_hex")
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Natural sort helpers
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(r"(\d+)")


def _natural_key(name: str) -> list[str | int]:
    """Natural sort key so dt2 precedes dt10."""
    parts = _NUMERIC_RE.split(name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


# ---------------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------------

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def _discover_images(folder: Path) -> list[Path]:
    """Return naturally sorted image paths from a flat directory."""
    paths = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    ]
    paths.sort(key=lambda p: _natural_key(p.stem))
    return paths


# ---------------------------------------------------------------------------
# YOLO box conversion (mirrors batch_hex_son_down.py pattern)
# ---------------------------------------------------------------------------

def _yolo_to_detections(result: Any) -> list[YoloDetection]:
    """Convert Ultralytics Results to typed YoloDetection list."""
    dets: list[YoloDetection] = []
    r0 = result[0]
    if r0.boxes is None:
        return dets
    for i in range(len(r0.boxes)):
        xyxy = r0.boxes.xyxy[i].cpu().numpy()
        cf = float(r0.boxes.conf[i].item())
        dets.append(YoloDetection(
            track_id=i + 1,
            bbox=BBox(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])),
            confidence=cf,
        ))
    return dets


# ---------------------------------------------------------------------------
# Config loader with strict whitelist
# ---------------------------------------------------------------------------

def _load_config(config_path: Path) -> HexDetectorConfig:
    """Load and validate debug_config.json; raise on any failure."""
    if not config_path.exists():
        cfg = HexDetectorConfig()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(dataclasses.asdict(cfg), indent=2), encoding="utf-8"
        )
        return cfg

    raw_text = config_path.read_text(encoding="utf-8")
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("debug_config.json must be a JSON object")

    allowed = {f.name for f in dataclasses.fields(HexDetectorConfig)}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise ValueError(
            f"Unknown config keys: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )

    cfg = HexDetectorConfig(**data)
    cfg.validate()
    return cfg


# ---------------------------------------------------------------------------
# JSON-safe sanitizer for full snapshots
# ---------------------------------------------------------------------------

def _sanitize_for_json(obj: Any) -> Any:
    """Recursively convert dataclasses, LineSegment, NumPy scalars, Path to JSON-safe types."""
    if obj is None:
        return None
    if isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (LineSegment,)):
        from hex_detector.debug_serialize import line_to_dict
        return line_to_dict(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result: dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            result[f.name] = _sanitize_for_json(getattr(obj, f.name))
        return result
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    # Fallback: stringify
    return str(obj)


# ---------------------------------------------------------------------------
# Level-specific overlay drawing
# ---------------------------------------------------------------------------

_FONT = cv2.FONT_HERSHEY_SIMPLEX

_COLORS = {
    "yolo": (0, 255, 255),
    "roi": (255, 128, 0),
    "winning": (0, 220, 0),
    "raw": (100, 100, 100),
    "filtered": (180, 180, 180),
    "grouped": (255, 200, 0),
    "merged": (0, 255, 255),
    "point": (0, 255, 0),
    "reject": (0, 0, 255),
    "held": (255, 255, 0),
    "candidate_pass": (0, 200, 0),
    "candidate_fail": (0, 0, 200),
    "timing": (200, 200, 200),
}


def _draw_level_overlays(
    overlay: np.ndarray,
    results: list[Any],
    yolo_dets: list[YoloDetection],
    frame_shape: tuple[int, int],
    level: int,
    edge_img: np.ndarray | None,
) -> None:
    """Add level-specific annotations on top of render_debug base overlay."""
    if level < 0 or level > 3:
        return

    # --- Level 0: YOLO boxes + confidence ---
    for det in yolo_dets:
        x1, y1, x2, y2 = det.bbox.as_int_tuple()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), _COLORS["yolo"], 2)
        label = f"YOLO id={det.track_id} conf={det.confidence:.2f}"
        cv2.putText(overlay, label, (x1, max(10, y1 - 6)),
                    _FONT, 0.4, _COLORS["yolo"], 1, cv2.LINE_AA)

    if level == 0:
        return

    # --- Level 1+: effective ROI, winning lines, score breakdown ---
    for res in results:
        bb = res.roi_bbox
        x1, y1, x2, y2 = int(bb["x1"]), int(bb["y1"]), int(bb["x2"]), int(bb["y2"])
        cv2.rectangle(overlay, (x1, y1), (x2, y2), _COLORS["roi"], 1)

        # Score breakdown
        if res.score_breakdown is not None:
            sb = res.score_breakdown
            lines = [
                f"E={sb.edge_support:.2f} P={sb.parallelism:.2f} T={sb.topology:.2f}",
                f"A={sb.area_position:.2f} Tm={sb.temporal:.2f} total={sb.total:.2f}",
            ]
            y_off = y2 + 14
            for line in lines:
                cv2.putText(overlay, line, (x1, y_off),
                            _FONT, 0.35, _COLORS["point"], 1, cv2.LINE_AA)
                y_off += 14

    if level == 1:
        return

    # --- Level 2+: raw/filtered/pre-merge/merged groups ---
    for res in results:
        dbg = res.debug
        bb = res.roi_bbox
        ox, oy = bb["x1"], bb["y1"]

        def _offset_lines(lines: list[dict[str, Any]], color: tuple[int, int, int]) -> None:
            for ln in lines:
                cv2.line(
                    overlay,
                    (int(ln["x1"] + ox), int(ln["y1"] + oy)),
                    (int(ln["x2"] + ox), int(ln["y2"] + oy)),
                    color, 1, cv2.LINE_AA,
                )

        if "raw_lines" in dbg and isinstance(dbg["raw_lines"], list):
            _offset_lines(dbg["raw_lines"], _COLORS["raw"])
        if "filtered_lines" in dbg and isinstance(dbg["filtered_lines"], list):
            _offset_lines(dbg["filtered_lines"], _COLORS["filtered"])

        # Grouped (pre-merge) lines
        if "grouped_lines" in dbg and isinstance(dbg["grouped_lines"], dict):
            group_colors = {
                "vertical": (255, 100, 0),
                "front_horizontal": (0, 255, 100),
                "right_diagonal": (255, 0, 100),
            }
            for gname, glines in dbg["grouped_lines"].items():
                if isinstance(glines, list):
                    _offset_lines(glines, group_colors.get(gname, _COLORS["grouped"]))

        # Merged line counts label
        if "merged_lines" in dbg and isinstance(dbg["merged_lines"], dict):
            counts = {k: len(v) for k, v in dbg["merged_lines"].items() if isinstance(v, list)}
            label = " | ".join(f"{k}={c}" for k, c in sorted(counts.items()))
            cv2.putText(overlay, f"merged: {label}", (x1 + 10, y1 + 20),
                        _FONT, 0.35, _COLORS["merged"], 1, cv2.LINE_AA)

    if level == 2:
        return

    # --- Level 3: candidates + validation + timing ---
    for res in results:
        dbg = res.debug

        if "top_candidates" in dbg and isinstance(dbg["top_candidates"], list):
            y_off = 30
            for cand in dbg["top_candidates"][:6]:
                mode = cand.get("mode", "?")
                score_val = cand.get("score", 0)
                label = f"{mode} score={float(score_val):.2f}"
                cv2.putText(overlay, label, (10, y_off),
                            _FONT, 0.35, _COLORS["candidate_pass"], 1, cv2.LINE_AA)
                y_off += 14

        if "validation_results" in dbg and isinstance(dbg["validation_results"], list):
            y_off = 120
            for vr in dbg["validation_results"][:8]:
                stage = vr.get("stage", "?")
                ok = vr.get("ok", True)
                reason = vr.get("reason", "")
                color = _COLORS["candidate_pass"] if ok else _COLORS["candidate_fail"]
                label = f"val {stage}: {'PASS' if ok else f'FAIL ({reason})'}"
                cv2.putText(overlay, label, (10, y_off),
                            _FONT, 0.3, color, 1, cv2.LINE_AA)
                y_off += 12

        if "stage_timings_ms" in dbg and isinstance(dbg["stage_timings_ms"], dict):
            y_off = frame_shape[0] - 10
            tlines: list[str] = []
            for k in ("hough", "filter", "group", "merge", "candidates", "total"):
                v = dbg["stage_timings_ms"].get(k)
                if v is not None:
                    tlines.append(f"{k}={float(v):.1f}ms")
            if tlines:
                cv2.putText(overlay, " | ".join(tlines), (10, y_off),
                            _FONT, 0.35, _COLORS["timing"], 1, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Lightweight JSON record
# ---------------------------------------------------------------------------

def _build_lightweight_record(
    path: Path,
    frame_shape: tuple[int, int],
    yolo_dets: list[YoloDetection],
    results: list[Any],
    timings: dict[str, float],
    error: str | None,
) -> dict[str, Any]:
    """Build the automatic lightweight per-image JSON record."""
    yolo_boxes = [
        {
            "track_id": d.track_id,
            "bbox": d.bbox.to_dict(),
            "confidence": d.confidence,
        }
        for d in yolo_dets
    ]
    result_dicts = []
    for r in results:
        d = r.to_dict()
        dbg = r.debug
        if "stage_timings_ms" in dbg:
            d["stage_timings_ms"] = dbg["stage_timings_ms"]
        if "merged_lines" in dbg and isinstance(dbg["merged_lines"], dict):
            d["line_counts"] = {
                k: len(v) for k, v in dbg["merged_lines"].items() if isinstance(v, list)
            }
        result_dicts.append(d)

    record: dict[str, Any] = {
        "image": str(path.name),
        "image_path": str(path),
        "shape": {"width": frame_shape[1], "height": frame_shape[0]},
        "yolo_boxes": yolo_boxes,
        "yolo_box_count": len(yolo_boxes),
        "results": result_dicts,
        "result_count": len(result_dicts),
        "success": error is None,
    }
    if error:
        record["error"] = error
    if timings:
        record["timings_ms"] = {k: round(v * 1000, 3) for k, v in timings.items()}
    return record


# ---------------------------------------------------------------------------
# Console log mirror
# ---------------------------------------------------------------------------

def _log_block(title: str, lines: list[str]) -> None:
    """Print a structured block to console and debug.log."""
    header = f"--- {title} ---"
    logger.info(header)
    print(header)
    for line in lines:
        logger.info(line)
        print(f"  {line}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive YOLO + hex-detector dataset debugger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Controls:
  Right / D  — next image
  Left  / A  — previous image
  0-3        — switch debug level
  R          — reload debug_config.json, rerun YOLO + hex
  S          — save overlay.jpg
  E          — save edges.png
  J          — save overlay + edges + full.json
  Q / ESC    — exit

Run:
  python scripts/debug_hex_dataset.py --images block_dataset --model models/son-down.pt --conf 0.35 --device cpu --output runs/debug_hex""",
    )
    parser.add_argument("--images", type=Path, default=ROOT / "block_dataset",
                        help="Image directory (default: block_dataset)")
    parser.add_argument("--model", type=Path, default=ROOT / "models" / "son-down.pt",
                        help="YOLO .pt model path")
    parser.add_argument("--conf", type=float, default=0.35,
                        help="YOLO confidence threshold")
    parser.add_argument("--iou", type=float, default=0.7,
                        help="YOLO IoU threshold")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="YOLO inference image size")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Inference device (cpu, cuda:0, ...)")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "debug_hex",
                        help="Output root directory")
    parser.add_argument("--start-index", type=int, default=0,
                        help="Start at this image index (0-based)")
    parser.add_argument("--debug-level", type=int, default=1, choices=[0, 1, 2, 3],
                        help="Debug level 0-3 (default: 1)")

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Phase 1: Fatal startup checks (imports, model, config, images)
    # -----------------------------------------------------------------------

    # Validate image directory
    images_dir = args.images.resolve()
    if not images_dir.is_dir():
        print(f"ERROR: --images directory not found: {images_dir}", file=sys.stderr)
        return 1

    image_paths = _discover_images(images_dir)
    if not image_paths:
        print(f"ERROR: no images found in {images_dir}", file=sys.stderr)
        return 1

    # Validate start index
    if args.start_index < 0 or args.start_index >= len(image_paths):
        print(
            f"ERROR: --start-index {args.start_index} out of range "
            f"(0-{len(image_paths) - 1})",
            file=sys.stderr,
        )
        return 1

    # Validate model path
    model_path = args.model.resolve()
    if not model_path.is_file():
        print(f"ERROR: --model file not found: {model_path}", file=sys.stderr)
        return 1

    # Setup output directories
    out_root = args.output.resolve()
    overlays_dir = out_root / "overlays"
    edges_dir = out_root / "edges"
    json_dir = out_root / "debug_json"
    log_path = out_root / "debug.log"

    try:
        out_root.mkdir(parents=True, exist_ok=True)
        overlays_dir.mkdir(parents=True, exist_ok=True)
        edges_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: cannot create output directories: {e}", file=sys.stderr)
        return 1

    # Setup file logger
    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Load YOLO model (fatal if fails)
    try:
        from ultralytics import YOLO
        model = YOLO(str(model_path))
    except Exception:
        print("FATAL: failed to load YOLO model", file=sys.stderr)
        traceback.print_exc()
        return 1

    # Load initial config (fatal if fails)
    config_path = out_root / "debug_config.json"
    try:
        config = _load_config(config_path)
        logger.info("Loaded config from %s", config_path)
    except Exception:
        print(f"FATAL: failed to load config from {config_path}", file=sys.stderr)
        traceback.print_exc()
        return 1

    # -----------------------------------------------------------------------
    # Phase 2: Navigation loop
    # -----------------------------------------------------------------------

    current_idx = args.start_index
    level = args.debug_level
    last_overlay: np.ndarray | None = None
    last_edge: np.ndarray | None = None
    last_results: list[Any] = []
    last_yolo_dets: list[YoloDetection] = []
    last_error: str | None = None
    last_timings: dict[str, float] = {}
    last_path: Path | None = None

    def process_image(idx: int) -> None:
        """Process a single image: read → YOLO → hex → render → overlay."""
        nonlocal last_overlay, last_edge, last_results, last_yolo_dets
        nonlocal last_error, last_timings, last_path

        path = image_paths[idx]
        last_path = path
        t_total = time.perf_counter()

        # Read image
        frame = cv2.imread(str(path))
        if frame is None:
            last_error = "cannot read image"
            last_overlay = np.zeros((480, 640, 3), dtype=np.uint8)
            last_edge = None
            last_results = []
            last_yolo_dets = []
            last_timings = {}
            _log_block(f"IMAGE {idx}/{len(image_paths)} {path.name}",
                       [f"ERROR: cannot read image (t={time.perf_counter() - t_total:.3f}s)"])
            _write_failure_record(path, frame_shape=(0, 0), error=last_error, t_total=t_total)
            return

        h, w = frame.shape[:2]
        t_read = time.perf_counter() - t_total

        # YOLO inference
        try:
            t_yolo_start = time.perf_counter()
            yolo_result = model.predict(
                frame, conf=args.conf, iou=args.iou,
                imgsz=args.imgsz, device=args.device, verbose=False,
            )
            t_yolo = time.perf_counter() - t_yolo_start
            yolo_dets = _yolo_to_detections(yolo_result)
            last_yolo_dets = yolo_dets
        except Exception:
            last_error = "YOLO inference failed"
            last_overlay = frame.copy() if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
            last_edge = None
            last_results = []
            last_timings = {}
            _log_block(f"IMAGE {idx}/{len(image_paths)} {path.name}",
                       ["YOLO inference failed"])
            traceback.print_exc()
            logger.exception("YOLO inference failed for %s", path.name)
            _write_failure_record(path, frame_shape=(h, w), error=last_error, t_total=time.perf_counter() - t_total)
            return

        # Build YOLO box log lines
        yolo_lines: list[str] = [f"boxes: {len(yolo_dets)}"]
        for d in yolo_dets:
            bb = d.bbox
            yolo_lines.append(
                f"  BOX id={d.track_id} "
                f"x1={bb.x1:.0f} y1={bb.y1:.0f} x2={bb.x2:.0f} y2={bb.y2:.0f} "
                f"conf={d.confidence:.3f}"
            )

        # Hex detector
        try:
            t_hex_start = time.perf_counter()
            detector = HexDetector(config)
            results = detector.detect_frame(frame, yolo_dets)
            t_hex = time.perf_counter() - t_hex_start
            last_results = results
        except Exception:
            last_error = "hex detector failed"
            overlay = frame.copy()
            _draw_level_overlays(overlay, [], yolo_dets, (h, w), level, None)
            last_overlay = overlay
            last_edge = None
            last_timings = {}
            _log_block(f"IMAGE {idx}/{len(image_paths)} {path.name}", yolo_lines + ["hex detector failed"])
            traceback.print_exc()
            logger.exception("hex detector failed for %s", path.name)
            _write_failure_record(path, frame_shape=(h, w), yolo_dets=yolo_dets,
                                  error=last_error, t_total=time.perf_counter() - t_total)
            return

        # Build result log lines
        result_lines: list[str] = []
        for r in results:
            line = (
                f"  RESULT id={r.track_id} mode={r.mode} status={r.status} "
                f"score={r.score:.3f}"
            )
            if r.reject_reason:
                line += f" reject={r.reject_reason}"
            result_lines.append(line)
            if r.score_breakdown is not None:
                sb = r.score_breakdown
                result_lines.append(
                    f"    SCORE E={sb.edge_support:.2f} P={sb.parallelism:.2f} "
                    f"T={sb.topology:.2f} A={sb.area_position:.2f} "
                    f"Tm={sb.temporal:.2f} total={sb.total:.2f}"
                )

            # Line counts from debug
            dbg = r.debug
            if "merged_lines" in dbg and isinstance(dbg["merged_lines"], dict):
                ml = dbg["merged_lines"]
                counts = {k: len(v) for k, v in ml.items() if isinstance(v, list)}
                result_lines.append(
                    "    MERGED " + " ".join(f"{k}={c}" for k, c in sorted(counts.items()))
                )
            if "raw_lines" in dbg and isinstance(dbg["raw_lines"], list):
                result_lines.append(f"    LINES raw={len(dbg['raw_lines'])}")
            if "filtered_lines" in dbg and isinstance(dbg["filtered_lines"], list):
                result_lines.append(f"    LINES filtered={len(dbg['filtered_lines'])}")
            if "grouped_lines" in dbg and isinstance(dbg["grouped_lines"], dict):
                gl = dbg["grouped_lines"]
                gcounts = {k: len(v) for k, v in gl.items() if isinstance(v, list)}
                result_lines.append(
                    "    GROUPS " + " ".join(f"{k}={c}" for k, c in sorted(gcounts.items()))
                )

        # Timing log
        t_total_elapsed = time.perf_counter() - t_total
        timing_lines = [
            f"TIMING read={t_read * 1000:.1f}ms yolo={t_yolo * 1000:.1f}ms "
            f"hex={t_hex * 1000:.1f}ms total={t_total_elapsed * 1000:.1f}ms",
        ]
        last_timings = {"read": t_read, "yolo": t_yolo, "hex": t_hex, "total": t_total_elapsed}

        # Log block
        _log_block(f"IMAGE {idx}/{len(image_paths)} {path.name}",
                   yolo_lines + result_lines + timing_lines)

        last_error = None

        # Render base overlay
        try:
            overlay = render_debug(frame, results, config)
            _draw_level_overlays(overlay, results, yolo_dets, (h, w), level, None)
        except Exception:
            overlay = frame.copy()
            _draw_level_overlays(overlay, results, yolo_dets, (h, w), level, None)
            traceback.print_exc()
            logger.exception("render_debug failed for %s", path.name)

        last_overlay = overlay

        # Extract edges for level 2+ display
        last_edge = None
        if level >= 2 and results:
            for r in results:
                dbg = r.debug
                if "edges" in dbg:
                    edge_data = dbg["edges"]
                    if isinstance(edge_data, np.ndarray) and edge_data.size > 0:
                        last_edge = edge_data
                        break

        # Write lightweight JSON record
        _write_lightweight_record(path, (h, w), yolo_dets, results, last_timings, None)

    def rerender_overlay() -> None:
        """Rerender overlay at current debug level using cached data."""
        nonlocal last_overlay, last_edge
        if last_path is None or last_overlay is None:
            return

        frame = cv2.imread(str(last_path))
        if frame is None:
            return

        h, w = frame.shape[:2]

        if last_error:
            overlay = frame.copy() if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            try:
                overlay = render_debug(frame, last_results, config)
            except Exception:
                overlay = frame.copy()
            _draw_level_overlays(overlay, last_results, last_yolo_dets, (h, w), level, None)

        last_overlay = overlay
        last_edge = None
        if level >= 2 and last_results:
            for r in last_results:
                dbg = r.debug
                if "edges" in dbg:
                    edge_data = dbg["edges"]
                    if isinstance(edge_data, np.ndarray) and edge_data.size > 0:
                        last_edge = edge_data
                        break

    def _write_lightweight_record(
        file_path: Path,
        frame_shape: tuple[int, int],
        yolo_dets: list[YoloDetection],
        results: list[Any],
        timings: dict[str, float],
        error: str | None,
    ) -> None:
        record = _build_lightweight_record(file_path, frame_shape, yolo_dets, results, timings, error)
        json_path = json_dir / f"{file_path.stem}.json"
        try:
            json_path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        except Exception:
            logger.exception("Failed to write lightweight JSON for %s", file_path.name)

    def _write_failure_record(
        file_path: Path,
        frame_shape: tuple[int, int],
        yolo_dets: list[YoloDetection] | None = None,
        error: str | None = None,
        t_total: float = 0,
    ) -> None:
        _write_lightweight_record(file_path, frame_shape, yolo_dets or [], [], {"total": t_total}, error)

    def save_overlay() -> None:
        if last_overlay is None or last_path is None:
            return
        out_path = overlays_dir / f"{last_path.stem}.overlay.jpg"
        try:
            cv2.imwrite(str(out_path), last_overlay)
            logger.info("Saved overlay: %s", out_path)
            print(f"  Saved overlay: {out_path}")
        except Exception:
            traceback.print_exc()
            logger.exception("Failed to save overlay for %s", last_path.name)

    def save_edges() -> None:
        if last_edge is None or last_path is None:
            return
        out_path = edges_dir / f"{last_path.stem}.edges.png"
        try:
            cv2.imwrite(str(out_path), last_edge)
            logger.info("Saved edges: %s", out_path)
            print(f"  Saved edges: {out_path}")
        except Exception:
            traceback.print_exc()
            logger.exception("Failed to save edges for %s", last_path.name)

    def save_full_snapshot() -> None:
        if last_path is None:
            return
        # Save overlay
        save_overlay()
        # Save edges
        save_edges()
        # Build full JSON record
        try:
            record: dict[str, Any] = {
                "image": str(last_path.name),
                "image_path": str(last_path),
                "debug_level": level,
                "config": dataclasses.asdict(config),
                "results": [_sanitize_for_json(r) for r in last_results],
                "yolo_detections": [_sanitize_for_json(d) for d in last_yolo_dets],
                "success": last_error is None,
                "overlay_path": str(overlays_dir / f"{last_path.stem}.overlay.jpg"),
                "edges_path": str(edges_dir / f"{last_path.stem}.edges.png") if last_edge is not None else None,
            }
            if last_error:
                record["error"] = last_error
            if last_timings:
                record["timings_ms"] = {k: round(v * 1000, 3) for k, v in last_timings.items()}

            json_path = json_dir / f"{last_path.stem}.full.json"
            json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Saved full snapshot: %s", json_path)
            print(f"  Saved full snapshot: {json_path}")
        except Exception:
            traceback.print_exc()
            logger.exception("Failed to save full snapshot for %s", last_path.name)

    def reload_config() -> None:
        """Reread debug_config.json and rerun current image."""
        nonlocal config
        try:
            new_cfg = _load_config(config_path)
            if level <= 1:
                new_cfg.debug_mode = "basic"
            else:
                new_cfg.debug_mode = "verbose"
            config = new_cfg
            logger.info("Config reloaded from %s (debug_mode=%s)", config_path, config.debug_mode)
            print(f"\n  Config reloaded: debug_mode={config.debug_mode}\n")
            process_image(current_idx)
        except Exception:
            print(f"\n  ERROR: config reload failed — keeping last valid state\n")
            traceback.print_exc()
            logger.exception("Config reload failed for %s", config_path)

    # Initial processing
    process_image(current_idx)

    # Window setup
    WINDOW_NAME = "Hex Debugger"
    EDGE_WINDOW = "Canny Edges"
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    if level >= 2:
        cv2.namedWindow(EDGE_WINDOW, cv2.WINDOW_NORMAL)

    # -----------------------------------------------------------------------
    # Navigation loop
    # -----------------------------------------------------------------------

    # Known key codes for arrow keys across backends
    RIGHT_KEYS = {ord("d"), ord("D"), 2555904, 65363, 2424832}   # D, Win32/Qt/Gtk right
    LEFT_KEYS = {ord("a"), ord("A"), 2424832, 65361, 2555904}    # A, Win32/Qt/Gtk left

    while True:
        if last_overlay is not None:
            cv2.imshow(WINDOW_NAME, last_overlay)

        # Edge window management
        if level >= 2 and last_edge is not None and last_edge.size > 0:
            edge_display = last_edge
            edge_bgr = cv2.cvtColor(edge_display, cv2.COLOR_GRAY2BGR)
            cv2.imshow(EDGE_WINDOW, edge_bgr)
        elif level < 2:
            try:
                cv2.destroyWindow(EDGE_WINDOW)
            except cv2.error:
                pass  # window already closed

        key = cv2.waitKeyEx(0)

        # --- Navigation ---
        if key in RIGHT_KEYS or key == ord("n"):
            if current_idx < len(image_paths) - 1:
                current_idx += 1
                process_image(current_idx)
            continue
        elif key in LEFT_KEYS or key == ord("p"):
            if current_idx > 0:
                current_idx -= 1
                process_image(current_idx)
            continue

        # --- Level switch ---
        elif key in (ord("0"), ord("1"), ord("2"), ord("3")):
            new_level = key - ord("0")
            if new_level != level:
                level = new_level
                if level <= 1:
                    config.debug_mode = "basic"
                else:
                    config.debug_mode = "verbose"
                print(f"\n  Debug level: {level} (debug_mode={config.debug_mode})\n")

                # Close/reopen edge window
                if level < 2:
                    try:
                        cv2.destroyWindow(EDGE_WINDOW)
                    except cv2.error:
                        pass
                elif level >= 2:
                    cv2.namedWindow(EDGE_WINDOW, cv2.WINDOW_NORMAL)

                # Reprocess if we need verbose data but only have basic
                if level >= 2 and config.debug_mode == "verbose" and last_results:
                    # Check if we already have verbose data
                    has_verbose = any(
                        "raw_lines" in r.debug and isinstance(r.debug.get("raw_lines"), list)
                        for r in last_results
                    )
                    if not has_verbose:
                        process_image(current_idx)
                        continue

                rerender_overlay()
            continue

        # --- Reload config ---
        elif key in (ord("r"), ord("R")):
            reload_config()
            continue

        # --- Save overlay ---
        elif key in (ord("s"), ord("S")):
            save_overlay()
            continue

        # --- Save edges ---
        elif key in (ord("e"), ord("E")):
            save_edges()
            continue

        # --- Full snapshot ---
        elif key in (ord("j"), ord("J")):
            save_full_snapshot()
            continue

        # --- Quit ---
        elif key in (ord("q"), ord("Q"), 27):  # Q, ESC
            break

    cv2.destroyAllWindows()
    logger.info("Debugger exited normally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
