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

"""WebSocket server for LiveSplit One Server Connection integration."""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Callable, Optional, Any

from websockets.asyncio.server import serve

_WS_PATH = "/livesplit"
_DEFAULT_HOST = "127.0.0.1"


class LiveSplitWebSocketServer:
    """Hosts a WebSocket endpoint that LiveSplit One connects to as a client."""

    def __init__(
        self,
        port: int,
        *,
        on_client_connected: Optional[Callable[[], None]] = None,
        on_client_disconnected: Optional[Callable[[], None]] = None,
    ) -> None:
        self._port = port
        self._host = _DEFAULT_HOST
        self._on_client_connected = on_client_connected
        self._on_client_disconnected = on_client_disconnected
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server = None
        self._client: Any = None
        self._running = False
        self._start_error: Optional[str] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        """Return the WebSocket URL to paste into LiveSplit One."""
        return f"ws://{self._host}:{self._port}{_WS_PATH}"

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_client_connected(self) -> bool:
        with self._lock:
            return self._client is not None

    @property
    def start_error(self) -> Optional[str]:
        return self._start_error

    def start(self) -> bool:
        """Start listening on a background thread. Returns False if already running."""
        if self._running:
            return True
        self._start_error = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="lso-ws")
        self._thread.start()
        for _ in range(100):
            if self._running:
                return True
            if self._start_error is not None:
                return False
            threading.Event().wait(0.02)
        return self._running

    def stop(self) -> None:
        """Stop the server and close any active client connection."""
        if not self._running or self._loop is None:
            with self._lock:
                self._client = None
            self._running = False
            return
        future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
        try:
            future.result(timeout=5)
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._thread = None
        self._loop = None
        self._server = None
        with self._lock:
            self._client = None
        self._running = False

    def send_command(self, command: str, **params: object) -> bool:
        """Send a LiveSplit One JSON server-protocol command to the timer.

        Command names use camelCase per livesplit-core ServerProtocol, e.g.
        splitOrStart, reset, start, split.
        """
        payload: dict[str, object] = {"command": command}
        payload.update(params)
        message = json.dumps(payload, separators=(",", ":"))
        return self._send_text(message)

    def _send_text(self, message: str) -> bool:
        with self._lock:
            client = self._client
            loop = self._loop
        if client is None or loop is None:
            return False
        future = asyncio.run_coroutine_threadsafe(client.send(message), loop)
        try:
            future.result(timeout=2)
            return True
        except Exception:
            return False

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except Exception as exc:
            self._start_error = str(exc)
        finally:
            self._running = False
            loop.close()

    async def _serve(self) -> None:
        self._stop_event = asyncio.Event()
        async with serve(
            self._connection_handler,
            self._host,
            self._port,
            ping_interval=20,
            ping_timeout=20,
        ) as server:
            self._server = server
            self._running = True
            await self._stop_event.wait()

    async def _shutdown(self) -> None:
        with self._lock:
            client = self._client
        if client is not None:
            await client.close()
        if self._stop_event is not None and not self._stop_event.is_set():
            self._stop_event.set()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _connection_handler(self, websocket: Any) -> None:
        request = getattr(websocket, "request", None)
        path = request.path if request is not None else getattr(websocket, "path", "")
        if path != _WS_PATH:
            await websocket.close(1008, "Invalid path")
            return

        with self._lock:
            if self._client is not None:
                await websocket.close(1008, "Another client is already connected")
                return
            self._client = websocket

        if self._on_client_connected is not None:
            self._on_client_connected()

        try:
            async for _message in websocket:
                # LiveSplit One may send timer events; no response required for v1.
                pass
        finally:
            with self._lock:
                if self._client is websocket:
                    self._client = None
            if self._on_client_disconnected is not None:
                self._on_client_disconnected()
