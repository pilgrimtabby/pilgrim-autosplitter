import os

from PyQt5.QtCore import QSettings


settings = QSettings("pilgrim_tabby", "Pilgrim Autosplitter")
if settings.value("SETTINGS_SET") is None:
    home_dir = os.path.expanduser("~")
    settings.setValue("SETTINGS_SET", True)
    settings.setValue("DEFAULT_THRESHOLD", .90)
    settings.setValue("DEFAULT_DELAY", 0)
    settings.setValue("DEFAULT_LOOP_COUNT", 0)
    settings.setValue("DEFAULT_PAUSE", 1)
    settings.setValue("FPS", 60)
    settings.setValue("LAST_IMAGE_DIR", home_dir)
    settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", False)
    settings.setValue("MATCH_PERCENT_DECIMALS", 0)
    settings.setValue("VERSION_NUMBER", "0.1.0-alpha")
    settings.setValue("SPLIT_HOTKEY_TEXT", "")
    settings.setValue("RESET_HOTKEY_TEXT", "")
    settings.setValue("PAUSE_HOTKEY_TEXT", "")
    settings.setValue("UNDO_HOTKEY_TEXT", "")
    settings.setValue("SKIP_HOTKEY_TEXT", "")
    settings.setValue("PREVIOUS_HOTKEY_TEXT", "")
    settings.setValue("NEXT_HOTKEY_TEXT", "")
    settings.setValue("SCREENSHOT_HOTKEY_TEXT", "")
    settings.setValue("SPLIT_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("RESET_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("PAUSE_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("UNDO_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("SKIP_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("PREVIOUS_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("NEXT_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("SCREENSHOT_HOTKEY_KEY_SEQUENCE", None)
    settings.setValue("THEME", "dark")
    settings.setValue("ASPECT_RATIO", "4:3 (480x360)")
    settings.setValue("LAST_CAPTURE_SOURCE_INDEX", 0)
    settings.setValue("START_WITH_VIDEO", False)
    settings.setValue("SHOW_MIN_VIEW", False)

# Always start in full view if video doesn't come on automatically
if not settings.value("START_WITH_VIDEO"):
    settings.setValue("SHOW_MIN_VIEW", False)

# Set correct video and split image width and height relative to aspect ratio
aspect_ratio = settings.value("ASPECT_RATIO")
if aspect_ratio == "4:3 (480x360)":
    settings.setValue("ASPECT_RATIO", "4:3 (480x360)")
    settings.setValue("FRAME_WIDTH", 480)
    settings.setValue("FRAME_HEIGHT", 360)
if aspect_ratio == "4:3 (320x240)":
    settings.setValue("ASPECT_RATIO", "4:3 (320x240)")
    settings.setValue("FRAME_WIDTH", 320)
    settings.setValue("FRAME_HEIGHT", 240)
if aspect_ratio == "16:9 (512x288)":
    settings.setValue("ASPECT_RATIO", "16:9 (512x288)")
    settings.setValue("FRAME_WIDTH", 512)
    settings.setValue("FRAME_HEIGHT", 288)
if aspect_ratio == "16:9 (432x243)":
    settings.setValue("ASPECT_RATIO", "16:9 (432x243)")
    settings.setValue("FRAME_WIDTH", 432)
    settings.setValue("FRAME_HEIGHT", 243)
