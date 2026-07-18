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

"""Per-aspect-ratio layout constants and bottom-row presets for the main window.

Design coordinates here are **before** ``LEFT_EDGE_CORRECTION`` /
``TOP_EDGE_CORRECTION`` (see ``ui_main_window``). ``ui_controller`` adds those
offsets when calling ``setGeometry``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from PyQt5.QtCore import QRect

# --- Shared chrome -----------------------------------------------------------

VIDEO_CROP_STRIP_LAYOUT_DY = 24
STRIP_GAP_BELOW_VIEWPORT_PX = 2
BOTTOM_BLOCK_LIFT_PX = -4
# Shared interstitial for screenshot↔gear, undo↔skip, and row1↔row2.
BOTTOM_ADJ_PAIR_GAP_PX = 9

# Small 16:9 on-screen pane width (capture frame width stays 432).
DISPLAY_W_432 = 432

# --- Video column stats + screenshot block -----------------------------------

VIDEO_COL_STATS_SPAN_W = 241
VIDEO_COL_STATS_LABEL_W = 161
VIDEO_COL_STATS_VALUE_X = 165
VIDEO_COL_STATS_PCT_X = 220
VIDEO_COL_STATS_ROW_H = 31
VIDEO_COL_STATS_ROW_STEP = 30
VIDEO_COL_SCREENSHOT_W_FULL = 187
VIDEO_COL_SCREENSHOT_W_COMPACT = 147
VIDEO_COL_SCREENSHOT_H = 41
# Row2 y = row1 y + this; Reset height = two buttons + one gap.
BOTTOM_ROW_STEP_PX = VIDEO_COL_SCREENSHOT_H + BOTTOM_ADJ_PAIR_GAP_PX
BOTTOM_RESET_H_PX = VIDEO_COL_SCREENSHOT_H * 2 + BOTTOM_ADJ_PAIR_GAP_PX

# Gap from stats block to screenshot column; also used as Pause→Reset gap.
VIDEO_COL_GAP_480 = 19
VIDEO_COL_GAP_512 = 51
VIDEO_COL_GAP_320 = 29
VIDEO_COL_GAP_432 = 18

# 432×243: geometric center reads slightly right on macOS.
VIDEO_COL_CENTER_NUDGE_432 = 48
# 320×240: block is wider than the pane; nudge left preserves legacy clearance from split column.
VIDEO_COL_CENTER_NUDGE_320 = 69

# --- Strip panel height per layout -------------------------------------------

STRIP_PANEL_DY_480 = 23
STRIP_PANEL_DY_320 = 24
STRIP_PANEL_DY_432 = 24

# --- 320×240 strip typography (used by ``strip_typography``) ----------------

STRIP_320_SIZE_F = 7.0
STRIP_320_ROW_MARGINS: Tuple[int, int, int, int] = (2, 3, 2, 3)
STRIP_320_ROW_SPACING = 4
STRIP_320_LABEL_FONT_PX = 12.0
STRIP_320_CONTROL_FONT_PX = 12.0
STRIP_320_LABEL_GAP_ADJ = -14
STRIP_320_ABBREV_LABEL_MIN_W = 26

@dataclass(frozen=True)
class ViewportDesignRect:
    """Viewport position/size in design space (before edge corrections)."""

    x: int
    y: int
    width: int
    height: int

    def to_rect(self, left: int, top: int) -> QRect:
        return QRect(self.x + left, self.y + top, self.width, self.height)


@dataclass(frozen=True)
class ChromeDesignRect:
    """Fixed chrome widget rect in design space (before edge corrections)."""

    x: int
    y: int
    width: int
    height: int

    def to_rect(self, left: int, top: int, *, extra_y: int = 0) -> QRect:
        return QRect(self.x + left, self.y + top + extra_y, self.width, self.height)


@dataclass(frozen=True)
class LayoutChromePreset:
    """Top chrome + overlays for one aspect ratio (design coords)."""

    split_directory_box: ChromeDesignRect
    split_dir_button: ChromeDesignRect
    min_view_button: ChromeDesignRect
    split_name_label: ChromeDesignRect
    split_loop_label: ChromeDesignRect
    video_title: ChromeDesignRect
    next_source_button: ChromeDesignRect
    previous_button: ChromeDesignRect
    next_button: ChromeDesignRect
    video_record_overlay: ChromeDesignRect
    video_info: ChromeDesignRect
    video_title_center_in_viewport: bool = False
    video_title_viewport_width: int = 231
    next_source_right_of_viewport: bool = False
    next_source_offset_from_right: int = 124
    nav_buttons_on_split_viewport: bool = False
    prev_button_split_offset_x: int = 12
    next_button_split_offset_from_right: int = 43
    video_info_anchor_viewport: bool = False


@dataclass(frozen=True)
class SplitColumnBottomPreset:
    """Pause / reset / undo / skip under the split-image pane."""

    pause_w: int
    reset_w: int
    undo_w: int
    skip_w: int
    gap_stats_to_screenshot: int

    @property
    def gap_pause_to_reset(self) -> int:
        return self.gap_stats_to_screenshot


@dataclass(frozen=True)
class VideoColumnBottomPreset:
    """How the stats + screenshot row is placed under the video pane."""

    gap_stats_to_screenshot: int
    screenshot_w: int
    center_nudge_x: int = 0


@dataclass(frozen=True)
class AspectLayoutPreset:
    """Bottom-row and viewport tuning for one ``ASPECT_RATIO`` setting."""

    aspect_ratio: str
    video_viewport: ViewportDesignRect
    split_viewport: ViewportDesignRect
    strip_panel_layout_dy: int
    bottom_row1_design: int
    bottom_row2_design: int
    split_column: SplitColumnBottomPreset
    video_column: VideoColumnBottomPreset
    chrome: LayoutChromePreset
    window_width: int
    window_height_base: int
    truncate_controls: bool

    def bottom_row1(self, layout_dy: int, top: int) -> int:
        return (self.bottom_row1_design - BOTTOM_BLOCK_LIFT_PX) + layout_dy + top

    def bottom_row2(self, layout_dy: int, top: int) -> int:
        return (self.bottom_row2_design - BOTTOM_BLOCK_LIFT_PX) + layout_dy + top

    def video_column_block_width(self) -> int:
        vc = self.video_column
        return VIDEO_COL_STATS_SPAN_W + vc.gap_stats_to_screenshot + vc.screenshot_w


_UNDO_SKIP_320 = 56
_UNDO_SKIP_FULL = 90
_UNDO_SKIP_432 = 75


def _pause_w(undo_w: int, skip_w: int) -> int:
    """Pause spans Undo + gap + Skip exactly (avoids a short right edge)."""
    return undo_w + BOTTOM_ADJ_PAIR_GAP_PX + skip_w


_SPLIT_320 = SplitColumnBottomPreset(
    pause_w=_pause_w(_UNDO_SKIP_320, _UNDO_SKIP_320),
    reset_w=121,
    undo_w=_UNDO_SKIP_320,
    skip_w=_UNDO_SKIP_320,
    gap_stats_to_screenshot=VIDEO_COL_GAP_320,
)

_CHROME_COMMON_DIR = ChromeDesignRect(60, 225, 180, 30)
_CHROME_COMMON_MIN = ChromeDesignRect(60, 270, 100, 31)

_CHROME_480 = LayoutChromePreset(
    split_directory_box=ChromeDesignRect(247, 225, 785, 30),
    split_dir_button=_CHROME_COMMON_DIR,
    min_view_button=_CHROME_COMMON_MIN,
    split_name_label=ChromeDesignRect(584, 255, 415, 31),
    split_loop_label=ChromeDesignRect(584, 280, 415, 31),
    video_title=ChromeDesignRect(260, 272, 80, 31),
    next_source_button=ChromeDesignRect(422, 272, 118, 31),
    previous_button=ChromeDesignRect(566, 270, 31, 31),
    next_button=ChromeDesignRect(1000, 270, 31, 31),
    video_record_overlay=ChromeDesignRect(497, 329, 24, 24),
    video_info=ChromeDesignRect(75, 610, 455, 30),
)

_CHROME_512 = LayoutChromePreset(
    split_directory_box=ChromeDesignRect(247, 225, 848, 30),
    split_dir_button=_CHROME_COMMON_DIR,
    min_view_button=_CHROME_COMMON_MIN,
    split_name_label=ChromeDesignRect(613, 255, 450, 31),
    split_loop_label=ChromeDesignRect(613, 280, 450, 31),
    video_title=ChromeDesignRect(276, 272, 80, 31),
    next_source_button=ChromeDesignRect(454, 272, 118, 31),
    previous_button=ChromeDesignRect(596, 270, 31, 31),
    next_button=ChromeDesignRect(1064, 270, 31, 31),
    video_record_overlay=ChromeDesignRect(542, 321, 19, 19),
    video_info=ChromeDesignRect(75, 538, 493, 30),
)

_CHROME_320 = LayoutChromePreset(
    split_directory_box=ChromeDesignRect(247, 225, 464, 30),
    split_dir_button=_CHROME_COMMON_DIR,
    min_view_button=_CHROME_COMMON_MIN,
    split_name_label=ChromeDesignRect(424, 255, 254, 31),
    split_loop_label=ChromeDesignRect(424, 280, 254, 31),
    video_title=ChromeDesignRect(180, 272, 80, 31),
    next_source_button=ChromeDesignRect(280, 272, 100, 31),
    previous_button=ChromeDesignRect(390, 270, 31, 31),
    next_button=ChromeDesignRect(680, 270, 31, 31),
    video_record_overlay=ChromeDesignRect(351, 323, 16, 16),
    video_info=ChromeDesignRect(72, 520, 310, 30),
)

_CHROME_432 = LayoutChromePreset(
    split_directory_box=ChromeDesignRect(247, 225, 688, 30),
    split_dir_button=_CHROME_COMMON_DIR,
    min_view_button=_CHROME_COMMON_MIN,
    split_name_label=ChromeDesignRect(534, 255, 371, 31),
    split_loop_label=ChromeDesignRect(534, 280, 371, 31),
    video_title=ChromeDesignRect(0, 272, 231, 31),
    next_source_button=ChromeDesignRect(0, 272, 118, 31),
    previous_button=ChromeDesignRect(0, 270, 31, 31),
    next_button=ChromeDesignRect(0, 270, 31, 31),
    video_record_overlay=ChromeDesignRect(467, 319, 16, 16),
    video_info=ChromeDesignRect(0, 524, 310, 30),
    video_title_center_in_viewport=True,
    next_source_right_of_viewport=True,
    nav_buttons_on_split_viewport=True,
    video_info_anchor_viewport=True,
)

LAYOUT_PRESET_480 = AspectLayoutPreset(
    aspect_ratio="4:3 (480x360)",
    video_viewport=ViewportDesignRect(60, 310, 480, 360),
    split_viewport=ViewportDesignRect(550, 310, 480, 360),
    strip_panel_layout_dy=STRIP_PANEL_DY_480,
    bottom_row1_design=680,
    bottom_row2_design=730,
    split_column=SplitColumnBottomPreset(
        pause_w=_pause_w(_UNDO_SKIP_FULL, _UNDO_SKIP_FULL),
        reset_w=191,
        undo_w=_UNDO_SKIP_FULL,
        skip_w=_UNDO_SKIP_FULL,
        gap_stats_to_screenshot=VIDEO_COL_GAP_480,
    ),
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_480,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_FULL,
    ),
    chrome=_CHROME_480,
    window_width=1002,
    window_height_base=570,
    truncate_controls=False,
)

LAYOUT_PRESET_512 = AspectLayoutPreset(
    aspect_ratio="16:9 (512x288)",
    video_viewport=ViewportDesignRect(60, 310, 512, 288),
    split_viewport=ViewportDesignRect(582, 310, 512, 288),
    strip_panel_layout_dy=VIDEO_CROP_STRIP_LAYOUT_DY,
    bottom_row1_design=608,
    bottom_row2_design=658,
    split_column=SplitColumnBottomPreset(
        pause_w=_pause_w(_UNDO_SKIP_FULL, _UNDO_SKIP_FULL),
        reset_w=191,
        undo_w=_UNDO_SKIP_FULL,
        skip_w=_UNDO_SKIP_FULL,
        gap_stats_to_screenshot=VIDEO_COL_GAP_512,
    ),
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_512,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_FULL,
    ),
    chrome=_CHROME_512,
    window_width=1064,
    window_height_base=497,
    truncate_controls=False,
)

LAYOUT_PRESET_320 = AspectLayoutPreset(
    aspect_ratio="4:3 (320x240)",
    video_viewport=ViewportDesignRect(60, 310, 320, 240),
    split_viewport=ViewportDesignRect(390, 310, 320, 240),
    strip_panel_layout_dy=VIDEO_CROP_STRIP_LAYOUT_DY,
    bottom_row1_design=560,
    bottom_row2_design=610,
    split_column=_SPLIT_320,
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_320,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_COMPACT,
        center_nudge_x=VIDEO_COL_CENTER_NUDGE_320,
    ),
    chrome=_CHROME_320,
    window_width=682,
    window_height_base=450,
    truncate_controls=True,
)

LAYOUT_PRESET_432 = AspectLayoutPreset(
    aspect_ratio="16:9 (432x243)",
    video_viewport=ViewportDesignRect(60, 310, 432, 243),
    split_viewport=ViewportDesignRect(502, 310, 432, 243),
    strip_panel_layout_dy=STRIP_PANEL_DY_432,
    bottom_row1_design=563,
    bottom_row2_design=613,
    split_column=SplitColumnBottomPreset(
        pause_w=_pause_w(_UNDO_SKIP_432, _UNDO_SKIP_432),
        reset_w=181,
        undo_w=_UNDO_SKIP_432,
        skip_w=_UNDO_SKIP_432,
        gap_stats_to_screenshot=VIDEO_COL_GAP_432,
    ),
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_432,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_COMPACT,
        center_nudge_x=VIDEO_COL_CENTER_NUDGE_432,
    ),
    chrome=_CHROME_432,
    window_width=904,
    window_height_base=452,
    truncate_controls=True,
)

LAYOUT_PRESETS: Dict[str, AspectLayoutPreset] = {
    LAYOUT_PRESET_480.aspect_ratio: LAYOUT_PRESET_480,
    LAYOUT_PRESET_512.aspect_ratio: LAYOUT_PRESET_512,
    LAYOUT_PRESET_320.aspect_ratio: LAYOUT_PRESET_320,
    LAYOUT_PRESET_432.aspect_ratio: LAYOUT_PRESET_432,
}

# Edge corrections from ``UIMainWindow`` — for tests and tooling.
MAIN_WINDOW_LEFT_EDGE_CORRECTION = -44
MAIN_WINDOW_TOP_EDGE_CORRECTION = -215


def split_viewport_for_tests(preset: AspectLayoutPreset) -> QRect:
    """Split pane ``QRect`` with edge corrections applied (for unit tests)."""
    return preset.split_viewport.to_rect(
        MAIN_WINDOW_LEFT_EDGE_CORRECTION,
        MAIN_WINDOW_TOP_EDGE_CORRECTION,
    )


def video_viewport_for_tests(preset: AspectLayoutPreset) -> QRect:
    """Video pane ``QRect`` with edge corrections applied (for unit tests)."""
    return preset.video_viewport.to_rect(
        MAIN_WINDOW_LEFT_EDGE_CORRECTION,
        MAIN_WINDOW_TOP_EDGE_CORRECTION,
    )
