#### OLD GUI_MAIN_WINDOW



# https://stackoverflow.com/questions/57076105/how-to-display-a-cv2-video-inside-a-python-gui

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAction, QFrame, QGridLayout,
                             QLabel, QMainWindow, QMenu, QMenuBar,
                             QPushButton, QWidget)



class GUIMainWindow(QMainWindow):
    match_percent_signal: pyqtSignal

    def __init__(self):
        super().__init__()

        match_percent_signal = pyqtSignal()

        menuBar = QMenuBar(None)  # Set up
        self.setWindowTitle("Universal Auto Splitter")

        # Setting up widgets
        self.screenshot_button = QPushButton("Screenshot")
        self.screenshot_button.setFixedSize(QSize(100, 32))

        self.reset_button = QPushButton("Reset splits")
        self.reset_button.setFixedSize(QSize(100, 32))

        self.reload_player_button = QPushButton("Reload player")
        self.reload_player_button.setFixedSize(QSize(110, 32))

        self.video_label = QLabel("Input video: ")

        self.video_feed = QLabel("No camera detected")
        self.set_current_frame()
        self.video_feed.setFrameStyle(QFrame.Box)
        self.video_feed.setLineWidth(1)
        
        self.match_percent = QLabel("Match %: ")

        self.template_label = QLabel("Current split image:")

        self.template_src = QPixmap("res/test100.png")
        self.template = QLabel()
        self.template.setPixmap(self.template_src)
        self.template.setFrameStyle(QFrame.Box)
        self.template.setLineWidth(1)

        self.split_counter = QLabel("Split x of y")

        # Connect buttons to methods
        self.screenshot_button.clicked.connect(self.controller.take_screenshot)
        self.reset_button.clicked.connect(self.controller.reset_splits)
        self.reload_player_button.clicked.connect(self.controller.restart_capture)

        # Set up layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(30, 10, 30, 20)

        self.layout.addWidget(self.video_label, 1, 1, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_feed, 2, 1, 4, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.match_percent, 6, 1, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.template_label, 1, 4, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.template, 2, 4, 4, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.screenshot_button, 8, 1, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.reset_button, 8, 5, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.reload_player_button, 8, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.split_counter, 6, 4, 1, 2, alignment=Qt.AlignHCenter)
        
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def contextMenuEvent(self, e):
        context = QMenu(self)

        # Define actions
        settings_action = QAction("Settings", self)
        reset_splits_action = QAction("Reset splits", self)
        select_folder_action = QAction("Select split image folder", self)

        # Connect actions to controller
        settings_action.triggered.connect(self.controller.open_settings)
        reset_splits_action.triggered.connect(self.controller.reset_splits)
        select_folder_action.triggered.connect(self.controller.select_templates_folder)

        # Add actions to context menu
        context.addAction(settings_action)
        context.addAction(reset_splits_action)
        context.addAction(select_folder_action)
        context.exec(e.globalPos())


if __name__ == "__main__":
    pass
