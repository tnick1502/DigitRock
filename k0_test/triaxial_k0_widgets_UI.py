__version__ = 1
# system
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QHBoxLayout,\
    QVBoxLayout, QGroupBox, QWidget, QLineEdit, QPushButton, QTextEdit
from PyQt5 import Qt
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
import sys
from io import BytesIO
# global
from excel_statment.initial_tables import LinePhysicalProperties
from general.initial_tables import TableVertical
from general.general_widgets import RangeSlider
from general.general_functions import read_json_file
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from singletons import statment

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-9] + "/configs/rcParams.json"))
plt.style.use('bmh')


class K0UI(QWidget):
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

        self.canvas_frame = QFrame()
        self.canvas_frame.setFrameShape(QFrame.StyledPanel)
        self.canvas_frame.setStyleSheet('background: #ffffff')
        self.canvas_frame_layout = QVBoxLayout()
        self.canvas_frame.setLayout(self.canvas_frame_layout)
        self.figure = plt.figure()
        self.figure.subplots_adjust(right=0.98, top=0.98, bottom=0.14, wspace=0.2, hspace=0.2, left=0.08)
        self.canvas = FigureCanvas(self.figure)

        self.ax_K0 = self.figure.add_subplot(1, 1, 1)
        self.ax_K0.set_xlabel("Горизонтальное напряжение $σ_{3}$, МПа", fontsize=8)
        self.ax_K0.set_ylabel("Вертикальное напряжение $σ_{1}$, МПа", fontsize=8)

        # self.ax_K0.set_ylim([-0.001, 2.2])
        # self.ax_K0.set_xlim([-0.001, 2])

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
            self.ax_K0.clear()
            self.ax_K0.set_xlabel("Горизонтальное напряжение $σ_{3}$, МПа", fontsize=8)
            self.ax_K0.set_ylabel("Вертикальное напряжение $σ_{1}$, МПа", fontsize=8)

            # self.ax_K0.set_ylim([-0.001, 2.2])
            # self.ax_K0.set_xlim([-0.001, 2])

            self.ax_K0.scatter(plot_data["sigma_3"], plot_data["sigma_1"], label="test data", color="tomato")
            self.ax_K0.plot(plot_data["k0_line_x"], plot_data["k0_line_y"], label="approximate data")

            self.ax_K0.scatter([], [], label="$K0$" + " = " + str(results["K0"]), color="#eeeeee")

            self.ax_K0.legend()

            self.canvas.draw()

        except:
            pass

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""
        plt.rc('axes', labelsize=12)
        self.ax_K0.get_legend().remove()
        self.canvas.draw()

        path = BytesIO()
        size = self.figure.get_size_inches()
        self.figure.set_size_inches([4, 4])
        self.figure.savefig(path, format='svg', transparent=True)
        path.seek(0)
        self.figure.set_size_inches(size)

        self.ax_K0.legend()
        self.canvas.draw()

        return path


class K0IdentificationUI(TableVertical):

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__({"laboratory_number": "Лаб. ном.",
                          "depth": "Глубина, м",
                          "OCR": "OCR",
                          "K0": "K0",
                          "sigma_1_step": "Шаг нагружения, МПа",
                          "sigma_1_max": "Максимальное давление, МПа"})


class K0OpenTestUI(QWidget):
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
        # self.file_path.setDisabled(True)
        # self.file_path.setFixedHeight(50)
        self.box_layout.addWidget(self.button_open_file)
        self.box_layout.addWidget(self.button_open_path)
        self.box_layout.addWidget(self.file_path)

        self.layout.addWidget(self.box)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_file_path(self, path):
        self.file_path.setText(path)


class K0SoilTestUI(K0UI):
    """Интерфейс моделирования опыта резонансной колонки"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()

        self._create_ST_UI()

    def _create_ST_UI(self):
        """Создание данных интерфейса"""
        self.sliders = TriaxialStaticLoading_Sliders({
                                                      "OCR": "OCR",
                                                      "sigma_1_step": "Шаг нагружения, 0.050 МПа",
                                                      "sigma_1_max": "Максимальное давление, кПа"
                                                      })
        self.sliders.set_sliders_params(
            {
                "OCR": {"value": 1.3, "borders": [0, 3]},
                "sigma_1_step": {"value": 3, "borders": [0, 100]},
                "sigma_1_max": {"value": 1200, "borders": [0, 10000]}
            })
        self.layout.addWidget(self.sliders)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = K0IdentificationUI()
    ex.show()
    sys.exit(app.exec_())
