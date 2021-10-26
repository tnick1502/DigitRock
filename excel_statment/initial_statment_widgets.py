from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QGroupBox, QTableWidget, QDialog, \
    QComboBox, QWidget, QHeaderView, QTableWidgetItem, QFileSystemModel, QTreeView, QLineEdit, QSplitter, QPushButton, \
    QVBoxLayout, QLabel, QMessageBox, QProgressBar, QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtGui import QPainter, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
import sys
import os

from openpyxl import load_workbook
from general.excel_functions import cfe_test_type_columns, k0_test_type_column, column_fullness_test, read_customer
from excel_statment.initial_tables import TableCastomer, ComboBox_Initial_Parameters, TableVertical, TablePhysicalProperties

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties, VibrationCreepProperties, ConsolidationProperties
from excel_statment.position_configs import IdentificationColumns
from loggers.logger import app_logger, log_this
from singletons import statment, models, E_models, FC_models, VC_models
from resonant_column.rezonant_column_hss_model import ModelRezonantColumnSoilTest
from consolidation.consolidation_model import ModelTriaxialConsolidationSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoadingSoilTest
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoadSoilTest
from static_loading.mohr_circles_test_model import ModelMohrCirclesSoilTest
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest


class InitialStatment(QWidget):
    """Класс макет для ведомости
    Входные параметры как у предыдущих классов (ComboBox_Initial_Parameters + Table_Vertical)
    Для кастомизации надо переопределить методы file_open и table_physical_properties_click"""
    statment_directory = pyqtSignal(str)
    signal = pyqtSignal(bool)

    def __init__(self, test_parameters, fill_keys, identification_column=None):
        super().__init__()

        self.identification_column = identification_column if identification_column else None
        self.test_parameters = test_parameters

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

        self.customer_line = TableCastomer()
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
            self.path = QFileDialog.getOpenFileName(self, 'Open file')[0]
            if self.path != "":
                self.file_open()

    def button_refresh_click(self):
        if self.path:
            self.file_open()

    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        pass

    @log_this(app_logger, "debug")
    def table_physical_properties_click(self, laboratory_number):
        self.table_vertical.set_data()
        self.signal.emit(True)

class RezonantColumnStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {#"p_ref": ["Выберите референтное давление", "Pref: Pref из столбца FV",
                                          #"Pref: Через бытовое давление"],
                                "K0_mode": ["Тип определения K0",
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

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker = ["FV"]

            columns_marker_k0 = k0_test_type_column(combo_params["K0_mode"])
            marker, customer = read_customer(wb)

            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=columns_marker),\
                    "Заполните K0 в ведомости"
                assert column_fullness_test(wb, columns=["BD", "BC", "BE"], initial_columns=columns_marker), \
                    "Заполните параметры прочности и деформируемости (BD, BC, BE)"
                assert not marker, "Проверьте " + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/Резонансная колонка.pickle"

                if os.path.exists(statment_file):
                    statment.load(statment_file)
                    app_logger.info(f"Загружен сохраненный файл ведомости Резонансная колонка.pickle")
                else:
                    statment.setTestClass(RCProperties)
                    combo_params["test_mode"] = "Резонансная колонка"
                    statment.setGeneralParameters(combo_params)
                    statment.readExcelFile(self.path, IdentificationColumns["Резонансная колонка"])
                    statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name="Резонансная колонка.pickle")

                self.customer_line.set_data()

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.reference_pressure:
                        del statment.tests[test]

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)
                    app_logger.info(f"Загружена ведомость: {self.path}")

                    model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/rc_models.pickle"
                    models.setModelType(ModelRezonantColumnSoilTest)

                    if os.path.exists(model_file):
                        app_logger.info("Загружен файл модели")
                        models.load(model_file)
                    else:
                        models.generateTests()
                        models.dump("".join([i for i in os.path.split(self.path)[:-1]]), name="rc_models.pickle")

class TriaxialStaticStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "equipment": [
                "Выберите прибор",
                "ЛИГА КЛ-1С",
                "АСИС ГТ.2.0.5",
                "GIESA UP-25a",
                "АСИС ГТ.2.0.5 (150х300)",
            ],

            "test_mode": [
                "Выберите тип испытания", "Трёхосное сжатие (E)",
                "Трёхосное сжатие (F, C)",
                "Трёхосное сжатие (F, C, E)",
                "Трёхосное сжатие с разгрузкой"],

            "K0_mode": [
                "Тип определения K0",
                "K0: По ГОСТ-65353", "K0: K0nc из ведомости",
                "K0: K0 из ведомости", "K0: Формула Джекки",
                "K0: K0 = 1"
            ]}

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

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker = cfe_test_type_columns(combo_params["test_mode"])
            columns_marker_k0 = k0_test_type_column(combo_params["K0_mode"])
            marker, customer = read_customer(wb)

            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker)), \
                    "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer
                #assert column_fullness_test(wb, columns=["CC", "CF"], initial_columns=list(columns_marker_cfe)), \
                    #"Заполните данные консолидации('CC', 'CF')"

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:

                def load_statment(statment_name):

                    statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name

                    if os.path.exists(statment_file):
                        statment.load(statment_file)
                        app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
                    else:
                        statment.setTestClass(MechanicalProperties)
                        statment.setGeneralParameters(combo_params)
                        statment.readExcelFile(self.path, None)
                        statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)

                load_statment(self.open_line.get_data()["test_mode"] + ".pickle")

                statment.general_parameters.reconsolidation = False

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]

                self.customer_line.set_data()

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)
                    app_logger.info(f"Загружена ведомость: {self.path}")

                    def load_E_models():
                        E_model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/E_models.pickle"
                        E_models.setModelType(ModelTriaxialStaticLoadSoilTest)

                        if os.path.exists(E_model_file):
                            app_logger.info("Загружен файл модели")
                            E_models.load(E_model_file)
                        else:
                            E_models.generateTests()
                            E_models.dump("".join([i for i in os.path.split(self.path)[:-1]]), "E_models.pickle")

                    def load_FC_models():
                        FC_model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/FC_models.pickle"
                        FC_models.setModelType(ModelMohrCirclesSoilTest)

                        if os.path.exists(FC_model_file):
                            app_logger.info("Загружен файл модели")
                            FC_models.load(FC_model_file)
                        else:
                            FC_models.generateTests()
                            FC_models.dump("".join([i for i in os.path.split(self.path)[:-1]]), "FC_models.pickle")

                    if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C)":
                        load_FC_models()

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (E)" or statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
                        load_E_models()

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                        load_E_models()
                        load_FC_models()

class CyclicStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "test_mode": [
                "Режим испытания",
                "Сейсморазжижение",
                "Штормовое разжижение"
            ],
            "K0_mode": [
                "Тип определения K0",
                "K0: По ГОСТ-65353",
                "K0: K0nc из ведомости",
                "K0: K0 из ведомости",
                "K0: Формула Джекки",
                "K0: K0 = 1"
            ]
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

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker = cfe_test_type_columns(combo_params["test_mode"])
            columns_marker_k0 = k0_test_type_column(combo_params["K0_mode"])
            marker, customer = read_customer(wb)

            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker)),\
                    "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer
                assert column_fullness_test(wb, columns=["AJ"], initial_columns=list(columns_marker)), \
                    "Заполните уровень грунтовых вод в ведомости"

                if combo_params["test_mode"] == "Штормовое разжижение":
                    assert column_fullness_test(wb, columns=['HR', 'HS', 'HT','HU'], \
                                                    initial_columns=list(columns_marker)), "Заполните данные по шторму в ведомости"
                elif combo_params["test_mode"] == "Штормовое разжижение":
                    assert column_fullness_test(wb, columns=["AM", "AQ"],
                                                    initial_columns=list(columns_marker)), \
                        "Заполните магнитуду и бальность"
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                def load_statment(statment_name):

                    statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name

                    if os.path.exists(statment_file):
                        statment.load(statment_file)
                        app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
                    else:
                        statment.setTestClass(CyclicProperties)
                        statment.setGeneralParameters(combo_params)
                        statment.readExcelFile(self.path, None)
                        statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)

                load_statment(self.open_line.get_data()["test_mode"] + ".pickle")

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]

                self.customer_line.set_data()

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)
                    app_logger.info(f"Загружена ведомость: {self.path}")

                    model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/cyclic_models.pickle"
                    models.setModelType(ModelTriaxialCyclicLoadingSoilTest)

                    if os.path.exists(model_file):
                        app_logger.info("Загружен файл модели")
                        models.load(model_file)
                    else:
                        models.generateTests()
                        models.dump("".join([i for i in os.path.split(self.path)[:-1]]), name="cyclic_models.pickle")

class VibrationCreepStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"static_equipment": ["Выберите прибор статики", "ЛИГА", "АСИС ГТ.2.0.5", "GIESA UP-25a"],
                                "K0_mode": ["Тип определения K0",
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

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            columns_marker_cfe = cfe_test_type_columns("Виброползучесть")
            columns_marker_k0 = k0_test_type_column(combo_params["K0_mode"])
            marker, customer = read_customer(wb)


            try:
                assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker_cfe)),\
                    "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer
                assert column_fullness_test(wb, columns=["AO"],
                                            initial_columns=cfe_test_type_columns("Виброползучесть")), \
                    "Заполните амплитуду ('AO')"

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:

                def load_statment(statment_name):

                    statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name

                    if os.path.exists(statment_file):
                        statment.load(statment_file)
                        app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
                    else:
                        statment.setTestClass(VibrationCreepProperties)
                        combo_params["test_mode"] = "Виброползучесть"
                        statment.setGeneralParameters(combo_params)
                        statment.readExcelFile(self.path, None)
                        statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)

                load_statment("Виброползучесть.pickle")

                self.customer_line.set_data()

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта"
                                        + str(cfe_test_type_columns("Виброползучесть")), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    app_logger.info(f"Загружена ведомость: {self.path}")

                    def load_E_models():
                        E_model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/E_models.pickle"
                        E_models.setModelType(ModelTriaxialStaticLoadSoilTest)

                        if os.path.exists(E_model_file):
                            app_logger.info("Загружен файл модели E_models.pickle")
                            E_models.load(E_model_file)
                        else:
                            E_models.generateTests()
                            E_models.dump("".join([i for i in os.path.split(self.path)[:-1]]), "E_models.pickle")

                    def load_VC_models():
                        VC_model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/VC_models.pickle"
                        VC_models.setModelType(ModelVibrationCreepSoilTest)

                        if os.path.exists(VC_model_file):
                            #app_logger.info("Загружен файл модели")
                            VC_models.load(VC_model_file)
                        else:
                            VC_models.generateTests()
                            VC_models.dump("".join([i for i in os.path.split(self.path)[:-1]]), "VC_models.pickle")

                    load_E_models()
                    load_VC_models()

class ConsolidationStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "equipment": ["Выберите прибор", "ЛИГА", "АСИС ГТ.2.0.5", "GIESA UP-25a"]
        }

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "Eoed": "Одометрический модуль Eoed, кПа",
            "p_max": "Максимальное давление, МПа",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "m": "Показатель степени жесткости"
        }

        super().__init__(data_test_parameters, fill_keys)

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            wb = load_workbook(self.path, data_only=True)

            combo_params = self.open_line.get_data()

            marker, customer = read_customer(wb)

            try:
                assert not marker, "Проверьте " + customer
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:

                def load_statment(statment_name):
                    statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name

                    if os.path.exists(statment_file):
                        statment.load(statment_file)
                        app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
                    else:
                        statment.setTestClass(ConsolidationProperties)
                        statment.setGeneralParameters(combo_params)
                        statment.readExcelFile(self.path, None)
                        statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)

                load_statment("consolidation.pickle")

                self.customer_line.set_data()

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.Eoed:
                        del statment.tests[test]

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта Eoed", QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)
                    app_logger.info(f"Загружена ведомость: {self.path}")

                    model_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/consolidation_models.pickle"
                    models.setModelType(ModelTriaxialConsolidationSoilTest)

                    if os.path.exists(model_file):
                        app_logger.info("Загружен файл модели")
                        models.load(model_file)
                    else:
                        models.generateTests()
                        models.dump("".join([i for i in os.path.split(self.path)[:-1]]), name="consolidation_models.pickle")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    Dialog = VibrationCreepStatment()
    Dialog.show()
    app.setStyle('Fusion')


    sys.exit(app.exec_())
