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

            QWidget#combo_box {
                selection-background-color: $widget_fill_color;
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
                padding-top: 2px;
                padding-left: 2px;
            }
            QPushButton:disabled {
                color: $disabled_button_text_color;
            }
            QPushButton:focus {
            }
            QPushButton#save_button {
            }

            QCheckBox {
                background-color: $widget_fill_color;
                border: 0px solid blue;
                border-radius: 2px;
            }
            QLineEdit {
                color: $disabled_button_text_color;
            }

            KeyLineEdit {
                border: 1px solid #404040;
                border-radius: 3px;
                background-color: $button_fill_color;
                color: white;
                padding-left: 2px;
            }
            KeyLineEdit:focus {
                border: 1px solid #3EA0EC;
            }

            QLabel#image_label_active {
                background: $default_background;
                border: 1px solid $text_and_borders;
            }
            QLabel#image_label_inactive {
                background: $widget_fill_color;
                border: 1px solid $text_and_borders;
            }
            QLabel#split_image_overlay {
                background-color: rgba(134, 134, 134, 0.7);
                border: 1px solid $text_and_borders;
            }
            QLabel#checkbox_helper {
                border: 1px solid white;
                background-color: rgba(0, 0, 0, 0);
                border-radius: 2px;
            }
            QLabel#spinbox_helper:hover {
                background-color: $widget_fill_color;
            }

            QSpinBox,
            QDoubleSpinBox {
                background-color: $button_fill_color;
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
            QLabel#split_image_overlay {
                background-color: rgba(134, 134, 134, 0.1);
                border: 1px solid $text_and_borders;
            }
            
            QLineEdit {
                color: $disabled_button_text_color;
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
