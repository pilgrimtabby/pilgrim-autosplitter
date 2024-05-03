import time

from PyQt5.QtWidgets import QApplication

from gui import GUI
from splitter import Splitter, SplitterThread
from utils import LAST_IMAGE_DIR


def main():
    app = QApplication([])
    gui = GUI()
    splitter = Splitter(LAST_IMAGE_DIR)

    splitter.match_percent_signal.connect(gui.set_match_percent)
    splitter.video_feed_frame_signal.connect(gui.set_video_frame)
    splitter.update_split_image_signal.connect(gui.set_split_image)

    gui.splitter_thread = SplitterThread(splitter)

    gui.threadpool.start(gui.splitter_thread)
    time.sleep(1)
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
