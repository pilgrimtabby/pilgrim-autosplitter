from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from capture import Capture
from gui.controller import GUIController
from hotkeys import Hotkeys
from split_directory import SplitDirectory
from splitter import Splitter
from utils import settings

# Fix settings gui


class PilgrimUniversalAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])
        self.capture = Capture()
        self.splitter = Splitter()
        self.split_directory = SplitDirectory(settings.value("LAST_IMAGE_DIR"))
        self.hotkeys = Hotkeys()
        self.gui = GUIController()

        # Signals (capture)
        self.capture.video_is_active_signal.connect(self.gui.set_video_feed_active_status)
        self.capture.send_to_gui_signal.connect(self.gui.set_video_frame)
        self.capture.screenshot_result_signal.connect(self.gui.show_screenshot_result)

        self.capture.video_is_active_signal.connect(self.splitter.set_video_feed_active_status)
        self.capture.send_to_splitter_signal.connect(self.splitter.compare_frame)

        # Signals (splitter)
        self.splitter.request_next_split_image_signal.connect(self.split_directory.load_next_split_image)
        self.splitter.suspended_status_signal.connect(self.gui.set_splitter_suspended_status)
        self.splitter.delaying_status_signal.connect(self.gui.set_splitter_delaying_status)
        self.splitter.match_percent_signal.connect(self.gui.set_match_percent)

        self.splitter.split_action_split_signal.connect(self.hotkeys.press_split_hotkey)
        self.splitter.split_action_pause_signal.connect(self.hotkeys.press_pause_hotkey)

        # Signals (split directory)
        self.split_directory.split_image_to_gui_signal.connect(self.gui.set_split_image)
        self.split_directory.loop_information_signal.connect(self.gui.set_loop_information)
        self.split_directory.image_amount_signal.connect(self.gui.set_image_amount)

        self.split_directory.split_image_to_splitter_signal.connect(self.splitter.set_split_image)

        # Activate splits and capture
        self.split_directory.prepare_split_images(make_image_list=True)
        self.capture.connect_to_video_feed()
        self.send_frame_timer = QTimer()
        self.send_frame_timer.setInterval(1000 // settings.value("DEFAULT_FPS"))
        self.send_frame_timer.timeout.connect(self.capture.send_frame)
        self.send_frame_timer.start()   # use self.timer.setInterval(1000 // new_time_here) to change time

        self.gui_main_window.show()
        self.pilgrim_universal_autosplitter.exec()        


if __name__ == "__main__":
    PilgrimUniversalAutosplitter()
