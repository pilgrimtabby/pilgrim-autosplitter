import glob
import pathlib

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from split_image import SplitImage


class SplitDirectory(QObject):
    split_image_to_gui_signal = pyqtSignal(object)
    split_image_to_splitter_signal = pyqtSignal(object)
    loop_information_signal = pyqtSignal(int, int)
    image_amount_signal = pyqtSignal(int)

    split_image: SplitImage
    image_dir: str
    image_list: list
    image_list_index: int
    remaining_loops: int

    def __init__(self, dir_path):
        super().__init__()
        self.path = dir_path

    def prepare_split_images(self, make_image_list: bool):
        if make_image_list:
            self.images = []
            for image in self.get_image_paths():
                self.images += [SplitImage(image)]
        if self.images:
            self.image_amount_signal.emit(len(self.images))
            self.load_next_split_image(first_image=True)
        else:
            self.split_image_to_gui_signal.emit(QPixmap())
            self.split_image_to_splitter_signal.emit(None)
            
    def load_next_split_image(self, first_image=False):
        if first_image:
            current_image = self.images[0]
            self.current_index = 0
            self.current_loop = 0
            self.split_image_to_gui_signal.emit(current_image.pixmap)
            self.split_image_to_splitter_signal.emit(current_image)

        else:
            current_image = self.images[self.current_index]
            if self.current_loop == current_image.loop_count:
                self.current_index += 1
                if self.current_index >= len(self.images):
                    self.current_index = 0
                self.current_loop = 0
                self.split_image_to_gui_signal.emit(current_image.pixmap)
                self.split_image_to_splitter_signal.emit(current_image)
            else:
                self.current_loop += 1
        self.loop_information_signal.emit(self.current_loop, current_image.loop_count)

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

    def set_dir_path(self, path: str):
        self.path = path
        self.prepare_split_images(make_image_list=True)
