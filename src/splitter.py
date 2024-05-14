import glob
import pathlib
import re
import time
from threading import Thread

import cv2
import numpy
from pynput import keyboard
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QFileDialog

from utils import PercentType, frame_to_pixmap, settings


class Splitter(QObject):
    def __init__(self, capture):
        self.capture = capture
        self.split_image = None

    def set_split_image(self, image):
        self.split_image = image
        if self.split_image:
            self.splits_active = True
            self.highest_match_percent = 0
            self.went_above_threshold_flag = False
            self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)

            templ = self.split_image.image[:,:,0:3]
            mask = self.split_image.alpha
            if self.split_matcher:
                self.split_matcher.exit_thread()
            self.split_matcher = self.SplitMatcher(templ, mask)
        else:
            self.splits_active = False

    def compare_frame(self, frame: numpy.ndarray):
        if not self.splits_active or not self.video_feed_active or self.suspended:
            return

        self.split_matcher.set_frame(frame)
        match_percent = self.split_matcher.get_match_percent()
        if match_percent is None:
            return

        self.match_percent_signal.emit(str(match_percent), PercentType.CURRENT)
        if match_percent > self.highest_match_percent:
            self.highest_match_percent = match_percent
            self.match_percent_signal.emit(str(self.highest_match_percent), PercentType.HIGHEST)

        if match_percent >= self.split_image.threshold:
            if self.split_image.below_flag:
                self.went_above_threshold_flag = True
            else:
                self.split()

        elif self.went_above_threshold_flag:
            self.split()

    def split(self):
        self.split_matcher.exit_thread()
        total_down_time = self.split_image.delay_duration + self.split_image.pause_duration
        if total_down_time > 0:
            self.set_suspended_status(True, self.split_image.delay_duration, self.split_image.pause_duration)
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
            self.keyboard.press(keyboard.Key.space)

        self.set_delay_status(False)
        self.request_next_split_image_signal.emit()

    def set_video_feed_active_status(self, status: bool):
        if self.video_feed_active != status:
            self.highest_match_percent = 0
            self.video_feed_active = status

    def set_suspended_status(self, status: bool, delay_duration=0.0, pause_duration=0.0):
        if self.suspended != status:
            self.highest_match_percent = 0
            self.suspended = status
            self.suspended_status_signal.emit(self.suspended, delay_duration, pause_duration)

    def set_delay_status(self, status: bool):
        if self.delaying != status:
            self.delaying = status
            self.delaying_status_signal.emit(self.delaying)

    def kill_split_matcher(self):
        if self.split_matcher is not None:
            self.split_matcher.exit_thread()
    
    def restart_split_matcher(self):
        if self.split_matcher is not None:
            self.split_matcher.restart_thread()

    def reset_all_match_percents(self):
        self.highest_match_percent = 0
        if self.split_image is None:
            self.match_percent_signal.emit("", PercentType.CURRENT)
            self.match_percent_signal.emit("", PercentType.HIGHEST)
            self.match_percent_signal.emit("", PercentType.THRESHOLD)
        else:
            self.match_percent_signal.emit("0", PercentType.CURRENT)
            self.match_percent_signal.emit("0", PercentType.HIGHEST)
            self.match_percent_signal.emit(str(self.split_image.threshold), PercentType.THRESHOLD)

    def prepare_split_images(self, make_image_list: bool):
        if self.path is None:
            self.split_image_to_gui_signal.emit(None)
            self.split_image_to_splitter_signal.emit(None)
            self.split_dir_path_signal.emit(None)
            return

        self.split_dir_path_signal.emit(self.path)
        if make_image_list:
            self.images = []
            for image in self.get_image_paths():
                self.images += [self.SplitImage(image)]
        if self.images:
            self.load_next_split_image(first_image=True)
        else:
            self.split_image_to_gui_signal.emit(None)
            self.split_image_to_splitter_signal.emit(None)
            
    def load_next_split_image(self, first_image=False):
        if first_image:
            current_image = self.images[0]
            self.current_index = 0
            self.current_loop = 0
            self.split_name_to_gui_signal.emit(current_image.name)
            self.split_image_to_gui_signal.emit(current_image.pixmap)
            self.split_image_to_splitter_signal.emit(current_image)

        else:
            if self.current_loop >= self.images[self.current_index].loop_count:
                self.current_index += 1
                if self.current_index >= len(self.images):
                    self.current_index = 0
                current_image = self.images[self.current_index]
                self.current_loop = 0
                self.split_name_to_gui_signal.emit(current_image.name)
                self.split_image_to_gui_signal.emit(current_image.pixmap)
                self.split_image_to_splitter_signal.emit(current_image)
            else:
                current_image = self.images[self.current_index]
                self.current_loop += 1
        
        self.loop_information_signal.emit(self.current_loop, current_image.loop_count)
        if self.current_index == 0 and self.current_loop == 0:
            self.set_is_first_split(True)
        else:
            self.set_is_first_split(False)
        if self.current_index == len(self.images) - 1 and self.current_loop == current_image.loop_count:
            self.set_is_last_split(True)
        else:
            self.set_is_last_split(False)

    def get_image_paths(self):
        if not pathlib.Path(self.path).is_dir():
            return []
        paths = (
                glob.glob(f"{self.path}/*.png")
                + glob.glob(f"{self.path}/*.jpg")
                + glob.glob(f"{self.path}/*.jpeg")
        )
        return sorted(paths)
    
    def reset_split_images(self):
        self.prepare_split_images(make_image_list=True)

    def set_is_first_split(self, status: bool):
        if self.is_first_split != status:
            self.is_first_split = status
            self.first_split_signal.emit(status)

    def set_is_last_split(self, status: bool):
        if self.is_last_split != status:
            self.is_last_split = status
            self.last_split_signal.emit(status)

    def load_previous_split_image(self):
        if self.current_loop == 0:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.images) - 1
            current_image = self.images[self.current_index]
            self.current_loop = current_image.loop_count
            self.split_name_to_gui_signal.emit(current_image.name)
            self.split_image_to_gui_signal.emit(current_image.pixmap)
            self.split_image_to_splitter_signal.emit(current_image)
        else:
            current_image = self.images[self.current_index]
            self.current_loop -= 1
        
        self.loop_information_signal.emit(self.current_loop, current_image.loop_count)
        if self.current_index == 0 and self.current_loop == 0:
            self.set_is_first_split(True)
        else:
            self.set_is_first_split(False)
        if self.current_index == len(self.images) - 1 and self.current_loop == self.current_image.loop_count:
            self.set_is_last_split(True)
        else:
            self.set_is_last_split(False)

    def set_dir_path(self):
        path = QFileDialog.getExistingDirectory(None, "Select splits folder")
        if path != "" and (self.path != path or self.path is None):
            self.path = path
            self.prepare_split_images(make_image_list=True)
            settings.setValue("LAST_IMAGE_DIR", self.path)

    def recalculate_default_delay(self):
        for image in self.images:
            if image.delay_is_default:
                image.delay_duration = settings.value("DEFAULT_DELAY")

    def recalculate_default_pause(self):
        for image in self.images:
            if image.pause_is_default:
                image.pause_duration = settings.value("DEFAULT_PAUSE")

    def recalculate_default_threshold(self):
        for image in self.images:
            if image.threshold_is_default:
                image.threshold = settings.value("DEFAULT_THRESHOLD")

    def recalculate_default_loop_count(self):
        for image in self.images:
            if image.loop_count_is_default:
                image.loop_count = settings.value("DEFAULT_LOOP_COUNT")

    def resize_images(self):
        for image in self.images:
            image.image = image.get_and_resize_image()
            image.alpha = image.get_alpha()
            image.pixmap = frame_to_pixmap(image.image, is_split=True)
            self.split_image_to_splitter_signal.emit(self.images[self.current_index])
            self.split_image_to_gui_signal.emit(self.images[self.current_index].pixmap)

    class SplitMatcher:
        def __init__(self, templ, mask) -> None:
            self.frame = None
            self.templ = templ
            self.mask = mask
            self.match_percent = None
            self.exit = False
            
            self.thread = Thread(target=self.compare, args=(1 / settings.value("FPS"),))
            self.thread.daemon = True
            self.thread.start()

        def compare(self, interval):
            while not self.exit:
                if self.frame is None:
                    continue
                try:
                    comparison_frame = cv2.matchTemplate(
                        self.frame,
                        self.templ,
                        cv2.TM_CCORR_NORMED,
                        mask=self.mask
                    )
                    self.match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
                except cv2.error:
                    pass
                time.sleep(interval)

        def set_frame(self, frame):
            self.frame = frame

        def get_match_percent(self):
            return self.match_percent

        def restart_thread(self):
            if self.thread.is_alive():
                self.exit_thread()

            self.thread = Thread(target=self.compare, args=(1 / settings.value("FPS"),))
            self.thread.daemon = True
            self.thread.start()

        def exit_thread(self):
            self.exit = True
            self.thread.join()
            self.exit = False

    class SplitImage:
        def __init__(self, image_path) -> None:
            self.path = image_path
            self.name = pathlib.Path(image_path).stem
            self.image = self.get_and_resize_image()
            self.alpha = self.get_alpha()
            self.pixmap = frame_to_pixmap(self.image, is_split=True)
            self.below_flag, self.dummy_flag, self.pause_flag = self.get_flags_from_name()
            self.delay_duration, self.delay_is_default = self.get_delay_from_name()
            self.pause_duration, self.pause_is_default = self.get_pause_from_name()
            self.threshold, self.threshold_is_default = self.get_threshold_from_name()
            self.loop_count, self.loop_count_is_default = self.get_loop_count_from_name()

        def get_and_resize_image(self) -> numpy.ndarray:
            image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(image, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
            # Add alpha to images if not already present (ie if image has only 3 channels, not 4)
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            return image
        
        def get_alpha(self):
            alpha = self.image[:,:,3]
            return cv2.merge([alpha, alpha, alpha])
        
        def get_flags_from_name(self):
            flags = re.findall(r"_\{([bdp]+?)\}", self.name)
            if "d" in flags and "p" in flags:
                flags.remove("p")

            if "b" in flags:
                below_flag = True
            else:
                below_flag = False
            if "d" in flags:
                dummy_flag = True
            else:
                dummy_flag = False
            if "p" in flags:
                pause_flag = True
            else:
                pause_flag = False

            return below_flag, dummy_flag, pause_flag

        def get_delay_from_name(self):
            delay = re.search(r"_\#(.+?)\#", self.name)
            if not delay:
                return settings.value("DEFAULT_DELAY"), True
            return float(delay[1]), False

        def get_pause_from_name(self):
            pause = re.search(r"_\[(.+?)\]", self.name)
            if not pause:
                return settings.value("DEFAULT_PAUSE"), True
            return float(pause[1]), False

        def get_threshold_from_name(self):
            threshold = re.search(r"_\((.+?)\)", self.name)
            if not threshold:
                return settings.value("DEFAULT_THRESHOLD"), True
            return float(threshold[1]), False

        def get_loop_count_from_name(self):
            loop_count = re.search(r"_\@(.+?)\@", self.name)
            if not loop_count:
                return settings.value("DEFAULT_LOOP_COUNT"), True
            return int(loop_count[1]), False
