"""GUI entry should be importable (PySide6 required at runtime)."""

import ast
from pathlib import Path


def test_gui_main_is_callable():
    from block_detected.apps.gui import app

    assert callable(app.main)


def test_main_py_delegates_to_gui_main():
    main_path = Path(__file__).resolve().parents[1] / "main.py"
    tree = ast.parse(main_path.read_text(encoding="utf-8"))
    imports = [
        node.names[0].name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "block_detected.apps.gui.app"
    ]
    assert "main" in imports


def test_console_script_target_matches_gui_main():
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["block-detected"] == "block_detected.apps.gui.app:main"


def test_print_missing_qt_returns_nonzero():
    from block_detected.apps.gui import app

    assert app._print_missing_qt() == 1
