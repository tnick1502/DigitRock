from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QGroupBox, QTableWidget, QDialog, \
    QComboBox, QWidget, QHeaderView, QTableWidgetItem, QFileSystemModel, QTreeView, QLineEdit, QSplitter, QPushButton, \
    QVBoxLayout, QLabel, QMessageBox, QProgressBar, QSlider, QStyle, QStyleOptionSlider, QRadioButton
from PyQt5.QtGui import QPainter, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
import sys
import os

from openpyxl import load_workbook
from excel_statment.functions import read_general_prameters, k0_test_type_column, column_fullness_test
from excel_statment.initial_tables import TableCastomer, ComboBox_Initial_Parameters, TableVertical, TablePhysicalProperties, ComboBox_Initial_ParametersV2

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties, VibrationCreepProperties, ConsolidationProperties, ShearProperties
from loggers.logger import app_logger, log_this
from singletons import statment, E_models, FC_models, VC_models, RC_models, Cyclic_models, Consolidation_models, Shear_models, Shear_Dilatancy_models, VibrationFC_models

from resonant_column.rezonant_column_hss_model import ModelRezonantColumnSoilTest
from consolidation.consolidation_model import ModelTriaxialConsolidationSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoadingSoilTest
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoadSoilTest
from static_loading.mohr_circles_test_model import ModelMohrCirclesSoilTest
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest
from shear_test.shear_test_model import ModelShearSoilTest
from shear_test.shear_dilatancy_test_model import ModelShearDilatancySoilTest
from excel_statment.params import accreditation
from excel_statment.position_configs import c_fi_E_PropertyPosition, GeneralDataColumns
from excel_statment.functions import set_cell_data

from vibration_strength.vibration_strangth_model import CyclicVibrationStrangthMohr

from transliterate import translit


class SetAccreditation(QGroupBox):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.add_UI()

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.setTitle('Аккредитация')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.layout_1 = QHBoxLayout()

        self.label = QLineEdit()
        self.label.setDisabled(True)

        self.rb_layout = QVBoxLayout()

        self.layout_1.addWidget(QLabel("Текущая аккредитация: "))
        self.layout_1.addWidget(self.label)
        self.layout.addLayout(self.layout_1)
        self.layout.addLayout(self.rb_layout)
        self.layout.addStretch(-1)

    def _onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            statment.general_data.accreditation_key = radioButton.value
        self.signal.emit()

    def set_data(self):
        for i in reversed(range(self.rb_layout.count())):
            self.rb_layout.itemAt(i).widget().setParent(None)
        self.label.setText(statment.general_data.accreditation)
        for key in accreditation[statment.general_data.accreditation]:
            setattr(self, "{}_radio".format(translit(key, language_code='ru', reversed=True)), QRadioButton(key))
            rb = getattr(self, "{}_radio".format(translit(key, language_code='ru', reversed=True)))
            rb.value = key
            rb.toggled.connect(self._onClicked)
            self.rb_layout.addWidget(rb)

            if key == statment.general_data.accreditation_key:
                rb.setChecked(True)
            else:
                rb.setChecked(False)

class ShipmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)


        self.setWindowTitle("Ошибка ведомости")

        self.layout = QHBoxLayout()
        self.line = QLineEdit()
        self.line.setText("1")
        self.button = QPushButton("Ok")
        self.button.clicked.connect(self.close)
        #self.button.clicked.connect(self.return_strings)
        self.layout.addWidget(QLabel("Введите номер привоза:"))
        self.layout.addWidget(self.line)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def return_strings(self):
        self.close()
        return self.line.text()

    @staticmethod
    def get_data(parent=None):
        dialog = ShipmentDialog(parent)
        dialog.exec_()
        return dialog.return_strings()

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
        self.accreditation.signal.connect(self.customer_line.set_data)
        self.open_line.button_open.clicked.connect(self.button_open_click)
        self.open_line.button_refresh.clicked.connect(self.button_refresh_click)

    def create_IU(self, fill_keys):

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.open_line = ComboBox_Initial_ParametersV2(self.test_parameters)
        self.open_line.setFixedHeight(120)

        self.customer_line = TableCastomer()
        self.accreditation = SetAccreditation()
        self.accreditation.setFixedWidth(200)
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
        self.customer_layout_widget = QWidget()
        self.customer_layout = QHBoxLayout()
        self.customer_layout.addWidget(self.customer_line)
        self.customer_layout.addWidget(self.accreditation)
        self.customer_layout_widget.setLayout(self.customer_layout)
        self.table_splitter_propetries_customer.addWidget(self.customer_layout_widget)
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
            if combo_params[key] == "Не выбрано":
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

    def load_statment(self, statment_name, properties_type, general_params):

        statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name

        if os.path.exists(statment_file):
            statment.load(statment_file)
            app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
        else:
            statment.setTestClass(properties_type)
            statment.setGeneralParameters(general_params)
            statment.readExcelFile(self.path, None)
            #statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)
            app_logger.info(f"Сгенерирован сохраненен новый файл ведомости {statment_name}")

        self.customer_line.set_data()
        self.accreditation.set_data()

        if statment.general_data.shipment_number == "":
            window = ShipmentDialog()
            statment.general_data.shipment_number = window.get_data()

            set_cell_data(self.path, (GeneralDataColumns["shipment_number"][0],
                                      (GeneralDataColumns["shipment_number"][1])),
                          statment.general_data.shipment_number, sheet="Лист1", color="FF6961")
        statment.save_dir.set_directory(self.path, statment_name.split(".")[0], statment.general_data.shipment_number)

    def load_models(self, models_name, models, models_type):
        if statment.general_data.shipment_number:
            shipment_number = f" - {statment.general_data.shipment_number}"
        else:
            shipment_number = ""

        model_file = os.path.join(statment.save_dir.save_directory, models_name.split(".")[0] + shipment_number + ".pickle")
        models.setModelType(models_type)
        if os.path.exists(model_file):
            models.load(model_file)
            app_logger.info(f"Загружен файл модели {models_name.split('.')[0] + shipment_number + '.pickle'}")
        else:
            models.generateTests()
            models.dump(model_file)
            app_logger.info(f"Сгенерирован сохраненен новый файл модели {models_name.split('.')[0] + shipment_number + '.pickle'}")

    @log_this(app_logger, "debug")
    def table_physical_properties_click(self, laboratory_number):
        self.table_vertical.set_data()
        self.signal.emit(True)

class RezonantColumnStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {#"p_ref": ["Выберите референтное давление", "Pref: Pref из столбца FV",
                                          #"Pref: Через бытовое давление"],
                                "K0_mode": {
                                    "label": "Тип определения K0",
                                    "vars": [
                                        "Не выбрано",
                                        "K0: По ГОСТ-56353", "K0: K0nc из ведомости",
                                        "K0: K0 из ведомости", "K0: Формула Джекки",
                                        "K0: K0 = 1", "K0: Формула Джекки c учетом переупл."]
                                }
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
            combo_params = self.open_line.get_data()

            columns_marker = [("FV", 177)]

            marker, customer = read_general_prameters(self.path)

            try:
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert column_fullness_test(self.path, columns=list(zip(*c_fi_E_PropertyPosition["Резонансная колонка"])),
                                            initial_columns=columns_marker), \
                    "Заполните параметры прочности и деформируемости (BD, BC, BE)"

                assert not marker, "Проверьте " + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                combo_params["test_mode"] = "Резонансная колонка"

                self.load_statment(
                    statment_name="Резонансная колонка.pickle",
                    properties_type=RCProperties,
                    general_params=combo_params)

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

                    self.load_models(models_name="rc_models.pickle",
                                     models=RC_models, models_type=ModelRezonantColumnSoilTest)

class TriaxialStaticStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "ЛИГА КЛ-1С",
                    "АСИС ГТ.2.0.5",
                    "GIESA UP-25a",
                    "АСИС ГТ.2.0.5 (150х300)"]
            },

            "test_mode": {
                "label": "Тип испытания",
                "vars": [
                    "Не выбрано",
                    "Трёхосное сжатие (E)",
                    "Трёхосное сжатие (F, C)",
                    "Трёхосное сжатие (F, C, E)",
                    "Трёхосное сжатие с разгрузкой",
                    "Трёхосное сжатие (F, C, Eur)",
                    "Трёхосное сжатие КН",
                    "Трёхосное сжатие НН"]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ-56353",
                    "K0: K0nc из ведомости",
                    "K0: K0 из ведомости",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл."]
            },

            "waterfill": {
                "label": "Водонасыщение",
                "vars": [
                    "Водонасыщенное состояние",
                    "Природная влажность",
                    "Не указывать"
                ]
            },
        }

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
            "m": "Показатель степени жесткости",
            "u": "Поровое давление"
        }

        super().__init__(data_test_parameters, fill_keys)

        self.open_line.combo_waterfill.setCurrentText("Не указывать")

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()
            columns_marker = list(zip(*c_fi_E_PropertyPosition[combo_params["test_mode"]]))
            marker, error = read_general_prameters(self.path)

            try:
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + error
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                self.load_statment(
                    statment_name=self.open_line.get_data()["test_mode"] + ".pickle",
                    properties_type=MechanicalProperties,
                    general_params=combo_params)


                statment.general_parameters.reconsolidation = False

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C)" or \
                            statment.general_parameters.test_mode == "Трёхосное сжатие КН" or \
                            statment.general_parameters.test_mode == "Трёхосное сжатие НН":
                        self.load_models(models_name="FC_models.pickle",
                                         models=FC_models, models_type=ModelMohrCirclesSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                        self.load_models(models_name="E_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
                        self.load_models(models_name="Eur_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                        self.load_models(models_name="E_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)
                        self.load_models(models_name="FC_models.pickle",
                                         models=FC_models, models_type=ModelMohrCirclesSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":
                        self.load_models(models_name="Eur_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)
                        self.load_models(models_name="FC_models.pickle",
                                         models=FC_models, models_type=ModelMohrCirclesSoilTest)

class CyclicStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {

            "test_mode": {
                "label": "Тип испытания",
                "vars": [
                    "Не выбрано",
                    "Сейсморазжижение",
                    "Штормовое разжижение",
                    "Демпфирование",
                    "По заданным параметрам"
                    ]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ-56353",
                    "K0: K0nc из ведомости",
                    "K0: K0 из ведомости",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл."]
            }
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
            "rw": "Плотность воды, кН/м3",
            "damping_ratio": "Коэффициент демпфирования, %"
        }

        super().__init__(data_test_parameters, fill_keys)

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()

            columns_marker = list(zip(*c_fi_E_PropertyPosition[combo_params["test_mode"]]))
            marker, customer = read_general_prameters(self.path)

            try:
                assert column_fullness_test(self.path, columns=[("AJ", 35)], initial_columns=columns_marker), \
                    "Заполните уровень грунтовых вод в ведомости"
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer

                if combo_params["test_mode"] == "Демпфирование":
                    assert column_fullness_test(self.path, columns=[("AO", 40), ("AN", 39)],
                                                initial_columns=columns_marker), \
                        "Заполните амплитуду ('AO') и частоту ('AN')"

                if combo_params["test_mode"] == "Штормовое разжижение":
                    assert column_fullness_test(self.path, columns=[('HR', 225), ('HS', 226), ('HT', 227), ('HU', 228)],
                                                initial_columns=columns_marker), "Заполните данные по шторму в ведомости"
                if combo_params["test_mode"] == "Сейсморазжижение":
                    assert column_fullness_test(self.path, columns=[("AM", 38), ("AQ", 42)], initial_columns=columns_marker), \
                        "Заполните магнитуду и бальность"

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:

                self.load_statment(
                    statment_name=self.open_line.get_data()["test_mode"] + ".pickle",
                    properties_type=CyclicProperties,
                    general_params=combo_params)

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]

                self.customer_line.set_data()
                self.accreditation.set_data()

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    self.load_models(models_name="cyclic_models.pickle",
                                     models=Cyclic_models, models_type=ModelTriaxialCyclicLoadingSoilTest)

class VibrationCreepStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ-56353",
                    "K0: K0nc из ведомости",
                    "K0: K0 из ведомости",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл."]
            }
        }

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

            combo_params = self.open_line.get_data()
            columns_marker = list(zip(*c_fi_E_PropertyPosition["Виброползучесть"]))
            marker, customer = read_general_prameters(self.path)

            try:
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:

                combo_params["test_mode"] = "Виброползучесть"

                self.load_statment(
                    statment_name="Виброползучесть.pickle",
                    properties_type=VibrationCreepProperties,
                    general_params=combo_params)

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта"
                                        + str(c_fi_E_PropertyPosition["Виброползучесть"][0]), QMessageBox.Ok)
                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    app_logger.info(f"Загружена ведомость: {self.path}")

                    self.load_models(models_name="E_models.pickle",
                                     models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    self.load_models(models_name="VC_models.pickle",
                                     models=VC_models, models_type=ModelVibrationCreepSoilTest)

class ConsolidationStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {

            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "Не выбрано",
                    "ЛИГА КЛ1",
                    "КППА 60/25 ДС (ГТ 1.1.1)",
                    "GIG, Absolut Digimatic ID-S",
                    "АСИС ГТ.2.0.5"]
            }
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

            combo_params = self.open_line.get_data()
            marker, customer = read_general_prameters(self.path)

            try:
                assert not marker, "Проверьте " + customer
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                combo_params["test_mode"] = "Консолидация"

                self.load_statment(
                    statment_name="Консолидация.pickle",
                    properties_type=ConsolidationProperties,
                    general_params=combo_params)

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

                    self.load_models(models_name="consolidation_models.pickle",
                                     models=Consolidation_models, models_type=ModelTriaxialConsolidationSoilTest)

class ShearStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    SHEAR_NATURAL = ShearProperties.SHEAR_NATURAL
    '''Срез природное'''
    SHEAR_SATURATED = ShearProperties.SHEAR_SATURATED
    '''Срез водонасыщенное'''
    SHEAR_DD = ShearProperties.SHEAR_DD
    '''Срез плашка по плашке'''
    SHEAR_NN = ShearProperties.SHEAR_NN
    '''Срез НН'''
    SHEAR_DILATANCY = ShearProperties.SHEAR_DILATANCY
    '''Срез дилатансия'''
    def __init__(self):
        data_test_parameters = {

            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "Не выбрано",
                    "АСИС ГТ.2.0.5",
                    "GIESA UP-25a",]
            },

            "test_mode": {
                "label": "Тип испытания",
                "vars": [
                    "Не выбрано",
                    "Срез природное",
                    "Срез водонасыщенное",
                    "Срез плашка по плашке",
                    "Срез НН",
                    "Срез дилатансия"]
            },

            "optional": {
                "label": "Водонасыщение",
                "vars": [
                    "Не выбрано",
                    "Природное",
                    "Водонасщенное"]
            }
            }

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "tau_max": "Максимальное касательное напряжение τ, кПа",
            "sigma": "Нормальное напряжение 𝜎, кПа",
            "poisons_ratio": "Коэффициент Пуассона",
            "build_press": "Давление от здания, кПа",
            "pit_depth": "Глубина котлована, м",
            "dilatancy_angle": "Угол дилатансии, град"
        }

        super().__init__(data_test_parameters, fill_keys)

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            combo_params = self.open_line.get_data()

            columns_marker = c_fi_E_PropertyPosition[combo_params["test_mode"]][0]
            marker, customer = read_general_prameters(self.path)

            try:
                # assert column_fullness_test(wb, columns=columns_marker_k0, initial_columns=list(columns_marker)), \
                #     "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer
                #assert column_fullness_test(wb, columns=["CC", "CF"], initial_columns=list(columns_marker_cfe)), \
                    #"Заполните данные консолидации('CC', 'CF')"

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:

                self.load_statment(
                    statment_name=self.open_line.get_data()["test_mode"] + ".pickle",
                    properties_type=ShearProperties,
                    general_params=combo_params)

                statment.general_parameters.reconsolidation = False

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.c or not statment[test].mechanical_properties.fi:
                        del statment.tests[test]

                pref_warning = False
                keys = list(statment.tests.keys())
                for test in keys:
                    if statment[test].mechanical_properties.pref_warning:
                        pref_warning = True

                if pref_warning:
                    QMessageBox.warning(QWidget(),
                                        "Внимание!",
                                        f"Референтное давление на задано. Используется расчётное")

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                    self.table_vertical.clear()
                    self.table_physical_properties.clear()
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    # if ShearStatment.shear_type(statment.general_parameters.test_mode) == self.SHEAR_NATURAL:
                    #     self.load_models(models_name="Shear_natural_models.pickle",
                    #                      models=Shear_models, models_type=ModelShearSoilTest)
                    # elif ShearStatment.shear_type(statment.general_parameters.test_mode) == self.SHEAR_SATURATED:
                    #     self.load_models(models_name="Shear_saturated_models.pickle",
                    #                      models=Shear_models, models_type=ModelShearSoilTest)
                    # elif ShearStatment.shear_type(statment.general_parameters.test_mode) == self.SHEAR_DD:
                    #     self.load_models(models_name="Shear_dd_models.pickle",
                    #                      models=Shear_models, models_type=ModelShearSoilTest)
                    # elif ShearStatment.shear_type(statment.general_parameters.test_mode) == self.SHEAR_NN:
                    #     self.load_models(models_name="Shear_nn_models.pickle",
                    #                      models=Shear_models, models_type=ModelShearSoilTest)
                    # elif ShearStatment.shear_type(statment.general_parameters.test_mode) == self.SHEAR_DILATANCY:
                    #     self.load_models(models_name="Shear_dilatancy_models.pickle",
                    #                      models=Shear_Dilatancy_models, models_type=ModelShearDilatancySoilTest)
                    _test_mode = statment.general_parameters.test_mode
                    if not ShearStatment.is_dilatancy_type(_test_mode):
                        self.load_models(models_name=ShearStatment.models_name(ShearStatment.shear_type(_test_mode)).split('.')[0],
                                         models=Shear_models, models_type=ModelShearSoilTest)
                    elif ShearStatment.is_dilatancy_type(_test_mode):
                        self.load_models(models_name=ShearStatment.models_name(ShearStatment.shear_type(_test_mode)).split('.')[0],
                                         models=Shear_Dilatancy_models, models_type=ModelShearDilatancySoilTest)

    def button_open_click(self):
        combo_params = self.open_line.get_data()
        test = True
        for key in self.test_parameters:
            if key == "optional":
                continue
            if combo_params[key] == self.test_parameters[key]["vars"][0]:
                test = False
                QMessageBox.critical(self, "Предупреждение", "Проверьте заполнение {}".format(key),
                                           QMessageBox.Ok)
                break

        if test:
            self.path = QFileDialog.getOpenFileName(self, 'Open file')[0]
            if self.path != "":
                self.file_open()

    def set_optional_parameter(self, test_mode):
        obj = getattr(self.open_line, "combo_optional")
        if ShearStatment.shear_type(test_mode) == ShearStatment.SHEAR_NATURAL:
            obj.setCurrentIndex(1)
        elif ShearStatment.shear_type(test_mode) == ShearStatment.SHEAR_SATURATED:
            obj.setCurrentIndex(2)
        else:
            obj.setCurrentIndex(0)

    def shear_test_type_from_open_line(self) -> int:
        test_mode = self.open_line.get_data()["test_mode"]
        return ShearProperties.shear_type(test_mode)

    @staticmethod
    def shear_type(test_mode) -> int:
        return ShearProperties.shear_type(test_mode)

    @staticmethod
    def is_dilatancy_type(test_mode) -> bool:
        return ShearProperties.is_dilatancy_type(test_mode)

    @staticmethod
    def models_name(shear_type: int) -> str:
        if shear_type == ShearStatment.SHEAR_NATURAL:
            return "Shear_natural_models.pickle"
        elif shear_type == ShearStatment.SHEAR_SATURATED:
            return "Shear_saturated_models.pickle"
        elif shear_type == ShearStatment.SHEAR_NN:
            return "Shear_nn_models.pickle"
        elif shear_type == ShearStatment.SHEAR_DD:
            return "Shear_dd_models.pickle"
        elif shear_type == ShearStatment.SHEAR_DILATANCY:
            return "Shear_dilatancy_models.pickle"

        return "models.pickle"

class VibrationStrangthStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "ЛИГА КЛ-1С",
                    "АСИС ГТ.2.0.5",
                    "GIESA UP-25a",
                    "АСИС ГТ.2.0.5 (150х300)"]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ-56353",
                    "K0: K0nc из ведомости",
                    "K0: K0 из ведомости",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл."]
            },

            "waterfill": {
                "label": "Водонасыщение",
                "vars": [
                    "Водонасыщенное состояние",
                    "Природная влажность",
                    "Не указывать"
                ]
            },
        }

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
            "m": "Показатель степени жесткости",
            "u": "Поровое давление"
        }

        super().__init__(data_test_parameters, fill_keys)

        self.open_line.combo_waterfill.setCurrentText("Не указывать")

    @log_this(app_logger, "debug")
    def file_open(self):
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()
            combo_params["test_mode"] = "Вибропрочность"
            columns_marker = list(zip(*c_fi_E_PropertyPosition[combo_params["test_mode"]]))
            marker, error = read_general_prameters(self.path)

            try:
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + error
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                self.load_statment(
                    statment_name=combo_params["test_mode"] + ".pickle",
                    properties_type=MechanicalProperties,
                    general_params=combo_params)


                statment.general_parameters.reconsolidation = False

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    self.load_models(models_name="FC_models.pickle",
                                     models=FC_models, models_type=ModelMohrCirclesSoilTest)
                    self.load_models(models_name="VibrationFC_models.pickle",
                                     models=VibrationFC_models, models_type=CyclicVibrationStrangthMohr)


class K0Statment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {"K0_mode": {"label": "Тип определения K0",
                                            "vars": ["Не выбрано",
                                                     "K0: По ГОСТ-56353", "K0: K0nc из ведомости",
                                                     "K0: K0 из ведомости", "K0: Формула Джекки",
                                                     "K0: K0 = 1", "K0: Формула Джекки c учетом переупл."]}}

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, МПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "e": "Коэффициент пористости, е",
            "reference_pressure": "Референтное давление, МПа",
            "K0": "K0"}

        super().__init__(data_test_parameters, fill_keys)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShipmentDialog()
    print(window.get_data())
    #print(Dialog.save())
    app.setStyle('Fusion')
    sys.exit(app.exec_())
