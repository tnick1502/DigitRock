from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QVBoxLayout, QTableWidget, QHBoxLayout, \
    QLineEdit, QGroupBox, QPushButton, QComboBox, QLabel, QRadioButton, QStyledItemDelegate, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from datetime import datetime
from singletons import statment
from loggers.logger import app_logger, log_this
from excel_statment.params import accreditation

class AlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

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

class ComboBox_Initial_ParametersV2(QWidget):
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
        self.open_box_layout = QVBoxLayout()
        self.open_box_layout_1 = QHBoxLayout()
        self.button_open = QPushButton("Открыть ведомость")#Button(icons + "Открыть журнал.png", 45, 45, 0.7)
        self.button_refresh = QPushButton("Обновить")
        self.open_box_layout_1.addWidget(self.button_open)
        self.open_box_layout_1.addWidget(self.button_refresh)
        self.open_box_layout.addLayout(self.open_box_layout_1)
        self.text_file_path = QLineEdit()
        self.text_file_path.setDisabled(True)
        self.open_box_layout.addWidget(self.text_file_path)
        self.open_box.setLayout(self.open_box_layout)

        self.parameter_box = QGroupBox("Параметры опыта")
        self.parameter_box_layout = QHBoxLayout()

        for key in self.data:
            setattr(self, "box_{}".format(key), QGroupBox(self.data[key]["label"]))
            setattr(self, "box_layout_{}".format(key), QVBoxLayout())
            setattr(self, "combo_{}".format(key), QComboBox())

            box = getattr(self, "box_{}".format(key))
            combobox = getattr(self, "combo_{}".format(key))
            layout = getattr(self, "box_layout_{}".format(key))

            combobox.addItems(self.data[key]["vars"])
            combobox.activated.connect(self._combo_changed)

            box.setLayout(layout)
            layout.addWidget(combobox)

            self.parameter_box_layout.addWidget(box)


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

    def set_data(self, data):
        """Задание выбранных параметров"""
        for key in self.data:
            if key in data:
                obj = getattr(self, "combo_{}".format(key))
                obj.blockSignals(True)
                idx = obj.findText(data[key])
                obj.setCurrentIndex(idx)
                obj.blockSignals(False)

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

        self.verticalHeader().setMinimumSectionSize(30)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        header = self.horizontalHeader()
        #header.setMaximumSectionSize(30)
        header.resizeSection(0, 60)
        header.resizeSection(1, 60)
        header.resizeSection(2, 60)
        for i in range(4, 30):
            header.resizeSection(i, 30)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

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
    def __init__(self, fill_keys, size=None):
        super().__init__()
        self._fill_keys = fill_keys
        self._size = size
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

        if self._size is not None:
            self.horizontalHeader().setMinimumSectionSize(self._size["size"])
            for i in self._size["size_fixed_index"]:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)

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

class LineTablePhysicalProperties(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionsMovable(True)
        self._clear_table()

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        replaceNone = lambda x: x if x != "None" else "-"

        while (self.rowCount() > 0):
            self.removeRow(0)

        self.setRowCount(5)
        self.setColumnCount(12)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, val in enumerate(["№ опыта", "Лаб. ном.", "Скважина", "Глубина", "Наименование"]):
            self.setItem(i, 0, QTableWidgetItem(replaceNone(val)))

        for i, val in enumerate(["Стр. индекс", "УГВ", "rs", "r", "rd"]):
            self.setItem(i, 2, QTableWidgetItem(replaceNone(val)))

        for i, val in enumerate(["n", "e", "W", "Sr", "Wl"]):
                self.setItem(i, 4, QTableWidgetItem(replaceNone(val)))

        for i, val in enumerate(["Wp", "Ip", "Il", "Ir", "10"]):
                self.setItem(i, 6, QTableWidgetItem(replaceNone(val)))

        for i, val in enumerate(["5", "2", "1", "0.5", "0.25"]):
            self.setItem(i, 8, QTableWidgetItem(replaceNone(val)))

        for i, val in enumerate(["0.1", "0.05", "0.01", "0.002", "<0.002"]):
            self.setItem(i, 10, QTableWidgetItem(replaceNone(val)))

        header = self.horizontalHeader()
        header.setMaximumSectionSize(80)

        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        header.setSectionResizeMode(9, QHeaderView.Fixed)
        header.setSectionResizeMode(10, QHeaderView.Fixed)
        header.setSectionResizeMode(11, QHeaderView.Fixed)

    def set_data(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()

        dict = statment[statment.current_test].physical_properties.__dict__

        for x in ["granulometric_10", "granulometric_5", "granulometric_2", "granulometric_1", "granulometric_05",
                  "granulometric_025", "granulometric_01", "granulometric_005", "granulometric_001",
                  "granulometric_0002", "granulometric_0000", "ground_water_depth", "stratigraphic_index",  "ige", "Sr", "Ir"]:
            dict.pop(x)

        for g, key in enumerate([str(statment[statment.current_test].physical_properties.__dict__[m]) for m in
                                 dict]):
            if key == "True":
                pass
            elif key == "False":
                pass
            elif g == 0:
                i = 1
                keys = [i for i in statment]
                for x in keys:
                    if statment.current_test == x:
                        break
                    else:
                        i += 1

                self.setItem(0, 0, QTableWidgetItem(str(i)))
            else:
                self.setItem(0, g + 1, QTableWidgetItem(replaceNone(key)))

class TablePhysicalPropertiesGeneral(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionsMovable(True)
        self._clear_table()

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        replaceNone = lambda x: x if x != "None" else "-"

        while (self.rowCount() > 0):
            self.removeRow(0)

        self.setRowCount(7)
        self.setColumnCount(2)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, val in enumerate(["№ опыта", "Лаб. ном.", "Скважина", "Глубина", "Наименование грунта", "Стр. индекс", "УГВ"]):
            self.setItem(i, 0, QTableWidgetItem(replaceNone(val)))

        header = self.horizontalHeader()
        header.setMaximumSectionSize(90)

        self.setSpan(4, 0, 2, 1)
        self.setSpan(4, 1, 2, 1)

        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def set_data(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()
        try:
            self.setItem(0, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.sample_number + 1)))
            self.setItem(1, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.laboratory_number)))
            self.setItem(2, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.borehole)))
            self.setItem(3, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.depth)))
            self.setItem(4, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.soil_name)))
            self.setItem(5, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.stratigraphic_index)))
            self.setItem(6, 1, QTableWidgetItem(
                str(statment[statment.current_test].physical_properties.ground_water_depth)))
        except:
            pass

class TablePhysicalPropertiesProp(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionsMovable(True)
        self._clear_table()

        delegate = AlignDelegate(self)
        for i in range(11):
            self.setItemDelegateForColumn(i, delegate)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        replaceNone = lambda x: x if x != "None" else "-"

        while (self.rowCount() > 0):
            self.removeRow(0)

        self.setRowCount(1)
        self.setColumnCount(11)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.verticalHeader().hide()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.setHorizontalHeaderLabels(
            ["rs", "r", "rd", "n", "e", "W", "Wl", "Wp", "Ip", "Il", "Ir"])

    def set_data(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()
        try:
            self.setItem(0, 0, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.rs))))
            self.setItem(0, 1, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.r))))
            self.setItem(0, 2, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.rd))))
            self.setItem(0, 3, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.n))))
            self.setItem(0, 4, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.e))))
            self.setItem(0, 5, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.W))))
            self.setItem(0, 6, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.Wl))))
            self.setItem(0, 7, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.Wp))))
            self.setItem(0, 8, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.Ip))))
            self.setItem(0, 9, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.Il))))
            self.setItem(0, 10, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.Ir))))
        except:
            pass

class TablePhysicalPropertiesGran(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionsMovable(True)
        self._clear_table()

        delegate = AlignDelegate(self)
        for i in range(11):
            self.setItemDelegateForColumn(i, delegate)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        replaceNone = lambda x: x if x != "None" else "-"

        while (self.rowCount() > 0):
            self.removeRow(0)

        self.setRowCount(1)
        self.setColumnCount(11)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.verticalHeader().hide()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.setHorizontalHeaderLabels(
            ["10", "5", "2", "1", "0.5", "0.25", "0.1", "0.05", "0.01", "0.002", "<0.002"])

    def set_data(self):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()

        try:
            self.setItem(0, 0, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_10))))
            self.setItem(0, 1, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_5))))
            self.setItem(0, 2, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_2))))
            self.setItem(0, 3, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_1))))
            self.setItem(0, 4, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_05))))
            self.setItem(0, 5, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_025))))
            self.setItem(0, 6, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_01))))
            self.setItem(0, 7, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_005))))
            self.setItem(0, 8, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_001))))
            self.setItem(0, 9, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_0002))))
            self.setItem(0, 10, QTableWidgetItem(
                replaceNone(str(statment[statment.current_test].physical_properties.granulometric_0000))))
        except:
            pass

class LinePhysicalProperties(QGroupBox):
    def __init__(self):
        super().__init__()
        self.add_UI()
        self._checked = None

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.setTitle('Физические свойства')
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)
        self.setFixedHeight(180)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.table_general = TablePhysicalPropertiesGeneral()
        self.table_general.setFixedWidth(400)
        self.table_physical = TablePhysicalPropertiesProp()
        self.table_gran = TablePhysicalPropertiesGran()

        self.refresh_button = QPushButton("Обновить модель")
        self.save_button = QPushButton("Сохранить и продолжить")

        self.tables_vertical_layout = QVBoxLayout()
        self.button_horizontal_layout = QHBoxLayout()
        self.button_horizontal_layout.addStretch(-1)

        self.button_horizontal_layout.addWidget(self.refresh_button)
        self.button_horizontal_layout.addWidget(self.save_button)

        self.tables_vertical_layout.addWidget(self.table_physical)
        self.tables_vertical_layout.addWidget(self.table_gran)
        self.tables_vertical_layout.addLayout(self.button_horizontal_layout)

        self.main_layout.addWidget(self.table_general)
        self.main_layout.addLayout(self.tables_vertical_layout)

    def set_data(self):
        self.table_general.set_data()
        self.table_gran.set_data()
        self.table_physical.set_data()




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


