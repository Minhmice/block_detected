"""Edge Impulse model selection routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.wire import EimConfigUpdateWire, EimConfigWire, EimModelWire
from app.services.edge_impulse_runner import ei_runner_service
from app.services.eim_model import (
    get_selected_model_entry,
    is_vision_mock_mode,
    list_eim_models,
    resolve_eim_path,
    resolve_selected_model_id,
    validate_eim_model,
)
from app.services.eim_runtime import eim_runtime

router = APIRouter(prefix="/api/eim", tags=["eim"])


def _build_config_wire() -> EimConfigWire:
    selected_id = resolve_selected_model_id()
    selected = get_selected_model_entry()
    status = validate_eim_model()
    models = [
        EimModelWire(
            id=entry.id,
            label=entry.label,
            path=str(entry.path),
            executable=entry.executable,
        )
        for entry in list_eim_models()
    ]
    return EimConfigWire(
        models=models,
        selected_id=selected_id,
        selected_path=str(status.path),
        selected_executable=status.executable,
        vision_mock_mode=is_vision_mock_mode(),
    )


@router.get("/config", response_model=EimConfigWire)
async def get_config() -> EimConfigWire:
    return _build_config_wire()


@router.post("/config", response_model=EimConfigWire)
async def update_config(body: EimConfigUpdateWire, request: Request) -> EimConfigWire:
    models = list_eim_models()
    valid_ids = {model.id for model in models}
    if body.model_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"unknown model id: {body.model_id!r}")

    entry = next(model for model in models if model.id == body.model_id)
    status = validate_eim_model(entry.path)
    if not status.executable:
        raise HTTPException(status_code=400, detail=status.error or "model not executable")

    loop = request.app.state.detection_loop
    was_running = loop.running
    if was_running:
        await loop.stop()

    eim_runtime.set_selected_id(body.model_id)
    ei_runner_service.reload()
    # #region agent log
    try:
        import json as _json
        import time as _time
        from pathlib import Path as _Path

        _log_path = _Path(__file__).resolve().parents[3] / ".cursor" / "debug-7b62f0.log"
        with _log_path.open("a", encoding="utf-8") as _f:
            _f.write(
                _json.dumps(
                    {
                        "sessionId": "7b62f0",
                        "timestamp": int(_time.time() * 1000),
                        "location": "eim.py:update_config",
                        "message": "model switched",
                        "data": {
                            "model_id": body.model_id,
                            "vision_mock_mode": is_vision_mock_mode(),
                            "was_running": was_running,
                        },
                        "hypothesisId": "C",
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion

    if was_running and not is_vision_mock_mode():
        await loop.start()

    return _build_config_wire()
