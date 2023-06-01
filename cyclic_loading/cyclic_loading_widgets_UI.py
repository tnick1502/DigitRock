"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
__version__ = 1

from PyQt5.QtWidgets import QApplication, QGridLayout, QFrame, QLabel, QHBoxLayout,\
    QVBoxLayout, QGroupBox, QWidget, QLineEdit, QPushButton, QTableWidget, QDialog, QHeaderView,  QTableWidgetItem, \
    QHeaderView, QDialogButtonBox, QFileDialog, QMessageBox, QItemDelegate, QComboBox, QScrollArea
from cyclic_loading.strangth_functions import define_t_rel_point, perpendicular_passing_through_the_point
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Rectangle
import os
import numpy as np
import sys
from io import BytesIO

from general.initial_tables import Table
from general.general_widgets import Float_Slider
from configs.plot_params import plotter_params
from general.general_functions import read_json_file, create_json_file
from configs.styles import style
from singletons import Cyclic_models, statment
from general.report_general_statment import save_report
from cyclic_loading.liquefaction_potential_model import GeneralLiquefactionModel
from general.reports import report_liquid_potential
from authentication.request_qr import request_ege_qr
from general.general_functions import line

import matplotlib as mpl
mpl.rcParams['agg.path.chunksize'] = 10000
try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file("C:/Users/Пользователь/PycharmProjects/DigitRock/configs/rcParams.json"))
plt.style.use('bmh')

class CyclicLoadingUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    Класс реализует Построение 4х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()

        # Параметры построения для всех графиков
        plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.12}

        # Данные для формы графиков
        self.deviator_params = {"label_x": "Количество циклов N, ед.",
                                "label_y": "Девиатор, кПа",
                                "toolbar": True,
                                "plot_params": {"right": 0.995, "top": 0.99, "bottom": 0.14, "wspace": 0.12,
                                                "hspace": 0.07, "left": 0.03}}
        self.strain_params = {"label_x": "Количество циклов N, ед.",
                              "label_y": "Вертикальная деформация ε, д.е.",
                              "toolbar": True,
                              "plot_params": plot_params}
        self.PPR_params = {"label_x": "Количество циклов N, ед.",
                           "label_y": "PPR, д.е.",
                           "toolbar": True,
                           "plot_params": plot_params}
        self.stress_params = {"label_x": "Среднее эффективное напряжение p`, кПа",
                              "label_y": "Максимальное касательное напряжение τ, кПа",
                              "toolbar": True,
                              "plot_params": plot_params}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QHBoxLayout()
        self.graph = QGroupBox("Графики опыта")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.result_table = Table()
        self.result_table.setFixedHeight(70)
        self.graph_layout.addWidget(self.result_table)
        self.result_table.set_data([["Критерий деформации", "Критерий PPR", "Критерий напряжений"], ["", "", ""]],
                            resize="Stretch")

        self.graph_canvas_layout = QHBoxLayout()
        self._canvas_UI("strain", self.strain_params)
        self._canvas_UI("PPR", self.PPR_params)
        self._canvas_UI("stress", self.stress_params)
        self._canvas_UI("deviator", self.deviator_params)

        self.graph_canvas_layout.addWidget(self.strain_canvas_frame)
        self.graph_canvas_layout.addWidget(self.PPR_canvas_frame)
        self.graph_canvas_layout.addWidget(self.stress_canvas_frame)

        self.graph_layout.addLayout(self.graph_canvas_layout)

        self.layout.addWidget(self.graph)
        self.graph_layout.addWidget(self.deviator_canvas_frame)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def _canvas_UI(self, name, params):
        """Функция создания графика"""
        # Создадим рамку для графика
        setattr(self, "{name_widget}_canvas_frame".format(name_widget=name), QFrame())
        chart_frame = getattr(self, "{name_widget}_canvas_frame".format(name_widget=name))
        chart_frame.setFrameShape(QFrame.StyledPanel)
        chart_frame.setStyleSheet('background: #ffffff')
        setattr(self, "{name_widget}_canvas_frame_layout".format(name_widget=name), QVBoxLayout())
        chart_frame_layout = getattr(self,
                                     "{name_widget}_canvas_frame_layout".format(name_widget=name))

        # Создадим canvas
        setattr(self, "{name_widget}_figure".format(name_widget=name), plt.figure())
        figure = getattr(self, "{name_widget}_figure".format(name_widget=name))
        figure.subplots_adjust(**params["plot_params"])

        setattr(self, "{name_widget}_canvas".format(name_widget=name), FigureCanvas(figure))
        canvas = getattr(self, "{name_widget}_canvas".format(name_widget=name))
        setattr(self, "{name_widget}_ax".format(name_widget=name), figure.add_subplot(111))
        ax = getattr(self, "{name_widget}_ax".format(name_widget=name))
        ax.set_xlabel(params["label_x"])
        ax.set_ylabel(params["label_y"])
        canvas.draw()

        chart_frame_layout.setSpacing(0)
        chart_frame_layout.addWidget(canvas)

        """if params["toolbar"]:
            setattr(self, "{name_widget}_canvas_toolbar".format(name_widget=name),
                    NavigationToolbar(canvas, self))
            toolbar = getattr(self, "{name_widget}_canvas_toolbar".format(name_widget=name))
            chart_frame_layout.addWidget(toolbar)"""

        chart_frame.setLayout(chart_frame_layout)

    def _fill_result_table(self, results):
        """Заполнение таблицы результатов опыта"""

        strain_text = "Максимальная деформация: " + str(
            results['max_strain']) + ", д.е.; Цикл начала разрушения: " + str(results['fail_cycle_criterion_strain'])

        PPR_text = "Максимальное PPR: " + str(
            results['max_PPR']) + ", д.е.; Цикл начала разрушения: " + str(results['fail_cycle_criterion_PPR'])

        stress_text = "Цикл начала разрушения: " + str(results['fail_cycle_criterion_stress'])

        self.result_table.set_data([["Критерий деформации", "Критерий PPR", "Критерий напряжений"],
                                    [strain_text, PPR_text, stress_text]], resize="Stretch")


        def table_item_color(сondition, index):
            if сondition:
                self.result_table.item(0, index).setBackground(QtGui.QColor(255, 99, 71))
            else:
                self.result_table.item(0, index).setBackground(QtGui.QColor(255, 255, 255))


        for i,j in zip([results['fail_cycle_criterion_strain'], results['fail_cycle_criterion_PPR'], results['fail_cycle_criterion_stress']], [0, 1, 2]):
            table_item_color(i, j)

    def plot(self, plot_data, results):
        """Построение графиков опыта"""
        try:
            self.strain_ax.clear()
            self.strain_ax.set_xlabel(self.strain_params["label_x"])
            self.strain_ax.set_ylabel(self.strain_params["label_y"])

            self.PPR_ax.clear()
            self.PPR_ax.set_xlabel(self.PPR_params["label_x"])
            self.PPR_ax.set_ylabel(self.PPR_params["label_y"])

            self.stress_ax.clear()
            self.stress_ax.set_xlabel(self.stress_params["label_x"])
            self.stress_ax.set_ylabel(self.stress_params["label_y"])

            self.strain_ax.set_ylim(plot_data["strain_lim"])
            self.PPR_ax.set_ylim(plot_data["PPR_lim"])


            self.strain_ax.plot(plot_data["cycles"], plot_data["strain"])
            self.PPR_ax.plot(plot_data["cycles"], plot_data["PPR"])
            self.stress_ax.plot(plot_data["mean_effective_stress"], plot_data["deviator"] / 2)

            if hasattr(self, "deviator_canvas_frame"):
                if self.deviator_canvas_frame is not None:
                    self.deviator_ax.clear()
                    self.deviator_ax.grid()
                    self.deviator_ax.set_xlabel(self.deviator_params["label_x"])
                    self.deviator_ax.set_ylabel(self.deviator_params["label_y"])
                    self.deviator_ax.plot(plot_data["cycles"], plot_data["deviator"])
                    self.deviator_canvas.draw()

            self.strain_canvas.draw()
            self.PPR_canvas.draw()
            self.stress_canvas.draw()

            self._fill_result_table(results)

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

        if format_ == "jpg":
            import matplotlib as mpl
            mpl.rcParams['agg.path.chunksize'] = len(self.model._test_data.cycles)
            format = 'jpg'
        else:
            format = 'svg'

        return [save(fig, can, size, format) for fig, can, size in zip([self.strain_figure,
                                                                            self.PPR_figure, self.stress_figure],
                                                   [self.strain_canvas, self.PPR_canvas, self.stress_canvas],
                                                                          [[3, 3], [3, 3], [6, 3]])]

class CyclicDampingUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    Класс реализует Построение 4х графиков опыта циклического разрушения, также таблицы результатов опыта."""

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()

        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.2, "wspace": 0.12, "hspace": 0.07, "left": 0.15}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox("Демпфирование")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.deviator_frame = QFrame()
        self.deviator_frame.setFrameShape(QFrame.StyledPanel)
        self.deviator_frame.setStyleSheet('background: #ffffff')
        self.deviator_frame_layout = QVBoxLayout()
        self.deviator_figure = plt.figure()
        self.deviator_figure.subplots_adjust(**self.plot_params)
        self.deviator_canvas = FigureCanvas(self.deviator_figure)
        self.deviator_ax = self.deviator_figure.add_subplot(111)
        self.deviator_ax.grid(axis='both', linewidth='0.4')
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, кПа")

        self.deviator_canvas.draw()
        self.deviator_frame_layout.setSpacing(0)
        self.deviator_frame_layout.addWidget(self.deviator_canvas)
        self.deviator_toolbar = NavigationToolbar(self.deviator_canvas, self)
        self.deviator_frame_layout.addWidget(self.deviator_toolbar)
        self.deviator_frame.setLayout(self.deviator_frame_layout)

        self.graph_layout.addWidget(self.deviator_frame)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, results):
        """Построение графиков опыта"""

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, кПа")

        self.deviator_ax.plot(plots["strain"], plots["deviator"])

        if plots["damping_strain"] is not None:
            self.deviator_ax.fill(plots["damping_strain"], plots["damping_deviator"],
                                  color="tomato", alpha=0.5, zorder=5)

            self.deviator_ax.plot([], [], label="ζ, %" + ", д.е. = " + str(results["damping_ratio"]),
                                       color="#eeeeee")

        self.deviator_ax.legend(loc='upper left')

        self.deviator_canvas.draw()

    def save_canvas(self, format_="svg"):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, ax, file_type):
            try:
                ax.get_legend().remove()
                canvas.draw()

                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                ax.legend(loc='upper left')
                canvas.draw()
            except AttributeError:
                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                canvas.draw()
            return path

        if format_ == "jpg":
            import matplotlib as mpl
            mpl.rcParams['agg.path.chunksize'] = len(self.model._test_data.cycles)
            format = 'jpg'
        else:
            format = 'svg'

        return save(self.deviator_figure, self.deviator_canvas, [4.75, 4.75], self.deviator_ax, "jpg")

class SeismicStrangthUI(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.2, "wspace": 0.12, "hspace": 0.07, "left": 0.15}
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox("Seismic strangth")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setStyleSheet('background: #ffffff')
        self.frame_layout = QVBoxLayout()
        self.figure = plt.figure()
        self.figure.subplots_adjust(**self.plot_params)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.grid(axis='both', linewidth='0.4')
        self.ax.set_xlabel("σ, МПа")
        self.ax.set_ylabel("τ, МПа")
        self.canvas.draw()
        self.frame_layout.setSpacing(0)
        self.frame_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.frame_layout.addWidget(self.toolbar)
        self.frame.setLayout(self.frame_layout)

        self.graph_layout.addWidget(self.frame)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, sigma_3, sigma_1, u, c, fi):
        """Построение графиков опыта"""
        self.ax.clear()
        self.ax.set_xlabel("σ, МПа")
        self.ax.set_ylabel("τ, МПа")

        x_start = -c / np.tan(np.deg2rad(fi))

        critical_line_x = np.linspace(x_start, sigma_1, 100)
        critical_line_y = line(np.tan(np.deg2rad(fi)), c, critical_line_x)

        mohr_x, mohr_y = SeismicStrangthUI.mohr_circle(sigma_3, sigma_1)

        self.ax.fill(mohr_x, mohr_y, alpha=0.6, label='Природное состояние')
        self.ax.fill(mohr_x - u, mohr_y, alpha=0.6, color="tomato", label='С учетом нагрузки')
        self.ax.plot(critical_line_x, critical_line_y, color="firebrick")

        trel_x, trel_y = define_t_rel_point(c, fi, sigma_3, sigma_1)
        self.ax.plot([(sigma_3 + sigma_1) / 2, trel_x], [0, trel_y], color='black', linewidth=0.5, linestyle="--")

        trel_x_ref, trel_y_ref = define_t_rel_point(c, fi, sigma_3 - u, sigma_1 - u)
        self.ax.plot([(sigma_3 - u + sigma_1 - u) / 2, trel_x_ref], [0, trel_y_ref], color='black', linewidth=0.5, linestyle="--")


        lim_x = abs(x_start) + sigma_1
        lim_y = critical_line_y[-1] * 1.1

        if lim_x > lim_y:
            a = lim_x
            self.ax.set_xlim(x_start, sigma_1 * 1.2)
            self.ax.set_ylim(0, (sigma_1 * 1.2 - x_start) * 0.5)
        else:
            a = lim_y
            self.ax.set_ylim(0, critical_line_y[-1] * 1.2)
            self.ax.set_xlim(x_start, (critical_line_y[-1] * 1.2 - abs(x_start)) * 2)

        self.ax.add_patch(
            Rectangle(
                (trel_x, trel_y),
                a / 25,
                a / 25,
                angle=fi + 180,
                edgecolor='black',
                facecolor='none',
                lw=0.2)
        )

        self.ax.add_patch(
            Rectangle(
                (trel_x_ref, trel_y_ref),
                a / 25,
                a / 25,
                angle=fi + 180,
                edgecolor='black',
                facecolor='none',
                lw=0.2)
        )

        self.ax.legend(loc='upper left')
        self.canvas.draw()

    @staticmethod
    def mohr_circle(sigma_3, sigma_1):
        def Round(x, a, b):
            val = np.full(len(x), 0.)
            for i in range(len(x)):
                val[i] = ((((b - a) ** 2) / 4) - ((((2 * x[i]) - b - a) ** 2) / 4))
                if val[i] < 0.:
                    val[i] = 0.
            return val ** 0.5

        X = np.linspace(sigma_3, sigma_1, 1000)
        Y = Round(X, sigma_3, sigma_1)

        return X, Y

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""
        path = BytesIO()
        size = self.figure.get_size_inches()
        self.figure.set_size_inches([7.5, 3.75])
        self.figure.savefig(path, format='svg', transparent=True)
        path.seek(0)
        self.figure.set_size_inches(size)
        self.canvas.draw()
        return path

class CyclicLoadingOpenTestUI(QWidget):
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

class ModelTriaxialCyclicLoading_Sliders(QWidget):
    """Виджет с ползунками для регулирования значений переменных.
    При перемещении ползунков отправляет 3 сигнала."""
    strain_signal = pyqtSignal(object)
    PPR_signal = pyqtSignal(object)
    cycles_count_signal = pyqtSignal(object)

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._strain_params = {"strain_max": "Асимптота",
                              "strain_slant": "Наклон",
                              "strain_E0": "E0 (Обратн. ампл.)",
                              "strain_rise_after_fail": "Рост после разрушения",
                              "strain_stabilization": "Стабилизация",
                              "strain_phase_offset": "Смещение по фазе",
                              # "strain_deviation": "None",
                              # "strain_filter": "None",
                              }

        self._PPR_params = {"PPR_n_fail": "Разрушение",
                           "PPR_max": "Асимптота",
                           "PPR_slant": "Наклон",
                           "PPR_skempton": "Амплитуда(скемптон)",
                           "PPR_rise_after_fail": "Рост после разрушения",
                           "PPR_phase_offset": "Смещение по фазе",
                           # "PPR_deviation": None,
                           # "PPR_filter": None,
                           }

        self._cycles_count_params = {"cycles_count": "Число циклов"}

        self._max_cycles = None

        self._activate = False

        self._createUI()

    def _create_UI_by_params(self, name, params):
        # Создадим групповой элемент и его layout
        setattr(self, "{}_box".format(name), QGroupBox(name))
        box = getattr(self, "{}_box".format(name))
        setattr(self, "{}_box_layout".format(name), QVBoxLayout())
        box_layout = getattr(self, "{}_box_layout".format(name))

        # Создадим рамку под слайдеры и ее layout
        setattr(self, "{}_frame".format(name), QFrame())
        sliders_frame = getattr(self, "{}_frame".format(name))
        sliders_frame.setFixedHeight(len(params)*25 if len(params)>1 else 50)
        sliders_frame.setFrameShape(QFrame.StyledPanel)
        setattr(self, "{}_frame_layout".format(name), QVBoxLayout())
        sliders_frame_layout = getattr(self, "{}_frame_layout".format(name))

        box_layout.addWidget(sliders_frame)

        for var in params:
            if params[var]:
                # Создадим подпись слайдера
                label = QLabel(params[var])  # Создааем подпись
                label.setFixedWidth(150)  # Фиксируем размер подписи

                # Создадим слайдер
                setattr(self, "{name_var}_slider".format(name_var=var),
                        Float_Slider(Qt.Horizontal))
                slider = getattr(self, "{name_var}_slider".format(name_var=var))

                # Создадим строку со значнием
                setattr(self, "{name_var}_label".format(name_var=var), QLabel())
                slider_label = getattr(self, "{name_var}_label".format(name_var=var))
                slider_label.setFixedWidth(40)
                #slider_label.setStyleSheet(style)

                # Создадтм строку для размещения
                setattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var), QHBoxLayout())
                line = getattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var))

                # СРазместим слайдер и подпись на строке
                line.addWidget(label)
                line.addWidget(slider)
                line.addWidget(slider_label)
                sliders_frame_layout.addLayout(line)
                func = getattr(self, "_{name_widget}_sliders_moove".format(name_widget=name, name_var=var))
                slider.sliderMoved.connect(func)
                release = getattr(self, "_{name_widget}_sliders_released".format(name_widget=name, name_var=var))
                slider.sliderReleased.connect(release)
                slider.setStyleSheet(style)
            else:
                label = QLabel(params[var])  # Создааем подпись
                label.setFixedWidth(150)  # Фиксируем размер подписи
                setattr(self, "{name_widget}_{name_var}_empty".format(name_widget=name,
                                                                      name_var=var), QHBoxLayout())
                line = getattr(self, "{name_widget}_{name_var}_empty".format(name_widget=name,
                                                                             name_var=var))
                line.addWidget(label)
                sliders_frame_layout.addLayout(line)



        sliders_frame.setLayout(sliders_frame_layout)
        box.setLayout(box_layout)

    def _createUI(self):
        self.layout = QGridLayout(self)
        self._create_UI_by_params("strain", self._strain_params)
        self.layout.addWidget(self.strain_box, 0, 0, alignment=Qt.AlignTop)
        self._create_UI_by_params("PPR", self._PPR_params)
        self.layout.addWidget(self.PPR_box, 0, 1, alignment=Qt.AlignTop)
        self._create_UI_by_params("cycles_count", self._cycles_count_params)
        self.layout.addWidget(self.cycles_count_box, 0, 2, alignment=Qt.AlignTop)

        self.csr_button = QPushButton("Потенциал разжижения")
        self.csr_button.setFixedHeight(30)
        self.cycles_count_box_layout.addWidget(self.csr_button)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self._set_slider_labels_params(self._get_slider_params(self._strain_params))
        self._set_slider_labels_params(self._get_slider_params(self._PPR_params))
        self._set_slider_labels_params(self._get_slider_params(self._cycles_count_params))

    def _get_slider_params(self, params):
        """Получение по ключам значения со всех слайдеров"""
        return_params = {}
        for key in params:
            slider = getattr(self, "{}_slider".format(key))
            return_params[key] = slider.current_value()
        return return_params

    def _set_slider_labels_params(self, params):
        """Установка по ключам текстовых полей значений слайдеров"""
        for key in params:
            label = getattr(self, "{}_label".format(key))
            label.setText(str(params[key]))

    def _strain_sliders_moove(self):
        """Обработка перемещения слайдеров деформации"""
        if self._activate:
            self._check_fail()
            params = self._get_slider_params(self._strain_params)
            self._set_slider_labels_params(params)

    def _PPR_sliders_moove(self):
        """Обработка перемещения слайдеров PPR"""
        if self._activate:
            self._check_fail()
            params = self._get_slider_params(self._PPR_params)
            self._set_slider_labels_params(params)

    def _strain_sliders_released(self):
        """Обработка окончания перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params(self._strain_params)
            self._set_slider_labels_params(params)
            self.strain_signal.emit(params)

    def _PPR_sliders_released(self):
        """Обработка окончания перемещения слайдеров PPR"""
        if self._activate:
            self._check_fail()
            params = self._get_slider_params(self._PPR_params)
            self._set_slider_labels_params(params)
            self.PPR_signal.emit(params)

    def _cycles_count_sliders_moove(self):
        if self._activate:
            params = self._get_slider_params(self._cycles_count_params)
            self._set_slider_labels_params(params)

    def _cycles_count_sliders_released(self):
        if self._activate:
            params = self._get_slider_params(self._cycles_count_params)
            self._set_slider_labels_params(params)
            self.cycles_count_signal.emit(params)

    def _check_fail(self):
        """Отключает слайдеры в случае разрушения"""
        if self.PPR_n_fail_slider.current_value() >= self._max_cycles:
            self.strain_rise_after_fail_slider.setDisabled(True)
            self.PPR_rise_after_fail_slider.setDisabled(True)
            self.PPR_max_slider.setDisabled(False)
            self.PPR_slant_slider.setDisabled(False)
        else:
            self.strain_rise_after_fail_slider.setDisabled(False)
            self.PPR_rise_after_fail_slider.setDisabled(False)
            self.PPR_max_slider.setDisabled(True)
            self.PPR_slant_slider.setDisabled(True)

    def set_sliders_params(self, strain_params, PPR_params, cycles_count_params, change_cycles_count=False):
        """становка заданых значений на слайдеры"""
        if change_cycles_count:
            self._max_cycles = cycles_count_params["cycles_count"]["value"]
        else:
            for var in cycles_count_params:
                current_slider = getattr(self, "{name_var}_slider".format(name_var=var))
                current_slider.set_borders(*cycles_count_params[var]["borders"])
                current_slider.set_value(cycles_count_params[var]["value"])

            self._max_cycles = cycles_count_params["cycles_count"]["value"]

        for var in strain_params:
            current_slider = getattr(self, "{name_var}_slider".format(name_var=var))
            current_slider.set_borders(*strain_params[var]["borders"])
            current_slider.set_value(strain_params[var]["value"])

        for var in PPR_params:

            if var == "PPR_n_fail":
                self.PPR_n_fail_slider.set_borders(0, cycles_count_params["cycles_count"]["value"])
                if PPR_params["PPR_n_fail"] is None:
                    self.PPR_n_fail_slider.set_value(cycles_count_params["cycles_count"]["value"])
                else:
                    if PPR_params["PPR_n_fail"] == 0:
                        PPR_params["PPR_n_fail"] = 1
                    self.PPR_n_fail_slider.set_value(PPR_params["PPR_n_fail"])
            else:
                current_slider = getattr(self, "{name_var}_slider".format(name_var=var))
                current_slider.set_borders(*PPR_params[var]["borders"])
                current_slider.set_value(PPR_params[var]["value"])


        self._activate = True

        self._strain_sliders_moove()
        self._PPR_sliders_moove()
        self._set_slider_labels_params(self._get_slider_params(self._cycles_count_params))

class CyclicLoadingUISoilTest(CyclicLoadingUI):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self.graph_layout.removeWidget(self.deviator_canvas_frame)
        self.deviator_canvas_frame.deleteLater()
        self.deviator_canvas_frame = None
        self.sliders_widget = ModelTriaxialCyclicLoading_Sliders()
        self.graph_layout.addWidget(self.sliders_widget)

class CSRResultTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self._clear_table()

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        while (self.rowCount() > 0):
            self.removeRow(0)
        self.verticalHeader().hide()
        self.setRowCount(1)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["α", "β"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def set_data(self, alpha, betta):
        """Получение данных, Заполнение таблицы параметрами"""
        self._clear_table()

        replaceNone = lambda x: x if x != "None" else "-"

        self.setItem(0, 0, QTableWidgetItem(replaceNone(str(alpha))))
        self.setItem(0, 1, QTableWidgetItem(replaceNone(str(betta))))

class CsrItemUI(QGroupBox):
    def __init__(self, EGE: str, model, parent=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        self.model = model

        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.18, "wspace": 0.12, "hspace": 0.07, "left": 0.12}
        self.setTitle(f"ИГЭ: {EGE}")
        self.EGE = EGE
        self._create_UI()

        self.CSR_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.CSR_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.CSR_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.CSR_log_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.CSR_log_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.CSR_log_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.point_identificator = None

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()

        self.layout_graph = QHBoxLayout()

        self.widgets_line = QHBoxLayout()

        self.CSR_frame = QFrame()
        self.CSR_frame.setFrameShape(QFrame.StyledPanel)
        self.CSR_frame.setStyleSheet('background: #ffffff')
        self.CSR_frame_layout = QVBoxLayout()
        self.CSR_figure = plt.figure()
        self.CSR_figure.subplots_adjust(**self.plot_params)
        self.CSR_canvas = FigureCanvas(self.CSR_figure)
        self.CSR_ax = self.CSR_figure.add_subplot(111)
        self.CSR_ax.grid(axis='both', linewidth='0.4')
        self.CSR_ax.set_xlabel("Число циклов N, ед.")
        self.CSR_ax.set_ylabel("Cyclic Stress Ratio, д.е.")
        self.CSR_canvas.draw()
        self.CSR_frame_layout.setSpacing(0)
        self.CSR_frame_layout.addWidget(self.CSR_canvas)
        self.CSR_toolbar = NavigationToolbar(self.CSR_canvas, self)
        self.CSR_frame_layout.addWidget(self.CSR_toolbar)
        self.CSR_frame.setLayout(self.CSR_frame_layout)

        self.CSR_log_frame = QFrame()
        self.CSR_log_frame.setFrameShape(QFrame.StyledPanel)
        self.CSR_log_frame.setStyleSheet('background: #ffffff')
        self.CSR_log_frame_layout = QVBoxLayout()
        self.CSR_log_figure = plt.figure()
        self.CSR_log_figure.subplots_adjust(**self.plot_params)
        self.CSR_log_canvas = FigureCanvas(self.CSR_log_figure)
        self.CSR_log_ax = self.CSR_log_figure.add_subplot(111)
        self.CSR_log_ax.grid(axis='both', linewidth='0.4')
        self.CSR_log_ax.set_xscale('log')
        self.CSR_log_ax.set_xlabel("Число циклов N, ед.")
        self.CSR_log_ax.set_ylabel("Cyclic Stress Ratio, д.е.")
        self.CSR_log_canvas.draw()
        self.CSR_log_frame_layout.setSpacing(0)
        self.CSR_log_frame_layout.addWidget(self.CSR_log_canvas)
        self.CSR_log_toolbar = NavigationToolbar(self.CSR_log_canvas, self)
        self.CSR_log_frame_layout.addWidget(self.CSR_log_toolbar)
        self.CSR_log_frame.setLayout(self.CSR_log_frame_layout)

        self.layout_graph.addLayout(self.widgets_line)
        self.layout_graph.addWidget(self.CSR_frame)
        self.layout_graph.addWidget(self.CSR_log_frame)

        self.layout.addLayout(self.layout_graph)

        self.res_table = CSRResultTable()
        self.res_table.setFixedHeight(50)
        self.layout.addWidget(self.res_table)

        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plot_data=None):
        """Построение графиков опыта"""
        self.CSR_ax.clear()
        self.CSR_log_ax.clear()

        self.CSR_ax.set_xlabel("Число циклов N, ед.")
        self.CSR_ax.set_ylabel("Cyclic Stress Ratio, д.е.")

        self.CSR_log_ax.set_xlabel("Число циклов N, ед.")
        self.CSR_log_ax.set_ylabel("Cyclic Stress Ratio, д.е.")
        self.CSR_log_ax.set_xscale('log')

        results = self.model[self.EGE].get_results()
        if not plot_data:
            plot_data = self.model[self.EGE].get_plot_data()

        self.CSR_ax.plot(plot_data['cycles_linspase_array'], plot_data['CSR_linspase_array'],
                         **plotter_params["main_line"])
        self.CSR_log_ax.plot(plot_data['cycles_linspase_array'], plot_data['CSR_linspase_array'],
                             **plotter_params["main_line"])

        self.CSR_log_ax.scatter([], [])
        self.CSR_ax.scatter([], [])

        for i in range(len(plot_data['cycles_array'])):
            self.CSR_log_ax.scatter(plot_data['cycles_array'][i], plot_data['CSR_array'][i],
                                    label=plot_data['tests'][i])
            self.CSR_ax.scatter(plot_data['cycles_array'][i], plot_data['CSR_array'][i],
                                label=plot_data['tests'][i])
        self.CSR_ax.legend()
        self.CSR_log_ax.legend()


        self.res_table.set_data(results["alpha"], results["betta"])

        self.CSR_log_canvas.draw()
        self.CSR_canvas.draw()

    def _canvas_click(self, event):
        if event.button == 1 and event.xdata and event.ydata and event.canvas is self.CSR_canvas:
            a = (max(self.model[self.EGE].cycles) / 50) ** 2
            b = (max(self.model[self.EGE].CSR ) / 50) ** 2

            for i in range(len(self.model[self.EGE].fail_tests)):
                if (((float(event.xdata) - self.model[self.EGE].cycles[i]) ** 2) / a) + (((float(event.ydata) - self.model[self.EGE].CSR[i]) ** 2) / b) <= 1:
                    self.point_identificator = self.model[self.EGE].fail_tests[i]

    def _canvas_on_moove(self, event):
        if self.point_identificator and event.xdata and event.ydata and event.button == 1 and event.canvas is self.CSR_canvas:
            plot_data = self.model[self.EGE].get_plot_data()

            plot_data['cycles_array'][plot_data['tests'].index(self.point_identificator)] = float(event.xdata)
            plot_data['CSR_array'][plot_data['tests'].index(self.point_identificator)] = float(event.ydata)

            self.plot(plot_data)

    def _canvas_on_release(self, event):
        if self.point_identificator and event.xdata and event.ydata and event.button == 1 and event.canvas is self.CSR_canvas:
            statment.current_test = self.point_identificator

            statment[self.point_identificator].mechanical_properties.n_fail = int(round(float(event.xdata)))
            statment[self.point_identificator].mechanical_properties.t = round(
                float(event.ydata) * statment[self.point_identificator].mechanical_properties.sigma_1)
            statment[self.point_identificator].mechanical_properties.cycles_count = int(
                statment[self.point_identificator].mechanical_properties.n_fail * 1.1)

            #print(self.point_identificator, print(Cyclic_models.tests.keys()))

            Cyclic_models[self.point_identificator].set_test_params()

            self.point_identificator = None
            self.model[self.EGE].processing()
            self.plot()

    def save_canvas(self, format_="svg"):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, file_type):
            path = BytesIO()
            size = figure.get_size_inches()
            figure.set_size_inches(size_figure)
            if file_type == "svg":
                figure.savefig(path, format='svg', transparent=True)
            elif file_type == "jpg":
                figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
            path.seek(0)
            figure.set_size_inches(size)
            canvas.draw()

            return path

        return {
            'lineral': save(self.CSR_figure, self.CSR_canvas, [6.5, 3.2], "svg"),
            'log': save(self.CSR_log_figure, self.CSR_log_canvas, [6.5, 3.2], "svg"),
        }

class CsrWidget(QGroupBox):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self._create_UI()
        self.plot()
        self.setMinimumHeight(800)
        self.setMinimumWidth(800)

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout_widget = QVBoxLayout()

        for EGE in self.model:
            setattr(self, f"CSR_{EGE}", CsrItemUI(EGE, self.model, parent=self))
            widget = getattr(self, f"CSR_{EGE}")
            widget.setFixedHeight(400)
            self.layout_widget.addWidget(widget)

        self.widget = QWidget()
        self.widget.setLayout(self.layout_widget)
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setWidget(self.widget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.area)

        self.save_button = QPushButton("Сохранить отчет")
        self.save_button.setFixedHeight(50)
        self.save_button.clicked.connect(self.save_report)
        self.layout.addWidget(self.save_button)

    def replot(self):
        widget = getattr(self, f"CSR_{statment[statment.current_test].physical_properties.ige}")
        widget.model.processing()
        widget.plot()

    def plot(self):
        """Построение графиков опыта"""
        for EGE in self.model:
            widget = getattr(self, f"CSR_{EGE}")
            widget.plot()

    def save_report(self):
        try:
            customer_name = ''.join(list(filter(lambda c: c not in '''«»\/:*?"'<>|''', statment.general_data.customer)))
            file_name = f"{statment.save_dir.directory}/{customer_name} - {statment.general_data.object_number} - {statment.general_data.object_short_name} - Сводная ведомость {'Потенциал разжижения'}{statment.general_data.get_shipment_number()}.pdf"

            data_customer = statment.general_data
            result = {}

            qr = request_ege_qr(test_type='Потенциал разжижения', laboratory_number=', '.join(self.model.EGES.keys()))

            for EGE in self.model:
                widget = getattr(self, f"CSR_{EGE}")
                result[EGE] = {
                    **self.model[EGE].get_results(),
                    **widget.save_canvas()
                }
            report_liquid_potential(
                file_name, data_customer, os.getcwd() + "/project_data/", result,
                version="{:.2f}".format(__version__), qr_code=qr
            )

            QMessageBox.about(self, "Сообщение", f"Отчет успешно сохранен: {file_name}")
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicLoadingUISoilTest()
    ex.show()
    sys.exit(app.exec_())
