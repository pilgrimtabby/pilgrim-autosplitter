from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import QFileDialog

from splitter.split_dir import SplitDir
from splitter.splitter import Splitter
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow
from ui.ui_style import UIStyle
from utils import settings


class UIController:
    def __init__(self, splitter) -> None:
        self.splitter = splitter
        self.style = UIStyle()
        self.main_window = UIMainWindow(self.style)
        self.settings_window = UISettingsWindow(self.style)

        self._poller = self._Poller(self.splitter, self.main_window, self.settings_window)

        #######################
        #                     #
        # Main Window Signals #
        #                     #
        #######################

        # Image directory button clicked
        self.main_window.split_directory_button.clicked.connect(self.set_image_directory_path)

        # Minimal view / full view button clicked
        self.main_window.minimal_view_button.clicked.connect(lambda: settings.setValue("SHOW_MIN_VIEW", not settings.value("SHOW_MIN_VIEW")))
        self.main_window.minimal_view_button.clicked.connect(lambda: self.main_window.set_layout(splitter_paused=self.splitter.suspended))

        # Next source button clicked
        self.main_window.next_source_button.clicked.connect(self.splitter.next_capture_source)
        self.main_window.next_source_button.clicked.connect(self.splitter.safe_exit_all_threads)  ## Not actually exiting splitter thread
        self.main_window.next_source_button.clicked.connect(self.splitter.start)  ### Make sure splitter thread only starts if video thread has started!!

        # Screenshot button clicked
        self.main_window.screenshot_button.clicked.connect(self.splitter.take_screenshot)

        # Reload video button clicked
        self.main_window.reload_video_button.clicked.connect(self.splitter.safe_exit_all_threads)
        self.main_window.reload_video_button.clicked.connect(self.splitter.start)

        # Pause comparison / unpause comparison button clicked
        self.main_window.pause_comparison_button.clicked.connect(self.splitter.toggle_suspended)
        self.main_window.pause_comparison_button.clicked.connect(lambda: self.main_window.toggle_pause_comparison_button_text(self.splitter.suspended))

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
        ##### Send reset keyboard shortcut

        # Reset splits keyboard shortcut entered
        self.main_window.reset_shortcut.activated.connect(self.splitter.splits.reset_split_images)

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
        self.settings_window.save_button.clicked.connect(self.settings_window.close)

        ##########################
        #                        #
        # Poll splitter for info #
        #                        #
        ##########################

        self.update_ui_timer = QTimer()
        self.update_ui_timer.setInterval(1000 // settings.value("FPS"))
        self.update_ui_timer.timeout.connect(self._poller.update_ui)
        self.update_ui_timer.start()

    # Called when select splits directory button pressed
    def set_image_directory_path(self):
        self.update_ui_timer.stop()
        path = QFileDialog.getExistingDirectory(self.main_window, "Select splits folder", settings.value("LAST_IMAGE_DIR"))
        if path != "" and path != settings.value("LAST_IMAGE_DIR"):
            settings.setValue("LAST_IMAGE_DIR", path)
            self.main_window.set_split_directory_line_edit_text()

            video_active = self.splitter.capture_thread.is_alive()
            self.splitter.safe_exit_all_threads
            self.splitter.splits = SplitDir()
            if video_active:
                self.splitter.start()

            self._current_split_image_index = -1
        self.update_ui_timer.start()

    # Called when settings window save button pressed
    def save_settings(self):
        self.settings_window.setFocus(True)  # Take focus off widgets

        fps = self.settings_window.fps_spinbox.value()
        if fps != settings.value("FPS"):
            settings.setValue("FPS", fps)
            self.splitter.interval = 1 / fps  # Update the value for the current Splitter instance

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

        match_percent_decimals = self.settings_window.match_percent_decimals_spinbox.value()
        if match_percent_decimals != settings.value("MATCH_PERCENT_DECIMALS"):
            settings.setValue("MATCH_PERCENT_DECIMALS", match_percent_decimals)
            # Reset saved match percent values in poller
            self._poller.current_current_match_percent = -1
            self._poller.current_highest_match_percent = -1
            self._poller.current_threshold_match_percent = -1

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
            # self._poller.current_split_image_index = -1 # Force ui to display new image

        start_with_video_value = self.settings_window.start_with_video_checkbox.checkState()
        if start_with_video_value == 0:
            start_with_video = False
        else:
            start_with_video = True
        if start_with_video != settings.value("START_WITH_VIDEO"):
            settings.setValue("START_WITH_VIDEO", start_with_video)

        theme = self.settings_window.theme_combo_box.currentText()
        if theme != settings.value("THEME"):
            if theme == "dark":
                settings.setValue("THEME", "dark")
            elif theme == "light":
                settings.setValue("THEME", "light")
            self.main_window.style_sheet.set_style(self.main_window)

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

    class _Poller:
        def __init__(self, splitter: Splitter, main_window: UIMainWindow, settings_window: UISettingsWindow) -> None:
            self._splitter = splitter
            self._main_window = main_window
            self._settings_windowsettings_window = settings_window
            
            self._current_split_image_index = 0  # This value is set to -1 if a new split_dir instance is created by ui_controller.set_image_directory_path, or if the aspect ratio is changed
            self._current_split_loop = 0
            self._current_total_loops = 0
            self._current_current_match_percent = 0
            self._current_highest_match_percent = 0
            self._current_threshold_match_percent = 0
            self._current_split_list_empty = False
            self._current_video_active = False
            self._current_splitter_delaying = False

            # Set these True so their respective methods are called on first update_ui call
            self._current_split_image_index_changed = True
            self._current_split_loop_changed = True
            self._current_total_loops_changed = True
            self._current_current_match_percent_changed = True
            self._current_highest_match_percent_changed = True
            self._current_threshold_match_percent = True
            self._current_split_list_empty_changed = True
            self._current_video_active_changed = True
            self._current_splitter_delaying_changed = True

        def update_ui(self) -> None:
            self._update_video_display()
            self._update_split_labels()
            self._update_match_percents()
            self._update_buttons_and_hotkeys()

        def _update_video_display(self):
            # 
            
            if self._splitter.frame_pixmap is None:
                if self._main_window.video_feed_display.text() == "":  # There is currently an image being displayed
                    self._main_window.video_feed_display.setText(self._main_window.video_feed_default_text)
            else:
                self._main_window.video_feed_display.setPixmap(self._splitter.frame_pixmap)

        def _update_split_labels(self):
            # Split image, split name
            if self._current_split_image_index != self._splitter.splits.current_image_index:
                self._current_split_image_index = self._splitter.splits.current_image_index
                self._current_split_image_index_changed = True

                if self._current_split_image_index is None:
                    self._main_window.split_image_display.setText(self._main_window.split_image_default_text)
                    self._main_window.split_name_label.setText("")
                else:
                    self._main_window.split_image_display.setPixmap(self._splitter.splits.list[self._current_split_image_index].pixmap)
                    print(self._splitter.splits.list[self._current_split_image_index].pixmap)
                    self._main_window.split_name_label.setText(self._splitter.splits.list[self._current_split_image_index].name)

            # Split loop
            # Check if split image's total loops have changed
            if self._current_total_loops != self._splitter.splits.list[self._splitter.splits.current_image_index].loops:
                self._current_total_loops = self._splitter.splits.list[self._splitter.splits.current_image_index].loops
                self._changes_made = True

                if self._current_split_image_index is None:
                    self._main_window.split_image_loop_label.setText("")
                else:
                    if self._current_split_loop != self._splitter.splits.current_loop:
                        self._current_split_loop = self._splitter.splits.current_loop

                    # self._current_split_loop is never None if self._current_split_image_index is not None
                    if self._current_split_loop == 0:
                        self._main_window.split_image_loop_label.setText("Split does not loop")
                    else:
                        self._main_window.split_image_loop_label.setText(f"Loop {self._current_split_loop} of {self._current_total_loops}")

            # Check if split image's current loop has changed
            if self._current_split_loop != self._splitter.splits.current_loop:
                self._current_split_loop = self._splitter.splits.current_loop
                self._changes_made = True

                if self._current_split_loop is None:
                    self._main_window.split_image_loop_label.setText("")
                if self._current_split_loop == 0:
                    self._main_window.split_image_loop_label.setText("Split does not loop")
                else:
                    self._main_window.split_image_loop_label.setText(f"Loop {self._current_split_loop} of {self._current_total_loops}")
        
        def _update_match_percents(self):
            if self._current_split_image_index is None:
                # Set current, highest, threshold blank if there is no split image
                self._main_window.current_match_percent.setText(self._null_match_percent_string())
                self._main_window.highest_match_percent.setText(self._null_match_percent_string())
                self._main_window.threshold_match_percent.setText(self._null_match_percent_string())
    
            else:
                decimals = settings.value("MATCH_PERCENT_DECIMALS")
                # Current match percent
                if self._current_current_match_percent != self._splitter.current_match_percent:
                    self._current_current_match_percent = self._splitter.current_match_percent
                    if self._current_current_match_percent is None:
                        self._main_window.current_match_percent.setText(self._null_match_percent_string())
                    else:
                        self._main_window.current_match_percent.setText(self._formatted_match_percent_string(self._current_current_match_percent, decimals))

                # Highest match percent
                if self._current_highest_match_percent != self._splitter.highest_match_percent:
                    self._current_highest_match_percent = self._splitter.highest_match_percent
                    if self._current_highest_match_percent is None:
                        self._main_window.highest_match_percent.setText(self._null_match_percent_string())
                    else:
                        self._main_window.highest_match_percent.setText(self._formatted_match_percent_string(self._current_highest_match_percent, decimals))

                # Threshold match percent
                if self._current_threshold_match_percent != self._splitter.splits.list[self._splitter.splits.current_image_index].threshold:
                    self._current_threshold_match_percent = self._splitter.splits.list[self._splitter.splits.current_image_index].threshold
                    if self._current_threshold_match_percent is None:
                        self._main_window.threshold_match_percent.setText(self._null_match_percent_string())
                    else:
                        self._main_window.threshold_match_percent.setText(self._formatted_match_percent_string(self._current_threshold_match_percent, decimals))

        def _update_buttons_and_hotkeys(self):
            # Check if this method should be ran through or not
            if self._current_split_list_empty and len(self._splitter.splits.list) > 0 or not self._current_split_list_empty and len(self._splitter.splits.list) == 0:
                self._current_split_list_empty = not self._current_split_list_empty
                self._changes_made = True

            if self._current_video_active and not self._splitter.capture_thread.is_alive() or not self._current_video_active and self._splitter.capture_thread.is_alive():
                self._current_video_active = not self._current_video_active
                self._changes_made = True

            if self._current_splitter_delaying and not self._splitter.delaying or not self._current_splitter_delaying and self._splitter.delaying:
                self._current_splitter_delaying = not self._current_splitter_delaying
                self._changes_made = True

            if self._changes_made:
                self._changes_made = False

                if self._current_split_list_empty:
                    # Disable split, undo, skip, previous, next split, reset, pause / unpause
                    self._main_window.split_shortcut.setEnabled(False)
                    self._main_window.undo_split_button.setEnabled(False)
                    self._main_window.undo_split_shortcut.setEnabled(False)
                    self._main_window.skip_split_button.setEnabled(False)
                    self._main_window.skip_split_shortcut.setEnabled(False)
                    self._main_window.previous_split_button.setEnabled(False)
                    self._main_window.next_split_button.setEnabled(False)
                    self._main_window.reset_splits_button.setEnabled(False)
                    self._main_window.reset_shortcut.setEnabled(False)
                    self._main_window.pause_comparison_button.setEnabled(False)

                    # Enable screenshots if video is on
                    if self._current_video_active:
                        self._main_window.screenshot_button.setEnabled(True)
                    else:
                        self._main_window.screenshot_button.setEnabled(False)

                else:
                    # Enable split and reset
                    self._main_window.split_shortcut.setEnabled(True)
                    self._main_window.reset_splits_button.setEnabled(True)
                    self._main_window.reset_shortcut.setEnabled(True)

                    # Enable screenshots if video is on
                    if self._current_video_active:
                        self._main_window.screenshot_button.setEnabled(True)
                        # Enable pause / unpause if splitter isn't delaying
                        if self._current_splitter_delaying:
                            self._main_window.pause_comparison_button.setEnabled(False)
                        else:
                            self._main_window.pause_comparison_button.setEnabled(True)
                    else:
                        self._main_window.screenshot_button.setEnabled(False)
                        self._main_window.pause_comparison_button.setEnabled(False)

                    # Enable undo and previous if this isn't the first split
                    if self._splitter.splits.current_image_index == 0 and self._splitter.splits.current_loop == 0:
                        self._main_window.undo_split_button.setEnabled(False)
                        self._main_window.undo_split_shortcut.setEnabled(False)
                        self._main_window.previous_split_button.setEnabled(False)
                    else:
                        self._main_window.undo_split_button.setEnabled(True)
                        self._main_window.undo_split_shortcut.setEnabled(True)
                        self._main_window.previous_split_button.setEnabled(True)

                    # Enable skip and next if this isn't the last split
                    if self._splitter.splits.current_image_index == len(self._splitter.splits.list) - 1 and self._splitter.splits.current_loop == self._splitter.splits.list[self._splitter.splits.current_image_index].loops:
                        self._main_window.skip_split_button.setEnabled(False)
                        self._main_window.skip_split_shortcut.setEnabled(False)
                        self._main_window.next_split_button.setEnabled(False)
                    else:
                        self._main_window.skip_split_button.setEnabled(True)
                        self._main_window.skip_split_shortcut.setEnabled(True)
                        self._main_window.next_split_button.setEnabled(True)

        def _null_match_percent_string(self):
            match_percent_string = "--"
            decimals = settings.value("MATCH_PERCENT_DECIMALS")
            if decimals > 0:
                match_percent_string += "."
                while decimals > 0:
                    match_percent_string += "-"
                    decimals -= 1
            return match_percent_string

        def _formatted_match_percent_string(self, match_percent: int, decimals: int) -> str:
            format_string = f"{{:.{decimals}f}}"
            return format_string.format(match_percent * 100)
