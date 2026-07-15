# Copyright (c) 2024-2025 pilgrim_tabby
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
