"""Dataset frame save route."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.schemas.wire import DatasetSaveWire

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _dataset_root() -> Path:
    raw = os.getenv("DATASET_DIR", "datasets/captured")
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


@router.post("/save-frame")
async def save_frame(request: Request, body: DatasetSaveWire | None = None) -> dict:
    loop = request.app.state.detection_loop
    jpeg = loop.latest_jpeg()
    if jpeg is None:
        raise HTTPException(status_code=503, detail="no frame available")

    root = _dataset_root()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"frame_{stamp}.jpg"
    target = (root / filename).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=400, detail="invalid save path")
    target.write_bytes(jpeg)
    return {"ok": True, "path": str(target), "reason": body.reason if body else None}
