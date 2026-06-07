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
