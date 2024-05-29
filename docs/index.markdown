# Pilgrim Autosplitter for MacOS

Finally, an image-based autosplitter for MacOS!

![Demonstration GIF](../resources/demo.gif)

Table of Contents
=================

* [Pilgrim Autosplitter](#pilgrim-autosplitter)
   * [Introduction](#works-on-macos-and-windows)
   * [Usage](#usage)
      * [Connect Video](#connect-video)
      * [Create Split Images](#create-split-images)
   * [Settings](#settings)
   * [Hotkeys](#hotkeys)
   * [Customize Splits](#customize-splits)
      * [Threshold](#threshold)
      * [Delay](#delay)
      * [Pause](#pause)
      * [Loops](#loops)
      * [Special Options](#special-options)
   * [Installation](#installation)
      * [MacOS](#macos)
      * [Windows](#windows)
      * [Linux](#linux)

# Works on MacOS and Windows

Are you a speedrunner who wants to use an autosplitter, but doesn't have access to a Windows PC?

Pilgrim Autosplitter was designed for MacOS users to fill the gap left by other image-based autosplitters, which generally only support Windows.

This program has only been minimally tested on Windows, so there may be unknown issues. If you encounter problems or have an idea for an improvement, [submit an issue](https://github.com/pilgrimtabby/pilgrim-autosplitter/issues) or [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

I don't have plans to introduce Linux support, but if you're interested in adding such support, feel free to [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls).

# Usage

## Connect Video

### Capture Card

If you're using a capture card, all you need to do is have it connected to your computer. In Pilgrim Autosplitter, click the Next Source button until your capture card feed appears.

> [!NOTE]  
> Because of limitations related to video capturing backends on MacOS, you have to click through each source until you find the one you want. This might trigger webcams or other video capture devices, so don't be alarmed; no one is spying on you.

### OBS Virtual Camera

If you're not using a capture card, the recommended capture method is OBS Virtual Camera. You can connect any window on your computer to the camera in OBS. Once OBS Virtual Camera is open, click the Next Source button until your game feed appears.

## Create Split Images

Now that your video's connected, let's make some splits!

Press the Take Screenshot button to take a screenshot of the currently displayed video frame. By default, these are saved to your home directory. Choose a custom folder by clicking the "Select Split Image Folder" button in the top left.

> [!TIP]  
> Press the Reset Splits button at any time to reload all images from your splits folder, allowing new and modified images to show up in Pilgrim Autosplitter.

Your speedgame may not have a reliable, repeatable frame for each split — that's fine! Try to identify some on-screen element the split always has, such as an icon or some text. See, for example, this split from The Legend of Zelda: Ocarina of Time:

![Example split 1](../resources/example-1.png)

My screen won't look exactly like this every time. However, the words on the screen are always in the same spot. I can use this fact to create a split image that will always return a match.

You can use any image editing software, but I recommend either of the following free tools:

* [paint.net](https://www.getpaint.net/) (Windows)

* [krita](https://krita.org/en/download/) (MacOS)

You can use the magic wand tool to extract unneeded elements from the split image. If you do, you'll end up with something like this:

![Example split 2](../resources/example-2.png)

Pilgrim Autosplitter only compares the video feed with non-transparent pixels, so once it sees the right on-screen text, it will split.

# Settings

This is the settings menu:

![Settings menu](../resources/settings-menu.png)

## Frames per second

The amount of frames per second you want to process. The lower this value is, the less CPU Pilgrim Autosplitter will use, but you might miss frames if you lower the FPS below your capture card's limit / the game's framerate. Minimum is 20, maximum is 60.

## Open screenshots

Choose whether Pilgrim Autosplitter opens images in your computer's default image viewer when you take screenshots.

## Default threshold

The percentage of similarity that the video feed must have with the current split image before splitting. If you find that splits are being triggered too easily, try increasing the default. You could also increase the value just for particular splits (see [Customize Splits](#customize-splits)).

## Default delay

The splitter will pause for this many seconds before splitting after it recognizes an image.

## Default pause

The splitter will not compare the video feed to the next split image for this many seconds after splitting. The minimum allowed pause is 1 second.

## GUI aspect ratio

This changes the size of your video feed and splits. Experiment to find the setting you like. Classic 4:3 resolutions, as well as modern 16:9 resolutions, are supported. This setting will NOT affect the splitter's accuracy, even if you switch aspect ratios frequently, because the splitter relies on internal images that are always the same size.

## Theme

Choose between light mode and dark mode.

## Start with video

Off by default. If checked, Pilgrim Autosplitter will try to connect to video as soon as it opens. Otherwise, you'll need to click Reconnect Video or Next Source to get a video feed connected.

## Global hotkeys

Allow global hotkeys. When off, hotkeys will still work when Pilgrim Autosplitter is in focus, but not when it's in the background.

# Hotkeys

A variety of hotkeys can be configured. Each hotkey can be assigned to only one key (i.e. NOT a combination of keys, such as `ctrl+m`).

## Start / split

Equivalent to the split hotkey in LiveSplit.

## Reset splits

Equivalent to the reset hotkey in LiveSplit.

## Pause timer

Equivalent to the pause hotkey in LiveSplit.

## Undo split

Equivalent to the undo hotkey in LiveSplit.

## Skip split

Equivalent to the skip hotkey in LiveSplit.

## Previous split

Go back one split. This hotkey is introduced so you can scroll quickly through splits without affecting the speedrun timer.

## Next split

Go forward one split. This hotkey is introduced so you can scroll quickly through splits without affecting the speedrun timer.

## Screenshot

Take a screenshot of the current video frame.

## Toggle global

Allow or disallow global hotkeys by pressing this key. This is convenient if you like to switch back and forth between windows and don't want to mess up your timer when typing.

# Customize Splits

If you want to use settings other than the defaults for individual splits, you can use the split name to set values.

When multiple values are desired, they should be surrounded by underscores except for the last one, like this:

> `001_mysplit_[5]_{b}_(85).png` The splitter will wait until the match percent goes above 85% and then lowers back beneath 85% before splitting, and it will not compare the video feed with the next split image for 5 seconds after splitting.

Here are examples for each option:

## Threshold

Change the [default threshold](#default-threshold) for this split only. Insert the value between parentheses `()`.

> Example: `001_mysplit_(95).png` The threshold match for this split is 95%.

## Delay

Change the [default delay](#default-delay) for this split only. Insert the value between pound signs `#`.

> Example: `001_mysplit_#5#.png` The splitter will wait 5 seconds before splitting after it finds a match.

## Pause

Change the [default pause](#default-pause) for this split only. Insert the value between brackets `[]`.

> Example: `001_mysplit_[120].png` The splitter will wait 2 minutes after splitting until it starts searching for the next match.

## Loops

Make a split loop. This can be useful if you are constantly splitting on the same image. The default loop amount is 0, so if you want the loop to repeat itself once, insert the value 1, and so on. Insert the value between `@`s.

> Example: `001_mysplit_@1@.png` The splitter will look for matches for this split twice instead of once.

## Special Options

There are three split types you can specify. Each one is specified by placing a letter between braces `{}`. 

> [!TIP]  
>These options can be used together, but the dummy option will always override the pause option.

### Pause split

A pause split is like a regular split, except the splitter will press the pause hotkey instead of the split hotkey when it finds a match. You could use this if, for example, you're running a game that's measured in game time and you regularly have to navigate menus between levels. Insert the value by typing a `p` between braces `{}`.

> Example: `001_mysplit_{p}.png` The splitter will pause your timer after it finds a match.

### Dummy split

Useful if you need to see a certain value to signal a split is coming up, but you don't want the timer to change when you get there. 

An example might be something like this: your split is a black screen, but you are going to encounter a variable number of black screens before the timer should split. However, you know a certain dialog will appear on the screen immediately before the correct black screen appears. You can set the dialog as a dummy split, and then the splitter will be ready to recognize the black screen when it appears. Insert the value by typing a `d` between braces `{}`.

> Example: `001_mysplit_{d}.png` The splitter will wait until it finds a match for this image, then move to the next image without doing anything.

### Below split

The splitter will not split when it finds a match. Instead, it will wait until the value is no longer matching before it splits.

> Example: `001_mysplit_{b}.png` Once the splitter finds a match, it will wait until the video feed is no longer matching before splitting.

# Installation

## MacOS

### Download application

> [!IMPORTANT]  
> This option is currently only available for silicon-based Macs. If you're not sure what kind of chip your computer has, see [Apple's guide](https://support.apple.com/en-us/116943). A build for Intel-based Macs will be released by the end of June. For now, you'll have to [run the app from source](#run-from-source-with-python).

Download the latest MacOS build by going to the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/) and downloading `pilgrim-autosplitter-v1.0.0.zip` (or whatever the newest version number is). Extract the app from the .zip folder.

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

* Run `pip3 install -r requirements.txt`

* Start the program with: `python3 pilgrim_autosplitter.py`

If you're NOT comfortable using Python:

* You need Python 3.9 or newer. [Install it here](https://www.python.org/downloads/).

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

* Run `python -m pip install -r requirements.txt`

* Start the program with: `python pilgrim_autosplitter.py`

If you're NOT comfortable using Python:

* You need Python 3.9 or newer. [Install it here](https://www.python.org/downloads/).

* Download Pilgrim Autosplitter's source code from the [most recent release](https://github.com/pilgrimtabby/pilgrim-autosplitter/releases/) (click on `Source code (zip)` or `Source code (tar.gz)`). Extract the files.

* Open Command Prompt (if you can't find it, open the Start Menu and search for "Command Prompt").

* Type `python -m pip install -r` (with a space after it) into Command Prompt, then click and drag the file `requirements.txt` from the program folder into Command Prompt. You should see the path to the file appear. Press enter, and you'll see a lot of text appear on your screen. That means Python is installing third-party packages needed to run Pilgrim Autosplitter.

* In the source code, open the folder called `src`. In Command Prompt, type `python` (with a space after it), then click and drag the file called `pilgrim_autosplitter.py` into Command Prompt, just like before, and press enter. If you did everything right, the program should open. You can minimize the Command Prompt window.

## Linux

I don't have a way to develop on Linux... sorry. If you're feeling motivated, feel free to [open a pull request](https://github.com/pilgrimtabby/pilgrim-autosplitter/pulls). Pilgrim Autosplitter is built to be cross-platform, and there shouldn't (in theory) be that much standing in the way of a working Linux implementation.
