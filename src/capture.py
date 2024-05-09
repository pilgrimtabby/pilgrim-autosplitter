import os
import platform
import subprocess
import time
from pathlib import Path
from threading import Thread

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from utils import settings


class Capture(QObject):
    send_to_gui_signal = pyqtSignal(QPixmap)
    send_to_splitter_signal = pyqtSignal(numpy.ndarray)
    screenshot_result_signal = pyqtSignal(object)
    video_is_active_signal = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.frame_count= 0
        self.frame_time = 0
        self.video_is_active = False
        self.streamer = Streamer(0)
        # self.streamer = Streamer("res/test-vid.mp4")

    def send_frame(self, measure_fps=False):
        frame = self.streamer.share()
        
        if measure_fps:
            if self.frame_time == 0:
                self.frame_time = time.time()
            elif time.time() - self.frame_time >= 1:
                self.frame_time = 0
                print(self.frame_count)
                self.frame_count = 0
            self.frame_count += 1

        if frame is None:
            self.set_video_active_status(False)
            self.send_to_gui_signal.emit(QPixmap())
        else:
            self.set_video_active_status(True)
            self.send_to_gui_signal.emit(self.frame_to_pixmap(frame))
            self.send_to_splitter_signal.emit(frame)
    
    def reconnect_video(self):
        self.streamer.reconnect()

    def frame_to_pixmap(self, frame: numpy.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        return QPixmap.fromImage(frame_img)
    
    def take_screenshot(self) -> bool:
        frame = self.streamer.share()
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
            self.screenshot_result_signal.emit(None)

    def set_video_active_status(self, status: bool):
        if self.video_is_active != status:
            self.video_is_active = status
            self.video_is_active_signal.emit(status)


class Streamer():
    def __init__(self, source: int) -> None:
        self.source = source
        self.buffer = 1
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer)
        self.frame = None
        self.exit = False

        self.thread = Thread(target=self.read, args=())
        self.thread.daemon = True
        self.thread.start()

    def read(self):
        while True:
            if self.exit:
                break

            if self.cap.isOpened:
                frame = self.cap.read()[1]
                if frame is None:
                    self.frame = None
                else:
                    self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
            time.sleep(1 / settings.value("DEFAULT_FPS"))

    def share(self):
        return self.frame
    
    def reconnect(self):
        self.exit = True
        self.thread.join()
        self.cap = cv2.VideoCapture(self.source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer)
        self.exit = False
    
        self.thread = Thread(target=self.read, args=())
        self.thread.daemon = True
        self.thread.start()
