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

"""Tests for Snap Peak / Peak Buffer screenshot capture."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import settings
from ui.screenshot_capture import (
    PEAK_BUFFER_DIALOG_TITLE,
    PEAK_BUFFER_SAVED_SUMMARY,
    PEAK_BUFFER_SUBDIR,
    SNAP_PEAK_HOTKEY_LABEL,
    ScreenshotCapture,
)


@pytest.fixture
def screenshot_capture(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings,
        "get_str",
        lambda key: str(tmp_path) if key == "BURST_SHOTS_BASE_DIR" else "",
    )
    monkeypatch.setattr(settings, "get_bool", lambda key: False)
    monkeypatch.setattr(settings, "get_int", lambda key: 2 if key == "MATCH_PERCENT_DECIMALS" else 0)
    ctrl = MagicMock()
    ctrl._splitter = MagicMock()
    return ScreenshotCapture(ctrl)


def test_peak_buffer_user_facing_labels():
    assert SNAP_PEAK_HOTKEY_LABEL == "Snap Peak"
    assert PEAK_BUFFER_DIALOG_TITLE == "Snapped Peak Buffer"
    assert PEAK_BUFFER_SAVED_SUMMARY == "Peak Buffer saved to:"
    assert PEAK_BUFFER_SUBDIR == "peak_buffer"


def test_peak_filename_part_respects_decimals(screenshot_capture, monkeypatch):
    monkeypatch.setattr(settings, "get_int", lambda key: 1 if key == "MATCH_PERCENT_DECIMALS" else 0)
    assert screenshot_capture.peak_filename_part(0.876) == "87.6"


def test_sanitize_peak_filename_part():
    cap = ScreenshotCapture(MagicMock())
    assert cap.sanitize_peak_filename_part("Boss Fight #2") == "Boss_Fight_2"
    assert cap.sanitize_peak_filename_part("   ") == "split"


def test_peak_buffer_output_dir(screenshot_capture, tmp_path):
    out = screenshot_capture.peak_buffer_output_dir()
    assert out == tmp_path / PEAK_BUFFER_SUBDIR
    assert out.is_dir()


def test_paths_for_count_skips_used_prefixes(tmp_path):
    (tmp_path / "001_screenshot.png").write_bytes(b"x")
    (tmp_path / "002_screenshot.png").write_bytes(b"x")
    cap = ScreenshotCapture(MagicMock())
    paths = cap.paths_for_count(str(tmp_path), 2)
    assert paths[0].endswith("000_screenshot.png")
    assert paths[1].endswith("003_screenshot.png")


@patch("ui.screenshot_capture.cv2.imwrite", return_value=True)
def test_save_peak_buffer_writes_under_peak_buffer(
    mock_imwrite, screenshot_capture, tmp_path
):
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    screenshot_capture._ctrl._splitter.get_highest_similarity_snapshot.return_value = (
        frame,
        0.91,
        0.85,
        "Test Split",
    )
    shown = {}

    def _show_saved_dialog(**kwargs):
        shown.update(kwargs)

    screenshot_capture.show_saved_dialog = _show_saved_dialog

    screenshot_capture.save_peak_buffer()

    mock_imwrite.assert_called_once()
    out_path = Path(mock_imwrite.call_args[0][0])
    assert PEAK_BUFFER_SUBDIR in out_path.parts
    assert "Test_Split" in out_path.name
    assert "high91.00" in out_path.name
    assert "thresh85.00" in out_path.name
    assert shown["window_title"] == PEAK_BUFFER_DIALOG_TITLE
    assert shown["title"] == PEAK_BUFFER_DIALOG_TITLE
    assert shown["summary"] == PEAK_BUFFER_SAVED_SUMMARY


def test_save_peak_buffer_no_op_without_frame(screenshot_capture):
    screenshot_capture._ctrl._splitter.get_highest_similarity_snapshot.return_value = (
        None,
        0.0,
        0.0,
        "split",
    )
    with patch("ui.screenshot_capture.cv2.imwrite") as mock_imwrite:
        screenshot_capture.save_peak_buffer()
        mock_imwrite.assert_not_called()
