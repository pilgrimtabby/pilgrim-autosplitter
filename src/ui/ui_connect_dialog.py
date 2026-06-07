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

"""Dialog for starting the LiveSplit One WebSocket server."""

from typing import Callable

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QFontMetrics, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

_DOT_SIZE = 5
_URL_H_PAD = 12  # matches QLineEdit#connect_ws_url horizontal padding (6px each side)
_URL_V_PAD = 6   # matches QLineEdit#connect_ws_url vertical padding (3px each side)
_URL_WIDTH_SLACK = 4
_DIALOG_EXTRA_WIDTH = 28  # whole popup slightly wider than the URL field


class _ConnectUrlLineEdit(QLineEdit):
    """Read-only URL field: select all on click; styled context menu."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.selectAll()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        select_action = menu.addAction("Select All")
        copy_action.triggered.connect(self._copy_from_menu)
        select_action.triggered.connect(self.selectAll)
        menu.exec_(event.globalPos())

    def _copy_from_menu(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = self.selectedText() or self.text()
        clipboard.setText(text)


class UIConnectWebSocketDialog(QDialog):
    """Show the WebSocket URL and allow copying it for LiveSplit One."""

    def __init__(
        self,
        url: str,
        *,
        is_connected: Callable[[], bool],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("WebSocket Server")
        self._is_connected = is_connected

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        border_frame = QFrame(self)
        border_frame.setObjectName("border")
        self._border_frame = border_frame
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

        intro = QLabel(
            "Paste this URL into LiveSplit One:\n"
            "Settings → Server Connection → Connect",
            border_frame,
        )
        intro.setWordWrap(True)

        self._url_field = _ConnectUrlLineEdit(url, border_frame)
        self._url_field.setObjectName("connect_ws_url")
        self._url_field.setReadOnly(True)

        copy_row = QHBoxLayout()
        copy_row.setContentsMargins(0, 0, 0, 0)
        copy_button = QPushButton("Copy URL", border_frame)
        copy_button.setFocusPolicy(Qt.NoFocus)
        copy_button.setAutoDefault(False)
        copy_button.setDefault(False)
        copy_button.clicked.connect(self._copy_url)
        copy_row.addWidget(copy_button)
        copy_row.addStretch(1)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.setSpacing(6)

        self._dot_label = QLabel(border_frame)
        self._dot_label.setObjectName("connect_status_dot")
        self._dot_label.setFixedSize(_DOT_SIZE, _DOT_SIZE)

        self._status_label = QLabel(border_frame)

        self._close_button = QPushButton("Close", border_frame)
        self._close_button.setFocusPolicy(Qt.NoFocus)
        self._close_button.setAutoDefault(False)
        self._close_button.setDefault(False)
        self._close_button.clicked.connect(self.reject)

        footer_row.addWidget(self._dot_label, 0, Qt.AlignVCenter)
        footer_row.addWidget(self._status_label, 0, Qt.AlignVCenter)
        footer_row.addStretch(1)
        footer_row.addWidget(self._close_button, 0, Qt.AlignVCenter)

        inner.addWidget(intro)
        inner.addWidget(self._url_field)
        inner.addLayout(copy_row)
        inner.addLayout(footer_row)

        root.addWidget(border_frame)

        self._refresh_connection_status()
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._refresh_connection_status)
        self._poll.start()

    def _fit_url_field_size(self) -> None:
        url = self._url_field.text()
        fm = QFontMetrics(self._url_field.font())
        style = self._url_field.style()
        frame = style.pixelMetric(QStyle.PM_DefaultFrameWidth) * 2
        text_w = fm.horizontalAdvance(url)
        width = text_w + frame + _URL_H_PAD + _URL_WIDTH_SLACK
        height = max(self._url_field.sizeHint().height(), fm.height() + _URL_V_PAD)
        self._url_field.setFixedSize(width, height)
        self._border_frame.setMinimumWidth(width + _DIALOG_EXTRA_WIDTH)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_url_field_size()
        self._url_field.deselect()
        QTimer.singleShot(0, self._clear_initial_focus)

    def _clear_initial_focus(self) -> None:
        focused = QApplication.focusWidget()
        if focused is not None and self.isAncestorOf(focused):
            focused.clearFocus()
        self.setFocus(Qt.OtherFocusReason)

    def _refresh_connection_status(self) -> None:
        connected = bool(self._is_connected())
        color = "#2ecc71" if connected else "#808080"
        text = "Connected" if connected else "Disconnected"
        self._dot_label.setStyleSheet(
            "QLabel#connect_status_dot {"
            f" background-color: {color};"
            " border-radius: 2px;"
            " padding: 0px; margin: 0px;"
            " }"
        )
        self._status_label.setText(text)

    def _copy_url(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._url_field.text())

    def closeEvent(self, event) -> None:
        self._poll.stop()
        super().closeEvent(event)

    def reject(self) -> None:
        self._poll.stop()
        super().reject()
