import cv2
import numpy
from pynput import keyboard
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from utils import PercentType


class Splitter(QObject):
    allow_external_pausing_signal = pyqtSignal(bool)
    execute_split_signal = pyqtSignal()
    split_name_signal = pyqtSignal(str)
    match_percent_signal = pyqtSignal(object, PercentType)
    split_loop_signal = pyqtSignal(object, object)
    unpause_splitter_button_text_correction = pyqtSignal()
    split_action_pause_signal = pyqtSignal()
    split_action_split_signal = pyqtSignal()

    image_dir: str
    image_list: list
    image_list_index: int
    current_loop_count: float
    
    def __init__(self):
        super().__init__()
        self.split_image = None
        self.paused = False
        self.keyboard = keyboard.Controller()

    def set_split_image(self, image):
        self.split_image = image
        if self.split_image:
            self.highest_match_percent = 0
            self.went_above_threshold_flag = False
            self.match_percent_signal.emit(self.split_image.threshold, PercentType.THRESHOLD)
            self.split_name_signal.emit(self.split_image.name)
            if self.split_image.loop_count == 0:
                self.current_loop_count = 0
                self.split_loop_signal.emit(0, 0)
            else:
                self.current_loop_count = 1
                self.split_loop_signal.emit(1, 1)
        else:
            self.match_percent_signal.emit("--.-", PercentType.THRESHOLD)
            self.split_name_signal.emit(None)
            self.split_loop_signal.emit(None)


    def compare_frame_to_split_image(self, frame: numpy.ndarray):
        if not self.split_image or self.paused:
            return

        comparison_frame = cv2.matchTemplate(
            frame,
            self.split_image.image[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=self.split_image.alpha
        )

        match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
        self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT)
        if match_percent > self.highest_match_percent:
            self.highest_match_percent = match_percent
            self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

        if match_percent > self.split_image.threshold:
            if self.split_image.below_flag:
                self.went_above_threshold_flag = True
            else:
                self.highest_match_percent = 0
                self.split()

        elif self.went_above_threshold_flag and match_percent < self.split_image.threshold:
            self.went_above_threshold_flag = False
            self.highest_match_percent = 0
            self.split()

    def split(self):
        # Delay, then split
        if self.split_image.delay_duration > 0:
            self.set_match_percent_null()
            QTimer.singleShot(int(self.split_image.delay_duration * 1000), self.split_action)
        else:
            self.split_action()

        self.execute_split_signal.emit()  # Request next split image
        self.iterate_split_image_loop()  # Update loop info in GUI

        # Pause comparisons
        if self.split_image.pause_duration > 0:
            self.pause_splitter()
            self.allow_external_pausing_signal.emit(False)
            QTimer.singleShot(int(self.split_image.pause_duration * 1000), self.unpause_splitter)
            QTimer.singleShot(int(self.split_image.pause_duration * 1000), self.unpause_splitter_button_text_correction.emit)

    def split_action(self):
        if self.split_image.pause_flag:
            self.split_action_pause_signal.emit()
        elif not self.split_image.dummy_flag:
            self.split_action_split_signal.emit()
            self.keyboard.press(keyboard.Key.space)

    def pause_splitter(self):
        self.paused = True
        self.set_match_percent_null()

    def unpause_splitter(self):
        self.paused = False
        self.allow_external_pausing_signal.emit(True)
        self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)
        self.match_percent_signal.emit(self.split_image.threshold, PercentType.THRESHOLD)

    def iterate_split_image_loop(self):
        if self.current_loop_count > 0:
            self.current_loop_count += 1
            self.split_loop_signal.emit(self.current_loop_count, self.split_image.loop_count)

    def set_match_percent_null(self):
        self.match_percent_signal.emit("--.-", PercentType.CURRENT)
        self.match_percent_signal.emit("--.-", PercentType.HIGHEST)
        self.match_percent_signal.emit("--.-", PercentType.THRESHOLD)
