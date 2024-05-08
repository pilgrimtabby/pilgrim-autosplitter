import os
import platform
import subprocess
from pathlib import Path
import time

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from utils import settings


class Capture(QObject):
    send_to_gui_signal = pyqtSignal(QPixmap)
    send_to_splitter_signal = pyqtSignal(numpy.ndarray)
    cap_open_signal = pyqtSignal(bool)
    screenshot_result_signal = pyqtSignal(object)
    video_is_active_signal = pyqtSignal(bool)

    cap: cv2.VideoCapture
    most_recent_frame: numpy.ndarray

    def __init__(self) -> None:
        super().__init__()
        self.cap = None
        self.most_recent_frame = None
        self.current_split_image = None
        self.splits_loaded = False
        self.video_is_active = False
        self.count = 0
        self.time = 0

    def connect_to_video_feed(self) -> bool:
        if self.cap:
            self.cap.release()

        self.cap = cv2.VideoCapture("res/test-vid.mp4")
        # self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.video_is_active = True
            self.video_is_active_signal.emit(True)
        else:
            self.video_is_active = False
            self.video_is_active_signal.emit(False)

    def send_frame(self):
        frame = self.get_and_resize_frame(is_screenshot=False)

        # Measure FPS
        # if self.time == 0:
        #     self.time = time.time()
        # elif time.time() - self.time >= 1:
        #     self.time = 0
        #     print(self.count)
        #     self.count = 0
        # self.count += 1

        if frame is None:
            return

        self.send_to_gui_signal.emit(self.frame_to_pixmap(frame))
        self.send_to_splitter_signal.emit(frame)
    
    def frame_to_pixmap(self, frame: numpy.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        frame_pixmap = QPixmap.fromImage(frame_img)
        return frame_pixmap
    
    def get_and_resize_frame(self, is_screenshot=False) -> numpy.ndarray | None:
        frame = self.cap.read()[1]
        if frame is None:
            # self.video_is_active = False  # Don't try to reconnect
            # self.video_is_active_signal.emit(False)
            # self.send_to_gui_signal.emit(QPixmap())
            # return None

            self.connect_to_video_feed()  # Try to reconnect
            if self.video_is_active:
                self.send_to_gui_signal.emit(QPixmap())
                return None
            else:
                return self.get_and_resize_frame()
        
        if not is_screenshot and (frame == self.most_recent_frame).all():
            return None

        self.most_recent_frame = frame
        frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
        return frame

    def take_screenshot(self) -> bool:
        frame = self.get_and_resize_frame(is_screenshot=True)
        if frame is None:
            self.screenshot_result_signal.emit(None)
            return

        image_dir = settings.value('LAST_IMAGE_DIR')
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/test200000.png"
        cv2.imwrite(screenshot_path, frame)
        if Path(screenshot_path).is_file():
            if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
                if platform.system() == "Windows":
                    os.startfile(screenshot_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", screenshot_path])
                else:
                    subprocess.call(["xdg-open", screenshot_path])
            else:
                self.screenshot_result_signal.emit(screenshot_path)
        else:
            print("Not a file@")