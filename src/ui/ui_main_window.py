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

import os
import platform
from typing import Optional

from PyQt5.QtCore import (
    pyqtSignal,
    QEvent,
    QObject,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QGraphicsOpacityEffect,
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
        err_invalid_dir_msg (QMessageBox): Message to display if the user tries
            to load an image directory outside the user's home directory. (This
            is disabled so users don't try to trigger i/o somewhere vulnerable,
            especially if they're running the program as root (e.g. on Linux)).
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
        split_loop_label_reset_txt (QLabel): Tells the user the currently
            displayed image is the reset image.
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

        self._mouse_allowed = True  # For usage, see self.eventFilter

        # Menu bar
        self.settings_action = QAction("Open settings menu", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.help_action = QAction("User manual", self)

        self._menu_bar = QMenuBar(self._container)
        self.setMenuBar(self._menu_bar)

        self._menu_bar_dropdown = self._menu_bar.addMenu("&Autosplitter Settings")
        self._menu_bar_dropdown.addAction(self.settings_action)
        self._menu_bar_dropdown.addAction(self.help_action)

        # Layout attributes
        self.LEFT_EDGE_CORRECTION = -44
        self.TOP_EDGE_CORRECTION = -215
        if platform.system() != "Darwin":
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

        self.video_display = ClickableQLabel(self._container)
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setObjectName("video_label")
        # Prevent clicking this widget when window is out of focus
        # from having any effect (see self.eventFilter)
        self.video_display.installEventFilter(self)
        self.video_display_txt = "No video feed detected"

        self.video_record_overlay = QLabel(self._container)
        self.video_record_overlay.setAlignment(Qt.AlignCenter)
        self.video_record_overlay.setObjectName("video_overlay")
        self.video_record_overlay.setVisible(False)
        self.video_record_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        program_dir = os.path.dirname(os.path.abspath(__file__))
        self.record_active_img = f"{program_dir}/../../resources/record_active.png"
        self.record_idle_img = f"{program_dir}/../../resources/record_idle.png"

        self.video_info_overlay = ShadowFadeQLabel(self._container)
        self.video_info_overlay.setAlignment(Qt.AlignLeft)
        self.video_info_overlay.setObjectName("video_overlay")
        self.video_info_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.video_info_overlay.set_text_color("white")
        self.video_info_overlay.set_shadow_color("black")

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
        self.split_loop_label_reset_txt = "Reset image"

        self.split_display = ClickableQLabel(self._container)
        self.split_display.setAlignment(Qt.AlignCenter)
        self.split_display.setObjectName("image_label")
        # Prevent clicking this widget when window is out of focus
        # from having any effect (see self.eventFilter)
        self.split_display.installEventFilter(self)
        self.split_display_txt = "No split images loaded"

        self.split_overlay = QLabel(self._container)
        self.split_overlay.setAlignment(Qt.AlignCenter)
        self.split_overlay.setObjectName("split_overlay")
        self.split_overlay.setVisible(False)
        self.split_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.overlay_delay_txt_secs = "Splitting in {:.1f} s"
        self.overlay_delay_txt_mins = "Splitting in {}"
        self.overlay_pause_txt_secs = "Paused for {:.1f} s"
        self.overlay_pause_txt_mins = "Paused for {}"

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
        self.match_reset_percent_txt = "Similarity to reset image:"

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
        # (No parent widget -- parent widget keeps it from closing)
        self.screenshot_ok_msg = QMessageBox()
        self.screenshot_ok_msg.setText("Screenshot taken")

        # Screenshot error message box (no video)
        # (No parent widget -- parent widget keeps it from closing)
        self.screenshot_err_no_video = QMessageBox()
        self.screenshot_err_no_video.setText("Could not take screenshot")
        self.screenshot_err_no_video.setInformativeText(
            "No video feed detected. Please make sure video feed is active and try again."
        )
        self.screenshot_err_no_video.setIcon(QMessageBox.Warning)

        # Screenshot error message box (file couldn't be saved)
        # (No parent widget -- parent widget keeps it from closing)
        self.screenshot_err_no_file = QMessageBox()
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
        # (Parent widget ok here since the signals are hooked up)
        self.update_available_msg = QMessageBox()
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
        self.err_not_found_msg = QMessageBox()
        self.err_not_found_msg.setText("File or folder not found")
        self.err_not_found_msg.setInformativeText(
            "The file or folder could not be found. Please try again."
        )
        self.err_not_found_msg.setIcon(QMessageBox.Warning)

        # Invalid image directory chosen message box
        self.err_invalid_dir_msg = QMessageBox()
        self.err_invalid_dir_msg.setText("Invalid folder selection")
        self.err_invalid_dir_msg.setInformativeText(
            f"You must select your home folder ({settings.get_home_dir()}) or one of its subfolders."
        )
        self.err_invalid_dir_msg.setIcon(QMessageBox.Warning)

    def eventFilter(self, obj: QObject, event: QEvent):
        """Watch for QEvent.WindowActivate, which is triggered when the window
        was not in focus and is brought into focus.

        This method disables mouse presses on a widget for 50 ms after the
        window is brought into focus. It does this by setting _mouse_allowed to
        False, then 50 ms later setting it True again. Mouse clicks only filter
        through if _mouse_allowed is True.

        Args:
            obj (QObject): The watched QObject. Unused here.
            event (QEvent): The event to filter out (or not).

        Returns:
            bool: Returning True stops the QEvent from propogating further
                (basically neutralizes it). Returning False allows it to filter
                through.
        """
        if event.type() == QEvent.WindowActivate:
            self._mouse_allowed = False
            QTimer.singleShot(50, lambda: setattr(self, "_mouse_allowed", True))

        elif event.type() == QEvent.MouseButtonPress and not self._mouse_allowed:
            self._mouse_allowed = True
            return True

        return False


class ShadowFadeQLabel(QWidget):
    """QWidget containing 2 QLabels, both with identical text, but with
    (optionally) different text colors to produce a drop shadow effect. Any
    text set fades out after _text_duration ms, with an animation length of
    _fade_duration ms.

    This is done because it's not natively possible to use a drop shadow effect
    and a fade effect together for some reason.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inherit from QWidget and set up the attributes.

        Args:
            parent (QWidget, optional): The parent class. Defaults to None.
        """
        QWidget.__init__(self, parent)

        # Create the two widgets that hold the text
        self._lower_txt = QLabel(self)
        self._upper_txt = QLabel(self)  # This one's last so it's on top

        # How long the text stays on screen (ms)
        self._text_duration = 3000

        # How long the text takes to fade out (ms)
        self._fade_duration = 1000

        # Create the fade effect and animation and a timer to start it
        self._fade_effect = QGraphicsOpacityEffect()
        self._fade_effect.setOpacity(1)
        self.setGraphicsEffect(self._fade_effect)

        self._fade_animation = QPropertyAnimation(self._fade_effect, b"opacity")
        self._fade_animation.setDuration(self._fade_duration)
        self._fade_animation.setStartValue(1)
        self._fade_animation.setEndValue(0)

        self._fade_timer = QTimer()
        self._fade_timer.setSingleShot(True)
        self._fade_timer.setInterval(self._text_duration)
        self._fade_timer.timeout.connect(self._fade_animation.start)

    def setAlignment(self, flag: Qt.Alignment) -> None:
        """Make sure text alignment for the two text labels match.

        Args:
            flag (Qt.Alignment): The alignment flag.
        """
        self._upper_txt.setAlignment(flag)
        self._lower_txt.setAlignment(flag)

    def setObjectName(self, name: str) -> None:
        """Make sure the object names for both parent and children match.

        Args:
            name (str): The object name.
        """
        self._upper_txt.setObjectName(name)
        self._lower_txt.setObjectName(name)
        super().setObjectName(name)

    def setAttribute(self, attribute: Qt.WidgetAttribute, on: bool = True) -> None:
        """Make sure the attributes of both parent and children match.

        Args:
            attribute (Qt.WidgetAttribute): The attribute to set.
            on (bool, optional): Whether the attribute is actually enabled.
                Defaults to True.
        """
        self._upper_txt.setAttribute(attribute, on)
        self._lower_txt.setAttribute(attribute, on)
        super().setAttribute(attribute, on)

    def setGeometry(self, geometry: QRect) -> None:
        """Move the child widgets and make sure _lower_txt is positioned down
        right of upper text to produce a drop shadow effect.

        For some reason, adjusting the geometry of the parent makes the child
        widgets disappear, so it's not affected here.

        Args:
            geometry (QRect): The geometry to apply.
        """
        self._upper_txt.setGeometry(geometry)
        self._lower_txt.setGeometry(geometry)
        self._lower_txt.move(self._lower_txt.x() + 2, self._lower_txt.y() + 2)

    def set_text_color(self, color: str) -> None:
        """Set the color of the widget's text.

        Args:
            color (str): The color to set. Any string accepted by CSS is fine.
        """
        style = self._upper_txt.styleSheet()
        style += f"""
            * {{
                color: {color};
            }}
        """
        self._upper_txt.setStyleSheet(style)

    def set_shadow_color(self, color: str) -> None:
        """Set the color of the widget's drop shadow.

        Args:
            color (str): The color to set. Any string accepted by CSS is fine.
        """
        style = self._lower_txt.styleSheet()
        style += f"""
            * {{
                color: {color};
            }}
        """
        self._lower_txt.setStyleSheet(style)

    def set_text(self, text: str) -> None:
        """Set (right-elided) text to both labels and restart the fade timer.

        Args:
            text (str): The text to set.
        """
        # Stop fading and make the text opaque
        self._fade_timer.stop()
        self._fade_animation.stop()
        self._fade_effect.setOpacity(1)

        # Set the text
        elided_text = self._get_elided_text(text)
        self._upper_txt.setText(elided_text)
        self._lower_txt.setText(elided_text)

        # Restart the timer
        self._fade_timer.start()

    def _get_elided_text(self, text: str) -> str:
        """Right-elide text to the width of the widget.

        Returns:
            str: The elided text.
        """
        return self.fontMetrics().elidedText(text, Qt.ElideRight, self.width() - 10)


class ClickableQLabel(QLabel):
    """QLabel with additional flags indicating whether it is being clicked and/
    or hovered by the mouse.

    One known limitation is that this doesn't set self.hovered to True if the
    mouse entered the widget while clicked. I'm fine with this -- it actually
    gives the behavior I want -- but it is technically wrong.

    Attributes:
        adjusted (bool): Whether the widget has been set to an alternate state.
            Can be used to keep track of widget modifications.
        clicked (bool): Whether the mouse is currently clicked on this widget.
        delayed_single_click (bool): Whether a single click was registered, but
            hasn't yet been released. Useful if you want the effect of a single
            click to take place after releasing the mouse, even if the user
            holds the mouse for a long time.
        double_click (bool): Whether the mouse was double-clicked.
        hovered (bool): Whether the mouse is currently hovered over this widget.
            Will not reflect a mouse hover if the hover began while the mouse
            was clicked on another widget and the mouse has not yet been
            released from that click.
        valid_double_click (pyqtSignal): Emitted when the widget is clicked and
            released twice within 200 ms while the mouse is over the widget.
        valid_single_click (pyqtSignal): Emitted when the widget is clicked and
            released just once with the left mouse button while the mouse is
            over the widget.
    """

    valid_single_click = pyqtSignal()
    valid_double_click = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inherit from QLabel and set default attribute values.

        Args:
            parent (QLabel, optional): The parent class. Defaults to None.
        """
        QLabel.__init__(self, parent)
        self.adjusted = False
        self.clicked = False
        self.delayed_single_click = False
        self.double_click = False
        self.hovered = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Set self.clicked to True when the left mouse button is pressed.

        Also start a 200 ms timer that calls mouseSingleClickEvent. If the
        timer goes off and a double click hasn't occured, that method will
        finish; otherwise, only the logic in mouseDoubleClickEvent will go
        through. This allows a single click and a double click to do different
        things.

        Set double_click to False so that, absent a double-click, only
        mouseSingleClickEvent will have any effect.

        Args:
            event: The mouse press event. See help(PyQt5.QtCore.QEvent).
        """
        if event.button() == Qt.LeftButton:
            self.clicked = True
            self.double_click = False
            QTimer.singleShot(
                QApplication.doubleClickInterval(),
                lambda event=event: self.mouseSingleClickEvent(event),
            )

    def mouseSingleClickEvent(self, event: QMouseEvent) -> None:
        """Emit valid_single_click if a single left mouse click is released
        within the widget's boundaries.

        If the mouse actually hasn't been released yet, set delayed_single_
        click to True instead, so the single click action can occur during
        mouseReleaseEvent.

        If self.double_click is False (due to no double click), do nothing.

        Args:
            event: The mouse press event. See help(PyQt5.QtCore.QEvent).
        """
        if event.pos() in self.rect() and not self.double_click:
            if self.clicked:
                self.delayed_single_click = True
            else:
                self.valid_single_click.emit()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Set double_click to True when a double click is registered so the
        double click action can occur during mouseReleaseEvent. This flag also
        prevents mouseSingleClickEvent from doing anything.

        Set clicked to True since the mouse is still clicked (this wouldn't be
        reflected otherwise since mousePressEvent isn't called for a double
        click).

        Args:
            event: The mouse press event. See help(PyQt5.QtCore.QEvent).
        """
        self.clicked = self.double_click = True

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Set self.clicked to False when the left mouse button is released.

        If delayed_single_click was set in mouseSingleClickEvent, do the single
        click action here and unset the flag.

        Otherwise if double_click was set in mouseDoubleClickEvent, do the
        double click action here.

        Args:
            event: The mouse release event. See help(PyQt5.QtCore.QEvent).
        """
        if event.button() == Qt.LeftButton:
            self.clicked = False

            if self.delayed_single_click:
                self.delayed_single_click = False
                if event.pos() in self.rect():
                    self.valid_single_click.emit()

            elif self.double_click and event.pos() in self.rect():
                self.valid_double_click.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Track whether the clicked mouse is inside the widget's bounds.

        This method only returns values when the mouse is clicked. Sets
        self.hovered to True if the mouse is over the widget, False
        otherwise.

        Args:
            event (QMouseEvent | None): The mouse drag event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        self.hovered = event.pos() in self.rect()

    def enterEvent(self, event: QMouseEvent) -> None:
        """Detect when the unclicked mouse enters the widget.

        The enter and leave methods are needed because mouseMoveEvent only
        works when the mouse isn't clicked, but we want to set hovered
        regardless of whether the mouse is clicked or not.

        Args:
            event (QMouseEvent | None): The mouse enter event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        self.hovered = True

    def leaveEvent(self, event: QMouseEvent) -> None:
        """Detect when the unclicked mouse leaves the widget.

        The enter and leave methods are needed because mouseMoveEvent only
        works when the mouse isn't clicked, but we want to set hovered
        regardless of whether the mouse is clicked or not.

        Args:
            event (QMouseEvent | None): The mouse enter event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        self.hovered = False


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inherit from QLineEdit and set attributes to None.

        Args:
            parent (QWidget, optional): The parent class. Defaults to None.
        """
        QLineEdit.__init__(self, parent)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Prevent the mouse moving from having any effect.

        I override this method specifically to prevent selecting text by
        clicking and dragging, since it's hard to deselect text once it's
        selected (that's a side effect of making this widget clickable).

        Args:
            a0 (QMouseEvent | None): The mouse drag event.
                See help(PyQt5.QtGui.QMouseEvent).
        """
        pass

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
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

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Emit self.clicked if the mouse was pressed and released.

        Args:
            event: The mouse release event. See help(PyQt5.QtCore.QEvent).
        """
        if event.button() == Qt.LeftButton and event.pos() in self.rect():
            self.clicked.emit()
