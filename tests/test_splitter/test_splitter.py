# Copyright (c) 2024-2025 pilgrim_tabby
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

"""Test splitter.py."""

import time
import cv2
import pytest
from PyQt5.QtWidgets import QApplication

import settings
from splitter.splitter import Splitter
from splitter.split_dir import SplitDir


class TestSplitter:
    """Test Splitter methods using a dummy class instance."""

    # Required for using QWidgets
    dummy_app = QApplication([])

    @pytest.fixture(autouse=True)
    def dummy_splitter(self):
        """Spin up dummy Splitter instance with no split images for testing.

        Yields:
            Splitter: The Splitter instance.
        """
        self.splitter = Splitter()
        self.splitter.splits.list = []

        yield self.splitter

        self.splitter.safe_exit_all_threads()

    def start_capture_and_compare(self):
        test_img = "resources/icon-macos.png"
        self.splitter.splits.list += [SplitDir._SplitImage(test_img)]
        self.splitter.start()

    def is_float_or_int(self, target: str):
        arg_list = target.split(".")
        for entry in arg_list:
            if not entry.isdigit():
                return False
        return True

    def test_start_no_splits(self):
        self.splitter.start()
        assert (
            self.splitter.capture_thread.is_alive()
            and not self.splitter._compare_thread.is_alive()
        )

    def test_start_with_splits(self):
        self.start_capture_and_compare()
        assert (
            self.splitter.capture_thread.is_alive()
            and self.splitter._compare_thread.is_alive()
        )

    def test_exit_all_threads(self):
        self.start_capture_and_compare()

        capture_thread_orig_status = self.splitter.capture_thread.is_alive()
        compare_thread_orig_status = self.splitter._compare_thread.is_alive()
        self.splitter.safe_exit_all_threads()

        assert (
            capture_thread_orig_status
            and compare_thread_orig_status
            and not self.splitter.capture_thread.is_alive()
            and not self.splitter._compare_thread.is_alive()
        )

    def test_start_compare_thread(self):
        self.splitter.start_compare_thread()
        assert self.splitter._compare_thread.is_alive()

    def test_safe_exit_compare_thread(self):
        self.start_capture_and_compare()
        compare_thread_orig_status = self.splitter._compare_thread.is_alive()
        self.splitter.safe_exit_compare_thread()
        assert (
            compare_thread_orig_status and not self.splitter._compare_thread.is_alive()
        )

    def test_set_next_capture_index(self):
        curr_index = settings.get_int("LAST_CAPTURE_SOURCE_INDEX")
        found_new_source = self.splitter.set_next_capture_index()
        new_index = settings.get_int("LAST_CAPTURE_SOURCE_INDEX")
        assert curr_index != new_index or not found_new_source

    def test_toggle_suspended_on(self):
        self.start_capture_and_compare()
        self.splitter.toggle_suspended()
        assert not self.splitter._compare_thread.is_alive()

    def test_toggle_suspended_off_with_split_image(self):
        test_img = "resources/icon-macos.png"
        self.splitter.splits.list += [SplitDir._SplitImage(test_img)]

        self.splitter.toggle_suspended()
        assert self.splitter._compare_thread.is_alive()

    def test_toggle_suspended_off_during_split_delay(self):
        pass

    def test_toggle_suspended_off_during_split_suspend(self):
        pass

    def test_toggle_suspended_off_without_split_image(self):
        self.splitter.toggle_suspended()
        assert not self.splitter._compare_thread.is_alive()

    def test_start_capture_thread(self):
        capture_thread_orig_status = self.splitter.capture_thread.is_alive()
        self.splitter._start_capture_thread()
        assert (
            not capture_thread_orig_status and self.splitter.capture_thread.is_alive()
        )

    def test_open_capture(self):
        cap = self.splitter._open_capture()
        assert type(cap) == cv2.VideoCapture

    def test_get_max_fps(self):
        cap = self.splitter._open_capture()
        max_fps = self.splitter._get_max_fps(cap)
        assert self.is_float_or_int(str(max_fps)) and max_fps >= 0

    def test_capture(self):
        pass

    def test_frame_to_pixmap(self):
        pass

    def test_wait_for_interval(self):
        start_time = time.perf_counter()
        new_time = self.splitter._wait_for_interval(start_time)

        assert (
            pytest.approx(new_time - start_time, abs=0.005) == self.splitter._interval
        )
