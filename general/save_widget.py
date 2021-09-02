from PyQt5.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QGroupBox, \
    QWidget, QFileSystemModel, QTreeView, QLineEdit, QPushButton, QVBoxLayout, QLabel
import sys
import os

from general.general_functions import create_path
from general.general_statement import StatementGenerator

class Save_Dir(QWidget):
    """Класс создает интерфейс для сохранения отчетов.
    Сигнал с директорией файла ведомости передается из класса открытия,
     после чего в этой директории создаются соответствующие папки.
     Название папки отчета передается в класс через коструктор mode"""

    def __init__(self):
        super().__init__()

        self._save_directory = "C:/"

        self.create_UI()

        self.save_directory_text.setText(self._save_directory)
        self.tree.setRootIndex(self.model.index(self._save_directory))

    def create_UI(self):

        self.savebox_layout = QVBoxLayout()
        self.savebox_layout_line_1 = QHBoxLayout()

        self.save_directory_text = QLineEdit()
        self.save_directory_text.setDisabled(True)

        self.path_box = QGroupBox("Параметры директории")
        self.change_save_directory_button = QPushButton("Изменить директорию")#Button(icons + "Папка сохранения.png", 60, 60, 0.7)
        self.change_save_directory_button.clicked.connect(self.change_save_directory)

        self.save_button = QPushButton("Сохранить отчет")#Button(icons + "Сохранить.png", 52, 52, 0.7)

        self.general_statment_button = QPushButton("Общая ведомость")  # Button(icons + "Сохранить.png", 52, 52, 0.7)
        self.general_statment_button.clicked.connect(self.general_statment)

        self.savebox_layout_line_1.addWidget(QLabel("Текущая директория:"))
        self.savebox_layout_line_1.addWidget(self.save_directory_text)
        self.savebox_layout_line_1.addWidget(self.change_save_directory_button)
        self.savebox_layout_line_1.addWidget(self.general_statment_button)
        self.savebox_layout_line_1.addWidget(self.save_button)
        self.path_box.setLayout(self.savebox_layout_line_1)

        self.savebox_layout.addWidget(self.path_box)

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
        return self._save_directory + "/Отчеты/"

    @property
    def arhive_directory(self):
        return self._save_directory + "/Архив/"

    def _create_save_directory(self, path, mode=""):
        """Создание папки и подпапок для сохранения отчета"""
        self._save_directory = path + "/" + mode

        create_path(self._save_directory)

        for path in [self.report_directory, self.arhive_directory]:
            create_path(path)

        self.save_directory_text.setText(self._save_directory)

        self.tree.setRootIndex(self.model.index(self._save_directory))

    def set_directory(self, signal, mode):
        """Получение пути к файлу ведомости excel"""
        self._create_save_directory(signal[0:-signal[::-1].index("/")], mode)

    def change_save_directory(self):
        """Самостоятельный выбор папки сохранения"""
        s = QFileDialog.getExistingDirectory(self, "Select Directory")
        if s:
            self._create_save_directory(s)

    def _doubleclick(self, item):
        "Обработчик события двойного клика в проводнике. Открывает файл"
        #print(str(item.data()))
        path = self.sender().model().filePath(item)
        os.startfile(path)

    def general_statment(self):
        statment = StatementGenerator(self)
        statment.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)



    Dialog = Save_Dir()
    Dialog.set_directory("C:/Users/Пользователь/Desktop/smof.xls", "FC")
    print(Dialog.report_directory)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


