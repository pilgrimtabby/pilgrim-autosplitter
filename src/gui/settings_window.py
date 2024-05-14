from PyQt5.QtCore import QRect, Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
                             QFrame, QKeySequenceEdit, QLabel, QPushButton,
                             QSpinBox, QWidget, QLineEdit, QShortcut, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QColor, QKeySequence

from utils import settings


class GUISettingsWindow(QDialog):
    set_global_style_signal = pyqtSignal()
    update_fps_start_signal = pyqtSignal()
    update_fps_finish_signal = pyqtSignal()
    update_aspect_ratio_start_signal = pyqtSignal()
    update_aspect_ratio_finish_signal = pyqtSignal()
    set_match_percent_decimals_signal = pyqtSignal()
    updated_default_threshold_signal = pyqtSignal()
    updated_default_delay_signal = pyqtSignal()
    updated_default_pause_signal = pyqtSignal()
    close_app_signal = pyqtSignal()
    set_shortcut_signal = pyqtSignal()

    def __init__(self, style):
        super().__init__()
        # Constants (to facilitate moving things around)
        self.LEFT_EDGE_CORRECTION = 0
        self.TOP_EDGE_CORRECTION = 3
        self.LEFT_EDGE_CORRECTION_FRAME = 0
        self.TOP_EDGE_CORRECTION_FRAME = 0

        # Settings window settings
        self.setWindowTitle("Settings")
        self.setFixedSize(610, 362)
        self.setFocus(True)
        self.style = style
        self.style.set_style(self)
        self.key_decoder = KeyDecoder()
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)
        self.close_window_shortcut_2 = QShortcut("ctrl+.", self)
        self.close_window_shortcut_2.activated.connect(self.close)
        self.close_app_shortcut = QShortcut("ctrl+q", self)
        self.close_app_shortcut.activated.connect(self.close)
        self.close_app_shortcut.activated.connect(self.close_app_signal.emit)     


        # Border
        self.border_helper_frame = QFrame(self)
        self.border_helper_frame.setGeometry(QRect(10 + self.LEFT_EDGE_CORRECTION_FRAME, 10 + self.TOP_EDGE_CORRECTION_FRAME, 590, 342))
        self.border_helper_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.border_helper_frame.setObjectName("border")

        # Labels
        self.fps_label = QLabel(self)
        self.fps_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 131, 31))
        self.fps_label.setText("Frames per second:")
        self.fps_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.fps_label.setToolTip("Read this many frames per second from video source")

        self.open_screenshots_label = QLabel(self)
        self.open_screenshots_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 141, 31))
        self.open_screenshots_label.setText("Open screenshots:")
        self.open_screenshots_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.open_screenshots_label.setToolTip("When enabled, opens screenshots with the system's default image viewer")

        self.default_threshold_label = QLabel(self)
        self.default_threshold_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.default_threshold_label.setText("Default threshold:")
        self.default_threshold_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_threshold_label.setToolTip("Images must match at least this much to trigger a split, pause, etc.")

        self.match_percent_decimals_label = QLabel(self)
        self.match_percent_decimals_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.match_percent_decimals_label.setText("Similarity decimals:")
        self.match_percent_decimals_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.match_percent_decimals_label.setToolTip("Images must match at least this much to trigger a split, pause, etc.")

        self.default_delay_label = QLabel(self)
        self.default_delay_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 201, 31))
        self.default_delay_label.setText("Default delay (sec.):")
        self.default_delay_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_delay_label.setToolTip("The default delay between the split threshold being reached and a split, pause, etc.")

        self.default_pause_label = QLabel(self)
        self.default_pause_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.default_pause_label.setText("Default pause (sec.):")
        self.default_pause_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.default_pause_label.setToolTip("The default waiting period after a split and before starting to compare the next image. Set this setting higher to save CPU")

        self.aspect_ratio_label = QLabel(self)
        self.aspect_ratio_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.aspect_ratio_label.setText("GUI aspect ratio:")
        self.aspect_ratio_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.aspect_ratio_label.setToolTip("This affects how images are displayed on the GUI and matched with split images. However, you can use 16:9 when playing games at 4:3, or vice versa.")

        self.start_with_video_label = QLabel(self)
        self.start_with_video_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.start_with_video_label.setText("Start with video:")
        self.start_with_video_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.start_with_video_label.setToolTip("Try to open video feed on bootup. Note that this could open a webcam (or any video device attached to your computer), which is harmless but could be surprising!")

        self.theme_label = QLabel(self)
        self.theme_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.theme_label.setText("Theme:")
        self.theme_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.theme_label.setToolTip("Does anyone actually use light mode?")

        self.hotkey_settings_label = QLabel(self)
        self.hotkey_settings_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 216, 31))
        self.hotkey_settings_label.setText("Hotkeys (click + type to change):")
        self.hotkey_settings_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.start_split_hotkey_label = QLabel(self)
        self.start_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.start_split_hotkey_label.setText("Start / split")
        self.start_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.reset_hotkey_label = QLabel(self)
        self.reset_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 91, 31))
        self.reset_hotkey_label.setText("Reset splits")
        self.reset_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.pause_hotkey_label = QLabel(self)
        self.pause_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 91, 31))
        self.pause_hotkey_label.setText("Pause timer")
        self.pause_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.undo_split_hotkey_label = QLabel(self)
        self.undo_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.undo_split_hotkey_label.setText("Undo split")
        self.undo_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.skip_split_hotkey_label = QLabel(self)
        self.skip_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.skip_split_hotkey_label.setText("Skip split")
        self.skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.skip_split_hotkey_label = QLabel(self)
        self.skip_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 101, 31))
        self.skip_split_hotkey_label.setText("Previous split")
        self.skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.skip_split_hotkey_label = QLabel(self)
        self.skip_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.skip_split_hotkey_label.setText("Next split")
        self.skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.screenshot_hotkey_label = QLabel(self)
        self.screenshot_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.screenshot_hotkey_label.setText("Screenshot")
        self.screenshot_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Non-label widgets
        LEFT_SIDE_WIDGET_WIDTH = 70
        LEFT_SIDE_WIDGET_HEIGHT = 27
        self.checkbox_shadow = QGraphicsDropShadowEffect()
        self.checkbox_shadow.setBlurRadius(10)
        self.checkbox_shadow.setOffset(12)
        self.checkbox_shadow.setColor(QColor(0, 0, 0, 1))

        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 12 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(120)
        self.fps_spinbox.setProperty("value", settings.value("FPS"))

        self.open_screenshots_checkbox = QCheckBox(self)
        self.open_screenshots_checkbox.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 49 + self.TOP_EDGE_CORRECTION, 13, 13))
        if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            self.open_screenshots_checkbox.setCheckState(Qt.Checked)
        else:
            self.open_screenshots_checkbox.setCheckState(Qt.Unchecked)

        self.open_screenshots_checkbox_helper_label = QLabel(self)
        self.open_screenshots_checkbox_helper_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 48 + self.TOP_EDGE_CORRECTION, 14, 15))
        self.open_screenshots_checkbox_helper_label.setObjectName("checkbox_helper")
        self.open_screenshots_checkbox_helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.open_screenshots_checkbox_helper_label.setGraphicsEffect(self.checkbox_shadow)

        self.default_threshold_double_spinbox = QDoubleSpinBox(self)
        self.default_threshold_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 72 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.default_threshold_double_spinbox.setDecimals(1)
        self.default_threshold_double_spinbox.setMinimum(0.1)
        self.default_threshold_double_spinbox.setMaximum(100)
        self.default_threshold_double_spinbox.setSingleStep(0.1)
        self.default_threshold_double_spinbox.setProperty("value", str(float(settings.value("DEFAULT_THRESHOLD") * 100)))
        self.default_threshold_double_spinbox.setSuffix("%")

        self.match_percent_decimals_spinbox = QSpinBox(self)
        self.match_percent_decimals_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 102 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.match_percent_decimals_spinbox.setMinimum(0)
        self.match_percent_decimals_spinbox.setMaximum(2)
        self.match_percent_decimals_spinbox.setProperty("value", settings.value("MATCH_PERCENT_DECIMALS"))

        self.default_delay_double_spinbox = QDoubleSpinBox(self)
        self.default_delay_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 132 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.default_delay_double_spinbox.setDecimals(3)
        self.default_delay_double_spinbox.setMinimum(0)
        self.default_delay_double_spinbox.setMaximum(10000000)
        self.default_delay_double_spinbox.setSingleStep(0.1)
        self.default_delay_double_spinbox.setProperty("value", settings.value("DEFAULT_DELAY"))

        self.default_pause_double_spinbox = QDoubleSpinBox(self)
        self.default_pause_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 162 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.default_pause_double_spinbox.setDecimals(0)
        self.default_pause_double_spinbox.setMinimum(0)
        self.default_pause_double_spinbox.setMaximum(10000000)
        self.default_pause_double_spinbox.setSingleStep(1.0)
        self.default_pause_double_spinbox.setProperty("value", settings.value("DEFAULT_PAUSE"))

        self.aspect_ratio_combo_box = QComboBox(self)
        self.aspect_ratio_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 194 + self.TOP_EDGE_CORRECTION, 130, LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.aspect_ratio_combo_box.addItems(["4:3 (480x360)", "4:3 (320x240)", "16:9 (512x288)", "16:9 (432x243)"])
        self.aspect_ratio_combo_box.setCurrentIndex(-1)
        if settings.value("ASPECT_RATIO") == "4:3 (480x360)":
            self.aspect_ratio_combo_box.setCurrentIndex(0)
        elif settings.value("ASPECT_RATIO") == "4:3 (320x240)":
            self.aspect_ratio_combo_box.setCurrentIndex(1)
        elif settings.value("ASPECT_RATIO") == "16:9 (512x288)":
            self.aspect_ratio_combo_box.setCurrentIndex(2)
        elif settings.value("ASPECT_RATIO") == "16:9 (432x243)":
            self.aspect_ratio_combo_box.setCurrentIndex(3)
        self.aspect_ratio_combo_box.setObjectName("combo_box")

        self.start_with_video_checkbox = QCheckBox(self)
        self.start_with_video_checkbox.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 259 + self.TOP_EDGE_CORRECTION, 13, 13))
        if settings.value("START_WITH_VIDEO"):
            self.start_with_video_checkbox.setCheckState(Qt.Checked)
        else:
            self.start_with_video_checkbox.setCheckState(Qt.Unchecked)

        self.start_with_video_checkbox_helper_label = QLabel(self)
        self.start_with_video_checkbox_helper_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 258 + self.TOP_EDGE_CORRECTION, 14, 15))
        self.start_with_video_checkbox_helper_label.setObjectName("checkbox_helper")
        self.start_with_video_checkbox_helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.start_with_video_checkbox_helper_label.setGraphicsEffect(self.checkbox_shadow)

        self.theme_combo_box = QComboBox(self)
        self.theme_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.theme_combo_box.addItems(["dark", "light"])
        self.theme_combo_box.setCurrentIndex(-1)
        if settings.value("THEME") == "dark":
            self.theme_combo_box.setCurrentIndex(0)
        elif settings.value("THEME") == "light":
            self.theme_combo_box.setCurrentIndex(1)
        self.theme_combo_box.setObjectName("combo_box")

        self.start_split_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.start_split_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 42 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.start_split_hotkey_shortcut_line_edit.setText(f'{settings.value("SPLIT_HOTKEY_TEXT")}')
        self.start_split_hotkey_shortcut_line_edit.setReadOnly(True)

        self.reset_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.reset_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 72 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.reset_hotkey_shortcut_line_edit.setText(f'{settings.value("RESET_HOTKEY_TEXT")}')
        self.reset_hotkey_shortcut_line_edit.setReadOnly(True)

        self.pause_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.pause_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 102 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.pause_hotkey_shortcut_line_edit.setText(f'{settings.value("PAUSE_HOTKEY_TEXT")}')
        self.pause_hotkey_shortcut_line_edit.setReadOnly(True)

        self.undo_split_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.undo_split_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 132 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.undo_split_hotkey_shortcut_line_edit.setText(f'{settings.value("UNDO_HOTKEY_TEXT")}')
        self.undo_split_hotkey_shortcut_line_edit.setReadOnly(True)

        self.skip_split_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.skip_split_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 162 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.skip_split_hotkey_shortcut_line_edit.setText(f'{settings.value("SKIP_HOTKEY_TEXT")}')
        self.skip_split_hotkey_shortcut_line_edit.setReadOnly(True)

        self.previous_split_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.previous_split_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 192 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.previous_split_hotkey_shortcut_line_edit.setText(f'{settings.value("PREVIOUS_HOTKEY_TEXT")}')
        self.previous_split_hotkey_shortcut_line_edit.setReadOnly(True)

        self.next_split_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.next_split_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 222 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.next_split_hotkey_shortcut_line_edit.setText(f'{settings.value("NEXT_HOTKEY_TEXT")}')
        self.next_split_hotkey_shortcut_line_edit.setReadOnly(True)

        self.screenshot_hotkey_shortcut_line_edit = KeyLineEdit(self)
        self.screenshot_hotkey_shortcut_line_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 252 + self.TOP_EDGE_CORRECTION, 121, 25))
        self.screenshot_hotkey_shortcut_line_edit.setText(f'{settings.value("SCREENSHOT_HOTKEY_TEXT")}')
        self.screenshot_hotkey_shortcut_line_edit.setReadOnly(True)

        # Buttons
        self.start_split_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.start_split_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 45 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.start_split_hotkey_shortcut_line_edit_button.setText("clear")
        self.start_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.start_split_hotkey_shortcut_line_edit.setText(""))
        self.start_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.start_split_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.start_split_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.start_split_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.reset_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.reset_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 75 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.reset_hotkey_shortcut_line_edit_button.setText("clear")
        self.reset_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.reset_hotkey_shortcut_line_edit.setText(""))
        self.reset_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.reset_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.reset_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.reset_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.pause_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.pause_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 105 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.pause_hotkey_shortcut_line_edit_button.setText("clear")
        self.pause_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.pause_hotkey_shortcut_line_edit.setText(""))
        self.pause_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.pause_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.pause_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.pause_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.undo_split_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.undo_split_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 135 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.undo_split_hotkey_shortcut_line_edit_button.setText("clear")
        self.undo_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.undo_split_hotkey_shortcut_line_edit.setText(""))
        self.undo_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.undo_split_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.undo_split_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.undo_split_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.skip_split_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.skip_split_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 165 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.skip_split_hotkey_shortcut_line_edit_button.setText("clear")
        self.skip_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.skip_split_hotkey_shortcut_line_edit.setText(""))
        self.skip_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.skip_split_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.skip_split_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.skip_split_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.previous_split_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.previous_split_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 195 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.previous_split_hotkey_shortcut_line_edit_button.setText("clear")
        self.previous_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.previous_split_hotkey_shortcut_line_edit.setText(""))
        self.previous_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.previous_split_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.previous_split_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.previous_split_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.next_split_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.next_split_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.next_split_hotkey_shortcut_line_edit_button.setText("clear")
        self.next_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.next_split_hotkey_shortcut_line_edit.setText(""))
        self.next_split_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.next_split_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.next_split_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.next_split_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.screenshot_hotkey_shortcut_line_edit_button = QPushButton(self)
        self.screenshot_hotkey_shortcut_line_edit_button.setGeometry(QRect(545 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.screenshot_hotkey_shortcut_line_edit_button.setText("clear")
        self.screenshot_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.screenshot_hotkey_shortcut_line_edit.setText(""))
        self.screenshot_hotkey_shortcut_line_edit_button.clicked.connect(lambda: self.screenshot_hotkey_shortcut_line_edit.set_key_sequence(None))
        self.screenshot_hotkey_shortcut_line_edit_button.setObjectName("clear_button")
        self.screenshot_hotkey_shortcut_line_edit_button.setFocusPolicy(Qt.NoFocus)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setGeometry(QRect(319 + self.LEFT_EDGE_CORRECTION, 296 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setFocusPolicy(Qt.NoFocus)

        self.save_button = QPushButton(self)
        self.save_button.setGeometry(QRect(459 + self.LEFT_EDGE_CORRECTION, 296 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.save_new_settings)
        self.save_button.clicked.connect(self.close)
        self.save_button.setObjectName("save_button")
        self.save_button.setFocusPolicy(Qt.NoFocus)


    def closeEvent(self, event):
        self.reset_settings()

    def reset_settings(self):
        self.setFocus(True)

        self.fps_spinbox.setProperty("value", settings.value("FPS"))
        if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            self.open_screenshots_checkbox.setCheckState(Qt.Checked)
        else:
            self.open_screenshots_checkbox.setCheckState(Qt.Unchecked)
        self.default_threshold_double_spinbox.setProperty("value", str(float(settings.value("DEFAULT_THRESHOLD") * 100)))
        self.match_percent_decimals_spinbox.setProperty("value", settings.value("MATCH_PERCENT_DECIMALS"))
        self.default_delay_double_spinbox.setProperty("value", settings.value("DEFAULT_DELAY"))
        self.default_pause_double_spinbox.setProperty("value", settings.value("DEFAULT_PAUSE"))
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

        hotkey_text, hotkey_key_sequence = settings.value("SPLIT_HOTKEY_TEXT"), settings.value("SPLIT_HOTKEY_KEY_SEQUENCE")
        self.start_split_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.start_split_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("RESET_HOTKEY_TEXT"), settings.value("RESET_HOTKEY_KEY_SEQUENCE")
        self.reset_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.reset_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("PAUSE_HOTKEY_TEXT"), settings.value("PAUSE_HOTKEY_KEY_SEQUENCE")
        self.pause_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.pause_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("UNDO_HOTKEY_TEXT"), settings.value("UNDO_HOTKEY_KEY_SEQUENCE")
        self.undo_split_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.undo_split_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("SKIP_HOTKEY_TEXT"), settings.value("SKIP_HOTKEY_KEY_SEQUENCE")
        self.skip_split_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.skip_split_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("PREVIOUS_HOTKEY_TEXT"), settings.value("PREVIOUS_HOTKEY_KEY_SEQUENCE")
        self.previous_split_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.previous_split_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("NEXT_HOTKEY_TEXT"), settings.value("NEXT_HOTKEY_KEY_SEQUENCE")
        self.next_split_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.next_split_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

        hotkey_text, hotkey_key_sequence = settings.value("SCREENSHOT_HOTKEY_TEXT"), settings.value("SCREENSHOT_HOTKEY_KEY_SEQUENCE")
        self.screenshot_hotkey_shortcut_line_edit.setText(hotkey_text)
        self.screenshot_hotkey_shortcut_line_edit.key_sequence = hotkey_key_sequence

    def save_new_settings(self):
        self.setFocus(True)

        fps = self.fps_spinbox.value()
        if fps != settings.value("FPS"):
            self.update_fps_start_signal.emit()
            settings.setValue("FPS", fps)
            self.update_fps_finish_signal.emit()

        open_screenshots_value = self.open_screenshots_checkbox.checkState()
        if open_screenshots_value == 0:
            open_screenshots = False
        else:
            open_screenshots = True
        if open_screenshots != settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", open_screenshots)

        default_threshold = float(self.default_threshold_double_spinbox.value()) / 100
        if default_threshold != settings.value("DEFAULT_THRESHOLD"):
            settings.setValue("DEFAULT_THRESHOLD", default_threshold)
            self.updated_default_threshold_signal.emit()

        match_percent_decimals = self.match_percent_decimals_spinbox.value()
        if match_percent_decimals != settings.value("MATCH_PERCENT_DECIMALS"):
            settings.setValue("MATCH_PERCENT_DECIMALS", match_percent_decimals)
            self.set_match_percent_decimals_signal.emit()

        default_delay = self.default_delay_double_spinbox.value()
        if default_delay != settings.value("DEFAULT_DELAY"):
            settings.setValue("DEFAULT_DELAY", default_delay)
            self.updated_default_delay_signal.emit()

        default_pause = self.default_pause_double_spinbox.value()
        if default_pause != settings.value("DEFAULT_PAUSE"):
            settings.setValue("DEFAULT_PAUSE", default_pause)
            self.updated_default_pause_signal.emit()

        aspect_ratio = self.aspect_ratio_combo_box.currentText()
        if aspect_ratio != settings.value("ASPECT_RATIO"):
            self.update_aspect_ratio_start_signal.emit()
            if aspect_ratio == "4:3 (480x360)":
                settings.setValue("ASPECT_RATIO", "4:3 (480x360)")
                settings.setValue("FRAME_WIDTH", 480)
                settings.setValue("FRAME_HEIGHT", 360)
            if aspect_ratio == "4:3 (320x240)":
                settings.setValue("ASPECT_RATIO", "4:3 (320x240)")
                settings.setValue("FRAME_WIDTH", 320)
                settings.setValue("FRAME_HEIGHT", 240)
            if aspect_ratio == "16:9 (512x288)":
                settings.setValue("ASPECT_RATIO", "16:9 (512x288)")
                settings.setValue("FRAME_WIDTH", 512)
                settings.setValue("FRAME_HEIGHT", 288)
            if aspect_ratio == "16:9 (432x243)":
                settings.setValue("ASPECT_RATIO", "16:9 (432x243)")
                settings.setValue("FRAME_WIDTH", 432)
                settings.setValue("FRAME_HEIGHT", 243)
            self.update_aspect_ratio_finish_signal.emit()

        start_with_video_value = self.start_with_video_checkbox.checkState()
        if start_with_video_value == 0:
            start_with_video = False
        else:
            start_with_video = True
        if start_with_video != settings.value("START_WITH_VIDEO"):
            settings.setValue("START_WITH_VIDEO", start_with_video)

        theme = self.theme_combo_box.currentText()
        if theme != settings.value("THEME"):
            if theme == "dark":
                settings.setValue("THEME", "dark")
            elif theme == "light":
                settings.setValue("THEME", "light")

        hotkey_changed = False

        hotkey_text, hotkey_key_sequence = self.start_split_hotkey_shortcut_line_edit.text(), self.start_split_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("SPLIT_HOTKEY_TEXT"):
            settings.setValue("SPLIT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SPLIT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.reset_hotkey_shortcut_line_edit.text(), self.reset_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("RESET_HOTKEY_TEXT"):
            settings.setValue("RESET_HOTKEY_TEXT", hotkey_text)
            settings.setValue("RESET_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.pause_hotkey_shortcut_line_edit.text(), self.pause_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("PAUSE_HOTKEY_TEXT"):
            settings.setValue("PAUSE_HOTKEY_TEXT", hotkey_text)
            settings.setValue("PAUSE_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.undo_split_hotkey_shortcut_line_edit.text(), self.undo_split_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("UNDO_HOTKEY_TEXT"):
            settings.setValue("UNDO_HOTKEY_TEXT", hotkey_text)
            settings.setValue("UNDO_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.skip_split_hotkey_shortcut_line_edit.text(), self.skip_split_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("SKIP_HOTKEY_TEXT"):
            settings.setValue("SKIP_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SKIP_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.previous_split_hotkey_shortcut_line_edit.text(), self.previous_split_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("PREVIOUS_HOTKEY_TEXT"):
            settings.setValue("PREVIOUS_HOTKEY_TEXT", hotkey_text)
            settings.setValue("PREVIOUS_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.next_split_hotkey_shortcut_line_edit.text(), self.next_split_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("NEXT_HOTKEY_TEXT"):
            settings.setValue("NEXT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("NEXT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        hotkey_text, hotkey_key_sequence = self.screenshot_hotkey_shortcut_line_edit.text(), self.screenshot_hotkey_shortcut_line_edit.key_sequence
        if hotkey_text != settings.value("SCREENSHOT_HOTKEY_TEXT"):
            settings.setValue("SCREENSHOT_HOTKEY_TEXT", hotkey_text)
            settings.setValue("SCREENSHOT_HOTKEY_KEY_SEQUENCE", hotkey_key_sequence)
            hotkey_changed = True

        if hotkey_changed:
            self.set_shortcut_signal.emit()

    def event(self, event):
        if (event.type() == QEvent.MouseButtonPress):
            self.setFocus(True)
            return True

        return QWidget.event(self, event)


class KeyDecoder():
    def __init__(self) -> None:
        self.keys_macos = {
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

    def decode_key(self, key):
        try:
            return self.keys_macos[key]
        except KeyError:
            return ""


class KeyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.key_decoder = parent.key_decoder
        self.key_sequence = QKeySequence()

    def event(self, event):
        if (event.type() == QEvent.KeyPress):
            self.key_sequence = QKeySequence(event.key())
            self.setText(f"{self.key_decoder.decode_key(event.key())}")
            return True

        return QWidget.event(self, event)

    def set_key_sequence(self, key_sequence: QKeySequence):
        self.key_sequence = key_sequence
