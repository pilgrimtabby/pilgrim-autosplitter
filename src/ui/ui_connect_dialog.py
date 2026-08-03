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

"""Dialogs for LiveSplit One WebSocket server and connection status."""

from typing import Callable, Optional

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

from ui.window_chrome import disable_context_help

_DOT_SIZE = 5
_URL_H_PAD = 12  # matches QLineEdit#connect_ws_url horizontal padding (6px each side)
_URL_V_PAD = 6   # matches QLineEdit#connect_ws_url vertical padding (3px each side)
_URL_WIDTH_SLACK = 4
_DIALOG_BREATHING = 36  # horizontal room past the widest line / URL text


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


def _set_status_dot(dot_label: QLabel, *, connected: bool) -> None:
    color = "#2ecc71" if connected else "#808080"
    dot_label.setStyleSheet(
        "QLabel#connect_status_dot {"
        f" background-color: {color};"
        " border-radius: 2px;"
        " padding: 0px; margin: 0px;"
        " }"
    )


class UIConnectWebSocketDialog(QDialog):
    """Show the WebSocket URL and allow copying it for LiveSplit One."""

    def __init__(
        self,
        url: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("WebSocket Server")
        disable_context_help(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        border_frame = QFrame(self)
        border_frame.setObjectName("border")
        self._border_frame = border_frame
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

        self._intro = QLabel(
            "Paste this URL into LiveSplit One:\n"
            "Settings → Server Connection → Connect",
            border_frame,
        )
        self._intro.setWordWrap(True)

        self._url_field = _ConnectUrlLineEdit(url, border_frame)
        self._url_field.setObjectName("connect_ws_url")
        self._url_field.setReadOnly(True)

        copy_row = QHBoxLayout()
        copy_row.setContentsMargins(0, 0, 0, 0)
        copy_row.setSpacing(6)
        copy_button = QPushButton("Copy URL", border_frame)
        copy_button.setFocusPolicy(Qt.NoFocus)
        copy_button.setAutoDefault(False)
        copy_button.setDefault(False)
        copy_button.clicked.connect(self._copy_url)
        copy_row.addWidget(copy_button)
        copy_row.addStretch(1)

        self._close_button = QPushButton("Close", border_frame)
        self._close_button.setFocusPolicy(Qt.NoFocus)
        self._close_button.setAutoDefault(False)
        self._close_button.setDefault(False)
        self._close_button.clicked.connect(self.reject)
        copy_row.addWidget(self._close_button, 0, Qt.AlignVCenter)

        inner.addWidget(self._intro)
        inner.addWidget(self._url_field)
        inner.addLayout(copy_row)

        root.addWidget(border_frame)

    def _fit_url_field_size(self) -> None:
        url = self._url_field.text()
        fm = QFontMetrics(self._url_field.font())
        style = self._url_field.style()
        frame = style.pixelMetric(QStyle.PM_DefaultFrameWidth) * 2
        url_w = fm.horizontalAdvance(url) + frame + _URL_H_PAD + _URL_WIDTH_SLACK
        intro_fm = QFontMetrics(self._intro.font())
        intro_w = max(
            (intro_fm.horizontalAdvance(line) for line in self._intro.text().splitlines()),
            default=0,
        )
        content_w = max(url_w, intro_w) + _DIALOG_BREATHING
        height = max(self._url_field.sizeHint().height(), fm.height() + _URL_V_PAD)
        self._url_field.setFixedSize(content_w, height)
        # +20 matches inner layout left/right margins
        self._border_frame.setMinimumWidth(content_w + 20)

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

    def _copy_url(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._url_field.text())


_STATUS_TEXTS = (
    "Disconnected",
    "Connected to LiveSplit",
    "Connected to LiveSplit One",
)
_STATUS_WIDTH_SLACK = 24  # room past the longest label (dot gap + comfort)


class UIConnectStatusDialog(QDialog):
    """Show LiveSplit / LiveSplit One connection status with a status dot."""

    def __init__(
        self,
        *,
        connection_kind: Callable[[], Optional[str]],
        parent=None,
    ) -> None:
        """Create the status dialog.

        Args:
            connection_kind: Returns ``"desktop"``, ``"one"``, or ``None``.
        """
        super().__init__(parent)
        self.setWindowTitle("Status")
        disable_context_help(self)
        self._connection_kind = connection_kind

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        border_frame = QFrame(self)
        border_frame.setObjectName("border")
        self._border_frame = border_frame
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)

        self._dot_label = QLabel(border_frame)
        self._dot_label.setObjectName("connect_status_dot")
        self._dot_label.setFixedSize(_DOT_SIZE, _DOT_SIZE)

        self._status_label = QLabel(border_frame)

        status_row.addWidget(self._dot_label, 0, Qt.AlignVCenter)
        status_row.addWidget(self._status_label, 0, Qt.AlignVCenter)
        status_row.addStretch(1)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addStretch(1)

        self._ok_button = QPushButton("Ok", border_frame)
        self._ok_button.setFocusPolicy(Qt.NoFocus)
        self._ok_button.setAutoDefault(False)
        self._ok_button.setDefault(False)
        self._ok_button.clicked.connect(self.accept)
        footer_row.addWidget(self._ok_button, 0, Qt.AlignVCenter)

        inner.addLayout(status_row)
        inner.addLayout(footer_row)
        root.addWidget(border_frame)

        self._refresh_connection_status()
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._refresh_connection_status)
        self._poll.start()

    def _fit_status_width(self) -> None:
        """Lock width to the longest status string so the dialog does not resize."""
        fm = QFontMetrics(self._status_label.font())
        text_w = max(fm.horizontalAdvance(t) for t in _STATUS_TEXTS)
        content_w = _DOT_SIZE + 6 + text_w + _STATUS_WIDTH_SLACK
        ok_w = self._ok_button.sizeHint().width()
        inner = max(content_w, ok_w)
        self._border_frame.setFixedWidth(inner + 20)  # inner layout margins
        self._status_label.setMinimumWidth(text_w)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_status_width()
        QTimer.singleShot(0, self._clear_initial_focus)

    def _clear_initial_focus(self) -> None:
        focused = QApplication.focusWidget()
        if focused is not None and self.isAncestorOf(focused):
            focused.clearFocus()
        self.setFocus(Qt.OtherFocusReason)

    def _refresh_connection_status(self) -> None:
        kind = self._connection_kind()
        connected = kind is not None
        _set_status_dot(self._dot_label, connected=connected)
        if kind == "desktop":
            text = "Connected to LiveSplit"
        elif kind == "one":
            text = "Connected to LiveSplit One"
        else:
            text = "Disconnected"
        self._status_label.setText(text)

    def closeEvent(self, event) -> None:
        self._poll.stop()
        super().closeEvent(event)

    def accept(self) -> None:
        self._poll.stop()
        super().accept()

    def reject(self) -> None:
        self._poll.stop()
        super().reject()
