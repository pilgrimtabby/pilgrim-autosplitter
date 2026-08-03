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

"""Test settings.py."""

import os

import pytest
import requests
from pathlib import Path
from PyQt5.QtCore import QSettings

import settings


class TestURLs:
    """Test whether defined URLs lead to live sites."""

    def get_url_code(self, url: str):
        return requests.head(url).status_code

    def test_repo_url_live(self):
        assert self.get_url_code(settings.REPO_URL) == 200

    def test_user_manual_url_live(self):
        assert self.get_url_code(settings.USER_MANUAL_URL) == 200


class TestSettingsFunctionsWithDummySettings:
    """Test functions in settings.py that rely on a "settings" var."""

    @pytest.fixture(autouse=True)
    def dummy_settings(self):
        """Provide blank QSettings file for testing.

        Yields:
            QSettings: The blank QSettings file.
        """
        self.dummy_settings = QSettings("pilgrim_tabby", "pilgrim_autosplitter_test")
        self.dummy_settings.clear()
        yield self.dummy_settings
        self.dummy_settings.clear()

    # Testing set_value
    def test_set_value_str(self):
        settings.set_value("test", "hello world", settings=self.dummy_settings)
        assert self.dummy_settings.value("test") == "hello world"

    def test_set_value_int(self):
        settings.set_value("test", 1337, settings=self.dummy_settings)
        assert self.dummy_settings.value("test") == "1337"

    def test_set_value_blank(self):
        settings.set_value("test", "", settings=self.dummy_settings)
        assert self.dummy_settings.value("test") == ""

    # Testing get_str
    def test_get_str_defined_val(self):
        self.dummy_settings.setValue("test", "foo")
        assert settings.get_str("test", settings=self.dummy_settings) == "foo"

    def test_get_str_unset_val(self):
        assert settings.get_str("test", settings=self.dummy_settings) == "None"

    def test_get_str_blank_val(self):
        self.dummy_settings.setValue("test", "")
        assert settings.get_str("test", settings=self.dummy_settings) == ""

    def test_get_str_from_int(self):
        self.dummy_settings.setValue("test", 123)
        assert settings.get_str("test", settings=self.dummy_settings) == "123"

    # Testing get_bool
    def test_get_bool_from_str_1(self):
        self.dummy_settings.setValue("test", "True")
        assert settings.get_bool("test", settings=self.dummy_settings) == True

    def test_get_bool_from_str_2(self):
        self.dummy_settings.setValue("test", "true")
        assert settings.get_bool("test", settings=self.dummy_settings) == False

    def test_get_bool_from_str_3(self):
        self.dummy_settings.setValue("test", "False")
        assert settings.get_bool("test", settings=self.dummy_settings) == False

    def test_get_bool_from_random_val(self):
        self.dummy_settings.setValue("test", 1.23456543)
        assert settings.get_bool("test", settings=self.dummy_settings) == False

    def test_get_bool_from_unset_val(self):
        assert settings.get_bool("test", settings=self.dummy_settings) == False

    def test_get_bool_from_blank_val(self):
        self.dummy_settings.setValue("test", "")
        assert settings.get_bool("test", settings=self.dummy_settings) == False

    # Testing get_int
    def test_get_int_from_non_int(self):
        self.dummy_settings.setValue("test", "this will fail")
        with pytest.raises(ValueError):
            settings.get_int("test", settings=self.dummy_settings)

    def test_get_int_from_blank_val(self):
        self.dummy_settings.setValue("test", "")
        with pytest.raises(ValueError):
            settings.get_int("test", settings=self.dummy_settings)

    def test_get_int_from_str_1(self):
        self.dummy_settings.setValue("test", "33")
        assert settings.get_int("test", settings=self.dummy_settings) == 33

    def test_get_int_from_str_2(self):
        self.dummy_settings.setValue("test", "-33")
        assert settings.get_int("test", settings=self.dummy_settings) == -33

    def test_get_int_from_int(self):
        self.dummy_settings.setValue("test", -1)
        assert settings.get_int("test", settings=self.dummy_settings) == -1

    # Testing get_float
    def test_get_float_from_str(self):
        self.dummy_settings.setValue("test", "this will fail")
        with pytest.raises(ValueError):
            settings.get_float("test", settings=self.dummy_settings)

    def test_get_float_from_blank_val(self):
        self.dummy_settings.setValue("test", "")
        with pytest.raises(ValueError):
            settings.get_float("test", settings=self.dummy_settings)

    def test_get_float_from_str(self):
        self.dummy_settings.setValue("test", "-0")
        assert settings.get_float("test", settings=self.dummy_settings) == 0

    def test_get_float_from_int(self):
        self.dummy_settings.setValue("test", 123)
        assert settings.get_float("test", settings=self.dummy_settings) == 123

    def test_get_float_from_float(self):
        self.dummy_settings.setValue("test", 123.123123)
        assert settings.get_float("test", settings=self.dummy_settings) == 123.123123

    # Testing set_program_vals
    def test_set_program_vals_runs_on_blank_settings(self):
        settings.set_program_vals(settings=self.dummy_settings)
        assert settings.get_bool("SETTINGS_SET", settings=self.dummy_settings)

    def test_set_program_vals_turns_off_show_min_view(self):
        settings.set_program_vals(settings=self.dummy_settings)
        orig_start_with_video = settings.get_bool(
            "START_WITH_VIDEO", settings=self.dummy_settings
        )
        settings.set_value("SHOW_MIN_VIEW", True, settings=self.dummy_settings)
        settings.set_program_vals(settings=self.dummy_settings)
        assert not orig_start_with_video and not settings.get_bool(
            "SHOW_MIN_VIEW", settings=self.dummy_settings
        )

    def test_set_program_vals_sets_correct_aspect_ratio_1(self):
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value(
            "ASPECT_RATIO", "4:3 (480x360)", settings=self.dummy_settings
        )
        settings.set_program_vals(settings=self.dummy_settings)
        assert (
            settings.get_int("FRAME_WIDTH", settings=self.dummy_settings) == 480
            and settings.get_int("FRAME_HEIGHT", settings=self.dummy_settings) == 360
        )

    def test_set_program_vals_sets_correct_aspect_ratio_2(self):
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value(
            "ASPECT_RATIO", "4:3 (320x240)", settings=self.dummy_settings
        )
        settings.set_program_vals(settings=self.dummy_settings)
        assert (
            settings.get_int("FRAME_WIDTH", settings=self.dummy_settings) == 320
            and settings.get_int("FRAME_HEIGHT", settings=self.dummy_settings) == 240
        )

    def test_set_program_vals_sets_correct_aspect_ratio_3(self):
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value(
            "ASPECT_RATIO", "16:9 (512x288)", settings=self.dummy_settings
        )
        settings.set_program_vals(settings=self.dummy_settings)
        assert (
            settings.get_int("FRAME_WIDTH", settings=self.dummy_settings) == 512
            and settings.get_int("FRAME_HEIGHT", settings=self.dummy_settings) == 288
        )

    def test_set_program_vals_sets_correct_aspect_ratio_4(self):
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value(
            "ASPECT_RATIO", "16:9 (432x243)", settings=self.dummy_settings
        )
        settings.set_program_vals(settings=self.dummy_settings)
        assert (
            settings.get_int("FRAME_WIDTH", settings=self.dummy_settings) == 432
            and settings.get_int("FRAME_HEIGHT", settings=self.dummy_settings) == 243
        )

    def test_missing_last_version_does_not_wipe_hotkeys(self):
        """Regression: missing LAST_VERSION must not wipe existing binds.

        get_str turns unset QSettings values into ``"None"``. The old upgrade
        path treated that as v1.0.0 and called unset_hotkey_bindings().
        """
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value("SPLIT_HOTKEY_NAME", "Num 0", settings=self.dummy_settings)
        settings.set_value("SPLIT_HOTKEY_CODE", "82", settings=self.dummy_settings)
        self.dummy_settings.remove("LAST_VERSION")
        assert not self.dummy_settings.contains("LAST_VERSION")
        settings.set_program_vals(settings=self.dummy_settings)
        assert settings.get_str("SPLIT_HOTKEY_NAME", settings=self.dummy_settings) == "Num 0"
        assert settings.get_str("SPLIT_HOTKEY_CODE", settings=self.dummy_settings) == "82"

    def test_old_last_version_still_wipes_hotkeys(self):
        settings.set_program_vals(settings=self.dummy_settings)
        settings.set_value("SPLIT_HOTKEY_NAME", "Num 0", settings=self.dummy_settings)
        settings.set_value("SPLIT_HOTKEY_CODE", "82", settings=self.dummy_settings)
        settings.set_value("LAST_VERSION", "v1.0.6", settings=self.dummy_settings)
        settings.set_program_vals(settings=self.dummy_settings)
        assert settings.get_str("SPLIT_HOTKEY_NAME", settings=self.dummy_settings) == ""
        assert settings.get_str("SPLIT_HOTKEY_CODE", settings=self.dummy_settings) == ""


def test_get_latest_version():
    latest_version = settings.get_latest_version()
    version_numbers = latest_version.split(".")
    assert (
        len(version_numbers) == 3
        and "v" in version_numbers[0]
        and version_numbers[1].isdigit()
        and version_numbers[2].isdigit()
    )


def test_get_home_dir_returns_real_path():
    assert Path(settings.get_home_dir()).is_dir()


def test_path_is_within_home_resolves_mixed_separators():
    home = Path(settings.get_home_dir())
    assert settings.path_is_within_home(str(home)) is True
    assert settings.path_is_within_home(str(home / "any_subdir_name")) is True
    if os.name == "nt":
        assert settings.path_is_within_home(str(home).replace("/", "\\")) is True
    assert settings.path_is_within_home("") is False


# Testing version_ge
def test_version_ge_1():
    assert settings.version_ge("1.0.1", "1.0.0")


def test_version_ge_2():
    assert settings.version_ge("1.0.1", "1.0.1")


def test_version_ge_3():
    assert settings.version_ge("1.1.0", "1.0.1")


def test_version_ge_4():
    assert settings.version_ge("2.1.0", "1.0.1")


def test_version_ge_5():
    assert settings.version_ge("1.1.0", "1.0.0")


def test_version_ge_6():
    assert not settings.version_ge("1.1.0", "1.1.1")


def test_version_ge_6():
    assert settings.version_ge("1.2.0", "1.1.10")


def test_version_ge_7():
    assert settings.version_ge("1.0.0", "0.20000.999")
