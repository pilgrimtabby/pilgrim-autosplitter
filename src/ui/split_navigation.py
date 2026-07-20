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

"""Thread-safe split index changes while compare_split may be active.

Dummy grouping matches Toufool AutoSplit: consecutive dummies plus the following
real split form one group. Skip/Undo jump by group; Next/Previous move one image.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional, Sequence

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


def build_dummy_groups(splits: Sequence) -> List[List[int]]:
    """Group split indices: dummies + following real split (Toufool-compatible)."""
    if not splits:
        return []
    groups: List[List[int]] = []
    current: List[int] = []
    groups.append(current)
    last = len(splits) - 1
    for i, split in enumerate(splits):
        current.append(i)
        if not getattr(split, "dummy_flag", False) and i < last:
            current = []
            groups.append(current)
    if groups and not groups[-1]:
        groups.pop()
    return groups


def skip_group_target_index(groups: Sequence[Sequence[int]], current_index: int) -> Optional[int]:
    """Index after the current group, or None if current_index is unknown."""
    for group in groups:
        if current_index in group:
            return group[-1] + 1
    return None


def undo_group_target_index(groups: Sequence[Sequence[int]], current_index: int) -> Optional[int]:
    """Last index of the previous group, or None if already in the first group."""
    for i, group in enumerate(groups):
        if current_index in group:
            if i == 0:
                return None
            return groups[i - 1][-1]
    return None


def group_contains_dummy(groups: Sequence[Sequence[int]], splits: Sequence, current_index: int) -> bool:
    """True if the group containing current_index includes a dummy split."""
    for group in groups:
        if current_index in group:
            return any(getattr(splits[i], "dummy_flag", False) for i in group)
    return False


def navigate_to_previous_split(splitter) -> None:
    """Move to the previous split image (one image / loop — not a dummy group)."""
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


def navigate_skip_split_group(splitter, *, continue_recording: bool) -> bool:
    """Skip the current dummy group (or single real split), Toufool-style.

    Returns:
        True when split labels should redraw.
    """
    splits = splitter.splits
    index = splits.current_image_index
    if index is None or len(splits.list) == 0:
        return False

    groups = build_dummy_groups(splits.list)
    target = skip_group_target_index(groups, index)
    if target is None:
        return False

    if not continue_recording:
        splitter.safe_exit_record_thread()

    past_end = target >= len(splits.list)

    def move() -> None:
        splits.jump_to_split_image(target)

    _change_split_image(splitter, move)

    if past_end:
        splitter.safe_exit_compare_split_thread()
        splitter.safe_exit_compare_reset_thread()

    if continue_recording:
        splitter.continue_recording = False
    else:
        splitter.restart_record_thread()

    return True


def navigate_undo_split_group(splitter) -> bool:
    """Undo to the previous dummy group's real split (Toufool-style).

    Returns:
        True when the index changed and labels should redraw.
    """
    splits = splitter.splits
    index = splits.current_image_index
    if index is None or len(splits.list) == 0:
        return False

    groups = build_dummy_groups(splits.list)
    target = undo_group_target_index(groups, index)
    if target is None:
        return False

    splitter.safe_exit_record_thread()

    def move() -> None:
        splits.jump_to_split_image(target)

    _change_split_image(splitter, move)
    splitter.restart_record_thread()
    return True
