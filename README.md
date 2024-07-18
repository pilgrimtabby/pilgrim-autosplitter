# Pilgrim Autosplitter

Finally, a truly multi-platform image-based speedrun autosplitter!

![Demonstration GIF](resources/demo.gif)

Pilgrim Autosplitter was designed to fill the gap left by other image-based speedrun autosplitters, which generally only run on Windows.

Bring your best speedgame on Windows, MacOS, and Linux (and whether you game on console or computer).

This program is still relatively new, so you may encounter bugs. If you do, or if you have an idea for a new feature or improvement, [submit an issue](https://github.com/pilgrimtabby/pilgrim-autosplitter/issues) or [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

# About

Use screenshots taken in-app to trigger splits (or other actions) while speedrunning. Never forget to split, accidentally miss a key, or get distracted during a PB-pace run again!

Table of contents:

- [Usage](#usage)
- [Installation](#installation)
   * [Windows](#windows)
      + [Method 1: Download Application](#method-1-download-application)
      + [Method 2: Run from source with Python](#method-2-run-from-source-with-python)
   * [MacOS](#macos)
      + [Method 1: Download application](#method-1-download-application-1)
         - [TROUBLESHOOTING](#troubleshooting)
      + [Method 2: Run from source with Python](#method-2-run-from-source-with-python-1)
   * [Linux](#linux)
      + [Method 1: Download application](#method-1-download-application-2)
      + [Method 2: Run from source with Python](#method-2-run-from-source-with-python-2)

# Usage

For usage instructions and a detailed tutorial with pictures, see the [Pilgrim Autosplitter user manual](https://pilgrimtabby.github.io/pilgrim-autosplitter/).

# Installation

The installation method depends on your operating system.

## Windows

### Method 1: Download Application

Download the latest Windows build (Pilgrim.Autosplitter.Windows.v1.x.x) from the [most recent release page](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest). Unzip and run Pilgrim Autosplitter.exe.

### Method 2: Run from source with Python

If you're familiar with Python:

* Make sure you have Python 3.10+ installed

* Run `python -m pip install -r requirements.txt`

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.

* Open the app with `python pilgrim_autosplitter.py`

If this is your first time using Python:

* Install the latest version of Python (3.12 at this time) by clicking [here](https://www.python.org/downloads/).

> [!Important]
> When installing Python using the Python installer, you MUST check the box next to `Add Python to PATH`. If you don't, the next part won't work.

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open the Start Menu and search for "Command Prompt", then click enter to open it.

* Type `python -m pip install -r ` (with a space after it) into Command Prompt, then click and drag the file `requirements.txt` from Pilgrim Autosplitter's source code into Command Prompt. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen informing you that Python is installing the necessary third-party packages for running the app.

* In the source code folder, open the folder `src`. In Command Prompt, type `python ` (with a space after it), then click and drag the file `pilgrim_autosplitter.py` into Command Prompt, just like before, and press enter. If you did everything right, the program should open. You can minimize the Command Prompt window.

## MacOS

### Method 1: Download application

> [!IMPORTANT]  
> This option is currently only available for silicon-based Macs. If you're not sure what kind of chip your computer has, see [Apple's guide](https://support.apple.com/en-us/116943). A build for Intel-based Macs will be released soon. For now, if you're using an Intel-based Mac, you'll have to [run the app from source](#run-from-source-with-python).

Download the latest MacOS build (Pilgrim.Autosplitter.MacOS.v1.x.x) from the [most recent release page](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest). Extract and run Pilgrim Autosplitter.app.

Known limitations:

* The MacOS build opens a Terminal window that can't be closed without shutting the program down.

* It takes a long time to boot up (at least 30 seconds on my M1 Macbook Air).

#### TROUBLESHOOTING

* If you get the following error: `“Pilgrim Autosplitter.app” cannot be opened because the developer cannot be verified.`

  * Right-click on the app, hold the `option` key, and press `open`. When the warning pops up, you should see a new option: `open`.

* If global hotkeys aren't working:

  * Make sure you've given the application accessibility permissions in `System Settings > Privacy and Security > Accessibility`. Pilgrim Autosplitter needs access to the keyboard so it can enter hotkeys.

* If you see an error in the Terminal window about using the wrong kind of CPU:

  * You're likely using an Intel-based Mac, not a silicon-based Mac. Use the other installation method below.

### Method 2: Run from source with Python

If you're familiar with Python:

* Make sure you have Python 3.10+ installed

* Run `pip3 install -r requirements.txt`

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.

* Open the app with `python3 pilgrim_autosplitter.py`

If this is your first time using Python:

* Install the latest version of Python (3.12 at this time) by clicking [here](https://www.python.org/downloads/).

> [!Important]
> When installing Python using the Python installer, you MUST check the box next to `Add Python to PATH`. If you don't, you won't be able to use Python in the command line.

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open Terminal (press `cmd+space` to open Spotlight and search for "Terminal").

* Type `pip install -r ` (with a space after it) in Terminal, then click and drag the file `requirements.txt` from Pilgrim Autosplitter's source code into Terminal. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen informing you that Python is installing the necessary third-party packages for running the app.

* In the source code, open the folder `src`. In Terminal, type `python3 ` (with a space after it), then click and drag the file `pilgrim_autosplitter.py` into the Terminal, just like before, and press enter. If you did everything right, the program should open. You can minimize the Terminal window.

## Linux

### Method 1: Download application

> [!IMPORTANT]  
> This option is currently only available for Linux distributions running on ARM-based architecture (tested on Ubuntu 20.04). Sorry.

Download the latest Linux build (Pilgrim.Autosplitter.Linux.v1.x.x) from the [most recent release page](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest). Extract Pilgrim Autosplitter and use the command line to run it AS ROOT (there is no other known way to make hotkeys work as intended).

Known limitations:

* Pilgrim Autosplitter on Linux must be run as root.

* There is no AMD-compatible executible build yet (the source code should work fine on AMD architectures, though).

### Method 2: Run from source with Python

If you're on Linux, I assume you know what you're doing. Get the latest release [here](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest), use pip to install the dependencies in `requirements-linux.txt`, and run `src/pilgrim_autosplitter.py` as root.

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.
