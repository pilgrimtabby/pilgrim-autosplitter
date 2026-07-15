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

"""Video crop inset spinboxes with undo/redo."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

import settings

if TYPE_CHECKING:
    from ui.ui_controller import UIController

MAX_VIDEO_CROP_UNDO = 100


class VideoCropController:
    """Crop inset UI, persistence, and undo/redo stacks."""

    def __init__(self, controller: "UIController") -> None:
        self._ctrl = controller
        self._undo_stack: List[Tuple[int, int, int, int]] = []
        self._redo_stack: List[Tuple[int, int, int, int]] = []
        self._snapshot: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self._undo_guard = False
        mw = controller._main_window
        self._undo_shortcut = QShortcut(QKeySequence.Undo, mw)
        self._undo_shortcut.setContext(Qt.WindowShortcut)
        self._undo_shortcut.activated.connect(self.undo)
        self._redo_shortcut = QShortcut(QKeySequence.Redo, mw)
        self._redo_shortcut.setContext(Qt.WindowShortcut)
        self._redo_shortcut.activated.connect(self.redo)
        self.sync_from_settings()

    def wire_controls(self) -> None:
        """Crop inset spinboxes (pixels trimmed per capture edge before resize)."""
        mw = self._ctrl._main_window
        mw.video_crop_spin_left.valueChanged.connect(self.on_spin_changed)
        mw.video_crop_spin_right.valueChanged.connect(self.on_spin_changed)
        mw.video_crop_spin_up.valueChanged.connect(self.on_spin_changed)
        mw.video_crop_spin_down.valueChanged.connect(self.on_spin_changed)
        mw.video_crop_btn_reset.clicked.connect(self.reset_insets)

        mw.setTabOrder(mw.video_crop_spin_left, mw.video_crop_spin_right)
        mw.setTabOrder(mw.video_crop_spin_right, mw.video_crop_spin_up)
        mw.setTabOrder(mw.video_crop_spin_up, mw.video_crop_spin_down)
        mw.setTabOrder(mw.video_crop_spin_down, mw.split_threshold_spin)
        mw.setTabOrder(mw.split_threshold_spin, mw.split_delay_spin)
        mw.setTabOrder(mw.split_delay_spin, mw.split_loop_spin)
        mw.setTabOrder(mw.split_loop_spin, mw.split_pause_spin)
        mw.setTabOrder(mw.split_pause_spin, mw.split_type_menu_button)

    def tuple_from_widgets(self) -> Tuple[int, int, int, int]:
        mw = self._ctrl._main_window
        return (
            int(mw.video_crop_spin_left.value()),
            int(mw.video_crop_spin_right.value()),
            int(mw.video_crop_spin_up.value()),
            int(mw.video_crop_spin_down.value()),
        )

    def persist_tuple(self, tup: Tuple[int, int, int, int]) -> None:
        l_, r_, t_, b_ = tup
        settings.set_value("VIDEO_CROP_INSET_LEFT", l_)
        settings.set_value("VIDEO_CROP_INSET_RIGHT", r_)
        settings.set_value("VIDEO_CROP_INSET_TOP", t_)
        settings.set_value("VIDEO_CROP_INSET_BOTTOM", b_)

    def apply_tuple_to_widgets(self, tup: Tuple[int, int, int, int]) -> None:
        mw = self._ctrl._main_window
        spins = (
            mw.video_crop_spin_left,
            mw.video_crop_spin_right,
            mw.video_crop_spin_up,
            mw.video_crop_spin_down,
        )
        for spin, val in zip(spins, tup):
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)

    def _trim_undo_stack(self) -> None:
        while len(self._undo_stack) > MAX_VIDEO_CROP_UNDO:
            self._undo_stack.pop(0)

    def _trim_redo_stack(self) -> None:
        while len(self._redo_stack) > MAX_VIDEO_CROP_UNDO:
            self._redo_stack.pop(0)

    def _update_shortcuts(self) -> None:
        self._undo_shortcut.setEnabled(bool(self._undo_stack))
        self._redo_shortcut.setEnabled(bool(self._redo_stack))

    def _update_reset_enabled(self) -> None:
        self._ctrl._main_window.video_crop_btn_reset.setEnabled(
            self.tuple_from_widgets() != (0, 0, 0, 0)
        )

    def on_spin_changed(self, _value: int) -> None:
        if self._undo_guard:
            return
        curr = self.tuple_from_widgets()
        if curr == self._snapshot:
            return
        self._redo_stack.clear()
        self._undo_stack.append(self._snapshot)
        self._trim_undo_stack()
        self._snapshot = curr
        self.persist_tuple(curr)
        self._update_shortcuts()
        self._update_reset_enabled()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        curr = self._snapshot
        self._redo_stack.append(curr)
        self._trim_redo_stack()
        prev = self._undo_stack.pop()
        self._undo_guard = True
        try:
            self.apply_tuple_to_widgets(prev)
            self._snapshot = prev
            self.persist_tuple(prev)
        finally:
            self._undo_guard = False
        self._update_shortcuts()
        self._update_reset_enabled()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        curr = self._snapshot
        self._undo_stack.append(curr)
        self._trim_undo_stack()
        nxt = self._redo_stack.pop()
        self._undo_guard = True
        try:
            self.apply_tuple_to_widgets(nxt)
            self._snapshot = nxt
            self.persist_tuple(nxt)
        finally:
            self._undo_guard = False
        self._update_shortcuts()
        self._update_reset_enabled()

    def reset_insets(self) -> None:
        """All-zero insets means full frame (no crop)."""
        self._redo_stack.clear()
        if self._snapshot != (0, 0, 0, 0):
            self._undo_stack.append(self._snapshot)
            self._trim_undo_stack()

        self._undo_guard = True
        try:
            self.apply_tuple_to_widgets((0, 0, 0, 0))
            self._snapshot = (0, 0, 0, 0)
            self.persist_tuple(self._snapshot)
        finally:
            self._undo_guard = False
        self._update_shortcuts()
        self._update_reset_enabled()

    def sync_from_settings(self) -> None:
        """Load crop spinboxes from persisted settings without emitting signals."""
        mw = self._ctrl._main_window
        mapping = (
            (mw.video_crop_spin_left, "VIDEO_CROP_INSET_LEFT"),
            (mw.video_crop_spin_right, "VIDEO_CROP_INSET_RIGHT"),
            (mw.video_crop_spin_up, "VIDEO_CROP_INSET_TOP"),
            (mw.video_crop_spin_down, "VIDEO_CROP_INSET_BOTTOM"),
        )
        self._undo_guard = True
        try:
            for spin, key in mapping:
                spin.blockSignals(True)
                spin.setValue(settings.get_int_nonneg(key))
                spin.blockSignals(False)
            self._snapshot = self.tuple_from_widgets()
            self._undo_stack.clear()
            self._redo_stack.clear()
        finally:
            self._undo_guard = False
        self._update_shortcuts()
        self._update_reset_enabled()
