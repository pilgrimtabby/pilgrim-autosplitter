# Copyright (c) 2024-2026 pilgrim_tabby

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Wrapper for separate keyboard manip libraries to support cross-platform dev.
"""


import platform
import time
from typing import Callable, Optional, Tuple, Union

if platform.system() == "Windows" or platform.system() == "Darwin":
    # Don't import the whole pynput library since that takes a while
    from pynput import keyboard as pynput_keyboard
else:
    # Pynput doesn't work well on Linux, so use keyboard instead
    import keyboard


class UIKeyboardController:
    """Basic frontend wrapper for controlling the keyboard cross-platform.

    On Windows and MacOS, use pynput; on Linux, use keyboard. This wrapper
    lacks many basic functionalities of both libraries because it was designed
    to meet the current needs of Pilgrim Autosplitter. It provides a layer of
    abstraction to simplify development and maintanence in ui_controller.py.
    """

    def __init__(self) -> None:
        """Initialize the keyboard controller (required for pynput backend)."""
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self._controller = pynput_keyboard.Controller()
        else:
            self._controller = None

    def start_listener(
        self,
        on_press: Optional[Callable[..., None]] = None,
        on_release: Optional[Callable[..., None]] = None,
    ) -> None:
        """Start a keyboard listener.

        This method doesn't return the listener, because it's not required
        (yet) for this project, but it can/should be modified to do so if it
        becomes necessary (only possible w/ pynput).

        Args:
            on_press (callable | None): Function to be executed on key down. If
                None, call _do_nothing (pass). Default is None.
            on_release (callable | None): Function to be executed on key up. If
                None, call _do_nothing (pass). Default is None.
        """
        if on_press is None:
            on_press = self._do_nothing
        if on_release is None:
            on_release = self._do_nothing

        if platform.system() == "Windows" or platform.system() == "Darwin":
            keyboard_listener = pynput_keyboard.Listener(
                on_press=on_press, on_release=on_release
            )
            keyboard_listener.start()
        else:
            keyboard.on_press(on_press)
            keyboard.on_release(on_release)

    def press_and_release(self, key_code: str) -> None:
        """Press and release a hotkey.

        Args:
            key_code (str): A string representation of a pynput.keyboard.Key.vk
                value (or a keyboard.KeyboardEvent.name value on Linux).
                Passed as a string because this project uses QSettings, which
                converts all types to strings on some backends.
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            key_code = int(key_code)
            key = pynput_keyboard.KeyCode(vk=key_code)
            self._controller.press(key)
            self._controller.release(key)
        else:
            keyboard.send(key_code)

    def release(
        self, key: Union["pynput_keyboard.key", "keyboard.KeyboardEvent"]
    ) -> None:
        """Release a key.

        Args:
            key (str): A string representation of a key. This method WILL FAIL
                when using pynput if the key is not an alphanumeric key (e.g.
                passing "f12" or "enter" will not work).
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self._controller.release(key)
        else:
            keyboard.release(key)

    def parse_key_info(
        self, key: Union["pynput_keyboard.key", "keyboard.KeyboardEvent"]
    ) -> Tuple[str, Union[str, int]]:
        """Return a key's string name and its internal integer value.

        Args:
            key: A wrapper whose structure and contents depend on the backend.
                With pynput (Windows / MacOS), it's a pynput.keyboard.Key; with
                keyboard (Linux) it's a keyboard.KeyboardEvent).

        Returns:
            key_name (str): Name of the key in a human-readable format.
            key_code (str | int): With pynput, it's a "vk" code, or an integer
                representation of a key that varies by machine. With keybaord,
                it's the same as key_name.
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            try:
                return key.char, key.vk
            # Thrown when the key isn't an alphanumeric key
            except AttributeError:
                return str(key).replace("Key.", ""), key.value.vk
        else:
            return key.name, key.name

    def _print_key_info(
        self, key: Union["pynput_keyboard.key", "keyboard.KeyboardEvent"]
    ) -> None:
        """Print a key's string name and its internal integer value. For debug.

        Args:
            key: A wrapper whose structure and contents depend on the backend.
                With pynput (Windows / MacOS), it's a pynput.keyboard.Key; with
                keyboard (Linux) it's a keyboard.KeyboardEvent).
        """
        if platform.system() == "Windows" or platform.system() == "Darwin":
            try:
                print(f"Key name: {key.char} | Key code: {key.vk}")
            # Thrown when the key isn't an alphanumeric key
            except AttributeError:
                print(
                    f"Key name: {str(key).replace('Key.', '')} | Key code: {key.value.vk}"
                )
        else:
            print(f"Key name: {key.name} | Key code: {key.name}")

    def _do_nothing(self, *args, **kwargs) -> None:
        """Dummy method for when you don't want anything to happen."""
        pass


if __name__ == "__main__":

    # Test key names and codes -- press any key to see its values
    controller = UIKeyboardController()
    controller.start_listener(on_press=controller._print_key_info)
    while True:
        time.sleep(1)
