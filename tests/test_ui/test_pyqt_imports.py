# Copyright (c) 2024-2026 pilgrim_tabby

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Regression tests for PyQt5 symbol usage in src/ui (missing-import crashes)."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_UI_DIR = Path(__file__).resolve().parents[2] / "src" / "ui"


def _is_pyqt_symbol(name: str) -> bool:
    return len(name) >= 2 and name[0] == "Q" and name[1].isupper()


def _pyqt_imports(tree: ast.AST) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
            "PyQt5"
        ):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    return imported


def _local_definitions(tree: ast.AST) -> set[str]:
    defined: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
    return defined


def _pyqt_usages(tree: ast.AST) -> set[str]:
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if _is_pyqt_symbol(node.id):
                used.add(node.id)
    return used


def missing_pyqt_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return _pyqt_usages(tree) - _pyqt_imports(tree) - _local_definitions(tree)


@pytest.mark.parametrize(
    "path",
    sorted(_UI_DIR.glob("*.py")),
    ids=lambda p: p.name,
)
def test_ui_module_pyqt_symbols_are_imported(path: Path):
    missing = missing_pyqt_imports(path)
    assert not missing, f"{path.name}: PyQt symbols used but not imported: {sorted(missing)}"


def test_ui_modules_import_cleanly():
    for path in sorted(_UI_DIR.glob("*.py")):
        module_name = f"ui.{path.stem}"
        importlib.import_module(module_name)


def test_screenshot_capture_imports_qsizepolicy():
    """Sanity check for the Snap Peak / preview-popup crash (QSizePolicy)."""
    import ui.screenshot_capture as sc

    source = Path(sc.__file__).read_text(encoding="utf-8")
    assert "QSizePolicy" in source
    tree = ast.parse(source, filename=sc.__file__)
    assert "QSizePolicy" in _pyqt_imports(tree)
