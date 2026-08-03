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
from typing import Callable, Optional, Tuple, Union

if platform.system() == "Windows" or platform.system() == "Darwin":
    # Don't import the whole pynput library since that takes a while
    from pynput import keyboard as pynput_keyboard
else:
    # Pynput doesn't work well on Linux, so use keyboard instead
    import keyboard

# macOS: keypad digit virtual keys are *not* contiguous (vk 90 is unused;
# keypad 8/9 are 91/92). Using vk - 0x52 wrongly maps keypad 8 to "Num 9".
# Aligned with pynput `lib/pynput/_util/darwin_vks.SYMBOLS` keypad entries.
_DARWIN_NUMPAD_DIGIT_VK = {
    82: 0,
    83: 1,
    84: 2,
    85: 3,
    86: 4,
    87: 5,
    88: 6,
    89: 7,
    91: 8,
    92: 9,
}


def _pynput_numpad_display_name(vk: int) -> Optional[str]:
    """Human-readable label for numeric keypad keys (Windows / macOS virtual keys)."""
    sys = platform.system()
    if sys == "Windows":
        if 96 <= vk <= 105:
            return f"Num {vk - 96}"
        operators = {
            106: "Num *",
            107: "Num +",
            109: "Num -",
            110: "Num .",
            111: "Num /",
        }
        return operators.get(vk)
    if sys == "Darwin":
        digit = _DARWIN_NUMPAD_DIGIT_VK.get(vk)
        if digit is not None:
            return f"Num {digit}"
        operators = {
            0x41: "Num .",
            0x43: "Num *",
            0x45: "Num +",
            0x47: "Num Clear",
            0x4B: "Num /",
            0x4C: "Num Enter",
            0x4E: "Num -",
            0x51: "Num =",
        }
        return operators.get(vk)
    return None


_darwin_pynput_events_patched = False


def _patch_darwin_pynput_listener_events() -> None:
    """Drop NSSystemDefined from pynput's macOS event mask.

    pynput converts NSSystemDefined CGEvents via NSEvent.eventWithCGEvent_ on
    the listener thread. On modern macOS that path can hit Caps Lock /
    Text Input Source APIs that require the main queue and abort with
    SIGTRAP (_dispatch_assert_queue_fail). We do not need media keys as
    hotkeys, so exclude that event type. See pynput#596.
    """
    global _darwin_pynput_events_patched
    if _darwin_pynput_events_patched or platform.system() != "Darwin":
        return
    from Quartz import (
        CGEventMaskBit,
        kCGEventFlagsChanged,
        kCGEventKeyDown,
        kCGEventKeyUp,
    )

    # Intentionally omit CGEventMaskBit(NSSystemDefined): that is what triggers
    # NSEvent.eventWithCGEvent_ for media keys / some Caps Lock system events.
    pynput_keyboard.Listener._EVENTS = (
        CGEventMaskBit(kCGEventKeyDown)
        | CGEventMaskBit(kCGEventKeyUp)
        | CGEventMaskBit(kCGEventFlagsChanged)
    )
    _darwin_pynput_events_patched = True


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
        on_press: Optional[Callable[..., None]],
        on_release: Optional[Callable[..., None]],
    ) -> None:
        """Start a keyboard listener.

        This method doesn't return the listener, because it's not required
        (yet) for this project, but it can/should be modified to do so if it
        becomes necessary (only possible w/ pynput).

        Args:
            on_press (callable | None): Function to be executed on key down. If
                None, call _do_nothing (pass).
            on_release (callable | None): Function to be executed on key up. If
                None, call _do_nothing (pass).
        """
        if on_press is None:
            on_press = self._do_nothing
        if on_release is None:
            on_release = self._do_nothing

        if platform.system() == "Windows" or platform.system() == "Darwin":
            _patch_darwin_pynput_listener_events()
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
                vk = key.vk
                numpad = _pynput_numpad_display_name(vk)
                if numpad is not None:
                    return numpad, vk
                ch = key.char
                if ch is not None:
                    return ch, vk
                return str(key).replace("Key.", ""), vk
            # Thrown when the key isn't an alphanumeric key
            except AttributeError:
                vk = key.value.vk
                numpad = _pynput_numpad_display_name(vk)
                if numpad is not None:
                    return numpad, vk
                return str(key).replace("Key.", ""), vk
        else:
            return key.name, key.name

    def _do_nothing(self, *args, **kwargs) -> None:
        """Dummy method for when you don't want anything to happen."""
        pass
