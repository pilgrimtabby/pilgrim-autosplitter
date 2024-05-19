import platform

if platform.system() == "Darwin":
    import os
    os.system("clear")
    print(
        "Welcome to Pilgrim Autosplitter!\n"
        "The application is loading.\n"
        "Don't close this window--the application will shut down!\n"
        "You may minimize this window at any time.\n"
    )
print("Importing packages...")

import faulthandler

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication

import settings
from splitter.splitter import Splitter
from ui.ui_controller import UIController

faulthandler.enable()
print("Setting everything up...")


class PilgrimAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])
        self.pilgrim_universal_autosplitter.setStyle("fusion")

        if platform.system() == "Windows":
            self.pilgrim_universal_autosplitter.setWindowIcon(QIcon(QPixmap("resources/icon-macos.png")))
        else:
            self.pilgrim_universal_autosplitter.setWindowIcon(QIcon(QPixmap("resources/icon-macos.png")))

        settings.load_defaults()

        self.splitter = Splitter()
        if settings.get_bool("START_WITH_VIDEO"):
            self.splitter.start()

        self.ui_controller = UIController(self.splitter)
        self.ui_controller.main_window.show()
        
        self.pilgrim_universal_autosplitter.exec()
        

if __name__ == "__main__":
    print("Starting Pilgrim Autosplitter...")
    PilgrimAutosplitter()
