import os
import platform
import subprocess
from pathlib import Path

import cv2
import numpy

from utils import (FRAME_HEIGHT, FRAME_WIDTH, LAST_IMAGE_DIR,
                   OPEN_SCREENSHOT_ON_CAPTURE)


class Capture:
    cap: cv2.VideoCapture
    most_recent_frame: numpy.ndarray

    def __init__(self) -> None:
        self.__set_capture()
        self.most_recent_frame = None

    def __set_capture(self) -> bool:
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def restart_capture(self) -> bool:
        self.cap.release()
        return self.__set_capture()

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
        if (frame == self.most_recent_frame).all():
            return None
        
        self.most_recent_frame = frame
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return frame
