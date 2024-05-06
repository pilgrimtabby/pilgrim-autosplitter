from PyQt5.QtCore import QRect, Qt, QSettings
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDoubleSpinBox, QFrame,
                             QKeySequenceEdit, QLabel, QPushButton, QSpinBox)

from utils import convert_css_to_string, settings


class GUISettingsWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("pilgrim_tabby", "Pilgrim Universal Autosplitter")

        # Constants (to facilitate moving things around)
        self.LEFT_EDGE_CORRECTION = 0
        self.TOP_EDGE_CORRECTION = 3
        self.LEFT_EDGE_CORRECTION_FRAME = 0
        self.TOP_EDGE_CORRECTION_FRAME = 0

        # Import style sheets
        self.settings_window_style = convert_css_to_string("res/css/main_window.css")
        self.settings_label_style = convert_css_to_string("res/css/settings_label.css")
        self.helper_frame_style = convert_css_to_string("res/css/helper_frame.css")

        # Settings window settings
        self.setWindowTitle("Settings")
        self.setFixedSize(341, 372)
        self.setStyleSheet(self.settings_window_style)

        # Labels
        self.fps_label = QLabel(self)
        self.fps_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 131, 31))
        self.fps_label.setText("Frames per second:")
        self.fps_label.setToolTip("Read this many frames per second from video source")
        self.fps_label.setStyleSheet(self.settings_label_style)

        self.fps_helper_label = QLabel(self)
        self.fps_helper_label.setGeometry(QRect(240 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 51, 31))
        self.fps_helper_label.setText("FPS")
        self.fps_helper_label.setStyleSheet(self.settings_label_style)

        self.open_screenshots_label = QLabel(self)
        self.open_screenshots_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 141, 31))
        self.open_screenshots_label.setText("Open screenshots:")
        self.open_screenshots_label.setToolTip("When enabled, opens screenshots with the system's default image viewer")
        self.open_screenshots_label.setStyleSheet(self.settings_label_style)

        self.default_threshold_label = QLabel(self)
        self.default_threshold_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.default_threshold_label.setText("Default threshold:")
        self.default_threshold_label.setToolTip("Images must match at least this much to trigger a split, pause, etc.")
        self.default_threshold_label.setStyleSheet(self.settings_label_style)

        self.default_delay_label = QLabel(self)
        self.default_delay_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 201, 31))
        self.default_delay_label.setText("Default delay:")
        self.default_delay_label.setToolTip("The default delay between the split threshold being reached and a split, pause, etc.")
        self.default_delay_label.setStyleSheet(self.settings_label_style)

        self.default_delay_helper_label = QLabel(self)
        self.default_delay_helper_label.setGeometry(QRect(240 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 51, 31))
        self.default_delay_helper_label.setText("seconds")
        self.default_delay_helper_label.setStyleSheet(self.settings_label_style)

        self.default_pause_label = QLabel(self)
        self.default_pause_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.default_pause_label.setText("Default pause:")
        self.default_pause_label.setToolTip("The default waiting period after a split and before starting to compare the next image. Set this setting higher to save CPU")
        self.default_pause_label.setStyleSheet(self.settings_label_style)

        self.default_pause_helper_label = QLabel(self)
        self.default_pause_helper_label.setGeometry(QRect(240 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 51, 31))
        self.default_pause_helper_label.setText("seconds")
        self.default_pause_helper_label.setStyleSheet(self.settings_label_style)

        self.hotkey_settings_label = QLabel(self)
        self.hotkey_settings_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.hotkey_settings_label.setText("Hotkey settings:")
        self.hotkey_settings_label.setStyleSheet(self.settings_label_style)

        self.start_split_hotkey_label = QLabel(self)
        self.start_split_hotkey_label.setGeometry(QRect(50 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.start_split_hotkey_label.setText("Start, split")
        self.start_split_hotkey_label.setStyleSheet(self.settings_label_style)

        self.reset_hotkey_label = QLabel(self)
        self.reset_hotkey_label.setGeometry(QRect(50 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 61, 31))
        self.reset_hotkey_label.setText("Reset")
        self.reset_hotkey_label.setStyleSheet(self.settings_label_style)

        self.pause_hotkey_label = QLabel(self)
        self.pause_hotkey_label.setGeometry(QRect(50 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 61, 31))
        self.pause_hotkey_label.setText("Reset")
        self.pause_hotkey_label.setStyleSheet(self.settings_label_style)

        self.undo_split_hotkey_label = QLabel(self)
        self.undo_split_hotkey_label.setGeometry(QRect(50 + self.LEFT_EDGE_CORRECTION, 180 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.undo_split_hotkey_label.setText("Pause")
        self.undo_split_hotkey_label.setStyleSheet(self.settings_label_style)

        self.skip_split_hotkey_label = QLabel(self)
        self.skip_split_hotkey_label.setGeometry(QRect(50 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.skip_split_hotkey_label.setText("Skip split")
        self.skip_split_hotkey_label.setStyleSheet(self.settings_label_style)

        # Widgets (spinboxes, checkboxes, and sequence edits)
        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(1000)
        self.fps_spinbox.setProperty("value", settings.value("DEFAULT_FPS"))

        self.open_screenshots_checkbox = QCheckBox(self)
        self.open_screenshots_checkbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 41 + self.TOP_EDGE_CORRECTION, 61, 31))
        if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            self.open_screenshots_checkbox.setCheckState(Qt.Checked)
        else:
            self.open_screenshots_checkbox.setCheckState(Qt.Unchecked)

        self.default_threshold_double_spinbox = QDoubleSpinBox(self)
        self.default_threshold_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 68, 31))
        self.default_threshold_double_spinbox.setDecimals(1)
        self.default_threshold_double_spinbox.setMinimum(0.1)
        self.default_threshold_double_spinbox.setMaximum(100)
        self.default_threshold_double_spinbox.setSingleStep(0.1)
        self.default_threshold_double_spinbox.setProperty("value", settings.value("DEFAULT_THRESHOLD"))
        self.default_threshold_double_spinbox.setSuffix("%")

        self.default_delay_double_spinbox = QDoubleSpinBox(self)
        self.default_delay_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 68, 31))
        self.default_delay_double_spinbox.setDecimals(3)
        self.default_delay_double_spinbox.setMinimum(0)
        self.default_delay_double_spinbox.setMaximum(10000000)
        self.default_delay_double_spinbox.setSingleStep(0.1)
        self.default_delay_double_spinbox.setProperty("value", settings.value("DEFAULT_DELAY"))

        self.default_pause_double_spinbox = QDoubleSpinBox(self)
        self.default_pause_double_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 68, 31))
        self.default_pause_double_spinbox.setDecimals(0)
        self.default_pause_double_spinbox.setMinimum(0)
        self.default_pause_double_spinbox.setMaximum(10000000)
        self.default_pause_double_spinbox.setSingleStep(1.0)
        self.default_pause_double_spinbox.setProperty("value", settings.value("DEFAULT_PAUSE"))

        self.start_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.start_split_hotkey_sequence_edit.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.start_split_hotkey_sequence_edit.setKeySequence(settings.value("SPLIT_HOTKEY"))

        self.reset_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.reset_hotkey_sequence_edit.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.reset_hotkey_sequence_edit.setKeySequence(settings.value("RESET_HOTKEY"))

        self.pause_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.pause_hotkey_sequence_edit.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.pause_hotkey_sequence_edit.setKeySequence(settings.value("PAUSE_HOTKEY"))

        self.undo_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.undo_split_hotkey_sequence_edit.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.undo_split_hotkey_sequence_edit.setKeySequence(settings.value("UNDO_HOTKEY"))

        self.skip_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.skip_split_hotkey_sequence_edit.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.skip_split_hotkey_sequence_edit.setKeySequence(settings.value("SKIP_HOTKEY"))

        # Border and buttons
        self.border_helper_frame = QFrame(self)
        self.border_helper_frame.setGeometry(QRect(10 + self.LEFT_EDGE_CORRECTION_FRAME, 10 + self.TOP_EDGE_CORRECTION_FRAME, 322, 351))
        self.border_helper_frame.setFrameShape(QFrame.StyledPanel)
        self.border_helper_frame.setFrameShadow(QFrame.Raised)
        self.border_helper_frame.setStyleSheet(self.helper_frame_style)
        self.border_helper_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setGeometry(QRect(30 + self.LEFT_EDGE_CORRECTION, 315 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.done)

        self.save_button = QPushButton(self)
        self.save_button.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 315 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.save_new_settings)

    def save_new_settings(self):
        fps = self.fps_spinbox.value()
        if fps != settings.value("DEFAULT_FPS"):
            settings.setValue("DEFAULT_FPS", fps)

        open_screenshots_value = self.open_screenshots_checkbox.checkState()
        if open_screenshots_value == 0:
            open_screenshots = False
        else:
            open_screenshots = True
        if open_screenshots != settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", open_screenshots)

        default_threshold = self.default_threshold_double_spinbox.value()
        if default_threshold != settings.value("DEFAULT_THRESHOLD"):
            settings.setValue("DEFAULT_THRESHOLD", default_threshold)

        default_delay = self.default_delay_double_spinbox.value()
        if default_delay != settings.value("DEFAULT_DELAY"):
            settings.setValue("DEFAULT_DELAY", default_delay)

        default_pause = self.default_pause_double_spinbox.value()
        if default_pause != settings.value("DEFAULT_PAUSE"):
            settings.setValue("DEFAULT_PAUSE", default_pause)

        split_hotkey = self.start_split_hotkey_sequence_edit.keySequence()
        if split_hotkey != settings.value("SPLIT_HOTKEY"):
            settings.setValue("SPLIT_HOTKEY", split_hotkey)

        reset_hotkey = self.reset_hotkey_sequence_edit.keySequence()
        if reset_hotkey != settings.value("RESET_HOTKEY"):
            settings.setValue("RESET_HOTKEY", reset_hotkey)

        pause_hotkey = self.pause_hotkey_sequence_edit.keySequence()
        if pause_hotkey != settings.value("PAUSE_HOTKEY"):
            settings.setValue("PAUSE_HOTKEY", pause_hotkey)

        undo_hotkey = self.undo_split_hotkey_sequence_edit.keySequence()
        if undo_hotkey != settings.value("UNDO_HOTKEY"):
            settings.setValue("UNDO_HOTKEY", undo_hotkey)

        skip_hotkey = self.skip_split_hotkey_sequence_edit.keySequence()
        if skip_hotkey != settings.value("SKIP_HOTKEY"):
            settings.setValue("SKIP_HOTKEY", skip_hotkey)
