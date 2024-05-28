# Copyright (c) 2024 pilgrim_tabby
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Manage the passing of information from the splitter to the UI, and from user
input to the UI and the splitter.
"""


import os
import platform
import subprocess
import time
import webbrowser
from pathlib import Path

import cv2
from pynput import keyboard
from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog

import settings
import ui.ui_style_sheet as style_sheet
from splitter.splitter import Splitter
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow


class UIController:
    """Manage the passing of information from the splitter to the UI, and from
    user input to the UI and the splitter.

    Perhaps the most important class method is _update_ui, which is ran once
    per frame using a QTimer. This method updates the UI and handles all user
    inputs.

    UIController has no public attributes, as it is meant to operate after
    initialization without further input. For details about each attribute,
    see method documentation.
    """

    def __init__(self, application: QApplication, splitter: Splitter) -> None:
        """Initialize the UI, then update it each frame.

        Creates each UI window and then shows the main window. Connects
        pyqtSignals from each UI window to their respective slots. Sets initial
        flags and values used by _update_ui. Starts the hotkey listener. Starts
        _update_ui_timer, which polls user input and splitter output at regular
        intervals.

        Args:
            application (QApplication): The QApplication that the program is
                based on.
            splitter (Splitter): The splitter capturing video and comparing
                video to splits.
        """
        # Initialize the UI
        self._application = application
        self._splitter = splitter
        self._main_window = UIMainWindow()
        self._settings_window = UISettingsWindow()

        theme = settings.get_str("THEME")
        style_sheet.set_style(self._main_window, theme)
        style_sheet.set_style(self._settings_window, theme)

        ############################
        #                          #
        # _update_ui Values, Flags #
        #                          #
        ############################

        # Store most recent values based on splitter state
        self._most_recent_split_index = None
        self._most_recent_loop = None
        self._most_recent_match_percent_decimals = settings.get_int(
            "MATCH_PERCENT_DECIMALS"
        )
        self._most_recent_match_percent_format_string = (
            f"{{:.{self._most_recent_match_percent_decimals}f}}"
        )
        self._most_recent_match_percent_null_string = self._null_match_percent_string()

        # Tell _update_ui to update split labels
        self._redraw_split_labels = True

        # Determine appropriate pause button text. This should ONLY be used
        # from within the context of update_ui to check whether the splitter's
        # suspended status has changed recently. Other methods should read the
        # value directly from self._splitter.suspended, since that value is
        # always 100% up-to-date.
        self._splitter_suspended = None

        # Enable buttons and hotkeys
        self._video_active = None
        self._splits_active = None
        self._first_split_active = None
        self._last_split_active = None
        self._split_hotkey_enabled = False
        self._reset_hotkey_enabled = False
        self._undo_hotkey_enabled = False
        self._skip_hotkey_enabled = False

        # React to hotkey presses
        self._settings_window_showing = False
        self._split_hotkey_pressed = False
        self._reset_hotkey_pressed = False
        self._undo_hotkey_pressed = False
        self._skip_hotkey_pressed = False
        self._previous_hotkey_pressed = False
        self._next_hotkey_pressed = False
        self._screenshot_hotkey_pressed = False
        self._toggle_hotkeys_hotkey_pressed = False

        ######################
        #                    #
        # Main Window Config #
        #                    #
        ######################

        # Set layout
        self._set_main_window_layout()

        # Split directory button
        self._main_window.split_directory_button.clicked.connect(
            self._set_image_directory_path
        )

        # Minimal view / full view button
        self._main_window.minimal_view_button.clicked.connect(
            lambda: settings.set_value(
                "SHOW_MIN_VIEW", not settings.get_bool("SHOW_MIN_VIEW")
            )
        )
        self._main_window.minimal_view_button.clicked.connect(
            self._set_main_window_layout
        )

        # Next source button
        self._main_window.next_source_button.clicked.connect(
            self._splitter.set_next_capture_index
        )
        self._main_window.next_source_button.clicked.connect(
            self._splitter.safe_exit_all_threads
        )
        self._main_window.next_source_button.clicked.connect(self._splitter.start)

        # Screenshot button
        self._main_window.screenshot_button.clicked.connect(self._take_screenshot)

        # Reload video button
        self._main_window.reload_video_button.clicked.connect(
            self._splitter.safe_exit_all_threads
        )
        self._main_window.reload_video_button.clicked.connect(self._splitter.start)

        # Pause comparison / unpause comparison button
        self._main_window.pause_comparison_button.clicked.connect(
            self._splitter.toggle_suspended
        )

        # Reset button
        self._main_window.reset_splits_button.clicked.connect(
            self._attempt_reset_hotkey
        )

        # Undo split button
        self._main_window.undo_split_button.clicked.connect(self._attempt_undo_hotkey)

        # Skip split button
        self._main_window.skip_split_button.clicked.connect(self._attempt_skip_hotkey)

        # Previous split button
        self._main_window.previous_split_button.clicked.connect(
            self._request_previous_split
        )

        # Next split button
        self._main_window.next_split_button.clicked.connect(self._request_next_split)

        # Settings window action
        self._main_window.settings_action.triggered.connect(self._exec_settings_window)

        # Help action
        self._main_window.help_action.triggered.connect(
            lambda: webbrowser.open(
                "https://github.com/pilgrimtabby/pilgrim-autosplitter/",
                new=0,
                autoraise=True,
            )
        )

        ##########################
        #                        #
        # Settings Window Config #
        #                        #
        ##########################

        # Close window convenience shortcut
        self._settings_window.close_window_shortcut.activated.connect(
            lambda: self._settings_window.done(0)
        )

        # Cancel button
        self._settings_window.cancel_button.clicked.connect(
            lambda: self._settings_window.done(0)
        )

        # Save button
        self._settings_window.save_button.clicked.connect(self._save_settings)
        self._settings_window.save_button.clicked.connect(
            lambda: self._settings_window.done(0)
        )

        #################
        #               #
        # Begin Polling #
        #               #
        #################

        # Start hotkey listener
        self._keyboard_controller = keyboard.Controller()
        self._hotkey_listener = keyboard.Listener(
            on_press=self._handle_hotkey_press, on_release=None
        )
        self._hotkey_listener.start()

        # Start timer
        self._update_ui_timer = QTimer()
        self._update_ui_timer.setInterval(1000 // settings.get_int("FPS"))
        self._update_ui_timer.timeout.connect(self._update_ui)
        self._update_ui_timer.start()

        self._main_window.show()

    ###########################
    #                         #
    # React to UI Interaction #
    #                         #
    ###########################

    def _attempt_undo_hotkey(self) -> None:
        """Try to press the undo split hotkey.

        If global hotkeys are enabled and an undo split hotkey is defined,
        presses the hotkey. Otherwise, simply requests the previous split.
        """
        key_code = settings.get_str("UNDO_HOTKEY_CODE")
        if len(key_code) > 0 and settings.get_bool("GLOBAL_HOTKEYS_ENABLED"):
            self._press_hotkey(key_code)
        else:
            self._request_previous_split()

    def _attempt_skip_hotkey(self) -> None:
        """Try to press the skip split hotkey.

        If global hotkeys are enabled and a skip split hotkey is defined,
        presses the hotkey. Otherwise, simply requests the next split.
        """
        key_code = settings.get_str("SKIP_HOTKEY_CODE")
        if len(key_code) > 0 and settings.get_bool("GLOBAL_HOTKEYS_ENABLED"):
            self._press_hotkey(key_code)
        else:
            self._request_next_split()

    def _attempt_reset_hotkey(self) -> None:
        """Try to press the reset splits hotkey.

        If global hotkeys are enabled and a reset splits hotkey is defined,
        presses the hotkey. Otherwise, simply resets splits.
        """
        key_code = settings.get_str("RESET_HOTKEY_CODE")
        if len(key_code) > 0 and settings.get_bool("GLOBAL_HOTKEYS_ENABLED"):
            self._press_hotkey(key_code)
        else:
            self._request_reset_splits()

    def _request_previous_split(self) -> None:
        """Tell `splitter.splits` to call `previous_split_image`, and ask
        splitter._look_for_match to reset its flags.

        If splitter is delaying or suspended, call
        `split_dir.previous_split_image`, since it is safe to do so. Otherwise,
        attempt for 1 second to pause the splitter (by setting
        `splitter.changing_splits` to True) before calling.
        """
        if self._splitter.delaying or self._splitter.suspended:
            self._splitter.splits.previous_split_image()
        else:
            start_time = time.perf_counter()
            self._splitter.changing_splits = True
            while (
                time.perf_counter() - start_time < 1
                and not self._splitter.waiting_for_split_change
            ):
                time.sleep(0.001)
            self._splitter.splits.previous_split_image()
            self._splitter.changing_splits = False

    def _request_next_split(self) -> None:
        """Tell `splitter.splits` to call `next_split_image`, and ask
        splitter._look_for_match to reset its flags.

        If splitter is delaying or suspended, call
        `split_dir.next_split_image`, since it is safe to do so. Otherwise,
        attempt for 1 second to pause the splitter (by setting
        `splitter.changing_splits` to True) before calling.
        """
        if self._splitter.delaying or self._splitter.suspended:
            self._splitter.splits.next_split_image()
        else:
            start_time = time.perf_counter()
            self._splitter.changing_splits = True
            while (
                time.perf_counter() - start_time < 1
                and not self._splitter.waiting_for_split_change
            ):
                time.sleep(0.001)
            self._splitter.splits.next_split_image()
            self._splitter.changing_splits = False

    def _request_reset_splits(self) -> None:
        """Tell `splitter.splits` to call `reset_split_images`, and ask
        splitter._look_for_match to reset its flags.

        Kills `splitter.compare_thread` (this allows the splitter to exit
        gracefully if the split image directory has changed to an empty
        directory, for example).
        """
        self._redraw_split_labels = True
        self._splitter.safe_exit_compare_thread()
        self._splitter.splits.reset_split_images()
        self._splitter.start_compare_thread()

    def _set_image_directory_path(self) -> None:
        """Prompt the user to select a split image directory, then open the new
        directory in a threadsafe manner.

        If the directory exists and is different from the last one, change
        `LAST_IMAGE_DIR` to the new choice. Then reset splits so the new ones
        show up.
        """
        path = QFileDialog.getExistingDirectory(
            self._main_window,
            "Select splits folder",
            settings.get_str("LAST_IMAGE_DIR"),
        )
        if path != "" and path != settings.get_str("LAST_IMAGE_DIR"):
            settings.set_value("LAST_IMAGE_DIR", path)
            self._set_split_directory_line_edit_text()
            self._request_reset_splits()

    def _set_split_directory_line_edit_text(self) -> None:
        """Convert the split image directory path to an elided string,
        based on the current size of main window's split directory line edit.
        """
        path = settings.get_str("LAST_IMAGE_DIR")
        elided_path = (
            self._main_window.split_directory_line_edit.fontMetrics().elidedText(
                path,
                Qt.ElideMiddle,
                self._main_window.split_directory_line_edit.width(),
            )
        )
        self._main_window.split_directory_line_edit.setText(elided_path)

    def _exec_settings_window(self) -> None:
        """Set up and open the settings window UI.

        Because exec() blocks, _settings_window_showing isn't set to false
        until the user closes the settings window.
        """
        self._settings_window.setFocus(True)  # Make sure no widgets have focus
        self._reset_settings()
        self._settings_window_showing = True
        self._settings_window.exec()
        self._settings_window_showing = False

    def _reset_settings(self) -> None:
        """Read settings from `settings.py` and write them into the settings
        menu UI.
        """
        # Spinboxes
        for spinbox, value in {
            self._settings_window.fps_spinbox: settings.get_int("FPS"),
            self._settings_window.default_threshold_double_spinbox: str(
                float(settings.get_float("DEFAULT_THRESHOLD") * 100)
            ),
            self._settings_window.match_percent_decimals_spinbox: settings.get_int(
                "MATCH_PERCENT_DECIMALS"
            ),
            self._settings_window.default_delay_double_spinbox: settings.get_float(
                "DEFAULT_DELAY"
            ),
            self._settings_window.default_pause_double_spinbox: settings.get_float(
                "DEFAULT_PAUSE"
            ),
        }.items():
            spinbox.setProperty("value", value)

        # Checkboxes
        for checkbox, value in {
            self._settings_window.open_screenshots_checkbox: settings.get_bool(
                "OPEN_SCREENSHOT_ON_CAPTURE"
            ),
            self._settings_window.start_with_video_checkbox: settings.get_bool(
                "START_WITH_VIDEO"
            ),
            self._settings_window.global_hotkeys_checkbox: settings.get_bool(
                "GLOBAL_HOTKEYS_ENABLED"
            ),
        }.items():
            if value:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        # Hotkeys
        for hotkey_line_edit, values in {
            self._settings_window.start_split_hotkey_line_edit: (
                settings.get_str("SPLIT_HOTKEY_NAME"),
                settings.get_str("SPLIT_HOTKEY_CODE"),
            ),
            self._settings_window.reset_hotkey_line_edit: (
                settings.get_str("RESET_HOTKEY_NAME"),
                settings.get_str("RESET_HOTKEY_CODE"),
            ),
            self._settings_window.pause_hotkey_line_edit: (
                settings.get_str("PAUSE_HOTKEY_NAME"),
                settings.get_str("PAUSE_HOTKEY_CODE"),
            ),
            self._settings_window.undo_split_hotkey_line_edit: (
                settings.get_str("UNDO_HOTKEY_NAME"),
                settings.get_str("UNDO_HOTKEY_CODE"),
            ),
            self._settings_window.skip_split_hotkey_line_edit: (
                settings.get_str("SKIP_HOTKEY_NAME"),
                settings.get_str("SKIP_HOTKEY_CODE"),
            ),
            self._settings_window.previous_split_hotkey_line_edit: (
                settings.get_str("PREVIOUS_HOTKEY_NAME"),
                settings.get_str("PREVIOUS_HOTKEY_CODE"),
            ),
            self._settings_window.next_split_hotkey_line_edit: (
                settings.get_str("NEXT_HOTKEY_NAME"),
                settings.get_str("NEXT_HOTKEY_CODE"),
            ),
            self._settings_window.screenshot_hotkey_line_edit: (
                settings.get_str("SCREENSHOT_HOTKEY_NAME"),
                settings.get_str("SCREENSHOT_HOTKEY_CODE"),
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_line_edit: (
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_NAME"),
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_CODE"),
            ),
        }.items():
            hotkey_line_edit.setText(values[0])
            hotkey_line_edit.key_name = values[0]
            hotkey_line_edit.key_code = values[1]

        # Comboboxes
        aspect_ratio = settings.get_str("ASPECT_RATIO")
        if aspect_ratio == "4:3 (480x360)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(0)
        elif aspect_ratio == "4:3 (320x240)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(1)
        elif aspect_ratio == "16:9 (512x288)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(2)
        elif aspect_ratio == "16:9 (432x243)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(3)

        theme = settings.get_str("THEME")
        if theme == "dark":
            self._settings_window.theme_combo_box.setCurrentIndex(0)
        elif theme == "light":
            self._settings_window.theme_combo_box.setCurrentIndex(1)

    def _save_settings(self) -> None:
        """Write the current values in settings_window to settings, and update
        program variables as needed.
        """
        # Spinboxes
        for spinbox, setting_string in {
            self._settings_window.fps_spinbox: "FPS",
            self._settings_window.default_threshold_double_spinbox: "DEFAULT_THRESHOLD",
            self._settings_window.match_percent_decimals_spinbox: "MATCH_PERCENT_DECIMALS",
            self._settings_window.default_delay_double_spinbox: "DEFAULT_DELAY",
            self._settings_window.default_pause_double_spinbox: "DEFAULT_PAUSE",
        }.items():
            if spinbox == self._settings_window.default_threshold_double_spinbox:
                value = float(spinbox.value()) / 100
            else:
                value = spinbox.value()

            # Send new FPS value to controller and splitter
            if spinbox == self._settings_window.fps_spinbox:
                self._update_ui_timer.setInterval(1000 // value)
                self._splitter.target_fps = value

            settings.set_value(setting_string, value)

        self._splitter.splits.set_default_threshold()
        self._splitter.splits.set_default_delay()
        self._splitter.splits.set_default_pause()

        # Checkboxes
        for checkbox, setting_string in {
            self._settings_window.open_screenshots_checkbox: "OPEN_SCREENSHOT_ON_CAPTURE",
            self._settings_window.start_with_video_checkbox: "START_WITH_VIDEO",
            self._settings_window.global_hotkeys_checkbox: "GLOBAL_HOTKEYS_ENABLED",
        }.items():
            if checkbox.checkState() == 0:
                value = False
            else:
                value = True
            settings.set_value(setting_string, value)

        # Hotkeys
        for hotkey, setting_strings in {
            self._settings_window.start_split_hotkey_line_edit: (
                "SPLIT_HOTKEY_NAME",
                "SPLIT_HOTKEY_CODE",
            ),
            self._settings_window.reset_hotkey_line_edit: (
                "RESET_HOTKEY_NAME",
                "RESET_HOTKEY_CODE",
            ),
            self._settings_window.pause_hotkey_line_edit: (
                "PAUSE_HOTKEY_NAME",
                "PAUSE_HOTKEY_CODE",
            ),
            self._settings_window.undo_split_hotkey_line_edit: (
                "UNDO_HOTKEY_NAME",
                "UNDO_HOTKEY_CODE",
            ),
            self._settings_window.skip_split_hotkey_line_edit: (
                "SKIP_HOTKEY_NAME",
                "SKIP_HOTKEY_CODE",
            ),
            self._settings_window.previous_split_hotkey_line_edit: (
                "PREVIOUS_HOTKEY_NAME",
                "PREVIOUS_HOTKEY_CODE",
            ),
            self._settings_window.next_split_hotkey_line_edit: (
                "NEXT_HOTKEY_NAME",
                "NEXT_HOTKEY_CODE",
            ),
            self._settings_window.screenshot_hotkey_line_edit: (
                "SCREENSHOT_HOTKEY_NAME",
                "SCREENSHOT_HOTKEY_CODE",
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_line_edit: (
                "TOGGLE_HOTKEYS_HOTKEY_NAME",
                "TOGGLE_HOTKEYS_HOTKEY_CODE",
            ),
        }.items():
            name, code = hotkey.text(), hotkey.key_code
            settings.set_value(setting_strings[0], name)
            settings.set_value(setting_strings[1], code)

        # Comboboxes --
        # Only update these settings if the value changed, since calling
        # resize_images, _set_main_window_layout, and set_style is expensive
        aspect_ratio = self._settings_window.aspect_ratio_combo_box.currentText()
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
            self._splitter.splits.resize_images()
            self._set_main_window_layout()

        theme = self._settings_window.theme_combo_box.currentText()
        if theme != settings.get_str("THEME"):
            if theme == "dark":
                settings.set_value("THEME", "dark")
            elif theme == "light":
                settings.set_value("THEME", "light")
            style_sheet.set_style(self._main_window, theme)
            style_sheet.set_style(self._settings_window, theme)

    def _take_screenshot(self) -> None:
        """Write `spltter.comparison_frame` to a file (and optionally open it
        in machine's default image viewer).
        """
        frame = self._splitter.comparison_frame
        if frame is None:
            self._main_window.screenshot_error_message_box.exec()
            return

        image_dir = settings.get_str("LAST_IMAGE_DIR")
        if image_dir is None or not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")  # Home directory is default

        screenshot_path = (
            f"{image_dir}/{self._get_unique_filename_number(image_dir)}_screenshot.png"
        )
        cv2.imwrite(screenshot_path, frame)

        if Path(screenshot_path).is_file():
            if settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._open_file(screenshot_path)
            else:
                self._main_window.screenshot_success_message_box.setInformativeText(
                    f"Screenshot saved to:\n{screenshot_path}"
                )
                self._main_window.screenshot_success_message_box.setIconPixmap(
                    QPixmap(screenshot_path).scaledToWidth(150)
                )
                self._main_window.screenshot_success_message_box.exec()

        else:  # Something went wrong saving the file
            self._main_window.screenshot_error_message_box.exec()

    def _get_unique_filename_number(self, dir: str) -> str:
        """Return the lowest three-digit number that will allow a unique
        filename in this format: "xxx_screenshot.png"

        Args:
            dir (str): The target directory for the file

        Raises:
            Exception: Throw an exception if there are more than 1,000 files in
                the abovementioned format. This should never happen, but it's
                included because I didn't feel like thinking up a workaround.

        Returns:
            file_number (str): The lowest three-digit number as a string.
        """
        file_int = 0
        while True:
            if file_int > 999:
                raise Exception(f"Error: no suitable filename found in {dir}")

            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            if Path(f"{dir}/{file_number}_screenshot.png").is_file():
                file_int += 1
            else:
                return file_number

    def _open_file(self, path: str) -> None:
        """Enables cross-platform opening of a file.

        Args:
            path (str): The file to open.
        """
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    def _set_main_window_layout(self) -> None:
        """Set the size, location, and visibility of the main window's widgets
        according to minimum view status and aspect ratio.
        """
        if settings.get_bool("SHOW_MIN_VIEW"):
            self._set_minimal_view()
        else:
            aspect_ratio = settings.get_str("ASPECT_RATIO")
            if aspect_ratio == "4:3 (480x360)":
                self._set_480x360_view()
            elif aspect_ratio == "4:3 (320x240)":
                self._set_320x240_view()
            elif aspect_ratio == "16:9 (512x288)":
                self._set_512x288_view()
            elif aspect_ratio == "16:9 (432x243)":
                self._set_432x243_view()

        # Split labels will be refreshed after this call finishes
        self._redraw_split_labels = True
        # Refresh the split directory text so it elides correctly
        self._set_split_directory_line_edit_text()

    def _set_minimal_view(self) -> None:
        """Resize and show widgets so that minimal view is displayed."""
        self._main_window.previous_split_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                224 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.split_name_label.setGeometry(
            QRect(
                92 + self._main_window.LEFT_EDGE_CORRECTION,
                214 + self._main_window.TOP_EDGE_CORRECTION,
                251,
                31,
            )
        )
        self._main_window.split_image_loop_label.setGeometry(
            QRect(
                92 + self._main_window.LEFT_EDGE_CORRECTION,
                239 + self._main_window.TOP_EDGE_CORRECTION,
                251,
                31,
            )
        )
        self._main_window.next_split_button.setGeometry(
            QRect(
                344 + self._main_window.LEFT_EDGE_CORRECTION,
                224 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.minimal_view_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.video_feed_label.setGeometry(
            QRect(
                161 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                213,
                31,
            )
        )
        self._main_window.pause_comparison_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                121,
                31,
            )
        )
        self._main_window.skip_split_button.setGeometry(
            QRect(
                125 + self._main_window.LEFT_EDGE_CORRECTION,
                350 + self._main_window.TOP_EDGE_CORRECTION,
                56,
                31,
            )
        )
        self._main_window.undo_split_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                350 + self._main_window.TOP_EDGE_CORRECTION,
                56,
                31,
            )
        )
        self._main_window.reset_splits_button.setGeometry(
            QRect(
                304 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                71,
                71,
            )
        )
        self._main_window.current_match_percent_label.setGeometry(
            QRect(
                62 + self._main_window.LEFT_EDGE_CORRECTION,
                304 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.highest_match_percent_label.setGeometry(
            QRect(
                62 + self._main_window.LEFT_EDGE_CORRECTION,
                331 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.threshold_match_percent_label.setGeometry(
            QRect(
                62 + self._main_window.LEFT_EDGE_CORRECTION,
                358 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.current_match_percent.setGeometry(
            QRect(
                227 + self._main_window.LEFT_EDGE_CORRECTION,
                304 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.highest_match_percent.setGeometry(
            QRect(
                227 + self._main_window.LEFT_EDGE_CORRECTION,
                331 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.threshold_match_percent.setGeometry(
            QRect(
                227 + self._main_window.LEFT_EDGE_CORRECTION,
                358 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.current_match_percent_sign.setGeometry(
            QRect(
                282 + self._main_window.LEFT_EDGE_CORRECTION,
                304 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.highest_match_percent_sign.setGeometry(
            QRect(
                282 + self._main_window.LEFT_EDGE_CORRECTION,
                331 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.threshold_match_percent_sign.setGeometry(
            QRect(
                282 + self._main_window.LEFT_EDGE_CORRECTION,
                358 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )

        self._set_nonessential_widgets_visible(False)
        self._set_button_and_label_text(truncate=True)
        self._main_window.setFixedSize(345, 179 + self._main_window.HEIGHT_CORRECTION)

    def _set_480x360_view(self) -> None:
        """Resize and show widgets so the 480x360 display is shown."""
        self._main_window.split_directory_line_edit.setGeometry(
            QRect(
                247 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                785,
                30,
            )
        )
        self._main_window.video_feed_label.setGeometry(
            QRect(
                260 + self._main_window.LEFT_EDGE_CORRECTION,
                272 + self._main_window.TOP_EDGE_CORRECTION,
                80,
                31,
            )
        )
        self._main_window.split_name_label.setGeometry(
            QRect(
                584 + self._main_window.LEFT_EDGE_CORRECTION,
                255 + self._main_window.TOP_EDGE_CORRECTION,
                415,
                31,
            )
        )
        self._main_window.split_image_loop_label.setGeometry(
            QRect(
                584 + self._main_window.LEFT_EDGE_CORRECTION,
                280 + self._main_window.TOP_EDGE_CORRECTION,
                415,
                31,
            )
        )
        self._main_window.current_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.highest_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                710 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.threshold_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                740 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.current_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.highest_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                710 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.threshold_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                740 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.current_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.highest_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                710 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.threshold_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                740 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.split_directory_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                180,
                30,
            )
        )
        self._main_window.minimal_view_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.next_source_button.setGeometry(
            QRect(
                440 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(
                340 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                171,
                41,
            )
        )
        self._main_window.reload_video_button.setGeometry(
            QRect(
                340 + self._main_window.LEFT_EDGE_CORRECTION,
                730 + self._main_window.TOP_EDGE_CORRECTION,
                171,
                41,
            )
        )
        self._main_window.previous_split_button.setGeometry(
            QRect(
                550 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.next_split_button.setGeometry(
            QRect(
                1000 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.pause_comparison_button.setGeometry(
            QRect(
                580 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                191,
                41,
            )
        )
        self._main_window.skip_split_button.setGeometry(
            QRect(
                680 + self._main_window.LEFT_EDGE_CORRECTION,
                730 + self._main_window.TOP_EDGE_CORRECTION,
                91,
                41,
            )
        )
        self._main_window.undo_split_button.setGeometry(
            QRect(
                580 + self._main_window.LEFT_EDGE_CORRECTION,
                730 + self._main_window.TOP_EDGE_CORRECTION,
                91,
                41,
            )
        )
        self._main_window.reset_splits_button.setGeometry(
            QRect(
                810 + self._main_window.LEFT_EDGE_CORRECTION,
                680 + self._main_window.TOP_EDGE_CORRECTION,
                191,
                91,
            )
        )
        self._main_window.video_feed_display.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                480,
                360,
            )
        )

        split_image_geometry = QRect(
            550 + self._main_window.LEFT_EDGE_CORRECTION,
            310 + self._main_window.TOP_EDGE_CORRECTION,
            480,
            360,
        )
        self._main_window.split_image_display.setGeometry(split_image_geometry)
        self._main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(1002, 570 + self._main_window.HEIGHT_CORRECTION)

    def _set_320x240_view(self) -> None:
        """Resize and show widgets so the 320x240 display is shown."""
        self._main_window.split_directory_line_edit.setGeometry(
            QRect(
                247 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                464,
                30,
            )
        )
        self._main_window.video_feed_label.setGeometry(
            QRect(
                180 + self._main_window.LEFT_EDGE_CORRECTION,
                272 + self._main_window.TOP_EDGE_CORRECTION,
                80,
                31,
            )
        )
        self._main_window.split_name_label.setGeometry(
            QRect(
                424 + self._main_window.LEFT_EDGE_CORRECTION,
                255 + self._main_window.TOP_EDGE_CORRECTION,
                254,
                31,
            )
        )
        self._main_window.split_image_loop_label.setGeometry(
            QRect(
                424 + self._main_window.LEFT_EDGE_CORRECTION,
                280 + self._main_window.TOP_EDGE_CORRECTION,
                254,
                31,
            )
        )
        self._main_window.current_match_percent_label.setGeometry(
            QRect(
                -50 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.highest_match_percent_label.setGeometry(
            QRect(
                -50 + self._main_window.LEFT_EDGE_CORRECTION,
                590 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.threshold_match_percent_label.setGeometry(
            QRect(
                -50 + self._main_window.LEFT_EDGE_CORRECTION,
                620 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.current_match_percent.setGeometry(
            QRect(
                115 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.highest_match_percent.setGeometry(
            QRect(
                115 + self._main_window.LEFT_EDGE_CORRECTION,
                590 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.threshold_match_percent.setGeometry(
            QRect(
                115 + self._main_window.LEFT_EDGE_CORRECTION,
                620 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.current_match_percent_sign.setGeometry(
            QRect(
                170 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.highest_match_percent_sign.setGeometry(
            QRect(
                170 + self._main_window.LEFT_EDGE_CORRECTION,
                590 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.threshold_match_percent_sign.setGeometry(
            QRect(
                170 + self._main_window.LEFT_EDGE_CORRECTION,
                620 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.split_directory_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                180,
                30,
            )
        )
        self._main_window.minimal_view_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.next_source_button.setGeometry(
            QRect(
                280 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(
                220 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                131,
                41,
            )
        )
        self._main_window.reload_video_button.setGeometry(
            QRect(
                220 + self._main_window.LEFT_EDGE_CORRECTION,
                610 + self._main_window.TOP_EDGE_CORRECTION,
                131,
                41,
            )
        )
        self._main_window.previous_split_button.setGeometry(
            QRect(
                390 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.next_split_button.setGeometry(
            QRect(
                680 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.pause_comparison_button.setGeometry(
            QRect(
                420 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                121,
                41,
            )
        )
        self._main_window.skip_split_button.setGeometry(
            QRect(
                485 + self._main_window.LEFT_EDGE_CORRECTION,
                610 + self._main_window.TOP_EDGE_CORRECTION,
                56,
                41,
            )
        )
        self._main_window.undo_split_button.setGeometry(
            QRect(
                420 + self._main_window.LEFT_EDGE_CORRECTION,
                610 + self._main_window.TOP_EDGE_CORRECTION,
                56,
                41,
            )
        )
        self._main_window.reset_splits_button.setGeometry(
            QRect(
                560 + self._main_window.LEFT_EDGE_CORRECTION,
                560 + self._main_window.TOP_EDGE_CORRECTION,
                121,
                91,
            )
        )
        self._main_window.video_feed_display.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                320,
                240,
            )
        )

        split_image_geometry = QRect(
            390 + self._main_window.LEFT_EDGE_CORRECTION,
            310 + self._main_window.TOP_EDGE_CORRECTION,
            320,
            240,
        )
        self._main_window.split_image_display.setGeometry(split_image_geometry)
        self._main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=True)
        self._main_window.setFixedSize(682, 450 + self._main_window.HEIGHT_CORRECTION)

    def _set_512x288_view(self) -> None:
        """Resize and show widgets so the 512x288 display is shown."""
        self._main_window.split_directory_line_edit.setGeometry(
            QRect(
                247 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                848,
                30,
            )
        )
        self._main_window.video_feed_label.setGeometry(
            QRect(
                276 + self._main_window.LEFT_EDGE_CORRECTION,
                272 + self._main_window.TOP_EDGE_CORRECTION,
                80,
                31,
            )
        )
        self._main_window.split_name_label.setGeometry(
            QRect(
                613 + self._main_window.LEFT_EDGE_CORRECTION,
                255 + self._main_window.TOP_EDGE_CORRECTION,
                450,
                31,
            )
        )
        self._main_window.split_image_loop_label.setGeometry(
            QRect(
                613 + self._main_window.LEFT_EDGE_CORRECTION,
                280 + self._main_window.TOP_EDGE_CORRECTION,
                450,
                31,
            )
        )
        self._main_window.current_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.highest_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                638 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.threshold_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                668 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.current_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.highest_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                638 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.threshold_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                668 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.current_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.highest_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                638 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.threshold_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                668 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.split_directory_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                180,
                30,
            )
        )
        self._main_window.minimal_view_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.next_source_button.setGeometry(
            QRect(
                472 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(
                372 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                171,
                41,
            )
        )
        self._main_window.reload_video_button.setGeometry(
            QRect(
                372 + self._main_window.LEFT_EDGE_CORRECTION,
                658 + self._main_window.TOP_EDGE_CORRECTION,
                171,
                41,
            )
        )
        self._main_window.previous_split_button.setGeometry(
            QRect(
                582 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.next_split_button.setGeometry(
            QRect(
                1064 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.pause_comparison_button.setGeometry(
            QRect(
                612 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                191,
                41,
            )
        )
        self._main_window.skip_split_button.setGeometry(
            QRect(
                712 + self._main_window.LEFT_EDGE_CORRECTION,
                658 + self._main_window.TOP_EDGE_CORRECTION,
                91,
                41,
            )
        )
        self._main_window.undo_split_button.setGeometry(
            QRect(
                612 + self._main_window.LEFT_EDGE_CORRECTION,
                658 + self._main_window.TOP_EDGE_CORRECTION,
                91,
                41,
            )
        )
        self._main_window.reset_splits_button.setGeometry(
            QRect(
                874 + self._main_window.LEFT_EDGE_CORRECTION,
                608 + self._main_window.TOP_EDGE_CORRECTION,
                191,
                91,
            )
        )
        self._main_window.video_feed_display.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                512,
                288,
            )
        )

        split_image_geometry = QRect(
            582 + self._main_window.LEFT_EDGE_CORRECTION,
            310 + self._main_window.TOP_EDGE_CORRECTION,
            512,
            288,
        )
        self._main_window.split_image_display.setGeometry(split_image_geometry)
        self._main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(1064, 497 + self._main_window.HEIGHT_CORRECTION)

    def _set_432x243_view(self) -> None:
        """Resize and show widgets so the 432x243 display is shown."""
        self._main_window.split_directory_line_edit.setGeometry(
            QRect(
                247 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                688,
                30,
            )
        )
        self._main_window.video_feed_label.setGeometry(
            QRect(
                161 + self._main_window.LEFT_EDGE_CORRECTION,
                272 + self._main_window.TOP_EDGE_CORRECTION,
                231,
                31,
            )
        )
        self._main_window.split_name_label.setGeometry(
            QRect(
                534 + self._main_window.LEFT_EDGE_CORRECTION,
                255 + self._main_window.TOP_EDGE_CORRECTION,
                371,
                31,
            )
        )
        self._main_window.split_image_loop_label.setGeometry(
            QRect(
                534 + self._main_window.LEFT_EDGE_CORRECTION,
                280 + self._main_window.TOP_EDGE_CORRECTION,
                371,
                31,
            )
        )
        self._main_window.current_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.highest_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                593 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.threshold_match_percent_label.setGeometry(
            QRect(
                80 + self._main_window.LEFT_EDGE_CORRECTION,
                623 + self._main_window.TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._main_window.current_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.highest_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                593 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.threshold_match_percent.setGeometry(
            QRect(
                245 + self._main_window.LEFT_EDGE_CORRECTION,
                623 + self._main_window.TOP_EDGE_CORRECTION,
                46,
                31,
            )
        )
        self._main_window.current_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.highest_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                593 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.threshold_match_percent_sign.setGeometry(
            QRect(
                300 + self._main_window.LEFT_EDGE_CORRECTION,
                623 + self._main_window.TOP_EDGE_CORRECTION,
                21,
                31,
            )
        )
        self._main_window.split_directory_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                225 + self._main_window.TOP_EDGE_CORRECTION,
                180,
                30,
            )
        )
        self._main_window.minimal_view_button.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.next_source_button.setGeometry(
            QRect(
                392 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(
                332 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                131,
                41,
            )
        )
        self._main_window.reload_video_button.setGeometry(
            QRect(
                332 + self._main_window.LEFT_EDGE_CORRECTION,
                613 + self._main_window.TOP_EDGE_CORRECTION,
                131,
                41,
            )
        )
        self._main_window.previous_split_button.setGeometry(
            QRect(
                502 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.next_split_button.setGeometry(
            QRect(
                904 + self._main_window.LEFT_EDGE_CORRECTION,
                270 + self._main_window.TOP_EDGE_CORRECTION,
                31,
                31,
            )
        )
        self._main_window.pause_comparison_button.setGeometry(
            QRect(
                532 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                181,
                41,
            )
        )
        self._main_window.skip_split_button.setGeometry(
            QRect(
                627 + self._main_window.LEFT_EDGE_CORRECTION,
                613 + self._main_window.TOP_EDGE_CORRECTION,
                86,
                41,
            )
        )
        self._main_window.undo_split_button.setGeometry(
            QRect(
                532 + self._main_window.LEFT_EDGE_CORRECTION,
                613 + self._main_window.TOP_EDGE_CORRECTION,
                86,
                41,
            )
        )
        self._main_window.reset_splits_button.setGeometry(
            QRect(
                724 + self._main_window.LEFT_EDGE_CORRECTION,
                563 + self._main_window.TOP_EDGE_CORRECTION,
                181,
                91,
            )
        )
        self._main_window.video_feed_display.setGeometry(
            QRect(
                60 + self._main_window.LEFT_EDGE_CORRECTION,
                310 + self._main_window.TOP_EDGE_CORRECTION,
                432,
                243,
            )
        )

        split_image_geometry = QRect(
            502 + self._main_window.LEFT_EDGE_CORRECTION,
            310 + self._main_window.TOP_EDGE_CORRECTION,
            432,
            243,
        )
        self._main_window.split_image_display.setGeometry(split_image_geometry)
        self._main_window.split_image_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(904, 452 + self._main_window.HEIGHT_CORRECTION)

    def _set_button_and_label_text(self, truncate: bool) -> None:
        """Adjust button and label text according to aspect ratio and minimal
        view status.

        Args:
            truncate (bool): If True, each widget's short text is used;
                otherwise, each widget's default (long) text is used.
        """
        if settings.get_bool("SHOW_MIN_VIEW"):
            self._main_window.minimal_view_button.setText("Full view")
        else:
            self._main_window.minimal_view_button.setText("Minimal view")

        if truncate:
            self._main_window.screenshot_button.setText("Screenshot")
            self._main_window.current_match_percent_label.setText("Sim:")
            self._main_window.highest_match_percent_label.setText("High:")
            self._main_window.threshold_match_percent_label.setText("Thr:")
            if self._splitter.suspended:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_unpause_text_truncated
                )
            else:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_pause_text_truncated
                )
            self._main_window.undo_split_button.setText("Undo")
            self._main_window.skip_split_button.setText("Skip")
            self._main_window.reset_splits_button.setText("Reset")

        else:
            self._main_window.screenshot_button.setText("Take screenshot")
            self._main_window.current_match_percent_label.setText(
                "Similarity to split image:"
            )
            self._main_window.highest_match_percent_label.setText(
                "Highest similarity so far:"
            )
            self._main_window.threshold_match_percent_label.setText(
                "Threshold similarity:"
            )
            if self._splitter.suspended:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_unpause_text_default
                )
            else:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_pause_text_default
                )
            self._main_window.undo_split_button.setText("Undo split")
            self._main_window.skip_split_button.setText("Skip split")
            self._main_window.reset_splits_button.setText("Reset run")

    def _set_nonessential_widgets_visible(self, visible: bool) -> None:
        """Set widget visibility according to minimal view status.

        Args:
            visible (bool): If True, show all non-minimal-view widgets. If
                False, hide all non-minimal-view widgets.
        """
        self._main_window.split_directory_line_edit.setVisible(visible)
        self._main_window.split_directory_button.setVisible(visible)
        self._main_window.next_source_button.setVisible(visible)
        self._main_window.screenshot_button.setVisible(visible)
        self._main_window.reload_video_button.setVisible(visible)
        self._main_window.video_feed_display.setVisible(visible)
        self._main_window.split_image_display.setVisible(visible)
        # Only display this when the other widgets are hidden
        self._main_window.minimal_view_no_splits_label.setVisible(not visible)

    #################################
    #                               #
    # Update UI, Respond to Hotkeys #
    #                               #
    #################################

    def _update_ui(self) -> None:
        """Read values from the splitter and use them to update the UI; also
        read inputs from the user and use them to update the UI and the
        splitter.

        Since this method is called many times per second, most of its method
        calls are wrapped in if statements. This diminishes readability
        significantly, but also cuts down so much on CPU usage that I thought
        it was worth it.
        """
        self._update_label_and_button_text()
        self._execute_hotkey()
        self._execute_split_action()

        splitter_flags_changed = self._update_flags()
        if splitter_flags_changed:
            self._set_buttons_and_hotkeys_enabled()

    def _handle_hotkey_press(self, key: keyboard.Key) -> None:
        """Set flags when hotkeys are pressed.

        Called each time any key is pressed globally. This method has two main
        uses:
            1) Hears and reacts to user keypresses when setting hotkey
                settings. It does this by checking if a given hotkey "line
                edit" has focus and, if it does, by changing its properties
                when a key is pressed.
            2) Hears and sets flags when hotkeys are pressed in the main
                window.

        For #2, the reason flags are set instead of taking an action directly
        is that PyQt5 doesn't play nice when other threads try to manipulate
        the GUI. I couldn't get anything direct to work without throwing a zsh
        trace trap error, so this is what we're going with.

        Args:
            key (keyboard.Key): The key that was pressed.
        """
        # Get the key's name and internal value. If the key is not an
        # alphanumeric key, the first two lines throw AttributeError.
        try:
            key_name = key.char
            key_code = key.vk
        except AttributeError:
            key_name = str(key).replace("Key.", "")
            key_code = key.value.vk

        # Use #1 (set hotkey settings in the settings menu)
        for hotkey_line_edit in [
            self._settings_window.start_split_hotkey_line_edit,
            self._settings_window.reset_hotkey_line_edit,
            self._settings_window.pause_hotkey_line_edit,
            self._settings_window.undo_split_hotkey_line_edit,
            self._settings_window.skip_split_hotkey_line_edit,
            self._settings_window.previous_split_hotkey_line_edit,
            self._settings_window.next_split_hotkey_line_edit,
            self._settings_window.screenshot_hotkey_line_edit,
            self._settings_window.toggle_global_hotkeys_hotkey_line_edit,
        ]:
            if hotkey_line_edit.hasFocus():
                hotkey_line_edit.setText(key_name)
                hotkey_line_edit.key_code = key_code
                return

        # Use #2 (set flag saying hotkey was pressed)
        if not self._settings_window_showing:
            for hotkey_flag, settings_string in {
                "_split_hotkey_pressed": "SPLIT_HOTKEY_CODE",
                "_reset_hotkey_pressed": "RESET_HOTKEY_CODE",
                "_undo_hotkey_pressed": "UNDO_HOTKEY_CODE",
                "_skip_hotkey_pressed": "SKIP_HOTKEY_CODE",
                "_previous_hotkey_pressed": "PREVIOUS_HOTKEY_CODE",
                "_next_hotkey_pressed": "NEXT_HOTKEY_CODE",
                "_screenshot_hotkey_pressed": "SCREENSHOT_HOTKEY_CODE",
                "_toggle_hotkeys_hotkey_pressed": "TOGGLE_HOTKEYS_HOTKEY_CODE",
            }.items():
                if str(key_code) == settings.get_str(settings_string):
                    # Use setattr because there's not a way to set the variable
                    # from another variable directly
                    setattr(self, hotkey_flag, True)
                    return

    def _execute_hotkey(self) -> None:
        """React to the flags set in _handle_hotkey_press.

        When a hotkey is pressed, this method determines what happens.
        The dict contains the following:
            1) `flags`: A tuple with three values. Value 1 is the flag set
                `in _handle_hotkey_press`; value 2 is a string representation
                of value 1; value 3 is the flag enabling or disabling the
                hotkey, which is set in `_set_buttons_and_hotkeys_enabled`.
            2) `action`: The method or function to be called when the hotkey is
                executed.
        This dict implementation is kind of messy and hard to understand, but I
        feel that the alternative of having everything laid out in if-blocks
        was worse.
        """
        # This value is used frequently, so I define it once here for simplicity
        global_hotkeys_enabled = settings.get_bool("GLOBAL_HOTKEYS_ENABLED")

        # Loop through each hotkey and execute any whose flags are set
        for flags, action in {
            (
                self._split_hotkey_pressed,
                "_split_hotkey_pressed",
                self._split_hotkey_enabled,
            ): self._request_next_split,
            (
                self._reset_hotkey_pressed,
                "_reset_hotkey_pressed",
                self._reset_hotkey_enabled,
            ): self._request_reset_splits,
            (
                self._undo_hotkey_pressed,
                "_undo_hotkey_pressed",
                self._undo_hotkey_enabled,
            ): self._request_previous_split,
            (
                self._skip_hotkey_pressed,
                "_skip_hotkey_pressed",
                self._skip_hotkey_enabled,
            ): self._request_next_split,
            (
                self._previous_hotkey_pressed,
                "_previous_hotkey_pressed",
                True,
            ): self._main_window.previous_split_button.click,
            (
                self._next_hotkey_pressed,
                "_next_hotkey_pressed",
                True,
            ): self._main_window.next_split_button.click,
            (
                self._screenshot_hotkey_pressed,
                "_screenshot_hotkey_pressed",
                True,
            ): self._main_window.screenshot_button.click,
            (
                self._toggle_hotkeys_hotkey_pressed,
                "_toggle_hotkeys_hotkey_pressed",
                True,
            ): lambda: settings.set_value(
                "GLOBAL_HOTKEYS_ENABLED", not global_hotkeys_enabled
            ),
        }.items():
            if flags[0]:
                setattr(self, flags[1], False)  # Unset the flag
                if flags[2] and (
                    global_hotkeys_enabled
                    or self._application.focusWindow() is not None
                ):  # focusWindow() returns None if one of this program's windows isn't in focus
                    action()
                    return

    def _press_hotkey(self, key_code: str) -> None:
        """Press and release a hotkey.

        Args:
            key_code (str): A string representation of a pynput.keyboard.Key.vk
                value. Passed as a string because I use QSettings, which only
                handles strings when used cross-platform.
        """
        key_code = int(key_code)
        key = keyboard.KeyCode(vk=key_code)
        self._keyboard_controller.press(key)
        self._keyboard_controller.release(key)

    def _execute_split_action(self) -> None:
        """Send a hotkey press and request the next split image when the
        splitter finds a matching image.

        If no hotkey is set for a given action, ignore the hotkey press and
        request the next split image anyway.
        """
        # This value is used frequently, so I define it here for simplicity
        global_hotkeys_enabled = settings.get_bool("GLOBAL_HOTKEYS_ENABLED")

        # Regular split (press split hotkey)
        if self._splitter.pause_split_action:
            self._splitter.pause_split_action = False
            key_code = settings.get_str("PAUSE_HOTKEY_CODE")
            if len(key_code) > 0 and global_hotkeys_enabled:
                self._press_hotkey(key_code)
            else:
                self._splitter.splits.next_split_image()

        # Dummy split (silently advance to next split)
        elif self._splitter.dummy_split_action:
            self._splitter.dummy_split_action = False
            self._splitter.splits.next_split_image()

        # Pause split (press pause hotkey)
        elif self._splitter.normal_split_action:
            self._splitter.normal_split_action = False
            key_code = settings.get_str("SPLIT_HOTKEY_CODE")
            if len(key_code) > 0 and global_hotkeys_enabled:
                self._press_hotkey(key_code)
            else:
                self._splitter.splits.next_split_image()

    def _update_label_and_button_text(self) -> None:
        """Update label and button text in the UI based on splitter state."""
        # This value is used frequently, so I define it once for readability
        min_view_showing = settings.get_bool("SHOW_MIN_VIEW")

        # Video feed
        if min_view_showing:
            pass
        else:
            # Video is down but looks up
            if (
                self._main_window.video_feed_display.text() == ""
                and not self._splitter.capture_thread.is_alive()
            ):
                self._main_window.video_feed_display.setText(
                    self._main_window.video_feed_display_default_text
                )
            # Video is up but looks down
            elif self._splitter.frame_pixmap is not None:
                self._main_window.video_feed_display.setPixmap(
                    self._splitter.frame_pixmap
                )

        # Video label
        if min_view_showing:
            # Video feed is live, but says it is down / is blank
            if (
                self._splitter.capture_thread.is_alive()
                and self._main_window.video_feed_label.text()
                != self._main_window.video_feed_label_live_text_min
            ):
                self._main_window.video_feed_label.setText(
                    self._main_window.video_feed_label_live_text_min
                )
            # Video feed is down, but says it is live / is blank
            elif (
                not self._splitter.capture_thread.is_alive()
                and self._main_window.video_feed_label.text()
                != self._main_window.video_feed_label_down_text_min
            ):
                self._main_window.video_feed_label.setText(
                    self._main_window.video_feed_label_down_text_min
                )
        else:
            # Video feed is live, but the label is wrong / blank
            if (
                self._splitter.capture_thread.is_alive()
                and self._main_window.video_feed_label.text()
                != self._main_window.video_feed_label_live_text
            ):
                self._main_window.video_feed_label.setText(
                    self._main_window.video_feed_label_live_text
                )
            # Video feed is down, but label is filled
            elif (
                not self._splitter.capture_thread.is_alive()
                and self._main_window.video_feed_label.text() != ""
            ):
                self._main_window.video_feed_label.setText("")

        # Split image, name, and loop count
        current_image_index = self._splitter.splits.current_image_index
        # No split image loaded, but split image still being displayed
        if (
            current_image_index is None
            and self._main_window.split_name_label.text()
            != self._main_window.split_image_default_text
        ):
            self._most_recent_split_index = None
            self._most_recent_loop = None

            self._main_window.split_image_display.setText(
                self._main_window.split_image_default_text
            )
            self._main_window.split_name_label.setText("")
            self._main_window.split_image_loop_label.setText("")
            self._main_window.minimal_view_no_splits_label.setText(
                self._main_window.split_image_default_text
            )
            # Make sure this label shows over other split image labels
            self._main_window.minimal_view_no_splits_label.raise_()
        # Split image loaded that is either different from most recent one or on a different loop
        elif (
            current_image_index is not None
            and (
                current_image_index != self._most_recent_split_index
                or self._splitter.splits.current_loop != self._most_recent_loop
            )
            or self._redraw_split_labels  # Set by various methods
        ):
            self._most_recent_split_index = current_image_index
            self._most_recent_loop = self._splitter.splits.current_loop

            self._redraw_split_labels = False

            if min_view_showing:
                pass
            else:
                self._main_window.split_image_display.setPixmap(
                    self._splitter.splits.list[self._most_recent_split_index].pixmap
                )

            split_name = self._splitter.splits.list[self._most_recent_split_index].name
            elided_name = self._main_window.split_name_label.fontMetrics().elidedText(
                split_name, Qt.ElideRight, self._main_window.split_name_label.width()
            )
            self._main_window.split_name_label.setText(elided_name)
            self._main_window.minimal_view_no_splits_label.setText("")
            # Make sure this label doesn't block other labels
            self._main_window.minimal_view_no_splits_label.lower()

            current_total_loops = self._splitter.splits.list[
                self._most_recent_split_index
            ].loops
            if current_total_loops == 0:
                self._main_window.split_image_loop_label.setText("Split does not loop")
            else:
                self._main_window.split_image_loop_label.setText(
                    f"Loop {self._splitter.splits.current_loop} of {current_total_loops}"
                )

        # Split image overlay
        if self._splitter.delaying and self._splitter.delay_remaining is not None:
            self._main_window.split_image_overlay.setVisible(True)
            self._main_window.split_image_overlay.setText(
                "Splitting in {amount:.1f} s".format(
                    amount=self._splitter.delay_remaining
                )
            )
        elif self._splitter.suspended and self._splitter.suspend_remaining is not None:
            self._main_window.split_image_overlay.setVisible(True)
            self._main_window.split_image_overlay.setText(
                "Paused for next {amount:.1f} s".format(
                    amount=self._splitter.suspend_remaining
                )
            )
        elif self._main_window.split_image_overlay.text() != "":
            self._main_window.split_image_overlay.setVisible(False)
            self._main_window.split_image_overlay.setText("")

        # This value is frequently used below, so I declare it here.
        decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
        if self._most_recent_match_percent_decimals != decimals:
            self._most_recent_match_percent_decimals = decimals
            self._most_recent_match_percent_format_string = (
                f"{{:.{self._most_recent_match_percent_decimals}f}}"
            )
            self._most_recent_match_percent_null_string = (
                self._null_match_percent_string()
            )

        # Current match percent
        if (
            self._splitter.current_match_percent is None
            and self._main_window.current_match_percent
            != self._most_recent_match_percent_null_string
        ):  # Match percent is blank, but is still showing a number
            self._main_window.current_match_percent.setText(
                self._most_recent_match_percent_null_string
            )
        else:
            self._main_window.current_match_percent.setText(
                self._most_recent_match_percent_format_string.format(
                    self._splitter.current_match_percent * 100
                )
            )

        # Highest match percent
        if (
            self._splitter.highest_match_percent is None
            and self._main_window.highest_match_percent
            != self._most_recent_match_percent_null_string
        ):  # Match percent is blank, but is still showing a number
            self._main_window.highest_match_percent.setText(
                self._most_recent_match_percent_null_string
            )
        else:
            self._main_window.highest_match_percent.setText(
                self._most_recent_match_percent_format_string.format(
                    self._splitter.highest_match_percent * 100
                )
            )

        # Threshold match percent
        # Make sure the splits list isn't empty before invoking it below
        if self._most_recent_split_index is None:
            if (
                self._main_window.threshold_match_percent
                != self._most_recent_match_percent_null_string
            ):  # Match percent is blank, but is still showing a number
                self._main_window.threshold_match_percent.setText(
                    self._most_recent_match_percent_null_string
                )
        else:
            threshold_match_percent = self._splitter.splits.list[
                self._most_recent_split_index
            ].threshold
            if (
                threshold_match_percent is None
                and self._main_window.threshold_match_percent
                != self._most_recent_match_percent_null_string
            ):  # Match percent is blank, but is still showing a number
                self._main_window.threshold_match_percent.setText(
                    self._most_recent_match_percent_null_string
                )
            else:
                self._main_window.threshold_match_percent.setText(
                    self._most_recent_match_percent_format_string.format(
                        threshold_match_percent * 100
                    )
                )

        # Pause / unpause button text
        if self._splitter_suspended != self._splitter.suspended:
            self._splitter_suspended = self._splitter.suspended
            self._toggle_pause_comparison_button_text()

    def _toggle_pause_comparison_button_text(self) -> None:
        """Adjust the length and content of the pause button's text according
        to aspect ratio and splitter status.
        """
        if (
            settings.get_bool("SHOW_MIN_VIEW")
            or settings.get_str("ASPECT_RATIO") == "4:3 (320x240)"
        ):
            if self._splitter_suspended:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_unpause_text_truncated
                )
            else:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_pause_text_truncated
                )

        else:
            if self._splitter_suspended:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_unpause_text_default
                )
            else:
                self._main_window.pause_comparison_button.setText(
                    self._main_window.pause_comparison_button_pause_text_default
                )

    def _update_flags(self) -> bool:
        """Check the splitter to see if certain states have changed since the
        last check.

        The following states are checked:
            video_active: Whether `splitter.capture_thread` is alive.
            splits_active: Whether `self.most_recent_split_index` is None. That
                value is set by _update_label_and_button_text, which is called
                just before this method.
            first_split_active: Whether the current split is the first split
                (if there is a current split). This means a split image is
                active, it's the first split image, and it's the first loop of
                the image.
            last_split_active: Whether the current split is the last split (if
                there is a current split). This means a split image is active,
                it's the last split image, and it's the last loop of the image.

        Returns:
            flag_changed (bool): True if any of the above flags were set or
                unset, False otherwise.
        """
        flag_changed = False

        # video_active
        if self._video_active != self._splitter.capture_thread.is_alive():
            self._video_active = self._splitter.capture_thread.is_alive()
            flag_changed = True

        # splits_active
        # Explicitly say "is not True", "is not False" on these last three
        # flags to catch None values from __init__()
        if self._most_recent_split_index is None:
            if self._splits_active is not False:
                self._splits_active = False
                flag_changed = True
        else:
            if self._splits_active is not True:
                self._splits_active = True
                flag_changed = True

        # first_split_active
        if (
            self._most_recent_split_index == 0
            and self._splitter.splits.current_loop == 0
        ):
            if self._first_split_active is not True:
                self._first_split_active = True
                flag_changed = True
        else:
            if self._first_split_active is not False:
                self._first_split_active = False
                flag_changed = True

        # last_split_active
        if (
            self._splits_active
            and self._most_recent_split_index == len(self._splitter.splits.list) - 1
            and self._splitter.splits.current_loop
            == self._splitter.splits.list[self._most_recent_split_index].loops
        ):
            if self._last_split_active is not True:
                self._last_split_active = True
                flag_changed = True
        else:
            if self._last_split_active is not False:
                self._last_split_active = False
                flag_changed = True

        return flag_changed

    def _set_buttons_and_hotkeys_enabled(self) -> None:
        """Set the enabled status of buttons and hotkeys, depending on the
        flags set in `_update_flags`.

        Since the status of these buttons and hotkeys depends entirely on the
        flags in `_update_flags`, this method is only called if `_update_flags`
        returns True.
        """
        if self._splits_active:
            # Enable split and reset
            self._split_hotkey_enabled = True
            self._reset_hotkey_enabled = True
            self._main_window.reset_splits_button.setEnabled(True)

            # Enable screenshots if video is on
            if self._video_active:
                self._main_window.screenshot_button.setEnabled(True)
                self._main_window.pause_comparison_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)
                self._main_window.pause_comparison_button.setEnabled(False)

            # Enable undo and previous if this isn't the first split
            if self._first_split_active:
                self._undo_hotkey_enabled = False
                self._main_window.undo_split_button.setEnabled(False)
                self._main_window.previous_split_button.setEnabled(False)
            else:
                self._undo_hotkey_enabled = True
                self._main_window.undo_split_button.setEnabled(True)
                self._main_window.previous_split_button.setEnabled(True)

            # Enable skip and next if this isn't the last split
            if self._last_split_active:
                self._skip_hotkey_enabled = False
                self._main_window.skip_split_button.setEnabled(False)
                self._main_window.next_split_button.setEnabled(False)
            else:
                self._skip_hotkey_enabled = True
                self._main_window.skip_split_button.setEnabled(True)
                self._main_window.next_split_button.setEnabled(True)

        else:
            # Disable split, undo, skip, previous, next split, reset, pause
            self._split_hotkey_enabled = False
            self._reset_hotkey_enabled = False
            self._undo_hotkey_enabled = False
            self._skip_hotkey_enabled = False
            self._main_window.reset_splits_button.setEnabled(False)
            self._main_window.undo_split_button.setEnabled(False)
            self._main_window.skip_split_button.setEnabled(False)
            self._main_window.previous_split_button.setEnabled(False)
            self._main_window.next_split_button.setEnabled(False)
            self._main_window.pause_comparison_button.setEnabled(False)

            # Enable screenshots if video is on
            if self._video_active:
                self._main_window.screenshot_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)

    def _null_match_percent_string(self) -> None:
        """Return a string representing a blank match percent with the number
        of decimal places the user chooses in settings.

        Returns:
            str: The null match percent string. Possible values are "--",
                "--.-", and "--.--".
        """
        match_percent_string = "--"
        decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
        if decimals > 0:
            match_percent_string += "."
            while decimals > 0:
                match_percent_string += "-"
                decimals -= 1
        return match_percent_string

    def _formatted_match_percent_string(
        self, match_percent: float, decimals: int
    ) -> str:
        """Format a raw match percent into a string with the number of decimal
        places the user chooses.

        Args:
            match_percent (float): The raw integer match. E.g., 0.8931285.
            decimals (int): The number of trailing decimals.

        Returns:
            str: The formatted value. E.g., "89.3".
        """
        format_string = f"{{:.{decimals}f}}"
        return format_string.format(match_percent * 100)
