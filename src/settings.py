import os
from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QKeySequence


settings = QSettings("pilgrim_tabby", "Pilgrim Autosplitter")

def get_str(key):
    return str(settings.value(key))

def get_bool(key):
    if settings.value(key) == "False":
        return False
    else:
        return True
    
def get_int(key):
    return int(settings.value(key))

def get_float(key):
    return float(settings.value(key))

def get_qkeysequence(key):
    return QKeySequence(str(settings.value(key)))

def set_value(key: str, value: any):
    settings.setValue(key, str(value))

def load_defaults():
    if get_str("SETTINGS_SET") != "yes":
        set_value("SETTINGS_SET", "yes")
        set_value("DEFAULT_THRESHOLD", .90)
        set_value("DEFAULT_DELAY", 0)
        set_value("DEFAULT_LOOP_COUNT", 0)
        set_value("DEFAULT_PAUSE", 1)
        set_value("FPS", 60)
        set_value("OPEN_SCREENSHOT_ON_CAPTURE", False)
        set_value("MATCH_PERCENT_DECIMALS", 0)
        set_value("VERSION_NUMBER", "0.0.1")
        set_value("SPLIT_HOTKEY_TEXT", "")
        set_value("RESET_HOTKEY_TEXT", "")
        set_value("PAUSE_HOTKEY_TEXT", "")
        set_value("UNDO_HOTKEY_TEXT", "")
        set_value("SKIP_HOTKEY_TEXT", "")
        set_value("PREVIOUS_HOTKEY_TEXT", "")
        set_value("NEXT_HOTKEY_TEXT", "")
        set_value("SCREENSHOT_HOTKEY_TEXT", "")
        set_value("SPLIT_HOTKEY_KEY_SEQUENCE", "")
        set_value("RESET_HOTKEY_KEY_SEQUENCE", "")
        set_value("PAUSE_HOTKEY_KEY_SEQUENCE", "")
        set_value("UNDO_HOTKEY_KEY_SEQUENCE", "")
        set_value("SKIP_HOTKEY_KEY_SEQUENCE", "")
        set_value("PREVIOUS_HOTKEY_KEY_SEQUENCE", "")
        set_value("NEXT_HOTKEY_KEY_SEQUENCE", "")
        set_value("SCREENSHOT_HOTKEY_KEY_SEQUENCE", "")
        set_value("THEME", "dark")
        set_value("ASPECT_RATIO", "4:3 (480x360)")
        set_value("LAST_CAPTURE_SOURCE_INDEX", 0)
        set_value("START_WITH_VIDEO", False)
        set_value("SHOW_MIN_VIEW", False)

    # Set last image dir to home dir if last image dir doesn't exist
    if not Path(get_str("LAST_IMAGE_DIR")).is_dir():
        home_dir = os.path.expanduser("~")
        set_value("LAST_IMAGE_DIR", home_dir)

    # Always start in full view if video doesn't come on automatically
    if not get_bool("START_WITH_VIDEO"):
        set_value("SHOW_MIN_VIEW", False)

    # Set correct video and split image width and height relative to aspect ratio
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
