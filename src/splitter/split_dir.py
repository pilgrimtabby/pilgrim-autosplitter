import glob
import pathlib
import re

import cv2
import numpy
from PyQt5.QtGui import QImage, QPixmap

import settings


class SplitDir:
    MAX_LOOPS_AND_PAUSE = 99999
    MAX_THRESHOLD = 1

    def __init__(self):
        self.dir_path = settings.get_str("LAST_IMAGE_DIR")
        self.list = self.get_split_images()
        if len(self.list) > 0:
            self.current_image_index = 0
            self.current_loop = 0
        else:
            self.current_image_index = None
            self.current_loop = None

    def get_split_images(self):
        split_images = []
        if not pathlib.Path(self.dir_path).is_dir():
            return split_images
        
        image_paths = (
            glob.glob(f"{self.dir_path}/*.png")
            + glob.glob(f"{self.dir_path}/*.jpg")
            + glob.glob(f"{self.dir_path}/*.jpeg")
        )
        for image_path in sorted(image_paths):
            split_images += [self._SplitImage(image_path)]

        return split_images
    
    def next_split_image(self):
        if len(self.list) == 0:
            raise Exception("Error: no split image list initialized")

        current_image = self.list[self.current_image_index]

        if self.current_loop == current_image.loops:
            if self.current_image_index < len(self.list) - 1:
                self.current_image_index += 1
            else:
                self.current_image_index = 0
            self.current_loop = 0

        else:
            self.current_loop += 1

        return self.current_image_index
        
    def previous_split_image(self):
        if len(self.list) == 0:
            raise Exception("Error: no split image list initialized")

        if self.current_loop == 0:
            if self.current_image_index == 0:
                self.current_image_index = len(self.list) - 1
            else:
                self.current_image_index -= 1
            
            current_image = self.list[self.current_image_index]
            self.current_loop = current_image.loops
            
        else:
            self.current_loop -= 1

        return self.current_image_index
        
    def reset_split_images(self):
        if len(self.list) == 0:
            raise Exception("Error: no split image list initialized")
        
        new_list = self.get_split_images()
        if len(new_list) != 0:  # Keep the old list if the directory is missing now
            self.list = new_list

        self.current_image_index = 0
        self.current_loop = 0

    def set_default_threshold(self):
        for image in self.list:
            if image.threshold_is_default:
                image.threshold = settings.get_float("DEFAULT_THRESHOLD")

    def set_default_delay(self):
        for image in self.list:
            if image.delay_is_default:
                image.delay_duration = settings.get_float("DEFAULT_DELAY")

    def set_default_pause(self):
        for image in self.list:
            if image.pause_is_default:
                image.pause_duration = settings.get_float("DEFAULT_PAUSE")

    def resize_images(self):
        for image in self.list:
            image.image = image.get_image()
            image.alpha = image.get_alpha()
            image.pixmap = image.get_pixmap()

    class _SplitImage:
        COMPARISON_FRAME_WIDTH = settings.get_int("COMPARISON_FRAME_WIDTH")
        COMPARISON_FRAME_HEIGHT = settings.get_int("COMPARISON_FRAME_HEIGHT")

        def __init__(self, image_path) -> None:
            self.path = image_path
            self.name = pathlib.Path(image_path).stem
            self.image = self.get_image()
            self.alpha = self.get_alpha()
            self.pixmap = self.get_pixmap()
            self.below_flag, self.dummy_flag, self.pause_flag = self.get_flags_from_name()
            self.delay_duration, self.delay_is_default = self.get_delay_from_name()
            self.pause_duration, self.pause_is_default = self.get_pause_from_name()
            self.threshold, self.threshold_is_default = self.get_threshold_from_name()
            self.loops, self.loops_is_default = self.get_loops_from_name()

        def get_image(self) -> numpy.ndarray:
            image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(image, (self.COMPARISON_FRAME_WIDTH, self.COMPARISON_FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
            # Add alpha to images if not already present (ie if image has only 3 channels, not 4)
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            return image
        
        def get_alpha(self):
            alpha = self.image[:, :, 3]
            return cv2.merge([alpha, alpha, alpha])
        
        def get_pixmap(self):
            image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(image, (settings.get_int("FRAME_WIDTH"), settings.get_int("FRAME_HEIGHT")), interpolation=cv2.INTER_NEAREST)
            # Add alpha to images if not already present (ie if image has only 3 channels, not 4)
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            frame_qimage = QImage(image, image.shape[1], image.shape[0], QImage.Format_RGBA8888).rgbSwapped()  # Make sure alpha channel is included, swap red and blue values
            return QPixmap.fromImage(frame_qimage)

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
            if delay is None or not str(delay[1]).replace(".", "", 1).isdigit():  # Only recognizes non-negative ints and floats, which is what we want
                return settings.get_float("DEFAULT_DELAY"), True
            return min(float(delay[1]), SplitDir.MAX_LOOPS_AND_PAUSE), False

        def get_pause_from_name(self):
            pause = re.search(r"_\[(.+?)\]", self.name)
            if pause is None or not str(pause[1]).replace(".", "", 1).isdigit():
                return settings.get_float("DEFAULT_PAUSE"), True
            return min(float(pause[1]), SplitDir.MAX_LOOPS_AND_PAUSE), False

        def get_threshold_from_name(self):
            threshold = re.search(r"_\((.+?)\)", self.name)
            if threshold is None or not str(threshold[1]).replace(".", "", 1).isdigit():
                return settings.get_float("DEFAULT_THRESHOLD"), True
            return min(float(threshold[1]) / 100, SplitDir.MAX_THRESHOLD), False

        def get_loops_from_name(self):
            loops = re.search(r"_\@(.+?)\@", self.name)
            if loops is None or not loops[1].isdigit():  # Only recognizes non-negative integers, which is what we want
                return settings.get_int("DEFAULT_LOOP_COUNT"), True
            return min(int(loops[1]), SplitDir.MAX_LOOPS_AND_PAUSE), False
