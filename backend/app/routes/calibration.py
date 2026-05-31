"""Calibration save route."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.wire import CalibrationSaveWire

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_ROOT = (_REPO_ROOT / "config").resolve()


@router.post("/save")
async def save_calibration(body: CalibrationSaveWire) -> dict:
    raw_path = os.getenv("CALIBRATION_PATH", "config/calibration.json")
    path = Path(raw_path)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    resolved = path.resolve()
    if not resolved.is_relative_to(_CONFIG_ROOT):
        raise HTTPException(status_code=400, detail="calibration path outside config dir")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = body.model_dump(by_alias=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=resolved.parent) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.replace(resolved)
    return {"ok": True, "path": str(resolved)}
