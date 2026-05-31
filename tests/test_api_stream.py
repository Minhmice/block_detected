"""MJPEG stream tests."""

from __future__ import annotations

import os


def test_mjpeg_content_type() -> None:
    """Verify MJPEG route declares multipart/x-mixed-replace (body read hangs in TestClient)."""
    os.environ.setdefault("MOCK_CAMERA", "true")
    from app.main import app

    paths = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            paths.append(path)
    assert "/video/stream" in paths
    content = open(
        os.path.join(os.path.dirname(__file__), "..", "backend", "app", "routes", "stream.py"),
        encoding="utf-8",
    ).read()
    assert "multipart/x-mixed-replace" in content
