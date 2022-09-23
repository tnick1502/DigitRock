"""Модуль графического интерфейса моделей
    """
__version__ = 1

import copy

import matplotlib.ticker
from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QComboBox
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
import numpy as np

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

        # Отсечение графика для малых нагружений
        self.split_deviator = QGroupBox("Отсечение девиатора")
        self.split_deviator_radio_button = QRadioButton('до 0.7qf, после 0.14')
        self.split_deviator_radio_button.setChecked(False)
        self.split_deviator_layout = QHBoxLayout()
        self.split_deviator_layout.addWidget(self.split_deviator_radio_button)
        self.split_deviator.setLayout(self.split_deviator_layout)

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
        self.widgets_line.addWidget(self.split_deviator)
        self.widgets_line.addWidget(self.chose_volumometer)

        self.chose_plot_type = QGroupBox("Режим построения")
        self.chose_plot_type_layout = QVBoxLayout()
        self.chose_plot_type.setLayout(self.chose_plot_type_layout)
        self.combo_box = QComboBox()
        self.combo_box.addItems(["E", "E50", "E и E50"])

        self.dilatancy_radio_btn = QRadioButton("Дилатансия")
        self.dilatancy_radio_btn.setChecked(False)

        self.chose_plot_type_layout.addWidget(self.combo_box)
        self.chose_plot_type_layout.addWidget(self.dilatancy_radio_btn)
        self.widgets_line.addWidget(self.chose_plot_type)


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

    def replot_deviator_axis(self):
        try:
            self.deviator_figure.delaxes(self.deviator_ax2)

            self.deviator_ax2 = self.deviator_figure.add_axes([0.62, 0.3, .35, .35])
            self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', кПА", fontsize=8)
            self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

            self.deviator_ax.grid(axis='both', linewidth='0.4')
            self.deviator_ax.tick_params(axis='both', which='both', colors='#000000')
            self.deviator_ax.spines['top'].set_color('#000000')
            self.deviator_ax.spines['bottom'].set_color('#000000')
            self.deviator_ax.spines['left'].set_color('#000000')
            self.deviator_ax.spines['right'].set_color('#000000')
        except:
            pass

    def replot_volume_strain_axis(self):
        try:
            self.volume_strain_ax.grid(axis='both', linewidth='0.4')
            self.volume_strain_ax.tick_params(axis='both', which='both', colors='#000000')
            self.volume_strain_ax.spines['top'].set_color('#000000')
            self.volume_strain_ax.spines['bottom'].set_color('#000000')
            self.volume_strain_ax.spines['left'].set_color('#000000')
            self.volume_strain_ax.spines['right'].set_color('#000000')
        except:
            pass

    def plot(self, plots, res):
        """Построение графиков опыта"""

        if statment.general_parameters.test_mode == "Виброползучесть":
            self.combo_box.setCurrentText("E50")
            self.combo_box.setDisabled(True)

        if statment.general_parameters.test_mode in ["Трёхосное сжатие с разгрузкой",
                                                     "Трёхосное сжатие (F, C, Eur)",
                                                     "Трёхосное сжатие с разгрузкой (plaxis)"]:

            if "Eur_E" not in [self.combo_box.itemText(i) for i in range(self.combo_box.count())]:
                self.combo_box.addItems(["Eur_E"])
                self.combo_box.addItems(["Eur_E50"])
                self.combo_box.addItems(["Eur"])
                if statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
                    self.combo_box.setCurrentText("Eur")
                else:
                    self.combo_box.setCurrentText("Eur_E")

        try:
            # Если необходимо безразрывное построение девиатора
            if not plots["is_split_deviator"] or plots["strain"][-1] < 0.13:
                if self.combo_box.currentText() == "E":
                    self._plot_E(plots, res)
                elif self.combo_box.currentText() == "E50":
                    self._plot_E50(plots, res)
                elif self.combo_box.currentText() == "E и E50":
                    self._plot_E_E50(plots, res)
                elif self.combo_box.currentText() == "Eur_E":
                    self._plot_Eur_E(plots, res)
                elif self.combo_box.currentText() == "Eur_E50":
                    self._plot_Eur_E50(plots, res)
                elif self.combo_box.currentText() == "Eur":
                    self._plot_Eur(plots, res)
                self._plot_volume_strain(plots, res, with_dilatancy=self.dilatancy_radio_btn.isChecked())
            # Если необходимо разрывное построение девиатора
            elif plots["is_split_deviator"]:
                if self.combo_box.currentText() == "E":
                    self._plot_E_split(plots, res)
                elif self.combo_box.currentText() == "E50":
                    self._plot_E50_split(plots, res)
                elif self.combo_box.currentText() == "E и E50":
                    self._plot_E_E50_split(plots, res)
                elif self.combo_box.currentText() == "Eur_E":
                    self._plot_Eur_E_split(plots, res)
                elif self.combo_box.currentText() == "Eur_E50":
                    self._plot_Eur_E50_split(plots, res)
                elif self.combo_box.currentText() == "Eur":
                    self._plot_Eur_split(plots, res)

                self._plot_volume_strain(plots, res, with_dilatancy=self.dilatancy_radio_btn.isChecked())
                # self._plot_volume_strain_split(plots, res, with_dilatancy=self.dilatancy_radio_btn.isChecked())
        except:
            pass

    def clear_split_axis(self, fig_type='deviator'):
        try:
            if fig_type == 'deviator':
                self.deviator_figure.delaxes(self.deviator_ax_1)
                self.deviator_figure.delaxes(self.deviator_ax_2)
                self.deviator_figure.delaxes(self.deviator_ax2_1)
                self.deviator_figure.delaxes(self.deviator_ax2_2)
            if fig_type == 'volume':
                self.volume_strain_figure.delaxes(self.volume_strain_ax_1)
                self.volume_strain_figure.delaxes(self.volume_strain_ax_2)
        except:
            pass

    def _plot_E(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            self.deviator_ax.plot(plots["strain"], plots["deviator"] + plots["sigma_3"],
                                  **plotter_params["static_loading_main_line"])
            self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax.scatter(*plots["E_point_1"], s=20, color="black")
            self.deviator_ax.scatter(*plots["E_point_2"], s=20, color="black")

            self.deviator_ax.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                  **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax2.plot(plots["strain"], plots["deviator"],
                                   **plotter_params["static_loading_main_line"])

            self.deviator_ax2.plot(plots["E"]["x"], plots["E"]["y"], label=_label,
                                  **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_E_split(self, plots, res):
        self.clear_split_axis()

        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)

        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()

        # Создаем пографики малого графика для разделения
        ax2_width = .34
        self.deviator_ax2_2 = self.deviator_figure.add_axes([0.62 + ax2_width/2 + 0.01, 0.3, ax2_width/2, .35])
        self.deviator_ax2_1 = self.deviator_figure.add_axes([0.62, 0.3, ax2_width / 2, .35])

        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()

        self.deviator_ax.clear()

        self.deviator_ax2_1.clear()
        self.deviator_ax2_2.clear()
        self.deviator_ax2.clear()

        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax2_1, self.deviator_ax2_2)
        self.deviator_ax2_1.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_2.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_1.locator_params(axis='x', nbins=3)
        self.deviator_ax2_2.locator_params(axis='x', nbins=3)

        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(plots["strain"],
                                                                                                         plots["deviator"])

            self.deviator_ax_1.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                    **plotter_params["static_loading_main_line"])
            self.deviator_ax_2.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                    **plotter_params["static_loading_main_line"])

            self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                  **plotter_params["static_loading_gray_line"])
            self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax_1.scatter(*plots["E_point_1"], s=20, color="black")
            self.deviator_ax_2.scatter(*plots["E_point_2"], s=20, color="black")
            self.deviator_ax_1.scatter(*plots["E_point_1"], s=20, color="black")
            self.deviator_ax_2.scatter(*plots["E_point_2"], s=20, color="black")

            self.deviator_ax_1.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                    **plotter_params["static_loading_black_dotted_line"])
            self.deviator_ax_2.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                    **plotter_params["static_loading_black_dotted_line"])

            # Задаем пределы на оси
            min_x_lim = plots["strain_cut"][0]-abs(plots["strain_cut"][0]*0.05)
            max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

            self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
            self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
            # Размеры на основной оси сохраняем для считывания другими параметрами
            self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

            # Задаем форматирование линий и подписей
            ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)

            # Построение малого подграфика
            self.deviator_ax2_1.plot(np.r_[strain_split[0], strain_split[1]],
                                     np.r_[deviator_split[0], deviator_split[1]],
                                     **plotter_params["static_loading_main_line"])
            self.deviator_ax2_2.plot(np.r_[strain_split[0], strain_split[1]],
                                     np.r_[deviator_split[0], deviator_split[1]],
                                     **plotter_params["static_loading_main_line"])
            self.deviator_ax2_1.plot(plots["E"]["x"], plots["E"]["y"], label=_label,
                                     **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax2_1.set_xlim(strain_split[0][0], strain_split[0][-1])
            self.deviator_ax2_2.set_xlim(strain_split[1][0], max_x_lim)
            self.deviator_ax2.set_xlim(min_x_lim, max_x_lim)

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.16)

        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)

        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_canvas.draw()

    def _plot_E_E50(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            self.deviator_ax.plot(plots["strain"], plots["deviator"] + plots["sigma_3"],
                                  **plotter_params["static_loading_main_line"])
            self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                  **plotter_params["static_loading_gray_line"])

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax.scatter(*plots["E_point_2"], s=20, color="black")

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.plot(*plots["E50"],
                                       label=_label,
                                       **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax2.plot(plots["strain"], plots["deviator"],
                                   **plotter_params["static_loading_main_line"])
            if res["E"] is not None:
                if statment.general_parameters.test_mode != "Виброползучесть":
                    self.deviator_ax.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                          **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_E_E50_split(self, plots, res):
        self.clear_split_axis()

        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)
        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()
        # Создаем пографики малого графика для разделения
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        ax2_width = .34
        self.deviator_ax2_2 = self.deviator_figure.add_axes([0.62 + ax2_width/2 + 0.01, 0.3, ax2_width/2, .35])
        self.deviator_ax2_1 = self.deviator_figure.add_axes([0.62, 0.3, ax2_width / 2, .35])


        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_ax2_1.clear()
        self.deviator_ax2_2.clear()
        self.deviator_ax2.clear()

        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax2_1, self.deviator_ax2_2)
        self.deviator_ax2_1.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_2.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_1.locator_params(axis='x', nbins=3)
        self.deviator_ax2_2.locator_params(axis='x', nbins=3)

        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(plots["strain"],
                                                                                                         plots["deviator"])

            self.deviator_ax_1.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                    **plotter_params["static_loading_main_line"])
            self.deviator_ax_2.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                    **plotter_params["static_loading_main_line"])

            self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                    **plotter_params["static_loading_gray_line"])
            self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                    **plotter_params["static_loading_gray_line"])

            # Задаем пределы на оси
            min_x_lim = plots["strain_cut"][0]-abs(plots["strain_cut"][0]*0.05)
            max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

            self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
            self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
            # Размеры на основной оси сохраняем для считывания другими параметрами
            self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax_1.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax_2.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax_1.scatter(*plots["E_point_2"], s=20, color="black")
                self.deviator_ax_2.scatter(*plots["E_point_2"], s=20, color="black")

            # Задаем форматирование линий и подписей
            ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)

            # Построение малого подграфика
            self.deviator_ax2_1.set_xlim(strain_split[0][0], strain_split[0][-1])
            self.deviator_ax2_2.set_xlim(strain_split[1][0], max_x_lim)
            self.deviator_ax2.set_xlim(min_x_lim, max_x_lim)

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2_1.scatter(res["Eps50"], res["qf50"], s=20, color="black")
                self.deviator_ax2_2.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2_1.plot(*plots["E50"],
                                       label=_label,
                                       **plotter_params["static_loading_black_dotted_line"])
                self.deviator_ax2_2.plot(*plots["E50"],
                                       label=_label,
                                       **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax2_1.plot(plots["strain"], plots["deviator"],
                                   **plotter_params["static_loading_main_line"])
            self.deviator_ax2_2.plot(plots["strain"], plots["deviator"],
                                   **plotter_params["static_loading_main_line"])
            if res["E"] is not None:
                if statment.general_parameters.test_mode != "Виброползучесть":
                    self.deviator_ax_1.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                          **plotter_params["static_loading_black_dotted_line"])
                    self.deviator_ax_2.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                          **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.16)

        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)

        self.deviator_canvas.draw()

    def _plot_E50(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', МПa", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            self.deviator_ax.plot(plots["strain"], plots["deviator"],
                                  **plotter_params["static_loading_main_line"])
            self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax.plot(*plots["E50"], label=_label,
                                   **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            self.deviator_ax2.plot(plots["strain"], plots["deviator"] + plots["sigma_3"],
                                   **plotter_params["static_loading_main_line"])

            self.deviator_ax2.scatter(res["Eps50"], res["qf50"]+ plots["sigma_3"], s=20, color="black")

            x, y = plots["E50"][0], np.array(plots["E50"][1])
            self.deviator_ax2.plot(x, y + plots["sigma_3"],label=_label,
                                   **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_E50_split(self, plots, res):
        self.clear_split_axis()
        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)

        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()

        # Создаем пографики малого графика для разделения
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        ax2_width = .34
        self.deviator_ax2_2 = self.deviator_figure.add_axes([0.62 + ax2_width / 2 + 0.01, 0.3, ax2_width / 2, .35])
        self.deviator_ax2_1 = self.deviator_figure.add_axes([0.62, 0.3, ax2_width / 2, .35])

        # ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax2_1, self.deviator_ax2_2)

        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        self.deviator_ax2_1.clear()
        self.deviator_ax2_2.clear()

        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax2_1, self.deviator_ax2_2)
        self.deviator_ax2_1.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_2.tick_params(axis=u'both', which=u'both', labelsize=6)
        self.deviator_ax2_1.locator_params(axis='x', nbins=3)
        self.deviator_ax2_2.locator_params(axis='x', nbins=3)


        self.deviator_ax2.set_ylabel("Напряжение $𝜎_1$', МПa", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"


            strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(plots["strain"],
                                                                                                         plots["deviator"])

            self.deviator_ax_1.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])
            self.deviator_ax_2.plot(np.r_[strain_split[0],strain_split[1]],
                                    np.r_[deviator_split[0],deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])

            self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"],
                                  **plotter_params["static_loading_gray_line"])
            self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax_1.plot(*plots["E50"], label=_label,
                                  **plotter_params["static_loading_black_dotted_line"])
            self.deviator_ax_2.plot(*plots["E50"], label=_label,
                                  **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax_1.scatter(res["Eps50"], res["qf50"], s=20, color="black")
            self.deviator_ax_2.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            # Задаем пределы на оси
            min_x_lim = plots["strain_cut"][0]-abs(plots["strain_cut"][0]*0.05)
            max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

            self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
            self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
            # Размеры на основной оси сохраняем для считывания другими параметрами
            self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

            # Задаем форматирование линий и подписей
            ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)

            # Построение малых подграфиков
            self.deviator_ax2_1.plot(np.r_[strain_split[0],strain_split[1]],
                                     np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                   **plotter_params["static_loading_main_line"])
            self.deviator_ax2_2.plot(np.r_[strain_split[0],strain_split[1]],
                                     np.r_[deviator_split[0],deviator_split[1]] + plots["sigma_3"],
                                   **plotter_params["static_loading_main_line"])

            self.deviator_ax2.scatter(res["Eps50"], res["qf50"] + plots["sigma_3"], s=20, color="black")

            self.deviator_ax2_1.set_xlim(strain_split[0][0], strain_split[0][-1])
            self.deviator_ax2_2.set_xlim(strain_split[1][0], max_x_lim)
            self.deviator_ax2.set_xlim(min_x_lim, max_x_lim)

            x, y = plots["E50"][0], np.array(plots["E50"][1])
            self.deviator_ax2_1.plot(x, y + plots["sigma_3"], label=_label,
                                   **plotter_params["static_loading_black_dotted_line"])
            self.deviator_ax2_2.plot(x, y + plots["sigma_3"], label=_label,
                                   **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.12)
        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)

        self.deviator_canvas.draw()

    def _plot_Eur_E(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            if plots["Eur"]:
                self.deviator_ax.plot(plots["strain"], plots["deviator"] + plots["sigma_3"],
                                      **plotter_params["static_loading_main_line"])
                self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                      **plotter_params["static_loading_gray_line"])

                self.deviator_ax.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                      **plotter_params["static_loading_black_dotted_line"])


                self.deviator_ax.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax.scatter(*plots["E_point_2"], s=20, color="black")

                self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                       **plotter_params["static_loading_main_line"])
                if statment.general_parameters.test_mode != "Виброползучесть":
                    self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])

                label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
                    "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

                if res["q_rel"]:
                    label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

                self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_Eur_E_split(self, plots, res):
        self.clear_split_axis()

        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)

        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()

        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()
        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Напряжение $𝜎_1$', МПa")

        self.deviator_ax2.clear()
        # ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            if plots["Eur"]:
                strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(
                    plots["strain"],
                    plots["deviator"])

                self.deviator_ax_1.plot(np.r_[strain_split[0], strain_split[1]],
                                        np.r_[deviator_split[0], deviator_split[1]] + plots["sigma_3"],
                                        **plotter_params["static_loading_main_line"])
                self.deviator_ax_2.plot(np.r_[strain_split[0], strain_split[1]],
                                        np.r_[deviator_split[0], deviator_split[1]] + plots["sigma_3"],
                                        **plotter_params["static_loading_main_line"])

                self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                        **plotter_params["static_loading_gray_line"])
                self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"] + plots["sigma_3"],
                                        **plotter_params["static_loading_gray_line"])

                self.deviator_ax_1.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                      **plotter_params["static_loading_black_dotted_line"])
                self.deviator_ax_2.plot(plots["E"]["x"], plots["E"]["y"] + plots["sigma_3"], label=_label,
                                      **plotter_params["static_loading_black_dotted_line"])

                self.deviator_ax_1.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax_2.scatter(*plots["E_point_2"], s=20, color="black")
                self.deviator_ax_1.scatter(*plots["E_point_1"], s=20, color="black")
                self.deviator_ax_2.scatter(*plots["E_point_2"], s=20, color="black")

                # Задаем пределы на оси
                min_x_lim = plots["strain_cut"][0] - abs(plots["strain_cut"][0] * 0.05)
                max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

                self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
                self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
                # Размеры на основной оси сохраняем для считывания другими параметрами
                self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

                # Задаем форматирование линий и подписей
                ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)

                # Построение малого подграфика
                self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                         **plotter_params["static_loading_main_line"])

                if statment.general_parameters.test_mode != "Виброползучесть":
                    self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])


                label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
                    "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

                if res["q_rel"]:
                    label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

                self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.12)
        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)
        self.deviator_canvas.draw()

    def _plot_Eur_E50(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            self.deviator_ax.plot(plots["strain"], plots["deviator"],
                                  **plotter_params["static_loading_main_line"])
            self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax.plot(*plots["E50"], label=_label,
                                  **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                   **plotter_params["static_loading_main_line"])
            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])



        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_Eur_E50_split(self, plots, res):
        self.clear_split_axis()

        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)

        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()

        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        # ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(
                plots["strain"],
                plots["deviator"])

            self.deviator_ax_1.plot(np.r_[strain_split[0], strain_split[1]],
                                    np.r_[deviator_split[0], deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])
            self.deviator_ax_2.plot(np.r_[strain_split[0], strain_split[1]],
                                    np.r_[deviator_split[0], deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])

            self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"],
                                    **plotter_params["static_loading_gray_line"])
            self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"],
                                    **plotter_params["static_loading_gray_line"])

            self.deviator_ax_1.plot(*plots["E50"], label=_label,
                                    **plotter_params["static_loading_black_dotted_line"])
            self.deviator_ax_2.plot(*plots["E50"], label=_label,
                                    **plotter_params["static_loading_black_dotted_line"])

            self.deviator_ax_1.scatter(res["Eps50"], res["qf50"], s=20, color="black")
            self.deviator_ax_2.scatter(res["Eps50"], res["qf50"], s=20, color="black")

            # Задаем пределы на оси
            min_x_lim = plots["strain_cut"][0] - abs(plots["strain_cut"][0] * 0.05)
            max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

            self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
            self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
            # Размеры на основной оси сохраняем для считывания другими параметрами
            self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

            # Задаем форматирование линий и подписей
            ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)

            self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                   **plotter_params["static_loading_main_line"])
            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.16)
        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)
        self.deviator_canvas.draw()

    def _plot_Eur(self, plots, res):
        self.clear_split_axis()
        self.replot_deviator_axis()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            self.deviator_ax.plot(plots["strain"], plots["deviator"],
                                  **plotter_params["static_loading_main_line"])
            self.deviator_ax.plot(plots["strain_cut"], plots["deviator_cut"],
                                  **plotter_params["static_loading_gray_line"])

            self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                   **plotter_params["static_loading_main_line"])
            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])



        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)
        self.deviator_canvas.draw()

    def _plot_Eur_split(self, plots, res):
        self.clear_split_axis()

        # Добавляем подграфики для построения разделенного графика
        self.deviator_ax_1 = self.deviator_figure.add_subplot(121)
        self.deviator_ax_2 = self.deviator_figure.add_subplot(122)

        # Перестраиваем графики девиаторки
        self.replot_deviator_axis()

        # Очистки и подписи
        self.deviator_ax_1.clear()
        self.deviator_ax_2.clear()

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.deviator_ax2.clear()
        # ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax2)
        self.deviator_ax2.set_ylabel("Девиатор q, МПа", fontsize=8)
        self.deviator_ax2.set_xlabel("Относительная деформация $ε_1$, д.е.", fontsize=8)

        if plots["strain"] is not None:

            if res["E"] is not None:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0])
            else:
                _label = "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + str(res["E"][0]) + "; $E_{ur}$ = " + str(
                    res["Eur"]) if res["Eur"] else "$E_{50} = $" + str(res["E50"]) + "; $E$ = " + "-"

            strain_split, deviator_split, self.split_ind = ModelTriaxialDeviatorLoadingUI.split_deviator(
                plots["strain"],
                plots["deviator"])

            self.deviator_ax_1.plot(np.r_[strain_split[0], strain_split[1]],
                                    np.r_[deviator_split[0], deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])
            self.deviator_ax_2.plot(np.r_[strain_split[0], strain_split[1]],
                                    np.r_[deviator_split[0], deviator_split[1]],
                                    **plotter_params["static_loading_main_line"])

            self.deviator_ax_1.plot(plots["strain_cut"], plots["deviator_cut"],
                                    **plotter_params["static_loading_gray_line"])
            self.deviator_ax_2.plot(plots["strain_cut"], plots["deviator_cut"],
                                    **plotter_params["static_loading_gray_line"])

            # Задаем пределы на оси
            min_x_lim = plots["strain_cut"][0] - abs(plots["strain_cut"][0] * 0.05)
            max_x_lim = 0.155 if strain_split[1][-1] < 0.155 else strain_split[1][-1]

            self.deviator_ax_1.set_xlim(min_x_lim, strain_split[0][-1])
            self.deviator_ax_2.set_xlim(strain_split[1][0], max_x_lim)
            # Размеры на основной оси сохраняем для считывания другими параметрами
            self.deviator_ax.set_xlim(min_x_lim, max_x_lim)

            # Задаем форматирование линий и подписей
            ModelTriaxialDeviatorLoadingUI.format_split(self.deviator_ax_1, self.deviator_ax_2)


            self.deviator_ax2.plot(plots["strain_Eur"], plots["deviator_Eur"],
                                   **plotter_params["static_loading_main_line"])
            if statment.general_parameters.test_mode != "Виброползучесть":
                self.deviator_ax2.plot(*plots["Eur"], **plotter_params["static_loading_black_dotted_line"])

        label = "$K_{E_{50}} = $" + str(res["K_E50"]) + "; " + "$K_{E_{ur}} = $" + str(res["K_Eur"]) if res[
            "K_Eur"] else "$K_{E_{50}} = $" + str(res["K_E50"])

        if res["q_rel"]:
            label = label + "; " + "$q_{rel} = $" + str(res["q_rel"])

        self.deviator_ax_2.plot([], [], label=label, color="#eeeeee")

        self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.82), fontsize=10)

        self.deviator_figure.subplots_adjust(wspace=0.12)
        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.deviator_ax)

        self.deviator_canvas.draw()

    def _plot_volume_strain(self, plots, res, with_dilatancy=False):
        self.clear_split_axis(fig_type='volume')
        self.replot_volume_strain_axis()

        self.volume_strain_ax.clear()
        self.volume_strain_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.volume_strain_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

        self.volume_strain_ax.plot(plots["strain"], plots["volume_strain"],
                                   **plotter_params["static_loading_main_line"])
        self.volume_strain_ax.plot(plots["strain"], plots["volume_strain_approximate"],
                                   **plotter_params["static_loading_red_dotted_line"])

        self.volume_strain_ax.set_xlim(self.deviator_ax.get_xlim())

        self.volume_strain_ax.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                   color="#eeeeee")

        if with_dilatancy:
            if plots["dilatancy"]:
                self.volume_strain_ax.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"],
                                           **plotter_params["static_loading_black_dotted_line"])
        if res["dilatancy_angle"] is not None:
            self.volume_strain_ax.plot([], [],
                                        label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                        color="#eeeeee")

        self.volume_strain_ax.legend()
        self.volume_strain_canvas.draw()

    def _plot_volume_strain_split(self, plots, res, with_dilatancy=False):
        self.clear_split_axis(fig_type='volume')
        # Добавляем подграфики
        self.volume_strain_ax_1 = self.volume_strain_figure.add_subplot(121)
        self.volume_strain_ax_2 = self.volume_strain_figure.add_subplot(122)
        # Перестраиваем основной график
        self.replot_volume_strain_axis()

        self.volume_strain_ax.clear()
        self.volume_strain_ax_1.clear()
        self.volume_strain_ax_2.clear()
        self.volume_strain_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.volume_strain_ax.set_ylabel("Объемная деформация $ε_v$, д.е.")

        strain_split = np.r_[plots["strain"][:self.split_ind[0]], plots["strain"][self.split_ind[1]:]]
        volume_strain_split = np.r_[plots["volume_strain"][:self.split_ind[0]], plots["volume_strain"][self.split_ind[1]:]]

        self.volume_strain_ax_1.plot(strain_split, volume_strain_split,
                                   **plotter_params["static_loading_main_line"])
        self.volume_strain_ax_2.plot(strain_split, volume_strain_split,
                                   **plotter_params["static_loading_main_line"])

        self.volume_strain_ax_1.plot(plots["strain"], plots["volume_strain_approximate"],
                                   **plotter_params["static_loading_red_dotted_line"])
        self.volume_strain_ax_2.plot(plots["strain"], plots["volume_strain_approximate"],
                                   **plotter_params["static_loading_red_dotted_line"])

        # Задаем пределы
        min_x_lim = plots["strain"][:self.split_ind[0]][0] - abs(plots["strain"][:self.split_ind[0]][0]) * 0.05
        max_x_lim = 0.155 if strain_split[-1] < 0.155 else strain_split[-1]
        self.volume_strain_ax_1.set_xlim(min_x_lim, plots["strain"][:self.split_ind[0]][-1])
        self.volume_strain_ax_2.set_xlim(plots["strain"][self.split_ind[1]:][0], max_x_lim)
        # Размеры на основной оси сохраняем для считывания другими параметрами
        self.volume_strain_ax.set_xlim(min_x_lim, max_x_lim)
        # Задаем форматирование линий и подписей
        ModelTriaxialDeviatorLoadingUI.format_split(self.volume_strain_ax_1, self.volume_strain_ax_2)
        self.volume_strain_figure.subplots_adjust(wspace=0.10)
        # Отключение всего что можно на основном графике
        ModelTriaxialDeviatorLoadingUI.hide_stuff(self.volume_strain_ax)


        self.volume_strain_ax_2.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                     color="#eeeeee")

        if with_dilatancy:
            if plots["dilatancy"]:
                self.volume_strain_ax_1.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"],
                                             **plotter_params["static_loading_black_dotted_line"])
                self.volume_strain_ax_2.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"],
                                             **plotter_params["static_loading_black_dotted_line"])
        if res["dilatancy_angle"] is not None:
            self.volume_strain_ax.plot([], [],
                                       label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                       color="#eeeeee")

        self.volume_strain_ax_2.legend()
        self.volume_strain_canvas.draw()

    @staticmethod
    def hide_stuff(axis):
        axis.grid(None)
        axis.spines['top'].set_color('none')
        axis.spines['bottom'].set_color('none')
        axis.spines['left'].set_color('none')
        axis.spines['right'].set_color('none')
        axis.tick_params(axis='both', which='both', labelcolor='none', bottom='off', top='off',
                                     labelbottom='off', right='off', left='off', labelleft='off', colors='#eeeeee')

    @staticmethod
    def format_split(left_subaxis, right_subaxis):
        left_subaxis.spines['right'].set(linestyle='--')
        right_subaxis.spines['left'].set(linestyle='--')

        left_subaxis.spines['right'].set_capstyle('butt')
        right_subaxis.spines['left'].set_capstyle('butt')

        left_subaxis.spines['right'].set_linewidth(0.5)
        right_subaxis.spines['left'].set_linewidth(0.5)

        left_subaxis.spines['right'].set_alpha(0.6)
        right_subaxis.spines['left'].set_alpha(0.6)

        right_subaxis.tick_params(axis='y',
                                       which='both',
                                       left='off',
                                       labelleft='off',
                                       colors='#eeeeee')

        def format(x, pos):
            if x > 0.15001:
                return ""
            if (x % 1) * 1000 < 1:
                return f"{x:.4f}"
            else:
                return f"{x:.3f}"

        formatter = matplotlib.ticker.FuncFormatter(format)
        left_subaxis.xaxis.set_major_formatter(formatter)
        right_subaxis.xaxis.set_major_formatter(formatter)

        # left_subaxis.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.4f'))
        # right_subaxis.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.4f'))

        # Черточки на разрывах осей
        # d = .01
        # kwargs = dict(transform=left_subaxis.transAxes, color='k', clip_on=False)
        # left_subaxis.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-left diagonal
        # left_subaxis.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
        #
        # kwargs.update(transform=right_subaxis.transAxes)  # switch to the bottom axes
        # right_subaxis.plot((-d, d), (-d, +d), **kwargs)  # top-right diagonal
        # right_subaxis.plot((-d, d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    def _combo_changed(self):
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

        def save_split(figure, canvas, size_figure, ax, file_type):

            ax.get_legend().remove()
            canvas.draw()

            try:
                self.deviator_ax_2.tick_params(axis='y',
                                               which=u'both',
                                               left='off',
                                               labelleft='off',
                                               colors='#ffffff')

                self.deviator_ax2_2.tick_params(axis='y',
                                                which=u'both',
                                                left='off',
                                                labelleft='off',
                                                color='#ffffff',
                                                labelcolor='#ffffff',
                                                colors='#ffffff')

                self.deviator_ax.tick_params(axis='both', which=u'both', colors='#ffffff')
                self.deviator_ax2.tick_params(axis='both', which=u'both', colors='#ffffff')

            except:
                pass

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

        if self.split_deviator_radio_button.isChecked():
            result = [save_split(fig, can, size, ax, _format) for fig, can, size, ax, _format in zip([self.deviator_figure,
                                                                                self.volume_strain_figure],
                                                       [self.deviator_canvas, self.volume_strain_canvas], size,
                                                                                  [self.deviator_ax_2, self.volume_strain_ax],
                                                                                             format)]
            try:
                self.deviator_ax_2.tick_params(axis='y',
                                               which='both',
                                               left='off',
                                               labelleft='off',
                                               colors='#eeeeee')
                self.deviator_ax2_2.tick_params(axis='y',
                                                which='both',
                                                left='off',
                                                labelleft='off',
                                                colors='#eeeeee')
                self.deviator_ax_2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)
            except:
                pass

            self.deviator_canvas.draw()
            return result

        return [save(fig, can, size, ax, _format) for fig, can, size, ax, _format in zip([self.deviator_figure,
                                                                                self.volume_strain_figure],
                                                       [self.deviator_canvas, self.volume_strain_canvas], size,
                                                                                  [self.deviator_ax, self.volume_strain_ax],
                                                                                             format)]

    @staticmethod
    def split_deviator(deviator, strain):
        y = copy.deepcopy(strain)
        x = copy.deepcopy(deviator)
        y_07_ind, = np.where(y >= 0.7 * np.max(y))

        x_b_07 = x[:y_07_ind[0]]
        y_b_07 = y[:y_07_ind[0]]

        x_80_ind, = np.where(x >= 0.14)

        x_a_80 = x[x_80_ind[0]:]
        y_a_80 = y[x_80_ind[0]:]

        return (x_b_07, x_a_80), (y_b_07, y_a_80), (y_07_ind[0], x_80_ind[0])

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

class ModelTriaxialItemUI(TableVertical):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "qf": "Максимальный девиатор qf, кПа",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "K0": "K0",
            "poisons_ratio": "Коэффициент Пуассона",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "build_press": "Давление от здания, кПа",
            "pit_depth": "Глубина котлована, м",
            "Eur": "Модуль разгрузки Eur, кПа",
            "dilatancy_angle": "Угол дилатансии, град",
            "OCR": "OCR",
            "m": "Показатель степени жесткости"
        }
        super().__init__(fill_keys=fill_keys, size={"size": 100, "size_fixed_index": [1]})
