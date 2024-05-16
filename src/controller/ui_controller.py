from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer

from splitter.split_dir import SplitDir
from ui.ui_main_window import GUIMainWindow
from ui.ui_settings_window import GUISettingsWindow
from ui.ui_style import GUIStyle
from utils import PercentType, settings


class UIController:
    def __init__(self, splitter) -> None:
        self.splitter = splitter
        self.last_split_image_index = None

        self.style = GUIStyle()    # fix the style related stuff
        self.main_window = GUIMainWindow(self.style)
        self.main_window.set_layout(self.splitter_suspended())
        self.settings_window = GUISettingsWindow(self.style)

        #######################
        #                     #
        # Main Window Signals #
        #                     #
        #######################

        # Image directory button clicked
        self.main_window.image_directory_button.clicked.connect(self.splitter.splits.set_image_directory_path)
        self.main_window.image_directory_button.clicked.connect(lambda self=self.splitter: setattr(self, "splits", SplitDir()))

        # Minimal view / full view button clicked
        self.main_window.minimal_view_button.clicked.connect(lambda: settings.setValue("SHOW_MIN_VIEW", not settings.value("SHOW_MIN_VIEW")))
        self.main_window.minimal_view_button.clicked.connect(self.main_window.toggle_min_view_button_text)
        self.main_window.minimal_view_button.clicked.connect(lambda: self.main_window.set_layout(splitter_paused=self.splitter.suspended))

        # Next source button clicked
        self.main_window.next_source_button.clicked.connect(self.splitter.next_capture_source)
        self.main_window.next_source_button.clicked.connect(self.splitter.safe_exit_all_threads)
        self.main_window.next_source_button.clicked.connect(self.splitter.start)

        # Screenshot button clicked
        self.main_window.screenshot_button.clicked.connect()

        # Reload video button clicked
        self.main_window.reload_video_button.clicked.connect(self.splitter.safe_exit_all_threads)
        self.main_window.reload_video_button.clicked.connect(self.splitter.start)

        # Pause comparison / unpause comparison button clicked
        self.main_window.pause_comparison_button.clicked.connect(self.splitter.toggle_suspended)

        # Split keyboard shortcut entered
        self.main_window.split_shortcut.activated.connect(self.splitter.splits.next_split_image)

        # Undo split button clicked
        self.main_window.undo_split_button.clicked.connect(self.splitter.splits.previous_split_image)
        ##### send undo button keystroke

        # Undo split keyboard shortcut entered
        self.main_window.undo_split_shortcut.activated.connect(self.splitter.splits.previous_split_image)

        # Skip split button clicked
        self.main_window.skip_split_button.clicked.connect(self.splitter.splits.next_split_image)
        ##### send skip button keystroke

        # Skip split keyboard shortcut entered
        self.main_window.skip_split_shortcut.activated.connect(self.splitter.splits.next_split_image)

        # Previous split button clicked
        self.main_window.previous_split_button.clicked.connect(self.splitter.splits.previous_split_image)

        # Next split button entered
        self.main_window.next_split_button.clicked.connect(self.splitter.splits.next_split_image)

        # Reset button clicked
        self.main_window.reset_splits_button.clicked.connect(self.splitter.splits.reset_split_images)
        self.last_split_image_index = None
        ##### Send reset keyboard shortcut

        # Reset splits keyboard shortcut entered
        self.main_window.reset_shortcut.activated.connect(self.splitter.splits.reset_split_images)
        self.last_split_image_index = None

        # Settings menu bar action triggered
        self.main_window.settings_action.triggered.connect(self.settings_window.exec)

        ###########################
        #                         #
        # Settings window signals #
        #                         #
        ###########################

        # Quit app keyboard shortcut entered (ctrl+q)
        self.settings_window.close_app_shortcut.activated.connect(self.settings_window.close)
        self.settings_window.close_app_shortcut.activated.connect(self.main_window.close)
        
        # Save button clicked
        self.settings_window.save_button.clicked.connect(self.save_settings)

        ##########################
        #                        #
        # Get info from splitter #
        #                        #
        ##########################

        self.update_ui_timer = QTimer()
        self.update_ui_timer.setInterval(1000 // settings.value("FPS"))
        self.update_ui_timer.timeout.connect(self.get_info_from_splitter)
        self.update_ui_timer.start()

    def get_info_from_splitter(self):
        # Video display
        if self.splitter.frame_pixmap is None:
            if self.main_window.video_feed_display.text() == "":  # There is currently an image being displayed
                self.main_window.video_feed_display.setText(self.main_window.video_feed_default_text)
        else:
            self.main_window.video_feed_display.setPixmap(self.splitter.frame_pixmap)

        # Split image
        if self.last_split_image_index is None or self.last_split_image_index != self.splitter.current_split_index:
            if self.splitter.current_split_index is None:
                self.main_window.split_image_display.setText(self.main_window.split_image_default_text)
            else:
                self.main_window.split_image_display.setPixmap(self.splitter.splits[self.splitter.splits.current_split_index].pixmap)

        

    def save_settings(self):
        self.settings_window.setFocus(True)  # Take focus off widgets

        fps = self.settings_window.fps_spinbox.value()
        if fps != settings.value("FPS"):
            video_active = self.splitter.capture_thread.is_alive()
            settings.setValue("FPS", fps)
            self.update_ui_timer.setInterval(1000 // fps)
            self.splitter.safe_exit_all_threads()
            if video_active:
                self.splitter.start()

        open_screenshots_value = self.settings_window.open_screenshots_checkbox.checkState()
        if open_screenshots_value == 0:
            open_screenshots = False
        else:
            open_screenshots = True
        if open_screenshots != settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", open_screenshots)

        default_threshold = float(self.settings_window.default_threshold_double_spinbox.value()) / 100
        if default_threshold != settings.value("DEFAULT_THRESHOLD"):
            settings.setValue("DEFAULT_THRESHOLD", default_threshold)
            self.splitter.splits.set_default_threshold()

        ##### FIX THIS
        match_percent_decimals = self.settings_window.match_percent_decimals_spinbox.value()
        if match_percent_decimals != settings.value("MATCH_PERCENT_DECIMALS"):
            settings.setValue("MATCH_PERCENT_DECIMALS", match_percent_decimals)
            # self.settings_window.set_match_percent_decimals_signal.emit()

        default_delay = self.settings_window.default_delay_double_spinbox.value()
        if default_delay != settings.value("DEFAULT_DELAY"):
            settings.setValue("DEFAULT_DELAY", default_delay)
            self.splitter.splits.set_default_delay()

        default_pause = self.settings_window.default_pause_double_spinbox.value()
        if default_pause != settings.value("DEFAULT_PAUSE"):
            settings.setValue("DEFAULT_PAUSE", default_pause)
            self.splitter.splits.set_default_pause()

        aspect_ratio = self.settings_window.aspect_ratio_combo_box.currentText()
        if aspect_ratio != settings.value("ASPECT_RATIO"):
            self.settings_window.update_aspect_ratio_start_signal.emit()
            if aspect_ratio == "4:3 (480x360)":
                settings.setValue("ASPECT_RATIO", "4:3 (480x360)")
                settings.setValue("FRAME_WIDTH", 480)
                settings.setValue("FRAME_HEIGHT", 360)
            if aspect_ratio == "4:3 (320x240)":
                settings.setValue("ASPECT_RATIO", "4:3 (320x240)")
                settings.setValue("FRAME_WIDTH", 320)
                settings.setValue("FRAME_HEIGHT", 240)
            if aspect_ratio == "16:9 (512x288)":
                settings.setValue("ASPECT_RATIO", "16:9 (512x288)")
                settings.setValue("FRAME_WIDTH", 512)
                settings.setValue("FRAME_HEIGHT", 288)
            if aspect_ratio == "16:9 (432x243)":
                settings.setValue("ASPECT_RATIO", "16:9 (432x243)")
                settings.setValue("FRAME_WIDTH", 432)
                settings.setValue("FRAME_HEIGHT", 243)
            self.main_window.set_layout(splitter_paused=self.splitter.suspended)

        start_with_video_value = self.settings_window.start_with_video_checkbox.checkState()
        if start_with_video_value == 0:
            start_with_video = False
        else:
            start_with_video = True
        if start_with_video != settings.value("START_WITH_VIDEO"):
            settings.setValue("START_WITH_VIDEO", start_with_video)

        ##### MAKE SURE THIS SETS THE CSS CORRECTLY
        theme = self.settings_window.theme_combo_box.currentText()
        if theme != settings.value("THEME"):
            if theme == "dark":
                settings.setValue("THEME", "dark")
            elif theme == "light":
                settings.setValue("THEME", "light")

        hotkey_changed = False
        hotkey_text, hotkey_key_sequence = self.settings_window.start_split_hotkey_line_edit.text(), self.settings_window.start_split_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("SPLIT_HOTKEY_TEXT"):
            settings.setValue("SPLIT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SPLIT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.reset_hotkey_line_edit.text(), self.settings_window.reset_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("RESET_HOTKEY_TEXT"):
            settings.setValue("RESET_HOTKEY_TEXT", hotkey_text)
            settings.setValue("RESET_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.pause_hotkey_line_edit.text(), self.settings_window.pause_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("PAUSE_HOTKEY_TEXT"):
            settings.setValue("PAUSE_HOTKEY_TEXT", hotkey_text)
            settings.setValue("PAUSE_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.undo_split_hotkey_line_edit.text(), self.settings_window.undo_split_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("UNDO_HOTKEY_TEXT"):
            settings.setValue("UNDO_HOTKEY_TEXT", hotkey_text)
            settings.setValue("UNDO_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.skip_split_hotkey_line_edit.text(), self.settings_window.skip_split_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("SKIP_HOTKEY_TEXT"):
            settings.setValue("SKIP_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SKIP_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.previous_split_hotkey_line_edit.text(), self.settings_window.previous_split_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("PREVIOUS_HOTKEY_TEXT"):
            settings.setValue("PREVIOUS_HOTKEY_TEXT", hotkey_text)
            settings.setValue("PREVIOUS_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.next_split_hotkey_line_edit.text(), self.settings_window.next_split_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("NEXT_HOTKEY_TEXT"):
            settings.setValue("NEXT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("NEXT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.screenshot_hotkey_line_edit.text(), self.settings_window.screenshot_hotkey_line_edit.key_sequence
        if hotkey_text != settings.value("SCREENSHOT_HOTKEY_TEXT"):
            settings.setValue("SCREENSHOT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SCREENSHOT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        if hotkey_changed:
            self.main_window.set_ui_shortcut_keybindings()


    ## Handle changing buttons and stuff in the pilgrim_autosplitter.py's timer. maintain a bunch of local variables whose
    ## only purpose is to activate the methods that update buttons and labels

























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
