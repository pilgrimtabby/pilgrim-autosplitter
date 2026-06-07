# Copyright (c) 2024-2026 pilgrim_tabby

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Stores css-style Template strings that can be edited by changing dict
variable values.

This could fit in ui_controller.py, but it is bulky enough that I felt it would
be less awkward to simply keep it in a separate file.
"""


import platform
from string import Template

from PyQt5.QtCore import QObject


##########################
#                        #
# Dark Theme Style Sheet #
#                        #
##########################

style_dict_dark = {
    "default_background": "#333333",
    "widget_fill_color": "#606060",
    "hover_widget_fill_color": "#6a6a6a",
    "hover_button_fill_color": "#5a5a5a",
    "disabled_button_text_color": "#888888",
    "button_fill_color": "#4e4e4e",
    "text_and_borders": "white",
}

if platform.system() == "Windows" or platform.system() == "Darwin":
    font_size = "16px"
else:
    font_size = "14px"
style_dict_dark["font_size"] = font_size

style_sheet_dark = Template(
    """
    * {
        font-family: "Gill Sans", "Calibri", "Noto Sans";
        font-size: $font_size;
        color: $text_and_borders;
        background-color: $default_background;
    }

    QComboBox {
        background-color: #4e4e4e;
        selection-background-color: $hover_widget_fill_color;
    }
    QComboBox:hover {
        background-color: #5e5e5e;
    }
    QComboBox QAbstractItemView {
        border: 3px solid $text_and_borders;
        background: $default_background;
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

    QCheckBox {
        background-color: $widget_fill_color;
        border: 0px solid blue;
        border-radius: 2px;
        color: $text_and_borders;
    }

    QLineEdit {
        color: $disabled_button_text_color;
        background-color: #444444;
        border: 1px solid #242424;
        border-radius: 2px;
    }
    QLineEdit:hover {
        color: $text_and_borders;
        border: 1px solid #383838;
    }

    KeyLineEdit {
        border: 1px solid #242424;
        border-radius: 3px;
        background-color: $widget_fill_color;
        color: $text_and_borders;
        padding-left: 2px;
    }
    KeyLineEdit:hover {
        background-color: $hover_widget_fill_color;
    }
    KeyLineEdit:focus {
        border: 1px solid #3EA0EC;
    }

    QLabel#video_label {
        background: #555555;
        border: 1px solid $text_and_borders;
    }
    QLabel#video_overlay {
        background-color: transparent;
    }
    QLabel#image_label {
        background: #555555;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_overlay {
        background-color: rgba(134, 134, 134, 0.7);
        border: 1px solid $text_and_borders;
    }
    QLabel#checkbox_helper {
        border: 1px solid $text_and_borders;
        background-color: rgba(0, 0, 0, 0);
        border-radius: 2px;
    }

    QSpinBox,
    QDoubleSpinBox {
        background-color: $widget_fill_color;
    }
    QSpinBox:hover,
    QDoubleSpinBox:hover {
        background-color: $hover_widget_fill_color;
    }
    """
).substitute(style_dict_dark)


###########################
#                         #
# Light Theme Style Sheet #
#                         #
###########################

style_dict_light = {
    "default_background": "#D3D3D3",
    "widget_fill_color": "#bbbbbb",
    "hover_widget_fill_color": "#c3c3c3",
    "hover_button_fill_color": "#aeaeae",
    "disabled_button_text_color": "#888888",
    "button_fill_color": "#aaaaaa",
    "text_and_borders": "black",
}
style_dict_light["font_size"] = font_size

style_sheet_light = Template(
    """
    * {
        font-family: "Gill Sans", "Calibri", "Noto Sans";
        font-size: $font_size;
        color: $text_and_borders;
        background-color: $default_background;
    }

    QComboBox {
        background-color: #aaaaaa;
        selection-background-color: $default_background;
    }
    QComboBox QAbstractItemView {
        border: 3px solid $text_and_borders;
        background: $widget_fill_color;
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

    QCheckBox {
        background-color: $widget_fill_color;
        border: 0px solid blue;
        border-radius: 2px;
        color: $text_and_borders;
    }

    QLineEdit {
        color: #555555;
        background-color: $widget_fill_color;
        border: 1px solid #cccccc;
        border-radius: 2px;
        padding-left: 5px;
    }
    QLineEdit:hover {
        color: $text_and_borders;
        border: 1px solid #aaaaaa;
    }

    KeyLineEdit {
        border: 1px solid #404040;
        border-radius: 3px;
        background-color: $widget_fill_color;
        color: $text_and_borders;
        padding-left: 2px;
    }
    KeyLineEdit:hover {
        background-color: $hover_widget_fill_color;
    }
    KeyLineEdit:focus {
        border: 1px solid #3EA0EC;
    }

    QLabel#video_label {
        background: #bbbbbb;
        border: 1px solid $text_and_borders;
    }
    QLabel#video_overlay {
        background-color: transparent;
    }
    QLabel#image_label {
        background: #bbbbbb;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_overlay {
        background-color: rgba(134, 134, 134, 0.7);
        border: 1px solid $text_and_borders;
    }
    QLabel#checkbox_helper {
        border: 1px solid $text_and_borders;
        background-color: rgba(0, 0, 0, 0);
        border-radius: 2px;
    }

    QSpinBox,
    QDoubleSpinBox {
        background-color: $widget_fill_color;
    }
    QSpinBox:hover,
    QDoubleSpinBox:hover {
        background-color: $hover_widget_fill_color;
    }
    """
).substitute(style_dict_light)
