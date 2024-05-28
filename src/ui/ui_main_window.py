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

"""Template for the main window view. Most functionality is not provided and
should be provided in a controller class.
"""


import platform

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import (QAction, QLabel, QLineEdit, QMainWindow, QMenuBar,
                             QMessageBox, QPushButton, QShortcut, QWidget)

import settings
from settings import VERSION_NUMBER


class UIMainWindow(QMainWindow):
    """Initialize main window widgets and allow the main window to be executed.

    The below widgets are initialized when a UIMainWindow instance is created
    but, with few exceptions, they are connected to their helper methods in
    ui_controller. This is to enforce a view-controller structure, where this
    file functions primarily as a view.

    Inherits QMainWindow and, by extension, its attributes and methods. See
    help(PyQt5.QtWidgets.QMainWindow).

    Attributes:
        HEIGHT_CORRECTION (int): The pixels the window's height is extended by.
            Useful on Windows, where QMenuBar is displayed on top of the main
            window, increasing window size.
        LEFT_EDGE_CORRECTION (int): The pixels the window's widgets are all
            pushed to the right.
        TOP_EDGE_CORRECTION (int): The pixels the window's widgets are all
            pushed down.
        close_window_shortcut (QShortcut): Keyboard shortcut to close the main
            window.
        current_match_percent (QLabel): Displays the current image match
            percent, or a null string (see ui_controller._update_ui for
            details).
        current_match_percent_label (QLabel): Displays text describing the
            current image match percent.
        current_match_percent_sign (QLabel): Displays a percent sign after the
            current image match percent.
        help_action (QAction): Adds a menu bar item which triggers opening the
            user manual.
        highest_match_percent (QLabel): Displays the highest image match
            percent so far, or a null string (see ui_controller._update_ui for
            details).
        highest_match_percent_label (QLabel): Displays text describing the
            highest image match percent.
        highest_match_percent_sign (QLabel): Displays a percent sign after the
            highest image match percent.
        minimal_view_button (QPushButton): Allows the user to show or hide
            minimal view.
        minimal_view_no_splits_label (QLabel): In minimal view, displays text
            saying no splits are active.
        next_source_button (QPushButton): Allows the user to attempt to connect
            to the next video source, if one exists.
        next_split_button (QPushButton): Allows the user to move to the next
            split without triggering any hotkeys.
        pause_comparison_button (QPushButton): Allows the user to stop the
            splitter from comparing images to the split image.
        pause_comparison_button_pause_text_default (str): Text prompting the
            user to pause the splitter (default length).
        pause_comparison_button_pause_text_truncated (str): Text prompting the
            user to pause the splitter (short length).
        pause_comparison_button_unpause_text_default (str): Text prompting the
            user to unpause the splitter (default length).
        pause_comparison_button_unpause_text_truncated (str): Text prompting
            the user to unpause the splitter (short length).
        previous_split_button (QPushButton): Allows the user to move to the
            previous split without triggering any hotkeys.
        reload_video_button (QPushButton): Allows the user to attempt to
            reconnect to the current video source.
        reset_splits_button (QPushButton): Allows the user to reset a run. This
            also refreshes the split image list if more splits have been added
            to the folder or if names have been updated.
        screenshot_button (QPushButton): Allows the user to take a screenshot
            of the current video frame and save it to the current split
            directory.
        screenshot_error_message_box (QMessageBox): Message to display if the
            screenshot button was pressed but the screenshot couldn't be taken.
        screenshot_success_message_box (QMessageBox): Message to display if a
            screenshot was taken successfully and the user doesn't have "open
            screenshots on capture" enabled.
        settings_action (QAction): Adds a menu bar item which triggers opening
            the settings menu.
        skip_split_button (QPushButton): Allows the user to move to the next
            split. Does the same thing as pressing the skip split hotkey.
        split_directory_button (QPushButton): Allows the user to select a split
            image folder.
        split_directory_line_edit (QLineEdit): Shows the path to the current
            split image folder.
        split_image_default_text (str): Informs the user there are no split
            images loaded currently.
        split_image_display (QLabel): Display split images if loaded, or else 
            show the split_image_default_text.
        split_image_loop_label (QLabel): Informs the user about the current
            split's loop information.
        split_image_overlay (QLabel): Informs the user that a pre-split delay
            or post-split pause is taking place.
        split_name_label (QLabel): Shows the current split name.
        threshold_match_percent (QLabel): Displays the threshold image match
            percent for the current split, or a null string (see
            ui_controller._update_ui for details).
        threshold_match_percent_label (QLabel): Displays text describing the
            threshold image match percent.
        threshold_match_percent_sign (QLabel): Displays a percent sign after
            the threshold image match percent.
        undo_split_button (QPushButton): Allows the user to move to the
            previous split. Does the same thing as pressing the undo split
            hotkey.
        video_feed_display (QLabel): Display video feed if connected, or else
            show the video_feed_display_default_text.
        video_feed_display_default_text (str): Informs the user there is no
            video connected currently.
        video_feed_label (QLabel): Show information about the current video if
            loaded.
        video_feed_label_down_text_min (str): In minimal view, inform the user
            there is no video connected.
        video_feed_label_live_text (str): In full view, inform the user the
            video is connected.
        video_feed_label_live_text_min (str): In minimal view, inform the user
            the video is connected.
    """
    def __init__(self) -> None:
        """Initialize all widgets in the main window.
        """
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        self._container = QWidget(self)
        self.setCentralWidget(self._container)

        self.setWindowTitle(f"Pilgrim Autosplitter v{VERSION_NUMBER}")

        # Menu bar
        self.settings_action = QAction("Open settings menu", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.help_action = QAction("Help", self)

        self._menu_bar = QMenuBar(self._container)
        self.setMenuBar(self._menu_bar)

        self._menu_bar_pilgrim_autosplitter = self._menu_bar.addMenu("&Autosplitter Settings")
        self._menu_bar_pilgrim_autosplitter.addAction(self.settings_action)
        self._menu_bar_pilgrim_autosplitter.addAction(self.help_action)

        # Layout attributes
        self.LEFT_EDGE_CORRECTION = -44
        self.TOP_EDGE_CORRECTION = -215
        if platform.system() == "Windows":
            self.HEIGHT_CORRECTION = 22  # Windows adds the menu bar as a tab-style widget, so the window needs to be taller
        else:
            self.HEIGHT_CORRECTION = 0

        # Close app convenience shortcut
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)

        ###########
        #         #
        # Widgets #
        #         #
        ###########

        # Split directory button and display
        self.split_directory_button = QPushButton("Select split image folder:", self._container)
        self.split_directory_button.setFocusPolicy(Qt.NoFocus)

        self.split_directory_line_edit = QLineEdit(self._container)
        self.split_directory_line_edit.setAlignment(Qt.AlignLeft)
        self.split_directory_line_edit.setText(settings.get_str("LAST_IMAGE_DIR"))
        self.split_directory_line_edit.setEnabled(False)

        # Video feed
        self.video_feed_label = QLabel(self._container)
        self.video_feed_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.video_feed_label.setAlignment(Qt.AlignCenter)

        self.video_feed_label_live_text = "Video feed"
        self.video_feed_label_down_text_min = "Video status:   down"
        self.video_feed_label_live_text_min = "Video status:   healthy"

        self.video_feed_display = QLabel(self._container)
        self.video_feed_display.setAlignment(Qt.AlignCenter)
        self.video_feed_display.setObjectName("image_label_inactive")

        self.video_feed_display_default_text = "No video feed detected"        

        # Split image
        self.minimal_view_no_splits_label = QLabel(self._container)
        self.minimal_view_no_splits_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.minimal_view_no_splits_label.setAlignment(Qt.AlignCenter)
        self.minimal_view_no_splits_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 251, 31))  # Always in the same spot

        self.split_name_label = QLabel(self._container)
        self.split_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.split_image_loop_label = QLabel(self._container)
        self.split_image_loop_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_image_loop_label.setAlignment(Qt.AlignCenter)

        self.split_image_display = QLabel(self._container)
        self.split_image_display.setAlignment(Qt.AlignCenter)
        self.split_image_display.setObjectName("image_label_inactive")
        self.split_image_default_text = "No split images loaded"

        self.split_image_overlay = QLabel(self._container)
        self.split_image_overlay.setAlignment(Qt.AlignCenter)
        self.split_image_overlay.setObjectName("split_image_overlay")
        self.split_image_overlay.setVisible(False)

        # Match percent (current)
        self.current_match_percent_label = QLabel(self._container)
        self.current_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent = QLabel(self._container)
        self.current_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent_sign = QLabel("%", self._container)
        self.current_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        
        # Match percent (highest)
        self.highest_match_percent_label = QLabel(self._container)
        self.highest_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent = QLabel(self._container)
        self.highest_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent_sign = QLabel("%", self._container)
        self.highest_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Match percent (threshold)
        self.threshold_match_percent_label = QLabel(self._container)
        self.threshold_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent = QLabel(self._container)
        self.threshold_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent_sign = QLabel("%", self._container)
        self.threshold_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Minimal view button
        self.minimal_view_button = QPushButton(self._container)
        self.minimal_view_button.setFocusPolicy(Qt.NoFocus)

        # Next source button
        self.next_source_button = QPushButton("Next source", self._container)
        self.next_source_button.setFocusPolicy(Qt.NoFocus)

        # Screenshot button
        self.screenshot_button = QPushButton(self._container)
        self.screenshot_button.setEnabled(False)
        self.screenshot_button.setFocusPolicy(Qt.NoFocus)

        # Screenshot success message box
        self.screenshot_success_message_box = QMessageBox(self)
        self.screenshot_success_message_box.setText("Screenshot taken")

        # Screenshot error message box
        self.screenshot_error_message_box = QMessageBox(self)
        self.screenshot_error_message_box.setText("Could not take screenshot")
        self.screenshot_error_message_box.setInformativeText("No video feed detected. Please make sure video feed is active and try again.")
        self.screenshot_error_message_box.setIcon(QMessageBox.Warning)

        # Reload video button
        self.reload_video_button = QPushButton("Reconnect video", self._container)
        self.reload_video_button.setFocusPolicy(Qt.NoFocus)

        # Previous split button
        self.previous_split_button = QPushButton("<", self._container)
        self.previous_split_button.setEnabled(False)
        self.previous_split_button.setFocusPolicy(Qt.NoFocus)

        # Next split button
        self.next_split_button = QPushButton(">", self._container)
        self.next_split_button.setEnabled(False)
        self.next_split_button.setFocusPolicy(Qt.NoFocus)

        # Skip split button
        self.skip_split_button = QPushButton(self._container)
        self.skip_split_button.setEnabled(False)
        self.skip_split_button.setFocusPolicy(Qt.NoFocus)

        # Undo split button
        self.undo_split_button = QPushButton(self._container)
        self.undo_split_button.setEnabled(False)
        self.undo_split_button.setFocusPolicy(Qt.NoFocus)

        # Pause comparison / unpause comparison button
        self.pause_comparison_button = QPushButton(self._container)
        self.pause_comparison_button.setEnabled(False)
        self.pause_comparison_button.setFocusPolicy(Qt.NoFocus)

        self.pause_comparison_button_pause_text_default = "Pause comparison"
        self.pause_comparison_button_pause_text_truncated = "Pause comp"
        self.pause_comparison_button_unpause_text_default = "Unpause comparison"
        self.pause_comparison_button_unpause_text_truncated = "Unpause comp"

        # Reset splits button
        self.reset_splits_button = QPushButton(self._container)
        self.reset_splits_button.setEnabled(False)
        self.reset_splits_button.setFocusPolicy(Qt.NoFocus)
