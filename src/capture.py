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

from utils import settings, frame_to_pixmap


class Capture(QObject):
    send_to_gui_signal = pyqtSignal(object)
    send_to_splitter_signal = pyqtSignal(numpy.ndarray)
    screenshot_result_signal = pyqtSignal(object)
    video_is_active_signal = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.frame_count= 0
        self.frame_time = 0
        self.source_index = settings.value("LAST_CAPTURE_SOURCE_INDEX")
        self.video_is_active = False
        self.streamer = Streamer(self.source_index)
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
            self.send_to_gui_signal.emit(None)
        else:
            self.set_video_active_status(True)
            self.send_to_gui_signal.emit(frame_to_pixmap(frame))
            self.send_to_splitter_signal.emit(frame)
    
    # Kill Streamer thread and create new Streamer object
    def reconnect_video(self):
        self.streamer.exit_thread()
        self.streamer = Streamer(self.source_index)

    # Kill streamer thread then start new thread in same streamer instance
    def kill_streamer(self):
        if self.streamer is not None:
            self.streamer.exit_thread()
    
    # Restart streamer thread
    def restart_streamer(self):
        if self.streamer is not None:
            self.streamer.restart_thread()

    def get_next_source(self):
        self.source_index = self.next_valid_source_index()
        settings.setValue("LAST_CAPTURE_SOURCE_INDEX", self.source_index)
        self.reconnect_video()

    def next_valid_source_index(self):
        test_source = self.source_index + 1
        tries = 0
        while tries < 3:
            test_cap = cv2.VideoCapture(test_source)
            if test_cap.isOpened():
                return test_source
            else:
                test_source += 1
                tries += 1
        
        return 0
    
    def take_screenshot(self) -> bool:
        frame = self.streamer.share()
        if frame is None:
            self.screenshot_result_signal.emit(None)
            return

        image_dir = settings.value("LAST_IMAGE_DIR")
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
    def __init__(self, source_index: int) -> None:
        self.source_index = source_index
        self.buffer = 1
        self.cap = cv2.VideoCapture(source_index)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer)
        self.frame = None
        self.exit = False

        self.thread = Thread(target=self.read, args=(1 / settings.value("FPS"),))
        self.thread.daemon = True
        self.thread.start()

    def read(self, interval):
        while not self.exit:
            if self.cap.isOpened:
                frame = self.cap.read()[1]
                if frame is None:
                    self.frame = None
                else:
                    self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
            time.sleep(interval)

    def share(self):
        return self.frame

    def restart_thread(self):
        if self.thread.is_alive():
            self.exit_thread()
            
        self.thread = Thread(target=self.read, args=(1 / settings.value("FPS"),))
        self.thread.daemon = True
        self.thread.start()

    def exit_thread(self):
        self.exit = True
        self.thread.join()
        self.exit = False
