# Copyright (c) 2024-2026 pilgrim_tabby

"""Tests for ui.split_navigation (including Toufool-style dummy groups)."""

from unittest.mock import MagicMock

from ui.split_navigation import (
    build_dummy_groups,
    group_contains_dummy,
    navigate_skip_split_group,
    navigate_to_next_split,
    navigate_to_previous_split,
    navigate_undo_split_group,
    skip_group_target_index,
    undo_group_target_index,
)


def _split(*, dummy: bool = False, loops: int = 1):
    s = MagicMock()
    s.dummy_flag = dummy
    s.loops = loops
    return s


def _splitter_stub(*, match_percent=None, continue_recording=False, splits=None):
    splitter = MagicMock()
    splitter.match_percent = match_percent
    splitter.continue_recording = continue_recording
    splitter.changing_splits = False
    splitter.waiting_for_split_change = False
    if splits is None:
        splits = [_split()]
    splitter.splits.list = splits
    splitter.splits.current_image_index = 0
    splitter.splits.current_loop = 1

    def jump_to(index: int) -> bool:
        if index >= len(splitter.splits.list):
            splitter.splits.current_image_index = len(splitter.splits.list) - 1
            splitter.splits.current_loop = splitter.splits.list[-1].loops
            return False
        splitter.splits.current_image_index = index
        splitter.splits.current_loop = 1
        return True

    splitter.splits.jump_to_split_image.side_effect = jump_to
    return splitter


def test_build_dummy_groups_matches_toufool():
    splits = [_split(dummy=True), _split(dummy=True), _split(), _split(dummy=True), _split()]
    assert build_dummy_groups(splits) == [[0, 1, 2], [3, 4]]


def test_build_dummy_groups_all_real():
    splits = [_split(), _split(), _split()]
    assert build_dummy_groups(splits) == [[0], [1], [2]]


def test_skip_and_undo_group_targets():
    groups = [[0, 1, 2], [3, 4]]
    assert skip_group_target_index(groups, 0) == 3
    assert skip_group_target_index(groups, 2) == 3
    assert skip_group_target_index(groups, 3) == 5
    assert undo_group_target_index(groups, 3) == 2
    assert undo_group_target_index(groups, 0) is None


def test_group_contains_dummy():
    splits = [_split(dummy=True), _split()]
    groups = build_dummy_groups(splits)
    assert group_contains_dummy(groups, splits, 0) is True
    assert group_contains_dummy(groups, splits, 1) is True


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


def test_navigate_skip_split_group_jumps_past_dummies():
    splits = [_split(dummy=True), _split(dummy=True), _split(), _split()]
    splitter = _splitter_stub(splits=splits)
    splitter.splits.current_image_index = 0
    assert navigate_skip_split_group(splitter, continue_recording=True) is True
    assert splitter.splits.current_image_index == 3


def test_navigate_undo_split_group_jumps_to_previous_real():
    splits = [_split(dummy=True), _split(), _split(dummy=True), _split()]
    splitter = _splitter_stub(splits=splits)
    splitter.splits.current_image_index = 2
    assert navigate_undo_split_group(splitter) is True
    assert splitter.splits.current_image_index == 1
