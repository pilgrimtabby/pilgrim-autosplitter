from splitter.frame_capture import FrameCapture
from splitter.frame_compare import FrameCompare
from splitter.split_dir import SplitDir
from utils import settings

from utils import settings



class Splitter:
    def __init__(self) -> None:
        self.splits = SplitDir()
        self.current_match_percent = 0
        self.highest_match_percent = 0
        self.went_above_threshold_flag = False
        if settings.value("START_WITH_VIDEO"):
            show_min_view = settings.value("SHOW_MIN_VIEW")
            if (show_min_view and len(self.splits.list) > 0) or not show_min_view:
                self.capture = FrameCapture()
                self.compare = FrameCompare()

    def splitter(self):
        while True:
            show_min_view = settings.value("SHOW_MIN_VIEW")
            if (show_min_view and len(self.splits.list == 0)) or not self.capture.cap.isOpened():
                # end this thread
                # kill capture and compare threads, set those objects to None
                # set match percents null
                break
            
            self.frame = self.capture.frame                
                pass

            if len(self.splits.list > 0):
                current_image = self.splits.list[self.splits.current_image_index]
                self.compare.current_frame = frame
                self.current_match_percent = self.compare.match_percent

                if match_percent > self.highest_match_percent:
                    self.highest_match_percent = match_percent

                if match_percent >= current_image.threshold:
                    if current_image.below_flag:
                        self.went_above_threshold_flag = True
                    else:
                        # split
                        pass

