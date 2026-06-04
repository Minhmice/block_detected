"""GUI entry should be importable (PySide6 required at runtime)."""


def test_gui_main_is_callable():
    from block_detected.apps.gui import app

    assert callable(app.main)
