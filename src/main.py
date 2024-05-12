from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from capture import Capture
from gui.controller import GUIController
from hotkeys import Hotkeys
from split_directory import SplitDirectory
from splitter import Splitter
from utils import settings


class PilgrimUniversalAutosplitter:
    def __init__(self) -> None:
        self.pilgrim_universal_autosplitter = QApplication([])
        self.capture = Capture()
        self.splitter = Splitter()
        self.split_directory = SplitDirectory(settings.value("LAST_IMAGE_DIR"))
        self.hotkeys = Hotkeys()
        self.gui = GUIController()
        self.send_frame_timer = None

        # Capture signals
        self.capture.video_is_active_signal.connect(self.gui.set_video_feed_active_status)
        self.capture.send_to_gui_signal.connect(self.gui.set_video_frame)
        self.capture.screenshot_result_signal.connect(self.gui.show_screenshot_result)

        self.capture.video_is_active_signal.connect(self.splitter.set_video_feed_active_status)
        self.capture.send_to_splitter_signal.connect(self.splitter.compare_frame)

        # Splitter signals
        self.splitter.request_next_split_image_signal.connect(self.split_directory.load_next_split_image)

        self.splitter.suspended_status_signal.connect(self.gui.set_splitter_suspended_status)
        self.splitter.delaying_status_signal.connect(self.gui.set_splitter_delaying_status)
        self.splitter.match_percent_signal.connect(self.gui.set_match_percent)

        self.splitter.split_action_split_signal.connect(self.hotkeys.press_split_hotkey)
        self.splitter.split_action_pause_signal.connect(self.hotkeys.press_pause_hotkey)

        # Split Directory signals
        self.split_directory.split_image_to_gui_signal.connect(self.gui.set_split_image_and_splits_active_status)
        self.split_directory.loop_information_signal.connect(self.gui.set_loop_text)
        self.split_directory.split_name_to_gui_signal.connect(self.gui.set_split_name)
        self.split_directory.first_split_signal.connect(self.gui.set_first_split_status)
        self.split_directory.last_split_signal.connect(self.gui.set_last_split_status)
        self.split_directory.split_dir_path_signal.connect(self.gui.set_split_directory_line_edit_text_status)

        self.split_directory.split_image_to_splitter_signal.connect(self.splitter.set_split_image)

        # GUI signals
        self.gui.screenshot_button_signal.connect(self.capture.take_screenshot)
        self.gui.reload_video_button_signal.connect(self.capture.reconnect_video)

        self.gui.pause_request_signal.connect(self.splitter.set_suspended_status)
        self.gui.set_match_percent_decimals_signal.connect(self.splitter.reset_all_match_percents)
        self.gui.updated_default_delay_signal.connect(self.split_directory.recalculate_default_delay)
        self.gui.updated_default_pause_signal.connect(self.split_directory.recalculate_default_pause)

        self.gui.image_directory_button_signal.connect(self.split_directory.set_dir_path)
        self.gui.minimal_view_button_signal.connect(lambda: None)
        self.gui.next_source_button_signal.connect(self.capture.get_next_source)
        self.gui.previous_split_button_signal.connect(self.split_directory.load_previous_split_image)
        self.gui.next_split_button_signal.connect(self.split_directory.load_next_split_image)
        self.gui.skip_split_button_signal.connect(self.split_directory.load_next_split_image)
        self.gui.undo_split_button_signal.connect(self.split_directory.load_previous_split_image)
        self.gui.reset_splits_button_signal.connect(self.split_directory.reset_split_images)
        self.gui.updated_default_threshold_signal.connect(self.split_directory.recalculate_default_threshold)
        self.gui.updated_default_threshold_signal.connect(self.splitter.match_percent_signal.emit)
        self.gui.updated_default_delay_signal.connect(self.split_directory.recalculate_default_delay)
        self.gui.updated_default_pause_signal.connect(self.split_directory.recalculate_default_pause)

        self.gui.skip_split_button_signal.connect(self.hotkeys.press_skip_hotkey)
        self.gui.undo_split_button_signal.connect(self.hotkeys.press_undo_hotkey)
        self.gui.reset_splits_button_signal.connect(self.hotkeys.press_reset_hotkey)

        self.gui.update_fps_start_signal.connect(self.capture.kill_streamer)
        self.gui.update_fps_start_signal.connect(self.splitter.kill_split_matcher)
        self.gui.update_fps_finish_signal.connect(self.change_frame_rate)
        self.gui.update_fps_finish_signal.connect(self.capture.restart_streamer)
        self.gui.update_fps_finish_signal.connect(self.splitter.restart_split_matcher)

        self.gui.update_aspect_ratio_start_signal.connect(self.capture.kill_streamer)
        self.gui.update_aspect_ratio_start_signal.connect(self.splitter.kill_split_matcher)
        self.gui.update_aspect_ratio_finish_signal.connect(self.split_directory.resize_images)
        self.gui.update_aspect_ratio_finish_signal.connect(self.capture.restart_streamer)
        self.gui.update_aspect_ratio_finish_signal.connect(self.splitter.restart_split_matcher)

        # Start program
        self.split_directory.prepare_split_images(make_image_list=True)
        
        self.send_frame_timer = QTimer()
        self.send_frame_timer.setInterval(1000 // settings.value("FPS"))
        self.send_frame_timer.timeout.connect(lambda: self.capture.send_frame(False))
        self.send_frame_timer.start()

        self.gui.main_window.show()
        self.pilgrim_universal_autosplitter.exec()

    def change_frame_rate(self):
        self.send_frame_timer.setInterval(1000 // settings.value("FPS"))


if __name__ == "__main__":
    PilgrimUniversalAutosplitter()
