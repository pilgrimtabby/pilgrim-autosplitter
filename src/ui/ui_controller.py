import os
import platform
import subprocess
from pathlib import Path

import cv2
from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

import hotkey
import settings
import ui.ui_style_sheet as style_sheet
from splitter.split_dir import SplitDir
from splitter.splitter import Splitter
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow


class UIController:
    def __init__(self, splitter) -> None:
        self.splitter = splitter
        self.settings_window = UISettingsWindow()
        self.main_window = UIMainWindow()
        self._poller = self._Poller(self.splitter, self.main_window)

        self.set_main_window_layout()
        self.set_shortcut_keybindings()

        #######################
        #                     #
        # Main Window Signals #
        #                     #
        #######################

        # Image directory button clicked
        self.main_window.split_directory_button.clicked.connect(self.set_image_directory_path)

        # Minimal view / full view button clicked
        self.main_window.minimal_view_button.clicked.connect(lambda: settings.set_value("SHOW_MIN_VIEW", not settings.get_bool("SHOW_MIN_VIEW")))
        self.main_window.minimal_view_button.clicked.connect(self.set_main_window_layout)

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
        self.update_ui_timer.setInterval(1000 // settings.get_int("FPS"))
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
        self._poller.redraw_split_labels = True
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
            self.set_split_directory_line_edit_text()

            video_active = self.splitter.capture_thread.is_alive()
            self.splitter.safe_exit_all_threads()
            self.splitter.splits = SplitDir()
            if video_active:
                self.splitter.start()

        self.update_ui_timer.start()

    # Called from set_image_directory_path and set_main_window_layout
    def set_split_directory_line_edit_text(self):
        path = settings.get_str("LAST_IMAGE_DIR")
        elided_path = self.main_window.split_directory_line_edit.fontMetrics().elidedText(path, Qt.ElideMiddle, self.main_window.split_directory_line_edit.width())
        self.main_window.split_directory_line_edit.setText(elided_path)        

    # Called in self.__init__ and when save button is pressed in settings window
    def set_shortcut_keybindings(self):
        for shortcut, key_sequence in {
            self.main_window.split_shortcut: settings.get_qkeysequence("SPLIT_HOTKEY_KEY_SEQUENCE"),
            self.main_window.reset_shortcut: settings.get_qkeysequence("RESET_HOTKEY_KEY_SEQUENCE"),
            self.main_window.undo_split_shortcut: settings.get_qkeysequence("UNDO_HOTKEY_KEY_SEQUENCE"),
            self.main_window.skip_split_shortcut: settings.get_qkeysequence("SKIP_HOTKEY_KEY_SEQUENCE"),
            self.main_window.previous_split_shortcut: settings.get_qkeysequence("PREVIOUS_HOTKEY_KEY_SEQUENCE"),
            self.main_window.next_split_shortcut: settings.get_qkeysequence("NEXT_HOTKEY_KEY_SEQUENCE"),
            self.main_window.screenshot_shortcut: settings.get_qkeysequence("SCREENSHOT_HOTKEY_KEY_SEQUENCE"),
        }.items():
            shortcut.setKey(key_sequence)

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
            elif aspect_ratio == "4:3 (320x240)":
                settings.set_value("ASPECT_RATIO", "4:3 (320x240)")
                settings.set_value("FRAME_WIDTH", 320)
                settings.set_value("FRAME_HEIGHT", 240)
            elif aspect_ratio == "16:9 (512x288)":
                settings.set_value("ASPECT_RATIO", "16:9 (512x288)")
                settings.set_value("FRAME_WIDTH", 512)
                settings.set_value("FRAME_HEIGHT", 288)
            elif aspect_ratio == "16:9 (432x243)":
                settings.set_value("ASPECT_RATIO", "16:9 (432x243)")
                settings.set_value("FRAME_WIDTH", 432)
                settings.set_value("FRAME_HEIGHT", 243)
            self.splitter.splits.resize_images()
            self.set_main_window_layout()

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
            self.main_window.set_shortcut_keybindings()

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

    # Called when initializing main_window, when aspect ratio changes, and when min view button is pressed
    def set_main_window_layout(self):
        self._poller.redraw_split_labels = True
        self._get_layout()
        self.set_split_directory_line_edit_text()

    # Called by self.set_main_window_layout
    def _get_layout(self):
        if settings.get_bool("SHOW_MIN_VIEW"):
            self._show_minimal_view()

        else:
            aspect_ratio = settings.get_str("ASPECT_RATIO")
            if aspect_ratio == "4:3 (480x360)":
                self._show_480x360_view()

            elif aspect_ratio == "4:3 (320x240)":
                self._show_320x240_view()

            elif aspect_ratio == "16:9 (512x288)":
                self._show_512x288_view()

            elif aspect_ratio == "16:9 (432x243)":
                self._show_432x243_view()

    # Called by self.set_main_window_layout
    def _show_minimal_view(self):
        self.main_window.previous_split_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 224 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.split_name_label.setGeometry(QRect(92 + self.main_window.LEFT_EDGE_CORRECTION, 214 + self.main_window.TOP_EDGE_CORRECTION, 251, 31))
        self.main_window.split_image_loop_label.setGeometry(QRect(92 + self.main_window.LEFT_EDGE_CORRECTION, 239 + self.main_window.TOP_EDGE_CORRECTION, 251, 31))
        self.main_window.next_split_button.setGeometry(QRect(344 + self.main_window.LEFT_EDGE_CORRECTION, 224 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.minimal_view_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.video_feed_label.setGeometry(QRect(161 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 213, 31))
        self.main_window.pause_comparison_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 121, 31))
        self.main_window.skip_split_button.setGeometry(QRect(125 + self.main_window.LEFT_EDGE_CORRECTION, 350 + self.main_window.TOP_EDGE_CORRECTION, 56, 31))
        self.main_window.undo_split_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 350 + self.main_window.TOP_EDGE_CORRECTION, 56, 31))
        self.main_window.reset_splits_button.setGeometry(QRect(304 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 71, 71))
        self.main_window.current_match_percent_label.setGeometry(QRect(62 + self.main_window.LEFT_EDGE_CORRECTION, 304 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.highest_match_percent_label.setGeometry(QRect(62 + self.main_window.LEFT_EDGE_CORRECTION, 331 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.threshold_match_percent_label.setGeometry(QRect(62 + self.main_window.LEFT_EDGE_CORRECTION, 358 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.current_match_percent.setGeometry(QRect(227 + self.main_window.LEFT_EDGE_CORRECTION, 304 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.highest_match_percent.setGeometry(QRect(227 + self.main_window.LEFT_EDGE_CORRECTION, 331 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.threshold_match_percent.setGeometry(QRect(227 + self.main_window.LEFT_EDGE_CORRECTION, 358 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.current_match_percent_sign.setGeometry(QRect(282 + self.main_window.LEFT_EDGE_CORRECTION, 304 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.highest_match_percent_sign.setGeometry(QRect(282 + self.main_window.LEFT_EDGE_CORRECTION, 331 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.threshold_match_percent_sign.setGeometry(QRect(282 + self.main_window.LEFT_EDGE_CORRECTION, 358 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))

        self._set_nonessential_widgets_visible(False)
        self._set_button_and_label_text(truncate=True)
        self.main_window.setFixedSize(345, 179 + self.main_window.HEIGHT_CORRECTION)

    # Called by self.set_main_window_layout
    def _show_480x360_view(self):
        self.main_window.split_directory_line_edit.setGeometry(QRect(247 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 785, 30))
        self.main_window.video_feed_label.setGeometry(QRect(260 + self.main_window.LEFT_EDGE_CORRECTION, 272 + self.main_window.TOP_EDGE_CORRECTION, 80, 31))
        self.main_window.split_name_label.setGeometry(QRect(584 + self.main_window.LEFT_EDGE_CORRECTION, 255 + self.main_window.TOP_EDGE_CORRECTION, 415, 31))
        self.main_window.split_image_loop_label.setGeometry(QRect(584 + self.main_window.LEFT_EDGE_CORRECTION, 280 + self.main_window.TOP_EDGE_CORRECTION, 415, 31))
        self.main_window.current_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.highest_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 710 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.threshold_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 740 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.current_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.highest_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 710 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.threshold_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 740 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.current_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.highest_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 710 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.threshold_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 740 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.split_directory_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 180, 30))
        self.main_window.minimal_view_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.next_source_button.setGeometry(QRect(440 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.screenshot_button.setGeometry(QRect(340 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 171, 41))
        self.main_window.reload_video_button.setGeometry(QRect(340 + self.main_window.LEFT_EDGE_CORRECTION, 730 + self.main_window.TOP_EDGE_CORRECTION, 171, 41))
        self.main_window.previous_split_button.setGeometry(QRect(550 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.next_split_button.setGeometry(QRect(1000 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.pause_comparison_button.setGeometry(QRect(580 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 191, 41))
        self.main_window.skip_split_button.setGeometry(QRect(680 + self.main_window.LEFT_EDGE_CORRECTION, 730 + self.main_window.TOP_EDGE_CORRECTION, 91, 41))
        self.main_window.undo_split_button.setGeometry(QRect(580 + self.main_window.LEFT_EDGE_CORRECTION, 730 + self.main_window.TOP_EDGE_CORRECTION, 91, 41))
        self.main_window.reset_splits_button.setGeometry(QRect(810 + self.main_window.LEFT_EDGE_CORRECTION, 680 + self.main_window.TOP_EDGE_CORRECTION, 191, 91))
        self.main_window.video_feed_display.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 480, 360))

        split_image_geometry = QRect(550 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 480, 360)
        self.main_window.split_image_display.setGeometry(split_image_geometry)
        self.main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self.main_window.setFixedSize(1002, 570 + self.main_window.HEIGHT_CORRECTION)

    # Called by self.set_main_window_layout
    def _show_320x240_view(self):
        self.main_window.split_directory_line_edit.setGeometry(QRect(247 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 464, 30))
        self.main_window.video_feed_label.setGeometry(QRect(180 + self.main_window.LEFT_EDGE_CORRECTION, 272 + self.main_window.TOP_EDGE_CORRECTION, 80, 31))
        self.main_window.split_name_label.setGeometry(QRect(424 + self.main_window.LEFT_EDGE_CORRECTION, 255 + self.main_window.TOP_EDGE_CORRECTION, 254, 31))
        self.main_window.split_image_loop_label.setGeometry(QRect(424 + self.main_window.LEFT_EDGE_CORRECTION, 280 + self.main_window.TOP_EDGE_CORRECTION, 254, 31))
        self.main_window.current_match_percent_label.setGeometry(QRect(-50 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.highest_match_percent_label.setGeometry(QRect(-50 + self.main_window.LEFT_EDGE_CORRECTION, 590 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.threshold_match_percent_label.setGeometry(QRect(-50 + self.main_window.LEFT_EDGE_CORRECTION, 620 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.current_match_percent.setGeometry(QRect(115 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.highest_match_percent.setGeometry(QRect(115 + self.main_window.LEFT_EDGE_CORRECTION, 590 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.threshold_match_percent.setGeometry(QRect(115 + self.main_window.LEFT_EDGE_CORRECTION, 620 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.current_match_percent_sign.setGeometry(QRect(170 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.highest_match_percent_sign.setGeometry(QRect(170 + self.main_window.LEFT_EDGE_CORRECTION, 590 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.threshold_match_percent_sign.setGeometry(QRect(170 + self.main_window.LEFT_EDGE_CORRECTION, 620 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.split_directory_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 180, 30))
        self.main_window.minimal_view_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.next_source_button.setGeometry(QRect(280 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.screenshot_button.setGeometry(QRect(220 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 131, 41))
        self.main_window.reload_video_button.setGeometry(QRect(220 + self.main_window.LEFT_EDGE_CORRECTION, 610 + self.main_window.TOP_EDGE_CORRECTION, 131, 41))
        self.main_window.previous_split_button.setGeometry(QRect(390 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.next_split_button.setGeometry(QRect(680 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.pause_comparison_button.setGeometry(QRect(420 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 121, 41))
        self.main_window.skip_split_button.setGeometry(QRect(485 + self.main_window.LEFT_EDGE_CORRECTION, 610 + self.main_window.TOP_EDGE_CORRECTION, 56, 41))
        self.main_window.undo_split_button.setGeometry(QRect(420 + self.main_window.LEFT_EDGE_CORRECTION, 610 + self.main_window.TOP_EDGE_CORRECTION, 56, 41))
        self.main_window.reset_splits_button.setGeometry(QRect(560 + self.main_window.LEFT_EDGE_CORRECTION, 560 + self.main_window.TOP_EDGE_CORRECTION, 121, 91))
        self.main_window.video_feed_display.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 320, 240))

        split_image_geometry = QRect(390 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 320, 240)
        self.main_window.split_image_display.setGeometry(split_image_geometry)
        self.main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=True)
        self.main_window.setFixedSize(682, 450 + self.main_window.HEIGHT_CORRECTION)

    # Called by self.set_main_window_layout
    def _show_512x288_view(self):
        self.main_window.split_directory_line_edit.setGeometry(QRect(247 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 848, 30))
        self.main_window.video_feed_label.setGeometry(QRect(276 + self.main_window.LEFT_EDGE_CORRECTION, 272 + self.main_window.TOP_EDGE_CORRECTION, 80, 31))
        self.main_window.split_name_label.setGeometry(QRect(613 + self.main_window.LEFT_EDGE_CORRECTION, 255 + self.main_window.TOP_EDGE_CORRECTION, 450, 31))
        self.main_window.split_image_loop_label.setGeometry(QRect(613 + self.main_window.LEFT_EDGE_CORRECTION, 280 + self.main_window.TOP_EDGE_CORRECTION, 450, 31))
        self.main_window.current_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.highest_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 638 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.threshold_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 668 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.current_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.highest_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 638 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.threshold_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 668 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.current_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.highest_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 638 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.threshold_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 668 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.split_directory_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 180, 30))
        self.main_window.minimal_view_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.next_source_button.setGeometry(QRect(472 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.screenshot_button.setGeometry(QRect(372 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 171, 41))
        self.main_window.reload_video_button.setGeometry(QRect(372 + self.main_window.LEFT_EDGE_CORRECTION, 658 + self.main_window.TOP_EDGE_CORRECTION, 171, 41))
        self.main_window.previous_split_button.setGeometry(QRect(582 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.next_split_button.setGeometry(QRect(1064 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.pause_comparison_button.setGeometry(QRect(612 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 191, 41))
        self.main_window.skip_split_button.setGeometry(QRect(712 + self.main_window.LEFT_EDGE_CORRECTION, 658 + self.main_window.TOP_EDGE_CORRECTION, 91, 41))
        self.main_window.undo_split_button.setGeometry(QRect(612 + self.main_window.LEFT_EDGE_CORRECTION, 658 + self.main_window.TOP_EDGE_CORRECTION, 91, 41))
        self.main_window.reset_splits_button.setGeometry(QRect(874 + self.main_window.LEFT_EDGE_CORRECTION, 608 + self.main_window.TOP_EDGE_CORRECTION, 191, 91))
        self.main_window.video_feed_display.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 512, 288))

        split_image_geometry = QRect(582 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 512, 288)
        self.main_window.split_image_display.setGeometry(split_image_geometry)
        self.main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self.main_window.setFixedSize(1064, 497 + self.main_window.HEIGHT_CORRECTION)

    # Called by self.set_main_window_layout
    def _show_432x243_view(self):
        self.main_window.split_directory_line_edit.setGeometry(QRect(247 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 688, 30))
        self.main_window.video_feed_label.setGeometry(QRect(161 + self.main_window.LEFT_EDGE_CORRECTION, 272 + self.main_window.TOP_EDGE_CORRECTION, 231, 31))
        self.main_window.split_name_label.setGeometry(QRect(534 + self.main_window.LEFT_EDGE_CORRECTION, 255 + self.main_window.TOP_EDGE_CORRECTION, 371, 31))
        self.main_window.split_image_loop_label.setGeometry(QRect(534 + self.main_window.LEFT_EDGE_CORRECTION, 280 + self.main_window.TOP_EDGE_CORRECTION, 371, 31))
        self.main_window.current_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.highest_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 593 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.threshold_match_percent_label.setGeometry(QRect(80 + self.main_window.LEFT_EDGE_CORRECTION, 623 + self.main_window.TOP_EDGE_CORRECTION, 161, 31))
        self.main_window.current_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.highest_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 593 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.threshold_match_percent.setGeometry(QRect(245 + self.main_window.LEFT_EDGE_CORRECTION, 623 + self.main_window.TOP_EDGE_CORRECTION, 46, 31))
        self.main_window.current_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.highest_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 593 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.threshold_match_percent_sign.setGeometry(QRect(300 + self.main_window.LEFT_EDGE_CORRECTION, 623 + self.main_window.TOP_EDGE_CORRECTION, 21, 31))
        self.main_window.split_directory_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 225 + self.main_window.TOP_EDGE_CORRECTION, 180, 30))
        self.main_window.minimal_view_button.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.next_source_button.setGeometry(QRect(392 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 100, 31))
        self.main_window.screenshot_button.setGeometry(QRect(332 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 131, 41))
        self.main_window.reload_video_button.setGeometry(QRect(332 + self.main_window.LEFT_EDGE_CORRECTION, 613 + self.main_window.TOP_EDGE_CORRECTION, 131, 41))
        self.main_window.previous_split_button.setGeometry(QRect(502 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.next_split_button.setGeometry(QRect(904 + self.main_window.LEFT_EDGE_CORRECTION, 270 + self.main_window.TOP_EDGE_CORRECTION, 31, 31))
        self.main_window.pause_comparison_button.setGeometry(QRect(532 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 181, 41))
        self.main_window.skip_split_button.setGeometry(QRect(627 + self.main_window.LEFT_EDGE_CORRECTION, 613 + self.main_window.TOP_EDGE_CORRECTION, 86, 41))
        self.main_window.undo_split_button.setGeometry(QRect(532 + self.main_window.LEFT_EDGE_CORRECTION, 613 + self.main_window.TOP_EDGE_CORRECTION, 86, 41))
        self.main_window.reset_splits_button.setGeometry(QRect(724 + self.main_window.LEFT_EDGE_CORRECTION, 563 + self.main_window.TOP_EDGE_CORRECTION, 181, 91))
        self.main_window.video_feed_display.setGeometry(QRect(60 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 432, 243))

        split_image_geometry = QRect(502 + self.main_window.LEFT_EDGE_CORRECTION, 310 + self.main_window.TOP_EDGE_CORRECTION, 432, 243)
        self.main_window.split_image_display.setGeometry(split_image_geometry)
        self.main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self.main_window.setFixedSize(904, 452 + self.main_window.HEIGHT_CORRECTION)

    # Called by the above 5 methods
    def _set_button_and_label_text(self, truncate: bool):
        if settings.get_bool("SHOW_MIN_VIEW"):
            self.main_window.minimal_view_button.setText("Full view")
        else:
            self.main_window.minimal_view_button.setText("Minimal view")

        if truncate:
            self.main_window.screenshot_button.setText("Screenshot")
            self.main_window.current_match_percent_label.setText("Sim:")
            self.main_window.highest_match_percent_label.setText("High:")
            self.main_window.threshold_match_percent_label.setText("Thr:")
            if self.splitter.suspended:
                self.main_window.pause_comparison_button.setText(self.main_window.pause_comparison_button_unpause_text_truncated)
            else:
                self.main_window.pause_comparison_button.setText(self.main_window.pause_comparison_button_pause_text_truncated)
            self.main_window.undo_split_button.setText("Undo")
            self.main_window.skip_split_button.setText("Skip")
            self.main_window.reset_splits_button.setText("Reset")

        else:
            self.main_window.screenshot_button.setText("Take screenshot")
            self.main_window.current_match_percent_label.setText("Similarity to split image:")
            self.main_window.highest_match_percent_label.setText("Highest similarity so far:")
            self.main_window.threshold_match_percent_label.setText("Threshold similarity:")
            if self.splitter.suspended:
                self.main_window.pause_comparison_button.setText(self.main_window.pause_comparison_button_unpause_text_default)
            else:
                self.main_window.pause_comparison_button.setText(self.main_window.pause_comparison_button_pause_text_default)
            self.main_window.undo_split_button.setText("Undo split")
            self.main_window.skip_split_button.setText("Skip split")
            self.main_window.reset_splits_button.setText("Reset run")

    # Called by the above 5 methods
    def _set_nonessential_widgets_visible(self, visible):
        self.main_window.split_directory_line_edit.setVisible(visible)
        self.main_window.split_directory_button.setVisible(visible)
        self.main_window.next_source_button.setVisible(visible)
        self.main_window.screenshot_button.setVisible(visible)
        self.main_window.reload_video_button.setVisible(visible)
        self.main_window.video_feed_display.setVisible(visible)
        self.main_window.split_image_display.setVisible(visible)
        self.main_window.minimal_view_no_splits_label.setVisible(not visible)  # Only display when the other widgets are hidden

    class _Poller:
        def __init__(self, splitter: Splitter, main_window: UIMainWindow) -> None:
            self._splitter = splitter
            self._main_window = main_window

            self._most_recent_split_index = None
            self._most_recent_loop = None
            self._most_recent_match_percent_decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
            self._most_recent_match_percent_format_string = f"{{:.{self._most_recent_match_percent_decimals}f}}"
            self._most_recent_match_percent_null_string = self._null_match_percent_string()

            self.redraw_split_labels = True  # This flag is only used to reset the split image in special circumstances

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

            elif current_image_index is not None and (current_image_index != self._most_recent_split_index or self._splitter.splits.current_loop != self._most_recent_loop) or self.redraw_split_labels:  # Split image loaded that is either different from most recent one or on a different loop
                self._most_recent_split_index = current_image_index
                self._most_recent_loop = self._splitter.splits.current_loop

                self.redraw_split_labels = False
    
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
