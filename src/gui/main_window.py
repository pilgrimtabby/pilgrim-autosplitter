import time
import webbrowser

from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAction, QLabel, QLineEdit, QMainWindow, QMenuBar,
                             QMessageBox, QPushButton, QShortcut, QWidget)

from utils import settings


class GUIMainWindow(QMainWindow):
    def __init__(self, style_sheet):
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        # Main widget and title
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.setWindowTitle(f"Pilgrim Autosplitter v{settings.value('VERSION_NUMBER')}")

        # Menu bar
        self.menu_bar = QMenuBar(self.container)
        self.setMenuBar(self.menu_bar)

        self.settings_action = QAction("Settings", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.help_action = QAction("Help", self)
        self.settings_action.triggered.connect(lambda: webbrowser.open("https://github.com/pilgrimtabby/image-capture/", new=0, autoraise=True))

        self.menu_bar_pilgrim_autosplitter = self.menu_bar.addMenu("&Pilgrim Autosplitter")
        self.menu_bar_pilgrim_autosplitter.addAction(self.settings_action)
        self.menu_bar_pilgrim_autosplitter.addAction(self.help_action)

        ###########
        #         #
        # Widgets #
        #         #
        ###########

        # Split directory button and display
        self.split_directory_button = QPushButton("Select split image folder:", self.container)

        self.split_directory_line_edit = QLineEdit(self.container)
        self.split_directory_line_edit.setEnabled(False)

        # Video feed
        self.video_feed_label = QLabel(self.container)
        self.video_feed_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.video_feed_label.setAlignment(Qt.AlignCenter)

        self.video_feed_display = QLabel(self.container)
        self.video_feed_display.setAlignment(Qt.AlignCenter)

        # Split image
        self.split_name_label = QLabel(self.container)
        self.split_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.split_image_loop_label = QLabel(self.container)
        self.split_image_loop_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_image_loop_label.setAlignment(Qt.AlignCenter)

        self.split_image_display = QLabel(self.container)
        self.split_image_display.setAlignment(Qt.AlignCenter)

        self.split_image_overlay = QLabel(self.container)
        self.split_image_overlay.setAlignment(Qt.AlignCenter)

        # Match percent (current)
        self.current_match_percent_label = QLabel(self.container)
        self.current_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent = QLabel(self.container)
        self.current_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.current_match_percent_sign = QLabel("%", self.container)
        self.current_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        
        # Match percent (highest)
        self.highest_match_percent_label = QLabel(self.container)
        self.highest_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent = QLabel(self.container)
        self.highest_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.highest_match_percent_sign = QLabel("%", self.container)
        self.highest_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.highest_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Match percent (threshold)
        self.threshold_match_percent_label = QLabel(self.container)
        self.threshold_match_percent_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent = QLabel(self.container)
        self.threshold_match_percent.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.threshold_match_percent_sign = QLabel("%", self.container)
        self.threshold_match_percent_sign.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.threshold_match_percent_sign.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        # Other buttons
        self.minimal_view_button = QPushButton(self.container)
        self.next_source_button = QPushButton("Next source", self.container)
        self.screenshot_button = QPushButton(self.container)
        self.reload_video_button = QPushButton("Reconnect video", self.container)
        self.previous_split_button = QPushButton("<", self.container)
        self.next_split_button = QPushButton(">", self.container)
        self.pause_comparison_button = QPushButton(self.container)
        self.skip_split_button = QPushButton(self.container)
        self.undo_split_button = QPushButton(self.container)
        self.reset_splits_button = QPushButton(self.container)

        #######################
        #                     #
        # Style and Shortcuts #
        #                     #
        #######################

        # Style and layout
        self.style_sheet = style_sheet
        self.style_sheet.set_style()

        # Program shortcuts
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)

        # UI shortcuts
        self.split_shortcut = QShortcut(self)
        self.reset_shortcut = QShortcut(self)
        self.undo_split_shortcut = QShortcut(self)
        self.skip_split_shortcut = QShortcut(self)
        self.previous_split_shortcut = QShortcut(self)
        self.next_split_shortcut = QShortcut(self)
        self.screenshot_shortcut = QShortcut(self)
        self.set_ui_shortcut_keybindings()

    ##################
    #                #
    # Setter Methods #
    #                #
    ##################

    def set_split_directory_line_edit_text(self):
        path = settings.value("LAST_IMAGE_DIR")
        elided_path = self.split_directory_line_edit.fontMetrics().elidedText(path, Qt.ElideMiddle, self.split_directory_line_edit.width())
        self.split_directory_line_edit.setText(elided_path)

    def toggle_min_view_button_text(self):
        if settings.value("SHOW_MIN_VIEW"):
            self.minimal_view_button.setText("Full view")
        else:
            self.minimal_view_button.setText("Minimal view")

    def set_ui_shortcut_keybindings(self):
        for shortcut, key_sequence in {
            self.split_shortcut: settings.value("SPLIT_HOTKEY_KEY_SEQUENCE"),
            self.reset_shortcut: settings.value("RESET_HOTKEY_KEY_SEQUENCE"),
            self.undo_split_shortcut: settings.value("UNDO_HOTKEY_KEY_SEQUENCE"),
            self.skip_split_shortcut: settings.value("SKIP_HOTKEY_KEY_SEQUENCE"),
            self.previous_split_shortcut: settings.value("PREVIOUS_HOTKEY_KEY_SEQUENCE"),
            self.next_split_shortcut: settings.value("NEXT_HOTKEY_KEY_SEQUENCE"),
            self.screenshot_shortcut: settings.value("SCREENSHOT_HOTKEY_KEY_SEQUENCE"),
        }.items():
            if key_sequence is None:
                shortcut = QShortcut(self)
            else:
                shortcut.setKey(key_sequence)

    def set_layout(self, splitter_paused: bool):
        layout = self.get_layout()
        layout(splitter_paused)

    def get_layout(self):
        if settings.value("SHOW_MIN_VIEW"):
            return self._show_minimal_view

        else:
            aspect_ratio = settings.value("ASPECT_RATIO")
            if aspect_ratio == "4:3 (480x360)":
                return self._show_480x360_view

            elif aspect_ratio == "4:3 (320x240)":
                return self._show_320x240_view

            elif aspect_ratio == "16:9 (512x288)":
                return self._show_512x288_view

            elif aspect_ratio == "16:9 (432x243)":
                return self._show_432x243_view

    def _show_minimal_view(self, splitter_paused: bool):
        self._show_nonessential_widgets(False)
        self._truncate_labels(truncate=True, splitter_paused=splitter_paused)
        self.setFixedSize(345, 179)

        self.previous_split_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.split_name_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 214 + self.TOP_EDGE_CORRECTION, 251, 31))
        self.split_loop_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 239 + self.TOP_EDGE_CORRECTION, 251, 31))
        self.next_split_button.setGeometry(QRect(344 + self.LEFT_EDGE_CORRECTION, 224 + self.TOP_EDGE_CORRECTION, 31, 31))
        self.minimal_view_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 100, 31))
        self.video_feed_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 270 + self.TOP_EDGE_CORRECTION, 213, 31))
        self.pause_comparison_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 121, 31))
        self.skip_split_button.setGeometry(QRect(125 + self.LEFT_EDGE_CORRECTION, 350 + self.TOP_EDGE_CORRECTION, 56, 31))
        self.undo_split_button.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 350 + self.TOP_EDGE_CORRECTION, 56, 31))
        self.reset_splits_button.setGeometry(QRect(304 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 71, 71))
        self.current_match_percent_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_match_percent_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_match_percent_label.setGeometry(QRect(62 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(232 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 304 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_match_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 331 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_match_percent_sign.setGeometry(QRect(282 + self.LEFT_EDGE_CORRECTION, 358 + self.TOP_EDGE_CORRECTION, 21, 31))

    def _show_480x360_view(self, splitter_paused: bool):
        self._show_nonessential_widgets(True)
        self._truncate_labels(truncate=False, splitter_paused=splitter_paused)
        self.setFixedSize(1002, 570)

        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 785, 30))
        self.video_feed_label.setGeometry(QRect(260 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(584 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 415, 31))
        self.split_loop_label.setGeometry(QRect(584 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 415, 31))
        self.current_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 680 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 710 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 740 + self.TOP_EDGE_CORRECTION, 21, 31))
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
        self.video_feed_display.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360))
        split_image_geometry = QRect(550 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 480, 360)
        self.split_image_display.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def _show_320x240_view(self, splitter_paused: bool):
        self._show_nonessential_widgets(True)
        self._truncate_labels(truncate=True, splitter_paused=splitter_paused)
        self.setFixedSize(682, 450)

        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 464, 30))
        self.video_feed_label.setGeometry(QRect(180 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(424 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 254, 31))
        self.split_loop_label.setGeometry(QRect(424 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 254, 31))
        self.current_match_percent_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_match_percent_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_match_percent_label.setGeometry(QRect(-50 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(120 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 560 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_match_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 590 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_match_percent_sign.setGeometry(QRect(170 + self.LEFT_EDGE_CORRECTION, 620 + self.TOP_EDGE_CORRECTION, 21, 31))
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
        self.video_feed_display.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 320, 240))
        split_image_geometry = QRect(390 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 320, 240)
        self.split_image_display.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def _show_512x288_view(self, splitter_paused: bool):
        self._show_nonessential_widgets(True)
        self._truncate_labels(truncate=False, splitter_paused=splitter_paused)
        self.setFixedSize(1064, 497)

        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 848, 30))
        self.video_feed_label.setGeometry(QRect(276 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 80, 31))
        self.split_name_label.setGeometry(QRect(613 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 450, 31))
        self.split_loop_label.setGeometry(QRect(613 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 450, 31))
        self.current_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 608 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 638 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 668 + self.TOP_EDGE_CORRECTION, 21, 31))
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
        self.video_feed_display.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 512, 288))
        split_image_geometry = QRect(582 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 512, 288)
        self.split_image_display.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def _show_432x243_view(self, splitter_paused):
        self._show_nonessential_widgets(True)
        self._truncate_labels(truncate=False, splitter_paused=splitter_paused)
        self.setFixedSize(904, 452)
        split_image_geometry = QRect(502 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 432, 243)

        self.image_directory_line_edit.setGeometry(QRect(247 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 688, 30))
        self.video_feed_label.setGeometry(QRect(161 + self.LEFT_EDGE_CORRECTION, 272 + self.TOP_EDGE_CORRECTION, 231, 31))
        self.split_name_label.setGeometry(QRect(534 + self.LEFT_EDGE_CORRECTION, 255 + self.TOP_EDGE_CORRECTION, 371, 31))
        self.split_loop_label.setGeometry(QRect(534 + self.LEFT_EDGE_CORRECTION, 280 + self.TOP_EDGE_CORRECTION, 371, 31))
        self.current_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.highest_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.threshold_match_percent_label.setGeometry(QRect(80 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 161, 31))
        self.current_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.highest_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.threshold_match_percent.setGeometry(QRect(250 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 41, 31))
        self.current_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 563 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.highest_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 593 + self.TOP_EDGE_CORRECTION, 21, 31))
        self.threshold_match_percent_sign.setGeometry(QRect(300 + self.LEFT_EDGE_CORRECTION, 623 + self.TOP_EDGE_CORRECTION, 21, 31))
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
        self.video_feed_display.setGeometry(QRect(60 + self.LEFT_EDGE_CORRECTION, 310 + self.TOP_EDGE_CORRECTION, 432, 243))
        self.split_image_display.setGeometry(split_image_geometry)
        self.split_image_overlay.setGeometry(split_image_geometry)

    def _truncate_labels(self, truncate: bool, splitter_paused: bool):
        if truncate:
            self.current_match_percent_label.setText("Sim:")
            self.highest_match_percent_label.setText("High:")
            self.threshold_match_percent_label.setText("Thr:")
            if splitter_paused:
                self.pause_comparison_button.setText("Unpause comp")
            else:
                self.pause_comparison_button.setText("Pause comp")
            self.small_undo_split_button_text = "Undo"
            self.small_skip_split_button_text = "Skip"
            self.small_reset_splits_button_text = "Reset"

        else:
            pass

    def _show_nonessential_widgets(self, visible):
        self.image_directory_line_edit.setVisible(visible)
        self.image_directory_button.setVisible(visible)
        self.next_source_button.setVisible(visible)
        self.screenshot_button.setVisible(visible)
        self.reload_video_button.setVisible(visible)
        self.video_feed_display.setVisible(visible)
        self.split_image_display.setVisible(visible)
