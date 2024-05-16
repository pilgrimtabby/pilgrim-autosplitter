import os
import platform
import subprocess
import threading
import time
from pathlib import Path

import cv2

from splitter.split_dir import SplitDir
from utils import frame_to_pixmap, settings


class Splitter:
    def __init__(self) -> None:
        self.interval = 1 / settings.value("FPS")  # modified by ui_controller.save_settings when fps is changed in settings menu
        self.delaying = False  # Referenced by ui_controller to set status of various ui elements
        self.suspended = False  # Referenced by ui_controller to set status of various ui elements

        # _capture_thread variables
        self._frame = None
        self.frame_pixmap = None  # Passed to UI by ui_controller._poller
        self._cap = None
        self.capture_thread = threading.Thread(target=self._capture)  # Referenced by ui_controller to check if thread is alive
        self._capture_thread_finished = False

        # _compare_thread variables
        self.splits = SplitDir()  # Referenced by ui_controller to set status of various ui elements
        self.current_match_percent = None  # Referenced by ui_controller to set match percent information
        self.highest_match_percent = None  # Referenced by ui_controller to set match percent information
        self._compare_thread = threading.Thread(target=self._compare)
        self._compare_thread_finished = False

    # Used by ui.controller in conjunction with safe_exit_all_threads
    def start(self):
        self._start_capture_thread()
        if len(self.splits.list) > 0:  # Start comparisons if there are splits loaded
            self._start_compare_thread()

    def _start_capture_thread(self):
        self._cap = self._get_new_capture_source()
        self._capture_thread_finished = False
        self.capture_thread = threading.Thread(target=self._capture)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _start_compare_thread(self):
        self._compare_thread = threading.Thread(target=self._compare)
        self._compare_thread_finished = False
        self._compare_thread.daemon = True
        self._compare_thread.start()

    def _capture(self):
        start_time = time.perf_counter()
        while not self._capture_thread_finished:
            current_time = time.perf_counter()
            if current_time - start_time >= self.interval:
                start_time = current_time
                frame = self._cap.read()[1]
                if frame is None:   # Something happened to the video feed, kill the thread
                    self._capture_thread_finished = True
                else:
                    self._frame = cv2.resize(frame, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
                    self.frame_pixmap = frame_to_pixmap(self._frame)

        self._cap.release()
        self._frame = None
        self.frame_pixmap = None
        # Kill comparer if capture goes down
        self._safe_exit_compare_thread()

    def _compare(self):
        still_going = True
        while still_going:
            still_going = self._look_for_match()
            if still_going:
                self._split()

    def _look_for_match(self):
        self.current_match_percent = 0
        self.highest_match_percent = 0

        match_found = False
        went_above_threshold_flag = False
        start_time = time.perf_counter()
        while not self._compare_thread_finished:
            current_time = time.perf_counter()
            if current_time - start_time >= self.interval:
                start_time = current_time
                current_frame = self._frame  # Prevent a None slipping through from the capture thread
                if current_frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        current_frame,
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
                        match_found = True
                        break

                elif went_above_threshold_flag:
                    match_found = True
                    break
        
        self.current_match_percent = None
        self.highest_match_percent = None
        return match_found

    def _split(self):
        print("Splitting")
        delay_duration = self.splits.list[self.splits.current_image_index].delay_duration
        if delay_duration > 0:

            self.delaying = True
            start_time = time.perf_counter()
            while time.perf_counter() - start_time < delay_duration and not self._compare_thread_finished:
                time.sleep(self.interval)
            self.delaying = False

            if self._compare_thread_finished:
                return

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
            start_time = time.perf_counter()
            while time.perf_counter() - start_time < suspended_duration and not self._compare_thread_finished:
                time.sleep(self.interval)
            self.suspended = False

            if self._compare_thread_finished:
                return

    # Exiting the capture thread also exits the compare thread.
    # Used to safely kill all threads in this class before replacing some important element.
    # Called by ui_controller.set_image_directory_path when that method creates a new split directory for this class
    # Called by ui_controller before starting the splitter
    def safe_exit_all_threads(self):
        if self._cap is not None:
            self._capture_thread_finished = True
        if self.capture_thread.is_alive():
            self.capture_thread.join()

    # Called by this._capture when its thread dies, and by toggle_suspended (pause / unpause button pressed in ui)
    def _safe_exit_compare_thread(self):
        if self._compare_thread.is_alive():
            self._compare_thread_finished = True
            self._compare_thread.join()

    # Called by self.start_capture_thread
    def _get_new_capture_source(self):
        cap = cv2.VideoCapture(settings.value("LAST_CAPTURE_SOURCE_INDEX"))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    # Called by ui controller when next source button pressed
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

    # Called by ui_controller when pause / unpause button clicked
    def toggle_suspended(self):
        if self.suspended:
            self.suspended = False
            self._safe_exit_compare_thread()
            if len(self.splits.list) > 0:
                self._start_compare_thread()
        else:
            self.suspended = True
            self._safe_exit_compare_thread()

    # Called by ui_controller when screenshot button pressed/ shortcut entered
    def take_screenshot(self) -> bool:
        if self._frame is None:
            return None

        image_dir = settings.value("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/{self._get_unique_filename_number(image_dir)}_screenshot.png"
        cv2.imwrite(screenshot_path, self._frame)

        if Path(screenshot_path).is_file():
            if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._open_file(screenshot_path)
            return screenshot_path
        return None
    
    # Called by self.take_screenshot
    def _get_unique_filename_number(self, dir: str):
        file_int = 1
        while True:
            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            if Path(f"{dir}/{file_number}_screenshot.png").is_file():
                file_int += 1
            else:
                return file_number

    # Called by self.take_screenshot
    def _open_file(path: str):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
