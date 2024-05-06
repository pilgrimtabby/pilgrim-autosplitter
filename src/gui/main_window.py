
from PyQt5.QtCore import QRect, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAction, QLabel, QLineEdit, QMainWindow, QMenuBar,
                             QPushButton, QWidget, QMessageBox)

from utils import VERSION_NUMBER, convert_css_to_string
from utils import PercentType, MATCH_PERCENT_DECIMALS

class GUIMainWindow(QMainWindow):
    pause_comparison_signal = pyqtSignal()
    unpause_comparison_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()

        # Constants (to facilitate moving things around)
        self.LEFT_EDGE_CORRECTION = -35
        self.TOP_EDGE_CORRECTION = -215

        # Import style sheets
        self.main_window_style = convert_css_to_string("res/css/main_window.css")
        self.line_edit_style = convert_css_to_string("res/css/line_edit.css")
        self.image_style = convert_css_to_string("res/css/image.css")
        self.loaded_split_image_style = convert_css_to_string("res/css/loaded_split_image.css")
        self.button_style = convert_css_to_string("res/css/button.css")

        # Main window
        self.setWindowTitle(f"Pilgrim Universal Autosplitter v{VERSION_NUMBER}")
        self.setFixedSize(1020, 570)
        self.main_window = QWidget(self)
        self.main_window.setStyleSheet(self.main_window_style)
        self.setCentralWidget(self.main_window)

        # Split image directory box  # self.file_dialog = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.image_directory_line_edit = QLineEdit(self.main_window)
        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 785, self.image_directory_line_edit.height()))
        self.image_directory_line_edit.setText(" Nothing selected yet")
        self.image_directory_line_edit.setEnabled(False)
        self.image_directory_line_edit.setStyleSheet(self.line_edit_style)

        # Video feed and split image
        self.video_feed = QLabel(self.main_window)
        self.video_feed.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360))
        self.video_feed.setText("No video feed detected")
        self.video_feed.setStyleSheet(self.image_style)
        self.video_feed.setAlignment(Qt.AlignCenter)

        self.split_image = QLabel(self.main_window)
        self.split_image.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360))
        self.split_image.setText("No split images loaded")
        self.split_image.setStyleSheet(self.image_style)
        self.split_image.setAlignment(Qt.AlignCenter)

        # Text labels
        self.video_feed_label = QLabel(self.main_window)
        self.video_feed_label.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 480, 31))
        self.video_feed_label.setText("")
        self.video_feed_label.setAlignment(Qt.AlignCenter)

        self.video_capture_method_label = QLabel(self.main_window)
        self.video_capture_method_label.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 480, 31))
        self.video_capture_method_label.setText("")
        self.video_capture_method_label.setAlignment(Qt.AlignCenter)

        self.split_name_label = QLabel(self.main_window)
        self.split_name_label.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 480, 31))
        self.split_name_label.setText("")
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.current_loop_label = QLabel(self.main_window)
        self.current_loop_label.setGeometry(QRect(590 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 401, 31))
        self.current_loop_label.setText("")
        self.current_loop_label.setAlignment(Qt.AlignCenter)

        self.similarity_label = QLabel(self.main_window)
        self.similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.similarity_label.setText("Similarity to split image:")
        self.similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_similarity_label = QLabel(self.main_window)
        self.highest_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_similarity_label.setText("Highest similarity so far:")
        self.highest_similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_similarity_label = QLabel(self.main_window)
        self.threshold_similarity_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_similarity_label.setText("Threshold similarity:")
        self.threshold_similarity_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent = QLabel(self.main_window)
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent.setText("--.-")
        self.current_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent = QLabel(self.main_window)
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setText("--.-")
        self.highest_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent = QLabel(self.main_window)
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setText("--.-")
        self.threshold_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.similarity_percent_sign = QLabel(self.main_window)
        self.similarity_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.similarity_percent_sign.setText("%")
        self.similarity_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.highest_percent_sign = QLabel(self.main_window)
        self.highest_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_percent_sign.setText("%")
        self.highest_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.threshold_percent_sign = QLabel(self.main_window)
        self.threshold_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_percent_sign.setText("%")
        self.threshold_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Buttons
        self.image_directory_button = QPushButton(self.main_window)
        self.image_directory_button.setText("Select split image folder:")
        self.image_directory_button.setGeometry(QRect(55 + self.LEFT_EDGE_CORRECTION, 222 + self.TOP_EDGE_CORRECTION, 190, 35))

        self.screenshot_button = QPushButton(self.main_window)
        self.screenshot_button.setGeometry(QRect(340 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.screenshot_button.setText("Take screenshot")
        self.screenshot_button.setEnabled(False)
        self.screenshot_button.setStyleSheet(self.button_style)

        self.reload_video_button = QPushButton(self.main_window)
        self.reload_video_button.setGeometry(QRect(340 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 171, 41))
        self.reload_video_button.setText("Reconnect video")
        self.reload_video_button.setEnabled(True)
        self.reload_video_button.setStyleSheet(self.button_style)

        self.previous_split_button = QPushButton(self.main_window)
        self.previous_split_button.setGeometry(QRect(550 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.previous_split_button.setText("<")
        self.previous_split_button.setEnabled(False)
        self.previous_split_button.setStyleSheet(self.button_style)

        self.next_split_button = QPushButton(self.main_window)
        self.next_split_button.setGeometry(QRect(1000 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.next_split_button.setText(">")
        self.next_split_button.setEnabled(False)
        self.next_split_button.setStyleSheet(self.button_style)

        self.pause_comparison_button = QPushButton(self.main_window)
        self.pause_comparison_button.setGeometry(QRect(580 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 191, 41))
        self.pause_comparison_button_pause_text = "Pause comparison"
        self.pause_comparison_button_unpause_text = "Resume comparison"
        self.pause_comparison_button.setText(self.pause_comparison_button_pause_text)
        self.pause_comparison_button.setEnabled(False)
        self.pause_comparison_button.setStyleSheet(self.button_style)
        self.pause_comparison_button.clicked.connect(self.toggle_pause_comparison)

        self.skip_split_button = QPushButton(self.main_window)
        self.skip_split_button.setGeometry(QRect(580 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.skip_split_button.setText("Skip split")
        self.skip_split_button.setEnabled(False)
        self.skip_split_button.setStyleSheet(self.button_style)

        self.undo_split_button = QPushButton(self.main_window)
        self.undo_split_button.setGeometry(QRect(680 + self.LEFT_EDGE_CORRECTION, 730 + self.TOP_EDGE_CORRECTION, 91, 41))
        self.undo_split_button.setText("Undo split")
        self.undo_split_button.setEnabled(False)
        self.undo_split_button.setStyleSheet(self.button_style)

        self.reset_splits_button = QPushButton(self.main_window)
        self.reset_splits_button.setGeometry(QRect(810 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 191, 91))
        self.reset_splits_button.setText("Reset run")
        self.reset_splits_button.setEnabled(False)
        self.reset_splits_button.setStyleSheet(self.button_style)

        # Menu bar
        self.menu_bar = QMenuBar(self.main_window)

        self.settings_action = QAction("&Open Settings Menu", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.about_action = QAction("&Help", self)
        self.about_action.setShortcut("Ctrl+shift+H")

        self.file_menu = self.menu_bar.addMenu("&Pilgrim UA")
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addAction(self.about_action)

        self.setMenuBar(self.menu_bar)

    def set_video_frame(self, frame: QPixmap):
        self.video_feed.setPixmap(frame)

    def set_split_image(self, frame: QPixmap):
        self.split_image.setPixmap(frame)

    def set_match_percent(self, match_percent: str, percent_type: PercentType):
        if percent_type == PercentType.CURRENT:
            label = self.current_match_percent
        elif percent_type == PercentType.HIGHEST:
            label = self.highest_match_percent
        else:
            label = self.threshold_match_percent

        if match_percent == "--.-":
            label.setText("--.-")
        else:
            match_percent_string = f"{{:.{MATCH_PERCENT_DECIMALS}f}}"
            label.setText(match_percent_string.format(float(match_percent) * 100))

    def toggle_pause_comparison(self):
        if self.pause_comparison_button.text() == self.pause_comparison_button_pause_text:
            self.pause_comparison_button.setText(self.pause_comparison_button_unpause_text)
            self.pause_comparison_signal.emit()
        else:
            self.pause_comparison_button.setText(self.pause_comparison_button_pause_text)
            self.unpause_comparison_signal.emit()

    def set_screenshot_button_status(self, status):
        self.screenshot_button.setEnabled(status)

    def set_previous_split_button_status(self, status):
        self.previous_split_button.setEnabled(status)

    def set_next_split_button_status(self, status):
        self.next_split_button.setEnabled(status)

    def set_pause_comparison_button_status(self, status):
        self.pause_comparison_button.setEnabled(status)

    def set_skip_split_button_status(self, status):
        self.skip_split_button.setEnabled(status)

    def set_undo_split_button_status(self, status):
        self.undo_split_button.setEnabled(status)

    def set_reset_splits_button_status(self, status):
        self.reset_splits_button.setEnabled(status)

    def set_split_image_css_status(self, splits_are_loaded: bool):
        if splits_are_loaded:
            self.split_image.setStyleSheet(self.loaded_split_image_style)
        else:
            self.split_image.setStyleSheet(self.image_style)

    def screenshot_success_message(self, screenshot_path):
        message = QMessageBox()
        message.setText("Screenshot taken")
        message.setInformativeText(f"Screenshot saved to:\n{screenshot_path}")
        message.setIcon(QMessageBox.Information)
        message.exec()

    def screenshot_error_message(self):
        message = QMessageBox()
        message.setText("Something went wrong")
        message.setInformativeText("Screenshot could not be taken. Please ensure video feed is active and try again.")
        message.setIcon(QMessageBox.Warning)
        message.exec()
