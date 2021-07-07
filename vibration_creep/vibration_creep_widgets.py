from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout
import numpy as np
import sys


from vibration_creep.vibration_creep_widgets_UI import VibrationCreepUI
from vibration_creep.vibration_creep_model import ModelVibrationCreepSoilTest

class VibrationCreepSoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelVibrationCreepSoilTest()
        self._create_Ui()

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.layout_1 = QHBoxLayout(self)
        self.test_widget = VibrationCreepUI()
        self.layout.addWidget(self.test_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_test_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        self._model.set_test_params(params)
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
