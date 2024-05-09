######################

#MULTIPROCESSING

######################

import queue
import time
import cv2
import numpy
from pynput import keyboard
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread, pyqtSlot

from utils import PercentType
import multiprocessing
from queue import Empty


def get_comparison_frame(frame: numpy.ndarray, templ, my_mask, q):
    q.put(
        cv2.matchTemplate(
            frame,
            templ,
            cv2.TM_CCORR_NORMED,
            mask=my_mask
        )
    )

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

    def compare_frame(self, frame):
        q = multiprocessing.SimpleQueue()
        annoying = multiprocessing.Process(target=get_comparison_frame, args=(frame, self.split_image.image[:,:,0:3], self.split_image.alpha, q))
        start = time.time()
        annoying.start()
        print(time.time() - start)
        try:
            comparison_frame = q.get()
        except:
            return
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






#####################

# WORKER AND POOL APPROACH (multiprocessing)

#####################
# import multiprocessing
# import cv2
# import numpy
# from pynput import keyboard
# from PyQt5.QtCore import QObject, QTimer, pyqtSignal
# import queue

# from utils import PercentType


# class Splitter(QObject):
#     suspended_status_signal = pyqtSignal(bool)
#     delaying_status_signal = pyqtSignal(bool)
#     request_next_split_image_signal = pyqtSignal()
#     match_percent_signal = pyqtSignal(str, PercentType)
#     split_action_pause_signal = pyqtSignal()
#     split_action_split_signal = pyqtSignal()
    
#     def __init__(self):
#         super().__init__()
#         self.split_image = None
#         self.video_feed_active = False
#         self.splits_active = False
#         self.suspended = False
#         self.delaying = False
#         self.pool, self.q = self.open_worker_pool()
#         self.keyboard = keyboard.Controller()

#     def set_split_image(self, image):
#         self.split_image = image
#         if self.split_image:
#             self.splits_active = True
#             self.highest_match_percent = 0
#             self.went_above_threshold_flag = False
#             self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)
#         else:
#             self.splits_active = False

#     def comparison_frame_worker(self, frame: numpy.ndarray):
#         self.q.put(
#             cv2.matchTemplate(
#                 frame,
#                 self.split_image.image[:,:,0:3],
#                 cv2.TM_CCORR_NORMED,
#                 mask=self.split_image.alpha
#             )
#         )

#     def compare_frame(self, frame: numpy.ndarray):
#         if not self.splits_active or not self.video_feed_active or self.suspended:
#             return

#         self.pool.apply_async(self.comparison_frame_worker, args=frame)
#         while not self.q.empty():
#             comparison_frame = self.q.get()
#             match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
#             self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT)
#             if match_percent > self.highest_match_percent:
#                 self.highest_match_percent = match_percent
#                 self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

#             if match_percent >= self.split_image.threshold:
#                 if self.split_image.below_flag:
#                     self.went_above_threshold_flag = True
#                 else:
#                     self.reset_worker_pool()
#                     self.pool, self.q = self.open_worker_pool()
#                     self.split()

#             elif self.went_above_threshold_flag:
#                 self.reset_worker_pool()
#                 self.pool, self.q = self.open_worker_pool()
#                 self.split()


#     def split(self):
#         total_down_time = self.split_image.delay_duration + self.split_image.pause_duration
#         if total_down_time > 0:
#             self.set_suspended_status(True)
#             if self.split_image.delay_duration > 0:
#                 self.set_delay_status(True)
#             QTimer.singleShot(int(self.split_image.delay_duration * 1000), self.split_action)
#             QTimer.singleShot(int(total_down_time * 1000), lambda: self.set_suspended_status(False))
#         else:
#             self.split_action()

#     def split_action(self):
#         if self.split_image.pause_flag:
#             self.split_action_pause_signal.emit()
#         elif not self.split_image.dummy_flag:
#             self.split_action_split_signal.emit()
#             self.keyboard.press(keyboard.Key.space)

#         self.set_delay_status(False)
#         self.request_next_split_image_signal.emit()

#     def set_video_feed_active_status(self, status: bool):
#         if self.video_feed_active != status:
#             self.highest_match_percent = 0
#             self.video_feed_active = status

#     def set_suspended_status(self, status: bool):
#         if self.suspended != status:
#             self.highest_match_percent = 0
#             self.suspended = status
#             self.suspended_status_signal.emit(self.suspended)

#     def set_delay_status(self, status: bool):
#         if self.delaying != status:
#             self.delaying = status
#             self.delaying_status_signal.emit(self.delaying)

#     def open_worker_pool(self):
#         POOLSIZE = multiprocessing.cpu_count()
#         pool = multiprocessing.Pool(POOLSIZE)
#         q = queue.Queue()
#         return pool, q
    
#     def reset_worker_pool(self):
#         try:
#             while True:
#                 self.q.get_nowait()
#         except self.q.Empty:
#             pass
#         self.pool.close()
#         self.pool.terminate()
#         self.pool.join()
