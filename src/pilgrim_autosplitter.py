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


import platform
import sys

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication

import settings
from splitter.splitter import Splitter
from ui.ui_controller import UIController

 
class PilgrimAutosplitter:
    """Initialize and run Pilgrim Autosplitter.

    Attributes:
        pilgrim_autosplitter (QApplication): The application container that allows QObjects, including the UI, to be initialized.
        splitter (Splitter): Backend for capturing and comparing images to video.
        ui_controller (UIController): Backend for updating the UI and handling user input.
    """
    def __init__(self) -> None:
        """Create an application, a splitter, and a UI, then run the application.
        """
        self.pilgrim_autosplitter = QApplication(sys.argv)
        self.pilgrim_autosplitter.setStyle("fusion")
        self.pilgrim_autosplitter.setApplicationName("Pilgrim Autosplitter")
        self.pilgrim_autosplitter.setWindowIcon(QIcon(QPixmap("resources/icon-macos.png")))

        settings.load_defaults()

        self.splitter = Splitter()
        if settings.get_bool("START_WITH_VIDEO"):
            self.splitter.start()

        self.ui_controller = UIController(self.pilgrim_autosplitter, self.splitter)

        self.pilgrim_autosplitter.exec()
         

def main() -> None:
    """Initialize PilgrimAutosplitter (with logging if not on Windows).
    """
    if platform.system() != "Windows":
        import traceback
        with open("/tmp/pilgrimautosplitter.log", "a") as log:
            try:
                PilgrimAutosplitter()
            except Exception:
                traceback.print_exc(file=log)

    else:
        PilgrimAutosplitter()


if __name__ == "__main__":
    main()
