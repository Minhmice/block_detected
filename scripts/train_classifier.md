# Classifier training scaffold (CLS-03)

1. Collect warped face PNGs via debug capture or `geometry_from_candidate` on labeled frames.
2. Train a small CNN (4 classes) and export TensorFlow Lite INT8:
   - Representative dataset for quantization
   - Output: `models/block_classifier_int8.tflite`
3. On Pi: set `config/classifier.example.json` → `"backend": "tflite"`.

Until a model exists, production dev uses `backend: stub` in tests and smoke runs.
