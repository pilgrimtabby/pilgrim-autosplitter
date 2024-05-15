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
        pass

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
