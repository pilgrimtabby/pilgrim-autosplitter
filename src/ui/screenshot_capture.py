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

"""Screenshot, burst capture, and Snap Peak / Peak Buffer saves."""

from __future__ import annotations

import datetime
import math
import os
import re
import time
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import TYPE_CHECKING, List, Optional, Tuple

import cv2
from PyQt5.QtCore import QEvent, QObject, QLocale, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import settings

if TYPE_CHECKING:
    from ui.ui_controller import UIController

PEAK_BUFFER_SUBDIR = "peak_buffer"
SNAP_PEAK_HOTKEY_LABEL = "Snap Peak"
PEAK_BUFFER_DIALOG_TITLE = "Snapped Peak Buffer"
PEAK_BUFFER_SAVED_SUMMARY = "Peak Buffer saved to:"

class _ScreenshotCountdownRing(QWidget):
    """Circular stroke ring; active arc shrinks clockwise as auto-close time runs out."""

    _DIAMETER = 22
    _STROKE = 2.25
    _START_ANGLE = 90 * 16  # 12 o'clock (top)

    def __init__(
        self,
        duration_ms: int,
        *,
        remaining_color: QColor,
        elapsed_color: QColor,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._duration_ms = max(1, duration_ms)
        self._start = time.monotonic()
        self._remaining_color = remaining_color
        self._elapsed_color = elapsed_color
        self.setFixedSize(self._DIAMETER, self._DIAMETER)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _remaining_fraction(self) -> float:
        elapsed_ms = (time.monotonic() - self._start) * 1000
        return max(0.0, min(1.0, 1.0 - elapsed_ms / self._duration_ms))

    def _tick(self) -> None:
        if self._remaining_fraction() <= 0:
            self._timer.stop()
        self.update()

    def stop(self) -> None:
        self._timer.stop()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        inset = max(2, int(math.ceil(self._STROKE / 2)) + 1)
        rect = self.rect().adjusted(inset, inset, -inset, -inset)

        track_pen = QPen(self._elapsed_color, self._STROKE)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        remaining = self._remaining_fraction()
        if remaining <= 0:
            return

        active_pen = QPen(self._remaining_color, self._STROKE)
        active_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(active_pen)
        span = int(round(remaining * 360 * 16))
        painter.drawArc(rect, self._START_ANGLE, -span)


class _ScreenshotSettingsDialog(QDialog):
    """Screenshot / burst options dialog: no auto-focus; click outside inputs clears focus."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)

    def _blur_focused_descendant(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        fw = app.focusWidget()
        if fw is None or not self.isAncestorOf(fw):
            return
        if isinstance(fw, QComboBox):
            fw.hidePopup()
        if isinstance(fw, QLineEdit):
            fw.deselect()
        fw.clearFocus()

    def _should_blur_for_mouse_press(self, watched: QObject) -> bool:
        if watched is self:
            return True
        if not isinstance(watched, QWidget) or not self.isAncestorOf(watched):
            return False
        app = QApplication.instance()
        if app is None:
            return False
        fw = app.focusWidget()
        if fw is None or not self.isAncestorOf(fw):
            return False
        if watched is fw:
            return False
        if watched.isAncestorOf(fw):
            return False
        # QAbstractSpinBox: focus can be on the wrapper while the press targets
        # the inner line edit (watched.isAncestorOf(fw) is false in that case).
        if isinstance(fw, QWidget) and fw.isAncestorOf(watched):
            return False
        return True

    def showEvent(self, event) -> None:
        super().showEvent(event)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        QTimer.singleShot(0, self._blur_focused_descendant)

    def hideEvent(self, event) -> None:
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress and self.isVisible():
            if self._should_blur_for_mouse_press(watched):
                self._blur_focused_descendant()
        return False


class ScreenshotCapture:
    """Single screenshot, burst capture, and Peak Buffer (Snap Peak) saves."""

    def __init__(self, controller: "UIController") -> None:
        self._ctrl = controller
        self._burst_capture_timer: Optional[QTimer] = None
        self._burst_shots_remaining = 0
        self._burst_saved_count = 0
        self._burst_in_progress = False
        self._burst_last_path: Optional[str] = None
        self._burst_session_dir: Optional[str] = None
        self._burst_overlay_deadline = 0.0
        self._burst_output_paths: List[str] = []
        self._burst_path_index = 0
        self._burst_pending_writes = 0
        self._burst_write_fail_count = 0
        self._burst_finishing = False
        self._burst_write_queue: Queue = Queue()
        self._burst_write_results: Queue = Queue()
        self._burst_writer_thread: Optional[Thread] = None

    @property
    def in_progress(self) -> bool:
        return self._burst_in_progress

    @property
    def overlay_deadline(self) -> float:
        return self._burst_overlay_deadline

    def sync_aux_controls_enabled(self) -> None:
        mw = self._ctrl._main_window
        # Settings (folder, burst mode, etc.) should work without live video; only
        # disable the gear while a burst is running (same as blocking the dialog).
        mw.screenshot_settings_button.setEnabled(not self._burst_in_progress)

    def output_dir_str(self) -> str:
        """Folder for screenshots, burst output, and Peak Buffer snaps."""
        configured = Path(settings.get_str("BURST_SHOTS_BASE_DIR")).expanduser()
        if configured.is_dir():
            return str(configured)
        return str(Path.home())

    def burst_base_dir_str(self) -> str:
        """Burst capture base directory."""
        return self.output_dir_str()

    def dated_session_folders_enabled(self) -> bool:
        """Prefer dated ``Burst shots …`` subfolders per run (default when unset)."""
        if not settings.settings.contains("BURST_DATED_SESSION_FOLDERS"):
            return True
        return settings.get_bool("BURST_DATED_SESSION_FOLDERS")

    def make_burst_session_folder(self, base: Path) -> Path:
        """Create ``Burst shots <date> <time>`` under ``base``; unique if needed."""
        base = base.expanduser()
        base.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        name = f"Burst shots {stamp}"
        path = base / name
        n = 0
        while path.exists():
            n += 1
            path = base / f"{name} ({n})"
        path.mkdir(parents=False, exist_ok=False)
        return path

    def exec_settings_dialog(self) -> None:
        if self._burst_in_progress:
            return
        mw = self._ctrl._main_window
        dlg = _ScreenshotSettingsDialog(mw)
        dlg.setWindowTitle("Screenshot settings")
        dlg.setModal(True)
        dlg.setAttribute(Qt.WA_TranslucentBackground, False)
        dlg.setAutoFillBackground(True)
        dlg.setFixedWidth(448)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(0)

        border_frame = QFrame(dlg)
        border_frame.setObjectName("border")
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(6)

        _init = Path(self.output_dir_str()).expanduser()
        folder_state: List[Path] = [_init if _init.is_dir() else Path.home()]

        panel = QWidget(border_frame)
        pan = QVBoxLayout(panel)
        pan.setContentsMargins(8, 2, 8, 4)
        pan.setSpacing(4)
        pan.setAlignment(Qt.AlignTop)

        _spin_w = 64
        # Left margin inside every field row + matching inner control width so
        # spinboxes and checkbox wrappers share the same column geometry.
        _field_cell_lmargin = 2
        _spin_inner = _spin_w - _field_cell_lmargin

        dur = QSpinBox(panel)
        dur.setRange(1, 60)
        dur.setSuffix(" s")
        _dur_sec = int(round(float(settings.get_float("BURST_DURATION_SEC"))))
        dur.setValue(max(1, min(60, _dur_sec)))
        dur.setFixedWidth(_spin_inner)
        fps = QDoubleSpinBox(panel)
        fps.setRange(1.0, 120.0)
        fps.setDecimals(0)
        fps.setSingleStep(1.0)
        fps.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        fps.setValue(int(round(float(settings.get_float("BURST_FPS")))))
        fps.setFixedWidth(_spin_inner)

        def make_settings_style_checkbox(
            checked: bool,
            field_w: int,
            *,
            wrap_object_name: str = "screenshot_dlg_checkbox_wrap",
        ) -> Tuple[QWidget, QCheckBox]:
            """Bordered helper + empty ``QCheckBox`` (same layout as ``UISettingsWindow``).

            Helper is at x=0 inside the wrapper so it lines up with ``QDoubleSpinBox``.
            ``field_w`` must match ``_spin_inner``. The helper is stacked above the
            checkbox so the indicator does not paint over the bordered frame.
            ``wrap_object_name`` must match stylesheet rules (burst vs dated row).
            """
            wrap = QWidget(panel)
            wrap.setObjectName(wrap_object_name)
            _pad_t, _pad_b = 2, 8
            _inset_l = 0
            cell_w = field_w
            cell_h = _pad_t + 15 + _pad_b
            wrap.setFixedSize(cell_w, cell_h)
            hx, hy = _inset_l, _pad_t
            # Match ``UISettingsWindow``: checkbox first, helper second so the helper
            # stacks above the indicator (otherwise ``raise_`` on the checkbox paints
            # over the bordered frame and the left stroke looks ``cut off'').
            cb = QCheckBox(wrap)
            cb.setText("")
            cb.setChecked(checked)
            cb.setFocusPolicy(Qt.ClickFocus)
            cb.setGeometry(hx, hy + 1, 13, 13)
            helper = QLabel(wrap)
            helper.setObjectName("checkbox_helper")
            helper.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            helper.setGeometry(hx, hy, 14, 15)
            helper.raise_()
            return wrap, cb

        burst_mode_label = QLabel("Burst mode:", panel)
        burst_mode_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        burst_mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        burst_mode_label.setToolTip("When on, the main button runs a timed burst capture.")
        burst_mode_wrap, burst_on = make_settings_style_checkbox(
            settings.get_bool("BURST_MODE_ENABLED"), _spin_inner
        )

        dated_label = QLabel("Create new folder:", panel)
        dated_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        dated_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        dated_label.setToolTip("")
        dated_wrap, burst_dated_folders = make_settings_style_checkbox(
            self.dated_session_folders_enabled(),
            _spin_inner,
            wrap_object_name="screenshot_dlg_dated_checkbox_wrap",
        )

        def sync_burst_folder_row() -> None:
            on = burst_on.isChecked()
            # Grey styling uses dynamic property ``burst_off`` (stylesheet), not
            # ``setEnabled`` on the wrapper — on some platforms disabled wrappers
            # left the inner checkbox looking grey after Burst mode was turned on.
            dated_wrap.setEnabled(True)
            burst_dated_folders.setEnabled(on)
            dated_wrap.setProperty("burst_off", not on)
            _st = dated_wrap.style()
            if _st is not None:
                _st.unpolish(dated_wrap)
                _st.polish(dated_wrap)
            _cb_st = burst_dated_folders.style()
            if _cb_st is not None:
                _cb_st.unpolish(burst_dated_folders)
                _cb_st.polish(burst_dated_folders)
            if on:
                dated_label.setStyleSheet("")
                dated_label.setToolTip("")
            else:
                dated_label.setStyleSheet("color: #888888;")
                dated_label.setToolTip("")

        burst_on.toggled.connect(sync_burst_folder_row)
        sync_burst_folder_row()

        _row_h = max(
            dur.sizeHint().height(),
            fps.sizeHint().height(),
            burst_mode_wrap.height(),
        )

        def form_field_cell(w: QWidget) -> QWidget:
            """Fixed-width field column (match spinboxes), uniform row height, left-aligned."""
            row = QWidget(panel)
            row.setFixedWidth(_spin_w)
            row.setMinimumHeight(_row_h)
            lay = QHBoxLayout(row)
            lay.setContentsMargins(_field_cell_lmargin, 0, 0, 0)
            lay.setSpacing(0)
            lay.addWidget(w, 0, Qt.AlignLeft | Qt.AlignVCenter)
            return row

        _form_opts = (
            (Qt.AlignLeft | Qt.AlignTop),
            (Qt.AlignLeft | Qt.AlignVCenter),
            QFormLayout.FieldsStayAtSizeHint,
            18,
            6,
        )
        fa, la, fgp, hs, vs = _form_opts

        left_form = QFormLayout()
        left_form.setFormAlignment(fa)
        left_form.setLabelAlignment(la)
        left_form.setFieldGrowthPolicy(fgp)
        left_form.setHorizontalSpacing(hs)
        left_form.setVerticalSpacing(vs)
        left_form.setContentsMargins(0, 0, 0, 0)
        left_form.addRow(burst_mode_label, form_field_cell(burst_mode_wrap))
        left_form.addRow(dated_label, form_field_cell(dated_wrap))

        right_form = QFormLayout()
        right_form.setFormAlignment(fa)
        right_form.setLabelAlignment(la)
        right_form.setFieldGrowthPolicy(fgp)
        right_form.setHorizontalSpacing(hs)
        right_form.setVerticalSpacing(vs)
        right_form.setContentsMargins(0, 0, 0, 0)
        right_form.addRow("Duration:", form_field_cell(dur))
        right_form.addRow("FPS:", form_field_cell(fps))

        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(20)
        columns.addLayout(left_form, 0)
        columns.addLayout(right_form, 0)
        columns.addStretch(1)
        pan.addLayout(columns)

        inner.addWidget(panel)

        def on_pick_folder() -> None:
            picked = QFileDialog.getExistingDirectory(
                dlg,
                "Select folder",
                str(folder_state[0]),
            )
            if not picked:
                return
            p = Path(picked)
            p.mkdir(parents=True, exist_ok=True)
            folder_state[0] = p

        def on_ok() -> None:
            exp = folder_state[0]
            if not exp.is_dir():
                QMessageBox.warning(
                    dlg,
                    "Folder",
                    "Choose a valid folder (use Select folder).",
                )
                return
            ss_resolved = str(exp.resolve())
            if not settings.path_is_within_home(ss_resolved):
                msg = self._ctrl._main_window.err_invalid_dir_msg
                msg.setStyleSheet(self._ctrl._get_style_sheet())
                msg.show()
                return

            settings.set_value("BURST_SHOTS_BASE_DIR", ss_resolved)

            settings.set_value("BURST_MODE_ENABLED", burst_on.isChecked())
            settings.set_value(
                "BURST_DATED_SESSION_FOLDERS",
                burst_on.isChecked() and burst_dated_folders.isChecked(),
            )
            settings.set_value("BURST_DURATION_SEC", float(dur.value()))
            settings.set_value("BURST_FPS", fps.value())
            dlg.accept()

        pick_folder_btn = QPushButton("Select folder", border_frame)
        pick_folder_btn.setFocusPolicy(Qt.NoFocus)
        pick_folder_btn.setDefault(False)
        pick_folder_btn.setAutoDefault(False)
        pick_folder_btn.setMinimumWidth(
            pick_folder_btn.fontMetrics().horizontalAdvance("Select folder") + 24
        )
        btn_cancel = QPushButton("Cancel", border_frame)
        btn_cancel.setFocusPolicy(Qt.NoFocus)
        btn_cancel.setDefault(False)
        btn_cancel.setAutoDefault(False)
        btn_ok = QPushButton("OK", border_frame)
        btn_ok.setFocusPolicy(Qt.NoFocus)
        btn_ok.setDefault(False)
        btn_ok.setAutoDefault(False)
        _btn_font = btn_ok.font()
        pick_folder_btn.setFont(_btn_font)
        btn_cancel.setFont(_btn_font)
        btn_ok.setFont(_btn_font)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        button_row.addWidget(pick_folder_btn)
        button_row.addStretch(1)
        button_row.addWidget(btn_cancel)
        button_row.addWidget(btn_ok)
        inner.addSpacing(6)
        inner.addLayout(button_row)

        root.addWidget(border_frame)
        dlg.setStyleSheet(self._ctrl._get_style_sheet())
        dlg.setFixedHeight(dlg.sizeHint().height())

        pick_folder_btn.clicked.connect(on_pick_folder)
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok.clicked.connect(on_ok)
        self._ctrl._clear_dialog_focus_after_show(dlg)

        if dlg.exec_() == QDialog.Accepted:
            self._ctrl._set_button_and_label_text(
                truncate=self._ctrl._layout_uses_truncated_control_text()
            )
            self._ctrl._update_pause_button()

    def take_screenshot(self) -> None:
        """Single screenshot, or burst capture when Burst mode is enabled."""
        if self._burst_in_progress:
            return
        if settings.get_bool("BURST_MODE_ENABLED"):
            self.start_burst_capture()
        else:
            self.take_single_screenshot()

    def take_single_screenshot(self) -> None:
        """Write ``splitter.comparison_frame`` to one file (optional open)."""
        frame = self._ctrl._splitter.comparison_frame
        if frame is None:
            msg = self._ctrl._main_window.screenshot_err_no_video
            msg.setStyleSheet(self._ctrl._get_style_sheet())
            msg.show()
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

        image_dir = self.output_dir_str()
        if not Path(image_dir).is_dir():
            image_dir = os.path.expanduser("~")

        screenshot_path = self.paths_for_count(image_dir, 1)[0]
        cv2.imwrite(screenshot_path, frame)

        if Path(screenshot_path).is_file():
            if settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._ctrl._open_file_or_dir(screenshot_path)
            else:
                self.show_saved_dialog(
                    window_title="Screenshot taken",
                    title="Screenshot taken",
                    summary="Screenshot saved to:",
                    location_path=self.saved_display_dir(),
                    preview_path=screenshot_path,
                )

        else:
            msg = self._ctrl._main_window.screenshot_err_no_file
            msg.setStyleSheet(self._ctrl._get_style_sheet())
            msg.show()
            QTimer.singleShot(10000, lambda: msg.done(0))

    def peak_filename_part(self, fraction: float) -> str:
        """Format a 0–1 match/threshold fraction for PNG filenames."""
        decimals = max(0, min(2, settings.get_int("MATCH_PERCENT_DECIMALS")))
        if decimals == 0:
            return str(round(fraction * 100))
        return f"{fraction * 100:.{decimals}f}"

    def sanitize_peak_filename_part(self, text: str) -> str:
        cleaned = re.sub(r"[^\w.-]+", "_", text.strip())
        return (cleaned[:60] if cleaned else "split")

    def peak_buffer_output_dir(self) -> Path:
        base = Path(self.output_dir_str())
        if not base.is_dir():
            base = Path(os.path.expanduser("~"))
        out = base / PEAK_BUFFER_SUBDIR
        out.mkdir(parents=True, exist_ok=True)
        return out

    def save_peak_buffer(self) -> None:
        """Write the Peak Buffer frame for the current split attempt."""
        frame, peak, threshold, split_name = (
            self._ctrl._splitter.get_highest_similarity_snapshot()
        )
        if frame is None:
            return

        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self.sanitize_peak_filename_part(split_name)
        high_part = self.peak_filename_part(peak)
        thresh_part = self.peak_filename_part(threshold)
        filename = f"{stamp}_{safe_name}_high{high_part}_thresh{thresh_part}.png"
        out_path = self.peak_buffer_output_dir() / filename

        if not cv2.imwrite(str(out_path), frame):
            return

        if settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
            self._ctrl._open_file_or_dir(str(out_path))
        else:
            decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
            self.show_saved_dialog(
                window_title=PEAK_BUFFER_DIALOG_TITLE,
                title=PEAK_BUFFER_DIALOG_TITLE,
                summary=PEAK_BUFFER_SAVED_SUMMARY,
                location_path=self.saved_display_dir(),
                preview_path=str(out_path),
                detail=(
                    f"High: {peak * 100:.{decimals}f}%  ·  "
                    f"Threshold: {threshold * 100:.{decimals}f}%"
                ),
            )

    def start_burst_capture(self) -> None:
        """Begin timed burst of PNGs from ``comparison_frame``."""
        frame = self._ctrl._splitter.comparison_frame
        if frame is None:
            msg = self._ctrl._main_window.screenshot_err_no_video
            msg.setStyleSheet(self._ctrl._get_style_sheet())
            msg.show()
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

        base = Path(self.burst_base_dir_str())
        use_dated_session = settings.get_bool(
            "BURST_MODE_ENABLED"
        ) and self.dated_session_folders_enabled()
        if use_dated_session:
            try:
                session_dir = self.make_burst_session_folder(base)
            except OSError:
                QMessageBox.warning(
                    self._ctrl._main_window,
                    "Burst folder",
                    "Could not create burst session folder.",
                )
                return
            self._burst_session_dir = str(session_dir)
        else:
            try:
                base.mkdir(parents=True, exist_ok=True)
            except OSError:
                QMessageBox.warning(
                    self._ctrl._main_window,
                    "Burst folder",
                    "Could not use burst folder.",
                )
                return
            self._burst_session_dir = str(base.resolve())

        duration = max(0.05, float(settings.get_float("BURST_DURATION_SEC")))
        fps = max(1.0, min(120.0, float(settings.get_float("BURST_FPS"))))
        interval_ms = max(1, int(round(1000.0 / fps)))
        self._burst_shots_remaining = max(1, int(round(duration * fps)))
        self._burst_saved_count = 0
        self._burst_last_path = None
        self._burst_output_paths = self.paths_for_count(
            self._burst_session_dir, self._burst_shots_remaining
        )
        self._burst_path_index = 0
        self._burst_pending_writes = 0
        self._burst_write_fail_count = 0
        self._burst_finishing = False
        self._burst_write_queue = Queue()
        self._burst_write_results = Queue()
        self._burst_writer_thread = Thread(
            target=self.burst_writer_loop,
            args=(self._burst_write_queue, self._burst_write_results),
            daemon=True,
        )
        self._burst_writer_thread.start()
        self._burst_in_progress = True
        self._burst_overlay_deadline = time.monotonic() + duration
        self.sync_aux_controls_enabled()
        self._ctrl._main_window.screenshot_button.setEnabled(False)

        if self._burst_capture_timer is None:
            self._burst_capture_timer = QTimer(self._ctrl._main_window)
            self._burst_capture_timer.timeout.connect(self.burst_capture_tick)
        else:
            self._burst_capture_timer.stop()
        self._burst_capture_timer.setInterval(interval_ms)
        self._burst_capture_timer.start()

    def saved_display_dir(self) -> str:
        """Configured screenshot folder (no burst session or peak_buffer subfolder)."""
        return str(Path(self.output_dir_str()).expanduser().resolve())

    def saved_path_label(
        self, parent: QWidget, display_path: str, max_width: int
    ) -> QLabel:
        """Single-line elided path for screenshot saved dialogs."""
        lbl = QLabel(parent)
        lbl.setObjectName("burst_complete_path")
        metrics = QFontMetrics(lbl.font())
        lbl.setText(metrics.elidedText(display_path, Qt.ElideMiddle, max_width))
        lbl.setWordWrap(False)
        return lbl

    def show_saved_dialog(
        self,
        *,
        window_title: str,
        title: str,
        summary: str,
        location_path: str,
        preview_path: Optional[str] = None,
        detail: Optional[str] = None,
        auto_close_ms: int = 7000,
    ) -> None:
        """Non-modal preview popup for screenshot, burst, and Peak Buffer snaps."""
        preview_width = 240
        content_spacing = 12
        text_min_width = 220
        outer_margin = 10
        inner_margin = 10

        dlg = QDialog(self._ctrl._main_window)
        dlg.setWindowTitle(window_title)
        dlg.setModal(False)
        dlg.setStyleSheet(self._ctrl._get_style_sheet())

        root = QVBoxLayout(dlg)
        root.setContentsMargins(outer_margin, outer_margin, outer_margin, outer_margin)
        root.setSpacing(0)

        border_frame = QFrame(dlg)
        border_frame.setObjectName("border")
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(inner_margin, inner_margin, inner_margin, inner_margin)
        inner.setSpacing(14)

        content = QHBoxLayout()
        content.setSpacing(content_spacing)
        content.setContentsMargins(0, 0, 0, 0)

        preview_file = preview_path if preview_path and Path(preview_path).is_file() else None
        preview_lbl = None
        if preview_file:
            pixmap = QPixmap(preview_file)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(
                    preview_width, Qt.SmoothTransformation
                )
                preview_lbl = QLabel(border_frame)
                preview_lbl.setPixmap(scaled)
                preview_lbl.setFixedSize(scaled.size())

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title, border_frame)
        title_font = QFont(title_lbl.font())
        title_font.setBold(True)
        if title_font.pointSize() > 0:
            title_font.setPointSize(title_font.pointSize() + 1)
        title_lbl.setFont(title_font)

        summary_lbl = QLabel(summary, border_frame)
        path_lbl = self.saved_path_label(
            border_frame, location_path, 340
        )

        text_col.addWidget(title_lbl)
        text_col.addWidget(summary_lbl)
        text_col.addWidget(path_lbl)
        if detail:
            detail_lbl = QLabel(detail, border_frame)
            detail_lbl.setObjectName("burst_complete_path")
            text_col.addWidget(detail_lbl)
        text_col.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        if settings.get_str("THEME") == "light":
            ring_remaining = QColor("#202020")
            ring_elapsed = QColor("#aaaaaa")
        else:
            ring_remaining = QColor("#ffffff")
            ring_elapsed = QColor("#555555")
        countdown_ring = _ScreenshotCountdownRing(
            auto_close_ms,
            remaining_color=ring_remaining,
            elapsed_color=ring_elapsed,
            parent=border_frame,
        )
        ok_btn = QPushButton("OK", border_frame)
        ok_btn.setFocusPolicy(Qt.NoFocus)
        ok_btn.setDefault(False)
        ok_btn.setAutoDefault(False)

        btn_row.addWidget(countdown_ring, 0, Qt.AlignVCenter)
        btn_row.addSpacing(8)
        btn_row.addWidget(ok_btn)
        text_col.addLayout(btn_row)

        text_host = QWidget(border_frame)
        text_host.setLayout(text_col)
        text_host.setMinimumWidth(text_min_width)
        content.addWidget(text_host, 1)

        if preview_lbl is not None:
            preview_col = QVBoxLayout()
            preview_col.setContentsMargins(0, 0, 0, 0)
            preview_col.addStretch(1)
            preview_col.addWidget(preview_lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
            preview_col.addStretch(1)
            preview_host = QWidget(border_frame)
            preview_host.setLayout(preview_col)
            preview_host.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            content.insertWidget(0, preview_host, 0)

        inner.addLayout(content)

        root.addWidget(border_frame)

        dlg.setMinimumWidth(420)
        dlg.adjustSize()

        dlg.show()
        self._ctrl._clear_dialog_focus_after_show(dlg)

        def _close_dialog() -> None:
            countdown_ring.stop()
            dlg.done(0)

        ok_btn.clicked.connect(_close_dialog)

        def _auto_close() -> None:
            try:
                if dlg.isVisible():
                    _close_dialog()
            except RuntimeError:
                pass

        QTimer.singleShot(auto_close_ms, _auto_close)

    def show_burst_complete_dialog(
        self, folder: str, saved_count: int, failed_count: int = 0
    ) -> None:
        """Non-modal summary after a burst."""
        if failed_count > 0:
            summary = f"{saved_count} frames saved ({failed_count} failed) to:"
        else:
            summary = f"{saved_count} frames saved to:"
        self.show_saved_dialog(
            window_title="Burst complete",
            title="Burst completed",
            summary=summary,
            location_path=self.saved_display_dir(),
            preview_path=self._burst_last_path,
            auto_close_ms=7000,
        )

    def burst_capture_tick(self) -> None:
        """Queue one frame per tick until burst quota is done."""
        self.drain_burst_write_results()
        if self._burst_finishing:
            if self._burst_pending_writes <= 0:
                self.complete_burst_capture()
            return

        frame = self._ctrl._splitter.comparison_frame
        if frame is not None and self._burst_path_index < len(self._burst_output_paths):
            path = self._burst_output_paths[self._burst_path_index]
            self._burst_path_index += 1
            self._burst_pending_writes += 1
            self._burst_write_queue.put((path, frame.copy()))

        self._burst_shots_remaining -= 1
        if self._burst_shots_remaining <= 0:
            self._burst_finishing = True
            self._burst_write_queue.put(None)
            if self._burst_capture_timer is not None:
                self._burst_capture_timer.setInterval(50)
            self.drain_burst_write_results()
            if self._burst_pending_writes <= 0:
                self.complete_burst_capture()

    def drain_burst_write_results(self) -> None:
        """Collect completed writer results on the UI thread."""
        while True:
            try:
                path, ok = self._burst_write_results.get_nowait()
            except Empty:
                return
            self._burst_pending_writes = max(0, self._burst_pending_writes - 1)
            if ok:
                self._burst_saved_count += 1
                self._burst_last_path = path
            else:
                self._burst_write_fail_count += 1

    def complete_burst_capture(self) -> None:
        if self._burst_capture_timer is not None:
            self._burst_capture_timer.stop()
        if self._burst_writer_thread is not None:
            self._burst_writer_thread.join(timeout=0.05)
        self._burst_in_progress = False
        self._burst_finishing = False
        session_dir = self._burst_session_dir
        self._burst_session_dir = None
        self._burst_output_paths = []
        self._burst_path_index = 0
        self._ctrl._set_buttons_and_hotkeys_enabled()
        if self._burst_saved_count > 0 and settings.get_bool(
            "OPEN_SCREENSHOT_ON_CAPTURE"
        ):
            if self._burst_last_path:
                self._ctrl._open_file_or_dir(self._burst_last_path)
        out_dir = session_dir or self.burst_base_dir_str()
        self.show_burst_complete_dialog(
            out_dir, self._burst_saved_count, self._burst_write_fail_count
        )

    def burst_writer_loop(self, jobs: Queue, results: Queue) -> None:
        """Write burst frames away from the Qt UI thread."""
        while True:
            job = jobs.get()
            try:
                if job is None:
                    return
                path, frame = job
                ok = False
                try:
                    ok = bool(cv2.imwrite(path, frame)) and Path(path).is_file()
                except Exception:
                    ok = False
                results.put((path, ok))
            finally:
                jobs.task_done()

    def paths_for_count(self, dir: str, count: int) -> List[str]:
        """Return unique screenshot paths with one directory scan."""
        target_dir = Path(dir)
        used = set()
        for child in target_dir.glob("*.png"):
            match = re.match(r"^(\d+)", child.name)
            if match:
                try:
                    used.add(int(match.group(1)))
                except ValueError:
                    pass

        paths = []
        file_int = 0
        for _ in range(max(0, count)):
            while file_int in used:
                file_int += 1
            used.add(file_int)
            paths.append(str(target_dir / f"{file_int:03d}_screenshot.png"))
            file_int += 1
        return paths
