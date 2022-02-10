from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout,\
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading

from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from excel_statment.initial_statment_widgets import ConsolidationStatment
from general.save_widget import Save_Dir
from general.initial_tables import TableVertical
from excel_statment.functions import set_cell_data
from general.reports import report_consolidation, report_FCE, report_FC
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
__version__ = actual_version


class ConsilidationSoilTestWidget(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self, model=None):
        super().__init__()

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "Eoed": "Одометрический модуль Eoed, кПа",
            "p_max": "Максимальное давление, МПа",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "m": "Показатель степени жесткости"
        }

        self.item_identification = TableVertical(fill_keys)
        self.item_identification.setFixedWidth(250)

        self.consolidation = ModelTriaxialConsolidationUI()

        self.consolidation_sliders = TriaxialStaticLoading_Sliders({
            "Cv": "Коэфициент Cv",
            "Ca": "Коэфициент Ca",
            "max_time": "Время испытания",
            "strain": "Значение деформации"})
        self.consolidation_sliders.setFixedHeight(150)

        self.consolidation.graph_layout.addWidget(self.consolidation_sliders)

        self.point_identificator = None
        self.consolidation.setFixedHeight(590)

        self.consolidation_sliders.signal[object].connect(self._consolidation_sliders_moove)

        self._create_UI()
        self._wigets_connect()

        self.refresh_test_button = QPushButton("Обновить опыт")
        self.refresh_test_button.clicked.connect(self.refresh)
        self.layout.insertWidget(0, self.refresh_test_button)

        #if model:
            #self.set_model(model)
        #else:
            #self._model = ModelTriaxialStaticLoad()

    def _create_UI(self):
        self.layout = QVBoxLayout()
        self.layout_1 = QHBoxLayout()
        self.layout_1.addWidget(self.item_identification)
        self.layout_1.addWidget(self.consolidation)

        self.layout.addLayout(self.layout_1)

        self.save_wigdet = Save_Dir()

        self.layout.addWidget(self.save_wigdet)

        self.setLayout(self.layout)

    def _wigets_connect(self):
        self.consolidation.function_replacement_button_group.buttonClicked.connect(self._consolidation_interpolation_type)
        self.consolidation.slider_cut.sliderMoved.connect(self._cut_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderMoved.connect(self._interpolate_slider_consolidation_moove)
        self.consolidation.function_replacement_slider.sliderReleased.connect(self._interpolate_slider_consolidation_release)
        self.consolidation.sqrt_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.sqrt_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.sqrt_canvas.mpl_connect('button_release_event', self._canvas_on_release)

        self.consolidation.log_canvas.mpl_connect('button_press_event', self._canvas_click)
        self.consolidation.log_canvas.mpl_connect("motion_notify_event", self._canvas_on_moove)
        self.consolidation.log_canvas.mpl_connect('button_release_event', self._canvas_on_release)

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
            if (int(self.consolidation.slider_cut.high()) - int(self.consolidation.slider_cut.low())) >= 50:
                Consolidation_models[statment.current_test].consolidation.change_borders(int(self.consolidation.slider_cut.low()),
                                                            int(self.consolidation.slider_cut.high()))
                self._plot_consolidation_sqrt()
                self._plot_consolidation_log()

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

    def _interpolate_slider_consolidation_moove(self):
        """Перемещение слайдера интерполяции. Не производит обработки, только отрисовка интерполированной кривой"""
        if Consolidation_models[statment.current_test].check_none():
            param = self.consolidation.function_replacement_slider.current_value()
            plot = Consolidation_models[statment.current_test].set_interpolation_param(param)
            self.consolidation.plot_interpolate(plot)

    def _interpolate_slider_consolidation_release(self):
        """Обработка консолидации при окончании движения слайдера"""
        if Consolidation_models[statment.current_test].check_none():
            Consolidation_models[statment.current_test].change_borders(int(self.consolidation.slider_cut.low()),
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

class ConsolidationSoilTestApp(QWidget):

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

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт консолидации")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.signal[bool].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_2.save_wigdet.set_directory(x, "Консолидация", statment.general_data.shipment_number))

        self.tab_2.save_wigdet.save_button.clicked.connect(self.save_report)
        self.tab_2.save_wigdet.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_2.save_wigdet.jornal_button.clicked.connect(self.jornal)

        self.save_massage = True
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
        self.tab_2.item_identification.set_data()
        self.tab_2.set_params()
        self.tab_2._consolidation_interpolation_type(self.tab_2.consolidation.function_replacement_button_group.checkedButton())

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.current_test.replace("/", "-").replace("*", "")

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

            save = self.tab_2.save_wigdet.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")
            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            name = file_path_name + " " + statment.general_data.object_number + " ВК" + ".pdf"
            Consolidation_models.dump(''.join(os.path.split(self.tab_2.save_wigdet.directory)[:-1]), name="consolidation_models.pickle")
            #models[statment.current_test].save_log_file(save + "/" + "Test.1.log")
            test_result = Consolidation_models[statment.current_test].get_test_results()
            Consolidation_models[statment.current_test].save_cvi_file(save, self.tab_2.save_wigdet.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

            report_consolidation(save + "/" + name, data_customer,
                                 statment[statment.current_test].physical_properties, statment.current_test,
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 self.tab_2.consolidation.save_canvas(), "{:.2f}".format(__version__))

            shutil.copy(save + "/" + name, self.tab_2.save_wigdet.report_directory + "/" + name)

            #set_cell_data(self.tab_1.path,
                          #"BK" + str(statment[statment.current_test].physical_properties.sample_number + 7),
                          #test_result["E50"], sheet="Лист1", color="FF6961")

            statment.dump(''.join(os.path.split(self.tab_2.save_wigdet.directory)[:-1]), "consolidation.pickle")

            Consolidation_models[statment.current_test].save_log(save, file_path_name + " " + statment.general_data.object_number + "ВК")

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
        self.dialog = TestsLogWidget({"ЛИГА КЛ-1С": 23, "АСИС ГТ.2.0.5": 30}, TestsLogCyclic, self.tab_1.path)
        self.dialog.show()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    # app.setStyleSheet("QLabel{font-size: 14pt;}")
    ex = ConsolidationSoilTestApp()
    ex.show()
    sys.exit(app.exec_())


