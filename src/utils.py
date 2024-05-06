# Read these from settings eventually (at least the flag stuff)

from enum import Enum, auto


FRAME_WIDTH = 480
FRAME_HEIGHT = 360
DEFAULT_THRESHOLD = .9
DEFAULT_DELAY = 0
DEFAULT_LOOP_COUNT = 0
DEFAULT_PAUSE = 1
DEFAULT_FPS = 100
LAST_IMAGE_DIR = "res"
OPEN_SCREENSHOT_ON_CAPTURE = False
SPLIT_KEY = "space"
PAUSE_KEY = "p"
VERSION_NUMBER = "0.1.0-alpha"
MATCH_PERCENT_DECIMALS = 2


def convert_css_to_string(file: str):
    with open(file, "r") as f:
        css_file = f.read()
    return css_file


class PercentType(Enum):
    CURRENT = auto()
    HIGHEST = auto()
    THRESHOLD = auto()
