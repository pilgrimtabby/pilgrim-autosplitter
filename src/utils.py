from enum import Enum, auto
import os
from PyQt5.QtCore import QSettings


def get_default_image_dir():
    pass



settings = QSettings("pilgrim_tabby", "Pilgrim Universal Autosplitter")

settings.setValue("FRAME_WIDTH", 480)
settings.setValue("FRAME_HEIGHT", 360)
settings.setValue("DEFAULT_THRESHOLD", .90)
settings.setValue("DEFAULT_DELAY", 0)
settings.setValue("DEFAULT_LOOP_COUNT", 0)
settings.setValue("DEFAULT_PAUSE", 1)
settings.setValue("DEFAULT_FPS", 100)
settings.setValue("LAST_IMAGE_DIR", None)
settings.setValue("OPEN_SCREENSHOT_ON_CAPTURE", False)
settings.setValue("MATCH_PERCENT_DECIMALS", 0)
settings.setValue("VERSION_NUMBER", "0.1.0-alpha")
settings.setValue("SPLIT_HOTKEY", "pause")
settings.setValue("RESET_HOTKEY", "pause")
settings.setValue("PAUSE_HOTKEY", "pause")
settings.setValue("UNDO_HOTKEY", "pause")
settings.setValue("SKIP_HOTKEY", "pause")


# print(settings.allKeys())
# print(settings.value("FRAME_WIDTH"))
# settings.setValue("DEFAULT_IMAGE_DIR", "res")

class PercentType(Enum):
    CURRENT = auto()
    HIGHEST = auto()
    THRESHOLD = auto()
