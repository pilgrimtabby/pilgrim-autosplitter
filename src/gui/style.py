from string import Template
from utils import settings

class GUIStyle: 
    def __init__(self):
        self.style_dict_dark = {
            "default_background": "#333333",
            "widget_fill_color": "#555555",
            "hover_button_fill_color": "#4e4e4e",
            "disabled_button_text_color": "#888888",
            "button_fill_color": "#444444",
            "text_and_borders": "white",
        }
        self.style_dict_light = {
            "default_background": "#f3f6f4",
            "widget_fill_color": "#555555",
            "hover_button_fill_color": "#4e4e4e",
            "disabled_button_text_color": "#888888",
            "button_fill_color": "#444444",
            "text_and_borders": "white",
        }

        self.style_sheet_dark = Template(
            """
            * {
                font-family: "Gill Sans";
                font-size: 16px;
                color: $text_and_borders;
                background-color: $default_background;
            }

            QFrame#border {
                border: 1px solid $text_and_borders;
            }
            QPushButton {
                background-color: $button_fill_color;
            }
            QPushButton:hover {
                background-color: $hover_button_fill_color;
            }
            QPushButton:pressed {
                padding-top: 3px;
                padding-left: 3px;
            }
            QPushButton:disabled {
                color: $disabled_button_text_color;
            }
            QPushButton#save_button {
            }

            QKeySequenceEdit {
                color: 3px solid purple;
            }

            QLabel#image_label_active {
                background: $default_background;
                border: 1px solid $text_and_borders;
            }
            QLabel#image_label_inactive {
                background: $widget_fill_color;
                border: 1px solid $text_and_borders;
            }
            QLabel#image_label_overlay {
                background-color: rgba(134, 134, 134, 0.1);
                border: 0px solid $text_and_borders;
            }
            
            QLineEdit#line_edit_default {
                color: $disabled_button_text_color;
            }
            QLineEdit#line_edit_live {
                color: $text_and_borders;
            }

            QComboBox {
                background-color: #3D3D3D;
                selection-background-color: $hover_button_fill_color;
                padding-top: 2px;
                padding-left: 5px;
                border: none;
            }
            
            QComboBox:disabled {
                background-color: $button_fill_color;
                color: $disabled_button_text_color;
            }

            QComboBox:hover {
                background-color: $button_fill_color;
            }

            QComboBox QAbstractItemView {
                border: 2px solid grey;
                border-radius: 5px;
                min-width: 80px;
            }
            """
        ).substitute(self.style_dict_dark)
        self.style_sheet_light = Template(
            """
            * {
                font-family: "Gill Sans";
                font-size: 16px;
                color: $text_and_borders;
                background-color: $default_background;
            }

            QFrame#border {
                border: 1px solid $text_and_borders;
            }
            QPushButton {
                background-color: $button_fill_color;
            }
            QPushButton:hover {
                background-color: $hover_button_fill_color;
            }
            QPushButton:pressed {
                padding-top: 3px;
                padding-left: 3px;
            }
            QPushButton:disabled {
                color: $disabled_button_text_color;
            }

            QLabel#image_label_active {
                background: $default_background;
                border: 1px solid $text_and_borders;
            }
            QLabel#image_label_inactive {
                background: $widget_fill_color;
                border: 1px solid $text_and_borders;
            }
            QLabel#image_label_overlay {
                background-color: rgba(134, 134, 134, 0.1);
                border: 0px solid $text_and_borders;
            }
            
            QLineEdit#line_edit_default {
                color: $disabled_button_text_color;
            }
            QLineEdit#line_edit_live {
                color: $text_and_borders;
            }
            """
        ).substitute(self.style_dict_light)

    def set_style(self, window):
        if settings.value("THEME") == "dark":
            window.setStyleSheet(self.style_sheet_dark)
        elif settings.value("THEME") == "light":
            window.setStyleSheet(self.style_sheet_light)

    def set_global_style(self, windows: list):
        for window in windows:
            self.set_style(window)
            window.update()
