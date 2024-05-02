import pathlib
import re

import cv2
import numpy

from utils import (DEFAULT_DELAY, DEFAULT_LOOP_COUNT, DEFAULT_PAUSE,
                   DEFAULT_THRESHOLD, FRAME_HEIGHT, FRAME_WIDTH)


class SplitImage:
    ndarray: numpy.ndarray
    alpha: numpy.ndarray
    path: str
    name: str
    flags: list
    delay: float
    pause: float
    threshold: float
    loop_count: float

    def __init__(self, image_path) -> None:
        self.path = image_path
        self.ndarray = self.convert_image_to_ndarray(self.path)
        self.alpha = self.create_alpha(self.ndarray)
        self.name = pathlib.Path(self.path).stem
        self.flags = self.read_flags_from_filename()
        self.delay = self.read_delay_from_filename()
        self.pause = self.read_pause_from_filename()
        self.threshold = self.read_threshold_from_filename()
        self.loop_count = self.read_loop_count_from_filename()

    def convert_image_to_ndarray(self, image_path: str) -> numpy.ndarray:
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        image = cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return image
    
    def create_alpha(self, image: numpy.ndarray):
        # see __read_image_bytes() in AutoSplit/AutoSplitImage.py. Not sure why this works
        # Apparently adds alpha to images if not already present
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

        alpha = image[:,:,3]
        return cv2.merge([alpha, alpha, alpha])

    def read_flags_from_filename(self):
        flags = re.findall(r"_\{([bdp]+?)\}", self.name)
        if "d" in flags and "p" in flags:
            flags.remove("p")
        return flags

    def read_delay_from_filename(self):
        delay = re.search(r"_\#(.+?)\#", self.name)
        if not delay:
            return DEFAULT_DELAY
        return delay[1]

    def read_pause_from_filename(self):
        pause = re.search(r"_\[(.+?)\]", self.name)
        if not pause:
            return DEFAULT_PAUSE
        return pause[1]

    def read_threshold_from_filename(self):
        threshold = re.search(r"_\((.+?)\)", self.name)
        if not threshold:
            return DEFAULT_THRESHOLD
        return threshold[1]
    
    def read_loop_count_from_filename(self):
        loop_count = re.search(r"_\@(.+?)\@", self.name)
        if not loop_count:
            return DEFAULT_LOOP_COUNT
        return loop_count[1]
