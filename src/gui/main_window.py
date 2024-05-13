import time
import webbrowser

from PyQt5.QtCore import QRect, Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAction, QLabel, QLineEdit, QMainWindow, QMenuBar,
                             QMessageBox, QPushButton, QShortcut, QWidget)

from utils import settings

# transparency: https://stackoverflow.com/questions/7928519/how-to-make-the-qlabel-background-semi-transparent

class GUIMainWindow(QMainWindow):
    set_pause_comparison_button_status_signal = pyqtSignal()
    update_video_feed_label_signal = pyqtSignal()
    reset_shortcut_signal = pyqtSignal()
    undo_split_shortcut_signal = pyqtSignal()
    skip_split_shortcut_signal = pyqtSignal()
    screenshot_shortcut_signal = pyqtSignal()

    def __init__(self, style):
        super().__init__()

        # Set title and window structure
        self.setWindowTitle(f"Pilgrim Autosplitter v{settings.value('VERSION_NUMBER')}")
        self.main_window = QWidget(self)
        self.main_window.setFocusPolicy(Qt.StrongFocus)
        self.setCentralWidget(self.main_window)
        self.set_keyboard_shortcuts()
        self.style = style
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)
        
        # Layout variables
        self.current_split_name = None
        self.current_image_dir_path = None
        self.delay_duration_timer = QTimer()
        self.pause_duration_timer = QTimer()

        self.LEFT_EDGE_CORRECTION = -44
        self.TOP_EDGE_CORRECTION = -215

        self.default_similarity_label_text = "Similarity to split image:"
        self.default_highest_similarity_label_text = "Highest similarity so far:"
        self.default_threshold_similarity_label_text = "Threshold similarity:"
        self.default_pause_comparison_button_text = "Pause comparison"
        self.default_unpause_comparison_button_text = "Unpause comparison"
        self.default_undo_split_button_text = "Undo split"
        self.default_skip_split_button_text = "Skip split"
        self.default_reset_splits_button_text = "Reset run"

        self.small_similarity_label_text = "Sim:"
        self.small_highest_similarity_label_text = "High:"
        self.small_threshold_similarity_label_text = "Thr:"
        self.small_pause_comparison_button_text = "Pause comp"
        self.small_unpause_comparison_button_text = "Unpause comp"
        self.small_undo_split_button_text = "Undo"
        self.small_skip_split_button_text = "Skip"
        self.small_reset_splits_button_text = "Reset"

        # Split image line edit
        self.image_directory_line_edit = QLineEdit(self.main_window)
        self.image_directory_line_edit.setText(" Nothing selected yet")
        self.image_directory_line_edit.setEnabled(False)

        # Text labels
        self.video_feed_label = QLabel(self.main_window)
        self.video_feed_label.setText("")
        self.video_feed_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.video_feed_label.setAlignment(Qt.AlignCenter)

        self.split_name_label = QLabel(self.main_window)
        self.split_name_label.setText("")
        self.split_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.current_loop_label = QLabel(self.main_window)
        self.current_loop_label.setText("")
        self.current_loop_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_loop_label.setAlignment(Qt.AlignCenter)

        self.similarity_label = QLabel(self.main_window)
        self.similarity_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_similarity_label = QLabel(self.main_window)
        self.threshold_similarity_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_similarity_label = QLabel(self.main_window)
        self.highest_similarity_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent = QLabel(self.main_window)
        self.current_match_percent.setText(self.get_match_percent_null_value())
        self.current_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent = QLabel(self.main_window)
        self.highest_match_percent.setText(self.get_match_percent_null_value())
        self.highest_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent = QLabel(self.main_window)
        self.threshold_match_percent.setText(self.get_match_percent_null_value())
        self.threshold_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.similarity_percent_sign = QLabel(self.main_window)
        self.similarity_percent_sign.setText("%")
        self.similarity_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.similarity_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.highest_percent_sign = QLabel(self.main_window)
        self.highest_percent_sign.setText("%")
        self.highest_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.threshold_percent_sign = QLabel(self.main_window)
        self.threshold_percent_sign.setText("%")
        self.threshold_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Video feed and split image
        self.video_feed = QLabel(self.main_window)
        self.video_feed_blank_text = "No video feed detected"
        self.video_feed.setText(self.video_feed_blank_text)
        self.video_feed.setAlignment(Qt.AlignCenter)
        self.video_feed.setObjectName("image_label_inactive")

        self.split_image = QLabel(self.main_window)
        self.split_image_blank_text = "No split images loaded"
        self.split_image.setText(self.split_image_blank_text)
        self.split_image.setAlignment(Qt.AlignCenter)
        self.split_image.setObjectName("image_label_inactive")

        self.split_image_overlay = QLabel(self.main_window)
        self.split_image_overlay.setObjectName("split_image_overlay")
        self.split_image_overlay.setVisible(False)
        self.split_image_overlay.setAlignment(Qt.AlignCenter)

        # Buttons
        self.image_directory_button = QPushButton(self.main_window)
        self.image_directory_button.setText("Select split image folder:")

        self.minimal_view_button = QPushButton(self.main_window)
        self.minimal_view_button_default_text = "Minimal view"
        self.minimal_view_button_minimal_text = "Full view"
        self.minimal_view_button.clicked.connect(self.set_minimal_view_status)
        self.minimal_view_button.clicked.connect(self.set_layout)

        self.next_source_button = QPushButton(self.main_window)
        self.next_source_button.setText("Next source")

        self.screenshot_button = QPushButton(self.main_window)
        self.screenshot_button.setText("Take screenshot")
        self.screenshot_button.setEnabled(False)

        self.reload_video_button = QPushButton(self.main_window)
        self.reload_video_button.setText("Reconnect video")

        self.previous_split_button = QPushButton(self.main_window)
        self.previous_split_button.setText("<")
        self.previous_split_button.setEnabled(False)

        self.next_split_button = QPushButton(self.main_window)
        self.next_split_button.setText(">")
        self.next_split_button.setEnabled(False)

        self.pause_comparison_button = QPushButton(self.main_window)
        self.pause_comparison_button.setEnabled(False)
        self.pause_comparison_button.clicked.connect(self.pause_duration_timer.stop)
        self.pause_comparison_button.clicked.connect(lambda: self.split_image_overlay.setVisible(False))

        self.skip_split_button = QPushButton(self.main_window)
        self.skip_split_button.setText("Skip split")
        self.skip_split_button.setEnabled(False)

        self.undo_split_button = QPushButton(self.main_window)
        self.undo_split_button.setText("Undo split")
        self.undo_split_button.setEnabled(False)

        self.reset_splits_button = QPushButton(self.main_window)
        self.reset_splits_button.setText("Reset run")
        self.reset_splits_button.setEnabled(False)

        # Menu bar
        self.menu_bar = QMenuBar(self.main_window)

        self.settings_window_action = QAction("&Open Settings Menu", self)
        self.settings_window_action.setShortcut("Ctrl+.")

        self.about_window_action = QAction("&Help", self)
        self.about_window_action.setShortcut("Ctrl+shift+H")
        self.about_window_action.triggered.connect(lambda: webbrowser.open("https://github.com/pilgrimtabby/image-capture/", new=0, autoraise=True))

        self.file_menu = self.menu_bar.addMenu("&Pilgrim Autosplitter")
        self.file_menu.addAction(self.settings_window_action)
        self.file_menu.addAction(self.about_window_action)

        self.setMenuBar(self.menu_bar)

        # Style and layout
        self.style.set_style(self.main_window)
        self.set_layout(on_init=True)

    # Set button status
    def set_image_directory_button_status(self, status):
        self.image_directory_button.setEnabled(status)

    def set_screenshot_button_status(self, status):
        self.screenshot_button.setEnabled(status)

    def set_minimal_view_button_status(self, status):
        self.minimal_view_button.setEnabled(status)

    def set_minimal_view_status(self):
        if settings.value("SHOW_MIN_VIEW"):
            settings.setValue("SHOW_MIN_VIEW", False)
        else:
            settings.setValue("SHOW_MIN_VIEW", True)
    
    def set_minimal_view_button_text(self):
        if settings.value("SHOW_MIN_VIEW"):
            self.minimal_view_button.setText(self.minimal_view_button_minimal_text)
        else:
            self.minimal_view_button.setText(self.minimal_view_button_default_text)

    def set_next_source_button_status(self, status):
        self.next_source_button.setEnabled(status)

    def set_reload_video_button_status(self, status):
        self.reload_video_button.setEnabled(status)

    def set_previous_split_button_status(self, status):
        self.previous_split_button.setEnabled(status)

    def set_next_split_button_status(self, status):
        self.next_split_button.setEnabled(status)

    def set_pause_comparison_button_status(self, status):
        self.pause_comparison_button.setEnabled(status)

    def set_pause_comparison_button_text_to_pause(self):
        if settings.value("SHOW_MIN_VIEW") or settings.value("ASPECT_RATIO") == "4:3 (320x240)":
            self.pause_comparison_button.setText(self.small_pause_comparison_button_text)
        else:
            self.pause_comparison_button.setText(self.default_pause_comparison_button_text)

    def set_pause_comparison_button_text_to_unpause(self):
        if settings.value("SHOW_MIN_VIEW") or settings.value("ASPECT_RATIO") == "4:3 (320x240)":
            self.pause_comparison_button.setText(self.small_unpause_comparison_button_text)
        else:
            self.pause_comparison_button.setText(self.default_unpause_comparison_button_text)

    def set_skip_split_button_status(self, status):
        self.skip_split_button.setEnabled(status)

    def set_undo_split_button_status(self, status):
        self.undo_split_button.setEnabled(status)

    def set_reset_splits_button_status(self, status):
        self.reset_splits_button.setEnabled(status)

    # Set label status
    def set_image_directory_line_edit(self, path: str | None):
        if path is not None:
            self.current_image_dir_path = path
            elided_path = self.image_directory_line_edit.fontMetrics().elidedText(f" {path}", Qt.ElideMiddle, self.image_directory_line_edit.width())
            self.image_directory_line_edit.setText(elided_path)
            self.style.set_style(self.main_window)

    def set_blank_video_frame(self):
        if self.video_feed.text() == "":  # There is a pixmap overriding the text
            self.video_feed.setText(self.video_feed_blank_text)
            self.video_feed.setObjectName("image_label_inactive")
            self.style.set_style(self.main_window)

    def set_live_video_frame(self, frame: QPixmap):
        video_feed_text = self.video_feed.text() # Check if there is an image (i.e. if there is no text)
        self.video_feed.setPixmap(frame)
        if video_feed_text != "":  # There was text, therefore no image
            self.video_feed.setObjectName("image_label_active")
            self.style.set_style(self.main_window)

    def set_video_feed_label(self, video_is_active: bool):
        if settings.value("SHOW_MIN_VIEW"):
            if video_is_active:
                self.video_feed_label.setText("Video status:   healthy")
            else:
                self.video_feed_label.setText("Video status:   down")
        else:
            if video_is_active:
                self.video_feed_label.setText("Video feed")
            else:
                self.video_feed_label.setText("")

    def set_blank_split_image(self):
        if self.split_image.text() == "":  # There is a pixmap overriding the text
            self.split_image.setText(self.split_image_blank_text)
            self.split_image.setObjectName("image_label_inactive")
            self.style.set_style(self.main_window)

    def set_live_split_image(self, frame: QPixmap):
        split_image_text = self.split_image.text() # Check if there is text (i.e. if there is no image)
        self.split_image.setPixmap(frame)
        if split_image_text != "":  # There is text, so there is no image
            self.split_image.setObjectName("image_label_active")
            self.style.set_style(self.main_window)

    def set_blank_split_name_label(self):
        self.split_name_label.setText("")

    def set_live_split_name_label(self, name: str):
        if name is not None:
            self.current_split_name = name
            elided_name = self.split_name_label.fontMetrics().elidedText(name, Qt.ElideMiddle, self.split_name_label.width())
            self.split_name_label.setText(elided_name)

    def set_blank_loop_label(self):
        self.current_loop_label.setText("")

    def set_no_loop_loop_label(self):
        self.current_loop_label.setText("Split does not loop")

    def set_live_loop_label_text(self, current: int, total: int):
        self.current_loop_label.setText(f"Loop {current} of {total}")

    def set_current_match_percent(self, match_percent: str | None):
        if match_percent is None:
            self.current_match_percent.setText(self.get_match_percent_null_value())
        else:
            self.current_match_percent.setText(match_percent)

    def set_highest_match_percent(self, match_percent: str | None):
        if match_percent is None:
            self.highest_match_percent.setText(self.get_match_percent_null_value())
        else:
            self.highest_match_percent.setText(match_percent)

    def set_threshold_match_percent(self, match_percent: str | None):
        if match_percent is None:
            self.threshold_match_percent.setText(self.get_match_percent_null_value())
        else:
            self.threshold_match_percent.setText(match_percent)

    def set_split_image_overlay_status(self, status, delay_duration: float, pause_duration: float):
        if status and (delay_duration > 0 or pause_duration > 0):
            self.split_image_overlay.setVisible(True)
            if delay_duration > 0:
                if pause_duration > 0:
                    self.hide_overlay_at_end = False
                    self.set_delay_timer(delay_duration)
                else:
                    self.hide_overlay_at_end = True
                    self.set_delay_timer(delay_duration)
            if pause_duration > 0:
                QTimer.singleShot(int(1000 * delay_duration), lambda: self.set_pause_timer(pause_duration))

    def set_delay_timer(self, delay_duration: float):
        self.delay_duration = delay_duration
        self.delay_duration_timer = QTimer()
        self.delay_duration_timer.setInterval(50)
        self.delay_duration_timer.timeout.connect(self.print_delay)
        self.start_time = time.perf_counter()
        self.delay_duration_timer.start()

    def set_pause_timer(self, pause_duration: float):
        self.pause_duration = pause_duration
        self.pause_duration_timer = QTimer()
        self.pause_duration_timer.setInterval(50)
        self.pause_duration_timer.timeout.connect(self.print_pause)
        self.start_time = time.perf_counter()
        self.delay_duration_timer.stop()
        self.pause_duration_timer.start()

    def print_delay(self):
        time_elapsed = time.perf_counter() - self.start_time
        if time_elapsed >= self.delay_duration:
            self.delay_duration_timer.stop()
            self.split_image_overlay.setText("")
            if self.hide_overlay_at_end:
                self.split_image_overlay.setVisible(False)
        else:
            self.split_image_overlay.setText(f"Splitting in {(self.delay_duration - time_elapsed):.1f} seconds")

    def print_pause(self):
        time_elapsed = time.perf_counter() - self.start_time
        if time_elapsed >= self.pause_duration:
            self.pause_duration_timer.stop()
            self.split_image_overlay.setText("")
            self.split_image_overlay.setVisible(False)
        else:
            self.split_image_overlay.setText(f"Paused for {(self.pause_duration - time_elapsed):.1f} seconds")

    def get_match_percent_null_value(self):
        null_value = "--"
        decimals = settings.value("MATCH_PERCENT_DECIMALS")
        if decimals > 0:
            null_value += "."
            while decimals > 0:
                null_value += "-"
                decimals -= 1
        return null_value

    # Dialogs
    def screenshot_success_message(self, path: str):
        message = QMessageBox()
        message.setText("Screenshot taken")
        message.setInformativeText(f"Screenshot saved to:\n{path}")
        message.setIconPixmap(QPixmap(path).scaledToWidth(150))
        message.exec()

    def screenshot_error_message(self):
        message = QMessageBox()
        message.setText("Could not take screenshot")
        message.setInformativeText("No video feed detected. Please make sure video feed is active and try again.")
        message.setIcon(QMessageBox.Warning)
        message.exec()

    # Keyboard shortcuts
    def set_keyboard_shortcuts(self):
        pass
        # self.reset_shortcut = QShortcut(settings.value("RESET_HOTKEY"), self)
        # self.undo_split_shortcut = QShortcut(settings.value("UNDO_HOTKEY"), self)
        # self.skip_split_shortcut = QShortcut(settings.value("SKIP_HOTKEY"), self)
        # self.screenshot_shortcut = QShortcut(settings.value("SCREENSHOT_HOTKEY"), self)

        # self.reset_shortcut.activated.connect(self.reset_shortcut_signal.emit)
        # self.undo_split_shortcut.activated.connect(self.undo_split_shortcut_signal.emit)
        # self.skip_split_shortcut.activated.connect(self.skip_split_shortcut_signal.emit)
        # self.screenshot_shortcut.activated.connect(self.screenshot_shortcut_signal.emit)

    # Set layout
    def set_layout(self, on_init=False):
        self.update_video_feed_label_signal.emit()
        self.set_minimal_view_button_text()
        if settings.value("SHOW_MIN_VIEW"):
            self.set_minimal_view()

        else:
            aspect_ratio = settings.value("ASPECT_RATIO")
            if aspect_ratio == "4:3 (480x360)":
                self.set_480x360()
                if on_init:
                    self.pause_comparison_button.setText(self.default_pause_comparison_button_text)

            elif aspect_ratio == "4:3 (320x240)":
                self.set_320x240()
                if on_init:
                    self.pause_comparison_button.setText(self.small_pause_comparison_button_text)

            elif aspect_ratio == "16:9 (512x288)":
                self.set_512x288()
                if on_init:
                    self.pause_comparison_button.setText(self.default_pause_comparison_button_text)

            elif aspect_ratio == "16:9 (432x243)":
                self.set_432x243()
                if on_init:
                    self.pause_comparison_button.setText(self.default_pause_comparison_button_text)
        
        self.set_live_split_name_label(self.current_split_name)
        self.set_image_directory_line_edit(self.current_image_dir_path)

    def set_minimal_view(self):
        self.set_nonessential_widgets_visible(False)
        self.set_widget_text_small()
        self.setFixedSize(345, 179)

        self.previous_split_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.split_name_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 214 + self.TOP_EDGE_CORRECTION, 251, 31))
        self.current_loop_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 239 + self.TOP_EDGE_CORRECTION, 251, 31))
        self.next_split_button.setGeometry(QRect(344 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.video_feed_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 213, 31))
        self.pause_comparison_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.skip_split_button.setGeometry(QRect(125 + self.LEFT_EDGE_CORRECTION, 350 + self.TOP_EDGE_CORRECTION, 56, 31))
        self.undo_split_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 350 + self.TOP_EDGE_CORRECTION, 56, 31))
        self.reset_splits_button.setGeometry(QRect(304 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 71, 71))
        self.similarity_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.similarity_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 21, 31))

    def set_480x360(self):
        self.set_nonessential_widgets_visible(True)
        self.set_widget_text_default()
        self.setFixedSize(1002, 570)
        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 785, 30))
        self.video_feed_label.setGeometry(QRect(260 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(584 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 415, 31))
        self.current_loop_label.setGeometry(QRect(584 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 415, 31))
        self.similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.similarity_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.image_directory_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 180, 30))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.next_source_button.setGeometry(QRect(440 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.screenshot_button.setGeometry(QRect(340 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.reload_video_button.setGeometry(QRect(340 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.previous_split_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.next_split_button.setGeometry(QRect(1000 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.pause_comparison_button.setGeometry(QRect(580 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 191, 41))
        self.skip_split_button.setGeometry(QRect(680 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.undo_split_button.setGeometry(QRect(580 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.reset_splits_button.setGeometry(QRect(810 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 191, 91))
        self.video_feed.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360))
        split_image_geometry = QRect(550 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360)
        self.split_image.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def set_320x240(self):  # -160, -120
        self.set_nonessential_widgets_visible(True)
        self.set_widget_text_small()
        self.setFixedSize(682, 450)
        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 464, 30))
        self.video_feed_label.setGeometry(QRect(180 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(424 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 254, 31))
        self.current_loop_label.setGeometry(QRect(424 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 254, 31))
        self.similarity_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.similarity_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.image_directory_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 180, 30))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.next_source_button.setGeometry(QRect(280 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.screenshot_button.setGeometry(QRect(220 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 131, 41))
        self.reload_video_button.setGeometry(QRect(220 + self.LEFT_EDGE_CORRECTION, 610 + self.TOP_EDGE_CORRECTION, 131, 41))
        self.previous_split_button.setGeometry(QRect(390 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.next_split_button.setGeometry(QRect(680 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.pause_comparison_button.setGeometry(QRect(420 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 121, 41))
        self.skip_split_button.setGeometry(QRect(485 + self.LEFT_EDGE_CORRECTION, 610 + self.TOP_EDGE_CORRECTION, 56, 41))
        self.undo_split_button.setGeometry(QRect(420 + self.LEFT_EDGE_CORRECTION, 610 + self.TOP_EDGE_CORRECTION, 56, 41))
        self.reset_splits_button.setGeometry(QRect(560 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 121, 91))
        self.video_feed.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 320, 240))
        split_image_geometry = QRect(390 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 320, 240)
        self.split_image.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def set_512x288(self):
        self.set_nonessential_widgets_visible(True)
        self.set_widget_text_default()
        self.setFixedSize(1064, 497)
        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 848, 30))
        self.video_feed_label.setGeometry(QRect(276 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(613 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 450, 31))
        self.current_loop_label.setGeometry(QRect(613 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 450, 31))
        self.similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.similarity_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.image_directory_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 180, 30))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.next_source_button.setGeometry(QRect(472 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.screenshot_button.setGeometry(QRect(372 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.reload_video_button.setGeometry(QRect(372 + self.LEFT_EDGE_CORRECTION, 658 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.previous_split_button.setGeometry(QRect(582 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.next_split_button.setGeometry(QRect(1064 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.pause_comparison_button.setGeometry(QRect(612 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 191, 41))
        self.skip_split_button.setGeometry(QRect(712 + self.LEFT_EDGE_CORRECTION, 658 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.undo_split_button.setGeometry(QRect(612 + self.LEFT_EDGE_CORRECTION, 658 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.reset_splits_button.setGeometry(QRect(874 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 191, 91))
        self.video_feed.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 512, 288))
        split_image_geometry = QRect(582 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 512, 288)
        self.split_image.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def set_432x243(self):  # -80, -45
        self.set_nonessential_widgets_visible(True)
        self.set_widget_text_default()
        self.setFixedSize(904, 452)

        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 688, 30))
        self.video_feed_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 231, 31))
        self.split_name_label.setGeometry(QRect(534 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 371, 31))
        self.current_loop_label.setGeometry(QRect(534 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 371, 31))
        self.similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.similarity_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.image_directory_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 180, 30))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.next_source_button.setGeometry(QRect(392 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.screenshot_button.setGeometry(QRect(332 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 131, 41))
        self.reload_video_button.setGeometry(QRect(332 + self.LEFT_EDGE_CORRECTION, 613 + self.TOP_EDGE_CORRECTION, 131, 41))
        self.previous_split_button.setGeometry(QRect(502 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.next_split_button.setGeometry(QRect(904 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.pause_comparison_button.setGeometry(QRect(532 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 181, 41))
        self.skip_split_button.setGeometry(QRect(627 + self.LEFT_EDGE_CORRECTION, 613 + self.TOP_EDGE_CORRECTION, 86, 41))
        self.undo_split_button.setGeometry(QRect(532 + self.LEFT_EDGE_CORRECTION, 613 + self.TOP_EDGE_CORRECTION, 86, 41))
        self.reset_splits_button.setGeometry(QRect(724 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 181, 91))
        self.video_feed.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 432, 243))
        split_image_geometry = QRect(502 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 432, 243)
        self.split_image.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def set_nonessential_widgets_visible(self, visible):
        self.image_directory_line_edit.setVisible(visible)
        self.image_directory_button.setVisible(visible)
        self.next_source_button.setVisible(visible)
        self.screenshot_button.setVisible(visible)
        self.reload_video_button.setVisible(visible)
        self.video_feed.setVisible(visible)
        self.split_image.setVisible(visible)

    def set_widget_text_small(self):
        self.similarity_label.setText(self.small_similarity_label_text)
        self.highest_similarity_label.setText(self.small_highest_similarity_label_text)
        self.threshold_similarity_label.setText(self.small_threshold_similarity_label_text)
        if self.pause_comparison_button.text() == self.default_pause_comparison_button_text or self.pause_comparison_button.text() == self.small_pause_comparison_button_text:
            self.pause_comparison_button.setText(self.small_pause_comparison_button_text)
        else:
            self.pause_comparison_button.setText(self.small_unpause_comparison_button_text)
        self.undo_split_button.setText(self.small_undo_split_button_text)
        self.skip_split_button.setText(self.small_skip_split_button_text)
        self.reset_splits_button.setText(self.small_reset_splits_button_text)

    def set_widget_text_default(self):
        self.similarity_label.setText(self.default_similarity_label_text)
        self.highest_similarity_label.setText(self.default_highest_similarity_label_text)
        self.threshold_similarity_label.setText(self.default_threshold_similarity_label_text)
        if self.pause_comparison_button.text() == self.default_pause_comparison_button_text or self.pause_comparison_button.text() == self.small_pause_comparison_button_text:
            self.pause_comparison_button.setText(self.default_pause_comparison_button_text)
        else:
            self.pause_comparison_button.setText(self.default_unpause_comparison_button_text)
        self.undo_split_button.setText(self.default_undo_split_button_text)
        self.skip_split_button.setText(self.default_skip_split_button_text)
        self.reset_splits_button.setText(self.default_reset_splits_button_text)

    # Use this to create a widget that will read a single key press, save it as a shortcut
    # Use a dict to translate to applescript on mac, wincom32 or something on windows
    # def event(self, event):
    #     if (event.type() == QEvent.KeyPress):
    #         print(f'{event.key()}: "{event.text()}",')
    #         return True
    #     return QWidget.event(self, event)
