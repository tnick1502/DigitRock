import sys, os
import PyQt5
pyqt = os.path.dirname(PyQt5.__file__)
os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt, "Qt5/plugins")

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QGridLayout, QPushButton, QDialog, \
    QHBoxLayout, QVBoxLayout, QTextEdit
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
from rayleigh_damping.rayleigh_damping_widgets import RayleighDampingSoilTestApp

icon_path = "project_data/icons/"

prog_dict = {
    "static": StatickSoilTestApp,
    "cyclic": CyclicSoilTestApp,
    "vibration_creep": VibrationCreepSoilTestApp,
    "shear": ShearSoilTestApp,
    "consolidation": ConsolidationSoilTestApp,
    "resonant_column": RezonantColumnSoilTestApp,
    "vibration_strength": VibrationStrangthSoilTestApp,
    "rayleigh_damping": RayleighDampingSoilTestApp
}

prog_name = {
    "static": "Трехосное нагружение",
    "cyclic": "Циклика/Шторм ",
    "vibration_creep": "Виброползучесть",
    "shear": "Сдвиг",
    "consolidation": "Консолидация",
    "resonant_column": "Резонансная колонка",
    "vibration_strength": "Вибропрочность",
    "rayleigh_damping": "Демпфирование"
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

    "vibration_strength": {
            "left": 100,
            "top": 30,
            "width": 1500,
            "height": 950
    },

    "rayleigh_damping": {
            "left": 100,
            "top": 30,
            "width": 1500,
            "height": 950
    }
}


def check_local_version(version):

    def program_data_dir(path: str):
        """Проверка наличия и создание пути в случае отсутствия"""

        check_array = os.path.normcase(path).split("\\")
        check_path = check_array[0]

        for subdirectory in check_array[1:]:
            check_path = f"{check_path}/{subdirectory}"
            if not os.path.isdir(check_path):
                os.mkdir(check_path)

    def version_file(version: str, file_path, file_name='version.txt'):
        file_path = os.path.normcase(file_path)
        program_data_dir(file_path)

        if not os.path.exists(file_path + '\\' + file_name):
            with open(file_path + '\\' + file_name, 'w') as file:
                file.write(version + '\n')
            return True

        with open(file_path + '\\' + file_name, 'r+') as file:
            file_version = file.readlines()
            if version > file_version[-1]:
                file.write(version + '\n')
                return True
            return False

    return version_file(version, file_path='C:/ProgramData/Digitrock')


class VersionLog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path = "Z:/НАУКА/Разработка/!Программы/Digitrock/version_log.json"
        self._UI()
        self.update()

    def _UI(self):
        self.setWindowTitle("Лог версий")
        self.setFixedWidth(500)
        self.setFixedHeight(600)
        self.layout = QVBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.setLayout(self.layout)
        self.textbox = QTextEdit()

        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(lambda: self.close())

        self.layout_buttons.addStretch(-1)
        self.layout_buttons.addWidget(self.ok_button)

        self.layout.addWidget(self.textbox)
        self.layout.addLayout(self.layout_buttons)

    def update(self):
        def open_json(path: str) -> dict:
            """Считывание json файла в словарь"""
            with open(path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            return "\n\n".join([f"{version}:\n{info}" for version, info in json_data.items()])

        self.textbox.setText(open_json(path))


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

        col, string = 0, 1

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
            if string == 4:
                string = 1
                col += 1


        self.setCentralWidget(self.table_widget)
        self.show()

        if check_local_version(f"{actual_version:.2f}"):
            self.info(f"ВЫ ЗАПУСКАЕТЕ НОВУЮ ВЕРСИЮ {actual_version:.2f}")

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

    def info(self, window_title=None):
        dialog = VersionLog(self)
        dialog.show()
        if window_title:
            dialog.setWindowTitle(window_title)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = App()
    sys.exit(app.exec_())