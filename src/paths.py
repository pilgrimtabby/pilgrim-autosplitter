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

"""Filesystem locations shared across the app (source tree vs PyInstaller bundle)."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True when running from a PyInstaller (or similar) frozen bundle."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def project_root() -> Path:
    """Source-tree project root (parent of ``src/``). Not used when frozen."""
    return Path(__file__).resolve().parent.parent


def resources_dir() -> Path:
    """Directory containing ``icon-macos.png``, ``demo.gif``, ``icons/``, etc."""
    if is_frozen():
        return Path(sys._MEIPASS) / "resources"
    return project_root() / "resources"


def default_saves_dir() -> Path:
    """Default profile-save folder (persistent even in frozen Windows builds).

    Frozen apps unpack under ``_MEIPASS`` (temp). Writing ``saves/`` there would
    lose profiles on quit. Prefer ``~/Documents/Pilgrim Autosplitter/saves``.
    From source, keep the repo ``saves/`` directory.
    """
    if is_frozen():
        return Path.home() / "Documents" / "Pilgrim Autosplitter" / "saves"
    return project_root() / "saves"
