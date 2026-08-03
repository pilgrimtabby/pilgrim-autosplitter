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

"""Throttled logging for exceptions in Qt timer slots and background threads."""

from __future__ import annotations

import sys
import time
import traceback
from typing import Dict, Tuple

_LAST_LOG: Dict[Tuple[str, str], float] = {}
_THROTTLE_SEC = 5.0


def log_slot_error(context: str, exc: BaseException) -> None:
    """Print a throttled traceback for a slot/thread error (keeps the app alive)."""
    key = (context, type(exc).__name__)
    now = time.monotonic()
    if now - _LAST_LOG.get(key, 0.0) < _THROTTLE_SEC:
        return
    _LAST_LOG[key] = now
    print(f"[Pilgrim Autosplitter] {context}: {exc}", file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
