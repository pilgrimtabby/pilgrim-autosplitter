import glob
import pathlib
import re

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from utils import (DEFAULT_DELAY, DEFAULT_LOOP_COUNT, DEFAULT_PAUSE,
                   DEFAULT_THRESHOLD, FRAME_HEIGHT, FRAME_WIDTH,
                   LAST_IMAGE_DIR)
from utils import PercentType


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
        self.raw_image = self.get_raw_image()
        self.alpha = self.get_alpha()
        self.pixmap = self.get_pixmap()
        self.name = pathlib.Path(self.path).stem
        self.flags = self.get_flags_from_filename()
        self.delay_duration = self.get_delay_from_filename()
        self.pause_duration = self.get_pause_from_filename()
        self.threshold = self.get_threshold_from_filename()
        self.loop_count = self.get_loop_count_from_filename()

    def get_raw_image(self) -> numpy.ndarray:
        image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
        image = cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return image

    def get_alpha(self):
        # see __read_image_bytes() in AutoSplit/AutoSplitImage.py. Not sure why this works
        # Apparently adds alpha to images if not already present
        if self.raw_image.shape[2] == 3:
            self.raw_image = cv2.cvtColor(self.raw_image, cv2.COLOR_BGR2BGRA)

        alpha = self.raw_image[:,:,3]
        return cv2.merge([alpha, alpha, alpha])
    
    def get_pixmap(self):
        image = QImage(self.raw_image, self.raw_image.shape[1], self.raw_image.shape[0], QImage.Format_RGB888)
        # return QPixmap.fromImage(image)
        return QPixmap(self.path)

    def get_flags_from_filename(self):
        flags = re.findall(r"_\{([bdp]+?)\}", self.name)
        if "d" in flags and "p" in flags:
            flags.remove("p")
        return flags

    def get_delay_from_filename(self):
        delay = re.search(r"_\#(.+?)\#", self.name)
        if not delay:
            return DEFAULT_DELAY
        return float(delay[1])

    def get_pause_from_filename(self):
        pause = re.search(r"_\[(.+?)\]", self.name)
        if not pause:
            return DEFAULT_PAUSE
        return float(pause[1])

    def get_threshold_from_filename(self):
        threshold = re.search(r"_\((.+?)\)", self.name)
        if not threshold:
            return DEFAULT_THRESHOLD
        return float(threshold[1])

    def get_loop_count_from_filename(self):
        loop_count = re.search(r"_\@(.+?)\@", self.name)
        if not loop_count:
            return DEFAULT_LOOP_COUNT
        return int(loop_count[1])


class SplitDirectory(QObject):
    match_percent_signal = pyqtSignal(str, PercentType)
    splits_loaded_signal = pyqtSignal(bool)
    split_image_signal = pyqtSignal(QPixmap)

    split_image: SplitImage
    image_dir: str
    image_list: list
    image_list_index: int
    current_loop_count: float
    
    def __init__(self):
        super().__init__()
        self.path = LAST_IMAGE_DIR

    def assemble_split_images(self):
        self.current_image = None
        self.current_index = -1
        self.current_loop_count = 0
        self.cap_is_open = False
        self.images = []
        for image in self.get_image_paths():
            self.images += [SplitImage(image)]
        if self.images:
            self.load_next_split()
            self.splits_loaded_signal.emit(True)
        else:
            self.splits_loaded_signal.emit(False)

    def load_next_split(self):
        if self.current_loop_count > 0:
            self.current_loop_count -= 1
            return
        
        self.current_index += 1
        if self.current_index == len(self.images):
            self.current_index = 0
        self.current_image = self.images[self.current_index]
        self.current_loop_count = self.current_image.loop_count
        
        self.split_image_signal.emit(self.current_image.pixmap)
        self.match_percent_signal.emit(str(self.current_image.threshold), PercentType.THRESHOLD)

    def reset_splits(self):
        self.current_index = -1
        self.current_loop_count = 0
        if self.images:
            self.load_next_split()
            self.splits_loaded_signal.emit(True)
        else:
            self.splits_loaded_signal.emit(False)

    def get_image_paths(self):
        if not pathlib.Path(self.path).is_dir():
            return []
        paths = (
                glob.glob(f"{self.path}/*.png")
                + glob.glob(f"{self.path}/*.jpg")
                + glob.glob(f"{self.path}/*.jpeg")
        )
        return sorted(paths)

    def set_dir_path(self, path: str):
        self.path = path
        self.assemble_split_images()

    def cap_is_open(self, status):
        self.cap_is_open = status
