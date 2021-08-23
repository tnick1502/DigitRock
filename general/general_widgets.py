from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QGroupBox, QTableWidget, QDialog, \
    QComboBox, QWidget, QHeaderView, QTableWidgetItem, QFileSystemModel, QTreeView, QLineEdit, QSplitter, QPushButton, \
    QVBoxLayout, QLabel, QMessageBox, QProgressBar, QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtGui import QPainter, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
import sys
import os

from openpyxl import load_workbook

from general.excel_functions import read_customer, read_dynemic, read_mech, resave_xls_to_xlsx, cfe_test_type_columns, \
    k0_test_type_column, column_fullness_test, read_phiz, read_dynemic_rc, read_vibration_creep
from general.initial_tables import Table_Castomer, Table_Physical_Properties, Table_Vertical, ComboBox_Initial_Parameters, TableVertical, TablePhysicalProperties

from general.excel_data_parser import getRCExcelData, getMechanicalExcelData, getCyclicExcelData, getVibrationCreepExcelData

class Float_Slider(QSlider):  # получает на входе размер окна. Если передать 0 то размер автоматический
    def __init__(self, m):
        super().__init__(m)
        self.slider_order = 1

    def order(self, x):
        return 1 / x

    def set_borders(self, minimum, maximum):
        if minimum <= 0:
            self.setMinimum(0)
            self.slider_order = 100 / (maximum)
            self.setMaximum(maximum * self.slider_order)
        else:
            self.slider_order = max([self.order(minimum), 100 / (maximum - minimum)])
            self.setMinimum(minimum * self.slider_order)
            self.setMaximum(maximum * self.slider_order)

    def current_value(self):
        return float(self.value()) / self.slider_order

    def set_value(self, val):
        self.setValue(val * self.slider_order)

class RangeSlider(QSlider):
    sliderMoved = QtCore.pyqtSignal(int, int)

    """ A slider for ranges.

        This class provides a dual-slider for ranges, where there is a defined
        maximum and minimum, as is a normal slider, but instead of having a
        single slider value, there are 2 slider values.

        This class emits the same signals as the QSlider base class, with the 
        exception of valueChanged
    """

    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)

        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QStyle.SC_None
        self.tick_interval = 0
        self.tick_position = QSlider.NoTicks
        self.hover_control = QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

    def low(self):
        return self._low

    def setLow(self, low: int):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high):
        self._high = high
        self.update()

    def paintEvent(self, event):
        # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QPainter(self)
        style = QApplication.style()

        # draw groove
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.siderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QStyle.SC_SliderGroove
        if self.tickPosition() != self.NoTicks:
            opt.subControls |= QStyle.SC_SliderTickmarks
        style.drawComplexControl(QStyle.CC_Slider, opt, painter, self)
        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)

        # drawSpan
        # opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.subControls = QStyle.SC_SliderGroove
        # if self.tickPosition() != self.NoTicks:
        #    opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
        opt.siderValue = 0
        # print(self._low)
        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        # print(low_rect, high_rect)
        low_pos = self.__pick(low_rect.center())
        high_pos = self.__pick(high_rect.center())

        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)

        c = QtCore.QRect(low_rect.center(), high_rect.center()).center()
        # print(min_pos, max_pos, c)
        if opt.orientation == QtCore.Qt.Horizontal:
            span_rect = QtCore.QRect(QtCore.QPoint(min_pos, c.y() - 2), QtCore.QPoint(max_pos, c.y() + 1))
        else:
            span_rect = QtCore.QRect(QtCore.QPoint(c.x() - 2, min_pos), QtCore.QPoint(c.x() + 1, max_pos))

        # self.initStyleOption(opt)
        # print(groove.x(), groove.y(), groove.width(), groove.height())
        if opt.orientation == QtCore.Qt.Horizontal:
            groove.adjust(0, 0, -1, 0)
        else:
            groove.adjust(0, 0, 0, -1)

        if True:  # self.isEnabled():
            highlight = self.palette().color(QPalette.Highlight)
            painter.setBrush(QBrush(highlight))
            painter.setPen(QPen(highlight, 0))
            # painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Dark), 0))
            '''
            if opt.orientation == QtCore.Qt.Horizontal:
                self.setupPainter(painter, opt.orientation, groove.center().x(), groove.top(), groove.center().x(), groove.bottom())
            else:
                self.setupPainter(painter, opt.orientation, groove.left(), groove.center().y(), groove.right(), groove.center().y())
            '''
            # spanRect =
            painter.drawRect(span_rect.intersected(groove))
            # painter.drawRect(groove)

        for i, value in enumerate([self._low, self._high]):
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = QStyle.SC_SliderHandle  # | QtWidgets.QStyle.SC_SliderGroove
            else:
                opt.subControls = QStyle.SC_SliderHandle

            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
            else:
                opt.activeSubControls = self.hover_control

            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QStyle.CC_Slider, opt, painter, self)

    def mousePressEvent(self, event):
        event.accept()

        style = QApplication.style()
        button = event.button()

        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts

        if button:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit

                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos

        self.update()

        # self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)
        self.sliderMoved.emit(self._low, self._high)

    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QApplication.style()

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        return style.sliderValueFromPosition(self.minimum(), self.maximum(),
                                             pos - slider_min, slider_max - slider_min,
                                             opt.upsideDown)


class InitialStatment(QWidget):
    """Класс макет для ведомости
    Входные параметры как у предыдущих классов (ComboBox_Initial_Parameters + Table_Vertical)
    Для кастомизации надо переопределить методы file_open и table_physical_properties_click"""
    statment_directory = pyqtSignal(str)
    signal = pyqtSignal(object)

    def __init__(self, test_parameters, fill_keys, identification_column=None):
        super().__init__()

        self.identification_column = identification_column if identification_column else None
        self.test_parameters = test_parameters

        self._data = None
        self._data_customer = None
        self._laboratory_number = None
        self.path = ""

        self.create_IU(fill_keys)
        self.open_line.combo_changes_signal.connect(self.file_open)
        self.table_physical_properties.laboratory_number_click_signal.connect(self.table_physical_properties_click)
        self.open_line.button_open.clicked.connect(self.button_open_click)
        self.open_line.button_refresh.clicked.connect(self.button_refresh_click)

    def create_IU(self, fill_keys):

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.open_line = ComboBox_Initial_Parameters(self.test_parameters)
        self.open_line.setFixedHeight(80)

        self.customer_line = Table_Castomer()
        #self.customer_line.setFixedHeight(80)

        self.layout_tables = QHBoxLayout()
        self.table_splitter_propetries = QSplitter(Qt.Horizontal)
        self.table_physical_properties = TablePhysicalProperties()
        self.table_vertical = TableVertical(fill_keys)
        self.splitter_table_vertical = QSplitter(Qt.Vertical)
        self.splitter_table_vertical_widget = QWidget()
        self.splitter_table_vertical.addWidget(self.table_vertical)
        self.splitter_table_vertical.addWidget(self.splitter_table_vertical_widget)
        self.splitter_table_vertical.setStretchFactor(0, 8)
        self.splitter_table_vertical.setStretchFactor(1, 1)
        #self.table_vertical.setFixedWidth(300)
        #self.table_vertical.setFixedHeight(40 * len(self.headlines))

        self.table_splitter_propetries = QSplitter(Qt.Horizontal)
        self.table_splitter_propetries.addWidget(self.table_physical_properties)
        self.table_splitter_propetries.addWidget(self.splitter_table_vertical)
        self.table_splitter_propetries.setStretchFactor(0, 2)

        #self.layout_tables.addWidget(self.table_splitter)
        #self.layout_tables.setAlignment(Qt.AlignTop)

        self.table_splitter_propetries_customer = QSplitter(Qt.Vertical)
        self.table_splitter_propetries_customer.addWidget(self.customer_line)
        self.table_splitter_propetries_customer.addWidget(self.table_splitter_propetries)
        self.table_splitter_propetries_customer.setStretchFactor(0, 1)
        self.table_splitter_propetries_customer.setStretchFactor(1, 10)
        self.layout.addWidget(self.open_line)
        self.layout.addWidget(self.table_splitter_propetries_customer)
        #self.layout.addLayout(self.layout_tables)
        self.setLayout(self.layout)

    def button_open_click(self):
        combo_params = self.open_line.get_data()

        test = True
        for key in self.test_parameters:
            if combo_params[key] == self.test_parameters[key][0]:
                test = False
                QMessageBox.critical(self, "Предупреждение", "Проверьте заполнение {}".format(key),
                                           QMessageBox.Ok)
                break

        if test:
            file = QFileDialog.getOpenFileName(self, 'Open file')[0]
            if file != "":
                self.path = resave_xls_to_xlsx(file)
                self.file_open()

    def button_refresh_click(self):
        if self.path:
            self.file_open()

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        pass

    def table_physical_properties_click(self):
        pass

    def get_customer_data(self):
        """Возвращает данные по заказчику"""
        return self._data_customer

    def get_physical_data(self):
        """Возвращает данные по физике"""
        return self._data[self._laboratory_number].physical_properties

    def get_data(self):
        """Возвращает данные по физике"""
        return self._data[self._laboratory_number]

    def get_lab_number(self):
        """Возвращает данные по физике"""
        return self._laboratory_number

class RezonantColumnStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"p_ref": ["Выберите референтное давление", "Pref: Pref из столбца FV",
                                          "Pref: Через бытовое давление"],
                                "k0_condition": ["Тип определения K0",
                                                 "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                                                 "K0: K0 из ведомости", "K0: Формула Джекки",
                                                 "K0: K0 = 1"]
                                }

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, МПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "e": "Коэффициент пористости, е",
            "reference_pressure": "Референтное давление, МПа",
            "K0": "K0"}

        super().__init__(data_test_parameters, fill_keys)

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path != "":

            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            if combo_params["p_ref"] == "Pref: Pref из столбца FV":
                columns_marker = ["FV"]
            elif combo_params["p_ref"] == "Pref: Через бытовое давление":
                columns_marker = ["A"]
            columns_marker_k0 = k0_test_type_column(combo_params["k0_condition"])
            marker, customer = read_customer(wb)

            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker)),\
                    "Заполните K0 в ведомости"
                assert column_fullness_test(wb, columns=["BD", "BC", "BE"], initial_columns=list(columns_marker)), \
                    "Заполните параметры прочности и деформируемости (BD, BC, BE)"
                assert not marker, "Проверьте заказчиков и даты"# + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                self.open_line.text_file_path.setText("")
                self._data_customer = customer
                self._data = getRCExcelData(self.path, combo_params["k0_condition"])

                if len(self._data) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.customer_line.set_data(self._data_customer)
                    self.table_physical_properties.set_data(self._data)
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

    def table_physical_properties_click(self, laboratory_number):
        data = self._data[laboratory_number]
        self._laboratory_number = laboratory_number
        self.table_vertical.set_data(data)
        self.signal.emit(data)

class TriaxialStaticStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"equipment": ["Выберите прибор", "ЛИГА", "АСИС ГТ.2.0.5", "GIESA UP-25a"],
                                "test_type": ["Выберите тип испытания", "Трёхосное сжатие (E)",
                                              "Трёхосное сжатие (F, C)",
                                              "Трёхосное сжатие (F, C, E)",
                                              "Трёхосное сжатие с разгрузкой"],
                                "k0_condition": ["Тип определения K0",
                                                 "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                                                 "K0: K0 из ведомости", "K0: Формула Джекки",
                                                 "K0: K0 = 1"]}

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "qf": "Максимальный девиатор qf, кПа",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "K0": "K0",
            "poisons_ratio": "Коэффициент Пуассона",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "build_press": "Давление от здания, кПа",
            "pit_depth": "Глубина котлована, м",
            "Eur": "Модуль разгрузки Eur, кПа",
            "dilatancy_angle": "Угол дилатансии, град",
            "OCR": "OCR",
            "m": "Показатель степени жесткости"
        }

        super().__init__(data_test_parameters, fill_keys)

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            try:
                wb = load_workbook(self.path, data_only=True)

                combo_params = self.open_line.get_data()

                columns_marker_cfe = cfe_test_type_columns(combo_params["test_type"])
                columns_marker_k0 = k0_test_type_column(combo_params["k0_condition"])
                marker, customer = read_customer(wb)

                try:
                    assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker_cfe)), \
                        "Заполните K0 в ведомости"
                    assert not marker, "Проверьте "  # + customer
                    #assert column_fullness_test(wb, columns=["CC", "CF"], initial_columns=list(columns_marker_cfe)), \
                        #"Заполните данные консолидации('CC', 'CF')"

                except AssertionError as error:
                    QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
                else:
                    self.table_physical_properties._clear_table()
                    self.open_line.text_file_path.setText("")
                    self._data_customer = customer

                    self._data = getMechanicalExcelData(self.path, test_mode=combo_params["test_type"],
                                                        K0_mode=combo_params["k0_condition"])

                    if len(self._data) < 1:
                        QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта",
                                             QMessageBox.Ok)
                    else:
                        self.customer_line.set_data(self._data_customer)
                        self.table_physical_properties.set_data(self._data)
                        self.statment_directory.emit(self.path)
                        self.open_line.text_file_path.setText(self.path)

            except TypeError as err:
                print(str(err))

    def table_physical_properties_click(self, laboratory_number):
        data = self._data[laboratory_number]
        self._laboratory_number = laboratory_number
        type = self.open_line.get_data()
        setattr(data, "test_type", type["test_type"])
        self.table_vertical.set_data(data)
        self.signal.emit(data)

class TriaxialCyclicStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"equipment": ["Выберите прибор", "Прибор: Вилли", "Прибор: Геотек"],
                                "test_type": ["Режим испытания", "Сейсморазжижение", "Штормовое разжижение"],
                                "k0_condition": ["Тип определения K0",
                                                 "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                                                 "K0: K0 из ведомости", "K0: Формула Джекки",
                                                 "K0: K0 = 1"]
                                }

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

        super().__init__(data_test_parameters, fill_keys)

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path != "":

            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker = cfe_test_type_columns(combo_params["test_type"])
            columns_marker_k0 = k0_test_type_column(combo_params["k0_condition"])
            marker, customer = read_customer(wb)

            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker)),\
                    "Заполните K0 в ведомости"
                assert not marker, "Проверьте "# + customer
                assert column_fullness_test(wb, columns=["AJ"], initial_columns=list(columns_marker)), \
                    "Заполните уровень грунтовых вод в ведомости"

                if combo_params["test_type"] == "Штормовое разжижение":
                    assert column_fullness_test(wb, columns=['HR', 'HS', 'HT','HU'], \
                                                    initial_columns=list(columns_marker)), "Заполните данные по шторму в ведомости"
                elif combo_params["test_type"] == "Штормовое разжижение":
                    assert column_fullness_test(wb, columns=["AM", "AQ"],
                                                    initial_columns=list(columns_marker)), \
                        "Заполните магнитуду и бальность"
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                self.table_physical_properties._clear_table()
                self.open_line.text_file_path.setText("")
                self._data_customer = customer
                self._data = getCyclicExcelData(self.path, combo_params["test_type"], combo_params["k0_condition"])

                if len(self._data) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.customer_line.set_data(self._data_customer)
                    self.table_physical_properties.set_data(self._data)
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

    def table_physical_properties_click(self, laboratory_number):
        data = self._data[laboratory_number]
        self._laboratory_number = laboratory_number
        type = self.open_line.get_data()
        setattr(data, "test_type", type["test_type"])
        self.table_vertical.set_data(data)
        self.signal.emit(data)

class VibrationCreepStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"static_equipment": ["Выберите прибор статики", "ЛИГА", "АСИС ГТ.2.0.5", "GIESA UP-25a"],
                                "dynamic_equipment": ["Выберите прибор динамики", "Wille", "Геотек"],
                                "k0_condition": ["Тип определения K0",
                                                 "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                                                 "K0: K0 из ведомости", "K0: Формула Джекки",
                                                 "K0: K0 = 1"]}

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "qf": "Максимальный девиатор qf, кПа",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "t": "Касательное напряжение τ, кПа",
            "Kd": "Kd, д.е.",
            "frequency": "Частота, Гц",
            "K0": "K0, д.е.",
            "poisons_ratio": "Коэффициент Пуассона, д.е.",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "dilatancy_angle": "Угол дилатансии, град",
            "OCR": "OCR",
            "m": "Показатель степени жесткости"
        }

        super().__init__(data_test_parameters, fill_keys)

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker_cfe = cfe_test_type_columns("Виброползучесть")
            columns_marker_k0 = k0_test_type_column(combo_params["k0_condition"])
            marker, customer = read_customer(wb)


            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker_cfe)),\
                    "Заполните K0 в ведомости"
                assert not marker, "Проверьте "# + customer
                assert column_fullness_test(wb, columns=["AO"],
                                            initial_columns=cfe_test_type_columns("Виброползучесть")), \
                    "Заполните амплитуду ('AO')"
                assert column_fullness_test(wb, columns=["CB"],
                                            initial_columns=cfe_test_type_columns("Виброползучесть")), \
                    "Заполните амплитуду ('CB')"

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                self._data_customer = customer

                self._data = getVibrationCreepExcelData(self.path, combo_params["k0_condition"])

                if len(self._data) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker_cfe), QMessageBox.Ok)
                else:
                    self.customer_line.set_data(self._data_customer)
                    self.table_physical_properties.set_data(self._data)
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

    def table_physical_properties_click(self, laboratory_number):
        data = self._data[laboratory_number]
        self._laboratory_number = laboratory_number
        #type = self.open_line.get_data()
        #setattr(data, "test_type", type["test_type"])
        self.table_vertical.set_data(data)
        self.signal.emit(data)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    Dialog = VibrationCreepStatment()
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())


class Progressbar(QWidget):
    def __init__(self, count):
        super().__init__()
        self.count = count
        self.setWindowTitle('Процесс выполнения')
        self.progressBar = QProgressBar(self)
        self.label = QLabel("Процесс выполнения: 0 из {}".format(self.count))
        layout = QVBoxLayout(self)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.label)
        self.set_params(0)

    def set_params(self, val):
        self.progressBar.setProperty("value", round(val*100/self.count))
        self.label.setText("Процесс выполнения: {} из {}".format(val, self.count))

"""
if __name__ == "__main__":
    main = QApplication(sys.argv)
    window = Progressbar(5)


    timer = QtCore.QTimer()

    def h():
        [i*i for i in range(1000000)]


    def onTimer():
        for i in range(6):
            h()
            window.set_params(i)

    timer.singleShot(1000, onTimer)
    timer.start(1000)

    window.show()
    sys.exit(main.exec_())"""
