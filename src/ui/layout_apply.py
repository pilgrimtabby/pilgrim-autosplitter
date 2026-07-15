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
