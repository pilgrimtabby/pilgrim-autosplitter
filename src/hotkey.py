from pynput import keyboard


keyboard_controller = keyboard.Controller()

def press_hotkey(key_code: str):
    key_code = int(key_code)
    key = keyboard.KeyCode(vk=key_code)
    keyboard_controller.press(key)
    keyboard_controller.release(key)
