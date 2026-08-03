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

"""Tests for ui.video_crop."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QApplication

import settings
from ui.ui_main_window import UIMainWindow
from ui.video_crop import VideoCropController


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp, monkeypatch):
    monkeypatch.setattr(settings, "get_str", lambda key: "")
    return UIMainWindow()


@pytest.fixture
def crop_ctrl(main_window, monkeypatch):
    stored = {
        "VIDEO_CROP_INSET_LEFT": 0,
        "VIDEO_CROP_INSET_RIGHT": 0,
        "VIDEO_CROP_INSET_TOP": 0,
        "VIDEO_CROP_INSET_BOTTOM": 0,
    }

    monkeypatch.setattr(settings, "get_str", lambda key: "")
    monkeypatch.setattr(settings, "get_int_nonneg", lambda key: stored.get(key, 0))
    monkeypatch.setattr(
        settings,
        "set_value",
        lambda key, val: stored.__setitem__(key, val),
    )

    ctrl = MagicMock()
    ctrl._main_window = main_window
    crop = VideoCropController(ctrl)
    return crop, stored


def test_undo_redo_persists_insets(crop_ctrl):
    crop, stored = crop_ctrl
    mw = crop._ctrl._main_window
    mw.video_crop_spin_left.setValue(4)
    crop.on_spin_changed(4)
    assert stored["VIDEO_CROP_INSET_LEFT"] == 4

    crop.undo()
    assert stored["VIDEO_CROP_INSET_LEFT"] == 0
    assert mw.video_crop_spin_left.value() == 0

    crop.redo()
    assert stored["VIDEO_CROP_INSET_LEFT"] == 4


def test_reset_insets_clears_all(crop_ctrl):
    crop, stored = crop_ctrl
    mw = crop._ctrl._main_window
    for spin, val in zip(
        (
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
        ),
        (2, 3, 4, 5),
    ):
        spin.setValue(val)
        crop.on_spin_changed(val)

    crop.reset_insets()
    assert crop.tuple_from_widgets() == (0, 0, 0, 0)
    for key in (
        "VIDEO_CROP_INSET_LEFT",
        "VIDEO_CROP_INSET_RIGHT",
        "VIDEO_CROP_INSET_TOP",
        "VIDEO_CROP_INSET_BOTTOM",
    ):
        assert stored[key] == 0
