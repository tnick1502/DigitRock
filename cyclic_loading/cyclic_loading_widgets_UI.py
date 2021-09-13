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

from general.initial_tables import Table, Table_Castomer
from general.general_widgets import Float_Slider
from general.general_functions import read_json_file, create_json_file
from configs.styles import style
from general.report_general_statment import save_report
from general.excel_data_parser import dataToDict, dictToData, CyclicData

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

        if params["toolbar"]:
            setattr(self, "{name_widget}_canvas_toolbar".format(name_widget=name),
                    NavigationToolbar(canvas, self))
            toolbar = getattr(self, "{name_widget}_canvas_toolbar".format(name_widget=name))
            chart_frame_layout.addWidget(toolbar)

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
                                                                          [[3, 3],[3, 3],[6, 3]])]

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
                              "strain_stabilization": "Стабилизация"
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
                setattr(self, "{name_var}_slider".format( name_var=var),
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

class CyclicLoadingUI_PredictLiquefaction(QDialog):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self, data, data_customer):
        super().__init__()
        self._table_is_full = False
        self._data_customer = data_customer
        self.setWindowTitle("Прогнозирование разжижаемости")
        self.create_IU()
        self._original_keys_for_sort = list(data.keys())
        self._set_data(data)
        self.table_castomer.set_data(data_customer)
        self.resize(1400, 800)

        self.open_data_button.clicked.connect(self._read_data_from_json)
        self.save_data_button.clicked.connect(self._save_data_to_json)
        self.save_button.clicked.connect(self._save_pdf)
        self.combo_box.activated.connect(self._sort_combo_changed)

    def create_IU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.table_castomer = Table_Castomer()
        self.table_castomer.setFixedHeight(80)
        self.layout.addWidget(self.table_castomer)

        self.l = QHBoxLayout()
        self.button_box = QGroupBox("Инструменты")
        self.button_box_layout = QHBoxLayout()
        self.button_box.setLayout(self.button_box_layout)
        self.open_data_button = QPushButton("Подгрузить данные")
        self.open_data_button.setFixedHeight(30)
        self.save_data_button = QPushButton("Сохранить данные")
        self.save_data_button.setFixedHeight(30)
        self.save_button = QPushButton("Сохранить данные PDF")
        self.save_button.setFixedHeight(30)
        self.combo_box = QComboBox()
        self.combo_box.setFixedHeight(30)
        self.combo_box.addItems(["Сортировка", "CSR", "sigma_3", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.open_data_button)
        self.button_box_layout.addWidget(self.save_data_button)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)
        self.l.addWidget(self.button_box)
        self.layout.addLayout(self.l)

        self.table = QTableWidget()
        self.table.itemChanged.connect(self._set_color_on_fail)
        self._clear_table()
        self.layout.addWidget(self.table)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def _clear_table(self):
        """Очистка таблицы и придание соответствующего вида"""
        self._table_is_full = False

        while (self.table.rowCount() > 0):
            self.table.removeRow(0)

        self.table.setColumnCount(12)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il", "e", "𝜎3, кПа", "𝜎1, кПа", "t, кПа", "CSR", "Число циклов",
             "Nfail", "Ms"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        self.table.horizontalHeader().setMinimumSectionSize(100)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(self._data))

        for string_number, lab_number in enumerate(self._data):
            for i, val in enumerate(
                    [
                        lab_number,
                        str(self._data[lab_number].physical_properties.depth),
                        self._data[lab_number].physical_properties.soil_name,
                        str(self._data[lab_number].physical_properties.Il) if self._data[lab_number].physical_properties.Il else "-",
                        str(self._data[lab_number].physical_properties.e),
                        str(self._data[lab_number].sigma_3),
                        str(self._data[lab_number].sigma_1),
                        str(self._data[lab_number].t),
                        str(self._data[lab_number].CSR),
                        str(self._data[lab_number].cycles_count),
                        str(self._data[lab_number].n_fail) if self._data[lab_number].n_fail else "-",
                        str(self._data[lab_number].Ms)
                    ]):

                self.table.setItem(string_number, i, QTableWidgetItem(val))

        self._table_is_full = True

        self._set_color_on_fail()

    def _update_data(self):
        """Метод обновляет данные разжижения из таблицы в структуру жанных"""
        def read_n_fail(x):
            try:
                y = int(x)
                return y
            except ValueError:
                return None

        for string_number, lab_number in enumerate(self._data):
            self._data[lab_number].n_fail = read_n_fail(self.table.item(string_number, 10).text())
            self._data[lab_number].Ms = float(self.table.item(string_number, 11).text())

            if self._data[lab_number].n_fail:
                self._data[lab_number].Mcsr = None
                if (self._data[lab_number].sigma_1 - self._data[lab_number].sigma_3) <= 1.5 * self._data[lab_number].t:
                    self._data[lab_number].Ms = np.round(np.random.uniform(100, 500), 2)
                else:
                    self._data[lab_number].Ms = np.round(np.random.uniform(0.7, 0.9), 2)
            else:
                self._data[lab_number].Mcsr = np.random.uniform(2, 3)

    def _set_color_on_fail(self):
        if self._table_is_full:
            self._update_data()
            for string_number, lab_number in enumerate(self._data):
                if self._data[lab_number].n_fail:
                    self._set_row_color(string_number, color=(255, 99, 71))
                elif self._data[lab_number].Ms <= 1:
                    self._set_row_color(string_number, color=(255, 215, 0))
                else:
                    self._set_row_color(string_number, color=(255, 255, 255))

    def _set_row_color(self, row, color=(255, 255, 255)):#color=(62, 180, 137)):
        """Раскрашиваем строку"""
        for i in range(self.table.columnCount()):
            if color == (255, 255, 255):
                item_color = str(self.table.item(row, i).background().color().name())
                if item_color != "#ffffff" and item_color != "#000000":
                    self.table.item(row, i).setBackground(QtGui.QColor(*color))
            else:
                self.table.item(row, i).setBackground(QtGui.QColor(*color))

    def _set_data(self, data):
        """Функция для получения данных"""
        self._data = data
        self._fill_table()

    def _save_data_to_json(self):
        s = QFileDialog.getSaveFileName(self, 'Open file')[0]
        if s:
            s += ".json"
            d = dataToDict(self._data)
            create_json_file(s, d)

    def _read_data_from_json(self):
        s = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if s:
            data = read_json_file(s)
            if sorted(data) == sorted(self._data):
                self._set_data(dictToData(data, CyclicData))
            else:
                QMessageBox.critical(self, "Ошибка", "Неверная структура данных", QMessageBox.Ok)

    def _sort_data(self, sort_key="CSR"):
        """Сортировка проб"""
        #sort_lab_numbers = sorted(list(self._data.keys()), key=lambda x: self._data[x][sort_key])
        #self._data = {key: self._data[key] for key in sort_lab_numbers}
        #self._data = dict(sorted(self._data.items(), key=lambda x: self._data[x[0]][sort_key]))
        self._data = dict(sorted(self._data.items(), key=lambda x: getattr(self._data[x[0]], sort_key)))

    def _sort_combo_changed(self):
        """Изменение способа сортировки combo_box"""
        if self._table_is_full:
            if self.combo_box.currentText() == "Сортировка":
                self._data = {key: self._data[key] for key in self._original_keys_for_sort}
                self._clear_table()
            else:
                self._sort_data(self.combo_box.currentText())
                self._clear_table()

            self._fill_table()

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирования разжижения"
            titles, data, scales = CyclicLoadingUI_PredictLiquefaction.transform_data_for_statment(self._data)
            try:
                save_report(titles, data, scales, self._data_customer["data"], ['Заказчик:', 'Объект:'],
                            [self._data_customer["customer"], self._data_customer["object_name"]], statement_title,
                            save_dir, "---", "Прогноз разжижения.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    def get_data(self):
        return self._data

    @staticmethod
    def transform_data_for_statment(data):
        """Трансформация данных для передачи в ведомость"""
        data_structure = []

        for string_number, lab_number in enumerate(data):
                data_structure.append([
                    lab_number,
                    str(data[lab_number].physical_properties.depth),
                    data[lab_number].physical_properties.soil_name,
                    data[lab_number].physical_properties.Il,
                    data[lab_number].physical_properties.e,
                    str(data[lab_number].CSR),
                    str(data[lab_number].cycles_count),
                    str(data[lab_number].n_fail) if data[lab_number].n_fail else "-",
                    str(data[lab_number].Ms)])

        titles = ["Лаб. номер", "Глубина, м", "Наименование грунта", "Il", "e", "CSR, д.е.", "Общее число циклов",
                   "Цикл разрушения", "Ms"]

        scale = [70, 70, "*", 70, 70, 70]

        return (titles, data_structure, scale)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicLoadingUISoilTest()
    ex.show()
    sys.exit(app.exec_())
