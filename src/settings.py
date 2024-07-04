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

"""Persist and reference user settings and key values.
"""


import os
from pathlib import Path

import requests
from PyQt5.QtCore import QSettings

# The width of the frame generated and used by splitter.py to find a match
COMPARISON_FRAME_WIDTH = 320

# The height of the frame generated and used by splitter.py to find a match
COMPARISON_FRAME_HEIGHT = 240

# Pilgrim Autosplitter's current version number
VERSION_NUMBER = "v1.0.5"

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


def get_str(key: str) -> str:
    """Return a str from settings, regardless of the stored value's type.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        str: The setting.
    """
    return str(settings.value(key))


def get_bool(key: str) -> bool:
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


def get_int(key: str) -> int:
    """Return an int from settings, regardless of the stored value's type.

    This should only be used on settings for which is_digit would return True,
    or Python will throw a TypeError.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        int: The setting.
    """
    return int(settings.value(key))


def get_float(key: str) -> float:
    """Return a float from settings, regardless of the stored value's type.

    This should only be used to retrieve settings for which float(foo) would
    not throw a TypeError.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".

    Returns:
        float: The setting.
    """
    return float(settings.value(key))


def set_value(key: str, value: any) -> None:
    """Persist a setting as a str, regardless of the value's type.

    Strings are preferred because QSettings doesn't remember types on all
    platforms-- it depends on the backend used.

    Args:
        key (str): The name of the setting. E.g. "CHEESE_FLAVOR".
        value (any): The value the key should reference.
    """
    settings.setValue(key, str(value))


def set_defaults() -> None:
    """Ensure that settings values make sense before they are used.

    Populates settings with default values if they have not yet been set.

    Ensures that LAST_IMAGE_DIR points to an existing path.

    Ensures that the program starts in full view if START_WITH_VIDEO is false,
    since the user would have to exit minimal view to turn the video on anyway.

    Makes sure that the correct aspect ratio is shown.
    """
    if not get_bool("SETTINGS_SET"):
        # Indicate whether default settings have been populated
        set_value("SETTINGS_SET", True)

        # The default minimum match percent needed to force a split action
        set_value("DEFAULT_THRESHOLD", 0.90)

        # The default delay (seconds) before a split
        set_value("DEFAULT_DELAY", 0.0)

        # The default pause (seconds) after a split
        set_value("DEFAULT_PAUSE", 1.0)

        # The FPS used by splitter and ui_controller
        set_value("FPS", 30)

        # The location of split images
        set_value("LAST_IMAGE_DIR", "")

        # Determine whether screenshots should be opened using the machine's
        # default image viewer after capture
        set_value("OPEN_SCREENSHOT_ON_CAPTURE", False)

        # The number of decimal places shown when displaying match percents
        set_value("MATCH_PERCENT_DECIMALS", 0)

        # The text value of the split hotkey
        set_value("SPLIT_HOTKEY_NAME", "")

        # The text value of the reset hotkey
        set_value("RESET_HOTKEY_NAME", "")

        # The text value of the pause hotkey
        set_value("PAUSE_HOTKEY_NAME", "")

        # The text value of the undo hotkey
        set_value("UNDO_HOTKEY_NAME", "")

        # The text value of the skip split hotkey
        set_value("SKIP_HOTKEY_NAME", "")

        # The text value of the previous split hotkey
        set_value("PREVIOUS_HOTKEY_NAME", "")

        # The text value of the next split hotkey
        set_value("NEXT_HOTKEY_NAME", "")

        # The text value of the screenshot hotkey
        set_value("SCREENSHOT_HOTKEY_NAME", "")

        # The text value of the toggle global hotkeys hotkey
        set_value("TOGGLE_HOTKEYS_HOTKEY_NAME", "")

        # The pynput.keyboard.Key.vk value of the split hotkey
        set_value("SPLIT_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the reset hotkey
        set_value("RESET_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the pause hotkey
        set_value("PAUSE_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the undo split hotkey
        set_value("UNDO_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the skip split hotkey
        set_value("SKIP_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the previous split hotkey
        set_value("PREVIOUS_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the next split hotkey
        set_value("NEXT_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the screenshot hotkey
        set_value("SCREENSHOT_HOTKEY_CODE", "")

        # The pynput.keyboard.Key.vk value of the toggle global hotkeys hotkey
        set_value("TOGGLE_HOTKEYS_HOTKEY_CODE", "")

        # The UI theme
        set_value("THEME", "dark")

        # The aspect ratio
        set_value("ASPECT_RATIO", "4:3 (480x360)")

        # The last cv2 capture source index. This is an imperfect way to
        # remember the last video source used, since the indexes can reference
        # different sources at different times, but it's the best I can do in a
        # cross-platform environment
        set_value("LAST_CAPTURE_SOURCE_INDEX", 0)

        # Whether the program should try to open video on startup, or wait for
        # the user to press "reconnect video"
        set_value("START_WITH_VIDEO", False)

        # Whether the minimal view should be showing
        set_value("SHOW_MIN_VIEW", False)

        # Whether global hotkeys are enabled (default) or only local hotkeys
        set_value("GLOBAL_HOTKEYS_ENABLED", True)

        # Whether program checks for updates on launch
        set_value("CHECK_FOR_UPDATES", True)

    # Set last image dir to home dir if last image dir doesn't exist, or if the
    # path is empty
    last_image_dir = get_str("LAST_IMAGE_DIR")
    if len(last_image_dir) < 2 or not Path(last_image_dir).is_dir():
        home_dir = os.path.expanduser("~")
        set_value("LAST_IMAGE_DIR", home_dir)

    # Always start in full view if video doesn't come on automatically
    if not get_bool("START_WITH_VIDEO"):
        set_value("SHOW_MIN_VIEW", False)

    # Set correct video, split image width and height relative to aspect ratio
    aspect_ratio = get_str("ASPECT_RATIO")
    if aspect_ratio == "4:3 (480x360)":
        set_value("ASPECT_RATIO", "4:3 (480x360)")
        set_value("FRAME_WIDTH", 480)
        set_value("FRAME_HEIGHT", 360)
    elif aspect_ratio == "4:3 (320x240)":
        set_value("ASPECT_RATIO", "4:3 (320x240)")
        set_value("FRAME_WIDTH", 320)
        set_value("FRAME_HEIGHT", 240)
    elif aspect_ratio == "16:9 (512x288)":
        set_value("ASPECT_RATIO", "16:9 (512x288)")
        set_value("FRAME_WIDTH", 512)
        set_value("FRAME_HEIGHT", 288)
    elif aspect_ratio == "16:9 (432x243)":
        set_value("ASPECT_RATIO", "16:9 (432x243)")
        set_value("FRAME_WIDTH", 432)
        set_value("FRAME_HEIGHT", 243)


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
