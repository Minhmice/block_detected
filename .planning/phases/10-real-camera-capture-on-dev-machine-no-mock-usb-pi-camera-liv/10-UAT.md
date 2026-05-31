# Phase 10 — User Acceptance Tests

**Phase:** Real camera on dev machine  
**Date:** 2026-05-31

---

## Test 1: Smoke capture

**Steps:**
```bash
source .venv/bin/activate
python scripts/camera_smoke.py --config config/camera.usb.mac.json --frames 3
```

**Expected:** Three JSON objects printed; each has `"shape": [480, 640, 3]` and `"source": "usb-opencv"`.

**Status:** ⬜ pending (requires camera permission)

---

## Test 2: Env boot (idle loop)

**Steps:**
```bash
cp .env.real.example .env
# start backend only or make dev
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

**Expected:** `"mockCamera": false`, `"detectionRunning": false`, `"cameraBackend": "usb"`.

**Status:** ⬜ pending

---

## Test 3: Console live feed

**Steps:**
1. `make dev` with `.env` from `.env.real.example`
2. Open http://localhost:3000
3. Click **INITIALIZE** — badge shows `LIVE_CAMERA — RUN_DETECTION` (not MOCK_MODE)
4. Click **RUN_DETECTION**
5. Camera viewport shows live MJPEG; FPS &gt; 0; WebSocket telemetry updates

**Expected:** Live video (not static `images/*.jpg` cycle); overlay updates when block in view.

**Status:** ⬜ pending

---

## Test 4: Permission recovery

**If** `camera_smoke` or START fails with `failed to open USB camera`:

1. System Settings → Privacy & Security → Camera → enable Terminal/Cursor
2. Quit and reopen terminal; retry smoke test
3. If still failing, try `"camera_index": 1` in `config/camera.usb.mac.json`

**Status:** ⬜ reference only

---

*Human checkpoint: Tests 1–3 must pass on dev Mac before phase sign-off.*
