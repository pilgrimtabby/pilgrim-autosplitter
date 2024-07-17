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

"""Initialize and run Pilgrim Autosplitter.
"""


def main():
    """Initialize PilgrimAutosplitter (with logging if not on Windows).

    This module is in an unusual format, with all the import statements behind
    main() and the class declaration inside of main(), to accomodate the time
    required to boot up the executable if this program is run after being built
    with PyInstaller. To reassure the user, I've placed print messages before
    and after the import statements, which take a very long time (sometimes as
    long as 30 seconds).
    """

    # Initial setup
    import os

    os.system("cls || clear")  # This works cross-platform

    print("Welcome to Pilgrim Autosplitter!")
    print("You can minimize this window, but DO NOT close it.\n")

    print("Importing third-party packages...")

    from PyQt5.QtGui import QIcon, QPixmap
    from PyQt5.QtWidgets import QApplication

    print("Importing built-in packages...")

    import platform
    import sys

    print("Initializing Pilgrim Autosplitter...")

    # Class definition
    class PilgrimAutosplitter:
        """Initialize and run Pilgrim Autosplitter.

        Attributes:
            pilgrim_autosplitter (QApplication): The application container that
                allows QObjects, including the UI, to be initialized.
            splitter (Splitter): Backend for capturing and comparing images to
                video.
            ui_controller (UIController): Backend for updating the UI and handling
                user input.
        """

        def __init__(self) -> None:
            """Initialize splitter and controller to run Pilgrim Autosplitter.

            Optionally, check for a newer release version if the user has
            enabled Check for updates in the settings window.
            """
            import settings
            from splitter.splitter import Splitter
            from ui.ui_controller import UIController

            program_directory = os.path.dirname(os.path.abspath(__file__))

            self.pilgrim_autosplitter = QApplication(sys.argv)
            self.pilgrim_autosplitter.setStyle("fusion")
            self.pilgrim_autosplitter.setApplicationName("Pilgrim Autosplitter")
            # Without the absolute path, the icon only shows up when running
            # the program from the same directory /resources is in. This makes
            # it show up regardless
            if platform.system() == "Windows":
                # This doesn't work yet, but I'm leaving it in because I think
                # I'm on the right track
                self.pilgrim_autosplitter.setWindowIcon(
                    QIcon(QPixmap(f"{program_directory}/../resources/icon-windows.png"))
                )
                # Tell Windows this app is its own process so icon shows up
                import ctypes
                app_id = u"pilgrim_tabby.pilgrim_autosplitter.latest"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            else:
                self.pilgrim_autosplitter.setWindowIcon(
                    QIcon(QPixmap(f"{program_directory}/../resources/icon-macos.png"))
                )

            settings.set_defaults()

            self.splitter = Splitter()
            if settings.get_bool("START_WITH_VIDEO"):
                self.splitter.start()

            self.ui_controller = UIController(self.pilgrim_autosplitter, self.splitter)

            self.pilgrim_autosplitter.exec()

            # Prevent segmentation fault or other clumsy errors on exit
            # The threads won't persist since they're daemons, but this helps
            # make sure they stop BEFORE the main thread ends
            self.splitter.safe_exit_all_threads()

    # Open application
    print("Starting Pilgrim Autosplitter...\n")
    PilgrimAutosplitter()


if __name__ == "__main__":
    main()
