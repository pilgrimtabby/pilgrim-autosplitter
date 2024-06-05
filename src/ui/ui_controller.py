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
from PyQt5.QtWidgets import QAbstractButton, QApplication, QFileDialog

import settings
import ui.ui_style_sheet as style_sheet
from splitter.splitter import Splitter
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow


class UIController:
    """Manage the passing of information from the splitter to the UI, and from
    user input to the UI and the splitter.

    Perhaps the most important class method is _poller, which is ran once
    per frame using a QTimer. This method updates the UI and handles all user
    inputs.

    UIController has no public attributes, as it is meant to operate after
    initialization without further input. For details about each attribute,
    see method documentation.
    """

    def __init__(self, application: QApplication, splitter: Splitter) -> None:
        """Initialize the UI, then update it each frame.

        Creates each UI window and then shows the main window.
        Connects pyqtSignals from each UI window to their respective slots.
        Sets initial flags and values used by _poller.
        Starts the keyboard listener.
        Starts _poller, which checks for user input and splitter outputs at
        regular intervals.

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

        #########################
        #                       #
        # _poller Values, Flags #
        #                       #
        #########################

        # Tell _update_ui to update split labels
        # Should be set whenever the split image is modified
        self._redraw_split_labels = True

        # Flags to disable hotkeys
        self._split_hotkey_enabled = False
        self._undo_hotkey_enabled = False
        self._skip_hotkey_enabled = False

        # Flags for detecting hotkey presses
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

        # "Update available" message box
        self._main_window.update_available_msg.buttonClicked.connect(
            self.update_available_msg_action
        )

        # Split directory line edit
        self._main_window.split_directory_box.clicked.connect(
            lambda: self._open_file_or_dir(settings.get_str("LAST_IMAGE_DIR"))
        )

        # Split directory button
        self._main_window.split_dir_button.clicked.connect(self.set_split_dir_path)

        # Minimal view / full view button
        self._main_window.min_view_button.clicked.connect(
            lambda: settings.set_value(
                "SHOW_MIN_VIEW", not settings.get_bool("SHOW_MIN_VIEW")
            )
        )
        self._main_window.min_view_button.clicked.connect(self._set_main_window_layout)

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
        self._main_window.reconnect_button.clicked.connect(
            self._splitter.safe_exit_all_threads
        )
        self._main_window.reconnect_button.clicked.connect(self._splitter.start)

        # Pause comparison / unpause comparison button
        self._main_window.pause_button.clicked.connect(self._splitter.toggle_suspended)

        # Reset button
        self._main_window.reset_button.clicked.connect(self._attempt_reset_hotkey)

        # Undo split button
        self._main_window.undo_button.clicked.connect(self._attempt_undo_hotkey)

        # Skip split button
        self._main_window.skip_button.clicked.connect(self._attempt_skip_hotkey)

        # Previous split button
        self._main_window.previous_button.clicked.connect(self._request_previous_split)

        # Next split button
        self._main_window.next_button.clicked.connect(self._request_next_split)

        # Settings window action
        self._main_window.settings_action.triggered.connect(self._exec_settings_window)

        # Help action
        self._main_window.help_action.triggered.connect(
            lambda: webbrowser.open(settings.USER_MANUAL_URL, new=0, autoraise=True)
        )

        ##########################
        #                        #
        # Settings Window Config #
        #                        #
        ##########################

        close_settings = lambda: self._settings_window.done(0)

        # Close window convenience shortcut
        self._settings_window.close_window_shortcut.activated.connect(close_settings)

        # Cancel button
        self._settings_window.cancel_button.clicked.connect(close_settings)

        # Save button
        self._settings_window.save_button.clicked.connect(self._save_settings)
        self._settings_window.save_button.clicked.connect(close_settings)

        #######################################
        #                                     #
        # Start Polling Keyboard and Splitter #
        #                                     #
        #######################################

        # Start keyboard listener
        self._keyboard_controller = keyboard.Controller()
        self._keyboard_listener = keyboard.Listener(
            on_press=self._handle_key_press, on_release=None
        )
        self._keyboard_listener.start()

        # Start poller
        self._poller = QTimer()
        self._poller.setInterval(self._get_interval())
        self._poller.timeout.connect(self._poll)
        self._poller.start()

        self._main_window.show()

    def _poll(self) -> None:
        """Use information from UI, splitter, and keyboard to update the UI
        and splitter.

        Should be called each frame.
        """
        self._update_from_splitter()
        self._update_from_keyboard()

    ###########################
    #                         #
    # Manage User Interaction #
    #                         #
    ###########################

    def _attempt_undo_hotkey(self) -> None:
        """Try to press the undo split hotkey.

        If an undo split hotkey is defined, press the hotkey.
        Otherwise, simply go to the previous split.

        We don't need to worry about whether global hotkeys are enabled
        because when this method is called, we know the user is pressing
        a button in the UI, so the program MUST be in focus, so hotkeys
        will always work. Similarly, it is impossible for the settings window
        to be opened when this method is called, so we don't need to worry
        about whether the settings window will block the hotkey flag
        from being set.

        If this method is ever used to accomplish something
        and it's not guaranteed that the program will be in focus, this may
        need to be rethought.
        """
        key_code = settings.get_str("UNDO_HOTKEY_CODE")
        if len(key_code) > 0:
            self._press_hotkey(key_code)
        else:
            self._request_previous_split()

    def _attempt_skip_hotkey(self) -> None:
        """Try to press the skip split hotkey.

        If a skip split hotkey is defined, press the hotkey.
        Otherwise, simply go to the next split.

        We don't need to worry about whether global hotkeys are enabled
        because when this method is called, we know the user is pressing
        a button in the UI, so the program MUST be in focus, so hotkeys
        will always work. Similarly, it is impossible for the settings window
        to be opened when this method is called, so we don't need to worry
        about whether the settings window will block the hotkey flag
        from being set.

        If this method is ever used to accomplish something
        and it's not guaranteed that the program will be in focus, this may
        need to be rethought.
        """
        key_code = settings.get_str("SKIP_HOTKEY_CODE")
        if len(key_code) > 0:
            self._press_hotkey(key_code)
        else:
            self._request_next_split()

    def _attempt_reset_hotkey(self) -> None:
        """Try to press the reset splits hotkey.

        If a reset splits hotkey is defined, press the hotkey.
        Otherwise, simply reset the splits.

        We don't need to worry about whether global hotkeys are enabled
        because when this method is called, we know the user is pressing
        a button in the UI, so the program MUST be in focus, so hotkeys
        will always work. Similarly, it is impossible for the settings window
        to be opened when this method is called, so we don't need to worry
        about whether the settings window will block the hotkey flag
        from being set.

        If this method is ever used to accomplish something
        and it's not guaranteed that the program will be in focus, this may
        need to be rethought.
        """
        key_code = settings.get_str("RESET_HOTKEY_CODE")
        if len(key_code) > 0:
            self._press_hotkey(key_code)
        else:
            self._request_reset_splits()

    def _request_previous_split(self) -> None:
        """Tell `splitter.splits` to call `previous_split_image`, and ask
        splitter._look_for_match to reset its flags if needed.

        If self._splitter.match_percent is None, this means that
        splitter.look_for_match isn't active, and we can move to the next split
        image without causing a segmentation error or breaking splitter flags.

        Otherwise, we know look_for_match is active, and we need to (1) pause
        it while we change split images for thread safety, then (2) reset its
        flags. We do this (or at least try to for 1 second) by by setting the
        splitter.changing_splits flag, waiting for splitter to confirm it's
        paused (splitter sets its waiting_for_split_change flag). We change
        the split image, then unset changing_splits, which signals to splitter
        it can reset its flags.
        """
        self._redraw_split_labels = True  # Make sure UI image is updated

        # Go to next split, no need to worry about flags / thread safety
        if self._splitter.match_percent is None:
            self._splitter.splits.previous_split_image()

        # Pause splitter._look_for_match before getting next split
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
        splitter._look_for_match to reset its flags if needed.

        If self._splitter.match_percent is None, this means that
        splitter.look_for_match isn't active, and we can move to the next split
        image without causing a segmentation error or breaking splitter flags.

        Otherwise, we know look_for_match is active, and we need to (1) pause
        it while we change split images for thread safety, then (2) reset its
        flags. We do this (or at least try to for 1 second) by by setting the
        splitter.changing_splits flag, waiting for splitter to confirm it's
        paused (splitter sets its waiting_for_split_change flag). We change
        the split image, then unset changing_splits, which signals to splitter
        it can reset its flags.

        This method also kills compare_thread if we're on the last loop of the
        last split when this method is called. The idea is that when the run is
        over, the comparer stops until the user presses reset or unpauses.
        However, this only should happen if the last split is accessed by
        pressing the split hotkey or if the program found a match, so that
        users can still scroll back and forth between splits without shutting
        the thread down on accident, so we also check if this method is being
        called as the result of a hotkey press.
        """
        # Kill compare_thread instead if we're on the last split
        # (This call must be the result of a split key hotpress)
        # (See docstring)
        split_index = self._splitter.splits.current_image_index
        total_splits = len(self._splitter.splits.list) - 1
        loop = self._splitter.splits.current_loop
        total_loops = self._splitter.splits.list[split_index].loops
        if (
            split_index == total_splits
            and loop == total_loops
            and self._split_hotkey_pressed
        ):
            self._splitter.safe_exit_compare_thread()
            return

        self._redraw_split_labels = True  # Make sure UI image is updated
        # Go to next split, no need to worry about flags / thread safety
        if self._splitter.match_percent is None:
            self._splitter.splits.next_split_image()

        # Pause splitter._look_for_match before getting next split
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
        splitter._look_for_match to reset its flags if necessary.

        Kills `splitter.compare_thread` (this allows the splitter to exit
        gracefully if the split image directory has changed to an empty
        directory, for example). Restarts the thread if the split list isn't
        empty and if video is running.
        """
        self._redraw_split_labels = True
        self._splitter.safe_exit_compare_thread()
        self._splitter.splits.reset_split_images()
        if (
            len(self._splitter.splits.list) > 0
            and self._splitter.capture_thread.is_alive()
        ):
            self._splitter.start_compare_thread()

    def set_split_dir_path(self) -> None:
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
        if len(path) > 1 and path != settings.get_str("LAST_IMAGE_DIR"):
            settings.set_value("LAST_IMAGE_DIR", path)
            self._set_split_directory_box_text()
            self._request_reset_splits()

    def _set_split_directory_box_text(self) -> None:
        """Convert the split image directory path to an elided string,
        based on the current size of main window's split directory line edit.
        """
        path = settings.get_str("LAST_IMAGE_DIR")
        elided_path = self._main_window.split_directory_box.fontMetrics().elidedText(
            f" {path} ",
            Qt.ElideMiddle,
            self._main_window.split_directory_box.width(),
        )
        self._main_window.split_directory_box.setText(elided_path)

    def update_available_msg_action(self, button: QAbstractButton):
        """React to button press in _main_window.update_available_msg.

        Args:
            button (QAbstractButton): The button that was pressed.
        """
        # "Don't ask again" was clicked -- stop checking for updates
        if button.text() == self._main_window.never_button_txt:
            settings.set_value("CHECK_FOR_UPDATES", False)

        # "Open" was clicked -- open the GitHub releases page
        elif button.text() == self._main_window.open_button_txt:
            webbrowser.open(
                f"{settings.REPO_URL}releases/latest", new=0, autoraise=True
            )

    def _exec_settings_window(self) -> None:
        """Set up and open the settings window UI."""
        self._settings_window.setFocus(True)  # Make sure no widgets have focus
        self._reset_settings()
        self._settings_window.exec()

    def _reset_settings(self) -> None:
        """Read settings from `settings.py` and write them into the settings
        menu UI.
        """
        # Spinboxes
        for spinbox, value in {
            self._settings_window.fps_spinbox: settings.get_int("FPS"),
            self._settings_window.threshold_spinbox: str(
                float(settings.get_float("DEFAULT_THRESHOLD") * 100)
            ),
            self._settings_window.decimals_spinbox: settings.get_int(
                "MATCH_PERCENT_DECIMALS"
            ),
            self._settings_window.delay_spinbox: settings.get_float("DEFAULT_DELAY"),
            self._settings_window.pause_spinbox: settings.get_float("DEFAULT_PAUSE"),
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
            self._settings_window.check_for_updates_checkbox: settings.get_bool(
                "CHECK_FOR_UPDATES"
            ),
        }.items():
            if value:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        # Hotkeys
        for hotkey_box, values in {
            self._settings_window.split_hotkey_box: (
                settings.get_str("SPLIT_HOTKEY_NAME"),
                settings.get_str("SPLIT_HOTKEY_CODE"),
            ),
            self._settings_window.reset_hotkey_box: (
                settings.get_str("RESET_HOTKEY_NAME"),
                settings.get_str("RESET_HOTKEY_CODE"),
            ),
            self._settings_window.pause_hotkey_box: (
                settings.get_str("PAUSE_HOTKEY_NAME"),
                settings.get_str("PAUSE_HOTKEY_CODE"),
            ),
            self._settings_window.undo_hotkey_box: (
                settings.get_str("UNDO_HOTKEY_NAME"),
                settings.get_str("UNDO_HOTKEY_CODE"),
            ),
            self._settings_window.skip_hotkey_box: (
                settings.get_str("SKIP_HOTKEY_NAME"),
                settings.get_str("SKIP_HOTKEY_CODE"),
            ),
            self._settings_window.previous_hotkey_box: (
                settings.get_str("PREVIOUS_HOTKEY_NAME"),
                settings.get_str("PREVIOUS_HOTKEY_CODE"),
            ),
            self._settings_window.next_hotkey_box: (
                settings.get_str("NEXT_HOTKEY_NAME"),
                settings.get_str("NEXT_HOTKEY_CODE"),
            ),
            self._settings_window.screenshot_hotkey_box: (
                settings.get_str("SCREENSHOT_HOTKEY_NAME"),
                settings.get_str("SCREENSHOT_HOTKEY_CODE"),
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_box: (
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_NAME"),
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_CODE"),
            ),
        }.items():
            hotkey_box.setText(values[0])
            hotkey_box.key_name = values[0]
            hotkey_box.key_code = values[1]

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
            self._settings_window.threshold_spinbox: "DEFAULT_THRESHOLD",
            self._settings_window.decimals_spinbox: "MATCH_PERCENT_DECIMALS",
            self._settings_window.delay_spinbox: "DEFAULT_DELAY",
            self._settings_window.pause_spinbox: "DEFAULT_PAUSE",
        }.items():
            if spinbox == self._settings_window.threshold_spinbox:
                value = float(spinbox.value()) / 100
            else:
                value = spinbox.value()

            # Send new FPS value to controller and splitter
            if spinbox == self._settings_window.fps_spinbox:
                self._poller.setInterval(self._get_interval())
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
            self._settings_window.check_for_updates_checkbox: "CHECK_FOR_UPDATES",
        }.items():
            if checkbox.checkState() == 0:
                value = False
            else:
                value = True
            settings.set_value(setting_string, value)

        # Hotkeys
        for hotkey, setting_strings in {
            self._settings_window.split_hotkey_box: (
                "SPLIT_HOTKEY_NAME",
                "SPLIT_HOTKEY_CODE",
            ),
            self._settings_window.reset_hotkey_box: (
                "RESET_HOTKEY_NAME",
                "RESET_HOTKEY_CODE",
            ),
            self._settings_window.pause_hotkey_box: (
                "PAUSE_HOTKEY_NAME",
                "PAUSE_HOTKEY_CODE",
            ),
            self._settings_window.undo_hotkey_box: (
                "UNDO_HOTKEY_NAME",
                "UNDO_HOTKEY_CODE",
            ),
            self._settings_window.skip_hotkey_box: (
                "SKIP_HOTKEY_NAME",
                "SKIP_HOTKEY_CODE",
            ),
            self._settings_window.previous_hotkey_box: (
                "PREVIOUS_HOTKEY_NAME",
                "PREVIOUS_HOTKEY_CODE",
            ),
            self._settings_window.next_hotkey_box: (
                "NEXT_HOTKEY_NAME",
                "NEXT_HOTKEY_CODE",
            ),
            self._settings_window.screenshot_hotkey_box: (
                "SCREENSHOT_HOTKEY_NAME",
                "SCREENSHOT_HOTKEY_CODE",
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_box: (
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
            msg = self._main_window.screenshot_err_no_video
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

        image_dir = settings.get_str("LAST_IMAGE_DIR")
        if not Path(image_dir).is_dir:
            image_dir = os.path.expanduser("~")  # Home directory is default

        screenshot_path = (
            f"{image_dir}/{self.get_file_number(image_dir)}_screenshot.png"
        )
        cv2.imwrite(screenshot_path, frame)

        if Path(screenshot_path).is_file():
            if settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"):
                self._open_file_or_dir(screenshot_path)
            else:
                msg = self._main_window.screenshot_ok_msg
                msg.setInformativeText(f"Screenshot saved to:\n{screenshot_path}")
                msg.setIconPixmap(QPixmap(screenshot_path).scaledToWidth(150))
                msg.show()
                # Close message box after 10 seconds
                QTimer.singleShot(10000, lambda: msg.done(0))

        else:  # File couldn't be written to the split image directory
            msg = self._main_window.screenshot_error_no_file_message_box
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))

    def get_file_number(self, dir: str) -> str:
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

    def _open_file_or_dir(self, path: str) -> None:
        """Enables cross-platform opening of a file or directory.

        If path points to a file, the file opens with the default application.
        If path points to a dir, the dir opens in the OS's file explorer.

        If the path doesn't exist, show an error message and return.

        Args:
            path (str): The file to open.
        """
        if not Path(path).exists():
            msg = self._main_window.err_not_found_msg
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

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
        self._set_split_directory_box_text()

    def _set_minimal_view(self) -> None:
        """Resize and show widgets so that minimal view is displayed."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.previous_button.setGeometry(
            QRect(60 + left, 224 + top, 31, 31)
        )
        self._main_window.split_name_label.setGeometry(
            QRect(92 + left, 214 + top, 251, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(92 + left, 239 + top, 251, 31)
        )
        self._main_window.next_button.setGeometry(QRect(344 + left, 224 + top, 31, 31))
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.video_title.setGeometry(QRect(161 + left, 270 + top, 213, 31))
        self._main_window.pause_button.setGeometry(QRect(60 + left, 310 + top, 121, 31))
        self._main_window.skip_button.setGeometry(QRect(125 + left, 350 + top, 56, 31))
        self._main_window.undo_button.setGeometry(QRect(60 + left, 350 + top, 56, 31))
        self._main_window.reset_button.setGeometry(QRect(304 + left, 310 + top, 71, 71))
        self._main_window.match_percent_label.setGeometry(
            QRect(62 + left, 304 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(62 + left, 331 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(62 + left, 358 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(227 + left, 304 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(227 + left, 331 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(227 + left, 358 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(282 + left, 304 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(282 + left, 331 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(282 + left, 358 + top, 21, 31)
        )

        self._set_nonessential_widgets_visible(False)
        self._set_button_and_label_text(truncate=True)
        self._main_window.setFixedSize(345, 179 + self._main_window.HEIGHT_CORRECTION)

    def _set_480x360_view(self) -> None:
        """Resize and show widgets so the 480x360 display is shown."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.split_directory_box.setGeometry(
            QRect(247 + left, 225 + top, 785, 30)
        )
        self._main_window.video_title.setGeometry(QRect(260 + left, 272 + top, 80, 31))
        self._main_window.split_name_label.setGeometry(
            QRect(584 + left, 255 + top, 415, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(584 + left, 280 + top, 415, 31)
        )
        self._main_window.match_percent_label.setGeometry(
            QRect(80 + left, 680 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(80 + left, 710 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(80 + left, 740 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(245 + left, 680 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(245 + left, 710 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(245 + left, 740 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(300 + left, 680 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(300 + left, 710 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(300 + left, 740 + top, 21, 31)
        )
        self._main_window.split_dir_button.setGeometry(
            QRect(60 + left, 225 + top, 180, 30)
        )
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.next_source_button.setGeometry(
            QRect(440 + left, 270 + top, 100, 31)
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(340 + left, 680 + top, 171, 41)
        )
        self._main_window.reconnect_button.setGeometry(
            QRect(340 + left, 730 + top, 171, 41)
        )
        self._main_window.previous_button.setGeometry(
            QRect(550 + left, 270 + top, 31, 31)
        )
        self._main_window.next_button.setGeometry(QRect(1000 + left, 270 + top, 31, 31))
        self._main_window.pause_button.setGeometry(
            QRect(580 + left, 680 + top, 191, 41)
        )
        self._main_window.skip_button.setGeometry(QRect(680 + left, 730 + top, 91, 41))
        self._main_window.undo_button.setGeometry(QRect(580 + left, 730 + top, 91, 41))
        self._main_window.reset_button.setGeometry(
            QRect(810 + left, 680 + top, 191, 91)
        )
        self._main_window.video_display.setGeometry(
            QRect(60 + left, 310 + top, 480, 360)
        )

        split_image_geometry = QRect(550 + left, 310 + top, 480, 360)
        self._main_window.split_display.setGeometry(split_image_geometry)
        self._main_window.split_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(1002, 570 + self._main_window.HEIGHT_CORRECTION)

    def _set_320x240_view(self) -> None:
        """Resize and show widgets so the 320x240 display is shown."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.split_directory_box.setGeometry(
            QRect(247 + left, 225 + top, 464, 30)
        )
        self._main_window.video_title.setGeometry(QRect(180 + left, 272 + top, 80, 31))
        self._main_window.split_name_label.setGeometry(
            QRect(424 + left, 255 + top, 254, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(424 + left, 280 + top, 254, 31)
        )
        self._main_window.match_percent_label.setGeometry(
            QRect(-50 + left, 560 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(-50 + left, 590 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(-50 + left, 620 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(115 + left, 560 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(115 + left, 590 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(115 + left, 620 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(170 + left, 560 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(170 + left, 590 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(170 + left, 620 + top, 21, 31)
        )
        self._main_window.split_dir_button.setGeometry(
            QRect(60 + left, 225 + top, 180, 30)
        )
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.next_source_button.setGeometry(
            QRect(280 + left, 270 + top, 100, 31)
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(220 + left, 560 + top, 131, 41)
        )
        self._main_window.reconnect_button.setGeometry(
            QRect(220 + left, 610 + top, 131, 41)
        )
        self._main_window.previous_button.setGeometry(
            QRect(390 + left, 270 + top, 31, 31)
        )
        self._main_window.next_button.setGeometry(QRect(680 + left, 270 + top, 31, 31))
        self._main_window.pause_button.setGeometry(
            QRect(420 + left, 560 + top, 121, 41)
        )
        self._main_window.skip_button.setGeometry(QRect(485 + left, 610 + top, 56, 41))
        self._main_window.undo_button.setGeometry(QRect(420 + left, 610 + top, 56, 41))
        self._main_window.reset_button.setGeometry(
            QRect(560 + left, 560 + top, 121, 91)
        )
        self._main_window.video_display.setGeometry(
            QRect(60 + left, 310 + top, 320, 240)
        )

        split_image_geometry = QRect(390 + left, 310 + top, 320, 240)
        self._main_window.split_display.setGeometry(split_image_geometry)
        self._main_window.split_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=True)
        self._main_window.setFixedSize(682, 450 + self._main_window.HEIGHT_CORRECTION)

    def _set_512x288_view(self) -> None:
        """Resize and show widgets so the 512x288 display is shown."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.split_directory_box.setGeometry(
            QRect(247 + left, 225 + top, 848, 30)
        )
        self._main_window.video_title.setGeometry(QRect(276 + left, 272 + top, 80, 31))
        self._main_window.split_name_label.setGeometry(
            QRect(613 + left, 255 + top, 450, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(613 + left, 280 + top, 450, 31)
        )
        self._main_window.match_percent_label.setGeometry(
            QRect(80 + left, 608 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(80 + left, 638 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(80 + left, 668 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(245 + left, 608 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(245 + left, 638 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(245 + left, 668 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(300 + left, 608 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(300 + left, 638 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(300 + left, 668 + top, 21, 31)
        )
        self._main_window.split_dir_button.setGeometry(
            QRect(60 + left, 225 + top, 180, 30)
        )
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.next_source_button.setGeometry(
            QRect(472 + left, 270 + top, 100, 31)
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(372 + left, 608 + top, 171, 41)
        )
        self._main_window.reconnect_button.setGeometry(
            QRect(372 + left, 658 + top, 171, 41)
        )
        self._main_window.previous_button.setGeometry(
            QRect(582 + left, 270 + top, 31, 31)
        )
        self._main_window.next_button.setGeometry(QRect(1064 + left, 270 + top, 31, 31))
        self._main_window.pause_button.setGeometry(
            QRect(612 + left, 608 + top, 191, 41)
        )
        self._main_window.skip_button.setGeometry(QRect(712 + left, 658 + top, 91, 41))
        self._main_window.undo_button.setGeometry(QRect(612 + left, 658 + top, 91, 41))
        self._main_window.reset_button.setGeometry(
            QRect(874 + left, 608 + top, 191, 91)
        )
        self._main_window.video_display.setGeometry(
            QRect(60 + left, 310 + top, 512, 288)
        )

        split_image_geometry = QRect(582 + left, 310 + top, 512, 288)
        self._main_window.split_display.setGeometry(split_image_geometry)
        self._main_window.split_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(1064, 497 + self._main_window.HEIGHT_CORRECTION)

    def _set_432x243_view(self) -> None:
        """Resize and show widgets so the 432x243 display is shown."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.split_directory_box.setGeometry(
            QRect(247 + left, 225 + top, 688, 30)
        )
        self._main_window.video_title.setGeometry(QRect(161 + left, 272 + top, 231, 31))
        self._main_window.split_name_label.setGeometry(
            QRect(534 + left, 255 + top, 371, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(534 + left, 280 + top, 371, 31)
        )
        self._main_window.match_percent_label.setGeometry(
            QRect(80 + left, 563 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(80 + left, 593 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(80 + left, 623 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(245 + left, 563 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(245 + left, 593 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(245 + left, 623 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(300 + left, 563 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(300 + left, 593 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(300 + left, 623 + top, 21, 31)
        )
        self._main_window.split_dir_button.setGeometry(
            QRect(60 + left, 225 + top, 180, 30)
        )
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.next_source_button.setGeometry(
            QRect(392 + left, 270 + top, 100, 31)
        )
        self._main_window.screenshot_button.setGeometry(
            QRect(332 + left, 563 + top, 131, 41)
        )
        self._main_window.reconnect_button.setGeometry(
            QRect(332 + left, 613 + top, 131, 41)
        )
        self._main_window.previous_button.setGeometry(
            QRect(502 + left, 270 + top, 31, 31)
        )
        self._main_window.next_button.setGeometry(QRect(904 + left, 270 + top, 31, 31))
        self._main_window.pause_button.setGeometry(
            QRect(532 + left, 563 + top, 181, 41)
        )
        self._main_window.skip_button.setGeometry(QRect(627 + left, 613 + top, 86, 41))
        self._main_window.undo_button.setGeometry(QRect(532 + left, 613 + top, 86, 41))
        self._main_window.reset_button.setGeometry(
            QRect(724 + left, 563 + top, 181, 91)
        )
        self._main_window.video_display.setGeometry(
            QRect(60 + left, 310 + top, 432, 243)
        )

        split_image_geometry = QRect(502 + left, 310 + top, 432, 243)
        self._main_window.split_display.setGeometry(split_image_geometry)
        self._main_window.split_overlay.setGeometry(split_image_geometry)

        self._set_nonessential_widgets_visible(True)
        self._set_button_and_label_text(truncate=False)
        self._main_window.setFixedSize(904, 452 + self._main_window.HEIGHT_CORRECTION)

    def _set_button_and_label_text(self, truncate: bool) -> None:
        """Set button and label text according to aspect ratio and min view.

        Args:
            truncate (bool): If True, each widget's short text is used;
                otherwise, each widget's default (long) text is used.
        """
        # Min view button
        if settings.get_bool("SHOW_MIN_VIEW"):
            min_view_txt = self._main_window.min_view_full_txt
        else:
            min_view_txt = self._main_window.min_view_min_txt

        # Other buttons
        if truncate:
            screenshot_txt = self._main_window.screenshot_button_short_txt
            match_txt = self._main_window.match_percent_short_txt
            highest_txt = self._main_window.highest_percent_short_txt
            threshold_txt = self._main_window.threshold_percent_short_txt
            undo_txt = self._main_window.undo_button_short_txt
            skip_txt = self._main_window.skip_button_short_txt
            reset_txt = self._main_window.reset_button_short_txt
        else:
            screenshot_txt = self._main_window.screenshot_button_long_txt
            match_txt = self._main_window.match_percent_long_txt
            highest_txt = self._main_window.highest_percent_long_txt
            threshold_txt = self._main_window.threshold_percent_long_txt
            undo_txt = self._main_window.undo_button_long_txt
            skip_txt = self._main_window.skip_button_long_txt
            reset_txt = self._main_window.reset_button_long_txt

        self._main_window.min_view_button.setText(min_view_txt)
        self._main_window.screenshot_button.setText(screenshot_txt)
        self._main_window.match_percent_label.setText(match_txt)
        self._main_window.highest_percent_label.setText(highest_txt)
        self._main_window.threshold_percent_label.setText(threshold_txt)
        self._main_window.undo_button.setText(undo_txt)
        self._main_window.skip_button.setText(skip_txt)
        self._main_window.reset_button.setText(reset_txt)

    def _set_nonessential_widgets_visible(self, visible: bool) -> None:
        """Set widget visibility according to minimal view status.

        Args:
            visible (bool): If True, show all non-minimal-view widgets. If
                False, hide all non-minimal-view widgets.
        """
        self._main_window.split_directory_box.setVisible(visible)
        self._main_window.split_dir_button.setVisible(visible)
        self._main_window.next_source_button.setVisible(visible)
        self._main_window.screenshot_button.setVisible(visible)
        self._main_window.reconnect_button.setVisible(visible)
        self._main_window.video_display.setVisible(visible)
        self._main_window.split_display.setVisible(visible)
        # Only display this when the other widgets are hidden
        self._main_window.split_info_min_label.setVisible(not visible)

    ###########################
    #                         #
    # Update UI from Splitter #
    #                         #
    ###########################

    def _update_from_splitter(self) -> None:
        """Read values from the splitter and use them to update the UI."""
        self._update_video_feed()
        self._update_video_title()
        self._update_split_image_labels()
        self._update_split_delay_suspend()
        self._update_match_percents()
        self._update_pause_button()
        self._set_buttons_and_hotkeys_enabled()

    def _update_video_feed(self) -> None:
        """Clear video if video is down; update video if video is alive."""
        if settings.get_bool("SHOW_MIN_VIEW"):
            return

        video_alive = self._splitter.capture_thread.is_alive()
        video = self._main_window.video_display

        # Video not connected, but video frame on UI
        if video.text() == "" and not video_alive:
            video.setText(self._main_window.video_display_txt)
        # Video is connected, but is not showing on UI
        elif self._splitter.frame_pixmap is not None:
            video.setPixmap(self._splitter.frame_pixmap)

    def _update_video_title(self) -> None:
        """Adjust video title depending on whether video is alive."""
        video_alive = self._splitter.capture_thread.is_alive()
        norm_live_txt = self._main_window.video_live_txt
        norm_down_txt = self._main_window.video_down_txt
        min_down_txt = self._main_window.min_video_down_txt
        min_live_txt = self._main_window.min_video_live_txt
        label = self._main_window.video_title

        if settings.get_bool("SHOW_MIN_VIEW"):
            # Video is connected, but label says it's not
            if video_alive and label.text() != min_live_txt:
                label.setText(min_live_txt)
            # Video isn't conected, but label says it is
            elif not video_alive and label.text() != min_down_txt:
                label.setText(min_down_txt)

        else:
            # Video is connected, but label says it's not
            if video_alive and label.text() != norm_live_txt:
                label.setText(norm_live_txt)
            # Video isn't connected, but label says it is
            elif not video_alive and label.text() != norm_down_txt:
                label.setText(norm_down_txt)

    def _update_split_image_labels(self) -> None:
        """Update split name, loops, and image."""
        current_index = self._splitter.splits.current_image_index
        current_loop = self._splitter.splits.current_loop
        split_display = self._main_window.split_display
        split_label = self._main_window.split_name_label
        loop_label = self._main_window.split_loop_label
        splits_down_txt = self._main_window.split_display_txt
        splits_min_label = self._main_window.split_info_min_label

        # No splits loaded, but UI showing split image
        if current_index is None:
            if split_display.text() != splits_down_txt:
                split_display.setText(splits_down_txt)
                split_label.setText("")
                loop_label.setText("")
                splits_min_label.setText(splits_down_txt)
                splits_min_label.raise_()  # Make sure it's not being covered

        # UI showing split but split has been changed, resized, or reset
        elif self._redraw_split_labels:
            self._redraw_split_labels = False

            current_split_image = self._splitter.splits.list[current_index]
            elided_name = split_label.fontMetrics().elidedText(
                current_split_image.name, Qt.ElideRight, split_label.width()
            )
            total_loops = current_split_image.loops
            loop_txt = self._main_window.split_loop_label_empty_txt

            if not settings.get_bool("SHOW_MIN_VIEW"):
                split_display.setPixmap(current_split_image.pixmap)
            split_label.setText(elided_name)
            if total_loops == 1:
                loop_txt = self._main_window.split_loop_label_empty_txt
                loop_label.setText(loop_txt)
            else:
                loop_txt = self._main_window.split_loop_label_txt
                loop_label.setText(loop_txt.format(current_loop, total_loops))
            splits_min_label.setText("")
            splits_min_label.lower()  # Make sure it's not covering others

    def _update_split_delay_suspend(self) -> None:
        """Display remaining delay or suspend time.

        Keep track of both overlays, regardless of view, so we can hide the one
        not currently in use.
        """
        if settings.get_bool("SHOW_MIN_VIEW"):
            overlay = self._main_window.min_view_overlay
            self._main_window.split_overlay.setVisible(False)
        else:
            overlay = self._main_window.split_overlay
            self._main_window.min_view_overlay.setVisible(False)
        delay_txt = self._main_window.overlay_delay_txt
        pause_txt = self._main_window.overlay_pause_txt

        # Splitter is delaying pre-split
        if self._splitter.delaying and self._splitter.delay_remaining is not None:
            overlay.setVisible(True)
            overlay.setText(delay_txt.format(amount=self._splitter.delay_remaining))

        # Splitter is pausing post-split
        elif self._splitter.suspended and self._splitter.suspend_remaining is not None:
            overlay.setVisible(True)
            overlay.setText(pause_txt.format(amount=self._splitter.suspend_remaining))

        # Splitter isn't pausing or delaying, but the overlay is showing
        elif overlay.text() != "":
            overlay.setVisible(False)
            overlay.setText("")

    def _update_match_percents(self):
        """Update match percents or set them to blank."""
        decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
        format_str = f"{{:.{decimals}f}}"
        null_str = self._null_match_percent_string(decimals)
        match_percent = self._splitter.match_percent
        match_label = self._main_window.match_percent
        high_percent = self._splitter.highest_percent
        high_label = self._main_window.highest_percent
        current_index = self._splitter.splits.current_image_index
        thresh_label = self._main_window.threshold_percent

        # Splitter isn't comparing images, but UI is showing current%, highest%
        if match_percent is None or high_percent is None:
            if match_label.text() != null_str or high_label != null_str:
                match_label.setText(null_str)
                high_label.setText(null_str)

        # Update current match%, highest%
        else:
            match_label.setText(format_str.format(match_percent * 100))
            high_label.setText(format_str.format(high_percent * 100))

        # No splits loaded, but UI is showing threshold%
        if current_index is None:
            if thresh_label.text() != null_str:
                thresh_label.setText(null_str)

        # Update threshold%
        else:
            threshold = self._splitter.splits.list[current_index].threshold
            thresh_label.setText(format_str.format(threshold * 100))

    def _update_pause_button(self):
        """Adjust the length and content of the pause button's text according
        to aspect ratio and splitter status.
        """
        suspended = self._splitter.suspended
        pause_button = self._main_window.pause_button
        show_short_text = (
            settings.get_bool("SHOW_MIN_VIEW")
            or settings.get_str("ASPECT_RATIO") == "4:3 (320x240)"
        )

        if show_short_text:
            if suspended:
                pause_button.setText(self._main_window.unpause_short_txt)
            else:
                pause_button.setText(self._main_window.pause_short_txt)

        else:
            if suspended:
                pause_button.setText(self._main_window.unpause_long_txt)
            else:
                pause_button.setText(self._main_window.pause_long_txt)

    def _set_buttons_and_hotkeys_enabled(self) -> bool:
        """Enable and disable hotkeys and buttons depending on whether splits
        are alive, the video is alive, and the current split is the first or
        last split."""
        current_split_index = self._splitter.splits.current_image_index
        video_alive = self._splitter.capture_thread.is_alive()

        if current_split_index is None:
            # Enable screenshots if video is on
            if video_alive:
                self._main_window.screenshot_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)

            # Disable split, undo, skip, previous, next split, pause
            self._split_hotkey_enabled = False
            self._undo_hotkey_enabled = False
            self._skip_hotkey_enabled = False
            self._main_window.undo_button.setEnabled(False)
            self._main_window.skip_button.setEnabled(False)
            self._main_window.previous_button.setEnabled(False)
            self._main_window.next_button.setEnabled(False)
            self._main_window.pause_button.setEnabled(False)

        else:
            loop = self._splitter.splits.current_loop
            total_loops = self._splitter.splits.list[current_split_index].loops
            total_splits = len(self._splitter.splits.list) - 1

            # Enable split hotkey
            self._split_hotkey_enabled = True

            # Enable screenshots if video is on
            if video_alive:
                self._main_window.screenshot_button.setEnabled(True)
                self._main_window.pause_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)
                self._main_window.pause_button.setEnabled(False)

            # Enable undo and previous if this isn't the first split
            if current_split_index == 0 and loop == 1:
                self._undo_hotkey_enabled = False
                self._main_window.undo_button.setEnabled(False)
                self._main_window.previous_button.setEnabled(False)
            else:
                self._undo_hotkey_enabled = True
                self._main_window.undo_button.setEnabled(True)
                self._main_window.previous_button.setEnabled(True)

            # Enable skip and next if this isn't the last split
            if current_split_index == total_splits and loop == total_loops:
                self._skip_hotkey_enabled = False
                self._main_window.skip_button.setEnabled(False)
                self._main_window.next_button.setEnabled(False)
            else:
                self._skip_hotkey_enabled = True
                self._main_window.skip_button.setEnabled(True)
                self._main_window.next_button.setEnabled(True)

    def _null_match_percent_string(self, decimals: int) -> None:
        """Return a string representing a blank match percent with the number
        of decimal places the user chooses in settings.

        Returns:
            str: The null match percent string. Possible return values are
            "--", "--.-", and "--.--".
        """
        match_percent_string = "--"
        if decimals > 0:
            match_percent_string += "."
            while decimals > 0:
                match_percent_string += "-"
                decimals -= 1
        return match_percent_string

    def _get_interval(self) -> int:
        """Calculate the rate at which _poller should poll.

        The minimum is 20 Hz (represented by the 50 ms value below). Any
        slower than 20 Hz and the UI starts to look pretty bad.

        1000 is used because that is the number of ms in a second.

        Returns:
            int: The amount of time in ms the poller waits between calls.
        """
        return min(1000 // settings.get_int("FPS"), 50)

    ###########################
    #                         #
    # Update UI from Keyboard #
    #                         #
    ###########################

    def _update_from_keyboard(self) -> None:
        """Use flags set in _handle_key_press to split and do other actions."""
        self._handle_hotkey_press()
        self._execute_split_action()

    def _handle_key_press(self, key: keyboard.Key) -> None:
        """Process key presses, setting flags if the key is a hotkey.

        Called each time any key is pressed, whether or not the program is in
        focus. This method has two main uses:
            1) Updates users' custom hotkey bindings. It does this by checking
                if a given hotkey "line edit" has focus and, if so, changing
                its key_code and text to match the key.
            2) If a hotkey is pressed, sets a flag indicating it was pressed.

        We set flags when hotkeys are pressed instead of directly calling a
        method because PyQt5 doesn't allow other threads to manipulate the UI.
        Doing so almost always causes a zsh trace trap error / crash.

        Args:
            key (keyboard.Key): The key that was pressed.
        """
        # Get the key's name and internal value. If the key is not an
        # alphanumeric key, the try block throws AttributeError.
        try:
            key_name, key_code = key.char, key.vk
        except AttributeError:
            key_name, key_code = str(key).replace("Key.", ""), key.value.vk

        # Use #1 (set hotkey settings in settings window)
        for hotkey_box in [
            self._settings_window.split_hotkey_box,
            self._settings_window.reset_hotkey_box,
            self._settings_window.pause_hotkey_box,
            self._settings_window.undo_hotkey_box,
            self._settings_window.skip_hotkey_box,
            self._settings_window.previous_hotkey_box,
            self._settings_window.next_hotkey_box,
            self._settings_window.screenshot_hotkey_box,
            self._settings_window.toggle_global_hotkeys_hotkey_box,
        ]:
            if hotkey_box.hasFocus():
                hotkey_box.setText(key_name)
                hotkey_box.key_code = key_code
                return

        # Use #2 (set "hotkey pressed" flag for _handle_hotkey_press)
        if not self._settings_window.isVisible():
            for hotkey_pressed, settings_string in {
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
                    # Use setattr because that allows us to use this dict format
                    setattr(self, hotkey_pressed, True)

    def _handle_hotkey_press(self) -> None:
        """React to the flags set in _handle_key_press.

        When a hotkey is pressed, this method determines what happens.
        The dict contains the following:
            1) `flags`: A tuple with three values. Value 1 is the flag set
                `in _handle_key_press`; value 2 is a string representation
                of value 1; value 3 is the flag enabling or disabling the
                hotkey, which is set in `_set_buttons_and_hotkeys_enabled`
                (or just `True` if there is no flag).
            2) `action`: The method or function to be called when the hotkey is
                executed.
        This dict implementation is kind of messy and hard to understand, but I
        feel that the alternative of having everything laid out in if-blocks
        was worse.
        """
        global_hotkeys_enabled = settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
        if self._toggle_hotkeys_hotkey_pressed:
            self._toggle_hotkeys_hotkey_pressed = False
            settings.set_value("GLOBAL_HOTKEYS_ENABLED", not global_hotkeys_enabled)
            return

        hotkey_press_allowed = (
            global_hotkeys_enabled or self._application.focusWindow() is not None
        )
        if not hotkey_press_allowed:
            return

        if self._split_hotkey_pressed:
            if self._split_hotkey_enabled:
                self._request_next_split()
            self._split_hotkey_pressed = False

        elif self._reset_hotkey_pressed:
            self._request_reset_splits()
            self._reset_hotkey_pressed = False

        elif self._undo_hotkey_pressed:
            if self._undo_hotkey_enabled:
                self._request_previous_split()
            self._undo_hotkey_pressed = False

        elif self._skip_hotkey_pressed:
            if self._skip_hotkey_enabled:
                self._request_next_split()
            self._skip_hotkey_pressed = False

        elif self._previous_hotkey_pressed:
            self._main_window.previous_button.click()
            self._previous_hotkey_pressed = False

        elif self._next_hotkey_pressed:
            self._main_window.next_button.click()
            self._next_hotkey_pressed = False

        elif self._screenshot_hotkey_pressed:
            self._main_window.screenshot_button.click()
            self._screenshot_hotkey_pressed = False

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
        # Pause split (press pause hotkey)
        if self._splitter.pause_split_action:
            self._splitter.pause_split_action = False
            key_code = settings.get_str("PAUSE_HOTKEY_CODE")
            if len(key_code) > 0:
                self._press_hotkey(key_code)
            self._request_next_split()

        # Dummy split (silently advance to next split)
        elif self._splitter.dummy_split_action:
            self._splitter.dummy_split_action = False
            self._request_next_split()

        # Normal split (press split hotkey)
        elif self._splitter.normal_split_action:
            self._splitter.normal_split_action = False
            key_code = settings.get_str("SPLIT_HOTKEY_CODE")
            if len(key_code) > 0:
                self._press_hotkey(key_code)
            # If key didn't get pressed, OR if it did get pressed but global
            # hotkeys are off and the app isn't in focus, move the split image
            # forward, since pressing the key on its own won't do that
            hotkey_not_caught = (
                self._application.focusWindow() is None
                and not settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
            )
            if len(key_code) == 0 or hotkey_not_caught:
                self._request_next_split()
