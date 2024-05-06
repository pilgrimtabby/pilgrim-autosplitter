import time
import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from split_images import SplitDirectory
from utils import PAUSE_KEY, SPLIT_KEY

from utils import PercentType
from pynput import keyboard


class Splitter(QObject):
    match_percent_signal = pyqtSignal(str, PercentType)
    pause_signal = pyqtSignal(float, float)
    delay_signal = pyqtSignal(float)
    split_signal = pyqtSignal()


    image_dir: str
    image_list: list
    image_list_index: int
    current_loop_count: float
    
    def __init__(self):
        super().__init__()
        self.split_images = SplitDirectory()
        self.highest_match_percent = 0
        self.went_above_threshold_flag = False
        self.below_flag = False
        self.dummy_flag = False
        self.pause_flag = False
        self.keyboard = keyboard.Controller()

    def compare_frame_to_split_image(self, raw_frame: numpy.ndarray):
        comparison_frame = cv2.matchTemplate(
            raw_frame,
            self.split_images.current_image.raw_image[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=self.split_images.current_image.alpha
        )
        match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
        self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT)
        if match_percent > self.highest_match_percent:
            self.highest_match_percent = match_percent
            self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

        if match_percent > self.split_images.current_image.threshold:
            if self.below_flag:
                self.went_above_threshold_flag = True
            else:
                self.split()

        elif self.went_above_threshold_flag and match_percent < self.split_images.current_image.threshold:
            self.split()

    def split(self):
        self.highest_match_percent = 0
        if self.split_images.current_image.delay_duration + self.split_images.current_image.pause_duration > 0:
            self.match_percent_signal.emit("--.-", PercentType.CURRENT)
            self.match_percent_signal.emit("--.-", PercentType.HIGHEST)
            self.split_images.match_percent_signal.emit("--.-", PercentType.THRESHOLD)

        QTimer.singleShot(int(self.split_images.current_image.delay_duration * 1000), self.split_action)
        self.pause_signal.emit(self.split_images.current_image.delay_duration, self.split_images.current_image.pause_duration)


    def split_action(self):
        if self.pause_flag:
            # pyautogui.press(PAUSE_KEY)
            pass
        elif not self.dummy_flag:
            self.keyboard.press(keyboard.Key.space)
            self.keyboard.release(keyboard.Key.space)

        self.split_images.load_next_split()

        self.went_above_threshold_flag = False
        if "b" in self.split_images.current_image.flags:
            self.below_flag = True
        else:
            self.below_flag = False

        if "d" in self.split_images.current_image.flags:
            self.dummy_flag = True
        else:
            self.dummy_flag = False

        if "p" in self.split_images.current_image.flags:
            self.pause_flag = True
        else:
            self.pause_flag = False
