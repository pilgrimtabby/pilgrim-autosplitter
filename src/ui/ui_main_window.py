import platform
import webbrowser

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import (QAction, QLabel, QLineEdit, QMainWindow, QMenuBar,
                             QMessageBox, QPushButton, QShortcut, QWidget)

import settings
import ui.ui_style_sheet as style_sheet


class UIMainWindow(QMainWindow):
    LEFT_EDGE_CORRECTION = -44
    TOP_EDGE_CORRECTION = -215

    def __init__(self):
        #################
        #               #
        # Window Config #
        #               #
        #################

        super().__init__()

        # Main widget and title
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.setWindowTitle(f"Pilgrim Autosplitter v{settings.get_str('VERSION_NUMBER')}")

        # Menu bar
        self.menu_bar = QMenuBar(self.container)
        self.setMenuBar(self.menu_bar)

        self.settings_action = QAction("Open settings menu", self)
        self.settings_action.setShortcut("Ctrl+.")

        self.help_action = QAction("Help", self)
        self.help_action.triggered.connect(lambda: webbrowser.open("https://github.com/pilgrimtabby/pilgrim-autosplitter/", new=0, autoraise=True))

        self.menu_bar_pilgrim_autosplitter = self.menu_bar.addMenu("&Autosplitter Settings")
        self.menu_bar_pilgrim_autosplitter.addAction(self.settings_action)
        self.menu_bar_pilgrim_autosplitter.addAction(self.help_action)

        # Style and layout
        style_sheet.set_style(self)
        if platform.system() == "Windows":
            self.HEIGHT_CORRECTION = 22
        else:
            self.HEIGHT_CORRECTION = 0

        # Shortcut to close app
        self.close_window_shortcut = QShortcut("ctrl+w", self)
        self.close_window_shortcut.activated.connect(self.close)

        ###########
        #         #
        # Widgets #
        #         #
        ###########

        # Split directory button and display
        self.split_directory_button = QPushButton("Select split image folder:", self.container)
        self.split_directory_button.setFocusPolicy(Qt.NoFocus)

        self.split_directory_line_edit = QLineEdit(self.container)
        self.split_directory_line_edit.setAlignment(Qt.AlignLeft)
        self.split_directory_line_edit.setText(settings.get_str("LAST_IMAGE_DIR"))
        self.split_directory_line_edit.setEnabled(False)

        # Video feed
        self.video_feed_label = QLabel(self.container)
        self.video_feed_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.video_feed_label.setAlignment(Qt.AlignCenter)

        self.video_feed_label_live_text = "Video feed"
        self.video_feed_label_down_text_min = "Video status:   down"
        self.video_feed_label_live_text_min = "Video status:   healthy"

        self.video_feed_display = QLabel(self.container)
        self.video_feed_display.setAlignment(Qt.AlignCenter)
        self.video_feed_display.setObjectName("image_label_inactive")

        self.video_feed_display_default_text = "No video feed detected"        

        # Split image
        self.minimal_view_no_splits_label = QLabel(self.container)
        self.minimal_view_no_splits_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.minimal_view_no_splits_label.setAlignment(Qt.AlignCenter)
        self.minimal_view_no_splits_label.setGeometry(QRect(92 + self.LEFT_EDGE_CORRECTION, 225 + self.TOP_EDGE_CORRECTION, 251, 31))  # Always in the same spot

        self.split_name_label = QLabel(self.container)
        self.split_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_name_label.setAlignment(Qt.AlignCenter)

        self.split_image_loop_label = QLabel(self.container)
        self.split_image_loop_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.split_image_loop_label.setAlignment(Qt.AlignCenter)

        self.split_image_display = QLabel(self.container)
        self.split_image_display.setAlignment(Qt.AlignCenter)
        self.split_image_display.setObjectName("image_label_inactive")
        self.split_image_default_text = "No split images loaded"

        self.split_image_overlay = QLabel(self.container)
        self.split_image_overlay.setAlignment(Qt.AlignCenter)
        self.split_image_overlay.setObjectName("split_image_overlay")
        self.split_image_overlay.setVisible(False)

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

        # Minimal view button
        self.minimal_view_button = QPushButton(self.container)
        self.minimal_view_button.setFocusPolicy(Qt.NoFocus)

        # Next source button
        self.next_source_button = QPushButton("Next source", self.container)
        self.next_source_button.setFocusPolicy(Qt.NoFocus)

        # Screenshot button
        self.screenshot_button = QPushButton(self.container)
        self.screenshot_button.setEnabled(False)
        self.screenshot_button.setFocusPolicy(Qt.NoFocus)

        # Screenshot success message box
        self.screenshot_success_message_box = QMessageBox(self)
        self.screenshot_success_message_box.setText("Screenshot taken")

        # Screenshot error message box
        self.screenshot_error_message_box = QMessageBox(self)
        self.screenshot_error_message_box.setText("Could not take screenshot")
        self.screenshot_error_message_box.setInformativeText("No video feed detected. Please make sure video feed is active and try again.")
        self.screenshot_error_message_box.setIcon(QMessageBox.Warning)

        # Reload video button
        self.reload_video_button = QPushButton("Reconnect video", self.container)
        self.reload_video_button.setFocusPolicy(Qt.NoFocus)

        # Previous split button
        self.previous_split_button = QPushButton("<", self.container)
        self.previous_split_button.setEnabled(False)
        self.previous_split_button.setFocusPolicy(Qt.NoFocus)

        # Next split button
        self.next_split_button = QPushButton(">", self.container)
        self.next_split_button.setEnabled(False)
        self.next_split_button.setFocusPolicy(Qt.NoFocus)

        # Skip split button
        self.skip_split_button = QPushButton(self.container)
        self.skip_split_button.setEnabled(False)
        self.skip_split_button.setFocusPolicy(Qt.NoFocus)

        # Undo split button
        self.undo_split_button = QPushButton(self.container)
        self.undo_split_button.setEnabled(False)
        self.undo_split_button.setFocusPolicy(Qt.NoFocus)

        # Pause comparison / unpause comparison button
        self.pause_comparison_button = QPushButton(self.container)
        self.pause_comparison_button.setEnabled(False)
        self.pause_comparison_button.setFocusPolicy(Qt.NoFocus)

        self.pause_comparison_button_pause_text_default = "Pause comparison"
        self.pause_comparison_button_pause_text_truncated = "Pause comp"
        self.pause_comparison_button_unpause_text_default = "Unpause comparison"
        self.pause_comparison_button_unpause_text_truncated = "Unpause comp"

        # Reset splits button
        self.reset_splits_button = QPushButton(self.container)
        self.reset_splits_button.setEnabled(False)
        self.reset_splits_button.setFocusPolicy(Qt.NoFocus)

    # called from ui_controller (pause / unpause button pressed) and ui_controller._poller when splitter suspended status changes
    def toggle_pause_comparison_button_text(self, splitter_suspended: bool) -> None:
        if settings.get_bool("SHOW_MIN_VIEW") or settings.get_str("ASPECT_RATIO") == "4:3 (320x240)":
            if splitter_suspended:
                self.pause_comparison_button.setText(self.pause_comparison_button_unpause_text_truncated)
            else:
                self.pause_comparison_button.setText(self.pause_comparison_button_pause_text_truncated)

        else:
            if splitter_suspended:
                self.pause_comparison_button.setText(self.pause_comparison_button_unpause_text_default)
            else:
                self.pause_comparison_button.setText(self.pause_comparison_button_pause_text_default)
