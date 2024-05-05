import glob
import pathlib

import cv2
import numpy
import pyautogui
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap

from split_image import SplitImage
from utils import PAUSE_KEY, SPLIT_KEY


class Splitter(QObject):
    match_percent_signal = pyqtSignal(float)
    blank_match_percent_signal = pyqtSignal()
    send_to_splitter_signal = pyqtSignal(bool)
    pause_after_split_signal = pyqtSignal(float)
    update_split_image_signal = pyqtSignal(QPixmap)

    split_image: SplitImage
    image_dir: str
    image_list: list
    image_list_index: int
    current_loop_count: float
    
    def __init__(self, image_dir: str):
        super().__init__()
        self.split_image = None
        self.image_dir = image_dir
        self.current_loop_count = 0
        self.image_list = []
        self.below_flag = False
        self.dummy_flag = False
        self.pause_flag = False
        self.went_below_threshold_flag = False
        for image in self.get_split_image_paths():
            self.image_list += [SplitImage(image)]

    def get_split_image_paths(self):
        if not pathlib.Path(self.image_dir).is_dir():
            return []
        return (
            glob.glob(f"{self.image_dir}/*.png")
            + glob.glob(f"{self.image_dir}/*.jpg")
            + glob.glob(f"{self.image_dir}/*.jpeg")
        )
        
    def set_splits_to_initial_state(self):
        self.image_list_index = -1
        if self.image_list:
            self.go_to_next_split()
        else:
            self.blank_match_percent_signal.emit()
            self.send_to_splitter_signal.emit(False)

    def go_to_next_split(self):
        self.went_below_threshold_flag = False

        if self.current_loop_count == 0:
            self.image_list_index += 1
            if self.image_list_index == len(self.image_list):
                self.image_list_index = 0
            self.split_image = self.image_list[self.image_list_index]
            self.current_loop_count = self.split_image.loop_count
            self.update_split_image_signal.emit(self.split_image.pixmap)

            if "b" in self.split_image.flags:
                self.below_flag = True
            else:
                self.below_flag = False

            if "d" in self.split_image.flags:
                self.dummy_flag = True
            else:
                self.dummy_flag = False

            if "p" in self.split_image.flags:
                self.pause_flag = True
            else:
                self.pause_flag = False

        else:
            self.current_loop_count -= 1
            self.update_split_image_signal.emit(self.split_image.pixmap)  # In case first image has multiple loops


    def compare_frame_with_split_image(self, raw_frame: numpy.ndarray):
        comparison_frame = cv2.matchTemplate(
            raw_frame,
            self.split_image.ndarray[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=self.split_image.alpha
        )

        match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
        self.match_percent_signal.emit(match_percent)

        if match_percent > self.split_image.threshold:
            if self.below_flag:
                self.went_above_threshold_flag = True
            else:
                self.split_action()

        elif self.went_above_threshold_flag and match_percent < self.split_image.threshold:
            self.split_action()

    def split_action(self):
        if self.dummy_flag:
            self.go_to_next_split()
        else:
            self.delay_before_split_signal.emit(self.split_image.delay_duration)
            if self.pause_flag:
                pyautogui.press(PAUSE_KEY)
            else:
                pyautogui.press(SPLIT_KEY)
            self.pause_after_split_signal.emit(self.split_image.pause_duration)
