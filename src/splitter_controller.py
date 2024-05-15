import threading
import time

import cv2
from splitter.frame_capture import FrameCapture
from splitter.frame_compare import FrameCompare
from splitter.split_dir import SplitDir
from utils import settings

from utils import settings



class Splitter:
    def __init__(self) -> None:
        self.frame = None
        self._cap = None
        self._capture_thread = None

        self._templ = None
        self._mask = None
        self.splits = SplitDir()
        if len(self.splits.list) > 0:
            self.current_split_image = self.splits.list[0]
            # Pass to gui
        else:
            self.current_split_image = None
        self.current_match_percent = None
        self.highest_match_percent = None
        self.threshold_match_percent = None
        self._went_above_threshold_flag = False
        self._compare_thread = None

        self.interval = 1 / settings.value("FPS")

        if settings.value("START_WITH_VIDEO"):
            show_min_view = settings.value("SHOW_MIN_VIEW")
            if (show_min_view and len(self.splits.list) > 0) or not show_min_view:
                self.start()

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
        split_image_lock = threading.Lock()
        self.current_match_percent = 0
        self.highest_match_percent = 0
        self.threshold_match_percent = self.target_frame.threshold

        start_time = time.perf_counter()
        self._compare_thread_finished = False
        while not self._compare_thread_finished and len(self.splits.list > 0):
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                start_time = current_time
                if self.frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        self.frame,
                        self._templ,
                        cv2.TM_CCORR_NORMED,
                        mask=self._mask
                    )
                    self.current_match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
                except cv2.error as e:
                    print(f"cv2 got an error: {e}")


                if self.current_match_percent > self.highest_match_percent:
                    self.highest_match_percent = self.current_match_percent

                if self.current_match_percent >= self.threshold_match_percent:
                    if current_image.below_flag:
                        self._went_above_threshold_flag = True
                    else:
                        # split
                        pass

        
        # Kill split checking if comparer goes down
        self.safe_exit_split_thread()


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





    def start(self):
        self.start_capture_thread()
        if len(self.splits.list) > 0:
            self.start_compare_thread

    def start_capture_thread(self):
        self._cap = self._get_new_capture_source()
        self._capture_thread = threading.Thread(target=self._capture, args=(self.interval,))
        self._capture_thread.daemon = True
        self._capture_thread.start()

    def start_compare_thread(self):
        self._compare_thread = threading.Thread(target=self._compare, args=(self.interval,))
        self._compare_thread.daemon = True
        self._compare_thread.start()
