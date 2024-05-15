import os
import platform
import subprocess
import time
from pathlib import Path
from threading import Thread

import cv2

from utils import settings


class FrameCapture:
    def __init__(self) -> None:
        self.frame = None
    #     self.cap = self._get_new_capture_source()
    #     self._capture_thread = Thread(target=self._capture, args=(1 / settings.value("FPS"),))
    #     self._capture_thread.daemon = True
    #     self._capture_thread.start()

    # def _get_new_capture_source(self):
    #     cap = cv2.VideoCapture(settings.value("LAST_CAPTURE_SOURCE_INDEX"))
    #     cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    #     return cap
    
    # def _capture(self, interval):
    #     start_time = time.perf_counter()
    #     while self.cap.isOpened():
    #         current_time = time.perf_counter()
    #         if current_time - start_time >= interval:
    #             start_time = current_time
    #             frame = self.cap.read()[1]
    #             if frame is None:   # Something happened to the video feed, kill the thread
    #                 self.frame = None
    #                 self.cap.release()
    #             else:
    #                 self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)

    # def safe_exit_capture_thread(self):
    #     if self._capture_thread.is_alive():
    #         self.cap.release()
    #         self._capture_thread.join()

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
    
    def take_screenshot(self) -> bool:
        if self.frame is None:
            return None

        image_dir = settings.value("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/{self._get_unique_filename_number(image_dir)}_screenshot.png"
        cv2.imwrite(screenshot_path, self.frame)

        if Path(screenshot_path).is_file():
            if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._open_file(screenshot_path)
            return screenshot_path
        return None
    
    def _get_unique_filename_number(self, dir: str):
        file_int = 1
        while True:
            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            if Path(f"{dir}/{file_number}_screenshot.png").is_file():
                file_int += 1
            else:
                return file_number

    def _open_file(path: str):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
