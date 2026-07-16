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
