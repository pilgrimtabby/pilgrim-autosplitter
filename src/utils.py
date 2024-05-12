import os
from enum import Enum, auto

import cv2
import numpy
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QImage, QPixmap


class PercentType(Enum):
    CURRENT = auto()
    HIGHEST = auto()
    THRESHOLD = auto()


def frame_to_pixmap(frame: numpy.ndarray, is_split=False):
    if is_split:
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGBA8888).rgbSwapped()  # Make sure alpha channel is included, swap red and blue values
    else:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # No alpha
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
    return QPixmap.fromImage(frame_img)


settings = QSettings("pilgrim_tabby", "Pilgrim Autosplitter")
if settings.value("SETTINGS_SET") is None:
    home_dir = os.path.expanduser("~")
    settings.setValue("SETTINGS_SET", True)
    settings.setValue("DEFAULT_THRESHOLD", .90)
    settings.setValue("DEFAULT_DELAY", 0)
    settings.setValue("DEFAULT_LOOP_COUNT", 0)
    settings.setValue("DEFAULT_PAUSE", 1)
    settings.setValue("FPS", 60) # most capture cards do 30 or 60
    settings.setValue("LAST_IMAGE_DIR", home_dir)
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
    settings.setValue("ASPECT_RATIO", "4:3 (480x360)")
    settings.setValue("LAST_CAPTURE_SOURCE_INDEX", 0)
    settings.setValue("START_WITH_VIDEO", False)
    settings.setValue("SHOW_MIN_VIEW", False)
    settings.setValue("GLOBAL_HOTKEYS", True)

if not settings.value("START_WITH_VIDEO"):
    settings.setValue("SHOW_MIN_VIEW", False)

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
