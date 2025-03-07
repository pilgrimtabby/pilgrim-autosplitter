# Copyright (c) 2024-2025 pilgrim_tabby
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


import datetime
import glob
import os
import platform
import subprocess
import time
from typing import Optional, Union
import webbrowser
from pathlib import Path
from threading import Lock, Thread

import cv2
from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAbstractButton, QApplication, QFileDialog

import settings
from splitter.splitter import Splitter
from ui.ui_keyboard_controller import UIKeyboardController
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow
from ui.ui_style_sheet import style_sheet_light, style_sheet_dark


class UIController:
    """Manage the passing of information from the splitter to the UI, and from
    user input to the UI and the splitter.

    Perhaps the most important class method is _poll, which is ran once per
    frame using a QTimer. This method updates the UI and handles all user
    inputs.

    UIController has no public attributes, as it is meant to operate after
    initialization without further input. For details about each attribute,
    see method documentation.
    """

    def __init__(self, application: QApplication, splitter: Splitter) -> None:
        """Initialize the UI, then update it each frame.

        Creates each UI window and then shows the main window.
        Connects pyqtSignals from each UI window to their respective slots.
        Sets initial flags and values used by poller.
        Starts the keyboard listener.
        Starts poller, which checks for user input and splitter outputs at
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

        style = self._get_style_sheet()
        self._main_window.setStyleSheet(style)
        self._settings_window.setStyleSheet(style)

        # Check if there's an update available and show message if so
        if settings.get_bool("CHECK_FOR_UPDATES"):
            latest_version = settings.get_latest_version()
            if not settings.version_ge(settings.VERSION_NUMBER, latest_version):
                msg = self._main_window.update_available_msg
                msg.setStyleSheet(style)
                msg.show()
                msg.raise_()  # Make sure msg isn't hidden behind app

        ########################
        #                      #
        # Poller Values, Flags #
        #                      #
        ########################

        # Tell _update_ui to update split labels
        # Should be set whenever the split image is modified
        self._redraw_split_labels = True

        # Tell _splitter to display reset image match percents, not split image
        # match percent
        self._show_reset_percents = False

        # Only update main_window's style sheet when it has changed
        self._most_recent_style_sheet = None

        # Only resize record icon when aspect ratio changes
        self._resize_record_icon = False
        self._record_active_pixmap = None
        self._record_idle_pixmap = None

        # Values for updating hotkeys in settings menu
        # (see _react_to_settings_menu_flags)
        self._hotkey_box_to_change = None
        self._hotkey_box_key_code = None
        self._hotkey_box_key_name = None
        self._hotkey_box_lock = Lock()

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

        # Values for keeping display awake (see _wake_display)
        self._last_wake_time = time.perf_counter()
        # Attempt wake after this many seconds. Should be < 1 min, since that's
        # the minimum allowed time to trigger display sleep on most OSs
        self._wake_interval = 45
        # MacOS-specific values (MacOS uses caffeinate)
        self._caffeinate_thread = Thread(target=self._caffeinate)
        self._caffeinate_thread_finished = True

        ######################
        #                    #
        # Main Window Config #
        #                    #
        ######################

        # Set layout
        self._set_main_window_layout()
        self._main_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )

        # "Update available" message box
        self._main_window.update_available_msg.buttonClicked.connect(
            self.update_available_msg_action
        )

        # Split directory line edit
        self._main_window.split_directory_box.clicked.connect(
            lambda: self._open_file_or_dir(settings.get_str("LAST_IMAGE_DIR"))
        )

        # Split directory button
        self._main_window.split_dir_button.clicked.connect(self._set_split_dir_path)

        # Video feed
        self._main_window.video_display.valid_single_click.connect(
            self._toggle_record_clips
        )
        self._main_window.video_display.valid_double_click.connect(
            self._set_record_dir_path
        )

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
        self._main_window.next_source_button.clicked.connect(self._splitter.restart)

        # Screenshot button
        self._main_window.screenshot_button.clicked.connect(self._take_screenshot)

        # Reload video button
        self._main_window.reconnect_button.clicked.connect(self._splitter.restart)

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
            lambda: self._open_url(settings.USER_MANUAL_URL)
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

        #################
        #               #
        # Start Polling #
        #               #
        #################

        # Start keyboard listener
        self._keyboard = UIKeyboardController()
        self._keyboard.start_listener(on_press=self._handle_key_press, on_release=None)

        # Start poller
        self._poller = QTimer()
        self._poller.setInterval(self._get_interval())
        self._poller.timeout.connect(self._poll)
        self._poller.start()

        self._main_window.show()

    ##################
    #                #
    # Helper Methods #
    #                #
    ##################

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

        If this method is ever used to accomplish something and it's not
        guaranteed that the program will be in focus, this may need to be
        rethought.
        """
        key_code = settings.get_str("UNDO_HOTKEY_CODE")
        if len(key_code) > 0:
            self._keyboard.press_and_release(key_code)
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
            self._keyboard.press_and_release(key_code)
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
            self._keyboard.press_and_release(key_code)
        else:
            self._request_reset_splits()

    def _request_previous_split(self) -> None:
        """Tell splitter.splits to call previous_split_image and ask
        splitter._look_for_split to reset its flags if needed.

        If self._splitter.match_percent is None, this means that
        splitter.look_for_split isn't active, and we can move to the next split
        image without causing a segmentation fault or breaking splitter flags.

        Otherwise, we know look_for_split is active, and we need to (1) pause
        it while we change split images for thread safety, then (2) reset its
        flags. We do this (or at least try to for 1 second) by setting the
        splitter.changing_splits flag, waiting for splitter to confirm it's
        paused (splitter sets its waiting_for_split_change flag). We change
        the split image, then unset changing_splits, which signals to splitter
        it can reset its flags.

        In this method and the next two, we also kill the recording before
        changing splits so, if recording is on, the recording has the chance
        to save, continue, or erase itself. Then at the end of the method, we
        restart the recording thread so we can do the next one (or in the case
        of request_next_split, so we can await the restarting of compare_split
        _thread and start recording when the next split becomes available).
        """
        # Kill recording
        self._splitter.safe_exit_record_thread()

        # Make sure UI image is updated
        self._redraw_split_labels = True

        # Go to next split, no need to worry about flags / thread safety
        if self._splitter.match_percent is None:
            self._splitter.splits.previous_split_image()

        # Pause splitter._look_for_split before getting next split
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

        # Restart recording
        self._splitter.restart_record_thread()

    def _request_next_split(self) -> None:
        """Tell splitter.splits to call next_split_image, and ask
        splitter._look_for_split to reset its flags if needed.

        If self._splitter.match_percent is None, this means that
        splitter.look_for_split isn't active, and we can move to the next split
        image without causing a segmentation fault or breaking splitter flags.

        Otherwise, we know look_for_split is active, and we need to (1) pause
        it while we change split images for thread safety, then (2) reset its
        flags. We do this (or at least try to for 1 second) by by setting the
        splitter.changing_splits flag, waiting for splitter to confirm it's
        paused (splitter sets its waiting_for_split_change flag). We change
        the split image, then unset changing_splits, which signals to splitter
        it can reset its flags.

        This method also kills the splitter's non-capture threads if we're on the
        last loop of the last split when this method is called, because if the
        run is over, the comparer stops until the user presses reset or
        unpauses. However, this only should happen if the last split is accessed
        by pressing the split hotkey or if the program found a match, so that
        users can still scroll back and forth between splits without shutting
        the thread down on accident, so we also check if this method is being
        called as the result of a hotkey press.
        """
        # Kill recording if not calling this method as the result of
        # a dummy split
        if not self._splitter.continue_recording:
            self._splitter.safe_exit_record_thread()

        # Kill splitter threads if we're on the last split
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
            self._splitter.safe_exit_compare_split_thread()
            self._splitter.safe_exit_compare_reset_thread()

        # Not on last split, or method not called by hotkey press
        else:

            # Make sure UI image is updated
            self._redraw_split_labels = True

            # Go to next split, no need to worry about flags / thread safety
            if self._splitter.match_percent is None:
                self._splitter.splits.next_split_image()

            # Pause splitter._look_for_split before getting next split
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

        # Restart recording if not calling this method as the result of
        # a dummy split
        if self._splitter.continue_recording:
            self._splitter.continue_recording = False
        else:
            self._splitter.restart_record_thread()

    def _request_reset_splits(self) -> None:
        """Tell splitter.splits to call reset_split_images, and ask
        splitter._look_for_split to reset its flags if necessary.

        Kill splitter's non-capture threads (this allows the splitter to exit
        gracefully if the split image directory has changed to an empty
        directory, for example). Restarts the threads if the split list isn't
        empty and if video is running.
        """
        # Kill recording
        self._splitter.safe_exit_record_thread()

        self._redraw_split_labels = True
        self._splitter.safe_exit_compare_split_thread()
        self._splitter.safe_exit_compare_reset_thread()
        self._splitter.splits.reset_split_images()

        if (
            len(self._splitter.splits.list) > 0
            and self._splitter.capture_thread.is_alive()
        ):
            self._splitter.restart_compare_split_thread()
            if self._splitter.splits.reset_image is not None:
                self._splitter.restart_compare_reset_thread()

        # Restart recording
        self._splitter.restart_record_thread()

    def _set_split_dir_path(self) -> None:
        """Prompt the user to select a split image directory, then open the new
        directory in a threadsafe manner.

        If the directory exists and is different from the last one, check if
        the dir is within the user's home directory. If not, show an error msg
        and re-run the method.

        Otherwise, change `LAST_IMAGE_DIR` to the new choice. Then reset splits
        so the new ones show up.
        """
        path = QFileDialog.getExistingDirectory(
            self._main_window,
            "Select splits folder",
            settings.get_str("LAST_IMAGE_DIR"),
        )
        if len(path) > 1 and path != settings.get_str("LAST_IMAGE_DIR"):
            if not path.startswith(settings.get_home_dir()):
                msg = self._main_window.err_invalid_dir_msg
                msg.setStyleSheet(self._get_style_sheet())
                msg.show()
                return self._set_split_dir_path()

            settings.set_value("LAST_IMAGE_DIR", path)
            self._set_split_directory_box_text()
            self._request_reset_splits()

    def _set_record_dir_path(self) -> None:
        """Prompt the user to select a recordings directory.

        If the directory exists and is different from the last one, check if
        the dir is within the user's home directory. If not, show an error msg
        and re-run the method.

        Otherwise, change `LAST_RECORD_DIR` to the new choice.
        """
        path = QFileDialog.getExistingDirectory(
            self._main_window,
            "Select recordings folder",
            settings.get_str("LAST_RECORD_DIR"),
        )
        if len(path) > 1 and path != settings.get_str("LAST_RECORD_DIR"):
            if not path.startswith(settings.get_home_dir()):
                msg = self._main_window.err_invalid_dir_msg
                msg.setStyleSheet(self._get_style_sheet())
                msg.show()
                return self._set_record_dir_path()

            settings.set_value("LAST_RECORD_DIR", path)

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
            self._open_url(f"{settings.REPO_URL}releases/latest")

        else:
            self._main_window.update_available_msg.close()

    def _show_reset_image_display(self) -> None:
        """Show the reset image, if it exists, over the current split image.

        Also force the match percent chart to show the match percents for the
        reset image.
        """
        reset_image = self._splitter.splits.reset_image
        split_display = self._main_window.split_display
        match_percent_label = self._main_window.match_percent_label
        split_name_label = self._main_window.split_name_label
        loop_label = self._main_window.split_loop_label
        loop_label_reset_text = self._main_window.split_loop_label_reset_txt

        # Set split name / loop label to reset image info
        split_name_label.setText(reset_image.name)
        loop_label.setText(loop_label_reset_text)

        # Set split image to reset image
        split_display.setPixmap(reset_image.pixmap)

        # Show reset image match percents instead of current split
        if settings.get_str("ASPECT_RATIO") != "4:3 (320x240)":
            match_percent_label.setText(self._main_window.match_reset_percent_txt)
        self._show_reset_percents = True

    def _hide_reset_image_display(self) -> None:
        """Remove reset image / info from UI."""
        match_percent_label = self._main_window.match_percent_label

        if settings.get_str("ASPECT_RATIO") == "4:3 (320x240)":
            match_percent_label.setText(self._main_window.match_percent_short_txt)
        else:
            match_percent_label.setText(self._main_window.match_percent_long_txt)

        self._redraw_split_labels = True  # Force UI to show split image again
        self._show_reset_percents = False

    def _exec_settings_window(self) -> None:
        """Set up and open the settings window UI."""
        self._settings_window.setFocus(True)  # Make sure no widgets have focus
        self._reset_settings()
        # On some platforms, the main window hides the settings window if we
        # don't set this flag
        self._settings_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )
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
            self._settings_window.always_on_top_checkbox: settings.get_bool(
                "ALWAYS_ON_TOP"
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
                settings.get_str("PREV_HOTKEY_NAME"),
                settings.get_str("PREV_HOTKEY_CODE"),
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
            settings.set_value(setting_string, value)

            # Send new FPS value to controller and splitter
            if spinbox == self._settings_window.fps_spinbox:
                self._poller.setInterval(self._get_interval())
                self._splitter.target_fps = value

        self._splitter.splits.set_default_threshold()
        self._splitter.splits.set_default_delay()
        self._splitter.splits.set_default_pause()

        # Checkboxes
        for checkbox, setting_string in {
            self._settings_window.open_screenshots_checkbox: "OPEN_SCREENSHOT_ON_CAPTURE",
            self._settings_window.start_with_video_checkbox: "START_WITH_VIDEO",
            self._settings_window.global_hotkeys_checkbox: "GLOBAL_HOTKEYS_ENABLED",
            self._settings_window.check_for_updates_checkbox: "CHECK_FOR_UPDATES",
            self._settings_window.always_on_top_checkbox: "ALWAYS_ON_TOP",
        }.items():
            if checkbox.checkState() == 0:
                value = False
            else:
                value = True
            settings.set_value(setting_string, value)

        self._main_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )
        # Required, since setting the above flag hides the window by default
        self._main_window.show()
        # Hack to make the transition look less awkward
        self._settings_window.show()

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
                "PREV_HOTKEY_NAME",
                "PREV_HOTKEY_CODE",
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
        # resize_images / _set_main_window_layout and setting style is expensive
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
            if theme == "light":
                settings.set_value("THEME", "light")
                style = style_sheet_light
            else:
                settings.set_value("THEME", "dark")
                style = style_sheet_dark
            self._main_window.setStyleSheet(style)
            self._settings_window.setStyleSheet(style)

    def _take_screenshot(self) -> None:
        """Write `spltter.comparison_frame` to a file (and optionally open it
        in machine's default image viewer).
        """
        frame = self._splitter.comparison_frame
        if frame is None:
            msg = self._main_window.screenshot_err_no_video
            msg.setStyleSheet(self._get_style_sheet())
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
                msg.setStyleSheet(self._get_style_sheet())
                msg.show()
                # Close message box after 10 seconds
                QTimer.singleShot(10000, lambda: msg.done(0))

        else:  # File couldn't be written to the split image directory
            msg = self._main_window.screenshot_err_no_file
            msg.setStyleSheet(self._get_style_sheet())
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))

    def get_file_number(self, dir: str) -> str:
        """Return the lowest three-digit number not already used as a .png
        filename suffix in the given directory.

        Args:
            dir (str): The target directory for the file.

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
                raise Exception(f"Error: over 1000 split images already in {dir}")

            leading_zeros = "0" * (3 - len(str(file_int)))
            file_number = f"{leading_zeros}{file_int}"
            files_with_same_number = glob.glob(f"{dir}/{file_number}*.png")
            if len(files_with_same_number) > 0:
                file_int += 1
            else:
                return file_number

    def _open_file_or_dir(self, path: str) -> None:
        """Enables cross-platform opening of a file or directory.

        If path points to a file, the file opens with the default application.
        If path points to a dir, the dir opens in the OS's file explorer.

        If the path doesn't exist, show an error message and return.

        On Linux, we have to spawn a child process that isn't using root, due
        to issues caused when trying to open the file explorer as root. To do
        that, we get the username from the environment variable $SUPER_USER and
        pass that value to subprocess.

        Args:
            path (str): The file to open.
        """
        if not Path(path).exists():
            msg = self._main_window.err_not_found_msg
            msg.setStyleSheet(self._get_style_sheet())
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            non_root_user = os.environ.get("SUDO_USER")
            subprocess.Popen(["xdg-open", path], user=non_root_user)

    def _open_url(self, url: str) -> None:
        """Open a URL using webbrowser or xdg-open, depending on platform.

        Use xdg-open on Linux so we can make sure to execute the process
        as user, not as root, to avoid crashes / permission errors.
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            webbrowser.open(url, new=0, autoraise=True)
        else:
            non_root_user = os.environ.get("SUDO_USER")
            subprocess.Popen(["xdg-open", url], user=non_root_user)

    def _get_style_sheet(self) -> str:
        """Retrieve the style sheet currently in use.

        Returns:
            str: The style sheet.
        """
        if settings.get_str("THEME") == "light":
            return style_sheet_light
        else:
            return style_sheet_dark

    def _toggle_record_clips(self) -> None:
        """Toggle "RECORD_CLIPS" in settings, but only if the video feed is
        currently active.
        """
        if self._splitter.capture_thread.is_alive():
            old_setting = settings.get_bool("RECORD_CLIPS")
            settings.set_value("RECORD_CLIPS", not old_setting)

            # Show recordings dest. hint when turned on
            if old_setting is False:
                self._main_window.video_info_overlay.set_text(
                    "Double click to change recordings folder"
                )

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
        # Video overlay icon will be resized after this call finishes
        self._resize_record_icon = True
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
        self._main_window.video_record_overlay.setGeometry(
            QRect(497 + left, 329 + top, 24, 24)
        )
        self._main_window.video_info_overlay.setGeometry(
            QRect(75 + left, 638 + top, 455, 30)
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
        self._main_window.video_record_overlay.setGeometry(
            QRect(351 + left, 323 + top, 16, 16)
        )
        self._main_window.video_info_overlay.setGeometry(
            QRect(72 + left, 520 + top, 310, 30)
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
        self._main_window.video_record_overlay.setGeometry(
            QRect(542 + left, 321 + top, 19, 19)
        )
        self._main_window.video_info_overlay.setGeometry(
            QRect(75 + left, 566 + top, 493, 30)
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
        self._main_window.video_record_overlay.setGeometry(
            QRect(467 + left, 319 + top, 16, 16)
        )
        self._main_window.video_info_overlay.setGeometry(
            QRect(72 + left, 524 + top, 422, 30)
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

        Widgets that are not affected by SHOW_MIN_VIEW alone may not be listed
        here, but may still only appear when minimal view is off.

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
        self._main_window.video_info_overlay.setVisible(visible)
        self._main_window.split_display.setVisible(visible)
        # Only display this when the other widgets are hidden
        self._main_window.split_info_min_label.setVisible(not visible)

    ###########
    #         #
    # Polling #
    #         #
    ###########

    def _poll(self) -> None:
        """Update the UI and splitter (should be called each frame).

        Uses information from UI, splitter, mouse, and keyboard to update UI
        and splitter. Also keeps the computer's display awake if the splitter
        is active.
        """
        self._update_video_feed()
        self._update_video_record_overlay()
        self._update_video_info_overlay()
        self._update_video_title()
        self._update_split_and_video_css()
        self._update_split_image_labels()
        self._update_split_delay_suspend()
        self._update_match_percents()
        self._update_pause_button()
        self._set_buttons_and_hotkeys_enabled()
        self._react_to_hotkey_flags()
        self._react_to_settings_menu_flags()
        self._react_to_split_flags()
        self._wake_display()

    def _update_video_feed(self) -> None:
        """Clear video if video is down; update video if video is alive."""
        if settings.get_bool("SHOW_MIN_VIEW"):
            return

        frame = self._splitter.frame_pixmap
        video = self._main_window.video_display

        # Video not connected, but video frame on UI
        if frame is None:
            if video.text() == "":
                video.setText(self._main_window.video_display_txt)
        # Video is connected, update it
        else:
            video.setPixmap(frame)

    def _update_video_record_overlay(self) -> None:
        """Show recording symbol when RECORD_CLIPS is True and video's on."""
        overlay = self._main_window.video_record_overlay
        video_on = self._splitter.capture_thread.is_alive()

        if settings.get_bool("SHOW_MIN_VIEW") or not video_on:
            overlay.setVisible(False)

        else:

            # Resizing the pixmap is expensive, so only do it when
            # aspect ratio changes
            if self._resize_record_icon:
                self._resize_record_icon = False

                active_img = self._main_window.record_active_img
                idle_img = self._main_window.record_idle_img

                self._record_active_pixmap = QPixmap(active_img).scaled(
                    overlay.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._record_idle_pixmap = QPixmap(idle_img).scaled(
                    overlay.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            if self._splitter.recording_enabled:
                pixmap = self._record_active_pixmap
            else:
                pixmap = self._record_idle_pixmap
            overlay.setPixmap(pixmap)

            visible = settings.get_bool("RECORD_CLIPS")
            overlay.setVisible(visible)

    def _update_video_info_overlay(self) -> None:
        """Update video info overlay text using output from _record."""
        text = self._splitter.result_text
        if text is not None:
            self._main_window.video_info_overlay.set_text(text)
            self._splitter.result_text = None

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

    def _update_split_and_video_css(self) -> None:
        """Generate new style sheet based on mouse interation with video feed
        and split image.

        Updating the style sheet ONLY when it has changed saves a ton of CPU,
        so we do that.
        """
        base_style = self._get_style_sheet()
        style_sheet = self._update_video_feed_css(base_style)
        style_sheet = self._update_split_image_css(style_sheet)

        if style_sheet != self._most_recent_style_sheet:
            self._most_recent_style_sheet = style_sheet
            self._main_window.setStyleSheet(style_sheet)

    def _update_video_feed_css(self, style_sheet: str) -> str:
        """Generate new style sheet on mouse interaction with video feed.

        Args:
            style_sheet (str): The base style sheet to which new CSS is added.

        Returns:
            str: The style sheet with modified CSS for the video feed widget.
        """
        # Don't react to mouse if video is down
        if self._splitter.capture_thread.is_alive():

            display = self._main_window.video_display
            record_overlay = self._main_window.video_record_overlay
            info_overlay = self._main_window.video_info_overlay

            # Clicked and hovered
            if display.clicked and display.hovered:
                style_sheet += """
                    QLabel#video_label {
                        border-width: 3px;
                    }
                """
                # Move image down / right a little bit to make it look clicked
                if not display.adjusted:
                    display.move(display.x() + 1, display.y() + 1)
                    record_overlay.move(record_overlay.x() + 1, record_overlay.y() + 1)
                    info_overlay.move(info_overlay.x() + 1, info_overlay.y() + 1)
                    display.adjusted = True

            # Clicked or hovered, but not both
            elif (display.clicked and not display.hovered) or (
                display.hovered and not display.clicked
            ):
                style_sheet += """
                    QLabel#video_label {
                        border-width: 3px;
                    }
                """
                # Move the image back to its original spot
                if display.adjusted:
                    display.move(display.x() - 1, display.y() - 1)
                    record_overlay.move(record_overlay.x() - 1, record_overlay.y() - 1)
                    info_overlay.move(info_overlay.x() - 1, info_overlay.y() - 1)
                    display.adjusted = False

            # Not clicked or hovered (just move it back)
            else:
                if display.adjusted:
                    display.move(display.x() - 1, display.y() - 1)
                    record_overlay.move(record_overlay.x() - 1, record_overlay.y() - 1)
                    info_overlay.move(info_overlay.x() - 1, info_overlay.y() - 1)
                    display.adjusted = False

        return style_sheet

    def _update_split_image_css(self, style_sheet: str) -> str:
        """Generate new style sheet on mouse interaction with video feed.

        Args:
            style_sheet (str): The base style sheet to which new CSS is added.

        Returns:
            str: The style sheet with modified CSS for the video feed widget.
        """
        reset_image = self._splitter.splits.reset_image
        if reset_image is not None:

            split_display = self._main_window.split_display
            split_overlay = self._main_window.split_overlay
            loop_label = self._main_window.split_loop_label
            reset_label_txt = self._main_window.split_loop_label_reset_txt

            # Show or hide image depending on mouse click status
            if split_display.clicked:
                self._show_reset_image_display()
            elif loop_label.text() == reset_label_txt:
                self._hide_reset_image_display()

            # Clicked and hovered
            if split_display.clicked and split_display.hovered:
                style_sheet += """
                    QLabel#image_label {
                        border-width: 3px;
                    }
                    QLabel#split_overlay {
                        border-width: 3px;
                    }
                """
                # Move image down / right a little bit to make it look clicked
                if not split_display.adjusted:
                    split_display.move(split_display.x() + 1, split_display.y() + 1)
                    split_overlay.move(split_overlay.x() + 1, split_overlay.y() + 1)
                    split_display.adjusted = True

            # Clicked or hovered, but not both
            elif (split_display.clicked and not split_display.hovered) or (
                split_display.hovered and not split_display.clicked
            ):
                style_sheet += """
                    QLabel#image_label {
                        border-width: 3px;
                    }
                    QLabel#split_overlay {
                        border-width: 3px;
                    }
                """
                # Move the image back to its original spot
                if split_display.adjusted:
                    split_display.move(split_display.x() - 1, split_display.y() - 1)
                    split_overlay.move(split_overlay.x() - 1, split_overlay.y() - 1)
                    split_display.adjusted = False

            # Not clicked or hovered (just move image back)
            else:
                if split_display.adjusted:
                    split_display.move(split_display.x() - 1, split_display.y() - 1)
                    split_overlay.move(split_overlay.x() - 1, split_overlay.y() - 1)
                    split_display.adjusted = False

        return style_sheet

    def _update_split_image_labels(self) -> None:
        """Update split name, loops, and image."""
        current_index = self._splitter.splits.current_image_index
        current_loop = self._splitter.splits.current_loop
        split_display = self._main_window.split_display
        reset_image = self._splitter.splits.reset_image
        split_label = self._main_window.split_name_label
        loop_label = self._main_window.split_loop_label
        splits_down_txt = self._main_window.split_display_txt
        splits_min_label = self._main_window.split_info_min_label

        # No splits loaded, but UI showing split image
        if current_index is None:
            if split_display.text() != splits_down_txt:
                # Only show splits down text if reset image isn't being viewed
                if reset_image is None or not split_display.clicked:
                    split_display.setText(splits_down_txt)
                    split_label.setText("")
                    loop_label.setText("")

                # Fix min view label
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
        """Display remaining delay or suspend time on the split image overlay."""
        overlay = self._main_window.split_overlay
        split_delay = self._splitter.split_delay_remaining
        reset_delay = self._splitter.reset_delay_remaining
        suspend = self._splitter.suspend_remaining
        min_view = settings.get_bool("SHOW_MIN_VIEW")

        # Splitter is delaying pre-split
        if split_delay is not None and not min_view:
            overlay.setVisible(True)
            if split_delay < 60:  # Less than 1 minute, so we show special text.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                delay_txt = self._main_window.overlay_split_delay_txt_secs
                overlay.setText(delay_txt.format(max(min(split_delay, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=split_delay)
                delay_txt = self._main_window.overlay_split_delay_txt_mins
                if split_delay < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(delay_txt.format(str(delta)[3:]).split(".")[0])
                elif split_delay < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(delay_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(delay_txt.format(str(delta)).split(".")[0])

        # Splitter is delaying pre-reset
        elif reset_delay is not None and not min_view:
            overlay.setVisible(True)
            if reset_delay < 60:  # Less than 1 minute, so we show special text.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                delay_txt = self._main_window.overlay_reset_delay_txt_secs
                overlay.setText(delay_txt.format(max(min(reset_delay, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=reset_delay)
                delay_txt = self._main_window.overlay_reset_delay_txt_mins
                if reset_delay < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(delay_txt.format(str(delta)[3:]).split(".")[0])
                elif reset_delay < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(delay_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(delay_txt.format(str(delta)).split(".")[0])

        # Splitter is pausing post-split
        elif suspend is not None and not min_view:
            overlay.setVisible(True)
            if suspend < 60:  # Less than 1 minute, so we show special txt.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                pause_txt = self._main_window.overlay_pause_txt_secs
                overlay.setText(pause_txt.format(max(min(suspend, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=suspend)
                pause_txt = self._main_window.overlay_pause_txt_mins
                if suspend < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(pause_txt.format(str(delta)[3:]).split(".")[0])
                elif suspend < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(pause_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(pause_txt.format(str(delta)).split(".")[0])

        # Splitter isn't pausing or delaying, but the overlay is showing
        elif overlay.text() != "":
            overlay.setVisible(False)
            overlay.setText("")

    def _update_match_percents(self):
        """Update match percents or set them to blank.

        When self._show_reset_percents is True, shows the match percent for the
        reset image instead of the current split image.
        """
        decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
        format_str = f"{{:.{decimals}f}}"
        null_str = self._null_match_percent_string(decimals)
        if self._show_reset_percents:
            match_percent = self._splitter.match_reset_percent
            high_percent = self._splitter.highest_reset_percent
        else:
            match_percent = self._splitter.match_percent
            high_percent = self._splitter.highest_percent
        match_label = self._main_window.match_percent
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
            if self._show_reset_percents:
                threshold = self._splitter.splits.reset_image.threshold
            else:
                threshold = self._splitter.splits.list[current_index].threshold
            thresh_label.setText(format_str.format(threshold * 100))

    def _update_pause_button(self):
        """Adjust the length and content of the pause button's text according
        to aspect ratio and whether the splitter is active.

        Rely on self._splitter.match_percent to detect whether the splitter is
        active, since this particular value is never None when the splitter is
        active.
        """
        splitter_active = self._splitter.match_percent is not None
        pause_button = self._main_window.pause_button
        show_short_text = (
            settings.get_bool("SHOW_MIN_VIEW")
            or settings.get_str("ASPECT_RATIO") == "4:3 (320x240)"
        )

        if show_short_text:
            if splitter_active:
                pause_button.setText(self._main_window.pause_short_txt)
            else:
                pause_button.setText(self._main_window.unpause_short_txt)

        else:
            if splitter_active:
                pause_button.setText(self._main_window.pause_long_txt)
            else:
                pause_button.setText(self._main_window.unpause_long_txt)

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

            # Disable split, undo, skip, previous, next split, pause, record
            self._split_hotkey_enabled = False
            self._undo_hotkey_enabled = False
            self._skip_hotkey_enabled = False
            self._main_window.undo_button.setEnabled(False)
            self._main_window.skip_button.setEnabled(False)
            self._main_window.previous_button.setEnabled(False)
            self._main_window.next_button.setEnabled(False)
            self._main_window.pause_button.setEnabled(False)
            self._splitter.recording_enabled = False

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

            # Enable record if we're not on the very first split image /
            # finished with the last split, and we're comparing splits
            if self._splitter.compare_split_thread.is_alive() and not (
                current_split_index == 0 and loop == 1
            ):
                self._splitter.recording_enabled = True
            else:
                self._splitter.recording_enabled = False

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
        """Calculate the rate at which poller should poll.

        The minimum is 20 Hz (represented by the 50 ms value below). Any
        slower than 20 Hz and the UI starts to look pretty bad.

        1000 is used because that is the number of ms in a second.

        Normally it would make sense to keep the UI at a constant 60 FPS, but
        we're letting the user throttle the framerate anyway, and throttling
        this value can save CPU -- not a ton, but around 10% on my machine when
        dropping from 60FPS to 20FPS for the UI loop.

        Returns:
            int: The amount of time (ms) the poller waits between calls.
        """
        return min(1000 // settings.get_int("FPS"), 50)

    def _handle_key_press(
        self, key: Union["pynput.keyboard.key", "keyboard.KeyboardEvent"]
    ) -> None:
        """Process key presses, setting flags if the key is a hotkey.

        Called each time any key is pressed, whether or not the program is in
        focus. This method has two main uses:
            1) Updates users' custom hotkey bindings. It does this by checking
                if a given hotkey "line edit" has focus and, if so, setting
                flags so its name and key code are updated.

                Uses a lock so the poller doesn't try to update these values as
                they're being written (the worst case would be setting a hotkey
                with the correct name but wrong key code -- unlikely but not
                impossible).

            2) If a hotkey is pressed, sets a flag indicating it was pressed.

        We set flags when keys are pressed instead of directly calling a method
        because PyQt5 doesn't play nice when other threads try to manipulate
        the GUI. Doing so often causes a trace trap / segmentation fault.

        Args:
            key: Wrapper containing info about the key that was pressed. For
                more information, see the ui_keyboard_controller module.
        """
        # Get the key's name and internal value. If the key is not an
        # alphanumeric key, the try block throws AttributeError.
        key_name, key_code = self._keyboard.parse_key_info(key)

        # Some keys aren't handled very well by pynput -- they return a key
        # code but no name. I don't have the resources to compile an exhaustive
        # list of codes that correspond to names on different platforms, so I
        # think it's better to just have them do nothing for now.
        if key_name is None:
            return

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

                # Set flags to be picked up by _react_to_settings_menu_flags
                with self._hotkey_box_lock:
                    self._hotkey_box_to_change = hotkey_box
                    self._hotkey_box_key_code = key_code
                    self._hotkey_box_key_name = key_name

                # Take focus off hotkey box so hotkey saves properly
                # (needed on some Linux versions)
                if platform.system() != "Windows" and platform.system() != "Darwin":
                    hotkey_box.clearFocus()

                return

        # Use #2 (set "hotkey pressed" flag for _react_to_hotkey_flags)
        if not self._settings_window.isVisible():
            for hotkey_pressed, setting in {
                "_split_hotkey_pressed": ("SPLIT_HOTKEY_NAME", "SPLIT_HOTKEY_CODE"),
                "_reset_hotkey_pressed": ("RESET_HOTKEY_NAME", "RESET_HOTKEY_CODE"),
                "_undo_hotkey_pressed": ("UNDO_HOTKEY_NAME", "UNDO_HOTKEY_CODE"),
                "_skip_hotkey_pressed": ("SKIP_HOTKEY_NAME", "SKIP_HOTKEY_CODE"),
                "_previous_hotkey_pressed": ("PREV_HOTKEY_NAME", "PREV_HOTKEY_CODE"),
                "_next_hotkey_pressed": ("NEXT_HOTKEY_NAME", "NEXT_HOTKEY_CODE"),
                "_screenshot_hotkey_pressed": (
                    "SCREENSHOT_HOTKEY_NAME",
                    "SCREENSHOT_HOTKEY_CODE",
                ),
                "_toggle_hotkeys_hotkey_pressed": (
                    "TOGGLE_HOTKEYS_HOTKEY_NAME",
                    "TOGGLE_HOTKEYS_HOTKEY_CODE",
                ),
            }.items():
                settings_name = settings.get_str(setting[0])
                settings_code = settings.get_str(setting[1])
                if str(key_name) == settings_name and str(key_code) == settings_code:
                    # Use setattr because that allows us to use this dict format
                    setattr(self, hotkey_pressed, True)

    def _react_to_hotkey_flags(self) -> None:
        """React to the flags set in _handle_key_press for hotkeys.

        When a hotkey is pressed, do its action if hotkeys are allowed now.
        Then, unset the flag no matter what.

        The toggle_hotkeys hotkey has no hotkey_presses_allowed check because
        it is always enabled, even when global hotkeys are disabled and the
        program isn't in focus. This is to make it easy for the user to enable/
        disable global hotkeys without having to click the app back in focus.

        Pressing the split hotkey also sets a flag telling _record to save its
        current recording.
        """
        global_hotkeys_enabled = settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
        hotkey_presses_allowed = (
            global_hotkeys_enabled or self._application.focusWindow() is not None
        )

        if self._toggle_hotkeys_hotkey_pressed:
            settings.set_value("GLOBAL_HOTKEYS_ENABLED", not global_hotkeys_enabled)
            self._toggle_hotkeys_hotkey_pressed = False

        elif self._split_hotkey_pressed:
            if self._split_hotkey_enabled and hotkey_presses_allowed:

                # Set appropriate flag for splitter._record. This is redundant
                # if _split_hotkey_pressed was set as the result of normal_
                # split_action being set, but not if this flag was set as the
                # result of an actual hotkey press, which is why we need this.
                split_index = self._splitter.splits.current_image_index
                if split_index is not None:
                    split = self._splitter.splits.list[split_index]
                    if split.dummy_flag:
                        self._splitter.continue_recording = True
                    else:
                        self._splitter.save_recording = True

                self._request_next_split()
            self._split_hotkey_pressed = False

        elif self._reset_hotkey_pressed:
            if hotkey_presses_allowed:
                self._request_reset_splits()
            self._reset_hotkey_pressed = False

        elif self._undo_hotkey_pressed:
            if self._undo_hotkey_enabled and hotkey_presses_allowed:
                self._request_previous_split()
            self._undo_hotkey_pressed = False

        elif self._skip_hotkey_pressed:
            if self._skip_hotkey_enabled and hotkey_presses_allowed:
                self._request_next_split()
            self._skip_hotkey_pressed = False

        elif self._previous_hotkey_pressed:
            if hotkey_presses_allowed:
                self._main_window.previous_button.click()
            self._previous_hotkey_pressed = False

        elif self._next_hotkey_pressed:
            if hotkey_presses_allowed:
                self._main_window.next_button.click()
            self._next_hotkey_pressed = False

        elif self._screenshot_hotkey_pressed:
            if hotkey_presses_allowed:
                self._main_window.screenshot_button.click()
            self._screenshot_hotkey_pressed = False

    def _react_to_settings_menu_flags(self) -> None:
        """React to the flags set in _handle_key_press for updating hotkeys.

        If _handle_hotkey_press has set self._hotkey_box_to_change to a hotkey
        box, use the values stored in _hotkey_box_key_name and _hotkey_box_key
        _code to update the hotkey box. Then, reset _hotkey_box_to_change back
        to None.

        We use _hotkey_box_lock to make sure the values passed from _handle_key
        _press aren't overwritten mid-method.

        Setting the hotkey box's attributes directly from _handle_hotkey_press
        is simpler, but PyQt5 doesn't like it and it occasionally causes a
        segmentation fault.
        """
        with self._hotkey_box_lock:
            if self._hotkey_box_to_change is None:
                return

            hotkey_box = self._hotkey_box_to_change
            key_name = self._hotkey_box_key_name
            key_code = self._hotkey_box_key_code

            # Set box attributes
            hotkey_box.setText(key_name)
            hotkey_box.key_code = key_code

            # Reset font size to the default
            f_size = self._settings_window.fontInfo().pointSize()
            hotkey_box.setStyleSheet(f"KeyLineEdit{{font-size: {f_size}pt;}}")

            # If the key name is too big for the box, resize the font down
            # until it fits. Subtract 10 from the width so that there's a
            # little bit of padding on the right-hand side of the box.
            while hotkey_box.get_text_width() >= hotkey_box.width() - 10:
                f_size = hotkey_box.get_font_size() - 1
                hotkey_box.setStyleSheet(f"KeyLineEdit{{font-size: {f_size}pt;}}")

            self._hotkey_box_to_change = None

    def _react_to_split_flags(self) -> None:
        """Press a hotkey & go to next split when self._splitter sets flags.

        If the normal_split_action flag is set but no split hotkey is assigned,
        or the hotkey wasn't heard by the application, request the next split
        image manually.
        """
        # Pause split (press pause hotkey)
        if self._splitter.pause_split_action:
            self._splitter.pause_split_action = False
            key_code = settings.get_str("PAUSE_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
            self._request_next_split()

        # Dummy split (silently advance to next split image)
        elif self._splitter.dummy_split_action:
            self._splitter.dummy_split_action = False
            self._request_next_split()

        # Normal split (press split hotkey)
        elif self._splitter.normal_split_action:
            self._splitter.normal_split_action = False
            key_code = settings.get_str("SPLIT_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
            # If key didn't get pressed, OR if it did get pressed but global
            # hotkeys are off and the app isn't in focus, move the split image
            # forward, since pressing the key on its own won't do that
            hotkey_not_caught = (
                self._application.focusWindow() is None
                and not settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
            )
            if len(key_code) == 0 or hotkey_not_caught:
                self._request_next_split()

        # Reset splits (press reset hotkey)
        elif self._splitter.reset_split_action:
            self._splitter.reset_split_action = False
            key_code = settings.get_str("RESET_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
            # If key didn't get pressed, OR if it did get pressed but global
            # hotkeys are off and the app isn't in focus, go back to the first
            # split image, since pressing the key on its own won't do that
            hotkey_not_caught = (
                self._application.focusWindow() is None
                and not settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
            )
            if len(key_code) == 0 or hotkey_not_caught:
                self._request_reset_splits()

    def _wake_display(self):
        """Keep the display awake when the splitter is active.

        Each time this method is called, check if at least _wake_interval
        seconds have passed. If so, update _last_wake_time to the current time,
        and check if the splitter is active or delaying / suspending with a
        countdown. If it is, attempt to wake the display (the method differs by
        operating system).

        MacOS method: caffeinate (key release as fallback, see below)
        Even if called with a 1 second timeout, as we do here, caffeinate
        resets the OS's sleep countdown, so we only need to run it about once a
        minute (1 minute is the lowest sleep timeout on MacOS) to prevent the
        screen from dimming. We use a separate thread to reduce overhead
        (creating a new thread requires less overhead than calling
        subprocess.Popen, once, and we only need to do it once, instead of once
        every _wake_interval).
        If caffeinate isn't available, fall back to the "release key" method.
        (see below). Caffeinate is preferred because, unlike releasing a key,
        it doesn't force the keyboard's backlight to stay on, but releasing a
        key at least keeps the display alive.

        Windows method: Key release
        This is the least invasive solution that doesn't require permanently
        changing a registry or system value, which would prevent the machine
        from sleeping normally if this program exits abruptly. Key releases
        instead of key presses or mouse clicks / wiggles are ideal because
        releasing a key doesn't require the key to be pressed, and does NOT
        interrupt an actual, physical keypress being held by the user, so users
        should never notice that anything is happening behind the scenes. It's
        hacky but hopefully relatively uninvasive, and its effects subside as
        soon as the program stops running.

        Linux: Key release (untested, may not be reliable)
        """
        if time.perf_counter() - self._last_wake_time >= self._wake_interval:
            self._last_wake_time = time.perf_counter()
            splitter_active = self._splitter.compare_split_thread.is_alive()

            # Key should be alphanumeric to work cross platform; beyond that it
            # doesn't matter, since the user won't detect its release
            key = "a"

            # MacOS: Try caffeinate, fall back to key release if necessary
            if platform.system() == "Darwin":
                if splitter_active:

                    caffeinate_path = self._get_exec_path("caffeinate")

                    # No caffeinate, use fallback
                    if caffeinate_path is None:
                        self._keyboard.release(key)

                    # Caffeinate exists; start thread if it hasn't been started
                    elif not self._caffeinate_thread.is_alive():
                        self._caffeinate_thread_finished = False
                        self._caffeinate_thread = Thread(
                            target=self._caffeinate, args=(caffeinate_path,)
                        )
                        self._caffeinate_thread.daemon = True
                        self._caffeinate_thread.start()

                # Splitter inactive; kill thread (join not needed, will die)
                else:
                    self._caffeinate_thread_finished = True

            # Winodws / Linux: release a key if splitter active
            elif splitter_active:
                self._keyboard.release(key)

    def _caffeinate(self, caffeinate_path: str) -> None:
        """Use built-in caffeinate to keep the machine's display on (MacOS).

        A 1-second timeout is used because caffeinate resets the sleep timer
        (i.e. it doesn't need to be constantly running). This is good because
        it's hard to reliably terminate an ongoing caffeinate process; this way
        we guarantee that users' sleep settings will return to normal after the
        program terminates.
        """
        while not self._caffeinate_thread_finished:
            subprocess.Popen([caffeinate_path, "-d", "-t", "1"])
            time.sleep(self._wake_interval)

    def _get_exec_path(self, name: str) -> Optional[str]:
        """Return the path to an executable file, if it exists.

        Args:
            name (str): The name (not path) of an exectable file. Ex: "grep"

        Returns:
            str: The absolute path to the executable, if it exists.
        """
        if platform.system() == "Windows":
            search = "where"
        else:
            search = "which"
        try:
            return subprocess.check_output([search, name]).decode().strip()

        # The executable doesn't exist (or at least isn't on PATH)
        except subprocess.CalledProcessError:
            return None
