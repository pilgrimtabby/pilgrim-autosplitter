import platform
import subprocess
import time


class Hotkey:
    def __init__(self) -> None:
        pass

    @staticmethod
    def press(key_code: int):
        if platform.system() == "Windows":
            pass
        elif platform.system() == "Darwin":
            Hotkey._press_macos(key_code)
        else:
            pass  # No Linux support yet (sorry...)

    @staticmethod
    def _press_macos(key_code: int):
        start = time.perf_counter()
        subprocess.call(["osascript", "-e", f"tell application \"System Events\" to key code {key_code}"])
        print(time.perf_counter() - start)

Hotkey.press(0)


# aaaaaaaaaaaa