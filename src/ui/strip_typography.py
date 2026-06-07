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

"""Crop/threshold strip fonts, spacing, and overflow shrinking."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QWidget,
)

import settings
from ui.layout_presets import (
    DISPLAY_W_432,
    STRIP_320_ABBREV_LABEL_MIN_W,
    STRIP_320_CONTROL_FONT_PX,
    STRIP_320_LABEL_FONT_PX,
    STRIP_320_LABEL_GAP_ADJ,
    STRIP_320_ROW_MARGINS,
    STRIP_320_ROW_SPACING,
    STRIP_320_SIZE_F,
)

if TYPE_CHECKING:
    from ui.ui_controller import UIController
    from ui.ui_main_window import UIMainWindow

STRIP_FONT_METRICS_FLOOR_PX = 8
STRIP_LOCAL_LABEL_PX = 12
STRIP_LOCAL_SPIN_PX = 13
STRIP_LOCAL_SPIN_PX_TINY = 12
STRIP_LABEL_SLACK_PX = 2
STRIP_MENU_BOX_WIDTH_PX = 54
STRIP_MENU_BOX_HEIGHT_PX = 19
STRIP_POPUP_BUTTON_SIDE_PX = 17
STRIP_MENU_BOX_WIDTH_320_PX = 52
STRIP_MENU_BOX_HEIGHT_320_PX = 19
STRIP_POPUP_BUTTON_SIDE_320_PX = 17
STRIP_MENU_BOX_WIDTH_432_PX = 52
STRIP_LABEL_TO_SPIN_GAP_PX = 2
STRIP_LABEL_LEFT_INSET_PX = 3
STRIP_ABBREV_LABEL_MIN_WIDTH_PX = 42


class StripTypographyApplier:
    """Apply per-aspect strip bar typography on behalf of ``UIController``."""

    def __init__(self, controller: UIController) -> None:
        self._ctrl = controller

    @property
    def _main_window(self) -> UIMainWindow:
        return self._ctrl._main_window

    def apply(self) -> None:
        """Set strip font/spacing adaptively to prevent overlap."""
        mw = self._main_window
        mw.video_crop_btn_reset.setMinimumSize(0, 0)
        mw.video_crop_btn_reset.setMaximumSize(16777215, 16777215)
        aspect_ratio = settings.get_str("ASPECT_RATIO")
        strip_scale = 1.0

        # Explicit per-ratio presets to avoid guesswork and clipping.
        if aspect_ratio == "4:3 (320x240)":
            size_f = STRIP_320_SIZE_F
            crop_row_margins = STRIP_320_ROW_MARGINS
            split_row_margins = STRIP_320_ROW_MARGINS
            crop_spacing = STRIP_320_ROW_SPACING
            split_spacing = STRIP_320_ROW_SPACING
            mw.video_crop_label_left.setText("L:")
            mw.video_crop_label_right.setText("R:")
            mw.video_crop_label_up.setText("U:")
            mw.video_crop_label_down.setText("D:")
            mw.split_threshold_label.setText("T:")
            mw.split_delay_label.setText("D:")
            mw.split_loop_label_2.setText("L:")
            mw.split_pause_label.setText("P:")
            mw.video_crop_btn_reset.setText("R")
        elif aspect_ratio == "4:3 (480x360)":
            # 480x360 still has tight horizontal room under both viewports.
            strip_scale = 0.32
            size_f = 8.4
            crop_row_margins = (16, 2, 16, 2)
            split_row_margins = (16, 2, 16, 2)
            crop_spacing = 4
            split_spacing = 5
            mw.video_crop_label_left.setText("Left:")
            mw.video_crop_label_right.setText("Right:")
            mw.video_crop_label_up.setText("Up:")
            mw.video_crop_label_down.setText("Down:")
            mw.split_threshold_label.setText("Threshold:")
            mw.split_delay_label.setText("Delay:")
            mw.split_loop_label_2.setText("Loop:")
            mw.split_pause_label.setText("Pause:")
            mw.video_crop_btn_reset.setText("Reset")
            mw.video_crop_btn_reset.setMinimumHeight(0)
            mw.video_crop_btn_reset.setMaximumHeight(16777215)
        elif aspect_ratio == "16:9 (432x243)":
            # Tighter window — a bit more strip inset so controls clear edges.
            strip_scale = 0.32
            size_f = 7.0
            crop_row_margins = (34, 3, 34, 3)
            split_row_margins = (34, 3, 34, 3)
            crop_spacing = 5
            split_spacing = 5
            mw.video_crop_label_left.setText("L:")
            mw.video_crop_label_right.setText("R:")
            mw.video_crop_label_up.setText("U:")
            mw.video_crop_label_down.setText("D:")
            mw.split_threshold_label.setText("T:")
            mw.split_delay_label.setText("D:")
            mw.split_loop_label_2.setText("L:")
            mw.split_pause_label.setText("P:")
            mw.video_crop_btn_reset.setText("R")
            mw.video_crop_btn_reset.setMinimumHeight(0)
            mw.video_crop_btn_reset.setMaximumHeight(16777215)
        else:
            # 16:9 (512×288)
            strip_scale = 0.40
            size_f = 9.4
            crop_row_margins = (18, 2, 18, 2)
            split_row_margins = (18, 2, 18, 2)
            crop_spacing = 22
            split_spacing = 22
            mw.video_crop_label_left.setText("Left:")
            mw.video_crop_label_right.setText("Right:")
            mw.video_crop_label_up.setText("Up:")
            mw.video_crop_label_down.setText("Down:")
            mw.split_threshold_label.setText("Threshold:")
            mw.split_delay_label.setText("Delay:")
            mw.split_loop_label_2.setText("Loop:")
            mw.split_pause_label.setText("Pause:")
            mw.video_crop_btn_reset.setText("Reset")
            mw.video_crop_btn_reset.setMinimumHeight(0)
            mw.video_crop_btn_reset.setMaximumHeight(16777215)

        # Apply strip_scale to layout (margins, spacing, chrome). Fonts use explicit
        # px below so they stay below the global 16px theme without collapsing to
        # illegal sizes that trigger fallback rendering.
        if strip_scale != 1.0:
            crop_row_margins = tuple(
                max(0, int(round(v * strip_scale))) for v in crop_row_margins
            )
            split_row_margins = tuple(
                max(0, int(round(v * strip_scale))) for v in split_row_margins
            )
            # Floor so scaled layouts keep gap between each spin and the next title.
            crop_spacing = max(4, int(round(crop_spacing * strip_scale)))
            split_spacing = max(4, int(round(split_spacing * strip_scale)))

        if aspect_ratio == "16:9 (432x243)":
            # Keep compact labels close to their value boxes on 432.
            crop_spacing = 4
            split_spacing = 4

        font = QFont(mw.font())
        font.setPointSizeF(size_f)
        # Ensure all strip children inherit the same scaled font baseline.
        mw.video_crop_panel.setFont(font)
        mw.split_override_panel.setFont(font)
        widgets = [
            mw.video_crop_label_left,
            mw.video_crop_label_right,
            mw.video_crop_label_up,
            mw.video_crop_label_down,
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
            mw.video_crop_btn_reset,
            mw.split_threshold_label,
            mw.split_threshold_spin,
            mw.split_delay_label,
            mw.split_delay_spin,
            mw.split_loop_label_2,
            mw.split_loop_spin,
            mw.split_pause_label,
            mw.split_pause_spin,
            mw.split_type_menu_button,
        ]
        for widget in widgets:
            widget.setFont(font)

        crop_labels = (
            mw.video_crop_label_left,
            mw.video_crop_label_right,
            mw.video_crop_label_up,
            mw.video_crop_label_down,
        )
        split_labels = (
            mw.split_threshold_label,
            mw.split_delay_label,
            mw.split_loop_label_2,
            mw.split_pause_label,
        )
        # Pixel sizes for metrics — actual painting uses per-widget stylesheets (see below).
        if aspect_ratio == "4:3 (320x240)":
            # Match compact 432 typography.
            label_font_px = STRIP_320_LABEL_FONT_PX
            font_px = STRIP_320_CONTROL_FONT_PX
        elif aspect_ratio == "16:9 (432x243)":
            label_font_px = 12.0
            font_px = float(STRIP_LOCAL_SPIN_PX_TINY)
        elif aspect_ratio == "4:3 (480x360)":
            label_font_px = float(STRIP_LOCAL_LABEL_PX) + 0.5
            font_px = float(STRIP_LOCAL_SPIN_PX) + 0.5
        elif aspect_ratio == "16:9 (512x288)":
            label_font_px = float(STRIP_LOCAL_LABEL_PX) + 0.8
            font_px = float(STRIP_LOCAL_SPIN_PX) + 0.8
        else:
            label_font_px = float(STRIP_LOCAL_LABEL_PX)
            font_px = float(STRIP_LOCAL_SPIN_PX)

        self._ctrl._strip_label_font_px = label_font_px
        self._ctrl._strip_control_font_px = font_px
        lip_i = int(round(label_font_px))
        fpx_i = int(round(font_px))

        # Clear legacy per-widget strip font rules (older builds).
        _strip_marker = "/* strip-font-size */"
        for w in (
            *crop_labels,
            *split_labels,
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
            mw.video_crop_btn_reset,
            mw.split_threshold_spin,
            mw.split_delay_spin,
            mw.split_loop_spin,
            mw.split_pause_spin,
            mw.split_type_menu_button,
        ):
            bs = w.styleSheet()
            if _strip_marker in bs:
                w.setStyleSheet(bs[: bs.find(_strip_marker)].rstrip())

        # Apply strip QSS first so label/spin fontMetrics match painted text (avoids
        # fixed widths computed from a different font than stylesheet rendering).
        composed = self._ctrl._compose_main_window_stylesheet()
        self._ctrl._most_recent_style_sheet = composed
        self._main_window.setStyleSheet(composed)
        self.apply_local_font_styles(mw, lip_i, fpx_i)
        app = QApplication.instance()
        if app is not None and app.style() is not None:
            sty = app.style()
            sty.unpolish(self._main_window)
            sty.polish(self._main_window)

        mw.video_crop_panel.ensurePolished()
        mw.split_override_panel.ensurePolished()

        lip = self._ctrl._strip_label_font_px
        fpx = self._ctrl._strip_control_font_px
        assert lip is not None and fpx is not None
        fm_strip = self.metrics_at_px(lip)
        _abbrev_strip = aspect_ratio in ("4:3 (320x240)", "16:9 (432x243)")
        _lab_gap = STRIP_LABEL_TO_SPIN_GAP_PX + (2 if _abbrev_strip else 0)
        if aspect_ratio == "4:3 (320x240)":
            # Keep title-to-own-menu spacing compact on 320.
            _lab_gap = max(1, _lab_gap + STRIP_320_LABEL_GAP_ADJ)
        elif aspect_ratio == "4:3 (480x360)":
            # Keep 480 labels closer to their own value boxes.
            _lab_gap = max(1, _lab_gap - 2)
        elif aspect_ratio == "16:9 (432x243)":
            _lab_gap = max(1, _lab_gap - 2)
        elif aspect_ratio == "16:9 (512x288)":
            _lab_gap = max(1, _lab_gap + 1)
        _lab_left_inset = STRIP_LABEL_LEFT_INSET_PX
        if aspect_ratio == "4:3 (480x360)":
            _lab_left_inset += 3
        for label in (*crop_labels, *split_labels):
            label.setMinimumWidth(0)
            label.setMaximumWidth(16777215)
            label.setContentsMargins(_lab_left_inset, 0, _lab_gap, 0)
        if _abbrev_strip:
            # Keep single-letter labels visually consistent on compact layouts.
            for label in (*crop_labels, *split_labels):
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            for label in (*crop_labels, *split_labels):
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        _abbrev_min_w = STRIP_ABBREV_LABEL_MIN_WIDTH_PX
        if aspect_ratio == "4:3 (320x240)":
            _abbrev_min_w = STRIP_320_ABBREV_LABEL_MIN_W
        elif aspect_ratio == "16:9 (432x243)":
            _abbrev_min_w = 26
        for label in (*crop_labels, *split_labels):
            label.ensurePolished()
            tw = fm_strip.horizontalAdvance(label.text())
            br_w = fm_strip.boundingRect(label.text()).width()
            text_basis = max(tw, br_w)
            # Outer width = left inset + text + slack + right margin gap before spin.
            w = int(
                math.ceil(
                    _lab_left_inset + text_basis + STRIP_LABEL_SLACK_PX + _lab_gap
                )
            )
            if _abbrev_strip:
                w = _abbrev_min_w
            label.setFixedWidth(w)

        # Narrow Reset: width follows text metrics only (same tight padding as QSS).
        mw.video_crop_btn_reset.ensurePolished()
        reset_fm = self.metrics_at_px(lip)
        reset_txt = mw.video_crop_btn_reset.text()
        metrics_gap = max(
            reset_fm.horizontalAdvance(reset_txt),
            reset_fm.boundingRect(reset_txt).width(),
        )
        self._ctrl._crop_reset_min_width = int(math.ceil(metrics_gap + 16))

        _strip_spins = (
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
            mw.split_threshold_spin,
            mw.split_delay_spin,
            mw.split_loop_spin,
            mw.split_pause_spin,
        )
        for sp in _strip_spins:
            sp.setMinimumSize(0, 0)
            sp.setMaximumSize(16777215, 16777215)
        mw.split_type_menu_button.setMinimumSize(0, 0)
        mw.split_type_menu_button.setMaximumSize(16777215, 16777215)

        if aspect_ratio == "4:3 (320x240)":
            strip_row_h = STRIP_MENU_BOX_HEIGHT_320_PX
            box_w = STRIP_MENU_BOX_WIDTH_320_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_320_PX
        elif aspect_ratio == "16:9 (432x243)":
            strip_row_h = STRIP_MENU_BOX_HEIGHT_PX
            box_w = STRIP_MENU_BOX_WIDTH_432_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_PX
        else:
            strip_row_h = STRIP_MENU_BOX_HEIGHT_PX
            box_w = STRIP_MENU_BOX_WIDTH_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_PX
        self._ctrl._strip_row_height = strip_row_h
        if _abbrev_strip:
            self._ctrl._crop_reset_min_width = strip_row_h

        for sp in _strip_spins:
            sp.setFixedSize(box_w, strip_row_h)
            sp.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._ctrl._strip_popup_side = popup_side
        if _abbrev_strip:
            mw.video_crop_btn_reset.setFixedSize(strip_row_h, strip_row_h)
            mw.video_crop_btn_reset.setMinimumSize(strip_row_h, strip_row_h)
            mw.video_crop_btn_reset.setMaximumSize(strip_row_h, strip_row_h)
        else:
            rw = self._ctrl._crop_reset_min_width
            mw.video_crop_btn_reset.setFixedSize(rw, strip_row_h)

        mw.split_type_menu_button.setFixedSize(popup_side, popup_side)
        if aspect_ratio == "4:3 (320x240)":
            mw.split_type_menu_button.setMinimumSize(popup_side, popup_side)
            mw.split_type_menu_button.setMaximumSize(popup_side, popup_side)
        chevron_side = max(8, popup_side - 6)
        mw.split_type_menu_button.setIconSize(QSize(chevron_side, chevron_side))
        mw.video_crop_btn_reset.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        mw.split_type_menu_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        crop_l, crop_t, crop_r, crop_b = crop_row_margins
        split_l, split_t, split_r, split_b = split_row_margins
        # Visual balance: label text is inset from the left edge, so mirror that
        # amount on the right side to keep edge distances looking equal.
        crop_row_margins_balanced = (
            crop_l,
            crop_t,
            crop_r + _lab_left_inset,
            crop_b,
        )
        split_row_margins_balanced = (
            split_l,
            split_t,
            split_r + _lab_left_inset,
            split_b,
        )
        # Lift strip contents slightly within the grey bar across all ratios.
        crop_row_margins_balanced = (
            crop_row_margins_balanced[0],
            max(0, crop_row_margins_balanced[1] - 1),
            crop_row_margins_balanced[2],
            crop_row_margins_balanced[3] + 1,
        )
        split_row_margins_balanced = (
            split_row_margins_balanced[0],
            max(0, split_row_margins_balanced[1] - 1),
            split_row_margins_balanced[2],
            split_row_margins_balanced[3] + 1,
        )

        mw.video_crop_row.setContentsMargins(*crop_row_margins_balanced)
        mw.video_crop_row.setSpacing(crop_spacing)
        mw.split_override_row.setContentsMargins(*split_row_margins_balanced)
        mw.split_override_row.setSpacing(split_spacing)
        # Keep popup-button gap visually consistent with row spacing on compact 320.
        pause_popup_spacer = mw.split_override_row.itemAt(9)
        if pause_popup_spacer is not None and pause_popup_spacer.spacerItem() is not None:
            popup_gap = split_spacing if aspect_ratio == "4:3 (320x240)" else 7
            pause_popup_spacer.spacerItem().changeSize(
                popup_gap, 0, QSizePolicy.Fixed, QSizePolicy.Minimum
            )
            mw.split_override_row.invalidate()

        self.shrink_both_rows_if_overflow(mw)
        # Spins / split-type button stay fixed size; re-apply in case Reset height drifted.
        if aspect_ratio == "4:3 (320x240)":
            h = STRIP_MENU_BOX_HEIGHT_320_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_320_PX
            box_w = STRIP_MENU_BOX_WIDTH_320_PX
        elif aspect_ratio == "16:9 (432x243)":
            h = STRIP_MENU_BOX_HEIGHT_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_PX
            box_w = STRIP_MENU_BOX_WIDTH_432_PX
        else:
            h = STRIP_MENU_BOX_HEIGHT_PX
            popup_side = STRIP_POPUP_BUTTON_SIDE_PX
            box_w = STRIP_MENU_BOX_WIDTH_PX
        self._ctrl._strip_row_height = h
        self._ctrl._strip_popup_side = popup_side
        mw.split_type_menu_button.setFixedSize(popup_side, popup_side)
        if aspect_ratio == "4:3 (320x240)":
            mw.split_type_menu_button.setMinimumSize(popup_side, popup_side)
            mw.split_type_menu_button.setMaximumSize(popup_side, popup_side)
        chevron_side = max(8, popup_side - 6)
        mw.split_type_menu_button.setIconSize(QSize(chevron_side, chevron_side))
        for sp in _strip_spins:
            sp.setFixedSize(box_w, h)
        if _abbrev_strip:
            mw.video_crop_btn_reset.setFixedSize(h, h)
            if aspect_ratio == "4:3 (320x240)":
                # Hard-lock 320 strip reset ("R") as a square.
                mw.video_crop_btn_reset.setMinimumSize(h, h)
                mw.video_crop_btn_reset.setMaximumSize(h, h)
                mw.video_crop_btn_reset.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            mw.video_crop_btn_reset.setFixedHeight(h)

        self.apply_bottom_panel()

    def apply_bottom_panel(self) -> None:
        """Keep bottom controls on source/default typography."""
        mw = self._main_window
        for w in (
            mw.screenshot_button,
            mw.screenshot_settings_button,
            mw.reconnect_button,
            mw.pause_button,
            mw.skip_button,
            mw.undo_button,
            mw.reset_button,
        ):
            w.setStyleSheet("")
            w.setFont(mw.font())
        # Match / highest / threshold row: inherit global stylesheet (16px), not
        # the compact-strip or button bump — matches classic Pilgrim display.
        for w in (
            mw.match_percent_label,
            mw.highest_percent_label,
            mw.threshold_percent_label,
            mw.match_percent,
            mw.highest_percent,
            mw.threshold_percent,
            mw.percent_sign_1,
            mw.percent_sign_2,
            mw.percent_sign_3,
        ):
            w.setStyleSheet("")
            w.setFont(mw.font())

    def shrink_row_once_nonspins(
        self,
        row: QHBoxLayout,
        fm_strip: Optional[QFontMetrics],
        reset_floor: int,
        strip_h: int,
        *,
        crop_row: bool,
    ) -> bool:
        """One pass: shrink first eligible label or crop Reset (spins/toolbutton fixed)."""
        small_square_reset = settings.get_str("ASPECT_RATIO") in (
            "4:3 (320x240)",
            "16:9 (432x243)",
        )
        for i in range(row.count()):
            item = row.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is None:
                continue
            if isinstance(w, (QSpinBox, QDoubleSpinBox, QToolButton)):
                continue
            if isinstance(w, QLabel) and fm_strip is not None:
                cm = w.contentsMargins()
                text_min = int(
                    math.ceil(
                        fm_strip.horizontalAdvance(w.text())
                        + cm.left()
                        + cm.right()
                        + 1
                    )
                )
                if w.width() > text_min:
                    w.setFixedWidth(w.width() - 1)
                    return True
            elif isinstance(w, QPushButton) and crop_row:
                if small_square_reset:
                    continue
                if w.width() > reset_floor:
                    nw = w.width() - 1
                    w.setMinimumWidth(nw)
                    w.setMaximumWidth(nw)
                    return True
        return False

    def row_inner_budget(self, panel: QWidget, row: QHBoxLayout) -> int:
        """Pixels inside strip margins for laying out label/spin rows.

        Full layouts size each strip to the viewport column width (usually
        ``FRAME_WIDTH``). Small 16:9 uses a narrower on-screen pane
        (``DISPLAY_W_432``) while capture stays 432 — budget must match the pane.
        """
        m = row.contentsMargins()
        if settings.get_bool("SHOW_MIN_VIEW"):
            return max(1, panel.width() - m.left() - m.right())
        if settings.get_str("ASPECT_RATIO") == "16:9 (432x243)":
            fw = max(1, DISPLAY_W_432)
        else:
            fw = max(1, settings.get_int("FRAME_WIDTH"))
        return max(1, fw - m.left() - m.right())

    def row_contents_minimum_width(self, row: QHBoxLayout) -> int:
        """Minimum horizontal space for all layout items (matches ``minimumSize().width()`` logic).

        Used instead of ``QLayout.minimumSize()`` alone so overflow detection stays consistent
        right after ``activate()`` without relying on a stale cached layout min width.
        """
        m = row.contentsMargins()
        sp = row.spacing()
        total = m.left() + m.right()
        first = True
        for i in range(row.count()):
            item = row.itemAt(i)
            if item is None:
                continue
            if not first:
                total += sp
            first = False
            total += item.minimumSize().width()
        return total

    def shrink_both_rows_if_overflow(self, mw: UIMainWindow) -> None:
        """If strips overflow, narrow QLabel widths (and crop Reset only).

        Spin boxes and the split-type toolbutton stay at fixed pixel size across ratios.
        """
        lip = self._ctrl._strip_label_font_px
        fm_strip = self.metrics_at_px(lip) if lip is not None else None
        is_small = settings.get_str("ASPECT_RATIO") == "4:3 (320x240)"
        floor_btn = 22 if is_small else 28
        crop_reset_min_w = (
            0
            if settings.get_str("ASPECT_RATIO") == "4:3 (320x240)"
            else self._ctrl._crop_reset_min_width
        )
        reset_floor = max(floor_btn, crop_reset_min_w) if crop_reset_min_w > 0 else floor_btn
        strip_h = self._ctrl._strip_row_height

        crop_panel, crop_row = mw.video_crop_panel, mw.video_crop_row
        split_panel, split_row = mw.split_override_panel, mw.split_override_row

        def strip_rows_fit() -> bool:
            crop_row.activate()
            split_row.activate()
            for panel, row in ((crop_panel, crop_row), (split_panel, split_row)):
                budget = self.row_inner_budget(panel, row)
                if budget <= 0:
                    continue
                required = self.row_contents_minimum_width(row)
                if required > budget:
                    return False
            return True

        for _ in range(900):
            if strip_rows_fit():
                return
            if self.shrink_row_once_nonspins(
                crop_row, fm_strip, reset_floor, strip_h, crop_row=True
            ):
                continue
            if self.shrink_row_once_nonspins(
                split_row, fm_strip, reset_floor, strip_h, crop_row=False
            ):
                continue
            break

    def apply_local_font_styles(
        self, mw: UIMainWindow, lip_i: int, fpx_i: int
    ) -> None:
        """Apply compact strip fonts on each control.

        The theme stylesheet sets ``* {{ font-size: 16px }}``. On Fusion, more-specific
        rules on the main window often still leave strip widgets at 16px. Per-widget
        stylesheets and matching ``setPixelSize`` match the older compact UI.
        """
        lab_ss = f"font-size: {lip_i}px; font-weight: normal;"
        spin_ss = f"font-size: {fpx_i}px; font-weight: normal;"
        px_lab = max(STRIP_FONT_METRICS_FLOOR_PX, lip_i)
        px_spin = max(STRIP_FONT_METRICS_FLOOR_PX, fpx_i)

        for lbl in (
            mw.video_crop_label_left,
            mw.video_crop_label_right,
            mw.video_crop_label_up,
            mw.video_crop_label_down,
            mw.split_threshold_label,
            mw.split_delay_label,
            mw.split_loop_label_2,
            mw.split_pause_label,
        ):
            lbl.setStyleSheet(lab_ss)
            lf = QFont(lbl.font())
            lf.setPixelSize(px_lab)
            lbl.setFont(lf)

        for sp in (
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
            mw.split_threshold_spin,
            mw.split_delay_spin,
            mw.split_loop_spin,
            mw.split_pause_spin,
        ):
            sp.setStyleSheet(spin_ss)
            sf = QFont(sp.font())
            sf.setPixelSize(px_spin)
            sp.setFont(sf)

        if settings.get_str("ASPECT_RATIO") in ("4:3 (320x240)", "16:9 (432x243)"):
            mw.video_crop_btn_reset.setStyleSheet(lab_ss + " padding: 0px;")
        else:
            mw.video_crop_btn_reset.setStyleSheet(lab_ss)
        rf = QFont(mw.video_crop_btn_reset.font())
        rf.setPixelSize(px_lab)
        mw.video_crop_btn_reset.setFont(rf)

        if settings.get_str("THEME") == "light":
            popup_bg = "#bbbbbb"
            popup_border = "#8f8f8f"
        else:
            popup_bg = "#606060"
            popup_border = "#242424"

        mw.split_type_menu_button.setStyleSheet(
            f"""QToolButton#split_type_menu_button {{
  font-size: {fpx_i}px;
  font-weight: normal;
  background-color: {popup_bg};
  border: 1px solid {popup_border};
  border-radius: 2px;
  padding: 0px;
}}
QToolButton#split_type_menu_button::menu-indicator {{
  image: none;
  width: 0px;
  height: 0px;
  subcontrol-position: right bottom;
}}
"""
        )
        tf = QFont(mw.split_type_menu_button.font())
        tf.setPixelSize(px_spin)
        mw.split_type_menu_button.setFont(tf)

    def metrics_at_px(self, px: float) -> QFontMetrics:
        """Metrics consistent with strip QSS font-size (px); avoids theme mismatch."""
        f = QFont(self._main_window.font())
        f.setPixelSize(
            max(STRIP_FONT_METRICS_FLOOR_PX, int(math.ceil(px)))
        )
        return QFontMetrics(f)

    def append_typography_css(self, style_sheet: str) -> str:
        """Append strip spacing rules (fonts use _apply_strip_local_font_styles per widget)."""
        if self._ctrl._strip_label_font_px is None or self._ctrl._strip_control_font_px is None:
            return style_sheet
        return (
            style_sheet
            + """
/* strip-typography layout */
QWidget#video_crop_strip QLabel,
QWidget#split_override_strip QLabel {
  padding: 0px;
}
QWidget#video_crop_strip QPushButton {
  padding: 0px 6px;
  min-height: 0px;
}
QWidget#video_crop_strip QAbstractSpinBox,
QWidget#split_override_strip QAbstractSpinBox {
  min-height: 0px;
}
QWidget#video_crop_strip QSpinBox,
QWidget#video_crop_strip QDoubleSpinBox,
QWidget#split_override_strip QSpinBox,
QWidget#split_override_strip QDoubleSpinBox {
  padding: 0px 1px 0px 0px;
}
QWidget#split_override_strip QToolButton#split_type_menu_button {
  min-height: 0px;
  padding: 0px;
}
"""
        )
