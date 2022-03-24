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
        self.figure.subplots_adjust(right=0.98, top=0.98, bottom=0.14, wspace=0.2, hspace=0.2, left=0.08)
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
            self.ax_G.scatter([], [], label="$γ_{0.7}$" + " = " + str(results["threshold_shear_strain"]) +
                                            " " + "$⋅10^{-4}$", color="#eeeeee")
            self.ax_G.legend()

            for i in range(len(plot_data["frequency"])):
                self.ax_rezonant.plot(plot_data["frequency"][i], plot_data["resonant_curves"][i])
                self.ax_rezonant.scatter(plot_data["frequency"][i], plot_data["resonant_curves"][i], s=10)

            self.canvas.draw()

        except:
            pass

    def save_canvas(self,):
        """Сохранение графиков для передачи в отчет"""

        self.ax_G.get_legend().remove()
        self.canvas.draw()

        path = BytesIO()
        size = self.figure.get_size_inches()
        self.figure.set_size_inches([6, 3])
        self.figure.savefig(path, format='svg', transparent=True)
        path.seek(0)
        self.figure.set_size_inches(size)

        self.ax_G.legend()
        self.canvas.draw()

        return path


class K0IdentificationUI_old(QWidget):
    """Интерфейс обработчика Резонансной колонки"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_UI()
        self.setFixedHeight(100)

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.box = QGroupBox("Идентификация пробы")
        self.box_layout = QHBoxLayout()
        self.box.setLayout(self.box_layout)

        self.lab_number_label = QLabel("Лабораторный номер")
        self.lab_number_label.setAlignment(Qt.AlignRight)
        self.lab_number_label.setFixedWidth(120)
        self.lab_number_text = QLineEdit()
        self.lab_number_text.setFixedWidth(80)
        self.lab_number_text.setDisabled(True)

        self.borehole_label = QLabel("Скважина")
        self.borehole_label.setAlignment(Qt.AlignRight)
        self.borehole_label.setFixedWidth(60)
        self.borehole_text = QLineEdit()
        self.borehole_text.setFixedWidth(80)
        self.borehole_text.setDisabled(True)

        self.depth_label = QLabel("Глубина")
        self.depth_label.setAlignment(Qt.AlignRight)
        self.depth_label.setFixedWidth(60)
        self.depth_text = QLineEdit()
        self.depth_text.setFixedWidth(80)
        self.depth_text.setDisabled(True)

        self.name_label = QLabel("Наименование")
        self.name_label.setAlignment(Qt.AlignRight)
        self.name_label.setFixedWidth(80)
        self.name_text = QTextEdit()
        self.name_text.setDisabled(True)

        self.p_ref_label = QLabel("Референтное давление")
        self.p_ref_label.setAlignment(Qt.AlignRight)
        self.p_ref_label.setFixedWidth(120)
        self.p_ref_text = QLineEdit()
        self.p_ref_text.setDisabled(True)
        self.p_ref_text.setFixedWidth(80)

        self.e_label = QLabel("Коэф. пористости")
        self.e_label.setAlignment(Qt.AlignRight)
        self.e_label.setFixedWidth(100)
        self.e_text = QLineEdit()
        self.e_text.setFixedWidth(80)
        self.e_text.setDisabled(True)

        self.E_label = QLabel("Модуль Е50")
        self.E_label.setAlignment(Qt.AlignRight)
        self.E_label.setFixedWidth(100)
        self.E_text = QLineEdit()
        self.E_text.setFixedWidth(80)
        self.E_text.setDisabled(True)

        self.column_1 = QVBoxLayout()
        self.column_2 = QVBoxLayout()
        self.column_3 = QVBoxLayout()
        self.column_4 = QVBoxLayout()
        self.column_5 = QVBoxLayout()
        self.column_6 = QVBoxLayout()
        self.column_7 = QVBoxLayout()
        self.column_8 = QVBoxLayout()

        self.column_1.addWidget(self.lab_number_label)
        self.column_1.addWidget(self.p_ref_label)
        self.column_2.addWidget(self.lab_number_text)
        self.column_2.addWidget(self.p_ref_text)

        self.column_3.addWidget(self.depth_label)
        self.column_3.addWidget(self.borehole_label)
        self.column_4.addWidget(self.depth_text)
        self.column_4.addWidget(self.borehole_text)

        self.column_5.addWidget(self.e_label)
        self.column_5.addWidget(self.E_label)
        self.column_6.addWidget(self.e_text)
        self.column_6.addWidget(self.E_text)

        self.column_7.addWidget(self.name_label)
        self.column_7.addStretch(-1)
        self.column_8.addWidget(self.name_text)

        self.box_layout.addLayout(self.column_1)
        self.box_layout.addLayout(self.column_2)
        self.box_layout.addLayout(self.column_3)
        self.box_layout.addLayout(self.column_4)
        self.box_layout.addLayout(self.column_5)
        self.box_layout.addLayout(self.column_6)
        self.box_layout.addLayout(self.column_7)
        self.box_layout.addLayout(self.column_8)

        self.layout.addWidget(self.box)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_params(self):
        self.lab_number_text.setText(str(statment[statment.current_test].physical_properties.laboratory_number))
        self.borehole_text.setText(str(statment[statment.current_test].physical_properties.borehole))
        self.depth_text.setText(str(statment[statment.current_test].physical_properties.depth))
        self.name_text.setText(str(statment[statment.current_test].physical_properties.soil_name))
        self.p_ref_text.setText(str(statment[statment.current_test].mechanical_properties.reference_pressure))
        self.e_text.setText(str(statment[statment.current_test].physical_properties.e))
        self.E_text.setText(str(statment[statment.current_test].mechanical_properties.E50))


class K0IdentificationUI(TableVertical):

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__({"laboratory_number": "Лаб. ном.",
                          "E50": "Модуль деформации E50, МПа",
                          "c": "Сцепление с, МПа",
                          "fi": "Угол внутреннего трения, град",
                          "e": "Коэффициент пористости, е",
                          "reference_pressure": "Референтное давление, МПа",
                          "K0": "K0"})


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
            "G0_ratio": "Коэффициент G0",
            "threshold_shear_strain_ratio": "Коэффициент жесткости",
            "frequency_step": "Шаг частоты"})
        self.sliders.set_sliders_params(
            {
                "G0_ratio": {"value": 1, "borders": [0.1, 5]},
                "threshold_shear_strain_ratio": {"value": 1, "borders": [0.1, 5]},
                "frequency_step": {"value": 3, "borders": [1, 5]}
            })
        self.layout.addWidget(self.sliders)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = K0IdentificationUI()
    ex.show()
    sys.exit(app.exec_())
