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

"""Tests for ui.split_navigation."""

from unittest.mock import MagicMock

from ui.split_navigation import navigate_to_next_split, navigate_to_previous_split


def _splitter_stub(*, match_percent=None, continue_recording=False):
    splitter = MagicMock()
    splitter.match_percent = match_percent
    splitter.continue_recording = continue_recording
    splitter.changing_splits = False
    splitter.waiting_for_split_change = False
    splitter.splits.current_image_index = 0
    splitter.splits.current_loop = 1
    split = MagicMock()
    split.loops = 1
    splitter.splits.list = [split]
    return splitter


def test_navigate_previous_without_active_compare():
    splitter = _splitter_stub(match_percent=None)
    navigate_to_previous_split(splitter)
    splitter.safe_exit_record_thread.assert_called_once()
    splitter.splits.previous_split_image.assert_called_once()
    splitter.restart_record_thread.assert_called_once()
    assert splitter.changing_splits is False


def test_navigate_previous_waits_for_compare_pause():
    splitter = _splitter_stub(match_percent=0.5)
    splitter.waiting_for_split_change = True
    navigate_to_previous_split(splitter)
    assert splitter.changing_splits is False
    splitter.splits.previous_split_image.assert_called_once()


def test_navigate_next_on_last_split_via_hotkey_stops_threads():
    splitter = _splitter_stub()
    splitter.splits.current_image_index = 0
    splitter.splits.current_loop = 1
    changed = navigate_to_next_split(
        splitter, continue_recording=False, split_hotkey_pressed=True
    )
    assert changed is False
    splitter.safe_exit_compare_split_thread.assert_called_once()
    splitter.safe_exit_compare_reset_thread.assert_called_once()
    splitter.splits.next_split_image.assert_not_called()


def test_navigate_next_advances_index():
    splitter = _splitter_stub(match_percent=None)
    changed = navigate_to_next_split(
        splitter, continue_recording=False, split_hotkey_pressed=False
    )
    assert changed is True
    splitter.splits.next_split_image.assert_called_once()


def test_navigate_next_dummy_clears_continue_recording_flag():
    splitter = _splitter_stub(continue_recording=True)
    navigate_to_next_split(
        splitter, continue_recording=True, split_hotkey_pressed=False
    )
    assert splitter.continue_recording is False
    splitter.restart_record_thread.assert_not_called()
