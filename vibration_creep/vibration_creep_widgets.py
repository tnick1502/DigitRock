from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QTabWidget, \
    QDialog, QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
import numpy as np
import sys


from vibration_creep.vibration_creep_widgets_UI import VibrationCreepUI
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest
from general.initial_tables import TableVertical
from static_loading.triaxial_static_test_widgets import TriaxialStaticWidgetSoilTest
from general.initial_tables import Table_Castomer
from general.excel_functions import create_json_file, read_json_file
from general.report_general_statment import save_report
from general.excel_data_parser import dataToDict, dictToData, VibrationCreepData
from loggers.logger import app_logger


class VibrationCreepSoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelVibrationCreepSoilTest()
        self._create_Ui()

        self.static_widget.deviator_loading_sliders.signal[object].connect(self._static_model_change)
        self.static_widget.consolidation_sliders.signal[object].connect(self._static_model_change)
        self.static_widget.deviator_loading.slider_cut.sliderMoved.connect(self._static_model_change)

    def _create_Ui(self):

        self.layout = QHBoxLayout(self)
        self.widget = QWidget()
        self.layout_dynamic_widget = QHBoxLayout()
        self.widget.setLayout(self.layout_dynamic_widget)
        self.dynamic_widget = VibrationCreepUI()
        self.layout_1 = QVBoxLayout()
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
        self.identification = TableVertical(fill_keys)
        self.identification.setFixedWidth(350)
        self.identification.setFixedHeight(700)
        self.layout_dynamic_widget.addWidget(self.dynamic_widget)
        self.layout_1.addWidget(self.identification)
        self.layout_1.addStretch(-1)
        self.layout_1.addLayout(self.layout_1)
        self.layout_dynamic_widget.addLayout(self.layout_1)
        self.layout_dynamic_widget.setContentsMargins(5, 5, 5, 5)

        self.static_widget = TriaxialStaticWidgetSoilTest()

        self.tab_widget = QTabWidget()
        self.tab_1 = self.static_widget
        self.tab_2 = self.widget

        self.tab_widget.addTab(self.tab_1, "Статический опыт")
        self.tab_widget.addTab(self.tab_2, "Динамический опыт")
        self.layout.addWidget(self.tab_widget)

    def set_test_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        app_logger.info(f"Моделирование опыта: {params.physical_properties.laboratory_number}")
        try:
            self._model.set_test_params(params)
            self.static_widget.set_model(self._model._static_test_data)
            self.static_widget.item_identification.set_data(params)
            self._plot()
            app_logger.info(f"Моделирование успешно")
        except:
            app_logger.info(f"Параметры моделируемого опыта: {params}")
            app_logger.info("ОШИБКА")
            app_logger.info(" ")
            pass

    def get_test_params(self):
        return self._model.get_test_params()

    def get_test_results(self):
        return self._model.get_test_results()

    def _static_model_change(self):
        self._model._static_test_data = self.static_widget._model
        self._plot()

    def save_log(self, directory):
        self._model.save_log(directory)

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.dynamic_widget.plot(plots, res)

        #plots = self._model._static_test_data.get_plot_data()
        #res = self._model._static_test_data.get_test_results()
        #self.static_widget.plot(plots, res)

class PredictVCTestResults(QDialog):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self, data=None, data_customer=None):
        super().__init__()
        self._table_is_full = False
        self._data_customer = data_customer
        self.setWindowTitle("Резонансная колонка")
        self.create_IU()

        self._G0_ratio = 1
        self._threshold_shear_strain_ratio = 1

        self._original_keys_for_sort = list(data.keys())
        self._set_data(data)
        self.table_castomer.set_data(data_customer)
        self.resize(1400, 800)


        self.open_data_button.clicked.connect(self._read_data_from_json)
        self.save_data_button.clicked.connect(self._save_data_to_json)
        self.save_button.clicked.connect(self._save_pdf)
        self.combo_box.activated.connect(self._sort_combo_changed)

    def create_IU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.table_castomer = Table_Castomer()
        self.table_castomer.setFixedHeight(80)
        self.layout.addWidget(self.table_castomer)

        self.l = QHBoxLayout()
        self.button_box = QGroupBox("Инструменты")
        self.button_box_layout = QHBoxLayout()
        self.button_box.setLayout(self.button_box_layout)
        self.open_data_button = QPushButton("Подгрузить данные")
        self.open_data_button.setFixedHeight(30)
        self.save_data_button = QPushButton("Сохранить данные")
        self.save_data_button.setFixedHeight(30)
        self.save_button = QPushButton("Сохранить данные PDF")
        self.save_button.setFixedHeight(30)
        self.combo_box = QComboBox()
        self.combo_box.setFixedHeight(30)
        self.combo_box.addItems(["Сортировка", "sigma_3", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.open_data_button)
        self.button_box_layout.addWidget(self.save_data_button)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)

        self.l.addWidget(self.button_box)
        self.layout.addLayout(self.l)

        self.table = QTableWidget()
        self._clear_table()
        self.layout.addWidget(self.table)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        self._table_is_full = False

        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il", "e", "𝜎3, кПа", "qf, кПа", "t, кПа",
             "Частота, Гц", "Kd, д.е."])
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

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(self._data))
        ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il", "e", "𝜎3, кПа", "qf, кПа", "t, кПа",
         "Частота, Гц", "Kd, д.е."]
        for string_number, lab_number in enumerate(self._data):
            for i, val in enumerate([
                lab_number,
                str(self._data[lab_number].physical_properties.depth),
                self._data[lab_number].physical_properties.soil_name,
                str(self._data[lab_number].Il) if self._data[lab_number].Il else "-",
                str(self._data[lab_number].e) if self._data[lab_number].e else "-",
                str(np.round(self._data[lab_number].sigma_3)),
                str(np.round(self._data[lab_number].qf)),
                str(np.round(self._data[lab_number].t)),
                str(self._data[lab_number].frequency).strip("[").strip("]"),
                str(self._data[lab_number].Kd).strip("[").strip("]")
            ]):

                self.table.setItem(string_number, i, QTableWidgetItem(val))

        self._table_is_full = True

    def _set_data(self, data):
        """Функция для получения данных"""
        self._data = data
        self._fill_table()

    def _sort_combo_changed(self):
        """Изменение способа сортировки combo_box"""
        if self._table_is_full:
            if self.combo_box.currentText() == "Сортировка":
                self._data = {key: self._data[key] for key in self._original_keys_for_sort}
                self._clear_table()
            else:
                self._sort_data(self.combo_box.currentText())
                self._clear_table()

            self._fill_table()

    def _save_data_to_json(self):
        s = QFileDialog.getSaveFileName(self, 'Open file')[0]
        if s:
            s += ".json"
            create_json_file(s, dataToDict(self.get_data()))

    def _read_data_from_json(self):
        s = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if s:
            data = read_json_file(s)
            if sorted(data) == sorted(self._data):
                self._set_data(dictToData(data, VibrationCreepData))
            else:
                QMessageBox.critical(self, "Ошибка", "Неверная структура данных", QMessageBox.Ok)

    def _sort_data(self, sort_key="sigma_3"):
        """Сортировка проб"""
        #sort_lab_numbers = sorted(list(self._data.keys()), key=lambda x: self._data[x][sort_key])
        #self._data = {key: self._data[key] for key in sort_lab_numbers}
        #self._data = dict(sorted(self._data.items(), key=lambda x: self._data[x[0]][sort_key]))

        self._data = dict(sorted(self._data.items(), key=lambda x: getattr(self._data[x[0]], sort_key)))

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирование парметров виброползучести"
            titles, data, scales = PredictVCTestResults.transform_data_for_statment(self.get_data())
            try:
                save_report(titles, data, scales, self._data_customer["data"], ['Заказчик:', 'Объект:'],
                            [self._data_customer["customer"], self._data_customer["object_name"]], statement_title,
                            save_dir, "---", "Прогноз Kd.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    def get_data(self):
        data = self._data
        for string_number, lab_number in enumerate(data):
            data[lab_number].Kd = [float(x) for x in self.table.item(string_number, 9).text().split(",")]
        return data

    @staticmethod
    def transform_data_for_statment(data):
        """Трансформация данных для передачи в ведомость"""
        data_structure = []

        for string_number, lab_number in enumerate(data):
                data_structure.append([
                    lab_number,
                    str(data[lab_number].physical_properties.depth),
                    data[lab_number].physical_properties.soil_name,
                    str(data[lab_number].Il) if data[lab_number].Il else "-",
                    str(data[lab_number].e) if data[lab_number].e else "-",
                    str(np.round(data[lab_number].sigma_3)),
                    str(np.round(data[lab_number].qf)),
                    str(np.round(data[lab_number].t)),
                    str(data[lab_number].frequency).strip("[").strip("]"),
                    str(data[lab_number].Kd).strip("[").strip("]")
                ])

        titles = ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il д.е.", "e, д.е.", "𝜎3, кПа",
                  "qf, кПа", "t, кПа", "Частота, Гц", "Kd, д.е."]

        scale = [60, 60, "*", 60, 60, 60, 60, 60, 60, 60]

        return (titles, data_structure, scale)



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = VibrationCreepSoilTestWidget()

    params = {'E': 50000.0, 'c': 0.023, 'fi': 45, 'qf': 593.8965363, "Kd": [0.86, 0.8, 0.7], 'sigma_3': 100,
                      'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'sigma_1': 300, 'dilatancy': 4.95, 'OCR': 1, 'm': 0.61,
     'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'depth': 9.8, 'Ip': 17.9,
     'Il': 0.79, 'K0': 1, 'groundwater': 0.0, 'ro': 1.76, 'balnost': 2.0, 'magnituda': 5.0, 'rd': '0.912', 'N': 100,
     'MSF': '2.82', 'I': 2.0, 'sigma1': 100, 't': 10, 'sigma3': 100, 'ige': '-', 'Nop': 20, 'lab_number': '4-5',
     'data_phiz': {'borehole': 'rete', 'depth': 9.8,
                   'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'ige': '-',
                   'rs': 2.73, 'r': 1.76, 'rd': 1.23, 'n': 55.0, 'e': 1.22, 'W': 43.4, 'Sr': 0.97, 'Wl': 47.1,
                   'Wp': 29.2, 'Ip': 17.9, 'Il': 0.79, 'Ir': 6.8, 'str_index': 'l', 'gw_depth': 0.0, 'build_press': '-',
                   'pit_depth': '-', '10': '-', '5': '-', '2': '-', '1': '-', '05': '-', '025': 0.3, '01': 0.1,
                   '005': 17.7, '001': 35.0, '0002': 18.8, '0000': 28.1, 'Nop': 20}, 'test_type': 'Сейсморазжижение',
                               "frequency": [1, 5, 10], "n_fail": None, "Mcsr": 100}
    ex.set_test_params(params)

    ex.show()
    sys.exit(app.exec_())
