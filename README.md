# Pilgrim Autosplitter for MacOS

Finally, an image-based speedrun autosplitter compatible with MacOS!

![Demonstration GIF](resources/demo.gif)

Pilgrim Autosplitter was designed to fill the gap left by other image-based speedrun autosplitters, which are generally incompatible with MacOS.

Bring your best speedgame whether you’re running on console, MacOS, or PC.

## Compatible with MacOS and Windows

This program has only been minimally tested on Windows, so there may be unknown issues. If you encounter problems or have an idea for an improvement, [submit an issue](https://github.com/pilgrimtabby/pilgrim-autosplitter/issues) or [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

I don't have plans to introduce Linux support, but if you're interested in adding such support, feel free to [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

# Usage

For usage instructions, see the [Pilgrim Autosplitter user manual](https://pilgrimtabby.github.io/pilgrim-autosplitter/).

# Installation

The installation method depends on your operating system.

## MacOS

### Download application

> [!IMPORTANT]  
> This option is currently only available for silicon-based Macs. If you're not sure what kind of chip your computer has, see [Apple's guide](https://support.apple.com/en-us/116943). A build for Intel-based Macs will be released by the end of June. For now, if you're using an Intel-based Mac, you'll have to [run the app from source](#run-from-source-with-python).

Download the latest MacOS build by going to the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/) and downloading `pilgrim-autosplitter-v1.0.1.zip` (or whatever the newest version number is). Extract the app from the .zip folder.

Pros:

* Only one file

* Easy to install and use.

Cons:

* A quirk of building this program on MacOS is that opening it always opens a Terminal window that can't be closed without shutting the program down too. However, the Terminal window can be easily minimzed and ignored.

* Pilgrim Autosplitter takes much longer to load when running from the executible (about 30 seconds on my M1 Macbook Air).

* The app's custom icon doesn't show up correctly in the dock (unfortunately, there is apparently no known way to persist MacOS icons for files in Github repositories).

* None of these problems exist when [running from source](#run-from-source-with-python), but running from source is much less convenient and can be tricky if you don't have much experience.

TROUBLESHOOTING

* If you get the following error: `“Pilgrim Autosplitter.app” cannot be opened because the developer cannot be verified.`

  * Right-click on the app, hold the `option` key, and press `open`. When the warning pops up, you should see a new option: `open`.

* If global hotkeys aren't working:

  * Make sure you've given the application accessibility permissions in `System Settings > Privacy and Security > Accessibility`. Pilgrim Autosplitter needs access to the keyboard so it can enter hotkeys.

* If you see an error in the Terminal window about using the wrong kind of CPU:

  * You're likely using an Intel-based Mac, not a silicon-based Mac. Use the other installation method below.

### Run from source with Python

If you're comfortable using Python:

* Make sure you have Python 3.9+ installed

* `pip3 install -r requirements.txt`

* `python3 pilgrim_autosplitter.py`

If you're NOT comfortable using Python:

* You need Python 3.9 or newer. [Install it here](https://www.python.org/downloads/).

> [!Important]
> When installing Python using the Python installer, you MUST check the box next to `Add Python to PATH`. If you don't, you won't be able to use Python in the command line.

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open Terminal (if you can't find it, press `cmd+space` to open Spotlight and search for "Terminal").

* Type `pip install -r` (with a space after it) into the open Terminal window, then click and drag the file `requirements.txt` from the program folder into Terminal. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen. That means Python is installing third-party packages needed to run Pilgrim Autosplitter.

* In the source code, open the folder called `src`. In Terminal, type `python3` (with a space after it), then click and drag the file called `pilgrim_autosplitter.py` into the Terminal, just like before, and press enter. If you did everything right, the program should open. You can minimize the Terminal window.

Pros:

* More flexible usage if you're comfortable using Python and the command line

* Much smaller file size

* Starts faster

* Terminal window can be closed if you use `bash` commands like `nohup`

Cons:

* Complicated installation process

* Lots of files

## Windows

### Run from source with Python

> [!WARNING]  
> It bears repeating that this program has only been tested minimally on Windows. There might be problems. Feel free to [submit an issue](https://github.com/pilgrimtabby/pilgrim-autosplitter/issues/) or [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

If you're comfortable using Python:

* Make sure you have Python 3.9+ installed

* `python -m pip install -r requirements.txt`

* `python pilgrim_autosplitter.py`

If you're NOT comfortable using Python:

* You need Python 3.9 or newer. [Install it here](https://www.python.org/downloads/).

> [!Important]
> When installing Python using the Python installer, you MUST check the box next to `Add Python to PATH`. If you don't, you won't be able to use Python in the command line.

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open Command Prompt (if you can't find it, open the Start Menu and search for "Command Prompt").

* Type `python -m pip install -r` (with a space after it) into Command Prompt, then click and drag the file `requirements.txt` from the program folder into Command Prompt. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen. That means Python is installing third-party packages needed to run Pilgrim Autosplitter.

* In the source code, open the folder called `src`. In Command Prompt, type `python` (with a space after it), then click and drag the file called `pilgrim_autosplitter.py` into Command Prompt, just like before, and press enter. If you did everything right, the program should open. You can minimize the Command Prompt window.

## Linux

I don't have access to a Linux development environment... sorry. If you're feeling motivated, feel free to [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls). Pilgrim Autosplitter is built to be cross-platform, and there shouldn't (in theory) be too much standing in the way of a working Linux implementation.
