import os
import platform
import subprocess
from pathlib import Path

import cv2
import numpy
from PyQt5.QtGui import QImage, QPixmap

from split_image import SplitImage
from utils import (FRAME_HEIGHT, FRAME_WIDTH, LAST_IMAGE_DIR,
                   OPEN_SCREENSHOT_ON_CAPTURE)


class Capture:
    cap: cv2.VideoCapture

    def __init__(self) -> None:
        self.__set_capture()

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

    def __get_raw_frame(self) -> numpy.ndarray:
        frame = self.cap.read()[1]
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return frame

    def get_frame_for_comparison(self, split_image: SplitImage) -> numpy.ndarray:
        frame = self.__get_raw_frame()
        processed_frame = cv2.matchTemplate(
            frame,
            split_image.ndarray[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=split_image.alpha
        )
        return processed_frame

    def get_frame_for_video_feed(self):
        frame = self.__get_raw_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        frame_pixmap = QPixmap.fromImage(frame_img)
        return frame_pixmap
