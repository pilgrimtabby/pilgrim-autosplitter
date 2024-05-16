from PyQt5.QtWidgets import QApplication

from splitter.splitter import Splitter
from ui.ui_controller import UIController
from utils import settings

import faulthandler
faulthandler.enable()

class PilgrimAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])
        self.pilgrim_universal_autosplitter.setStyle("fusion")

        self.splitter = Splitter()
        if settings.value("START_WITH_VIDEO"):
            self.splitter.start()

        self.ui_controller = UIController(self.splitter)

        self.ui_controller.main_window.show()
        self.pilgrim_universal_autosplitter.exec()

if __name__ == "__main__":
    PilgrimAutosplitter()
