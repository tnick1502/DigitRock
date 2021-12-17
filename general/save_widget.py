from PyQt5.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QGroupBox, \
    QWidget, QFileSystemModel, QTreeView, QLineEdit, QPushButton, QVBoxLayout, QLabel, QRadioButton
import sys
import os

from general.general_functions import create_path
from general.general_statement import StatementGenerator
from loggers.logger import app_logger

class Save_Dir(QWidget):
    """Класс создает интерфейс для сохранения отчетов.
    Сигнал с директорией файла ведомости передается из класса открытия,
     после чего в этой директории создаются соответствующие папки.
     Название папки отчета передается в класс через коструктор mode"""

    def __init__(self, report_type=None):
        super().__init__()

        self._save_directory = "C:/"

        self.postfix = ""
        self.mode = ""
        self._report_types = report_type

        self.create_UI()

        self.save_directory_text.setText(self._save_directory)
        self.tree.setRootIndex(self.model.index(self._save_directory))

    def create_UI(self):

        self.savebox_layout = QVBoxLayout()
        self.savebox_layout_line_1 = QHBoxLayout()


        self.path_box = QGroupBox("Параметры директории")
        self.path_box_layout = QHBoxLayout()
        self.path_box.setLayout(self.path_box_layout)
        self.save_directory_text = QLineEdit()
        self.save_directory_text.setDisabled(True)
        self.change_save_directory_button = QPushButton("Изменить директорию")
        self.change_save_directory_button.clicked.connect(self.change_save_directory)
        self.path_box_layout.addWidget(QLabel("Текущая директория:"))
        self.path_box_layout.addWidget(self.save_directory_text)
        self.path_box_layout.addWidget(self.change_save_directory_button)

        self.save_button = QPushButton("Сохранить отчет")#Button(icons + "Сохранить.png", 52, 52, 0.7)
        self.save_button.setFixedHeight(65)
        self.savebox_layout_line_1.addWidget(self.path_box)
        self.savebox_layout_line_1.addWidget(self.save_button)

        self.save_all_button = QPushButton("Сохранить все отчеты")  # Button(icons + "Сохранить.png", 52, 52, 0.7)
        self.save_all_button.setFixedHeight(65)
        self.savebox_layout_line_1.addWidget(self.save_all_button)

        self.advanced_box = QGroupBox("Расширенные возможности")
        self.advanced_box_layout = QHBoxLayout()
        self.advanced_box.setLayout(self.advanced_box_layout)
        self.general_statment_button = QPushButton("Общая ведомость")  # Button(icons + "Сохранить.png", 52, 52, 0.7)
        self.general_statment_button.clicked.connect(self.general_statment)
        self.advanced_box_layout.addWidget(self.general_statment_button)
        self.jornal_button = QPushButton("Журнал опытов")
        self.advanced_box_layout.addWidget(self.jornal_button)
        self.advanced_box_layout.addStretch(-1)

        self.savebox_layout.addLayout(self.savebox_layout_line_1)

        if self._report_types is not None:
            self._report_types_widget = ReportType(self._report_types)
            self.savebox_layout.addWidget(self._report_types_widget)
        else:
            self._report_types_widget = None

        self.savebox_layout.addWidget(self.advanced_box)

        self.model_box = QGroupBox("Проводник")
        self.model_box_layout = QHBoxLayout()
        self.model = QFileSystemModel()
        self.model.setReadOnly(True)
        self.model.setRootPath('')

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setColumnWidth(0, 500)
        self.tree.setRootIndex(self.model.index(self._save_directory))
        self.tree.doubleClicked.connect(self._doubleclick)

        self.tree.setAnimated(True)
        #self.tree.setIndentation(50)
        self.tree.setSortingEnabled(True)

        self.model_box_layout.addWidget(self.tree)
        self.model_box.setLayout(self.model_box_layout)

        self.savebox_layout.addWidget(self.model_box)

        self.setLayout(self.savebox_layout)
        self.savebox_layout.setContentsMargins(5, 5, 5, 5)

    @property
    def report_directory(self):
        return self._save_directory + f"/{self.mode}{self.postfix}/"

    @property
    def arhive_directory(self):
        return self._save_directory + f"/Архив {self.mode}{self.postfix}/"

    @property
    def directory(self):
        return self._save_directory

    @property
    def report_type(self):
        if self._report_types_widget is not None:
            return self._report_types_widget.checked
        else:
            return None

    def _create_save_directory(self, path, mode=""):
        """Создание папки и подпапок для сохранения отчета"""
        self._save_directory = path + "/" + mode

        create_path(self._save_directory)

        for path in [self.report_directory, self.arhive_directory]:
            create_path(path)

        self.save_directory_text.setText(self._save_directory)

        self.tree.setRootIndex(self.model.index(self._save_directory))

        app_logger.info(f"Папка сохранения опытов {self._save_directory}")

    def set_directory(self, signal, mode):
        """Получение пути к файлу ведомости excel"""
        self.mode = mode
        try:
            self.postfix = signal[signal.index("мех")+3:-5]
        except ValueError:
            try:
                self.postfix = signal[signal.index("циклика") + 7:-5]
            except ValueError:
                self.postfix = ""

        self._create_save_directory(signal[0:-signal[::-1].index("/")], mode)

    def change_save_directory(self):
        """Самостоятельный выбор папки сохранения"""
        s = QFileDialog.getExistingDirectory(self, "Select Directory")
        if s:
            self._create_save_directory(s)

    def _doubleclick(self, item):
        "Обработчик события двойного клика в проводнике. Открывает файл"
        path = self.sender().model().filePath(item)
        os.startfile(path)

    def general_statment(self):
        statment = StatementGenerator(self)
        statment.show()

class ReportType(QGroupBox):

    def __init__(self, report_types: dict = {"имя переменной": "имя отчета для отображения"}):
        super().__init__()
        self.setTitle('Тип отчета')
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        #self.setFixedHeight(60)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.report_types = report_types

        for key in self.report_types:
            setattr(self, key, QRadioButton(self.report_types[key]))
            rb = getattr(self, key)
            rb.value = key
            rb.toggled.connect(self._onClicked)
            self.layout.addWidget(rb)

        rb = getattr(self, list(self.report_types.keys())[0])
        rb.setChecked(True)

        self.layout.addStretch(-1)

    def _onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self._checked = radioButton.value

    @property
    def checked(self):
        return self._checked

if __name__ == "__main__":
    app = QApplication(sys.argv)
    Dialog = Save_Dir()
    Dialog.set_directory("C:/Users/Пользователь/Desktop/smof.xls", "FC")
    print(Dialog.report_directory)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


