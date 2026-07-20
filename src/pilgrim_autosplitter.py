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

"""Initialize and run Pilgrim Autosplitter."""

import os
import platform
import sys
import time
import traceback

import paths


def _install_excepthook() -> None:
    """Log uncaught exceptions to stderr before the default handler runs."""
    _default = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb) -> None:
        print("[Pilgrim Autosplitter] Uncaught exception:", file=sys.stderr)
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
        _default(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


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
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtWidgets import QApplication

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        import settings
        from splitter.splitter import Splitter
        from ui.ui_controller import UIController

        _res = paths.resources_dir()

        from livesplit.desktop_stdio import strip_auto_controlled_flag

        if platform.system() == "Windows":
            # Force title bar to follow system theme
            extra_args = ["-platform", "windows:darkmode=1"]
        else:
            extra_args = []
        # Drop --auto-controlled so Qt does not treat it as a file path.
        qt_argv = strip_auto_controlled_flag(sys.argv) + extra_args
        self.app = QApplication(qt_argv)
        self.app.setStyle("fusion")
        self.app.setApplicationName("Pilgrim Autosplitter")

        # Set taskbar icons. Doesn't seem to really do anything, but it's a
        # work in progress so I'll leave it for now
        if platform.system() == "Windows":
            import ctypes

            self.app.setWindowIcon(QIcon(QPixmap(str(_res / "icon-windows.png"))))
            # Tell Windows this app is its own process so icon shows up
            app_id = "pilgrim_tabby.pilgrim_autosplitter.latest"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        # Without the absolute path, the icon only shows up when running
        # the program from the same directory /resources is in. This makes
        # it show up regardless (at least when ran from source, not build)
        else:
            self.app.setWindowIcon(QIcon(QPixmap(str(_res / "icon-macos.png"))))

        settings.set_program_vals()

        self.splitter = Splitter()
        if settings.get_bool("START_WITH_VIDEO"):
            self.splitter.restart()

        self.ui_controller = UIController(self.app, self.splitter)


def main() -> None:
    """Initialize PilgrimAutosplitter."""
    _install_excepthook()

    from livesplit.desktop_stdio import is_auto_controlled, print_handshake
    import settings

    auto_controlled = is_auto_controlled()
    if auto_controlled:
        print_handshake(settings.VERSION_NUMBER)
        print("Loading...", file=sys.stderr)
    else:
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
    pilgrim_autosplitter.app.aboutToQuit.connect(
        pilgrim_autosplitter.ui_controller.stop_livesplit_ws_server
    )
    pilgrim_autosplitter.app.aboutToQuit.connect(
        pilgrim_autosplitter.ui_controller.stop_desktop_stdio
    )
    # Wait for any singleshot QTimers started by widgets to finish.
    # Right now, this includes only the double click timer in some
    # ui_main_window widgets. If we quit while a timer is running, it
    # can cause a segfault, so we want to prevent that.
    pilgrim_autosplitter.app.aboutToQuit.connect(lambda sec=0.2: time.sleep(sec))

    if auto_controlled:
        print("Starting...", file=sys.stderr)
    else:
        print("Starting...")
    pilgrim_autosplitter.app.exec()


if __name__ == "__main__":
    main()
