from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading

from general.general_functions import create_path
from general.tab_view import TabMixin
from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from excel_statment.initial_statment_widgets import TriaxialStaticStatment
from excel_statment.initial_tables import LinePhysicalProperties
from general.save_widget import Save_Dir
from excel_statment.functions import set_cell_data
from excel_statment.position_configs import c_fi_E_PropertyPosition, MechanicalPropertyPosition
from general.reports import report_consolidation, report_FCE, report_FC, report_FC_KN, report_E, report_FC_NN, report_FC_res
from static_loading.triaxial_static_widgets_UI import ModelTriaxialItemUI, ModelTriaxialFileOpenUI, ModelTriaxialReconsolidationUI, \
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
from saver import XMLWidget

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
        self.deviator_loading.setFixedHeight(500)
        self.reconsolidation.setFixedHeight(300)

        self.deviator_loading.combo_box.activated.connect(self._combo_plot_deviator_changed)

        self._create_UI()
        self._wigets_connect()

        #if model:
            #self.set_model(model)
        #else:
            #self._model = ModelTriaxialStaticLoad()

    def _create_UI(self):
        self.layout_wiget = QVBoxLayout()
        self.layout_wiget.addWidget(self.open_log_file)
        self.layout_wiget.addLayout(self.line)
        self.layout_wiget.addWidget(self.deviator_loading)
        self.layout_wiget.addWidget(self.consolidation)
        self.layout_wiget.addWidget(self.reconsolidation)
        #self.layout_wiget.addWidget(self.deviator_loading)

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
        self.consolidation.function_replacement_button_group.buttonClicked.connect(self._consolidation_interpolation_type)

        self.deviator_loading.slider_cut.sliderMoved.connect(self._cut_slider_deviator_moove)
        self.consolidation.slider_cut.sliderMoved.connect(self._cut_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderMoved.connect(self._interpolate_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderReleased.connect(self._interpolate_slider_consolidation_release)

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

        self._deviator_volumeter_current_vol(E_models[statment.current_test].deviator_loading.get_current_volume_strain())
        self._consolidation_volumeter_current_vol(E_models[statment.current_test].consolidation.get_current_volume_strain())

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

    def _plot_deviator_loading(self):
        try:
            plot_data = E_models[statment.current_test].deviator_loading.get_plot_data()
            res = E_models[statment.current_test].deviator_loading.get_test_results()
            self.deviator_loading.plot(plot_data, res)
        except KeyError:
            pass

    def _deviator_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if E_models[statment.current_test].deviator_loading.check_none():
            E_models[statment.current_test].deviator_loading.choise_volume_strain(button.text())
            self._cut_slider_deviator_set_val(E_models[statment.current_test].deviator_loading.get_borders())
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
                E_models[statment.current_test].deviator_loading.change_borders(int(self.deviator_loading.slider_cut.low()),
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
            self.point_identificator = E_models[statment.current_test].consolidation.define_click_point(float(event.xdata),
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
            E_models[statment.current_test].deviator_loading.moove_catch_point(float(event.xdata), float(event.ydata), self.point_identificator_deviator)
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
            E_models[statment.current_test].consolidation.moove_catch_point(float(event.xdata), float(event.ydata), self.point_identificator,
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
                  "Eur": "Модуль разгрузки"})
        self.deviator_loading_sliders.setFixedHeight(210)

        self.consolidation_sliders = TriaxialStaticLoading_Sliders({"max_time": "Время испытания",
                                                                         "volume_strain_90": "Объемная деформация в Cv"})
        self.consolidation_sliders.setFixedHeight(90)

        self.consolidation.graph_layout.addWidget(self.consolidation_sliders)
        self.deviator_loading.graph_layout.addWidget(self.deviator_loading_sliders)

        self.consolidation.setFixedHeight(500+90)
        self.deviator_loading.setFixedHeight(530+180)

        self.deviator_loading_sliders.signal[object].connect(self._deviator_loading_sliders_moove)
        self.consolidation_sliders.signal[object].connect(self._consolidation_sliders_moove)

    def refresh(self):
        try:
            E_models[statment.current_test].set_test_params()
            self.deviator_loading_sliders.set_sliders_params(E_models[statment.current_test].get_deviator_loading_draw_params())
            self.consolidation_sliders.set_sliders_params(E_models[statment.current_test].get_consolidation_draw_params())

            self._plot_reconsolidation()
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def set_params(self, param=None):
        try:
            self.deviator_loading_sliders.set_sliders_params(E_models[statment.current_test].get_deviator_loading_draw_params())
            self.consolidation_sliders.set_sliders_params(E_models[statment.current_test].get_consolidation_draw_params())

            self._plot_reconsolidation()
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._plot_deviator_loading()
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
        #self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Е")
        self.tab_widget.addTab(self.tab_3, "Опыт FC")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.signal[object].connect(self.tab_2.item_identification.set_data)
        self.tab_1.signal[object].connect(self.tab_3.item_identification.set_data)
        self.tab_1.statment_directory[str].connect(self.set_save_directory)
        self.tab_4.save_button.clicked.connect(self.save_report)
        #self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

    def save_report(self):
        try:
            assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
            #assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
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
                #Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-ДН" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " +\
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
                test_result["c"], test_result["fi"] = self.tab_3._model.get_test_results()["c"], self.tab_3._model.get_test_results()["fi"]
                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-КМ" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") +\
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

        self.tab_4 = Save_Dir(
            {
                "standart_E": "Стандардный E",
                "standart_E50": "Стандардный E50",
                "E_E50": "Совместный E/E50",
                "plaxis": "Plaxis/Midas",
                "user_define_1": "Пользовательский с ε50",
                "vibro": "Вибропрочность"
            })

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
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_4.update())

        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_4.jornal_button.clicked.connect(self.jornal)

        self.save_massage = True

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line_for_phiz.addWidget(self.physical_line_1)
        self.tab_2.line_for_phiz.addStretch(-1)
        self.physical_line_1.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3.refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)

        self.xml_button = QPushButton("Выгнать xml")
        self.xml_button.clicked.connect(self.xml)
        self.tab_4.advanced_box_layout.insertWidget(3, self.xml_button)
        #self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)


        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

    def keyPressEvent(self, event):
        if statment.current_test:
            list = [x for x in statment]
            index = list.index(statment.current_test)
            if str(event.key()) == "90":
                if index >= 1:
                    statment.current_test = list[index-1]
                    self.set_test_parameters(True)
            elif str(event.key()) == "88":
                if index < len(list) -1:
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
        elif statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C)' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие НН' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or \
                statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C) res':
            self.tab_3.item_identification.set_data()
            self.tab_3.set_params()
            self.physical_line_2.set_data()
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

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            if statment.general_parameters.equipment == "АСИС ГТ.2.0.5 (150х300)":
                h, d = 300, 150
            else:
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

            if statment.general_parameters.test_mode == "Трёхосное сжатие (E)":
                name = file_path_name + " " + statment.general_data.object_number + " ТС" + ".pdf"

                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d))
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"), statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                test_result = E_models[statment.current_test].get_test_results()

                report_E(save + "/" + name, data_customer,
                                 statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 (*self.tab_2.consolidation.save_canvas(),
                                  *self.tab_2.deviator_loading.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__))

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                if self.tab_4.report_type == "standart_E50":
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
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d))
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                                f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
                test_result = E_models[statment.current_test].get_test_results()
                report_E(save + "/" + name, data_customer,
                                     statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                                     os.getcwd() + "/project_data/",
                                     test_parameter, test_result,
                                     (*self.tab_2.consolidation.save_canvas(),
                                      *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), self.tab_4.report_type, "{:.2f}".format(__version__))

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              ("GI" + str(number), (number, 190)),
                              test_result["Eur"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][0][2] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][1][2])),
                              test_result["E"][0], sheet="Лист1", color="FF6961")
            elif statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
                name = file_path_name + " " + statment.general_data.object_number + " ТС Р (plaxis)" + ".pdf"
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d))
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                                f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
                test_result = E_models[statment.current_test].get_test_results()
                report_E(save + "/" + name, data_customer,
                                     statment[statment.current_test].physical_properties, statment.getLaboratoryNumber(),
                                     os.getcwd() + "/project_data/",
                                     test_parameter, test_result,
                                     (*self.tab_2.consolidation.save_canvas(),
                                      *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), self.tab_4.report_type, "{:.2f}".format(__version__))

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              ("GI" + str(number), (number, 190)),
                              test_result["Eur"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой (plaxis)"][0][2] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой (plaxis)"][1][2])),
                              test_result["E"][0], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, E)":
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"

                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"FC_models{statment.general_data.get_shipment_number()}.pickle"))

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d))
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                test_result = E_models[statment.current_test].get_test_results()
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[statment.current_test].get_sigma_3_1()
                test_result["c"], test_result["fi"], test_result["m"] = \
                FC_models[statment.current_test].get_test_results()["c"], \
                FC_models[statment.current_test].get_test_results()["fi"], \
                FC_models[statment.current_test].get_test_results()["m"]

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

                #s = MohrSaver(FC_models[statment.current_test], statment.save_dir.save_directory + "/geologs", size=[h, d])
                #s.save_log_file(file_path_name)
                #qr = request_qr(data)

                report_FCE(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                           (*self.tab_2.deviator_loading.save_canvas(),
                            *self.tab_3.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__))#, qr_code=qr)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                if self.tab_4.report_type == "Standart_E50":
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
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][0] + str(number), (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][0][1] + str(number), (number, c_fi_E_PropertyPosition["Трёхосное сжатие (F, C, E)"][1][1])),
                              test_result["fi"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C, Eur)":

                report_directory_FC = statment.save_dir.report_directory + "/Трёхосное сжатие (F, C)"
                report_directory_Eur = statment.save_dir.report_directory + "/Трёхосное сжатие с разгрузкой"

                create_path(report_directory_FC)
                create_path(report_directory_Eur)


                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"

                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"Eur_models{statment.general_data.get_shipment_number()}.pickle"))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")
                E_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log", sample_size=(h, d))
                E_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
                shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

                test_result = E_models[statment.current_test].get_test_results()
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[statment.current_test].get_sigma_3_1()
                test_result["c"], test_result["fi"], test_result["m"] = \
                FC_models[statment.current_test].get_test_results()["c"], \
                FC_models[statment.current_test].get_test_results()["fi"], \
                FC_models[statment.current_test].get_test_results()["m"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                          test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__))

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
                         "{:.2f}".format(__version__))

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

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][0][2] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие с разгрузкой"][1][2])),
                              test_result["E"][0], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == 'Трёхосное сжатие (F, C)':
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"
                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"], test_result["fi"], test_result["m"] = FC_models[statment.current_test].get_test_results()["c"], \
                                                      FC_models[statment.current_test].get_test_results()["fi"], \
                                                      FC_models[statment.current_test].get_test_results()["m"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                           statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__))

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
                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))
                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"], test_result["fi"] = FC_models[statment.current_test].get_test_results()["c"], \
                                                      FC_models[statment.current_test].get_test_results()["fi"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_KN(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                           statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__))

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

                name = file_path_name + " " + statment.general_data.object_number + " НН" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))

                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[statment.current_test].get_sigma_3_deviator()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"]= FC_models[statment.current_test].get_test_results()["c"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_NN(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                           statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), "{:.2f}".format(__version__))

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие НН"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие НН"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

            elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"
                FC_models[statment.current_test].save_log_files(save, file_path_name, sample_size=(h, d))
                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))
                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["sigma_1_res"] = FC_models[
                    statment.current_test].get_sigma_1_res()

                test_result["c"], test_result["fi"], test_result["m"], test_result["c_res"], test_result["fi_res"] = \
                    FC_models[statment.current_test].get_test_results()["c"], \
                    FC_models[statment.current_test].get_test_results()["fi"],\
                    FC_models[statment.current_test].get_test_results()["m"],\
                    FC_models[statment.current_test].get_test_results()["c_res"],\
                    FC_models[statment.current_test].get_test_results()["fi_res"],


                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                report_FC_res(save + "/" + name, data_customer, statment[statment.current_test].physical_properties,
                           statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__))

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




            #statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
                          #name=statment.general_parameters.test_mode + ".pickle")

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(
                    f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", f"Закройте файл отчета {name}", QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except:
            app_logger.exception(f"Не выгнан {statment.current_test}")

    def save_report_and_continue(self):
        try:
            self.save_report()
        except:
            pass
        keys = [key for key in statment]
        for i, val in enumerate(keys):
            if (val == statment.current_test) and (i < len(keys) - 1):
                statment.current_test = keys[i+1]
                self.set_test_parameters(True)
                break
            else:
                pass

    def save_all_reports(self):
        statment.save_dir.clear_dirs()
        progress = QProgressDialog("Сохранение протоколов...", "Процесс сохранения:", 0, len(statment), self)
        progress.setCancelButton(None)
        progress.setWindowFlags(progress.windowFlags() & ~Qt.WindowCloseButtonHint)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)

        def save():
            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self.set_test_parameters(True)
                self.save_report()
                progress.setValue(i)
            progress.setValue(len(statment))
            progress.close()
            QMessageBox.about(self, "Сообщение", "Объект выгнан")
            app_logger.info("Объект успешно выгнан")
            self.save_massage = True

        t = threading.Thread(target=save)
        progress.show()
        t.start()

    def jornal(self):
        if statment.tests == {}:
            QMessageBox.critical(self, "Ошибка", "Загрузите объект", QMessageBox.Ok)
        else:
            self.dialog = TestsLogWidget(static, TestsLogTriaxialStatic, self.tab_1.path)
            self.dialog.show()

    def xml(self):
        try:
            self.wm = XMLWidget(statment.save_dir.save_directory + "/xml")
            QMessageBox.about(self, "Сообщение", "XML выгнаны")
        except Exception as err:
            print(str(err))



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = StatickSoilTestApp()
    ex.show()
    sys.exit(app.exec_())


