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
from general.general_widgets import Float_Slider
from general.general_functions import read_json_file, create_json_file
from configs.styles import style
from singletons import models, statment
from general.report_general_statment import save_report

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file("C:/Users/Пользователь/PycharmProjects/DigitRock/configs/rcParams.json"))
plt.style.use('bmh')

class CyclicDampingUI(QWidget):
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
        print("ojpds")
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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicLoadingUISoilTest()
    ex.show()
    sys.exit(app.exec_())
