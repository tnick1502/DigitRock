from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QVBoxLayout, QTableWidget, QHBoxLayout, \
    QLineEdit, QGroupBox, QPushButton, QComboBox, QLabel, QRadioButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from datetime import datetime
from singletons import statment
from loggers.logger import app_logger, log_this
from excel_statment.params import accreditation

class Table(QTableWidget):
    """Расширенный класс таблиц"""
    def __init__(self, headers=None, moove=None, resize = None):
        super().__init__()
        if headers:
            self.setColumnCount(len(headers))
            self.setHorizontalHeaderLabels(headers)
        if moove: self.horizontalHeader().setSectionsMovable(True)


    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.rowCount() > 0):
            self.removeRow(0)
        self.setRowCount(40)
        self.setColumnCount(40)
        self.verticalHeader().hide()

    def set_data(self, data, resize = None):
        """Заполнение таблицы параметрами"""
        self._clear_table()
        self.setRowCount(len(data)-1)
        self.setColumnCount(len(data[0]))
        self.setHorizontalHeaderLabels(data[0])

        for i in range(1, len(data)):
            for j in range(len(data[i])):
                self.setItem(i-1, j, QTableWidgetItem(str(data[i][j])))

        if resize == "ResizeToContents":
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        elif resize == "Stretch":
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def get_label(self):
        header = self.horizontalHeader()
        labels = [header.model().headerData(header.logicalIndex(i), Qt.Horizontal) for i in range(header.count())]
        print(labels)
        return labels

class ComboBox_Initial_Parameters(QWidget):
    """Класс отрисовки параметров опыта и открытия ведомости
    Входные параметры:
        Словарь, в котором ключ - имя combo_box и ключ для считывания, по ключу лежат списки со значениями"""
    combo_changes_signal = pyqtSignal() # сигнал сигнализирует о смене параметров для переоткрытия ведомости
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.create_IU()
        self.get_data()

    def create_IU(self):
        self.layout = QHBoxLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.open_box = QGroupBox("Текущая ведомость")
        self.open_box_layout = QHBoxLayout()
        self.button_open = QPushButton("Открыть ведомость")#Button(icons + "Открыть журнал.png", 45, 45, 0.7)
        self.button_refresh = QPushButton("Обновить")
        self.open_box_layout.addWidget(self.button_open)
        self.open_box_layout.addWidget(self.button_refresh)
        self.text_file_path = QLineEdit()
        self.text_file_path.setDisabled(True)
        self.open_box_layout.addWidget(self.text_file_path)
        self.open_box.setLayout(self.open_box_layout)

        self.parameter_box = QGroupBox("Параметры опыта")
        self.parameter_box_layout = QHBoxLayout()

        for key in self.data:
            self.combo_box = QComboBox()
            self.combo_box.addItems(self.data[key])
            self.parameter_box_layout.addWidget(self.combo_box)
            self.combo_box.activated.connect(self._combo_changed)
            setattr(self, "combo_{}".format(key), self.combo_box)


        self.parameter_box.setLayout(self.parameter_box_layout)

        self.layout.addWidget(self.open_box)
        self.layout.addWidget(self.parameter_box)

        self.setLayout(self.layout)

    def _combo_changed(self):
        """Изменение параметров"""
        self.combo_changes_signal.emit()

    def get_data(self):
        """Чтение выбранных параметров"""
        data = {}
        for key in self.data:
            obj = getattr(self, "combo_{}".format(key))
            data[key] = obj.currentText()
        return data

class TablePhysicalProperties(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    laboratory_number_click_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionsMovable(True)
        self.clicked.connect(self.click)
        self._clear_table()

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.rowCount() > 0):
            self.removeRow(0)

        self.setRowCount(30)
        self.setColumnCount(30)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Скважина", "Глубина", "Наименование грунта", "ИГЭ", "rs", "r", "rd", "n", "e", "W", "Sr",
             "Wl", "Wp", "Ip", "Il", "Ir", "Стр. индекс", "УГВ",
             "10", "5", "2", "1", "0.5", "0.25", "0.1", "0.05", "0.01", "0.002", "<0.002"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.table.horizontalHeader().resizeSection(1, 500)

    def set_row_color(self, row, color=(129, 216, 208)):#color=(62, 180, 137)):
        """Раскрашиваем строку"""
        if row is not None:
            for i in range(self.columnCount()):
                self.item(row, i).setBackground(QtGui.QColor(*color))

    def get_row_by_lab_naumber(self, lab):
        """Поиск номера строки по значению лабномера"""
        for row in range(self.columnCount()):
            if self.item(row, 0).text() == lab:
                return row
        return None

    def set_data(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()

        self.setRowCount(len(statment))

        for i, lab in enumerate(statment):
            for g, key in enumerate([str(statment[lab].physical_properties.__dict__[m]) for m in
                                     statment[lab].physical_properties.__dict__]):
                if key == "True":
                    self.set_row_color(i)
                elif key == "False":
                    pass
                else:
                    self.setItem(i, g, QTableWidgetItem(replaceNone(key)))
    @log_this(app_logger, "debug")
    def click(self, clickedIndex):
        """Обработчик события клика на ячейку"""
        try:
            statment.setCurrentTest(str(self.item(clickedIndex.row(), 0).text()))
            self.laboratory_number_click_signal.emit(True)
        except AttributeError:
            pass

    def get_labels(self):
        #names = []
        #for i in range(self.table.horizontalHeader().count()):
            #names.append(self.table.horizontalHeaderItem(i).text())
        #print(names)
        header = self.table.horizontalHeader()
        labels = [header.model().headerData(header.logicalIndex(i), Qt.Horizontal) for i in range(header.count())]
        print(labels)

class TableVertical(QTableWidget):
    """Класс реализует отрисовку вертикальной таблицы
    Входные параметры:
        headlines - список заголовков, идущих в левом столбце
        fill_keys - список ключей, по порядку которых данные будут писаться в таблицу(соответствие заголовок-ключ)"""
    def __init__(self, fill_keys):
        super().__init__()
        self._fill_keys = fill_keys
        self._clear_table()

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.rowCount() > 0):
            self.removeRow(0)

        self.verticalHeader().hide()
        self.setRowCount(len(self._fill_keys))

        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Текущий опыт", "Значения"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, key in enumerate(self._fill_keys):
            self.setItem(i, 0, QTableWidgetItem(self._fill_keys[key]))
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def set_data(self):
        """Получение данных, Заполнение таблицы параметрами"""
        self._clear_table()

        replaceNone = lambda x: x if x != "None" else "-"

        for i, key in enumerate(self._fill_keys):
            if hasattr(statment[statment.current_test].physical_properties, key):
                attr = replaceNone(str(getattr(statment[statment.current_test].physical_properties, key)))
            elif hasattr(statment[statment.current_test].mechanical_properties, key):
                attr = replaceNone(str(getattr(statment[statment.current_test].mechanical_properties, key)))
            else:
                raise AttributeError(f"Отсутствует атрибут {key} в опыте {statment.current_test}")

            self.setItem(i, 1, QTableWidgetItem(attr))

class TableCastomer(QWidget):
    """Класс отрисовывает таблицу с данными заказчика"""
    def __init__(self):
        super().__init__()
        self._createIU()

    def _createIU(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.table = QTableWidget()
        self._clearTable()
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.setFixedHeight(165)

    def _clearTable(self):
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.setRowCount(5)
        self.table.setColumnCount(2)

        for i, val in enumerate(["Заказчик:", "Объект:", "Дата начала опытов:", "Дата окончания опытов:", "Аккредитация:"]):
            self.table.setItem(i, 0, QTableWidgetItem(val))


        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(150)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

    def set_data(self):
        """Заполнение таблицы параметрами"""
        self._clearTable()

        for i, key in enumerate(["customer", "object_name", "start_date", "end_date", "accreditation"]):
            if key in ("start_date", "end_date"):
                self.table.setItem(i, 1, QTableWidgetItem(str(getattr(statment.general_data, key).strftime("%d.%m.%Y"))))
            elif key == "accreditation":
                self.table.setItem(i, 1, QTableWidgetItem(
                    accreditation[statment.general_data.accreditation][statment.general_data.accreditation_key][0] +
                    " " +
                    accreditation[statment.general_data.accreditation][statment.general_data.accreditation_key][1]))
            else:
                self.table.setItem(i, 1, QTableWidgetItem(str(getattr(statment.general_data, key))))


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    headlines = ["Лаб. ном.", "Модуль деформации E50, кПа", "Сцепление с, МПа",
                 "Угол внутреннего трения, град"]

    fill_keys = {
        "laboratory_number": "Лаб. ном.",
        "E50": "Модуль деформации E50, кПа",
        "c": "Сцепление с, МПа",
        "fi": "Угол внутреннего трения, град",
        "CSR": "CSR, д.е.",
        "sigma_3": "Обжимающее давление 𝜎3, кПа",
        "K0": "K0, д.е.",
        "t": "Касательное напряжение τ, кПа",
        "cycles_count": "Число циклов N, ед.",
        "intensity": "Бальность, балл",
        "magnitude": "Магнитуда",
        "rd": "Понижающий коэф. rd",
        "MSF": "MSF",
        "frequency": "Частота, Гц",
        "Hw": "Расчетная высота волны, м",
        "rw": "Плотность воды, кН/м3"
    }

    Dialog = TableVertical(fill_keys=fill_keys)
    Dialog.set_data()
    #Dialog.set_data(data)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


