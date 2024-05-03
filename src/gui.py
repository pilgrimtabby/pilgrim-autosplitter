# https://stackoverflow.com/questions/57076105/how-to-display-a-cv2-video-inside-a-python-gui


import sys
from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal, QTimer, QThreadPool
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QGridLayout,
                             QLabel, QMainWindow, QMenu, QMenuBar, QPushButton,
                             QWidget)

from capture import Capture
from utils import DEFAULT_FPS, LAST_IMAGE_DIR


class GUI(QMainWindow):
    screenshot_signal = pyqtSignal()

    threadpool: QThreadPool
    video_source: Capture
    screenshot_button: QPushButton
    reset_button: QPushButton
    reload_player_button: QPushButton
    video_label: QLabel
    video_feed: QLabel
    match_percent_label: QLabel
    split_image_label: QLabel
    split_image: QLabel
    split_counter: QLabel
    layout: QGridLayout
    container: QWidget

    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.splitter_thread = None
        self.video_source = Capture()

        menuBar = QMenuBar(None)  # Set up
        self.setWindowTitle("Universal Auto Splitter")

        # Widgets
        self.screenshot_button = QPushButton("Screenshot")
        self.screenshot_button.setFixedSize(QSize(100, 32))

        self.reset_button = QPushButton("Reset splits")
        self.reset_button.setFixedSize(QSize(100, 32))

        self.reload_player_button = QPushButton("Reload player")
        self.reload_player_button.setFixedSize(QSize(110, 32))

        self.video_label = QLabel("Input video: ")

        self.video_feed = QLabel("No camera detected")
        # self.set_current_frame()
        self.video_feed.setFrameStyle(QFrame.Box)
        self.video_feed.setLineWidth(1)
        
        self.match_percent_label = QLabel("Match %: ")

        self.split_image_label = QLabel("Current split image:")

        # self.split_image_src = QPixmap("res/test100.png")
        self.split_image = QLabel("Split image here")
        # self.split_image.setPixmap(self.split_image_src)
        self.split_image.setFrameStyle(QFrame.Box)
        self.split_image.setLineWidth(1)

        self.split_counter = QLabel("Split x of y")

        # Connect buttons to methods
        self.screenshot_button.clicked.connect(self.take_screenshot)
        self.reset_button.clicked.connect(self.reset_splits)
        self.reload_player_button.clicked.connect(self.restart_capture)

        # Set up layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(30, 10, 30, 20)

        self.layout.addWidget(self.video_label, 1, 1, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_feed, 2, 1, 4, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.match_percent_label, 6, 1, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.split_image_label, 1, 4, 1, 2, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.split_image, 2, 4, 4, 2, alignment=Qt.AlignHCenter)
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
        select_image_dir_action = QAction("Select split image folder", self)

        # Connect actions to controller
        settings_action.triggered.connect(self.open_settings)
        reset_splits_action.triggered.connect(self.reset_splits)
        select_image_dir_action.triggered.connect(self.select_image_dir)

        # Add actions to context menu
        context.addAction(settings_action)
        context.addAction(reset_splits_action)
        context.addAction(select_image_dir_action)
        context.exec(e.globalPos())

    def take_screenshot(self):
        self.screenshot_signal.emit()

    def restart_capture(self):
        self.video_source.restart_capture()

    def open_settings(self):
        print("opened settings")

    def reset_splits(self):
        print("resetted splits")

    def select_image_dir_(self):
        print("selected new folder")

    def set_video_frame(self, frame):
        self.video_feed.setPixmap(frame)

    def set_split_image(self, frame):
        print("Yay")
        self.split_image.setPixmap(frame)

    def set_match_percent(self, value):
        self.match_percent_label.setText(f"Percent match: {value}%")
