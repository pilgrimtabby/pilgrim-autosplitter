# Copyright (c) 2024-2025 pilgrim_tabby
# All rights reserved.

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
