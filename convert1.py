"""Export .pt models to ONNX (detection + OBB)."""

from pathlib import Path

from ultralytics import YOLO

MODELS_DIR = Path(__file__).resolve().parent / "models"

# Models to export: each (filename, is_obb)
TARGETS = [
    ("rbs-final.pt", False),   # detection
    ("obb-111.pt", True),      # OBB
    ("obb-18.pt", True),       # OBB
]

for fname, is_obb in TARGETS:
    pt_path = MODELS_DIR / fname
    if not pt_path.is_file():
        print(f"Skip {fname} — not found")
        continue

    model = YOLO(str(pt_path))
    onnx_path = pt_path.with_suffix(".onnx")

    if onnx_path.is_file():
        print(f"Skip {fname} → {onnx_path.name} (already exists)")
        continue

    print(f"Export {fname} → {onnx_path.name} ...")
    model.export(format="onnx", imgsz=640)
    print(f"  OK: {onnx_path.name}")

print("\nDone.")
