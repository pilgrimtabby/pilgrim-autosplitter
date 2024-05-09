from PyQt5.QtCore import QRect, Qt, pyqtSignal
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
                             QFrame, QKeySequenceEdit, QLabel, QPushButton,
                             QSpinBox)

from utils import PercentType, settings


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

    def __init__(self, style):
        super().__init__()

        # Constants (to facilitate moving things around)
        self.LEFT_EDGE_CORRECTION = 0
        self.TOP_EDGE_CORRECTION = 3
        self.LEFT_EDGE_CORRECTION_FRAME = 0
        self.TOP_EDGE_CORRECTION_FRAME = 0

        # Settings window settings
        self.setWindowTitle("Settings")
        self.setFixedSize(610, 302)
        self.style = style
        self.style.set_style(self)

        # Border
        self.border_helper_frame = QFrame(self)
        self.border_helper_frame.setGeometry(QRect(10 + self.LEFT_EDGE_CORRECTION_FRAME, 10 + self.TOP_EDGE_CORRECTION_FRAME, 590, 282))
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

        self.capture_source_label = QLabel(self)
        self.capture_source_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 220 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.capture_source_label.setText("Capture source:")
        self.capture_source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.capture_source_label.setToolTip("Coming soon!")

        self.theme_label = QLabel(self)
        self.theme_label.setGeometry(QRect(20 + self.LEFT_EDGE_CORRECTION, 250 + self.TOP_EDGE_CORRECTION, 191, 31))
        self.theme_label.setText("Theme:")
        self.theme_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.theme_label.setToolTip("Does anyone actually use light mode?")

        self.hotkey_settings_label = QLabel(self)
        self.hotkey_settings_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 10 + self.TOP_EDGE_CORRECTION, 216, 31))
        self.hotkey_settings_label.setText("Hotkeys (click + type to change):")
        self.hotkey_settings_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.start_split_hotkey_label = QLabel(self)
        self.start_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.start_split_hotkey_label.setText("Start, split")
        self.start_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.reset_hotkey_label = QLabel(self)
        self.reset_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 61, 31))
        self.reset_hotkey_label.setText("Reset")
        self.reset_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.pause_hotkey_label = QLabel(self)
        self.pause_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 61, 31))
        self.pause_hotkey_label.setText("Reset")
        self.pause_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.undo_split_hotkey_label = QLabel(self)
        self.undo_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 81, 31))
        self.undo_split_hotkey_label.setText("Pause")
        self.undo_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.skip_split_hotkey_label = QLabel(self)
        self.skip_split_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.skip_split_hotkey_label.setText("Skip split")
        self.skip_split_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.screenshot_hotkey_label = QLabel(self)
        self.screenshot_hotkey_label.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 71, 31))
        self.screenshot_hotkey_label.setText("Screenshot")
        self.screenshot_hotkey_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Non-label widgets
        LEFT_SIDE_WIDGET_WIDTH = 70
        LEFT_SIDE_WIDGET_HEIGHT = 27
        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 12 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT))
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(120)
        self.fps_spinbox.setProperty("value", settings.value("FPS"))

        self.open_screenshots_checkbox = QCheckBox(self)
        self.open_screenshots_checkbox.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 42 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH - 7, LEFT_SIDE_WIDGET_HEIGHT + 2))
        if settings.value("OPEN_SCREENSHOT_ON_CAPTURE"):
            self.open_screenshots_checkbox.setCheckState(Qt.Checked)
        else:
            self.open_screenshots_checkbox.setCheckState(Qt.Unchecked)

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
        self.aspect_ratio_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 194 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.aspect_ratio_combo_box.addItems(["4:3", "16:9"])
        self.aspect_ratio_combo_box.setCurrentIndex(-1)
        if settings.value("ASPECT_RATIO") == "4:3":
            self.aspect_ratio_combo_box.setCurrentIndex(0)
        elif settings.value("ASPECT_RATIO") == "16:9":
            self.aspect_ratio_combo_box.setCurrentIndex(1)

        self.capture_source_combo_box = QComboBox(self)
        self.capture_source_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.capture_source_combo_box.setPlaceholderText("N/A")
        self.capture_source_combo_box.setEnabled(False)

        self.theme_combo_box = QComboBox(self)
        self.theme_combo_box.setGeometry(QRect(160 + self.LEFT_EDGE_CORRECTION, 254 + self.TOP_EDGE_CORRECTION, LEFT_SIDE_WIDGET_WIDTH, LEFT_SIDE_WIDGET_HEIGHT - 4))
        self.theme_combo_box.addItems(["dark", "light", "system"])
        self.theme_combo_box.setCurrentIndex(-1)
        if settings.value("THEME") == "dark":
            self.theme_combo_box.setCurrentIndex(0)
        elif settings.value("THEME") == "light":
            self.theme_combo_box.setCurrentIndex(1)
        elif settings.value("THEME") == "system":
            self.theme_combo_box.setCurrentIndex(2)

        self.start_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.start_split_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 40 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.start_split_hotkey_sequence_edit.setKeySequence(settings.value("SPLIT_HOTKEY"))

        self.reset_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.reset_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 70 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.reset_hotkey_sequence_edit.setKeySequence(settings.value("RESET_HOTKEY"))

        self.pause_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.pause_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 100 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.pause_hotkey_sequence_edit.setKeySequence(settings.value("PAUSE_HOTKEY"))

        self.undo_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.undo_split_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 130 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.undo_split_hotkey_sequence_edit.setKeySequence(settings.value("UNDO_HOTKEY"))

        self.skip_split_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.skip_split_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 160 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.skip_split_hotkey_sequence_edit.setKeySequence(settings.value("SKIP_HOTKEY"))

        self.screenshot_hotkey_sequence_edit = QKeySequenceEdit(self)
        self.screenshot_hotkey_sequence_edit.setGeometry(QRect(410 + self.LEFT_EDGE_CORRECTION, 190 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.screenshot_hotkey_sequence_edit.setKeySequence(settings.value("SCREENSHOT_HOTKEY"))

        # Buttons
        self.start_split_hotkey_sequence_edit_button = QPushButton(self)
        self.start_split_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 46 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.start_split_hotkey_sequence_edit_button.setText("clear")
        self.start_split_hotkey_sequence_edit_button.clicked.connect(self.start_split_hotkey_sequence_edit.clear)
        self.start_split_hotkey_sequence_edit_button.setObjectName("clear_button")

        self.reset_hotkey_sequence_edit_button = QPushButton(self)
        self.reset_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 76 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.reset_hotkey_sequence_edit_button.setText("clear")
        self.reset_hotkey_sequence_edit_button.clicked.connect(self.reset_hotkey_sequence_edit.clear)
        self.reset_hotkey_sequence_edit_button.setObjectName("clear_button")

        self.pause_hotkey_sequence_edit_button = QPushButton(self)
        self.pause_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 106 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.pause_hotkey_sequence_edit_button.setText("clear")
        self.pause_hotkey_sequence_edit_button.clicked.connect(self.pause_hotkey_sequence_edit.clear)
        self.pause_hotkey_sequence_edit_button.setObjectName("clear_button")

        self.undo_split_hotkey_sequence_edit_button = QPushButton(self)
        self.undo_split_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 136 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.undo_split_hotkey_sequence_edit_button.setText("clear")
        self.undo_split_hotkey_sequence_edit_button.clicked.connect(self.undo_split_hotkey_sequence_edit.clear)
        self.undo_split_hotkey_sequence_edit_button.setObjectName("clear_button")

        self.skip_split_hotkey_sequence_edit_button = QPushButton(self)
        self.skip_split_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 166 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.skip_split_hotkey_sequence_edit_button.setText("clear")
        self.skip_split_hotkey_sequence_edit_button.clicked.connect(self.skip_split_hotkey_sequence_edit.clear)
        self.skip_split_hotkey_sequence_edit_button.setObjectName("clear_button")
        
        self.screenshot_hotkey_sequence_edit_button = QPushButton(self)
        self.screenshot_hotkey_sequence_edit_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 196 + self.TOP_EDGE_CORRECTION, 39, 20))
        self.screenshot_hotkey_sequence_edit_button.setText("clear")
        self.screenshot_hotkey_sequence_edit_button.clicked.connect(self.screenshot_hotkey_sequence_edit.clear)
        self.screenshot_hotkey_sequence_edit_button.setObjectName("clear_button")

        self.cancel_button = QPushButton(self)
        self.cancel_button.setGeometry(QRect(319 + self.LEFT_EDGE_CORRECTION, 236 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.done)
        self.cancel_button.setObjectName("cancel_button")

        self.save_button = QPushButton(self)
        self.save_button.setGeometry(QRect(459 + self.LEFT_EDGE_CORRECTION, 236 + self.TOP_EDGE_CORRECTION, 111, 31))
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.save_new_settings)
        self.save_button.clicked.connect(self.done)
        self.save_button.setObjectName("save_button")

    def save_new_settings(self):
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
            if aspect_ratio == "4:3":
                settings.setValue("ASPECT_RATIO", "4:3")
                settings.setValue("FRAME_WIDTH", 480)
                settings.setValue("FRAME_HEIGHT", 360)
            else:
                settings.setValue("ASPECT_RATIO", "16:9")
                settings.setValue("FRAME_WIDTH", 512)
                settings.setValue("FRAME_HEIGHT", 288)
            self.update_aspect_ratio_finish_signal.emit()

        capture_source = self.capture_source_combo_box.currentText()
        if capture_source != settings.value("CAPTURE_SOURCE"):
            settings.setValue("CAPTURE_SOURCE", capture_source)

        theme = self.theme_combo_box.currentText()
        if theme != settings.value("THEME"):
            if theme == "dark":
                settings.setValue("THEME", "dark")
            elif theme == "light":
                settings.setValue("THEME", "light")
            else:  #system
                settings.setValue("THEME", "system")

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

        screenshot_hotkey = self.screenshot_hotkey_sequence_edit.keySequence()
        if screenshot_hotkey != settings.value("SCREENSHOT_HOTKEY"):
            settings.setValue("SCREENSHOT_HOTKEY", screenshot_hotkey)

    def get_camera_indexes(self):
        pass
        # if platform.system == "Windows":
        #     from pygrabber.dshow_graph import FilterGraph
        #     index_list, name_list = [], []
        #     cameras = FilterGraph().get_input_devices()

        #     # this is definitely broken
        #     count = 0
        #     while count < len(cameras):
        #         index_list[count] = cameras[count]
        #         name_list[count] = cameras[count]

        #     return index_list, name_list
        
        # else:
        # open_ports = []
        # unopen_ports = []
        # port = 0

        # while len(unopen_ports) < 3:
        #     test_cam = cv2.VideoCapture(port)
        #     if test_cam.isOpened():
        #         open_ports.append(port)
        #     else:
        #         unopen_ports.append(port)
        #     port += 1
    
        # return open_ports
