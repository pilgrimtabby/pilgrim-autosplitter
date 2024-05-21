import os
from pathlib import Path
import platform
import subprocess
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPixmap
import cv2

from splitter.split_dir import SplitDir
from splitter.splitter import Splitter
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow
import ui.ui_style_sheet as style_sheet
import settings
import hotkey


class UIController:
    def __init__(self, splitter) -> None:
        self.splitter = splitter
        self.main_window = UIMainWindow()
        self.settings_window = UISettingsWindow()
        self._poller = self._Poller(self.splitter, self.main_window)

        #######################
        #                     #
        # Main Window Signals #
        #                     #
        #######################

        # Image directory button clicked
        self.main_window.split_directory_button.clicked.connect(self.set_image_directory_path)

        # Minimal view / full view button clicked
        self.main_window.minimal_view_button.clicked.connect(lambda: settings.set_value("SHOW_MIN_VIEW", not settings.get_bool("SHOW_MIN_VIEW")))
        self.main_window.minimal_view_button.clicked.connect(lambda: self.main_window.set_layout(splitter_paused=self.splitter.suspended))
        self.main_window.minimal_view_button.clicked.connect(lambda: setattr(self._poller, "reset_split_image", True))  # So that split name gets elided if necessary

        # Next source button clicked
        self.main_window.next_source_button.clicked.connect(self.splitter.next_capture_source)
        self.main_window.next_source_button.clicked.connect(self.splitter.safe_exit_all_threads)
        self.main_window.next_source_button.clicked.connect(self.splitter.start)

        # Screenshot button clicked
        self.main_window.screenshot_button.clicked.connect(self._take_screenshot)

        # Reload video button clicked
        self.main_window.reload_video_button.clicked.connect(self.splitter.safe_exit_all_threads)
        self.main_window.reload_video_button.clicked.connect(self.splitter.start)

        # Pause comparison / unpause comparison button clicked
        self.main_window.pause_comparison_button.clicked.connect(self.splitter.toggle_suspended)
        self.main_window.pause_comparison_button.clicked.connect(lambda: self.main_window.toggle_pause_comparison_button_text(self.splitter.suspended))

        # Split keyboard shortcut entered
        self.main_window.split_shortcut.activated.connect(self.request_next_split)

        # Undo split button clicked
        self.main_window.undo_split_button.clicked.connect(self.attempt_undo_hotkey)

        # Undo split keyboard shortcut entered
        self.main_window.undo_split_shortcut.activated.connect(self.request_previous_split)

        # Skip split button clicked
        self.main_window.skip_split_button.clicked.connect(self.attempt_skip_hotkey)

        # Skip split keyboard shortcut entered
        self.main_window.skip_split_shortcut.activated.connect(self.request_next_split)

        # Previous split button clicked
        self.main_window.previous_split_button.clicked.connect(self.request_previous_split)

        # Next split button clicked
        self.main_window.next_split_button.clicked.connect(self.request_next_split)

        # Reset button clicked
        self.main_window.reset_splits_button.clicked.connect(self.attempt_reset_hotkey)

        # Reset splits keyboard shortcut entered
        self.main_window.reset_shortcut.activated.connect(self.request_reset)
        self.main_window.reset_shortcut.activated.connect(lambda: setattr(self._poller, "reset_split_image", True))

        # Settings menu bar action triggered
        self.main_window.settings_action.triggered.connect(self.settings_window.exec)

        ###########################
        #                         #
        # Settings window signals #
        #                         #
        ###########################

        # Quit app keyboard shortcut entered (ctrl+q)
        if platform.system() == "Darwin":
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
        self.update_ui_timer.setInterval(1000 // settings.get_int("FPS")) # This takes about 1/10000 of a second on average
        self.update_ui_timer.timeout.connect(self._poller.update_ui)
        self.update_ui_timer.start()

    # Called when undo button pressed
    def attempt_undo_hotkey(self):
        hotkey_set = hotkey.press_hotkey(settings.get_str("UNDO_HOTKEY_TEXT"))
        if not hotkey_set:
            self.request_previous_split()

    # Called when skip button pressed
    def attempt_skip_hotkey(self):
        hotkey_set = hotkey.press_hotkey(settings.get_str("SKIP_HOTKEY_TEXT"))
        if not hotkey_set:
            self.request_next_split()

    # Called when reset button pressed
    def attempt_reset_hotkey(self):
        hotkey_set = hotkey.press_hotkey(settings.get_str("RESET_HOTKEY_TEXT"))
        if not hotkey_set:
            self.request_reset()
            self._poller.reset_split_image = True

    # Called when undo or previous button / hotkey pressed
    def request_previous_split(self):
        if self.splitter.suspended:
            self.splitter.splits.previous_split_image()
        else:
            self.splitter._safe_exit_compare_thread()
            self.splitter.splits.previous_split_image()
            self.splitter._start_compare_thread()

    # Called when next or skip button / hotkey pressed, and when split hotkey pressed
    def request_next_split(self):
        if self.splitter.pressing_hotkey:
            self.splitter.pressing_hotkey = False
            return

        if self.splitter.suspended:
            self.splitter.splits.next_split_image()
        else:
            self.splitter._safe_exit_compare_thread()
            self.splitter.splits.next_split_image()
            self.splitter._start_compare_thread()

    # Called when reset button / hotkey pressed 
    def request_reset(self):
        if self.splitter.suspended:
            self.splitter.splits.reset_split_images()
        else:
            self.splitter._safe_exit_compare_thread()
            self.splitter.splits.reset_split_images()
            self.splitter._start_compare_thread()

    # Called when select splits directory button pressed
    def set_image_directory_path(self):
        self.update_ui_timer.stop()
        path = QFileDialog.getExistingDirectory(self.main_window, "Select splits folder", settings.get_str("LAST_IMAGE_DIR"))
        if path != "" and path != settings.get_str("LAST_IMAGE_DIR"):
            settings.set_value("LAST_IMAGE_DIR", path)
            self.main_window.set_split_directory_line_edit_text()

            video_active = self.splitter.capture_thread.is_alive()
            self.splitter.safe_exit_all_threads()
            self.splitter.splits = SplitDir()
            if video_active:
                self.splitter.start()

        self.update_ui_timer.start()

    # Called when settings window save button pressed
    def save_settings(self):
        self.settings_window.setFocus(True)  # Take focus off widgets

        fps = self.settings_window.fps_spinbox.value()
        if fps != settings.get_int("FPS"):
            settings.set_value("FPS", fps)
            self.splitter.interval = 1 / fps  # Update the value for the current Splitter instance

        open_screenshots_value = self.settings_window.open_screenshots_checkbox.checkState()
        if open_screenshots_value == 0:
            open_screenshots = False
        else:
            open_screenshots = True
        if open_screenshots != settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
            settings.set_value("OPEN_SCREENSHOT_ON_CAPTURE", open_screenshots)

        default_threshold = float(self.settings_window.default_threshold_double_spinbox.value()) / 100
        if default_threshold != settings.get_float("DEFAULT_THRESHOLD"):
            settings.set_value("DEFAULT_THRESHOLD", default_threshold)
            self.splitter.splits.set_default_threshold()

        match_percent_decimals = self.settings_window.match_percent_decimals_spinbox.value()
        if match_percent_decimals != settings.get_int("MATCH_PERCENT_DECIMALS"):
            settings.set_value("MATCH_PERCENT_DECIMALS", match_percent_decimals)

        default_delay = self.settings_window.default_delay_double_spinbox.value()
        if default_delay != settings.get_float("DEFAULT_DELAY"):
            settings.set_value("DEFAULT_DELAY", default_delay)
            self.splitter.splits.set_default_delay()

        default_pause = self.settings_window.default_pause_double_spinbox.value()
        if default_pause != settings.get_float("DEFAULT_PAUSE"):
            settings.set_value("DEFAULT_PAUSE", default_pause)
            self.splitter.splits.set_default_pause()

        aspect_ratio = self.settings_window.aspect_ratio_combo_box.currentText()
        if aspect_ratio != settings.get_str("ASPECT_RATIO"):
            if aspect_ratio == "4:3 (480x360)":
                settings.set_value("ASPECT_RATIO", "4:3 (480x360)")
                settings.set_value("FRAME_WIDTH", 480)
                settings.set_value("FRAME_HEIGHT", 360)
            if aspect_ratio == "4:3 (320x240)":
                settings.set_value("ASPECT_RATIO", "4:3 (320x240)")
                settings.set_value("FRAME_WIDTH", 320)
                settings.set_value("FRAME_HEIGHT", 240)
            if aspect_ratio == "16:9 (512x288)":
                settings.set_value("ASPECT_RATIO", "16:9 (512x288)")
                settings.set_value("FRAME_WIDTH", 512)
                settings.set_value("FRAME_HEIGHT", 288)
            if aspect_ratio == "16:9 (432x243)":
                settings.set_value("ASPECT_RATIO", "16:9 (432x243)")
                settings.set_value("FRAME_WIDTH", 432)
                settings.set_value("FRAME_HEIGHT", 243)
            self.main_window.set_layout(splitter_paused=self.splitter.suspended)
            self.splitter.splits.resize_images()
            # Make sure the resized image shows up in the ui
            self._poller.reset_split_image = True

        start_with_video_value = self.settings_window.start_with_video_checkbox.checkState()
        if start_with_video_value == 0:
            start_with_video = False
        else:
            start_with_video = True
        if start_with_video != settings.get_bool("START_WITH_VIDEO"):
            settings.set_value("START_WITH_VIDEO", start_with_video)

        theme = self.settings_window.theme_combo_box.currentText()
        if theme != settings.get_str("THEME"):
            if theme == "dark":
                settings.set_value("THEME", "dark")
            elif theme == "light":
                settings.set_value("THEME", "light")
            style_sheet.set_style(self.main_window)
            style_sheet.set_style(self.settings_window)

        hotkey_changed = False
        hotkey_text, hotkey_key_sequence = self.settings_window.start_split_hotkey_line_edit.text(), self.settings_window.start_split_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("SPLIT_HOTKEY_TEXT"):
            settings.set_value("SPLIT_HOTKEY_TEXT", hotkey_text)
            settings.set_value("SPLIT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.reset_hotkey_line_edit.text(), self.settings_window.reset_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("RESET_HOTKEY_TEXT"):
            settings.set_value("RESET_HOTKEY_TEXT", hotkey_text)
            settings.set_value("RESET_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.pause_hotkey_line_edit.text(), self.settings_window.pause_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("PAUSE_HOTKEY_TEXT"):
            settings.set_value("PAUSE_HOTKEY_TEXT", hotkey_text)
            settings.set_value("PAUSE_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.undo_split_hotkey_line_edit.text(), self.settings_window.undo_split_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("UNDO_HOTKEY_TEXT"):
            settings.set_value("UNDO_HOTKEY_TEXT", hotkey_text)
            settings.set_value("UNDO_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.skip_split_hotkey_line_edit.text(), self.settings_window.skip_split_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("SKIP_HOTKEY_TEXT"):
            settings.set_value("SKIP_HOTKEY_TEXT", hotkey_text)
            settings.set_value("SKIP_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.previous_split_hotkey_line_edit.text(), self.settings_window.previous_split_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("PREVIOUS_HOTKEY_TEXT"):
            settings.set_value("PREVIOUS_HOTKEY_TEXT", hotkey_text)
            settings.set_value("PREVIOUS_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.next_split_hotkey_line_edit.text(), self.settings_window.next_split_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("NEXT_HOTKEY_TEXT"):
            settings.set_value("NEXT_HOTKEY_TEXT", hotkey_text)
            settings.set_value("NEXT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.settings_window.screenshot_hotkey_line_edit.text(), self.settings_window.screenshot_hotkey_line_edit.key_sequence.toString()
        if hotkey_text != settings.get_str("SCREENSHOT_HOTKEY_TEXT"):
            settings.set_value("SCREENSHOT_HOTKEY_TEXT", hotkey_text)
            settings.set_value("SCREENSHOT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        if hotkey_changed:
            self.main_window.set_ui_shortcut_keybindings()

    # Called by ui_controller when screenshot button pressed/ shortcut entered
    def _take_screenshot(self) -> None:
        frame = self.splitter.frame
        if frame is None:
            self.main_window.screenshot_error_message_box.exec()
            return

        image_dir = settings.get_str("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/{self._get_unique_filename_number(image_dir)}_screenshot.png"
        cv2.imwrite(screenshot_path, frame)

        if Path(screenshot_path).is_file():
            if settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._open_file(screenshot_path)
            else:
                self.main_window.screenshot_success_message_box.setInformativeText(f"Screenshot saved to:\n{screenshot_path}")
                self.main_window.screenshot_success_message_box.setIconPixmap(QPixmap(screenshot_path).scaledToWidth(150))
                self.main_window.screenshot_success_message_box.exec()        
            return
        
        self.main_window.screenshot_error_message_box.exec()
        
    # Called by self._take_screenshot
    def _get_unique_filename_number(self, dir: str):
        file_int = 1
        while True:
            if file_int > 999:
                raise Exception(f"Error: no suitable filename found in {dir}")
            
            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            if Path(f"{dir}/{file_number}_screenshot.png").is_file():
                file_int += 1
            else:
                return file_number

    # Called by self._take_screenshot
    def _open_file(self, path: str):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    class _Poller:
        def __init__(self, splitter: Splitter, main_window: UIMainWindow) -> None:
            self._splitter = splitter
            self._main_window = main_window

            self._most_recent_split_index = None
            self._most_recent_loop = None
            self._most_recent_match_percent_decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
            self._most_recent_match_percent_format_string = f"{{:.{self._most_recent_match_percent_decimals}f}}"
            self._most_recent_match_percent_null_string = self._null_match_percent_string()

            self.reset_split_image = False  # This flag is only used to reset the split image in special circumstances

            self._splitter_suspended = None  # This flag is only used and updated by _set_pause_button_text

            # These flags are only modified in _update_flags and otherwise referenced only in _update_buttons_and_hotkeys
            self._video_active = None
            self._splits_active = None
            self._first_split_active = None
            self._last_split_active = None

        def update_ui(self):
            self._update_labels()
            self._set_pause_button_text()
            something_changed = self._update_flags()
            if something_changed:
                self._update_buttons_and_hotkeys()

        def _update_labels(self) -> None:
            min_view_showing = settings.get_bool("SHOW_MIN_VIEW")

            # Video feed
            if not min_view_showing:
                if self._main_window.video_feed_display.text() == "" and not self._splitter.capture_thread.is_alive():  # Video is down, but video image still showing
                    self._main_window.video_feed_display.setText(self._main_window.video_feed_display_default_text)
                elif self._splitter.frame_pixmap is not None:  # Video is not down
                    self._main_window.video_feed_display.setPixmap(self._splitter.frame_pixmap)

            # Video label
            if min_view_showing:
                if self._splitter.capture_thread.is_alive() and self._main_window.video_feed_label.text() != self._main_window.video_feed_label_live_text_min:  # Video feed is live, but says it is down / is blank
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_live_text_min)
                elif not self._splitter.capture_thread.is_alive() and self._main_window.video_feed_label.text() != self._main_window.video_feed_label_down_text_min:  # Video feed is down, but says it is live / is blank
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_down_text_min)
            else:
                if self._splitter.capture_thread.is_alive() and self._main_window.video_feed_label.text() != self._main_window.video_feed_label_live_text:  # Video feed is live, but the label is wrong / blank
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_live_text)
                elif not self._splitter.capture_thread.is_alive() and self._main_window.video_feed_label.text() != "":  # Video feed is down, but label is filled
                    self._main_window.video_feed_label.setText("")

            # Split image, name, and loop count
            current_image_index = self._splitter.splits.current_image_index
            if current_image_index is None and self._main_window.split_name_label.text() != self._main_window.split_image_default_text:  # No split image loaded, but split image still being displayed
                self._most_recent_split_index = None
                self._most_recent_loop = None

                self._main_window.split_image_display.setText(self._main_window.split_image_default_text)
                self._main_window.split_name_label.setText("")
                self._main_window.split_image_loop_label.setText("")
                self._main_window.minimal_view_no_splits_label.setText(self._main_window.split_image_default_text)
                self._main_window.minimal_view_no_splits_label.raise_()  # Make sure it shows over other split image labels

            elif current_image_index is not None and (current_image_index != self._most_recent_split_index or self._splitter.splits.current_loop != self._most_recent_loop) or self.reset_split_image:  # Split image loaded that is either different from most recent one or on a different loop
                self._most_recent_split_index = current_image_index
                self._most_recent_loop = self._splitter.splits.current_loop

                self.reset_split_image = False
    
                if not min_view_showing:  # Save some cpu when minimal view on
                    self._main_window.split_image_display.setPixmap(self._splitter.splits.list[self._most_recent_split_index].pixmap)

                split_name = self._splitter.splits.list[self._most_recent_split_index].name
                elided_name = self._main_window.split_name_label.fontMetrics().elidedText(split_name, Qt.ElideRight, self._main_window.split_name_label.width())
                self._main_window.split_name_label.setText(elided_name)
                self._main_window.minimal_view_no_splits_label.setText("")
                self._main_window.minimal_view_no_splits_label.lower()  # Make sure it is hidden under other split image labels

                current_total_loops = self._splitter.splits.list[self._most_recent_split_index].loops
                if current_total_loops == 0:
                    self._main_window.split_image_loop_label.setText("Split does not loop")
                else:
                    self._main_window.split_image_loop_label.setText(f"Loop {self._splitter.splits.current_loop} of {current_total_loops}")
        
            # Split image overlay
            if self._splitter.delaying and self._splitter.delay_remaining is not None:
                self._main_window.split_image_overlay.setVisible(True)
                self._main_window.split_image_overlay.setText("Splitting in {amount:.1f} s".format(amount=self._splitter.delay_remaining))
            elif self._splitter.suspended and self._splitter.suspend_remaining is not None:
                self._main_window.split_image_overlay.setVisible(True)
                self._main_window.split_image_overlay.setText("Paused for next {amount:.1f} s".format(amount=self._splitter.suspend_remaining))
            elif self._main_window.split_image_overlay.text() != "":
                self._main_window.split_image_overlay.setVisible(False)
                self._main_window.split_image_overlay.setText("")

            # Match percent labels
            decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
            if self._most_recent_match_percent_decimals != decimals:
                self._most_recent_match_percent_decimals = decimals
                self._most_recent_match_percent_format_string = f"{{:.{self._most_recent_match_percent_decimals}f}}"
                self._most_recent_match_percent_null_string = self._null_match_percent_string()
            # Current match percent
            if self._splitter.current_match_percent is None and self._main_window.current_match_percent != self._most_recent_match_percent_null_string:  # Match percent is blank, but still is showing a number
                self._main_window.current_match_percent.setText(self._most_recent_match_percent_null_string)
            else:
                self._main_window.current_match_percent.setText(self._most_recent_match_percent_format_string.format(self._splitter.current_match_percent * 100))

            # Highest match percent
            if self._splitter.highest_match_percent is None and self._main_window.highest_match_percent != self._most_recent_match_percent_null_string:  # Match percent is blank, but still is showing a number
                self._main_window.highest_match_percent.setText(self._most_recent_match_percent_null_string)
            else:
                self._main_window.highest_match_percent.setText(self._most_recent_match_percent_format_string.format(self._splitter.highest_match_percent * 100))

            # Threshold match percent
            if self._most_recent_split_index is None and self._main_window.threshold_match_percent != self._most_recent_match_percent_null_string:  # Match percent is blank, but still is showing a number
                self._main_window.threshold_match_percent.setText(self._most_recent_match_percent_null_string)
            else:
                threshold_match_percent = self._splitter.splits.list[self._most_recent_split_index].threshold
                if threshold_match_percent is None and self._main_window.threshold_match_percent != self._most_recent_match_percent_null_string:  # Match percent is blank, but still is showing a number
                    self._main_window.threshold_match_percent.setText(self._most_recent_match_percent_null_string)
                else:
                    self._main_window.threshold_match_percent.setText(self._most_recent_match_percent_format_string.format(threshold_match_percent * 100))

        def _update_flags(self):
            flag_changed = False

            if self._video_active != self._splitter.capture_thread.is_alive():
                self._video_active = self._splitter.capture_thread.is_alive()
                flag_changed = True

            if self._most_recent_split_index is None:
                if self._splits_active is not False:  # Explicitly say "is not True", "is not False" on these last three flags so we can catch None values from __init__()
                    self._splits_active = False
                    flag_changed = True
            else:
                if self._splits_active is not True:
                    self._splits_active = True
                    flag_changed = True
        
            if self._most_recent_split_index == 0 and self._splitter.splits.current_loop == 0:  # First split image, first loop
                if self._first_split_active is not True:
                    self._first_split_active = True
                    flag_changed = True
            else:
                if self._first_split_active is not False:
                    self._first_split_active = False
                    flag_changed = True

            # Image list isn't active, last split image, last loop of that image
            if self._splits_active and self._most_recent_split_index == len(self._splitter.splits.list) - 1 and self._splitter.splits.current_loop == self._splitter.splits.list[self._most_recent_split_index].loops:
                if self._last_split_active is not True:
                    self._last_split_active = True
                    flag_changed = True
            else:
                if self._last_split_active is not False:
                    self._last_split_active = False
                    flag_changed = True

            return flag_changed

        def _set_pause_button_text(self):
            if self._splitter_suspended != self._splitter.suspended:  # This will catch the None from __init__()
                self._splitter_suspended = self._splitter.suspended
                self._main_window.toggle_pause_comparison_button_text(self._splitter_suspended)

        def _update_buttons_and_hotkeys(self):
            if self._splits_active:
                # Enable split and reset
                self._main_window.split_shortcut.setEnabled(True)
                self._main_window.reset_splits_button.setEnabled(True)
                self._main_window.reset_shortcut.setEnabled(True)

                # Enable screenshots if video is on
                if self._video_active:
                    self._main_window.screenshot_button.setEnabled(True)
                    self._main_window.pause_comparison_button.setEnabled(True)
                else:
                    self._main_window.screenshot_button.setEnabled(False)
                    self._main_window.pause_comparison_button.setEnabled(False)

                # Enable undo and previous if this isn't the first split
                if self._first_split_active:
                    self._main_window.undo_split_button.setEnabled(False)
                    self._main_window.undo_split_shortcut.setEnabled(False)
                    self._main_window.previous_split_button.setEnabled(False)
                else:
                    self._main_window.undo_split_button.setEnabled(True)
                    self._main_window.undo_split_shortcut.setEnabled(True)
                    self._main_window.previous_split_button.setEnabled(True)

                # Enable skip and next if this isn't the last split
                if self._last_split_active:
                    self._main_window.skip_split_button.setEnabled(False)
                    self._main_window.skip_split_shortcut.setEnabled(False)
                    self._main_window.next_split_button.setEnabled(False)
                else:
                    self._main_window.skip_split_button.setEnabled(True)
                    self._main_window.skip_split_shortcut.setEnabled(True)
                    self._main_window.next_split_button.setEnabled(True)

            else:
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
                if self._video_active:
                    self._main_window.screenshot_button.setEnabled(True)
                else:
                    self._main_window.screenshot_button.setEnabled(False)


        def _null_match_percent_string(self):
            match_percent_string = "--"
            decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
            if decimals > 0:
                match_percent_string += "."
                while decimals > 0:
                    match_percent_string += "-"
                    decimals -= 1
            return match_percent_string

        def _formatted_match_percent_string(self, match_percent: int, decimals: int) -> str:
            format_string = f"{{:.{decimals}f}}"
            return format_string.format(match_percent * 100)
