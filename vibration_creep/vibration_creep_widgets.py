from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QTabWidget, \
    QDialog, QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QTableWidgetItem, QHeaderView, \
    QTextEdit, QProgressDialog, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
import sys
import shutil
import os
import threading

from excel_statment.initial_tables import LinePhysicalProperties
from excel_statment.initial_statment_widgets import VibrationCreepStatment
from general.reports import report_VibrationCreep, report_VibrationCreep3, zap
from general.save_widget import Save_Dir
from general.general_widgets import Float_Slider
from configs.styles import style
from vibration_creep.vibration_creep_widgets_UI import VibrationCreepUI
from excel_statment.initial_tables import TableVertical
from static_loading.triaxial_static_test_widgets import StaticSoilTestWidget
from general.initial_tables import TableCastomer
from general.excel_functions import create_json_file, read_json_file
from excel_statment.functions import set_cell_data
from general.report_general_statment import save_report
from singletons import E_models, VC_models, statment
from loggers.logger import app_logger, handler
from version_control.configs import actual_version
from general.tab_view import TabMixin, AppMixin
__version__ = actual_version
from general.general_statement import StatementGenerator
from authentication.control import control

from authentication.request_qr import request_qr
from metrics.session_writer import SessionWriter
from general.movie_label import Loader

class VibrationCreepSoilTestWidget(TabMixin, QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    signal = pyqtSignal()
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()

    def _create_Ui(self):
        self.main_layout = QVBoxLayout(self)

        self.layout = QHBoxLayout()
        self.dynamic_widget = VibrationCreepUI()
        self.layout_2 = QVBoxLayout()

        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "qf": "Максимальный девиатор qf, кПа",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "t": "Касательное напряжение τ, кПа",
            "Kd": "Kd, д.е.",
            "frequency": "Частота, Гц",
            "K0": "K0, д.е.",
            "poisons_ratio": "Коэффициент Пуассона, д.е.",
            "Cv": "Коэффициент консолидации Cv",
            "Ca": "Коэффициент вторичной консолидации Ca",
            "dilatancy_angle": "Угол дилатансии, град",
            "OCR": "OCR",
            "m": "Показатель степени жесткости"
        }
        self.identification = TableVertical(fill_keys, size={"size": 100, "size_fixed_index": [1]})
        self.identification.setFixedWidth(350)
        self.identification.setFixedHeight(350)
        self.layout.addWidget(self.dynamic_widget)
        self.sliders = KdSliders()
        self.sliders.setFixedWidth(350)

        self.layout_2.addWidget(self.identification)
        self.layout_2.addWidget(self.sliders)
        self.layout.addLayout(self.layout_2)
        self.layout_2.addStretch(-1)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addLayout(self.layout)

        self.dynamic_widget.predition_radio_btn.clicked.connect(self._plot)

    def set_test_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        self._plot()
        self.signal.emit()

    def static_model_change(self, param):
        VC_models[statment.current_test]._test_processing()
        self._plot()
        self.signal.emit()

    def _refresh(self):
        try:
            VC_models[statment.current_test].set_test_params()
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    def _plot(self):
        """Построение графиков опыта"""
        plots = VC_models[statment.current_test].get_plot_data()
        res = VC_models[statment.current_test].get_test_results()
        self.dynamic_widget.plot(plots, res)

        #plots = self._model._static_test_data.get_plot_data()
        #res = self._model._static_test_data.get_test_results()
        #self.static_widget.plot(plots, res)

class KdSliders(QWidget):
    signal = pyqtSignal(object)

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._activate = False
        self._createUI()

    def _createUI(self):
        self.layout = QVBoxLayout(self)
        self.box = QGroupBox("Параметры Kd")
        self.box_layout = QVBoxLayout()
        self.box.setLayout(self.box_layout)

        for i in range(1, 6):
            # Имя параметра
            setattr(self, f'param_name_{i}', QLabel(f'i'))
            param_name = getattr(self, f'param_name_{i}')

            # Cлайдер
            setattr(self, f'slider_{i}', Float_Slider(Qt.Horizontal))
            slider = getattr(self, f'slider_{i}')

            # Строка со значнием слайдера
            setattr(self, f'label_{i}', QLabel())
            slider_label = getattr(self, f'label_{i}')
            slider_label.setFixedWidth(40)

            # Строка для размещения
            setattr(self, f'line_{i}', QHBoxLayout())
            line = getattr(self, f'line_{i}')
            setattr(self, f'widget_line_{i}', QWidget())
            widget_line = getattr(self, f'widget_line_{i}')
            widget_line.setLayout(line)

            # Разместим слайдер и подпись на строке
            line.addWidget(param_name)
            line.addWidget(slider)
            line.addWidget(slider_label)
            self.box_layout.addWidget(widget_line)
            func = getattr(self, '_sliders_moove')
            slider.sliderMoved.connect(func)
            release = getattr(self, '_sliders_released')
            slider.sliderReleased.connect(release)
            slider.setStyleSheet(style)
            widget_line.setVisible(False)

        self.layout.addWidget(self.box)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _get_slider_params(self):
        """Получение по ключам значения со всех слайдеров"""
        return_params = []
        for i in range(1, 6):
            slider = getattr(self, f'slider_{i}')
            return_params.append(slider.current_value())
        return return_params

    def _set_slider_labels_params(self, params):
        """Установка по ключам текстовых полей значений слайдеров"""
        for i, val in enumerate(params):
            slider_label = getattr(self, f'label_{i + 1}')
            slider_label.setText(str(val))

    def _sliders_moove(self):
        """Обработка перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params()
            self._set_slider_labels_params(params)

    def _sliders_released(self):
        """Обработка окончания перемещения слайдеров деформации"""
        if self._activate:
            params = list(filter(lambda x: x != 0, self._get_slider_params()))
            self._set_slider_labels_params(params)
            statment[statment.current_test].mechanical_properties.Kd = params
            self.signal.emit(True)

    def set_sliders_params(self):
        try:

            for i in range(1, 6):
                widget_line = getattr(self, f'widget_line_{i}')
                widget_line.setVisible(False)

            frequency = statment[statment.current_test].mechanical_properties.frequency
            Kd = [res['Kd'] for res in VC_models[statment.current_test].get_test_results()]

            for Kd, frequency, i in zip(Kd, frequency, range(1, 6)):
                current_slider = getattr(self, f'slider_{i}')
                current_slider.set_borders(0.3, 1)
                current_slider.set_value(Kd)
                param_name = getattr(self, f'param_name_{i}')
                param_name.setText(str(frequency))
                widget_line = getattr(self, f'widget_line_{i}')
                widget_line.setVisible(True)

            self._activate = True

            self._sliders_moove()
        except Exception as err:
            print(err)

class PredictVCTestResults(QDialog):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self._table_is_full = False
        self.setWindowTitle("Прогнозирование Kd")
        self.create_IU()

        self.resize(1400, 800)

        self.save_button.clicked.connect(self._save_pdf)
        self.combo_box.activated.connect(lambda s: self._sort_combo_changed(statment))

        self._fill_table()

    def create_IU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.table_castomer = TableCastomer()
        self.table_castomer.set_data()
        self.layout.addWidget(self.table_castomer)

        self.l = QHBoxLayout()
        self.button_box = QGroupBox("Инструменты")
        self.button_box_layout = QHBoxLayout()
        self.button_box.setLayout(self.button_box_layout)
        self.save_button = QPushButton("Сохранить данные PDF")
        self.save_button.setFixedHeight(30)
        self.combo_box = QComboBox()
        self.combo_box.setFixedHeight(30)
        self.combo_box.addItems(["Сортировка", "sigma_3", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)
        self.l.addWidget(self.button_box)
        self.layout.addLayout(self.l)

        self.table = QTableWidget()
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

        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il", "e", "𝜎3, кПа", "qf, кПа", "t, кПа",
             "Частота, Гц", "Kd, д.е."])
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

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(statment))

        for string_number, lab_number in enumerate(statment):
            for i, val in enumerate([
                lab_number,
                str(statment[lab_number].physical_properties.depth),
                statment[lab_number].physical_properties.soil_name,
                str(statment[lab_number].physical_properties.Il) if statment[lab_number].physical_properties.Il else "-",
                str(statment[lab_number].physical_properties.e) if statment[lab_number].physical_properties.e else "-",
                str(np.round(statment[lab_number].mechanical_properties.sigma_3)),
                str(np.round(statment[lab_number].mechanical_properties.qf)),
                str(np.round(statment[lab_number].mechanical_properties.t)),
                str(statment[lab_number].mechanical_properties.frequency).strip("[").strip("]"),
                str(statment[lab_number].mechanical_properties.Kd).strip("[").strip("]")
            ]):

                self.table.setItem(string_number, i, QTableWidgetItem(val))

        self._table_is_full = True

    def _set_data(self, data):
        """Функция для получения данных"""
        self._data = data
        self._fill_table()

    def _sort_combo_changed(self, statment):
        """Изменение способа сортировки combo_box"""
        if self._table_is_full:
            if self.combo_box.currentText() == "Сортировка":
                statment.sort("origin")
                self._clear_table()
            else:
                statment.sort(self.combo_box.currentText())
                self._clear_table()

            self._fill_table()

    def get_data(self):
        for string_number, lab_number in enumerate(statment):
            try:
                statment[lab_number].mechanical_properties.Kd = [float(self.table.item(string_number, 9).text())]
            except ValueError:
                statment[lab_number].mechanical_properties.Kd = [float(x) for x in self.table.item(string_number, 9).text().split(",")]

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирование парметров виброползучести"
            titles, data, scales = PredictVCTestResults.transform_data_for_statment(statment)



            try:
                save_report(titles, data, scales, statment.general_data.end_date, ['Заказчик:', 'Объект:'],
                            [statment.general_data.customer, statment.general_data.object_name], statement_title,
                            save_dir, "---", "Прогноз Kd.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    @staticmethod
    def transform_data_for_statment(data):
        """Трансформация данных для передачи в ведомость"""
        data_structure = []

        for string_number, lab_number in enumerate(data):
                data_structure.append([
                    lab_number,
                    str(statment[lab_number].physical_properties.depth),
                    statment[lab_number].physical_properties.soil_name,
                    str(statment[lab_number].physical_properties.Il) if statment[lab_number].physical_properties.Il else "-",
                    str(statment[lab_number].physical_properties.e) if statment[lab_number].physical_properties.e else "-",
                    str(np.round(statment[lab_number].mechanical_properties.sigma_3)),
                    str(np.round(statment[lab_number].mechanical_properties.qf)),
                    str(np.round(statment[lab_number].mechanical_properties.t)),
                    str(statment[lab_number].mechanical_properties.frequency).strip("[").strip("]"),
                    str(statment[lab_number].mechanical_properties.Kd).strip("[").strip("]")
                ])

        titles = ["Лаб. ном.", "Глубина", "Наименование грунта", "Консистенция Il д.е.", "e, д.е.", "𝜎3, кПа",
                  "qf, кПа", "t, кПа", "Частота, Гц", "Kd, д.е."]

        scale = [60, 60, "*", 60, 60, 60, 60, 60, 60, 60]

        return (titles, data_structure, scale)

class VibrationCreepSoilTestApp(AppMixin, QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])
        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = VibrationCreepStatment()
        self.tab_2 = StaticSoilTestWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)
        self.tab_3 = VibrationCreepSoilTestWidget()
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_4 = Save_Dir(
            {
                "standart": "Стандардный отчет",
                "cryo": "Крио",
                "predict50": "Прогноз 50 лет",
                "predict100": "Прогноз 100 лет",
                'E50_E': "Е50 + Е",
            },

            result_table_params={
            "Kd": lambda lab: "; ".join([str(i["Kd"]) for i in VC_models[lab].get_test_results()]),
            "E50d": lambda lab: "; ".join([str(i["E50d"]) for i in VC_models[lab].get_test_results()]),
            "E50": lambda lab: "; ".join([str(i["E50"]) for i in VC_models[lab].get_test_results()]),
            },  qr={"state": True},
            result_table_condition_params={
            "Kd": lambda lab:  sorted([i["Kd"] for i in VC_models[lab].get_test_results()])[::-1] != [i["Kd"] for i in VC_models[lab].get_test_results()],
            })

        self.tab_4.popIn.connect(self.addTab)
        self.tab_4.popOut.connect(self.removeTab)

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Опыт E")
        self.tab_widget.addTab(self.tab_3, "Опыт вибро")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.statment_directory[str].connect(lambda signal: self.tab_4.update(signal))
        #self.tab_1.signal[object].connect(self.tab_2.identification.set_data)
        self.tab_1.signal[bool].connect(self._set_params)
        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_pickle.clicked.connect(self.save_pickle)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_2.signal[bool].connect(self.tab_3.set_test_params)
        self.tab_3.signal.connect(self.tab_4.result_table.update)

        self.tab_3.sliders.signal[object].connect(lambda signal: self.tab_3._refresh())

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.layuot_for_button.addWidget(self.button_predict)

        self.save_massage = True

        self.tab_4.general_statment_button.clicked.connect(self.general_statment)

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line_for_phiz.addWidget(self.physical_line_1)
        self.tab_2.line_for_phiz.addStretch(-1)
        self.physical_line_1.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.main_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3._refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)

        self.tab_4.roundFI_btn.hide()

        self.loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                             message_port=7781, parent=self)

    def _set_params(self, param):
        self.tab_2.set_params(param)
        self.tab_3.set_test_params(param)
        self.tab_3.identification.set_data()
        self.tab_2.item_identification.set_data()
        self.physical_line_1.set_data()
        self.physical_line_2.set_data()
        self.tab_3.sliders.set_sliders_params()

    def save_report(self, save_all_mode = False):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            #statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
                          #name=statment.general_parameters.test_mode + ".pickle")

            test_parameter = {'sigma_3': statment[statment.current_test].mechanical_properties.sigma_3,
                              't': statment[statment.current_test].mechanical_properties.t,
                              'frequency': statment[statment.current_test].mechanical_properties.frequency,
                              'Rezhim': 'Изотропная реконсолидация, девиаторное циклическое нагружение',
                              'Oborudovanie': "Wille Geotechnik 13-HG/020:001", 'h': "76,00", 'd': "38,00"}

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if self.tab_4.qr:
                qr = request_qr()
            else:
                qr = None

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if self.tab_4.report_type == "cryo":
                file_name = "/" + "Отчет " + file_path_name + "-ВПК" + ".pdf"
            else:
                file_name = "/" + "Отчет " + file_path_name + "-ВП" + ".pdf"

            E_models[statment.current_test].save_log_file(save + "/" + "Test.1.log")
            VC_models[statment.current_test].save_log(save)

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            res = VC_models[statment.current_test].get_test_results()

            if len(res) > 1:
                pick_vc_array, pick_c_array = [], []
                plots = VC_models[statment.current_test].get_plot_data()
                res = VC_models[statment.current_test].get_test_results()
                for i in range(len(res)):
                    actual_plots = dict(plots)
                    for key in plots:
                        actual_plots[key] = [plots[key][i]]
                    self.tab_3.dynamic_widget.plot(actual_plots, [res[i]])
                    pick_vc, pick_c = self.tab_3.dynamic_widget.save_canvas()
                    pick_vc_array.append(pick_vc)
                    pick_c_array.append(pick_c)

                self.tab_3.dynamic_widget.plot(plots, res)
                pick_vc, pick_c = self.tab_3.dynamic_widget.save_canvas()
                pick_vc_array.append(pick_vc)
                pick_c_array.append(pick_c)

                report_VibrationCreep3(save + "/" + file_name, data_customer,
                                      statment[statment.current_test].physical_properties,
                                      statment.getLaboratoryNumber(),
                                      os.getcwd() + "/project_data/",
                                      test_parameter, E_models[statment.current_test].get_test_results(),
                                      VC_models[statment.current_test].get_test_results(),
                                      [pick_vc_array, pick_c_array,
                                       *self.tab_2.deviator_loading.save_canvas(format=["jpg", "jpg"])], self.tab_4.report_type,
                                      "{:.2f}".format(__version__), qr_code=qr)

                Kd = []
                E50d = []
                E50 = []
                prediction = []
                Ed = []
                for i in range(len(res)):
                    Kd.append(zap(res[i]["Kd"], 2))
                    E50d.append(zap(res[i]["E50d"], 1))
                    Ed.append(zap(res[i]["Ed"], 1))
                    prediction.append(zap(res[i]["prediction"]["50_years"], 3))

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path, ("IH" + str(number), (number, 241)), ';'.join(E50), sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path, ("II" + str(number), (number, 242)), ';'.join(E50d), sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path, ("CB" + str(number), (number, 79)), ';'.join(Kd), sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path, ("IJ" + str(number), (number, 243)), ';'.join(Ed), sheet="Лист1", color="FF6961")

            else:
                pick_vc, pick_c = self.tab_3.dynamic_widget.save_canvas()
                report_VibrationCreep(save + "/" + file_name, data_customer,
                                      statment[statment.current_test].physical_properties,
                                      statment.getLaboratoryNumber(),
                                      os.getcwd() + "/project_data/",
                                      test_parameter, E_models[statment.current_test].get_test_results(),
                                      VC_models[statment.current_test].get_test_results(),
                                      [pick_vc, pick_c, *self.tab_2.deviator_loading.save_canvas(format=["jpg", "jpg"])],
                                      self.tab_4.report_type, statment.general_parameters.test_mode, "{:.2f}".format(__version__), qr_code=qr)
                res = res[0]

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path, ("IH" + str(number), (number, 241)), res["E50"], sheet="Лист1",
                              color="FF6961")
                set_cell_data(self.tab_1.path, ("II" + str(number), (number, 242)), res["E50d"], sheet="Лист1",
                              color="FF6961")
                set_cell_data(self.tab_1.path, ("CB" + str(number), (number, 79)), res["Kd"], sheet="Лист1",
                              color="FF6961")
                set_cell_data(self.tab_1.path, ("BU" + str(number), (number, 72)), res["E50"], sheet="Лист1",
                              color="FF6961")
                set_cell_data(self.tab_1.path, ("IJ" + str(number), (number, 243)), res["Ed"], sheet="Лист1",
                              color="FF6961")


            shutil.copy(save + "/" + file_name, statment.save_dir.report_directory + "/" + file_name)

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            control()
            return True, "Успешно"

        except AssertionError as error:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")
            return False, f'{str(error)}'

        except TypeError as error:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")

            return False, f'{str(error)}'

        except PermissionError:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", f"Закройте файл отчета {statment.current_test}", QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")
            return False, 'Не закрыт файл отчета'

        except Exception as error:

            if not save_all_mode:
                app_logger.exception(f"Не выгнан {statment.current_test}")

            return False, f'{str(error)}'

    def save_pickle(self):
        try:
            statment.save([VC_models, E_models],
                          [f"VC_models{statment.general_data.get_shipment_number()}.pickle",
                           f"E_models{statment.general_data.get_shipment_number()}.pickle"])
            VC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"VC_models{statment.general_data.get_shipment_number()}.pickle"))
            E_models.dump(os.path.join(statment.save_dir.save_directory,
                                       f"E_models{statment.general_data.get_shipment_number()}.pickle"))
            QMessageBox.about(self, "Сообщение", "Pickle успешно сохранен")
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

    def save_all_reports(self):

        if self.loader.is_running:
            QMessageBox.critical(self, "Ошибка", "Закройте окно сохранения")
            return

        try:
            statment.save([VC_models, E_models],
                          [f"VC_models{statment.general_data.get_shipment_number()}.pickle",
                           f"E_models{statment.general_data.get_shipment_number()}.pickle"])
            VC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"VC_models{statment.general_data.get_shipment_number()}.pickle"))
            E_models.dump(os.path.join(statment.save_dir.save_directory,
                                       f"E_models{statment.general_data.get_shipment_number()}.pickle"))
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        try:
            statment.save_dir.clear_dirs()
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", "Ошибка очистки папки с отчетами. Не закрыт файл отчета.")
            return

        def save():

            count = len(statment)
            Loader.send_message(self.loader.port, f"Сохранено 0 из {count}")

            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self._set_params(True)
                try:
                    is_ok, message = self.save_report(save_all_mode=True)
                    if not is_ok:
                        self.loader.close_OK(
                            f"Ошибка сохранения пробы {statment.current_test}\n{message}.\nОперация прервана.")
                        app_logger.info(f"Ошибка сохранения пробы {message}")
                        return
                except Exception as err:
                    self.loader.close_OK(f"Ошибка сохранения пробы {statment.current_test}\n{err}.\nОперация прервана.")
                    app_logger.info(f"Ошибка сохранения пробы {err}")
                    return

                Loader.send_message(self.loader.port, f"Сохранено {i + 1} из {count}")
            Loader.send_message(self.loader.port, f"Сохранено {count} из {count}")

            self.loader.close_OK(f"Объект выгнан")
            self.save_massage = True

        t = threading.Thread(target=save)
        self.loader.start()
        t.start()

        SessionWriter.write_session(len(statment))

    def _predict(self):
        if len(statment):
            dialog = PredictVCTestResults()
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                dialog.get_data()
                VC_models.generateTests()
                VC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"VC_models{statment.general_data.get_shipment_number()}.pickle"))
                E_models.dump(os.path.join(statment.save_dir.save_directory,
                                           f"E_models{statment.general_data.get_shipment_number()}.pickle"))
                app_logger.info("Новые параметры ведомости и модели сохранены")

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        test_mode_file_name = None
        if statment.general_parameters.test_mode == "Виброползучесть":
            test_mode_file_name = 'вибро'
            statement_structure_key = "vibration_creep"
        else:
            test_mode_file_name = 'сейсмо'
            statement_structure_key = "seismic_creep"

        _statment = StatementGenerator(self, path=s, statement_structure_key=statement_structure_key,
                                       test_mode_and_shipment=(test_mode_file_name,
                                                               statment.general_data.get_shipment_number()))
        _statment.show()

    def save_report_and_continue(self):
        try:
            statment.save([VC_models, E_models],
                          [f"VC_models{statment.general_data.get_shipment_number()}.pickle",
                           f"E_models{statment.general_data.get_shipment_number()}.pickle"])
            VC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"VC_models{statment.general_data.get_shipment_number()}.pickle"))
            E_models.dump(os.path.join(statment.save_dir.save_directory,
                                       f"E_models{statment.general_data.get_shipment_number()}.pickle"))
        except Exception as err:
            print(err)
        try:
            self.save_report()
        except:
            pass
        keys = [key for key in statment]
        for i, val in enumerate(keys):
            if (val == statment.current_test) and (i < len(keys) - 1):
                statment.current_test = keys[i+1]
                self._set_params(True)
                self.physical_line_1.set_data()
                self.physical_line_2.set_data()
                break
            else:
                pass

        SessionWriter.write_test()




if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    #ex = VibrationCreepSoilTestApp()
    ex = QTextEdit()
    handler.emit = lambda record: ex.append(handler.format(record))
    app_logger.info("dgf")

    ex.show()
    sys.exit(app.exec_())