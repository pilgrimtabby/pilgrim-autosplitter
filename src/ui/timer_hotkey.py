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

"""Simulate timer hotkeys when the external app does not receive the key."""

from __future__ import annotations

from typing import Callable


def hotkey_not_caught(focus_window, global_hotkeys_enabled: bool) -> bool:
    """True when a local hotkey press would not reach the focused timer app."""
    return focus_window is None and not global_hotkeys_enabled


def press_hotkey_or_fallback(
    key_code: str,
    press_and_release: Callable[[str], None],
    *,
    focus_window,
    global_hotkeys_enabled: bool,
    fallback: Callable[[], None],
) -> None:
    """Press a configured hotkey, or run fallback if it would not be caught."""
    if len(key_code) > 0:
        press_and_release(key_code)
    if len(key_code) == 0 or hotkey_not_caught(focus_window, global_hotkeys_enabled):
        fallback()
