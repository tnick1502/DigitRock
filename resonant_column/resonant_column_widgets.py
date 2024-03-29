from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QDialog, QHBoxLayout, \
    QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QHeaderView, QTableWidgetItem, QTabWidget, \
    QTextEdit, QProgressDialog
import os
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
import sys
import shutil
import threading

from resonant_column.resonant_column_widgets_UI import RezonantColumnUI, RezonantColumnOpenTestUI, \
    RezonantColumnSoilTestUI, RezonantColumnIdentificationUI
from excel_statment.initial_tables import LinePhysicalProperties
from resonant_column.rezonant_column_hss_model import ModelRezonantColumn, ModelRezonantColumnSoilTest
from excel_statment.initial_statment_widgets import TableCastomer
from general.report_general_statment import save_report
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from general.save_widget import Save_Dir
from general.reports import report_rc
from excel_statment.initial_statment_widgets import RezonantColumnStatment
from loggers.logger import app_logger, log_this, handler
from excel_statment.functions import set_cell_data
from singletons import RC_models, statment
from version_control.configs import actual_version
from general.movie_label import Loader

from general.tab_view import AppMixin, TabMixin
__version__ = actual_version
from general.general_statement import StatementGenerator
from authentication.request_qr import request_qr
from authentication.control import control
from metrics.session_writer import SessionWriter

class RezonantColumnProcessingWidget(TabMixin, QWidget):
    """Виджет для открытия и обработки файла прибора"""
    signal = pyqtSignal()

    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()
        self.test_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)
        self.open_widget.button_open_path.clicked.connect(self._open_path)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.line_1 = QHBoxLayout()
        self.identification_widget = RezonantColumnIdentificationUI()
        self.test_widget = RezonantColumnUI()
        self.identification_widget.setFixedHeight(180)
        self.identification_widget.setFixedWidth(300)
        self.line_1.addWidget(self.identification_widget)

        self.open_widget = RezonantColumnOpenTestUI()
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)

        self.layout.addLayout(self.line_1)
        self.layout.addWidget(self.test_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        try:
            if RC_models[statment.current_test]._test_data.G_array is not None:
                RC_models[statment.current_test].set_borders(int(self.test_widget.cut_slider.low()),
                                                             int(self.test_widget.cut_slider.high()))
                self._plot()
        except:
            pass

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_widget.cut_slider.setMinimum(0)
        self.test_widget.cut_slider.setMaximum(len)
        self.test_widget.cut_slider.setLow(0)
        self.test_widget.cut_slider.setHigh(len)

    @log_this(app_logger, "debug")
    def set_test_params(self, params):
        try:
            self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
            self._plot()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _params_slider_moove(self, params):
        try:
            RC_models[statment.current_test].set_draw_params(params)
            self.set_test_params(True)
            self.signal.emit()
        except KeyError:
            pass

    # @log_this(app_logger, "debug")
    def _refresh(self):
        pass

    def _plot(self):
        """Построение графиков опыта"""
        try:
            plots = RC_models[statment.current_test].get_plot_data()
            res = RC_models[statment.current_test].get_test_results()
            self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
            self.test_widget.plot(plots, res)
        except:
            self.test_widget.clear()

    def _open_path(self):
        """Открытие файла опыта"""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.open_widget.set_file_path("")
            try:
                RC_models[statment.current_test].open_path(path)
                self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
                self.open_widget.set_file_path(path)
            except:
                pass
            self._plot()

class RezonantColumnSoilTestWidget(TabMixin, QWidget):
    """Виджет для открытия и обработки файла прибора"""
    signal = pyqtSignal()
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()
        self.test_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)
        self.test_widget.sliders.signal[object].connect(self._params_slider_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.line_1 = QHBoxLayout()
        self.identification_widget = RezonantColumnIdentificationUI()
        self.test_widget = RezonantColumnSoilTestUI()
        self.identification_widget.setFixedHeight(180)
        self.identification_widget.setFixedWidth(300)
        self.line_1.addWidget(self.identification_widget)
        self.layout.addLayout(self.line_1)
        self.layout.addWidget(self.test_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        try:
            if RC_models[statment.current_test]._test_data.G_array is not None:
                RC_models[statment.current_test].set_borders(int(self.test_widget.cut_slider.low()),
                                                            int(self.test_widget.cut_slider.high()))
                self._plot()
        except KeyError:
            pass

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_widget.cut_slider.setMinimum(0)
        self.test_widget.cut_slider.setMaximum(len)
        self.test_widget.cut_slider.setLow(0)
        self.test_widget.cut_slider.setHigh(len)

    def set_test_params(self, params):
        try:
            self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
            self._plot()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _params_slider_moove(self, params):
        try:
            RC_models[statment.current_test].set_draw_params(params)
            self.set_test_params(True)
            self.signal.emit()
        except KeyError:
            pass

    #@log_this(app_logger, "debug")
    def _refresh(self):
        try:
            RC_models[statment.current_test].set_test_params()
            self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    def _plot(self):
        """Построение графиков опыта"""
        try:
            plots = RC_models[statment.current_test].get_plot_data()
            res = RC_models[statment.current_test].get_test_results()
            self.test_widget.plot(plots, res)
        except KeyError:
            pass

class PredictRCTestResults(QDialog):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self._table_is_full = False
        self.setWindowTitle("Резонансная колонка")
        self.create_IU()

        self._G0_ratio = 1
        self._threshold_shear_strain_ratio = 1

        self._original_keys_for_sort = list(statment.tests.keys())
        self.resize(1400, 800)

        self.sliders.signal[object].connect(self._sliders_moove)


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
        self.combo_box.addItems(["Сортировка", "reference_pressure", "depth"])
        self.button_box_layout.addWidget(self.combo_box)
        self.button_box_layout.addWidget(self.save_button)

        self.l.addStretch(-1)
        self.sliders = TriaxialStaticLoading_Sliders({
            "G0_ratio": "Коэффициент G0",
            "threshold_shear_strain_ratio": "Коэффициент жесткости"})
        self.sliders.set_sliders_params(
            {
                "G0_ratio": {"value": 1, "borders": [0.1, 5]},
                "threshold_shear_strain_ratio": {"value": 1, "borders": [0.1, 5]}
            })

        self.l.addWidget(self.sliders)

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

        self.table.setColumnCount(8)
        #self.table.horizontalHeader().resizeSection(1, 200)
        self.table.setHorizontalHeaderLabels(
            ["Лаб. ном.", "Глубина", "Наименование грунта", "Реф.давление, МПа", "Коэфф. пористости e", "Е50, МПа", "G0, МПА",
             "𝛾07, д.е."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        self.table.horizontalHeader().setMinimumSectionSize(150)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)

    def _fill_table(self):
        """Заполнение таблицы параметрами"""
        self.table.setRowCount(len(statment))
        for string_number, lab_number in enumerate(statment):
            for i, val in enumerate([
                statment[lab_number].physical_properties.laboratory_number,
                str(statment[lab_number].physical_properties.depth),
                statment[lab_number].physical_properties.soil_name,
                str(statment[lab_number].mechanical_properties.reference_pressure),
                str(statment[lab_number].physical_properties.e),
                str(np.round(statment[lab_number].mechanical_properties.E50, 1)),
                str(np.round(statment[lab_number].mechanical_properties.G0 * self._G0_ratio, 1)),
                str(np.round(statment[lab_number].mechanical_properties.threshold_shear_strain *self._threshold_shear_strain_ratio, 2))
            ]):

                self.table.setItem(string_number, i, QTableWidgetItem(val))

        self._table_is_full = True

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

    def _sliders_moove(self, param):
        self._G0_ratio = param["G0_ratio"]
        self._threshold_shear_strain_ratio = param["threshold_shear_strain_ratio"]
        self._fill_table()

    def _save_pdf(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_dir:
            statement_title = "Прогнозирование парметров G0"
            titles, data, scales = PredictRCTestResults.transform_data_for_statment(self.get_data())
            try:
                save_report(titles, data, scales, statment.general_data.end_date, ['Заказчик:', 'Объект:'],
                            [statment.general_data.customer, statment.general_data.object_name], statement_title,
                            save_dir, "---", "Прогноз G0.pdf")
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
            except PermissionError:
                QMessageBox.critical(self, "Ошибка", "Закройте ведомость", QMessageBox.Ok)

    def get_data(self):
        for string_number, lab_number in enumerate(statment):
            statment[lab_number].mechanical_properties.G0 = float(self.table.item(string_number, 6).text())
            statment[lab_number].mechanical_properties.threshold_shear_strain = float(self.table.item(string_number, 7).text())

    @staticmethod
    def transform_data_for_statment(data):
        """Трансформация данных для передачи в ведомость"""
        data_structure = []

        for string_number, lab_number in enumerate(statment):
                data_structure.append([
                    lab_number,
                    str(statment[lab_number].physical_properties.depth),
                    statment[lab_number].physical_properties.soil_name,
                    str(statment[lab_number].mechanical_properties.reference_pressure),
                    str(statment[lab_number].physical_properties.e),
                    str(np.round(statment[lab_number].mechanical_properties.E50, 1)),
                    str(np.round(statment[lab_number].mechanical_properties.G0, 1)),
                    str(np.round(statment[lab_number].mechanical_properties.threshold_shear_strain, 2))])

        titles = ["Лаб. номер", "Глубина, м", "Наименование грунта", "Реф.давление, МПа", "Коэфф. пористости e",
                  "Е50, МПа", "G0, МПА", "𝛾07, д.е."]

        scale = [70, 70, "*", 70, 70, 70, 70, 70]

        return (titles, data_structure, scale)

class RezonantColumnProcessingApp(AppMixin, QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)
        self.save_massage = True

        self.tab_widget = QTabWidget()
        self.tab_1 = RezonantColumnStatment(generate=False)
        self.tab_2 = RezonantColumnProcessingWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)

        self.tab_3 = Save_Dir(result_table_params={
            "G0": lambda lab: RC_models[lab].get_test_results()['G0'],
            "gam_07": lambda lab: RC_models[lab].get_test_results()["threshold_shear_strain"],
        }, qr=True)
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.tab_widget.addTab(self.tab_3, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.statment_directory[str].connect(lambda x:
                                                   self.tab_3.update(x))
        self.physical_line = LinePhysicalProperties()

        self.tab_1.signal[bool].connect(lambda x: self.tab_2._plot())
        self.tab_1.signal[bool].connect(lambda x: self.physical_line.set_data())

        self.tab_1.signal[bool].connect(self.tab_2.identification_widget.set_data)
        self.tab_3.save_button.clicked.connect(self.save_report)
        self.tab_3.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_2.signal.connect(self.tab_3.update)

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.layuot_for_button.addWidget(self.button_predict)

        self.tab_3.general_statment_button.clicked.connect(self.general_statment)

        self.tab_2.line_1.addWidget(self.physical_line)
        self.physical_line.refresh_button.clicked.connect(self.tab_2._refresh)
        self.physical_line.save_button.clicked.connect(self.save_report_and_continue)

    def _predict(self):
        if len(statment):
            dialog = PredictRCTestResults()
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                dialog.get_data()
                RC_models.generateTests()
                RC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"rc_models{statment.general_data.get_shipment_number()}.pickle"))
                # statment.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]),
                # name="Резонансная колонка.pickle")
                app_logger.info("Новые параметры ведомости и модели сохранены")

    # @log_this(app_logger, "debug")
    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            file_name = save + "/" + "Отчет " + file_path_name + "-РК" + ".pdf"

            test_result = RC_models[statment.current_test].get_test_results()

            results = {"G0": test_result["G0"], "gam07": test_result["threshold_shear_strain"]}

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            if self.tab_3.qr:
                qr = request_qr()
            else:
                qr = None

            report_rc(file_name, data_customer,
                      statment[statment.current_test].physical_properties,
                      statment.getLaboratoryNumber(),
                      os.getcwd() + "/project_data/", statment[statment.current_test].mechanical_properties, results,
                      self.tab_2.test_widget.save_canvas(), __version__, qr_code=qr)

            number = statment[statment.current_test].physical_properties.sample_number + 7

            set_cell_data(self.tab_1.path, ("HL" + str(number), (number, 219)), test_result["G0"], sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HK" + str(number), (number, 218)), test_result["threshold_shear_strain"],
                          sheet="Лист1")

            shutil.copy(file_name, statment.save_dir.report_directory + "/" + file_name[len(file_name) -
                                                                                        file_name[::-1].index("/"):])
            RC_models[statment.current_test].save_log_file(save)
            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

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
                self.tab_2.set_test_params(True)
                self.save_report()
                progress.setValue(i)
            progress.setValue(len(statment))
            progress.close()
            QMessageBox.about(self, "Сообщение", "Объект выгнан")
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
                statment.current_test = keys[i + 1]
                self.tab_2.set_test_params(True)
                self.physical_line.set_data()
                break
            else:
                pass

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None


        _statment = StatementGenerator(self, path=s, statement_structure_key="Resonance column",
                                       test_mode_and_shipment=(test_mode_file_name,
                                                               statment.general_data.get_shipment_number()))
        _statment.show()

class RezonantColumnSoilTestApp(AppMixin, QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)
        self.save_massage = True

        self.tab_widget = QTabWidget()
        self.tab_1 = RezonantColumnStatment()
        self.tab_2 = RezonantColumnSoilTestWidget()
        self.tab_2.popIn.connect(self.addTab)
        self.tab_2.popOut.connect(self.removeTab)

        self.loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                             message_port=7786, parent=self)

        def G0_repeat(lab):
            G0 = int(RC_models[lab].get_test_results()["G0"])
            G0_list = [int(RC_models[i].get_test_results()["G0"]) for i in statment]
            G0_list.pop(G0_list.index(G0))

            return G0 in G0_list


        self.tab_3 = Save_Dir({
                "G0": "G0",
                "G0E0": "G0 + E0"},
        result_table_params={
            "G0": lambda lab: RC_models[lab].get_test_results()['G0'],
            "gam_07": lambda lab: RC_models[lab].get_test_results()["threshold_shear_strain"],
        }, qr={"state": True},
            result_table_condition_params={
                "G0_repeat": lambda lab: G0_repeat(lab)
            }
        )
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.tab_widget.addTab(self.tab_3, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.statment_directory[str].connect(lambda x:
                                                   self.tab_3.update(x))
        self.physical_line = LinePhysicalProperties()

        self.tab_1.signal[bool].connect(self.tab_2.set_test_params)
        self.tab_1.signal[bool].connect(lambda x: self.physical_line.set_data())

        self.tab_1.signal[bool].connect(self.tab_2.identification_widget.set_data)
        self.tab_3.save_button.clicked.connect(self.save_report)
        self.tab_3.save_pickle.clicked.connect(self.save_pickle)
        self.tab_3.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_2.signal.connect(self.tab_3.result_table.update)

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.layuot_for_button.addWidget(self.button_predict)

        self.tab_3.general_statment_button.clicked.connect(self.general_statment)

        self.tab_2.line_1.addWidget(self.physical_line)
        self.physical_line.refresh_button.clicked.connect(self.tab_2._refresh)
        self.physical_line.save_button.clicked.connect(self.save_report_and_continue)

        self.tab_3.roundFI_btn.hide()

    def _predict(self):
        if len(statment):
            dialog = PredictRCTestResults()
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                dialog.get_data()
                RC_models.generateTests()
                RC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"rc_models{statment.general_data.get_shipment_number()}.pickle"))
                #statment.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]),
                              #name="Резонансная колонка.pickle")
                app_logger.info("Новые параметры ведомости и модели сохранены")

    #@log_this(app_logger, "debug")
    def save_report(self, save_all_mode = False):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            file_name = save + "/" + "Отчет " + file_path_name + "-РК" + ".pdf"

            test_result = RC_models[statment.current_test].get_test_results()

            results = {
                "G0": test_result["G0"],
                "gam07": test_result["threshold_shear_strain"],
                "E0": test_result["E0"],
            }

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            if self.tab_3.qr:
                qr = request_qr()
            else:
                qr = None
            try:
                report_rc(file_name, data_customer,
                          statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(),
                          os.getcwd() + "/project_data/", statment[statment.current_test].mechanical_properties, results,
                          self.tab_2.test_widget.save_canvas(), self.tab_3.report_type, __version__, qr_code=qr)
            except Exception as err:
                print(err)

            number = statment[statment.current_test].physical_properties.sample_number + 7

            set_cell_data(self.tab_1.path, ("HL" + str(number), (number, 219)), test_result["G0"], sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HJ" + str(number), (number, 217)), test_result["E0"], sheet="Лист1")
            set_cell_data(self.tab_1.path, ("HK" + str(number), (number, 218)), test_result["threshold_shear_strain"], sheet="Лист1")

            shutil.copy(file_name, statment.save_dir.report_directory + "/" + file_name[len(file_name) -
                                                                                      file_name[::-1].index("/"):])
            RC_models[statment.current_test].save_log_file(save)
            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
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

        except PermissionError:
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", f"Закройте файл отчета {statment.current_test}", QMessageBox.Ok)
                app_logger.exception(f"Не выгнан {statment.current_test}")
            return False, 'Не закрыт файл отчета'

    def save_pickle(self):
        try:
            statment.save([RC_models], [f"rc_models{statment.general_data.get_shipment_number()}.pickle"])
            RC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"rc_models{statment.general_data.get_shipment_number()}.pickle"))
            QMessageBox.about(self, "Сообщение", "Pickle успешно сохранен")
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

    def save_all_reports(self):

        if self.loader.is_running:
            QMessageBox.critical(self, "Ошибка", "Закройте окно сохранения")
            return

        try:
            statment.save([RC_models], [f"rc_models{statment.general_data.get_shipment_number()}.pickle"])
        except Exception as err:
            QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        RC_models.dump(os.path.join(statment.save_dir.save_directory,
                                    f"rc_models{statment.general_data.get_shipment_number()}.pickle"))

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
                self.tab_2.set_test_params(True)
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

    def save_report_and_continue(self):
        try:
            statment.save([RC_models], [f"rc_models{statment.general_data.get_shipment_number()}.pickle"])
            RC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"rc_models{statment.general_data.get_shipment_number()}.pickle"))
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
                self.tab_2.set_test_params(True)
                self.physical_line.set_data()
                break
            else:
                pass
        SessionWriter.write_test()

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        test_mode_file_name = "G0"

        _statment = StatementGenerator(self, path=s, statement_structure_key="Resonance column",
                                       test_mode_and_shipment=(test_mode_file_name,
                                                               statment.general_data.get_shipment_number()))
        _statment.show()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = RezonantColumnSoilTestApp()
    ex.show()
    sys.exit(app.exec_())