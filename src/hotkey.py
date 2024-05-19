import platform
from pynput import keyboard
import pyautogui


class Hotkey:
    controller = keyboard.Controller()
    pyautogui.PAUSE = 0.0000001
    def __init__(self) -> None:
        pass

    def type(self, key: str):
        if platform.system() == "Windows":
            pass
        elif platform.system() == "Darwin":
            self._type_macos(key)
        else:
            pass  # No Linux support yet (sorry...)

    def _type_macos(self, key: int):
        # start = time.perf_counter()
        self.controller.press(keyboard.Key.space)
        self.controller.release(keyboard.Key.space)
        # print(time.perf_counter() - start)

# aaaaa