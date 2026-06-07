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
