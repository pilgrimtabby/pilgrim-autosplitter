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

"""Tests for paths.py (source vs frozen locations)."""

from __future__ import annotations

from pathlib import Path

import paths


def test_project_root_is_repo_when_not_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    root = paths.project_root()
    assert (root / "src" / "paths.py").is_file()
    assert (root / "src").is_dir()


def test_default_saves_dir_uses_repo_saves_when_not_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    assert paths.default_saves_dir() == paths.project_root() / "saves"


def test_default_saves_dir_uses_documents_when_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    expected = Path.home() / "Documents" / "Pilgrim Autosplitter" / "saves"
    assert paths.default_saves_dir() == expected


def test_resources_dir_uses_meipass_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert paths.resources_dir() == tmp_path / "resources"
