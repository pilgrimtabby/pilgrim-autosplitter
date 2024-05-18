import os
from pathlib import Path
import platform
import subprocess
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPixmap
import cv2

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

        self._poller = self._Poller(self.splitter, self.main_window)

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
        self.main_window.split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.split_shortcut.activated.connect(self.splitter.splits.next_split_image)

        # Undo split button clicked
        self.main_window.undo_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.undo_split_button.clicked.connect(self.splitter.splits.previous_split_image)
        ##### send undo button keystroke

        # Undo split keyboard shortcut entered
        self.main_window.undo_split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.undo_split_shortcut.activated.connect(self.splitter.splits.previous_split_image)

        # Skip split button clicked
        self.main_window.skip_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.skip_split_button.clicked.connect(self.splitter.splits.next_split_image)
        ##### send skip button keystroke

        # Skip split keyboard shortcut entered
        self.main_window.skip_split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.skip_split_shortcut.activated.connect(self.splitter.splits.next_split_image)

        # Previous split button clicked
        self.main_window.previous_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.previous_split_button.clicked.connect(self.splitter.splits.previous_split_image)

        # Next split button clicked
        self.main_window.next_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.next_split_button.clicked.connect(self.splitter.splits.next_split_image)

        # Reset button clicked
        self.main_window.reset_splits_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
        self.main_window.reset_splits_button.clicked.connect(self.splitter.splits.reset_split_images)
        ##### Send reset keyboard shortcut

        # Reset splits keyboard shortcut entered
        self.main_window.reset_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
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
        self.update_ui_timer.setInterval(1000 // settings.value("FPS")) # This takes about 1/10000 of a second on average
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
            self.splitter.safe_exit_all_threads()
            self.splitter.splits = SplitDir()
            if video_active:
                self.splitter.start()

            # Reconnect signals to new SplitDir instance
            self.main_window.split_shortcut.activated.disconnect()
            self.main_window.undo_split_button.clicked.disconnect()
            self.main_window.undo_split_shortcut.activated.disconnect()
            self.main_window.skip_split_button.clicked.disconnect()
            self.main_window.skip_split_shortcut.activated.disconnect()
            self.main_window.previous_split_button.clicked.disconnect()
            self.main_window.next_split_button.clicked.disconnect()
            self.main_window.reset_splits_button.clicked.disconnect()
            self.main_window.reset_shortcut.activated.disconnect()

            self.main_window.split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.split_shortcut.activated.connect(self.splitter.splits.next_split_image)
            self.main_window.undo_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.undo_split_button.clicked.connect(self.splitter.splits.previous_split_image)
            self.main_window.undo_split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.undo_split_shortcut.activated.connect(self.splitter.splits.previous_split_image)
            self.main_window.skip_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.skip_split_button.clicked.connect(self.splitter.splits.next_split_image)
            self.main_window.skip_split_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.skip_split_shortcut.activated.connect(self.splitter.splits.next_split_image)
            self.main_window.previous_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.previous_split_button.clicked.connect(self.splitter.splits.previous_split_image)
            self.main_window.next_split_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.next_split_button.clicked.connect(self.splitter.splits.next_split_image)
            self.main_window.reset_splits_button.clicked.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.reset_splits_button.clicked.connect(self.splitter.splits.reset_split_images)
            self.main_window.reset_shortcut.activated.connect(lambda: self.splitter.start_reset_compare_stats_thread(self.splitter.splits.current_image_index))
            self.main_window.reset_shortcut.activated.connect(self.splitter.splits.reset_split_images)

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
            self.splitter.splits.resize_images()

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

    # Called by ui_controller when screenshot button pressed/ shortcut entered
    def _take_screenshot(self) -> None:
        frame = self.splitter.frame
        if frame is None:
            self.main_window.screenshot_error_message_box.exec()
            return

        image_dir = settings.value("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")

        screenshot_path = f"{image_dir}/{self._get_unique_filename_number(image_dir)}_screenshot.png"
        cv2.imwrite(screenshot_path, frame)

        if Path(screenshot_path).is_file():
            if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
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
            

        def update_ui(self):
            self._update_labels()
            self._update_buttons_and_hotkeys()

        def _update_labels(self) -> None:
            current_image_index = self._splitter.splits.current_image_index

            # Video feed
            if not settings.value("SHOW_MIN_VIEW"):  # Save some cpu when minimal view on
                if self._splitter.frame_pixmap is None:
                    self._main_window.video_feed_display.setText(self._main_window.video_feed_display_default_text)
                else:
                    self._main_window.video_feed_display.setPixmap(self._splitter.frame_pixmap)

            # Video label
            if settings.value("SHOW_MIN_VIEW"):
                if self._splitter.capture_thread.is_alive():
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_live_text_min)
                else:
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_down_text_min)
            else:
                if self._splitter.capture_thread.is_alive():
                    self._main_window.video_feed_label.setText(self._main_window.video_feed_label_live_text)
                else:
                    self._main_window.video_feed_label.setText("")

            # Split image, name, and loop count
            if current_image_index is None:
                self._main_window.split_image_display.setText(self._main_window.split_image_default_text)
                self._main_window.split_name_label.setText("")
                self._main_window.split_image_loop_label.setText("")
                self._main_window.minimal_view_no_splits_label.setText(self._main_window.split_image_default_text)
                self._main_window.minimal_view_no_splits_label.raise_()  # Make sure it shows over other split image labels
            else:
                if not settings.value("SHOW_MIN_VIEW"):  # Save some cpu when minimal view on
                    self._main_window.split_image_display.setPixmap(self._splitter.splits.list[current_image_index].pixmap)
                self._main_window.split_name_label.setText(self._splitter.splits.list[current_image_index].name)
                self._main_window.minimal_view_no_splits_label.setText("")
                self._main_window.minimal_view_no_splits_label.lower()  # Make sure it is hidden under other split image labels

                current_total_loops = self._splitter.splits.list[current_image_index].loops
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
            else:
                self._main_window.split_image_overlay.setVisible(False)

            # Match percent labels
            decimals = settings.value("MATCH_PERCENT_DECIMALS")
            # Current match percent
            if self._splitter.current_match_percent is None:
                self._main_window.current_match_percent.setText(self._null_match_percent_string())
            else:
                self._main_window.current_match_percent.setText(self._formatted_match_percent_string(self._splitter.current_match_percent, decimals))

            # Highest match percent
            if self._splitter.highest_match_percent is None:
                self._main_window.highest_match_percent.setText(self._null_match_percent_string())
            else:
                self._main_window.highest_match_percent.setText(self._formatted_match_percent_string(self._splitter.highest_match_percent, decimals))

            # Threshold match percent
            if current_image_index is None:
                self._main_window.threshold_match_percent.setText(self._null_match_percent_string())
            else:
                threshold_match_percent = self._splitter.splits.list[current_image_index].threshold
                if threshold_match_percent is None:
                    self._main_window.threshold_match_percent.setText(self._null_match_percent_string())
                else:
                    self._main_window.threshold_match_percent.setText(self._formatted_match_percent_string(threshold_match_percent, decimals))

        def _update_buttons_and_hotkeys(self):
            current_image_index = self._splitter.splits.current_image_index
            self._main_window.toggle_pause_comparison_button_text(self._splitter.suspended)

            if len(self._splitter.splits.list) == 0:
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
                if self._splitter.capture_thread.is_alive():
                    self._main_window.screenshot_button.setEnabled(True)
                else:
                    self._main_window.screenshot_button.setEnabled(False)

            else:
                # Enable split and reset
                self._main_window.split_shortcut.setEnabled(True)
                self._main_window.reset_splits_button.setEnabled(True)
                self._main_window.reset_shortcut.setEnabled(True)

                # Enable screenshots if video is on
                if self._splitter.capture_thread.is_alive():
                    self._main_window.screenshot_button.setEnabled(True)
                    # Enable pause / unpause if splitter isn't delaying
                    if self._splitter.delaying:
                        self._main_window.pause_comparison_button.setEnabled(False)
                    else:
                        self._main_window.pause_comparison_button.setEnabled(True)
                else:
                    self._main_window.screenshot_button.setEnabled(False)
                    self._main_window.pause_comparison_button.setEnabled(False)

                # Enable undo and previous if this isn't the first split
                if (current_image_index is None or current_image_index == 0) and self._splitter.splits.current_loop == 0:
                    self._main_window.undo_split_button.setEnabled(False)
                    self._main_window.undo_split_shortcut.setEnabled(False)
                    self._main_window.previous_split_button.setEnabled(False)
                else:
                    self._main_window.undo_split_button.setEnabled(True)
                    self._main_window.undo_split_shortcut.setEnabled(True)
                    self._main_window.previous_split_button.setEnabled(True)

                # Enable skip and next if this isn't the last split
                if current_image_index is None or current_image_index == len(self._splitter.splits.list) - 1 and self._splitter.splits.current_loop == self._splitter.splits.list[current_image_index].loops:
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
