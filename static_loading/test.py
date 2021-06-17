from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QWidget, QDialog
from PyQt5 import QtCore, Qt
from PyQt5.QtGui import QMovie
import sys


class LoadingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("loading...")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        #self.setWindowFlag(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
        self.resize(400, 300)
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.movie = QMovie("C:/Users/Пользователь/Desktop/Загрузки/loading-44.gif")
        self.label.setMovie(self.movie)
        #self.label.setGeometry(QtCore.QRect(0, 0, 200, 200))
        #rect = self.geometry()
        #size = QtCore.QSize(min(rect.width(), rect.height()), min(rect.width(), rect.height()))
        #self.movie.setScaledSize(size)
        timer = QtCore.QTimer(self)
        self.start()
        timer.singleShot(3000, self.start)
        self.show()

    def start(self):
        self.movie.start()

    def stop(self):
        self.movie.stop()
        self.close()

class LoadingWindow1(QMainWindow):
    def __init__(self):
        super().__init__()
        self.show()

        def h():
            [i * i for i in range(100000000)]

        self.k = LoadingWindow()
        p = QtCore.QProcess()
        p.readyReadStandardOutput.connect(self.k)
        h()
        self.k.stop()

if __name__ == "__main__":
    """app = QApplication(sys.argv)

    window = LoadingWindow1()
    sys.exit(app.exec_())"""
    import numpy as np
    print(round(1.5), round(2.5))
    print(np.round(1.5), np.round(2.5))

