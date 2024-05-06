from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from capture import Capture
from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from hotkeys import Hotkeys
from split_directory import SplitDirectory
from splitter import Splitter
from utils import settings

# Make sure all the buttons on the gui actually work (see below)
# Fix settings gui


# splits take down all the buttons except screenshot and reconnect video.
# video takes down all the buttons except left / right nav and take reconnect video.

# To go up:
# take screenshot -- just video (done)
# Reconnect video -- nothing    (done)
# Pause / resume comparison -- video AND splits must be active
# Skip split, undo split, reset run, left / right splits -- splits must be active

class PilgrimUniversalAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])
        self.capture = Capture()
        self.splitter = Splitter()
        self.split_directory = SplitDirectory(settings.value("LAST_IMAGE_DIR"))
        self.hotkeys = Hotkeys()
        self.gui_main_window = GUIMainWindow()
        self.gui_settings_window = GUISettingsWindow()

        # capture active -> splitter turns on (and is receiving images)
        # images active -> send to splitter, splitter starts doing comparisons ||| this should also turn on right side buttons

        # Tell GUI that video is active
        self.capture.video_is_active_signal.connect(self.gui_main_window.set_screenshot_button_status)
        # Send video to GUI
        self.capture.frame_to_gui_signal.connect(self.gui_main_window.set_video_frame)
        # Send video to splitter
        self.capture.frame_to_splitter_signal.connect(self.splitter.compare_frame_to_split_image)
        # Return success message after screenshot attempt
        self.capture.screenshot_success_signal.connect(self.gui_main_window.screenshot_success_message)
        # Return error message after screenshot attempt
        self.capture.screenshot_error_signal.connect(self.gui_main_window.screenshot_error_message)

        # Give GUI split image (if it has split image, it knows splits are active)
        self.split_directory.current_or_empty_split_image_to_gui_signal.connect(self.gui_main_window.set_split_image)
        # Tell splitter splits are active; feed it split image
        self.split_directory.current_or_empty_split_image_to_splitter_signal.connect(self.splitter.set_split_image)

        # Ask split directory for next split image
        self.splitter.execute_split_signal.connect(self.split_directory.load_next_split_image)
        # Disable "Pause comparisons" button in GUI
        self.splitter.allow_external_pausing_signal.connect(self.gui_main_window.set_pause_comparison_button_status)
        # Force "Pause comparisons" button to say "Pause", just in case
        self.splitter.unpause_splitter_button_text_correction.connect(self.gui_main_window.reset_pause_comparison_button_text)
        # Send match %s to GUI
        self.splitter.match_percent_signal.connect(self.gui_main_window.set_match_percent)
        # Send split name to GUI
        self.splitter.split_name_signal.connect(self.gui_main_window.set_split_name)
        # Send loop count / info to GUI
        self.splitter.split_loop_signal.connect(self.gui_main_window.set_loop_text)
        # Pause timer
        self.splitter.split_action_split_signal.connect(self.hotkeys.press_split_hotkey)
        # Split timer
        self.splitter.split_action_pause_signal.connect(self.hotkeys.press_pause_hotkey)

        # Open settings menu
        self.gui_main_window.settings_action.triggered.connect(self.gui_settings_window.exec)
        # Take screenshot
        self.gui_main_window.screenshot_button.clicked.connect(self.capture.take_screenshot)
        # (Re)connect to video feed
        self.gui_main_window.reload_video_button.clicked.connect(self.capture.connect_to_video_feed)
        # Pause comparisons
        self.gui_main_window.pause_comparison_button_clicked_signal.connect(self.splitter.pause_splitter)
        # Unpause comparisons
        self.gui_main_window.unpause_comparison_button_clicked_signal.connect(self.splitter.unpause_splitter)
        # Reset splits
        self.gui_main_window.reset_splits_button.clicked.connect(self.split_directory.reset_split_images)
        # move to next split, go back a split, skip, undo

        # Signals (GUI to GUI settings)

        # open help menu

        # Signals (GUI_settings to settings)
        # request change to settings

        # Signals (settings to capture)

        # Signals (settings to splitter)

        # Signals (settings to split_image)

        # Open splits (or stop comparisons, if no valid split image directory is saved)
        self.split_directory.prepare_split_images(make_image_list=True)

        # start video feed
        self.capture.connect_to_video_feed()
        self.send_frame_timer = QTimer()
        self.send_frame_timer.setInterval(1000 // settings.value("DEFAULT_FPS"))
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
