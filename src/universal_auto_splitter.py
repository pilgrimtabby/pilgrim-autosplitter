import glob
import pathlib
import sys
import time

import cv2
import numpy
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from capture import Capture
from gui.gui import GUI
from gui.main_window import GUIMainWindow
from split_image import SplitImage
from utils import DEFAULT_FPS, FRAME_HEIGHT, FRAME_WIDTH, LAST_IMAGE_DIR


class UniversalAutoSplitter:
    video_source: cv2.VideoCapture
    gui: GUI
    split_image: SplitImage
    image_dir: str
    image_list: list
    image_list_index: int
    # last_raw_frame: numpy.ndarray
    current_loop_count: float
    
    def __init__(self, image_dir: str):
        self.video_source = Capture()
        self.gui = GUI()
        self.last_raw_frame = None
        self.new_image_dir(image_dir)
        self.read_loop()

    def new_image_dir(self, path: str):
        self.image_dir = path
        image_paths = self.get_split_image_paths()

        self.image_list = []
        for image in image_paths:
            self.image_list += [SplitImage(image)]
        if len(self.image_list) == 0:
            self.split_image = None
            self.image_list_index = None
        else:
            self.reset_splits()

    def get_match_percent(self, current_frame: numpy.ndarray) -> float:
        compare = cv2.matchTemplate(
            current_frame,
            self.split_image.ndarray[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=self.split_image.alpha
        )
        return max(cv2.minMaxLoc(compare)[1], 0)

    def get_split_image_paths(self):
        if not pathlib.Path(self.image_dir).is_dir():
            return []
        return (
            glob.glob(f"{self.image_dir}/*.png")
            + glob.glob(f"{self.image_dir}/*.jpg")
            + glob.glob(f"{self.image_dir}/*.jpeg")
        )
    
    def reset_splits(self):
        self.split_image = self.image_list[0]
        self.image_list_index = 0
        self.current_loop_count = self.split_image.loop_count
        self.read_loop()

    def read_loop(self):
        while True:
            if not self.watch_for_match():
                self.reset_splits()
            
            # send match_percent of 0 to gui
            time.sleep(self.split_image.delay)

            if "p" in self.split_image.flags:
                # key in the pause key
                pass
            elif not "d" in self.split_image.flags:
                # key in the split key
                pass

            time.sleep(self.split_image.pause)

            if self.current_loop_count == 0:
                self.image_list_index += 1
                if self.image_list_index == len(self.image_list):
                    self.reset_splits()
                self.split_image = self.image_list[self.image_list_index]
            else:
                self.current_loop_count -= 1


    def watch_for_match(self):
        prev_time = 0
        went_above = False
        below_flag = False
        if "b" in self.split_image.flags:
            below_flag = True

        while True:
            time_elapsed = time.time() - prev_time
            if time_elapsed > 1. / DEFAULT_FPS:
                # if reset_split_button_pressed():
                #     return False
                prev_time = time.time()
                raw_frame = self.video_source.cap.read()[1]

                # Apparently the frames are never quite exactly the same (I could only get "equal" to print when the card was off).
                # if (raw_frame == self.last_raw_frame).all():
                #     print("equal")
                #     continue
                # self.last_raw_frame = raw_frame
                
                resized_frame = cv2.resize(raw_frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
                match_percent = self.get_match_percent(resized_frame)
                self.gui.update_match_percent(match_percent)

                if match_percent > self.split_image.threshold:
                    if not below_flag:
                        return True
                    if not went_above:
                        went_above = True

                elif went_above and match_percent < self.split_image.threshold:
                    return True


def main():
    splitter = QApplication([])
    gui = GUI()

    timer = QTimer()
    timer.timeout.connect(gui.window.set_current_frame)
    timer.start(1000 // DEFAULT_FPS)

    splitter.exec()

    sys.exit()


if __name__ == "__main__":
    main()
