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

"""LiveSplit One timer commands over the WebSocket server protocol."""

from __future__ import annotations

import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from livesplit.ws_server import LiveSplitWebSocketServer

_MANUAL_NAV_COOLDOWN_SEC = 0.75


class LiveSplitTimerSync:
    """Send timer commands when LiveSplit One is connected to our WebSocket server."""

    def __init__(self) -> None:
        self._server: Optional[LiveSplitWebSocketServer] = None
        self._manual_nav_deadline = 0.0

    def set_server(self, server: Optional[LiveSplitWebSocketServer]) -> None:
        self._server = server

    @property
    def linked(self) -> bool:
        return self._server is not None and self._server.is_client_connected

    def send(self, command: str, **params: object) -> bool:
        if not self.linked or self._server is None:
            return False
        return self._server.send_command(command, **params)

    def after_manual_navigation(self) -> None:
        """Ignore autosplit timer commands briefly after manual skip/undo/reset."""
        self._manual_nav_deadline = time.monotonic() + _MANUAL_NAV_COOLDOWN_SEC

    def autosplit_may_send(self) -> bool:
        return time.monotonic() >= self._manual_nav_deadline
