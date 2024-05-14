import os
import platform
import subprocess
import time
from pathlib import Path
from threading import Thread

import cv2

from utils import settings


class Capture():
    def __init__(self) -> None:
        self.source_index = settings.value("LAST_CAPTURE_SOURCE_INDEX")
        self.frame = None
        if settings.value("START_WITH_VIDEO"):
            self.start_capture()
        else:
            self.frame_grabber = None
    
    def start_capture(self):
        if self.frame_grabber is not None:
            self.frame_grabber.safe_exit()
        new_cap = self.get_new_capture()
        if new_cap is not None:
            self.frame_grabber = self._FrameGrabber(new_cap)
    
    def get_new_capture(self):
        cap = cv2.VideoCapture(self.source_index)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if cap.isOpened():
            return cap
        else:
            return None

    def get_frame(self):
        if self.frame_grabber.cap.isOpened():
            self.frame = self.frame_grabber.get_frame()            
        else:
            self.frame = None
            self.frame_grabber.safe_exit()

    def stop_capture(self):
        if self.frame_grabber is not None:
            self.frame_grabber.safe_exit()
    
    def start_capture_from_next_source(self):
        self.source_index = self.next_valid_source_index()
        settings.setValue("LAST_CAPTURE_SOURCE_INDEX", self.source_index)
        self.start_capture()

    def next_valid_source_index(self):
        test_source = self.source_index + 1
        tries = 0
        while tries < 3:
            test_cap = cv2.VideoCapture(test_source)
            if test_cap.isOpened():
                return test_source
            else:
                test_source += 1
                tries += 1
        return 0
    
    def take_screenshot(self) -> bool:
        if self.frame is None:
            self.screenshot_result_signal.emit(None)  ## Fix this
            return

        image_dir = settings.value("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/{self.get_unique_number(image_dir)}_screenshot.png"
        cv2.imwrite(screenshot_path, self.frame)
        if Path(screenshot_path).is_file():
            if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
                if platform.system() == "Windows":
                    os.startfile(screenshot_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", screenshot_path])
                else:
                    subprocess.call(["xdg-open", screenshot_path])
            else:
                self.screenshot_result_signal.emit(screenshot_path)  # Fix this
        else:
            self.screenshot_result_signal.emit(None)  ## Fix this

    def get_unique_number(self, dir: str):
        file_int = 1
        while True:
            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            if Path(f"{dir}/{file_number}_screenshot.png").is_file():
                file_int += 1
            else:
                return file_number

    class _FrameGrabber:   ### make this more precise with time.whatever
        def __init__(self, cap) -> None:    
            self.cap = cap
            self.frame = None  # In case other thread calls _grab_frame too soon

            self.thread = Thread(target=self._grab_frame, args=(1 / settings.value("FPS"),))
            self.thread.daemon = True
            self.thread.start()

        def _grab_frame(self, interval):
            while self.cap.isOpened:
                frame = self.cap.read()[1]
                if frame is None:   # Something happened to the video feed, kill the thread
                    self.cap.release()
                self.frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
                time.sleep(interval)

        def get_frame(self):
            return self.frame

        def safe_exit(self):
            if self.thread.is_alive():
                self.cap.release()
                self.thread.join()
