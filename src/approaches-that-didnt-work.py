
################

# FIRST QTHREAD ATTEMPT

################
import queue
import cv2
import numpy
from pynput import keyboard
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread, pyqtSlot

from utils import PercentType


class Splitter(QObject):
    suspended_status_signal = pyqtSignal(bool)
    delaying_status_signal = pyqtSignal(bool)
    request_next_split_image_signal = pyqtSignal()
    match_percent_signal = pyqtSignal(str, PercentType)
    split_action_pause_signal = pyqtSignal()
    split_action_split_signal = pyqtSignal()
    compare_frame_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.split_image = None
        self.video_feed_active = False
        self.splits_active = False
        self.suspended = False
        self.delaying = False
        self.splits_paused = False
        self.frame_queue = queue.SimpleQueue()
        self.keyboard = keyboard.Controller()

    def set_split_image(self, image):
        self.split_image = image
        if self.split_image:
            self.splits_active = True
            self.highest_match_percent = 0
            self.went_above_threshold_flag = False
            self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)
        else:
            self.splits_active = False

    def get_comparison_frame(self, frame: numpy.ndarray):
        self.worker = ComparisonFrameWorker(frame, self.split_image.image[:,:,0:3], self.split_image.alpha)
        self.thread = QThread(self)

        self.worker.frame_generated_signal.connect(self.put_on_queue)
        self.worker.moveToThread(self.thread)

        self.worker.finished_signal.connect(self.thread.quit)
        self.thread.started.connect(self.worker.get_comparison_frame)
        self.thread.start()

    def put_on_queue(self, frame):
        self.frame_queue.put(frame)

    def compare_frame(self):
        if self.frame_queue.empty():
            return
        comparison_frame = self.frame_queue.get_nowait()
        match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
        self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT)
        if match_percent > self.highest_match_percent:
            self.highest_match_percent = match_percent
            self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

        if match_percent >= self.split_image.threshold:
            if self.split_image.below_flag:
                self.went_above_threshold_flag = True
            else:
                if not self.splits_paused:
                    self.split()
                    self.splits_paused = True

        elif self.went_above_threshold_flag:
            self.split()

    def split(self):
        total_down_time = self.split_image.delay_duration + self.split_image.pause_duration
        if total_down_time > 0:
            self.set_suspended_status(True)
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
            self.split_action_split_signal.emit()
            self.keyboard.press(keyboard.Key.space)

        self.set_delay_status(False)
        self.request_next_split_image_signal.emit()

    def set_video_feed_active_status(self, status: bool):
        if self.video_feed_active != status:
            self.highest_match_percent = 0
            self.video_feed_active = status

    def set_suspended_status(self, status: bool):
        if self.suspended != status:
            self.highest_match_percent = 0
            self.suspended = status
            self.suspended_status_signal.emit(self.suspended)
            self.splits_paused = status

    def set_delay_status(self, status: bool):
        if self.delaying != status:
            self.delaying = status
            self.delaying_status_signal.emit(self.delaying)

    def reset_queue(self):
        try:
            while True:
                self.comparison_frame_queue.get_nowait()
        except self.comparison_frame_queue.Empty:
            pass


class ComparisonFrameWorker(QObject):
    frame_generated_signal = pyqtSignal(numpy.ndarray)
    finished_signal = pyqtSignal()
    started = pyqtSignal()

    def __init__(self, frame: numpy.ndarray, templ: numpy.ndarray, mask: numpy.ndarray) -> None:
        super().__init__()
        self.frame = frame
        self.templ = templ
        self.mask = mask
        self.started.emit()

    @pyqtSlot()
    def get_comparison_frame(self):
        self.frame_generated_signal.emit(
            cv2.matchTemplate(
                self.frame,
                self.templ,
                cv2.TM_CCORR_NORMED,
                mask=self.mask
            )
        )
        self.finished_signal.emit()
