from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QVBoxLayout, QTableWidget, QHBoxLayout, \
    QLineEdit, QGroupBox, QPushButton, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from datetime import datetime

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

class Table_Physical_Properties(QWidget):
    """Класс отрисовывает таблицу физических свойств"""
    lab_number_click_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self._data = None
        self.lab_number = ""
        self.create_IU()

    def create_IU(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.clicked.connect(self.click)
        self._clear_table()
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setRowCount(30)
        self.table.setColumnCount(32)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Скважина", "Глубина", "Наименование грунта", "ИГЭ", "rs", "r", "rd", "n", "e", "W", "Sr",
             "Wl", "Wp", "Ip", "Il", "Ir", "Стр. индекс", "УГВ", "Pзд", "Hk",
             "10", "5", "2", "1", "0.5", "0.25", "0.1", "0.05", "0.01", "0.002", "<0.002"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.table.horizontalHeader().resizeSection(1, 500)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self._clear_table

        self.table.setRowCount(len(self._data))

        for i, lab in enumerate(self._data):
            self.table.setItem(i, 0, QTableWidgetItem(lab))

            for g, key in enumerate([str(self._data[lab][m]) for m in self._data[lab]]):
                if key == "True":
                    self.set_row_color(i)
                elif key == "False":
                    pass
                else:
                    self.table.setItem(i, g+1, QTableWidgetItem(key))

    def set_row_color(self, row, color=(129, 216, 208)):#color=(62, 180, 137)):
        """Раскрашиваем строку"""
        if row is not None:
            for i in range(self.table.columnCount()):
                self.table.item(row, i).setBackground(QtGui.QColor(*color))

    def get_row_by_lab_naumber(self, lab):
        """Поиск номера строки по значению лабномера"""
        for row in range(self.table.columnCount()):
            if self.table.item(row, 0).text() == lab:
                return row
        return None

    def set_data(self, data):
        """Функция для получения данных"""
        self._data = data
        self._fill_table()

    def get_data(self):
        return self._data

    def click(self, clickedIndex):
        """Обработчик события клика на ячейку"""
        try:
            self.lab_number = self.table.item(clickedIndex.row(), 0).text()
            self.lab_number_click_signal.emit(self.lab_number)
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

class Table_Vertical(QWidget):
    """Класс реализует отрисовку вертикальной таблицы
    Входные параметры:
        headlines - список заголовков, идущих в левом столбце
        fill_keys - список ключей, по порядку которых данные будут писаться в таблицу(соответствие заголовок-ключ)"""
    def __init__(self, headlines, fill_keys):
        super().__init__()
        self._headlines = headlines
        self._fill_keys = fill_keys
        self._data = None
        self.create_IU()

    def create_IU(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.table = QTableWidget()
        self._clear_table()
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)


        self.table.verticalHeader().hide()
        self.table.setRowCount(len(self._fill_keys))

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Текущий опыт", "Значения"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, name in enumerate(self._headlines):
            self.table.setItem(i, 0, QTableWidgetItem(name))
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self._clear_table()

        for i, key in enumerate(self._fill_keys):
            self.table.setItem(i, 1, QTableWidgetItem(str(self._data[key])))

    def set_data(self, data):
        """Получение данных"""
        self._data = data
        self._fill_table()

    def get_data(self):
        """Чтение данных с таблицы"""
        return self._data

class Table_Castomer(QWidget):
    """Класс отрисовывает таблицу с данными заказчика"""
    def __init__(self):
        super().__init__()
        self._data = None
        self.create_IU()

    def create_IU(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.table = QTableWidget()
        self._clear_table()
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def _clear_table(self):
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.verticalHeader().hide()
        self.table.setRowCount(1)

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Заказчик", "Объект", "Дата", "Аккредитация"])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self._clear_table()

        for i, key in enumerate(["customer", "object_name", "data", "accreditation"]):
            if key == "data":
                self.table.setItem(0, i, QTableWidgetItem(str(self._data[key].strftime("%d.%m.%Y"))))
            else:
                self.table.setItem(0, i, QTableWidgetItem(str(self._data[key])))

    def set_data(self, data):
        """Получение данных"""
        self._data = data
        self._fill_table()

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


#refactor
class TablePhysicalProperties(QTableWidget):
    """Класс отрисовывает таблицу физических свойств"""
    laboratory_number_click_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.laboratory_number = ""
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

    def set_data(self, data):
        """Функция для получения данных"""
        replaceNone = lambda x: x if x != "None" else "-"

        self._clear_table()

        self.setRowCount(len(data))

        for i, lab in enumerate(data):
            for g, key in enumerate([str(data[lab].physical_properties.__dict__[m]) for m in
                                     data[lab].physical_properties.__dict__]):
                if key == "True":
                    pass
                    #self.set_row_color(i)
                elif key == "False":
                    pass
                else:
                    self.setItem(i, g, QTableWidgetItem(replaceNone(key)))

    def click(self, clickedIndex):
        """Обработчик события клика на ячейку"""
        try:
            self.laboratory_number = self.item(clickedIndex.row(), 0).text()
            self.laboratory_number_click_signal.emit(self.laboratory_number)
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

    def set_data(self, data):
        """Получение данных, Заполнение таблицы параметрами"""
        self._clear_table()

        replaceNone = lambda x: x if x != "None" else "-"

        for i, key in enumerate(self._fill_keys):
            self.setItem(i, 1, QTableWidgetItem(replaceNone(str(getattr(data, key)))))

class TableCastomer(QWidget):
    """Класс отрисовывает таблицу с данными заказчика"""
    def __init__(self):
        super().__init__()
        self._data = None
        self._createIU()

    def _createIU(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.table = QTableWidget()
        self._clearTable()
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.setFixedHeight(132)

    def _clearTable(self):
        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.setRowCount(4)
        self.table.setColumnCount(2)

        for i, val in enumerate(["Заказчик", "Объект", "Дата выдачи", "Аккредитация"]):
            self.table.setItem(i, 0, QTableWidgetItem(val))


        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.horizontalHeader().setMinimumSectionSize(100)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

    def _fillTable(self):
        """Заполнение таблицы параметрами"""
        self._clearTable()

        for i, key in enumerate(["customer", "object_name", "data", "accreditation"]):
            if key == "data":
                self.table.setItem(i, 1, QTableWidgetItem(str(self._data[key].strftime("%d.%m.%Y"))))
            else:
                self.table.setItem(i, 1, QTableWidgetItem(str(self._data[key])))


    def setData(self, data):
        """Получение данных"""
        self._data = data
        self._fillTable()


if __name__ == "__main__":
    import sys
    from general.excel_data_parser import getRCExcelData
    data = getRCExcelData("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", "K0: Формула Джекки")
    app = QApplication(sys.argv)

    headlines = ["Лаб. ном.", "Модуль деформации E50, кПа", "Сцепление с, МПа",
                 "Угол внутреннего трения, град"]

    fill_keys = ["laboratory_number", "E50", "c", "fi",]

    Dialog = TableCastomer()
    #Dialog.set_data(data)
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


