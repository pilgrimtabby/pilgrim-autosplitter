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

from PyQt5.QtCore import QRect, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QAction,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QShortcut,
    QWidget,
)

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
        match_percent (QLabel): Displays the current image match
            percent, or a null string (see ui_controller._update_ui for
            details).
        match_percent_label (QLabel): Displays text describing the
            current image match percent.
        match_percent_sign (QLabel): Displays a percent sign after the
            current image match percent.
        err_not_found_msg (QMessageBox): Message to display if the
            controller attempts to open a file or directory that doesn't exist.
        help_action (QAction): Adds a menu bar item which triggers opening the
            user manual.
        highest_percent (QLabel): Displays the highest image match
            percent so far, or a null string (see ui_controller._update_ui for
            details).
        highest_percent_label (QLabel): Displays text describing the
            highest image match percent.
        highest_percent_sign (QLabel): Displays a percent sign after the
            highest image match percent.
        min_view_button (QPushButton): Allows the user to show or hide
            minimal view.
        split_info_min_label (QLabel): In minimal view, displays text
            saying no splits are active.
        next_source_button (QPushButton): Allows the user to attempt to connect
            to the next video source, if one exists.
        next_button (QPushButton): Allows the user to move to the next
            split without triggering any hotkeys.
        pause_button (QPushButton): Allows the user to stop the
            splitter from comparing images to the split image.
        pause_button_overlay_pause_txt_default (str): Text prompting the
            user to pause the splitter (default length).
        pause_button_overlay_pause_txt_truncated (str): Text prompting the
            user to pause the splitter (short length).
        pause_button_unoverlay_pause_txt_default (str): Text prompting the
            user to unpause the splitter (default length).
        pause_button_unoverlay_pause_txt_truncated (str): Text prompting
            the user to unpause the splitter (short length).
        previous_button (QPushButton): Allows the user to move to the
            previous split without triggering any hotkeys.
        reconnect_button (QPushButton): Allows the user to attempt to
            reconnect to the current video source.
        reset_button (QPushButton): Allows the user to reset a run. This
            also refreshes the split image list if more splits have been added
            to the folder or if names have been updated.
        screenshot_button (QPushButton): Allows the user to take a screenshot
            of the current video frame and save it to the current split
            directory.
        screenshot_err_no_video (QMessageBox): Message to display
            if the screenshot button or hotkey was pressed, ui_controller.
            take_screenshot was called, but splitter.comparison_frame was None.
        screenshot_err_no_file (QMessageBox): Message to display
            if the screenshot was captured but could not be written to a file
            (99% this should come down to permissions errors).
        screenshot_ok_msg (QMessageBox): Message to display if a
            screenshot was taken successfully and the user doesn't have "open
            screenshots on capture" enabled.
        settings_action (QAction): Adds a menu bar item which triggers opening
            the settings menu.
        skip_button (QPushButton): Allows the user to move to the next
            split. Does the same thing as pressing the skip split hotkey.
        split_dir_button (QPushButton): Allows the user to select a split
            image folder.
        split_directory_box (QLineEdit): Shows the path to the current
            split image folder. If clicked, it opens the split image folder in
            the OS's file explorer.
        split_display_txt (str): Informs the user there are no split
            images loaded currently.
        split_display (QLabel): Display split images if loaded, or else
            show the split_display_txt.
        split_loop_label (QLabel): Informs the user about the current
            split's loop information.
        split_overlay (QLabel): Informs the user that a pre-split delay
            or post-split pause is taking place.
        split_name_label (QLabel): Shows the current split name.
        threshold_percent (QLabel): Displays the threshold image match
            percent for the current split, or a null string (see
            ui_controller._update_ui for details).
        threshold_percent_label (QLabel): Displays text describing the
            threshold image match percent.
        threshold_percent_sign (QLabel): Displays a percent sign after
            the threshold image match percent.
        undo_button (QPushButton): Allows the user to move to the
            previous split. Does the same thing as pressing the undo split
            hotkey.
        later_button_txt (str): The text that appears on the
            "remind me later" button in update_available_msg.
        update_available_msg (QMessageBox): Message that appears when
            an update is available.
        open_button_txt (str): The text that appears on the
            "open" button in update_available_msg.
        never_button_txt (str): The text that appears on the
            "don't ask again" button in update_available_msg.
        video_display (QLabel): Display video feed if connected, or else
            show the video_display_txt.
        video_display_txt (str): Informs the user there is no
            video connected currently.
        video_title (QLabel): Show information about the current video if
            loaded.
        video_down_txt_min (str): In minimal view, inform the user
            there is no video connected.
        video_live_txt (str): In full view, inform the user the
            video is connected.
        video_live_txt_min (str): In minimal view, inform the user
            the video is connected.
    """

    def __init__(self) -> None:
        """Initialize all widgets in the main window."""
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        self._container = QWidget(self)
        self.setCentralWidget(self._container)

        self.setWindowTitle(f"Pilgrim Autosplitter {VERSION_NUMBER}")

        # Menu bar
        self.settings_action = QAction("Open settings menu", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.help_action = QAction("Help", self)

        self._menu_bar = QMenuBar(self._container)
        self.setMenuBar(self._menu_bar)

        self._menu_bar_dropdown = self._menu_bar.addMenu("&Autosplitter Settings")
        self._menu_bar_dropdown.addAction(self.settings_action)
        self._menu_bar_dropdown.addAction(self.help_action)

        # Layout attributes
        self.LEFT_EDGE_CORRECTION = -44
        self.TOP_EDGE_CORRECTION = -215
        if platform.system() == "Windows":
            self.HEIGHT_CORRECTION = 22
        else:
            self.HEIGHT_CORRECTION = 0

        # Close app convenience shortcut
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)

        #######################
        #                     #
        # Widgets (Split dir) #
        #                     #
        #######################

        txt = "Select split image folder:"
        self.split_dir_button = QPushButton(txt, self._container)
        self.split_dir_button.setFocusPolicy(Qt.NoFocus)

        self.split_directory_box = ClickableLineEdit(self._container)
        self.split_directory_box.setAlignment(Qt.AlignLeft)
        self.split_directory_box.setText(settings.get_str("LAST_IMAGE_DIR"))
        # Make sure cursor doesn't change on hover
        self.split_directory_box.setFocusPolicy(Qt.NoFocus)
        # Needed to make sure text can't be selected, including blank spaces
        # before and after text. I'm not sure why this is necessary since mouse
        # events are intercepted in ClickableLineEdit anyway, but in my testing
        # this is the case.
        self.split_directory_box.setReadOnly(True)

        ###########################
        #                         #
        # Widgets (Video display) #
        #                         #
        ###########################

        # Video feed
        self.video_title = QLabel(self._container)
        self.video_title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.video_title.setAlignment(Qt.AlignCenter)
        self.video_live_txt = "Video feed"
        self.video_down_txt = ""

        self.video_display = QLabel(self._container)
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setObjectName("image_label_inactive")
        self.video_display_txt = "No video feed detected"

        #########################
        #                       #
        # Widgets (Split image) #
        #                       #
        #########################

        left, top = self.LEFT_EDGE_CORRECTION, self.TOP_EDGE_CORRECTION
        self.split_labels_empty_txt = ""

        self.split_name_label = QLabel(self._container)
        self.split_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.split_loop_label = QLabel(self._container)
        self.split_loop_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_loop_label.setAlignment(Qt.AlignCenter)
        self.split_loop_label_empty_txt = "Split does not loop"
        # Include placeholders for current and total loops
        self.split_loop_label_txt = "Loop {} of {}"

        self.split_display = QLabel(self._container)
        self.split_display.setAlignment(Qt.AlignCenter)
        self.split_display.setObjectName("image_label_inactive")
        self.split_display_txt = "No split images loaded"

        self.split_overlay = QLabel(self._container)
        self.split_overlay.setAlignment(Qt.AlignCenter)
        self.split_overlay.setObjectName("split_overlay")
        self.split_overlay.setVisible(False)

        self.overlay_delay_txt = "Splitting in {amount:.1f} s"
        self.overlay_pause_txt = "Paused for {amount:.1f} s"

        self.split_info_min_label = QLabel(self._container)
        self.split_info_min_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_info_min_label.setAlignment(Qt.AlignCenter)
        # This label's always in the same spot
        self.split_info_min_label.setGeometry(QRect(92 + left, 225 + top, 251, 31))
        self.min_video_down_txt = "Video status:   down"
        self.min_video_live_txt = "Video status:   healthy"

        #############################
        #                           #
        # Widgets (Current match %) #
        #                           #
        #############################

        self.match_percent_label = QLabel(self._container)
        self.match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.match_percent_label.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )
        self.match_percent_short_txt = "Sim:"
        self.match_percent_long_txt = "Similarity to split image:"

        self.match_percent = QLabel(self._container)
        self.match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.match_percent.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )

        #############################
        #                           #
        # Widgets (Highest match %) #
        #                           #
        #############################

        self.highest_percent_label = QLabel(self._container)
        self.highest_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_percent_label.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )
        self.highest_percent_short_txt = "High:"
        self.highest_percent_long_txt = "Highest similarity so far:"

        self.highest_percent = QLabel(self._container)
        self.highest_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_percent.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )

        ###############################
        #                             #
        # Widgets (Threshold match %) #
        #                             #
        ###############################

        self.threshold_percent_label = QLabel(self._container)
        self.threshold_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_percent_label.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )
        self.threshold_percent_short_txt = "Thr:"
        self.threshold_percent_long_txt = "Threshold similarity:"

        self.threshold_percent = QLabel(self._container)
        self.threshold_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_percent.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )

        ###########################
        #                         #
        # Widgets (Percent signs) #
        #                         #
        ###########################

        self.percent_sign_1 = QLabel("%", self._container)
        self.percent_sign_1.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.percent_sign_1.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter
        )

        self.percent_sign_2 = QLabel("%", self._container)
        self.percent_sign_2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.percent_sign_2.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter
        )

        self.percent_sign_3 = QLabel("%", self._container)
        self.percent_sign_3.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.percent_sign_3.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter
        )

        ###############################
        #                             #
        # Widgets (Left side buttons) #
        #                             #
        ###############################

        # Minimal view button
        self.min_view_button = QPushButton(self._container)
        self.min_view_button.setFocusPolicy(Qt.NoFocus)
        self.min_view_min_txt = "Minimal view"
        self.min_view_full_txt = "Full view"

        # Next source button
        self.next_source_button = QPushButton("Next source", self._container)
        self.next_source_button.setFocusPolicy(Qt.NoFocus)

        # Screenshot button
        self.screenshot_button = QPushButton(self._container)
        self.screenshot_button.setEnabled(False)
        self.screenshot_button.setFocusPolicy(Qt.NoFocus)
        self.screenshot_button_short_txt = "Screenshot"
        self.screenshot_button_long_txt = "Take screenshot"

        # Screenshot success message box
        self.screenshot_ok_msg = QMessageBox(self)
        self.screenshot_ok_msg.setText("Screenshot taken")

        # Screenshot error message box (no video)
        self.screenshot_err_no_video = QMessageBox(self)
        self.screenshot_err_no_video.setText("Could not take screenshot")
        self.screenshot_err_no_video.setInformativeText(
            "No video feed detected. Please make sure video feed is active and try again."
        )
        self.screenshot_err_no_video.setIcon(QMessageBox.Warning)

        # Screenshot error message box (file couldn't be saved)
        self.screenshot_err_no_file = QMessageBox(self)
        self.screenshot_err_no_file.setText("Could not save screenshot")
        self.screenshot_err_no_file.setInformativeText(
            "Pilgrim Autosplitter can't write files to this folder. Please select a different folder and try again."
        )
        self.screenshot_err_no_file.setIcon(QMessageBox.Warning)

        ################################
        #                              #
        # Widgets (Right side buttons) #
        #                              #
        ################################

        # Reload video button
        self.reconnect_button = QPushButton("Reconnect video", self._container)
        self.reconnect_button.setFocusPolicy(Qt.NoFocus)

        # Previous split button
        self.previous_button = QPushButton("<", self._container)
        self.previous_button.setEnabled(False)
        self.previous_button.setFocusPolicy(Qt.NoFocus)

        # Next split button
        self.next_button = QPushButton(">", self._container)
        self.next_button.setEnabled(False)
        self.next_button.setFocusPolicy(Qt.NoFocus)

        # Undo split button
        self.undo_button = QPushButton(self._container)
        self.undo_button.setEnabled(False)
        self.undo_button.setFocusPolicy(Qt.NoFocus)
        self.undo_button_short_txt = "Undo"
        self.undo_button_long_txt = "Undo split"

        # Skip split button
        self.skip_button = QPushButton(self._container)
        self.skip_button.setEnabled(False)
        self.skip_button.setFocusPolicy(Qt.NoFocus)
        self.skip_button_short_txt = "Skip"
        self.skip_button_long_txt = "Skip split"

        # Pause comparison / unpause comparison button
        self.pause_button = QPushButton(self._container)
        self.pause_button.setEnabled(False)
        self.pause_button.setFocusPolicy(Qt.NoFocus)
        self.pause_short_txt = "Pause comp"
        self.pause_long_txt = "Pause comparison"
        self.unpause_short_txt = "Unpause comp"
        self.unpause_long_txt = "Unpause comparison"

        # Reset splits button
        self.reset_button = QPushButton(self._container)
        self.reset_button.setFocusPolicy(Qt.NoFocus)
        self.reset_button_short_txt = "Reset"
        self.reset_button_long_txt = "Reset splits"

        ##################################
        #                                #
        # Widgets (Update available msg) #
        #                                #
        ##################################

        # Update available message box
        self.update_available_msg = QMessageBox(self._container)
        self.update_available_msg.setText("New update available!")
        self.update_available_msg.setInformativeText(
            "Pilgrim Autosplitter has been updated!\nShow new release?"
        )
        self.update_available_msg.setIcon(QMessageBox.Information)
        self.update_available_msg.setStandardButtons(
            QMessageBox.Open | QMessageBox.Close | QMessageBox.Discard
        )
        # Make sure "Remind me later" button is highlighted
        self.update_available_msg.setDefaultButton(
            self.update_available_msg.button(QMessageBox.Close)
        )

        # Update available message box buttons
        # You can't directly create QMessageBox buttons -- you either have to
        # call QMessageBox.addButton, which doesn't let you keep a reference to
        # the button, or you have to make the buttons by calling
        # QMessageBox.setStandardButtons, then referencing the buttons by the
        # role they have. If you do that, you can BOTH set the button's text
        # AND make one of the buttons the default.
        self.open_button_txt = "Open"
        self._open_button = self.update_available_msg.button(QMessageBox.Open)
        self._open_button.setText(self.open_button_txt)

        self.later_button_txt = "Remind me later"
        self._later_button = self.update_available_msg.button(QMessageBox.Close)
        self._later_button.setText(self.later_button_txt)

        self.never_button_txt = "Don't ask again"
        self._never_button = self.update_available_msg.button(QMessageBox.Discard)
        self._never_button.setText(self.never_button_txt)

        ##################
        #                #
        # Widgets (Misc) #
        #                #
        ##################

        # Couldn't find file or directory error message box
        self.err_not_found_msg = QMessageBox(self)
        self.err_not_found_msg.setText("File or folder not found")
        self.err_not_found_msg.setInformativeText(
            "The file or folder could not be found. Please try again."
        )
        self.err_not_found_msg.setIcon(QMessageBox.Warning)

        #####################
        #                   #
        # Check for updates #
        #                   #
        #####################

        if settings.get_bool("CHECK_FOR_UPDATES"):
            latest_version = settings.get_latest_version()
            if latest_version != settings.VERSION_NUMBER:
                # Yes, I call both show and open. If you just call show, the
                # box doesn't always appear centered over the window (it's way
                # off to the side). If you just call show, then bafflingly, the
                # wrong button is highlighted by default. Calling both makes
                # everything work, for some reason.
                self.update_available_msg.show()
                self.update_available_msg.open()


class ClickableLineEdit(QLineEdit):
    """QLineEdit subclass that understands and reacts to single mouse presses.

    Double clicks and drags are neutralized, since they otherwise would allow
    the user to highlight the text in the line edit, which could be confusing
    given that its purpose is to serve as a pseudo-button.

    This whole class is probably unnecessary -- the same kind of thing could be
    implemented with a button or a label, probably. But I like the look of the
    QLineEdit class and figuring out custom css with QWidgets is a nightmare,
    so I'm going with this.

    Attributes:
        clicked (PyQt5.QtCore.pyqtSignal): Emitted when a click is successfully
            done and released on the ClickableLineEdit.
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """Inherit from QLineEdit and set attributes to None.

        Args:
            parent (QWidget, optional): The parent class. Defaults to None.
        """
        QLineEdit.__init__(self, parent)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        """Prevent the mouse moving from having any effect.

        I override this method specifically to prevent selecting text by
        clicking and dragging, since it's hard to deselect text once it's
        selected (that's a side effect of making this widget clickable).

        Args:
            a0 (QMouseEvent | None): The mouse drag event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        pass

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        """Prevent a double click from having any effect.

        I override this method specifically to prevent double-clicking to
        select text, since single clicking will open a dialog (it would
        be confusing for a single click to open a window and a double
        click to do nothing).

        Args:
            a0 (QMouseEvent | None): The mouse double click event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        pass

    def mouseReleaseEvent(self, event):
        """Emit self.clicked if the mouse was pressed and released.

        Args:
            event: The mouse release event. See help(PyQt5.QtCore.QEvent).
        """
        if event.button() == Qt.LeftButton and event.pos() in self.rect():
            self.clicked.emit()
