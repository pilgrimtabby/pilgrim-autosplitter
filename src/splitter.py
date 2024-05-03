import glob
import pathlib
import time

import cv2
import numpy

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
from PyQt5.QtGui import QPixmap

from capture import Capture
from split_image import SplitImage
from utils import DEFAULT_FPS


class Splitter(QObject):
    video_feed_frame_signal = pyqtSignal(QPixmap)
    match_percent_signal = pyqtSignal(str)
    update_split_image_signal = pyqtSignal(QPixmap)

    video_source: cv2.VideoCapture
    split_image: SplitImage
    image_dir: str
    image_list: list
    image_list_index: int
    current_loop_count: float
    fps: int
    
    def __init__(self, image_dir: str):
        super().__init__()
        self.video_source = Capture()
        self.split_image = None
        self.image_dir = image_dir

        self.image_list = []
        self.splits_active = False
        for image in self.get_split_image_paths():
            self.image_list += [SplitImage(image)]
        if self.image_list:
            self.splits_active = True

        self.image_list_index = 0
        self.current_loop_count = 0
        self.fps = DEFAULT_FPS

    def get_split_image_paths(self):
        if not pathlib.Path(self.image_dir).is_dir():
            return []
        return (
            glob.glob(f"{self.image_dir}/*.png")
            + glob.glob(f"{self.image_dir}/*.jpg")
            + glob.glob(f"{self.image_dir}/*.jpeg")
        )
        
    def set_splits_to_initial_state(self):
        self.image_list_index = 0
        self.go_to_next_split()

    def go_to_next_split(self):
        self.split_image = self.image_list[self.image_list_index]
        self.current_loop_count = self.split_image.loop_count
        self.update_split_image_signal.emit(self.split_image.image_for_gui)
    
    def get_comparison_frame(self, split_image: SplitImage, frame: numpy.ndarray) -> numpy.ndarray:
        comparison_frame = cv2.matchTemplate(
            frame,
            split_image.raw_image[:,:,0:3],
            cv2.TM_CCORR_NORMED,
            mask=split_image.alpha
        )
        return comparison_frame

    def read_loop(self):
        prev_time = 0

        while True:
            time_elapsed = time.time() - prev_time
            if time_elapsed > 1. / self.fps:
                prev_time = time.time()

                raw_frame = self.video_source.get_raw_frame()
                if not self.is_valid_image(raw_frame):
                    continue

                video_feed_frame = SplitImage.get_pixmap_from_frame(raw_frame)
                self.video_feed_frame_signal.emit(video_feed_frame)


    # def read_loop(self):
    #     while True:
    #         if not self.watch_for_match():
    #             self.set_splits_to_initial_state()
    #             self.read_loop()
            
    #         # send match_percent of 0 to gui
    #         time.sleep(self.split_image.delay)

    #         if "p" in self.split_image.flags:
    #             # key in the pause key
    #             pass
    #         elif not "d" in self.split_image.flags:
    #             # key in the split key
    #             pass

    #         time.sleep(self.split_image.pause)

    #         if self.current_loop_count > 0:
    #             self.current_loop_count -= 1
    #         else:
    #             self.image_list_index += 1
    #             if self.image_list_index == len(self.image_list):
    #                 self.set_splits_to_initial_state()
    #                 self.read_loop()

    #             self.go_to_next_split()

    # def watch_for_match(self):
    #     prev_time = 0
    #     went_above_threshold = False
    #     below_flag_set = False
    #     if "b" in self.split_image.flags:
    #         below_flag_set = True

    #     while True:
    #         time_elapsed = time.time() - prev_time
    #         if time_elapsed > 1. / self.fps:
    #             prev_time = time.time()

    #             comparison_frame, video_feed_frame = self.video_source.get_processed_frames(self.split_image)
    #             if not self.is_valid_image(comparison_frame):
    #                 continue

    #             match_percent = max(cv2.minMaxLoc(comparison_frame)[1], 0)
    #             self.video_feed_frame_signal.emit(video_feed_frame)
    #             self.match_percent_signal.emit("{:.1f}".format(match_percent * 100))

    #             if match_percent > self.split_image.threshold:
    #                 if below_flag_set:
    #                     went_above_threshold = True
    #                 else:
    #                     return True

    #             elif went_above_threshold and match_percent < self.split_image.threshold:
    #                 return True                

    def is_valid_image(self, image: numpy.ndarray):
        return image is not None
    
    def update_default_fps(self, fps):
        self.fps = fps

class SplitterThread(QRunnable):
    def __init__(self, splitter: Splitter):
        super(SplitterThread, self).__init__()
        self.splitter = splitter

    @pyqtSlot()
    def run(self):
        self.splitter.set_splits_to_initial_state()
        self.splitter.read_loop()




def main():
    print("Hello")


if __name__ == "__main__":
    main()

