from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QDialog, \
    QDialogButtonBox, QGroupBox, QPushButton, QTableWidget, QComboBox, QHeaderView, QTableWidgetItem, QTabWidget, \
    QTextEdit, QProgressDialog
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from excel_statment.initial_tables import TableCastomer
import numpy as np
import sys
import os
import time
#import pyautogui
import shutil
from general.reports import report_triaxial_cyclic, report_cyclic_damping, report_triaxial_cyclic_shear
import threading
from authentication.request_qr import request_qr


from cyclic_loading.cyclic_loading_widgets_UI import CyclicLoadingUI, CyclicLoadingOpenTestUI, CyclicLoadingUISoilTest, CyclicDampingUI, CsrWidget, SeismicStrangthUI
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoading, ModelTriaxialCyclicLoadingSoilTest
from cyclic_loading.liquefaction_potential_model import GeneralLiquefactionModel
from excel_statment.initial_tables import LinePhysicalProperties
from general.save_widget import Save_Dir
from general.report_general_statment import save_report
from excel_statment.initial_statment_widgets import CyclicStatment
from excel_statment.functions import write_to_excel, set_cell_data
from excel_statment.initial_tables import TableVertical
from loggers.logger import app_logger, log_this, handler
from singletons import Cyclic_models, statment
from tests_log.equipment import dynamic

from tests_log.widget import TestsLogWidget
from tests_log.test_classes import TestsLogCyclic
from version_control.configs import actual_version
from general.general_statement import StatementGenerator
from general.tab_view import AppMixin, TabMixin
__version__ = actual_version

from authentication.request_qr import request_qr
from authentication.control import control
from metrics.session_writer import SessionWriter
from general.movie_label import Loader

class CyclicProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelTriaxialCyclicLoading()
        self._create_Ui()
        self.open_widget.button_open.clicked.connect(self._open_log)
        self.open_widget.button_plot.clicked.connect(self._plot)
        self.open_widget.button_screen.clicked.connect(self._screenshot)

    def _screenshot(self):
        """Сохранение скриншота"""
        s = QFileDialog.getSaveFileName(self, 'Open file')[0]#QFileDialog.getExistingDirectory(self, "Select Directory")
        if s:
            try:
                time.sleep(0.3)
                #pyautogui.screenshot(s+".png", region=(0, 0, 1920, 1080))
                QMessageBox.about(self, "Сообщение", "Скриншот сохранен")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)
            except:
                QMessageBox.critical(self, "Ошибка", "", QMessageBox.Ok)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.open_widget = CyclicLoadingOpenTestUI()
        self.open_widget.button_plot.clicked.connect(self._plot)
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)
        self.test_processing_widget = CyclicLoadingUI()
        self.layout.addWidget(self.test_processing_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _open_log(self):
        """Открытие файла опыта"""
        path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if path:
            self.open_widget.set_file_path("")
            test_data = None
            try:
                test_data = ModelTriaxialCyclicLoading.open_wille_log(path)
            except (ValueError, IndexError):
                try:
                    test_data = ModelTriaxialCyclicLoading.open_geotek_log(path)
                except:
                    pass
        if test_data:
            sigma_3 = round(np.mean(test_data["cell_pressure"]))
            sigma_1 = str(round(((max(test_data["deviator"][int(0.5 * len(test_data["deviator"])):]) + min(
                test_data["deviator"][int(0.5 * len(test_data["deviator"])):])) / 2) + sigma_3))
            t = str(round((max(test_data["deviator"][int(0.5 * len(test_data["deviator"])):]) - min(
                test_data["deviator"][int(0.5 * len(test_data["deviator"])):])) / 4))
            sigma_3 = str(sigma_3)

            self.open_widget.set_params({"sigma_1": sigma_1,
                                         "sigma_3": sigma_3,
                                         "t": t,
                                         "frequency": str(test_data["frequency"])
                                         })

            self._model.set_test_data(test_data)

            self.open_widget.set_file_path(path)

            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        def check_params(params):
            for i in params:
                if params[i]:
                    continue
                else:
                    return False
            return True

        params = self.open_widget.get_params()

        if check_params(params):
            self._model.set_frequency(params["frequency"])
            plots = self._model.get_plot_data()
            res = self._model.get_test_results()
            self.test_processing_widget.plot(plots, res)
        else:
            QMessageBox.critical(self, "Ошибка", "Проверьте заполнение параметров", QMessageBox.Ok)

class CyclicSoilTestWidget(TabMixin, QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    signal = pyqtSignal()
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()
        self.test_widget.sliders_widget.strain_signal[object].connect(self._sliders_strain)
        self.test_widget.sliders_widget.PPR_signal[object].connect(self._sliders_PPR)
        self.test_widget.sliders_widget.cycles_count_signal[object].connect(self._sliders_cycles_count)
        self.test_widget.sliders_widget.csr_button.clicked.connect(self._csr)
#        self.screen_button.clicked.connect(self._screenshot)

    def _create_Ui(self):
        self.layout = QHBoxLayout(self)
        self.layout_1 = QVBoxLayout()

        self.test_widget = CyclicLoadingUISoilTest()
        fill_keys = {
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "K0": "K0, д.е.",
            "t": "Касательное напряжение τ, кПа",
            "intensity": "Бальность, балл",
            "frequency": "Частота, Гц",
            "damping_ratio": "Коэффициент демпфирования, %"
        }
        self.identification = TableVertical(fill_keys)
        self.identification.setFixedWidth(380)
        self.identification.setFixedHeight(200)
        self.damping = CyclicDampingUI()
        self.seismic_strangth = SeismicStrangthUI()
        self.seismic_strangth.setFixedHeight(280)
        self.layout_2 = QVBoxLayout()
        self.layout_1.addWidget(self.test_widget)
        self.layout_2.addWidget(self.identification)
        self.layout_2.addWidget(self.seismic_strangth)
        self.layout_2.addWidget(self.damping)
        self.layout.addLayout(self.layout_1)
        self.layout.addLayout(self.layout_2)
        self.layout.setContentsMargins(5, 5, 5, 5)

    @log_this(app_logger, "debug")
    def _sliders_strain(self, param):
        try:
            Cyclic_models[statment.current_test].set_strain_params(param)
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _sliders_PPR(self, param):
        try:
            Cyclic_models[statment.current_test].set_PPR_params(param)
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _sliders_cycles_count(self, param):
        try:
            Cyclic_models[statment.current_test].set_cycles_count(param["cycles_count"])
            strain_params, ppr_params, cycles_count_params = Cyclic_models[statment.current_test].get_draw_params()
            self.test_widget.sliders_widget.set_sliders_params(strain_params, ppr_params, cycles_count_params, True)
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    def _csr(self):
        try:
            model = GeneralLiquefactionModel()
            self.csr_widget = CsrWidget(model)
            self.csr_widget.show()
        except Exception as err:
            print(err)

    def set_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        strain_params, ppr_params, cycles_count_params = Cyclic_models[statment.current_test].get_draw_params()
        self.test_widget.sliders_widget.set_sliders_params(strain_params, ppr_params, cycles_count_params)
        self._plot()

    def open_log(self, path):
        """Открытие файла опыта"""
        test_data = ModelTriaxialCyclicLoading.open_wille_log(path)
        self._model.set_test_data(test_data)
        self._model.set_processing_parameters(test_data)
        self._plot()

    def refresh(self):
        Cyclic_models[statment.current_test].set_test_params()
        strain_params, ppr_params, cycles_count_params = Cyclic_models[statment.current_test].get_draw_params()
        self.test_widget.sliders_widget.set_sliders_params(strain_params, ppr_params, cycles_count_params, True)
        self._plot()
        self.signal.emit()

    def _plot(self):
        """Построение графиков опыта"""
        plots = Cyclic_models[statment.current_test].get_plot_data()
        res = Cyclic_models[statment.current_test].get_test_results()
        self.test_widget.plot(plots, res)
        self.damping.plot(plots, res)

        parameters = Cyclic_models[statment.current_test].get_test_parameters()
        u = np.round((Cyclic_models[statment.current_test].get_test_results()['max_PPR'] * parameters['sigma_3']) / 1000, 2)
        self.seismic_strangth.plot(
            parameters['sigma_3']/1000,
            parameters['sigma_1']/1000,
            u,
            statment[statment.current_test].mechanical_properties.c,
            statment[statment.current_test].mechanical_properties.fi
        )


    def _screenshot(self):
        """Сохранение скриншота"""
        s = QFileDialog.getSaveFileName(self, 'Open file')[0]#QFileDialog.getExistingDirectory(self, "Select Directory")
        if s:
            try:
                time.sleep(0.3)
                #pyautogui.screenshot(s+".png", region=(0, 0, 1920, 600))
                QMessageBox.about(self, "Сообщение", "Скриншот сохранен")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)
            except:
                QMessageBox.critical(self, "Ошибка", "", QMessageBox.Ok)

class CyclicPredictLiquefaction(QDialog):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self._table_is_full = False
        self.setWindowTitle("Прогнозирование разжижаемости")
        self.create_IU()

        self.resize(1400, 800)

        self.save_button.clicked.connect(self._save_pdf)
        self.combo_box.activated.connect(lambda s: self._sort_combo_changed(statment))

        self._fill_table()

    def create_IU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.table_castomer = TableCastomer()
        self.table_castomer.set_data()
        self.layout.addWidget(self.table_castomer)

        self.l = QHBoxLayout()
        self.button_box = QGroupBox("Инструменты")
        self.button_box_layout = QHBoxLayout()
        self.button_box.setLayout(self.button_box_layout)
        self.save_button = QPushButton("Сохранить данные PDF")
        self.save_button.setFixedHeight(30)
        self.combo_box = QComboBox()
        self.combo_box.setFixedHeight(30)
        self.combo_box.addItems(["Сортировка", "CSR", "sigma_3", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)
        self.l.addWidget(self.button_box)
        self.layout.addLayout(self.l)

        self.table = QTableWidget()
        self.table.itemChanged.connect(self._set_color_on_fail)
        self._clear_table()
        self.layout.addWidget(self.table)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        self._table_is_full = False

        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setColumnCount(13)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il", "e", "𝜎3, кПа", "𝜎1, кПа", "t, кПа", "CSR", "Число циклов",
             "Nfail", "Ms", "Коэф. демпф."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        self.table.horizontalHeader().setMinimumSectionSize(100)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(12, QHeaderView.Fixed)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(statment))

        for string_number, lab_number in enumerate(statment):
            for i, val in enumerate(
                    [
                        lab_number,
                        str(statment[lab_number].physical_properties.depth),
                        statment[lab_number].physical_properties.soil_name,
                        str(statment[lab_number].physical_properties.Il) if statment[lab_number].physical_properties.Il else "-",
                        str(statment[lab_number].physical_properties.e) if statment[lab_number].physical_properties.e else "-",
                        str(statment[lab_number].mechanical_properties.sigma_3),
                        str(statment[lab_number].mechanical_properties.sigma_1),
                        str(statment[lab_number].mechanical_properties.t),
                        str(statment[lab_number].mechanical_properties.CSR),
                        str(statment[lab_number].mechanical_properties.cycles_count),
                        str(statment[lab_number].mechanical_properties.n_fail) if statment[lab_number].mechanical_properties.n_fail else "-",
                        str(statment[lab_number].mechanical_properties.Ms),
                        str(statment[lab_number].mechanical_properties.damping_ratio)
                    ]):

                self.table.setItem(string_number, i, QTableWidgetItem(val))

        self._table_is_full = True

        self._set_color_on_fail()

    def _update_data(self):
        """Метод обновляет данные разжижения из таблицы в структуру жанных"""
        def read_n_fail(x):
            try:
                y = int(x)
                return y
            except ValueError:
                return None

        for string_number, lab_number in enumerate(statment):
            statment[lab_number].mechanical_properties.n_fail = read_n_fail(self.table.item(string_number, 10).text())
            statment[lab_number].mechanical_properties.Ms = float(self.table.item(string_number, 11).text())

            if statment[lab_number].mechanical_properties.n_fail:
                statment[lab_number].mechanical_properties.Mcsr = None
                if (statment[lab_number].mechanical_properties.sigma_1 - statment[lab_number].mechanical_properties.sigma_3) <= 1.5 * statment[lab_number].mechanical_properties.t:
                    statment[lab_number].mechanical_properties.Ms = np.round(np.random.uniform(100, 500), 2)
                else:
                    statment[lab_number].mechanical_properties.Ms = np.round(np.random.uniform(0.7, 0.9), 2)
            else:
                statment[lab_number].mechanical_properties.Mcsr = np.random.uniform(2, 3)

    def _set_color_on_fail(self):
        if self._table_is_full:
            self._update_data()
            for string_number, lab_number in enumerate(statment):
                if statment[lab_number].mechanical_properties.n_fail:
                    self._set_row_color(string_number, color=(255, 99, 71))
                elif statment[lab_number].mechanical_properties.Ms <= 1:
                    self._set_row_color(string_number, color=(255, 215, 0))
                else:
                    self._set_row_color(string_number, color=(255, 255, 255))

    def _set_row_color(self, row, color=(255, 255, 255)):#color=(62, 180, 137)):
        """Раскрашиваем строку"""
        for i in range(self.table.columnCount()):
            if color == (255, 255, 255):
                item_color = str(self.table.item(row, i).background().color().name())
                if item_color != "#ffffff" and item_color != "#000000":
                    self.table.item(row, i).setBackground(QtGui.QColor(*color))
            else:
                self.table.item(row, i).setBackground(QtGui.QColor(*color))

    def _sort_combo_changed(self, statment):
        """Изменение способа сортировки combo_box"""
        if self._table_is_full:
            if self.combo_box.currentText() == "Сортировка":
                statment.sort("origin")
                self._clear_table()
            else:
                statment.sort(self.combo_box.currentText())
                self._clear_table()

            self._fill_table()

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирования разжижения"
            titles, data, scales = CyclicPredictLiquefaction.transform_data_for_statment(statment)
            try:
                save_report(titles, data, scales, statment.general_data.end_date, ['Заказчик:', 'Объект:'],
                            [statment.general_data.customer, statment.general_data.object_name], statement_title,
                            save_dir, "---", "Прогноз разжижения.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    def on_accept(self):
        ret = QMessageBox.question(self, 'Предупреждение',
                                   f"Вы уверены что хотите сохранить изменения?",
                                   QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if ret == QMessageBox.Yes:
            self.accept()

    @staticmethod
    def transform_data_for_statment(data):
        """Трансформация данных для передачи в ведомость"""
        data_structure = []

        for string_number, lab_number in enumerate(data):
                data_structure.append([
                    lab_number,
                    str(statment[lab_number].physical_properties.depth),
                    statment[lab_number].physical_properties.soil_name,
                    str(statment[lab_number].physical_properties.Il) if statment[
                        lab_number].physical_properties.Il else "-",
                    str(statment[lab_number].physical_properties.e) if statment[
                        lab_number].physical_properties.e else "-",
                    str(statment[lab_number].mechanical_properties.CSR),
                    str(statment[lab_number].mechanical_properties.cycles_count),
                    str(statment[lab_number].mechanical_properties.n_fail) if statment[
                        lab_number].mechanical_properties.n_fail else "-",
                    str(statment[lab_number].mechanical_properties.Ms),
                    str(statment[lab_number].mechanical_properties.damping_ratio)
                ])

        titles = ["Лаб. номер", "Глубина, м", "Наименование грунта", "Il", "e", "CSR, д.е.", "Общее число циклов",
                   "Цикл разрушения", "Ms", "Коэф. демпф."]

        scale = [60, 60, "*", 60, 60, 60, 60, 60, 60, 60]

        return (titles, data_structure, scale)

class CyclicProcessingApp(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = CyclicStatment()
        self.tab_2 = CyclicProcessingWidget()
        self.tab_3 = Save_Dir()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.tab_widget.addTab(self.tab_3, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self._set_save_directory)
        self.tab_3.save_button.clicked.connect(self.save_report)

    def _set_save_directory(self, signal):
        read_parameters = self.tab_1.open_line.get_data()
        self.tab_2.save_widget.set_directory(signal, read_parameters["test_type"])

    def save_report(self):

        def check_none(s):
            if s:
                return str(s)
            else:
                return "-"

        test_parameter = self.tab_1.table.open_line.get_data()

        try:
            assert self.tab_1.table.get_lab_number(), "Не выбран образец в ведомости"
            len(self.tab_2.wigdet._model._test_data.cycles)
            # assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            file_path_name = self.tab_1.table.get_lab_number().replace("/", "-").replace("*", "")

            save = self.tab_3.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if test_parameter["test_type"] == "Сейсморазжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-С" + ".pdf"
            elif test_parameter["test_type"] == "Штормовое разжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-ШТ" + ".pdf"

            """if test_parameter['equipment'] == "Прибор: Геотек":
                test_time = geoteck_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["sigma3"], self.Data["frequency"], self.Data["Points"], self.file.Data_phiz[self.file.Lab]["Ip"])

            elif test_parameter['equipment'] == "Прибор: Вилли":
                test_time = willie_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["frequency"], self.Data["N"], self.Data["Points"],
                                 self.Setpoint, self.Arrays["cell_press"], self.file.Data_phiz[self.file.Lab]["Ip"])"""

            if test_parameter['equipment'] == 'Прибор: Вилли':
                equipment = "Wille Geotechnik 13-HG/020:001"
                h = 76
                d = 38
            else:
                equipment = "Динамический стабилометр Геотек"
                h = 100
                d = 50

            params = self.tab_2.wigdet.open_widget.get_params()

            test_parameter = {'sigma3': params["sigma_3"], 'sigma1': params["sigma_1"], 'tau': params["t"], 'K0': 1,
                              'frequency': params["frequency"],
                              "Hw": params.get("Hw", None),
                              "rw": params.get("rw", None),
                              'I': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]["balnost"],
                              'M': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]["magnituda"],
                              'MSF': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]['MSF'],
                              'rd': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]['rd'],
                              'type': test_parameter["test_type"],
                              'Rezhim': 'Анизотропная реконсолидация, девиаторное циклическое нагружение',
                              'Oborudovanie': equipment, 'h': h, 'd': d}

            test_result = self.tab_2.wigdet._model.get_test_results()

            results = {'PPRmax': test_result['max_PPR'], 'EPSmax': test_result['max_strain'],
                       'res': test_result['conclusion'], 'nc': check_none(test_result['fail_cycle'])}

            report_triaxial_cyclic(file_name, self.tab_1.table.get_customer_data(),
                                   self.tab_1.table.get_physical_data(),
                                   self.tab_1.table.get_lab_number(),
                                   os.getcwd() + "/project_data/", test_parameter, results,
                                   self.tab_2.wigdet.test_processing_widget.save_canvas(), __version__)

            try:
                if test_parameter['Oborudovanie'] == "Wille Geotechnik 13-HG/020:001":
                    self.tab_2.generate_log_file(save)
            except AttributeError:
                pass

            shutil.copy(file_name, self.tab_3.report_directory + "/" + file_name[len(file_name) -
                                                                                 file_name[::-1].index("/"):])
            QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
            self.tab_1.table.table_physical_properties.set_row_color(
                self.tab_1.table.table_physical_properties.get_row_by_lab_naumber(self.tab_1.table.get_lab_number()))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", "Не загружен файл опыта", QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

class CyclicSoilTestApp(AppMixin, QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])
        # Создаем вкладки

        self.save_massage = True
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = CyclicStatment()

        self.tab_2 = CyclicSoilTestWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)

        self.tab_3 = Save_Dir(
            {"standart": "Стандартный отчет",
             "t_rel": "Отчет о снижении прочности при динамическом воздействии"
             },
            result_table_params={
            "Макс. PPR": lambda lab: Cyclic_models[lab].get_test_results()['max_PPR'],
            "Макс. деформ.": lambda lab: Cyclic_models[lab].get_test_results()['max_strain'],
            "Цикл разрушения": lambda lab: Cyclic_models[lab].get_test_results()['fail_cycle'],
            "t_max_dynamic/t_max_static": lambda lab: np.round(Cyclic_models[lab].get_test_results()['t_rel_dynamic'] / Cyclic_models[lab].get_test_results()['t_rel_static'], 2),
            "Коэффициент демпфирования": lambda lab: Cyclic_models[lab].get_test_results()['damping_ratio'],
            "Заключение": lambda lab: Cyclic_models[lab].get_test_results()['conclusion'],
        },  qr={"state": True})

        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.tab_widget.addTab(self.tab_3, "Отчеты")
        self.layout.addWidget(self.tab_widget)

        self.log_widget = QTextEdit()
        self.log_widget.setFixedHeight(180)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.physical_line = LinePhysicalProperties()
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_3.update(x))
        self.tab_1.signal[bool].connect(self.tab_2.set_params)
        self.tab_1.signal[bool].connect(self.tab_2.identification.set_data)
        self.tab_2.signal.connect(self.tab_3.result_table.update)
        #self.tab_1.signal[bool].connect(self.tab_3.result_table.update)

        self.tab_1.signal[bool].connect(lambda x: self.physical_line.set_data())

        self.tab_3.save_button.clicked.connect(self.save_report)
        self.tab_3.save_pickle.clicked.connect(self.save_pickle)
        #self.tab_2.save_button.clicked.connect(self.save_report)
        self.tab_3.save_all_button.clicked.connect(self.save_all_reports)

        self.tab_2.signal.connect(self.replot_csr)

        self.tab_3.jornal_button.clicked.connect(self.jornal)

        #self.tab_3.jornal_button.clicked.connect(self.jornal)
#        self.tab_3.reprocessing_button.clicked.connect(self.reprocessing)

        self.button_predict_liquefaction = QPushButton("Прогнозирование разжижаемости")
        self.button_predict_liquefaction.setFixedHeight(50)
        self.button_predict_liquefaction.clicked.connect(self._predict)
        self.tab_1.layuot_for_button.addWidget(self.button_predict_liquefaction)

        self.tab_3.general_statment_button.clicked.connect(self.general_statment)

        self.tab_2.layout_1.insertWidget(0, self.physical_line)
        self.physical_line.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line.save_button.clicked.connect(self.save_report_and_continue)
        self.tab_3.roundFI_btn.hide()

        self.loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                             message_port=7787, parent=self)

    def keyPressEvent(self, event):
        if statment.current_test:
            list = [x for x in statment]
            index = list.index(statment.current_test)
            if str(event.key()) == "90":
                if index >= 1:
                    statment.current_test = list[index-1]
                    self.tab_2.set_params(True)
                    self.tab_2.identification.set_data()
            elif str(event.key()) == "88":
                if index < len(list) -1:
                    statment.current_test = list[index + 1]
                    self.tab_2.set_params(True)
                    self.tab_2.identification.set_data()

    def replot_csr(self, *kwargs):
        try:
            self.tab_2.csr_widget.replot()
        except Exception as err:
            print(err)

    def save_pickle(self):
        try:
            statment.save([Cyclic_models], [f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"])
            Cyclic_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"))
            QMessageBox.about(self, "Сообщение", "Pickle успешно сохранен")
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

    def _predict(self):
        if len(statment):
            dialog = CyclicPredictLiquefaction()
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                Cyclic_models.generateTests()
                Cyclic_models.dump(os.path.join(statment.save_dir.save_directory,
                                                f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"))
                app_logger.info("Новые параметры ведомости и модели сохранены")

    def save_report(self, save_all_mode = False):

        def check_none(s):
            if s:
                return str(s)
            else:
                return "-"

        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if statment.general_parameters.test_mode == "Сейсморазжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-С" + ".pdf"
            elif statment.general_parameters.test_mode == "Штормовое разжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-ШТ" + ".pdf"
            elif statment.general_parameters.test_mode == "Демпфирование":
                file_name = save + "/" + "Отчет " + file_path_name + "-Д" + ".pdf"
            elif statment.general_parameters.test_mode == "По заданным параметрам":
                file_name = save + "/" + "Отчет " + file_path_name + "-Д" + ".pdf"
            elif statment.general_parameters.test_mode == "Динамическая прочность на сдвиг":
                file_name = save + "/" + "Отчет " + file_path_name + "-С" + ".pdf"

            from_model = Cyclic_models[statment.current_test].get_test_parameters()

            test_parameter = {'sigma3': from_model['sigma_3'],
                              'sigma1': from_model['sigma_1'],
                              'tau': int(from_model['t'] * 2),
                              'K0': statment[statment.current_test].mechanical_properties.K0,
                              'frequency': statment[statment.current_test].mechanical_properties.frequency,
                              "Hw": statment[statment.current_test].mechanical_properties.Hw,
                              "rw": statment[statment.current_test].mechanical_properties.rw,
                              'I': statment[statment.current_test].mechanical_properties.intensity,
                              'M': statment[statment.current_test].mechanical_properties.magnitude,
                              'MSF': statment[statment.current_test].mechanical_properties.MSF,
                              'rd': statment[statment.current_test].mechanical_properties.rd,
                              'type': statment.general_parameters.test_mode,
                              'Rezhim': 'Анизотропная реконсолидация, девиаторное циклическое нагружение',
                              'Oborudovanie': "Камера трехосного сжатия динамическая ГТ 2.3.20, Wille Geotechnik 13-HG/020:001",
                              'h': 100, 'd': 50}

            test_result = Cyclic_models[statment.current_test].get_test_results()

            results = {'PPRmax': test_result['max_PPR'],
                       'EPSmax': test_result['max_strain'],
                       'res': test_result['conclusion'],
                       'nc': check_none(test_result['fail_cycle']),
                       "damping_ratio": test_result["damping_ratio"],
                       "t_max_static": test_result["t_rel_static"],
                       "t_max_dynamic": test_result["t_rel_dynamic"]}

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            if test_result["fail_cycle"] is None:
                test_result["fail_cycle"] = "-"

            if statment.general_parameters.test_mode == "Сейсморазжижение" or statment.general_parameters.test_mode == "Штормовое разжижение" or statment.general_parameters.test_mode == "По заданным параметрам":
                if statment.general_parameters.test_mode == "Сейсморазжижение":
                    name = "cyclic"
                elif statment.general_parameters.test_mode == "Штормовое разжижение":
                    name = "storm"
                elif statment.general_parameters.test_mode == "По заданным параметрам":
                    name = "user_cyclic"

                data = {
                    "laboratory": "mdgt",
                    "password": "it_user",

                    "test_name": "Cyclic",
                    "object": str(statment.general_data.object_number),
                    "laboratory_number": str(statment.current_test),
                    "test_type": name,

                    "data": {
                        "Лаболаторный номер:": str(statment.current_test),
                        "Обжимающее давление 𝜎3, МПа:": str(np.round(statment[statment.current_test].mechanical_properties.sigma_3/1000, 3)),
                        "К0:": str(statment[statment.current_test].mechanical_properties.K0),
                        "Максимальное значение PPR, д.е.:": str(test_result["max_PPR"]),
                        "Максимальное значение деформации, д.е.:": str(test_result["max_strain"]),
                        "Результат испытания:": str(test_result["conclusion"]),
                    }
                }

                if self.tab_3.qr:
                    qr = request_qr()
                else:
                    qr = None

                if self.tab_3.report_type == 'standart':
                    canvas = self.tab_2.test_widget.save_canvas()
                elif self.tab_3.report_type == 't_rel':
                    canvas = [*self.tab_2.test_widget.save_canvas(), self.tab_2.seismic_strangth.save_canvas()]

                report_triaxial_cyclic(file_name, data_customer,
                                       statment[statment.current_test].physical_properties,
                                       statment.getLaboratoryNumber(),
                                       os.getcwd() + "/project_data/", test_parameter, results,
                                       canvas, "{:.2f}".format(__version__), qr_code=qr)
            elif statment.general_parameters.test_mode == "Демпфирование":
                data = {
                    "laboratory": "mdgt",
                    "password": "it_user",

                    "test_name": "Cyclic",
                    "object": str(statment.general_data.object_number),
                    "laboratory_number": str(statment.current_test),
                    "test_type": "damping",

                    "data": {
                        "Лаболаторный номер:": str(statment.current_test),
                        "Обжимающее давление 𝜎3, МПа:": str(
                            np.round(statment[statment.current_test].mechanical_properties.sigma_3 / 1000, 3)),
                        "Коэффициент демпфирования, %:": str(test_result["damping_ratio"]),
                    }
                }

                if self.tab_3.qr:
                    qr = request_qr()
                else:
                    qr = None

                report_cyclic_damping(file_name, data_customer,
                                       statment[statment.current_test].physical_properties,
                                       statment.getLaboratoryNumber(),
                                       os.getcwd() + "/project_data/", test_parameter, results,
                                       [self.tab_2.damping.save_canvas()], "{:.2f}".format(__version__), qr_code=qr)
            elif statment.general_parameters.test_mode == "Динамическая прочность на сдвиг":
                results["gamma_critical"] = test_result['gamma_critical']
                data = {
                    "laboratory": "mdgt",
                    "password": "it_user",

                    "test_name": "Cyclic",
                    "object": str(statment.general_data.object_number),
                    "laboratory_number": str(statment.current_test),
                    "test_type": "Dynamic_shear",

                    "data": {
                        "Лаболаторный номер:": str(statment.current_test),
                        "Обжимающее давление 𝜎3, МПа:": str(
                            np.round(statment[statment.current_test].mechanical_properties.sigma_3 / 1000, 3)),
                        "К0:": str(statment[statment.current_test].mechanical_properties.K0),
                        "Максимальное значение PPR, д.е.:": str(test_result["max_PPR"]),
                        "Максимальное значение деформации, д.е.:": str(test_result["max_strain"]),
                        "Динамическая прочностьт грунта на сдвиг, ед.": str(test_result["fail_cycle"]) if test_result["fail_cycle"] else "1500",
                    }
                }

                if self.tab_3.qr:
                    qr = request_qr()
                else:
                    qr = None

                report_triaxial_cyclic_shear(file_name, data_customer,
                                       statment[statment.current_test].physical_properties,
                                       statment.getLaboratoryNumber(),
                                       os.getcwd() + "/project_data/", test_parameter, results,
                                       self.tab_2.test_widget.save_canvas(), "{:.2f}".format(__version__), qr_code=qr)


            Cyclic_models[statment.current_test].generate_log_file(save)

            shutil.copy(file_name, statment.save_dir.report_directory + "/" + file_name[len(file_name) -
                                                                                 file_name[::-1].index("/"):])

            set_cell_data(self.tab_1.path, ("HY5", (5, 232)), "Сигма1, кПа", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HZ5", (5, 233)), "Сигма3, кПа", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IA5", (5, 234)), "Тау, кПа", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IB5", (5, 235)), "K0", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IC5", (5, 236)), "Частота, Гц", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("ID5", (5, 237)), "Цикл разрушения", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IU5", (5, 254)), "t_max_static", sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IV5", (5, 255)), "t_max_dynamic", sheet="Лист1")


            number = statment[statment.current_test].physical_properties.sample_number + 7

            set_cell_data(self.tab_1.path, ("HW" + str(number), (number, 230)), round(test_result['max_strain'], 3),
                          sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HX" + str(number), (number, 231)), round(test_result['max_PPR'], 3),
                          sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HY" + str(number), (number, 232)),
                          round(statment[statment.current_test].mechanical_properties.sigma_1, 3), sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HZ" + str(number), (number, 233)),
                          round(float(statment[statment.current_test].mechanical_properties.sigma_3), 3), sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IA" + str(number), (number, 234)),
                          round(statment[statment.current_test].mechanical_properties.t, 3), sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IB" + str(number), (number, 235)),
                          round(statment[statment.current_test].mechanical_properties.K0, 3), sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IC" + str(number), (number, 236)),
                          statment[statment.current_test].mechanical_properties.frequency, sheet="Лист1")
            set_cell_data(self.tab_1.path, ("ID" + str(number), (number, 237)), test_result["fail_cycle"],
                          sheet="Лист1")

            set_cell_data(self.tab_1.path, ("IE" + str(number), (number, 254)), results["t_max_static"],
                          sheet="Лист1")
            set_cell_data(self.tab_1.path, ("IF" + str(number), (number, 255)), results["t_max_dynamic"],
                          sheet="Лист1")

            if statment.general_parameters.test_mode == "Демпфирование":
                set_cell_data(self.tab_1.path, ("HM" + str(number), (number, 220)), test_result["damping_ratio"],
                              sheet="Лист1")


            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
                app_logger.info(
                    f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            #statment.dump(''.join(os.path.split(self.tab_3.directory)[:-1]),
                          #ame=statment.general_parameters.test_mode + ".pickle")

            control()
            return True, "Успешно"


        except AssertionError as error:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")
            return False, f'{str(error)}'

        #except TypeError as error:
            #QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", f"Закройте файл отчета {statment.current_test}", QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")
            return False, 'Не закрыт файл отчета'


        except Exception as error:

            if not save_all_mode:
                app_logger.exception(f"Не выгнан {statment.current_test}")

            return False, f'{str(error)}'

    def save_all_reports(self):

        if self.loader.is_running:
            QMessageBox.critical(self, "Ошибка", "Закройте окно сохранения")
            return

        try:
            statment.save([Cyclic_models], [f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"])
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        Cyclic_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"))

        try:
            statment.save_dir.clear_dirs()
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", "Ошибка очистки папки с отчетами. Не закрыт файл отчета.")
            return

        def save():

            count = len(statment)
            Loader.send_message(self.loader.port, f"Сохранено 0 из {count}")

            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self.tab_2.set_params(True)
                try:
                    is_ok, message = self.save_report(save_all_mode=True)
                    if not is_ok:
                        self.loader.close_OK(
                            f"Ошибка сохранения пробы {statment.current_test}\n{message}.\nОперация прервана.")
                        app_logger.info(f"Ошибка сохранения пробы {message}")
                        return
                except Exception as err:
                    self.loader.close_OK(f"Ошибка сохранения пробы {statment.current_test}\n{err}.\nОперация прервана.")
                    app_logger.info(f"Ошибка сохранения пробы {err}")
                    return

                Loader.send_message(self.loader.port, f"Сохранено {i + 1} из {count}")

            Loader.send_message(self.loader.port, f"Сохранено {count} из {count}")
            self.loader.close_OK(f"Объект выгнан")
            self.save_massage = True

        t = threading.Thread(target=save)
        self.loader.start()
        t.start()

        SessionWriter.write_session(len(statment))

    def jornal(self):
        self.dialog = TestsLogWidget(dynamic, TestsLogCyclic, self.tab_1.path)
        self.dialog.show()

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        key = None
        test_mode_file_name = None
        try:
            if statment.general_parameters.test_mode == "Сейсморазжижение":
                key = "Seismic liquefaction"
                test_mode_file_name = "сейсмо"
            elif statment.general_parameters.test_mode == "Штормовое разжижение":
                key = "Storm liquefaction"
                test_mode_file_name = "шторм"
            elif statment.general_parameters.test_mode == "Демпфирование":
                key = "damping"
                test_mode_file_name = 'демпфирование'
            elif statment.general_parameters.test_mode == "По заданным параметрам":
                key = "Seismic liquefaction"
                test_mode_file_name = 'по заданным параметрам'
        except:
            key = None

        _statment = StatementGenerator(self, path=s, statement_structure_key=key,
                                       test_mode_and_shipment=(test_mode_file_name,
                                                               statment.general_data.get_shipment_number()))
        _statment.show()

    def save_report_and_continue(self):
        try:
            statment.save([Cyclic_models], [f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"])
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        Cyclic_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"cyclic_models{statment.general_data.get_shipment_number()}.pickle"))

        try:
            self.save_report()
        except:
            pass
        keys = [key for key in statment]
        for i, val in enumerate(keys):
            if (val == statment.current_test) and (i < len(keys) - 1):
                statment.current_test = keys[i+1]
                self.physical_line.set_data()
                self.tab_2.set_params(True)
                self.tab_2.identification.set_data()
                break
            else:
                pass
        SessionWriter.write_test()




if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicSoilTestApp()

    ex.show()
    sys.exit(app.exec_())
