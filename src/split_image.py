import pathlib
import re

import cv2
import numpy

from utils import settings, frame_to_pixmap

class SplitImage:
    def __init__(self, image_path) -> None:
        self.path = image_path
        self.name = pathlib.Path(image_path).stem
        self.image = self.get_and_resize_image()
        self.pixmap = frame_to_pixmap(self.image)
        self.alpha = self.get_alpha()
        self.below_flag, self.dummy_flag, self.pause_flag = self.get_flags_from_name()
        self.delay_duration, self.delay_is_default = self.get_delay_from_name()
        self.pause_duration, self.pause_is_default = self.get_pause_from_name()
        self.threshold, self.threshold_is_default = self.get_threshold_from_name()
        self.loop_count, self.loop_count_is_default = self.get_loop_count_from_name()

    def get_and_resize_image(self) -> numpy.ndarray:
        image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
        image = cv2.resize(image, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
        return image
    
    def get_alpha(self):
        # see __read_image_bytes() in AutoSplit/AutoSplitImage.py. Not sure why this works
        # Apparently adds alpha to images if not already present
        if self.image.shape[2] == 3:
            image = cv2.cvtColor(self.image, cv2.COLOR_BGR2BGRA)
        else:
            image = self.image

        alpha = image[:,:,3]
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
