import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from cyclic_loading.DigitRock_Cyclic_widgets import DigitRock_CyclicLoadingSoilTest, __version__

from version_control.json_management import test_version, get_actual_version
from version_control.configs import actual_version

class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.title = "Cyclic Loading Soil Test " + "{:.2f}".format(__version__)
        self.left = 100
        self.top = 30
        self.width = 1800
        self.height = 1000
        self.setWindowTitle(self.title)
        #self.setWindowIcon(QIcon(icons + "ST.png"))
        self.setGeometry(self.left, self.top, 1200, 900)
        #self.showFullScreen()
        self.table_widget = DigitRock_CyclicLoadingSoilTest()
        self.setCentralWidget(self.table_widget)
        self.show()
        if test_version(actual_version):
            self.table_widget = DigitRock_CyclicLoadingSoilTest()
            self.setCentralWidget(self.table_widget)
            self.show()
        else:
            QMessageBox.critical(self, "Ошибка",
                                 f"Скачайте актуальную версию приложения {get_actual_version()}",
                                 QMessageBox.Ok)

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
    sys.exit(app.exec_())