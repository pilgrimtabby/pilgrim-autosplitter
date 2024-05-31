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

"""Capture video and compare it to a template image.
"""


import threading
import time
from typing import Tuple

import cv2
import numpy
from PyQt5.QtGui import QImage, QPixmap

import settings
from settings import COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT
from splitter.split_dir import SplitDir


class Splitter:
    """Capture video and compare it to a split image.

    Video capture and image matching are both performed in their own dedicated
    threads, which means that thread safety is always a top priority when
    working with this class. _capture_thread saves information about the
    current frame to class attributes, which are in turn used by
    _compare_thread to generate a probability of match with the current split
    image. If a match is found, a flag is set indicating which type of split
    (dummy, normal, or pause) should occur.

    ui_controller is constantly accessing the public attributes of this class,
    whether or not the threads are active, which is why several of these
    attributes are set to None after use.

    Attributes:
        capture_thread (threading.Thread): Thread instance that reads and
            resizes images from a cv2.VideoCapture instance.
        changing_splits (bool): Flag set by ui_controller before telling
            self.splits to go to a new split image.
        comparison_frame (numpy.ndarray): Numpy array used to generate a
            comparison with a split image.
        current_match_percent (float): The most recent match percent between a
            frame and a split image.
        delay_remaining (float): The amount of time left (in seconds) until a
            planned split occurs.
        delaying (bool): Indicates whether _split is waiting before setting a
            split action flag.
        dummy_split_action (bool): When True, tells ui_controller to perform a
            dummy split action.
        frame_pixmap (QPixmap): QPixmap used to show video feed on UI.
        highest_match_percent (float): The highest match percent so far between
            a frame and a split image.
        normal_split_action (bool): When True, tells ui_controller to perform a
            normal split action.
        pause_split_action (bool): When True, tells ui_controller to perform a
            pause split action.
        splits (SplitDir): The directory of split images currently in use.
        suspend_remaining (float): The amount of time left (in seconds) before
            the end of a pause after a split.
        suspended (bool): Indicates whether _compare_thread is alive.
        target_fps (int): The framerate set by the user.
        waiting_for_split_change (bool): Indicates to ui_controller that
            _look_for_match received its changing_splits request and is waiting
            for the new split.
    """

    def __init__(self) -> None:
        """Set all flags and values needed to operate _capture_thread and
        _compare_thread.
        """
        self.target_fps = settings.get_int("FPS")
        self._capture_max_fps = 60
        self._fps_adjust_factor = 1.22  # Roughly the amount needed here; YMMV
        self._interval = self._get_interval()

        # _capture_thread
        self.comparison_frame = None
        self.frame_pixmap = None
        self.capture_thread = threading.Thread(target=self._capture)
        self._ui_frame = None
        self._cap = None
        self._capture_thread_finished = False

        # _compare_thread
        self.splits = SplitDir()
        self.current_match_percent = None
        self.highest_match_percent = None
        self.delaying = False
        self.delay_remaining = None
        self.suspended = True
        self.suspend_remaining = None
        self.pause_split_action = False
        self.dummy_split_action = False
        self.normal_split_action = False
        self._compare_thread = threading.Thread(target=self._compare)
        self._compare_thread_finished = False

        self.changing_splits = False
        self.waiting_for_split_change = False

        # _split_thread variables
        self._split_thread = threading.Thread(target=self._set_normal_split_action)
        self._split_thread_finished = False

    ##################
    #                #
    # Public Methods #
    #                #
    ##################

    def start(self) -> None:
        """Start _capture_thread and, if possible, start _compare_thread.

        It is essential to ensure that all previous _capture_threads and
        _compare_threads have been safely exited before calling this method.
        """
        self._start_capture_thread()
        if len(self.splits.list) > 0:
            self.start_compare_thread()

    def safe_exit_all_threads(self) -> None:
        """Safely kill _capture_thread.

        Because killing _capture_thread also kills _compare_thread, this will
        always safely exit _compare_thread too.
        """
        self._capture_thread_finished = True
        if self.capture_thread.is_alive():
            self.capture_thread.join()
        if self._split_thread.is_alive():
            self._split_thread_finished = True
            self._split_thread.join()

    def start_compare_thread(self) -> None:
        """Safely start _compare_thread.

        It is essential to ensure that all previous _compare_threads have been
        safely exited before calling this method.
        """
        self._compare_thread = threading.Thread(target=self._compare)
        self._compare_thread_finished = False
        self._compare_thread.daemon = True
        self._compare_thread.start()
        self.suspended = False

    def safe_exit_compare_thread(self) -> None:
        """Safely kill _compare_thread.
        
        Also kills _split_thread, since _split_thread should only be active if
        _compare_thread is active.
        """
        if self._compare_thread.is_alive():
            self._compare_thread_finished = True
            self._compare_thread.join()
        if self._split_thread.is_alive():
            self._split_thread_finished = True
            self._split_thread.join()
        self.suspended = True

    def set_next_capture_index(self) -> None:
        """Try to find the next valid cv2 capture index, if it exists.

        cv2 capture indexes can be separated by invalid indexes (for example, 0
        and 2 could be valid indexes but not 1). To account for this, this
        method will try 3 invalid indexes before returning to index 0.

        Saves the new index to settings, has no return value.
        """
        source = settings.get_int("LAST_CAPTURE_SOURCE_INDEX") + 1
        found_valid_source = False
        tries = 0
        while tries < 3:
            test_cap = cv2.VideoCapture(source)
            if test_cap.isOpened():
                found_valid_source = True
                break
            else:
                source += 1
                tries += 1
        if not found_valid_source:
            source = 0  # Give up, go back to first possible index
        settings.set_value("LAST_CAPTURE_SOURCE_INDEX", source)

    def toggle_suspended(self) -> None:
        """Stop _compare_thread if it's running; else, start it if possible."""
        if self.suspended:
            self.safe_exit_compare_thread()
            if len(self.splits.list) > 0:
                self.start_compare_thread()
        else:
            self.safe_exit_compare_thread()

    ###################################
    #                                 #
    # Private _capture_thread Methods #
    #                                 #
    ###################################

    def _start_capture_thread(self) -> None:
        """Safely start capture_thread.

        It is essential to ensure that all previous _capture_threads have been
        safely exited before calling this method.
        """
        self._cap = self._open_capture()
        self.capture_thread = threading.Thread(target=self._capture)
        self._capture_thread_finished = False
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _open_capture(self) -> cv2.VideoCapture:
        """Open and configure a cv2 VideoCapture.

        Sets CAP_PROP_BUFFERSIZE to 1 to reduce stuttering.
        Sets CAP_PROP_FRAME_WIDTH and CAP_PROP_FRAME_HEIGHT to their respective
        values because these appear to be the smallest available values. The
        smaller the capture's width and height, the fast images can be
        downscaled, and the less CPU is required to do so.
        Sets self._capture_max_fps to the capture's maximum FPS on platforms
        where this is supported. This is done to prevent unnecessary
        comparisons from being generated in _compare due to a mismatch between
        the user's selected framerate and a capture-imposed cap which is lower.

        Returns:
            cv2.VideoCapture: The initialized and configured VideoCapture.
        """
        cap = cv2.VideoCapture(settings.get_int("LAST_CAPTURE_SOURCE_INDEX"))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        try:
            self._capture_max_fps = cap.get(cv2.CAP_PROP_FPS)
        except cv2.error:
            self._capture_max_fps = 60
        return cap

    def _capture(self) -> None:
        """Read frames from a capture source, resize them, and expose them to
        _compare and ui_controller.

        self.comparison_frame should always be 320x240. This helps with results
        consistency when matching split images; it also saves a lot of time and
        CPU power when making comparisons in _compare, and saves users space
        because they don't have to store dozens of massive image files. The
        ui_frame, on the other hand, is designed to be the size the user
        chooses, so it is resized accordingly and converted into a QPixmap.

        The choices of cv2.INTER_LINEAR and cv2.INTER_NEAREST are deliberate.
        cv2.INTER_NEAREST provides the fastest method, by far, for downscaling
        images, but the quality is much worse and can throw off comparisons.
        For that reason, I use it when reading the ui_frame, but stick to
        cv2.INTER_LINEAR for the comparison_frame.

        cv2.INTER_LINEAR is the next fastest setting after cv2.INTER_NEAREST.
        Its quality is significantly better for only a minor performance cost,
        which makes it a good choice for image matching.

        This method continues indefinitely until self._capture_thread_finished
        is set.
        """
        start_time = time.perf_counter()
        while not self._capture_thread_finished:

            # We don't need to wait if we are hitting the max capture fps,
            # since cap.read() blocks until the next frame is available anyway.
            # So we only do this if we are targeting a framerate that is lower
            # than the max fps
            if self.target_fps < self._capture_max_fps:
                current_time = time.perf_counter()
                if current_time - start_time < self._interval:
                    time.sleep(self._interval - (current_time - start_time))
                start_time = time.perf_counter()

            frame = self._cap.read()[1]
            if frame is None:  # Video feed is down, kill the thread
                self._capture_thread_finished = True
                break

            if settings.get_str("ASPECT_RATIO") == "4:3 (320x240)":
                self.comparison_frame = cv2.resize(
                    frame,
                    (settings.get_int("FRAME_WIDTH"), settings.get_int("FRAME_HEIGHT")),
                    interpolation=cv2.INTER_LINEAR,
                )

                # Don't need to generate a separate ui_frame -- the
                # comparison_frame is already the right size
                if settings.get_bool("SHOW_MIN_VIEW"):
                    self._ui_frame = None
                else:
                    self._ui_frame = self.comparison_frame

            else:
                self.comparison_frame = cv2.resize(
                    frame,
                    (COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT),
                    interpolation=cv2.INTER_LINEAR,
                )
                if settings.get_bool("SHOW_MIN_VIEW"):
                    self._ui_frame = None
                else:
                    self._ui_frame = cv2.resize(
                        frame,
                        (
                            settings.get_int("FRAME_WIDTH"),
                            settings.get_int("FRAME_HEIGHT"),
                        ),
                        interpolation=cv2.INTER_NEAREST,
                    )

            self.frame_pixmap = self._frame_to_pixmap(self._ui_frame)

        self._cap.release()

        # Setting these to None tells ui_controller the capture isn't active
        self._ui_frame = None
        self.comparison_frame = None
        self.frame_pixmap = None

        # Kill comparer if capture goes down
        self.safe_exit_compare_thread()

    def _frame_to_pixmap(self, frame: numpy.ndarray) -> QPixmap:
        """Generate a QPixmap instance from a 3-channel image stored as a numpy
        array.

        Args:
            frame (numpy.ndarray): The source image.

        Returns:
            QPixmap: The converted image. Returns a plain QPixmap instance is
                frame is None.
        """
        if frame is None:
            return QPixmap()

        # Use Format_BGR888 because images generated with cv2 are in BGR format
        frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
        return QPixmap.fromImage(frame_img)

    ###################################
    #                                 #
    # Private _compare_thread Methods #
    #                                 #
    ###################################

    def _compare(self) -> None:
        """Look for matches for each split image, splitting when matches are
        found.
        """
        still_going = True
        while still_going:
            still_going = self._look_for_match()
            if still_going:
                self._split()

    def _look_for_match(self) -> bool:
        """Compare each frame generated by _capture with the current split
        image.

        The block beginning with "if self.changing_split" is used to let the
        ui_controller pause and restart this method without killing the thread.
        Changing the split image while this method is running is theoretically
        thread-safe, but it can lead to odd side effects if the flags at the
        top aren't reset.

        The following flags are used to determine when to return a value:
            match_found: False until one of two conditions is met--
                1) The split image's below_flag is False, and
                    current_match_percent >= threshold_match_percent
                2) went_above_threshold_flag is True and current_match_percent
                    < threshold_match_percent
            went_above_threshold_flag: False until the split image's below_flag
                is True, and current_match_percent >= threshold_match_percent

        Returns:
            bool: True if one of the two above match_found conditions are met.
                False if self._compare_thread_finished is called, terminating
                the thread.
        """
        self.current_match_percent = 0
        self.highest_match_percent = 0
        match_found = False
        went_above_threshold_flag = False
        frames_this_second = 0
        start_time = frame_counter_start_time = time.perf_counter()

        while not self._compare_thread_finished:
            current_time = time.perf_counter()
            if current_time - start_time < self._interval:
                time.sleep(self._interval - (current_time - start_time))
            start_time = time.perf_counter()

            # Update self._interval to better track target framerate
            frames_this_second, frame_counter_start_time = self._update_fps_factor(
                frames_this_second, frame_counter_start_time
            )

            # Restart if the current split image is changed mid-run
            if self.changing_splits:
                self.waiting_for_split_change = True
                while self.changing_splits:
                    time.sleep(self._interval)
                self.waiting_for_split_change = False
                return self._look_for_match()

            # Use a snapshot of comparison_frame for thread safety
            frame = self.comparison_frame
            if frame is None:
                continue

            # Check image against template image
            self.current_match_percent = self._get_match_percent(frame)
            if self.current_match_percent > self.highest_match_percent:
                self.highest_match_percent = self.current_match_percent

            if (
                self.current_match_percent
                >= self.splits.list[self.splits.current_image_index].threshold
            ):
                if self.splits.list[self.splits.current_image_index].below_flag:
                    went_above_threshold_flag = True
                else:
                    match_found = True
                    break

            elif went_above_threshold_flag:
                match_found = True
                break

        # Setting these to None tells the ui_controller the splitter is down
        self.current_match_percent = None
        self.highest_match_percent = None
        return match_found

    def _update_fps_factor(
        self, frames_this_second: int, frame_counter_start_time: float
    ) -> Tuple[int, float]:
        """Watch _look_for_match's actual FPS count and adjusts self._interval
        as needed to reach the target framerate. This is needed since using
        time.sleep, as this method does, always introduces a little bit of
        drag, but the amount of drag depends on the machine and on the FPS
        setting the user chooses.

        This method is currently only implemented in _look_for_match. It could
        be implemented in _capture, too, but there are two reasons I don't want
        to:
            1) _look_for_match runs a little slower than _capture, at least on
                my machine, so basing self._interval off the speed of
                _look_for_match guarantees that the _capture framerate isn't
                needlessly throttled.
            2) Implementing this method inside more than one method would
                require tracking multiple intervals, which I feel would be
                needlessly complicated.

        Args:
            frames_this_second (int): The amount of frames processed this
                second so far.
            frame_counter_start_time (float): The exact time, measured by
                time.perf_counter(), the current second started.

        Returns:
            Tuple[int, float]: The update frames_this_second and
                frame_counter_start_time values.
        """
        if time.perf_counter() - frame_counter_start_time >= 1:
            fps = min(self.target_fps, self._capture_max_fps)
            if frames_this_second != fps:
                difference = fps - frames_this_second
                self._fps_adjust_factor += difference * 0.002
            self._interval = self._get_interval()
            frames_this_second = 0
            frame_counter_start_time = time.perf_counter()
        else:
            frames_this_second += 1

        return frames_this_second, frame_counter_start_time

    def _get_interval(self) -> float:
        """Return the amount of time loops in this class should sleep before
        each round.

        Calculated using the maximum fps available to the splitter multiplied
        by some adjustment factor, which is dynamically tweaked by
        _update_fps_factor.

        Returns:
            float: The time.
        """
        return 1 / (
            min(self.target_fps, self._capture_max_fps) * self._fps_adjust_factor
        )

    def _get_match_percent(self, frame: numpy.ndarray) -> float:
        """Get the percent likelihood that two images are the same.

        I do this by calculating the Euclidean distance between the two images.
        Euclidean distance is calculated by summing the squares of the value
        differences of each pixel in each channel when comparing two images of
        the same size, then taking the square root of that sum. For more
        information, see, e.g., https://en.wikipedia.org/wiki/Euclidean_distance.

        Fortunately, cv2.norm provides an easy way to do this by passing in
        normType=cv2.NORM_L2. In images with transparency, a mask must be
        supplied also which tells cv2.norm which pixels matter and which should
        be ignored.

        To generate a match value between 0 and 1, you need to normalize the
        result. This can be done by dividing the result by the largest possible
        Euclidean distance for the given image. Details on this are provided in
        split_dir.py's documentation.

        Args:
            frame (numpy.ndarray): The current comparison frame from the video
                feed.

        Returns:
            float: The percent likelihood that the split image and the frame
                are the same image, expressed as a float between 0 and 1.
        """
        euclidean_dist = cv2.norm(
            src1=self.splits.list[self.splits.current_image_index].image,
            src2=frame,
            normType=cv2.NORM_L2,
            mask=self.splits.list[self.splits.current_image_index].mask,
        )
        return 1 - (
            euclidean_dist / self.splits.list[self.splits.current_image_index].max_dist
        )

    def _split(self) -> None:
        """Handle the events immediately before, during, and after a split.

        The various flags set by this method are read by ui_controller, which
        references them to update the UI and send hotkey presses.
        """
        # Get these values now so that changing splits later doesn't break
        # anything
        delay_duration = self.splits.list[
            self.splits.current_image_index
        ].delay_duration
        suspend_duration = self.splits.list[
            self.splits.current_image_index
        ].pause_duration
        pause_flag = self.splits.list[self.splits.current_image_index].pause_flag
        dummy_flag = self.splits.list[self.splits.current_image_index].dummy_flag

        # Handle delay
        if delay_duration > 0:
            self.delaying = True
            self.delay_remaining = delay_duration
            start_time = time.perf_counter()

            # Poll at regular intervals, both to update self.delay_remaining,
            # which is read by ui_controller, and also to allow the user to
            # kill the thread. The same thing is done in the suspend_duration
            # block below.
            while (
                time.perf_counter() - start_time < delay_duration
                and not self._compare_thread_finished
            ):
                self.delay_remaining = delay_duration - (
                    time.perf_counter() - start_time
                )
                time.sleep(self._interval)
            self.delaying = False
            self.delay_remaining = None

            if self._compare_thread_finished:
                return

        # Handle split
        self.pause_split_action = False
        self.dummy_split_action = False
        self.normal_split_action = False
        if pause_flag:
            self.pause_split_action = True
        elif dummy_flag:
            self.dummy_split_action = True
        else:
            self._start_split_thread()

        # Handle post-split pause
        if suspend_duration > 0:
            self.suspended = True
            self.suspend_remaining = suspend_duration
            start_time = time.perf_counter()
            while (
                time.perf_counter() - start_time < suspend_duration
                and not self._compare_thread_finished
            ):
                self.suspend_remaining = suspend_duration - (
                    time.perf_counter() - start_time
                )
                time.sleep(self._interval)
            self.suspended = False
            self.suspend_remaining = None

            if self._compare_thread_finished:
                return

    def _start_split_thread(self) -> None:
        """Start _split_thread with target=self._set_normal_split_action.
        """
        self._split_thread = threading.Thread(target=self._set_normal_split_action)
        self._split_thread_finished = False
        self._split_thread.daemon = True
        self._split_thread.start()

    def _set_normal_split_action(self) -> None:
        """Set normal_split_action = True without triggering a "double split".

        Since there is a chance a split image could be matched when global
        hotkeys are disabled and the program is not in focus, we want to make
        sure the program can still send the split keypress without failing to
        split. We do this by calling next_split_image directly from this method
        and setting a flag in split_dir that prevents next_split_image() from
        being called again for 1 second.

        If next_split_image() is called within 1 second, ignore_split_request
        is unset and the loop ends.

        Using this method guarantees that though there might be 2 calls made
        to next_split_image, there will never be 0, and we will always go
        forward exactly 1 split image, not 0 or 2.

        A thread is used so that this doesn't block for 1 second in the worst
        case scenario. Instead, the worse case scenario is that for 1 second,
        if the user presses the split hotkey after a split already occurs,
        nothing will happen, which I can live with.

        This is not exactly a clean solution, but I think something like this
        has to be implemented if we are going to allow disabling global
        hotkeys.
        """
        self.splits.next_split_image()
        self.splits.ignore_split_request = True

        self.normal_split_action = True

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < 1 and self.splits.ignore_split_request and not self._split_thread_finished:
            time.sleep(0.001)

        self.splits.ignore_split_request = False
