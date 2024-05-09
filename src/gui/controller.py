from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from gui.style import GUIStyle
from utils import PercentType, settings


class GUIController(QObject):
    image_directory_button_signal = pyqtSignal()
    screenshot_button_signal = pyqtSignal()
    reload_video_button_signal = pyqtSignal()
    previous_split_button_signal = pyqtSignal()
    next_split_button_signal = pyqtSignal()
    pause_request_signal = pyqtSignal(bool)
    skip_split_button_signal = pyqtSignal()
    undo_split_button_signal = pyqtSignal()
    reset_splits_button_signal = pyqtSignal()
    update_fps_start_signal = pyqtSignal()
    update_fps_finish_signal = pyqtSignal()
    update_aspect_ratio_start_signal = pyqtSignal()
    update_aspect_ratio_finish_signal = pyqtSignal()
    set_match_percent_decimals_signal = pyqtSignal()
    updated_default_threshold_signal = pyqtSignal(str, PercentType)
    updated_default_delay_signal = pyqtSignal()
    updated_default_pause_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.style = GUIStyle()
        self.main_window = GUIMainWindow(self.style)
        self.settings_window = GUISettingsWindow(self.style)

        self.video_feed_active = False
        self.splits_active = False
        self.splitter_suspended = False
        self.splitter_delaying = False
        self.is_first_split = False
        self.is_last_split = False
        self.show_video_feed_label = False
        self.show_video_capture_method_label = False
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

        # Handle signals from GUi
        self.main_window.settings_window_action.triggered.connect(self.settings_window.exec)
        self.main_window.about_window_action.triggered.connect(lambda: None)

        self.main_window.image_directory_button.clicked.connect(self.image_directory_button_signal.emit)
        self.main_window.screenshot_button.clicked.connect(self.screenshot_button_signal.emit)
        self.main_window.reload_video_button.clicked.connect(self.reload_video_button_signal.emit)
        self.main_window.previous_split_button.clicked.connect(self.previous_split_button_signal.emit)
        self.main_window.next_split_button.clicked.connect(self.next_split_button_signal.emit)
        self.main_window.pause_comparison_button.clicked.connect(self.process_pause_request)
        self.main_window.skip_split_button.clicked.connect(self.skip_split_button_signal.emit)
        self.main_window.undo_split_button.clicked.connect(self.undo_split_button_signal.emit)
        self.main_window.reset_splits_button.clicked.connect(self.reset_splits_button_signal.emit)

        self.settings_window.save_button.clicked.connect(lambda: self.style.set_global_style([self.main_window.main_window, self.settings_window]))
        self.settings_window.update_fps_start_signal.connect(self.update_fps_start_signal.emit)
        self.settings_window.update_fps_finish_signal.connect(self.update_fps_finish_signal.emit)
        self.settings_window.update_aspect_ratio_start_signal.connect(self.update_aspect_ratio_start_signal.emit)
        self.settings_window.update_aspect_ratio_finish_signal.connect(self.update_aspect_ratio_finish_signal.emit)
        self.settings_window.set_match_percent_decimals_signal.connect(self.set_match_percent_decimals_signal.emit)
        self.settings_window.updated_default_threshold_signal.connect(lambda: self.updated_default_threshold_signal.emit(str(settings.value("DEFAULT_THRESHOLD")), PercentType.THRESHOLD))
        self.settings_window.updated_default_delay_signal.connect(self.updated_default_delay_signal.emit)
        self.settings_window.updated_default_pause_signal.connect(self.updated_default_pause_signal.emit)

    def update_enabled_comparison_data(self):
        if self.splits_active:
            self.set_show_threshold_status(True)
            if self.video_feed_active and not self.splitter_suspended:
                self.set_show_comparison_match_status(True)
            else:
                self.set_show_comparison_match_status(False)
        else:
            self.set_show_threshold_status(False)
            self.set_show_comparison_match_status(False)

    def update_enabled_buttons(self):
        self.set_image_directory_button_enabled_status(True)
        self.set_reload_video_button_enabled_status(True)

        if self.splits_active:
            self.set_reset_splits_button_enabled_status(True)

            if self.is_first_split:
                self.set_undo_split_button_enabled_status(False)
                self.set_previous_split_button_enabled_status(False)
            else:
                self.set_undo_split_button_enabled_status(True)
                self.set_previous_split_button_enabled_status(True)

            if self.is_last_split:
                self.set_skip_split_button_enabled_status(False)
                self.set_next_split_button_enabled_status(False)
            else:
                self.set_skip_split_button_enabled_status(True)
                self.set_next_split_button_enabled_status(True)

            if self.video_feed_active:
                self.set_screenshot_button_enabled_status(True)

                if self.splitter_delaying:
                    self.set_pause_comparison_button_enabled_status(False)
                else:
                    self.set_pause_comparison_button_enabled_status(True)

            else:
                self.set_screenshot_button_enabled_status(False)
                self.set_pause_comparison_button_enabled_status(False)

        else:
            self.set_skip_split_button_enabled_status(False)
            self.set_undo_split_button_enabled_status(False)
            self.set_reset_splits_button_enabled_status(False)
            self.set_previous_split_button_enabled_status(False)
            self.set_next_split_button_enabled_status(False)
            self.set_pause_comparison_button_enabled_status(False)
            if self.video_feed_active:
                self.set_screenshot_button_enabled_status(True)
            else:
                self.set_screenshot_button_enabled_status(False)

    def update_labels(self):
        if self.video_feed_active:
            self.set_video_feed_label_status(True)
            self.set_video_capture_method_label_status(True)
        else:
            self.set_video_feed_label_status(False)
            self.set_video_capture_method_label_status(False)

        if not self.splits_active:
            self.set_split_name(None)
            self.set_loop_text(None, None)

    def update_all_elements(self):
        self.update_enabled_comparison_data()
        self.update_enabled_buttons()
        self.update_labels()

    def set_video_feed_active_status(self, status: bool):
        if self.video_feed_active != status:
            self.video_feed_active = status
            self.update_all_elements()

    def set_split_image_and_splits_active_status(self, frame: QPixmap):
        if frame is None:
            self.main_window.set_blank_split_image()
            if self.splits_active:
                self.splits_active = False
                self.update_all_elements()
        else:
            self.main_window.set_live_split_image(frame)
            if not self.splits_active:
                self.splits_active = True
                self.update_enabled_comparison_data()
                self.update_enabled_buttons()

    def set_splitter_suspended_status(self, status: bool):
        if self.splitter_suspended != status:
            self.splitter_suspended = status
            self.update_enabled_comparison_data()
            self.update_enabled_buttons()
            self.set_pause_comparison_button_text()

    def set_splitter_delaying_status(self, status: bool):
        if self.splitter_delaying != status:
            self.splitter_delaying = status
            self.update_enabled_buttons()

    def set_first_split_status(self, status):
        if self.is_first_split != status:
            self.is_first_split = status
            self.update_enabled_buttons()

    def set_last_split_status(self, status):
        if self.is_last_split != status:
            self.is_last_split = status
            self.update_enabled_buttons()

    def set_split_directory_line_edit_text_status(self, path):
        self.main_window.set_image_directory_line_edit(path)

    def set_video_feed_label_status(self, status):
        if self.show_video_feed_label != status:
            self.show_video_feed_label = status
            self.main_window.set_video_feed_label(status)

    def set_video_capture_method_label_status(self, status):
        if self.show_video_capture_method_label != status:
            self.show_video_capture_method_label = status
            self.main_window.set_video_capture_method_label(status)

    def set_show_comparison_match_status(self, status):
        if self.show_comparison_match != status:
            self.show_comparison_match = status
            if not self.show_comparison_match:
                self.set_match_percent(None, PercentType.CURRENT)
                self.set_match_percent(None, PercentType.HIGHEST)

    def set_show_threshold_status(self, status):
        if self.show_threshold != status:
            self.show_threshold = status
            if not self.show_threshold:
                self.set_match_percent(None, PercentType.THRESHOLD)

    def set_image_directory_button_enabled_status(self, status):
        if self.image_directory_button_enabled != status:
            self.image_directory_button_enabled = status
            self.main_window.set_image_directory_button_status(status)

    def set_screenshot_button_enabled_status(self, status):
        if self.screenshot_button_enabled != status:
            self.screenshot_button_enabled = status
            self.main_window.set_screenshot_button_status(status)

    def set_reload_video_button_enabled_status(self, status):
        if self.reload_video_button_enabled != status:
            self.reload_video_button_enabled = status
            self.main_window.set_reload_video_button_status(status)

    def set_previous_split_button_enabled_status(self, status):
        if self.previous_split_button_enabled != status:
            self.previous_split_button_enabled = status
            self.main_window.set_previous_split_button_status(status)

    def set_next_split_button_enabled_status(self, status):
        if self.next_split_button_enabled != status:
            self.next_split_button_enabled = status
            self.main_window.set_next_split_button_status(status)

    def set_pause_comparison_button_enabled_status(self, status):
        if self.pause_comparison_button_enabled != status:
            self.pause_comparison_button_enabled = status
            self.main_window.set_pause_comparison_button_status(status)

    def process_pause_request(self):
        if self.splitter_suspended:
            self.pause_request_signal.emit(False)
        else:
            self.pause_request_signal.emit(True)
        self.set_pause_comparison_button_text()

    def set_pause_comparison_button_text(self):
        if self.splitter_suspended:
            self.main_window.set_pause_comparison_button_text_to_unpause()
        else:
            self.main_window.set_pause_comparison_button_text_to_pause()

    def set_skip_split_button_enabled_status(self, status):
        if self.skip_split_button_enabled != status:
            self.skip_split_button_enabled = status
            self.main_window.set_skip_split_button_status(status)

    def set_undo_split_button_enabled_status(self, status):
        if self.undo_split_button_enabled != status:
            self.undo_split_button_enabled = status
            self.main_window.set_undo_split_button_status(status)

    def set_reset_splits_button_enabled_status(self, status):
        if self.reset_splits_button_enabled != status:
            self.reset_splits_button_enabled = status
            self.main_window.set_reset_splits_button_status(status)

    def set_match_percent(self, match_percent: str | None, percent_type: PercentType):
        if percent_type == PercentType.CURRENT:
            if self.show_comparison_match:
                self.main_window.set_current_match_percent(self.format_match_percent(match_percent))
            else:
                self.main_window.set_current_match_percent(None)

        elif percent_type == PercentType.HIGHEST:
            if self.show_comparison_match:
                self.main_window.set_highest_match_percent(self.format_match_percent(match_percent))
            else:
                self.main_window.set_highest_match_percent(None)
        
        else:  # PercentType.THRESHOLD
            if self.show_threshold:
                self.main_window.set_threshold_match_percent(self.format_match_percent(match_percent))
            else:
                self.main_window.set_threshold_match_percent(None)

    def format_match_percent(self, match_percent: str) -> str:
        format_string = f"{{:.{settings.value('MATCH_PERCENT_DECIMALS')}f}}"
        return format_string.format(float(match_percent) * 100)
            
    def show_screenshot_result(self, path: str):
        if path is None:
            self.main_window.screenshot_error_message()
        else:
            self.main_window.screenshot_success_message(path)

    def set_video_frame(self, frame: QPixmap):
        if frame is None:
            self.main_window.set_blank_video_frame()
        else:
            self.main_window.set_live_video_frame(frame)

    def set_split_name(self, name: str | None):
        if name is None:
            self.main_window.set_blank_split_name_label()
        else:
            self.main_window.set_live_split_name_label(name)

    def set_loop_text(self, current_loop: int | None, total_loops: int):
        if current_loop is None:
            self.main_window.set_blank_loop_label()
        elif current_loop == 0:
            self.main_window.set_no_loop_loop_label()
        else:
            self.main_window.set_live_loop_label_text(current_loop, total_loops)
