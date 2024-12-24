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

"""Capture video and compare it to a template image."""

from datetime import datetime
import pathlib
import platform
from queue import Full, Queue
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy
from PyQt5.QtGui import QImage, QPixmap

import settings
from settings import COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT
from splitter.split_dir import SplitDir


class Splitter:
    """Capture video frame-by-frame and use it to split.

    This class makes use of four threads:
    - capture_thread: Captures video frame-by-frame and feeds it in three
        dedicated queues to the other three threads for processing.
    - record_thread: When recording is enabled (see ui_controller), writes each
        frame to an .mp4 file. Saves this file on each normal and pause split
        action.
    - compare_split_thread: Compares each frame to the current split image.
        If a match is found, performs a split action.
    - compare_reset_thread: Compares each frame to the reset image, if it
        exists. If a match is found, performs a reset action.

    ui_controller is constantly accessing the public attributes of this class,
    whether or not the threads are active, which is why several of these
    attributes are set to None when their threads go down.

    Attributes:
        capture_thread (threading.Thread): Thread instance that reads and
            resizes images from a cv2.VideoCapture instance.
        changing_splits (bool): Flag set by ui_controller before telling
            self.splits to go to a new split image.
        comparison_frame (numpy.ndarray): Numpy array used to generate a
            comparison with a split image.
        delay_remaining (float): The amount of time left (in seconds) until a
            planned split occurs.
        delaying (bool): Indicates whether _split is waiting before setting a
            split action flag.
        dummy_split_action (bool): When True, tells ui_controller to perform a
            dummy split action.
        frame_pixmap (QPixmap): QPixmap used to show video feed on UI.
        highest_percent (float): The highest match percent so far between
            a frame and a split image.
        highest_reset_percent (float): The highest match percent so far between
            a frame and the reset image, if it exists. Unlike highest_percent,
            this value only resets when the reset button / hotkey is pressed --
            it persists from split to split.
        match_percent (float): The most recent match percent between a
            frame and a split image. Can safely be used by other classes to
            check if splitter_thread is active.
        match_reset_percent (float): The most recent match percent between a
            frame and the reset image, if it exists.
        normal_split_action (bool): When True, tells ui_controller to perform a
            normal split action.
        pause_split_action (bool): When True, tells ui_controller to perform a
            pause split action.
        reset_split_action (bool): When True, tells ui_controller to perform a
            reset action.
        splits (SplitDir): The directory of split images currently in use.
        suspend_remaining (float): The amount of time left (in seconds) before
            the end of a pause after a split.
        suspended (bool): Indicates whether compare_split_thread is currently
            comparing images.
        target_fps (int): The framerate set by the user.
        waiting_for_split_change (bool): Indicates to ui_controller that
            _look_for_split received its changing_splits request and is waiting
            for the new split.
    """

    def __init__(self) -> None:
        """Set all flags and values needed to run the threads."""
        self.target_fps = settings.get_int("FPS")
        self._capture_max_fps = 60
        self._fps_adjust_factor = 1.22  # Roughly the amount needed here; YMMV
        self._interval = self._get_interval()

        # capture_thread
        self.capture_thread = threading.Thread(target=self._capture)
        self._capture_thread_finished = False
        self.comparison_frame = None
        self.frame_pixmap = None
        self._cap = None

        # record_thread
        self._record_queue = Queue(10)  # Number doesn't matter, should be small
        self.record_thread = threading.Thread(target=self._record)
        self._record_thread_finished = False
        self.save_recording = False
        self.continue_recording = False
        self.recording_enabled = False

        # compare_split_thread
        self._compare_split_queue = Queue(10)
        self.compare_split_thread = threading.Thread(target=self._compare_split)
        self._compare_split_thread_finished = False
        self.splits = SplitDir()
        self.match_percent = None
        self.highest_percent = None
        self.delaying = False
        self.delay_remaining = None
        self.suspended = True
        self.suspend_remaining = None
        self.pause_split_action = False
        self.dummy_split_action = False
        self.normal_split_action = False
        self.changing_splits = False
        self.waiting_for_split_change = False

        # compare_reset_thread
        self._compare_reset_queue = Queue(10)
        self.compare_reset_thread = threading.Thread(target=self._compare_reset)
        self._compare_reset_thread_finished = False
        self.match_reset_percent = None
        self.highest_reset_percent = None
        self.reset_split_action = False

    ##################
    #                #
    # Public Methods #
    #                #
    ##################

    def restart(self) -> None:
        """Start capture_thread and try to start the other threads, killing all
        other instances of those threads first.
        """
        self._restart_capture_thread()

        if len(self.splits.list) > 0:
            self.restart_record_thread()
            self.restart_compare_split_thread()

            if self.splits.reset_image is not None:
                self.restart_compare_reset_thread()

    def safe_exit_all_threads(self) -> None:
        """Safely kill capture_thread.

        The logic at end of _capture ensures this kills all other threads too.
        """
        self._capture_thread_finished = True
        if self.capture_thread.is_alive():
            self.capture_thread.join()

    def restart_record_thread(self) -> None:
        """Safely start record_thread (killing all other instances first)."""
        self.safe_exit_record_thread()

        self._record_queue = Queue(10)  # Clear queue of old images
        self._record_thread_finished = False

        # Re-instantiate and start thread
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.daemon = True
        self.record_thread.start()

    def restart_compare_split_thread(self) -> None:
        """Safely start compare_split_thread (killing all other instances
        first).
        """
        self.safe_exit_compare_split_thread()

        self._compare_split_queue = Queue(10)  # Clear queue
        self._compare_split_thread_finished = False
        self.suspended = False

        # Re-instantiate and start thread
        self.compare_split_thread = threading.Thread(target=self._compare_split)
        self.compare_split_thread.daemon = True
        self.compare_split_thread.start()

    def restart_compare_reset_thread(self) -> None:
        """Safely start compare_reset_thread (killing all other instances
        first).
        """
        self.safe_exit_compare_reset_thread()

        self._compare_reset_queue = Queue(10)  # Clear queue
        self._compare_reset_thread_finished = False

        # Re-instantiate and start thread
        self.compare_reset_thread = threading.Thread(target=self._compare_reset)
        self.compare_reset_thread.daemon = True
        self.compare_reset_thread.start()

    def safe_exit_record_thread(self) -> None:
        """Safely kill record_thread.

        Put None into the queue so that get() doesn't block indefinitely in the
        loop if the queue is empty.
        """
        if self.record_thread.is_alive():
            self._record_thread_finished = True
            try:
                self._record_queue.put_nowait(None)
            except Full:
                pass
            self.record_thread.join()

    def safe_exit_compare_split_thread(self) -> None:
        """Safely kill compare_split_thread.

        Put None into the queue so that get() doesn't block indefinitely in the
        loop.
        """
        if self.compare_split_thread.is_alive():
            self._compare_split_thread_finished = True
            try:
                self._compare_split_queue.put_nowait(None)
            except Full:
                pass
            self.compare_split_thread.join()
        self.suspended = True

    def safe_exit_compare_reset_thread(self) -> None:
        """Safely kill compare_reset_thread.

        Put None into the queue so that get() doesn't block indefinitely in the
        loop.
        """
        if self.compare_reset_thread.is_alive():
            self._compare_reset_thread_finished = True
            try:
                self._compare_reset_queue.put_nowait(None)
            except Full:
                pass
            self.compare_reset_thread.join()

    def set_next_capture_index(self) -> bool:
        """Try to find the next valid cv2 capture index, if it exists.

        cv2 capture indexes can be separated by invalid indexes (for example, 0
        and 2 could be valid indexes but not 1). To account for this, this
        method tries 3 invalid indexes before returning to index 0.

        Saves the new index to settings, has no return value.

        Returns:
            bool: True if a new source was found.
        """
        source = settings.get_int("LAST_CAPTURE_SOURCE_INDEX") + 1
        found_valid_source = False
        tries = 0

        while tries < 3:
            if platform.system() == "Windows":
                # Using CAP_DSHOW greatly boosts performance on Windows.
                # It can break things on other platforms.
                test_cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            else:
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

        return found_valid_source

    def toggle_suspended(self) -> None:
        """Stop the compare threads, then start them if the splitter was
        suspended and there are splits.

        Use self.match_percent, since it will never be None if
        compare_split_thread is alive AND not suspended, which is the condition
        we're looking for.
        """
        current_match_percent = self.match_percent

        self.safe_exit_compare_split_thread()
        self.safe_exit_compare_reset_thread()

        if current_match_percent is None and len(self.splits.list) > 0:
            self.restart_compare_split_thread()
            if self.splits.reset_image is not None:
                self.restart_compare_reset_thread()

    ##################################
    #                                #
    # Private capture_thread Methods #
    #                                #
    ##################################

    def _restart_capture_thread(self) -> None:
        """Safely start capture_thread (killing all other instances first)."""
        self.safe_exit_all_threads()

        self._cap = self._open_capture()
        self._capture_max_fps = self._get_max_fps(self._cap)
        self._capture_thread_finished = False
        self.capture_thread = threading.Thread(target=self._capture)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _open_capture(self) -> cv2.VideoCapture:
        """Open and configure a cv2 VideoCapture.

        Set CAP_PROP_BUFFERSIZE to 1 to reduce stuttering.

        Set CAP_PROP_FRAME_WIDTH and CAP_PROP_FRAME_HEIGHT to our target value.
        I can't imagine any capture cards actually support this, but this
        forces the capture source to choose the next-closest value, which in
        some cases is quite a lot smaller than the default. This saves CPU.

        Returns:
            cv2.VideoCapture: The initialized and configured VideoCapture.
        """
        if platform.system() == "Windows":
            # Using CAP_DSHOW greatly boosts performance on Windows.
            # It can break things on other platforms.
            cap = cv2.VideoCapture(
                settings.get_int("LAST_CAPTURE_SOURCE_INDEX"), cv2.CAP_DSHOW
            )
        else:
            cap = cv2.VideoCapture(settings.get_int("LAST_CAPTURE_SOURCE_INDEX"))

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, COMPARISON_FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, COMPARISON_FRAME_HEIGHT)
        return cap

    def _capture(self) -> None:
        """Read frames from a capture source, resize them, and expose them to
        the other three threads in dedicated queues.

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
        is set to True.
        """
        frames_this_second = 0
        start_time = frame_counter_start_time = time.perf_counter()

        while not self._capture_thread_finished:

            # We don't need to wait if we are hitting the max capture fps,
            # since cap.read() blocks until the next frame is available anyway.
            # So we only wait on the interval if we are targeting a framerate
            # that is lower than the max fps.
            if self.target_fps < self._capture_max_fps:
                start_time = self._wait_for_interval(start_time)

                # Update self._interval to better track target framerate
                frames_this_second, frame_counter_start_time = self._update_fps_factor(
                    frames_this_second, frame_counter_start_time
                )

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
                    ui_frame = None
                else:
                    ui_frame = self.comparison_frame

            else:
                self.comparison_frame = cv2.resize(
                    frame,
                    (COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT),
                    interpolation=cv2.INTER_LINEAR,
                )
                # Generate ui_frame (if not in min view)
                if settings.get_bool("SHOW_MIN_VIEW"):
                    ui_frame = None
                else:
                    ui_frame = cv2.resize(
                        frame,
                        (
                            settings.get_int("FRAME_WIDTH"),
                            settings.get_int("FRAME_HEIGHT"),
                        ),
                        interpolation=cv2.INTER_NEAREST,
                    )

            # Convert ui_frame to pixmap
            self.frame_pixmap = self._frame_to_pixmap(ui_frame)

            # Place comparison frame in recording / comparison queues
            for queue in [
                self._record_queue,
                self._compare_reset_queue,
                self._compare_split_queue,
            ]:
                try:
                    queue.put_nowait(self.comparison_frame)
                except Full:
                    pass

        self._cap.release()

        # Setting these to None tells ui_controller the capture isn't active
        self.comparison_frame = None
        self.frame_pixmap = None

        # Kill all other splitter threads if capture goes down
        self.safe_exit_record_thread()
        self.safe_exit_compare_split_thread()
        self.safe_exit_compare_reset_thread()

    def _frame_to_pixmap(self, frame: Optional[numpy.ndarray]) -> QPixmap:
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

    def _get_max_fps(self, cap: cv2.VideoCapture) -> int:
        """Get the max FPS of a capture source.

        Set self._capture_max_fps to the capture's maximum FPS on platforms
        where this is supported. This is done to prevent unnecessary
        comparisons from being generated in _compare due to a mismatch between
        the user's selected framerate and a capture-imposed cap which is lower.
        This also saves CPU.

        Args:
            cap (cv2.VideoCapture): The capture source to check.

        Returns:
            int: The max frames per second.
        """
        try:
            max_fps = cap.get(cv2.CAP_PROP_FPS)
            if max_fps == 0:
                max_fps = 60
        except cv2.error:
            max_fps = 60

        return max_fps

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
            # print(frames_this_second)  # For debug

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

    def _wait_for_interval(self, start_time: float):
        """Sleep until self._interval seconds has passed since start_time.

        Args:
            start_time (float): The starting time.

        Returns:
            float: The current time after sleeping.
        """
        current_time = time.perf_counter()
        if current_time - start_time < self._interval:
            time.sleep(self._interval - (current_time - start_time))
        return time.perf_counter()

    #################################
    #                               #
    # Private record_thread Methods #
    #                               #
    #################################

    def _record(
        self,
        output_path: Optional[str] = None,
        fps: Optional[float] = None,
        recordings_dir: Optional[str] = None,
    ) -> None:
        """Record and save clips of each completed split.

        When this method ends, it erases the recording it made unless flags are
        set somewhere else.

        If no arguments are supplied, those arguments are generated in the
        method. They should only be supplied when continuing, not restarting, a
        recording.

        Framerate used is necessarily somewhat of a guess.

        Args:
            output_path (str, optional): The path to write the video to.
                Defaults to None.
            fps (float, optional): The FPS at which to save the video. Defaults
                to None.
            recordings_dir (str, optional): The directory that holds the
                recordings. Defaults to None.
        """
        # Wait for recording to become enabled
        while not (self.recording_enabled and settings.get_bool("RECORD_CLIPS")):
            time.sleep(0.01)
            if self._record_thread_finished:
                return

        # Unset flags
        self.save_recording = False
        self.continue_recording = False

        # Create output if none supplied
        if output_path is None:
            fps = min(self._cap.get(cv2.CAP_PROP_FPS), self.target_fps)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            recordings_dir = settings.get_str("LAST_RECORD_DIR")
            timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
            output_path = f"{recordings_dir}/{timestamp}.mp4"
            output = cv2.VideoWriter(
                output_path,
                fourcc,
                fps,
                (COMPARISON_FRAME_WIDTH, COMPARISON_FRAME_HEIGHT),
            )

            # Get rid of (potentially very old) images
            self._record_queue = Queue(10)

        # Record each frame
        while not self._record_thread_finished:

            # Delete + restart recording if:
            # Recording isn't enabled anymore
            # FPS has changed (messes with saving)
            # Output path has changed
            if (
                not (self.recording_enabled and settings.get_bool("RECORD_CLIPS"))
                or fps != min(self._cap.get(cv2.CAP_PROP_FPS), self.target_fps)
                or recordings_dir != settings.get_str("LAST_RECORD_DIR")
            ):
                self._delete_video(output_path)
                return self._record()

            # Save the frame
            frame = self._record_queue.get()
            if frame is not None:
                output.write(frame)

        # Broken loop caused by normal or pause split / split hotkey
        # (end recording, don't delete)
        if self.save_recording:
            self.save_recording = False

        # Broken loop caused by dummy split (keep recording same video)
        elif self.continue_recording:
            self.continue_recording = False
            self._record(output_path, fps, recordings_dir)

        # Broken loop caused by any other split image change, program closing,
        # or anything else (end recording, delete video)
        else:
            self._delete_video(output_path)

    def _delete_video(self, video_path: str) -> None:
        """Delete the video file at video_path.

        No error is thrown if the video file doesn't exist.

        Args:
            video_path (str): Path to the video.
        """
        video = pathlib.Path(video_path)
        video.unlink(missing_ok=True)

    ########################################
    #                                      #
    # Private compare_split_thread Methods #
    #                                      #
    ########################################

    def _compare_split(self) -> None:
        """Look for matches for each split image, splitting when matches are
        found, and quitting on the last split or when the thread is killed.
        """
        while self._look_for_split() and self._split():
            continue

    def _look_for_split(self) -> bool:
        """Compare each frame from _capture with the current split image.

        The block beginning with "if self.changing_split" is used to let the
        ui_controller pause and restart this method without killing the thread.
        Changing the split image while this method is running is probably
        thread-safe, but it can lead to odd side effects if the flags at the
        top aren't reset.

        The following flags are used to determine when to return a value:
            match_found: False until one of three conditions is met--
                1) The split image's below_flag is False, and
                    match_percent >= threshold_percent
                2) above_split_threshold is True and match_percent
                    < threshold_percent
                3) Either of the above is satisfied for the reset image
            above_split_threshold: False until the split image's below_flag
                is True, and match_percent >= threshold_percent

        Returns:
            bool: True if a match was found, False otherwise.
        """
        above_split_threshold = False
        match_found = False
        self.match_percent = 0
        self.highest_percent = 0
        self._compare_split_queue = Queue(10)  # Get rid of old images

        while not self._compare_split_thread_finished:

            # Restart if the current split image is changed mid-run
            if self.changing_splits:
                self.waiting_for_split_change = True
                while self.changing_splits:
                    time.sleep(0.005)
                self.waiting_for_split_change = False
                return self._look_for_split()

            # Get current image
            frame = self._compare_split_queue.get()
            if frame is None:
                continue

            # Check image against split image
            match_found, above_split_threshold = self._compare_with_split_image(
                frame, above_split_threshold
            )
            if match_found:
                break

        # Tell the ui_controller not to display match percents
        self.match_percent = None
        self.highest_percent = None

        return match_found

    def _compare_with_split_image(
        self, frame: numpy.ndarray, above_split_threshold: bool
    ) -> Tuple[bool, bool]:
        """Check if a frame matches the split image.

        First, check the match percentage between the frame and the image. If
        it's a match, return True unless the image is a {b} image. In that case,
        wait until the match percent falls back beneath the threshold.

        Args:
            frame (numpy.ndarray): The sample frame for comparison.
            above_split_threshold (bool): Whether the threshold has previously
                been met (used to execute {b} flags).

        Returns:
            Tuple[bool, bool]: match_found and above_split_threshold,
                respectively. If match_found is True, the image is a match. If
                above_split_threshold is a match, the image is a match, but we
                wait until frames fall below the matching threshold before
                returning true for match_found (this is a {b} flag scenario).
        """
        # Set match and highest percents
        self.match_percent = self._get_match_percent(
            frame, self.splits.list[self.splits.current_image_index]
        )
        if self.match_percent > self.highest_percent:
            self.highest_percent = self.match_percent

        # Image match is above threshold
        if (
            self.match_percent
            >= self.splits.list[self.splits.current_image_index].threshold
        ):

            # {b} image -- show that the threshold was met, but no "match" yet
            if self.splits.list[self.splits.current_image_index].below_flag:
                return False, True

            # Not a {b} image -- match found
            else:
                return True, True

        # {b} image -- we are below the threshold now and the threshold has
        # previously been met. It's a match
        elif above_split_threshold:
            return True, True

        # Threshold never met
        return False, False

    def _get_match_percent(
        self, curr_frame: numpy.ndarray, template: SplitDir._SplitImage
    ) -> float:
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
            template (SplitDir._SplitImage): The template image to compare
                against.

        Returns:
            float: The percent likelihood that the template image and the frame
                are the same image, expressed as a float between 0 and 1.
        """
        euclidean_dist = cv2.norm(
            src1=template.image,
            src2=curr_frame,
            normType=cv2.NORM_L2,
            mask=template.mask,
        )
        return 1 - euclidean_dist / template.max_dist

    def _split(self) -> bool:
        """Handle the events immediately before, during, and after a split.

        The various flags set by this method are read by ui_controller, which
        references them to update the UI and send hotkey presses. Flags for
        _record are also set.

        Returns:
            bool: True if the thread wasn't killed / if this isn't the last
                split, otherwise False.
        """
        # Save now so we can execute the delay_duration block correctly
        # The split will have already changed, but we rely on these values
        # to execute that block so we need to save them now
        loop = self.splits.current_loop
        index = self.splits.current_image_index
        split_image = self.splits.list[index]

        # Handle delay
        if split_image.delay_duration > 0:
            self.delaying = True
            # Save total_delay because if the user changes default delay in
            # settings during this method, we don't want the delay remaining
            # for this split to change
            self.delay_remaining = total_delay = split_image.delay_duration
            start_time = time.perf_counter()

            # Poll at regular intervals, both to update self.delay_remaining,
            # which is read by ui_controller, and also to allow the user to
            # kill the thread. The same thing is done in the suspend_duration
            # block below.
            while (
                time.perf_counter() - start_time < total_delay
                and not self._compare_split_thread_finished
            ):
                self.delay_remaining = total_delay - (time.perf_counter() - start_time)
                time.sleep(0.01)
            self.delaying = False
            self.delay_remaining = None

            if self._compare_split_thread_finished:
                return False

        # Set split flag
        self.pause_split_action = False
        self.dummy_split_action = False
        self.normal_split_action = False

        # Pause split; make sure recording is saved
        if split_image.pause_flag:
            self.save_recording = True
            self.pause_split_action = True

        # Dummy split; make sure recording doesn't stop
        elif split_image.dummy_flag:
            self.continue_recording = True
            self.dummy_split_action = True

        # Normal split; make sure recording is saved
        else:
            self.save_recording = True
            self.normal_split_action = True

        # Don't pause splitter after very last split, just exit
        if index == len(self.splits.list) - 1 and loop == split_image.loops:
            return False

        # Handle post-split pause
        elif split_image.pause_duration > 0:
            self.suspended = True
            # Save total_suspend because if the user changes default suspend in
            # settings during this method, we don't want the suspend remaining
            # for this split to change
            self.suspend_remaining = total_suspend = split_image.pause_duration
            start_time = time.perf_counter()
            while (
                time.perf_counter() - start_time < total_suspend
                and not self._compare_split_thread_finished
            ):
                self.suspend_remaining = total_suspend - (
                    time.perf_counter() - start_time
                )
                time.sleep(0.01)
            self.suspended = False
            self.suspend_remaining = None

        return True

    ########################################
    #                                      #
    # Private compare_reset_thread Methods #
    #                                      #
    ########################################

    def _compare_reset(self) -> None:
        """Look for the reset image until a match is found, then reset."""
        while self._look_for_reset() and self._reset():
            continue

    def _look_for_reset(self) -> bool:
        """Compare each frame from _capture with the reset image.

        The following flags are used to determine when to return a value:
            match_found: False until one of three conditions is met--
                1) The reset image's below_flag is False, and
                    match_percent >= threshold_percent
                2) above_reset_threshold is True and match_percent
                    < threshold_percent
                3) Either of the above is satisfied for the reset image
            above_reset_threshold: False until the reset image's below_flag
                is True, and match_percent >= threshold_percent

        Returns:
            bool: True if a match was found, False otherwise.
        """
        above_reset_threshold = False
        match_found = False
        self.match_reset_percent = None
        self.highest_reset_percent = None

        # Don't do anything on the first loop of the first split image.
        # This first split is considered the de facto "start image."
        while (
            self.splits.current_image_index == 0
            and self.splits.current_loop == 1
            and not self._compare_reset_thread_finished
        ):
            time.sleep(0.01)

        # Start displaying match percents
        self.match_reset_percent = 0
        self.highest_reset_percent = 0
        self._compare_reset_queue = Queue(10)  # Get rid of old images

        while not self._compare_reset_thread_finished:

            # Restart method if we're back to first split and loop
            # (e.g. if user hit back button)
            if self.splits.current_image_index == 0 and self.splits.current_loop == 1:
                return self._look_for_reset()

            # Get current image
            frame = self._compare_reset_queue.get()
            if frame is None:
                continue

            # Check image against reset image
            match_found, above_reset_threshold = self._compare_with_reset_image(
                frame, above_reset_threshold
            )
            if match_found:
                break

        # Tell ui_controller not to display match percents
        self.match_reset_percent = None
        self.highest_reset_percent = None

        return match_found

    def _compare_with_reset_image(
        self, frame: numpy.ndarray, above_reset_threshold: bool
    ) -> Tuple[bool, bool]:
        """Check if a frame matches the reset image.

        First, checks the match percentage between the frame and the reset
        image. If the image is a match, returns True unless the reset image is
        a {b} image. In that case, wait until the match percent falls back
        beneath the threshold.

        Args:
            frame (numpy.ndarray): The sample frame for comparison.
            above_reset_threshold (bool): Whether the threshold has previously
                been met (useful for executing {b} flags).

        Returns:
            Tuple[bool, bool]: match_found and above_reset_threshold,
                respectively. If match_found is True, the image is a match. If
                above_reset_threshold is a match, the image is a match, but we
                wait until frames fall below the matching threshold before
                returning true for match_found (this is a {b} flag scenario).
        """
        # See _compare_with_split_image for comments -- logic is basically same
        self.match_reset_percent = self._get_match_percent(
            frame, self.splits.reset_image
        )
        if self.match_reset_percent > self.highest_reset_percent:
            self.highest_reset_percent = self.match_reset_percent

        if self.match_reset_percent >= self.splits.reset_image.threshold:
            if self.splits.reset_image.below_flag:
                return False, True
            else:
                return True, False

        elif above_reset_threshold:
            return True, True

        return False, False

    def _reset(self):
        """Handle the events immediately before, during, and after a reset.

        The various flags set by this method are read by ui_controller, which
        references them to update the UI and send hotkey presses.

        Returns:
            bool: True if the thread wasn't killed, otherwise False.
        """
        # Handle delay
        if self.splits.reset_image.delay_duration > 0:
            self.delaying = True
            # Save total_delay because if the user changes default delay in
            # settings during this method, we don't want the delay remaining
            # to actually change until we're done here
            self.delay_remaining = total_delay = self.splits.reset_image.delay_duration
            start_time = time.perf_counter()

            # Poll at regular intervals, both to update self.delay_remaining,
            # which is read by ui_controller, and also to allow the user to
            # kill the thread. The same thing is done in the suspend_duration
            # block below.
            while (
                time.perf_counter() - start_time < total_delay
                and not self._compare_reset_thread_finished
            ):
                self.delay_remaining = total_delay - (time.perf_counter() - start_time)
                time.sleep(0.01)
            self.delaying = False
            self.delay_remaining = None

            if self._compare_reset_thread_finished:
                return False

        # Handle reset
        self.reset_split_action = True
        return True
