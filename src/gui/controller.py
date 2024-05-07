from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from utils import PercentType
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal


class GUIController:
    image_directory_button_signal = pyqtSignal()
    screenshot_button_signal = pyqtSignal()
    reload_video_button_signal = pyqtSignal()
    previous_split_button_signal = pyqtSignal()
    next_split_button_signal = pyqtSignal()
    pause_comparison_button_signal = pyqtSignal()
    unpause_comparison_button_signal = pyqtSignal()
    skip_split_button_signal = pyqtSignal()
    undo_split_button_signal = pyqtSignal()
    reset_splits_button_signal = pyqtSignal()

    def __init__(self) -> None:
        self.main_window = GUIMainWindow()
        self.settings_window = GUISettingsWindow()

        self.video_feed_active = False
        self.splits_active = False
        self.splitter_suspended = False
        self.splitter_delaying = False
        
        self.split_image = QPixmap()
        self.image_amount = 0

        self.show_comparison_match = False
        self.show_threshold = False
        self.image_directory_button_enabled = False
        self.screenshot_button_enabled = False
        self.reload_video_button_enabled = False
        self.previous_split_button_enabled = False
        self.next_split_button_enabled = False
        self.pause_comparison_button_enabled = False
        self.skip_split_button_enabled = False
        self.undo_split_button_enabled = False
        self.reset_splits_button_enabled = False

        self.main_window.settings_action.triggered.connect(self.settings_window.exec)

        self.main_window.image_directory_button.clicked.connect(self.image_directory_button_signal.emit)
        self.main_window.screenshot_button.clicked.connect(self.screenshot_button_signal.emit)
        self.main_window.reload_video_button.clicked.connect(self.reload_video_button_signal.emit)
        self.main_window.previous_split_button.clicked.connect(self.previous_split_button_signal.emit)
        self.main_window.next_split_button.clicked.connect(self.next_split_button_signal.emit)
        self.main_window.pause_comparison_button_clicked_signal.connect(self.pause_comparison_button_signal.emit)
        self.main_window.unpause_comparison_button_clicked_signal.connect(self.unpause_comparison_button_signal.emit)
        self.main_window.skip_split_button.clicked.connect(self.skip_split_button_signal.emit)
        self.main_window.undo_split_button_signal.clicked.connect(self.undo_split_button_signal.emit)
        self.main_window.reset_splits_button.clicked.connect(self.reset_splits_button_signal.emit)

    def set_video_feed_active_status(self, status: bool):
        if self.video_feed_active != status:
            self.video_feed_active = status
            self.update_enabled_elements()

    def set_split_image(self, image: object):
        self.split_image = image
        if self.split_image.isNull() and self.splits_active:
            self.splits_active = False
            self.update_enabled_elements()
        elif not self.split_image.isNull() and not self.splits_active:
            self.splits_active = True
            self.update_enabled_elements()

    def set_splitter_suspended_status(self, status: bool):
        if self.splitter_suspended != status:
            self.splitter_suspended = status
            self.update_enabled_elements()

    def set_splitter_delaying_status(self, status: bool):
        if self.splitter_delaying != status:
            self.splitter_delaying = status
            self.update_enabled_elements()

    def update_enabled_elements(self):
        self.update_enabled_comparison_data()
        self.update_enabled_buttons()

    def update_enabled_comparison_data(self):
        if self.splits_active:
            self.show_threshold = True
            if self.video_feed_active and not self.splitter_suspended:
                self.show_comparison_match = True
        else:
            self.show_threshold = False
            self.show_comparison_match = False

    def update_enabled_buttons(self):
        self.image_directory_button_enabled = True
        if self.splits_active: # Qualify this
            self.skip_split_button_enabled = True # not if last split
            self.undo_split_button_enabled = True # not if first split
            self.reset_splits_button_enabled = True
            self.previous_split_button_enabled = True # not if first split
            self.next_split_button_enabled = True # not if last split
            if self.video_feed_active:
                self.screenshot_button_enabled = True
                if self.splitter_delaying:
                    self.set_pause_comparison_button_status(False)
                else:
                    self.set_pause_comparison_button_status(True)
            else:
                self.screenshot_button_enabled = False
                self.set_pause_comparison_button_status(False)

        else:
            self.skip_split_button_enabled = False
            self.undo_split_button_enabled = False
            self.reset_splits_button_enabled = False
            self.previous_split_button_enabled = False
            self.next_split_button_enabled = False
            self.set_pause_comparison_button_status(False)
            if self.video_feed_active:
                self.screenshot_button_enabled = True
            else:
                self.screenshot_button_enabled = False

    def set_comparison_match_percents_null(self):
        self.match_percent_signal.emit("--.-", PercentType.CURRENT)
        self.match_percent_signal.emit("--.-", PercentType.HIGHEST)

    def set_threshold_match_percent_null(self):
        self.match_percent_signal.emit("--.-", PercentType.THRESHOLD)

    def show_screenshot_result(self, message):
        # None
        # "No video feed detected. Please make sure video feed is active and try again."
        pass

    def set_video_frame(self):
        pass

    def set_match_percent(self):
        pass

    def set_image_amount(self, amount):
        self.image_amount = amount

    def set_pause_comparison_button_status(self, status: bool):
        if self.pause_comparison_button_enabled != status:
            self.pause_comparison_button_enabled = status
        # set text (dependent on self.splitter_suspended -- if is suspended, should say "unpause" or whatever)
        # should this be inside or outside the `if` statement?
