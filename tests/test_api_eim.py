"""Edge Impulse model selection API tests."""

from __future__ import annotations

import importlib
import sys
from unittest import mock

import numpy as np
import pytest
from fastapi.testclient import TestClient


def _reload_app(monkeypatch: pytest.MonkeyPatch):
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    monkeypatch.setenv("MOCK_CAMERA", "true")
    monkeypatch.setenv("DETECTION_MODE", "mock")
    monkeypatch.setenv("VISION_MOCK_MODE", "true")
    monkeypatch.delenv("EI_MODEL_PATH", raising=False)
    camera_runtime.set_mock(True)

    from app.services.eim_runtime import eim_runtime

    eim_runtime.reset_for_tests()

    import app.main as main_module
    import app.services.detection_loop as loop_module

    importlib.reload(loop_module)
    importlib.reload(main_module)
    return main_module, eim_runtime


def test_eim_config_lists_registry_models(monkeypatch: pytest.MonkeyPatch) -> None:
    main_module, _ = _reload_app(monkeypatch)
    client = TestClient(main_module.app)
    with client:
        response = client.get("/api/eim/config")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) >= 2
    ids = {model["id"] for model in data["models"]}
    assert "minhmice-v2" in ids
    assert "shit-v1" in ids


def test_eim_config_switch_model(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    main_module, eim_runtime = _reload_app(monkeypatch)

    fake_runner = mock.Mock()
    fake_runner.init = mock.Mock(return_value={})
    fake_runner.get_features_from_image = mock.Mock(
        return_value=(np.zeros(10, dtype=np.float32), None)
    )
    fake_runner.classify = mock.Mock(
        return_value={"result": {"classification": {"block_01": 0.9}}}
    )
    image_mod = mock.MagicMock()
    image_mod.ImageImpulseRunner = mock.Mock(return_value=fake_runner)

    with mock.patch.dict(
        sys.modules,
        {
            "edge_impulse_linux": mock.MagicMock(),
            "edge_impulse_linux.image": image_mod,
        },
    ):
        client = TestClient(main_module.app)
        with client:
            switch = client.post("/api/eim/config", json={"modelId": "shit-v1"})
            assert switch.status_code == 200
            assert switch.json()["selectedId"] == "shit-v1"

            health = client.get("/health")
            assert health.status_code == 200
            assert health.json()["eiModelId"] == "shit-v1"
            assert health.json()["eiModelLabel"] == "shit v1"

    assert eim_runtime.get_selected_id() == "shit-v1"
