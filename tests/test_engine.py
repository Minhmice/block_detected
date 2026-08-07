"""Tests for runtime engine behavior that does not require a real camera."""

import copy
from pathlib import Path

from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine


class _FakeDetector:
    def __init__(self, name: str = "old.pt") -> None:
        self._name = name
        self.closed = False

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float, **kwargs):
        raise AssertionError("not used")

    def close(self) -> None:
        self.closed = True


def test_switch_model_keeps_previous_detector_when_load_fails(monkeypatch):
    config = AppConfig.defaults()
    previous = _FakeDetector("old.pt")
    engine = WebcamEngine(config, [Path("old.pt"), Path("bad.pt")], previous)

    def fail_load(_path: Path):
        raise RuntimeError("bad model")

    monkeypatch.setattr("block_detected.runtime.engine.load_detector", fail_load)

    engine.switch_model()

    assert engine.detector is previous
    assert previous.closed is False
    assert engine.state.model_index == 0


def test_switch_model_persists_last_model_name(monkeypatch):
    config = AppConfig.defaults()
    previous = _FakeDetector("old.pt")
    replacement = _FakeDetector("new.pt")
    engine = WebcamEngine(config, [Path("old.pt"), Path("new.pt")], previous)
    saved: list[AppConfig] = []

    monkeypatch.setattr("block_detected.runtime.engine.load_detector", lambda _path: replacement)
    monkeypatch.setattr(
        "block_detected.runtime.engine.save_config",
        lambda cfg: saved.append(copy.deepcopy(cfg)),
    )

    engine.switch_model()

    assert engine.config.inference.last_model_name == "new.pt"
    assert len(saved) == 1
    assert saved[0].inference.last_model_name == "new.pt"


def test_switch_model_swaps_and_closes_previous_detector(monkeypatch):
    config = AppConfig.defaults()
    previous = _FakeDetector("old.pt")
    replacement = _FakeDetector("new.pt")
    engine = WebcamEngine(config, [Path("old.pt"), Path("new.pt")], previous)

    monkeypatch.setattr("block_detected.runtime.engine.load_detector", lambda _path: replacement)
    monkeypatch.setattr("block_detected.runtime.engine.save_config", lambda _config: None)

    engine.switch_model()

    assert engine.detector is replacement
    assert previous.closed is True
    assert engine.state.model_index == 1
