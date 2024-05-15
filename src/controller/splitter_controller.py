import copy
import threading
import time

import cv2
from splitter.split_dir import SplitDir
from utils import settings

from utils import settings



class Splitter:
    def __init__(self) -> None:
        # Splitter variables
        self.ui_controller = UIController()

        self._interval = 1 / settings.value("FPS")
        self.delaying = False
        self.suspended = False

        # _capture_thread variables
        self.frame = None
        self._cap = None
        self._capture_thread = None

        # _compare_thread variables
        self.splits = SplitDir()
        if len(self.splits.list) > 0:
            self.current_split_index = 0  # Use deepcopy if this is an issue
        else:
            self.current_split_index = None
        self.current_match_percent = None
        self.highest_match_percent = None
        self._compare_thread = None
        self._compare_thread_finished = False

    def start(self):
        self.safe_exit_capture_thread()  # This kills _compare_thread too
        self.start_capture_thread()
        if len(self.splits.list) > 0:
            self.start_compare_thread

    def start_capture_thread(self):
        self._cap = self._get_new_capture_source()
        self._capture_thread = threading.Thread(target=self._capture, args=(self._interval,))
        self._capture_thread.daemon = True
        self._capture_thread.start()

    def start_compare_thread(self):
        self._compare_thread = threading.Thread(target=self._compare, args=(self._interval,))
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
                    self.frame = None
                    self._cap.release()
                else:
                    self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
        
        # Kill comparer if capture goes down
        self.safe_exit_compare_thread()

    def _compare(self, interval):
        time_to_split = self._look_for_match(interval)
        if time_to_split:
            self._split()

    def _look_for_match(self, interval):
        self.current_match_percent = 0
        self.highest_match_percent = 0
        went_above_threshold_flag = False
        time_to_split = False

        start_time = time.perf_counter()
        self._compare_thread_finished = False   # Do i need this?
        while not self._compare_thread_finished and len(self.splits.list > 0):
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                start_time = current_time
                if self.frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        self.frame,
                        self.splits.list[self.current_split_index].image[:, :, :3],
                        cv2.TM_CCORR_NORMED,
                        mask=self.splits.list[self.current_split_index].alpha
                    )
                    self.current_match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
                except cv2.error as e:
                    print(f"cv2 got an error: {e}")

                if self.current_match_percent > self.highest_match_percent:
                    self.highest_match_percent = self.current_match_percent

                if self.current_match_percent >= self.splits.list[self.current_split_index].threshold:
                    if self.splits.list[self.current_split_index].below_flag:
                        went_above_threshold_flag = True
                    else:
                        time_to_split = True
                        break

                elif went_above_threshold_flag:
                    time_to_split = True
                    break
        
        return time_to_split

    def _split(self):
        delay_duration = self.splits.list[self.current_split_index].delay_duration
        if delay_duration > 0:
            self.delaying = True
            time.sleep(delay_duration)
            self.delaying = False

        if self.splits.list[self.current_split_index].pause_flag:
            # press pause key
            pass
        elif not self.splits.list[self.current_split_index].dummy_flag:
            # press split key
            pass

        self.current_split_index = self.splits.next_split_image()

        suspended_duration = self.splits.list[self.current_split_index].pause_duration
        if suspended_duration > 0:
            self.suspended = True
            time.sleep(suspended_duration)
            self.suspended = False


    def safe_exit_capture_thread(self):
        self._cap.release()   # Need to check if not already released first?
        self._capture_thread.join()

    def safe_exit_compare_thread(self):
        self._compare_thread_finished = True
        self._compare_thread.join()

    def _get_new_capture_source(self):
        cap = cv2.VideoCapture(settings.value("LAST_CAPTURE_SOURCE_INDEX"))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap
