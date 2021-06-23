__version__ = 1

from PyQt5.QtWidgets import QApplication, QGridLayout, QFrame, QLabel, QHBoxLayout,\
    QVBoxLayout, QGroupBox, QWidget, QLineEdit, QPushButton
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import os
import sys
from io import BytesIO

from general.initial_tables import Table
from general.general_widgets import Float_Slider, RangeSlider
from general.general_functions import read_json_file
from configs.styles import style
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders

plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
plt.style.use('bmh')

class RezonantColumnUI(QWidget):
    """Интерфейс обработчика Резонансной колонки"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox("Обработка опыта")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.cut_box = QGroupBox("Обрезка значений")
        self.cut_box_layout = QVBoxLayout()
        self.cut_box.setLayout(self.cut_box_layout)
        self.cut_slider = RangeSlider(Qt.Horizontal)
        self.cut_box_layout.addWidget(self.cut_slider)
        self.graph_layout.addWidget(self.cut_box)

        self.canvas_frame = QFrame()
        self.canvas_frame.setFrameShape(QFrame.StyledPanel)
        self.canvas_frame.setStyleSheet('background: #ffffff')
        self.canvas_frame_layout = QVBoxLayout()
        self.canvas_frame.setLayout(self.canvas_frame_layout)
        self.figure = plt.figure()
        self.figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.2, hspace=0.2, left=0.08)
        self.canvas = FigureCanvas(self.figure)

        self.ax_G = self.figure.add_subplot(1, 2, 2)
        self.ax_G.set_xlabel("Деформация сдвига γ, д.е.")
        self.ax_G.set_xscale("log")
        self.ax_G.set_ylabel("Модуль сдвига G, МПа")

        self.ax_rezonant = self.figure.add_subplot(1, 2, 1)
        self.ax_rezonant.set_xlabel("Частота f, Гц")
        self.ax_rezonant.set_ylabel("Деформация сдвига γ, д.е.")
        self.canvas.draw()

        self.canvas_frame_layout.setSpacing(0)
        self.canvas_frame_layout.addWidget(self.canvas)

        self.graph_layout.addWidget(self.canvas_frame)
        self.layout.addWidget(self.graph)

        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def plot(self, plot_data, results):
        """Построение графиков опыта"""
        try:
            self.ax_G.clear()
            self.ax_G.set_xscale("log")
            self.ax_G.set_xlabel("Деформация сдвига γ, д.е.")
            self.ax_G.set_ylabel("Модуль сдвига G, МПа")

            self.ax_rezonant.clear()
            self.ax_rezonant.set_xlabel("Частота f, Гц")
            self.ax_rezonant.set_ylabel("Деформация сдвига γ, д.е.")

            self.ax_G.scatter(plot_data["shear_strain"], plot_data["G"], label="test data", color="tomato")
            self.ax_G.plot(plot_data["shear_strain_approximate"], plot_data["G_approximate"], label="approximate data")

            self.ax_G.scatter([], [], label="$G_{0}$" + " = " + str(results["G0"]), color="#eeeeee")
            self.ax_G.scatter([], [], label="$γ_{0.7}$" + " = " + str(results["threshold_shear_strain"]) + " " +
                                       "$⋅10^{-4}$", color="#eeeeee")
            self.ax_G.legend()

            for i in range(len(plot_data["frequency"])):
                self.ax_rezonant.plot(plot_data["frequency"][i], plot_data["resonant_curves"][i])
                self.ax_rezonant.scatter(plot_data["frequency"][i], plot_data["resonant_curves"][i], s=10)

            self.canvas.draw()

        except:
            pass

    def save_canvas(self, format_="svg"):
        """Сохранение графиков для передачи в отчет"""
        def save(figure, canvas, size_figure, file_type):
            path = BytesIO()
            size = figure.get_size_inches()
            figure.set_size_inches(size_figure)
            if file_type == "svg":
                figure.savefig(path, format='svg', transparent=True)
            elif file_type == "jpg":
                figure.savefig(path, format='jpg', dpi=200, bbox_inches='tight')
            path.seek(0)
            figure.set_size_inches(size)
            canvas.draw()
            return path

        return save(self.figure, self.canvas, [6, 3], 'svg')

class RezonantColumnOpenTestUI(QWidget):
    """Виджет для открытия файла прибора и определения параметров опыта"""
    # Сигнал для построения опыта после открытия файла. Передается в ModelTriaxialCyclicLoadingUI для активации plot
    signal_open_data = pyqtSignal(int)

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()

        self.test_data = None

        self._create_UI()

    def _create_UI(self):
        self.layout = QHBoxLayout(self)

        self.box = QGroupBox("Файл прибора")
        self.box_layout = QHBoxLayout()
        self.box.setLayout(self.box_layout)

        self.button_open_file = QPushButton("Открыть файл прибора")
        self.button_open_path = QPushButton("Открыть папку с файлами прибора")

        self.file_path = QLineEdit()
        font = self.file_path.font()
        font.setPointSize(50)
        #self.file_path.setDisabled(True)
        #self.file_path.setFixedHeight(50)
        self.box_layout.addWidget(self.button_open_file)
        self.box_layout.addWidget(self.button_open_path)
        self.box_layout.addWidget(self.file_path)

        self.layout.addWidget(self.box)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_file_path(self, path):
        self.file_path.setText(path)

class RezonantColumnSoilTestUI(RezonantColumnUI):
    """Интерфейс моделирования опыта резонансной колонки"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()

        self._create_ST_UI()

    def _create_ST_UI(self):
        """Создание данных интерфейса"""
        self.sliders = TriaxialStaticLoading_Sliders({
            "G0_ratio": "Коэффициент G0",
            "threshold_shear_strain_ratio": "Коэффициент жесткости",
            "frequency_step": "Шаг частоты"})
        self.sliders.set_sliders_params(
            {
                "G0_ratio": {"value": 1, "borders": [0.1, 5]},
                "threshold_shear_strain_ratio": {"value": 1, "borders": [0.1, 5]},
                "frequency_step": {"value": 5, "borders": [1, 5]}
            })
        self.layout.addWidget(self.sliders)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = RezonantColumnSoilTestUI()
    ex.show()
    sys.exit(app.exec_())
