# Copyright (c) 2024 pilgrim_tabby
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Stores css-style Template strings that can be edited by changing dict variable values.

This could fit in ui_controller.py, but it is bulky enough that I felt it would be less awkward to simply keep it in a separate file.
"""


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
style_sheet_dark = Template(
    """
    * {
        font-family: "Gill Sans", "Calibri";
        font-size: 16px;
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
        padding-left: 5px;
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

    QLabel#image_label_active {
        background: $default_background;
        border: 1px solid $text_and_borders;
    }
    QLabel#image_label_inactive {
        background: #555555;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_image_overlay {
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
style_sheet_light = Template(
    """
    * {
        font-family: "Gill Sans", "Calibri";
        font-size: 16px;
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

    QLabel#image_label_active {
        background: $default_background;
        border: 1px solid $text_and_borders;
    }
    QLabel#image_label_inactive {
        background: #bbbbbb;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_image_overlay {
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


def set_style(window: QObject, theme: str) -> None:
    """Set the style sheet of a QWidget.

    Args:
        window (QWidget): The widget whose style is being set.
        theme (str): The theme to be set.
    """
    if theme == "dark":
        window.setStyleSheet(style_sheet_dark)
    elif theme == "light":
        window.setStyleSheet(style_sheet_light)
