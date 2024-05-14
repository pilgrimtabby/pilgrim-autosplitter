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
        self.image_directory_button = QPushButton("Select split image folder:", self.container)

        self.image_directory_line_edit = QLineEdit(self.container)
        self.image_directory_line_edit.setEnabled(False)

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
