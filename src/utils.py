from enum import Enum, auto

from PyQt5.QtCore import QSettings


class PercentType(Enum):
    CURRENT = auto()
    HIGHEST = auto()
    THRESHOLD = auto()


settings = QSettings("pilgrim_tabby", "Pilgrim Universal Autosplitter")

if settings.value("SETTINGS_SET") is None:
    settings.setValue("SETTINGS_SET", True)
    settings.setValue("DEFAULT_THRESHOLD", .90)
    settings.setValue("DEFAULT_DELAY", 0)
    settings.setValue("DEFAULT_LOOP_COUNT", 0)
    settings.setValue("DEFAULT_PAUSE", 1)
    settings.setValue("FPS", 60) # my capture card does 60
    settings.setValue("LAST_IMAGE_DIR", "res")
    settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", False)
    settings.setValue("MATCH_PERCENT_DECIMALS", 0)
    settings.setValue("VERSION_NUMBER", "0.1.0-alpha")
    settings.setValue("SPLIT_HOTKEY", "space")
    settings.setValue("RESET_HOTKEY", "backspace")
    settings.setValue("PAUSE_HOTKEY", "down")
    settings.setValue("UNDO_HOTKEY", "left")
    settings.setValue("SKIP_HOTKEY", "right")
    settings.setValue("SCREENSHOT_HOTKEY", "s")
    settings.setValue("THEME", "dark")
    settings.setValue("ASPECT_RATIO", "4:3")
    settings.setValue("CAPTURE_SOURCE", "usb_camera")

if settings.value("ASPECT_RATIO") == "4:3":
    settings.setValue("FRAME_WIDTH", 480)
    settings.setValue("FRAME_HEIGHT", 360)
elif settings.value("ASPECT_RATIO") == "16:9":
    settings.setValue("FRAME_WIDTH", 512)
    settings.setValue("FRAME_HEIGHT", 288)
