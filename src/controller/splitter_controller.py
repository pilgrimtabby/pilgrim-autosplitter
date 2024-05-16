import threading
import time

import cv2
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSlot
from splitter.split_dir import SplitDir
from utils import settings, frame_to_pixmap


class Splitter:
    def __init__(self) -> None:   # Guard against none types for each of these
        self.ui_controller = None  # Passed in by pilgrim_autosplitter.py

        self.interval = 1 / settings.value("FPS")
        self.delaying = False
        self.suspended = False

        # _capture_thread variables
        self.frame = None
        self.frame_pixmap = None
        self._cap = None
        self.capture_thread = None

        # _compare_thread variables
        self.splits = SplitDir()
        self.current_match_percent = None
        self.highest_match_percent = None
        self._compare_thread = None
        self._compare_thread_finished = False

    def start(self):
        self.safe_exit_all_threads()
        self.start_capture_thread()
        if len(self.splits.list) > 0:  # Start comparisons if there are splits loaded
            self.start_compare_thread()

    def start_capture_thread(self):
        self._cap = self._get_new_capture_source()
        self.capture_thread = threading.Thread(target=self._capture, args=(self.interval,))
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def start_compare_thread(self):
        self._compare_thread = threading.Thread(target=self._compare, args=(self.interval,))
        self._compare_thread.daemon = True
        self._compare_thread.start()

    def _capture(self, interval):
        start_time = time.perf_counter()
        while self._cap.isOpened():
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                start_time = current_time
                frame = self._cap.read()[1]
                if frame is None:   # Something happened to the video feed, kill the thread
                    self._cap.release()
                else:
                    self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
                    self.frame_pixmap = frame_to_pixmap(self.frame)

        self.frame = None
        self.frame_pixmap = None
        # Kill comparer if capture goes down
        self.safe_exit_compare_thread()

    def _compare(self, interval):
        still_going = True
        while still_going:
            still_going = self._look_for_match(interval)
            if still_going:
                self._split()


    def _look_for_match(self, interval):
        self.current_match_percent = 0
        self.highest_match_percent = 0
        went_above_threshold_flag = False
        time_to_split = False

        start_time = time.perf_counter()
        self._compare_thread_finished = False   # Do i need this?
        self.current_match_percent = 0
        self.highest_match_percent = 0
        while not self._compare_thread_finished:  # Make sure to kill this once all split images are gone !!!
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                start_time = current_time
                if self.frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        self.frame,
                        self.splits.list[self.splits.current_image_index].image[:, :, :3],
                        cv2.TM_CCORR_NORMED,
                        mask=self.splits.list[self.splits.current_image_index].alpha
                    )
                    self.current_match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
                except cv2.error as e:
                    print(f"cv2 got an error: {e}")

                if self.current_match_percent > self.highest_match_percent:
                    self.highest_match_percent = self.current_match_percent

                if self.current_match_percent >= self.splits.list[self.splits.current_image_index].threshold:
                    if self.splits.list[self.splits.current_image_index].below_flag:
                        went_above_threshold_flag = True
                    else:
                        time_to_split = True
                        break

                elif went_above_threshold_flag:
                    time_to_split = True
                    break
        
        self.current_match_percent = None
        self.highest_match_percent = None
        return time_to_split

    def _split(self):
        delay_duration = self.splits.list[self.splits.current_image_index].delay_duration
        if delay_duration > 0:
            self.delaying = True
            time.sleep(delay_duration)
            self.delaying = False

        if self.splits.list[self.splits.current_image_index].pause_flag:
            # press pause key
            pass
        elif not self.splits.list[self.splits.current_image_index].dummy_flag:
            # press split key
            pass

        self.splits.current_image_index = self.splits.next_split_image()

        suspended_duration = self.splits.list[self.splits.current_image_index].pause_duration
        if suspended_duration > 0:
            self.suspended = True
            time.sleep(suspended_duration)
            self.suspended = False

    def safe_exit_all_threads(self):
        self._cap.release()
        self.capture_thread.join()
        self._compare_thread.join()

    def safe_exit_compare_thread(self):
        self._compare_thread_finished = True
        self._compare_thread.join()

    def _get_new_capture_source(self):
        cap = cv2.VideoCapture(settings.value("LAST_CAPTURE_SOURCE_INDEX"))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def next_capture_source(self):
        source = settings.value("LAST_CAPTURE_SOURCE_INDEX") + 1
        found_valid_source = False
        tries = 0
        while tries < 3:
            test_cap = cv2.VideoCapture(source)
            if test_cap.isOpened():
                found_valid_source = True
                break
            else:
                source += 1
                tries += 1
        if not found_valid_source:
            source = 0  # Give up, go back to first possible index
        settings.setValue("LAST_CAPTURE_SOURCE_INDEX", source)

    def toggle_suspended(self):
        if self.suspended:
            self.suspended = False
            self.safe_exit_compare_thread()
            self.start_compare_thread()
        else:
            self.suspended = True
            self.safe_exit_compare_thread()

    @pyqtSlot()
    def set_new_split_dir(self):
        self.splits = SplitDir()
