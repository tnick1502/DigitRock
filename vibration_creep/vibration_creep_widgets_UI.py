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
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.15, "wspace": 0.12, "hspace": 0.07, "left": 0.1}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()

        self.main_graph = QGroupBox("График виброползучести")
        self.main_graph_layout = QVBoxLayout()
        self.main_graph.setLayout(self.main_graph_layout)

        self.vibration_creep_frame = QFrame()
        self.vibration_creep_frame.setFrameShape(QFrame.StyledPanel)
        self.vibration_creep_frame.setStyleSheet('background: #ffffff')
        self.vibration_creep_frame_layout = QVBoxLayout()
        self.vibration_creep_frame.setLayout(self.vibration_creep_frame_layout)
        self.vibration_creep_figure = plt.figure()
        self.vibration_creep_figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.05, hspace=0, left=0.1)
        self.vibration_creep_canvas = FigureCanvas(self.vibration_creep_figure)
        self.vibration_creep_ax = self.vibration_creep_figure.add_subplot(1, 1, 1)
        self.vibration_creep_ax.set_xlabel("Деформация $ε_1$, д.е.")
        self.vibration_creep_ax.set_ylabel("Девиатор q, кПА")
        self.vibration_creep_canvas.draw()
        self.vibration_creep_frame_layout.setSpacing(0)
        self.vibration_creep_frame_layout.addWidget(self.vibration_creep_canvas)
        self.vibration_creep_toolbar = NavigationToolbar(self.vibration_creep_canvas, self)
       # self.dyn_phase_ax = self.vibration_creep_figure.add_subplot(3, 1, 3)#self.vibration_creep_figure.add_axes([0.67, 0.18, .3, .5])
        #self.dyn_phase_ax.set_title('Динамическая нагрузка', fontsize=10)
        #self.dyn_phase_ax.set_xlabel("Деформация $ε_1$, д.е.")
        #self.dyn_phase_ax.set_ylabel("Девиатор q, МПА")
        #self.dyn_phase_ax.set_xticks([])
        #self.dyn_phase_ax.set_yticks([])
        self.vibration_creep_frame_layout.addWidget(self.vibration_creep_toolbar)
        self.main_graph_layout.addWidget(self.vibration_creep_frame)

        self.layout.addWidget(self.main_graph)

        self.creep_graph = QGroupBox("Кривая ползучести")
        self.creep_graph_layout = QVBoxLayout()
        self.creep_graph.setLayout(self.creep_graph_layout)

        self.creep_frame = QFrame()
        self.creep_frame.setFixedHeight(300)
        self.creep_frame.setFrameShape(QFrame.StyledPanel)
        self.creep_frame.setStyleSheet('background: #ffffff')
        self.creep_frame_layout = QVBoxLayout()
        self.creep_frame.setLayout(self.creep_frame_layout)
        self.creep_figure = plt.figure()
        self.creep_figure.subplots_adjust(right=0.98, top=0.98, bottom=0.19, wspace=0.05, hspace=0, left=0.1)
        self.creep_canvas = FigureCanvas(self.creep_figure)
        self.creep_ax = self.creep_figure.add_subplot(111)
        self.creep_ax.set_xlabel("Время, c")
        self.creep_ax.set_ylabel("Деформация $ε_1$, д.е.")
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

    def plot(self, plot_data, result_data):
        """Построение графиков опыта"""
        self.vibration_creep_ax.clear()
        self.vibration_creep_ax.set_xlabel("Деформация $ε_1$, д.е.")
        self.vibration_creep_ax.set_ylabel("Девиатор q, МПа")

        #self.dyn_phase_ax.clear()
        #self.dyn_phase_ax.set_title('Динамическая нагрузка')#, fontsize=10)
        #self.dyn_phase_ax.set_xlabel("Деформация $ε_1$, д.е.")
        #self.dyn_phase_ax.set_ylabel("Девиатор q, МПА")
        #self.dyn_phase_ax.set_xticks([])
        #self.dyn_phase_ax.set_yticks([])

        self.creep_ax.clear()
        self.creep_ax.set_xlabel("Время, c")
        self.creep_ax.set_ylabel("Относительная деформация $ε_1$, д.е.")
        self.creep_ax.set_xscale("log")


        #self.vibration_creep_ax.plot(plot_data["strain"], plot_data["deviator"], alpha=0.5, linewidth=2)
        lims = [min([min(x) for x in plot_data["creep_curve"]]),
                max([max(x) for x in plot_data["creep_curve"]]) * 1.05]
        #self.dyn_phase_ax.set_xlim(*lims)
        for i, color in zip(range(len(plot_data["strain_dynamic"])), ["tomato", "forestgreen", "purple"]):
            #plot_data["creep_curve"][i][1] = 0
            self.vibration_creep_ax.plot(plot_data["strain_dynamic"][i], plot_data["deviator_dynamic"][i], alpha=0.5,
                             linewidth=1.5,
                             color=color, label="Kd = " + str(result_data[i]["Kd"]) + "; f = " + str(
                    plot_data["frequency"][i]) + " Hz" +  "; E50 = " + str(result_data[i]["E50"]))

            #self.dyn_phase_ax.plot(plot_data["creep_curve"][i],
                              #plot_data["deviator_dynamic"][i][len(plot_data["deviator_dynamic"][i]) -
                                                               #len(plot_data["creep_curve"][i]):],
                              #alpha=0.5, linewidth=1.5, color=color)

            if plot_data["creep_curve"][i] is not None:
                self.creep_ax.plot(plot_data["time"][i], plot_data["creep_curve"][i], alpha=0.5, color=color,
                              label="frequency = " + str(plot_data["frequency"][i]) + " Hz")
                #self.creep_ax.plot(*plot_data["approximate_curve"][i], alpha=0.9, color=color,
                     #                        label="prediction 50/100 year = " + str(
                    #                             result_data[i]["prediction"]["50_years"]) + "/" + str(
                    #                             result_data[i]["prediction"]["100_years"]),
                    #                         linestyle="--")

            if plot_data["E50d"][i]:
                self.vibration_creep_ax.plot(*plot_data["E50d"][i], **plotter_params["static_loading_black_dotted_line"])
            if len(plot_data["strain_dynamic"]) == 1:
                if plot_data["E50"][i]:
                    self.vibration_creep_ax.plot(*plot_data["E50"][i], **plotter_params["static_loading_black_dotted_line"])



            self.vibration_creep_ax.legend(loc="lower right")#, bbox_to_anchor=(0.65, 0))
            self.creep_ax.legend()
            self.vibration_creep_canvas.draw()
            self.creep_canvas.draw()

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

        return [save(fig, can, size, ax, format) for fig, can, size, ax, format in zip([self.vibration_creep_figure,
                                                                               self.creep_figure],
                                                                              [self.vibration_creep_canvas,
                                                                               self.creep_canvas],
                                                                              [[8, 2], [6, 2]],
                                                                              [self.vibration_creep_ax,
                                                                               self.creep_ax],
                                                                                      ["jpg", "jpg"])]

class VibrationCreepOpenTestUI(QWidget):
    """Виджет для открытия файла прибора и определения параметров опыта"""
    # Сигнал для построения опыта после открытия файла. Передается в ModelTriaxialCyclicLoadingUI для активации plot
    signal_open_data = pyqtSignal(int)

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_UI()

    def _create_UI(self):
        self.layout = QVBoxLayout()

        self.buttons_group = QGroupBox("Файлы приборов")
        self.buttons_group_layout = QHBoxLayout()
        self.buttons_group.setLayout(self.buttons_group_layout)

        self.line_1_layout = QHBoxLayout()
        self.open_static_test_button = QPushButton("Файл статики")
        self.static_test_line = QLineEdit()
        self.static_test_line.setDisabled(True)
        self.line_1_layout.addWidget(self.open_static_test_button)
        self.line_1_layout.addWidget(self.static_test_line)

        self.line_2_layout = QHBoxLayout()
        self.open_dynamic_test_button = QPushButton("Файл динамики")
        self.dynamic_test_line = QLineEdit()
        self.dynamic_test_line.setDisabled(True)
        self.line_2_layout.addWidget(self.open_dynamic_test_button)
        self.line_2_layout.addWidget(self.dynamic_test_line)

        self.buttons_group_layout.addLayout(self.line_1_layout)
        self.buttons_group_layout.addLayout(self.line_2_layout)
        self.layout.addWidget(self.buttons_group)

        self.setLayout(self.layout)
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
