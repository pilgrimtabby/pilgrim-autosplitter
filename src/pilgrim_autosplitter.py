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

"""Initialize and run Pilgrim Autosplitter."""

import os
import platform
import sys
import time


class PilgrimAutosplitter:
    """Initialize and run Pilgrim Autosplitter.

    Import statements are in __init__ because I only expect this class to be
    instantiated once per session and I want the print statements in main to
    appear before the import statements are run (they can take a long time to
    complete, especially using PyInstaller).

    Attributes:
        pilgrim_autosplitter (QApplication): The application container that
            allows QObjects, including the UI, to be initialized.
        splitter (Splitter): Backend for capturing and comparing images to
            video.
        ui_controller (UIController): Backend for updating the UI and handling
            user input.
    """

    def __init__(self) -> None:
        """Initialize splitter and controller to run Pilgrim Autosplitter."""
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtWidgets import QApplication

        import settings
        from splitter.splitter import Splitter
        from ui.ui_controller import UIController

        program_directory = os.path.dirname(os.path.abspath(__file__))

        if platform.system() == "Windows":
            # Force title bar to follow system theme
            extra_args = ["-platform", "windows:darkmode=1"]
        else:
            extra_args = []
        self.app = QApplication(sys.argv + extra_args)
        self.app.setStyle("fusion")
        self.app.setApplicationName("Pilgrim Autosplitter")

        # Set taskbar icons. Doesn't seem to really do anything, but it's a
        # work in progress so I'll leave it for now
        if platform.system() == "Windows":
            import ctypes

            self.app.setWindowIcon(
                QIcon(QPixmap(f"{program_directory}/../resources/icon-windows.png"))
            )
            # Tell Windows this app is its own process so icon shows up
            app_id = "pilgrim_tabby.pilgrim_autosplitter.latest"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        # Without the absolute path, the icon only shows up when running
        # the program from the same directory /resources is in. This makes
        # it show up regardless (at least when ran from source, not build)
        else:
            self.app.setWindowIcon(
                QIcon(QPixmap(f"{program_directory}/../resources/icon-macos.png"))
            )

        settings.set_program_vals()

        self.splitter = Splitter()
        if settings.get_bool("START_WITH_VIDEO"):
            self.splitter.start()

        self.ui_controller = UIController(self.app, self.splitter)


def main():
    """Initialize PilgrimAutosplitter."""
    os.system("cls || clear")  # Cross-platform clear screen

    print("Welcome to Pilgrim Autosplitter!")
    print("You may minimize this window, but DO NOT close it.\n")
    print("Loading Pilgrim Autosplitter (this may take a few minutes)...")

    pilgrim_autosplitter = PilgrimAutosplitter()

    # Close threads safely (these sometimes cause segfaults otherwise), even
    # though they are daemons.
    # Other app threads don't risk segfaults and are daemons, so leave them
    # alone.
    pilgrim_autosplitter.app.aboutToQuit.connect(
        pilgrim_autosplitter.splitter.safe_exit_all_threads
    )
    # Wait for any singleshot QTimers started by widgets to finish.
    # Right now, this includes only the double click timer in some
    # ui_main_window widgets. If we quit while a timer is running, it
    # can cause a segfault, so we want to prevent that.
    pilgrim_autosplitter.app.aboutToQuit.connect(lambda sec=0.2: time.sleep(sec))

    print("Starting...")
    pilgrim_autosplitter.app.exec()


if __name__ == "__main__":
    main()
