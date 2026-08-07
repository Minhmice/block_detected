from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from . import config
from .models import Point2D
from .pipeline import detect_raw_hexagons
from .preprocessing import preprocess
from .roi import ROIBox

_PKG_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = _PKG_DIR / "benchmark_output"


def dataset_dir() -> Path:
    return _PKG_DIR.parent.parent / "block_dataset"


def list_dataset() -> List[Path]:
    return sorted(dataset_dir().glob("dt*.jpg"), key=lambda p: int(p.stem[2:]))


def draw_roi(img: np.ndarray, roi: ROIBox, color: tuple[int, int, int] = (255, 180, 0)) -> None:
    overlay = img.copy()
    overlay[roi.mask > 0] = (overlay[roi.mask > 0] * 0.55 + np.array(color) * 0.45).astype(np.uint8)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    cv2.rectangle(img, (roi.x, roi.y), (roi.x + roi.w, roi.y + roi.h), color, 2)


def draw_hexagon(
    img: np.ndarray,
    points: dict[str, Point2D],
    color: tuple[int, int, int] = (0, 255, 0),
) -> None:
    order = ["A", "B", "C", "D", "E", "F", "A"]
    arr = np.array([[int(points[k].x), int(points[k].y)] for k in order], dtype=np.int32)
    cv2.polylines(img, [arr], False, color, 2)
    for label in "ABCDEF":
        pt = points[label]
        cv2.circle(img, (int(pt.x), int(pt.y)), 4, color, -1)


def process_image(path: Path) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False, "error": "read_failed"}

    color, gray = preprocess(frame)
    dets, meta = detect_raw_hexagons(color, gray)
    score = float(meta.get("score", 0.0))
    if dets and score == 0.0:
        score = max(d.score for d in dets)
    ok = bool(dets) and score >= config.DETECTION_SCORE_MIN
    result: dict = {
        "file": path.name,
        "ok": ok,
        "score": score,
        "stage": meta.get("stage"),
        "lines": meta.get("lines", 0),
        "roi_lines": meta.get("roi_lines", 0),
        "roi_area": meta.get("roi_area", 0),
        "yolo_count": meta.get("yolo_count", 0),
        "yolo_conf": meta.get("yolo_conf"),
    }
    if dets:
        from .score import edge_support, _polygon_area
        from .edges import detect_edges
        from .roi import extract_cluster_roi

        pts = dets[0].points
        edges, _ = detect_edges(gray)
        roi = extract_cluster_roi(edges, color.shape[:2], block_mode=config.BLOCK_MODE)
        if roi:
            masked = cv2.bitwise_and(edges, roi.mask)
            result["hex_area"] = _polygon_area([pts[k].as_tuple() for k in "ABCDEF"])
            result["edge_support"] = edge_support(pts, masked)
            result["points"] = {k: [pts[k].x, pts[k].y] for k in "ABCDEF"}
    return result


def render_overlay(path: Path, out_dir: Path) -> dict:
    result = process_image(path)
    frame = cv2.imread(str(path))
    if frame is None:
        return result

    color, gray = preprocess(frame)
    from .edges import detect_edges
    from .roi import extract_cluster_roi

    edges, _ = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=config.BLOCK_MODE)
    vis = color.copy()
    if roi:
        draw_roi(vis, roi)
        dets, _ = detect_raw_hexagons(color, gray)
        if dets:
            accepted = result.get("ok", False)
            draw_hexagon(vis, dets[0].points, (0, 255, 0) if accepted else (0, 140, 255))
            status = "OK" if accepted else "LOW"
            cv2.putText(
                vis,
                f"{path.stem} {status} score={result.get('score', 0):.2f}",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / f"{path.stem}_bench.jpg"), vis)
    return result


def run_benchmark(*, write_overlays: bool = True, out_dir: Optional[Path] = None) -> dict:
    base = out_dir or DEFAULT_OUT
    overlay_dir = base / "overlays"
    paths = list_dataset()
    results = []
    for p in paths:
        if write_overlays:
            results.append(render_overlay(p, overlay_dir))
        else:
            results.append(process_image(p))

    ok = [r for r in results if r.get("ok")]
    fail_roi = [r for r in results if r.get("stage") == "roi"]
    fail_fit = [r for r in results if r.get("stage") == "fit"]
    low_score = [r for r in results if r.get("score") is not None and not r.get("ok")]
    yolo_roi = [r for r in results if r.get("stage") == "yolo_roi"]
    edge_roi = [r for r in results if r.get("stage") == "edge_roi"]

    summary = {
        "total": len(results),
        "accepted": len(ok),
        "accept_rate": len(ok) / max(len(results), 1),
        "fail_roi": len(fail_roi),
        "fail_fit": len(fail_fit),
        "low_score": len(low_score),
        "yolo_roi": len(yolo_roi),
        "edge_roi": len(edge_roi),
        "avg_score": sum(r.get("score", 0) for r in ok) / max(len(ok), 1),
        "avg_hex_area": sum(r.get("hex_area", 0) for r in ok) / max(len(ok), 1),
    }
    base.mkdir(parents=True, exist_ok=True)
    report = {"summary": summary, "failures": [r["file"] for r in results if not r.get("ok")], "results": results}
    (base / "benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = run_benchmark()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
