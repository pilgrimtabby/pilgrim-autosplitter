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
BOTTOM_ADJ_PAIR_GAP_PX = 5

# Small 16:9 on-screen pane width (capture frame width stays 432).
DISPLAY_W_432 = 432

# --- Video column stats + screenshot block -----------------------------------

VIDEO_COL_STATS_SPAN_W = 241
VIDEO_COL_STATS_LABEL_W = 161
VIDEO_COL_STATS_VALUE_X = 165
VIDEO_COL_STATS_PCT_X = 220
VIDEO_COL_STATS_ROW_H = 31
VIDEO_COL_STATS_ROW_STEP = 30
VIDEO_COL_SCREENSHOT_W_FULL = 171
VIDEO_COL_SCREENSHOT_W_COMPACT = 131
VIDEO_COL_SCREENSHOT_H = 41

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
    centered_under_viewport: bool = True
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
_SPLIT_320 = SplitColumnBottomPreset(
    pause_w=_UNDO_SKIP_320 + BOTTOM_ADJ_PAIR_GAP_PX + _UNDO_SKIP_320,
    reset_w=121,
    undo_w=_UNDO_SKIP_320,
    skip_w=_UNDO_SKIP_320,
    gap_stats_to_screenshot=VIDEO_COL_GAP_320,
)

LAYOUT_PRESET_480 = AspectLayoutPreset(
    aspect_ratio="4:3 (480x360)",
    video_viewport=ViewportDesignRect(60, 310, 480, 360),
    split_viewport=ViewportDesignRect(550, 310, 480, 360),
    strip_panel_layout_dy=STRIP_PANEL_DY_480,
    bottom_row1_design=680,
    bottom_row2_design=730,
    split_column=SplitColumnBottomPreset(
        pause_w=185,
        reset_w=191,
        undo_w=90,
        skip_w=90,
        gap_stats_to_screenshot=VIDEO_COL_GAP_480,
    ),
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_480,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_FULL,
        centered_under_viewport=True,
    ),
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
        pause_w=185,
        reset_w=191,
        undo_w=90,
        skip_w=90,
        gap_stats_to_screenshot=VIDEO_COL_GAP_512,
    ),
    video_column=VideoColumnBottomPreset(
        gap_stats_to_screenshot=VIDEO_COL_GAP_512,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_FULL,
        centered_under_viewport=True,
    ),
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
        centered_under_viewport=True,
        center_nudge_x=VIDEO_COL_CENTER_NUDGE_320,
    ),
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
        pause_w=155,
        reset_w=181,
        undo_w=75,
        skip_w=75,
        gap_stats_to_screenshot=VIDEO_COL_GAP_432,
    ),
    video_column=VideoColumnBottomPreset(
        centered_under_viewport=True,
        gap_stats_to_screenshot=VIDEO_COL_GAP_432,
        screenshot_w=VIDEO_COL_SCREENSHOT_W_COMPACT,
        center_nudge_x=VIDEO_COL_CENTER_NUDGE_432,
    ),
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
