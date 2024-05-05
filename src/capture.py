import os
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap

from utils import (DEFAULT_FPS, FRAME_HEIGHT, FRAME_WIDTH, LAST_IMAGE_DIR,
                   OPEN_SCREENSHOT_ON_CAPTURE)


class Capture(QObject):
    video_frame_signal = pyqtSignal(QPixmap)
    raw_frame_signal = pyqtSignal(numpy.ndarray)
    block_capture_signal = pyqtSignal()

    cap: cv2.VideoCapture
    most_recent_frame: numpy.ndarray

    def __init__(self) -> None:
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.most_recent_frame = None
        self.send_to_splitter = True  # when?
        self.prev_time = 0
        self.current_split_image = None

    def restart_capture(self) -> bool:
        self.cap.release()
        self.cap = cv2.VideoCapture(0)

    def take_screenshot(self) -> bool:   # There's a chance that the way I save these files might affect image matching. We'll see...
        frame = self.__get_raw_frame()
        screenshot_path = f"{LAST_IMAGE_DIR}/test100000.png"     #TODO: filename auto-generation
        cv2.imwrite(screenshot_path, frame)
        screenshot = Path(screenshot_path)
        if screenshot.is_file() and OPEN_SCREENSHOT_ON_CAPTURE:
            if platform.system() == "Windows":
                os.startfile(screenshot_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", screenshot_path])
            else:
                subprocess.call(["xdg-open", screenshot_path])

    def get_raw_frame(self) -> numpy.ndarray:
        frame = self.cap.read()[1]
        if frame is None:
            # print("Blank frame")
            return None
        if (frame == self.most_recent_frame).all():
            # print("Same as last one")
            return None
        
        self.most_recent_frame = frame
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return frame
    
    def get_frame_for_video_feed(self, frame: numpy.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        frame_pixmap = QPixmap.fromImage(frame_img)
        return frame_pixmap
    
    def output_frame(self):
        time_elapsed = time.time() - self.prev_time
        if time_elapsed > 1. / DEFAULT_FPS:
            self.prev_time = time.time()

            raw_frame = self.get_raw_frame()
            if raw_frame is None:
                return

            video_feed_frame = self.get_frame_for_video_feed(raw_frame)
            self.video_frame_signal.emit(video_feed_frame)

            if self.send_to_splitter:
                self.raw_frame_signal.emit(raw_frame)


class CaptureThread(QRunnable):
    def __init__(self, capture: Capture) -> None:
        super(CaptureThread, self).__init__()
        self.capture = capture
        self.is_paused = False

    @pyqtSlot()
    def run(self):
        while True:
            if self.is_paused:
                time.sleep(0)
            else:
                print("Hey")
                self.capture.output_frame()

    def pause(self, seconds):
        self.is_paused = True
        print("wait")
        time.sleep(seconds)
        self.is_paused = False
