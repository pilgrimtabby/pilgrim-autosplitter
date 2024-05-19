from pynput import keyboard


class Hotkey:
    controller = keyboard.Controller()
    def __init__(self) -> None:
        pass

    def type(self, key: str):
        self.controller.press(keyboard.Key.space)
        self.controller.release(keyboard.Key.space)
