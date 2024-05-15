import webbrowser
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

from gui.main_window import GUIMainWindow
from gui.settings_window import GUISettingsWindow
from gui.style import GUIStyle
from splitter.split_dir import SplitDirectory
from utils import PercentType, settings


class GUIController():
    def __init__(self) -> None:
        self.style = GUIStyle()    # fix the style related stuff
        self.main_window = GUIMainWindow(self.style)
        self.main_window.set_layout(self.splitter_suspended())
        self.settings_window = GUISettingsWindow(self.style)
        self.split_directory = SplitDirectory()

        ###########
        #         #
        # Signals #
        #         #
        ###########

        # Image directory button
        self.main_window.image_directory_button.clicked.connect(self.split_directory.set_dir_path)
        self.main_window.image_directory_button.clicked.connect(self.main_window.set_split_directory_line_edit_text)

        # Minimal view / full view button
        self.main_window.minimal_view_button.clicked.connect(self.toggle_min_view_settings_value)
        self.main_window.minimal_view_button.clicked.connect(self.main_window.toggle_min_view_button_text)
        self.main_window.minimal_view_button.clicked.connect(lambda: self.main_window.set_layout(self.splitter_suspended()))

        # Next source button
        self.main_window.next_source_button.clicked.connect()

        self.main_window.screenshot_button.clicked.connect()
        self.main_window.reload_video_button.clicked.connect()
        self.main_window.previous_split_button.clicked.connect()
        self.main_window.next_split_button.clicked.connect()
        self.main_window.pause_comparison_button.clicked.connect()
        self.main_window.undo_split_button.clicked.connect()
        self.main_window.skip_split_button.clicked.connect()
        self.main_window.reset_splits_button.clicked.connect()

        # Menu bar actions
        self.main_window.settings_action.triggered.connect()

        # Keyboard shortcuts
        self.main_window.split_shortcut.activated.connect()
        self.main_window.reset_shortcut.activated.connect()
        self.main_window.undo_split_shortcut.activated.connect()
        self.main_window.skip_split_shortcut.activated.connect()
        self.main_window.previous_split_shortcut.activated.connect()
        self.main_window.next_split_shortcut.activated.connect()
        self.main_window.screenshot_shortcut.activated.connect()

        ###########################
        #                         #
        # Settings window signals #
        #                         #
        ###########################

        # Close all windows with ctrl+q
        self.settings_window.close_app_shortcut.activated.connect(self.settings_window.close)
        self.settings_window.close_app_shortcut.activated.connect(self.main_window.close)
        
        ######## Implement this from scraps
        self.settings_window.save_button.clicked.connect(self.save_settings)


    # HANDLE THIS SOMEWHERE
    # def set_dir_path(self):
    #     path = QFileDialog.getExistingDirectory(None, "Select splits folder")
    #     if path != "" and (self.dir_path != path or self.dir_path is None):
    #         self.dir_path = path
    #         self.prepare_split_images(make_image_list=True)
    #         settings.setValue("LAST_IMAGE_DIR", self.dir_path)




    ##################
    #                #
    # Getter Methods #
    #                #
    ##################

    def video_feed_active(self):
        pass

    def splits_active(self):
        pass

    def splitter_delaying(self):
        pass

    def splitter_suspended(self):   #### CHANGE ALL REFERENCES OF "PAUSED" TO "SUSPENDED"
        pass

    def is_first_split(self):
        pass

    def is_last_split(self):
        pass

    ##################
    #                #
    # Setter Methods #
    #                #
    ##################

    def toggle_min_view_settings_value(self):
        if settings.value("SHOW_MIN_VIEW"):
            settings.setValue("SHOW_MIN_VIEW", False)
        else:
            settings.setValue("SHOW_MIN_VIEW", True)




    def old(self):
        # Handle signals from GUI
        self.main_window.settings_window_action.triggered.connect(self.settings_window.exec)

        self.main_window.image_directory_button.clicked.connect(self.image_directory_button_signal.emit)
        self.main_window.screenshot_button.clicked.connect(self.screenshot_button_signal.emit)
        self.main_window.minimal_view_button.clicked.connect(self.minimal_view_button_signal.emit)
        self.main_window.next_source_button.clicked.connect(self.next_source_button_signal.emit)
        self.main_window.reload_video_button.clicked.connect(self.reload_video_button_signal.emit)
        self.main_window.previous_split_button.clicked.connect(self.previous_split_button_signal.emit)
        self.main_window.next_split_button.clicked.connect(self.next_split_button_signal.emit)
        self.main_window.pause_comparison_button.clicked.connect(self.process_pause_request)
        self.main_window.set_pause_comparison_button_status_signal.connect(self.set_pause_comparison_button_text)
        self.main_window.skip_split_button.clicked.connect(self.skip_split_button_signal.emit)
        self.main_window.undo_split_button.clicked.connect(self.undo_split_button_signal.emit)
        self.main_window.reset_splits_button.clicked.connect(self.reset_splits_button_signal.emit)
        self.main_window.update_video_feed_label_signal.connect(lambda: self.set_video_feed_label_status(status=self.video_feed_active, override=True))
        self.main_window.split_shortcut_signal.connect(self.split_request)
        self.main_window.reset_shortcut_signal.connect(self.request_reset)
        self.main_window.undo_split_shortcut_signal.connect(self.request_undo_split)
        self.main_window.skip_split_shortcut_signal.connect(self.request_skip_split)
        self.main_window.screenshot_shortcut_signal.connect(self.request_screenshot)

        self.settings_window.save_button.clicked.connect(lambda: self.style.set_global_style([self.main_window.main_window, self.settings_window]))
        self.settings_window.update_fps_start_signal.connect(self.update_fps_start_signal.emit)
        self.settings_window.update_fps_finish_signal.connect(self.update_fps_finish_signal.emit)
        self.settings_window.update_aspect_ratio_start_signal.connect(self.update_aspect_ratio_start_signal.emit)
        self.settings_window.update_aspect_ratio_finish_signal.connect(self.update_aspect_ratio_finish_signal.emit)
        self.settings_window.update_aspect_ratio_finish_signal.connect(self.main_window.set_layout)
        self.settings_window.set_match_percent_decimals_signal.connect(self.set_match_percent_decimals_signal.emit)
        self.settings_window.updated_default_threshold_signal.connect(lambda: self.updated_default_threshold_signal.emit(str(settings.value("DEFAULT_THRESHOLD")), PercentType.THRESHOLD))
        self.settings_window.updated_default_delay_signal.connect(self.updated_default_delay_signal.emit)
        self.settings_window.updated_default_pause_signal.connect(self.updated_default_pause_signal.emit)
        self.settings_window.close_app_signal.connect(self.main_window.close)
        self.settings_window.set_shortcut_signal.connect(self.main_window.set_shortcuts)

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

    def update_video_feed_label(self):
        if self.video_feed_active:
            self.set_video_feed_label_status(True)
        else:
            self.set_video_feed_label_status(False)

    def update_split_labels(self):
        if not self.splits_active:
            self.set_split_name(None)
            self.set_loop_text(None, None)

    def update_all_elements(self):
        self.update_enabled_comparison_data()
        self.update_enabled_buttons()
        self.update_video_feed_label()
        self.update_split_labels()

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

    def set_splitter_suspended_status(self, status: bool, delay_duration, pause_duration):
        if self.splitter_suspended != status:
            self.splitter_suspended = status
            self.update_enabled_comparison_data()
            self.update_enabled_buttons()
            self.set_pause_comparison_button_text()
            self.main_window.set_split_image_overlay_status(status, delay_duration, pause_duration)

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

    def set_video_feed_label_status(self, status: bool, override=True):
        if override or self.show_video_feed_label != status:
            self.show_video_feed_label = status
            self.main_window.set_video_feed_label(status)

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
    
    def set_minimal_view_button_enabled_status(self, status):
        if self.minimal_view_button_enabled != status:
            self.minimal_view_button_enabled = status
            self.main_window.set_minimal_view_button_status(status)

    def set_next_source_button_enabled_status(self, status):
        if self.next_source_button_enabled != status:
            self.next_source_button_enabled = status
            self.main_window.set_next_source_button_status(status)

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

    def split_request(self):
        if self.video_feed_active and self.splits_active and not self.splitter_suspended and not self.splitter_delaying:
            self.split_shortcut_signal.emit()

    def request_reset(self):
        if self.splits_active:
            self.reset_splits_button_signal.emit()

    def request_undo_split(self):
        if self.splits_active and not self.is_first_split:
            self.undo_split_button_signal.emit()

    def request_skip_split(self):
        if self.splits_active and not self.is_last_split:
            self.skip_split_button_signal.emit()

    def request_screenshot(self):
        if self.video_feed_active:
            self.screenshot_button_signal.emit()