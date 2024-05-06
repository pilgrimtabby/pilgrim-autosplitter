from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from capture import Capture
from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from splitter import Splitter
from utils import DEFAULT_FPS


class PilgrimUniversalAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])

        # Initialize capture, splitter, and GUI
        self.capture = Capture()
        self.splitter = Splitter()
        self.gui_main_window = GUIMainWindow()
        self.gui_settings_window = GUISettingsWindow()

        # Signals (capture to splitter)
        self.capture.raw_frame_signal.connect(self.splitter.compare_frame_to_split_image)
        self.capture.cap_open_signal.connect(self.splitter.split_images.cap_is_open)

        # Signals (capture to GUI main window)
        self.capture.video_frame_signal.connect(self.gui_main_window.set_video_frame)
        self.capture.cap_open_signal.connect(self.gui_main_window.set_screenshot_button_status)
        self.capture.screenshot_success_signal.connect(self.gui_main_window.screenshot_success_message)
        self.capture.screenshot_error_signal.connect(self.gui_main_window.screenshot_error_message)
        self.capture.match_percent_signal.connect(self.gui_main_window.set_match_percent)

        # Signals (splitter to capture)
        self.splitter.split_images.splits_loaded_signal.connect(self.capture.set_splits_loaded_status)
        self.splitter.pause_signal.connect(self.capture.pause_comparison_for_set_time)
        # request pause (after split), delay (before split), unpause
        # send current split image

        # Signals (splitter to GUI main window)
        self.splitter.split_images.split_image_signal.connect(self.gui_main_window.set_split_image)
        self.splitter.match_percent_signal.connect(self.gui_main_window.set_match_percent)
        self.splitter.split_images.match_percent_signal.connect(self.gui_main_window.set_match_percent)
        self.splitter.split_images.splits_loaded_signal.connect(self.gui_main_window.set_split_image_css_status)
        self.splitter.pause_signal.connect(lambda: self.gui_main_window.set_pause_comparison_button_status(False))
        # send split name for display
        # send next split name for display

        # Signals (GUI to capture)
        self.gui_main_window.screenshot_button.clicked.connect(self.capture.take_screenshot)
        self.gui_main_window.reload_video_button.clicked.connect(self.capture.connect_to_video_feed)
        self.gui_main_window.pause_comparison_signal.connect(self.capture.pause_comparison)
        self.gui_main_window.unpause_comparison_signal.connect(self.capture.unpause_comparison)

        # Signals (GUI to splitter)
        self.gui_main_window.reset_splits_button.clicked.connect(self.splitter.split_images.reset_splits)
        # move to next split, go back a split, skip, undo, reset

        # Signals (GUI to GUI settings)
        self.gui_main_window.settings_action.triggered.connect(self.gui_settings_window.exec)

        # open help menu

        # Signals (GUI_settings to settings)
        # request change to settings

        # Signals (settings to capture)

        # Signals (settings to splitter)

        # Signals (settings to split_image)

        # Open splits (or stop comparisons, if no valid split image directory is saved)
        self.splitter.split_images.assemble_split_images()

        # start video feed
        self.capture.connect_to_video_feed()
        self.send_frame_timer = QTimer()
        self.send_frame_timer.setInterval(1000 // DEFAULT_FPS)
        self.send_frame_timer.timeout.connect(self.capture.send_frame)
        self.send_frame_timer.start()   # use self.timer.setInterval(1000 // new_time_here) to change time

        self.gui_main_window.show()
        self.pilgrim_universal_autosplitter.exec()        

    def set_pause_timer(self, delay, pause):
        # Grey out pause_comparison button during this time
        self.send_frame_timer.stop()
        QTimer.singleShot(int((delay + pause) * 1000), self.send_frame_timer)


if __name__ == "__main__":
    PilgrimUniversalAutosplitter()
 