# Copyright (c) 2024 pilgrim_tabby
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Store and manipulate split images.
"""


import glob
import math
import pathlib
import re
from typing import Tuple

import cv2
import numpy
from PyQt5.QtGui import QImage, QPixmap

import settings
from settings import (
    COMPARISON_FRAME_HEIGHT,
    COMPARISON_FRAME_WIDTH,
    MAX_LOOPS_AND_WAIT,
    MAX_THRESHOLD,
)


class SplitDir:
    """Maintain and modify a list of SplitImage objects.

    Attributes:
        current_image_index (int): The current index being used in list, if it
            exists.
        current_loop (int): The current split image's current loop, if it
            exists.
        list (list[_SplitImage]): A list of all split images in
            settings.get_str("LAST_IMAGE_DIR").
    """

    def __init__(self):
        """Initialize a list of SplitImage objects; set flags based on whether
        the list is empty.
        """
        self.list = self._get_split_images()
        if len(self.list) > 0:
            self.current_image_index = 0
            self.current_loop = 0
        else:
            self.current_image_index = None
            self.current_loop = None

    ##################
    #                #
    # Public Methods #
    #                #
    ##################

    def next_split_image(self) -> None:
        """Go to the next split image or, if current_loop < loops, to the next
        loop.
        """
        if self.current_loop == self.list[self.current_image_index].loops:
            if self.current_image_index < len(self.list) - 1:
                self.current_image_index += 1
                self.current_loop = 0

        else:
            self.current_loop += 1

    def previous_split_image(self) -> None:
        """Go to the previous split image or, if current_loop > 0, to the
        previous loop.
        """
        if self.current_loop == 0:
            if self.current_image_index > 0:
                self.current_image_index -= 1
                self.current_loop = self.list[self.current_image_index].loops

        else:
            self.current_loop -= 1

    def reset_split_images(self) -> None:
        """Recreate the split image list from scratch, resetting appropriate
        flags.

        Use the old list after all if the new list is empty, for thread safety.
        """
        new_list = self._get_split_images()
        if len(new_list) == 0:
            pass
        else:
            self.list = new_list

        self.current_image_index = 0
        self.current_loop = 0

    def set_default_threshold(self) -> None:
        """Update threshold in each SplitImage whose threshold is default."""
        default_threshold = settings.get_float("DEFAULT_THRESHOLD")
        for image in self.list:
            if image.threshold_is_default:
                image.threshold = default_threshold

    def set_default_delay(self) -> None:
        """Update delay_duration in each SplitImage whose delay_duration is
        default.
        """
        default_delay = settings.get_float("DEFAULT_DELAY")
        for image in self.list:
            if image.delay_is_default:
                image.delay_duration = default_delay

    def set_default_pause(self) -> None:
        """Update pause_duration in each SplitImage whose pause_duration is
        default.
        """
        default_pause = settings.get_float("DEFAULT_PAUSE")
        for image in self.list:
            if image.pause_is_default:
                image.pause_duration = default_pause

    def resize_images(self) -> None:
        """Regenerate the image, mask, and pixmap attributes of all splits.

        Useful when changing aspect ratios, since the size of the pixmap can
        change.

        #TODO: This method may not need to call get_image_and_mask, since the
        split image should always be the same size anyway.
        """
        for image in self.list:
            image.image, image.mask = image.get_image_and_mask()
            image.pixmap = image.get_pixmap()

    ###############
    #             #
    # Private API #
    #             #
    ###############

    def _get_split_images(self) -> list["_SplitImage"]:
        """Get a list of SplitImage objects from a directory.

        Currently supported image types include .png, .jpg, and .jpeg. Only
        .png is tested, and it is the only recommended image format.

        Returns:
            list[_SplitImage]: The list of SplitImage objects.
        """
        split_images = []
        dir_path = settings.get_str("LAST_IMAGE_DIR")
        if not pathlib.Path(dir_path).is_dir():
            return split_images

        image_paths = (
            glob.glob(f"{dir_path}/*.png")
            + glob.glob(f"{dir_path}/*.jpg")
            + glob.glob(f"{dir_path}/*.jpeg")
        )
        for image_path in sorted(image_paths):
            split_images += [self._SplitImage(image_path)]

        return split_images

    class _SplitImage:
        """Store and modify details attributes of a single split image.

        Attributes:
            below_flag (bool): Whether this split is a "below split".
            delay_duration (float): The amount of time the splitter will wait
                before splitting when a match is found.
            delay_is_default (bool): Whether this split's delay_duration is the
                default.
            dummy_flag (bool): Whether this split is a "dummy split".
            image (numpy.ndarray): The split image, stored in a numpy array.
            loops (int): The amount of times this split will loop.
            loops_is_default (bool): Whether this split's loop amount is the
                default.
            mask (numpy.ndarray): The mask, stored in a numpy array. Only
                images not covered by the mask are compared by the splitter.
            max_dist (float): The maximum possible Euclidean distance from the
                split image (used by splitter to determine overall match
                percent).
            name (str): The split name (no file extension or directory
                information).
            path (str): The full path to the split image.
            pause_duration (float): The amount of time the splitter will wait
                after splitting when a match is found.
            pause_flag (bool): Whether this split is a "pause split".
            pause_is_default (bool): Whether this split's pause_duration is the
                default.
            pixmap (QPixmap): A QPixmap of the split image.
            threshold (float): The match percent the splitter needs to reach to
                decide it has found a match.
            threshold_is_default (bool): Whether this split's threshold match
                percent is the default.
        """

        def __init__(self, image_path: str) -> None:
            """Set flags and read values from split image and pathname.

            Args:
                image_path (str): Path to the image.
            """
            self._path = image_path
            self.name = pathlib.Path(image_path).stem
            self.image, self.mask = self.get_image_and_mask()
            self.max_dist = self._get_max_dist()
            self.pixmap = self.get_pixmap()
            self.below_flag, self.dummy_flag, self.pause_flag = (
                self._get_flags_from_name()
            )
            self.delay_duration, self.delay_is_default = self._get_delay_from_name()
            self.pause_duration, self.pause_is_default = self._get_pause_from_name()
            self.threshold, self.threshold_is_default = self._get_threshold_from_name()
            self.loops, self.loops_is_default = self._get_loops_from_name()

        ##################
        #                #
        # Public Methods #
        #                #
        ##################

        def get_image_and_mask(self) -> Tuple[numpy.ndarray, numpy.ndarray]:
            """Read a split image from a file and generate a mask.

            If the split image has an alpha channel (transparency), strip the
            alpha channel off and use it as a mask. Doing this will ensure that
            the splitter only checks the non-transparent parts of the image,
            allowing the user to make split images that look for certain things
            and ignore other elements (e.g., targeting a certain icon
            onscreen).

            If there is no alpha channel, splitter will compare the entire
            image, and no mask is needed.

            Returns:
                Tuple[numpy.ndarray, numpy.ndarray]: The split image and mask,
                respectively.
            """
            image = cv2.imread(self._path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(
                image,
                (COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT),
                interpolation=cv2.INTER_AREA,
            )

            if self._has_alpha_channel(image):
                mask = image[:, :, 3]
                image = image[:, :, 0:3]
            else:
                mask = None

            return image, mask

        def get_pixmap(self) -> QPixmap:
            """Generate a QPixmap from a numpy array.

            The process for converting numpy arrays to QImages varies depending
            on the number of channels, so I handle that by using different
            Format values. Working with BGR is necessary because cv2 uses BGR,
            not RGB.

            cv2.INTER_NEAREST is used to generate the image because it's the
            fastest interpolation method cv2 offers, and speed is important
            here, especially if the user has a large number of split images.
            Image quality is not a huge concern, since this image isn't being
            used for image matching.

            Returns:
                QPixmap: The generated QPixmap.
            """
            image = cv2.imread(self._path, cv2.IMREAD_UNCHANGED)
            image = cv2.resize(
                image,
                (settings.get_int("FRAME_WIDTH"), settings.get_int("FRAME_HEIGHT")),
                interpolation=cv2.INTER_NEAREST,
            )

            # QImage has no BGRA Format flag, or we would use that and omit 
            # .rgbSwapped()
            if self._has_alpha_channel(image):
                frame_qimage = QImage(
                    image, image.shape[1], image.shape[0], QImage.Format_RGBA8888
                ).rgbSwapped()
            else:
                frame_qimage = QImage(
                    image, image.shape[1], image.shape[0], QImage.Format_BGR888
                )
            return QPixmap.fromImage(frame_qimage)

        ###################
        #                 #
        # Private Methods #
        #                 #
        ###################

        def _get_max_dist(self) -> float:
            """Calculate the maximum possible Euclidean distance from an image.

            This value is used to normalize actual Euclidean distance values,
            and is calculated as follows: We assume the maximum distance
            possible between each pixel, which is 255 (assuming one image's
            pixels all had value 255, the maximum, and all the other image's
            pixels had value 0, the minimum). Then we calculate the Euclidean
            distance by taking the square root of the total number of pixels in
            the image, including all channels (length * width * 3 channels),
            and multiplying that value by 255.

            When images have transparency, we repeat this process, but only
            with the number of pixels that aren't in the alpha channel. That
            value is retrieved by calling cv2.countNonZero(mask) and
            multiplying that number by the number of channels, which is always
            3 in this method.

            See splitter._get_match_percent for details on Euclidean distance
            in general.

            Returns:
                float: The maximum Euclidean distance for the current split
                image.
            """
            if self.mask is None:  # No alpha channel
                return (
                    math.sqrt(COMPARISON_FRAME_WIDTH * COMPARISON_FRAME_HEIGHT * 3)
                    * 255
                )
            else:
                return math.sqrt(cv2.countNonZero(self.mask) * 3) * 255

        def _has_alpha_channel(self, image: numpy.ndarray) -> bool:
            """Show whether a given image with at least 3 channels has an alpha
            channel.

            image.shape returns a tuple with three values: the length, the
            width, and the number of channels (if more than one channel). If
            the number of channels is three, there is no alpha channel, since
            the alpha channel is always channel no. 4.

            If IndexError is thrown, that means there is only 1 channel. This,
            of course, means there is no alpha channel.

            #TODO: This method doesn't currently handle single-channel images
            like it should. The program doesn't crash, but single-channel
            images fail to generate a match percent when compares against video
            footage, and the QPixmap is also not generated correctly.

            Args:
                image (numpy.ndarray): The image to check.

            Returns:
                bool: True if the image contains an alpha channel, false
                otherwise.
            """
            try:
                return image.shape[2] == 4
            except IndexError:
                return False

        def _get_flags_from_name(self) -> Tuple[bool, bool, bool]:
            """Get split image's below, dummy, and pause flags by reading the
            filename.

            A below flag is indicated with a b between brackets, like this:
            _{b}_ (the splitter will not consider a match found until the
            current match percent rises above the threshold, then goes back
            beneath the threshold)

            A dummy flag is indicated with a d between brackets, like this:
            _{d}_ (the splitter will tell the ui_controller to advance to the
            next split, but not to press a hotkey)

            A pause flag is indicated with a b between brackets, like this:
            _{p}_ (the splitter will tell the ui_controller to advance to the
            next split, but to press the pause hotkey instead of the split
            hotkey)

            A split cannot be a dummy split and a pause split, because a dummy
            split implies no hotkey press. If both flags are set, the pause
            flag is removed.

            Returns:
                Tuple[bool, bool, bool]: below_flag, dummy_flag, and
                pause_flag, respectively (True if set, False if not).
            """
            flags = re.findall(r"_\{([bdp]+?)\}", self.name)
            if "d" in flags and "p" in flags:
                flags.remove("p")

            if "b" in flags:
                below_flag = True
            else:
                below_flag = False
            if "d" in flags:
                dummy_flag = True
            else:
                dummy_flag = False
            if "p" in flags:
                pause_flag = True
            else:
                pause_flag = False

            return below_flag, dummy_flag, pause_flag

        def _get_delay_from_name(self) -> float:
            """Set split image's delay duration before split by reading
            filename flags.

            Delay duration is set in the filename by placing a float between
            pound signs, like this: _#0.5#_ (the splitter will delay for 0.5
            seconds before splitting)

            Using is_digit guarantees that this method will not return negative
            numbers, which is what we want.

            Returns:
                float: The delay duration indicated in the filename, or the
                default if none is indicated.
            """
            delay = re.search(r"_\#(.+?)\#", self.name)
            if delay is None or not str(delay[1]).replace(".", "", 1).isdigit():
                return settings.get_float("DEFAULT_DELAY"), True
            return min(float(delay[1]), MAX_LOOPS_AND_WAIT), False

        def _get_pause_from_name(self) -> float:
            """Set split image's pause duration after split by reading filename
            flags.

            Pause duration is set in the filename by placing a float in
            brackets, like this: _[60]_ (the splitter will pause for 60 seconds
            after splitting)

            Using is_digit guarantees that this method will not return negative
            numbers, which is what we want.

            Returns:
                float: The pause duration indicated in the filename, or the
                default if none is indicated.
            """
            pause = re.search(r"_\[(.+?)\]", self.name)
            if pause is None or not str(pause[1]).replace(".", "", 1).isdigit():
                return settings.get_float("DEFAULT_PAUSE"), True
            return min(float(pause[1]), MAX_LOOPS_AND_WAIT), False

        def _get_threshold_from_name(self) -> float:
            """Set split image's threshold match percent by reading filename
            flags.

            Threshold match percent is set in the filename by placing a float
            in parenthesis, like this: _(95)_ (the threshold match percent is
            95%)

            Using is_digit guarantees that this method will not return negative
            numbers, which is what we want.

            Returns:
                float: The threshold match percent indicated in the filename,
                or the default if none is indicated.
            """
            threshold = re.search(r"_\((.+?)\)", self.name)
            if threshold is None or not str(threshold[1]).replace(".", "", 1).isdigit():
                return settings.get_float("DEFAULT_THRESHOLD"), True
            return min(float(threshold[1]) / 100, MAX_THRESHOLD), False

        def _get_loops_from_name(self) -> int:
            """Set split image's loop count by reading filename flags.

            Loop amount is set in the filename by placing an integer between
            two @s, like this: _@4@_ (the image loops 4 extra times)

            Using is_digit guarantees that this method will not return negative
            numbers, which is what we want.

            Returns:
                int: The number of loops indicated in the filename, or the
                default if none is indicated.
            """
            loops = re.search(r"_\@(.+?)\@", self.name)
            if loops is None or not loops[1].isdigit():
                return settings.get_int("DEFAULT_LOOP_COUNT"), True
            return min(int(loops[1]), MAX_LOOPS_AND_WAIT), False
