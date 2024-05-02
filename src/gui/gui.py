from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from gui.controller import GUIController
from gui.main_window import GUIMainWindow
from utils import DEFAULT_FPS


class GUI(QObject):
    signal = pyqtSignal(int)
    gui: QApplication
    window: GUIMainWindow
    controller: GUIController

    def __init__(self):
        super().__init__()
        self.gui = QApplication([])
        self.window = GUIMainWindow()
        self.controller = self.window.controller

        self.signal.connect(self.update_match_percent) 
        self._update_match_percent = self.signal.emit

        print("Once through")

        timer = QTimer()
        timer.timeout.connect(self.window.set_current_frame)
        timer.start(1000 // DEFAULT_FPS)

        self.window.show()
        self.gui.exec()

    def update_match_percent(self, percent: float):
        print("Test")
