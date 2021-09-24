from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout
import numpy as np
import sys


from cyclic_loading.cyclic_loading_widgets_UI import CyclicLoadingUI, CyclicLoadingOpenTestUI, CyclicLoadingUISoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoading, ModelTriaxialCyclicLoadingSoilTest
from general.initial_tables import TableVertical

class CyclicLoadingProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelTriaxialCyclicLoading()
        self._create_Ui()
        self.open_widget.button_open.clicked.connect(self._open_log)
        self.open_widget.button_plot.clicked.connect(self._plot)

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

class CyclicLoadingSoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelTriaxialCyclicLoadingSoilTest()
        self._create_Ui()
        self.test_widget.sliders_widget.strain_signal[object].connect(self._sliders_strain)
        self.test_widget.sliders_widget.PPR_signal[object].connect(self._sliders_PPR)
        self.test_widget.sliders_widget.cycles_count_signal[object].connect(self._sliders_cycles_count)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.layout_1 = QHBoxLayout(self)
        self.test_widget = CyclicLoadingUISoilTest()
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
        self.identification = TableVertical(fill_keys)
        self.identification.setFixedWidth(300)
        self.layout_1.addWidget(self.test_widget)
        self.layout_1.addWidget(self.identification)
        self.layout.addLayout(self.layout_1)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def _sliders_strain(self, param):
        self._model.set_strain_params(param)
        self._plot()

    def _sliders_PPR(self, param):
        self._model.set_PPR_params(param)
        self._plot()

    def _sliders_cycles_count(self, param):
        self._model.set_cycles_count(param["cycles_count"])
        strain_params, ppr_params, cycles_count_params = self._model.get_draw_params()
        self.test_widget.sliders_widget.set_sliders_params(strain_params, ppr_params, cycles_count_params, True)
        self._plot()

    def set_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        self._model.set_test_params(params)
        strain_params, ppr_params, cycles_count_params = self._model.get_draw_params()
        self.test_widget.sliders_widget.set_sliders_params(strain_params, ppr_params, cycles_count_params)
        self._plot()

    def open_log(self, path):
        """Открытие файла опыта"""
        test_data = ModelTriaxialCyclicLoading.open_wille_log(path)
        self._model.set_test_data(test_data)
        self._model.set_processing_parameters(test_data)
        self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_widget.plot(plots, res)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicLoadingSoilTestWidget()

    params = {'E': 50000.0, 'c': 0.023, 'fi': 8.2,
              'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'depth': 9.8,
              'Ip': 17.9,
              'Il': 0.79, 'K0': 1, 'groundwater': 0.0, 'ro': 1.76, 'balnost': 2.0, 'magnituda': 5.0, 'rd': '0.912',
              'N': 1200,
              'MSF': '2.82', 'I': 2.0, 'sigma1': 96, 't': 22.56, 'sigma3': 96, 'ige': '-', 'Nop': 20,
              'lab_number': '4-5',
              'data_phiz': {'borehole': 'rete', 'depth': 9.8,
                            'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества',
                            'ige': '-',
                            'rs': 2.73, 'r': 1.76, 'rd': 1.23, 'n': 55.0, 'e': 1.22, 'W': 43.4, 'Sr': 0.97, 'Wl': 47.1,
                            'Wp': 29.2, 'Ip': 17.9, 'Il': 0.79, 'Ir': 6.8, 'str_index': 'l', 'gw_depth': 0.0,
                            'build_press': '-',
                            'pit_depth': '-', '10': '-', '5': '-', '2': '-', '1': '-', '05': '-', '025': 0.3, '01': 0.1,
                            '005': 17.7, '001': 35.0, '0002': 18.8, '0000': 28.1, 'Nop': 20},
              'test_type': 'Сейсморазжижение'}
    ex.set_params(params)

    ex.show()
    sys.exit(app.exec_())
