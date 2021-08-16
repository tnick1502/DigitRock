__version__ = 1

from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt

from static_loading.triaxial_static_widgets_UI import ModelTriaxialItemUI, ModelTriaxialFileOpenUI, ModelTriaxialReconsolidationUI, \
    ModelTriaxialConsolidationUI, ModelTriaxialDeviatorLoadingUI
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad, ModelTriaxialStaticLoadSoilTest
from general.general_widgets import Float_Slider
from configs.styles import style

class TriaxialStaticWidget(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self, model=None):
        super().__init__()

        self.open_log_file = ModelTriaxialFileOpenUI()
        self.log_file_path = None

        self.item_identification = ModelTriaxialItemUI()
        self.item_identification.setFixedHeight(330)
        self.reconsolidation = ModelTriaxialReconsolidationUI()
        self.line = QHBoxLayout()
        self.line.addWidget(self.item_identification)
        self.line.addWidget(self.reconsolidation)

        self.consolidation = ModelTriaxialConsolidationUI()
        self.point_identificator = None
        self.consolidation.setFixedHeight(500)
        self.deviator_loading = ModelTriaxialDeviatorLoadingUI()
        self.deviator_loading.setFixedHeight(500)

        self._create_UI()
        self._wigets_connect()

        if model:
            self.set_model(model)
        else:
            self._model = ModelTriaxialStaticLoad()

    def _create_UI(self):
        self.layout_wiget = QVBoxLayout()
        self.layout_wiget.addWidget(self.open_log_file)
        self.layout_wiget.addLayout(self.line)
        self.layout_wiget.addWidget(self.consolidation)
        self.layout_wiget.addWidget(self.deviator_loading)

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

    def set_model(self, model):
        self._model = model

        self.layout_wiget.removeWidget(self.open_log_file)
        self.open_log_file.deleteLater()
        self.open_log_file = None

        self._plot_reconsolidation()
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()
        self._plot_deviator_loading()

        self._connect_model_Ui()

    def _open_file(self):
        self.log_file_path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if self.log_file_path:
            try:
                self._model.set_test_file_path(self.log_file_path)
                self._plot_reconsolidation()
                self._plot_consolidation_sqrt()
                self._plot_consolidation_log()
                self._plot_deviator_loading()

                self._connect_model_Ui()

                self.open_log_file.set_path(self.log_file_path)
            except (ValueError, IndexError):
                pass

    def _connect_model_Ui(self):
        """Связь слайдеров с моделью"""
        self._cut_slider_deviator_set_len(len(self._model.deviator_loading._test_data.strain))
        self._cut_slider_deviator_set_val(self._model.deviator_loading.get_borders())
        self._cut_slider_consolidation_set_len(len(self._model.consolidation._test_data.time))

        self._deviator_volumeter_current_vol(self._model.deviator_loading.get_current_volume_strain())
        self._consolidation_volumeter_current_vol(self._model.consolidation.get_current_volume_strain())

    def _plot_reconsolidation(self):
        plot_data = self._model.reconsolidation.get_plot_data()
        res = self._model.reconsolidation.get_test_results()
        self.reconsolidation.plot(plot_data, res)

    def _plot_consolidation_sqrt(self):
        plot_data = self._model.consolidation.get_plot_data_sqrt()
        res = self._model.consolidation.get_test_results()
        self.consolidation.plot_sqrt(plot_data, res)

    def _plot_consolidation_log(self):
        plot_data = self._model.consolidation.get_plot_data_log()
        res = self._model.consolidation.get_test_results()
        self.consolidation.plot_log(plot_data, res)

    def _plot_deviator_loading(self):
        plot_data = self._model.deviator_loading.get_plot_data()
        res = self._model.deviator_loading.get_test_results()
        self.deviator_loading.plot(plot_data, res)


    def _deviator_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if self._model.deviator_loading.check_none():
            self._model.deviator_loading.choise_volume_strain(button.text())
            self._cut_slider_deviator_set_val(self._model.deviator_loading.get_borders())
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
        if self._model.deviator_loading.check_none():
            if (int(self.deviator_loading.slider_cut.high()) - int(self.deviator_loading.slider_cut.low())) >= 50:
                self._model.deviator_loading.change_borders(int(self.deviator_loading.slider_cut.low()),
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
        if self._model.consolidation.check_none():
            self._model.consolidation.choise_volume_strain(button.text())
            self._cut_slider_consolidation_set_len(len(self._model.consolidation._test_data.time))
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _cut_slider_consolidation_set_len(self, len):
        self.consolidation.slider_cut.setMinimum(0)
        self.consolidation.slider_cut.setMaximum(len)
        self.consolidation.slider_cut.setLow(0)
        self.consolidation.slider_cut.setHigh(len)

    def _cut_slider_consolidation_moove(self):
        if self._model.consolidation.check_none():
            if (int(self.consolidation.slider_cut.high()) - int(self.consolidation.slider_cut.low())) >= 50:
                self._model.consolidation.change_borders(int(self.consolidation.slider_cut.low()),
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

            self._model.consolidation.set_interpolation_param(param)
            self._model.consolidation.set_interpolation_type(interpolation_type)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _interpolate_slider_consolidation_moove(self):
        """Перемещение слайдера интерполяции. Не производит обработки, только отрисовка интерполированной кривой"""
        if self._model.consolidation.check_none():
            param = self.consolidation.function_replacement_slider.current_value()
            plot = self._model.consolidation.set_interpolation_param(param)
            self.consolidation.plot_interpolate(plot)

    def _interpolate_slider_consolidation_release(self):
        """Обработка консолидации при окончании движения слайдера"""
        if self._model.consolidation.check_none():
            self._model.consolidation.change_borders(int(self.consolidation.slider_cut.low()),
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
            self.point_identificator = self._model.consolidation.define_click_point(float(event.xdata),
                                                                                    float(event.ydata), canvas)

    def _canvas_on_moove(self, event):
        """Метод обрабаотывает перемещение зажатой точки"""
        if event.canvas is self.consolidation.sqrt_canvas:
            canvas = "sqrt"
        if event.canvas is self.consolidation.log_canvas:
            canvas = "log"

        if self.point_identificator and event.xdata and event.ydata and event.button == 1:
            self._model.consolidation.moove_catch_point(float(event.xdata), float(event.ydata), self.point_identificator,
                                                        canvas)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _canvas_on_release(self, event):
        """Метод обрабатывает итпуск зажатой точки"""
        self.point_identificator = None

    def get_test_results(self):
        return self._model.get_test_results()

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
            current_slider.set_borders(*params[var]["borders"])
            current_slider.set_value(params[var]["value"])

        self._activate = True

        self._sliders_moove()

class TriaxialStaticWidgetSoilTest(TriaxialStaticWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self, model=None):
        super().__init__()

        self.layout_wiget.removeWidget(self.open_log_file)
        self.open_log_file.deleteLater()
        self.open_log_file = None

        self.deviator_loading_sliders = TriaxialStaticLoading_Sliders({"fail_strain": "Деформация разрушения",
                  "residual_strength": "Остаточная прочность",
                  "residual_strength_param": "Изгиб остаточной прочности",
                  "qocr": "Значение дивиатора OCR",
                  "poisson": "Коэффициент Пуассона",
                  "dilatancy": "Угол дилатансии"})
        self.deviator_loading_sliders.setFixedHeight(180)

        self.consolidation_sliders = TriaxialStaticLoading_Sliders({"max_time": "Время испытания",
                                                                         "volume_strain_90": "Объемная деформация в Cv"})
        self.consolidation_sliders.setFixedHeight(90)

        self.consolidation.graph_layout.addWidget(self.consolidation_sliders)
        self.deviator_loading.graph_layout.addWidget(self.deviator_loading_sliders)

        self.consolidation.setFixedHeight(500+90)
        self.deviator_loading.setFixedHeight(500+180)

        if model:
            self.set_model(model)
        else:
            self._model = ModelTriaxialStaticLoadSoilTest()

        self.deviator_loading_sliders.signal[object].connect(self._deviator_loading_sliders_moove)
        self.consolidation_sliders.signal[object].connect(self._consolidation_sliders_moove)

        self.refresh_test_button = QPushButton("Обновить опыт")
        self.refresh_test_button.clicked.connect(self.refresh)
        self.layout_wiget.insertWidget(0, self.refresh_test_button)

       # self.set_test_params()
    def set_model(self, model):
        self._model = model
        self.deviator_loading_sliders.set_sliders_params(self._model.get_deviator_loading_draw_params())
        self.consolidation_sliders.set_sliders_params(self._model.get_consolidation_draw_params())

        self._plot_reconsolidation()
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()
        self._plot_deviator_loading()
        self._connect_model_Ui()

    def refresh(self):
        param = self._model.get_test_params()
        self._model.set_test_params(param)
        self.deviator_loading_sliders.set_sliders_params(self._model.get_deviator_loading_draw_params())
        self.consolidation_sliders.set_sliders_params(self._model.get_consolidation_draw_params())

        self._plot_reconsolidation()
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()
        self._plot_deviator_loading()
        self._connect_model_Ui()

    def set_params(self, param):
        """param = {'E': 30500.0, 'sigma_3': 186.4, 'sigma_1': 981.1, 'c': 0.001, 'fi': 42.8, 'qf': 794.7, 'K0': 0.5,
                 'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'build_press': 500.0, 'pit_depth': 7.0, 'Eur': '-',
                 'dilatancy': 4.95, 'OCR': 1, 'm': 0.61, 'lab_number': '7а-1',
                 'data_physical': {'borehole': '7а', 'depth': 19.0, 'name': 'Песок крупный неоднородный', 'ige': '-',
                                   'rs': 2.73, 'r': '-', 'rd': '-', 'n': '-', 'e': '-', 'W': 12.8, 'Sr': '-', 'Wl': '-',
                                   'Wp': '-', 'Ip': '-', 'Il': '-', 'Ir': '-', 'str_index': '-', 'gw_depth': '-',
                                   'build_press': 500.0, 'pit_depth': 7.0, '10': '-', '5': '-', '2': 6.8, '1': 39.2,
                                   '05': 28.0, '025': 9.2, '01': 6.1, '005': 10.7, '001': '-', '0002': '-', '0000': '-',
                                   'Nop': 7, 'flag': False}, 'test_type': 'Трёхосное сжатие (E)'}"""
        self._model.set_test_params(param)
        self.deviator_loading_sliders.set_sliders_params(self._model.get_deviator_loading_draw_params())
        self.consolidation_sliders.set_sliders_params(self._model.get_consolidation_draw_params())

        self._plot_reconsolidation()
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()
        self._plot_deviator_loading()
        self._connect_model_Ui()

    def _consolidation_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        self._model.set_consolidation_draw_params(params)
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()
        self._connect_model_Ui()

    def _deviator_loading_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        self._model.set_deviator_loading_draw_params(params)
        self._plot_deviator_loading()
        self._connect_model_Ui()



class TriaxialStaticDialog(QDialog):
    def __init__(self,test, parent=None):
        super(TriaxialStaticDialog, self).__init__(parent)
        self.resize(1200, 800)
        self.setWindowTitle("Обработка опыта")
        self.layout = QVBoxLayout(self)
        self.widget = TriaxialStaticWidget(test)
        self.layout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        #QMetaObject.connectSlotsByName(TriaxialStaticDialog)

class TriaxialStaticDialogSoilTest(QDialog):
    def __init__(self,test, parent=None):
        super(TriaxialStaticDialogSoilTest, self).__init__(parent)
        self.resize(1200, 800)
        self.setWindowTitle("Обработка опыта")
        self.layout = QVBoxLayout(self)
        self.widget = TriaxialStaticWidgetSoilTest(test)
        self.layout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        #QMetaObject.connectSlotsByName(TriaxialStaticDialog)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = TriaxialStaticWidgetSoilTest()
    ex.show()
    sys.exit(app.exec_())


