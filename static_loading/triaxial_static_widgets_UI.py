"""Модуль графического интерфейса моделей
    """
__version__ = 1

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
from general.general_functions import read_json_file

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class ModelTriaxialDeviatorLoadingUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.12}
        #self.plot_params_dev = {"right": 0.88, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.12}
        #self.plot_params_epsV = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.15}
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox("Девиаторное нагружение")
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

        # Выбор валюмометра
        self.chose_volumometer = QGroupBox("Волюмометр")
        self.chose_volumometer_radio_button_1 = QRadioButton('pore_volume')
        self.chose_volumometer_radio_button_2 = QRadioButton('cell_volume')
        self.chose_volumometer_radio_button_1.setChecked(True)

        self.chose_volumometer_button_group = QButtonGroup()
        self.chose_volumometer_button_group.addButton(self.chose_volumometer_radio_button_1)
        self.chose_volumometer_button_group.addButton(self.chose_volumometer_radio_button_2)
        #self.chose_volumometer_button_group.buttonClicked.connect(self.radio_button_clicked)

        self.chose_volumometer_layout = QHBoxLayout()
        self.chose_volumometer_layout.addWidget(self.chose_volumometer_radio_button_1)
        self.chose_volumometer_layout.addWidget(self.chose_volumometer_radio_button_2)
        self.chose_volumometer.setLayout(self.chose_volumometer_layout)

        self.widgets_line.addWidget(self.slider_cut_frame)
        self.widgets_line.addWidget(self.chose_volumometer)


        self.graph_canvas_layout = QHBoxLayout()

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

        self.deviator_ax2 = self.deviator_figure.add_axes([0.62, 0.3, .35, .35])
        self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', кПА", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        self.deviator_canvas.draw()
        self.deviator_frame_layout.setSpacing(0)
        self.deviator_frame_layout.addWidget(self.deviator_canvas)
        self.deviator_toolbar = NavigationToolbar(self.deviator_canvas, self)
        self.deviator_frame_layout.addWidget(self.deviator_toolbar)
        self.deviator_frame.setLayout(self.deviator_frame_layout)

        self.volume_strain_frame = QFrame()
        self.volume_strain_frame.setFrameShape(QFrame.StyledPanel)
        self.volume_strain_frame.setStyleSheet('background: #ffffff')
        self.volume_strain_frame_layout = QVBoxLayout()
        self.volume_strain_figure = plt.figure()
        self.volume_strain_figure.subplots_adjust(**self.plot_params)
        self.volume_strain_canvas = FigureCanvas(self.volume_strain_figure)
        self.volume_strain_ax = self.volume_strain_figure.add_subplot(111)
        self.volume_strain_ax.grid(axis='both', linewidth='0.4')
        self.volume_strain_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.volume_strain_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")
        self.volume_strain_canvas.draw()
        self.volume_strain_frame_layout.setSpacing(0)
        self.volume_strain_frame_layout.addWidget(self.volume_strain_canvas)
        self.volume_strain_toolbar = NavigationToolbar(self.volume_strain_canvas, self)
        self.volume_strain_frame_layout.addWidget(self.volume_strain_toolbar)
        self.volume_strain_frame.setLayout(self.volume_strain_frame_layout)

        self.graph_layout.addLayout(self.widgets_line)
        self.graph_canvas_layout.addWidget(self.deviator_frame)
        self.graph_canvas_layout.addWidget(self.volume_strain_frame)

        self.graph_layout.addLayout(self.graph_canvas_layout)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, res):
        """Построение графиков опыта"""
        try:
            self.deviator_ax.clear()
            self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
            self.deviator_ax.set_ylabel("Девиатор q, кПа")

            self.volume_strain_ax.clear()
            self.volume_strain_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
            self.volume_strain_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

            self.deviator_ax2.clear()

            if plots["strain"] is not None:
                self.deviator_ax.plot(plots["strain"], plots["deviator"],
                                      **plotter_params["static_loading_main_line"])

                self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"],
                                      **plotter_params["static_loading_gray_line"])

                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])

                self.deviator_ax.plot(*plots["E50"],
                                      label=_label,
                                      **plotter_params["static_loading_black_dotted_line"])

                if plots["Eur"]:
                    #self.deviator_ax.plot(*plots["Eur"], **plotter_params["static_loading_red_dotted_line"],
                                          #label="$E_{ur}$" + ", MПа = " + str(res["Eur"]))
                    self.deviator_ax2.set_ylabel("Девиатор q, кПа", fontsize=8)
                    self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

                    self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                           **plotter_params["static_loading_main_line"])
                    self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])
                    # label="$E$" + ", MПа = " + str(res["E"][0]) + "\n" + "$E$" + ", MПа = " + str(res["E"][0]))
                    plt.xticks(fontsize=8)
                    plt.yticks(fontsize=8)

                else:
                    self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', кПa", fontsize=8)
                    self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

                    #lim = self.deviator_ax.get_xlim()
                    #self.deviator_ax2.set_xlim([lim[0], lim[1]])

                    self.deviator_ax2.plot(plots["strain"], plots["deviator"] + plots["sigma_3"],
                                      **plotter_params["static_loading_main_line"])

                    self.deviator_ax2.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"],
                                      **plotter_params["static_loading_red_dotted_line"])
                                      #label="$E$" + ", MПа = " + str(res["E"][0]) + "\n" + "$E$" + ", MПа = " + str(res["E"][0]))
                    plt.xticks(fontsize=8)
                    plt.yticks(fontsize=8)
                    #self.deviator_ax2.set_xticklabels(self.deviator_ax2.get_xticks(), size=8)
                    #self.deviator_ax2.set_yticklabels(self.deviator_ax2.get_yticks(), size=8)

                #self.deviator_ax.plot([], [], label="$E_{50}$" + ", MПа = " + str(res["E50"]), color="#eeeeee")
                #self.deviator_ax.plot([], [], label="$E$" + ", MПа = " + str(res["E"][0]), color="#eeeeee")

                self.volume_strain_ax.plot(plots["strain"], plots["volume_strain"], **plotter_params["static_loading_main_line"])
                self.volume_strain_ax.plot(plots["strain"], plots["volume_strain_approximate"],
                                      **plotter_params["static_loading_red_dotted_line"])
                if plots["dilatancy"]:
                    self.volume_strain_ax.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"],
                                          **plotter_params["static_loading_black_dotted_line"])

                self.volume_strain_ax.set_xlim(self.deviator_ax.get_xlim())

                self.volume_strain_ax.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                      color="#eeeeee")
                if res["dilatancy_angle"] is not None:
                    self.volume_strain_ax.plot([], [],
                                          label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                          color="#eeeeee")

                self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.75))
                self.volume_strain_ax.legend()

            self.deviator_canvas.draw()
            self.volume_strain_canvas.draw()

        except:
            pass

    def save_canvas(self, format=["svg", "svg"], size=[[6, 2], [6, 2]]):
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
            ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.75))

            canvas.draw()
            return path

        return [save(fig, can, size, ax, _format) for fig, can, size, ax, _format in zip([self.deviator_figure,
                                                                            self.volume_strain_figure],
                                                   [self.deviator_canvas, self.volume_strain_canvas], size,
                                                                              [self.deviator_ax, self.volume_strain_ax],
                                                                                         format)]

class ModelTriaxialConsolidationUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.12}

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

        # Выбор валюмометра
        self.chose_volumometer = QGroupBox("Волюмометр")
        self.chose_volumometer_radio_button_1 = QRadioButton('pore_volume')
        self.chose_volumometer_radio_button_2 = QRadioButton('cell_volume')
        self.chose_volumometer_radio_button_1.setChecked(True)

        self.chose_volumometer_button_group = QButtonGroup()
        self.chose_volumometer_button_group.addButton(self.chose_volumometer_radio_button_1)
        self.chose_volumometer_button_group.addButton(self.chose_volumometer_radio_button_2)
        #self.chose_volumometer_button_group.buttonClicked.connect(self.radio_button_clicked)

        self.chose_volumometer_layout = QHBoxLayout()
        self.chose_volumometer_layout.addWidget(self.chose_volumometer_radio_button_1)
        self.chose_volumometer_layout.addWidget(self.chose_volumometer_radio_button_2)
        self.chose_volumometer.setLayout(self.chose_volumometer_layout)

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
        self.function_replacement_slider.set_value(2)
        #self.function_replacement_slider.sliderMoved.connect(self.function_replacement_slider_move)
        #self.function_replacement_slider.sliderReleased.connect(self.function_replacement_slider_release)

        self.function_replacement_line2.addWidget(self.function_replacement_label)
        self.function_replacement_line2.addWidget(self.function_replacement_slider)

        self.function_replacement_layuot.addLayout(self.function_replacement_line1)
        self.function_replacement_layuot.addLayout(self.function_replacement_line2)

        self.function_replacement.setLayout(self.function_replacement_layuot)

        self.widgets_line.addWidget(self.slider_cut_frame)
        self.widgets_line.addWidget(self.chose_volumometer)
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
        self.sqrt_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")
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
        self.log_ax.grid(axis='both', linewidth='0.4')
        self.log_ax.set_xlabel("Время")
        self.log_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")
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
            self.sqrt_ax.set_xlabel("Время")
            self.sqrt_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

            if plots is not None:
                # Квадратный корень
                # Основной график
                self.sqrt_ax.plot(plots["time_sqrt"], plots["volume_strain_approximate"], **plotter_params["static_loading_main_line"])
                # Точки концов линий
                self.sqrt_ax.scatter(*plots["sqrt_line_points"].line_start_point, zorder=5, color="dimgray")
                self.sqrt_ax.scatter(*plots["sqrt_line_points"].line_end_point, zorder=5, color="dimgray")

                # Линии обработки
                if plots["sqrt_line_points"].line_start_point and plots["sqrt_line_points"].line_end_point:
                    # Основные линии обработки
                    self.sqrt_ax.plot(*point_to_xy(plots["sqrt_line_points"].line_start_point,
                                              plots["sqrt_line_points"].line_end_point),
                                 **plotter_params["static_loading_sandybrown_line"])

                if plots["sqrt_line_points"].Cv:
                    self.sqrt_ax.plot(
                        *point_to_xy(plots["sqrt_line_points"].line_start_point, plots["sqrt_line_points"].Cv),
                        **plotter_params["static_loading_sandybrown_line"])

                    # Точки обработки
                    self.sqrt_ax.scatter(*plots["sqrt_line_points"].Cv, zorder=5, color="tomato")

                    # Пунктирные линии
                    self.sqrt_ax.plot(*plots["sqrt_t90_vertical_line"],
                                      **plotter_params["static_loading_black_dotted_line"])
                    self.sqrt_ax.plot(*plots["sqrt_t90_horizontal_line"],
                                      **plotter_params["static_loading_black_dotted_line"])

                    if plots["sqrt_t100_vertical_line"]:
                        self.sqrt_ax.plot(*plots["sqrt_t100_vertical_line"],
                                          **plotter_params["static_loading_black_dotted_line"])
                        self.sqrt_ax.plot(*plots["sqrt_t100_horizontal_line"],
                                          **plotter_params["static_loading_black_dotted_line"])
                        self.sqrt_ax.plot(*plots["sqrt_t50_vertical_line"],
                                          **plotter_params["static_loading_black_dotted_line"])
                        self.sqrt_ax.plot(*plots["sqrt_t50_horizontal_line"],
                                          **plotter_params["static_loading_black_dotted_line"])

                    # Текстовые подписи
                    self.sqrt_ax.text(*plots["sqrt_t90_text"], '$\sqrt{t_{90}}$', horizontalalignment='center',
                                 verticalalignment='bottom')
                    self.sqrt_ax.text(*plots["sqrt_strain90_text"], '$ε_{90}$', horizontalalignment='right',
                                 verticalalignment='center')
                    if plots["sqrt_t100_text"]:
                        self.sqrt_ax.text(*plots["sqrt_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                     verticalalignment='bottom')
                        self.sqrt_ax.text(*plots["sqrt_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                     verticalalignment='center')
                        self.sqrt_ax.text(*plots["sqrt_t50_text"], '$\sqrt{t_{50}}$', horizontalalignment='center',
                                          verticalalignment='bottom')
                        self.sqrt_ax.text(*plots["sqrt_strain50_text"], '$ε_{50}$', horizontalalignment='right',
                                          verticalalignment='center')

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
            self.log_ax.set_xlabel("Время")
            self.log_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

            if plots is not None:
                # Логарифм
                # Основной график
                self.log_ax.plot(plots["time_log"], plots["volume_strain_approximate"], **plotter_params["static_loading_main_line"])

                # Линии обработки
                if plots["log_line_points"]:
                    # Основные линии обработки
                    self.log_ax.plot(*point_to_xy(plots["log_line_points"].first_line_start_point,
                                             plots["log_line_points"].first_line_end_point),
                                **plotter_params["static_loading_sandybrown_line"])
                    self.log_ax.plot(*point_to_xy(plots["log_line_points"].second_line_start_point,
                                             plots["log_line_points"].second_line_end_point),
                                **plotter_params["static_loading_sandybrown_line"])

                    # Точки концов линий
                    self.log_ax.scatter(*plots["log_line_points"].first_line_start_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].first_line_end_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].second_line_start_point, zorder=5, color="dimgray")
                    self.log_ax.scatter(*plots["log_line_points"].second_line_end_point, zorder=5, color="dimgray")

                    # Точки обработки
                    if plots["log_line_points"].Cv:
                        self.log_ax.scatter(*plots["log_line_points"].Cv, zorder=5, color="tomato")
                        self.log_ax.scatter(*plots["d0"], zorder=5, color="tomato")

                        # Пунктирные линии
                        self.log_ax.plot(*plots["log_t100_vertical_line"],
                                         **plotter_params["static_loading_black_dotted_line"])
                        self.log_ax.plot(*plots["log_t100_horizontal_line"],
                                         **plotter_params["static_loading_black_dotted_line"])

                        # Текстовые подписи
                        self.log_ax.text(*plots["log_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                    verticalalignment='bottom')
                        self.log_ax.text(*plots["log_strain100_text"], '$ε_{100}$', horizontalalignment='right',
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
                                                   [self.sqrt_canvas, self.log_canvas], [[3, 3], [3, 3]],
                                                                              [self.sqrt_ax, self.log_ax])]

class ModelTriaxialReconsolidationUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.22, "wspace": 0.12, "hspace": 0.07, "left": 0.12}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QHBoxLayout()
        self.graph = QGroupBox("Реконсолидация")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        #self.result_table = Table()
        #self.result_table.setFixedHeight(70)
        #self.graph_layout.addWidget(self.result_table)
        #self.result_table.set_data([[self._result_params[key] for key in self._result_params],
                                    #["" for _ in self._result_params]], resize="Stretch")

        self.graph_canvas_layout = QHBoxLayout()

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setStyleSheet('background: #ffffff')
        self.frame_layout = QVBoxLayout()
        self.figure = plt.figure()
        self.figure.subplots_adjust(**self.plot_params)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.grid(axis='both', linewidth='0.4')
        self.ax.set_xlabel("Давление в камере, кПа")
        self.ax.set_ylabel("Поровое давление, кПа")
        self.canvas.draw()
        self.frame_layout.setSpacing(0)
        self.frame_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.frame_layout.addWidget(self.toolbar)
        self.frame.setLayout(self.frame_layout)

        self.graph_canvas_layout.addWidget(self.frame)

        self.graph_layout.addLayout(self.graph_canvas_layout)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, res):
        """Построение графиков опыта"""
        try:
            self.ax.clear()
            self.ax.set_xlabel("Давление в камере, кПа")
            self.ax.set_ylabel("Поровое давление, кПа")

            if plots:
                self.ax.plot(plots["cell_pressure"], plots["pore_pressure"], **plotter_params["static_loading_main_line"])
                self.ax.plot([], [], label="Scempton ratio = " + str(res["scempton"]),
                        color="#eeeeee")
                self.ax.legend()
            self.canvas.draw()

        except:
            pass

    def save_canvas(self):
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

        return save(self.figure, self.canvas, [6, 4], "svg")

class ModelTriaxialFileOpenUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QHBoxLayout(self)
        self.box = QGroupBox("Открытие файла испытания")
        self.box_layout = QHBoxLayout()
        self.box.setLayout(self.box_layout)

        self.open_button = QPushButton("Выбрать файл опыта")
        self.open_button.setFixedWidth(130)
        self.file_path_line = QLineEdit()
        self.file_path_line.setDisabled(True)

        self.box_layout.addWidget(self.open_button)
        self.box_layout.addWidget(self.file_path_line)

        self.layout.addWidget(self.box)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_path(self, path):
        self.file_path_line.setText(path)

class ModelTriaxialItemUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        super().__init__()
        self._create_UI()

    def _create_UI(self):
        self.layout = QVBoxLayout(self)

        self.box = QGroupBox("Идентификация пробы")
        self.box_layout = QVBoxLayout()
        self.box.setLayout(self.box_layout)

        self.box_layout_1 = QHBoxLayout()
        self.box_layout_2 = QHBoxLayout()
        self.box_layout_3 = QHBoxLayout()
        self.box_layout_4 = QHBoxLayout()

        self.lab = QLineEdit()
        self.lab.setDisabled(True)
        self.lab.setFixedWidth(300)
        self.borehole = QLineEdit()
        self.borehole.setDisabled(True)
        self.borehole.setFixedWidth(300)
        self.depth = QLineEdit()
        self.depth.setDisabled(True)
        self.depth.setFixedWidth(300)
        self.name = QTextEdit()
        self.name.setDisabled(True)
        self.name.setFixedWidth(300)

        text_1 = QLabel("Лаб. номер: ")
        text_1.setFixedWidth(80)
        text_2 = QLabel("Скважина: ")
        text_2.setFixedWidth(80)
        text_3 = QLabel("Глубина: ")
        text_3.setFixedWidth(80)
        text_4 = QLabel("Наименование: ")
        text_4.setFixedWidth(80)


        self.box_layout_1.addWidget(text_1)
        self.box_layout_2.addWidget(text_2)
        self.box_layout_3.addWidget(text_3)
        self.box_layout_4.addWidget(text_4)

        self.box_layout_1.addWidget(self.lab)
        self.box_layout_2.addWidget(self.borehole)
        self.box_layout_3.addWidget(self.depth)
        self.box_layout_4.addWidget(self.name)

        self.box_layout.addLayout(self.box_layout_1)
        self.box_layout.addLayout(self.box_layout_2)
        self.box_layout.addLayout(self.box_layout_3)
        self.box_layout.addLayout(self.box_layout_4)
        self.box_layout.addStretch(-1)

        self.layout.setContentsMargins(5, 5, 5, 5)

        self.layout.addWidget(self.box)

    def set_data(self, data):
        self.lab.setText(str(data["lab_number"]))
        self.borehole.setText(str(data["data_phiz"]["borehole"]))
        self.depth.setText(str(data["data_phiz"]["depth"]))
        self.name.setText(str(data["data_phiz"]["name"]))
