from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QDialog, QHBoxLayout, \
    QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QHeaderView, QTableWidgetItem
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np
import sys
import copy

from resonant_column.resonant_column_widgets_UI import RezonantColumnUI, RezonantColumnOpenTestUI, \
    RezonantColumnSoilTestUI, RezonantColumnIdentificationUI
from resonant_column.rezonant_column_hss_model import ModelRezonantColumn, ModelRezonantColumnSoilTest
from general.initial_tables import Table_Castomer
from general.excel_functions import create_json_file, read_json_file
from general.report_general_statment import save_report
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from general.excel_data_parser import dataToDict, dictToData, RCData

class RezonantColumnProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelRezonantColumn()
        self._create_Ui()
        #self.open_widget.button_open_file.clicked.connect(self._open_file)
        self.open_widget.button_open_path.clicked.connect(self._open_path)
        self.test_processing_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.identification_widget = RezonantColumnIdentificationUI()
        self.open_widget = RezonantColumnOpenTestUI()
        self.layout.addWidget(self.identification_widget)
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)
        self.test_processing_widget = RezonantColumnUI()
        self.layout.addWidget(self.test_processing_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        if self._model._test_data.G_array is not None:
            self._model.set_borders(int(self.test_processing_widget.cut_slider.low()),
                                                        int(self.test_processing_widget.cut_slider.high()))
            self._plot()

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_processing_widget.cut_slider.setMinimum(0)
        self.test_processing_widget.cut_slider.setMaximum(len)
        self.test_processing_widget.cut_slider.setLow(0)
        self.test_processing_widget.cut_slider.setHigh(len)

    def _open_path(self):
        """Открытие файла опыта"""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.open_widget.set_file_path("")
            self._plot()
            try:
                self._model.open_path(path)
                self._cut_slider_set_len(len(self._model._test_data.G_array))
                self.open_widget.set_file_path(path)
            except (ValueError, IndexError, FileNotFoundError):
                pass
            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_processing_widget.plot(plots, res)

class RezonantColumnSoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelRezonantColumnSoilTest()
        self._create_Ui()
        #self.open_widget.button_open_file.clicked.connect(self._open_file)
        self.test_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.identification_widget = RezonantColumnIdentificationUI()
        self.test_widget = RezonantColumnSoilTestUI()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self._refresh)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.identification_widget)
        self.layout.addWidget(self.test_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        if self._model._test_data.G_array is not None:
            self._model.set_borders(int(self.test_widget.cut_slider.low()),
                                                        int(self.test_widget.cut_slider.high()))
            self._plot()

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_widget.cut_slider.setMinimum(0)
        self.test_widget.cut_slider.setMaximum(len)
        self.test_widget.cut_slider.setLow(0)
        self.test_widget.cut_slider.setHigh(len)

    def set_test_params(self, params):
        self._model.set_test_params(params)
        self._cut_slider_set_len(len(self._model._test_data.G_array))
        self._plot()

    def _refresh(self):
        params = self._model.get_test_params()
        if params:
            self._model.set_test_params(params)
            self._cut_slider_set_len(len(self._model._test_data.G_array))
            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_widget.plot(plots, res)

class PredictRCTestResults(QDialog):
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

        self.sliders.signal[object].connect(self._sliders_moove)

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
        self.combo_box.addItems(["Сортировка", "reference_pressure", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.open_data_button)
        self.button_box_layout.addWidget(self.save_data_button)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)
        self.sliders = TriaxialStaticLoading_Sliders({
            "G0_ratio": "Коэффициент G0",
            "threshold_shear_strain_ratio": "Коэффициент жесткости"})
        self.sliders.set_sliders_params(
            {
                "G0_ratio": {"value": 1, "borders": [0.1, 5]},
                "threshold_shear_strain_ratio": {"value": 1, "borders": [0.1, 5]}
            })

        self.l.addWidget(self.sliders)

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

        self.table.setColumnCount(8)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Реф.давление, МПа", "Коэфф. пористости e", "Е50, МПа", "G0, МПА",
             "𝛾07, д.е."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        self.table.horizontalHeader().setMinimumSectionSize(150)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(self._data))
        for string_number, lab_number in enumerate(self._data):
            for i, val in enumerate([
                lab_number,
                str(self._data[lab_number].physical_properties.depth),
                self._data[lab_number].physical_properties.soil_name,
                str(self._data[lab_number].reference_pressure),
                str(self._data[lab_number].e),
                str(np.round(self._data[lab_number].E50, 1)),
                str(np.round(self._data[lab_number].G0 * self._G0_ratio, 1)),
                str(np.round(self._data[lab_number].threshold_shear_strain *self._threshold_shear_strain_ratio, 2))
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

    def _sliders_moove(self, param):
        self._G0_ratio = param["G0_ratio"]
        self._threshold_shear_strain_ratio = param["threshold_shear_strain_ratio"]
        self._fill_table()

    def _save_data_to_json(self):
        s = QFileDialog.getSaveFileName(self, 'Open file')[0]
        if s:
            s += ".json"
            create_json_file(s, dataToDict(self._data))

    def _read_data_from_json(self):
        s = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if s:
            data = read_json_file(s)
            if sorted(data) == sorted(self._data):
                self._set_data(dictToData(data, RCData))
            else:
                QMessageBox.critical(self, "Ошибка", "Неверная структура данных", QMessageBox.Ok)

    def _sort_data(self, sort_key="reference_pressure"):
        """Сортировка проб"""
        #sort_lab_numbers = sorted(list(self._data.keys()), key=lambda x: self._data[x][sort_key])
        #self._data = {key: self._data[key] for key in sort_lab_numbers}
        #self._data = dict(sorted(self._data.items(), key=lambda x: self._data[x[0]][sort_key]))

        self._data = dict(sorted(self._data.items(), key=lambda x: getattr(self._data[x[0]], sort_key)))

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирование парметров G0"
            titles, data, scales = PredictRCTestResults.transform_data_for_statment(self.get_data())
            try:
                save_report(titles, data, scales, self._data_customer["data"], ['Заказчик:', 'Объект:'],
                            [self._data_customer["customer"], self._data_customer["object_name"]], statement_title,
                            save_dir, "---", "Прогноз G0.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    def get_data(self):
        data = copy.deepcopy(self._data)
        for string_number, lab_number in enumerate(data):
            data[lab_number].G0 = float(self.table.item(string_number, 6).text())
            data[lab_number].threshold_shear_strain = float(self.table.item(string_number, 7).text())

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
                    str(data[lab_number].reference_pressure),
                    str(data[lab_number].e),
                    str(np.round(data[lab_number].E50, 1)),
                    str(np.round(data[lab_number].G0, 1)),
                    str(np.round(data[lab_number].threshold_shear_strain, 2))])

        titles = ["Лаб. номер", "Глубина, м", "Наименование грунта", "Реф.давление, МПа", "Коэфф. пористости e",
                  "Е50, МПа", "G0, МПА", "𝛾07, д.е."]

        scale = [70, 70, "*", 70, 70, 70, 70, 70]

        return (titles, data_structure, scale)



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = PredictRCTestResults()
    ex.show()
    sys.exit(app.exec_())