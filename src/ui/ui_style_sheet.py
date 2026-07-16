# Copyright (c) 2024-2025 pilgrim_tabby
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
    "default_background": "#2c2c2c",
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
    QComboBox QLineEdit,
    QComboBox QLineEdit:hover,
    QComboBox QLineEdit:focus {
        border: none;
        border-radius: 0px;
    }
    QComboBox QAbstractItemView {
        border: 3px solid $text_and_borders;
        background: $default_background;
    }

    QFrame#border {
        border: 1px solid $text_and_borders;
        background-color: $default_background;
    }

    QWidget#screenshot_dlg_checkbox_wrap {
        background-color: $default_background;
    }
    QWidget#screenshot_dlg_checkbox_wrap QCheckBox {
        background-color: $widget_fill_color;
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QWidget#screenshot_dlg_checkbox_wrap QLabel#checkbox_helper {
        background-color: rgba(0, 0, 0, 0);
    }

    QWidget#screenshot_dlg_dated_checkbox_wrap {
        background-color: $default_background;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap QCheckBox {
        background-color: $widget_fill_color;
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap QLabel#checkbox_helper {
        background-color: rgba(0, 0, 0, 0);
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap[burst_off="true"] QCheckBox {
        background-color: #4a4a4a;
        color: $disabled_button_text_color;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap[burst_off="true"] QLabel#checkbox_helper {
        border: 1px solid $disabled_button_text_color;
        background-color: rgba(0, 0, 0, 0);
    }

    QLabel#burst_complete_path {
        color: $disabled_button_text_color;
    }
    QMenuBar {
        padding: 5px 12px;
        spacing: 12px;
    }
    QMenuBar::item {
        padding: 8px 18px;
        background-color: transparent;
    }
    QMenuBar::item:selected {
        background-color: $widget_fill_color;
    }

    QMenu {
        font-family: "Gill Sans", "Calibri", "Noto Sans";
        font-size: $font_size;
        border: 1px solid $text_and_borders;
        background-color: $default_background;
        padding: 2px 0px;
    }
    QMenu::item {
        padding: 6px 16px;
        background-color: transparent;
    }
    QMenu::item:selected {
        background-color: $widget_fill_color;
    }
    QMenu::separator {
        height: 1px;
        background-color: $text_and_borders;
        margin: 4px 12px;
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
        background-color: #3e3e3e;
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
    QLineEdit#connect_ws_url {
        padding: 3px 6px;
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
    }
    QLabel#video_overlay {
        background-color: transparent;
    }
    QLabel#image_label {
        background: #555555;
    }
    QLabel#video_viewport_border,
    QLabel#split_viewport_border {
        background-color: transparent;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_overlay {
        background-color: rgba(134, 134, 134, 0.7);
    }
    QLabel#video_burst_overlay {
        background-color: rgba(134, 134, 134, 0.7);
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

    QWidget#video_crop_strip,
    QWidget#split_override_strip {
        background-color: #242424;
        border-radius: 2px;
    }
    QWidget#video_crop_strip QLabel,
    QWidget#split_override_strip QLabel {
        background: transparent;
    }
    QToolButton#split_type_menu_button {
        background-color: $widget_fill_color;
        border: none;
        border-radius: 2px;
        padding: 0px;
    }
    QToolButton#split_type_menu_button:hover {
        background-color: $hover_widget_fill_color;
    }

    QToolTip {
        padding-left: 2px;
        padding-right: 2px;
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
    "text_and_borders": "#202020",
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
    QComboBox QLineEdit,
    QComboBox QLineEdit:hover,
    QComboBox QLineEdit:focus {
        border: none;
        border-radius: 0px;
    }
    QComboBox QAbstractItemView {
        border: 3px solid $text_and_borders;
        background: $widget_fill_color;
    }

    QFrame#border {
        border: 1px solid $text_and_borders;
        background-color: $default_background;
    }

    QWidget#screenshot_dlg_checkbox_wrap {
        background-color: $default_background;
    }
    QWidget#screenshot_dlg_checkbox_wrap QCheckBox {
        background-color: $widget_fill_color;
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QWidget#screenshot_dlg_checkbox_wrap QLabel#checkbox_helper {
        background-color: rgba(0, 0, 0, 0);
    }

    QWidget#screenshot_dlg_dated_checkbox_wrap {
        background-color: $default_background;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap QCheckBox {
        background-color: $widget_fill_color;
        spacing: 0px;
        padding: 0px;
        margin: 0px;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap QLabel#checkbox_helper {
        background-color: rgba(0, 0, 0, 0);
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap[burst_off="true"] QCheckBox {
        background-color: #c8c8c8;
        color: $disabled_button_text_color;
    }
    QWidget#screenshot_dlg_dated_checkbox_wrap[burst_off="true"] QLabel#checkbox_helper {
        border: 1px solid $disabled_button_text_color;
        background-color: rgba(0, 0, 0, 0);
    }

    QLabel#burst_complete_path {
        color: $disabled_button_text_color;
    }
    QMenuBar {
        padding: 5px 12px;
        spacing: 12px;
    }
    QMenuBar::item {
        padding: 8px 18px;
        background-color: transparent;
    }
    QMenuBar::item:selected {
        background-color: $widget_fill_color;
    }

    QMenu {
        font-family: "Gill Sans", "Calibri", "Noto Sans";
        font-size: $font_size;
        border: 1px solid $text_and_borders;
        background-color: $default_background;
        padding: 2px 0px;
    }
    QMenu::item {
        padding: 6px 16px;
        background-color: transparent;
    }
    QMenu::item:selected {
        background-color: $widget_fill_color;
    }
    QMenu::separator {
        height: 1px;
        background-color: $text_and_borders;
        margin: 4px 12px;
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
        background-color: #dadada;
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
    QLineEdit#connect_ws_url {
        padding: 3px 6px;
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
    }
    QLabel#video_overlay {
        background-color: transparent;
    }
    QLabel#image_label {
        background: #bbbbbb;
    }
    QLabel#video_viewport_border,
    QLabel#split_viewport_border {
        background-color: transparent;
        border: 1px solid $text_and_borders;
    }
    QLabel#split_overlay {
        background-color: rgba(134, 134, 134, 0.7);
    }
    QLabel#video_burst_overlay {
        background-color: rgba(134, 134, 134, 0.7);
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

    QWidget#video_crop_strip,
    QWidget#split_override_strip {
        background-color: #ababab;
        border-radius: 2px;
    }
    QWidget#video_crop_strip QLabel,
    QWidget#split_override_strip QLabel {
        background: transparent;
    }
    QToolButton#split_type_menu_button {
        background-color: $widget_fill_color;
        border: 1px solid #8f8f8f;
        border-radius: 2px;
        padding: 0px;
    }
    QToolButton#split_type_menu_button:hover {
        background-color: $hover_widget_fill_color;
    }

    QToolTip {
        padding-left: 2px;
        padding-right: 2px;
    }
    """
).substitute(style_dict_light)
