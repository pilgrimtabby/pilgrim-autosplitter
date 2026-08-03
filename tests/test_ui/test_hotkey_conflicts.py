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

"""Tests for hotkey conflict detection labels."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from ui.labels import SNAP_PEAK_HOTKEY_LABEL
from ui.ui_controller import UIController


class _HotkeyBox:
    def __init__(self, name: str, code: str) -> None:
        self._name = name
        self.key_code = code

    def text(self) -> str:
        return self._name


def _controller_with_bindings(codes):
    labels = [
        "Split",
        "Reset",
        "Pause",
        "Undo",
        "Skip",
        "Previous",
        "Next",
        "Screenshot",
        SNAP_PEAK_HOTKEY_LABEL,
        "Toggle Global Hotkeys",
    ]
    boxes = [_HotkeyBox(labels[i], codes[i]) for i in range(len(labels))]
    sw = SimpleNamespace(
        split_hotkey_box=boxes[0],
        reset_hotkey_box=boxes[1],
        pause_hotkey_box=boxes[2],
        undo_hotkey_box=boxes[3],
        skip_hotkey_box=boxes[4],
        previous_hotkey_box=boxes[5],
        next_hotkey_box=boxes[6],
        screenshot_hotkey_box=boxes[7],
        save_peak_hotkey_box=boxes[8],
        toggle_global_hotkeys_hotkey_box=boxes[9],
    )
    ctrl = object.__new__(UIController)
    ctrl._settings_window = sw
    return ctrl


def test_no_conflict_when_codes_unique():
    ctrl = _controller_with_bindings(
        ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]
    )
    assert ctrl._detect_hotkey_conflict() is None


def test_conflict_reports_snap_peak_label():
    ctrl = _controller_with_bindings(
        ["dup", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "dup", "c10"]
    )
    conflict = ctrl._detect_hotkey_conflict()
    assert conflict is not None
    a_label, b_label, _key = conflict
    assert SNAP_PEAK_HOTKEY_LABEL in (a_label, b_label)
    assert "Split" in (a_label, b_label)
