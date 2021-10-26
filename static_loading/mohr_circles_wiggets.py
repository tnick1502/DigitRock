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

from static_loading.mohr_circles_test_model import ModelMohrCircles, ModelMohrCirclesSoilTest
from static_loading.triaxial_static_widgets_UI import ModelTriaxialItemUI
from static_loading.triaxial_static_test_widgets import TriaxialStaticDialog, TriaxialStaticDialogSoilTest
from general.initial_tables import Table
from configs.plot_params import plotter_params
from general.general_functions import read_json_file, AttrDict

plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
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

        self.set_param({"sigma_3": "",
                        "sigma_1": "",
                        "u": ""})

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
                                    ["σ3', МПа",
                                     "σ1', МПа",
                                     "u, МПа"],
                                    [param["sigma_3"], param["sigma_1"], param["u"]]], "Stretch")

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

class MohrWidget(QWidget):
    """Класс для табличного отображения параметров кругов Мора"""

    def __init__(self):
        super().__init__()

        self._model = ModelMohrCircles()

        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.14, "wspace": 0.12, "hspace": 0.07, "left": 0.1}

        self.item_identification = ModelTriaxialItemUI()
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
                self._model.add_test(path)
                self._create_test_tables()
                self._plot()
            except:
                QMessageBox.critical(self, "Ошибка", "Неправильно выбран файл", QMessageBox.Ok)

    def _dell_test(self):
        """Удаление опыта"""
        parent = self.sender().parent()
        test_id = int(parent.title()[-1])
        self._model.dell_test(test_id)
        self._create_test_tables()
        self._plot()

    def _create_test_tables(self):
        """Отрисовка всех опытов а менеджере"""
        for Table in self.mohr_test_manager.findChildren(MohrTable):
            Table.deleteLater()

        for num, test in enumerate(self._model.get_tests()):
            res = test.deviator_loading.get_test_results()
            res["sigma_1"] = res["sigma_3"] + res["qf"]

            _format = "{:.3f}"
            for key in ["sigma_1", "sigma_3", "u"]:
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

        dialog = TriaxialStaticDialog(self._model._tests[test_id], self)
        # показывает диалог и после нажатия Ok передаёт виджету модель из диалога
        if dialog.exec() == QDialog.Accepted:
            self._model._tests[test_id] = dialog.widget._model
            self._create_test_tables()
            self._plot()

    def _plot(self):
        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, МПа")

        self.mohr_ax.clear()
        self.mohr_ax.set_xlabel("σ, МПа")
        self.mohr_ax.set_ylabel("τ, МПа")

        plots = self._model.get_plot_data()
        res = self._model.get_test_results()

        if plots is not None:
            for i in range(len(plots["strain"])):
                self.deviator_ax.plot(plots["strain"][i], plots["deviator"][i], **plotter_params["main_line"])
                self.mohr_ax.plot(plots["mohr_x"][i], plots["mohr_y"][i], **plotter_params["main_line"])

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

class MohrWidgetSoilTest(MohrWidget):
    """Класс для табличного отображения параметров кругов Мора"""
    def __init__(self):
        super().__init__()
        self.add_UI()
        self._model = ModelMohrCirclesSoilTest()
        self.refresh_test_button = QPushButton("Обновить опыт")
        self.refresh_test_button.clicked.connect(self.refresh)
        self.layout_wiget.insertWidget(0, self.refresh_test_button)
        self.mohr_test_manager.add_test_button.hide()

    def add_UI(self):
        """Дополнительный интерфейс"""
        self.reference_pressure_array_box = PressureArray()
        self.layout_wiget.addWidget(self.reference_pressure_array_box)

    def add_test(self, path):
        self._model.add_test(path)
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

    def set_params(self, params, reset=True):
        self.reference_pressure_array_box.set_data(params.pressure_array, reset)
        reference_pressure_array = params.pressure_array[self.reference_pressure_array_box.get_checked()]
        """reference_pressure_array_user = self.get_reference_pressure_array()
        reference_pressure_array = ModelMohrCirclesSoilTest.define_reference_pressure_array(
            params.build_press, params.pit_depth,
            params.physical_properties.depth, params.physical_properties.e, params.physical_properties.Il,
            params.physical_properties.type_ground, params.K0)
        self.set_reference_pressure_array(reference_pressure_array)

        if reference_pressure_array_user:
            reference_pressure_array = reference_pressure_array_user"""

        if reference_pressure_array:
            self._model.set_reference_pressure_array(reference_pressure_array)
            self._model.set_test_params(params)
            self._model._test_modeling()
            self._create_test_tables()
            self._plot()

    def refresh(self):
        params = self._model.get_test_params()
        if params:
            self.set_params(params, reset=False)

    def clear(self):

        self._model._tests = []
        self._model._test_data = AttrDict({"fi": None, "c": None})
        self._model._test_result = AttrDict({"fi": None, "c": None, "m": None})
        self._model._test_reference_params = AttrDict({"p_ref": None, "Eref": None})

    def _processing_test(self):
        """Вызов окна обработки опыта"""
        parent = self.sender().parent()
        test_id = int(parent.title()[-1])

        dialog = TriaxialStaticDialogSoilTest(self._model._tests[test_id], self)
        # показывает диалог и после нажатия Ok передаёт виджету модель из диалога
        if dialog.exec() == QDialog.Accepted:
            self._model._tests[test_id] = dialog.widget._model
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

        self.radiobutton_state_standard = QRadioButton("ГОСТ 12248.3-2020")
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

    def set_data(self, data, reset=True):
        def str_array(array):
            if array is None:
                return "-"
            else:
                s = ""
                for i in array:
                    s += f"{str(i)}; "
                return s
        for key in data:
            line = getattr(self, f"line_{key}")
            radiobutton = getattr(self, f"radiobutton_{key}")
            line.setText(str_array(data[key]))
            if data[key] is None:
                radiobutton.setDisabled(True)
            else:
                radiobutton.setDisabled(False)

        if reset:
            if data["set_by_user"] is not None:
                self.radiobutton_set_by_user.setChecked(True)
            elif data["calculated_by_pressure"] is not None:
                self.radiobutton_calculated_by_pressure.setChecked(True)
            elif data["state_standard"] is not None:
                self.radiobutton_state_standard.setChecked(True)

    def get_checked(self):
        return self._checked





if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = MohrWidget()
    ex.show()
    sys.exit(app.exec_())
