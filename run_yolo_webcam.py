import sys
from collections import deque
from pathlib import Path

import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DEFAULT_MODEL_NAME = "train-3.pt"
CAMERA_INDEX = 0
MAX_CAMERA_INDEX = 5
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
WINDOW_NAME = "YOLO Webcam Inference"
CONF_MIN = 0.001
CONF_MAX = 0.95
CONF_STEP = 0.001
OVERLAY_HISTORY = 5
EVAL_CONF = 0.01
BUTTON_MARGIN = 12
BUTTON_HEIGHT = 40
BUTTON_PAD_X = 14


def discover_model_paths() -> list[Path]:
    if not MODELS_DIR.is_dir():
        return []
    return sorted(p for p in MODELS_DIR.glob("*.pt") if p.is_file())


def default_model_index(model_paths: list[Path]) -> int:
    for index, path in enumerate(model_paths):
        if path.name == DEFAULT_MODEL_NAME:
            return index
    return 0


def extract_boxes(result):
    boxes = []
    if result.boxes is None:
        return boxes

    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        boxes.append((int(x1), int(y1), int(x2), int(y2)))
    return boxes


def draw_overlay_history(frame, history):
    if not history:
        return

    for age, boxes in enumerate(reversed(history), start=1):
        weight = age / len(history)
        color = (0, int(255 * weight), int(255 * (1.0 - weight)))
        thickness = 1 if age < len(history) else 2
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)


def draw_eval_boxes(frame, result):
    if result.boxes is None:
        return

    names = result.names
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        cv2.rectangle(frame, p1, p2, (0, 220, 255), 2)
        label = f"{names.get(cls_id, cls_id)} {conf * 100:.1f}%"
        label_y = max(p1[1] - 8, 0)
        cv2.putText(
            frame,
            label,
            (p1[0], label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )


def point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def draw_model_switch_button(frame, model_name: str) -> tuple[int, int, int, int]:
    """Draw clickable button; returns (x1, y1, x2, y2)."""
    label = f"  Model: {model_name}  |  Click or [V] next  "
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, scale, thickness)
    h, w = frame.shape[:2]

    btn_w = text_w + BUTTON_PAD_X * 2
    btn_h = max(BUTTON_HEIGHT, text_h + baseline + 12)
    x1 = BUTTON_MARGIN
    y2 = h - BUTTON_MARGIN
    y1 = y2 - btn_h
    x2 = min(x1 + btn_w, w - 1)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 40, 40), -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 120), 2)
    text_x = x1 + BUTTON_PAD_X
    text_y = y1 + (btn_h + text_h) // 2 - baseline
    cv2.putText(frame, label, (text_x, text_y), font, scale, (240, 240, 240), thickness, cv2.LINE_AA)
    return x1, y1, x2, y2


def open_camera(index: int) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    return cap


def on_mouse(event, x, y, _flags, state: dict) -> None:
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    rect = state.get("button_rect")
    if rect and point_in_rect(x, y, rect):
        state["switch_model"]()


def main() -> int:
    model_paths = discover_model_paths()
    if not model_paths:
        print(f"[ERROR] No .pt models found in: {MODELS_DIR}")
        return 1

    model_index = default_model_index(model_paths)
    current_path = model_paths[model_index]

    try:
        model = YOLO(str(current_path))
        print(f"[INFO] Loaded model ({model_index + 1}/{len(model_paths)}): {current_path.name}")
    except Exception as exc:
        print(f"[ERROR] Failed to load model: {exc}")
        return 1

    current_camera = CAMERA_INDEX
    cap = open_camera(current_camera)
    if cap is None:
        print(f"[ERROR] Failed to open webcam source: {CAMERA_INDEX}")
        return 1

    print(f"[INFO] Opened webcam source: {current_camera}")
    print(f"[INFO] Available models ({len(model_paths)}): {', '.join(p.name for p in model_paths)}")
    print("[INFO] Click the model button (bottom-left) or press 'v' to switch model.")
    print("[INFO] Press 'c' to switch camera source.")
    print("[INFO] Press Arrow Up/Down to increase/decrease confidence.")
    print("[INFO] Press 'm' to toggle multi-overlay history.")
    print("[INFO] Press 'n' to toggle eval mode (percentage labels).")
    print("[INFO] Press 'q' to quit.")

    conf = 0.25
    overlay_enabled = True
    eval_mode = False
    box_history = deque(maxlen=OVERLAY_HISTORY)
    ui_state: dict = {"button_rect": None}

    def switch_model() -> None:
        nonlocal model, model_index, current_path
        model_index = (model_index + 1) % len(model_paths)
        current_path = model_paths[model_index]
        try:
            model = YOLO(str(current_path))
            box_history.clear()
            print(f"[INFO] Switched model ({model_index + 1}/{len(model_paths)}): {current_path.name}")
        except Exception as exc:
            print(f"[ERROR] Failed to load model {current_path.name}: {exc}")

    ui_state["switch_model"] = switch_model

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, ui_state)

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("[WARN] Camera frame read failed. Stopping inference loop.")
                break

            try:
                active_conf = EVAL_CONF if eval_mode else conf
                results = model(frame, conf=active_conf, verbose=False)
                result = results[0]
                current_boxes = extract_boxes(result)
            except Exception as exc:
                print(f"[ERROR] Inference failed: {exc}")
                break

            if eval_mode:
                annotated = frame.copy()
                draw_eval_boxes(annotated, result)
                box_history.clear()
            else:
                annotated = result.plot()
                if overlay_enabled:
                    box_history.append(current_boxes)
                    draw_overlay_history(annotated, box_history)
                else:
                    box_history.clear()

            status = (
                f"mode: eval | conf: {EVAL_CONF:.3f} | model: {current_path.name}"
                if eval_mode
                else (
                    f"mode: normal | conf: {conf:.3f} | overlay: {'on' if overlay_enabled else 'off'}"
                    f" | model: {current_path.name}"
                )
            )
            cv2.putText(
                annotated,
                status,
                (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            ui_state["button_rect"] = draw_model_switch_button(annotated, current_path.name)
            cv2.imshow(WINDOW_NAME, annotated)

            key = cv2.waitKeyEx(1)
            if key == ord("c"):
                next_camera = (current_camera + 1) % (MAX_CAMERA_INDEX + 1)
                switched = False

                for _ in range(MAX_CAMERA_INDEX + 1):
                    new_cap = open_camera(next_camera)
                    if new_cap is not None:
                        cap.release()
                        cap = new_cap
                        current_camera = next_camera
                        switched = True
                        print(f"[INFO] Switched to webcam source: {current_camera}")
                        break
                    next_camera = (next_camera + 1) % (MAX_CAMERA_INDEX + 1)

                if not switched:
                    print("[WARN] No other camera source available to switch.")
            elif key in (ord("v"), ord("V")):
                switch_model()
            elif key == ord("n"):
                eval_mode = not eval_mode
                print(f"[INFO] Eval mode: {'ON' if eval_mode else 'OFF'}")
            elif key == 2490368:
                if eval_mode:
                    print("[INFO] Arrow Up disabled in eval mode.")
                else:
                    conf = min(CONF_MAX, conf + CONF_STEP)
                    print(f"[INFO] Confidence increased to: {conf:.3f}")
            elif key == 2621440:
                if eval_mode:
                    print("[INFO] Arrow Down disabled in eval mode.")
                else:
                    conf = max(CONF_MIN, conf - CONF_STEP)
                    print(f"[INFO] Confidence decreased to: {conf:.3f}")
            elif key == ord("m"):
                overlay_enabled = not overlay_enabled
                print(f"[INFO] Multi-overlay: {'ON' if overlay_enabled else 'OFF'}")
            elif key == ord("q"):
                print("[INFO] Quit requested by user (q key).")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released and windows destroyed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
