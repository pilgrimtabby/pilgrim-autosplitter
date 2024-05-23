from PyQt5.QtCore import QEvent, QRect, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
                             QFrame, QGraphicsDropShadowEffect, QLabel,
                             QLineEdit, QPushButton, QShortcut, QSpinBox,
                             QWidget)

import settings
import ui.ui_style_sheet as style_sheet


class UISettingsWindow(QDialog):
    LEFT_EDGE_CORRECTION = 0
    TOP_EDGE_CORRECTION = 3
    LEFT_EDGE_CORRECTION_FRAME = 0
    TOP_EDGE_CORRECTION_FRAME = 0
    LEFT_SIDE_WIDGET_WIDTH = 70
    LEFT_SIDE_WIDGET_HEIGHT = 27

    def __init__(self):
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()
        self.is_showing = False

        # Set size, title
        self.setFixedSize(610, 362)
        self.setWindowTitle("Settings")

        # Shortcuts
        self.close_window_shortcut_option = QShortcut("ctrl+w", self)
        self.close_window_shortcut_option.activated.connect(self.close)

        # Style
        style_sheet.set_style(self)

        ###########
        #         #
        # Widgets #
        #         #
        ###########

        # Checkbox effect
        self.checkbox_shadow = QGraphicsDropShadowEffect()
        self.checkbox_shadow.setBlurRadius(10)
        self.checkbox_shadow.setOffset(12)
        self.checkbox_shadow.setColor(QColor(0, 0, 0, 1))

        # Border
        self.border_helper_frame = QFrame(self)
        self.border_helper_frame.setGeometry(QRect(10 + self.LEFT_EDGE_CORRECTION_FRAME, 10 + self.TOP_EDGE_CORRECTION_FRAME, 590, 342))
        self.border_helper_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.border_helper_frame.setObjectName("border")

        # FPS spinbox
        self.fps_label = QLabel("Frames per second:", self)
        self.fps_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 131, 31))
        self.fps_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.fps_label.setToolTip("Read this many frames per second from video source")
        
        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 12 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT))
        self.fps_spinbox.setMinimum(20)
        self.fps_spinbox.setMaximum(60)

        # Screenshots checkbox
        self.open_screenshots_label = QLabel("Open screenshots:", self)
        self.open_screenshots_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 141, 31))
        self.open_screenshots_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.open_screenshots_label.setToolTip("When enabled, opens screenshots with the system's default image viewer")

        self.open_screenshots_checkbox = QCheckBox(self)
        self.open_screenshots_checkbox.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 49 + self.TOP_EDGE_CORRECTION, 13, 13))

        self.open_screenshots_checkbox_helper_label = QLabel(self)
        self.open_screenshots_checkbox_helper_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 48 + self.TOP_EDGE_CORRECTION, 14, 15))
        self.open_screenshots_checkbox_helper_label.setObjectName("checkbox_helper")
        self.open_screenshots_checkbox_helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.open_screenshots_checkbox_helper_label.setGraphicsEffect(self.checkbox_shadow)

        # Default threshold spinbox
        self.default_threshold_label = QLabel("Default threshold:", self)
        self.default_threshold_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.default_threshold_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_threshold_label.setToolTip("Images must match at least this much to trigger a split, pause, etc.")
        
        self.default_threshold_double_spinbox = QDoubleSpinBox(self)
        self.default_threshold_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 72 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT))
        self.default_threshold_double_spinbox.setDecimals(2)
        self.default_threshold_double_spinbox.setMinimum(0.1)
        self.default_threshold_double_spinbox.setMaximum(100)
        self.default_threshold_double_spinbox.setSingleStep(0.1)
        self.default_threshold_double_spinbox.setSuffix("%")

        # Match percent decimals spinbox
        self.match_percent_decimals_label = QLabel("Similarity decimals:", self)
        self.match_percent_decimals_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.match_percent_decimals_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.match_percent_decimals_label.setToolTip("Images must match at least this much to trigger a split, pause, etc.")

        self.match_percent_decimals_spinbox = QSpinBox(self)
        self.match_percent_decimals_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 102 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT))
        self.match_percent_decimals_spinbox.setMinimum(0)
        self.match_percent_decimals_spinbox.setMaximum(2)

        # Default delay spinbox
        self.default_delay_label = QLabel("Default delay (sec.):", self)
        self.default_delay_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 201, 31))
        self.default_delay_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_delay_label.setToolTip("The default delay between the split threshold being reached and a split, pause, etc.")

        self.default_delay_double_spinbox = QDoubleSpinBox(self)
        self.default_delay_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 132 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT))
        self.default_delay_double_spinbox.setDecimals(3)
        self.default_delay_double_spinbox.setMinimum(0)
        self.default_delay_double_spinbox.setMaximum(10000000)
        self.default_delay_double_spinbox.setSingleStep(0.1)

        # Default pause spinbox
        self.default_pause_label = QLabel("Default pause (sec.):", self)
        self.default_pause_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.default_pause_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_pause_label.setToolTip("The default waiting period after a split and before starting to compare the next image. Set this setting higher to save CPU")

        self.default_pause_double_spinbox = QDoubleSpinBox(self)
        self.default_pause_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 162 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT))
        self.default_pause_double_spinbox.setDecimals(0)
        self.default_pause_double_spinbox.setMinimum(1)
        self.default_pause_double_spinbox.setMaximum(10000000)
        self.default_pause_double_spinbox.setSingleStep(1.0)

        # Aspect ratio combobox
        self.aspect_ratio_label = QLabel("GUI aspect ratio:", self)
        self.aspect_ratio_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.aspect_ratio_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.aspect_ratio_label.setToolTip("This affects how images are displayed on the GUI and matched with split images. However, you can use 16:9 when playing games at 4:3, or vice versa.")

        self.aspect_ratio_combo_box = QComboBox(self)
        self.aspect_ratio_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 194 + self.TOP_EDGE_CORRECTION, 130, self.LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.aspect_ratio_combo_box.addItems(["4:3 (480x360)", "4:3 (320x240)", "16:9 (512x288)", "16:9 (432x243)"])

        # Start with video checkbox
        self.start_with_video_label = QLabel("Start with video:", self)
        self.start_with_video_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.start_with_video_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.start_with_video_label.setToolTip("Try to open video feed on bootup. Note that this could open a webcam (or any video device attached to your computer), which is harmless but could be surprising!")

        self.start_with_video_checkbox = QCheckBox(self)
        self.start_with_video_checkbox.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 259 + self.TOP_EDGE_CORRECTION, 13, 13))

        self.start_with_video_checkbox_helper_label = QLabel(self)
        self.start_with_video_checkbox_helper_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 258 + self.TOP_EDGE_CORRECTION, 14, 15))
        self.start_with_video_checkbox_helper_label.setObjectName("checkbox_helper")
        self.start_with_video_checkbox_helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.start_with_video_checkbox_helper_label.setGraphicsEffect(self.checkbox_shadow)

        # Theme combobox
        self.theme_label = QLabel("Theme:", self)
        self.theme_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.theme_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.theme_label.setToolTip("Does anyone actually use light mode?")

        self.theme_combo_box = QComboBox(self)
        self.theme_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, self.LEFT_SIDE_WIDGET_WIDTH, self.LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.theme_combo_box.addItems(["dark", "light"])

        # Hotkey header
        self.hotkey_settings_label = QLabel("Hotkeys (click + type to change):", self)
        self.hotkey_settings_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 216, 31))
        self.hotkey_settings_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Start / split hotkey
        self.start_split_hotkey_label = QLabel("Start / split", self)
        self.start_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.start_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.start_split_hotkey_line_edit = KeyLineEdit(self)
        self.start_split_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 42 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.start_split_hotkey_line_edit.setReadOnly(True)

        self.start_split_hotkey_clear_button = QPushButton("clear", self)
        self.start_split_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 45 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.start_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.start_split_hotkey_clear_button.clicked.connect(lambda: self.start_split_hotkey_line_edit.setText(""))
        self.start_split_hotkey_clear_button.clicked.connect(lambda: setattr(self.start_split_hotkey_line_edit, "key_code", ""))

        # Reset splits hotkey
        self.reset_hotkey_label = QLabel("Reset splits", self)
        self.reset_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 91, 31))
        self.reset_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.reset_hotkey_line_edit = KeyLineEdit(self)
        self.reset_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 72 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.reset_hotkey_line_edit.setReadOnly(True)

        self.reset_hotkey_clear_button = QPushButton("clear", self)
        self.reset_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 75 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.reset_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.reset_hotkey_clear_button.clicked.connect(lambda: self.reset_hotkey_line_edit.setText(""))
        self.reset_hotkey_clear_button.clicked.connect(lambda: setattr(self.reset_hotkey_line_edit, "key_code", ""))

        # Pause hotkey
        self.pause_hotkey_label = QLabel("Pause timer", self)
        self.pause_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 91, 31))
        self.pause_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.pause_hotkey_line_edit = KeyLineEdit(self)
        self.pause_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 102 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.pause_hotkey_line_edit.setReadOnly(True)

        self.pause_hotkey_clear_button = QPushButton("clear", self)
        self.pause_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 105 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.pause_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.pause_hotkey_clear_button.clicked.connect(lambda: self.pause_hotkey_line_edit.setText(""))
        self.pause_hotkey_clear_button.clicked.connect(lambda: setattr(self.pause_hotkey_line_edit, "key_code", ""))

        # Undo split hotkey
        self.undo_split_hotkey_label = QLabel("Undo split", self)
        self.undo_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.undo_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.undo_split_hotkey_line_edit = KeyLineEdit(self)
        self.undo_split_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 132 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.undo_split_hotkey_line_edit.setReadOnly(True)

        self.undo_split_hotkey_clear_button = QPushButton("clear", self)
        self.undo_split_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 135 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.undo_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.undo_split_hotkey_clear_button.clicked.connect(lambda: self.undo_split_hotkey_line_edit.setText(""))
        self.undo_split_hotkey_clear_button.clicked.connect(lambda: setattr(self.undo_split_hotkey_line_edit, "key_code", ""))

        # Skip split hotkey
        self.skip_split_hotkey_label = QLabel("Skip split", self)
        self.skip_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.skip_split_hotkey_line_edit = KeyLineEdit(self)
        self.skip_split_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 162 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.skip_split_hotkey_line_edit.setReadOnly(True)

        self.skip_split_hotkey_clear_button = QPushButton("clear", self)
        self.skip_split_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 165 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.skip_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.skip_split_hotkey_clear_button.clicked.connect(lambda: self.skip_split_hotkey_line_edit.setText(""))
        self.skip_split_hotkey_clear_button.clicked.connect(lambda: setattr(self.skip_split_hotkey_line_edit, "key_code", ""))

        # Previous split hotkey
        self.previous_split_hotkey_label = QLabel("Previous split", self)
        self.previous_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 101, 31))
        self.previous_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.previous_split_hotkey_line_edit = KeyLineEdit(self)
        self.previous_split_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 192 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.previous_split_hotkey_line_edit.setReadOnly(True)

        self.previous_split_hotkey_clear_button = QPushButton("clear", self)
        self.previous_split_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 195 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.previous_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.previous_split_hotkey_clear_button.clicked.connect(lambda: self.previous_split_hotkey_line_edit.setText(""))
        self.previous_split_hotkey_clear_button.clicked.connect(lambda: setattr(self.previous_split_hotkey_line_edit, "key_code", ""))

        # Next split hotkey
        self.next_split_hotkey_label = QLabel("Next split", self)
        self.next_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.next_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.next_split_hotkey_line_edit = KeyLineEdit(self)
        self.next_split_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 222 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.next_split_hotkey_line_edit.setReadOnly(True)

        self.next_split_hotkey_clear_button = QPushButton("clear", self)
        self.next_split_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.next_split_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.next_split_hotkey_clear_button.clicked.connect(lambda: self.next_split_hotkey_line_edit.setText(""))
        self.next_split_hotkey_clear_button.clicked.connect(lambda: setattr(self.next_split_hotkey_line_edit, "key_code", ""))

        # Screenshot hotkey
        self.screenshot_hotkey_label = QLabel("Screenshot", self)
        self.screenshot_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.screenshot_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.screenshot_hotkey_line_edit = KeyLineEdit(self)
        self.screenshot_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 252 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.screenshot_hotkey_line_edit.setText(f'{settings.get_str("SCREENSHOT_HOTKEY_NAME")}')
        self.screenshot_hotkey_line_edit.setReadOnly(True)

        self.screenshot_hotkey_clear_button = QPushButton("clear", self)
        self.screenshot_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.screenshot_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.screenshot_hotkey_clear_button.clicked.connect(lambda: self.screenshot_hotkey_line_edit.setText(""))
        self.screenshot_hotkey_clear_button.clicked.connect(lambda: setattr(self.screenshot_hotkey_line_edit, "key_code", ""))

        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(QRect(319 + self.LEFT_EDGE_CORRECTION, 296 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.cancel_button.setFocusPolicy(Qt.NoFocus)
        self.cancel_button.clicked.connect(self.close)

        # Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.setGeometry(QRect(459 + self.LEFT_EDGE_CORRECTION, 296 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.save_button.setFocusPolicy(Qt.NoFocus)

        # Set all widget values to stored values
        self.reset_settings()

    # Called when self.close is called (red x is pressed to close window, keyboard shortcut closes window, cancel button pressed, etc.)
    def closeEvent(self, _):
        self.is_showing = False
        self.reset_settings()

    def open(self):
        super().open()
        self.is_showing = True

    # Called when save button is pressed
    def reset_settings(self):
        self.setFocus(True)  # Take focus off the last widget the user selected
        
        # Settings aren't reset automatically when the window is closed, so they are read from utils.settings and placed back manually here
        # Spinboxes
        for spinbox, value in {
            self.fps_spinbox: settings.get_int("FPS"),
            self.default_threshold_double_spinbox: str(float(settings.get_float("DEFAULT_THRESHOLD") * 100)),
            self.match_percent_decimals_spinbox: settings.get_int("MATCH_PERCENT_DECIMALS"),
            self.default_delay_double_spinbox: settings.get_float("DEFAULT_DELAY"),
            self.default_pause_double_spinbox: settings.get_float("DEFAULT_PAUSE"),
        }.items():
            spinbox.setProperty("value", value)

        # Checkboxes
        for checkbox, value in {
            self.open_screenshots_checkbox: settings.get_bool("OPEN_SCREENSHOT_ON_CAPTURE"),
            self.start_with_video_checkbox: settings.get_bool("START_WITH_VIDEO"),
        }.items():
            if value:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        # Hotkeys
        for hotkey_line_edit, values in {
            self.start_split_hotkey_line_edit: (settings.get_str("SPLIT_HOTKEY_NAME"), settings.get_str("SPLIT_HOTKEY_CODE")),
            self.reset_hotkey_line_edit: (settings.get_str("RESET_HOTKEY_NAME"), settings.get_str("RESET_HOTKEY_CODE")),
            self.pause_hotkey_line_edit: (settings.get_str("PAUSE_HOTKEY_NAME"), settings.get_str("PAUSE_HOTKEY_CODE")),
            self.undo_split_hotkey_line_edit: (settings.get_str("UNDO_HOTKEY_NAME"), settings.get_str("UNDO_HOTKEY_CODE")),
            self.skip_split_hotkey_line_edit: (settings.get_str("SKIP_HOTKEY_NAME"), settings.get_str("SKIP_HOTKEY_CODE")),
            self.previous_split_hotkey_line_edit: (settings.get_str("PREVIOUS_HOTKEY_NAME"), settings.get_str("PREVIOUS_HOTKEY_CODE")),
            self.next_split_hotkey_line_edit: (settings.get_str("NEXT_HOTKEY_NAME"), settings.get_str("NEXT_HOTKEY_CODE")),
            self.screenshot_hotkey_line_edit: (settings.get_str("SCREENSHOT_HOTKEY_NAME"), settings.get_str("SCREENSHOT_HOTKEY_CODE")),
        }.items():
            hotkey_line_edit.setText(values[0])
            hotkey_line_edit.key_name = values[0]
            hotkey_line_edit.key_code = values[1]

        # Comboboxes
        if settings.get_str("ASPECT_RATIO") == "4:3 (480x360)":
            self.aspect_ratio_combo_box.setCurrentIndex(0)
        elif settings.get_str("ASPECT_RATIO") == "4:3 (320x240)":
            self.aspect_ratio_combo_box.setCurrentIndex(1)
        elif settings.get_str("ASPECT_RATIO") == "16:9 (512x288)":
            self.aspect_ratio_combo_box.setCurrentIndex(2)
        elif settings.get_str("ASPECT_RATIO") == "16:9 (432x243)":
            self.aspect_ratio_combo_box.setCurrentIndex(3)

        if settings.get_str("THEME") == "dark":
            self.theme_combo_box.setCurrentIndex(0)
        elif settings.get_str("THEME") == "light":
            self.theme_combo_box.setCurrentIndex(1)

    # Allow user to take focus off a widget by clicking empty space
    def event(self, event):
        if (event.type() == QEvent.MouseButtonPress):
            self.setFocus(True)
            return True
        return QWidget.event(self, event)
    
class KeyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.key_code = ""
