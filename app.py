import sys, os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QGridLayout, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import QSize
from consolidation.consolidation_widget import ConsolidationSoilTestApp, __version__

from version_control.json_management import test_version, get_actual_version
from version_control.configs import actual_version
from loggers.logger import app_logger

from static import StatickSoilTestApp
from cyclic import CyclicSoilTestApp
from shear import ShearSoilTestApp
from vibration_creep.vibration_creep_widgets import VibrationCreepSoilTestApp
from consolidation.consolidation_widget import ConsolidationSoilTestApp
from resonant_column.resonant_column_widgets import RezonantColumnSoilTestApp

icon_path = "project_data/icons/"

prog_dict = {
    "static": StatickSoilTestApp,
    "cyclic": CyclicSoilTestApp,
    "vibration_creep": VibrationCreepSoilTestApp,
    "shear": ShearSoilTestApp,
    "consolidation": ConsolidationSoilTestApp,
    "resonant_column": RezonantColumnSoilTestApp,
}

prog_name = {
    "static": "Трехосное нагружение",
    "cyclic": "Циклика/Шторм ",
    "vibration_creep": "Виброползучесть",
    "shear": "Сдвиг",
    "consolidation": "Консолидация",
    "resonant_column": "Резонансная колонка",
}

prog_geometry = {
    "static": {
        "left": 100,
        "top": 30,
        "width": 1500,
        "height": 950
    },

    "cyclic": {
        "left": 100,
        "top": 30,
        "width": 1800,
        "height": 1000
    },

   "vibration_creep": {
        "left": 100,
        "top": 30,
        "width": 1500,
        "height": 950
    },

    "shear": {
        "left": 100,
        "top": 30,
        "width": 1500,
        "height": 950
    },

    "consolidation": {
        "left": 100,
        "top": 30,
        "width": 1800,
        "height": 1000
    },

    "resonant_column": {
        "left": 100,
        "top": 30,
        "width": 1800,
        "height": 1000
    }
}


class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.title = "DigitRock SoilTest " + "{:.2f}".format(__version__)
        self.left = 100
        self.top = 100
        self.width = 900
        self.height = 900
        self.setWindowTitle(self.title)
        #self.setWindowIcon(QIcon(icons + "ST.png"))
        self.setGeometry(self.left, self.top, self.width, self.height)
        if test_version(actual_version):
            self.table_widget = QWidget()
            self.layout = QGridLayout()
            self.table_widget.setLayout(self.layout)

            col, string = 0, 0

            for key in prog_dict:
                setattr(self, key, QPushButton(prog_name[key]))
                btn = getattr(self, key)
                btn.setObjectName(key)
                btn.clicked.connect(self.buttons_click)
                btn.setFixedHeight(290)

                btn.setStyleSheet("QPushButton { text-align: left; }")
                btn.setFont(QFont('Times', 24))
                btn.setIcon(QIcon(QPixmap(os.path.join(icon_path, key + ".jpg"))))
                btn.setIconSize(QSize(280, 280))

                self.layout.addWidget(btn, string, col)
                col += 1
                if col == 2:
                    col = 0
                    string += 1

            self.setCentralWidget(self.table_widget)
            self.show()
        else:
            QMessageBox.critical(self, "Ошибка",
                                 f"Скачайте актуальную версию приложения {get_actual_version()}",
                                 QMessageBox.Ok)

    def buttons_click(self):
        sender = self.sender().objectName()
        prog = prog_dict[sender](geometry=prog_geometry[sender])
        prog.show()

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