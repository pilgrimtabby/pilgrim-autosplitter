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

"""Shared window chrome helpers (Windows title-bar flags, etc.)."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QWidget


def disable_context_help(window: QWidget) -> None:
    """Remove the Windows title-bar '?' (What's This) button."""
    window.setWindowFlag(Qt.WindowContextHelpButtonHint, False)


def message_warning(
    parent: Optional[QWidget],
    title: str,
    text: str,
    informative: str = "",
) -> int:
    """``QMessageBox.warning`` without the Windows context-help button."""
    box = QMessageBox(parent)
    disable_context_help(box)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    if informative:
        box.setInformativeText(informative)
    return box.exec_()


def message_information(
    parent: Optional[QWidget],
    title: str,
    text: str,
    informative: str = "",
) -> int:
    """``QMessageBox.information`` without the Windows context-help button."""
    box = QMessageBox(parent)
    disable_context_help(box)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(text)
    if informative:
        box.setInformativeText(informative)
    return box.exec_()
