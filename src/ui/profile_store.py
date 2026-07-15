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

"""Profile save/load, recents menu, and payload serialization."""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

import paths
import settings

if TYPE_CHECKING:
    from ui.ui_controller import UIController

PROFILE_SCHEMA_VERSION = 1
PROFILE_RECENTS_MAX = 5
PROFILE_SETTING_KEYS = (
    "LAST_IMAGE_DIR",
    "DEFAULT_THRESHOLD",
    "DEFAULT_DELAY",
    "DEFAULT_PAUSE",
    "DEFAULT_RESET_WAIT",
    "FPS",
    "MATCH_PERCENT_DECIMALS",
    "ASPECT_RATIO",
    "SHOW_MIN_VIEW",
    "VIDEO_CROP_INSET_LEFT",
    "VIDEO_CROP_INSET_RIGHT",
    "VIDEO_CROP_INSET_TOP",
    "VIDEO_CROP_INSET_BOTTOM",
    "OPEN_SCREENSHOT_ON_CAPTURE",
)
PROFILE_BURST_SETTING_KEYS = (
    "BURST_MODE_ENABLED",
    "BURST_DATED_SESSION_FOLDERS",
    "BURST_DURATION_SEC",
    "BURST_FPS",
    "BURST_SHOTS_BASE_DIR",
)


class ProfileStore:
    """Save/load profiles and maintain the recent-profiles menu."""

    def __init__(self, controller: "UIController") -> None:
        self._ctrl = controller

    def profile_saves_dir(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        configured = settings.get_str("PROFILE_SAVE_DIR")
        if configured not in ("", "None", None):
            path = Path(configured)
        else:
            path = root / "saves"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def profile_recent_paths(self) -> List[str]:
        raw = settings.get_str("RECENT_PROFILE_PATHS")
        if raw in ("None", "", None):
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        out: List[str] = []
        for item in parsed:
            if isinstance(item, str) and item:
                out.append(item)
        return out[:PROFILE_RECENTS_MAX]

    def set_profile_recent_paths(self, paths: List[str]) -> None:
        deduped: List[str] = []
        for path in paths:
            if path and path not in deduped:
                deduped.append(path)
        settings.set_value("RECENT_PROFILE_PATHS", json.dumps(deduped[:PROFILE_RECENTS_MAX]))

    def push_recent_profile_path(self, path: str) -> None:
        existing = [p for p in self.profile_recent_paths() if p != path]
        self.set_profile_recent_paths([path] + existing)
        self.refresh_recent_profile_actions()

    def refresh_recent_profile_actions(self) -> None:
        existing = [p for p in self.profile_recent_paths() if Path(p).is_file()]
        self.set_profile_recent_paths(existing)
        for i, action in enumerate(self._ctrl._main_window.profile_recent_actions):
            if i < len(existing):
                p = Path(existing[i])
                action.setText(p.stem)
                action.setToolTip(str(p))
                action.setEnabled(True)
                action.setData(str(p))
                try:
                    action.triggered.disconnect()
                except TypeError:
                    pass
                action.triggered.connect(
                    lambda _checked=False, path=str(p): self.load_profile_from_path(path)
                )
            else:
                action.setText("(empty)")
                action.setToolTip("")
                action.setEnabled(False)
                action.setData(None)
                try:
                    action.triggered.disconnect()
                except TypeError:
                    pass

    def profile_payload(self, profile_name: str) -> dict:
        qsettings = settings.settings
        settings_map = {
            key: settings.get_str(key)
            for key in PROFILE_SETTING_KEYS
            if qsettings.contains(key)
        }
        burst_settings = {
            key: settings.get_str(key)
            for key in PROFILE_BURST_SETTING_KEYS
            if qsettings.contains(key)
        }
        split_dir = Path(settings.get_str("LAST_IMAGE_DIR"))
        try:
            rel_split = str(split_dir.relative_to(Path(__file__).resolve().parents[2]))
        except ValueError:
            rel_split = None
        split_files = []
        if split_dir.is_dir():
            for child in sorted(split_dir.iterdir()):
                if child.is_file():
                    split_files.append(
                        {"name": child.name, "size": child.stat().st_size}
                    )
        return {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "profile_name": profile_name,
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "app_version": settings.VERSION_NUMBER,
            "settings": settings_map,
            "burst_settings": burst_settings,
            "split_dir": {
                "absolute": str(split_dir),
                "relative_to_project": rel_split,
                "files": split_files,
            },
        }

    def sanitize_profile_name(self, text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", text).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned[:80]

    def existing_profile_names(self, saves_dir: Optional[Path] = None) -> List[str]:
        saves = saves_dir or self.profile_saves_dir()
        files = [p for p in saves.glob("*.json") if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return [p.stem for p in files]

    def display_profile_dir(self, path: Path) -> str:
        """Shorten folder label by hiding /Users/<name>/ when applicable."""
        p = path.expanduser().resolve()
        home = Path.home().resolve()
        try:
            rel = p.relative_to(home)
        except ValueError:
            return str(p)
        rel_parts = rel.parts
        if rel_parts:
            return str(Path(*rel_parts))
        return str(p)

    def save_profile_via_dialog(self) -> None:
        default_name = "New profile"
        current_dir = self.profile_saves_dir()

        dlg = QDialog(self._ctrl._main_window)
        dlg.setWindowTitle("Save Profile")
        dlg.setStyleSheet(self._ctrl._get_style_sheet())
        dlg.setFixedWidth(390)
        root = QVBoxLayout(dlg)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        border_frame = QFrame(dlg)
        border_frame.setObjectName("border")
        inner = QVBoxLayout(border_frame)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

        profile_name_label = QLabel("Profile name", border_frame)
        profile_name_row = QHBoxLayout()
        profile_name_row.setContentsMargins(0, 0, 0, 0)
        profile_name_row.addWidget(profile_name_label)
        profile_name_row.addStretch(1)
        inner.addLayout(profile_name_row)
        name_row = QHBoxLayout()
        name_combo = QComboBox(border_frame)
        name_combo.setEditable(True)
        name_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_combo.setFixedHeight(name_combo.sizeHint().height())
        arrow_path = str(
            (paths.resources_dir() / "icons" / "chevron_down_white.svg").resolve()
        ).replace("\\", "/")
        name_combo.setStyleSheet(
            "QComboBox { padding: 2px 0px 2px 2px; }"
            "QComboBox QLineEdit { border: 0px; padding: 0px; margin: 0px; }"
            "QComboBox::down-arrow {"
            f" image: url({arrow_path});"
            " width: 14px; height: 14px;"
            " position: relative; left: 1px;"
            "}"
            "QComboBox::drop-down {"
            " border: 0px;"
            " subcontrol-origin: padding;"
            " subcontrol-position: center right;"
            " width: 22px;"
            "}"
        )
        btn_minus = QPushButton("-", border_frame)
        btn_minus.setFocusPolicy(Qt.NoFocus)
        btn_minus.setDefault(False)
        btn_minus.setAutoDefault(False)
        btn_minus.setToolTip("Delete selected profile")
        box_size = name_combo.sizeHint().height()
        btn_minus.setFixedSize(box_size, box_size)
        btn_minus.setStyleSheet("font-weight: normal; padding-bottom: 2px;")
        name_row.addWidget(name_combo)
        name_row.addWidget(btn_minus)
        inner.addLayout(name_row)

        dir_label = QLabel(self.display_profile_dir(current_dir), border_frame)
        dir_label.setStyleSheet("color: #888888; font-size: 12px; font-style: italic;")
        dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.addWidget(dir_label)
        path_row.addStretch(1)
        inner.addLayout(path_row)

        def refresh_names() -> None:
            current_text = name_combo.currentText().strip()
            names = self.existing_profile_names(current_dir)
            name_combo.blockSignals(True)
            name_combo.clear()
            if default_name not in names:
                name_combo.addItem(default_name)
            for n in names:
                name_combo.addItem(n)
            name_combo.blockSignals(False)
            if current_text:
                name_combo.setEditText(current_text)
            else:
                name_combo.setCurrentText(default_name)

        refresh_names()

        button_row = QHBoxLayout()
        btn_select_folder = QPushButton("Select folder", border_frame)
        btn_select_folder.setFocusPolicy(Qt.NoFocus)
        btn_select_folder.setDefault(False)
        btn_select_folder.setAutoDefault(False)
        btn_select_folder.setMinimumWidth(
            btn_select_folder.fontMetrics().horizontalAdvance("Select folder") + 24
        )
        btn_cancel = QPushButton("Cancel", border_frame)
        btn_cancel.setFocusPolicy(Qt.NoFocus)
        btn_cancel.setDefault(False)
        btn_cancel.setAutoDefault(False)
        btn_ok = QPushButton("Save", border_frame)
        btn_ok.setFocusPolicy(Qt.NoFocus)
        btn_ok.setDefault(False)
        btn_ok.setAutoDefault(False)
        button_font = btn_ok.font()
        btn_select_folder.setFont(button_font)
        btn_cancel.setFont(button_font)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        button_row.addWidget(btn_select_folder)
        button_row.addStretch(1)
        button_row.addWidget(btn_cancel)
        button_row.addWidget(btn_ok)
        inner.addSpacing(4)
        inner.addLayout(button_row)

        root.addWidget(border_frame)

        btn_cancel.clicked.connect(dlg.reject)
        btn_ok.clicked.connect(dlg.accept)

        def on_select_folder() -> None:
            nonlocal current_dir
            picked = QFileDialog.getExistingDirectory(
                dlg,
                "Select profile folder",
                str(current_dir),
            )
            if not picked:
                return
            current_dir = Path(picked)
            current_dir.mkdir(parents=True, exist_ok=True)
            dir_label.setText(self.display_profile_dir(current_dir))
            refresh_names()

        btn_select_folder.clicked.connect(on_select_folder)

        def on_delete_profile() -> None:
            """Delete an existing profile file; does not save anything."""
            name = self.sanitize_profile_name(name_combo.currentText())
            if not name:
                return
            target = current_dir / f"{name}.json"
            if not target.is_file():
                QMessageBox.information(
                    dlg,
                    "Delete Profile",
                    "Select an existing profile from the dropdown to delete.",
                )
                return

            msg = QMessageBox(dlg)
            msg.setWindowTitle("Delete profile?")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Delete this profile?")
            msg.setInformativeText(name)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            if msg.exec() != QMessageBox.Yes:
                return

            try:
                target.unlink()
            except OSError:
                QMessageBox.warning(dlg, "Delete failed", "Could not delete profile.")
                return

            # Remove from recents (best-effort) and refresh menu + dropdown.
            self.set_profile_recent_paths(
                [p for p in self.profile_recent_paths() if p != str(target)]
            )
            self.refresh_recent_profile_actions()
            refresh_names()

        btn_minus.clicked.connect(on_delete_profile)
        dlg.setFixedHeight(dlg.sizeHint().height())
        self._ctrl._clear_dialog_focus_after_show(dlg)

        while True:
            if dlg.exec() != QDialog.Accepted:
                return
            profile_name = self.sanitize_profile_name(name_combo.currentText())
            if not profile_name:
                QMessageBox.warning(
                    dlg,
                    "Invalid profile name",
                    "Profile name must contain letters, numbers, spaces, dot, dash or underscore.",
                )
                continue
            target = current_dir / f"{profile_name}.json"
            if target.exists():
                msg = QMessageBox(dlg)
                msg.setWindowTitle("Overwrite profile?")
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Do you want to overwrite it?")
                msg.setInformativeText(f"Profile '{profile_name}' already exists.")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                answer = msg.exec()
                if answer != QMessageBox.Yes:
                    # Stay in save dialog so user can pick another name.
                    continue
            settings.set_value("PROFILE_SAVE_DIR", str(current_dir))
            payload = self.profile_payload(profile_name)
            tmp = target.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(target)
            self.push_recent_profile_path(str(target))
            return

    def load_profile_via_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self._ctrl._main_window,
            "Load Profile",
            str(self.profile_saves_dir()),
            "JSON files (*.json)",
        )
        if not path:
            return
        self.load_profile_from_path(path)

    def load_profile_from_path(self, path: str) -> None:
        p = Path(path)
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            QMessageBox.warning(
                self._ctrl._main_window,
                "Failed to load profile",
                "Profile file could not be read.",
            )
            return
        if not isinstance(payload, dict):
            QMessageBox.warning(
                self._ctrl._main_window, "Invalid profile", "Profile format is invalid."
            )
            return
        try:
            schema_version = int(payload.get("schema_version", 0))
        except (TypeError, ValueError):
            schema_version = 0
        if schema_version != PROFILE_SCHEMA_VERSION:
            QMessageBox.warning(
                self._ctrl._main_window,
                "Unsupported profile version",
                "This profile uses an unsupported schema version.",
            )
            return
        raw_settings = payload.get("settings")
        if not isinstance(raw_settings, dict):
            QMessageBox.warning(
                self._ctrl._main_window, "Invalid profile", "Profile settings are missing."
            )
            return
        before_strip = self._ctrl._strip_layout_settings_tuple()
        for key, value in raw_settings.items():
            if isinstance(key, str) and key in PROFILE_SETTING_KEYS:
                settings.set_value(key, value)
        settings.set_program_vals(align_burst_fps_to_main=False)
        self.apply_burst_settings(payload)
        after_strip = self._ctrl._strip_layout_settings_tuple()
        view_layout_changed = before_strip[:4] != after_strip[:4]
        theme_changed = before_strip[4] != after_strip[4]
        poller_was_active = self._ctrl._poller.isActive()
        if poller_was_active:
            self._ctrl._poller.stop()
        try:
            self._ctrl._apply_profile_runtime_state(
                payload,
                view_layout_changed=view_layout_changed,
                theme_changed=theme_changed,
            )
        finally:
            if poller_was_active:
                self._ctrl._poller.start()
        self.push_recent_profile_path(str(p))

    def apply_burst_settings(self, payload: dict) -> None:
        """Restore saved Burst screenshot settings after settings normalization."""
        burst_settings = payload.get("burst_settings")
        if not isinstance(burst_settings, dict):
            burst_settings = payload.get("settings")
        if not isinstance(burst_settings, dict):
            return
        for key in PROFILE_BURST_SETTING_KEYS:
            if key in burst_settings:
                settings.set_value(key, burst_settings[key])

    def resolve_split_dir_after_load(self, split_meta: dict) -> None:
        abs_path = split_meta.get("absolute")
        rel_path = split_meta.get("relative_to_project")
        root = Path(__file__).resolve().parents[2]
        candidate_paths = []
        if isinstance(abs_path, str) and abs_path:
            candidate_paths.append(Path(abs_path))
        if isinstance(rel_path, str) and rel_path:
            candidate_paths.append(root / rel_path)
        for candidate in candidate_paths:
            if candidate.is_dir():
                settings.set_value("LAST_IMAGE_DIR", str(candidate))
                return
