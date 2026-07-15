# Copyright (c) 2024-2025 pilgrim_tabby
# All rights reserved.

"""Tests for burst screenshot helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import settings
from ui.screenshot_capture import ScreenshotCapture


@pytest.fixture
def capture(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings,
        "get_str",
        lambda key: str(tmp_path) if key == "BURST_SHOTS_BASE_DIR" else "",
    )
    return ScreenshotCapture(MagicMock())


def test_dated_session_folders_default_true(capture, monkeypatch):
    monkeypatch.setattr(settings.settings, "contains", lambda key: False)
    assert capture.dated_session_folders_enabled() is True


def test_dated_session_folders_respects_setting(capture, monkeypatch):
    monkeypatch.setattr(settings.settings, "contains", lambda key: True)
    monkeypatch.setattr(settings, "get_bool", lambda key: False)
    assert capture.dated_session_folders_enabled() is False


def test_make_burst_session_folder_unique(capture, tmp_path):
    first = capture.make_burst_session_folder(tmp_path)
    assert first.is_dir()
    assert first.name.startswith("Burst shots ")

    second = capture.make_burst_session_folder(tmp_path)
    assert second.is_dir()
    assert second != first
    assert " (" in second.name or second.name != first.name


def test_output_dir_falls_back_to_home(capture, monkeypatch, tmp_path):
    missing = tmp_path / "missing"
    monkeypatch.setattr(settings, "get_str", lambda key: str(missing))
    out = Path(capture.output_dir_str())
    assert out == Path.home()
