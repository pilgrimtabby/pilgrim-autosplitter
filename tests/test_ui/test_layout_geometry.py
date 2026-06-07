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

"""Geometry checks for bottom-row layout helpers in ui_controller."""

from __future__ import annotations

import os

# Headless CI / sandbox: avoid macOS GUI registration when constructing widgets.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication

from ui.layout_presets import (
    BOTTOM_ADJ_PAIR_GAP_PX,
    LAYOUT_PRESET_320,
    LAYOUT_PRESET_432,
    LAYOUT_PRESET_480,
    LAYOUT_PRESET_512,
    MAIN_WINDOW_LEFT_EDGE_CORRECTION,
    VIDEO_COL_CENTER_NUDGE_320,
    VIDEO_COL_CENTER_NUDGE_432,
    VIDEO_COL_STATS_SPAN_W,
    split_viewport_for_tests,
    video_viewport_for_tests,
)
from ui.ui_controller import UIController
from ui.ui_main_window import UIMainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    return UIMainWindow()


def _placer(main_window: UIMainWindow):
    obj = type("_Placer", (), {"_main_window": main_window})()

    def _layout_screenshot_burst_controls(_self, shot_rect: QRect) -> None:
        main_window.screenshot_button.setGeometry(shot_rect)
        main_window.reconnect_button.setGeometry(
            QRect(shot_rect.x(), shot_rect.y() + 50, shot_rect.width(), shot_rect.height())
        )

    obj._layout_screenshot_burst_controls = _layout_screenshot_burst_controls.__get__(
        obj, type(obj)
    )
    return obj


def _symmetric_margins(container: QRect, content_left: int, content_right: int) -> None:
    left = content_left - container.x()
    right = container.x() + container.width() - content_right
    assert abs(left - right) <= 1


_SPLIT_LAYOUT_PRESETS = (
    LAYOUT_PRESET_480,
    LAYOUT_PRESET_512,
    LAYOUT_PRESET_320,
    LAYOUT_PRESET_432,
)


@pytest.mark.parametrize("preset", _SPLIT_LAYOUT_PRESETS, ids=lambda p: p.aspect_ratio)
def test_split_column_pause_reset_gap(main_window, preset):
    placer = _placer(main_window)
    sc = preset.split_column
    split_viewport = split_viewport_for_tests(preset)
    UIController._place_split_column_bottom_controls(
        placer,
        split_viewport,
        row1=100,
        row2=150,
        pause_w=sc.pause_w,
        reset_w=sc.reset_w,
        gap_pause_to_reset=sc.gap_pause_to_reset,
        undo_w=sc.undo_w,
        skip_w=sc.skip_w,
    )
    pause = main_window.pause_button.geometry()
    reset = main_window.reset_button.geometry()
    assert reset.x() - pause.x() - pause.width() == sc.gap_pause_to_reset


@pytest.mark.parametrize("preset", _SPLIT_LAYOUT_PRESETS, ids=lambda p: p.aspect_ratio)
def test_split_column_cluster_centered(main_window, preset):
    placer = _placer(main_window)
    sc = preset.split_column
    split_viewport = split_viewport_for_tests(preset)
    UIController._place_split_column_bottom_controls(
        placer,
        split_viewport,
        row1=100,
        row2=150,
        pause_w=sc.pause_w,
        reset_w=sc.reset_w,
        gap_pause_to_reset=sc.gap_pause_to_reset,
        undo_w=sc.undo_w,
        skip_w=sc.skip_w,
    )
    pause = main_window.pause_button.geometry()
    reset = main_window.reset_button.geometry()
    _symmetric_margins(split_viewport, pause.x(), reset.x() + reset.width())


@pytest.mark.parametrize("preset", _SPLIT_LAYOUT_PRESETS, ids=lambda p: p.aspect_ratio)
def test_split_column_undo_skip_gap(main_window, preset):
    placer = _placer(main_window)
    sc = preset.split_column
    split_viewport = split_viewport_for_tests(preset)
    UIController._place_split_column_bottom_controls(
        placer,
        split_viewport,
        row1=100,
        row2=150,
        pause_w=sc.pause_w,
        reset_w=sc.reset_w,
        gap_pause_to_reset=sc.gap_pause_to_reset,
        undo_w=sc.undo_w,
        skip_w=sc.skip_w,
    )
    undo = main_window.undo_button.geometry()
    skip = main_window.skip_button.geometry()
    assert skip.x() - undo.x() - undo.width() == BOTTOM_ADJ_PAIR_GAP_PX


def test_320_pause_width_matches_undo_skip_row(main_window):
    preset = LAYOUT_PRESET_320
    sc = preset.split_column
    placer = _placer(main_window)
    UIController._place_split_column_bottom_controls(
        placer,
        split_viewport_for_tests(preset),
        row1=100,
        row2=150,
        pause_w=sc.pause_w,
        reset_w=sc.reset_w,
        gap_pause_to_reset=sc.gap_pause_to_reset,
        undo_w=sc.undo_w,
        skip_w=sc.skip_w,
    )
    pause = main_window.pause_button.geometry()
    undo = main_window.undo_button.geometry()
    skip = main_window.skip_button.geometry()
    assert pause.width() == skip.x() + skip.width() - undo.x()


_CENTERED_VIDEO_PRESETS = (
    LAYOUT_PRESET_480,
    LAYOUT_PRESET_512,
    LAYOUT_PRESET_320,
    LAYOUT_PRESET_432,
)


@pytest.mark.parametrize("preset", _CENTERED_VIDEO_PRESETS, ids=lambda p: p.aspect_ratio)
def test_video_column_stats_screenshot_gap(main_window, preset):
    vc = preset.video_column
    video = video_viewport_for_tests(preset)
    placer = _placer(main_window)
    UIController._place_video_column_stats_and_screenshot_row(
        placer,
        video,
        row1=200,
        row2=250,
        gap_stats_to_screenshot=vc.gap_stats_to_screenshot,
        screenshot_w=vc.screenshot_w,
        center_nudge_x=vc.center_nudge_x,
    )
    stats_right = main_window.match_percent_label.geometry().x() + VIDEO_COL_STATS_SPAN_W
    screenshot = main_window.screenshot_button.geometry()
    assert screenshot.x() - stats_right == vc.gap_stats_to_screenshot


def test_320_video_column_nudge_clears_split_column(main_window):
    """Centered 320 block is wider than the pane; nudge keeps Screenshot off Pause."""
    preset = LAYOUT_PRESET_320
    assert preset.video_column_block_width() > preset.video_viewport.width
    video = video_viewport_for_tests(preset)
    split = split_viewport_for_tests(preset)
    vc = preset.video_column
    placer = _placer(main_window)
    UIController._place_video_column_stats_and_screenshot_row(
        placer,
        video,
        row1=200,
        row2=250,
        gap_stats_to_screenshot=vc.gap_stats_to_screenshot,
        screenshot_w=vc.screenshot_w,
        center_nudge_x=vc.center_nudge_x,
    )
    screenshot_right = (
        main_window.screenshot_button.geometry().x() + vc.screenshot_w
    )
    assert screenshot_right <= split.x()


def test_320_center_nudge_matches_legacy_fixed_positions(main_window):
    """Nudge 69 reproduces the former hand-tuned 320 coords."""
    preset = LAYOUT_PRESET_320
    left = MAIN_WINDOW_LEFT_EDGE_CORRECTION
    vc = preset.video_column
    placer = _placer(main_window)
    UIController._place_video_column_stats_and_screenshot_row(
        placer,
        video_viewport_for_tests(preset),
        row1=200,
        row2=250,
        gap_stats_to_screenshot=vc.gap_stats_to_screenshot,
        screenshot_w=vc.screenshot_w,
        center_nudge_x=VIDEO_COL_CENTER_NUDGE_320,
    )
    assert main_window.match_percent_label.geometry().x() == -50 + left
    assert main_window.screenshot_button.geometry().x() == 220 + left


def test_video_column_block_centered_under_viewport(main_window):
    preset = LAYOUT_PRESET_432
    vc = preset.video_column
    video = video_viewport_for_tests(preset)
    gap = vc.gap_stats_to_screenshot
    screenshot_w = vc.screenshot_w
    block_w = VIDEO_COL_STATS_SPAN_W + gap + screenshot_w
    nudge = VIDEO_COL_CENTER_NUDGE_432
    placer = _placer(main_window)
    UIController._place_video_column_stats_and_screenshot_row(
        placer,
        video,
        row1=200,
        row2=250,
        gap_stats_to_screenshot=gap,
        screenshot_w=screenshot_w,
        center_nudge_x=nudge,
    )
    block_left = main_window.match_percent_label.geometry().x()
    block_right = main_window.screenshot_button.geometry().x() + screenshot_w
    left = block_left - video.x()
    right = video.x() + video.width() - block_right
    assert left + right == video.width() - block_w
    assert right - left == 2 * nudge
