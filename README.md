# Block Detected

Non-ArUco cube block detection pipeline for robot pick-and-place, plus a Next.js operator console backed by FastAPI.

## Detection Console UI

### Local development

1. **Python backend**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   pip install -r backend/requirements.txt
   cp .env.example .env
   cp frontend/.env.local.example frontend/.env.local
   ```

2. **Frontend**
   ```bash
   cd frontend && npm install && cd ..
   npm install   # root concurrently for dev:all
   ```

3. **Start both**
   ```bash
   make dev
   # or: npm run dev:all
   ```
   Open http://localhost:3000

### Mock vs real camera

| Mode | Env vars | Behavior |
|------|----------|----------|
| Mock (dev) | `MOCK_CAMERA=true` or `DETECTION_MODE=mock` | Cycles `images/*.jpg`; auto-starts detection loop |
| Real USB | `MOCK_CAMERA=false`, `CAMERA_CONFIG=config/camera.usb.mac.json` | OpenCV VideoCapture (AVFoundation on macOS) |
| Pi CSI | `MOCK_CAMERA=false`, profile `picamera2` | Requires picamera2 on device |

### Real camera on dev Mac

1. Copy env template: `cp .env.real.example .env`
2. Grant **Terminal** or **Cursor** camera access: **System Settings → Privacy & Security → Camera**
3. Smoke test (no backend required):
   ```bash
   python scripts/camera_smoke.py --config config/camera.usb.mac.json --frames 3
   ```
   Expect three JSON lines with `"shape": [480, 640, 3]`.
4. Start console: `make dev` → open http://localhost:3000 → **INITIALIZE** → **RUN_DETECTION**

Detection does **not** auto-start when `MOCK_CAMERA=false`; click **RUN_DETECTION** to open the camera.

If `camera_smoke` fails with `failed to open USB camera`, check camera permission or try `camera_index: 1` in `config/camera.usb.mac.json`.

### Docker

```bash
docker compose up --build
```

### Raspberry Pi

- Install `python3-picamera2` via apt for CSI camera
- Deploy `block_detected` package + `backend/` + Edge Impulse `.eim` model
- Set `MOCK_CAMERA=false` and tune `config/camera.example.json`
- Run backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`

## Edge Impulse (.eim) deployment

Deploy the Linux AARCH64 impulse exported from Edge Impulse Studio for on-device classification on Raspberry Pi 5.

### Model placement

Two Linux AARCH64 impulses are registered in [`config/eim_models.json`](config/eim_models.json):

```bash
chmod +x models/minhmice-project-1-linux-aarch64-v1-impulse-#2.eim
chmod +x models/shit-linux-aarch64-v1-impulse-#1.eim
```

Optional legacy single-path override (gitignored deploy copy):

```bash
cp models/minhmice-project-1-linux-aarch64-v1-impulse-#2.eim backend/models/block_detector.eim
chmod +x backend/models/block_detector.eim
```

Model binaries under `backend/models/*.eim` are gitignored. Registry paths under `models/` are tracked.

### System dependencies (Raspberry Pi / Debian)

```bash
sudo apt-get install -y libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
pip install -r backend/requirements.txt
# PyAudio is pulled via requirements.txt; on Pi you may prefer: sudo apt-get install python3-pyaudio
```

### Environment

| Variable | Example | Purpose |
|----------|---------|---------|
| `EI_MODELS_CONFIG` | `config/eim_models.json` | Registry of selectable `.eim` models |
| `EI_MODEL_ID` | `minhmice-v2` | Default selected model id (bootstrap) |
| `EI_MODEL_PATH` | *(empty)* | Optional override path to a single `.eim` |
| `VISION_MOCK_MODE` | `true` (dev Mac) / `false` (Pi 5) | Skip EI and return stable mock detections |

Add to `.env` (see `.env.example`):

```
EI_MODELS_CONFIG=config/eim_models.json
EI_MODEL_ID=minhmice-v2
EI_MODEL_PATH=
VISION_MOCK_MODE=true
```

### Run and verify

```bash
cp .env.example .env
make dev
curl http://127.0.0.1:8000/health
open http://localhost:3000
```

`/health` returns Edge Impulse status fields:

- `eiModelId` / `eiModelLabel` — selected registry entry
- `visionMockMode` — when true, EI runner is not loaded
- `eiModelLoaded` — true when model is executable and mock mode is off
- `eiModelExecutable` — file exists and has execute permission
- `eiModelError` — actionable message (e.g. missing file or `chmod +x` hint)

On Pi 5 with live camera: set `VISION_MOCK_MODE=false`, ensure models are executable, pick a model in the console **Model** panel, then **RUN_DETECTION**.

Reference test (Pi, live EIM):

```bash
PYTHONPATH=backend:src pytest tests/test_reference_four_blocks.py -k live -v
```

### Reference UI

Static HTML mockups live in `example_ui/` (reference only — do not delete).

## Tests

```bash
source .venv/bin/activate
PYTHONPATH=backend:src pytest tests/ -q
```
