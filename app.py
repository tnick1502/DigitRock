import sys, os
import PyQt5
pyqt = os.path.dirname(PyQt5.__file__)
os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt, "Qt/plugins")

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QGridLayout, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import QSize
import traceback
import subprocess
from consolidation.consolidation_widget import ConsolidationSoilTestApp
from multiprocessing import Process
import threading
import json

from version_control.json_management import test_version, get_actual_version
from version_control.configs import actual_version
from loggers.logger import app_logger
from version_control.configs import path

from static import StatickSoilTestApp
from cyclic import CyclicSoilTestApp
from shear import ShearSoilTestApp
from vibration_creep.vibration_creep_widgets import VibrationCreepSoilTestApp
from consolidation.consolidation_widget import ConsolidationSoilTestApp
from resonant_column.resonant_column_widgets import RezonantColumnSoilTestApp
from vibration_strength.vibration_strangth_widgets import VibrationStrangthSoilTestApp

icon_path = "project_data/icons/"

prog_dict = {
    "static": StatickSoilTestApp,
    "cyclic": CyclicSoilTestApp,
    "vibration_creep": VibrationCreepSoilTestApp,
    "shear": ShearSoilTestApp,
    "consolidation": ConsolidationSoilTestApp,
    "resonant_column": RezonantColumnSoilTestApp,
    "vibration_strangth": VibrationStrangthSoilTestApp
}

prog_name = {
    "static": "Трехосное нагружение",
    "cyclic": "Циклика/Шторм ",
    "vibration_creep": "Виброползучесть",
    "shear": "Сдвиг",
    "consolidation": "Консолидация",
    "resonant_column": "Резонансная колонка",
    "vibration_strangth": "Вибропрочность",
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
        "width": 1600,
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
    },
    "vibration_strangth": {
            "left": 100,
            "top": 30,
            "width": 1500,
            "height": 950
    }
}

class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.title = "DigitRock SoilTest " + "{:.2f}".format(actual_version)
        self.left = 100
        self.top = 50
        self.width = 1350
        self.height = 950
        self.setWindowTitle(self.title)
        #self.setWindowIcon(QIcon(icons + "ST.png"))
        self.setGeometry(self.left, self.top, self.width, self.height)
        if test_version(actual_version):
            self.run()
        else:
            ret = QMessageBox.question(self, 'Предупреждение',
                                       f"Вы запускаете устаревшую версию программы. Актуальная версия {get_actual_version()}",
                                       QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                try:
                    self.run()
                except:
                    app_logger.exception("Ошибка приложения")
            else:
                sys.exit()

    def run(self):
        self.table_widget = QWidget()
        self.layout = QGridLayout()
        self.table_widget.setLayout(self.layout)
        self.info_button = QPushButton("Лог версий")
        self.info_button.setFixedHeight(50)
        self.info_button.clicked.connect(self.info)
        self.layout.addWidget(self.info_button, 0, 0, 1, -1)

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

            string += 1
            if string == 3:
                string = 0
                col += 1


        self.setCentralWidget(self.table_widget)
        self.show()

    def buttons_click(self):

        sender = self.sender().objectName()
        #os.system(f"python {os.path.join(os.getcwd(), sender + '.py')}")

        pipe = subprocess.Popen(f"python {os.path.join(os.getcwd(), sender + '.py')}", stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        output, error = pipe.communicate()
        if pipe.returncode != 0:
            QMessageBox.critical(self, "Ошибка", f"{str(output)}\n{str(error)}", QMessageBox.Ok)
            #print(pipe.returncode)

            #exc_info = sys.exc_info()
            #print("1", exc_info[0])
            #print("2", exc_info[1])
            #traceback.print_tb("3", exc_info[2])
        #pipe.returncode

        # self.prog = prog_dict[sender](geometry=prog_geometry[sender])
        #self.prog.show()

        #def f(sender):
            #self.prog = prog_dict[sender](parent=None, geometry=prog_geometry[sender])
            #self.prog.show()
            #sys.exit(app.exec())

        #p = Process(target=f, args=(sender,))
        #p.start()
        #p.join()
        #thr = threading.Thread(target=f, args=(sender, ))
        #thr.start()

    def keyPressEvent(self, event):
        if str(event.key()) == "16777216":
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def info(self):
        path = "Z:/НАУКА/Разработка/!Программы/Digitrock/version_log.json"

        def open_json(path: str) -> dict:
            """Считывание json файла в словарь"""
            with open(path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            return "\n\n".join([f"{version}:\n{info}" for version, info in json_data.items()])

        QMessageBox.about(self, "Лог версий", open_json(path))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = App()
    sys.exit(app.exec_())