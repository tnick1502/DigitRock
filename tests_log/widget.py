from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QHBoxLayout, QFileDialog, QVBoxLayout, QGroupBox, \
    QWidget, QLineEdit, QPushButton, QTableWidget, QHeaderView, QDateEdit, QTextEdit, QDial, QMessageBox, \
    QTableWidgetItem, QCheckBox, QDialog
from PyQt5 import QtCore, QtGui
import sys
from collections import Counter
import pickle

from PyQt5.QtCore import Qt

from excel_statment.initial_tables import TableCastomer
from datetime import datetime, timedelta
from general.excel_functions import read_customer, resave_xls_to_xlsx
from openpyxl import load_workbook
from tests_log.test_classes import TestsLogCyclic, timedelta_to_dhms, TestsLogTriaxialStatic

from general.general_functions import unique_number
from general.report_general_statment import save_report
from singletons import statment
from transliterate import translit
from loggers.logger import log_this, app_logger


class ValueDial(QWidget):
    _dialProperties = ('minimum', 'maximum', 'value', 'singleStep', 'pageStep',
        'notchesVisible', 'tracking', 'wrapping',
        'invertedAppearance', 'invertedControls', 'orientation')
    _inPadding = 3
    _outPadding = 2
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        # remove properties used as keyword arguments for the dial
        dialArgs = {k:v for k, v in kwargs.items() if k in self._dialProperties}
        for k in dialArgs.keys():
            kwargs.pop(k)
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        self.dial = QDial(self, **dialArgs)
        layout.addWidget(self.dial)
        self.dial.valueChanged.connect(self.valueChanged)
        self.dial.setNotchesVisible(True)
        # make the dial the focus proxy (so that it captures focus *and* key events)
        self.setFocusProxy(self.dial)

        # simple "monkey patching" to access dial functions
        self.value = self.dial.value
        self.setValue = self.dial.setValue
        self.minimum = self.dial.minimum
        self.maximum = self.dial.maximum
        self.wrapping = self.dial.wrapping
        self.notchesVisible = self.dial.notchesVisible
        self.setNotchesVisible = self.dial.setNotchesVisible
        self.setNotchTarget = self.dial.setNotchTarget
        self.notchSize = self.dial.notchSize
        self.invertedAppearance = self.dial.invertedAppearance
        self.setInvertedAppearance = self.dial.setInvertedAppearance

        self.updateSize()

    def inPadding(self):
        return self._inPadding

    def setInPadding(self, padding):
        self._inPadding = max(0, padding)
        self.updateSize()

    def outPadding(self):
        return self._outPadding

    def setOutPadding(self, padding):
        self._outPadding = max(0, padding)
        self.updateSize()

    # the following functions are required to correctly update the layout
    def setMinimum(self, minimum):
        self.dial.setMinimum(minimum)
        self.updateSize()

    def setMaximum(self, maximum):
        self.dial.setMaximum(maximum)
        self.updateSize()

    def setWrapping(self, wrapping):
        self.dial.setWrapping(wrapping)
        self.updateSize()

    def updateSize(self):
        # a function that sets the margins to ensure that the value strings always
        # have enough space
        fm = self.fontMetrics()
        minWidth = max(fm.width(str(v)) for v in range(self.minimum(), self.maximum() + 1))
        self.offset = max(minWidth, fm.height()) / 2
        margin = int(self.offset + self._inPadding + self._outPadding)
        self.layout().setContentsMargins(margin, margin, margin, margin)

    def translateMouseEvent(self, event):
        # a helper function to translate mouse events to the dial
        return QtGui.QMouseEvent(event.type(),
            self.dial.mapFrom(self, event.pos()),
            event.button(), event.buttons(), event.modifiers())

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.FontChange:
            self.updateSize()

    def mousePressEvent(self, event):
        self.dial.mousePressEvent(self.translateMouseEvent(event))

    def mouseMoveEvent(self, event):
        self.dial.mouseMoveEvent(self.translateMouseEvent(event))

    def mouseReleaseEvent(self, event):
        self.dial.mouseReleaseEvent(self.translateMouseEvent(event))

    def paintEvent(self, event):
        radius = min(self.width(), self.height()) / 2
        radius -= (self.offset / 2 + self._outPadding)
        invert = -1 if self.invertedAppearance() else 1
        if self.wrapping():
            angleRange = 360
            startAngle = 270
            rangeOffset = 0
        else:
            angleRange = 300
            startAngle = 240 if invert > 0 else 300
            rangeOffset = 1
        fm = self.fontMetrics()

        # a reference line used for the target of the text rectangle
        reference = QtCore.QLineF.fromPolar(radius, 0).translated(self.rect().center())
        fullRange = self.maximum() - self.minimum()
        textRect = QtCore.QRect()

        qp = QtGui.QPainter(self)
        qp.setRenderHints(qp.Antialiasing)
        for p in [0, fullRange]:#range(0, fullRange + rangeOffset, self.notchSize()*2):
            value = self.minimum() + p
            if invert < 0:
                value -= 1
                if value < self.minimum():
                    continue
            angle = p / fullRange * angleRange * invert
            reference.setAngle(startAngle - angle)
            textRect.setSize(fm.size(QtCore.Qt.TextSingleLine, str(value)))
            textRect.moveCenter(reference.p2().toPoint())
            qp.drawText(textRect, QtCore.Qt.AlignCenter, str(value))

class TestsLogWidget(QWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self, equipment, model, excel=None):
        super().__init__()

        self.setWindowTitle('Журнал опытов')

        self.setFixedHeight(900)
        self.setFixedWidth(700)

        self._equipment = {
            "прибор_1": ["kpodfv", "kgbdb", "kkofob"],
            "прибор_2": ["kpodfv", "kgbdb", "kkofob"],
            "прибор_3": ["kpodfv", "kgbdb", "kkofob"],

        }

        self._model = model()

        self._statment_path = excel

        self._createIU()
        self._retranslateUI()

        self.box_statment_widget.set_data()
        self.box_test_date_start_date.setDate(statment.general_data.start_date)
        self.box_test_date_end_date.setDate(statment.general_data.start_date)
        self.box_statment_path_line.setText(self._statment_path)
        self._model.processing_models()

    def _createIU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        self.box_statment = QGroupBox("Ведомость")
        self.box_statment.setFixedHeight(225)
        self.box_statment_layout = QGridLayout()
        self.box_statment.setLayout(self.box_statment_layout)
        self.box_statment_open_button = QPushButton("Выбрать ведомость")
        self.box_statment_path_line = QLineEdit()
        self.box_statment_path_line.setDisabled(True)
        self.box_statment_widget = TableCastomer()
        self.box_statment_layout.addWidget(self.box_statment_open_button, 0, 0, 1, 1)
        self.box_statment_layout.addWidget(self.box_statment_path_line, 0, 1, 1, 5)
        self.box_statment_layout.addWidget(self.box_statment_widget, 1, 0, 2, 6)

        self.box_test_path = QGroupBox("Папка с опытами")
        self.box_test_path.setFixedHeight(70)
        self.box_test_path_layout = QHBoxLayout()
        self.box_test_path.setLayout(self.box_test_path_layout)
        self.box_test_path_open_button = QPushButton("Выбрать папку с опытами")
        self.box_test_path_path_line = QLineEdit()
        self.box_test_path_path_label = QLabel("Опытов: ")
        self.box_test_path_path_label.setFixedWidth(100)
        self.box_test_path_path_line.setDisabled(True)
        self.box_test_path_layout.addWidget(self.box_test_path_open_button)
        self.box_test_path_layout.addWidget(self.box_test_path_path_line)
        self.box_test_path_layout.addWidget(self.box_test_path_path_label)

        self.box_test_date = QGroupBox("Дата начала/окончания")
        self.box_test_date.setFixedHeight(70)
        self.box_test_date_layout = QHBoxLayout()
        self.box_test_date.setLayout(self.box_test_date_layout)
        self.box_test_date_start_date = QDateEdit()
        self.box_test_date_start_date.setCalendarPopup(True)
        self.box_test_date_start_date.setDate(datetime.now())
        self.box_test_date_end_date = QDateEdit()
        self.box_test_date_end_date.setDate(datetime.now())
        self.box_test_date_end_date.setDisabled(True)
        self.box_test_date_night_check_box = QCheckBox("работа ночью")
        self.box_test_date_processing = QPushButton("Обработка")
        self.box_test_date_layout.addWidget(QLabel("Дата начала"))
        self.box_test_date_layout.addWidget(self.box_test_date_start_date)
        self.box_test_date_layout.addWidget(self.box_test_date_night_check_box)
        self.box_test_date_layout.addWidget(self.box_test_date_processing)
        self.box_test_date_layout.addWidget(QLabel("Дата окончания"))
        self.box_test_date_layout.addWidget(self.box_test_date_end_date)
        self.box_test_date_layout.addStretch(-1)

        self.box_test_equipment = QGroupBox("Приборы")
        self.box_test_equipment.setFixedHeight(150)
        self.box_test_equipment_layout = QHBoxLayout()
        self.box_test_equipment.setLayout(self.box_test_equipment_layout)
        self.box_test_equipment_text = QTextEdit()
        self.box_test_equipment_text.setFixedWidth(200)
        self.box_test_equipment_layout.addWidget(self.box_test_equipment_text)

        for key in self._equipment:
            name = translit(key, language_code='ru', reversed=True)

            setattr(self, f"layout_{name}", QVBoxLayout())
            layout = getattr(self, f"layout_{name}")
            setattr(self, f"spin_{name}", ValueDial())
            spin = getattr(self, f"spin_{name}")


            label = QLabel(key)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            layout.addWidget(spin)

            spin.valueChanged.connect(self._spinMoved)
            spin.setValue(1)
            spin.setMinimum(0)
            spin.setMaximum(len(self._equipment[key]))
            self.box_test_equipment_layout.addLayout(layout)

        """self.box_test_equipment_spin = ValueDial()
        #self.box_test_equipment_spin.setNotchesVisible(True)
        self.box_test_equipment_spin_lable = QLabel()
        self.box_test_equipment_spin_lable.setFixedWidth(50)
        self.box_test_equipment_spin_layout = QHBoxLayout()
        self.box_test_equipment_spin_layout.addWidget(self.box_test_equipment_spin)
        #self.box_test_equipment_spin_layout.addWidget(self.box_test_equipment_spin_lable)
        self.box_test_equipment_layout.addWidget(self.box_test_equipment_text)
        self.box_test_equipment_layout.addLayout(self.box_test_equipment_spin_layout)"""


        self.table = QTableWidget()
        self._clearTable()

        self.box_save = QGroupBox("Сохранение")
        self.box_save.setFixedHeight(70)
        self.box_save_layout = QHBoxLayout()
        self.box_save.setLayout(self.box_save_layout)
        self.box_save_excel_button = QPushButton("Сохранить в ведомость")
        self.box_save_pdf_button = QPushButton("Сохранить в файл PDF")
        self.box_dump_pickle_button = QPushButton("Сохранить данные")
        self.box_load_pickle_button = QPushButton("Загрузить данные")
        self.box_save_layout.addStretch(-1)
        self.box_save_layout.addWidget(self.box_dump_pickle_button)
        self.box_save_layout.addWidget(self.box_load_pickle_button)
        self.box_save_layout.addWidget(self.box_save_pdf_button)
        self.box_save_layout.addWidget(self.box_save_excel_button)

        self.layout.addWidget(self.box_statment)
        self.layout.addWidget(self.box_test_path)
        self.layout.addWidget(self.box_test_date)
        self.layout.addWidget(self.box_test_equipment)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.box_save)

    def _retranslateUI(self):
        #self.box_statment_open_button.clicked.connect(self._openStatment)
        self.box_test_path_open_button.clicked.connect(self._openDirectory)
        self.box_test_date_processing.clicked.connect(self._processing)
        self.box_save_excel_button.clicked.connect(self._writeExcel)
        self.box_save_pdf_button.clicked.connect(self._writePDF)
        self.box_dump_pickle_button.clicked.connect(self._dumpPICKLE)
        self.box_load_pickle_button.clicked.connect(self._loadPICKLE)

    def _spinMoved(self):
        self.sender()
        val = {}
        equipment = []
        print(self.sender())
        for key in self._equipment:
            name = translit(key, language_code='ru', reversed=True)
            spin = self.sender()#getattr(self, f"spin_{name}")
            #print(self.sender().value())
            #val[key] = spin.value()
            #equipment += self._equipment[key][:spin.value()]

        #text = "\n\n".join(f"{key}: {val[key]}" for key in self._equipment)
        #self.box_test_equipment_text.setText(text)
        #self._model.equipment_names = equipment

        #self.box_test_equipment_spin_lable.setText("Value: %i" % (self.box_test_equipment_spin.value()))
        #c = Counter(self._equipment[:int(self.box_test_equipment_spin.value())])
        #text = "\n\n".join(f"{key}: {c[key]}" for key in c)
        #self.box_test_equipment_text.setText(text)
        #self._model.equipment_names = self._equipment[:int(self.box_test_equipment_spin.value())]

    def _clearTable(self):
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setColumnCount(5)
        # self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Дата начала", "Дата окончания", "Продолжительность", "Прибор"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        #self.table.horizontalHeader().setMinimumSectionSize(100)

        #self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        #self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        #self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        #self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)

    def _fillTable(self):
        self.table.setRowCount(len(self._model))

        for i, key in enumerate(self._model):
            self.table.setItem(i, 0, QTableWidgetItem(key))
            self.table.setItem(i, 1, QTableWidgetItem(self._model[key].start_datetime.strftime("%H:%M %d.%m.%Y")))
            self.table.setItem(i, 2, QTableWidgetItem(self._model[key].end_datetime.strftime("%H:%M %d.%m.%Y")))
            self.table.setItem(i, 3, QTableWidgetItem(timedelta_to_dhms(self._model[key].duration, ["д", "ч", "мин"])))
            self.table.setItem(i, 4, QTableWidgetItem(self._model[key].equipment))

    def _openDirectory(self):
        dir = QFileDialog.getExistingDirectory(self, 'Выберите папку с архивом')
        if dir:
            count = self._model.set_directory(dir)
            QMessageBox.about(self, "Сообщение", f"Найдено {count} опытов")
            if count > 0:
                self.box_test_path_path_line.setText(dir)
                self.box_test_path_path_label.setText(f'Опытов: {count}')

    def _processing(self):
        date = self.box_test_date_start_date.dateTime().toPyDateTime()
        self._model.start_datetime = date + timedelta(hours=8)
        if len(self._model):
            self._model.processing(work_at_night=self.box_test_date_night_check_box.checkState())
            self._fillTable()
            self.box_test_date_end_date.setDate(self._model.end_datetime)

    def _writeExcel(self):
        try:
            assert self._statment_path, "Выберите ведомость"
            assert self._model, "Не обработано ни одного опыта"
            TestsLogWidget.writeExcel(self._statment_path, self._model)
            QMessageBox.about(self, "Сообщение", "Данные успешно записаны в ведомость")
        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    def _writePDF(self):
        try:
            assert self._statment_path, "Выберите ведомость"
            assert self._model, "Не обработано ни одного опыта"

            save_file_pass = QFileDialog.getExistingDirectory(self, "Select Directory")

           # save_file_name = f'Журнал опытов {self._data_customer["object_name"]}.pdf'
            save_file_name = f'Журнал опытов.pdf'
            statement_title = "Журнал опытов"

            titles = ["Лабораторный номер", "Дата начала опыта", "Дата окончания опыта", "Продолжительность опыта", "Прибор"]
            data = []
            for test in self._model:
                line = [
                    test,
                    self._model[test].start_datetime.strftime("%H:%M %d.%m.%Y"),
                    self._model[test].end_datetime.strftime("%H:%M %d.%m.%Y"),
                    timedelta_to_dhms(self._model[test].duration, ["д", "ч", "мин"]),
                    self._model[test].equipment
                ]
                data.append(line)

            data.append([f"Дата начала опытов: {self._model.start_datetime.strftime('%d.%m.%Y')}"])
            data.append([f"Дата окончания опытов: {self._model.end_datetime.strftime('%d.%m.%Y')}"])

            scales = ["*", "*", "*", "*", "*"]

            data_report = statment.general_data.end_date
            customer_data_info = ['Заказчик:', 'Объект:']
            # Сами данные (подробнее см. Report.py)
            customer_data = [statment.general_data.customer, statment.general_data.object_name]

            try:
                if save_file_pass:
                    save_report(titles, data, scales, data_report, customer_data_info, customer_data,
                                statement_title, save_file_pass, unique_number(length=7, postfix="-ОВ"),
                                save_file_name)
                    QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте файл для записи", QMessageBox.Ok)
            except:
                pass

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    def _dumpPICKLE(self):
        try:
            assert self._statment_path, "Выберите ведомость"
            assert self._model, "Не обработано ни одного опыта"

            save_file_pass = QFileDialog.getExistingDirectory(self, "Select Directory")

            save_file_name = f'Журнал опытов.pickle'

            with open(save_file_pass + "/" + save_file_name, 'wb') as f:
                pickle.dump(self._model, f)

            QMessageBox.about(self, "Сообщение", "Успешно сохранено")

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    def _loadPICKLE(self):
        try:
            file = QFileDialog.getOpenFileName(self, 'Open file')[0]
            if file:
                with open(file, 'rb') as f:
                    self._model = pickle.load(f)

                self.box_test_date_start_date.setDate(self._model.start_datetime)
                self.box_test_date_end_date.setDate(self._model.end_datetime)

                self._fillTable()
        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    @staticmethod
    def writeExcel(path: str, tests: object):
        wb = load_workbook(path)
        for i in range(7, len(wb['Лист1']['A']) + 5):
            if str(wb["Лист1"]['A' + str(i)].value) != "None":
                if str(wb["Лист1"]['IG' + str(i)].value) != "None":
                    key = str(wb["Лист1"]['IG' + str(i)].value)
                else:
                    key = str(wb["Лист1"]['A' + str(i)].value)
                try:
                    t = tests[key.replace("*", "").replace("/", "-")]
                    if isinstance(t, KeyError):
                        date = None
                    else:
                        date = t.end_datetime
                except KeyError:
                    date = None
                if date:
                    wb["Лист1"]['IF' + str(i)] = date

        wb.save(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    statment.load("C:/Users/Пользователь/Desktop/test/Трёхосное сжатие (F, C, E).pickle")

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #ex = TestsLogWidget({"ЛИГА КЛ-1С": 20, "АСИС ГТ.2.0.5": 30}, TestsLogTriaxialStatic)
    ex = TestsLogWidget({"ЛИГА КЛ-1С": 5, "АСИС ГТ.2.0.5": 0}, TestsLogTriaxialStatic, "C:/Users/Пользователь/Desktop/test/818-20 Атомфлот - мех.xlsx")
    ex.show()
    sys.exit(app.exec_())
