import platform
import subprocess
import time
from pynput import keyboard
import pyautogui


class Hotkey:
    controller = keyboard.Controller()
    pyautogui.PAUSE = 0.0000001
    def __init__(self) -> None:
        pass

    def press(self, key: str):
        if platform.system() == "Windows":
            pass
        elif platform.system() == "Darwin":
            self._press_macos(key)
        else:
            pass  # No Linux support yet (sorry...)

    def _press_macos(self, key: int):
        start = time.perf_counter()
        self.controller.press(keyboard.Key.space)
        self.controller.release(keyboard.Key.space)
        # self.controller.release(key)
        print(time.perf_counter() - start)

# aaaaa