"""Модуль графического интерфейса моделей
    """
from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import os
from io import BytesIO

from general.general_widgets import Float_Slider, RangeSlider
from general.general_functions import point_to_xy
from configs.plot_params import plotter_params
import numpy as np


#try:
#    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
#except FileNotFoundError:
#    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class ModelTriaxialConsolidationUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.14}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox("Консолидация")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        #self.result_table = Table()
        #self.result_table.setFixedHeight(70)
        #self.graph_layout.addWidget(self.result_table)
        #self.result_table.set_data([[self._result_params[key] for key in self._result_params],
                                    #["" for _ in self._result_params]], resize="Stretch")

        self.widgets_line = QHBoxLayout()
        # Обрезание функции
        self.slider_cut_frame = QGroupBox("Обрезание функции")
        self.slider_cut_frame_layout = QVBoxLayout()
        self.slider_cut = RangeSlider(Qt.Horizontal)
        #self.slider_cut.sliderMoved.connect(self.slider_cut_move)
        self.slider_cut_frame_layout.addWidget(self.slider_cut)
        self.slider_cut_frame.setLayout(self.slider_cut_frame_layout)

        # Выбор аппроксимации
        self.function_replacement_type = "ermit"
        self.function_replacement = QGroupBox("Замена функции")
        self.function_replacement.setFixedHeight(80)
        self.function_replacement_layuot = QVBoxLayout()
        self.function_replacement_line1 = QHBoxLayout()
        self.function_replacement_line2 = QHBoxLayout()

        self.function_replacement_radio_button_1 = QRadioButton('Интерполяция полиномом')
        self.function_replacement_radio_button_2 = QRadioButton('Интерполяция Эрмита')
        self.function_replacement_radio_button_2.setChecked(True)
        self.function_replacement_button_group = QButtonGroup()
        self.function_replacement_button_group.addButton(self.function_replacement_radio_button_1)
        self.function_replacement_button_group.addButton(self.function_replacement_radio_button_2)
        #self.function_replacement_button_group.buttonClicked.connect(self.function_replacement_button_group_clicked)

        self.function_replacement_line1.addWidget(QLabel("Тип замены:"))
        self.function_replacement_line1.addWidget(self.function_replacement_radio_button_1)
        self.function_replacement_line1.addWidget(self.function_replacement_radio_button_2)

        self.function_replacement_label = QLabel()
        self.function_replacement_slider = Float_Slider(Qt.Horizontal)
        self.function_replacement_label.setText("Степень сглаживания:")
        self.function_replacement_slider.set_borders(0, 5)
        self.function_replacement_slider.set_value(0.5)
        #self.function_replacement_slider.sliderMoved.connect(self.function_replacement_slider_move)
        #self.function_replacement_slider.sliderReleased.connect(self.function_replacement_slider_release)

        self.function_replacement_line2.addWidget(self.function_replacement_label)
        self.function_replacement_line2.addWidget(self.function_replacement_slider)

        self.function_replacement_layuot.addLayout(self.function_replacement_line1)
        self.function_replacement_layuot.addLayout(self.function_replacement_line2)

        self.function_replacement.setLayout(self.function_replacement_layuot)

        self.widgets_line.addWidget(self.slider_cut_frame)
        self.widgets_line.addWidget(self.function_replacement)

        # Графики
        self.graph_canvas_layout = QHBoxLayout()
        self.sqrt_frame = QFrame()
        self.sqrt_frame.setFrameShape(QFrame.StyledPanel)
        self.sqrt_frame.setStyleSheet('background: #ffffff')
        self.sqrt_frame_layout = QVBoxLayout()
        self.sqrt_figure = plt.figure()
        self.sqrt_figure.subplots_adjust(**self.plot_params)
        self.sqrt_canvas = FigureCanvas(self.sqrt_figure)
        self.sqrt_ax = self.sqrt_figure.add_subplot(111)
        self.sqrt_ax.grid(axis='both', linewidth='0.4')
        self.sqrt_ax.set_xlabel("Время")
        self.sqrt_ax.set_ylabel("Относительная вертикальная\nдеформация $ε_1$, д.е.")
        self.sqrt_canvas.draw()
        self.sqrt_frame_layout.setSpacing(0)
        self.sqrt_frame_layout.addWidget(self.sqrt_canvas)
        self.sqrt_toolbar = NavigationToolbar(self.sqrt_canvas, self)
        self.sqrt_frame_layout.addWidget(self.sqrt_toolbar)
        self.sqrt_frame.setLayout(self.sqrt_frame_layout)

        self.log_frame = QFrame()
        self.log_frame.setFrameShape(QFrame.StyledPanel)
        self.log_frame.setStyleSheet('background: #ffffff')
        self.log_frame_layout = QVBoxLayout()
        self.log_figure = plt.figure()
        self.log_figure.subplots_adjust(**self.plot_params)
        self.log_canvas = FigureCanvas(self.log_figure)
        self.log_ax = self.log_figure.add_subplot(111)
        self.log_ax.set_xscale("log")
        self.log_ax.grid(axis='both', linewidth='0.4')
        self.log_ax.set_xlabel("Время")
        self.log_ax.set_ylabel("Относительная вертикальная\nдеформация $ε_1$, д.е.")
        self.log_canvas.draw()
        self.log_frame_layout.setSpacing(0)
        self.log_frame_layout.addWidget(self.log_canvas)
        self.log_toolbar = NavigationToolbar(self.log_canvas, self)
        self.log_frame_layout.addWidget(self.log_toolbar)
        self.log_frame.setLayout(self.log_frame_layout)

        self.graph_canvas_layout.addWidget(self.sqrt_frame)
        self.graph_canvas_layout.addWidget(self.log_frame)

        self.graph_layout.addLayout(self.widgets_line)
        self.graph_layout.addLayout(self.graph_canvas_layout)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot_sqrt(self, plots, res):
        """Построение графиков опыта"""
        try:
            self.sqrt_ax.clear()
            self.sqrt_ax.set_xlabel("Квадратный корень из времени, $\sqrt{мин}$")
            self.sqrt_ax.set_ylabel("Относительная вертикальная\nдеформация $ε_1$, д.е.")

            if plots is not None:
                """new_tick_locations = np.array([-0.1, plots["time_sqrt"][10], plots["time_sqrt"][20],
                                               plots["time_sqrt"][30], plots["time_sqrt"][40], plots["time_sqrt"][49]])

                def tick_function(x):
                    return np.round(x**2)

                self.sqrt_ax.set_xlim(self.sqrt_ax.get_xlim())
                self.sqrt_ax.set_xticks(new_tick_locations)
                self.sqrt_ax.set_xticklabels(tick_function(new_tick_locations))"""
                # Квадратный корень
                # Основной график
                self.sqrt_ax.plot(plots["time"], plots["volume_strain"], linewidth=2, alpha=0.6)
                self.sqrt_ax.scatter(plots["time"], plots["volume_strain"], s=15)

                self.sqrt_ax.plot(plots["time_sqrt"], plots["volume_strain_approximate"], color="tomato", linewidth=1)
                # Точки концов линий
                self.sqrt_ax.scatter(*plots["sqrt_line_points"].line_start_point, zorder=5, color="dimgray")
                self.sqrt_ax.scatter(*plots["sqrt_line_points"].line_end_point, zorder=5, color="dimgray")

                # Линии обработки
                if plots["sqrt_line_points"].line_start_point and plots["sqrt_line_points"].line_end_point:
                    # Основные линии обработки
                    self.sqrt_ax.plot(*point_to_xy(plots["sqrt_line_points"].line_start_point,
                                              plots["sqrt_line_points"].line_end_point),
                                 **plotter_params["consolidation_sandybrown_line"])

                if plots["sqrt_line_points"].Cv:
                    self.sqrt_ax.plot(
                        *point_to_xy(plots["sqrt_line_points"].line_start_point, plots["sqrt_line_points"].Cv),
                        **plotter_params["consolidation_sandybrown_line"])

                    # Точки обработки
                    self.sqrt_ax.scatter(*plots["sqrt_line_points"].Cv, zorder=5, color="tomato")

                    # Пунктирные линии
                    self.sqrt_ax.plot(*plots["sqrt_t90_vertical_line"],
                                      **plotter_params["consolidation_black_dotted_line"])
                    self.sqrt_ax.plot(*plots["sqrt_t90_horizontal_line"],
                                      **plotter_params["consolidation_black_dotted_line"])

                    #if plots["sqrt_t100_vertical_line"]:
                        #self.sqrt_ax.plot(*plots["sqrt_t100_vertical_line"],
                                          #**plotter_params["static_loading_black_dotted_line"])
                        #self.sqrt_ax.plot(*plots["sqrt_t100_horizontal_line"],
                                          #**plotter_params["static_loading_black_dotted_line"])

                    # Текстовые подписи
                    self.sqrt_ax.text(*plots["sqrt_t90_text"], '$\sqrt{t_{90}}$', horizontalalignment='center',
                                 verticalalignment='bottom')
                    self.sqrt_ax.text(*plots["sqrt_strain90_text"], '$ε_{90}$', horizontalalignment='right',
                                 verticalalignment='center')
                    #if plots["sqrt_t100_text"]:
                        #self.sqrt_ax.text(*plots["sqrt_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                     #verticalalignment='bottom')
                        #self.sqrt_ax.text(*plots["sqrt_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                     #verticalalignment='center')


                    self.sqrt_ax.plot([], [], label="$C_{v}$" + " = " + str(res["Cv_sqrt"]),
                                 color="#eeeeee")
                    self.sqrt_ax.plot([], [], label="$t_{100}$" + " = " + str(round(res["t100_sqrt"])),
                                 color="#eeeeee")
                    self.sqrt_ax.plot([], [], label="$t_{50}$" + " = " + str(round(res["t50_sqrt"], 3)),
                                      color="#eeeeee")
                    self.sqrt_ax.legend()

            self.sqrt_canvas.draw()
        except:
            pass

    def plot_log(self, plots, res):
        """Построение графиков опыта"""
        try:
            self.log_ax.clear()
            self.log_ax.set_xlabel("Время, мин")
            self.log_ax.set_ylabel("Относительная вертикальная\nдеформация $ε_1$, д.е.")

            if plots is not None:

                def define_sticks(x):
                    sticks = []
                    text = []
                    for i, k in zip([1, 10, 100, 1000, 10000, 100000, 1000000],
                                    ["$10^{-1}$", "$10^{0}$", "$10^{1}$", "$10^{2}$", "$10^{3}$", "$10^{4}$",
                                     "$10^{5}$", "$10^{6}$"]):
                        sticks += [i * val for val in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]]
                        text += [k] + ["" for i in range(8)]

                    values = np.hstack((np.log10(sticks)))
                    """values = np.array([1, 10, 100, 1000, 10000, 100000, 1000000])
                    values = np.hstack((np.array([-1, -0.9, -0.8,]), np.log10(values)))
                    text = ["$10^{-1}$", "$10^{0}$", "$10^{1}$", "$10^{2}$", "$10^{3}$", "$10^{4}$",
                            "$10^{5}$", "$10^{6}$"]"""
                    for i in range(len(values)):
                        if values[i] > x:
                            break
                    return values[:i + 1], text[:i + 1]

                new_tick_locations = np.array([-1, plots["time_log"][10], plots["time_log"][20],
                                       plots["time_log"][30], plots["time_log"][40], plots["time_log"][49]])
                #new_tick_locations = np.array([-1, 0, 1, 2])

                # plots["time"][0] = plots["time"][0] + 0.001

                def tick_function(x):
                    # if x == -0.1:
                    #     return 0
                    return np.round(10**x,2)

                #self.log_ax.set_xlim(self.log_ax.get_xlim())
                """self.log_ax.set_xticks(new_tick_locations)
                new_tick_locations[0] = -1 #???????????????
                self.log_ax.set_xticklabels(tick_function(new_tick_locations))"""
                stick, text = define_sticks(plots["time_log"][-1])
                #stick[0] = -1
                self.log_ax.set_xticks(stick)
                self.log_ax.set_xticklabels(text)
                #self.log_ax.set_xticklabels([tick_function(t) for t in new_tick_locations])

                #self.log_ax.set_xticklabels([0.1,1,10,100,1000,10000])

                print(new_tick_locations)

                # Логарифм
                # Основной график

                self.log_ax.plot(np.log10(plots["time"] ), plots["volume_strain"], linewidth=2, alpha=0.6)
                self.log_ax.scatter(np.log10(plots["time"] ), plots["volume_strain"], s=15)

                self.log_ax.plot(plots["time_log"], plots["volume_strain_approximate"], color="tomato", linewidth=1)


                # Линии обработки
                if plots["log_line_points"]:
                    # Основные линии обработки
                    self.log_ax.plot(*point_to_xy(plots["log_line_points"].first_line_start_point,
                                             plots["log_line_points"].first_line_end_point),
                                **plotter_params["consolidation_sandybrown_line"])
                    self.log_ax.plot(*point_to_xy(plots["log_line_points"].second_line_start_point,
                                             plots["log_line_points"].second_line_end_point),
                                **plotter_params["consolidation_sandybrown_line"])

                    # Точки концов линий
                    self.log_ax.scatter(*plots["log_line_points"].first_line_start_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].first_line_end_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].second_line_start_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].second_line_end_point, zorder=5, color="dimgray")

                    # Точки обработки
                    if plots["log_line_points"].Cv:
                        self.log_ax.scatter(*plots["log_line_points"].Cv, zorder=5, color="tomato")
                        #self.log_ax.scatter(*plots["d0"], zorder=5, color="tomato")

                        # Пунктирные линии
                        self.log_ax.plot(*plots["log_t50_vertical_line"],
                                         **plotter_params["consolidation_black_dotted_line"])
                        self.log_ax.plot(*plots["log_t50_horizontal_line"],
                                         **plotter_params["consolidation_black_dotted_line"])

                        self.log_ax.plot(*plots["log_t100_vertical_line"],
                                         **plotter_params["consolidation_black_dotted_line"])
                        self.log_ax.plot(*plots["log_t100_horizontal_line"],
                                         **plotter_params["consolidation_black_dotted_line"])
                        self.log_ax.plot(*plots["d0_line"],
                                         **plotter_params["consolidation_black_dotted_line"])

                        # Текстовые подписи
                        self.log_ax.text(*plots["log_t100_text"], '$t_{100}$', horizontalalignment='center',
                                    verticalalignment='bottom')
                        self.log_ax.text(*plots["log_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                    verticalalignment='center')

                        self.log_ax.text(*plots["log_t50_text"], '$t_{50}$', horizontalalignment='center',
                                         verticalalignment='bottom')
                        self.log_ax.text(*plots["log_strain50_text"], '$ε_{50}$', horizontalalignment='right',
                                         verticalalignment='center')

                        self.log_ax.text(*plots["d0"], '$d_{0}$', horizontalalignment='center',
                                         verticalalignment='center')


                    self.log_ax.plot([], [], label="$C_{v}$" + " = " + str(res["Cv_log"]), color="#eeeeee")
                    self.log_ax.plot([], [], label="$t_{100}$" + " = " + str(res["t100_log"]),
                                color="#eeeeee")
                    self.log_ax.plot([], [], label="$C_{a}$" + " = " + str(res["Ca_log"]), color="#eeeeee")
                    self.log_ax.legend()

            self.sqrt_canvas.draw()
            self.log_canvas.draw()

        except:
            pass

    def plot_interpolate(self, plots):
        try:
            self.sqrt_ax.clear()
            self.sqrt_ax.set_xlabel("Время")
            self.sqrt_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

            self.log_ax.clear()
            self.log_ax.set_xlabel("Время")
            self.log_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

            if plots is not None:
                self.sqrt_ax.plot(plots["time_sqrt_origin"], plots["volume_strain"],
                                  **plotter_params["static_loading_main_line"],
                                  label="Опытные данные")
                self.sqrt_ax.plot(plots["time_sqrt"], plots["volume_strain_approximate"],
                                  **plotter_params["static_loading_red_line"],
                                  label="Аппроксимация")

                self.log_ax.plot(plots["time_log_origin"], plots["volume_strain"],
                                 **plotter_params["static_loading_main_line"],
                                 label="Опытные данные")
                self.log_ax.plot(plots["time_log"], plots["volume_strain_approximate"],
                                 **plotter_params["static_loading_red_line"],
                                 label="Аппроксимация")

                self.sqrt_ax.legend()
                self.log_ax.legend()

            self.sqrt_canvas.draw()
            self.log_canvas.draw()

        except:
            pass

    def save_canvas(self):
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
                    figure.savefig(path, format='jpg', dpi=200, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                ax.legend()
                canvas.draw()
            except AttributeError:
                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=200, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)

            return path

        return [save(fig, can, size, ax, "svg") for fig, can, size, ax in zip([self.sqrt_figure,
                                                                            self.log_figure],
                                                   [self.sqrt_canvas, self.log_canvas], [[6, 2], [6, 2]],
                                                                              [self.sqrt_ax, self.log_ax])]
