from enum import Enum, auto

from PyQt5.QtCore import QSettings


settings = QSettings("pilgrim_tabby", "Pilgrim Universal Autosplitter")
# print(settings.allKeys())
# print(settings.value("FRAME_WIDTH"))
# settings.setValue("name", value)


def convert_css_to_string(file: str):
    with open(file, "r") as f:
        css_file = f.read()
    return css_file


class PercentType(Enum):
    CURRENT = auto()
    HIGHEST = auto()
    THRESHOLD = auto()

# "SPLIT_HOTKEY"
# "RESET_HOTKEY"
# "PAUSE_HOTKEY"
# "UNDO_HOTKEY"
# "SKIP_HOTKEY"

# settings.setValue("SKIP_HOTKEY", settings.value("SPLIT_KEY"))