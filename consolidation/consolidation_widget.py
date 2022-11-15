from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout, \
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading

from general.tab_view import AppMixin
from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from excel_statment.initial_statment_widgets import ConsolidationStatment
from general.save_widget import Save_Dir
from excel_statment.initial_tables import TableVertical, LinePhysicalProperties
from excel_statment.functions import set_cell_data
from general.reports import report_consolidation, report_FCE, report_FC, zap
from consolidation.consolidation_UI import ModelTriaxialConsolidationUI
import numpy as np
from general.general_widgets import Float_Slider
from configs.styles import style
from singletons import Consolidation_models, statment
from loggers.logger import app_logger, log_this, handler
from tests_log.widget import TestsLogWidget
from tests_log.test_classes import TestsLogTriaxialStatic, TestsLogCyclic
import os
from version_control.configs import actual_version
from general.tab_view import TabMixin
__version__ = actual_version

from authentication.request_qr import request_qr


class ConsilidationSoilTestWidget(TabMixin, QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""

    MIN_SLIDER_LEN = 10  # in pnts

    def __init__(self, model=None):
        super().__init__()

        fill_keys = {
            "Eoed": "Одометрический модуль Eoed, кПа",
            "p_max": "Максимальное давление, МПа",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "m": "Показатель степени жесткости"
        }

        self.item_identification = TableVertical(fill_keys, size={"size": 100, "size_fixed_index": [1]})
        self.item_identification.setFixedHeight(180)
        self.item_identification.setFixedWidth(300)

        self.consolidation = ModelTriaxialConsolidationUI()
        self.prec_btn = QRadioButton('Повысить точность датчика')
        self.consolidation.function_replacement_line1.addWidget(self.prec_btn)

        self.consolidation_sliders = TriaxialStaticLoading_Sliders({
            "Cv": "Коэфициент Cv",
            "Ca": "Коэфициент Ca",
            "max_time": "Время испытания",
            "strain": "Значение деформации"})
        self.consolidation_sliders.setFixedHeight(150)

        self.consolidation.graph_layout.addWidget(self.consolidation_sliders)

        self.point_identificator = None


        self.consolidation_sliders.signal[object].connect(self._consolidation_sliders_moove)

        self._slider_cut_low_best_position = 0
        self._slider_cut_high_best_position = self.MIN_SLIDER_LEN + 1

        self._create_UI()
        self._wigets_connect()
        #if model:
            #self.set_model(model)
        #else:
            #self._model = ModelTriaxialStaticLoad()

    def _create_UI(self):
        self.layout = QVBoxLayout()
        self.layout_identification = QHBoxLayout()
        self.layout_identification.addWidget(self.item_identification)
        self.layout_1 = QHBoxLayout()
        self.layout_1.addWidget(self.consolidation)
        self.layout.addLayout(self.layout_identification)
        self.layout.addLayout(self.layout_1)

        self.setLayout(self.layout)

    def _wigets_connect(self):
        self.consolidation.function_replacement_button_group.buttonClicked.connect(self._consolidation_interpolation_type)
        self.prec_btn.clicked.connect(self._prec_type)
        self.consolidation.slider_cut.sliderMoved.connect(self._cut_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderMoved.connect(self._interpolate_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderReleased.connect(self._interpolate_slider_consolidation_release)
        self.consolidation.sqrt_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.sqrt_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.sqrt_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.consolidation.log_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.log_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.log_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.consolidation.mode_plot_dotted.clicked.connect(self._mode_dotted_connect)

    def _connect_model_Ui(self):
        """Связь слайдеров с моделью"""
        self._cut_slider_consolidation_set_len(len(Consolidation_models[statment.current_test]._test_data.time))

    def _plot_consolidation_sqrt(self):
        try:
            plot_data = Consolidation_models[statment.current_test].get_plot_data_sqrt()
            res = Consolidation_models[statment.current_test].get_test_results()
            self.consolidation.plot_sqrt(plot_data, res)
        except KeyError:
            pass

    def _plot_consolidation_log(self):
        try:
            plot_data = Consolidation_models[statment.current_test].get_plot_data_log()
            res = Consolidation_models[statment.current_test].get_test_results()
            self.consolidation.plot_log(plot_data, res)
        except KeyError:
            pass

    def _cut_slider_consolidation_set_len(self, len):
        self.consolidation.slider_cut.setMinimum(0)
        self.consolidation.slider_cut.setMaximum(len)
        self.consolidation.slider_cut.setLow(0)
        self.consolidation.slider_cut.setHigh(len)

    def _cut_slider_consolidation_moove(self):
        if Consolidation_models[statment.current_test].check_none():

            _left = int(self.consolidation.slider_cut.low())
            _right = int(self.consolidation.slider_cut.high())

            curr_len = _right - _left

            if curr_len < self.MIN_SLIDER_LEN:
                _left = int(self._slider_cut_low_best_position)
                _right = int(self._slider_cut_high_best_position)
                # self.consolidation.slider_cut.setLow(self._slider_cut_low_best_position)
                # self.consolidation.slider_cut.setHigh(self._slider_cut_high_best_position)

            Consolidation_models[statment.current_test].change_borders(_left, _right)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

            self._slider_cut_low_best_position = int(_left)
            self._slider_cut_high_best_position = int(_right)

    def _consolidation_interpolation_type(self, button):
        """Смена метода интерполяции консолидации"""
        if Consolidation_models[statment.current_test].check_none():
            if button.text() == "Интерполяция полиномом":
                interpolation_type = "poly"
                param = 8
                self.consolidation.function_replacement_slider.set_borders(5, 15)
                self.consolidation.function_replacement_slider.set_value(param)
            elif button.text() == "Интерполяция Эрмита":
                interpolation_type = "ermit"
                param = 0.5
                self.consolidation.function_replacement_slider.set_borders(0, 5)
                self.consolidation.function_replacement_slider.set_value(param)

            Consolidation_models[statment.current_test].set_interpolation_param(param)
            Consolidation_models[statment.current_test].set_interpolation_type(interpolation_type)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _mode_dotted_connect(self):
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()

    def _prec_type(self, checked):
        prec = None
        if checked:
            prec = 5
        Consolidation_models[statment.current_test].set_prec_type(prec)
        self._plot_consolidation_sqrt()
        self._plot_consolidation_log()

    def _interpolate_slider_consolidation_moove(self):
        """Перемещение слайдера интерполяции. Не производит обработки, только отрисовка интерполированной кривой"""
        if Consolidation_models[statment.current_test].check_none():
            param = self.consolidation.function_replacement_slider.current_value()
            plot = Consolidation_models[statment.current_test].set_interpolation_param(param)
            self.consolidation.plot_interpolate(plot)

    def _interpolate_slider_consolidation_release(self):
        """Обработка консолидации при окончании движения слайдера"""
        self._cut_slider_consolidation_moove()

    def _canvas_click(self, event):
        """Метод обрабатывает нажатие на канвас"""
        if event.canvas is self.consolidation.sqrt_canvas:
            canvas = "sqrt"
        if event.canvas is self.consolidation.log_canvas:
            canvas = "log"
        if event.button == 1 and event.xdata and event.ydata:
            self.point_identificator = Consolidation_models[statment.current_test].define_click_point(float(event.xdata),
                                                                                    float(event.ydata), canvas)

    def _canvas_on_moove(self, event):
        """Метод обрабаотывает перемещение зажатой точки"""
        if event.canvas is self.consolidation.sqrt_canvas:
            canvas = "sqrt"
        if event.canvas is self.consolidation.log_canvas:
            canvas = "log"

        if self.point_identificator and event.xdata and event.ydata and event.button == 1:
            Consolidation_models[statment.current_test].moove_catch_point(float(event.xdata), float(event.ydata), self.point_identificator,
                                                        canvas)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()

    def _canvas_on_release(self, event):
        """Метод обрабатывает итпуск зажатой точки"""
        self.point_identificator = None

    def refresh(self):
        try:
            Consolidation_models[statment.current_test].set_test_params()
            self.set_params(True)
        except:
            pass


    @log_this(app_logger, "debug")
    def set_params(self, param=None):
        try:
            self.consolidation_sliders.set_sliders_params(Consolidation_models[statment.current_test].get_draw_params())

            interpolation_type = Consolidation_models[statment.current_test].get_interpolation_type()
            if interpolation_type == "poly":
                self.consolidation.function_replacement_radio_button_1.setChecked(True)
                self.consolidation.function_replacement_radio_button_2.setChecked(False)
            elif interpolation_type == "ermit":
                self.consolidation.function_replacement_radio_button_1.setChecked(False)
                self.consolidation.function_replacement_radio_button_2.setChecked(True)

            prec_type = Consolidation_models[statment.current_test].get_prec_type()
            if prec_type:
                self.prec_btn.setChecked(True)
            else:
                self.prec_btn.setChecked(False)

            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._connect_model_Ui()

        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _consolidation_sliders_moove(self, params):
        """Обработчик движения слайдера"""
        try:
            Consolidation_models[statment.current_test].set_draw_params(params)
            self._plot_consolidation_sqrt()
            self._plot_consolidation_log()
            self._connect_model_Ui()
        except KeyError:
            pass

class ConsolidationSoilTestApp(AppMixin,QWidget):

    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = ConsolidationStatment()
        self.tab_2 = ConsilidationSoilTestWidget()
        self.tab_3 = Save_Dir( {
                "standart": "Стандардный",
                "plaxis": "Plaxis"},
            qr=True)

        self.save_cv_ca_btn = QCheckBox('Сохранить cv ca')
        self.save_cv_ca_btn.setChecked(False)
        self.cv_ca_save_path = None
        self.save_cv_ca_btn.clicked.connect(self.on_save_cv_ca_btn)
        self.tab_3.advanced_box_layout.insertWidget(self.tab_3.advanced_box_layout.count() - 1, self.save_cv_ca_btn)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт консолидации")
        self.tab_widget.addTab(self.tab_3, "Сохранение отчетов")
        self.layout.addWidget(self.tab_widget)

        self.physical_line = LinePhysicalProperties()

        self.tab_1.signal[bool].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_3.update())
        self.tab_1.signal[bool].connect(lambda x: self.physical_line.set_data())

        self.tab_3.save_button.clicked.connect(self.save_report)
        self.tab_3.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_3.jornal_button.clicked.connect(self.jornal)

        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.save_massage = True
        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

        self.tab_2.layout_identification.addWidget(self.physical_line)
        self.physical_line.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line.save_button.clicked.connect(self.save_report_and_continue)

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
        self.tab_2.item_identification.set_data()
        self.tab_2.set_params()
        # self.tab_2._consolidation_interpolation_type(self.tab_2.consolidation.function_replacement_button_group.checkedButton())

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            if statment[statment.current_test].mechanical_properties.p_max >= 1:
                equipment = "GIG, Absolut Digimatic ID-S"
            else:
                equipment = "ЛИГА КЛ1, КППА 60/25 ДС (ГТ 1.1.1), GIG, Absolut Digimatic ID-S, АСИС ГТ.2.0.5"


            test_parameter = {"equipment": equipment,
                              "mode": "Статическая нагрузка",
                              "p_max": statment[statment.current_test].mechanical_properties.p_max,
                              "h": 20,
                              "d": 71.4}

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

            name = file_path_name + " " + statment.general_data.object_number + " ВК" + ".pdf"
            Consolidation_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"consolidation_models{statment.general_data.get_shipment_number()}.pickle"))
            #models[statment.current_test].save_log_file(save + "/" + "Test.1.log")
            test_result = Consolidation_models[statment.current_test].get_test_results()
            Consolidation_models[statment.current_test].save_cvi_file(save, statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

            if self.tab_3.qr:
                qr = request_qr()
            else:
                qr = None

            report_consolidation(save + "/" + name, data_customer,
                                 statment[statment.current_test].physical_properties, statment.current_test,
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 self.tab_2.consolidation.save_canvas(), self.tab_3.report_type, "{:.2f}".format(__version__), qr_code=qr)

            shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

            #set_cell_data(self.tab_1.path,
                          #"BK" + str(statment[statment.current_test].physical_properties.sample_number + 7),
                          #test_result["E50"], sheet="Лист1", color="FF6961")

            Consolidation_models[statment.current_test].save_log(save, file_path_name + " " + statment.general_data.object_number + "ВК")

            # Запись в xls параметров ca и cv
            if self.save_cv_ca_btn.isChecked():
                cv_ca_file_name = 'Параметры cv ca.xlsx'

                if self.cv_ca_save_path:
                    cv_ca_save_path = self.cv_ca_save_path + "/" + cv_ca_file_name
                else:
                    cv_ca_save_path = statment.save_dir.arhive_directory + "/" + cv_ca_file_name

                if os.path.isfile(cv_ca_save_path):
                    pass
                else:
                    shutil.copy('./consolidation/'+cv_ca_file_name, cv_ca_save_path)

                set_cell_data(cv_ca_save_path,
                              ('A' + str(statment[statment.current_test].physical_properties.sample_number + 2),
                              (statment[statment.current_test].physical_properties.sample_number + 2, 0)),
                              statment[statment.current_test].physical_properties.laboratory_number,
                              sheet="Лист1")
                set_cell_data(cv_ca_save_path,
                              ('B' + str(statment[statment.current_test].physical_properties.sample_number + 2),
                              (statment[statment.current_test].physical_properties.sample_number + 2, 1)),
                              statment[statment.current_test].physical_properties.borehole,
                              sheet="Лист1")
                set_cell_data(cv_ca_save_path,
                              ('C' + str(statment[statment.current_test].physical_properties.sample_number + 2),
                              (statment[statment.current_test].physical_properties.sample_number + 2, 2)),
                              statment[statment.current_test].physical_properties.depth,
                              sheet="Лист1")
                set_cell_data(cv_ca_save_path,
                              ('D' + str(statment[statment.current_test].physical_properties.sample_number + 2),
                              (statment[statment.current_test].physical_properties.sample_number + 2, 3)),
                              test_result["Cv_log"],
                              sheet="Лист1")
                set_cell_data(cv_ca_save_path,
                              ('E' + str(statment[statment.current_test].physical_properties.sample_number + 2),
                              (statment[statment.current_test].physical_properties.sample_number + 2, 4)),
                              test_result["Ca_log"],
                              sheet="Лист1")


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
                self.physical_line.set_data()
                break
            else:
                pass

    def jornal(self):
        self.dialog = TestsLogWidget({"ЛИГА КЛ-1С": 23, "АСИС ГТ.2.0.5": 30}, TestsLogCyclic, self.tab_1.path)
        self.dialog.show()

    def on_save_cv_ca_btn(self, checked):
        if checked and self.cv_ca_save_path is None:
            self.cv_ca_save_path = QFileDialog.getExistingDirectoryUrl(self, 'Папка для сохранения cv ca').toLocalFile()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = ConsolidationSoilTestApp()
    ex.show()
    sys.exit(app.exec_())


