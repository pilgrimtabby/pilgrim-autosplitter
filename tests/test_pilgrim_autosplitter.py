# Copyright (c) 2024 pilgrim_tabby
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

"""Test pilgrim_autosplitter.py."""


import platform
import time
from threading import active_count, Thread

from PyQt5.QtWidgets import QApplication

from src.pilgrim_autosplitter import PilgrimAutosplitter


def test_run() -> None:
    """Make sure app opens correctly and shuts down cleanly (kills threads)."""
    def quit_app(app: QApplication) -> None:
        time.sleep(2)
        app.quit()

    pilgrim_autosplitter = PilgrimAutosplitter()

    exit_gui_thread = Thread(target=quit_app, args=(pilgrim_autosplitter.app,))
    exit_gui_thread.daemon = True
    exit_gui_thread.start()

    pilgrim_autosplitter.run()
    exit_gui_thread.join()

    # Give joined threads time to clear from active_count
    time.sleep(1)

    if platform.system() == "Darwin":
        # On MacOS, allow caffeinate thread (see ui_controller.py) to continue
        # because it won't cause a segfault and takes a long time to exit
        baseline_thread_count = 2
    else:
        baseline_thread_count = 1

    assert active_count() <= baseline_thread_count
