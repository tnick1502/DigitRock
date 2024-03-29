
from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout, \
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog, QHeaderView, \
    QCheckBox, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading

from excel_statment.initial_tables import LinePhysicalProperties
from shear_test.shear_widgets import ShearWidget, ShearWidgetSoilTest
from excel_statment.initial_statment_widgets import ShearStatment
from excel_statment.position_configs import c_fi_E_PropertyPosition
from general.save_widget import Save_Dir
from excel_statment.functions import set_cell_data
from general.reports import report_consolidation, report_FCE, report_Shear, report_Shear_Dilatancy, zap
from shear_test.shear_dilatancy_widgets_UI import ModelShearItemUI, ModelShearFileOpenUI, ModelShearDilatancyUI
from general.general_widgets import Slider
from configs.styles import style
from singletons import Shear_Dilatancy_models, Shear_models, statment
from loggers.logger import app_logger, log_this, handler
from tests_log.widget import TestsLogWidget
from tests_log.test_classes import TestsLogTriaxialStatic
import os
from general.tab_view import TabMixin, AppMixin
from version_control.configs import actual_version
__version__ = actual_version
from authentication.request_qr import request_qr
from authentication.control import control
from metrics.session_writer import SessionWriter
from general.movie_label import Loader

class ShearProcessingWidget(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self, model=None):
        super().__init__()

        self.open_log_file = ModelShearFileOpenUI()
        self.log_file_path = None

        self.item_identification = ModelShearItemUI()
        self.item_identification.setFixedWidth(300)
        #self.item_identification.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.line = QHBoxLayout()
        self.line.addWidget(self.item_identification)

        self.point_identificator = None
        self.deviator_loading = ModelShearDilatancyUI()
        self.deviator_loading.setFixedHeight(500)

        self._create_UI()
        self._wigets_connect()


    def _create_UI(self):
        self.layout_wiget = QVBoxLayout()
        self.layout_wiget.addWidget(self.open_log_file)
        self.layout_wiget.addLayout(self.line)
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
        self.deviator_loading.slider_cut.sliderMoved.connect(self._cut_slider_deviator_moove)

    def _open_file(self, path=None):
        if not path:
            self.log_file_path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        else:
            self.log_file_path = path

        if self.log_file_path:
            try:
                self._model.set_test_file_path(self.log_file_path)
                self._plot_deviator_loading()

                self._connect_model_Ui()
                if not path:
                    self.open_log_file.set_path(self.log_file_path)

            except (ValueError, IndexError):
                pass

    def _connect_model_Ui(self):
        """Связь слайдеров с моделью"""
        self._cut_slider_deviator_set_len(len(Shear_Dilatancy_models[statment.current_test]._test_data.strain))
        self._cut_slider_deviator_set_val(Shear_Dilatancy_models[statment.current_test].get_borders())
        self._deviator_volumeter_current_vol(Shear_Dilatancy_models[statment.current_test].get_current_volume_strain())

    def _plot_deviator_loading(self):
        try:
            plot_data = Shear_Dilatancy_models[statment.current_test].get_plot_data()
            res = Shear_Dilatancy_models[statment.current_test].get_test_results()
            self.deviator_loading.plot(plot_data, res)
        except KeyError:
            pass

    def _deviator_volumeter(self, button):
        """Передача значения выбранного волюмометра в модель"""
        if Shear_Dilatancy_models[statment.current_test].shear_dilatancy.check_none():
            Shear_Dilatancy_models[statment.current_test].shear_dilatancy.choise_volume_strain(button.text())
            self._cut_slider_deviator_set_val(Shear_Dilatancy_models[statment.current_test].shear_dilatancy.get_borders())
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
        if Shear_Dilatancy_models[statment.current_test].check_none():
            if (int(self.deviator_loading.slider_cut.high()) - int(self.deviator_loading.slider_cut.low())) >= 50:
                Shear_Dilatancy_models[statment.current_test].change_borders(int(self.deviator_loading.slider_cut.low()),
                                                        int(self.deviator_loading.slider_cut.high()))
            self._plot_deviator_loading()

    def _canvas_on_release(self, event):
        """Метод обрабатывает итпуск зажатой точки"""
        self.point_identificator = None

    def get_test_results(self):
        return Shear_Dilatancy_models[statment.current_test].get_test_results()


class Shear_Sliders(QWidget):
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

class ShearDilatancySoilTestWidget(TabMixin, ShearProcessingWidget):
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

        self.deviator_loading_sliders = Shear_Sliders({"E50": "Наклон прямолинейного участка",
                                                       "fail_strain": "Деформация разрушения",
                  "residual_strength": "Остаточная прочность",
                  "residual_strength_param": "Изгиб остаточной прочности",
                  "qocr": "Значение дивиатора OCR",
                  "poisson": "Коэффициент Пуассона",
                  "dilatancy": "Угол дилатансии",
                  "volumetric_strain_xc": "Объемн. деформ. в пике",
                    "amplitude": "Амплитуда девиаций"})
        self.deviator_loading_sliders.setFixedHeight(210)

        self.deviator_loading.graph_layout.addWidget(self.deviator_loading_sliders)
        self.deviator_loading.setFixedHeight(530+180)
        self.deviator_loading_sliders.signal[object].connect(self._deviator_loading_sliders_moove)

    def refresh(self):
        try:
            Shear_Dilatancy_models[statment.current_test].set_test_params()
            self.deviator_loading_sliders.set_sliders_params(Shear_Dilatancy_models[statment.current_test].get_draw_params())
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def set_params(self, param=None):
        try:
            self.deviator_loading_sliders.set_sliders_params(Shear_Dilatancy_models[statment.current_test].get_draw_params())
            self._plot_deviator_loading()
            self._connect_model_Ui()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _consolidation_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _deviator_loading_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            Shear_Dilatancy_models[statment.current_test].set_draw_params(params)
            self._plot_deviator_loading()
            self._connect_model_Ui()
            self.signal.emit(True)
        except KeyError:
            pass


class ShearProcessingApp(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()

        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = ShearStatment()
        self.tab_2 = ShearProcessingWidget()
        self.tab_3 = ShearWidget()
        self.tab_4 = Save_Dir()

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
                              "sigma_3": self.tab_2._model.shear_dilatancy._test_params.sigma_3,
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
                assert self.tab_2._model.shear_dilatancy._test_params.sigma_3, "Не загружен файл опыта"
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

class ShearSoilTestApp(AppMixin, QWidget):

    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])
        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = ShearStatment()
        self.tab_2 = ShearDilatancySoilTestWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)
        self.tab_3 = ShearWidgetSoilTest()
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)
        self.tab_4 = Save_Dir(qr=True, asis_btn=True)
        self.tab_4.popIn.connect(self.addTab)
        self.tab_4.popOut.connect(self.removeTab)

        self.vertical_def_btn = QCheckBox('Вертикальная деформация')
        self.vertical_def_btn.setChecked(True)
        self.tab_4.advanced_box_layout.insertWidget(self.tab_4.advanced_box_layout.count() - 1, self.vertical_def_btn)

        box = QGroupBox('Состояние образца')
        self.combobox = QComboBox()
        layout = QVBoxLayout()

        self.combobox.addItems(["Автоматически", "Не указывать", "При природной влажности", "В водонасыщенном состоянии"])

        box.setLayout(layout)
        layout.addWidget(self.combobox)

        self.tab_4.advanced_box_layout.insertWidget(self.tab_4.advanced_box_layout.count() - 1, box)

        # self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Срез Дилатансия")
        self.tab_widget.addTab(self.tab_3, "Опыт Срез")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.signal[bool].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_4.update(x))

        self.previous_test_type = ''
        self.tab_1.open_line.combo_changes_signal.connect(self.on_test_type_changed)

        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_pickle.clicked.connect(self.save_pickle)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_4.jornal_button.clicked.connect(self.jornal)

        self.save_massage = True
        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line.addWidget(self.physical_line_1)
        self.physical_line_1.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3.refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)

        self.loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                        message_port=7782, parent=self)

    def save_pickle(self):
        try:
            models = [model for model in [Shear_models] if len(model)]

            names = []
            if len(Shear_models):
                names.append(
                    f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle")

            statment.save(models, names)

            _test_mode = statment.general_parameters.test_mode

            if ShearStatment.is_dilatancy_type(_test_mode):
                Shear_Dilatancy_models.dump(os.path.join(statment.save_dir.save_directory,
                                                         f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
            elif not ShearStatment.is_dilatancy_type(_test_mode):
                Shear_models.dump(os.path.join(statment.save_dir.save_directory,
                                               f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
            QMessageBox.about(self, "Сообщение", "Pickle успешно сохранен")
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

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
        if self.tab_1.shear_test_type_from_open_line() in [ShearStatment.SHEAR, ShearStatment.SHEAR_NATURAL,
                                                           ShearStatment.SHEAR_SATURATED,
                                                           ShearStatment.SHEAR_NN, ShearStatment.SHEAR_DD,
                                                           ShearStatment.SHEAR_DD_NATURAL,
                                                           ShearStatment.SHEAR_DD_SATURATED]:
            self.tab_3.item_identification.set_data()
            self.tab_3.set_params()
            self.physical_line_2.set_data()
        elif self.tab_1.shear_test_type_from_open_line() == ShearStatment.SHEAR_DILATANCY:
            self.tab_2.item_identification.set_data()
            self.tab_2.set_params()
            self.physical_line_1.set_data()


    def save_report(self, save_all_mode=False):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            # if statment.general_parameters.equipment == "АСИС ГТ.2.0.5 (150х300)":
            #     h, d = 300, 150
            # else:
            #     d, h = statment[statment.current_test].physical_properties.sample_size
            # h = 35.0
            # d = 71.4

            h, d = statment.general_parameters.equipment_sample_h_d

            moisture_type = self.tab_1.open_line.get_data()["optional"]
            if self.combobox.currentText() == "Автоматически":
                moisture = ""
                if moisture_type == self.tab_1.test_parameters["optional"]["vars"][1]:
                    moisture = "при природной влажности, "
                elif moisture_type == self.tab_1.test_parameters["optional"]["vars"][2]:
                    moisture = "в водонасыщенном состоянии, "
            else:
                moisture_type_custom = self.combobox.currentText()
                moisture = ""
                if moisture_type_custom == "Не указывать":
                    moisture = " "
                elif moisture_type_custom == "В водонасыщенном состоянии":
                    moisture = "в водонасыщенном состоянии, "
                elif moisture_type_custom == "При природной влажности":
                    moisture = "при природной влажности, "

            test_mode = self.tab_1.shear_test_type_from_open_line()
            mode = "КД"
            if test_mode == ShearStatment.SHEAR_NN:
                mode = "НН"
            elif test_mode in [ShearStatment.SHEAR_DD, ShearStatment.SHEAR_DD_NATURAL, ShearStatment.SHEAR_DD_SATURATED]:
                mode = "ПП"

            test_parameter = {"equipment": statment.general_parameters.equipment,
                              "mode": mode + ", " + moisture + "кинематическое нагружение",
                              "sigma": statment[statment.current_test].mechanical_properties.sigma,
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

            _test_mode = statment.general_parameters.test_mode

            if self.tab_4.qr:
                qr = request_qr()
            else:
                qr = None

            shear_type_code = ""
            moisture = ""
            if moisture_type == self.tab_1.test_parameters["optional"]["vars"][1]:
                moisture = "п"
            elif moisture_type == self.tab_1.test_parameters["optional"]["vars"][2]:
                moisture = "в"

            if ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR:
                '''Cрез не природное и не водонасыщенное'''
                shear_type_code = "С"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_NATURAL:
                '''Срез природное'''
                shear_type_code = "С"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_SATURATED:
                '''Срез водонасыщенное'''
                shear_type_code = "С"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_DD:
                '''Срез плашка по плашке'''
                shear_type_code = "СПП"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_DD_NATURAL:
                '''Срез плашка по плашке природный'''
                shear_type_code = "СПП"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_DD_SATURATED:
                '''Срез плашка по плашке водонасыщенный'''
                shear_type_code = "СПП"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_NN:
                '''Срез НН'''
                shear_type_code = "НН"+moisture
            elif ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_DILATANCY:
                '''Срез дилатансия'''
                shear_type_code = "СД"+moisture



            if ShearStatment.is_dilatancy_type(_test_mode):
                name = file_path_name + " " + statment.general_data.object_number + f" {shear_type_code}" + ".pdf"

                Shear_Dilatancy_models[statment.current_test].save_log_file(save + "/" + "Test.1.log",
                                                                            nonzero_vertical_def=self.vertical_def_btn.isChecked())
                Shear_Dilatancy_models[statment.current_test].save_cvi_file(save,
                                                                            statment.save_dir.cvi_directory +
                                                                            "/" + f"{file_path_name} ЦВИ.xls")

                test_result = Shear_Dilatancy_models[statment.current_test].get_test_results()
                report_Shear_Dilatancy(save + "/" + name, data_customer,
                                       statment[statment.current_test].physical_properties, statment.current_test,
                                       os.getcwd() + "/project_data/", test_parameter, test_result,
                                       (*self.tab_2.deviator_loading.save_canvas(), None), "{:.2f}".format(__version__), qr_code=qr, name=shear_type_code)

                shutil.copy(save + "/" + name,  statment.save_dir.report_directory + "/" + name)

            elif not ShearStatment.is_dilatancy_type(_test_mode):
                name = file_path_name + " " + statment.general_data.object_number + f" {shear_type_code}" + ".pdf"
                Shear_models[statment.current_test].save_log_files(save, nonzero_vertical_def=self.vertical_def_btn.isChecked())
                Shear_models[statment.current_test].save_cvi_file(save,
                                                                  statment.save_dir.cvi_directory +
                                                                  "/" + f"{file_path_name} ЦВИ.xls",
                                                                  ShearStatment.shear_type(_test_mode) == ShearStatment.SHEAR_NATURAL)
                test_result = {}
                test_result["sigma_shear"], test_result["tau_max"] = Shear_models[
                    statment.current_test].get_sigma_tau_max()

                test_result["c"], test_result["fi"] = Shear_models[statment.current_test].get_test_results()["c"], \
                                                      Shear_models[statment.current_test].get_test_results()["fi"]

                if self.tab_4.roundFI_btn.isChecked():
                    test_result["fi"] = zap(test_result["fi"], 0)

                report_Shear(save + "/" + name, data_customer,
                             statment[statment.current_test].physical_properties, statment.current_test,
                             os.getcwd() + "/project_data/", test_parameter, test_result,
                             (*self.tab_3.save_canvas(), *self.tab_3.save_canvas()), "{:.2f}".format(__version__),
                             qr_code=qr, name=shear_type_code)

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7


                set_cell_data(
                    self.tab_1.path,
                    (c_fi_E_PropertyPosition[statment.general_parameters.test_mode][0][1] + str(number),
                    (number, c_fi_E_PropertyPosition[statment.general_parameters.test_mode][1][1])),
                    test_result["fi"], sheet="Лист1", color="FF6961")

                set_cell_data(
                    self.tab_1.path,
                    (c_fi_E_PropertyPosition[statment.general_parameters.test_mode][0][0] + str(number),
                    (number, c_fi_E_PropertyPosition[statment.general_parameters.test_mode][1][0])),
                    test_result["c"], sheet="Лист1", color="FF6961")



            #statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
                          #name=statment.general_parameters.test_mode + ".pickle")

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(
                    f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            control()
            return True, 'Успешно'

        except AssertionError as error:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            return False, f'{str(error)}'

        except PermissionError:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)
            return False, 'Не закрыт файл отчета'

        except:
            app_logger.exception(f"Не выгнан {statment.current_test}")



    def save_all_reports(self):
        if self.loader.is_running:
            QMessageBox.critical(self, "Ошибка", "Закройте окно сохранения")
            return
        try:
            models = [model for model in [Shear_models] if len(model)]

            names = []
            if len(Shear_models):
                names.append(
                    f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle")

            statment.save(models, names)

            _test_mode = statment.general_parameters.test_mode

            if ShearStatment.is_dilatancy_type(_test_mode):
                Shear_Dilatancy_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
            elif not ShearStatment.is_dilatancy_type(_test_mode):
                Shear_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        statment.save_dir.clear_dirs()


        def save():
            count = len(statment)
            Loader.send_message(self.loader.port, f"Сохранено 0 из {count}")

            errors = []
            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self.set_test_parameters(True)
                try:
                    is_ok, message = self.save_report(save_all_mode=True)
                    if not is_ok:
                        self.loader.close_OK(
                            f"Ошибка сохранения пробы {statment.current_test}\n{message}.\nОперация прервана.")
                        app_logger.info(f"Ошибка сохранения пробы {message}")
                        return
                except Exception as err:
                    self.loader.close_OK(f"Ошибка сохранения пробы {statment.current_test}. Операция прервана.")
                    app_logger.info(f"Ошибка сохранения пробы {err}")
                    return
                Loader.send_message(self.loader.port, f"Сохранено {i + 1} из {count}")
            Loader.send_message(self.loader.port, f"Сохранено {count} из {count}")

            self.loader.close_OK(f"Объект выгнан")
            self.save_massage = True

            try:
                models = [model for model in [Shear_models] if len(model)]

                names = []
                if len(Shear_models):
                    names.append(f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle")

                statment.save(models, names)

            except Exception as err:
                QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        t = threading.Thread(target=save)
        self.loader.start()
        t.start()

        SessionWriter.write_session(len(statment))

    def jornal(self):
        self.dialog = TestsLogWidget({"ЛИГА КЛ-1С": 23, "АСИС ГТ.2.0.5": 30}, TestsLogTriaxialStatic, self.tab_1.path)
        self.dialog.show()

    def on_test_type_changed(self):
        if self.tab_1.shear_test_type_from_open_line() in [ShearStatment.SHEAR,
                                                           ShearStatment.SHEAR_NATURAL, ShearStatment.SHEAR_SATURATED,
                                                           ShearStatment.SHEAR_NN, ShearStatment.SHEAR_DD,
                                                           ShearStatment.SHEAR_DD_NATURAL,
                                                           ShearStatment.SHEAR_DD_SATURATED]:
            self.tab_widget.setTabEnabled(1, False)
            self.tab_widget.setTabEnabled(2, True)
        elif self.tab_1.shear_test_type_from_open_line() == ShearStatment.SHEAR_DILATANCY:
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setTabEnabled(2, False)
        else:
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setTabEnabled(2, True)

        #        Устарело!
        # if self.tab_1.open_line.get_data()["test_mode"] != self.previous_test_type:
        #     test_mode = self.tab_1.open_line.get_data()["test_mode"]
        #     self.tab_1.set_optional_parameter(test_mode)
        # self.previous_test_type = self.tab_1.open_line.get_data()["test_mode"]

    def save_report_and_continue(self):
        try:
            models = [model for model in [Shear_models] if len(model)]

            names = []
            if len(Shear_models):
                names.append(
                    f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle")

            statment.save(models, names)

            _test_mode = statment.general_parameters.test_mode

            if ShearStatment.is_dilatancy_type(_test_mode):
                Shear_Dilatancy_models.dump(os.path.join(statment.save_dir.save_directory,
                                                         f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
            elif not ShearStatment.is_dilatancy_type(_test_mode):
                Shear_models.dump(os.path.join(statment.save_dir.save_directory,
                                               f"{ShearStatment.models_name(ShearStatment.shear_type(self.tab_1._shear_type)).split('.')[0]}{statment.general_data.get_shipment_number()}.pickle"))
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

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

        SessionWriter.write_test()



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = ShearSoilTestApp()
    ex.show()
    sys.exit(app.exec_())


