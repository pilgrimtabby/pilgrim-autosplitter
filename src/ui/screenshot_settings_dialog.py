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

"""Screenshot / burst settings dialog."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from PyQt5.QtCore import QEvent, QObject, QLocale, Qt, QTimer
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
    from ui.screenshot_capture import ScreenshotCapture


class ScreenshotSettingsDialog(QDialog):
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


def exec_screenshot_settings_dialog(capture: "ScreenshotCapture") -> bool:
    """Show screenshot settings; return True when the user accepts."""
    ctrl = capture._ctrl
    mw = ctrl._main_window
    dlg = ScreenshotSettingsDialog(mw)
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

    _init = Path(capture.output_dir_str()).expanduser()
    folder_state: List[Path] = [_init if _init.is_dir() else Path.home()]

    panel = QWidget(border_frame)
    pan = QVBoxLayout(panel)
    pan.setContentsMargins(8, 2, 8, 4)
    pan.setSpacing(4)
    pan.setAlignment(Qt.AlignTop)

    _spin_w = 64
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
        wrap = QWidget(panel)
        wrap.setObjectName(wrap_object_name)
        _pad_t, _pad_b = 2, 8
        _inset_l = 0
        cell_w = field_w
        cell_h = _pad_t + 15 + _pad_b
        wrap.setFixedSize(cell_w, cell_h)
        hx, hy = _inset_l, _pad_t
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
        capture.dated_session_folders_enabled(),
        _spin_inner,
        wrap_object_name="screenshot_dlg_dated_checkbox_wrap",
    )

    def sync_burst_folder_row() -> None:
        on = burst_on.isChecked()
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
            msg = mw.err_invalid_dir_msg
            msg.setStyleSheet(ctrl._get_style_sheet())
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
    dlg.setStyleSheet(ctrl._get_style_sheet())
    dlg.setFixedHeight(dlg.sizeHint().height())

    pick_folder_btn.clicked.connect(on_pick_folder)
    btn_cancel.clicked.connect(dlg.reject)
    btn_ok.clicked.connect(on_ok)
    ctrl._clear_dialog_focus_after_show(dlg)

    return dlg.exec_() == QDialog.Accepted
