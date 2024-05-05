from PyQt5.QtWidgets import QApplication

from capture import Capture, CaptureThread
from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from splitter import Splitter
from utils import LAST_IMAGE_DIR
import faulthandler
faulthandler.enable()

##### SEE THE TODO
class PilgrimUniversalAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])

        # Initialize capture, splitter, and GUI, inject capture into capture thread
        self.capture = Capture()
        self.capture_thread = CaptureThread(self.capture)
        self.splitter = Splitter(LAST_IMAGE_DIR)
        self.gui_main_window = GUIMainWindow()
        self.gui_settings_window = GUISettingsWindow()

        # Open splits (or stop comparisons, if no valid split image directory is saved)
        self.splitter.set_splits_to_initial_state()

        # Signals (capture to splitter)
        # sending frame for comparison

        # Signals (capture to GUI main window)
        self.capture.video_frame_signal.connect(self.gui_main_window.set_video_frame)

        # Signals (splitter to capture)
        # request pause (after split), delay (before split), unpause
        # send current split image

        # Signals (splitter to GUI main window)
        self.splitter.update_split_image_signal.connect(self.gui_main_window.set_split_image)
        self.splitter.match_percent_signal.connect(self.gui_main_window.set_match_percent)
        # send split name for display
        # send next split name for display

        # Signals (GUI to capture)
        self.gui_main_window.screenshot_button.clicked.connect(self.capture.take_screenshot)
        self.gui_main_window.reload_video_button.clicked.connect(self.restart_capture)
        # ? (maybe nothing else -- was going to say pause and unpause, but you can just pause / unpause the timer directly or use flags)

        # Signals (GUI to splitter)
        self.gui_main_window.reset_splits_button.clicked.connect(self.splitter.set_splits_to_initial_state)
        # move to next split, go back a split, skip, undo, reset

        # Signals (GUI to GUI settings)
        self.gui_main_window.settings_action.triggered.connect(self.gui_settings_window.exec)

        # open help menu

        # Signals (GUI_settings to settings)
        # request change to settings

        # Signals (settings to capture)

        # Signals (settings to splitter)

        # Signals (settings to split_image)


        self.gui_main_window.threadpool.start(self.capture_thread)
        self.gui_main_window.show()
        self.pilgrim_universal_autosplitter.exec()
    
    #### MAybe: instead of using a thread to run the capture loop, I can just use a QTimer. That should be a lot easier to pause.
    # Then I shouldn't have to block the button, either. 
    # Rule of thumb - don't access the same instance of an object from different threads. That's probably why Python keeps crashing.

    #TODO: Figure out why this doesn't work -- everything should be fine, but it's hanging up the gui... why?
    # IT's because this thread and the gui are in the same... thread? or is it because the button and the gui are in the same thread? I have no idea
    # Also check return value of cv2.videocapture(0) and maybe make sure it works in capture constructor
    def restart_capture(self):
        self.gui_main_window.block_object_signal(self.gui_main_window.reload_video_button, 1)  
        self.capture_thread.pause(1)
        self.capture.restart_capture()


if __name__ == "__main__":
    PilgrimUniversalAutosplitter()
