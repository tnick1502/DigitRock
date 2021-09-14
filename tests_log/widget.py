from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QHBoxLayout, QFileDialog, QVBoxLayout, QGroupBox, \
    QWidget, QLineEdit, QPushButton, QTableWidget, QHeaderView, QDateEdit, QTextEdit, QDial, QMessageBox, \
    QTableWidgetItem, QCheckBox
import sys
from collections import Counter

from general.initial_tables import TableCastomer
from datetime import datetime, timedelta
from general.excel_functions import read_customer, resave_xls_to_xlsx
from openpyxl import load_workbook
from tests_log.test_classes import TestsLogCyclic, timedelta_to_dhms



class TestsLogWidget(QWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self, equipment, model):
        super().__init__()

        self.setFixedHeight(800)
        self.setFixedWidth(700)

        self._equipment = []
        for i in equipment:
            self._equipment += [i] * equipment[i]

        self._model = model()

        self._createIU()
        self._retranslateUI()

    def _createIU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        self.box_statment = QGroupBox("Ведомость")
        self.box_statment.setFixedHeight(200)
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
        self.box_test_equipment.setFixedHeight(100)
        self.box_test_equipment_layout = QHBoxLayout()
        self.box_test_equipment.setLayout(self.box_test_equipment_layout)
        self.box_test_equipment_text = QTextEdit()
        self.box_test_equipment_spin = QDial()
        self.box_test_equipment_spin_lable = QLabel()
        self.box_test_equipment_spin_layout = QHBoxLayout()
        self.box_test_equipment_spin_layout.addWidget(self.box_test_equipment_spin)
        self.box_test_equipment_spin_layout.addWidget(self.box_test_equipment_spin_lable)
        self.box_test_equipment_layout.addWidget(self.box_test_equipment_text)
        self.box_test_equipment_layout.addLayout(self.box_test_equipment_spin_layout)

        self.table = QTableWidget()
        self._clearTable()

        self.layout.addWidget(self.box_statment)
        self.layout.addWidget(self.box_test_path)
        self.layout.addWidget(self.box_test_date)
        self.layout.addWidget(self.box_test_equipment)
        self.layout.addWidget(self.table)

    def _retranslateUI(self):
        self.box_test_equipment_spin.valueChanged.connect(self._spinMoved)
        self.box_test_equipment_spin.setValue(1)
        self.box_test_equipment_spin.setMinimum(1)
        self.box_test_equipment_spin.setMaximum(len(self._equipment))

        self.box_statment_open_button.clicked.connect(self._openStatment)
        self.box_test_path_open_button.clicked.connect(self._openDirectory)
        self.box_test_date_processing.clicked.connect(self._processing)

    def _spinMoved(self):
        self.box_test_equipment_spin_lable.setText("Value: %i" % (self.box_test_equipment_spin.value()))
        c = Counter(self._equipment[:int(self.box_test_equipment_spin.value())])
        text = "; ".join(f"{key}: {c[key]}" for key in c)
        self.box_test_equipment_text.setText(text)
        self._model.equipment_names = self._equipment[:int(self.box_test_equipment_spin.value())]

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

    def _openStatment(self):
        file = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if file != "":
            self.path = resave_xls_to_xlsx(file)

            wb = load_workbook(self.path, data_only=True)

            marker, customer = read_customer(wb)

            try:
                assert not marker, "Проверьте " + customer
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                self._data_customer = customer
                self.box_statment_widget.setData(self._data_customer)
                self.box_test_date_start_date.setDate(self._data_customer["data"])
                self.box_test_date_end_date.setDate(self._data_customer["data"])

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
        if self.box_test_path_path_line.text():
            self._model.processing(work_at_night=self.box_test_date_night_check_box.checkState())
            self._fillTable()
            self.box_test_date_end_date.setDate(self._model.end_datetime)






if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = TestsLogWidget({"Wille": 1, "Geotech": 3}, TestsLogCyclic)
    ex.show()
    sys.exit(app.exec_())
