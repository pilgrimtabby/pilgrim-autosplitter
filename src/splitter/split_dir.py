import glob
import pathlib
import re

import cv2
import numpy

from utils import frame_to_pixmap, settings


class SplitDir:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.list = self.get_split_images()
        self.current_image_index = 0
        self.current_loop = 0

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
        current_image = self.list[self.current_image_index]

        if self.current_loop == current_image.loops:
            if self.current_image_index < len(self.list) - 1:
                self.current_image_index += 1
            else:
                self.current_image_index = 0
            self.current_loop = 0

        else:
            self.current_loop += 1
        
    def previous_split_image(self):
        if self.current_loop == 0:
            if self.current_image_index == 0:
                self.current_image_index = len(self.list) - 1
            else:
                self.current_image_index -= 1
            
            current_image = self.list[self.current_image_index]
            self.current_loop = current_image.loops
            
        else:
            self.current_loop -= 1
        
    def reset_split_images(self):
        self.current_image_index = 0
        self.current_loop = 0

    class _SplitImage:
        def __init__(self, image_path) -> None:
            self.path = image_path
            self.name = pathlib.Path(image_path).stem
            self.image = self.get_and_resize_image()
            self.alpha = self.get_alpha()
            self.pixmap = frame_to_pixmap(self.image, is_split=True)  ### Maybe split this method back into 2 methods
            self.below_flag, self.dummy_flag, self.pause_flag = self.get_flags_from_name()
            self.delay_duration, self.delay_is_default = self.get_delay_from_name()
            self.pause_duration, self.pause_is_default = self.get_pause_from_name()
            self.threshold, self.threshold_is_default = self.get_threshold_from_name()
            self.loops, self.loops_is_default = self.get_loops_from_name()

        def get_and_resize_image(self) -> numpy.ndarray:
            image = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(image, (settings.value("FRAME_WIDTH"), settings.value("FRAME_HEIGHT")), interpolation=cv2.INTER_AREA)
            # Add alpha to images if not already present (ie if image has only 3 channels, not 4)
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            return image
        
        def get_alpha(self):
            alpha = self.image[:, :, 3]
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

        def get_loops_from_name(self):
            loops = re.search(r"_\@(.+?)\@", self.name)
            if not loops:
                return settings.value("DEFAULT_LOOPS"), True
            return int(loops[1]), False