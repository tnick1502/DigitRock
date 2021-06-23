import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from static_loading.DigitRock_TriaxialStatick_widgets import DigitRock_TriaxialStatickSoilTest

class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.title = "DigitRock"
        self.left = 100
        self.top = 30
        self.width = 1800
        self.height = 1000
        self.setWindowTitle(self.title)
        #self.setWindowIcon(QIcon(icons + "ST.png"))
        self.setGeometry(self.left, self.top, 1200, 900)
        #self.showFullScreen()

        self.table_widget = DigitRock_TriaxialStatickSoilTest()#
        self.setCentralWidget(self.table_widget)

        self.show()

    def keyPressEvent(self, event):
        if str(event.key()) == "16777216":
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = App()
    ex.show()
    sys.exit(app.exec_())