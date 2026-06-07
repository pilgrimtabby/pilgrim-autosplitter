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
