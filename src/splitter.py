import time
from threading import Thread

import cv2
import numpy
from pynput import keyboard
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from utils import PercentType, settings


class Splitter(QObject):
    suspended_status_signal = pyqtSignal(bool, float, float)
    delaying_status_signal = pyqtSignal(bool)
    request_next_split_image_signal = pyqtSignal()
    match_percent_signal = pyqtSignal(str, PercentType)
    split_action_pause_signal = pyqtSignal()
    split_action_split_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.split_image = None
        self.video_feed_active = False
        self.splits_active = False
        self.suspended = False
        self.delaying = False
        self.split_matcher = None
        self.keyboard = keyboard.Controller()

    def set_split_image(self, image):
        self.split_image = image
        if self.split_image:
            self.splits_active = True
            self.highest_match_percent = 0
            self.went_above_threshold_flag = False
            self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)

            templ = self.split_image.image[:,:,0:3]
            mask = self.split_image.alpha
            if self.split_matcher:
                self.split_matcher.exit_thread()
            self.split_matcher = SplitMatcher(templ, mask)
        else:
            self.splits_active = False

    def compare_frame(self, frame: numpy.ndarray):
        if not self.splits_active or not self.video_feed_active or self.suspended:
            return

        self.split_matcher.set_frame(frame)
        match_percent = self.split_matcher.get_match_percent()
        if match_percent is None:
            return

        self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT) ## It's returning the same value every frame -- why?
        if match_percent > self.highest_match_percent:
            self.highest_match_percent = match_percent
            self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

        if match_percent >= self.split_image.threshold:
            if self.split_image.below_flag:
                self.went_above_threshold_flag = True
            else:
                self.split_matcher.exit_thread()
                self.split()

        elif self.went_above_threshold_flag:
            self.split_matcher.exit_thread()
            self.split()

    def split(self):
        total_down_time = self.split_image.delay_duration + self.split_image.pause_duration
        if total_down_time > 0:
            self.set_suspended_status(True, self.split_image.delay_duration, self.split_image.pause_duration)
            if self.split_image.delay_duration > 0:
                self.set_delay_status(True)
            QTimer.singleShot(int(self.split_image.delay_duration * 1000), self.split_action)
            QTimer.singleShot(int(total_down_time * 1000), lambda: self.set_suspended_status(False))
        else:
            self.split_action()

    def split_action(self):
        if self.split_image.pause_flag:
            self.split_action_pause_signal.emit()
        elif not self.split_image.dummy_flag:
            self.keyboard.press(keyboard.Key.space)

        self.set_delay_status(False)
        self.request_next_split_image_signal.emit()

    def set_video_feed_active_status(self, status: bool):
        if self.video_feed_active != status:
            self.highest_match_percent = 0
            self.video_feed_active = status

    def set_suspended_status(self, status: bool, delay_duration=0.0, pause_duration=0.0):
        if self.suspended != status:
            self.highest_match_percent = 0
            self.suspended = status
            self.suspended_status_signal.emit(self.suspended, delay_duration, pause_duration)

    def set_delay_status(self, status: bool):
        if self.delaying != status:
            self.delaying = status
            self.delaying_status_signal.emit(self.delaying)

    def kill_split_matcher(self):
        if self.split_matcher is not None:
            self.split_matcher.exit_thread()
    
    def restart_split_matcher(self):
        if self.split_matcher is not None:
            self.split_matcher.restart_thread()

    def reset_all_match_percents(self):
        self.highest_match_percent = 0
        self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)

class SplitMatcher:
    def __init__(self, templ, mask) -> None:
        self.frame = None
        self.templ = templ
        self.mask = mask
        self.match_percent = None
        self.exit = False
        
        self.thread = Thread(target=self.compare, args=(1 / settings.value("FPS"),))
        self.thread.daemon = True
        self.thread.start()

    def compare(self, interval):
        while not self.exit:
            if self.frame is None:
                continue
            try:
                comparison_frame = cv2.matchTemplate(
                    self.frame,
                    self.templ,
                    cv2.TM_CCORR_NORMED,
                    mask=self.mask
                )
                self.match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
            except cv2.error:
                pass
            time.sleep(interval)

    def set_frame(self, frame):
        self.frame = frame

    def get_match_percent(self):
        return self.match_percent

    def restart_thread(self):
        if self.thread.is_alive():
            self.exit_thread()

        self.thread = Thread(target=self.compare, args=(1 / settings.value("FPS"),))
        self.thread.daemon = True
        self.thread.start()

    def exit_thread(self):
        self.exit = True
        self.thread.join()
        self.exit = False
