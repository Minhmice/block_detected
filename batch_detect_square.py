import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch detect images and draw square boxes")
    parser.add_argument(
        "--model",
        default=str(BASE_DIR / "models" / "train-3.pt"),
        help="Path to YOLO model",
    )
    parser.add_argument("--input", default=str(BASE_DIR / "images"), help="Input image folder")
    parser.add_argument("--output", default=str(BASE_DIR / "images_out"), help="Output folder")
    parser.add_argument("--conf", type=float, default=0.01, help="Confidence threshold")
    parser.add_argument("--show", action="store_true", help="Show each annotated image")
    return parser.parse_args()


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def draw_square_box(img, x1, y1, x2, y2, color=(0, 255, 0), thickness=2):
    h, w = img.shape[:2]
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    side = max(x2 - x1, y2 - y1)

    sx1 = int(round(cx - side / 2.0))
    sy1 = int(round(cy - side / 2.0))
    sx2 = int(round(cx + side / 2.0))
    sy2 = int(round(cy + side / 2.0))

    sx1 = clamp(sx1, 0, w - 1)
    sy1 = clamp(sy1, 0, h - 1)
    sx2 = clamp(sx2, 0, w - 1)
    sy2 = clamp(sy2, 0, h - 1)

    cv2.rectangle(img, (sx1, sy1), (sx2, sy2), color, thickness)
    return sx1, sy1, sx2, sy2


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)
    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not model_path.exists():
        print(f"[ERROR] Model not found: {model_path}")
        return 1
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] Input folder invalid: {input_dir}")
        return 1

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_paths = [p for p in sorted(input_dir.iterdir()) if p.suffix.lower() in image_exts]
    if not image_paths:
        print(f"[ERROR] No images found in: {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(model_path))

    print(f"[INFO] Model: {model_path}")
    print(f"[INFO] Input images: {len(image_paths)}")
    print(f"[INFO] Output folder: {output_dir}")

    for idx, image_path in enumerate(image_paths, start=1):
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[WARN] Skip unreadable image: {image_path.name}")
            continue

        results = model.predict(source=img, conf=args.conf, verbose=False)
        result = results[0]
        names = result.names

        det_count = 0
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                sx1, sy1, sx2, sy2 = draw_square_box(img, x1, y1, x2, y2)
                det_count += 1
                label = f"{names.get(cls_id, cls_id)} {conf:.2f}"
                cv2.putText(
                    img,
                    label,
                    (sx1, max(sy1 - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

        out_path = output_dir / image_path.name
        cv2.imwrite(str(out_path), img)
        print(f"[{idx}/{len(image_paths)}] Saved: {out_path.name} | detections: {det_count}")

        if args.show:
            cv2.imshow("Detections (Square Boxes)", img)
            key = cv2.waitKey(0) & 0xFF
            if key == ord("q"):
                print("[INFO] Stop preview by user.")
                break

    if args.show:
        cv2.destroyAllWindows()

    print("[INFO] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
