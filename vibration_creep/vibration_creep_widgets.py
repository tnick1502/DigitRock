from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QTabWidget
import numpy as np
import sys


from vibration_creep.vibration_creep_widgets_UI import VibrationCreepUI
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest
from general.initial_tables import Table_Vertical
from static_loading.triaxial_static_test_widgets import TriaxialStaticWidgetSoilTest


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
        headlines = [
            "Лаб. ном.",
            "Модуль деформации E50, кПа",
            "Сцепление с, МПа",
            "Угол внутреннего трения, град",
            "Максимальный девиатор qf, кПа",
            "Обжимающее давление sigma3, кПа",
            "Касательное напряжение, кПа",
            "Kd, д.е.",
            "Частота, Гц",
            "K0",
            "Коэффициент Пуассона",
            "Коэффициент консолидации Cv",
            "Коэффициент вторичной консолидации Ca",
            "Угол дилатансии, град",
            "OCR",
            "Показатель степени жесткости"]
        fill_keys = [
            "lab_number",
            "E50",
            "c",
            "fi",
            "qf",
            "sigma_3",
            "t",
            "Kd",
            "frequency",
            "K0",
            "poisson",
            "Cv",
            "Ca",
            "dilatancy",
            "OCR",
            "m"]
        self.identification = Table_Vertical(headlines, fill_keys)
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
        self._model.set_test_params(params)
        self.static_widget.set_model(self._model._static_test_data)
        self.static_widget.item_identification.set_data(params)
        self._plot()

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
                               "frequency": [1, 5 ,10], "n_fail": None, "Mcsr": 100}
    ex.set_test_params(params)

    ex.show()
    sys.exit(app.exec_())
