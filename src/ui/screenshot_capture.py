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
from PyQt5.QtCore import QEvent, QObject, QLocale, Qt, QTimer, pyqtSignal
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
from ui.labels import (
    PEAK_BUFFER_DIALOG_TITLE,
    PEAK_BUFFER_SAVED_SUMMARY,
    PEAK_BUFFER_SUBDIR,
    SNAP_PEAK_HOTKEY_LABEL,
)
from ui.screenshot_settings_dialog import exec_screenshot_settings_dialog
from ui.slot_errors import log_slot_error

if TYPE_CHECKING:
    from ui.ui_controller import UIController


class _ScreenshotCountdownRing(QWidget):
    """Circular stroke ring; active arc shrinks clockwise as auto-close time runs out."""

    finished = pyqtSignal()

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
        self._finished_emitted = False
        self.setFixedSize(self._DIAMETER, self._DIAMETER)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        """Begin the countdown when the popup is actually visible."""
        self._start = time.monotonic()
        self._finished_emitted = False
        self._timer.start(40)
        self.update()

    def _remaining_fraction(self) -> float:
        elapsed_ms = (time.monotonic() - self._start) * 1000
        return max(0.0, min(1.0, 1.0 - elapsed_ms / self._duration_ms))

    def _tick(self) -> None:
        if self._remaining_fraction() <= 0:
            self._timer.stop()
            if not self._finished_emitted:
                self._finished_emitted = True
                self.finished.emit()
        self.update()

    def stop(self, *, complete: bool = False) -> None:
        """Stop ticking. If ``complete``, snap the ring empty for close/fade."""
        self._timer.stop()
        if complete:
            self._start = time.monotonic() - self._duration_ms
            self._finished_emitted = True
        self.update()

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
        if exec_screenshot_settings_dialog(self):
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

    def folder_to_open_from_saved(
        self, location_path: str, preview_path: Optional[str] = None
    ) -> str:
        """Folder revealed by ``Open folder``: preview's parent, else location."""
        if preview_path:
            preview = Path(preview_path).expanduser()
            if preview.is_file():
                return str(preview.parent.resolve())
            if preview.is_dir():
                return str(preview.resolve())
        loc = Path(location_path).expanduser()
        try:
            return str(loc.resolve())
        except OSError:
            return location_path

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

        open_folder_btn = QPushButton("Open folder", border_frame)
        open_folder_btn.setFocusPolicy(Qt.NoFocus)
        open_folder_btn.setDefault(False)
        open_folder_btn.setAutoDefault(False)
        open_folder_path = self.folder_to_open_from_saved(location_path, preview_path)

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

        # Bottom actions: countdown, then Open folder, then OK.
        btn_row.addWidget(countdown_ring, 0, Qt.AlignVCenter)
        btn_row.addSpacing(8)
        btn_row.addWidget(open_folder_btn, 0, Qt.AlignVCenter)
        btn_row.addSpacing(8)
        btn_row.addWidget(ok_btn)
        text_col.addLayout(btn_row)

        text_host = QWidget(border_frame)
        text_host.setLayout(text_col)
        text_host.setMinimumWidth(text_min_width)
        content.addWidget(text_host, 1)

        if preview_lbl is not None:
            content.insertWidget(0, preview_lbl, 0, Qt.AlignVCenter)

        inner.addLayout(content)

        root.addWidget(border_frame)

        dlg.setMinimumWidth(420)
        dlg.adjustSize()

        dlg.show()
        self._ctrl._clear_dialog_focus_after_show(dlg)

        def _close_dialog() -> None:
            try:
                countdown_ring.finished.disconnect(_close_dialog)
            except TypeError:
                pass
            # Empty the ring before close so it is not still ticking during fade.
            countdown_ring.stop(complete=True)
            QApplication.processEvents()
            try:
                if dlg.isVisible():
                    dlg.done(0)
            except RuntimeError:
                pass

        def _open_folder() -> None:
            self._ctrl._open_file_or_dir(open_folder_path)

        open_folder_btn.clicked.connect(_open_folder)
        ok_btn.clicked.connect(_close_dialog)
        # Close only when the ring finishes — not a separate timer that can drift.
        countdown_ring.finished.connect(_close_dialog)
        countdown_ring.start()

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
            location_path=folder,
            preview_path=self._burst_last_path,
            auto_close_ms=7000,
        )

    def burst_capture_tick(self) -> None:
        """Queue one frame per tick until burst quota is done."""
        try:
            self._burst_capture_tick_body()
        except Exception as exc:
            log_slot_error("Burst capture", exc)

    def _burst_capture_tick_body(self) -> None:
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
