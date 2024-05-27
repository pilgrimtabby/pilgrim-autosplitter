import platform
import sys

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
        self.pilgrim_autosplitter = QApplication(sys.argv)
        self.pilgrim_autosplitter.setStyle("fusion")
        self.pilgrim_autosplitter.setApplicationName("Pilgrim Autosplitter")
        self.pilgrim_autosplitter.setWindowIcon(QIcon(QPixmap("resources/icon-macos.png")))

        settings.load_defaults()

        self.splitter = Splitter()
        if settings.get_bool("START_WITH_VIDEO"):
            self.splitter.start()

        self.ui_controller = UIController(self.pilgrim_autosplitter, self.splitter)
        self.ui_controller.main_window.show()
        
        self.pilgrim_autosplitter.exec()
         

if __name__ == "__main__":
    print("Starting Pilgrim Autosplitter...")
    # if platform.system() == "Darwin":
    #     import traceback
    #     with open("/tmp/pilgrimautosplitter.log", "a") as log:
    #         try:
    #             PilgrimAutosplitter()
    #         except Exception:
    #             traceback.print_exc(file=log)

    # else:
    PilgrimAutosplitter()
