from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout, \
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading
import numpy as np

from general.general_functions import create_path
from general.tab_view import TabMixin
from plaxis_average.plaxis_avereged_widget import AverageWidget
from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from excel_statment.initial_statment_widgets import TriaxialStaticStatment
from excel_statment.initial_tables import LinePhysicalProperties
from general.save_widget import Save_Dir
from excel_statment.functions import set_cell_data
from excel_statment.position_configs import c_fi_E_PropertyPosition, MechanicalPropertyPosition
from general.reports import report_consolidation, report_FCE, report_FC, report_FC_KN, report_E, report_FC_NN, \
    report_FC_res, zap
from static_loading.triaxial_static_widgets_UI import ModelTriaxialItemUI, ModelTriaxialFileOpenUI, \
    ModelTriaxialReconsolidationUI, \
    ModelTriaxialConsolidationUI, ModelTriaxialDeviatorLoadingUI
from general.general_widgets import Float_Slider
from configs.styles import style
from singletons import E_models, FC_models, statment
from loggers.logger import app_logger, log_this, handler
from tests_log.widget import TestsLogWidget
from tests_log.equipment import static
from tests_log.test_classes import TestsLogTriaxialStatic
import os
from version_control.configs import actual_version
from general.tab_view import AppMixin

__version__ = actual_version

from authentication.request_qr import request_qr
from authentication.control import control
from saver import XMLWidget
from general.general_statement import StatementGenerator
from metrics.session_writer import SessionWriter
from general.movie_label import Loader


class StaticProcessingWidget(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""

    def __init__(self, model=None):
        super().__init__()

        self.open_log_file = ModelTriaxialFileOpenUI()
        self.log_file_path = None

        self.item_identification = ModelTriaxialItemUI()
        self.item_identification.setFixedHeight(330)
        self.item_identification.setFixedWidth(350)
        self.reconsolidation = ModelTriaxialReconsolidationUI()
        self.line = QHBoxLayout()
        self.line.addWidget(self.item_identification)
        self.line_for_phiz = QVBoxLayout()
        self.line.addLayout(self.line_for_phiz)

        self.consolidation = ModelTriaxialConsolidationUI()
        self.point_identificator = None
        self.point_identificator_deviator = None
        self.consolidation.setFixedHeight(500)
        self.deviator_loading = ModelTriaxialDeviatorLoadingUI()
        self.deviator_loading.setFixedHeight(600)
        self.reconsolidation.setFixedHeight(300)

        self.deviator_loading.combo_box.activated.connect(self._combo_plot_deviator_changed)
        self.deviator_loading.dilatancy_radio_btn.clicked.connect(self._combo_plot_deviator_changed)

        self._create_UI()
        self._wigets_connect()

        # if model:
        # self.set_model(model)
        # else:
        # self._model = ModelTriaxialStaticLoad()

    def _create_UI(self):
        self.layout_wiget = QVBoxLayout()
        self.layout_wiget.addWidget(self.open_log_file)
        self.layout_wiget.addLayout(self.line)
        self.layout_wiget.addWidget(self.deviator_loading)
        self.layout_wiget.addWidget(self.consolidation)
        self.layout_wiget.addWidget(self.reconsolidation)
        # self.layout_wiget.addWidget(self.deviator_loading)

        self.wiget = QWidget()
        self.wiget.setLayout(self.layout_wiget)
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setWidget(self.wiget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.area)

    def _wigets_connect(self):
        self.open_log_file.open_button.clicked.connect(self._open_file)

        self.deviator_loading.chose_volumometer_button_group.buttonClicked.connect(self._deviator_volumeter)
        self.consolidation.chose_volumometer_button_group.buttonClicked.connect(self._consolidation_volumeter)
        self.deviator_loading.split_deviator_radio_button.clicked.connect(self._split_deviator)

        self.consolidation.function_replacement_button_group.buttonClicked.connect(
            self._consolidation_interpolation_type)

        self.deviator_loading.slider_cut.sliderMoved.connect(self._cut_slider_deviator_moove)
        self.consolidation.slider_cut.sliderMoved.connect(self._cut_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderMoved.connect(self._interpolate_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderReleased.connect(
            self._interpolate_slider_consolidation_release)

        self.consolidation.sqrt_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.sqrt_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.sqrt_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.consolidation.log_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.log_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.log_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.deviator_loading.deviator_canvas.mpl_connect('button_press_event', self._canvas_deviator_click)
        self.deviator_loading.deviator_canvas.mpl_connect("motion_notify_event", self._canvas_deviator_on_moove)
        self.deviator_loading.deviator_canvas.mpl_connect('button_release_event', self._canvas_deviator_on_release)

    def _open_file(self, path=None):
        if not path:
            self.log_file_path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        else:
            self.log_file_path = path

        if self.log_file_path:
            try:
                self._model.set_test_file_path(self.log_file_path)
                self._plot_reconsolidation()
                self._plot_consolidation_sqrt()
                self._plot_consolidation_log()
                self._plot_deviator_loading()

                self._connect_model_Ui()
                if not path:
                    self.open_log_file.set_path(self.log_file_path)

            except (ValueError, IndexError):
                pass

    def _connect_model_Ui(self):
        """Связь слайдеров с моделью"""
        self._cut_slider_deviator_set_len(len(E_models[statment.current_test].deviator_loading._test_data.strain))
        self._cut_slider_deviator_set_val(E_models[statment.current_test].deviator_loading.get_borders())
        self._cut_slider_consolidation_set_len(len(E_models[statment.current_test].consolidation._test_data.time))

        self._deviator_volumeter_current_vol(
            E_models[statment.current_test].deviator_loading.get_current_volume_strain())
        self._consolidation_volumeter_current_vol(
            E_models[statment.current_test].consolidation.get_current_volume_strain())

    def _plot_reconsolidation(self):
        try:
            plot_data = E_models[statment.current_test].reconsolidation.get_plot_data()
            res = E_models[statment.current_test].reconsolidation.get_test_results()
            self.reconsolidation.plot(plot_data, res)
        except KeyError:
            pass

    def _plot_consolidation_sqrt(self):
        try:
            plot_data = E_models[statment.current_test].consolidation.get_plot_data_sqrt()
            res = E_models[statment.current_test].consolidation.get_test_results()
            self.consolidation.plot_sqrt(plot_data, res)
        except KeyError:
            pass

    def _plot_consolidation_log(self):
        try:
            plot_data = E_models[statment.current_test].consolidation.get_plot_data_log()
            res = E_models[statment.current_test].consolidation.get_test_results()
            self.consolidation.plot_log(plot_data, res)
        except KeyError:
            pass

    def _plot_deviator_loading(self, plot_dots):
        try:
            plot_data = E_models[statment.current_test].deviator_loading.get_plot_data()
            res = E_models[statment.current_test].deviator_loading.get_test_results()
            self.deviator_loading.plot(plot_data, res, plot_dots=plot_dots)
        except KeyError:
            pass

    def _deviator_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if E_models[statment.current_test].deviator_loading.check_none():
            E_models[statment.current_test].deviator_loading.choise_volume_strain(button.text())
            self._cut_slider_deviator_set_val(E_models[statment.current_test].deviator_loading.get_borders())
            self._plot_deviator_loading()

    def _split_deviator(self, is_split_deviator):
        if E_models[statment.current_test].deviator_loading.check_none():
            E_models[statment.current_test].deviator_loading.set_split_deviator(is_split_deviator)
            self._plot_deviator_loading()

    def _deviator_volumeter_current_vol(self, current_volume_strain):
        """Чтение с модели, какие волюмометры рабочие и заполнение в интерфейсе"""
        if current_volume_strain["current"] == "pore_volume":
            self.deviator_loading.chose_volumometer_radio_button_1.setChecked(True)
        else:
            self.deviator_loading.chose_volumometer_radio_button_2.setChecked(True)

        if current_volume_strain["pore_volume"]:
            self.deviator_loading.chose_volumometer_radio_button_1.setDisabled(False)
        else:
            self.deviator_loading.chose_volumometer_radio_button_1.setDisabled(True)

        if current_volume_strain["cell_volume"]:
            self.deviator_loading.chose_volumometer_radio_button_2.setDisabled(False)
        else:
            self.deviator_loading.chose_volumometer_radio_button_2.setDisabled(True)

    def _cut_slider_deviator_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.deviator_loading.slider_cut.setMinimum(0)
        self.deviator_loading.slider_cut.setMaximum(len)

    def _cut_slider_deviator_set_val(self, vals):
        """Установка значений слайдера обрезки"""
        self.deviator_loading.slider_cut.setLow(vals["left"])
        self.deviator_loading.slider_cut.setHigh(vals["right"])

    def _cut_slider_deviator_moove(self):
        """Обработчик перемещения слайдера обрезки"""
        if E_models[statment.current_test].deviator_loading.check_none():
            if (int(self.deviator_loading.slider_cut.high()) - int(self.deviator_loading.slider_cut.low())) >= 50:
                E_models[statment.current_test].deviator_loading.change_borders(
                    int(self.deviator_loading.slider_cut.low()),
                    int(self.deviator_loading.slider_cut.high()))
            self._plot_deviator_loading()

    def _consolidation_volumeter_current_vol(self, current_volume_strain):
        """Чтение с модели, какие волюмометры рабочие и заполнение в интерфейсе"""
        if current_volume_strain["current"] == "pore_volume":
            self.consolidation.chose_volumometer_radio_button_1.setChecked(True)
        else:
            self.consolidation.chose_volumometer_radio_button_2.setChecked(True)

        if current_volume_strain["pore_volume"]:
            self.consolidation.chose_volumometer_radio_button_1.setDisabled(False)
        else:
            self.consolidation.chose_volumometer_radio_button_1.setDisabled(True)

        if current_volume_strain["cell_volume"]:
            self.consolidation.chose_volumometer_radio_button_2.setDisabled(False)
        else:
            self.consolidation.chose_volumometer_radio_button_2.setDisabled(True)

    def _consolidation_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if E_models[statment.current_test].consolidation.check_none():
            E_models[statment.current_test].consolidation.choise_volume_strain(button.text())
            self._cut_slider_consolidation_set_len(len(E_models[statment.current_test].consolidation._test_data.time))
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _cut_slider_consolidation_set_len(self, len):
        self.consolidation.slider_cut.setMinimum(0)
        self.consolidation.slider_cut.setMaximum(len)
        self.consolidation.slider_cut.setLow(0)
        self.consolidation.slider_cut.setHigh(len)

    def _cut_slider_consolidation_moove(self):
        if E_models[statment.current_test].consolidation.check_none():
            if (int(self.consolidation.slider_cut.high()) - int(self.consolidation.slider_cut.low())) >= 50:
                E_models[statment.current_test].consolidation.change_borders(int(self.consolidation.slider_cut.low()),
                                                                             int(self.consolidation.slider_cut.high()))
                self._plot_consolidation_sqrt()
                self._plot_consolidation_log()

    def _consolidation_interpolation_type(self, button):
        """Смена метода интерполяции консолидации"""
        if self._model.deviator_loading.check_none():
            if button.text() == "Интерполяция полиномом":
                interpolation_type = "poly"
                param = 8
                self.consolidation.function_replacement_slider.set_borders(5, 15)
                self.consolidation.function_replacement_slider.set_value(8)
            elif button.text() == "Интерполяция Эрмита":
                interpolation_type = "ermit"
                param = 2
                self.consolidation.function_replacement_slider.set_borders(0, 5)
                self.consolidation.function_replacement_slider.set_value(2)

            E_models[statment.current_test].consolidation.set_interpolation_param(param)
            E_models[statment.current_test].consolidation.set_interpolation_type(interpolation_type)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _interpolate_slider_consolidation_moove(self):
        """Перемещение слайдера интерполяции. Не производит обработки, только отрисовка интерполированной кривой"""
        if E_models[statment.current_test].consolidation.check_none():
            param = self.consolidation.function_replacement_slider.current_value()
            plot = E_models[statment.current_test].consolidation.set_interpolation_param(param)
            self.consolidation.plot_interpolate(plot)

    def _interpolate_slider_consolidation_release(self):
        """Обработка консолидации при окончании движения слайдера"""
        if E_models[statment.current_test].consolidation.check_none():
            E_models[statment.current_test].consolidation.change_borders(int(self.consolidation.slider_cut.low()),
                                                                         int(self.consolidation.slider_cut.high()))
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _canvas_click(self, event):
        """Метод обрабатывает нажатие на канвас"""
        if event.canvas is self.consolidation.sqrt_canvas:
            canvas = "sqrt"
        if event.canvas is self.consolidation.log_canvas:
            canvas = "log"
        if event.button == 1 and event.xdata and event.ydata:
            self.point_identificator = E_models[statment.current_test].consolidation.define_click_point(
                float(event.xdata),
                float(event.ydata), canvas)

    def _canvas_deviator_click(self, event):
        """Метод обрабатывает нажатие на канвас"""
        if event.button == 1 and event.xdata and event.ydata:
            self.point_identificator_deviator = E_models[statment.current_test].deviator_loading.define_click_point(
                float(event.xdata),
                float(event.ydata))

    def _canvas_deviator_on_moove(self, event):
        """Метод обрабаотывает перемещение зажатой точки"""
        if self.point_identificator_deviator and event.xdata and event.ydata and event.button == 1:
            E_models[statment.current_test].deviator_loading.moove_catch_point(float(event.xdata), float(event.ydata),
                                                                               self.point_identificator_deviator)
            self._plot_deviator_loading()

    def _canvas_deviator_on_release(self, event):
        """Метод обрабатывает итпуск зажатой точки"""
        self.point_identificator_deviator = None

    def _canvas_on_moove(self, event):
        """Метод обрабаотывает перемещение зажатой точки"""
        if event.canvas is self.consolidation.sqrt_canvas:
            canvas = "sqrt"
        if event.canvas is self.consolidation.log_canvas:
            canvas = "log"

        if self.point_identificator and event.xdata and event.ydata and event.button == 1:
            E_models[statment.current_test].consolidation.moove_catch_point(float(event.xdata), float(event.ydata),
                                                                            self.point_identificator,
                                                                            canvas)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _canvas_on_release(self, event):
        """Метод обрабатывает итпуск зажатой точки"""
        self.point_identificator = None

    def _combo_plot_deviator_changed(self):
        self._plot_deviator_loading()

    def get_test_results(self):
        return E_models[statment.current_test].get_test_results()


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
                        Float_Slider(Qt.Horizontal))
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
            if params[var]["value"]:
                current_slider.set_borders(*params[var]["borders"])
            current_slider.set_value(params[var]["value"])

        self._activate = True

        self._sliders_moove()


class StaticSoilTestWidget(TabMixin, StaticProcessingWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.open_log_file.setParent(None)
        self.layout_wiget.removeWidget(self.open_log_file)
        self.open_log_file.deleteLater()
        self.open_log_file = None

        self.deviator_loading_sliders = TriaxialStaticLoading_Sliders({"fail_strain": "Деформация разрушения",
                                                                       "residual_strength": "Остаточная прочность",
                                                                       "residual_strength_param": "Изгиб остаточной прочности",
                                                                       "qocr": "Значение дивиатора OCR",
                                                                       "poisson": "Коэффициент Пуассона",
                                                                       "dilatancy": "Угол дилатансии",
                                                                       "volumetric_strain_xc": "Объемн. деформ. в пике",
                                                                       "Eur": "Модуль разгрузки",
                                                                       "amplitude_1": "Амп. дев. (низк. час.)",
                                                                       "amplitude_2": "Амп. дев. (сред. час.)",
                                                                       "amplitude_3": "Амп. дев. (выс. час.)",
                                                                       "hyp_ratio": "Коэффициент влияния"
                                                                       })

        self.deviator_loading_sliders.setFixedHeight(280)

        self.deviator_loading_sliders_unload_start_y_slider = TriaxialStaticLoading_Sliders({"unload_start_y": "Сдвиг разгрузки"})
        box = getattr(self.deviator_loading_sliders_unload_start_y_slider, "{}_box".format("Настройки отрисовки"))
        box.setTitle('')
        self.deviator_loading_sliders_unload_start_y_slider.setFixedHeight(80)


        self.consolidation_sliders = TriaxialStaticLoading_Sliders({"max_time": "Время испытания",
                                                                    "volume_strain_90": "Объемная деформация в Cv"})
        self.consolidation_sliders.setFixedHeight(90)

        self.consolidation.graph_layout.addWidget(self.consolidation_sliders)
        self.deviator_loading.graph_layout.addWidget(self.deviator_loading_sliders)
        self.deviator_loading.graph_layout.addWidget(self.deviator_loading_sliders_unload_start_y_slider)

        self.consolidation.setFixedHeight(500 + 90)
        self.deviator_loading.setFixedHeight(530 + 180 + 60 + 100)

        self.deviator_loading_sliders.signal[object].connect(self._deviator_loading_sliders_moove)
        self.deviator_loading_sliders_unload_start_y_slider.signal[object].connect(self._deviator_loading_sliders_unload_start_y_slider_moove)

        self.consolidation_sliders.signal[object].connect(self._consolidation_sliders_moove)

    def refresh(self):
        try:
            E_models[statment.current_test].set_test_params()
            self.deviator_loading_sliders.set_sliders_params(
                E_models[statment.current_test].get_deviator_loading_draw_params())

            self.deviator_loading_sliders_unload_start_y_slider.set_sliders_params(
                E_models[statment.current_test].get_deviator_loading_draw_params_unload_start_y())

            self.consolidation_sliders.set_sliders_params(
                E_models[statment.current_test].get_consolidation_draw_params())

            self._plot_reconsolidation()
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def set_params(self, param=None, plot_dots=True):
        try:
            self.deviator_loading_sliders.set_sliders_params(
                E_models[statment.current_test].get_deviator_loading_draw_params())

            self.deviator_loading.split_deviator_radio_button.setChecked(
                E_models[statment.current_test].deviator_loading.get_split_deviator())

            self.deviator_loading_sliders_unload_start_y_slider.set_sliders_params(
                E_models[statment.current_test].get_deviator_loading_draw_params_unload_start_y())

            self.consolidation_sliders.set_sliders_params(
                E_models[statment.current_test].get_consolidation_draw_params())

            self._plot_reconsolidation()
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._plot_deviator_loading(plot_dots)
            self._connect_model_Ui()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _consolidation_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            E_models[statment.current_test].set_consolidation_draw_params(params)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _deviator_loading_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            E_models[statment.current_test].set_deviator_loading_draw_params(params)
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _deviator_loading_sliders_unload_start_y_slider_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            E_models[statment.current_test].set_deviator_loading_draw_params_unload_start_y(params)
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass


class StatickProcessingApp(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()

        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = TriaxialStaticStatment()
        self.tab_2 = StaticProcessingWidget()
        self.tab_3 = MohrWidget()
        self.tab_4 = Save_Dir()
        # self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Е")
        self.tab_widget.addTab(self.tab_3, "Опыт FC")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.signal[object].connect(self.tab_2.item_identification.set_data)
        self.tab_1.signal[object].connect(self.tab_3.item_identification.set_data)
        self.tab_1.statment_directory[str].connect(self.set_save_directory)
        self.tab_4.save_button.clicked.connect(self.save_report)
        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

    def save_report(self):
        try:
            assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
            # assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            read_parameters = self.tab_1.open_line.get_data()

            test_parameter = {"equipment": read_parameters["equipment"],
                              "mode": "КД, девиаторное нагружение в кинематическом режиме",
                              "sigma_3": self.tab_2._model.deviator_loading._test_params.sigma_3,
                              "K0": "1",
                              "h": 76,
                              "d": 38}

            test_result = self.tab_2.get_test_results()

            save = self.tab_4.arhive_directory + "/" + self.tab_1.get_lab_number().replace("/", "-")
            save = save.replace("*", "")
            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            data_customer = self.tab_1.get_customer_data()
            if params.date:
                data_customer.data = params.date

            if read_parameters["test_type"] == "Трёхосное сжатие (E)":
                assert self.tab_2._model.deviator_loading._test_params.sigma_3, "Не загружен файл опыта"
                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-ДН" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " + \
                       data_customer["object_number"] + " ТС Р" + ".pdf"

                report_consolidation(save + "/" + Name, data_customer,
                                     self.tab_1.get_physical_data(), self.tab_1.get_lab_number(),
                                     os.getcwd() + "/project_data/",
                                     test_parameter, test_result,
                                     (*self.tab_2.consolidation.save_canvas(),
                                      *self.tab_2.deviator_loading.save_canvas()), "{:.2f}".format(__version__))

            elif read_parameters["test_type"] == "Трёхосное сжатие (F, C, E)":
                assert self.tab_3._model._test_result.fi, "Не загружен файл опыта"
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = self.tab_3._model.get_sigma_3_1()
                test_result["c"], test_result["fi"] = self.tab_3._model.get_test_results()["c"], \
                                                      self.tab_3._model.get_test_results()["fi"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-КМ" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + \
                       " " + data_customer["object_number"] + " ТД" + ".pdf"

                report_FCE(save + "/" + Name, data_customer, self.tab_1.get_physical_data(),
                           self.tab_1.get_lab_number(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                           (*self.tab_2.deviator_loading.save_canvas(),
                            *self.tab_3.save_canvas()), "{:.2f}".format(__version__))

            shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)
            QMessageBox.about(self, "Сообщение", "Успешно сохранено")

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

    def set_save_directory(self, signal):
        read_parameters = self.tab_1.open_line.get_data()
        self.tab_4.set_directory(signal, read_parameters["test_type"])


class StatickSoilTestApp(AppMixin, QWidget):

    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()

        self.tab_1 = TriaxialStaticStatment()

        self.tab_2 = StaticSoilTestWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)

        self.tab_3 = MohrWidgetSoilTest()
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_4 = Save_Dir({
                "standart_E": "Стандардный E",
                "standart_E50": "Стандардный E50",
                "E_E50": "Совместный E/E50",
                "plaxis_m": "Plaxis/Midas m",
                "plaxis": "Plaxis/Midas",
                "user_define_1": "Пользовательский с ε50",
                "vibro": "Вибропрочность",
                "vibroNN": "КриовиброНН",
                "standart_E50_with_dilatancy": "Е50 с дилатнсией",
                "E_E50_with_dilatancy": "E/Е50 с дилатнсией",
                "standart_E50_with_dilatancy": "Е50 с дилатнсией"
            }, qr=True, additional_dirs=["plaxis_log_E50", "plaxis_log_FC"], plaxis_btn=True, asis_btn=True)

        self.tab_4.popIn.connect(self.addTab)
        self.tab_4.popOut.connect(self.removeTab)
        # self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Е")
        self.tab_widget.addTab(self.tab_3, "Опыт FC")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.signal[bool].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_4.update(x))

        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_pickle.clicked.connect(self.save_pickle)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_4.jornal_button.clicked.connect(self.jornal)

        self.save_massage = True

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line_for_phiz.addWidget(self.physical_line_1)
        self.tab_2.line_for_phiz.addStretch(-1)
        self.physical_line_1.refresh_button.clicked.connect(self.call_tab2_refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3.refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)

        self.xml_button = QPushButton("Выгнать xml")
        self.xml_button.clicked.connect(self.xml)
        self.tab_4.advanced_box_layout.insertWidget(3, self.xml_button)

        self.excel_statment_button = QPushButton("Сводная ведомость excel")
        self.excel_statment_button.clicked.connect(self.save_excel)
        self.tab_4.advanced_box_layout.insertWidget(4, self.excel_statment_button)

        self.average_button = QPushButton("Усреднение кривых по ИГЭ")
        self.average_button.clicked.connect(self.average)
        self.tab_4.advanced_box_layout.insertWidget(3, self.average_button)
        # self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)

        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

        self.plaxis_log_path = os.path.join(statment.save_dir.save_directory, "plaxis_log")

        self.tab_1.open_line.combo_changes_signal.connect(self.on_test_type_changed)

        self.tab_4._report_types_widget.clicked.connect(self.on_report_type_clicked)

        self.tab_4.general_statment_button.clicked.connect(self.general_statment)

        if not os.path.exists(self.plaxis_log_path):
            os.mkdir(self.plaxis_log_path)

    def call_tab2_refresh(self):
        self.tab_2.refresh()
        if statment.general_parameters.test_mode in ["Трёхосное сжатие (F, C, E)", 'Трёхосное сжатие (F, C, Eur)']:
            self.tab_3.refresh()

    def keyPressEvent(self, event):
        if statment.current_test:
            list = [x for x in statment]
            index = list.index(statment.current_test)
            if str(event.key()) == "90":
                if index >= 1:
                    statment.current_test = list[index - 1]
                    self.set_test_parameters(True)
            elif str(event.key()) == "88":
                if index < len(list) - 1:
                    statment.current_test = list[index + 1]
                    self.set_test_parameters(True)

    def set_test_parameters(self, params):
        if statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C, E)' or statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C, Eur)':
            self.tab_2.item_identification.set_data()
            self.tab_3.item_identification.set_data()
            self.tab_2.set_params()
            self.tab_3.set_params()
            self.physical_line_1.set_data()
            self.physical_line_2.set_data()
            try:
                self.tab_3.mohr_dialog_widget.set_params()
            except:
                pass
        elif statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C)' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие НН' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C) res':
            self.tab_3.item_identification.set_data()
            self.tab_3.set_params()
            self.physical_line_2.set_data()
            try:
                self.tab_3.mohr_dialog_widget.set_params()
            except:
                pass
        elif statment.general_parameters.test_mode == 'Трёхосное сжатие (E)':
            self.tab_2.item_identification.set_data()
            self.tab_2.set_params()
            self.physical_line_1.set_data()
        elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
            self.tab_2.item_identification.set_data()
            self.tab_2.set_params()
            self.physical_line_1.set_data()

        elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
            self.tab_2.item_identification.set_data()
            self.tab_2.set_params()
            self.physical_line_1.set_data()

    def on_test_type_changed(self):
        try:
            if self.tab_1.open_line.get_data()['test_mode'] == 'Трёхосное сжатие с разгрузкой (plaxis)':
                self.tab_4.plaxis_btn.setChecked(True)
                return

            if self.tab_4.plaxis_btn.isChecked():
                self.tab_4.plaxis_btn.setChecked(False)

        except AttributeError:
            pass

    def on_report_type_clicked(self):
        try:
            report_type = self.tab_4.report_type
            if 'plaxis' in report_type.lower():
                self.tab_4.plaxis_btn.setChecked(True)
            else:
                if self.tab_1.open_line.get_data()['test_mode'] == 'Трёхосное сжатие с разгрузкой (plaxis)':
                    return

                self.tab_4.plaxis_btn.setChecked(False)

        except AttributeError:
            pass

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            d, h = statment[statment.current_test].physical_properties.sample_size

            try:
                if statment.general_parameters.waterfill == "Водонасыщенное состояние":
                    s = "в водонасыщенном состоянии"
                elif statment.general_parameters.waterfill == "Природная влажность":
                    s = "при природной влажности"
                elif statment.general_parameters.waterfill == "Не указывать":
                    s = ""
            except:
                s = ""

            test_parameter = {"equipment": statment.general_parameters.equipment,
                              "mode": "КД, девиаторное нагружение в кинематическом режиме " + s,
                              "sigma_3": statment[statment.current_test].mechanical_properties.sigma_3,
                              "K0": [statment[statment.current_test].mechanical_properties.K0,
                                     "-" if self.tab_3.reference_pressure_array_box.get_checked() == "set_by_user" or
                                            self.tab_3.reference_pressure_array_box.get_checked() == "state_standard"
                                     else statment[statment.current_test].mechanical_properties.K0],
                              "h": h,
                              "d": d}

            if self.tab_1.open_line.get_data()["K0_mode"] in ["K0: По ГОСТ 12248.3-2020", "K0: Формула Джекки"]\
                    and statment[statment.current_test].physical_properties.type_ground in [1, 2, 3, 4]:
                test_parameter["K0"][0] = zap(test_parameter["K0"][0], 1)
            else:
                test_parameter["K0"][0] = zap(test_parameter["K0"][0], 2)

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")
            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            statment.save_dir.check_dirs()

            if self.tab_4.qr:
                qr = request_qr()
            else:
                qr = None

            save_plaxis = False
            try:
                save_plaxis = self.tab_4.plaxis_btn.isChecked()

                if not save_plaxis:
                    if os.path.exists(statment.save_dir.plaxis_log):
                        # os.rmdir(statment.save_dir.plaxis_log)
                        pass
                if save_plaxis:
                    if not os.path.exists(statment.save_dir.plaxis_log):
                        os.makedirs(statment.save_dir.plaxis_log)
            except AttributeError:
                pass

            if statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                name = file_path_name + " " + statment.general_data.object_number + " ТС" + ".pdf"

                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d),
                                                              save_plaxis=save_plaxis)
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")

                if save_plaxis:
                    shutil.copy(
                        os.path.join(save, f"plaxis_log.txt"),
                        os.path.join(statment.save_dir.plaxis_log_E50,
                                     f"{file_path_name} {statment[statment.current_test].mechanical_properties.sigma_3} kPa.txt"))

                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                test_result = E_models[statment.current_test].get_test_results()

                report_E(save + "/" + name, data_customer,
                         statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                         os.getcwd() + "/project_data/",
                         test_parameter, test_result,
                         (*self.tab_2.consolidation.save_canvas(),
                          *self.tab_2.deviator_loading.save_canvas()), self.tab_4.report_type,
                         "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                if self.tab_4.report_type == "standart_E50" or self.tab_4.report_type == "plaxis_m" or self.tab_4.report_type == "plaxis":
                    set_cell_data(self.tab_1.path,
                                  (c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][0][2] + str(number),
                                   (number, c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][1][2])),
                                  test_result["E50"], sheet="Лист1", color="FF6961")
                else:
                    set_cell_data(self.tab_1.path,
                                  (c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][0][2] + str(number),
                                   (number, c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][1][2])),
                                  test_result["E"][0], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой":
                name = file_path_name + " " + statment.general_data.object_number + " ТС Р" + ".pdf"
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d),
                                                              save_plaxis=save_plaxis)
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                if save_plaxis:
                    shutil.copy(
                        os.path.join(save, f"plaxis_log.txt"),
                        os.path.join(statment.save_dir.plaxis_log_E50,
                                     f"{file_path_name} {statment[statment.current_test].mechanical_properties.sigma_3} kPa.txt"))

                test_result = E_models[statment.current_test].get_test_results()
                report_E(save + "/" + name, data_customer,
                         statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                         os.getcwd() + "/project_data/",
                         test_parameter, test_result,
                         (*self.tab_2.consolidation.save_canvas(),
                          *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), self.tab_4.report_type,
                         "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              ("GI" + str(number), (number, 190)),
                              test_result["Eur"], sheet="Лист1", color="FF6961")

                if self.tab_4.report_type == "standart_E50" or self.tab_4.report_type == "plaxis_m" or self.tab_4.report_type == "plaxis":
                    set_cell_data(self.tab_1.path,
                                  (c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][0][2] + str(number),
                                   (number, c_fi_E_PropertyPosition["Трёхосное сжатие (E)"][1][2])),
                                  test_result["E50"], sheet="Лист1", color="FF6961")
                else:
                    set_cell_data(self.tab_1.path,
                                  (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][0][2] + str(number),
                                   (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][1][2])),
                                  test_result["E"][0], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
                name = file_path_name + " " + statment.general_data.object_number + " ТС Р (plaxis)" + ".pdf"
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d),
                                                              save_plaxis=save_plaxis)
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                if save_plaxis:
                    shutil.copy(
                        os.path.join(save, f"plaxis_log.txt"),
                        os.path.join(statment.save_dir.plaxis_log_E50,
                                     f"{file_path_name} {statment[statment.current_test].mechanical_properties.sigma_3} kPa.txt"))

                test_result = E_models[statment.current_test].get_test_results()
                report_E(save + "/" + name, data_customer,
                         statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                         os.getcwd() + "/project_data/",
                         test_parameter, test_result,
                         (*self.tab_2.consolidation.save_canvas(),
                          *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), self.tab_4.report_type,
                         "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              ("GI" + str(number), (number, 190)),
                              test_result["Eur"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой (plaxis)"][0][2] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой (plaxis)"][1][2])),
                              test_result["E50"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d),
                                                              save_plaxis=save_plaxis)
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")

                if save_plaxis:
                    shutil.copy(
                        os.path.join(save, f"plaxis_log.txt"),
                        os.path.join(statment.save_dir.plaxis_log_E50,
                                     f"{file_path_name} {statment[statment.current_test].mechanical_properties.sigma_3} kPa.txt"))

                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3']*1000)} kPa.txt"))


                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                test_result = E_models[statment.current_test].get_test_results()
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()
                test_result["c"], test_result["fi"], test_result["m"] = \
                    FC_models[statment.current_test].get_test_results()["c"], \
                    FC_models[statment.current_test].get_test_results()["fi"], \
                    FC_models[statment.current_test].get_test_results()["m"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                data = {
                    "laboratory": "mdgt",
                    "password": "it_user",

                    "test_name": "FC",
                    "object": str(statment.general_data.object_number),
                    "laboratory_number": str(statment.current_test),
                    "test_type": "FC",

                    "data": {
                        "Лаболаторный номер": str(statment.current_test),
                        "Модуль деформации E, МПа:": str(test_result["E"][0]),
                        "Коэффициент поперечной деформации ν, д.е.:": str(test_result["poissons_ratio"]),
                        "Эффективное сцепление с', МПа:": str(test_result["c"]),
                        "Эффективный угол внутреннего трения φ', град:": str(test_result["fi"]),
                    }
                }

                # s = MohrSaver(FC_models[statment.current_test], statment.save_dir.save_directory + "/geologs", size=[h, d])
                # s.save_log_file(file_path_name)
                # qr = request_qr(data)

                report_FCE(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                           statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                           (*self.tab_2.deviator_loading.save_canvas(),
                            *self.tab_3.save_canvas()), self.tab_4.report_type,
                           "{:.2f}".format(__version__), qr_code=qr)  # , qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                if self.tab_4.report_type == "Standart_E50" or self.tab_4.report_type == "plaxis":
                    set_cell_data(
                        self.tab_1.path,
                        (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][2] + str(number),
                         (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][2])),
                        test_result["E50"], sheet="Лист1", color="FF6961")
                else:
                    set_cell_data(
                        self.tab_1.path,
                        (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][2] + str(number),
                         (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][2])),
                        test_result["E"][0], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][1] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":

                report_directory_FC = statment.save_dir.report_directory + "/Трёхосное сжатие (F, C)"
                report_directory_Eur = statment.save_dir.report_directory + "/Трёхосное сжатие с разгрузкой"

                create_path(report_directory_FC)
                create_path(report_directory_Eur)

                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d),
                                                              save_plaxis=save_plaxis)
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                if save_plaxis:
                    shutil.copy(
                        os.path.join(save, f"plaxis_log.txt"),
                        os.path.join(statment.save_dir.plaxis_log_E50,
                                     f"{file_path_name} {statment[statment.current_test].mechanical_properties.sigma_3} kPa.txt"))

                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3'] * 1000)} kPa.txt"))

                test_result = E_models[statment.current_test].get_test_results()
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()
                test_result["c"], test_result["fi"], test_result["m"] = \
                    FC_models[statment.current_test].get_test_results()["c"], \
                    FC_models[statment.current_test].get_test_results()["fi"], \
                    FC_models[statment.current_test].get_test_results()["m"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                          test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, report_directory_FC + "/" + name)

                test_parameter["K0"] = [statment[statment.current_test].mechanical_properties.K0,
                                        "-" if self.tab_3.reference_pressure_array_box.get_checked() == "set_by_user" or
                                               self.tab_3.reference_pressure_array_box.get_checked() == "state_standard"
                                        else statment[statment.current_test].mechanical_properties.K0]

                report_E(save + "/" + name[:-4] + " Р.pdf", data_customer,
                         statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                         os.getcwd() + "/project_data/",
                         test_parameter, test_result,
                         (*self.tab_2.consolidation.save_canvas(),
                          *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), self.tab_4.report_type,
                         "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name[:-4] + " Р.pdf", report_directory_Eur + "/" + name[:-4] + " Р.pdf")

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][0][1] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              ("GI" + str(number), (number, 190)),
                              test_result["Eur"], sheet="Лист1", color="FF6961")
                if self.tab_4.report_type == "plaxis":
                    set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][0][2] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][1][2])),
                              test_result["E50"][0], sheet="Лист1", color="FF6961")
                else:
                    set_cell_data(self.tab_1.path,
                                  (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][0][2] + str(number),
                                   (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][1][2])),
                                  test_result["E"][0], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C)':
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"
                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                if save_plaxis:
                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3'] * 1000)} kPa.txt"))

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"], test_result["fi"], test_result["m"] = \
                FC_models[statment.current_test].get_test_results()["c"], \
                FC_models[statment.current_test].get_test_results()["fi"], \
                FC_models[statment.current_test].get_test_results()["m"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                          test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][0][1] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C)"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие КН':

                test_parameter["mode"] = "KH, девиаторное нагружение в кинематическом режиме " + s

                name = file_path_name + " " + statment.general_data.object_number + " КН" + ".pdf"
                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                if save_plaxis:
                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3'] * 1000)} kPa.txt"))

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"], test_result["fi"] = FC_models[statment.current_test].get_test_results()["c"], \
                                                      FC_models[statment.current_test].get_test_results()["fi"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_KN(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                             statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                             test_parameter, test_result,
                             (*self.tab_3.save_canvas(),
                              *self.tab_3.save_canvas()), "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие КН"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие КН"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие КН"][0][1] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие КН"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие НН':

                test_parameter["mode"] = "НН, девиаторное нагружение в кинематическом режиме " + s

                if self.tab_4.report_type == "vibroNN":
                    name = file_path_name + " " + statment.general_data.object_number + " КВ" + ".pdf"
                else:
                    name = file_path_name + " " + statment.general_data.object_number + " НН" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)

                if save_plaxis:
                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3'] * 1000)} kPa.txt"))

                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_deviator()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"] = FC_models[statment.current_test].get_test_results()["c"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_NN(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                             statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                             test_parameter, test_result,
                             (*self.tab_3.save_canvas(),
                              *self.tab_3.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие НН"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие НН"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                if self.tab_4.report_type == "vibro":
                    name = file_path_name + " " + statment.general_data.object_number + " ТДВ" + ".pdf"
                else:
                    name = file_path_name + " " + statment.general_data.object_number + " ТДО" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d),
                                                                save_plaxis=save_plaxis)

                if save_plaxis:
                    for test in FC_models[statment.current_test]._tests:
                        results = test.deviator_loading.get_test_results()
                        path = os.path.normpath(os.path.join(save, str(results["sigma_3"])))

                        shutil.copy(
                            os.path.join(path, f"plaxis_log.txt"),
                            os.path.join(statment.save_dir.plaxis_log_FC,
                                         f"{file_path_name} {int(results['sigma_3'] * 1000)} kPa.txt"))

                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["sigma_1_res"] = FC_models[
                    statment.current_test].get_sigma_1_res()

                test_result["c"], test_result["fi"], test_result["m"], test_result["c_res"], test_result["fi_res"] = \
                    FC_models[statment.current_test].get_test_results()["c"], \
                    FC_models[statment.current_test].get_test_results()["fi"], \
                    FC_models[statment.current_test].get_test_results()["m"], \
                    FC_models[statment.current_test].get_test_results()["c_res"], \
                    FC_models[statment.current_test].get_test_results()["fi_res"],

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)
                    test_result["fi_res"] = zap(test_result["fi_res"], 0)

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_res(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                              statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                              test_parameter, test_result,
                              (*self.tab_3.save_canvas(),
                               *self.tab_3.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__), qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C) res"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C) res"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C) res"][0][1] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C) res"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (MechanicalPropertyPosition["c_res"][0] + str(number),
                               (number, MechanicalPropertyPosition["c_res"][1])),
                              test_result["c_res"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (MechanicalPropertyPosition["fi_res"][0] + str(number),
                               (number, MechanicalPropertyPosition["fi_res"][1])),
                              test_result["fi_res"], sheet="Лист1", color="FF6961")

            self.write_excel_general_data(number)

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(
                    f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            control()

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", f"Закройте файл отчета {name}", QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except:
            app_logger.exception(f"Не выгнан {statment.current_test}")

    def save_report_and_continue(self):
        self.save_pickle()
        try:
            self.save_report()
        except:
            pass
        keys = [key for key in statment]
        for i, val in enumerate(keys):
            if (val == statment.current_test) and (i < len(keys) - 1):
                statment.current_test = keys[i + 1]
                self.set_test_parameters(True)
                break
            else:
                pass
        SessionWriter.write_test()

    def write_excel_general_data(self, number):

        general_for_write = {
            "test_type": [],
            "sigma_3": [],
            "sigma_1": [],
            "fi": [],
            "c": [],
            "E": [],
            "E50": [],
            "Eur": [],
            "poissons_ratio": [],
        }

        general_for_write_params = {
            "test_type": ("CY" + str(number), (number, 102)),
            "sigma_3": ("CZ" + str(number), (number, 103)),
            "sigma_1": ("DA" + str(number), (number, 104)),
            "fi": ("DB" + str(number), (number, 105)),
            "c": ("DC" + str(number), (number, 106)),
            "E": ("DD" + str(number), (number, 107)),
            "E50": ("DE" + str(number), (number, 108)),
            "Eur": ("DF" + str(number), (number, 109)),
            "poissons_ratio": ("DG" + str(number), (number, 110)),
        }
        if statment.general_parameters.test_mode in [
            "Трёхосное сжатие (F, C, E)",
            "Трёхосное сжатие (F, C, Eur)",
            'Трёхосное сжатие (F, C)',
            'Трёхосное сжатие КН',
            'Трёхосное сжатие НН',
            "Трёхосное сжатие (F, C) res"
        ]:

            if statment.general_parameters.test_mode in [
                "Трёхосное сжатие (F, C, E)",
                "Трёхосное сжатие (F, C, Eur)",
                ]:
                result_E = E_models[statment.current_test].deviator_loading.get_test_results()
                general_for_write["test_type"].append("E")
                general_for_write["sigma_3"].append(result_E['sigma_3'])
                general_for_write["sigma_1"].append(round(result_E['sigma_3'] + result_E["qf"], 2))
                general_for_write["E"].append(result_E['E'][0])
                general_for_write["E50"].append(result_E['E50'])
                if result_E['Eur']:
                    general_for_write["Eur"].append(result_E['Eur'])
                general_for_write["poissons_ratio"].append(result_E['poissons_ratio'])


            for test in FC_models[statment.current_test]:
                result_test = test.deviator_loading.get_test_results()

                general_for_write["test_type"].append("FC")
                general_for_write["sigma_3"].append(result_test['sigma_3'])
                general_for_write["sigma_1"].append(round(result_test['sigma_3'] + result_test["qf"], 2))
                general_for_write["E"].append(result_test['E'][0])
                general_for_write["E50"].append(result_test['E50'])
                general_for_write["poissons_ratio"].append(result_test['poissons_ratio'])

            general_for_write["c"].append(FC_models[statment.current_test].get_test_results()["c"])
            general_for_write["fi"].append(FC_models[statment.current_test].get_test_results()["fi"])

        if statment.general_parameters.test_mode in [
            "Трёхосное сжатие (E)",
            "Трёхосное сжатие с разгрузкой",
            "Трёхосное сжатие с разгрузкой (plaxis)"
        ]:
            result_E = E_models[statment.current_test].deviator_loading.get_test_results()
            general_for_write["test_type"].append("E")
            general_for_write["sigma_3"].append(result_E['sigma_3'])
            general_for_write["sigma_1"].append(round(result_E['sigma_3'] + result_E["qf"], 2))
            general_for_write["E"].append(result_E['E'][0])
            general_for_write["E50"].append(result_E['E50'])
            if result_E['Eur']:
                general_for_write["Eur"].append(result_E['Eur'])
            general_for_write["poissons_ratio"].append(result_E['poissons_ratio'])


        for key in general_for_write:
            set_cell_data(
                self.tab_1.path,
                general_for_write_params[key],
                ';'.join([str(i).replace(".", ",") for i in general_for_write[key]]) if len(general_for_write[key]) else "-",
                sheet="Лист1",
                color="FF6961"
            )

    def save_all_reports(self):
        try:
            models = [model for model in [E_models, FC_models] if len(model)]

            names = []
            if len(E_models):
                if statment.general_parameters.test_mode in [
                    "Трёхосное сжатие с разгрузкой",
                    "Трёхосное сжатие с разгрузкой (plaxis)",
                    "Трёхосное сжатие (F, C, Eur)"
                ]:
                    names.append(f"Eur_models{statment.general_data.get_shipment_number()}.pickle")
                else:
                    names.append(f"E_models{statment.general_data.get_shipment_number()}.pickle")
            if len(FC_models):
                names.append(f"FC_models{statment.general_data.get_shipment_number()}.pickle")

            statment.save(models, names)

            if statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode in [
                "Трёхосное сжатие с разгрузкой",
                "Трёхосное сжатие с разгрузкой (plaxis)"
            ]:
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode in [
                'Трёхосное сжатие (F, C)',
                'Трёхосное сжатие КН',
                'Трёхосное сжатие НН',
                "Трёхосное сжатие (F, C) res"
            ]:
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))

        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        statment.save_dir.clear_dirs()

        loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                        message_port=7781)
        count = len(statment)
        Loader.send_message(loader.port, f"Сохранено 0 из {count}")

        def save():
            is_ok = True
            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self.set_test_parameters(True)
                self.tab_2.set_params(plot_dots=False)
                try:
                    self.save_report()
                except Exception as err:
                    is_ok = False
                    loader.close()
                    app_logger.info(f"Ошибка сохранения пробы {err}")
                    QMessageBox.critical(self, "Ошибка",
                                         f"Ошибка сохранения пробы {statment.current_test}. Операция прервана.")
                    break
                else:
                    Loader.send_message(loader.port, f"Сохранено {i + 1} из {count}")

            if is_ok:
                Loader.send_message(loader.port, f"Сохранено {count} из {count}")
                loader.close()
                app_logger.info("Объект успешно выгнан")
                self.save_massage = True
                QMessageBox.about(self, "Сообщение", "Объект выгнан")

        t = threading.Thread(target=save)
        loader.show()
        t.start()

        SessionWriter.write_session(len(statment))

    def jornal(self):
        if statment.tests == {}:
            QMessageBox.critical(self, "Ошибка", "Загрузите объект", QMessageBox.Ok)
        else:
            self.dialog = TestsLogWidget(static, TestsLogTriaxialStatic, self.tab_1.path)
            self.dialog.show()

    def save_pickle(self):
        try:
            models = [model for model in [E_models, FC_models] if len(model)]

            names = []
            if len(E_models):
                if statment.general_parameters.test_mode in [
                    "Трёхосное сжатие с разгрузкой",
                    "Трёхосное сжатие с разгрузкой (plaxis)",
                    "Трёхосное сжатие (F, C, Eur)"
                ]:
                    names.append(f"Eur_models{statment.general_data.get_shipment_number()}.pickle")
                else:
                    names.append(f"E_models{statment.general_data.get_shipment_number()}.pickle")
            if len(FC_models):
                names.append(f"FC_models{statment.general_data.get_shipment_number()}.pickle")

            statment.save(models, names)

            if statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode in [
                "Трёхосное сжатие с разгрузкой",
                "Трёхосное сжатие с разгрузкой (plaxis)"
            ]:
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
            elif statment.general_parameters.test_mode in [
                'Трёхосное сжатие (F, C)',
                'Трёхосное сжатие КН',
                'Трёхосное сжатие НН',
                "Трёхосное сжатие (F, C) res"
            ]:
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))

            QMessageBox.about(self, "Сообщение", "Pickle успешно сохранен")
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

    def xml(self):
        try:
            self.wm = XMLWidget(statment.save_dir.save_directory + "/xml")
            QMessageBox.about(self, "Сообщение", "XML выгнаны")
        except Exception as err:
            print(str(err))

    def average(self):
        try:
            self.av = AverageWidget()
            self.av.show()
        except Exception as err:
            print(str(err))

    def save_excel(self):
        try:
            customer_name = ''.join(list(filter(lambda c: c not in '''«»\/:*?"'<>|''', statment.general_data.customer)))
            save_file_name = f"{customer_name} - {statment.general_data.object_number} - {statment.general_data.object_short_name} - Сводная ведомость {'Трехосное сжатие'}{statment.general_data.get_shipment_number()}.xlsx"


            path = os.path.join(statment.save_dir.save_directory, save_file_name)
            shutil.copy(os.getcwd() + "/project_data/" + "FCE. Выгрузка.xlsx", path)
            i = 3

            parameters_for_write = []

            for test in statment:
                statment.setCurrentTest(test)
                laboratory_number = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")
                depth = statment[statment.current_test].physical_properties.depth
                borehole = statment[statment.current_test].physical_properties.borehole

                parameters = {
                    "laboratory_number": ['B', 1],
                    "borehole": ['C', 2],
                    "depth": ['D', 3],
                    "test_type": ['G', 6],
                    "scheme": ['E', 4],
                    "waterfill": ['F', 5],
                    "sigma_1": ['I', 8],
                    "sigma_3": ['H', 7],
                    "E": ['M', 12],
                    "E50": ['N', 13],
                    "Eur": ['O', 14],
                    "poissons_ratio": ['P', 15],
                    "c": ['S', 19],
                    "fi": ['T', 20],
                    "cu": ['U', 21],
                    "uf": ['J', 9],
                    "K0": ['K', 10],
                    "Skempton": ['AA', 27],
                }

                try:
                    if statment.general_parameters.waterfill == "Водонасыщенное состояние":
                        waterfill = "водонасыщенное"
                    elif statment.general_parameters.waterfill == "Природная влажность":
                        waterfill = "природное"
                    elif statment.general_parameters.waterfill == "Не указывать":
                        waterfill = ""
                except:
                    waterfill = ""

                try:
                    E_models[statment.current_test]

                    set_cell_data(path, (parameters["laboratory_number"][0] + str(i), (i, parameters["laboratory_number"][1])),
                                  laboratory_number, sheet="Лист1")
                    set_cell_data(path, (parameters["borehole"][0] + str(i), (i, parameters["borehole"][1])),
                                  borehole, sheet="Лист1")
                    set_cell_data(path, (parameters["depth"][0] + str(i), (i, parameters["depth"][1])),
                                  depth, sheet="Лист1")
                    set_cell_data(path, (parameters["waterfill"][0] + str(i), (i, parameters["waterfill"][1])),
                                  waterfill, sheet="Лист1")

                    set_cell_data(path, (parameters["test_type"][0] + str(i), (i, parameters["test_type"][1])),
                                  "E", sheet="Лист1")
                    set_cell_data(path, (parameters["scheme"][0] + str(i), (i, parameters["scheme"][1])),
                                  "КД", sheet="Лист1")

                    set_cell_data(path, (parameters["sigma_3"][0] + str(i), (i, parameters["sigma_3"][1])),
                                  round(statment[statment.current_test].mechanical_properties.sigma_3 / 1000, 3), sheet="Лист1")
                    set_cell_data(path, (parameters["sigma_1"][0] + str(i), (i, parameters["sigma_1"][1])),
                                  round(statment[statment.current_test].mechanical_properties.sigma_1 / 1000, 3), sheet="Лист1")
                    set_cell_data(path, (parameters["K0"][0] + str(i), (i, parameters["K0"][1])),
                                  statment[statment.current_test].mechanical_properties.K0,
                                  sheet="Лист1")
                    E = E_models[statment.current_test].deviator_loading.get_test_results()["E"]
                    try:
                        E[0]
                        set_cell_data(path, (parameters["E"][0] + str(i), (i, parameters["E"][1])),
                                      E[0], sheet="Лист1")
                    except:
                        pass

                    set_cell_data(path, (parameters["E50"][0] + str(i), (i, parameters["E50"][1])),
                                  E_models[statment.current_test].deviator_loading.get_test_results()["E50"], sheet="Лист1")

                    Eur = E_models[statment.current_test].deviator_loading.get_test_results()["Eur"]
                    if Eur is not None:
                        set_cell_data(path, (parameters["Eur"][0] + str(i), (i, parameters["Eur"][1])),
                                      Eur, sheet="Лист1")

                    poissons_ratio = E_models[statment.current_test].deviator_loading.get_test_results()["poissons_ratio"]
                    set_cell_data(path, (parameters["poissons_ratio"][0] + str(i), (i, parameters["poissons_ratio"][1])),
                                  poissons_ratio, sheet="Лист1")

                    set_cell_data(path,
                                  (parameters["uf"][0] + str(i), (i, parameters["uf"][1])),
                                  E_models[statment.current_test].deviator_loading.get_test_results()[
                                      "max_pore_pressure"],
                                  sheet="Лист1")

                    set_cell_data(path, (parameters["c"][0] + str(i), (i, parameters["c"][1])),
                                  statment[statment.current_test].mechanical_properties.c,
                                  sheet="Лист1")
                    set_cell_data(path, (parameters["fi"][0] + str(i), (i, parameters["fi"][1])),
                                  statment[statment.current_test].mechanical_properties.fi,
                                  sheet="Лист1")
                    if E_models[statment.current_test].reconsolidation is not None:
                        set_cell_data(path, (parameters["Skempton"][0] + str(i), (i, parameters["Skempton"][1])),
                                      E_models[statment.current_test].reconsolidation.get_test_results()["scempton"],
                                      sheet="Лист1")

                    set_cell_data(path, ("A" + str(i), (i, 1)), i - 2, sheet="Лист1")
                    i += 1
                except Exception as err:
                    print(err)

                try:
                    FC_models[statment.current_test]

                    for test in FC_models[statment.current_test]:
                        set_cell_data(path, (
                        parameters["laboratory_number"][0] + str(i), (i, parameters["laboratory_number"][1])),
                                      laboratory_number, sheet="Лист1")
                        set_cell_data(path, (parameters["borehole"][0] + str(i), (i, parameters["borehole"][1])),
                                      borehole, sheet="Лист1")
                        set_cell_data(path, (parameters["depth"][0] + str(i), (i, parameters["depth"][1])),
                                      depth, sheet="Лист1")
                        set_cell_data(path, (parameters["waterfill"][0] + str(i), (i, parameters["waterfill"][1])),
                                      waterfill, sheet="Лист1")

                        set_cell_data(path, (parameters["K0"][0] + str(i), (i, parameters["K0"][1])),
                                      statment[statment.current_test].mechanical_properties.K0, sheet="Лист1")


                        set_cell_data(path, (parameters["test_type"][0] + str(i), (i, parameters["test_type"][1])),
                                      "FC", sheet="Лист1")
                        set_cell_data(path, (parameters["scheme"][0] + str(i), (i, parameters["scheme"][1])),
                                      "КД", sheet="Лист1")
                        set_cell_data(path, (parameters["sigma_3"][0] + str(i), (i, parameters["sigma_3"][1])),
                                      test.deviator_loading.get_test_results()["sigma_3"], sheet="Лист1")
                        sigma_1 = round(test.deviator_loading.get_test_results()["sigma_3"] + test.deviator_loading.get_test_results()["qf"], 3)

                        set_cell_data(path, (parameters["sigma_1"][0] + str(i), (i, parameters["sigma_1"][1])),
                                      sigma_1, sheet="Лист1")

                        E = test.deviator_loading.get_test_results()["E"]
                        try:
                            E[0]
                            set_cell_data(path, (parameters["E"][0] + str(i), (i, parameters["E"][1])),
                                          E[0], sheet="Лист1")
                        except:
                            pass

                        set_cell_data(path, (parameters["E50"][0] + str(i), (i, parameters["E50"][1])),
                                      test.deviator_loading.get_test_results()["E50"],
                                      sheet="Лист1")

                        poissons_ratio = test.deviator_loading.get_test_results()["poissons_ratio"]
                        set_cell_data(path, (
                        parameters["poissons_ratio"][0] + str(i), (i, parameters["poissons_ratio"][1])),
                                      poissons_ratio,
                                      sheet="Лист1")

                        set_cell_data(path,
                                      (parameters["uf"][0] + str(i), (i, parameters["uf"][1])),
                                      test.deviator_loading.get_test_results()["max_pore_pressure"],
                                      sheet="Лист1")

                        set_cell_data(path, (parameters["c"][0] + str(i), (i, parameters["c"][1])),
                                      FC_models[statment.current_test].get_test_results()["c"],
                                      sheet="Лист1")
                        set_cell_data(path, (parameters["fi"][0] + str(i), (i, parameters["fi"][1])),
                                      FC_models[statment.current_test].get_test_results()["fi"],
                                      sheet="Лист1")
                        if test.reconsolidation is not None:
                            set_cell_data(path, (parameters["Skempton"][0] + str(i), (i, parameters["Skempton"][1])),
                                          test.reconsolidation.get_test_results()["scempton"],
                                          sheet="Лист1")

                        set_cell_data(path, ("A" + str(i), (i, 1)), i - 2, sheet="Лист1")
                        i += 1
                except Exception as err:
                    print(err)

            QMessageBox.about(self, "Сообщение", "Excel сохранен")
            app_logger.info("Excel сохранен")
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None
        try:
            test_mode_file_name = "FCE"

            _statment = StatementGenerator(self, path=s, statement_structure_key="FCE",
                                           test_mode_and_shipment=(test_mode_file_name,
                                                                   statment.general_data.get_shipment_number()))
            _statment.show()
        except Exception as err:
            print(err)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = StatickSoilTestApp()
    ex.show()
    sys.exit(app.exec_())
