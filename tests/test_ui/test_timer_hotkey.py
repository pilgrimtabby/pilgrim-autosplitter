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

"""Tests for ui.timer_hotkey."""

from unittest.mock import MagicMock

from ui.timer_hotkey import hotkey_not_caught, press_hotkey_or_fallback


def test_hotkey_not_caught_when_unfocused_and_not_global():
    assert hotkey_not_caught(None, False) is True
    assert hotkey_not_caught(MagicMock(), True) is False


def test_press_hotkey_or_fallback_empty_key():
    pressed = []
    fallback = []

    press_hotkey_or_fallback(
        "",
        pressed.append,
        focus_window=None,
        global_hotkeys_enabled=False,
        fallback=lambda: fallback.append(1),
    )
    assert pressed == []
    assert fallback == [1]


def test_press_hotkey_or_fallback_uses_fallback_when_not_caught():
    pressed = []
    fallback = []

    press_hotkey_or_fallback(
        "x",
        pressed.append,
        focus_window=None,
        global_hotkeys_enabled=False,
        fallback=lambda: fallback.append(1),
    )
    assert pressed == ["x"]
    assert fallback == [1]
