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

"""Template for the settings window view. Most functionality is not provided
and should be provided in a controller class.
"""


from typing import Union

from PyQt5.QtCore import QEvent, QRect, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QPushButton,
    QShortcut,
    QSpinBox,
    QWidget,
)


class UISettingsWindow(QDialog):
    """Initialize settings window widgets and allow the settings window to be
    executed.

    The below widgets are initialized when a UISettingsWindow instance is
    created but, with few exceptions, they are connected to their helper
    methods in ui_controller. This is to enforce a view-controller structure,
    where this file functions primarily as a view.

    Inherits QDialog and, by extension, its attributes and methods. See
    help(PyQt5.QtWidgets.QDialog).

    Attributes:
        aspect_ratio_combo_box (QComboBox): Store and allow selection of aspect
            ratio settings.
        border_helper_frame (QFrame): Draw a border around the edge of the menu
            for aesthetic purposes.
        cancel_button (QPushButton): Close the menu without saving. Same as
            clicking the "x button", pressing esc, etc.
        close_window_shortcut (QShortcut): Same as cancel_button.
        default_delay_double_spinbox (QDoubleSpinBox): Store and allow
            selection of default delay before splitting.
        default_pause_double_spinbox (QDoubleSpinBox): Store and allow
            selection of default pause after splitting.
        default_threshold_double_spinbox (QDoubleSpinBox): Store and allow
            selection of default match percent threshold for triggering a
            split.
        fps_spinbox (QSpinBox): Store and allow selection of default frames per
            second.
        global_hotkeys_checkbox (QCheckBox): Store and allow selection of
            whether global hotkeys are enabled.
        match_percent_decimals_spinbox (QSpinBox): Store and allow selection of
            amount of decimal places shown when displaying match percents.
        next_split_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            next split hotkey.
        open_screenshots_checkbox (QCheckBox): Store and allow selection of
            whether screenshots are opened when they are captured.
        pause_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            pause timer hotkey.
        previous_split_hotkey_line_edit (KeyLineEdit): Store and allow
            selection of previous split hotkey.
        reset_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            reset splits hotkey.
        save_button (QPushButton): Save all settings and close the window.
        screenshot_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            screenshot hotkey.
        skip_split_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            skip split hotkey.
        split_hotkey_line_edit (KeyLineEdit): Store and allow selection
            of split hotkey.
        start_with_video_checkbox (QCheckBox): Store and allow selection of
            whether this program should try to open a video feed on startup.
        theme_combo_box (QComboBox): Store and allow selection of UI theme.
        toggle_global_hotkeys_hotkey_line_edit (KeyLineEdit): Store and allow
            selection of toggle global hotkeys enabled hotkey.
        undo_split_hotkey_line_edit (KeyLineEdit): Store and allow selection of
            undo split hotkey.
    """

    def __init__(self) -> None:
        """Initialize all widgets in the settings window, including helper
        widgets.
        """
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        # Shift all widgets, except the frame, this many pixels right
        self._LEFT_EDGE_CORRECTION = 0
        # Shift all widgets, except the frame, this many pixels down
        self._TOP_EDGE_CORRECTION = 3
        # Shift the frame this many pixels right
        self._LEFT_EDGE_CORRECTION_FRAME = 0
        # Shift the frame this many pixels down
        self._TOP_EDGE_CORRECTION_FRAME = 0
        # Left side widgets are, generally, this many pixels wide
        self._LEFT_SIDE_WIDGET_WIDTH = 70
        # Left side widgets are, generally, this many pixels high
        self._LEFT_SIDE_WIDGET_HEIGHT = 27

        self.setFixedSize(610, 392)
        self.setWindowTitle("Settings")

        self.close_window_shortcut = QShortcut("ctrl+w", self)

        #####################
        #                   #
        # Left Side Widgets #
        #                   #
        #####################

        # Checkbox effect
        self._checkbox_shadow = QGraphicsDropShadowEffect()
        self._checkbox_shadow.setBlurRadius(10)
        self._checkbox_shadow.setOffset(12)
        self._checkbox_shadow.setColor(QColor(0, 0, 0, 1))

        # Border
        self.border_helper_frame = QFrame(self)
        self.border_helper_frame.setGeometry(
            QRect(
                10 + self._LEFT_EDGE_CORRECTION_FRAME,
                10 + self._TOP_EDGE_CORRECTION_FRAME,
                590,
                372,
            )
        )
        self.border_helper_frame.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.border_helper_frame.setObjectName("border")

        # FPS spinbox
        self._fps_label = QLabel("Frames per second:", self)
        self._fps_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION, 10 + self._TOP_EDGE_CORRECTION, 131, 31
            )
        )
        self._fps_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._fps_label.setToolTip("Read this many frames per second from video source")

        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                12 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT,
            )
        )
        self.fps_spinbox.setMinimum(20)
        self.fps_spinbox.setMaximum(60)

        # Screenshots checkbox
        self._open_screenshots_label = QLabel("Open screenshots:", self)
        self._open_screenshots_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION, 40 + self._TOP_EDGE_CORRECTION, 141, 31
            )
        )
        self._open_screenshots_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._open_screenshots_label.setToolTip(
            "When enabled, opens screenshots with the system's default image viewer"
        )

        self.open_screenshots_checkbox = QCheckBox(self)
        self.open_screenshots_checkbox.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION, 49 + self._TOP_EDGE_CORRECTION, 13, 13
            )
        )

        self._open_screenshots_checkbox_helper_label = QLabel(self)
        self._open_screenshots_checkbox_helper_label.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION, 48 + self._TOP_EDGE_CORRECTION, 14, 15
            )
        )
        self._open_screenshots_checkbox_helper_label.setObjectName("checkbox_helper")
        self._open_screenshots_checkbox_helper_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._open_screenshots_checkbox_helper_label.setGraphicsEffect(
            self._checkbox_shadow
        )

        # Default threshold spinbox
        self._default_threshold_label = QLabel("Default threshold:", self)
        self._default_threshold_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION, 70 + self._TOP_EDGE_CORRECTION, 161, 31
            )
        )
        self._default_threshold_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._default_threshold_label.setToolTip(
            "Images must match at least this much to trigger a split, pause, etc."
        )

        self.default_threshold_double_spinbox = QDoubleSpinBox(self)
        self.default_threshold_double_spinbox.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                72 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT,
            )
        )
        self.default_threshold_double_spinbox.setDecimals(2)
        self.default_threshold_double_spinbox.setMinimum(0.1)
        self.default_threshold_double_spinbox.setMaximum(100)
        self.default_threshold_double_spinbox.setSingleStep(0.1)
        self.default_threshold_double_spinbox.setSuffix("%")

        # Match percent decimals spinbox
        self._match_percent_decimals_label = QLabel("Similarity decimals:", self)
        self._match_percent_decimals_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                100 + self._TOP_EDGE_CORRECTION,
                161,
                31,
            )
        )
        self._match_percent_decimals_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self._match_percent_decimals_label.setToolTip(
            "Images must match at least this much to trigger a split, pause, etc."
        )

        self.match_percent_decimals_spinbox = QSpinBox(self)
        self.match_percent_decimals_spinbox.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                102 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT,
            )
        )
        self.match_percent_decimals_spinbox.setMinimum(0)
        self.match_percent_decimals_spinbox.setMaximum(2)

        # Default delay spinbox
        self._default_delay_label = QLabel("Default delay (sec.):", self)
        self._default_delay_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                130 + self._TOP_EDGE_CORRECTION,
                201,
                31,
            )
        )
        self._default_delay_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._default_delay_label.setToolTip(
            "The default delay between the split threshold being reached and a split, pause, etc."
        )

        self.default_delay_double_spinbox = QDoubleSpinBox(self)
        self.default_delay_double_spinbox.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                132 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT,
            )
        )
        self.default_delay_double_spinbox.setDecimals(3)
        self.default_delay_double_spinbox.setMinimum(0)
        self.default_delay_double_spinbox.setMaximum(99999)
        self.default_delay_double_spinbox.setSingleStep(0.1)

        # Default pause spinbox
        self._default_pause_label = QLabel("Default pause (sec.):", self)
        self._default_pause_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                160 + self._TOP_EDGE_CORRECTION,
                191,
                31,
            )
        )
        self._default_pause_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._default_pause_label.setToolTip(
            "The default waiting period after a split and before starting to compare the next "
            "image. Set this setting higher to save CPU"
        )

        self.default_pause_double_spinbox = QDoubleSpinBox(self)
        self.default_pause_double_spinbox.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                162 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT,
            )
        )
        self.default_pause_double_spinbox.setDecimals(0)
        # Use a 1 second minimum pause because no pause can cause problems, and
        # is likely not desireable from a user standpoint anyway
        self.default_pause_double_spinbox.setMinimum(1)
        self.default_pause_double_spinbox.setMaximum(99999)
        self.default_pause_double_spinbox.setSingleStep(1.0)

        # Aspect ratio combobox
        self._aspect_ratio_label = QLabel("GUI aspect ratio:", self)
        self._aspect_ratio_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                190 + self._TOP_EDGE_CORRECTION,
                191,
                31,
            )
        )
        self._aspect_ratio_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._aspect_ratio_label.setToolTip(
            "This affects how images are displayed on the GUI and matched with split images. "
            "However, you can use 16:9 when playing games at 4:3, or vice versa."
        )

        self.aspect_ratio_combo_box = QComboBox(self)
        self.aspect_ratio_combo_box.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                194 + self._TOP_EDGE_CORRECTION,
                130,
                self._LEFT_SIDE_WIDGET_HEIGHT - 4,
            )
        )
        self.aspect_ratio_combo_box.addItems(
            ["4:3 (480x360)", "4:3 (320x240)", "16:9 (512x288)", "16:9 (432x243)"]
        )
        # Theme combobox
        self._theme_label = QLabel("Theme:", self)
        self._theme_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                220 + self._TOP_EDGE_CORRECTION,
                191,
                31,
            )
        )
        self._theme_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._theme_label.setToolTip("Does anyone actually use light mode?")

        self.theme_combo_box = QComboBox(self)
        self.theme_combo_box.setGeometry(
            QRect(
                160 + self._LEFT_EDGE_CORRECTION,
                224 + self._TOP_EDGE_CORRECTION,
                self._LEFT_SIDE_WIDGET_WIDTH,
                self._LEFT_SIDE_WIDGET_HEIGHT - 4,
            )
        )
        self.theme_combo_box.addItems(["dark", "light"])

        # Start with video checkbox
        self._start_with_video_label = QLabel("Start with video:", self)
        self._start_with_video_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                250 + self._TOP_EDGE_CORRECTION,
                191,
                31,
            )
        )
        self._start_with_video_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._start_with_video_label.setToolTip(
            "Try to open video feed on bootup. Note that this could open a webcam (or any video "
            "device attached to your computer), which is harmless but could be surprising!"
        )

        self.start_with_video_checkbox = QCheckBox(self)
        self.start_with_video_checkbox.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION,
                259 + self._TOP_EDGE_CORRECTION,
                13,
                13,
            )
        )

        self._start_with_video_checkbox_helper_label = QLabel(self)
        self._start_with_video_checkbox_helper_label.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION,
                258 + self._TOP_EDGE_CORRECTION,
                14,
                15,
            )
        )
        self._start_with_video_checkbox_helper_label.setObjectName("checkbox_helper")
        self._start_with_video_checkbox_helper_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._start_with_video_checkbox_helper_label.setGraphicsEffect(
            self._checkbox_shadow
        )

        # Enable global hotkeys checkbox
        self._global_hotkeys_label = QLabel("Global hotkeys:", self)
        self._global_hotkeys_label.setGeometry(
            QRect(
                20 + self._LEFT_EDGE_CORRECTION,
                280 + self._TOP_EDGE_CORRECTION,
                191,
                31,
            )
        )
        self._global_hotkeys_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._global_hotkeys_label.setToolTip(
            "When disabled, hotkeys will only work when this program is in focus."
        )

        self.global_hotkeys_checkbox = QCheckBox(self)
        self.global_hotkeys_checkbox.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION,
                289 + self._TOP_EDGE_CORRECTION,
                13,
                13,
            )
        )

        self._global_hotkeys_checkbox_helper_label = QLabel(self)
        self._global_hotkeys_checkbox_helper_label.setGeometry(
            QRect(
                161 + self._LEFT_EDGE_CORRECTION,
                288 + self._TOP_EDGE_CORRECTION,
                14,
                15,
            )
        )
        self._global_hotkeys_checkbox_helper_label.setObjectName("checkbox_helper")
        self._global_hotkeys_checkbox_helper_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._global_hotkeys_checkbox_helper_label.setGraphicsEffect(
            self._checkbox_shadow
        )

        ######################
        #                    #
        # Right Side Widgets #
        #                    #
        ######################

        # Hotkey header
        self._hotkey_settings_label = QLabel("Hotkeys (click + type to change):", self)
        self._hotkey_settings_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                10 + self._TOP_EDGE_CORRECTION,
                216,
                31,
            )
        )
        self._hotkey_settings_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Start / split hotkey
        self.split_hotkey_line_edit = KeyLineEdit(self)
        self.split_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                42 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.split_hotkey_line_edit.setReadOnly(True)

        self._split_hotkey_label = QLabel("Start / split", self)
        self._split_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION, 40 + self._TOP_EDGE_CORRECTION, 81, 31
            )
        )
        self._split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._split_hotkey_clear_button = QPushButton("clear", self)
        self._split_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION, 45 + self._TOP_EDGE_CORRECTION, 39, 20
            )
        )
        self._split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._split_hotkey_clear_button.clicked.connect(
            lambda: self.split_hotkey_line_edit.setText("")
        )
        self._split_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.split_hotkey_line_edit, "key_code", "")
        )

        # Reset splits hotkey
        self.reset_hotkey_line_edit = KeyLineEdit(self)
        self.reset_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                72 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.reset_hotkey_line_edit.setReadOnly(True)

        self._reset_hotkey_label = QLabel("Reset splits", self)
        self._reset_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION, 70 + self._TOP_EDGE_CORRECTION, 91, 31
            )
        )
        self._reset_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._reset_hotkey_clear_button = QPushButton("clear", self)
        self._reset_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION, 75 + self._TOP_EDGE_CORRECTION, 39, 20
            )
        )
        self._reset_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._reset_hotkey_clear_button.clicked.connect(
            lambda: self.reset_hotkey_line_edit.setText("")
        )
        self._reset_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.reset_hotkey_line_edit, "key_code", "")
        )

        # Pause hotkey
        self.pause_hotkey_line_edit = KeyLineEdit(self)
        self.pause_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                102 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.pause_hotkey_line_edit.setReadOnly(True)

        self._pause_hotkey_label = QLabel("Pause timer", self)
        self._pause_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                100 + self._TOP_EDGE_CORRECTION,
                91,
                31,
            )
        )
        self._pause_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._pause_hotkey_clear_button = QPushButton("clear", self)
        self._pause_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                105 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._pause_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._pause_hotkey_clear_button.clicked.connect(
            lambda: self.pause_hotkey_line_edit.setText("")
        )
        self._pause_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.pause_hotkey_line_edit, "key_code", "")
        )

        # Undo split hotkey
        self.undo_split_hotkey_line_edit = KeyLineEdit(self)
        self.undo_split_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                132 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.undo_split_hotkey_line_edit.setReadOnly(True)

        self._undo_split_hotkey_label = QLabel("Undo split", self)
        self._undo_split_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                130 + self._TOP_EDGE_CORRECTION,
                81,
                31,
            )
        )
        self._undo_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._undo_split_hotkey_clear_button = QPushButton("clear", self)
        self._undo_split_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                135 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._undo_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._undo_split_hotkey_clear_button.clicked.connect(
            lambda: self.undo_split_hotkey_line_edit.setText("")
        )
        self._undo_split_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.undo_split_hotkey_line_edit, "key_code", "")
        )

        # Skip split hotkey
        self.skip_split_hotkey_line_edit = KeyLineEdit(self)
        self.skip_split_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                162 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.skip_split_hotkey_line_edit.setReadOnly(True)

        self._skip_split_hotkey_label = QLabel("Skip split", self)
        self._skip_split_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                160 + self._TOP_EDGE_CORRECTION,
                71,
                31,
            )
        )
        self._skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._skip_split_hotkey_clear_button = QPushButton("clear", self)
        self._skip_split_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                165 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._skip_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._skip_split_hotkey_clear_button.clicked.connect(
            lambda: self.skip_split_hotkey_line_edit.setText("")
        )
        self._skip_split_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.skip_split_hotkey_line_edit, "key_code", "")
        )

        # Previous split hotkey
        self.previous_split_hotkey_line_edit = KeyLineEdit(self)
        self.previous_split_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                192 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.previous_split_hotkey_line_edit.setReadOnly(True)

        self._previous_split_hotkey_label = QLabel("Previous split", self)
        self._previous_split_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                190 + self._TOP_EDGE_CORRECTION,
                101,
                31,
            )
        )
        self._previous_split_hotkey_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        self._previous_split_hotkey_clear_button = QPushButton("clear", self)
        self._previous_split_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                195 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._previous_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._previous_split_hotkey_clear_button.clicked.connect(
            lambda: self.previous_split_hotkey_line_edit.setText("")
        )
        self._previous_split_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.previous_split_hotkey_line_edit, "key_code", "")
        )

        # Next split hotkey
        self.next_split_hotkey_line_edit = KeyLineEdit(self)
        self.next_split_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                222 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.next_split_hotkey_line_edit.setReadOnly(True)

        self._next_split_hotkey_label = QLabel("Next split", self)
        self._next_split_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                220 + self._TOP_EDGE_CORRECTION,
                71,
                31,
            )
        )
        self._next_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._next_split_hotkey_clear_button = QPushButton("clear", self)
        self._next_split_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                225 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._next_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._next_split_hotkey_clear_button.clicked.connect(
            lambda: self.next_split_hotkey_line_edit.setText("")
        )
        self._next_split_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.next_split_hotkey_line_edit, "key_code", "")
        )

        # Screenshot hotkey
        self.screenshot_hotkey_line_edit = KeyLineEdit(self)
        self.screenshot_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                252 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.screenshot_hotkey_line_edit.setReadOnly(True)

        self._screenshot_hotkey_label = QLabel("Screenshot", self)
        self._screenshot_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                250 + self._TOP_EDGE_CORRECTION,
                71,
                31,
            )
        )
        self._screenshot_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._screenshot_hotkey_clear_button = QPushButton("clear", self)
        self._screenshot_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                255 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._screenshot_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._screenshot_hotkey_clear_button.clicked.connect(
            lambda: self.screenshot_hotkey_line_edit.setText("")
        )
        self._screenshot_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.screenshot_hotkey_line_edit, "key_code", "")
        )

        # Toggle global hotkeys hotkey
        self.toggle_global_hotkeys_hotkey_line_edit = KeyLineEdit(self)
        self.toggle_global_hotkeys_hotkey_line_edit.setGeometry(
            QRect(
                410 + self._LEFT_EDGE_CORRECTION,
                282 + self._TOP_EDGE_CORRECTION,
                121,
                25,
            )
        )
        self.toggle_global_hotkeys_hotkey_line_edit.setReadOnly(True)

        self._toggle_global_hotkeys_hotkey_label = QLabel("Toggle global", self)
        self._toggle_global_hotkeys_hotkey_label.setGeometry(
            QRect(
                300 + self._LEFT_EDGE_CORRECTION,
                280 + self._TOP_EDGE_CORRECTION,
                100,
                31,
            )
        )
        self._toggle_global_hotkeys_hotkey_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        self._toggle_global_hotkeys_hotkey_clear_button = QPushButton("clear", self)
        self._toggle_global_hotkeys_hotkey_clear_button.setGeometry(
            QRect(
                545 + self._LEFT_EDGE_CORRECTION,
                285 + self._TOP_EDGE_CORRECTION,
                39,
                20,
            )
        )
        self._toggle_global_hotkeys_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self._toggle_global_hotkeys_hotkey_clear_button.clicked.connect(
            lambda: self.toggle_global_hotkeys_hotkey_line_edit.setText("")
        )
        self._toggle_global_hotkeys_hotkey_clear_button.clicked.connect(
            lambda: setattr(self.toggle_global_hotkeys_hotkey_line_edit, "key_code", "")
        )

        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(
            QRect(
                319 + self._LEFT_EDGE_CORRECTION,
                326 + self._TOP_EDGE_CORRECTION,
                111,
                31,
            )
        )
        self.cancel_button.setFocusPolicy(Qt.NoFocus)

        # Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.setGeometry(
            QRect(
                459 + self._LEFT_EDGE_CORRECTION,
                326 + self._TOP_EDGE_CORRECTION,
                111,
                31,
            )
        )
        self.save_button.setFocusPolicy(Qt.NoFocus)

    def event(self, event) -> Union[bool, QWidget.event]:
        """Allow the user to take focus off a widget by clicking somewhere
        else.

        Overrides QDialog.event. See help(PyQt5.QtWidgets.QDialog) for
        implementation details.

        Returns:
            Union[bool, QWidget.event]: True if the mouse press was handled;
                otherwise, return the event for further handling by the system.
        """
        if event.type() == QEvent.MouseButtonPress:
            self.setFocus(True)
            return True
        return QWidget.event(self, event)


class KeyLineEdit(QLineEdit):
    """Box that allows users to enter a single key as a hotkey.

    KeyLineEdit depends on ui_controller._handle_hotkey_press for its
    implementation. See that method for details. Alternatively, you can create
    a listener that will catch keypresses and write their values into this
    class.

    KeyLineEdit extends QLineEdit. See help(PyQt5.QtWidgets.QLineEdit) for
    implementation details.

    Attributes:
        key_code (str): A string representation of a pynput.keyboard.Key.vk
            value. In other words, the virtual key integer value of a given
            key.
    """

    def __init__(self, parent=None) -> None:
        """Initialize a KeyLineEdit with a blank key_code value.

        Args:
            parent (QWidget, optional): The parent QWidget. Defaults to None.
                See help(PyQt5.QtWidgets.QLineEdit) for details.
        """
        QLineEdit.__init__(self, parent)
        self.key_code = ""
