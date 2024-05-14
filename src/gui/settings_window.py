from PyQt5.QtCore import QRect, Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
                             QFrame, QKeySequenceEdit, QLabel, QPushButton,
                             QSpinBox, QWidget, QAction, QLineEdit, QShortcut, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QColor, QKeySequence

from utils import settings


class GUISettingsWindow(QDialog):
    LEFT_EDGE_CORRECTION = 0
    TOP_EDGE_CORRECTION = 3
    LEFT_EDGE_CORRECTION_FRAME = 0
    TOP_EDGE_CORRECTION_FRAME = 0
    LEFT_SIDE_WIDGET_WIDTH = 70
    LEFT_SIDE_WIDGET_HEIGHT = 27

    def __init__(self, style):
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        # Set size, title
        self.setFixedSize(610, 362)
        self.setWindowTitle("Settings")

        # Shortcuts
        self.close_window_action = QAction("Close Window", self)
        self.close_window_action.setShortcuts(["ctrl+.", "ctrl+w"])  # ctrl+. already closes the window since main_window has this shortcut, but this overrides it... is that needed? reset_settings was being called twice before but maybe now it's ok -- check
        self.close_window_action.triggered.connect(self.close)
        
        self.close_app_shortcut = QShortcut("ctrl+q", self)

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
        self.fps_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 12 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(120)

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
        self.default_threshold_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 72 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
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
        self.match_percent_decimals_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 102 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.match_percent_decimals_spinbox.setMinimum(0)
        self.match_percent_decimals_spinbox.setMaximum(2)

        # Default delay spinbox
        self.default_delay_label = QLabel("Default delay (sec.):", self)
        self.default_delay_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 201, 31))
        self.default_delay_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_delay_label.setToolTip("The default delay between the split threshold being reached and a split, pause, etc.")

        self.default_delay_double_spinbox = QDoubleSpinBox(self)
        self.default_delay_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 132 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
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
        self.default_pause_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 162 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.default_pause_double_spinbox.setDecimals(0)
        self.default_pause_double_spinbox.setMinimum(0)
        self.default_pause_double_spinbox.setMaximum(10000000)
        self.default_pause_double_spinbox.setSingleStep(1.0)

        # Aspect ratio combobox
        self.aspect_ratio_label = QLabel("GUI aspect ratio:", self)
        self.aspect_ratio_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.aspect_ratio_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.aspect_ratio_label.setToolTip("This affects how images are displayed on the GUI and matched with split images. However, you can use 16:9 when playing games at 4:3, or vice versa.")

        self.aspect_ratio_combo_box = QComboBox(self)
        self.aspect_ratio_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 194 + self.TOP_EDGE_CORRECTION, 130, LEFT_SIDE_WIDGET_HEIGHT - 4))
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
        self.theme_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT - 4))
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
        self.start_split_hotkey_clear_button.clicked.connect(lambda: self.start_split_hotkey_line_edit.set_key_sequence(None))

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
        self.reset_hotkey_clear_button.clicked.connect(lambda: self.reset_hotkey_line_edit.set_key_sequence(None))

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
        self.pause_hotkey_clear_button.clicked.connect(lambda: self.pause_hotkey_line_edit.set_key_sequence(None))

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
        self.undo_split_hotkey_clear_button.clicked.connect(lambda: self.undo_split_hotkey_line_edit.set_key_sequence(None))

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
        self.skip_split_hotkey_clear_button.clicked.connect(lambda: self.skip_split_hotkey_line_edit.set_key_sequence(None))

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
        self.previous_split_hotkey_clear_button.clicked.connect(lambda: self.previous_split_hotkey_line_edit.set_key_sequence(None))

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
        self.next_split_hotkey_clear_button.clicked.connect(lambda: self.next_split_hotkey_line_edit.set_key_sequence(None))

        # Screenshot hotkey
        self.screenshot_hotkey_label = QLabel("Screenshot", self)
        self.screenshot_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.screenshot_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.screenshot_hotkey_line_edit = KeyLineEdit(self)
        self.screenshot_hotkey_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 252 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.screenshot_hotkey_line_edit.setText(f'{settings.value("SCREENSHOT_HOTKEY_TEXT")}')
        self.screenshot_hotkey_line_edit.setReadOnly(True)

        self.screenshot_hotkey_clear_button = QPushButton("clear", self)
        self.screenshot_hotkey_clear_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.screenshot_hotkey_clear_button.setFocusPolicy(Qt.NoFocus)
        self.screenshot_hotkey_clear_button.clicked.connect(lambda: self.screenshot_hotkey_line_edit.setText(""))
        self.screenshot_hotkey_clear_button.clicked.connect(lambda: self.screenshot_hotkey_line_edit.set_key_sequence(None))

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

    def closeEvent(self, _):
        self.reset_settings()

    def reset_settings(self):
        self.setFocus(True)  # Take focus off the last widget the user selected
        
        # Settings aren't reset automatically when the window is closed, so they are read from utils.settings and placed back manually here
        # Spinboxes
        for spinbox, setting in {
            self.fps_spinbox: settings.value("FPS"),
            self.default_threshold_double_spinbox: str(float(settings.value("DEFAULT_THRESHOLD") * 100)),
            self.match_percent_decimals_spinbox: settings.value("MATCH_PERCENT_DECIMALS"),
            self.default_delay_double_spinbox: settings.value("DEFAULT_DELAY"),
            self.default_pause_double_spinbox: settings.value("DEFAULT_PAUSE"),
        }.items():
            spinbox.setProperty("value", setting)

        # Checkboxes
        for checkbox, setting in {
            self.open_screenshots_checkbox: settings.value("OPEN_SCREENSHOT_ON_CAPTURE"),
            self.start_with_video_checkbox: settings.value("START_WITH_VIDEO"),
        }.items():
            if setting:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        # Hotkeys
        for hotkey_line_edit, settings in {
            self.start_split_hotkey_line_edit: (settings.value("SPLIT_HOTKEY_TEXT"), settings.value("SPLIT_HOTKEY_KEY_SEQUENCE")),
            self.reset_hotkey_line_edit: (settings.value("RESET_HOTKEY_TEXT"), settings.value("RESET_HOTKEY_KEY_SEQUENCE")),
            self.pause_hotkey_line_edit: (settings.value("PAUSE_HOTKEY_TEXT"), settings.value("PAUSE_HOTKEY_KEY_SEQUENCE")),
            self.undo_split_hotkey_line_edit: (settings.value("UNDO_HOTKEY_TEXT"), settings.value("UNDO_HOTKEY_KEY_SEQUENCE")),
            self.skip_split_hotkey_line_edit: (settings.value("SKIP_HOTKEY_TEXT"), settings.value("SKIP_HOTKEY_KEY_SEQUENCE")),
            self.previous_split_hotkey_line_edit: (settings.value("PREVIOUS_HOTKEY_TEXT"), settings.value("PREVIOUS_HOTKEY_KEY_SEQUENCE")),
            self.next_split_hotkey_line_edit: (settings.value("NEXT_HOTKEY_TEXT"), settings.value("NEXT_HOTKEY_KEY_SEQUENCE")),
            self.screenshot_hotkey_line_edit: (settings.value("SCREENSHOT_HOTKEY_TEXT"), settings.value("SCREENSHOT_HOTKEY_KEY_SEQUENCE")),
        }.items():
            hotkey_line_edit.setText(settings[0])
            hotkey_line_edit.key_sequence = settings[1]

        # Comboboxes
        if settings.value("ASPECT_RATIO") == "4:3 (480x360)":
            self.aspect_ratio_combo_box.setCurrentIndex(0)
        elif settings.value("ASPECT_RATIO") == "4:3 (320x240)":
            self.aspect_ratio_combo_box.setCurrentIndex(1)
        elif settings.value("ASPECT_RATIO") == "16:9 (512x288)":
            self.aspect_ratio_combo_box.setCurrentIndex(2)
        elif settings.value("ASPECT_RATIO") == "16:9 (432x243)":
            self.aspect_ratio_combo_box.setCurrentIndex(3)

        if settings.value("THEME") == "dark":
            self.theme_combo_box.setCurrentIndex(0)
        elif settings.value("THEME") == "light":
            self.theme_combo_box.setCurrentIndex(1)

    def event(self, event):
        # Allow user to take focus off a widget by clicking empty space
        if (event.type() == QEvent.MouseButtonPress):
            self.setFocus(True)
            return True
        return QWidget.event(self, event)


class KeyLineEdit(QLineEdit):
    keys_macos = {
        32: "space",
        33: "!",
        34: "\"",
        35: "#",
        36: "$",
        37: "%",
        38: "&",
        39: "'",
        40: "(",
        41: ")",
        42: "*",
        43: "+",
        44: ",",
        45: "-",
        46: ".",
        47: "/",
        48: "0",
        49: "1",
        50: "2",
        51: "3",
        52: "4",
        53: "5",
        54: "6",
        55: "7",
        56: "8",
        57: "9",
        58: ":",
        59: ";",
        60: "<",
        61: "=",
        62: ">",
        63: "?",
        64: "@",
        65: "a",
        66: "b",
        67: "c",
        68: "d",
        69: "e",
        70: "f",
        71: "g",
        72: "h",
        73: "i",
        74: "j",
        75: "k",
        76: "l",
        77: "m",
        78: "n",
        79: "o",
        80: "p",
        81: "Q",
        81: "q",
        82: "r",
        83: "s",
        84: "t",
        85: "u",
        86: "v",
        87: "w",
        88: "x",
        89: "y",
        90: "Z",
        90: "z",
        91: "[",
        92: "\\",
        93: "]",
        94: "^",
        95: "_",
        96: "`",
        123: "{",
        124: "|",
        125: "}",
        126: "~",
        63289: "delete",
        777220: "return",
        16777216: "esc",
        16777217: "tab",
        16777219: "backspace",
        16777220: "return",
        16777221: "enter",
        16777223: "delete",
        16777232: "home",
        16777233: "end",
        16777234: "left",
        16777235: "up",
        16777236: "right",
        16777237: "down",
        16777238: "page up",
        16777239: "page down",
        16777248: "shift",
        16777249: "cmd",
        16777250: "ctrl",
        16777251: "option",
        16777252: "caps lock",
        16777264: "f1",
        16777265: "f2",
        16777266: "f3",
        16777267: "f4",
        16777268: "f5",
        16777269: "f6",
        16777270: "f7",
        16777271: "f8",
        16777272: "f9",
        16777273: "f10",
        16777274: "f11",
        16777275: "f12",
        16777276: "f13",
        16777277: "f14",
        16777278: "f15",
        16777279: "f16",
        16777280: "f17",
        16777281: "f18",
        16777282: "f19",
    }

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.key_sequence = QKeySequence()

    def event(self, event):
        if (event.type() == QEvent.KeyPress):
            decoded_key = self.decode_key(event.key())
            if decoded_key == "":
                self.key_sequence = None
                self.setText("")
            else:
                self.key_sequence = QKeySequence(event.key())
                self.setText(decoded_key)
            return True
        return QWidget.event(self, event)

    def set_key_sequence(self, key_sequence: QKeySequence):
        self.key_sequence = key_sequence

    def decode_key(self, key):
        try:
            return self.keys_macos[key]
        except KeyError:
            return ""
