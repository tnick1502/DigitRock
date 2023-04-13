from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QGroupBox, QHeaderView, QTableWidgetItem, \
    QWidget, QFileSystemModel, QTreeView, QLineEdit, QPushButton, QVBoxLayout, QLabel, QRadioButton, QTableWidget, \
    QCheckBox, QMessageBox
import sys
import os

from general.asis_collector import AsisCollector
from loggers.logger import app_logger
from pdf_watermark.widget import PDFWatermark

from singletons import statment
from general.tab_view import TabMixin
from general import reports


class Save_Dir(TabMixin, QWidget):
    """Класс создает интерфейс для сохранения отчетов.
    Сигнал с директорией файла ведомости передается из класса открытия,
     после чего в этой директории создаются соответствующие папки.
     Название папки отчета передается в класс через коструктор mode"""

    def __init__(self, report_type=None, result_table_params=None, qr=None,  additional_dirs: list = [],
                 plaxis_btn=False, asis_btn=False):
        super().__init__()

        self.additional_dirs = additional_dirs

        self._report_types = report_type

        self._result_table_params = result_table_params

        self.full_executors = True

        self.create_UI(qr, plaxis_btn, asis_btn)

        self.save_directory_text.setText(statment.save_dir.save_directory)
        self.tree.setRootIndex(self.model.index(statment.save_dir.save_directory))

    def create_UI(self, qr, plaxis_btn=False, asis_btn=False):

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

        self.qr_checkbox = QCheckBox("QR аутентификации")
        try:
            if qr.get("state", None):
                self.qr = qr.get("state")
            else:
                self.qr = False
        except:
            self.qr = False

        self.qr_checkbox.setChecked(self.qr)
        self.qr_checkbox.stateChanged.connect(self.qr_changed)

        self.executors_checkbox = QCheckBox("Полный список исполнителей")
        self.executors_checkbox.setChecked(self.full_executors)
        self.executors_checkbox.stateChanged.connect(self.executors_changed)

        self.pdf_watermark_button = QPushButton("Маркировка отчетов")  # Button(icons + "Сохранить.png", 52, 52, 0.7)
        self.pdf_watermark_button.clicked.connect(self.pdf_watermark)
        self.advanced_box_layout.addWidget(self.pdf_watermark_button)

        if asis_btn:
            self.asis_btn = QPushButton("Выгнать АСИС")  # Button(icons + "Сохранить.png", 52, 52, 0.7)
            self.asis_btn.clicked.connect(self.on_asis_btn)
            self.advanced_box_layout.addWidget(self.asis_btn)

        self.advanced_box_layout.addWidget(self.executors_checkbox)

        if qr:
            self.advanced_box_layout.addWidget(self.qr_checkbox)

        if plaxis_btn:
            self.plaxis_btn = QCheckBox("файл Plaxis")
            self.plaxis_btn.setChecked(False)
            self.advanced_box_layout.addWidget(self.plaxis_btn)

        self.roundFI_btn = QCheckBox("округлять PHI до целых")
        self.roundFI_btn.setChecked(False)
        self.advanced_box_layout.addWidget(self.roundFI_btn)

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
        self.tree.setRootIndex(self.model.index(statment.save_dir.save_directory))
        self.tree.doubleClicked.connect(self._doubleclick)

        self.tree.setAnimated(True)
        #self.tree.setIndentation(50)
        self.tree.setSortingEnabled(True)

        self.model_box_layout.addWidget(self.tree)
        self.model_box.setLayout(self.model_box_layout)

        self.layout_end = QHBoxLayout()
        self.layout_end.addWidget(self.model_box)

        if self._result_table_params is not None:
            self.result_table = ResultsTable(self._result_table_params)
            self.layout_end.addWidget(self.result_table)

        self.savebox_layout.addLayout(self.layout_end)

        self.setLayout(self.savebox_layout)
        self.savebox_layout.setContentsMargins(5, 5, 5, 5)

    @property
    def report_type(self):
        if self._report_types_widget is not None:
            return self._report_types_widget.checked
        else:
            return None

    def update(self, s):
        try:
            if statment.general_parameters.test_mode in [
                "Трёхосное сжатие (E)",
                "Трёхосное сжатие (F, C)",
                "Трёхосное сжатие (F, C, E)",
                "Трёхосное сжатие с разгрузкой",
                "Трёхосное сжатие с разгрузкой (plaxis)",
                "Трёхосное сжатие (F, C, Eur)",
                "Трёхосное сжатие КН",
                "Трёхосное сжатие НН",
                "Трёхосное сжатие (F, C) res"
            ]:
                waterfill = ' ' + statment.general_parameters.waterfill if statment.general_parameters.waterfill not in ('', 'Не указывать') else ''
            else:
                waterfill = ''
        except AttributeError:
            waterfill = ''

        statment.save_dir.set_directory(s, statment.general_parameters.test_mode + waterfill,
                                        statment.general_data.shipment_number, additional_dirs=self.additional_dirs)
        self.save_directory_text.setText(statment.save_dir.save_directory)
        self.tree.setRootIndex(self.model.index(statment.save_dir.save_directory))
        if self._result_table_params is not None:
            self.result_table.update()


    def change_save_directory(self):
        """Самостоятельный выбор папки сохранения"""
        s = QFileDialog.getExistingDirectory(self, "Select Directory")
        statment.save_dir.set_directory(s, statment.general_parameters.test_mode, statment.general_data.shipment_number,
                                        additional_dirs=self.additional_dirs)

    def _doubleclick(self, item):
        "Обработчик события двойного клика в проводнике. Открывает файл"
        path = self.sender().model().filePath(item)
        os.startfile(path)

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        #_statment = StatementGenerator(self, path=s)
        #_statment.show()

    def pdf_watermark(self):
        try:
            self.wm = PDFWatermark(statment.save_dir.save_directory)
        except Exception as err:
            print(str(err))

    def qr_changed(self):
        if self.qr_checkbox.isChecked():
            self.qr = True
        else:
            self.qr = False

    def executors_changed(self):
        if self.executors_checkbox.isChecked():
            self.full_executors = True
            reports.full_executors = True
        else:
            reports.full_executors = False
            self.full_executors = False

    def on_asis_btn(self):
        #print(statment.save_dir.save_directory)
        collector = AsisCollector()
        try:
            """
            Коды ошибок:
            - `1` : Сбор прошёл успешно
            - `0` : Выбраного пути `path` не существует
            - `-1` : Папки "Архив [Тип испытания]" не существует
            - `-2' : Список проб пустой
            - `-3` : Ошибка очистки папки Логи АСИС
            - `-4` : Не найден файл .log в папке c пробой
            """
            error_code = collector.collect_logs(path=statment.save_dir.save_directory, print_logs=True)
            if error_code == 1:
                QMessageBox.about(self, "Успешно", str('Логи АСИС успешно сгенерированы'))
                app_logger.info(f'Логи АСИС успешно сгенерированы')
            elif error_code == 0:
                QMessageBox.critical(self, "Ошибка", str('Папки не существует'), QMessageBox.Ok)
                app_logger.exception(f'Папки не существует')
            elif error_code == -1:
                QMessageBox.critical(self, "Ошибка", str('Папки "Архив [Тип испытания]" не существует'), QMessageBox.Ok)
                app_logger.exception(f'Папки "Архив [Тип испытания]" не существует')
            elif error_code == -2:
                QMessageBox.critical(self, "Ошибка", str('Список проб пустой'), QMessageBox.Ok)
                app_logger.exception(f'Список проб пустой')
            elif error_code == -3:
                QMessageBox.critical(self, "Ошибка", str('Ошибка очистки папки Логи АСИС'), QMessageBox.Ok)
                app_logger.exception(f'Ошибка очистки папки Логи АСИС')
            elif error_code == -4:
                QMessageBox.critical(self, "Ошибка", str('Не найден файл .log в папке c пробой. Процесс копирования прерван.'), QMessageBox.Ok)
                app_logger.exception(f'Не найден файл .log в папке c пробой. Процесс копирования прерван.')

        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            app_logger.exception(f"Ошибка генерации логов АСИС")

class ReportType(QGroupBox):
    clicked = pyqtSignal()
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
        self.clicked.emit()

    @property
    def checked(self):
        return self._checked

class ResultsTable(QGroupBox):

    def __init__(self, params: dict):
        super().__init__()
        self.setTitle('Таблица результатов')
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.params = params

        self._clear_table()


    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""

        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setRowCount(len(statment))
        self.table.setColumnCount(len(self.params) + 1)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.verticalHeader().hide()

        self.table.verticalHeader().setMinimumHeight(30)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.table.setHorizontalHeaderLabels(["Лаб. ном.", *self.params.keys()])

    def update(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()

        for i, lab in enumerate(statment):
            self.table.setItem(i, 0, QTableWidgetItem(
                replaceNone(str(lab))))
            for j, key in enumerate(self.params):
                self.table.setItem(i, j + 1, QTableWidgetItem(replaceNone(str(self.params[key](lab)))))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    Dialog = Save_Dir()
    Dialog.set_directory("C:/Users/Пользователь/Desktop/smof.xls", "FC")
    print(Dialog.report_directory)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


