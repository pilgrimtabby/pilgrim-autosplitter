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

"""Persist and reference user settings and key values."""


import os
from pathlib import Path

import requests
from PyQt5.QtCore import QSettings

# The width of the frame generated and used by splitter.py to find a match
COMPARISON_FRAME_WIDTH = 320

# The height of the frame generated and used by splitter.py to find a match
COMPARISON_FRAME_HEIGHT = 240

# Pilgrim Autosplitter's current version number (fork tag; upstream release is v1.1.0).
VERSION_NUMBER = "v1.1.3"

# The URL of Pilgrim Autosplitter's GitHub repo
REPO_URL = "https://github.com/pilgrimtabby/pilgrim-autosplitter/"

# The URL of Pilgrim Autosplitter's user manual
USER_MANUAL_URL = "https://pilgrimtabby.github.io/pilgrim-autosplitter/"

# Create or access the QSettings file that persists user settings
settings = QSettings("pilgrim_tabby", "Pilgrim Autosplitter")

# The default number of loops per split
DEFAULT_LOOP_COUNT = 1

# The max amount of loops and wait time (in seconds) permitted for split images
MAX_LOOPS_AND_WAIT = 99999

# The highest threshold permitted for split images
MAX_THRESHOLD = 1


def get_str(key: str, settings: QSettings = settings) -> str:
    """Return a str from settings, regardless of the stored value's type.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        str: The setting.
    """
    return str(settings.value(key))


def get_bool(key: str, settings: QSettings = settings) -> bool:
    """Return a bool from settings, regardless of the stored value's type.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        bool: The setting.
    """
    if settings.value(key) == "True":
        return True
    else:
        return False


def get_int(key: str, settings: QSettings = settings) -> int:
    """Return an int from settings, regardless of the stored value's type.

    This should only be used on settings for which is_digit would return True,
    or Python will throw a TypeError.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        int: The setting.
    """
    return int(settings.value(key))


def get_int_nonneg(key: str, default: int = 0, settings: QSettings = settings) -> int:
    """Non-negative int from settings; tolerate missing or corrupt values.

    Used for values like crop insets where invalid stored data must not crash
    the capture thread.

    Args:
        key (str): Setting name.
        default (int): Fallback when unset or unparsable.
        settings (QSettings): Settings store.

    Returns:
        int: ``max(0, parsed)`` or ``default``.
    """
    raw = settings.value(key)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except (ValueError, TypeError):
        return default


def get_float(key: str, settings: QSettings = settings) -> float:
    """Return a float from settings, regardless of the stored value's type.

    This should only be used to retrieve settings for which float(foo) would
    not throw a TypeError.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        float: The setting.
    """
    return float(settings.value(key))


def set_value(key: str, value: any, settings: QSettings = settings) -> None:
    """Persist a setting as a str, regardless of the value's type.

    Strings are preferred because QSettings doesn't remember types on all
    platforms-- it depends on the backend used.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".
        value (any): The value the key should reference.
    """
    settings.setValue(key, str(value))


def set_program_vals(
    settings: QSettings = settings, *, align_burst_fps_to_main: bool = True
) -> None:
    """Ensure that settings values are updated and make sense before use.

    Unsets hotkeys if last used version was <=1.0.6 due to a change in the way
    hotkeys are implemented.

    Populates settings with default values if they have not yet been set.

    Ensures that LAST_IMAGE_DIR and LAST_RECORD_DIR point to existing paths.

    Ensures that the program starts in full view if START_WITH_VIDEO is false,
    since the user would have to exit minimal view to turn the video on anyway.

    Makes sure that the correct aspect ratio is shown.

    Args:
        settings: Settings store.
        align_burst_fps_to_main: When True (app launch), set ``BURST_FPS`` from
            general ``FPS``. When False (e.g. profile load), keep stored burst FPS.
    """
    home_dir = get_home_dir()

    # Unset hotkeys if upgrading from <=v1.0.6 because of hotkey implementation
    # updates. Set a default reset wait for the same reason.
    #
    # Important: get_str() turns a missing QSettings value into the literal
    # string "None". Treating that as v1.0.0 wiped hotkeys whenever prefs failed
    # to read (macOS AccessError / cfprefsd glitches). Only clear binds when we
    # have a real stored version that is older than v1.0.7.
    if settings.contains("LAST_VERSION"):
        last_version = get_str("LAST_VERSION", settings)
        if last_version not in ("", "None") and not version_ge(
            last_version, "v1.0.7"
        ):
            unset_hotkey_bindings(settings)
            set_value("DEFAULT_RESET_WAIT", 0.0, settings)

    if not get_bool("SETTINGS_SET", settings):
        # Indicate that default settings have been populated
        set_value("SETTINGS_SET", True, settings)

        # Set hotkeys to default values
        unset_hotkey_bindings(settings)

        # Turn off recording splits as clips by default
        set_value("RECORD_CLIPS", False, settings)

        # The default minimum match percent needed to force a split action
        set_value("DEFAULT_THRESHOLD", 0.90, settings)

        # The default delay (seconds) before a split
        set_value("DEFAULT_DELAY", 0.0, settings)

        # The default pause (seconds) after a split
        set_value("DEFAULT_PAUSE", 1.0, settings)

        # The default wait time before looking for reset image
        set_value("DEFAULT_RESET_WAIT", 0.0, settings)

        # The FPS used by splitter and ui_controller
        set_value("FPS", 30, settings)

        # The location of split images
        set_value("LAST_IMAGE_DIR", home_dir, settings)

        # The location of recordings
        set_value("LAST_RECORD_DIR", home_dir, settings)

        # Determine whether screenshots should be opened using the machine's
        # default image viewer after capture
        set_value("OPEN_SCREENSHOT_ON_CAPTURE", False, settings)

        # The number of decimal places shown when displaying match percents
        set_value("MATCH_PERCENT_DECIMALS", 0, settings)

        # The UI theme
        set_value("THEME", "dark", settings)

        # The aspect ratio
        set_value("ASPECT_RATIO", "4:3 (480x360)", settings)

        # Always on top value
        set_value("ALWAYS_ON_TOP", False, settings)

        # The last cv2 capture source index. This is an imperfect way to
        # remember the last video source used, since the indexes can reference
        # different sources at different times, but it's the best I can do in a
        # cross-platform environment
        set_value("LAST_CAPTURE_SOURCE_INDEX", 0, settings)

        # Whether the program should try to open video on startup, or wait for
        # the user to press "reconnect video"
        set_value("START_WITH_VIDEO", False, settings)

        # Whether the minimal view should be showing
        set_value("SHOW_MIN_VIEW", False, settings)

        # Whether global hotkeys are enabled (default) or only local hotkeys
        set_value("GLOBAL_HOTKEYS_ENABLED", True, settings)

        # Whether program checks for updates on launch
        set_value("CHECK_FOR_UPDATES", True, settings)

        # JSON list of recently loaded/saved profile paths
        set_value("RECENT_PROFILE_PATHS", "[]", settings)

        # Optional override for profile save directory; empty means project /saves
        set_value("PROFILE_SAVE_DIR", "", settings)

        # LiveSplit One WebSocket server port (localhost only)
        set_value("WS_SERVER_PORT", 16834, settings)

    if not settings.contains("WS_SERVER_PORT"):
        set_value("WS_SERVER_PORT", 16834, settings)

    # Make sure image dir exists and is within the user's home dir
    # (This limits i/o to user-controlled areas)
    last_image_dir = get_str("LAST_IMAGE_DIR", settings)
    if not path_is_within_home(last_image_dir) or not Path(last_image_dir).is_dir():
        set_value("LAST_IMAGE_DIR", home_dir, settings)

    # Make sure recordings dir exists and is within the user's home dir
    # (This limits i/o to user-controlled areas)
    last_record_dir = get_str("LAST_RECORD_DIR", settings)
    if not path_is_within_home(last_record_dir) or not Path(last_record_dir).is_dir():
        set_value("LAST_RECORD_DIR", home_dir, settings)

    # Always start in full view if video doesn't come on automatically
    if not get_bool("START_WITH_VIDEO", settings):
        set_value("SHOW_MIN_VIEW", False, settings)

    # Remember last used version number (to unset hotkeys if upgrading)
    set_value("LAST_VERSION", VERSION_NUMBER, settings)

    if not settings.contains("RECENT_PROFILE_PATHS"):
        set_value("RECENT_PROFILE_PATHS", "[]", settings)
    if not settings.contains("PROFILE_SAVE_DIR"):
        set_value("PROFILE_SAVE_DIR", "", settings)

    # Burst screenshot capture (burst FPS is aligned with Settings ▸ FPS on each startup)
    if not settings.contains("BURST_MODE_ENABLED"):
        set_value("BURST_MODE_ENABLED", False, settings)
    if not settings.contains("BURST_DURATION_SEC"):
        set_value("BURST_DURATION_SEC", 2.0, settings)
    if align_burst_fps_to_main:
        _main_fps = max(1, min(120, get_int("FPS", settings)))
        set_value("BURST_FPS", float(_main_fps), settings)
    elif not settings.contains("BURST_FPS"):
        _main_fps = max(1, min(120, get_int("FPS", settings)))
        set_value("BURST_FPS", float(_main_fps), settings)

    if not settings.contains("BURST_DATED_SESSION_FOLDERS"):
        set_value("BURST_DATED_SESSION_FOLDERS", True, settings)

    # Parent folder for screenshots and burst runs.
    if not settings.contains("BURST_SHOTS_BASE_DIR"):
        set_value("BURST_SHOTS_BASE_DIR", home_dir, settings)
    else:
        burst_base = get_str("BURST_SHOTS_BASE_DIR", settings)
        if (
            not path_is_within_home(burst_base)
            or not Path(burst_base).expanduser().is_dir()
        ):
            set_value("BURST_SHOTS_BASE_DIR", home_dir, settings)

    # Snap Peak hotkey (added after initial release; unset reads as "None")
    for key in ("SAVE_PEAK_HOTKEY_NAME", "SAVE_PEAK_HOTKEY_CODE"):
        if not settings.contains(key) or get_str(key, settings) == "None":
            set_value(key, "", settings)

    # Video crop (source pixels; applied before resize to comparison/UI frame)
    _ensure_video_crop_defaults(settings)

    # Set correct video, split image width and height relative to aspect ratio
    aspect_ratio = get_str("ASPECT_RATIO", settings)
    if aspect_ratio == "4:3 (480x360)":
        set_value("FRAME_WIDTH", 480, settings)
        set_value("FRAME_HEIGHT", 360, settings)
    elif aspect_ratio == "4:3 (320x240)":
        set_value("FRAME_WIDTH", 320, settings)
        set_value("FRAME_HEIGHT", 240, settings)
    elif aspect_ratio == "16:9 (512x288)":
        set_value("FRAME_WIDTH", 512, settings)
        set_value("FRAME_HEIGHT", 288, settings)
    elif aspect_ratio == "16:9 (432x243)":
        set_value("FRAME_WIDTH", 432, settings)
        set_value("FRAME_HEIGHT", 243, settings)


def version_ge(version1: str, version2: str) -> bool:
    """Check whether version1 equal to or more recent than version2.

    Versions are in format x.x.x or vx.x.x, where x is a nonnegative integer.

    Args:
        version1 (str): The first version number.
        version2 (str): The second version number.

    Returns:
        bool: True if version1 is equal to or more recent than version2.
    """

    version1_numbers = version1.replace("v", "").split(".")
    version2_numbers = version2.replace("v", "").split(".")

    for i in range(3):
        if version1_numbers[i] > version2_numbers[i]:
            return True
        if version1_numbers[i] < version2_numbers[i]:
            return False

    return True


def _ensure_video_crop_defaults(settings: QSettings = settings) -> None:
    """Populate video crop inset keys when missing (pixels trimmed per edge).

    All zeros means no crop. Legacy VIDEO_CROP_* keys are ignored.
    """
    defaults = {
        "VIDEO_CROP_INSET_LEFT": 0,
        "VIDEO_CROP_INSET_RIGHT": 0,
        "VIDEO_CROP_INSET_TOP": 0,
        "VIDEO_CROP_INSET_BOTTOM": 0,
    }
    for key, value in defaults.items():
        if not settings.contains(key):
            set_value(key, value, settings=settings)


def unset_hotkey_bindings(settings: QSettings = settings) -> None:
    """Unset all hotkey bindings."""
    # Text values
    set_value("SPLIT_HOTKEY_NAME", "", settings)
    set_value("RESET_HOTKEY_NAME", "", settings)
    set_value("PAUSE_HOTKEY_NAME", "", settings)
    set_value("UNDO_HOTKEY_NAME", "", settings)
    set_value("SKIP_HOTKEY_NAME", "", settings)
    set_value("PREV_HOTKEY_NAME", "", settings)
    set_value("NEXT_HOTKEY_NAME", "", settings)
    set_value("SCREENSHOT_HOTKEY_NAME", "", settings)
    set_value("SAVE_PEAK_HOTKEY_NAME", "", settings)
    set_value("TOGGLE_HOTKEYS_HOTKEY_NAME", "", settings)

    # Key IDs
    set_value("SPLIT_HOTKEY_CODE", "", settings)
    set_value("RESET_HOTKEY_CODE", "", settings)
    set_value("PAUSE_HOTKEY_CODE", "", settings)
    set_value("UNDO_HOTKEY_CODE", "", settings)
    set_value("SKIP_HOTKEY_CODE", "", settings)
    set_value("PREV_HOTKEY_CODE", "", settings)
    set_value("NEXT_HOTKEY_CODE", "", settings)
    set_value("SCREENSHOT_HOTKEY_CODE", "", settings)
    set_value("SAVE_PEAK_HOTKEY_CODE", "", settings)
    set_value("TOGGLE_HOTKEYS_HOTKEY_CODE", "", settings)


def get_latest_version() -> str:
    """Get the latest release's version number from the github repo.

    The `try` block at the beginning is to handle cases where the internet is
    either (1) not connected or (2) very slow.

    Returns:
        str: The version number (or the current version if something goes
            wrong).
    """
    try:
        # Use timeout=1 to prevent hanging for too long
        github_page_text = requests.get(REPO_URL, timeout=1).text
    except (requests.exceptions.ConnectionError, requests.Timeout):
        return VERSION_NUMBER

    # The way GitHub works right now, releases_text is present in the html
    # right before the most recent release number. I know this is a pretty
    # hacky way of finding the latest release number...
    releases_text = "/pilgrimtabby/pilgrim-autosplitter/releases/tag/"
    releases_text_index = int(github_page_text.find(releases_text))

    if releases_text_index == -1:
        return VERSION_NUMBER  # releases_text text not found, don't worry
    else:
        version_location = releases_text_index + len(releases_text)
        # The version number is follow by a quotation mark. 9 extra chars is
        # more than we need, but we're splitting by the `"` anyway.
        latest_version = github_page_text[
            version_location : (version_location + 9)
        ].split('"')[0]
        return latest_version


def get_home_dir() -> str:
    """Get home directory of user, even when running as root.

    Replace backslashes found in Windows-like paths with forward slashes for
    consistency.

    Returns:
        str: The home directory path.
    """
    home_dir = os.path.expanduser("~")
    if home_dir == "/root":  # Returned if running as root
        user = os.environ.get("SUDO_USER")
        home_dir = os.path.expanduser(f"~{user}")
    return home_dir.replace("\\", "/")


def path_is_within_home(path: str) -> bool:
    """True if ``path`` resolves to the user's home directory or a subdirectory.

    ``QFileDialog`` on Windows returns backslashes; ``get_home_dir`` uses
    forward slashes, so string ``startswith`` is not reliable for this check.
    """
    if not (path or "").strip():
        return False
    try:
        resolved = Path(path).expanduser().resolve()
        home = Path(get_home_dir()).expanduser().resolve()
        resolved.relative_to(home)
        return True
    except (ValueError, OSError, RuntimeError):
        return False
