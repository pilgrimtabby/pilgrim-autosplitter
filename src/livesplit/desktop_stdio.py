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

"""LiveSplit Desktop integration via stdin/stdout (--auto-controlled).

Compatible with Toufool's LiveSplit.AutoSplitIntegration component: LiveSplit
launches Pilgrim with ``--auto-controlled``, redirects stdin/stdout, and
exchanges plain-text command lines.

Outbound (Pilgrim → LiveSplit): ``start``, ``split``, ``reset``, ``pause``.
Inbound (LiveSplit → Pilgrim): ``start``, ``split``, ``skip``, ``undo``,
``reset``, ``settings|<path>``, ``kill``.

Pilgrim has no separate start-image file. Autosplit uses start-or-split:
emit ``start`` when the timer is not running, otherwise ``split`` (same idea
as LiveSplit One ``splitOrStart``). That works with stock AutoSplit
Integration; the patched component under ``livesplit-desktop-integration/``
is optional and still treats outbound ``split`` as start-or-split.

Inbound ``start`` means “timer started in LiveSplit — begin/ensure comparing,”
not “advance a start split.”

Inbound ``split`` and ``skip`` both advance one ``@N@`` loop cycle when
mid-loop; on the last cycle (or a non-looping image) they skip the
Toufool-style dummy group so Pilgrim stays aligned with LiveSplit's visible
segments. With no timer link, Pilgrim's Skip button always advances one
image/loop cycle (classic behavior — no group jump).
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal

_AUTO_CONTROLLED_FLAG = "--auto-controlled"
_MANUAL_NAV_COOLDOWN_SEC = 0.75


def is_auto_controlled(argv: Optional[list[str]] = None) -> bool:
    """Return True when launched by LiveSplit Desktop's AutoSplit Integration."""
    args = sys.argv if argv is None else argv
    return _AUTO_CONTROLLED_FLAG in args


def strip_auto_controlled_flag(argv: Optional[list[str]] = None) -> list[str]:
    """Return argv without ``--auto-controlled`` (for QApplication)."""
    args = list(sys.argv if argv is None else argv)
    return [a for a in args if a != _AUTO_CONTROLLED_FLAG]


def print_handshake(version: str) -> None:
    """Print version and PID as the first two stdout lines (required by the component)."""
    # THIS HAS TO BE THE FIRST TWO LINES SENT on stdout.
    print(f"{version}\n{os.getpid()}", flush=True)


def emit_command(command: str) -> None:
    """Send a command line to LiveSplit on stdout."""
    print(command, flush=True)


class _StdinReader(QObject):
    """Background stdin reader; emits lines on the Qt main thread via signal."""

    line_received = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="ls-desktop-stdin"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                line = sys.stdin.readline()
            except (RuntimeError, OSError, ValueError):
                break
            if line == "":
                # EOF — LiveSplit closed the pipe; keep waiting briefly then exit.
                if self._stop.wait(0.25):
                    break
                continue
            text = line.strip()
            if text:
                self.line_received.emit(text)


class DesktopStdioSession:
    """Session state for LiveSplit Desktop stdio control."""

    def __init__(self) -> None:
        self._active = False
        self._timer_running = False
        self._reader: Optional[_StdinReader] = None
        self._manual_nav_deadline = 0.0
        self._on_line: Optional[Callable[[str], None]] = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def timer_running(self) -> bool:
        """Best-effort: True after start, False after reset (stdio has no phase query)."""
        return self._timer_running

    def set_timer_running(self, running: bool) -> None:
        self._timer_running = running

    def start(self, on_line: Callable[[str], None]) -> None:
        """Begin listening for LiveSplit stdin commands."""
        if self._active:
            return
        self._on_line = on_line
        self._timer_running = False
        self._reader = _StdinReader()
        self._reader.line_received.connect(self._dispatch_line)
        self._reader.start()
        self._active = True

    def stop(self) -> None:
        if self._reader is not None:
            self._reader.stop()
            try:
                self._reader.line_received.disconnect(self._dispatch_line)
            except TypeError:
                pass
            self._reader = None
        self._active = False
        self._timer_running = False
        self._on_line = None

    def emit(self, command: str) -> bool:
        if not self._active:
            return False
        emit_command(command)
        if command == "reset":
            self._timer_running = False
        elif command == "start":
            self._timer_running = True
        return True

    def emit_split_or_start(self) -> bool:
        """Start the timer if needed, otherwise split (stock AutoSplit Integration)."""
        if not self._active:
            return False
        if self._timer_running:
            emit_command("split")
        else:
            emit_command("start")
            self._timer_running = True
        return True

    def after_manual_navigation(self) -> None:
        """Ignore autosplit timer commands briefly after manual skip/undo/reset."""
        self._manual_nav_deadline = time.monotonic() + _MANUAL_NAV_COOLDOWN_SEC

    def autosplit_may_send(self) -> bool:
        return time.monotonic() >= self._manual_nav_deadline

    def _dispatch_line(self, line: str) -> None:
        if self._on_line is not None:
            self._on_line(line)
