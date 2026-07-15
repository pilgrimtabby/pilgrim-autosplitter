# Copyright (c) 2024-2025 pilgrim_tabby
# All rights reserved.

"""Tests for ui.profile_store."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import settings
from ui.profile_store import (
    PROFILE_SCHEMA_VERSION,
    PROFILE_SETTING_KEYS,
    ProfileStore,
)


@pytest.fixture
def profile_store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "get_str", lambda key: "" if key != "PROFILE_SAVE_DIR" else str(tmp_path))
    monkeypatch.setattr(settings, "set_value", lambda key, val: None)
    ctrl = MagicMock()
    ctrl._main_window.profile_recent_actions = [MagicMock() for _ in range(5)]
    return ProfileStore(ctrl)


def test_sanitize_profile_name_strips_invalid_chars(profile_store):
    assert profile_store.sanitize_profile_name("  Boss #1!  ") == "Boss 1"


def test_profile_payload_includes_schema_and_settings(profile_store, monkeypatch, tmp_path):
    split_dir = tmp_path / "splits"
    split_dir.mkdir()
    (split_dir / "001.png").write_bytes(b"x")

    def _get_str(key):
        mapping = {
            "LAST_IMAGE_DIR": str(split_dir),
            "FPS": "60",
            "ASPECT_RATIO": "480",
        }
        return mapping.get(key, "")

    monkeypatch.setattr(settings, "get_str", _get_str)
    monkeypatch.setattr(settings.settings, "contains", lambda key: key in PROFILE_SETTING_KEYS)

    payload = profile_store.profile_payload("Test Run")
    assert payload["schema_version"] == PROFILE_SCHEMA_VERSION
    assert payload["profile_name"] == "Test Run"
    assert payload["settings"]["FPS"] == "60"
    assert payload["split_dir"]["absolute"] == str(split_dir)
    assert payload["split_dir"]["files"][0]["name"] == "001.png"


def test_recent_paths_round_trip(profile_store, monkeypatch, tmp_path):
    stored = {}
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    for p in (a, b, c):
        p.write_text("{}", encoding="utf-8")

    def _set_value(key, val):
        stored[key] = val

    monkeypatch.setattr(settings, "set_value", _set_value)
    monkeypatch.setattr(settings, "get_str", lambda key: stored.get(key, ""))

    profile_store.set_profile_recent_paths([str(a), str(b)])
    assert profile_store.profile_recent_paths() == [str(a), str(b)]

    profile_store.push_recent_profile_path(str(c))
    assert profile_store.profile_recent_paths()[0] == str(c)


def test_resolve_split_dir_prefers_existing_absolute(profile_store, monkeypatch, tmp_path):
    split_dir = tmp_path / "my_splits"
    split_dir.mkdir()
    applied = {}

    monkeypatch.setattr(settings, "set_value", lambda k, v: applied.update({k: v}))

    profile_store.resolve_split_dir_after_load(
        {
            "absolute": str(split_dir),
            "relative_to_project": "missing/relative",
        }
    )
    assert applied["LAST_IMAGE_DIR"] == str(split_dir)


def test_display_profile_dir_hides_home_prefix(profile_store, monkeypatch):
    home = Path.home()
    assert profile_store.display_profile_dir(home / "Documents" / "profiles") == str(
        Path("Documents") / "profiles"
    )
