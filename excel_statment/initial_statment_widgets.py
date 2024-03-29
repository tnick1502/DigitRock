from typing import List

from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QGroupBox, QTableWidget, QDialog, \
    QComboBox, QWidget, QHeaderView, QTableWidgetItem, QFileSystemModel, QTreeView, QLineEdit, QSplitter, QPushButton, \
    QVBoxLayout, QLabel, QMessageBox, QProgressBar, QSlider, QStyle, QStyleOptionSlider, QRadioButton, QGridLayout
from PyQt5.QtGui import QPainter, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
import sys
import os

from openpyxl import load_workbook
from excel_statment.functions import read_general_prameters, k0_test_type_column, column_fullness_test
from excel_statment.initial_tables import TableCastomer, ComboBox_Initial_Parameters, TableVertical, TablePhysicalProperties, ComboBox_Initial_ParametersV2

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties, VibrationCreepProperties, ConsolidationProperties, ShearProperties, RayleighDampingProperties, K0Properties
from loggers.logger import app_logger, log_this
from singletons import statment, E_models, FC_models, VC_models, RC_models, Cyclic_models, Consolidation_models, Shear_models, Shear_Dilatancy_models, VibrationFC_models, RayleighDamping_models, K0_models

from resonant_column.rezonant_column_hss_model import ModelRezonantColumnSoilTest
from consolidation.consolidation_model import ModelTriaxialConsolidationSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoadingSoilTest
from rayleigh_damping.rayleigh_damping_model import ModelRayleighDampingSoilTest
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoadSoilTest
from static_loading.mohr_circles_test_model import ModelMohrCirclesSoilTest
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest
from shear_test.shear_test_model import ModelShearSoilTest
from shear_test.shear_dilatancy_test_model import ModelShearDilatancySoilTest
from k0_test.triaxial_k0_model import ModelK0SoilTest

from excel_statment.params import accreditation
from cyclic_loading.cyclic_stress_ratio_function import define_cycles_array_from_count_linery, define_t_from_csr, define_t_from_csr, define_csr_from_cycles_array, cyclic_stress_ratio_curve_params
from excel_statment.position_configs import c_fi_E_PropertyPosition, GeneralDataColumns, MechanicalPropertyPosition
from excel_statment.functions import set_cell_data
from metrics.session_writer import SessionWriter

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

    def __init__(self, test_parameters, fill_keys, identification_column=None, generate=True):
        super().__init__()

        self.identification_column = identification_column if identification_column else None
        self.test_parameters = test_parameters

        self.path = ""

        self.force_recreate = False

        self.generate = generate

        self.create_IU(fill_keys)
        self.open_line.combo_changes_signal.connect(self.file_open)
        self.table_physical_properties.laboratory_number_click_signal.connect(self.table_physical_properties_click)
        self.accreditation.signal.connect(self.customer_line.set_data)
        self.open_line.button_open.clicked.connect(self.button_open_click)
        self.open_line.button_refresh.clicked.connect(self.button_refresh_click)

    def create_IU(self, fill_keys):

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.table_vertical = TableVertical(fill_keys)

        self.open_line = ComboBox_Initial_ParametersV2(self.test_parameters)
        self.open_line.setFixedHeight(120)

        self.customer_line = TableCastomer()
        self.accreditation = SetAccreditation()
        self.accreditation.setFixedWidth(200)
        self.accreditation.setFixedHeight(165)
        #self.customer_line.setFixedHeight(80)
        self.table_physical_properties = TablePhysicalProperties()
        self.table_physical_properties.setMinimumWidth(1400)


        self.customer_layout = QHBoxLayout()
        self.customer_layout.addWidget(self.customer_line)
        self.customer_layout.addWidget(self.accreditation)


        self.layout.addWidget(self.open_line)
        self.layout.addLayout(self.customer_layout)
        self.layout.addWidget(self.table_physical_properties)
        self.layuot_for_button = QHBoxLayout()
        self.layuot_for_button.addStretch(-1)
        self.layout.addLayout(self.layuot_for_button)
        self.layuot_for_button.setContentsMargins(5, 5, 5, 5)
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

    def load_statment(self, statment_name, properties_type, general_params, waterfill=''):

        waterfill = ' ' + waterfill if waterfill not in ('', 'Не указывать') else ''

        statment_file = "".join([i for i in os.path.split(self.path)[:-1]]) + "/" + statment_name + waterfill

        if os.path.exists(statment_file) and not self.force_recreate:
            statment.load(statment_file)
            app_logger.info(f"Загружен сохраненный файл ведомости {statment_name}")
        else:
            statment.setTestClass(properties_type)
            statment.setGeneralParameters(general_params)
            statment.readExcelFile(self.path, None)
            #statment.dump("".join([i for i in os.path.split(self.path)[:-1]]), name=statment_name)
            # app_logger.info(f"Сгенерирован сохраненен новый файл ведомости {statment_name}")

        self.customer_line.set_data()
        self.accreditation.set_data()

        if statment.general_data.shipment_number == "":
            window = ShipmentDialog()
            statment.general_data.shipment_number = window.get_data()

            set_cell_data(self.path, (GeneralDataColumns["shipment_number"][0],
                                      (2, 9)),
                          statment.general_data.shipment_number, sheet="Лист1", color="FF6961")
        statment.save_dir.set_directory(self.path, statment_name.split(".")[0] + waterfill, statment.general_data.shipment_number)

    def load_models(self, models_name, models, models_type):
        if statment.general_data.shipment_number:
            shipment_number = f" - {statment.general_data.shipment_number}"
        else:
            shipment_number = ""

        model_file = os.path.join(statment.save_dir.save_directory, models_name.split(".")[0] + shipment_number + ".pickle")
        models.setModelType(models_type)
        if os.path.exists(model_file) and not self.force_recreate:
            try:
                models.load(model_file)
                app_logger.info(f"Загружен файл модели {models_name.split('.')[0] + shipment_number + '.pickle'}")
            except AssertionError as err:
                QMessageBox.critical(self, "Ошибка", str(err), QMessageBox.Ok)
                raise
        else:
            models.generateTests(generate=self.generate)
            models.dump(model_file)
            app_logger.info(f"Сгенерирован сохраненен новый файл модели {models_name.split('.')[0] + shipment_number + '.pickle'}")

    @log_this(app_logger, "debug")
    def table_physical_properties_click(self, laboratory_number):
        self.table_vertical.set_data()
        self.signal.emit(True)

class RezonantColumnStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self, generate=True):
        data_test_parameters = {#"p_ref": ["Выберите референтное давление", "Pref: Pref из столбца FV",
                                          #"Pref: Через бытовое давление"],
                                "K0_mode": {
                                    "label": "Тип определения K0",
                                    "vars": [
                                        "Не выбрано",
                                        "K0: По ГОСТ 12248.3-2020",
                                        "K0: По ГОСТ-56353-2022",
                                        "K0: По ГОСТ-56353-2015",
                                        "K0: Формула Джекки",
                                        "K0: K0 = 1",
                                        "K0: Формула Джекки c учетом переупл.",
                                        "K0: С ведомости (GZ)",
                                        "K0: С ведомости (FW)"]
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

        super().__init__(data_test_parameters, fill_keys, generate=generate)

    @log_this(app_logger, "debug")
    def file_open(self):
        SessionWriter.set_sheet_load_datetime()
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
                    "Заполните параметры прочности и деформируемости (HM, HN, HO)"

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

                    self.load_models(models_name="rc_models.pickle",
                                     models=RC_models, models_type=ModelRezonantColumnSoilTest)

                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

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
                    "Трёхосное сжатие с разгрузкой (plaxis)",
                    "Трёхосное сжатие (F, C, Eur)",
                    "Трёхосное сжатие КН",
                    "Трёхосное сжатие НН",
                    "Трёхосное сжатие (F, C) res"]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ 12248.3-2020",
                    "K0: По ГОСТ-56353-2022",
                    "K0: По ГОСТ-56353-2015",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл.",
                    "K0: С ведомости (GZ)",
                    "K0: С ведомости (FW)"
                ]
            },

            "pressure_mode": {
                "label": "Давление на кругах",
                "vars": [
                    "Автоматически",
                    "Расчетное давление",
                    "По ГОСТу",
                    "Ручные ступени давления"]
            },

            "waterfill": {
                "label": "Водонасыщение",
                "vars": [
                    "Водонасыщенное состояние",
                    "Природная влажность",
                    "Не указывать"
                ]
            },
            "sigma3_lim": {
                "label": "Ограничение на σ3",
                "vars": [
                    "Не менее 50 кПа",
                    "Не менее 100 кПа"
                ]
            },
            "phi_mode": {
                "label": "Тип определения PHI",
                "vars": [
                    "Автоматически",
                    "PHI по ведомости",
                    "PHI с рандомом"
                ]
            }
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

        self.deviations_amplitude = None

        super().__init__(data_test_parameters, fill_keys)

        self.open_line.combo_waterfill.setCurrentText("Не указывать")

        self.deviationsBox = DeviationsCustomBox()

        self.deviationsBox.acceptBtn.clicked.connect(self._onAcceptBtn)

        self.layout.setSpacing(10)

        self.layout.insertWidget(self.layout.count() - 2, self.deviationsBox)

    @log_this(app_logger, "debug")
    def file_open(self):
        SessionWriter.set_sheet_load_datetime()
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()
            columns_marker = list(zip(*c_fi_E_PropertyPosition[combo_params["test_mode"]]))
            marker, error = read_general_prameters(self.path)

            if combo_params["test_mode"] == "Трёхосное сжатие (F, C) res":
                columns_marker.extend([MechanicalPropertyPosition["c_res"], MechanicalPropertyPosition["fi_res"]])

            if self.deviations_amplitude:
                combo_params["deviations_amplitude"] = self.deviations_amplitude

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
                    general_params=combo_params,
                    waterfill=combo_params["waterfill"])

                if self.open_line.get_data()["test_mode"] == "Трёхосное сжатие КН":
                    statment.general_parameters.reconsolidation = True
                else:
                    statment.general_parameters.reconsolidation = False

                keys = list(statment.tests.keys())
                for test in keys:
                    if not statment[test].mechanical_properties.E50:
                        del statment.tests[test]
                        continue

                    if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                        if not statment[test].mechanical_properties.c_res:
                            del statment.tests[test]
                            continue

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:

                    if combo_params["pressure_mode"] == "Расчетное давление":
                        keys = list(statment.tests.keys())
                        for test in keys:
                            if statment[test].mechanical_properties.pressure_array["calculated_by_pressure"] is not None:
                                statment[test].mechanical_properties.pressure_array["current"] = \
                                    statment[test].mechanical_properties.pressure_array["calculated_by_pressure"]
                    elif combo_params["pressure_mode"] == "По ГОСТу":
                        keys = list(statment.tests.keys())
                        for test in keys:
                            if statment[test].mechanical_properties.pressure_array[
                                "state_standard"] is not None:
                                statment[test].mechanical_properties.pressure_array["current"] = \
                                    statment[test].mechanical_properties.pressure_array["state_standard"]
                    elif combo_params["pressure_mode"] == "Ручные ступени давления":
                        keys = list(statment.tests.keys())
                        for test in keys:
                            if statment[test].mechanical_properties.pressure_array[
                                "set_by_user"] is not None:
                                statment[test].mechanical_properties.pressure_array["current"] = \
                                    statment[test].mechanical_properties.pressure_array["set_by_user"]
                    else:
                        pass


                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C)" or \
                            statment.general_parameters.test_mode == "Трёхосное сжатие КН" or \
                            statment.general_parameters.test_mode == "Трёхосное сжатие НН" or \
                            statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                        self.load_models(models_name="FC_models.pickle",
                                         models=FC_models, models_type=ModelMohrCirclesSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                        self.load_models(models_name="E_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
                        self.load_models(models_name="Eur_models.pickle",
                                         models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
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

        self.force_recreate = False

    def _onAcceptBtn(self):

        if E_models or FC_models:
            ret = QMessageBox.question(self, 'Предупреждение',
                                       f"Применение параметров вызовет Полное пересоздание модели и всех опытов. Вы уверены?",
                                       QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                pass
            else:
                return


        if self.deviationsBox.radiobutton_state_standard.isChecked():
            self.deviations_amplitude = None

            if E_models or FC_models:
                self.force_recreate = True
                self.file_open()
            return

        if self.deviationsBox.radiobutton_custom.isChecked():
            try:
                amplitude_1 = float(self.deviationsBox.line_amp1.displayText())
                amplitude_2 = float(self.deviationsBox.line_amp2.displayText())
                amplitude_3 = float(self.deviationsBox.line_amp3.displayText())

                self.deviations_amplitude = [float(amplitude_1), float(amplitude_2), float(amplitude_3)]

            except ValueError:
                QMessageBox.critical(self, "Не верный формат данных", "Укажите в формате x.x",
                                     QMessageBox.Ok)
                return
            except Exception as err:
                QMessageBox.critical(self, "Ошибка", str(err), QMessageBox.Ok)
                return

            if E_models or FC_models:
                self.force_recreate = True
                self.file_open()


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
                    "По заданным параметрам",
                    "Динамическая прочность на сдвиг",
                    "Потенциал разжижения"
                    ]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ 12248.3-2020",
                    "K0: По ГОСТ-56353-2022",
                    "K0: По ГОСТ-56353-2015",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл.",
                    "K0: С ведомости (GZ)",
                    "K0: С ведомости (FW)"
                ]
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
        SessionWriter.set_sheet_load_datetime()
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
                    assert column_fullness_test(self.path, columns=[("AN", 39)],
                                                initial_columns=columns_marker), \
                        "Заполните частоту ('AN')"
                if combo_params["test_mode"] == "Штормовое разжижение":
                    assert column_fullness_test(self.path, columns=[('HR', 225), ('HS', 226), ('HT', 227), ('HU', 228)],
                                                initial_columns=columns_marker), "Заполните данные по шторму в ведомости"
                if combo_params["test_mode"] == "Сейсморазжижение" or combo_params["test_mode"] == "Потенциал разжижения":
                    assert column_fullness_test(self.path, columns=[("AQ", 42)], initial_columns=columns_marker) and \
                           (column_fullness_test(self.path, columns=[("AM", 42)], initial_columns=columns_marker) or
                            column_fullness_test(self.path, columns=[("AP", 42)], initial_columns=columns_marker)), \
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
                    if combo_params["test_mode"] == "Потенциал разжижения":
                        if statment.general_data.shipment_number:
                            shipment_number = f" - {statment.general_data.shipment_number}"
                        else:
                            shipment_number = ""

                        model_file = os.path.join(statment.save_dir.save_directory, "cyclic_models.pickle".split(".")[0] + shipment_number + ".pickle")

                        if not os.path.exists(model_file):
                            test_dict = {}

                            for test in statment:
                                EGE = statment[test].physical_properties.ige
                                if test_dict.get(EGE, None):
                                    test_dict[EGE].append(test)
                                else:
                                    test_dict[EGE] = [test]

                            for EGE in test_dict:
                                count_in_EGE = len(test_dict[EGE])
                                alpha, betta = cyclic_stress_ratio_curve_params(
                                    statment[test_dict[EGE][0]].physical_properties.Ip)
                                cycles = define_cycles_array_from_count_linery(count_in_EGE)
                                csr = define_csr_from_cycles_array(cycles, alpha, betta)

                                for i in range(count_in_EGE):
                                    statment[test_dict[EGE][i]].mechanical_properties.n_fail = cycles[i]
                                    statment[test_dict[EGE][i]].mechanical_properties.t = round(define_t_from_csr(
                                        csr[i],
                                        statment[test_dict[EGE][i]].mechanical_properties.sigma_1
                                    ))
                                    statment[test_dict[EGE][i]].mechanical_properties.cycles_count = int(cycles[i] * 1.1)

                    self.table_physical_properties.set_data()
                    try:
                        self.load_models(models_name="cyclic_models.pickle",
                                         models=Cyclic_models, models_type=ModelTriaxialCyclicLoadingSoilTest)
                        self.statment_directory.emit(self.path)
                        self.open_line.text_file_path.setText(self.path)
                    except Exception as err:
                        print(err)

class VibrationCreepStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
            "test_mode": {
                "label": "Тип испытания",
                "vars": [
                    "Виброползучесть",
                    "Снижение модуля деформации сейсмо"
                ]
            },

            "K0_mode": {
                "label": "Тип определения K0",
                "vars": [
                    "Не выбрано",
                    "K0: По ГОСТ 12248.3-2020",
                    "K0: По ГОСТ-56353-2022",
                    "K0: По ГОСТ-56353-2015",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл.",
                    "K0: С ведомости (GZ)",
                    "K0: С ведомости (FW)"
                ]
            },
            "sigma3_lim": {
                "label": "Ограничение на σ3",
                "vars": ["Не менее 50 кПа",
                         "Не менее 100 кПа"]}
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

        self.deviations_amplitude = None

        super().__init__(data_test_parameters, fill_keys)

        self.deviationsBox = DeviationsCustomBox()

        self.deviationsBox.acceptBtn.clicked.connect(self._onAcceptBtn)

        self.layout.setSpacing(10)

        self.layout.insertWidget(self.layout.count() - 2, self.deviationsBox)

    @log_this(app_logger, "debug")
    def file_open(self):
        SessionWriter.set_sheet_load_datetime()
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            combo_params = self.open_line.get_data()
            columns_marker = list(zip(*c_fi_E_PropertyPosition["Виброползучесть"]))
            marker, customer = read_general_prameters(self.path)

            if self.deviations_amplitude:
                combo_params["deviations_amplitude"] = self.deviations_amplitude

            try:
                assert column_fullness_test(
                    self.path, columns=k0_test_type_column(combo_params["K0_mode"]),
                    initial_columns=columns_marker), "Заполните K0 в ведомости"
                assert not marker, "Проверьте " + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                self.load_statment(
                    statment_name=self.open_line.get_data()["test_mode"] + ".pickle",
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

                    app_logger.info(f"Загружена ведомость: {self.path}")

                    self.load_models(models_name="E_models.pickle",
                                     models=E_models, models_type=ModelTriaxialStaticLoadSoilTest)

                    self.load_models(models_name="VC_models.pickle",
                                     models=VC_models, models_type=ModelVibrationCreepSoilTest)

                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

    def _onAcceptBtn(self):
        if E_models:
            ret = QMessageBox.question(self, 'Предупреждение',
                                       f"Применение параметров вызовет Полное пересоздание модели и всех опытов. Вы уверены?",
                                       QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if ret == QMessageBox.Yes:
                pass
            else:
                return

        if self.deviationsBox.radiobutton_state_standard.isChecked():
            self.deviations_amplitude = None

            if E_models:
                for modelKey in E_models.tests:
                    statment.setCurrentTest(modelKey)
                    statment.tests[modelKey].mechanical_properties.set_deviations_amplitude(self.deviations_amplitude)
                    E_models.tests[modelKey].set_test_params()

                QMessageBox.warning(self, "Обновление завешено", "Все модели обновлены",
                                     QMessageBox.Ok)
            return

        if self.deviationsBox.radiobutton_custom.isChecked():
            try:
                amplitude_1 = float(self.deviationsBox.line_amp1.displayText())
                amplitude_2 = float(self.deviationsBox.line_amp2.displayText())
                amplitude_3 = float(self.deviationsBox.line_amp3.displayText())

                self.deviations_amplitude = [float(amplitude_1), float(amplitude_2), float(amplitude_3)]

            except ValueError:
                QMessageBox.critical(self, "Не верный формат данных", "Укажите в формате x.x",
                                     QMessageBox.Ok)
                return
            except Exception as err:
                QMessageBox.critical(self, "Ошибка", str(err), QMessageBox.Ok)
                return

            if E_models:
                if E_models:
                    for modelKey in E_models.tests:
                        statment.setCurrentTest(modelKey)
                        statment.tests[modelKey].mechanical_properties.deviations_amplitude = self.deviations_amplitude
                        E_models.tests[modelKey].set_test_params()

                    QMessageBox.warning(self, "Обновление завешено", "Все модели обновлены",
                                        QMessageBox.Ok)

class ConsolidationStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        self.test_mode = "Консолидация"

        data_test_parameters = {

            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "Не выбрано",
                    "ЛИГА КЛ1",
                    "КППА 60/25 ДС (ГТ 1.1.1)",
                    "GIG, Absolut Digimatic ID-S",
                    "АСИС ГТ.2.0.5"]
            },
            "axis": {
                "label": "Ось скважены",
                "vars": [
                    "Не выбрано",
                    "Параллельно оси скважены",
                    "Перпендикулярно оси скважены"
                ]
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
        SessionWriter.set_sheet_load_datetime()
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):

            combo_params = self.open_line.get_data()
            marker, customer = read_general_prameters(self.path)

            try:
                assert not marker, "Проверьте " + customer
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                if self.open_line.get_data()["axis"] == 'Не выбрано':
                    combo_params["test_mode"] = "Консолидация"
                else:
                    combo_params["test_mode"] = f"Консолидация {self.open_line.get_data()['axis'].lower()}"

                self.test_mode = combo_params["test_mode"]

                self.load_statment(
                    statment_name=f"{combo_params['test_mode']}.pickle",
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

                    if combo_params["test_mode"] == "Консолидация":
                        models = "consolidation_models.pickle"
                    elif combo_params["test_mode"] == f"Консолидация {self.test_parameters['axis']['vars'][1].lower()}":
                        models = "consolidation_parallel_models.pickle"
                    elif combo_params["test_mode"] == f"Консолидация {self.test_parameters['axis']['vars'][2].lower()}":
                        models = "consolidation_perpendicular_models.pickle"

                    self.load_models(models_name=models,
                                     models=Consolidation_models, models_type=ModelTriaxialConsolidationSoilTest)

    def button_open_click(self):
        combo_params = self.open_line.get_data()
        test = True
        for key in self.test_parameters:
            if key in ["axis"]:
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

class ShearStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    SHEAR = ShearProperties.SHEAR
    '''Cрез не природное и не водонасыщенное'''
    SHEAR_NATURAL = ShearProperties.SHEAR_NATURAL
    '''Срез природное'''
    SHEAR_SATURATED = ShearProperties.SHEAR_SATURATED
    '''Срез водонасыщенное'''
    SHEAR_DD = ShearProperties.SHEAR_DD
    '''Срез плашка по плашке'''
    SHEAR_DD_NATURAL = ShearProperties.SHEAR_DD_NATURAL
    '''Срез плашка по плашке природный'''
    SHEAR_DD_SATURATED = ShearProperties.SHEAR_DD_SATURATED
    '''Срез плашка по плашке водонасыщенный'''
    SHEAR_NN = ShearProperties.SHEAR_NN
    '''Срез НН'''
    SHEAR_DILATANCY = ShearProperties.SHEAR_DILATANCY
    '''Срез дилатансия'''
    def __init__(self):
        self._shear_type = "Срез"

        self.combo_params_loaded = None
        '''Параметры испыатания, с которомы Успешно была загружена модель'''

        data_test_parameters = {

            "equipment": {
                "label": "Оборудование",
                "vars": [
                    "Не выбрано",
                    "АСИС ГТ.2.0.5",
                    "GIESA UP-25a",
                    "ASIS ГТ 2.2.6"]
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
                "label": "Состояние образца",
                "vars": [
                    "Не выбрано",
                    "Природное",
                    "Водонасыщенное"]
            },
            "phi_mode": {
                "label": "Тип определения PHI",
                "vars": [
                    "Автоматически",
                    "PHI по ведомости",
                    "PHI с рандомом"
                ]
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
        SessionWriter.set_sheet_load_datetime()
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
                if self.open_line.get_data()['test_mode'] in ['Срез природное', 'Срез водонасыщенное']:
                    if self.open_line.get_data()['optional'] == 'Не выбрано':
                        self._shear_type = "Срез"
                    else:
                        self._shear_type = f"Срез {self.open_line.get_data()['optional']}"
                elif self.open_line.get_data()['test_mode'] in ['Срез плашка по плашке']:
                    if self.open_line.get_data()['optional'] == 'Не выбрано':
                        self._shear_type = self.open_line.get_data()['test_mode']
                    else:
                        self._shear_type = f"{self.open_line.get_data()['test_mode']} {self.open_line.get_data()['optional'].lower()}"
                else:
                    self._shear_type = self.open_line.get_data()['test_mode']

                _path = f"{''.join([i for i in os.path.split(self.path)[:-1]])}/{self._shear_type}"

                if_exist_check = os.path.exists(_path) and len(list(filter(lambda val: '.pickle' in val, os.listdir(_path)))) > 0
                if if_exist_check:
                    ret = QMessageBox.question(self, 'Предупреждение',
                                               f"Файл модели уже существует в папке {self.path}/{self._shear_type}. "
                                               f"Вы уверены что он соответствует выбранным параметрам опыта и файлу задания?",
                                               QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                    if ret != QMessageBox.Yes:
                        if self.combo_params_loaded:
                            self.open_line.set_data(self.combo_params_loaded)
                        return

                if combo_params['equipment'] == 'ASIS ГТ 2.2.6':
                    h = 140  # mm
                    d = 150  # mm
                    combo_params['equipment_sample_h_d'] = (h, d)
                else:
                    h = 35.0  # mm
                    d = 71.4  # mm
                    combo_params['equipment_sample_h_d'] = (h, d)

                self.load_statment(
                    statment_name=self._shear_type + ".pickle",
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
                    statment.general_parameters.test_mode = self._shear_type
                    self.statment_directory.emit(self.path)
                    statment.general_parameters.test_mode = combo_params["test_mode"]
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
                    if not ShearStatment.is_dilatancy_type(self._shear_type):
                        self.load_models(models_name=ShearStatment.models_name(ShearStatment.shear_type(self._shear_type)).split('.')[0],
                                         models=Shear_models, models_type=ModelShearSoilTest)
                    elif ShearStatment.is_dilatancy_type(self._shear_type):
                        self.load_models(models_name=ShearStatment.models_name(ShearStatment.shear_type(self._shear_type)).split('.')[0],
                                         models=Shear_Dilatancy_models, models_type=ModelShearDilatancySoilTest)

                    self.combo_params_loaded = self.open_line.get_data()

    def button_open_click(self):
        combo_params = self.open_line.get_data()
        test = True
        for key in self.test_parameters:
            if key in ["optional", "phi_mode"]:
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
        if shear_type == ShearStatment.SHEAR:
            return "Shear_models.pickle"
        elif shear_type == ShearStatment.SHEAR_NATURAL:
            return "Shear_natural_models.pickle"
        elif shear_type == ShearStatment.SHEAR_SATURATED:
            return "Shear_saturated_models.pickle"
        elif shear_type == ShearStatment.SHEAR_NN:
            return "Shear_nn_models.pickle"
        elif shear_type == ShearStatment.SHEAR_DD:
            return "Shear_dd_models.pickle"
        elif shear_type == ShearStatment.SHEAR_DD_NATURAL:
            return "Shear_dd_models_natural.pickle"
        elif shear_type == ShearStatment.SHEAR_DD_SATURATED:
            return "Shear_dd_models_saturated.pickle"
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
                    "K0: По ГОСТ 12248.3-2020",
                    "K0: По ГОСТ-56353-2022",
                    "K0: По ГОСТ-56353-2015",
                    "K0: Формула Джекки",
                    "K0: K0 = 1",
                    "K0: Формула Джекки c учетом переупл.",
                    "K0: С ведомости (GZ)",
                    "K0: С ведомости (FW)"
                ]
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
        SessionWriter.set_sheet_load_datetime()
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

class RayleighDampingStatment(InitialStatment):
    """Класс обработки файла задания для трехосника"""
    def __init__(self):
        data_test_parameters = {
        }

        fill_keys = {
            "laboratory_number": "Лаб. ном."
        }

        super().__init__(data_test_parameters, fill_keys)

    @log_this(app_logger, "debug")
    def file_open(self):
        SessionWriter.set_sheet_load_datetime()
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()
            combo_params["K0_mode"] = "K0: K0 = 1"
            combo_params["test_mode"] = "Демпфирование по Релею"
            columns_marker = list(zip(*c_fi_E_PropertyPosition[combo_params["test_mode"]]))
            marker, error = read_general_prameters(self.path)

            try:
                assert not marker, "Проверьте " + error
            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            else:
                self.load_statment(
                    statment_name=combo_params["test_mode"] + ".pickle",
                    properties_type=RayleighDampingProperties,
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

                    self.load_models(models_name="RayleighDamping_models.pickle",
                                     models=RayleighDamping_models, models_type=ModelRayleighDampingSoilTest)

                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

class K0Statment(InitialStatment):
    """Класс обработки файла задания для трехосника"""

    test_modes: List = []

    def __init__(self):
        data_test_parameters = {
            "test_mode": {
                "label": "Режим испытания",
                "vars": [
                    "Трехосное сжатие K0",
                    "Трехосное сжатие K0 с разгрузкой"
                    ]
            },
            "K0_mode": {
                "label": "Модель расчета",
                "vars": [
                    "Мора-Кулона",
                    "Hardening Soil"
                ]
            }
        }

        K0Statment.test_modes = data_test_parameters['test_mode']['vars']

        fill_keys = {
            'laboratory_number': 'Лаб. ном.',
            'depth': 'Глубина, м',
            'OCR': 'OCR',
            'K0nc': 'K0nc',
            'sigma_1_step': 'Шаг нагружения, МПа',
            'sigma_1_max': 'Максимальное давление, МПа'}

        super().__init__(data_test_parameters, fill_keys)

    @log_this(app_logger, "debug")
    def file_open(self):
        SessionWriter.set_sheet_load_datetime()
        """Открытие и проверка заполненности всего файла веддомости"""
        if self.path and (self.path.endswith("xls") or self.path.endswith("xlsx")):
            combo_params = self.open_line.get_data()
            combo_params['K0_mode'] = K0Statment.is_hs_model(self.open_line.get_data()["K0_mode"])

            columns_marker = [("FV", 177)]

            marker, customer = read_general_prameters(self.path)

            try:
                # assert column_fullness_test(self.path, columns=list(zip(*c_fi_E_PropertyPosition["Резонансная колонка"])),
                #                             initial_columns=columns_marker), \
                #     "Заполните параметры прочности и деформируемости (BD, BC, BE)"

                assert not marker, "Проверьте " + customer

            except AssertionError as error:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

            else:
                self.load_statment(statment_name=self.open_line.get_data()["test_mode"] + ".pickle",
                                   properties_type=K0Properties, general_params=combo_params)

                keys = list(statment.tests.keys())
                for test in keys:
                    if statment.general_parameters.test_mode == K0Statment.test_modes[0]:
                        if not statment[test].mechanical_properties.K0nc:
                            del statment.tests[test]
                    elif statment.general_parameters.test_mode == K0Statment.test_modes[1]:
                        if not statment[test].mechanical_properties.K0nc\
                                or not statment[test].mechanical_properties.Nuur:
                            del statment.tests[test]

                if len(statment) < 1:
                    QMessageBox.warning(self, "Предупреждение", "Нет образцов с заданными параметрами опыта "
                                        + str(columns_marker), QMessageBox.Ok)
                else:
                    self.table_physical_properties.set_data()
                    self.statment_directory.emit(self.path)
                    self.open_line.text_file_path.setText(self.path)

                    if statment.general_parameters.test_mode == K0Statment.test_modes[0]:
                        self.load_models(models_name="k0_models.pickle", models=K0_models, models_type=ModelK0SoilTest)
                    if statment.general_parameters.test_mode == K0Statment.test_modes[1]:
                        self.load_models(models_name="k0ur_models.pickle", models=K0_models, models_type=ModelK0SoilTest)

    @staticmethod
    def is_hs_model(_mode):
        if _mode == 'Hardening Soil':
            return True
        return False


class DeviationsCustomBox(QGroupBox):
    def __init__(self):
        super().__init__()
        self.add_UI()
        self._checked = None

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.setTitle('Выбор девиаций')
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(750)

        self.radiobutton_state_standard = QRadioButton("По умолчанию")
        self.radiobutton_state_standard.setChecked(True)
        self.radiobutton_state_standard.value = "state_standard"
        self.radiobutton_state_standard.toggled.connect(self._onClicked)
        self.layout.addWidget(self.radiobutton_state_standard)

        self.radiobutton_custom = QRadioButton("Ручное:")

        self.line_amp1 = QLineEdit("0.04")
        self.line_amp1.setDisabled(True)
        self.lable_1 = QLabel("Амп. дев. (низк. час.)")
        self.line_amp2 = QLineEdit("0.02")
        self.line_amp2.setDisabled(True)
        self.lable_2 = QLabel("Амп. дев. (сред. час.)")
        self.line_amp3 = QLineEdit("0.01")
        self.line_amp3.setDisabled(True)
        self.lable_3 = QLabel("Амп. дев. (выс. час.)")


        self.radiobutton_custom.value = "custom"
        self.radiobutton_custom.toggled.connect(self._onClicked)

        self.acceptBtn = QPushButton("Применить")

        self.layout.addWidget(self.radiobutton_state_standard)
        self.layout.addWidget(self.radiobutton_custom)
        self.layout.addWidget(self.lable_1)
        self.layout.addWidget(self.line_amp1)
        self.layout.addWidget(self.lable_2)
        self.layout.addWidget(self.line_amp2)
        self.layout.addWidget(self.lable_3)
        self.layout.addWidget(self.line_amp3)

        self.layout.addWidget(self.acceptBtn)

    def _onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self._checked = radioButton.value

            if radioButton.value == "custom":
                self.line_amp1.setDisabled(False)
                self.line_amp2.setDisabled(False)
                self.line_amp3.setDisabled(False)

            else:
                self.line_amp1.setDisabled(True)
                self.line_amp2.setDisabled(True)
                self.line_amp3.setDisabled(True)

    # def set_data(self):
    #     data = statment[statment.current_test].mechanical_properties.pressure_array
    #     def str_array(array):
    #         if array is None:
    #             return "-"
    #         else:
    #             s = ""
    #             for i in array:
    #                 s += f"{str(i)}; "
    #             return s
    #     for key in data:
    #         if key != "current":
    #             line = getattr(self, f"line_{key}")
    #             radiobutton = getattr(self, f"radiobutton_{key}")
    #             line.setText(str_array(data[key]))
    #             if data[key] is None:
    #                 radiobutton.setDisabled(True)
    #             else:
    #                 radiobutton.setDisabled(False)
    #             if data[key] == data["current"]:
    #                 radiobutton.setChecked(True)

    def get_checked(self):
        return self._checked


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RayleighDampingStatment()
    window.show()
    #print(Dialog.save())
    app.setStyle('Fusion')
    sys.exit(app.exec_())
