"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
__version__ = 1

from PyQt5.QtWidgets import QApplication, QGridLayout, QFrame, QLabel, QHBoxLayout,\
    QVBoxLayout, QGroupBox, QWidget, QLineEdit, QPushButton, QTableWidget, QDialog, QHeaderView,  QTableWidgetItem, \
    QHeaderView, QDialogButtonBox, QFileDialog, QMessageBox, QItemDelegate, QComboBox
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import os
import numpy as np
import sys
from io import BytesIO

from general.initial_tables import Table
from general.general_functions import read_json_file
from configs.plot_params import plotter_params

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class VibrationCreepUI(QWidget):
    """Интерфейс обработчика виброползучести"""

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.2, "wspace": 0.12, "hspace": 0.07, "left": 0.1}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()

        self.buttons_group = QGroupBox("Функции обработки")
        self.buttons_group_layout = QHBoxLayout()
        self.buttons_group.setLayout(self.buttons_group_layout)
        self.static_test_button = QPushButton("Обработчик статики")
        self.buttons_group_layout.addWidget(self.static_test_button)
        self.layout.addWidget(self.buttons_group)


        self.main_graph = QGroupBox("График виброползучести")
        self.main_graph_layout = QVBoxLayout()
        self.main_graph.setLayout(self.main_graph_layout)

        self.vibration_creep_frame = QFrame()
        self.vibration_creep_frame.setFrameShape(QFrame.StyledPanel)
        self.vibration_creep_frame.setStyleSheet('background: #ffffff')
        self.vibration_creep_frame_layout = QVBoxLayout()
        self.vibration_creep_frame.setLayout(self.vibration_creep_frame_layout)
        self.vibration_creep_figure = plt.figure()
        self.vibration_creep_figure.subplots_adjust(**self.plot_params)
        self.vibration_creep_canvas = FigureCanvas(self.vibration_creep_figure)
        self.vibration_creep_ax = self.vibration_creep_figure.add_subplot(111)
        self.vibration_creep_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.vibration_creep_ax.set_ylabel("Девиатор q, кПА")
        self.vibration_creep_canvas.draw()
        self.vibration_creep_frame_layout.setSpacing(0)
        self.vibration_creep_frame_layout.addWidget(self.vibration_creep_canvas)
        self.vibration_creep_toolbar = NavigationToolbar(self.vibration_creep_canvas, self)
        self.dyn_phase_ax = self.vibration_creep_figure.add_axes([0.65, 0.25, .3, .5])
        self.dyn_phase_ax.set_title('Динамическая нагрузка', fontsize=10)
        self.dyn_phase_ax.set_xticks([])
        self.dyn_phase_ax.set_yticks([])
        self.vibration_creep_frame_layout.addWidget(self.vibration_creep_toolbar)
        self.main_graph_layout.addWidget(self.vibration_creep_frame)

        self.layout.addWidget(self.main_graph)

        self.creep_graph = QGroupBox("Кривая ползучести")
        self.creep_graph_layout = QVBoxLayout()
        self.creep_graph.setLayout(self.creep_graph_layout)

        self.creep_frame = QFrame()
        self.creep_frame.setFrameShape(QFrame.StyledPanel)
        self.creep_frame.setStyleSheet('background: #ffffff')
        self.creep_frame_layout = QVBoxLayout()
        self.creep_frame.setLayout(self.creep_frame_layout)
        self.creep_figure = plt.figure()
        self.creep_figure.subplots_adjust(**self.plot_params)
        self.creep_canvas = FigureCanvas(self.creep_figure)
        self.creep_ax = self.creep_figure.add_subplot(111)
        self.creep_ax.set_xlabel("Время")
        self.creep_ax.set_ylabel("Относительная деформация $ε_1$, д.е.")
        self.creep_ax.set_xscale("log")
        self.creep_canvas.draw()
        self.creep_frame_layout.setSpacing(0)
        self.creep_frame_layout.addWidget(self.creep_canvas)
        self.creep_toolbar = NavigationToolbar(self.creep_canvas, self)
        self.creep_frame_layout.addWidget(self.creep_toolbar)
        self.creep_graph_layout.addWidget(self.creep_frame)

        self.layout.addWidget(self.creep_graph)

        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def plot(self, plot_data, result_data ):
        """Построение графиков опыта"""

        self.vibration_creep_ax.clear()
        self.vibration_creep_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.vibration_creep_ax.set_ylabel("Девиатор q, кПА")

        self.dyn_phase_ax.clear()
        self.dyn_phase_ax.set_title('Динамическая нагрузка', fontsize=10)
        self.dyn_phase_ax.set_xticks([])
        self.dyn_phase_ax.set_yticks([])

        self.creep_ax.clear()
        self.creep_ax.set_xlabel("Время")
        self.creep_ax.set_ylabel("Относительная деформация $ε_1$, д.е.")
        self.creep_ax.set_xscale("log")


        try:
            self.vibration_creep_ax.plot(plot_data["strain"], plot_data["deviator"], alpha=0.5, linewidth=2)
            lims = [min([min(x) for x in plot_data["creep_curve"]]),
                    max([max(x) for x in plot_data["creep_curve"]]) * 1.05]

            self.dyn_phase_ax.set_xlim(*lims)

            for i, color in zip(range(len(plot_data["strain_dynamic"])), ["tomato", "forestgreen", "purple"]):
                plot_data["creep_curve"][i] -= plot_data["creep_curve"][i][0]
                self.vibration_creep_ax.plot(plot_data["strain_dynamic"][i], plot_data["deviator_dynamic"][i], alpha=0.5,
                                 linewidth=1.5,
                                 color=color, label="Kd = " + str(result_data[i]["Kd"]) + "; frequency = " + str(
                        plot_data["frequency"][i]) + " Hz")

                self.dyn_phase_ax.plot(plot_data["creep_curve"][i],
                                  plot_data["deviator_dynamic"][i][len(plot_data["deviator_dynamic"][i]) -
                                                                   len(plot_data["creep_curve"][i]):],
                                  alpha=0.5, linewidth=1, color=color)

                if plot_data["creep_curve"][i] is not None:
                    self.creep_ax.plot(plot_data["time"][i], plot_data["creep_curve"][i], alpha=0.5, color=color,
                                  label="frequency = " + str(plot_data["frequency"][i]) + " Hz")

                if plot_data["E50d"][i]:
                    self.vibration_creep_ax.plot(*plot_data["E50d"][i], **plotter_params["black_dotted_line"])

                # if plot_data["E50"][i]:
                # ax_deviator.plot(*plot_data["E50"][i], **plotter_params["black_dotted_line"])

                self.vibration_creep_ax.legend()
                self.creep_ax.legend()
        except:
            pass

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, ax, file_type):

            ax.get_legend().remove()
            canvas.draw()

            path = BytesIO()
            size = figure.get_size_inches()
            figure.set_size_inches(size_figure)
            if file_type == "svg":
                figure.savefig(path, format='svg', transparent=True)
            elif file_type == "jpg":
                figure.savefig(path, format='jpg', dpi=200, bbox_inches='tight')
            path.seek(0)
            figure.set_size_inches(size)
            ax.legend()
            canvas.draw()
            return path

        return [save(fig, can, size, ax, "svg") for fig, can, size, ax in zip([self.deviator_figure,
                                                                               self.volume_strain_figure],
                                                                              [self.deviator_canvas,
                                                                               self.volume_strain_canvas],
                                                                              [[6, 2], [6, 2]],
                                                                              [self.deviator_ax,
                                                                               self.volume_strain_ax])]

class VibrationCreepOpenTestUI(QWidget):
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

        self.button_open = QPushButton("Открыть файл прибора")
        #self.button_open.setFixedHeight(50)

        self.file_path = QLineEdit()
        font = self.file_path.font()
        font.setPointSize(50)
        #self.file_path.setDisabled(True)
        #self.file_path.setFixedHeight(50)
        self.box_layout.addWidget(self.button_open)
        self.box_layout.addWidget(self.file_path)

        self.table = Table()
        self.table.setFixedHeight(50)
        self.table.setFixedWidth(400)
        self.table.set_data([["𝜎1, кПа", "𝜎3, кПа", "τ, кПа",
                             "Частота, Гц"], ["", "", "", ""]], resize="Stretch")
        self.box_layout.addWidget(self.table)

        self.button_plot = QPushButton("Построить график")
        self.button_plot.setFixedHeight(50)
        self.box_layout.addWidget(self.button_plot)

        self.button_screen = QPushButton("Скриншот")
        self.button_screen.setFixedHeight(50)
        self.box_layout.addWidget(self.button_screen)

        self.layout.addWidget(self.box)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_file_path(self, path):
        self.file_path.setText(path)

    def set_params(self, params):
        self.table.set_data([["𝜎1, кПа", "𝜎3, кПа", "τ, кПа", "Частота, Гц"],
                             [params["sigma_1"], params["sigma_3"], params["t"], params["frequency"]]], resize="Stretch")

    def get_params(self):
        """Считывание таблицы параметров"""
        def float_item(x):
            try:
                y = float(x)
                return (y)
            except ValueError:
                return None

        params = {"sigma_1": float_item(self.table.item(0, 0).text()),
                  "sigma_3": float_item(self.table.item(0, 1).text()),
                  "t": float_item(self.table.item(0, 2).text()),
                  "frequency": float_item(self.table.item(0, 3).text())}

        return params


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = VibrationCreepUI()
    ex.show()
    sys.exit(app.exec_())
