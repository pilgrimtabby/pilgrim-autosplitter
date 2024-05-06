import os
import platform
import subprocess
from pathlib import Path

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap

from utils import (FRAME_HEIGHT, FRAME_WIDTH, LAST_IMAGE_DIR,
                   OPEN_SCREENSHOT_ON_CAPTURE, TEST_VID_PATH, PercentType)


class Capture(QObject):
    video_frame_signal = pyqtSignal(QPixmap)
    raw_frame_signal = pyqtSignal(numpy.ndarray)
    cap_open_signal = pyqtSignal(bool)
    screenshot_success_signal = pyqtSignal(str)
    screenshot_error_signal = pyqtSignal()
    match_percent_signal = pyqtSignal(str, PercentType)

    cap: cv2.VideoCapture
    most_recent_frame: numpy.ndarray

    def __init__(self) -> None:
        super().__init__()
        self.cap = None
        self.most_recent_frame = None
        self.current_split_image = None
        self.splits_loaded = False
        self.comparison_is_paused = False

    def connect_to_video_feed(self) -> bool:
        if self.cap:
            self.cap.release()

        # self.cap = cv2.VideoCapture(TEST_VID_PATH)
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.cap_open_signal.emit(True)
        else:
            self.cap_open_signal.emit(False)

    def send_frame(self):
        raw_frame = self.get_raw_frame(is_screenshot=False)
        if raw_frame is None:  ## A.K.A if video is not connected:
            return
        
        self.video_frame_signal.emit(self.get_video_frame(raw_frame))  ## sending for video

        if self.splits_loaded and not self.comparison_is_paused:
            self.raw_frame_signal.emit(raw_frame)  ## sending for comparisons

    def get_raw_frame(self, is_screenshot: bool) -> numpy.ndarray:
        frame = self.cap.read()[1]
        if frame is None:
            return None
        
        if not is_screenshot and (frame == self.most_recent_frame).all():
            return None

        self.most_recent_frame = frame
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return frame
    
    def get_video_frame(self, frame: numpy.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        frame_pixmap = QPixmap.fromImage(frame_img)
        return frame_pixmap

    def take_screenshot(self) -> bool:   # There's a chance that the way I save these files might affect image matching. We'll see...
        frame = self.get_raw_frame(is_screenshot=True)
        if frame is None:
            self.screenshot_error_signal.emit()
            return

        screenshot_path = f"{LAST_IMAGE_DIR}/test100000.png"     #TODO: filename auto-generation
        cv2.imwrite(screenshot_path, frame)
        if Path(screenshot_path).is_file():
            if OPEN_SCREENSHOT_ON_CAPTURE:
                if platform.system() == "Windows":
                    os.startfile(screenshot_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", screenshot_path])
                else:
                    subprocess.call(["xdg-open", screenshot_path])
            else:
                self.screenshot_success_signal.emit(screenshot_path)

    def set_splits_loaded_status(self, status):
        self.splits_loaded = status

    def pause_comparison(self):
        self.comparison_is_paused = True
        self.match_percent_signal.emit("--.-", PercentType.CURRENT)
        self.match_percent_signal.emit("--.-", PercentType.HIGHEST)
        self.match_percent_signal.emit("--.-", PercentType.THRESHOLD)

    def unpause_comparison(self):
        self.comparison_is_paused = False

    def pause_comparison_for_set_time(self, delay, pause):
        self.pause_comparison()
        QTimer.singleShot(int((delay + pause) * 1000), self.unpause_comparison)
