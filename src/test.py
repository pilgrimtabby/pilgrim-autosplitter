# import sys
# from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
# from PyQt5.QtCore import pyqtSignal, QObject

# class MySignalEmitter(QObject):
#     # Define a custom signal with a value
#     custom_signal = pyqtSignal(str)

# class MyCustomWidget(QWidget):
#     def __init__(self):
#         super().__init__()

#         # Create an instance of the signal emitter
#         self.signal_emitter = MySignalEmitter()

#         # Create a button
#         button = QPushButton("Click Me", self)
#         button.clicked.connect(self.on_button_click)

#     def on_button_click(self):
#         # Emit the custom signal with a value
#         self.signal_emitter.custom_signal.emit("Exercises from w3resource!")

# def custom_slot(value):
#     print("Python PyQt:", value)

# def main():
#     app = QApplication(sys.argv)
#     window = MyCustomWidget()
#     window.setWindowTitle("Custom Signal Example")
#     window.setGeometry(100, 100, 400, 200)  # (x, y, width, height)

#     # Connect the custom signal to the custom slot
#     window.signal_emitter.custom_signal.connect(custom_slot)

#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     main()







# ### OLD GUI.PY


# from PyQt5.QtCore import QTimer, QObject, pyqtSignal
# from PyQt5.QtWidgets import QApplication

# # from gui.controller import GUIController
# from gui import GUIMainWindow
# from utils import DEFAULT_FPS


# class GUI(QObject):
#     signal = pyqtSignal(int)
#     gui: QApplication
#     window: GUIMainWindow
#     # controller: GUIController

#     def __init__(self):
#         super().__init__()
#         self.gui = QApplication([])
#         self.window = GUIMainWindow()
#         # self.controller = self.window.controller

#         self.signal.connect(self.update_match_percent) 
#         self._update_match_percent = self.signal.emit

#         print("Once through")

        # timer = QTimer()
        # timer.timeout.connect(self.window.set_current_frame)
        # timer.start(1000 // DEFAULT_FPS)

#         self.window.show()
#         self.gui.exec()

#     def update_match_percent(self, percent: float):
#         print("Test")


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time


class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Your code goes in this function
        '''
        print(*self.args, **self.kwargs)
        print("Thread start")
        time.sleep(5)
        print("Thread complete")


class MainWindow(QMainWindow):


    def __init__(self, *args, **kwargs):

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0

        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b = QPushButton("DANGER!")
        b.pressed.connect(self.oh_no)

        layout.addWidget(self.l)
        layout.addWidget(b)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

    def oh_no(self):
        worker = Worker()
        self.threadpool.start(worker)

    def recurring_timer(self):
        self.counter +=1
        self.l.setText("Counter: %d" % self.counter)


app = QApplication([])
window = MainWindow()
app.exec_()
