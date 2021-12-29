"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
__version__ = 1

from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from io import BytesIO


from shear_test.shear_test_model import ModelShear, ModelShearSoilTest
from shear_test.shear_dilatancy_widgets_UI import ModelShearItemUI
from configs.styles import style
from general.initial_tables import Table
from general.general_widgets import Slider
from configs.plot_params import plotter_params
from general.general_functions import read_json_file, AttrDict
from singletons import Shear_models, Shear_Dilatancy_models, statment
from loggers.logger import app_logger, log_this
from shear_test.shear_dilatancy_widgets_UI import ModelShearDilatancyUI

#plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
plt.style.use('bmh')

class AlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class MohrTable(QWidget):
    """Класс для табличного отображения параметров кругов Мора"""

    def __init__(self, number):
        super().__init__()
        self._create_UI(number)
        self.setFixedHeight(110)

    def _create_UI(self, number):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.box = QGroupBox("Опыт {}".format(number))
        self.layout_box = QHBoxLayout()
        self.box.setLayout(self.layout_box)

        self.table_widget = Table()
        self.table_widget.setFixedHeight(50)
        self.table_widget.setFixedWidth(300)

        self.table_widget.setFocusPolicy(Qt.NoFocus)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        palette = QPalette()
        palette.setBrush(QPalette.Highlight, QBrush(Qt.white))
        palette.setBrush(QPalette.HighlightedText, QBrush(Qt.black))
        self.table_widget.setPalette(palette)

        self.table_widget.horizontalHeader().setVisible(False)
        delegate = AlignDelegate(self.table_widget)
        self.table_widget.setItemDelegateForColumn(2, delegate)
        self.table_widget.setItemDelegateForColumn(1, delegate)
        self.table_widget.setItemDelegateForColumn(0, delegate)

        self.layout_box.addWidget(self.table_widget)

        self.set_param({"sigma": "",
                        "tau_max": "",
                        "dilatancy_angle": ""})

        self.plot_button = QPushButton("Обработчик опыта")
        self.plot_button.setFixedHeight(50)
        self.plot_button.setFixedWidth(120)
        self.layout_box.addWidget(self.plot_button)

        self.dell_button = QPushButton("Удалить опыт")
        self.dell_button.setFixedHeight(50)
        self.dell_button.setFixedWidth(120)
        self.layout_box.addWidget(self.dell_button)

        self.layout.addWidget(self.box)

    def set_param(self, param):
        self.table_widget.set_data([["", "", ""],
                                    ["σ, МПа",
                                     "τ, МПа",
                                     "ψ, град"],
                                    [param["sigma"], param["tau_max"], param["dilatancy_angle"]]], "Stretch")

class MohrTestManager(QWidget):
    """Класс для табличного отображения параметров кругов Мора"""
    def __init__(self):
        super().__init__()
        self.tests = []
        self._create_UI()

    def _create_UI(self):
        self.layout = QVBoxLayout(self)

        self.box = QGroupBox("Менеджер опытов")
        self.layout_box = QVBoxLayout()
        self.box.setLayout(self.layout_box)

        self.add_test_button = QPushButton("Добавить опыт")
        self.add_test_button.setFixedHeight(50)
        self.layout_box.addWidget(self.add_test_button)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QWidget()
        self.scroll_area_widget_layout = QVBoxLayout()
        # self.scroll_area_widget_layout.addWidget(MohrTable(1))
        self.scroll_area_widget.setLayout(self.scroll_area_widget_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.layout.addWidget(self.box)
        self.layout_box.addWidget(self.scroll_area)

        self.layout.setContentsMargins(5, 5, 5, 5)

    def add_test(self, test):
        self.scroll_area_widget_layout.addWidget(test)
        self.scroll_area_widget.setLayout(self.scroll_area_widget_layout)

class ShearWidget(QWidget):
    """Класс для табличного отображения параметров кругов Мора"""

    def __init__(self):
        super().__init__()

        self._model = ModelShear()

        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.1}

        self.item_identification = ModelShearItemUI()
        self.item_identification.setFixedHeight(330)
        self.item_identification.setFixedWidth(450)
        self.mohr_test_manager = MohrTestManager()
        self.mohr_test_manager.setFixedHeight(330)
        self._create_UI()

        self.mohr_test_manager.add_test_button.clicked.connect(self._add_test)

    def _create_UI(self):
        self.layout_wiget = QVBoxLayout(self)
        # self.layout_wiget.setContentsMargins(5, 5, 5, 5)

        self.line_1_layout = QHBoxLayout()
        self.line_1_layout.addWidget(self.item_identification)
        self.line_1_layout.addWidget(self.mohr_test_manager)
        self.layout_wiget.addLayout(self.line_1_layout)
        self.line_2_layout = QHBoxLayout()

        self.box_graph = QGroupBox("Построение графиков")
        self.graph_canvas_layout = QHBoxLayout()
        self.box_graph.setLayout(self.graph_canvas_layout)

        # Графики
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

        self.mohr_frame = QFrame()
        self.mohr_frame.setFrameShape(QFrame.StyledPanel)
        self.mohr_frame.setStyleSheet('background: #ffffff')
        self.mohr_frame_layout = QVBoxLayout()
        self.mohr_figure = plt.figure()
        self.mohr_figure.subplots_adjust(**self.plot_params)
        self.mohr_canvas = FigureCanvas(self.mohr_figure)
        self.mohr_ax = self.mohr_figure.add_subplot(111)
        self.mohr_ax.grid(axis='both', linewidth='0.4')
        self.mohr_ax.set_xlabel("σ, МПа")
        self.mohr_ax.set_ylabel("τ, МПа")
        self.mohr_canvas.draw()
        self.mohr_frame_layout.setSpacing(0)
        self.mohr_frame_layout.addWidget(self.mohr_canvas)
        self.mohr_toolbar = NavigationToolbar(self.mohr_canvas, self)
        self.mohr_frame_layout.addWidget(self.mohr_toolbar)
        self.mohr_frame.setLayout(self.mohr_frame_layout)

        self.graph_canvas_layout.addWidget(self.deviator_frame)
        self.graph_canvas_layout.addWidget(self.mohr_frame)

        self.line_2_layout.addWidget(self.box_graph)

        self.layout_wiget.addLayout(self.line_2_layout)
        self.layout_wiget.addStretch(-1)

    def resizeEvent(self, event):
        self.width = self.rect().width()
        self.height = self.rect().height()
        if self.width >= 1300:
            self.width = 1300
        w = self.width - 25
        self.box_graph.setFixedWidth(w)
        self.box_graph.setFixedHeight(int(w / 3))

    def _add_test(self):
        path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if path:
            try:
                Shear_models[statment.current_test].add_test(path)
                self._create_test_tables()
                self._plot()
            except:
                QMessageBox.critical(self, "Ошибка", "Неправильно выбран файл", QMessageBox.Ok)

    def _dell_test(self):
        """Удаление опыта"""
        parent = self.sender().parent()
        test_id = int(parent.title()[-1])
        Shear_models[statment.current_test].dell_test(test_id)
        self._create_test_tables()
        self._plot()

    def _create_test_tables(self):
        """Отрисовка всех опытов а менеджере"""
        for Table in self.mohr_test_manager.findChildren(MohrTable):
            Table.deleteLater()

        for num, test in enumerate(Shear_models[statment.current_test].get_tests()):
            res = test.get_test_results()

            _format = "{:.3f}"
            for key in ["tau_max", "sigma", "dilatancy_angle"]:
                if key == "tau_max":
                    res[key] = _format.format(round(res[key]/1000, 3))
                elif key == "dilatancy_angle":
                    res[key] = _format.format(res[key][0])
                else:
                    res[key] = _format.format(res[key])

            setattr(self, "MohrTable_{}".format(num), MohrTable(num))
            mohr = getattr(self, "MohrTable_{}".format(num))
            mohr.set_param(res)
            mohr.dell_button.clicked.connect(self._dell_test)
            mohr.plot_button.clicked.connect(self._processing_test)
            self.mohr_test_manager.add_test(mohr)

    def _processing_test(self):
        """Вызов окна обработки опыта"""
        parent = self.sender().parent()
        test_id = int(parent.title()[-1])

        #dialog = TriaxialStaticDialog(self._model._tests[test_id], self)
        # показывает диалог и после нажатия Ok передаёт виджету модель из диалога
        #if dialog.exec() == QDialog.Accepted:
            #self._model._tests[test_id] = dialog.widget._model
            #self._create_test_tables()
            #self._plot()

    def _plot(self):
        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Абсолютная деформация $l_1$, мм")
        self.deviator_ax.set_ylabel("Касательное напряжение τ, МПа")

        self.mohr_ax.clear()
        self.mohr_ax.set_xlabel("Нормальное напряжение σ, МПа")
        self.mohr_ax.set_ylabel("Касательное напряжение τ, МПа")

        plots = Shear_models[statment.current_test].get_plot_data()
        res = Shear_models[statment.current_test].get_test_results()

        if plots is not None:
            for i in range(len(plots["strain"])):
                self.deviator_ax.plot(plots["strain"][i], plots["deviator"][i], **plotter_params["main_line"])
                self.deviator_ax.scatter(plots["strain"][i], plots["deviator"][i], s=20)
                #self.mohr_ax.plot(plots["mohr_x"][i], plots["mohr_y"][i], **plotter_params["main_line"])
            lim = self.deviator_ax.get_xlim()
            self.deviator_ax.set_xlim([lim[0], 7.25])
            self.mohr_ax.scatter(plots["sigma"],plots["tau_max"], color=['r', 'r', 'r'])
            self.mohr_ax.plot(plots["mohr_line_x"], plots["mohr_line_y"], **plotter_params["main_line"])


            self.mohr_ax.plot([], [], label="c" + ", МПа = " + str(res["c"]), color="#eeeeee")
            self.mohr_ax.plot([], [], label="fi" + ", град. = " + str(res["fi"]), color="#eeeeee")
            if res["m"]:
                self.mohr_ax.plot([], [], label="m" + ", МПа$^{-1}$ = " + str(res["m"]), color="#eeeeee")

            self.mohr_ax.set_xlim(*plots["x_lims"])
            self.mohr_ax.set_ylim(*plots["y_lims"])

            self.mohr_ax.legend()

        self.deviator_canvas.draw()
        self.mohr_canvas.draw()

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""
        def save(figure, canvas, size_figure, ax, file_type):
            if canvas == self.mohr_canvas:
                if (ax.get_legend()):
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
            if canvas == self.mohr_canvas:
                ax.get_legend()
                ax.legend()
            canvas.draw()
            return path

        return [save(fig, can, size, ax, "svg") for fig, can, size, ax in zip([self.deviator_figure,
                                                                            self.mohr_figure],
                                                   [self.deviator_canvas, self.mohr_canvas], [[6, 2.4], [3, 1.5]],
                                                                              [self.deviator_ax, self.mohr_ax])]

class ShearWidgetSoilTest(ShearWidget):
    """Класс для табличного отображения параметров кругов Мора"""
    def __init__(self):
        super().__init__()
        self.add_UI()
        self.refresh_test_button = QPushButton("Обновить опыт")
        self.refresh_test_button.clicked.connect(self.refresh)
        self.layout_wiget.insertWidget(0, self.refresh_test_button)
        self.mohr_test_manager.add_test_button.hide()

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.add_parameters_layout = QHBoxLayout()
        self.reference_pressure_array_box = PressureArray()
        self.add_parameters_layout.addWidget(self.reference_pressure_array_box)
        self.add_parameters_layout.addStretch(-1)
        self.layout_wiget.addLayout(self.add_parameters_layout)


        """self.reference_pressure_array_box = QGroupBox("Обжимающие давления")
        self.reference_pressure_array_box_layout = QVBoxLayout()
        self.reference_pressure_array_box.setLayout(self.reference_pressure_array_box_layout)
        self.reference_pressure_array_box.setFixedWidth(600)
        self.reference_pressure_array_box.setFixedHeight(70)
        self.reference_pressure_array_box_layout.setContentsMargins(5, 5, 5, 5)

        self.reference_pressure_array_box_line_1_layout = QHBoxLayout()
        self.reference_pressure_array_box_line_user = QLineEdit()
        self.reference_pressure_array_box_line = QLineEdit()
        self.reference_pressure_array_box_line.setDisabled(True)

        self.reference_pressure_array_box_line_1_label = QLabel("Рассчитанные давления")
        self.reference_pressure_array_box_line_1_label_user = QLabel("Пользовательский массив")
        self.reference_pressure_array_box_line_1_layout.addWidget(self.reference_pressure_array_box_line_1_label)
        self.reference_pressure_array_box_line_1_layout.addWidget(self.reference_pressure_array_box_line)
        self.reference_pressure_array_box_line_1_layout.addWidget(self.reference_pressure_array_box_line_1_label_user)
        self.reference_pressure_array_box_line_1_layout.addWidget(self.reference_pressure_array_box_line_user)
        self.reference_pressure_array_box_layout.addLayout(self.reference_pressure_array_box_line_1_layout)

        self.layout_wiget.addWidget(self.reference_pressure_array_box)
        self.reference_pressure_array_box_layout.addStretch(-1)"""

    def add_test(self, path):
        Shear_models[statment.current_test].add_test(path)
        self._create_test_tables()
        self._plot()

    def get_reference_pressure_array(self):
        try:
            text = self.reference_pressure_array_box_line_user.text()
            reference_pressure_array = [float(x.strip(" ")) for x in text.split(";")]
            if len(reference_pressure_array) >=1:
                assert not (len(reference_pressure_array) < 3), "Недостаточно данных. Введите минимум 3 обжимающих давления"
        except ValueError:
            #QMessageBox.critical(self, "Ошибка", "Введите через запятую значения обжимающих давлений", QMessageBox.Ok)
            return None
        except AssertionError as err:
            QMessageBox.critical(self, "Ошибка", str(err), QMessageBox.Ok)
            return None
        else:
            return reference_pressure_array

    def set_reference_pressure_array(self, reference_pressure_array):
        self.reference_pressure_array_box_line.setText('; '.join([str(i) for i in reference_pressure_array]))

    def set_params(self):
        self.reference_pressure_array_box.set_data()
        self._create_test_tables()
        self._plot()

    #@log_this(app_logger, "debug")
    def refresh(self):
        try:
            Shear_models[statment.current_test].set_test_params()
            self.set_params()
        except KeyError:
            pass

    def clear(self):
        Shear_models[statment.current_test]._tests = []
        Shear_models[statment.current_test]._test_data = AttrDict({"fi": None, "c": None})
        Shear_models[statment.current_test]._test_result = AttrDict({"fi": None, "c": None, "m": None})
        Shear_models[statment.current_test]._test_reference_params = AttrDict({"p_ref": None, "Eref": None})

    def _processing_test(self):
        """Вызов окна обработки опыта"""
        parent = self.sender().parent()
        test_id = int(parent.title()[-1])

        dialog = ShearDilatancyTestDialog(Shear_models[statment.current_test]._tests[test_id], self)
        # показывает диалог и после нажатия Ok передаёт виджету модель из диалога
        if dialog.exec() == QDialog.Accepted:
            Shear_models[statment.current_test]._tests[test_id] = dialog._model
            self._create_test_tables()
            self._plot()

class PressureArray(QGroupBox):
    def __init__(self):
        super().__init__()
        self.add_UI()
        self._checked = None

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.setTitle('Выбор масива обжимающих давлений')
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setFixedHeight(120)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.radiobutton_state_standard = QRadioButton("ГОСТ 12248-2010")
        self.line_state_standard = QLineEdit()
        self.line_state_standard.setDisabled(True)
        self.radiobutton_state_standard.value = "state_standard"
        self.radiobutton_state_standard.toggled.connect(self._onClicked)
        self.layout.addWidget(self.radiobutton_state_standard, 0, 0)
        self.layout.addWidget(self.line_state_standard, 0, 1)

        self.radiobutton_calculated_by_pressure = QRadioButton("Расчетное давление")
        self.line_calculated_by_pressure = QLineEdit()
        self.line_calculated_by_pressure.setDisabled(True)
        self.radiobutton_calculated_by_pressure.value = "calculated_by_pressure"
        self.radiobutton_calculated_by_pressure.toggled.connect(self._onClicked)
        self.layout.addWidget(self.radiobutton_calculated_by_pressure, 1, 0)
        self.layout.addWidget(self.line_calculated_by_pressure, 1, 1)

        self.radiobutton_set_by_user = QRadioButton("Ручные ступени давления")
        self.line_set_by_user = QLineEdit()
        self.line_set_by_user.setDisabled(True)
        self.radiobutton_set_by_user.value = "set_by_user"
        self.radiobutton_set_by_user.toggled.connect(self._onClicked)
        self.layout.addWidget(self.radiobutton_set_by_user, 2, 0)
        self.layout.addWidget(self.line_set_by_user, 2, 1)

    def _onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self._checked = radioButton.value
            statment[statment.current_test].mechanical_properties.pressure_array["current"] = \
                statment[statment.current_test].mechanical_properties.pressure_array[self._checked]

    def set_data(self):
        data = statment[statment.current_test].mechanical_properties.pressure_array
        def str_array(array):
            if array is None:
                return "-"
            else:
                s = ""
                for i in array:
                    s += f"{str(i)}; "
                return s

        checked: bool = False
        for key in data:
            if key != "current":
                line = getattr(self, f"line_{key}")
                radiobutton = getattr(self, f"radiobutton_{key}")
                line.setText(str_array(data[key]))
                if data[key] is None:
                    radiobutton.setDisabled(True)
                else:
                    radiobutton.setDisabled(False)
                if data[key] == data["current"] and not checked:
                    radiobutton.setChecked(True)
                    checked = True

    def get_checked(self):
        return self._checked


class TriaxialStaticLoading_Sliders(QWidget):
    """Виджет с ползунками для регулирования значений переменных.
    При перемещении ползунков отправляет 2 сигнала."""
    signal = pyqtSignal(object)
    def __init__(self, params):
        """Определяем основную структуру данных"""
        super().__init__()
        self._params = params

        self._activate = False

        self._createUI("Настройки отрисовки", params)

    def _createUI(self, name, params):
        self.layout = QVBoxLayout(self)
        setattr(self, "{}_box".format(name), QGroupBox(name))
        box = getattr(self, "{}_box".format(name))
        setattr(self, "{}_box_layout".format(name), QVBoxLayout())
        box_layout = getattr(self, "{}_box_layout".format(name))

        for var in params:
            if params[var]:
                # Создадим подпись слайдера
                label = QLabel(params[var])  # Создааем подпись
                label.setFixedWidth(150)  # Фиксируем размер подписи

                # Создадим слайдер
                setattr(self, "{name_var}_slider".format(name_var=var),
                        Slider(Qt.Horizontal))
                slider = getattr(self, "{name_var}_slider".format(name_var=var))

                # Создадим строку со значнием
                setattr(self, "{name_var}_label".format(name_var=var), QLabel())
                slider_label = getattr(self, "{name_var}_label".format(name_var=var))
                slider_label.setFixedWidth(40)
                # slider_label.setStyleSheet(style)

                # Создадтм строку для размещения
                setattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var), QHBoxLayout())
                line = getattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var))

                # СРазместим слайдер и подпись на строке
                line.addWidget(label)
                line.addWidget(slider)
                line.addWidget(slider_label)
                box_layout.addLayout(line)
                func = getattr(self, "_sliders_moove".format(name_widget=name, name_var=var))
                slider.sliderMoved.connect(func)
                release = getattr(self, "_sliders_released".format(name_widget=name, name_var=var))
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
                box_layout.addLayout(line)

        box.setLayout(box_layout)

        self.layout.addWidget(box)
        self.layout.setContentsMargins(5, 5, 5, 5)

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

    def _sliders_moove(self):
        """Обработка перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params(self._params)
            self._set_slider_labels_params(params)

    def _sliders_released(self):
        """Обработка окончания перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params(self._params)
            self._set_slider_labels_params(params)
            self.signal.emit(params)

    def set_sliders_params(self, params):
        """становка заданых значений на слайдеры"""
        for var in params:
            current_slider = getattr(self, "{name_var}_slider".format(name_var=var))
            current_slider.set_borders(*params[var]["borders"])
            current_slider.set_value(params[var]["value"])

        self._activate = True

        self._sliders_moove()

class ShearDilatancyTestDialog(QDialog):
    def __init__(self, test, parent=None):
        super(ShearDilatancyTestDialog, self).__init__(parent)
        self.resize(1200, 700)
        self.setWindowTitle("Обработка опыта")
        self._model = test

        self.layout = QVBoxLayout()
        self.shear_dilatancy = ModelShearDilatancyUI()
        self.layout.addWidget(self.shear_dilatancy)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.shear_dilatancy.chose_volumometer_button_group.buttonClicked.connect(self._deviator_volumeter)
        self.shear_dilatancy.slider_cut.sliderMoved.connect(self._cut_slider_deviator_moove)

        self.deviator_loading_sliders = TriaxialStaticLoading_Sliders({"E50": "Наклон прямолинейного участка",
                                                                       "fail_strain": "Деформация разрушения",
                                                                       "residual_strength": "Остаточная прочность",
                                                                       "residual_strength_param": "Изгиб остаточной прочности",
                                                                       "qocr": "Значение дивиатора OCR",
                                                                       "poisson": "Коэффициент Пуассона",
                                                                       "dilatancy": "Угол дилатансии",
                                                                       "volumetric_strain_xc": "Объемн. деформ. в пике"})
        self.deviator_loading_sliders.setFixedHeight(180)
        self.deviator_loading_sliders.signal[object].connect(self._deviator_loading_sliders_moove)
        self.shear_dilatancy.graph_layout.addWidget(self.deviator_loading_sliders)


        self._connect_model_Ui()
        self._plot_deviator_loading()

        self.deviator_loading_sliders.set_sliders_params(self._model.get_draw_params())

        self.setLayout(self.layout)

    def _connect_model_Ui(self):
        """Связь слайдеров с моделью"""
        self._cut_slider_deviator_set_len(len(self._model._test_data.strain))
        self._cut_slider_deviator_set_val(self._model.get_borders())

        self._deviator_volumeter_current_vol(self._model.get_current_volume_strain())

    def _plot_deviator_loading(self):
        try:
            plot_data = self._model.get_plot_data()
            res = self._model.get_test_results()
            self.shear_dilatancy.plot(plot_data, res)
        except KeyError:
            pass

    def _deviator_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if self._model.check_none():
            self._model.choise_volume_strain(button.text())
            self._cut_slider_deviator_set_val(self._model.get_borders())
            self._plot_deviator_loading()

    def _deviator_volumeter_current_vol(self, current_volume_strain):
        """Чтение с модели, какие волюмометры рабочие и заполнение в интерфейсе"""
        if current_volume_strain["current"] == "pore_volume":
            self.shear_dilatancy.chose_volumometer_radio_button_1.setChecked(True)
        else:
            self.shear_dilatancy.chose_volumometer_radio_button_2.setChecked(True)

        if current_volume_strain["pore_volume"]:
            self.shear_dilatancy.chose_volumometer_radio_button_1.setDisabled(False)
        else:
            self.shear_dilatancy.chose_volumometer_radio_button_1.setDisabled(True)

        if current_volume_strain["cell_volume"]:
            self.shear_dilatancy.chose_volumometer_radio_button_2.setDisabled(False)
        else:
            self.shear_dilatancy.chose_volumometer_radio_button_2.setDisabled(True)

    def _cut_slider_deviator_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.shear_dilatancy.slider_cut.setMinimum(0)
        self.shear_dilatancy.slider_cut.setMaximum(len)

    def _cut_slider_deviator_set_val(self, vals):
        """Установка значений слайдера обрезки"""
        self.shear_dilatancy.slider_cut.setLow(vals["left"])
        self.shear_dilatancy.slider_cut.setHigh(vals["right"])

    def _cut_slider_deviator_moove(self):
        """Обработчик перемещения слайдера обрезки"""
        if Shear_Dilatancy_models[statment.current_test].check_none():
            if (int(self.shear_dilatancy.slider_cut.high()) - int(self.shear_dilatancy.slider_cut.low())) >= 50:
                self._model.change_borders(
                    int(self.shear_dilatancy.slider_cut.low()),
                    int(self.shear_dilatancy.slider_cut.high()))
            self._plot_deviator_loading()

    def _deviator_loading_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            self._model.set_draw_params(params)
            self._plot_deviator_loading()
            self._connect_model_Ui()
        except KeyError:
            pass



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = ShearWidget()
    ex.show()
    sys.exit(app.exec_())
