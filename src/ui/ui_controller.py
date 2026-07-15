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

"""Manage the passing of information from the splitter to the UI, and from user
input to the UI and the splitter.
"""


import datetime
import json
import os
import paths
import platform
import re
import subprocess
import time
from pathlib import Path
from threading import Lock, Thread
from typing import Any, List, Optional, Tuple, Union
import webbrowser

import cv2
from PyQt5.QtCore import QEvent, QObject, QLocale, QRect, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import settings
from livesplit.timer_sync import LiveSplitTimerSync
from splitter.splitter import Splitter
from ui.split_navigation import navigate_to_next_split, navigate_to_previous_split
from ui.timer_hotkey import press_hotkey_or_fallback
from ui.ui_connect_dialog import UIConnectWebSocketDialog
from ui.ui_keyboard_controller import UIKeyboardController
from ui.ui_main_window import UIMainWindow
from ui.ui_settings_window import UISettingsWindow
from ui.ui_style_sheet import style_sheet_light, style_sheet_dark
from ui.layout_presets import (
    AspectLayoutPreset,
    BOTTOM_ADJ_PAIR_GAP_PX,
    BOTTOM_BLOCK_LIFT_PX,
    LAYOUT_PRESET_320,
    LAYOUT_PRESET_432,
    LAYOUT_PRESET_480,
    LAYOUT_PRESET_512,
    LAYOUT_PRESETS,
    SplitColumnBottomPreset,
    STRIP_GAP_BELOW_VIEWPORT_PX,
    VIDEO_CROP_STRIP_LAYOUT_DY,
    VIDEO_COL_SCREENSHOT_H,
    VIDEO_COL_STATS_LABEL_W,
    VIDEO_COL_STATS_PCT_X,
    VIDEO_COL_STATS_ROW_H,
    VIDEO_COL_STATS_ROW_STEP,
    VIDEO_COL_STATS_SPAN_W,
    VIDEO_COL_STATS_VALUE_X,
    VideoColumnBottomPreset,
)
from ui.strip_typography import (
    STRIP_LOCAL_LABEL_PX,
    STRIP_LOCAL_SPIN_PX,
    STRIP_MENU_BOX_HEIGHT_PX,
    StripTypographyApplier,
)
from ui.layout_apply import apply_aspect_layout
from ui.profile_store import ProfileStore
from ui.video_crop import VideoCropController
from ui.labels import SNAP_PEAK_HOTKEY_LABEL
from ui.screenshot_capture import ScreenshotCapture
from ui.slot_errors import log_slot_error

# Slightly larger than global theme for bottom stats + main action buttons only.
_BOTTOM_PANEL_FONT_PX = 17


class UIController:
    """Manage the passing of information from the splitter to the UI, and from
    user input to the UI and the splitter.

    Perhaps the most important class method is _poll, which is ran once per
    frame using a QTimer. This method updates the UI and handles all user
    inputs.

    UIController has no public attributes, as it is meant to operate after
    initialization without further input. For details about each attribute,
        see method documentation.
    """

    def __init__(self, application: QApplication, splitter: Splitter) -> None:
        """Initialize the UI, then update it each frame.

        Creates each UI window and then shows the main window.
        Connects pyqtSignals from each UI window to their respective slots.
        Sets initial flags and values used by poller.
        Starts the keyboard listener.
        Starts poller, which checks for user input and splitter outputs at
        regular intervals.

        Args:
            application (QApplication): The QApplication that the program is
                based on.
            splitter (Splitter): The splitter capturing video and comparing
                video to splits.
        """
        # Initialize the UI
        self._application = application
        self._splitter = splitter
        self._main_window = UIMainWindow()
        self._settings_window = UISettingsWindow()
        self._strip_typography = StripTypographyApplier(self)
        self._screenshot = ScreenshotCapture(self)
        self._profiles = ProfileStore(self)
        self._video_crop = VideoCropController(self)
        self._livesplit_ws_server: Optional[Any] = None
        self._lso = LiveSplitTimerSync()
        self._livesplit_menu_linked: Optional[bool] = None

        style = self._get_style_sheet()
        self._main_window.setStyleSheet(style)
        self._settings_window.setStyleSheet(style)
        self._apply_theme_icons()

        # Check if there's an update available and show message if so
        if settings.get_bool("CHECK_FOR_UPDATES"):
            latest_version = settings.get_latest_version()
            if not settings.version_ge(settings.VERSION_NUMBER, latest_version):
                msg = self._main_window.update_available_msg
                msg.setStyleSheet(style)
                msg.show()
                msg.raise_()  # Make sure msg isn't hidden behind app

        ########################
        #                      #
        # Poller Values, Flags #
        #                      #
        ########################

        # Tell _update_ui to update split labels
        # Should be set whenever the split image is modified
        self._redraw_split_labels = True

        # Tell _splitter to display reset image match percents, not split image
        # match percent
        self._show_reset_percents = False

        # Only update main_window's style sheet when it has changed
        self._most_recent_style_sheet = None
        # Strip typography (injected into the composed main-window stylesheet)
        # Defaults so composed QSS always includes strip layout rules before first layout pass.
        self._strip_label_font_px: Optional[float] = float(STRIP_LOCAL_LABEL_PX)
        self._strip_control_font_px: Optional[float] = float(STRIP_LOCAL_SPIN_PX)
        self._crop_reset_min_width = 0
        self._strip_row_height: int = STRIP_MENU_BOX_HEIGHT_PX
        self._strip_popup_side: int = STRIP_MENU_BOX_HEIGHT_PX

        # Only resize record icon when aspect ratio changes
        self._resize_record_icon = False
        self._record_active_pixmap = None
        self._record_idle_pixmap = None

        # Layout rects for video/split panes (press effect uses translate, not move).
        self._video_viewport_base: Optional[QRect] = None
        self._split_viewport_base: Optional[QRect] = None

        # Values for updating hotkeys in settings menu
        # (see _react_to_settings_menu_flags)
        self._hotkey_box_to_change = None
        self._hotkey_box_key_code = None
        self._hotkey_box_key_name = None
        self._hotkey_box_lock = Lock()

        # Flags to disable hotkeys
        self._split_hotkey_enabled = False
        self._undo_hotkey_enabled = False
        self._skip_hotkey_enabled = False

        # Flags for detecting hotkey presses
        self._split_hotkey_pressed = False
        self._reset_hotkey_pressed = False
        self._undo_hotkey_pressed = False
        self._skip_hotkey_pressed = False
        self._previous_hotkey_pressed = False
        self._next_hotkey_pressed = False
        self._screenshot_hotkey_pressed = False
        self._save_peak_hotkey_pressed = False
        self._toggle_hotkeys_hotkey_pressed = False

        # Values for keeping display awake (see _wake_display)
        self._last_wake_time = time.perf_counter()
        # Attempt wake after this many seconds. Should be < 1 min, since that's
        # the minimum allowed time to trigger display sleep on most OSs
        self._wake_interval = 45
        # MacOS-specific values (MacOS uses caffeinate)
        self._caffeinate_thread = Thread(target=self._caffeinate)
        self._caffeinate_thread_finished = True

        self._split_override_guard = False
        self._split_override_sync_key: Optional[Tuple[int, str]] = None

        ######################
        #                    #
        # Main Window Config #
        #                    #
        ######################

        # Set layout
        self._set_main_window_layout()

        self._main_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )

        # "Update available" message box
        self._main_window.update_available_msg.buttonClicked.connect(
            self.update_available_msg_action
        )

        # Split directory line edit
        self._main_window.split_directory_box.clicked.connect(
            lambda: self._open_file_or_dir(settings.get_str("LAST_IMAGE_DIR"))
        )

        # Split directory button
        self._main_window.split_dir_button.clicked.connect(self._set_split_dir_path)

        # Video feed
        self._main_window.video_display.valid_single_click.connect(
            self._toggle_record_clips
        )
        self._main_window.video_display.valid_double_click.connect(
            self._set_record_dir_path
        )

        # Minimal view / full view button
        self._main_window.min_view_button.clicked.connect(
            lambda: settings.set_value(
                "SHOW_MIN_VIEW", not settings.get_bool("SHOW_MIN_VIEW")
            )
        )
        self._main_window.min_view_button.clicked.connect(self._set_main_window_layout)

        # Next source button
        self._main_window.next_source_button.clicked.connect(
            self._splitter.set_next_capture_index
        )
        self._main_window.next_source_button.clicked.connect(self._splitter.restart)

        # Screenshot button
        self._main_window.screenshot_button.clicked.connect(self._screenshot.take_screenshot)
        self._main_window.screenshot_settings_button.clicked.connect(
            self._screenshot.exec_settings_dialog
        )

        # Reload video button
        self._main_window.reconnect_button.clicked.connect(self._splitter.restart)

        self._video_crop.wire_controls()
        self._wire_split_override_controls()

        # Pause comparison / unpause comparison button
        self._main_window.pause_button.clicked.connect(self._splitter.toggle_suspended)

        # Reset button
        self._main_window.reset_button.clicked.connect(self._attempt_reset_hotkey)

        # Undo split button
        self._main_window.undo_button.clicked.connect(self._attempt_undo_hotkey)

        # Skip split button
        self._main_window.skip_button.clicked.connect(self._attempt_skip_hotkey)

        # Previous split button
        self._main_window.previous_button.clicked.connect(self._request_previous_split)

        # Next split button
        self._main_window.next_button.clicked.connect(self._request_next_split)

        # Settings window action
        self._main_window.settings_action.triggered.connect(self._exec_settings_window)

        # Help action
        self._main_window.help_action.triggered.connect(
            lambda: self._open_url(settings.USER_MANUAL_URL)
        )
        self._main_window.profile_load_action.triggered.connect(
            self._profiles.load_profile_via_dialog
        )
        self._main_window.profile_save_action.triggered.connect(
            self._profiles.save_profile_via_dialog
        )
        self._profiles.refresh_recent_profile_actions()

        self._main_window.connect_disconnect_action.triggered.connect(
            self.stop_livesplit_ws_server
        )
        self._main_window.connect_start_server_action.triggered.connect(
            self._open_livesplit_ws_server_dialog
        )
        self._update_connect_menu_state()

        ##########################
        #                        #
        # Settings Window Config #
        #                        #
        ##########################

        close_settings = lambda: self._settings_window.done(0)

        # Close window convenience shortcut
        self._settings_window.close_window_shortcut.activated.connect(close_settings)

        # Cancel button
        self._settings_window.cancel_button.clicked.connect(close_settings)

        # Save button
        self._settings_window.save_button.clicked.connect(self._save_settings_and_close)

        #################
        #               #
        # Start Polling #
        #               #
        #################

        # Start keyboard listener
        self._keyboard = UIKeyboardController()
        self._keyboard.start_listener(on_press=self._handle_key_press, on_release=None)

        # Start poller
        self._poller = QTimer()
        self._poller.setInterval(self._get_interval())
        self._poller.timeout.connect(self._poll)
        self._poller.start()

        self._main_window.show()

    ##################
    #                #
    # Helper Methods #
    #                #
    ##################

    def stop_livesplit_ws_server(self) -> None:
        """Stop the LiveSplit One WebSocket server if it is running."""
        if self._livesplit_ws_server is not None:
            self._livesplit_ws_server.stop()
            self._livesplit_ws_server = None
        self._lso.set_server(None)
        self._update_connect_menu_state()

    def _update_connect_menu_state(self) -> None:
        linked = self._lso.linked
        if self._livesplit_menu_linked is not None and linked == self._livesplit_menu_linked:
            return
        self._livesplit_menu_linked = linked
        self._main_window.connect_disconnect_action.setEnabled(linked)

    def _on_livesplit_ws_client_change(self) -> None:
        QTimer.singleShot(0, self._update_connect_menu_state)

    def _import_livesplit_ws_server(self) -> Any:
        try:
            from livesplit.ws_server import LiveSplitWebSocketServer
        except ImportError:
            QMessageBox.warning(
                self._main_window,
                "Missing dependency",
                "The websockets package is required for LiveSplit One integration.\n\n"
                "Install it from the project folder:\n"
                "  pip install -r requirements.txt",
            )
            raise
        return LiveSplitWebSocketServer

    def _ensure_livesplit_ws_server(self) -> Any:
        if self._livesplit_ws_server is None:
            server_cls = self._import_livesplit_ws_server()
            port = settings.get_int("WS_SERVER_PORT")
            self._livesplit_ws_server = server_cls(
                port,
                on_client_connected=self._on_livesplit_ws_client_change,
                on_client_disconnected=self._on_livesplit_ws_client_change,
            )
            self._lso.set_server(self._livesplit_ws_server)
        return self._livesplit_ws_server

    def _open_livesplit_ws_server_dialog(self) -> None:
        try:
            server = self._ensure_livesplit_ws_server()
        except ImportError:
            return
        if not server.is_running:
            if not server.start():
                detail = server.start_error or "The port may already be in use."
                QMessageBox.warning(
                    self._main_window,
                    "WebSocket server failed",
                    "Could not start the WebSocket server.\n\n" + detail,
                )
                self._livesplit_ws_server = None
                self._lso.set_server(None)
                self._update_connect_menu_state()
                return
        dialog = UIConnectWebSocketDialog(
            server.url,
            is_connected=lambda: server.is_client_connected,
            parent=self._main_window,
        )
        dialog.setStyleSheet(self._get_style_sheet())
        dialog.exec_()

    def _ui_chrome_updates_paused(self) -> bool:
        """True while a menu is open — avoid repaints that flicker the menu bar."""
        if QApplication.activePopupWidget() is not None:
            return True
        if QApplication.activeModalWidget() is not None:
            return True
        menu_bar = self._main_window.menuBar()
        if menu_bar is None:
            return False
        for action in menu_bar.actions():
            menu = action.menu()
            if menu is not None and menu.isVisible():
                return True
        return False

    def _current_split_image(self):
        split_index = self._splitter.splits.current_image_index
        if split_index is None or not self._splitter.splits.list:
            return None
        return self._splitter.splits.list[split_index]

    def _current_split_is_dummy(self) -> bool:
        split = self._current_split_image()
        return split is not None and split.dummy_flag

    def _viewing_reset_image(self) -> bool:
        return (
            self._show_reset_percents
            and self._splitter.splits.reset_image is not None
        )

    def _on_first_split_image(self) -> bool:
        return self._splitter.splits.current_image_index == 0

    def _next_split_is_dummy(self) -> bool:
        split_index = self._splitter.splits.current_image_index
        if split_index is None:
            return False
        splits = self._splitter.splits
        split = splits.list[split_index]
        if splits.current_loop < split.loops:
            return split.dummy_flag
        if split_index >= len(splits.list) - 1:
            return False
        return splits.list[split_index + 1].dummy_flag

    def _request_next_split_preserving_recording_on_dummy(self) -> None:
        if self._current_split_is_dummy() or self._next_split_is_dummy():
            self._splitter.continue_recording = True
        self._request_next_split()

    def _livesplit_undo_suppressed(self) -> bool:
        return self._viewing_reset_image() or self._current_split_is_dummy()

    def _livesplit_skip_suppressed(self) -> bool:
        return (
            self._viewing_reset_image()
            or self._on_first_split_image()
            or self._current_split_is_dummy()
        )

    def _notify_livesplit(self, command: str, suppressed: bool) -> None:
        if not suppressed:
            self._lso.send(command)

    def _dismiss_reset_overlay_if_showing(self) -> bool:
        if not self._viewing_reset_image():
            return False
        self._hide_reset_image_display()
        return True

    def _pilgrim_undo(self) -> None:
        if self._dismiss_reset_overlay_if_showing():
            return
        self._request_previous_split()

    def _pilgrim_skip(self) -> None:
        if self._dismiss_reset_overlay_if_showing():
            return
        self._request_next_split_preserving_recording_on_dummy()

    def _manual_undo(self, *, via_button: bool = False) -> None:
        if self._lso.linked:
            self._notify_livesplit("undoSplit", self._livesplit_undo_suppressed())
            self._lso.after_manual_navigation()
            self._pilgrim_undo()
            return
        if via_button:
            key_code = settings.get_str("UNDO_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
                return
        self._pilgrim_undo()

    def _manual_skip(self, *, via_button: bool = False) -> None:
        self._prepare_skip_recording_flags()
        if self._lso.linked:
            self._notify_livesplit("skipSplit", self._livesplit_skip_suppressed())
            self._lso.after_manual_navigation()
            self._pilgrim_skip()
            return
        if via_button:
            key_code = settings.get_str("SKIP_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
                return
        self._pilgrim_skip()

    def _manual_reset(self, *, via_button: bool = False) -> None:
        if self._lso.linked:
            self._lso.send("reset")
            self._lso.after_manual_navigation()
        elif via_button:
            key_code = settings.get_str("RESET_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
                return
        self._request_reset_splits()

    def _autosplit_normal_split(self) -> None:
        if self._lso.linked and not self._lso.autosplit_may_send():
            self._request_next_split()
            return
        if self._lso.send("splitOrStart"):
            self._request_next_split()
            return
        press_hotkey_or_fallback(
            settings.get_str("SPLIT_HOTKEY_CODE"),
            self._keyboard.press_and_release,
            focus_window=self._application.focusWindow(),
            global_hotkeys_enabled=settings.get_bool("GLOBAL_HOTKEYS_ENABLED"),
            fallback=self._request_next_split,
        )

    def _autosplit_reset(self) -> None:
        if self._lso.linked:
            self._lso.send("reset")
            self._lso.after_manual_navigation()
            self._request_reset_splits()
            return
        press_hotkey_or_fallback(
            settings.get_str("RESET_HOTKEY_CODE"),
            self._keyboard.press_and_release,
            focus_window=self._application.focusWindow(),
            global_hotkeys_enabled=settings.get_bool("GLOBAL_HOTKEYS_ENABLED"),
            fallback=self._request_reset_splits,
        )

    def _prepare_skip_recording_flags(self) -> None:
        split_index = self._splitter.splits.current_image_index
        if split_index is None:
            return
        split = self._splitter.splits.list[split_index]
        if split.dummy_flag:
            self._splitter.continue_recording = True
        else:
            self._splitter.save_recording = True

    def _clear_dialog_focus_after_show(self, dlg: QDialog) -> None:
        """Clear Qt's automatically assigned initial focus in custom dialogs."""

        def clear_focus() -> None:
            focused = QApplication.focusWidget()
            if focused is not None and (focused is dlg or dlg.isAncestorOf(focused)):
                focused.clearFocus()
            dlg.setFocus(Qt.OtherFocusReason)

        dlg.setFocusPolicy(Qt.StrongFocus)
        QTimer.singleShot(0, clear_focus)

    def _strip_layout_settings_tuple(self) -> Tuple[bool, str, int, int, str]:
        """Snapshot settings that drive main-window geometry and strip typography.

        Used to avoid re-running layout/typography on profile load when nothing
        layout-related changed (prevents strip controls from resizing/shifting).
        """
        return (
            settings.get_bool("SHOW_MIN_VIEW"),
            settings.get_str("ASPECT_RATIO"),
            settings.get_int("FRAME_WIDTH"),
            settings.get_int("FRAME_HEIGHT"),
            settings.get_str("THEME"),
        )

    def _apply_profile_runtime_state(
        self,
        payload: dict,
        *,
        view_layout_changed: bool,
        theme_changed: bool,
    ) -> None:
        self._poller.setInterval(self._get_interval())
        self._splitter.target_fps = settings.get_int("FPS")
        self._video_crop.sync_from_settings()
        self._splitter.splits.set_default_threshold()
        self._splitter.splits.set_default_delay()
        self._splitter.splits.set_default_pause()
        if view_layout_changed:
            self._splitter.splits.resize_images()
            self._set_main_window_layout()
        elif theme_changed:
            self._apply_strip_typography()
        style = self._get_style_sheet()
        self._settings_window.setStyleSheet(style)
        self._apply_theme_icons()
        self._main_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )
        self._main_window.show()
        self._set_button_and_label_text(
            truncate=self._layout_uses_truncated_control_text()
        )
        self._update_pause_button()
        split_meta = payload.get("split_dir")
        if isinstance(split_meta, dict):
            self._profiles.resolve_split_dir_after_load(split_meta)
        self._set_split_directory_box_text()
        self._reset_settings()
        self._request_reset_splits()
        if self._splitter.capture_thread.is_alive():
            self._splitter.restart()

    def _wire_split_override_controls(self) -> None:
        mw = self._main_window
        # Threshold / delay / loop / pause: apply split filename + settings only when
        # the user leaves the field or presses Enter — not on every keystroke.
        for spin in (
            mw.split_threshold_spin,
            mw.split_delay_spin,
            mw.split_loop_spin,
            mw.split_pause_spin,
        ):
            spin.editingFinished.connect(self._on_split_override_changed)
        mw.split_type_dummy_action.toggled.connect(
            lambda _checked: self._on_split_override_changed()
        )
        mw.split_type_below_action.toggled.connect(
            lambda _checked: self._on_split_override_changed()
        )

    def _set_split_type_toggle_text(self) -> None:
        return

    @staticmethod
    def _pixmap_for_display_label(pixmap: QPixmap, label: QLabel) -> QPixmap:
        """Scale pixmap to the label size at the screen device pixel ratio."""
        if pixmap.isNull():
            return pixmap
        lw, lh = label.width(), label.height()
        if lw < 2 or lh < 2:
            return pixmap
        dpr = float(label.devicePixelRatioF())
        tw = max(1, int(round(lw * dpr)))
        th = max(1, int(round(lh * dpr)))
        if pixmap.width() != tw or pixmap.height() != th:
            pixmap = pixmap.scaled(
                tw, th, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        pixmap.setDevicePixelRatio(dpr)
        return pixmap

    def _apply_video_viewport_geometry(self, press_offset: int = 0) -> None:
        """Place video widgets from the stored layout rect (+ optional press nudge)."""
        if self._video_viewport_base is None:
            return
        geometry = self._video_viewport_base.translated(press_offset, press_offset)
        mw = self._main_window
        mw.video_viewport_border.setGeometry(geometry.adjusted(-1, -1, 1, 1))
        mw.video_display.setGeometry(geometry)
        mw.video_burst_overlay.setGeometry(geometry)

    def _set_video_viewport_geometry(self, geometry: QRect) -> None:
        """Remember and apply video pane geometry (resets press-offset drift)."""
        self._video_viewport_base = QRect(geometry)
        self._apply_video_viewport_geometry(0)
        self._main_window.video_display.adjusted = False

    def _apply_split_viewport_geometry(self, press_offset: int = 0) -> None:
        """Place split widgets from the stored layout rect (+ optional press nudge)."""
        if self._split_viewport_base is None:
            return
        geometry = self._split_viewport_base.translated(press_offset, press_offset)
        mw = self._main_window
        mw.split_viewport_border.setGeometry(geometry.adjusted(-1, -1, 1, 1))
        mw.split_display.setGeometry(geometry)
        mw.split_overlay.setGeometry(geometry)

    def _set_split_viewport_geometry(self, geometry: QRect) -> None:
        """Remember and apply split pane geometry (resets press-offset drift)."""
        self._split_viewport_base = QRect(geometry)
        self._apply_split_viewport_geometry(0)
        self._main_window.split_display.adjusted = False

    def _place_video_column_stats_and_screenshot_row(
        self,
        video_viewport: QRect,
        row1: int,
        row2: int,
        *,
        gap_stats_to_screenshot: int,
        screenshot_w: int,
        center_nudge_x: int = 0,
    ) -> None:
        """Place Sim/High/Thr + screenshot/reconnect centered under ``video_viewport``."""
        block_w = VIDEO_COL_STATS_SPAN_W + gap_stats_to_screenshot + screenshot_w
        block_left = (
            video_viewport.x() + (video_viewport.width() - block_w) // 2 - center_nudge_x
        )
        p_label_x = block_left
        p_value_x = block_left + VIDEO_COL_STATS_VALUE_X
        p_pct_x = block_left + VIDEO_COL_STATS_PCT_X
        sx = block_left + VIDEO_COL_STATS_SPAN_W + gap_stats_to_screenshot
        row_h = VIDEO_COL_STATS_ROW_H
        step = VIDEO_COL_STATS_ROW_STEP
        mw = self._main_window
        mw.match_percent_label.setGeometry(QRect(p_label_x, row1, VIDEO_COL_STATS_LABEL_W, row_h))
        mw.highest_percent_label.setGeometry(
            QRect(p_label_x, row1 + step, VIDEO_COL_STATS_LABEL_W, row_h)
        )
        mw.threshold_percent_label.setGeometry(
            QRect(p_label_x, row1 + 2 * step, VIDEO_COL_STATS_LABEL_W, row_h)
        )
        mw.match_percent.setGeometry(QRect(p_value_x, row1, 46, row_h))
        mw.highest_percent.setGeometry(QRect(p_value_x, row1 + step, 46, row_h))
        mw.threshold_percent.setGeometry(QRect(p_value_x, row1 + 2 * step, 46, row_h))
        mw.percent_sign_1.setGeometry(QRect(p_pct_x, row1, 21, row_h))
        mw.percent_sign_2.setGeometry(QRect(p_pct_x, row1 + step, 21, row_h))
        mw.percent_sign_3.setGeometry(QRect(p_pct_x, row1 + 2 * step, 21, row_h))
        self._layout_screenshot_burst_controls(
            QRect(sx, row1, screenshot_w, VIDEO_COL_SCREENSHOT_H)
        )
        mw.reconnect_button.setGeometry(QRect(sx, row2, screenshot_w, VIDEO_COL_SCREENSHOT_H))

    def _place_split_column_bottom_controls(
        self,
        split_viewport: QRect,
        row1: int,
        row2: int,
        *,
        pause_w: int,
        reset_w: int,
        gap_pause_to_reset: int,
        undo_w: int,
        skip_w: int,
    ) -> None:
        """Pause / reset / undo / skip centered under the split pane.

        ``gap_pause_to_reset`` matches the stats→screenshot gap on the video column.
        """
        cluster_w = pause_w + gap_pause_to_reset + reset_w
        pause_x = split_viewport.x() + (split_viewport.width() - cluster_w) // 2
        reset_x = pause_x + pause_w + gap_pause_to_reset
        skip_x = pause_x + undo_w + BOTTOM_ADJ_PAIR_GAP_PX
        row_h = 41
        mw = self._main_window
        mw.pause_button.setGeometry(QRect(pause_x, row1, pause_w, row_h))
        mw.reset_button.setGeometry(QRect(reset_x, row1, reset_w, 91))
        mw.undo_button.setGeometry(QRect(pause_x, row2, undo_w, row_h))
        mw.skip_button.setGeometry(QRect(skip_x, row2, skip_w, row_h))

    def _place_split_column_from_preset(
        self,
        split_viewport: QRect,
        row1: int,
        row2: int,
        preset: SplitColumnBottomPreset,
    ) -> None:
        self._place_split_column_bottom_controls(
            split_viewport,
            row1,
            row2,
            pause_w=preset.pause_w,
            reset_w=preset.reset_w,
            gap_pause_to_reset=preset.gap_pause_to_reset,
            undo_w=preset.undo_w,
            skip_w=preset.skip_w,
        )

    def _place_video_column_from_preset(
        self,
        video_viewport: QRect,
        row1: int,
        row2: int,
        preset: VideoColumnBottomPreset,
    ) -> None:
        self._place_video_column_stats_and_screenshot_row(
            video_viewport,
            row1,
            row2,
            gap_stats_to_screenshot=preset.gap_stats_to_screenshot,
            screenshot_w=preset.screenshot_w,
            center_nudge_x=preset.center_nudge_x,
        )

    def _apply_video_column_layout(
        self,
        preset: AspectLayoutPreset,
        video_viewport: QRect,
        row1: int,
        row2: int,
        left: int,
    ) -> None:
        vc = preset.video_column
        self._place_video_column_from_preset(video_viewport, row1, row2, vc)

    def _sync_split_override_controls(self) -> None:
        splits = self._splitter.splits
        idx = splits.current_image_index
        if idx is None or idx >= len(splits.list):
            self._main_window.split_threshold_spin.setEnabled(False)
            self._main_window.split_delay_spin.setEnabled(False)
            self._main_window.split_loop_spin.setEnabled(False)
            self._main_window.split_pause_spin.setEnabled(False)
            self._main_window.split_type_menu_button.setEnabled(False)
            return
        self._main_window.split_threshold_spin.setEnabled(True)
        self._main_window.split_delay_spin.setEnabled(True)
        self._main_window.split_loop_spin.setEnabled(True)
        self._main_window.split_pause_spin.setEnabled(True)
        self._main_window.split_type_menu_button.setEnabled(True)
        split = splits.list[idx]
        key = (idx, split.name)
        if self._split_override_sync_key == key:
            return
        threshold_match = re.search(r"_\((.+?)\)", split.name)
        delay_match = re.search(r"_\#(.+?)\#", split.name)
        loops_match = re.search(r"_\@(.+?)\@", split.name)
        pause_match = re.search(r"_\[(.+?)\]", split.name)
        flags_match = re.search(r"\{(.+?)\}", split.name)

        threshold_value = 0.0
        if threshold_match and str(threshold_match[1]).replace(".", "", 1).isdigit():
            threshold_value = float(threshold_match[1])

        delay_value = 0.0
        if delay_match and str(delay_match[1]).replace(".", "", 1).isdigit():
            delay_value = float(delay_match[1])

        loops_value = 0
        if loops_match and loops_match[1].isdigit():
            loops_value = int(loops_match[1])

        pause_value = 0.0
        if pause_match and str(pause_match[1]).replace(".", "", 1).isdigit():
            pause_value = float(pause_match[1])
        flags = flags_match[1] if flags_match is not None else ""

        self._split_override_guard = True
        try:
            self._main_window.split_threshold_spin.setValue(round(threshold_value, 1))
            self._main_window.split_delay_spin.setValue(round(delay_value, 1))
            self._main_window.split_loop_spin.setValue(loops_value)
            self._main_window.split_pause_spin.setValue(round(pause_value, 1))
            self._main_window.split_type_dummy_action.setChecked("d" in flags)
            self._main_window.split_type_below_action.setChecked("b" in flags)
            self._split_override_sync_key = key
        finally:
            self._split_override_guard = False

    def _format_float_for_name(self, value: float) -> str:
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text if text else "0"

    def _on_split_override_changed(self) -> None:
        if self._split_override_guard:
            return
        splits = self._splitter.splits
        idx = splits.current_image_index
        if idx is None or idx >= len(splits.list):
            return
        split = splits.list[idx]
        old_path = Path(split._path)
        stem = old_path.stem
        stem = re.sub(r"_\#(.+?)\#", "", stem)
        stem = re.sub(r"_\((.+?)\)", "", stem)
        stem = re.sub(r"_\@(.+?)\@", "", stem)
        stem = re.sub(r"_\[(.+?)\]", "", stem)
        stem = re.sub(r"_\{(.+?)\}", "", stem)
        stem = re.sub(r"\{(.+?)\}", "", stem)
        stem = re.sub(r"__+", "_", stem).rstrip("_")

        threshold = float(self._main_window.split_threshold_spin.value())
        delay = float(self._main_window.split_delay_spin.value())
        loops = int(self._main_window.split_loop_spin.value())
        pause = float(self._main_window.split_pause_spin.value())
        flags = ""
        if self._main_window.split_type_below_action.isChecked():
            flags += "b"
        if self._main_window.split_type_dummy_action.isChecked():
            flags += "d"

        if flags:
            stem += f"_{{{flags}}}"

        if delay > 0:
            stem += f"_#{self._format_float_for_name(delay)}#"
        if threshold > 0:
            stem += f"_({self._format_float_for_name(threshold)})"
        if loops > 0:
            stem += f"_@{loops}@"
        if pause > 0:
            stem += f"_[{self._format_float_for_name(pause)}]"

        new_path = old_path.with_name(f"{stem}{old_path.suffix}")
        if new_path == old_path:
            return
        if new_path.exists() and new_path != old_path:
            QMessageBox.warning(
                self._main_window,
                "Cannot update split filename",
                f"Target filename already exists:\n{new_path.name}",
            )
            self._sync_split_override_controls()
            return
        try:
            old_path.replace(new_path)
        except OSError:
            QMessageBox.warning(
                self._main_window,
                "Could not rename split",
                "Failed to apply threshold/delay/loop override.",
            )
            self._sync_split_override_controls()
            return

        old_idx = idx
        self._request_reset_splits()
        if self._splitter.splits.list:
            self._splitter.splits.current_image_index = min(
                old_idx, len(self._splitter.splits.list) - 1
            )
            self._splitter.splits.current_loop = 1
        self._redraw_split_labels = True
        self._split_override_sync_key = None
        self._sync_split_override_controls()

    def _attempt_undo_hotkey(self) -> None:
        """Undo button: sync LiveSplit One when connected, else hotkey or Pilgrim."""
        self._manual_undo(via_button=True)

    def _attempt_skip_hotkey(self) -> None:
        """Skip button: sync LiveSplit One when connected, else hotkey or Pilgrim."""
        self._manual_skip(via_button=True)

    def _attempt_reset_hotkey(self) -> None:
        """Reset button: sync LiveSplit One when connected, else hotkey or Pilgrim."""
        self._manual_reset(via_button=True)

    def _request_previous_split(self) -> None:
        """Move to the previous split image (see ui.split_navigation)."""
        self._redraw_split_labels = True
        navigate_to_previous_split(self._splitter)

    def _request_next_split(self) -> None:
        """Move to the next split image (see ui.split_navigation)."""
        if navigate_to_next_split(
            self._splitter,
            continue_recording=self._splitter.continue_recording,
            split_hotkey_pressed=self._split_hotkey_pressed,
        ):
            self._redraw_split_labels = True

    def _request_reset_splits(self) -> None:
        """Tell splitter.splits to call reset_split_images, and ask
        splitter._look_for_split to reset its flags if necessary.

        Kill splitter's non-capture threads (this allows the splitter to exit
        gracefully if the split image directory has changed to an empty
        directory, for example). Restarts the threads if the split list isn't
        empty and if video is running.
        """
        # Kill recording
        self._splitter.safe_exit_record_thread()

        self._redraw_split_labels = True
        self._splitter.safe_exit_compare_split_thread()
        self._splitter.safe_exit_compare_reset_thread()
        self._splitter.splits.reset_split_images()

        if (
            len(self._splitter.splits.list) > 0
            and self._splitter.capture_thread.is_alive()
        ):
            self._splitter.restart_compare_split_thread()
            if self._splitter.splits.reset_image is not None:
                self._splitter.restart_compare_reset_thread()

        # Restart recording
        self._splitter.restart_record_thread()

    def _set_split_dir_path(self) -> None:
        """Prompt the user to select a split image directory, then open the new
        directory in a threadsafe manner.

        If the directory exists and is different from the last one, check if
        the dir is within the user's home directory. If not, show an error msg
        and re-run the method.

        Otherwise, change `LAST_IMAGE_DIR` to the new choice. Then reset splits
        so the new ones show up.
        """
        path = QFileDialog.getExistingDirectory(
            self._main_window,
            "Select splits folder",
            settings.get_str("LAST_IMAGE_DIR"),
        )
        if len(path) > 1 and path != settings.get_str("LAST_IMAGE_DIR"):
            if not settings.path_is_within_home(path):
                msg = self._main_window.err_invalid_dir_msg
                msg.setStyleSheet(self._get_style_sheet())
                msg.show()
                return self._set_split_dir_path()

            settings.set_value("LAST_IMAGE_DIR", path)
            self._set_split_directory_box_text()
            self._request_reset_splits()

    def _set_record_dir_path(self) -> None:
        """Prompt the user to select a recordings directory.

        If the directory exists and is different from the last one, check if
        the dir is within the user's home directory. If not, show an error msg
        and re-run the method.

        Otherwise, change `LAST_RECORD_DIR` to the new choice.
        """
        path = QFileDialog.getExistingDirectory(
            self._main_window,
            "Select recordings folder",
            settings.get_str("LAST_RECORD_DIR"),
        )
        if len(path) > 1 and path != settings.get_str("LAST_RECORD_DIR"):
            if not settings.path_is_within_home(path):
                msg = self._main_window.err_invalid_dir_msg
                msg.setStyleSheet(self._get_style_sheet())
                msg.show()
                return self._set_record_dir_path()

            settings.set_value("LAST_RECORD_DIR", path)

    def _set_split_directory_box_text(self) -> None:
        """Convert the split image directory path to an elided string,
        based on the current size of main window's split directory line edit.
        """
        box = self._main_window.split_directory_box
        path = settings.get_str("LAST_IMAGE_DIR")
        elided_path = box.fontMetrics().elidedText(
            f" {path} ",
            Qt.ElideRight,
            max(1, box.width() - 16),
        )
        box.setText(elided_path)
        box.setCursorPosition(0)

    def update_available_msg_action(self, button: QAbstractButton):
        """React to button press in _main_window.update_available_msg.

        Args:
            button (QAbstractButton): The button that was pressed.
        """
        # "Don't ask again" was clicked -- stop checking for updates
        if button.text() == self._main_window.never_button_txt:
            settings.set_value("CHECK_FOR_UPDATES", False)

        # "Open" was clicked -- open the GitHub releases page
        elif button.text() == self._main_window.open_button_txt:
            self._open_url(f"{settings.REPO_URL}releases/latest")

        else:
            self._main_window.update_available_msg.close()

    def _show_reset_image_display(self) -> None:
        """Show the reset image, if it exists, over the current split image.

        Also force the match percent chart to show the match percents for the
        reset image.
        """
        reset_image = self._splitter.splits.reset_image
        split_display = self._main_window.split_display
        match_percent_label = self._main_window.match_percent_label
        split_name_label = self._main_window.split_name_label
        loop_label = self._main_window.split_loop_label
        loop_label_reset_text = self._main_window.split_loop_label_reset_txt

        # Set split name / loop label to reset image info
        split_name_label.setText(reset_image.name)
        loop_label.setText(loop_label_reset_text)

        # Set split image to reset image
        split_display.setPixmap(
            self._pixmap_for_display_label(reset_image.pixmap, split_display)
        )

        # Show reset image match percents instead of current split
        if settings.get_str("ASPECT_RATIO") != "4:3 (320x240)":
            match_percent_label.setText(self._main_window.match_reset_percent_txt)
        self._show_reset_percents = True

    def _hide_reset_image_display(self) -> None:
        """Remove reset image / info from UI."""
        match_percent_label = self._main_window.match_percent_label

        if settings.get_str("ASPECT_RATIO") == "4:3 (320x240)":
            match_percent_label.setText(self._main_window.match_percent_short_txt)
        else:
            match_percent_label.setText(self._main_window.match_percent_long_txt)

        self._redraw_split_labels = True  # Force UI to show split image again
        self._show_reset_percents = False

    def _exec_settings_window(self) -> None:
        """Set up and open the settings window UI."""
        self._reset_settings()
        # On some platforms, the main window hides the settings window if we
        # don't set this flag
        self._settings_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )
        self._settings_window.exec()

    def _reset_settings(self) -> None:
        """Read settings from `settings.py` and write them into the settings
        menu UI.
        """
        # Spinboxes
        for spinbox, value in {
            self._settings_window.fps_spinbox: settings.get_int("FPS"),
            self._settings_window.threshold_spinbox: str(
                float(settings.get_float("DEFAULT_THRESHOLD") * 100)
            ),
            self._settings_window.decimals_spinbox: settings.get_int(
                "MATCH_PERCENT_DECIMALS"
            ),
            self._settings_window.delay_spinbox: settings.get_float("DEFAULT_DELAY"),
            self._settings_window.pause_spinbox: settings.get_float("DEFAULT_PAUSE"),
        }.items():
            spinbox.setProperty("value", value)

        # Checkboxes
        for checkbox, value in {
            self._settings_window.open_screenshots_checkbox: settings.get_bool(
                "OPEN_SCREENSHOT_ON_CAPTURE"
            ),
            self._settings_window.start_with_video_checkbox: settings.get_bool(
                "START_WITH_VIDEO"
            ),
            self._settings_window.global_hotkeys_checkbox: settings.get_bool(
                "GLOBAL_HOTKEYS_ENABLED"
            ),
            self._settings_window.check_for_updates_checkbox: settings.get_bool(
                "CHECK_FOR_UPDATES"
            ),
            self._settings_window.always_on_top_checkbox: settings.get_bool(
                "ALWAYS_ON_TOP"
            ),
        }.items():
            if value:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        # Hotkeys
        for hotkey_box, values in {
            self._settings_window.split_hotkey_box: (
                settings.get_str("SPLIT_HOTKEY_NAME"),
                settings.get_str("SPLIT_HOTKEY_CODE"),
            ),
            self._settings_window.reset_hotkey_box: (
                settings.get_str("RESET_HOTKEY_NAME"),
                settings.get_str("RESET_HOTKEY_CODE"),
            ),
            self._settings_window.pause_hotkey_box: (
                settings.get_str("PAUSE_HOTKEY_NAME"),
                settings.get_str("PAUSE_HOTKEY_CODE"),
            ),
            self._settings_window.undo_hotkey_box: (
                settings.get_str("UNDO_HOTKEY_NAME"),
                settings.get_str("UNDO_HOTKEY_CODE"),
            ),
            self._settings_window.skip_hotkey_box: (
                settings.get_str("SKIP_HOTKEY_NAME"),
                settings.get_str("SKIP_HOTKEY_CODE"),
            ),
            self._settings_window.previous_hotkey_box: (
                settings.get_str("PREV_HOTKEY_NAME"),
                settings.get_str("PREV_HOTKEY_CODE"),
            ),
            self._settings_window.next_hotkey_box: (
                settings.get_str("NEXT_HOTKEY_NAME"),
                settings.get_str("NEXT_HOTKEY_CODE"),
            ),
            self._settings_window.screenshot_hotkey_box: (
                settings.get_str("SCREENSHOT_HOTKEY_NAME"),
                settings.get_str("SCREENSHOT_HOTKEY_CODE"),
            ),
            self._settings_window.save_peak_hotkey_box: (
                settings.get_str("SAVE_PEAK_HOTKEY_NAME"),
                settings.get_str("SAVE_PEAK_HOTKEY_CODE"),
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_box: (
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_NAME"),
                settings.get_str("TOGGLE_HOTKEYS_HOTKEY_CODE"),
            ),
        }.items():
            name, code = values
            if name == "None":
                name = ""
            if code == "None":
                code = ""
            hotkey_box.setText(name)
            hotkey_box.key_name = name
            hotkey_box.key_code = code

        # Comboboxes
        aspect_ratio = settings.get_str("ASPECT_RATIO")
        if aspect_ratio == "4:3 (480x360)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(0)
        elif aspect_ratio == "4:3 (320x240)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(1)
        elif aspect_ratio == "16:9 (512x288)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(2)
        elif aspect_ratio == "16:9 (432x243)":
            self._settings_window.aspect_ratio_combo_box.setCurrentIndex(3)

        theme = settings.get_str("THEME")
        if theme == "dark":
            self._settings_window.theme_combo_box.setCurrentIndex(0)
        elif theme == "light":
            self._settings_window.theme_combo_box.setCurrentIndex(1)

    def _save_settings(self) -> bool:
        """Write the current values in settings_window to settings, and update
        program variables as needed.

        Returns:
            bool: True when settings were saved successfully, else False.
        """
        conflict = self._detect_hotkey_conflict()
        if conflict is not None:
            a_name, b_name, key_name = conflict
            QMessageBox.warning(
                self._settings_window,
                "Hotkey conflict",
                (
                    f"'{a_name}' and '{b_name}' use the same hotkey ({key_name}).\n\n"
                    "Please assign unique hotkeys before saving."
                ),
            )
            return False

        # Spinboxes
        for spinbox, setting_string in {
            self._settings_window.fps_spinbox: "FPS",
            self._settings_window.threshold_spinbox: "DEFAULT_THRESHOLD",
            self._settings_window.decimals_spinbox: "MATCH_PERCENT_DECIMALS",
            self._settings_window.delay_spinbox: "DEFAULT_DELAY",
            self._settings_window.pause_spinbox: "DEFAULT_PAUSE",
        }.items():
            if spinbox == self._settings_window.threshold_spinbox:
                value = float(spinbox.value()) / 100
            else:
                value = spinbox.value()
            settings.set_value(setting_string, value)

            # Send new FPS value to controller and splitter
            if spinbox == self._settings_window.fps_spinbox:
                self._poller.setInterval(self._get_interval())
                self._splitter.target_fps = value

        self._splitter.splits.set_default_threshold()
        self._splitter.splits.set_default_delay()
        self._splitter.splits.set_default_pause()

        # Checkboxes
        for checkbox, setting_string in {
            self._settings_window.open_screenshots_checkbox: "OPEN_SCREENSHOT_ON_CAPTURE",
            self._settings_window.start_with_video_checkbox: "START_WITH_VIDEO",
            self._settings_window.global_hotkeys_checkbox: "GLOBAL_HOTKEYS_ENABLED",
            self._settings_window.check_for_updates_checkbox: "CHECK_FOR_UPDATES",
            self._settings_window.always_on_top_checkbox: "ALWAYS_ON_TOP",
        }.items():
            if checkbox.checkState() == 0:
                value = False
            else:
                value = True
            settings.set_value(setting_string, value)

        self._main_window.setWindowFlag(
            Qt.WindowStaysOnTopHint, settings.get_bool("ALWAYS_ON_TOP")
        )
        # Required, since setting the above flag hides the window by default
        self._main_window.show()
        # Hack to make the transition look less awkward
        self._settings_window.show()

        # Hotkeys
        for hotkey, setting_strings in {
            self._settings_window.split_hotkey_box: (
                "SPLIT_HOTKEY_NAME",
                "SPLIT_HOTKEY_CODE",
            ),
            self._settings_window.reset_hotkey_box: (
                "RESET_HOTKEY_NAME",
                "RESET_HOTKEY_CODE",
            ),
            self._settings_window.pause_hotkey_box: (
                "PAUSE_HOTKEY_NAME",
                "PAUSE_HOTKEY_CODE",
            ),
            self._settings_window.undo_hotkey_box: (
                "UNDO_HOTKEY_NAME",
                "UNDO_HOTKEY_CODE",
            ),
            self._settings_window.skip_hotkey_box: (
                "SKIP_HOTKEY_NAME",
                "SKIP_HOTKEY_CODE",
            ),
            self._settings_window.previous_hotkey_box: (
                "PREV_HOTKEY_NAME",
                "PREV_HOTKEY_CODE",
            ),
            self._settings_window.next_hotkey_box: (
                "NEXT_HOTKEY_NAME",
                "NEXT_HOTKEY_CODE",
            ),
            self._settings_window.screenshot_hotkey_box: (
                "SCREENSHOT_HOTKEY_NAME",
                "SCREENSHOT_HOTKEY_CODE",
            ),
            self._settings_window.save_peak_hotkey_box: (
                "SAVE_PEAK_HOTKEY_NAME",
                "SAVE_PEAK_HOTKEY_CODE",
            ),
            self._settings_window.toggle_global_hotkeys_hotkey_box: (
                "TOGGLE_HOTKEYS_HOTKEY_NAME",
                "TOGGLE_HOTKEYS_HOTKEY_CODE",
            ),
        }.items():
            name, code = hotkey.text(), hotkey.key_code
            settings.set_value(setting_strings[0], name)
            settings.set_value(setting_strings[1], code)

        # Comboboxes --
        # Only update these settings if the value changed, since calling
        # resize_images / _set_main_window_layout and setting style is expensive
        aspect_ratio = self._settings_window.aspect_ratio_combo_box.currentText()
        if aspect_ratio != settings.get_str("ASPECT_RATIO"):
            if aspect_ratio == "4:3 (480x360)":
                settings.set_value("ASPECT_RATIO", "4:3 (480x360)")
                settings.set_value("FRAME_WIDTH", 480)
                settings.set_value("FRAME_HEIGHT", 360)
            elif aspect_ratio == "4:3 (320x240)":
                settings.set_value("ASPECT_RATIO", "4:3 (320x240)")
                settings.set_value("FRAME_WIDTH", 320)
                settings.set_value("FRAME_HEIGHT", 240)
            elif aspect_ratio == "16:9 (512x288)":
                settings.set_value("ASPECT_RATIO", "16:9 (512x288)")
                settings.set_value("FRAME_WIDTH", 512)
                settings.set_value("FRAME_HEIGHT", 288)
            elif aspect_ratio == "16:9 (432x243)":
                settings.set_value("ASPECT_RATIO", "16:9 (432x243)")
                settings.set_value("FRAME_WIDTH", 432)
                settings.set_value("FRAME_HEIGHT", 243)
            self._splitter.splits.resize_images()
            self._set_main_window_layout()

        theme = self._settings_window.theme_combo_box.currentText()
        if theme != settings.get_str("THEME"):
            if theme == "light":
                settings.set_value("THEME", "light")
                style = style_sheet_light
            else:
                settings.set_value("THEME", "dark")
                style = style_sheet_dark
            self._settings_window.setStyleSheet(style)
            self._apply_theme_icons()
            self._apply_strip_typography()
        return True

    def _save_settings_and_close(self) -> None:
        if self._save_settings():
            self._settings_window.done(0)

    def _detect_hotkey_conflict(self) -> Optional[Tuple[str, str, str]]:
        """Return first conflicting pair of hotkeys by code, else None."""
        bindings = [
            ("Split", self._settings_window.split_hotkey_box),
            ("Reset", self._settings_window.reset_hotkey_box),
            ("Pause", self._settings_window.pause_hotkey_box),
            ("Undo", self._settings_window.undo_hotkey_box),
            ("Skip", self._settings_window.skip_hotkey_box),
            ("Previous", self._settings_window.previous_hotkey_box),
            ("Next", self._settings_window.next_hotkey_box),
            ("Screenshot", self._settings_window.screenshot_hotkey_box),
            (SNAP_PEAK_HOTKEY_LABEL, self._settings_window.save_peak_hotkey_box),
            ("Toggle Global Hotkeys", self._settings_window.toggle_global_hotkeys_hotkey_box),
        ]
        seen: dict = {}
        for label, box in bindings:
            code = str(box.key_code or "").strip()
            name = str(box.text() or "").strip()
            if not code:
                continue
            if code in seen:
                prev_label, prev_name = seen[code]
                show_name = name or prev_name or code
                return prev_label, label, show_name
            seen[code] = (label, name)
        return None

    def _layout_screenshot_burst_controls(self, shot_rect: QRect) -> None:
        """Place the screenshot button and settings (gear) control within ``shot_rect``."""
        mw = self._main_window
        gap = BOTTOM_ADJ_PAIR_GAP_PX
        h = max(1, shot_rect.height())
        x0, y0 = shot_rect.x(), shot_rect.y()
        total = max(1, shot_rect.width())

        sb = mw.screenshot_button
        tb = mw.screenshot_settings_button
        tb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        side = h
        shot_w = max(1, total - gap - side)
        sb.setGeometry(QRect(x0, y0, shot_w, h))

        sbr = sb.geometry()
        gear_side = max(1, sbr.height())
        tb.setGeometry(QRect(sbr.right() + gap, sbr.y(), gear_side, gear_side))

        _ico = max(12, min(gear_side - 8, int(gear_side * 0.42)))
        tb.setIconSize(QSize(_ico, _ico))
        tb.raise_()

    def get_file_number(self, dir: str) -> str:
        """Return the lowest number not already used as a .png filename prefix.

        Args:
            dir (str): The target directory for the file.

        Returns:
            file_number (str): The lowest number as a zero-padded string.
        """
        path = Path(self._screenshot.paths_for_count(dir, 1)[0])
        return path.name.split("_", 1)[0]

    def _open_file_or_dir(self, path: str) -> None:
        """Enables cross-platform opening of a file or directory.

        If path points to a file, the file opens with the default application.
        If path points to a dir, the dir opens in the OS's file explorer.

        If the path doesn't exist, show an error message and return.

        On Linux, we have to spawn a child process that isn't using root, due
        to issues caused when trying to open the file explorer as root. To do
        that, we get the username from the environment variable $SUPER_USER and
        pass that value to subprocess.

        Args:
            path (str): The file to open.
        """
        if not Path(path).exists():
            msg = self._main_window.err_not_found_msg
            msg.setStyleSheet(self._get_style_sheet())
            msg.show()
            # Close message box after 10 seconds
            QTimer.singleShot(10000, lambda: msg.done(0))
            return

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            non_root_user = os.environ.get("SUDO_USER")
            subprocess.Popen(["xdg-open", path], user=non_root_user)

    def _open_url(self, url: str) -> None:
        """Open a URL using webbrowser or xdg-open, depending on platform.

        Use xdg-open on Linux so we can make sure to execute the process
        as user, not as root, to avoid crashes / permission errors.
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            webbrowser.open(url, new=0, autoraise=True)
        else:
            non_root_user = os.environ.get("SUDO_USER")
            subprocess.Popen(["xdg-open", url], user=non_root_user)

    def _get_style_sheet(self) -> str:
        """Retrieve the style sheet currently in use.

        Returns:
            str: The style sheet.
        """
        if settings.get_str("THEME") == "light":
            return style_sheet_light
        else:
            return style_sheet_dark

    def _apply_theme_icons(self) -> None:
        """Keep SVG-only icons matched to the active theme text color."""
        gear_icon_name = (
            "gear_dark.svg" if settings.get_str("THEME") == "light" else "gear_white.svg"
        )
        chevron_icon_name = (
            "chevron_down_dark.svg"
            if settings.get_str("THEME") == "light"
            else "chevron_down_white.svg"
        )
        icons_dir = paths.resources_dir() / "icons"
        self._main_window.screenshot_settings_button.setIcon(
            QIcon(str(icons_dir / gear_icon_name))
        )
        self._main_window.split_type_menu_button.setIcon(
            QIcon(str(icons_dir / chevron_icon_name))
        )

    def _toggle_record_clips(self) -> None:
        """Toggle "RECORD_CLIPS" in settings, but only if the video feed is
        currently active.
        """
        if self._splitter.capture_thread.is_alive():
            old_setting = settings.get_bool("RECORD_CLIPS")
            settings.set_value("RECORD_CLIPS", not old_setting)

            # Show recordings dest. hint when turned on
            if old_setting is False:
                self._main_window.video_info_overlay.set_text(
                    "Double click to change recordings folder"
                )

    def _set_main_window_layout(self) -> None:
        """Set the size, location, and visibility of the main window's widgets
        according to minimum view status and aspect ratio.
        """
        if settings.get_bool("SHOW_MIN_VIEW"):
            self._set_minimal_view()
        else:
            preset = LAYOUT_PRESETS.get(settings.get_str("ASPECT_RATIO"))
            if preset is not None:
                self._apply_layout_from_preset(preset)

        # Split labels will be refreshed after this call finishes
        self._redraw_split_labels = True
        # Video overlay icon will be resized after this call finishes
        self._resize_record_icon = True
        # Refresh the split directory text so it elides correctly
        self._set_split_directory_box_text()
        # Strip typography after the event loop applies setGeometry — same-call
        # shrink used stale layout mins vs FRAME_WIDTH and still drifted on aspect toggles.
        QTimer.singleShot(0, self._apply_strip_typography)

    def _apply_strip_typography(self) -> None:
        self._strip_typography.apply()

    def _compose_main_window_stylesheet(self) -> str:
        """Theme + dynamic hover borders + strip typography."""
        base_style = self._get_style_sheet()
        style_sheet = self._update_video_feed_css(base_style)
        style_sheet = self._update_split_image_css(style_sheet)
        return self._strip_typography.append_typography_css(style_sheet)

    def _set_minimal_view(self) -> None:
        """Resize and show widgets so that minimal view is displayed."""
        left = self._main_window.LEFT_EDGE_CORRECTION
        top = self._main_window.TOP_EDGE_CORRECTION
        self._main_window.previous_button.setGeometry(
            QRect(60 + left, 224 + top, 31, 31)
        )
        self._main_window.split_name_label.setGeometry(
            QRect(92 + left, 214 + top, 251, 31)
        )
        self._main_window.split_loop_label.setGeometry(
            QRect(92 + left, 239 + top, 251, 31)
        )
        self._main_window.next_button.setGeometry(QRect(344 + left, 224 + top, 31, 31))
        self._main_window.min_view_button.setGeometry(
            QRect(60 + left, 270 + top, 100, 31)
        )
        self._main_window.video_title.setGeometry(QRect(161 + left, 270 + top, 213, 31))
        self._main_window.pause_button.setGeometry(QRect(60 + left, 310 + top, 121, 31))
        self._main_window.skip_button.setGeometry(QRect(125 + left, 350 + top, 56, 31))
        self._main_window.undo_button.setGeometry(QRect(60 + left, 350 + top, 56, 31))
        self._main_window.reset_button.setGeometry(QRect(304 + left, 310 + top, 71, 71))
        self._main_window.split_override_panel.setGeometry(QRect(60 + left, 390 + top, 315, 28))
        self._main_window.match_percent_label.setGeometry(
            QRect(62 + left, 304 + top, 161, 31)
        )
        self._main_window.highest_percent_label.setGeometry(
            QRect(62 + left, 331 + top, 161, 31)
        )
        self._main_window.threshold_percent_label.setGeometry(
            QRect(62 + left, 358 + top, 161, 31)
        )
        self._main_window.match_percent.setGeometry(
            QRect(227 + left, 304 + top, 46, 31)
        )
        self._main_window.highest_percent.setGeometry(
            QRect(227 + left, 331 + top, 46, 31)
        )
        self._main_window.threshold_percent.setGeometry(
            QRect(227 + left, 358 + top, 46, 31)
        )
        self._main_window.percent_sign_1.setGeometry(
            QRect(282 + left, 304 + top, 21, 31)
        )
        self._main_window.percent_sign_2.setGeometry(
            QRect(282 + left, 331 + top, 21, 31)
        )
        self._main_window.percent_sign_3.setGeometry(
            QRect(282 + left, 358 + top, 21, 31)
        )

        self._set_nonessential_widgets_visible(False)
        self._set_button_and_label_text(truncate=True)
        self._main_window.setFixedSize(
            345, 179 + self._main_window.HEIGHT_CORRECTION
        )

    def _apply_layout_from_preset(self, preset: AspectLayoutPreset) -> None:
        """Apply chrome, viewports, and bottom rows from ``preset``."""
        apply_aspect_layout(self, preset)

    def _layout_uses_truncated_control_text(self) -> bool:
        """Return True when the current layout uses short control labels.

        Matches ``_set_min_view`` / ``_set_320x240_view`` / ``_set_432x243_view``
        (always truncate) vs full-size 480 / 512 layouts (never truncate): either
        minimal view is on, or the aspect ratio is a compact capture size.
        """
        if settings.get_bool("SHOW_MIN_VIEW"):
            return True
        return settings.get_str("ASPECT_RATIO") in (
            "4:3 (320x240)",
            "16:9 (432x243)",
        )

    def _set_button_and_label_text(self, truncate: bool) -> None:
        """Set button and label text according to aspect ratio and min view.

        Args:
            truncate (bool): If True, each widget's short text is used;
                otherwise, each widget's default (long) text is used. Callers
                should pass ``self._layout_uses_truncated_control_text()`` when
                refreshing after settings changes, not ``SHOW_MIN_VIEW`` alone.
        """
        # Min view button
        if settings.get_bool("SHOW_MIN_VIEW"):
            min_view_txt = self._main_window.min_view_full_txt
        else:
            min_view_txt = self._main_window.min_view_min_txt

        # Other buttons
        if truncate:
            if settings.get_bool("BURST_MODE_ENABLED"):
                screenshot_txt = self._main_window.screenshot_button_burst_short_txt
            else:
                screenshot_txt = self._main_window.screenshot_button_short_txt
            match_txt = self._main_window.match_percent_short_txt
            highest_txt = self._main_window.highest_percent_short_txt
            threshold_txt = self._main_window.threshold_percent_short_txt
            undo_txt = self._main_window.undo_button_short_txt
            skip_txt = self._main_window.skip_button_short_txt
            reset_txt = self._main_window.reset_button_short_txt
        else:
            if settings.get_bool("BURST_MODE_ENABLED"):
                screenshot_txt = self._main_window.screenshot_button_burst_long_txt
            else:
                screenshot_txt = self._main_window.screenshot_button_long_txt
            match_txt = self._main_window.match_percent_long_txt
            highest_txt = self._main_window.highest_percent_long_txt
            threshold_txt = self._main_window.threshold_percent_long_txt
            undo_txt = self._main_window.undo_button_long_txt
            skip_txt = self._main_window.skip_button_long_txt
            reset_txt = self._main_window.reset_button_long_txt

        self._main_window.min_view_button.setText(min_view_txt)
        self._main_window.screenshot_button.setText(screenshot_txt)
        self._main_window.match_percent_label.setText(match_txt)
        self._main_window.highest_percent_label.setText(highest_txt)
        self._main_window.threshold_percent_label.setText(threshold_txt)
        self._main_window.undo_button.setText(undo_txt)
        self._main_window.skip_button.setText(skip_txt)
        self._main_window.reset_button.setText(reset_txt)

    def _set_nonessential_widgets_visible(self, visible: bool) -> None:
        """Set widget visibility according to minimal view status.

        Widgets that are not affected by SHOW_MIN_VIEW alone may not be listed
        here, but may still only appear when minimal view is off.

        Args:
            visible (bool): If True, show all non-minimal-view widgets. If
                False, hide all non-minimal-view widgets.
        """
        self._main_window.split_directory_box.setVisible(visible)
        self._main_window.split_dir_button.setVisible(visible)
        self._main_window.next_source_button.setVisible(visible)
        self._main_window.screenshot_button.setVisible(visible)
        self._main_window.screenshot_settings_button.setVisible(visible)
        self._main_window.reconnect_button.setVisible(visible)
        self._main_window.video_viewport_border.setVisible(visible)
        self._main_window.video_display.setVisible(visible)
        self._main_window.video_crop_panel.setVisible(visible)
        self._main_window.video_info_overlay.setVisible(visible)
        self._main_window.split_viewport_border.setVisible(visible)
        self._main_window.split_display.setVisible(visible)
        self._main_window.split_override_panel.setVisible(visible)
        # Only display this when the other widgets are hidden
        self._main_window.split_info_min_label.setVisible(not visible)

    ###########
    #         #
    # Polling #
    #         #
    ###########

    def _poll(self) -> None:
        """Update the UI and splitter (should be called each frame).

        Uses information from UI, splitter, mouse, and keyboard to update UI
        and splitter. Also keeps the computer's display awake if the splitter
        is active.
        """
        try:
            self._update_video_feed()
            self._update_video_record_overlay()
            self._update_video_info_overlay()
            self._update_video_burst_overlay()
            self._update_video_title()
            self._update_split_and_video_css()
            self._update_split_image_labels()
            self._update_split_delay_suspend()
            self._update_match_percents()
            self._update_pause_button()
            self._set_buttons_and_hotkeys_enabled()
            self._react_to_hotkey_flags()
            self._react_to_settings_menu_flags()
            self._react_to_split_flags()
            self._wake_display()
        except Exception as exc:
            log_slot_error("UI poll", exc)

    def _update_video_feed(self) -> None:
        """Clear video if video is down; update video if video is alive."""
        if settings.get_bool("SHOW_MIN_VIEW"):
            return

        frame = self._splitter.frame_pixmap
        video = self._main_window.video_display

        # Video not connected, but video frame on UI
        if frame is None:
            if video.text() == "":
                video.setText(self._main_window.video_display_txt)
        # Video is connected, update it
        else:
            video.setPixmap(self._pixmap_for_display_label(frame, video))

    def _update_video_record_overlay(self) -> None:
        """Show recording symbol when RECORD_CLIPS is True and video's on."""
        overlay = self._main_window.video_record_overlay
        video_on = self._splitter.capture_thread.is_alive()

        if settings.get_bool("SHOW_MIN_VIEW") or not video_on:
            overlay.setVisible(False)

        else:

            # Resizing the pixmap is expensive, so only do it when
            # aspect ratio changes
            if self._resize_record_icon:
                self._resize_record_icon = False

                active_img = self._main_window.record_active_img
                idle_img = self._main_window.record_idle_img

                self._record_active_pixmap = QPixmap(active_img).scaled(
                    overlay.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._record_idle_pixmap = QPixmap(idle_img).scaled(
                    overlay.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            if self._splitter.recording_enabled:
                pixmap = self._record_active_pixmap
            else:
                pixmap = self._record_idle_pixmap
            overlay.setPixmap(pixmap)

            visible = settings.get_bool("RECORD_CLIPS")
            overlay.setVisible(visible)

    def _update_video_info_overlay(self) -> None:
        """Update video info overlay text using output from _record."""
        text = self._splitter.result_text
        if text is not None:
            self._main_window.video_info_overlay.set_text(text)
            self._splitter.result_text = None

    def _update_video_burst_overlay(self) -> None:
        """Grey veil over the video feed while burst capture runs (like split pause)."""
        overlay = self._main_window.video_burst_overlay
        min_view = settings.get_bool("SHOW_MIN_VIEW")

        if self._screenshot.in_progress and not min_view:
            remain = max(0.0, self._screenshot.overlay_deadline - time.monotonic())
            overlay.setText(f"Taking burst... {remain:.1f}s")
            overlay.setVisible(True)
            overlay.raise_()
        elif overlay.text() != "":
            overlay.setVisible(False)
            overlay.setText("")

    def _update_video_title(self) -> None:
        """Adjust video title depending on whether video is alive."""
        video_alive = self._splitter.capture_thread.is_alive()
        norm_live_txt = self._main_window.video_live_txt
        norm_down_txt = self._main_window.video_down_txt
        min_down_txt = self._main_window.min_video_down_txt
        min_live_txt = self._main_window.min_video_live_txt
        label = self._main_window.video_title

        if settings.get_bool("SHOW_MIN_VIEW"):
            # Video is connected, but label says it's not
            if video_alive and label.text() != min_live_txt:
                label.setText(min_live_txt)
            # Video isn't conected, but label says it is
            elif not video_alive and label.text() != min_down_txt:
                label.setText(min_down_txt)

        else:
            # Video is connected, but label says it's not
            if video_alive and label.text() != norm_live_txt:
                label.setText(norm_live_txt)
            # Video isn't connected, but label says it is
            elif not video_alive and label.text() != norm_down_txt:
                label.setText(norm_down_txt)

    def _update_split_and_video_css(self) -> None:
        """Generate new style sheet based on mouse interation with video feed
        and split image.

        Updating the style sheet ONLY when it has changed saves a ton of CPU,
        so we do that.
        """
        # Hover/click chrome moves widgets and can repaint the menu bar (macOS).
        if self._ui_chrome_updates_paused():
            return

        style_sheet = self._compose_main_window_stylesheet()

        if style_sheet != self._most_recent_style_sheet:
            self._most_recent_style_sheet = style_sheet
            self._main_window.setStyleSheet(style_sheet)

    def _update_video_feed_css(self, style_sheet: str) -> str:
        """Generate new style sheet on mouse interaction with video feed.

        Args:
            style_sheet (str): The base style sheet to which new CSS is added.

        Returns:
            str: The style sheet with modified CSS for the video feed widget.
        """
        # Don't react to mouse if video is down
        if self._splitter.capture_thread.is_alive():

            display = self._main_window.video_display

            # Clicked and hovered — nudge from stored layout rect (no move() drift).
            if display.clicked and display.hovered:
                if not display.adjusted:
                    self._apply_video_viewport_geometry(1)
                    display.adjusted = True
            else:
                if display.adjusted:
                    self._apply_video_viewport_geometry(0)
                    display.adjusted = False

        return style_sheet

    def _update_split_image_css(self, style_sheet: str) -> str:
        """Generate new style sheet on mouse interaction with video feed.

        Args:
            style_sheet (str): The base style sheet to which new CSS is added.

        Returns:
            str: The style sheet with modified CSS for the video feed widget.
        """
        reset_image = self._splitter.splits.reset_image
        if reset_image is not None:

            split_display = self._main_window.split_display
            loop_label = self._main_window.split_loop_label
            reset_label_txt = self._main_window.split_loop_label_reset_txt

            # Show or hide image depending on mouse click status
            if split_display.clicked:
                self._show_reset_image_display()
            elif loop_label.text() == reset_label_txt:
                self._hide_reset_image_display()

            if split_display.clicked and split_display.hovered:
                if not split_display.adjusted:
                    self._apply_split_viewport_geometry(1)
                    split_display.adjusted = True
            else:
                if split_display.adjusted:
                    self._apply_split_viewport_geometry(0)
                    split_display.adjusted = False

        return style_sheet

    def _update_split_image_labels(self) -> None:
        """Update split name, loops, and image."""
        current_index = self._splitter.splits.current_image_index
        current_loop = self._splitter.splits.current_loop
        split_display = self._main_window.split_display
        reset_image = self._splitter.splits.reset_image
        split_label = self._main_window.split_name_label
        loop_label = self._main_window.split_loop_label
        splits_down_txt = self._main_window.split_display_txt
        splits_min_label = self._main_window.split_info_min_label

        # No splits loaded, but UI showing split image
        if current_index is None:
            if split_display.text() != splits_down_txt:
                # Only show splits down text if reset image isn't being viewed
                if reset_image is None or not split_display.clicked:
                    split_display.setText(splits_down_txt)
                    split_label.setText("")
                    loop_label.setText("")

                # Fix min view label
                splits_min_label.setText(splits_down_txt)
                splits_min_label.raise_()  # Make sure it's not being covered
            self._split_override_sync_key = None
            self._sync_split_override_controls()

        # UI showing split but split has been changed, resized, or reset
        elif self._redraw_split_labels:
            self._redraw_split_labels = False

            current_split_image = self._splitter.splits.list[current_index]
            elided_name = split_label.fontMetrics().elidedText(
                current_split_image.name, Qt.ElideRight, split_label.width()
            )
            total_loops = current_split_image.loops
            loop_txt = self._main_window.split_loop_label_empty_txt

            if not settings.get_bool("SHOW_MIN_VIEW"):
                split_display.setPixmap(
                    self._pixmap_for_display_label(
                        current_split_image.pixmap, split_display
                    )
                )
            split_label.setText(elided_name)
            if total_loops == 1:
                loop_txt = self._main_window.split_loop_label_empty_txt
                loop_label.setText(loop_txt)
            else:
                loop_txt = self._main_window.split_loop_label_txt
                loop_label.setText(loop_txt.format(current_loop, total_loops))
            splits_min_label.setText("")
            splits_min_label.lower()  # Make sure it's not covering others

        if current_index is not None:
            self._sync_split_override_controls()

    def _update_split_delay_suspend(self) -> None:
        """Display remaining delay or suspend time on the split image overlay."""
        overlay = self._main_window.split_overlay
        split_delay = self._splitter.split_delay_remaining
        reset_delay = self._splitter.reset_delay_remaining
        suspend = self._splitter.suspend_remaining
        min_view = settings.get_bool("SHOW_MIN_VIEW")

        # Splitter is delaying pre-split
        if split_delay is not None and not min_view:
            overlay.setVisible(True)
            if split_delay < 60:  # Less than 1 minute, so we show special text.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                delay_txt = self._main_window.overlay_split_delay_txt_secs
                overlay.setText(delay_txt.format(max(min(split_delay, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=split_delay)
                delay_txt = self._main_window.overlay_split_delay_txt_mins
                if split_delay < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(delay_txt.format(str(delta)[3:]).split(".")[0])
                elif split_delay < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(delay_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(delay_txt.format(str(delta)).split(".")[0])

        # Splitter is delaying pre-reset
        elif reset_delay is not None and not min_view:
            overlay.setVisible(True)
            if reset_delay < 60:  # Less than 1 minute, so we show special text.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                delay_txt = self._main_window.overlay_reset_delay_txt_secs
                overlay.setText(delay_txt.format(max(min(reset_delay, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=reset_delay)
                delay_txt = self._main_window.overlay_reset_delay_txt_mins
                if reset_delay < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(delay_txt.format(str(delta)[3:]).split(".")[0])
                elif reset_delay < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(delay_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(delay_txt.format(str(delta)).split(".")[0])

        # Splitter is pausing post-split
        elif suspend is not None and not min_view:
            overlay.setVisible(True)
            if suspend < 60:  # Less than 1 minute, so we show special txt.
                # Round high values down to 59.94 and low values up to 0.06
                # so that the string formatter in main_window doesn't show
                # 60.0 and 0.0 on the overlay.
                pause_txt = self._main_window.overlay_pause_txt_secs
                overlay.setText(pause_txt.format(max(min(suspend, 59.94), 0.06)))
            else:
                delta = datetime.timedelta(seconds=suspend)
                pause_txt = self._main_window.overlay_pause_txt_mins
                if suspend < 600:  # Less than 10 minutes -- remove leading 0
                    # Split call strips decimals from the second
                    overlay.setText(pause_txt.format(str(delta)[3:]).split(".")[0])
                elif suspend < 3600:  # Less than 1 hr -- remove hour info
                    overlay.setText(pause_txt.format(str(delta)[2:]).split(".")[0])
                else:  # At least 1 hour, show the whole thing
                    overlay.setText(pause_txt.format(str(delta)).split(".")[0])

        # Splitter isn't pausing or delaying, but the overlay is showing
        elif overlay.text() != "":
            overlay.setVisible(False)
            overlay.setText("")

    def _update_match_percents(self):
        """Update match percents or set them to blank.

        When self._show_reset_percents is True, shows the match percent for the
        reset image instead of the current split image.
        """
        decimals = settings.get_int("MATCH_PERCENT_DECIMALS")
        format_str = f"{{:.{decimals}f}}"
        null_str = self._null_match_percent_string(decimals)
        suspend = self._splitter.suspend_remaining
        frozen_high = self._splitter.suspend_display_highest
        frozen_thresh = self._splitter.suspend_display_threshold
        freeze_similarity = (
            suspend is not None
            and frozen_high is not None
            and not self._show_reset_percents
        )
        if self._show_reset_percents:
            match_percent = self._splitter.match_reset_percent
            high_percent = self._splitter.highest_reset_percent
        else:
            match_percent = self._splitter.match_percent
            high_percent = self._splitter.highest_percent
        match_label = self._main_window.match_percent
        high_label = self._main_window.highest_percent
        current_index = self._splitter.splits.current_image_index
        thresh_label = self._main_window.threshold_percent

        # Splitter isn't comparing images, but UI is showing current%, highest%
        if match_percent is None or high_percent is None:
            if freeze_similarity:
                high_label.setText(format_str.format(frozen_high * 100))
                match_label.setText(null_str)
            elif match_label.text() != null_str or high_label.text() != null_str:
                match_label.setText(null_str)
                high_label.setText(null_str)

        # Update current match%, highest%
        else:
            match_label.setText(format_str.format(match_percent * 100))
            high_label.setText(format_str.format(high_percent * 100))

        # No splits loaded, but UI is showing threshold%
        if freeze_similarity and frozen_thresh is not None:
            thresh_label.setText(format_str.format(frozen_thresh * 100))
        elif current_index is None:
            if thresh_label.text() != null_str:
                thresh_label.setText(null_str)

        # Update threshold%
        else:
            if self._show_reset_percents:
                threshold = self._splitter.splits.reset_image.threshold
            else:
                threshold = self._splitter.splits.list[current_index].threshold
            thresh_label.setText(format_str.format(threshold * 100))

    def _update_pause_button(self):
        """Adjust the length and content of the pause button's text according
        to aspect ratio and whether the splitter is active.

        Rely on self._splitter.match_percent to detect whether the splitter is
        active, since this particular value is never None when the splitter is
        active.
        """
        splitter_active = self._splitter.match_percent is not None
        pause_button = self._main_window.pause_button
        show_short_text = self._layout_uses_truncated_control_text()

        if show_short_text:
            if splitter_active:
                pause_button.setText(self._main_window.pause_short_txt)
            else:
                pause_button.setText(self._main_window.unpause_short_txt)

        else:
            if splitter_active:
                pause_button.setText(self._main_window.pause_long_txt)
            else:
                pause_button.setText(self._main_window.unpause_long_txt)

    def _set_buttons_and_hotkeys_enabled(self) -> bool:
        """Enable and disable hotkeys and buttons depending on whether splits
        are alive, the video is alive, and the current split is the first or
        last split."""
        current_split_index = self._splitter.splits.current_image_index
        video_alive = self._splitter.capture_thread.is_alive()

        if current_split_index is None:
            # Enable screenshots if video is on
            if video_alive and not self._screenshot.in_progress:
                self._main_window.screenshot_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)

            # Disable split, undo, skip, previous, next split, pause, record
            self._split_hotkey_enabled = False
            self._undo_hotkey_enabled = False
            self._skip_hotkey_enabled = False
            self._main_window.undo_button.setEnabled(False)
            self._main_window.skip_button.setEnabled(False)
            self._main_window.previous_button.setEnabled(False)
            self._main_window.next_button.setEnabled(False)
            self._main_window.pause_button.setEnabled(False)
            self._splitter.recording_enabled = False

        else:
            loop = self._splitter.splits.current_loop
            total_loops = self._splitter.splits.list[current_split_index].loops
            total_splits = len(self._splitter.splits.list) - 1

            # Enable split hotkey
            self._split_hotkey_enabled = True

            # Enable screenshots if video is on
            if video_alive and not self._screenshot.in_progress:
                self._main_window.screenshot_button.setEnabled(True)
                self._main_window.pause_button.setEnabled(True)
            else:
                self._main_window.screenshot_button.setEnabled(False)
                self._main_window.pause_button.setEnabled(False)

            # Enable undo and previous if this isn't the first split
            if current_split_index == 0 and loop == 1:
                self._undo_hotkey_enabled = False
                self._main_window.undo_button.setEnabled(False)
                self._main_window.previous_button.setEnabled(False)
            else:
                self._undo_hotkey_enabled = True
                self._main_window.undo_button.setEnabled(True)
                self._main_window.previous_button.setEnabled(True)

            # Enable skip and next if this isn't the last split
            if current_split_index == total_splits and loop == total_loops:
                self._skip_hotkey_enabled = False
                self._main_window.skip_button.setEnabled(False)
                self._main_window.next_button.setEnabled(False)
            else:
                self._skip_hotkey_enabled = True
                self._main_window.skip_button.setEnabled(True)
                self._main_window.next_button.setEnabled(True)

            # Enable record if we're not on the very first split image /
            # finished with the last split, and we're comparing splits
            if self._splitter.compare_split_thread.is_alive() and not (
                current_split_index == 0 and loop == 1
            ):
                self._splitter.recording_enabled = True
            else:
                self._splitter.recording_enabled = False

        self._screenshot.sync_aux_controls_enabled()

    def _null_match_percent_string(self, decimals: int) -> None:
        """Return a string representing a blank match percent with the number
        of decimal places the user chooses in settings.

        Returns:
            str: The null match percent string. Possible return values are
                "--", "--.-", and "--.--".
        """
        match_percent_string = "--"
        if decimals > 0:
            match_percent_string += "."
            while decimals > 0:
                match_percent_string += "-"
                decimals -= 1
        return match_percent_string

    def _get_interval(self) -> int:
        """Calculate the rate at which poller should poll.

        The minimum is 20 Hz (represented by the 50 ms value below). Any
        slower than 20 Hz and the UI starts to look pretty bad.

        1000 is used because that is the number of ms in a second.

        Normally it would make sense to keep the UI at a constant 60 FPS, but
        we're letting the user throttle the framerate anyway, and throttling
        this value can save CPU -- not a ton, but around 10% on my machine when
        dropping from 60FPS to 20FPS for the UI loop.

        Returns:
            int: The amount of time (ms) the poller waits between calls.
        """
        return min(1000 // settings.get_int("FPS"), 50)

    def _handle_key_press(
        self, key: Union["pynput.keyboard.key", "keyboard.KeyboardEvent"]
    ) -> None:
        """Process key presses, setting flags if the key is a hotkey.

        Called each time any key is pressed, whether or not the program is in
        focus. This method has two main uses:
            1) Updates users' custom hotkey bindings. It does this by checking
                if a given hotkey "line edit" has focus and, if so, setting
                flags so its name and key code are updated.

                Uses a lock so the poller doesn't try to update these values as
                they're being written (the worst case would be setting a hotkey
                with the correct name but wrong key code -- unlikely but not
                impossible).

            2) If a hotkey is pressed, sets a flag indicating it was pressed.

        We set flags when keys are pressed instead of directly calling a method
        because PyQt5 doesn't play nice when other threads try to manipulate
        the GUI. Doing so often causes a trace trap / segmentation fault.

        Args:
            key: Wrapper containing info about the key that was pressed. For
                more information, see the ui_keyboard_controller module.
        """
        try:
            self._handle_key_press_body(key)
        except Exception as exc:
            log_slot_error("Hotkey listener", exc)

    def _handle_key_press_body(
        self, key: Union["pynput.keyboard.key", "keyboard.KeyboardEvent"]
    ) -> None:
        # Get the key's name and internal value. If the key is not an
        # alphanumeric key, the try block throws AttributeError.
        key_name, key_code = self._keyboard.parse_key_info(key)

        # Some keys aren't handled very well by pynput -- they return a key
        # code but no name. I don't have the resources to compile an exhaustive
        # list of codes that correspond to names on different platforms, so I
        # think it's better to just have them do nothing for now.
        if key_name is None:
            return

        # Use #1 (set hotkey settings in settings window)
        for hotkey_box in [
            self._settings_window.split_hotkey_box,
            self._settings_window.reset_hotkey_box,
            self._settings_window.pause_hotkey_box,
            self._settings_window.undo_hotkey_box,
            self._settings_window.skip_hotkey_box,
            self._settings_window.previous_hotkey_box,
            self._settings_window.next_hotkey_box,
            self._settings_window.screenshot_hotkey_box,
            self._settings_window.save_peak_hotkey_box,
            self._settings_window.toggle_global_hotkeys_hotkey_box,
        ]:
            if hotkey_box.hasFocus():

                # Set flags to be picked up by _react_to_settings_menu_flags
                with self._hotkey_box_lock:
                    self._hotkey_box_to_change = hotkey_box
                    self._hotkey_box_key_code = key_code
                    self._hotkey_box_key_name = key_name

                # Take focus off hotkey box so hotkey saves properly
                # (needed on some Linux versions)
                if platform.system() != "Windows" and platform.system() != "Darwin":
                    hotkey_box.clearFocus()

                return

        # Use #2 (set "hotkey pressed" flag for _react_to_hotkey_flags)
        if not self._settings_window.isVisible():
            for hotkey_pressed, setting in {
                "_split_hotkey_pressed": ("SPLIT_HOTKEY_NAME", "SPLIT_HOTKEY_CODE"),
                "_reset_hotkey_pressed": ("RESET_HOTKEY_NAME", "RESET_HOTKEY_CODE"),
                "_undo_hotkey_pressed": ("UNDO_HOTKEY_NAME", "UNDO_HOTKEY_CODE"),
                "_skip_hotkey_pressed": ("SKIP_HOTKEY_NAME", "SKIP_HOTKEY_CODE"),
                "_previous_hotkey_pressed": ("PREV_HOTKEY_NAME", "PREV_HOTKEY_CODE"),
                "_next_hotkey_pressed": ("NEXT_HOTKEY_NAME", "NEXT_HOTKEY_CODE"),
                "_screenshot_hotkey_pressed": (
                    "SCREENSHOT_HOTKEY_NAME",
                    "SCREENSHOT_HOTKEY_CODE",
                ),
                "_save_peak_hotkey_pressed": (
                    "SAVE_PEAK_HOTKEY_NAME",
                    "SAVE_PEAK_HOTKEY_CODE",
                ),
                "_toggle_hotkeys_hotkey_pressed": (
                    "TOGGLE_HOTKEYS_HOTKEY_NAME",
                    "TOGGLE_HOTKEYS_HOTKEY_CODE",
                ),
            }.items():
                settings_name = settings.get_str(setting[0])
                settings_code = settings.get_str(setting[1])
                if not settings_code or settings_code == "None":
                    continue
                if platform.system() in ("Windows", "Darwin"):
                    if str(key_code) == settings_code:
                        setattr(self, hotkey_pressed, True)
                else:
                    if str(key_name) == settings_name and str(key_code) == settings_code:
                        setattr(self, hotkey_pressed, True)

    def _react_to_hotkey_flags(self) -> None:
        """React to the flags set in _handle_key_press for hotkeys.

        When a hotkey is pressed, do its action if hotkeys are allowed now.
        Then, unset the flag no matter what.

        The toggle_hotkeys hotkey has no hotkey_presses_allowed check because
        it is always enabled, even when global hotkeys are disabled and the
        program isn't in focus. This is to make it easy for the user to enable/
        disable global hotkeys without having to click the app back in focus.

        Pressing the split hotkey also sets a flag telling _record to save its
        current recording.
        """
        global_hotkeys_enabled = settings.get_bool("GLOBAL_HOTKEYS_ENABLED")
        hotkey_presses_allowed = (
            global_hotkeys_enabled or self._application.focusWindow() is not None
        )

        if self._toggle_hotkeys_hotkey_pressed:
            settings.set_value("GLOBAL_HOTKEYS_ENABLED", not global_hotkeys_enabled)
            self._toggle_hotkeys_hotkey_pressed = False

        elif self._split_hotkey_pressed:
            if self._split_hotkey_enabled and hotkey_presses_allowed:

                # Set appropriate flag for splitter._record. This is redundant
                # if _split_hotkey_pressed was set as the result of normal_
                # split_action being set, but not if this flag was set as the
                # result of an actual hotkey press, which is why we need this.
                split_index = self._splitter.splits.current_image_index
                if split_index is not None:
                    split = self._splitter.splits.list[split_index]
                    if split.dummy_flag:
                        self._splitter.continue_recording = True
                    else:
                        self._splitter.save_recording = True

                self._request_next_split()
            self._split_hotkey_pressed = False

        elif self._reset_hotkey_pressed:
            if hotkey_presses_allowed:
                self._manual_reset()
            self._reset_hotkey_pressed = False

        elif self._undo_hotkey_pressed:
            if self._undo_hotkey_enabled and hotkey_presses_allowed:
                self._manual_undo()
            self._undo_hotkey_pressed = False

        elif self._skip_hotkey_pressed:
            if self._skip_hotkey_enabled and hotkey_presses_allowed:
                self._manual_skip()
            self._skip_hotkey_pressed = False

        elif self._previous_hotkey_pressed:
            if hotkey_presses_allowed:
                self._main_window.previous_button.click()
            self._previous_hotkey_pressed = False

        elif self._next_hotkey_pressed:
            if hotkey_presses_allowed:
                self._main_window.next_button.click()
            self._next_hotkey_pressed = False

        elif self._screenshot_hotkey_pressed:
            if hotkey_presses_allowed and not self._screenshot.in_progress:
                self._main_window.screenshot_button.click()
            self._screenshot_hotkey_pressed = False

        elif self._save_peak_hotkey_pressed:
            if hotkey_presses_allowed:
                self._screenshot.save_peak_buffer()
            self._save_peak_hotkey_pressed = False

    def _react_to_settings_menu_flags(self) -> None:
        """React to the flags set in _handle_key_press for updating hotkeys.

        If _handle_hotkey_press has set self._hotkey_box_to_change to a hotkey
        box, use the values stored in _hotkey_box_key_name and _hotkey_box_key
        _code to update the hotkey box. Then, reset _hotkey_box_to_change back
        to None.

        We use _hotkey_box_lock to make sure the values passed from _handle_key
        _press aren't overwritten mid-method.

        Setting the hotkey box's attributes directly from _handle_hotkey_press
        is simpler, but PyQt5 doesn't like it and it occasionally causes a
        segmentation fault.
        """
        with self._hotkey_box_lock:
            if self._hotkey_box_to_change is None:
                return

            hotkey_box = self._hotkey_box_to_change
            key_name = self._hotkey_box_key_name
            key_code = self._hotkey_box_key_code

            # Set box attributes
            hotkey_box.setText(key_name)
            hotkey_box.key_code = key_code

            # Reset font size to the default
            f_size = self._settings_window.fontInfo().pointSize()
            hotkey_box.setStyleSheet(f"KeyLineEdit{{font-size: {f_size}pt;}}")

            # If the key name is too big for the box, resize the font down
            # until it fits. Subtract 10 from the width so that there's a
            # little bit of padding on the right-hand side of the box.
            while hotkey_box.get_text_width() >= hotkey_box.width() - 10:
                f_size = hotkey_box.get_font_size() - 1
                hotkey_box.setStyleSheet(f"KeyLineEdit{{font-size: {f_size}pt;}}")

            self._hotkey_box_to_change = None

    def _react_to_split_flags(self) -> None:
        """Press a hotkey & go to next split when self._splitter sets flags.

        If the normal_split_action flag is set but no split hotkey is assigned,
        or the hotkey wasn't heard by the application, request the next split
        image manually.
        """
        # Pause split (press pause hotkey)
        if self._splitter.pause_split_action:
            self._splitter.pause_split_action = False
            key_code = settings.get_str("PAUSE_HOTKEY_CODE")
            if len(key_code) > 0:
                self._keyboard.press_and_release(key_code)
            self._request_next_split()

        # Dummy split (silently advance to next split image)
        elif self._splitter.dummy_split_action:
            self._splitter.dummy_split_action = False
            self._request_next_split()

        # Normal split (LiveSplit command or split hotkey)
        elif self._splitter.normal_split_action:
            self._splitter.normal_split_action = False
            self._autosplit_normal_split()

        # Reset splits (LiveSplit command or reset hotkey)
        elif self._splitter.reset_split_action:
            self._splitter.reset_split_action = False
            self._autosplit_reset()

    def _wake_display(self):
        """Keep the display awake when the splitter is active.

        Each time this method is called, check if at least _wake_interval
        seconds have passed. If so, update _last_wake_time to the current time,
        and check if the splitter is active or delaying / suspending with a
        countdown. If it is, attempt to wake the display (the method differs by
        operating system).

        MacOS method: caffeinate (key release as fallback, see below)
        Even if called with a 1 second timeout, as we do here, caffeinate
        resets the OS's sleep countdown, so we only need to run it about once a
        minute (1 minute is the lowest sleep timeout on MacOS) to prevent the
        screen from dimming. We use a separate thread to reduce overhead
        (creating a new thread requires less overhead than calling
        subprocess.Popen, once, and we only need to do it once, instead of once
        every _wake_interval).
        If caffeinate isn't available, fall back to the "release key" method.
        (see below). Caffeinate is preferred because, unlike releasing a key,
        it doesn't force the keyboard's backlight to stay on, but releasing a
        key at least keeps the display alive.

        Windows method: Key release
        This is the least invasive solution that doesn't require permanently
        changing a registry or system value, which would prevent the machine
        from sleeping normally if this program exits abruptly. Key releases
        instead of key presses or mouse clicks / wiggles are ideal because
        releasing a key doesn't require the key to be pressed, and does NOT
        interrupt an actual, physical keypress being held by the user, so users
        should never notice that anything is happening behind the scenes. It's
        hacky but hopefully relatively uninvasive, and its effects subside as
        soon as the program stops running.

        Linux: Key release (untested, may not be reliable)
        """
        if time.perf_counter() - self._last_wake_time >= self._wake_interval:
            self._last_wake_time = time.perf_counter()
            splitter_active = self._splitter.compare_split_thread.is_alive()

            # Key should be alphanumeric to work cross platform; beyond that it
            # doesn't matter, since the user won't detect its release
            key = "a"

            # MacOS: Try caffeinate, fall back to key release if necessary
            if platform.system() == "Darwin":
                if splitter_active:

                    caffeinate_path = self._get_exec_path("caffeinate")

                    # No caffeinate, use fallback
                    if caffeinate_path is None:
                        self._keyboard.release(key)

                    # Caffeinate exists; start thread if it hasn't been started
                    elif not self._caffeinate_thread.is_alive():
                        self._caffeinate_thread_finished = False
                        self._caffeinate_thread = Thread(
                            target=self._caffeinate, args=(caffeinate_path,)
                        )
                        self._caffeinate_thread.daemon = True
                        self._caffeinate_thread.start()

                # Splitter inactive; kill thread (join not needed, will die)
                else:
                    self._caffeinate_thread_finished = True

            # Winodws / Linux: release a key if splitter active
            elif splitter_active:
                self._keyboard.release(key)

    def _caffeinate(self, caffeinate_path: str) -> None:
        """Use built-in caffeinate to keep the machine's display on (MacOS).

        A 1-second timeout is used because caffeinate resets the sleep timer
        (i.e. it doesn't need to be constantly running). This is good because
        it's hard to reliably terminate an ongoing caffeinate process; this way
        we guarantee that users' sleep settings will return to normal after the
        program terminates.
        """
        while not self._caffeinate_thread_finished:
            subprocess.Popen([caffeinate_path, "-d", "-t", "1"])
            time.sleep(self._wake_interval)

    def _get_exec_path(self, name: str) -> Optional[str]:
        """Return the path to an executable file, if it exists.

        Args:
            name (str): The name (not path) of an exectable file. Ex: "grep"

        Returns:
            str: The absolute path to the executable, if it exists.
        """
        if platform.system() == "Windows":
            search = "where"
        else:
            search = "which"
        try:
            return subprocess.check_output([search, name]).decode().strip()

        # The executable doesn't exist (or at least isn't on PATH)
        except subprocess.CalledProcessError:
            return None
