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

"""Apply full main-window layout from an ``AspectLayoutPreset``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QRect

from ui.layout_presets import (
    AspectLayoutPreset,
    BOTTOM_BLOCK_LIFT_PX,
    STRIP_GAP_BELOW_VIEWPORT_PX,
)

if TYPE_CHECKING:
    from ui.ui_controller import UIController


def apply_aspect_layout(ctrl: "UIController", preset: AspectLayoutPreset) -> None:
    """Place chrome, viewports, bottom rows, and strip panels for one aspect ratio."""
    mw = ctrl._main_window
    left = mw.LEFT_EDGE_CORRECTION
    top = mw.TOP_EDGE_CORRECTION
    layout_dy = preset.strip_panel_layout_dy
    chrome = preset.chrome
    row1 = preset.bottom_row1(layout_dy, top)
    row2 = preset.bottom_row2(layout_dy, top)

    mw.split_directory_box.setGeometry(chrome.split_directory_box.to_rect(left, top))
    mw.split_dir_button.setGeometry(chrome.split_dir_button.to_rect(left, top))
    mw.min_view_button.setGeometry(chrome.min_view_button.to_rect(left, top))
    mw.split_name_label.setGeometry(chrome.split_name_label.to_rect(left, top))
    mw.split_loop_label.setGeometry(chrome.split_loop_label.to_rect(left, top))

    video_viewport = preset.video_viewport.to_rect(left, top)
    split_viewport = preset.split_viewport.to_rect(left, top)

    if chrome.video_title_center_in_viewport:
        vt_w = chrome.video_title_viewport_width
        mw.video_title.setGeometry(
            QRect(
                video_viewport.x() + (video_viewport.width() - vt_w) // 2,
                chrome.video_title.y + top,
                vt_w,
                chrome.video_title.height,
            )
        )
    else:
        mw.video_title.setGeometry(chrome.video_title.to_rect(left, top))

    if chrome.next_source_right_of_viewport:
        ns = chrome.next_source_button
        mw.next_source_button.setGeometry(
            QRect(
                video_viewport.x() + video_viewport.width() - chrome.next_source_offset_from_right,
                ns.y + top,
                ns.width,
                ns.height,
            )
        )
    else:
        mw.next_source_button.setGeometry(chrome.next_source_button.to_rect(left, top))

    ctrl._apply_video_column_layout(preset, video_viewport, row1, row2, left)

    if chrome.nav_buttons_on_split_viewport:
        pb = chrome.previous_button
        nb = chrome.next_button
        mw.previous_button.setGeometry(
            QRect(
                split_viewport.x() + chrome.prev_button_split_offset_x,
                pb.y + top,
                pb.width,
                pb.height,
            )
        )
        mw.next_button.setGeometry(
            QRect(
                split_viewport.x() + split_viewport.width() - chrome.next_button_split_offset_from_right,
                nb.y + top,
                nb.width,
                nb.height,
            )
        )
    else:
        mw.previous_button.setGeometry(chrome.previous_button.to_rect(left, top))
        mw.next_button.setGeometry(chrome.next_button.to_rect(left, top))

    ctrl._place_split_column_from_preset(split_viewport, row1, row2, preset.split_column)
    ctrl._set_video_viewport_geometry(video_viewport)
    mw.video_record_overlay.setGeometry(chrome.video_record_overlay.to_rect(left, top))

    vi = chrome.video_info
    if chrome.video_info_anchor_viewport:
        mw.video_info_overlay.setGeometry(
            QRect(
                video_viewport.x() + 10,
                vi.y + layout_dy + top,
                max(180, video_viewport.width() - 20),
                vi.height,
            )
        )
    else:
        mw.video_info_overlay.setGeometry(vi.to_rect(left, top, extra_y=layout_dy))

    strip_y = video_viewport.y() + video_viewport.height() + STRIP_GAP_BELOW_VIEWPORT_PX
    mw.video_crop_panel.setGeometry(
        QRect(
            video_viewport.x() - 1,
            strip_y,
            video_viewport.width() + 2,
            layout_dy,
        )
    )

    ctrl._set_split_viewport_geometry(split_viewport)
    split_strip_y = split_viewport.y() + split_viewport.height() + STRIP_GAP_BELOW_VIEWPORT_PX
    mw.split_override_panel.setGeometry(
        QRect(split_viewport.x(), split_strip_y, split_viewport.width(), layout_dy)
    )

    ctrl._set_nonessential_widgets_visible(True)
    ctrl._set_button_and_label_text(truncate=preset.truncate_controls)
    mw.setFixedSize(
        preset.window_width,
        (preset.window_height_base - BOTTOM_BLOCK_LIFT_PX)
        + layout_dy
        + mw.HEIGHT_CORRECTION,
    )
