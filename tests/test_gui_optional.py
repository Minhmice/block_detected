"""GUI package should stay optional for CLI/test users."""


def test_gui_module_imports_without_requiring_pyside():
    from block_detected.apps.gui import app

    assert callable(app.main)
