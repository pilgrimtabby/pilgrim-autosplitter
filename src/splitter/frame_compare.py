
import time
from threading import Thread

import cv2
import numpy

from utils import settings


class FrameCompare:
    def __init__(self, current_frame: numpy.ndarray, templ: numpy.ndarray, mask: numpy.ndarray):
        self.current_frame = current_frame
        self.templ = templ
        self.mask = mask

        self._compare_thread_finished = False
        self._compare_thread = Thread(target=self._compare, args=(1 / settings.value("FPS"),))
        self._compare_thread.daemon = True
        self._compare_thread.start()

    def _compare(self, interval):
        start_time = time.perf_counter()
        while not self._compare_thread_finished:
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                start_time = current_time
                if self.current_frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        self.current_frame,
                        self.templ,
                        cv2.TM_CCORR_NORMED,
                        mask=self.mask
                    )
                    self.match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
                except cv2.error:
                    pass

    def safe_exit_compare_thread(self):
        if self._compare_thread.is_alive():
            self._compare_thread_finished = True
            self._compare_thread.join()
