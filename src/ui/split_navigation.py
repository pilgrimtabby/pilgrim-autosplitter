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

"""Thread-safe split index changes while compare_split may be active."""

from __future__ import annotations

import time
from typing import Callable

_CHANGE_WAIT_S = 1.0
_CHANGE_POLL_S = 0.001


def _change_split_image(splitter, move: Callable[[], None]) -> None:
    """Pause compare_split if active, change index, then release the pause."""
    if splitter.match_percent is None:
        move()
        return
    start_time = time.perf_counter()
    splitter.changing_splits = True
    while (
        time.perf_counter() - start_time < _CHANGE_WAIT_S
        and not splitter.waiting_for_split_change
    ):
        time.sleep(_CHANGE_POLL_S)
    move()
    splitter.changing_splits = False


def navigate_to_previous_split(splitter) -> None:
    """Move to the previous split image."""
    splitter.safe_exit_record_thread()
    _change_split_image(splitter, splitter.splits.previous_split_image)
    splitter.restart_record_thread()


def navigate_to_next_split(
    splitter,
    *,
    continue_recording: bool,
    split_hotkey_pressed: bool,
) -> bool:
    """Move to the next split image, or stop compare threads on final split.

    Returns:
        True when the split index changed and split labels should redraw.
    """
    if not continue_recording:
        splitter.safe_exit_record_thread()

    split_index = splitter.splits.current_image_index
    total_splits = len(splitter.splits.list) - 1
    loop = splitter.splits.current_loop
    total_loops = splitter.splits.list[split_index].loops
    if (
        split_index == total_splits
        and loop == total_loops
        and split_hotkey_pressed
    ):
        splitter.safe_exit_compare_split_thread()
        splitter.safe_exit_compare_reset_thread()
        changed_index = False
    else:
        _change_split_image(splitter, splitter.splits.next_split_image)
        changed_index = True

    if continue_recording:
        splitter.continue_recording = False
    else:
        splitter.restart_record_thread()

    return changed_index
