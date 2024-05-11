import glob
import pathlib

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

from split_image import SplitImage
from utils import frame_to_pixmap, settings


class SplitDirectory(QObject):
    split_name_to_gui_signal = pyqtSignal(str)
    split_image_to_gui_signal = pyqtSignal(object)
    split_image_to_splitter_signal = pyqtSignal(object)
    loop_information_signal = pyqtSignal(int, int)
    split_dir_path_signal = pyqtSignal(object)
    image_index_signal = pyqtSignal(int)
    first_split_signal = pyqtSignal(bool)
    last_split_signal = pyqtSignal(bool)

    def __init__(self, dir_path):
        super().__init__()
        self.path = dir_path
        self.is_first_split = False
        self.is_last_split = False

    def prepare_split_images(self, make_image_list: bool):
        if self.path is None:
            self.split_image_to_gui_signal.emit(None)
            self.split_image_to_splitter_signal.emit(None)
            self.split_dir_path_signal.emit(None)
            return

        self.split_dir_path_signal.emit(self.path)
        if make_image_list:
            self.images = []
            for image in self.get_image_paths():
                self.images += [SplitImage(image)]
        if self.images:
            self.load_next_split_image(first_image=True)
        else:
            self.split_image_to_gui_signal.emit(None)
            self.split_image_to_splitter_signal.emit(None)
            
    def load_next_split_image(self, first_image=False):
        if first_image:
            current_image = self.images[0]
            self.current_index = 0
            self.current_loop = 0
            self.split_name_to_gui_signal.emit(current_image.name)
            self.split_image_to_gui_signal.emit(current_image.pixmap)
            self.split_image_to_splitter_signal.emit(current_image)

        else:
            if self.current_loop >= self.images[self.current_index].loop_count:
                self.current_index += 1
                if self.current_index >= len(self.images):
                    self.current_index = 0
                current_image = self.images[self.current_index]
                self.current_loop = 0
                self.split_name_to_gui_signal.emit(current_image.name)
                self.split_image_to_gui_signal.emit(current_image.pixmap)
                self.split_image_to_splitter_signal.emit(current_image)
            else:
                current_image = self.images[self.current_index]
                self.current_loop += 1
        
        self.loop_information_signal.emit(self.current_loop, current_image.loop_count)
        if self.current_index == 0 and self.current_loop == 0:
            self.set_is_first_split(True)
        else:
            self.set_is_first_split(False)
        if self.current_index == len(self.images) - 1 and self.current_loop == current_image.loop_count:
            self.set_is_last_split(True)
        else:
            self.set_is_last_split(False)

    def get_image_paths(self):
        if not pathlib.Path(self.path).is_dir():
            return []
        paths = (
                glob.glob(f"{self.path}/*.png")
                + glob.glob(f"{self.path}/*.jpg")
                + glob.glob(f"{self.path}/*.jpeg")
        )
        return sorted(paths)
    
    def reset_split_images(self):
        self.prepare_split_images(make_image_list=False)

    def set_is_first_split(self, status: bool):
        if self.is_first_split != status:
            self.is_first_split = status
            self.first_split_signal.emit(status)

    def set_is_last_split(self, status: bool):
        if self.is_last_split != status:
            self.is_last_split = status
            self.last_split_signal.emit(status)

    def load_previous_split_image(self):
        if self.current_loop == 0:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.images) - 1
            current_image = self.images[self.current_index]
            self.current_loop = current_image.loop_count
            self.split_name_to_gui_signal.emit(current_image.name)
            self.split_image_to_gui_signal.emit(current_image.pixmap)
            self.split_image_to_splitter_signal.emit(current_image)
        else:
            current_image = self.images[self.current_index]
            self.current_loop -= 1
        
        self.loop_information_signal.emit(self.current_loop, current_image.loop_count)
        if self.current_index == 0 and self.current_loop == 0:
            self.set_is_first_split(True)
        else:
            self.set_is_first_split(False)
        if self.current_index == len(self.images) - 1 and self.current_loop == self.current_image.loop_count:
            self.set_is_last_split(True)
        else:
            self.set_is_last_split(False)

    def set_dir_path(self):
        path = QFileDialog.getExistingDirectory(None, "Select splits folder")
        if path != "" and (self.path != path or self.path is None):
            self.path = path
            self.prepare_split_images(make_image_list=True)
            settings.setValue("LAST_IMAGE_DIR", self.path)

    def recalculate_default_delay(self):
        for image in self.images:
            if image.delay_is_default:
                image.delay_duration = settings.value("DEFAULT_DELAY")

    def recalculate_default_pause(self):
        for image in self.images:
            if image.pause_is_default:
                image.pause_duration = settings.value("DEFAULT_PAUSE")

    def recalculate_default_threshold(self):
        for image in self.images:
            if image.threshold_is_default:
                image.threshold = settings.value("DEFAULT_THRESHOLD")

    def recalculate_default_loop_count(self):
        for image in self.images:
            if image.loop_count_is_default:
                image.loop_count = settings.value("DEFAULT_LOOP_COUNT")

    def resize_images(self):
        for image in self.images:
            image.image = image.get_and_resize_image()
            image.pixmap = frame_to_pixmap(image.image)
            image.alpha = image.get_alpha()
            self.split_image_to_gui_signal.emit(self.images[self.current_index].pixmap)
