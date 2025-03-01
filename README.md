# NOTE

This is a dev branch that allows recording clips with audio. It should work fine, but the audio source name is currently hard coded in and I don't have plans to add the ability to manually adjust this in-app anytime soon. If someone would like to make some adjustments to allow this, that would be more than welcome. Until the ability to adjust the source is added, I won't consider this branch production-ready.

In addition, for the audio recording features to work, you must have [FFmpeg and ffprobe installed](https://formulae.brew.sh/formula/ffmpeg) and on your PATH.

# Pilgrim Autosplitter

Finally, a multi-platform image-based speedrun autosplitter!

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

* Make sure you have Python 3.8+ installed (Python 3.11+ is recommended for an optimal experience)

* Run `python -m pip install -r requirements.txt`

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.
> In addition, if using Python <=3.10, you may need to manually install PyQt5 using `python -m pip install pyqt5-tools`.

* Open the app with `python pilgrim_autosplitter.py`

If this is your first time using Python:

* Install the latest stable Python release (3.12 at this time) by clicking [here](https://www.python.org/downloads/).

> [!Important]
> When installing Python using the Python installer, you MUST check the box next to `Add Python to PATH`. If you don't, the next part won't work.

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open the Start Menu and search for "Command Prompt", then click enter to open it.

* Type `python -m pip install -r ` (with a space after it) into Command Prompt, then click and drag the file `requirements.txt` from Pilgrim Autosplitter's source code into Command Prompt. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen informing you that Python is installing the necessary third-party packages for running the app.

* In the source code folder, open the folder `src`. In Command Prompt, type `python ` (with a space after it), then click and drag the file `pilgrim_autosplitter.py` into Command Prompt, just like before, and press enter. If you did everything right, the program should open. You can minimize the Command Prompt window.

## MacOS

### Method 1: Download application

Download the latest MacOS build corresponding to your computer's architecture (`MacOS.Intel` or `MacOS.Silicon`) from the [most recent release page](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest). If you're not sure which option you should choose, see [this guide](https://support.apple.com/en-us/116943).

Extract and run Pilgrim Autosplitter.app. When prompted to allow access in System Settings (or System Preferences, depending on your MacOS version), do it. Then, navigate to `Privacy and Security > Accessibility` and toggle the app so it has permissions. You may need to close and restart the app. 

Known limitations:

* The MacOS build opens a Terminal window that can't be closed without shutting the program down.

* It takes a long time to boot up (at least 30 seconds on my M1 Macbook Air).

#### TROUBLESHOOTING

* If you get the following error: `“Pilgrim Autosplitter.app” cannot be opened because the developer cannot be verified.`

  * Right-click on the app, hold the `option` key, and press `open`. When the warning pops up, you should see a new option: `open`.

* If global hotkeys aren't working / you are seeing the following message: `This process is not trusted! Input event monitoring will not be possible until it is added to accessibility clients.`:

  * Make sure you've given the application accessibility permissions in `System Settings > Privacy and Security > Accessibility`. For good measure, allow access to the keyboard as well.

### Method 2: Run from source with Python

If you're familiar with Python:

* Make sure you have Python 3.8+ installed (Python 3.11+ is recommended for an optimal experience)

* Run `pip3 install -r requirements.txt`

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.
> In addition, if using Python <=3.10, you may need to manually install PyQt5 using `python -m pip install pyqt5-tools`.

* Open the app with `python3 pilgrim_autosplitter.py`

If this is your first time using Python:

* Install the latest stable Python release (3.12 at this time) by clicking [here](https://www.python.org/downloads/).

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open Terminal (press `cmd+space` to open Spotlight and search for "Terminal").

* Type `pip3 install -r ` (with a space after it) in Terminal, then click and drag the file `requirements.txt` from Pilgrim Autosplitter's source code into Terminal. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen informing you that Python is installing the necessary third-party packages for running the app.

* In the source code, open the folder `src`. In Terminal, type `python3 ` (with a space after it), then click and drag the file `pilgrim_autosplitter.py` into the Terminal, just like before, and press enter. If you did everything right, the program should open. You can minimize the Terminal window.

## Linux

### Method 1: Download application

Download the latest Linux build for your architecture (`Linux.AMD` or `Linux.ARM`) from the [most recent release page](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest). Extract Pilgrim Autosplitter and use the command line to run it AS ROOT (there is no other known way to make hotkeys work as intended).

Known limitations:

* Pilgrim Autosplitter on Linux must be run as root.

### Method 2: Run from source with Python

If you're on Linux, I assume you know what you're doing. Get the latest release [here](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/latest), use pip to install the dependencies in `requirements-linux.txt`, and run `src/pilgrim_autosplitter.py` as root. Python >=3.8 is required (Python 3.11+ is recommended for an optimal experience).

> [!Note]
> If installation hangs up when trying to download PyQt5, try running the following command: `python -m pip install pyqt5 --config-settings --confirm-license= --verbose`.
> Some users (including myself) have experienced a softlock when verifying the PyQt5 license; this should solve that problem.
> In addition, if using Python <=3.10, you may need to manually install PyQt5 using `python -m pip install pyqt5-tools`.
