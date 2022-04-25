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
from excel_statment.initial_tables import TableVertical
from configs.plot_params import plotter_params
from general.general_functions import read_json_file
from singletons import statment

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class ModelShearDilatancyUI(QWidget):
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

        # self.deviator_ax2 = self.deviator_figure.add_axes([0.62, 0.3, .35, .35])
        # self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', кПА", fontsize=8)
        # self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

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
            self.deviator_ax.set_xlabel("Абсолютная деформация $l_1$, мм")
            self.deviator_ax.set_ylabel("Касательное напряжение τ, МПа")

            self.volume_strain_ax.clear()
            self.volume_strain_ax.set_xlabel("Абсолютная деформация $l_1$, мм")
            self.volume_strain_ax.set_ylabel("Абсолютная \n вертикальная деформация $h_1$, мм")

            # self.deviator_ax2.clear()

            if plots["strain"] is not None:
                self.deviator_ax.plot(plots["strain"], plots["deviator"],
                                      **plotter_params["static_loading_main_line"])

                self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"],
                                      **plotter_params["static_loading_gray_line"])
                self.deviator_ax.scatter(plots["strain"], plots["deviator"], s=50)

                lim = self.deviator_ax.get_xlim()
                self.deviator_ax.set_xlim([lim[0], 7.25])

                self.volume_strain_ax.plot(plots["strain"], plots["volume_strain"], **plotter_params["static_loading_main_line"])
                self.volume_strain_ax.plot(plots["strain"], plots["volume_strain_approximate"],
                                      **plotter_params["static_loading_red_dotted_line"])
                self.volume_strain_ax.scatter(plots["strain"], plots["volume_strain"], s=20)
                if plots["dilatancy"]:
                    self.volume_strain_ax.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"],
                                          **plotter_params["static_loading_black_dotted_line"])

                self.volume_strain_ax.set_xlim([lim[0], 7.25])

                self.volume_strain_ax.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                      color="#eeeeee")
                if res["dilatancy_angle"] is not None:
                    self.volume_strain_ax.plot([], [],
                                          label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                          color="#eeeeee")

                # self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.75))
                self.volume_strain_ax.legend()

            self.deviator_canvas.draw()
            self.volume_strain_canvas.draw()

        except:
            pass

    def save_canvas(self, format=["svg", "svg"], size=[[6, 2], [6, 2]]):
        """Сохранение графиков для передачи в отчет"""
        def save(figure, canvas, size_figure, ax, file_type):

            if ax.get_legend():
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

class ModelShearFileOpenUI(QWidget):
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

class ModelTriaxialItemUIOld(QWidget):
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

    def set_data(self):
        self.lab.setText(str(statment[statment.current_test].physical_properties.laboratory_number))
        self.borehole.setText(str(statment[statment.current_test].physical_properties.borehole))
        self.depth.setText(str(statment[statment.current_test].physical_properties.depth))
        self.name.setText(str(statment[statment.current_test].physical_properties.soil_name))

class ModelShearItemUI(TableVertical):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        fill_keys = {
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "tau_max": "Максимальное касательное напряжение τ, кПа",
            "sigma": "Нормальное напряжение 𝜎, кПа",
            "poisons_ratio": "Коэффициент Пуассона",
            "build_press": "Давление от здания, кПа",
            "pit_depth": "Глубина котлована, м",
            "dilatancy_angle": "Угол дилатансии, град"
        }
        super().__init__(fill_keys=fill_keys, size={"size": 100, "size_fixed_index": [1]})
