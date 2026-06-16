from pathlib import Path

from ultralytics import YOLO

MODELS_DIR = Path(__file__).resolve().parent / "models"

# Load model from models/
model = YOLO(str(MODELS_DIR / "rbs-final.pt"))

# Export ONNX — Ultralytics saves beside the .pt by default
model.export(format="onnx")
print(f"Saved: {MODELS_DIR / 'rbs-final.onnx'}")

model.export(format="onnx", int8=True, data="coco8.yaml")
print(f"Saved: {MODELS_DIR / 'rbs-final_int8.onnx'}")