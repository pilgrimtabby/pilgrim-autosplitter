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
