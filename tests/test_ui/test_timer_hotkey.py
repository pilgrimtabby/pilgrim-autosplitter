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
