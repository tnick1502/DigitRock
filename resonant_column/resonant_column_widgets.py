from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QDialog, QHBoxLayout, \
    QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QHeaderView, QTableWidgetItem, QTabWidget, \
    QTextEdit, QProgressDialog
import os
from PyQt5.QtCore import Qt
import numpy as np
import sys
import shutil
import threading

from resonant_column.resonant_column_widgets_UI import RezonantColumnUI, RezonantColumnOpenTestUI, \
    RezonantColumnSoilTestUI, RezonantColumnIdentificationUI
from resonant_column.rezonant_column_hss_model import ModelRezonantColumn, ModelRezonantColumnSoilTest
from excel_statment.initial_statment_widgets import TableCastomer
from general.report_general_statment import save_report
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from general.save_widget import Save_Dir
from general.reports import report_rc
from excel_statment.initial_statment_widgets import RezonantColumnStatment
from loggers.logger import app_logger, log_this, handler
from general.excel_functions import set_cell_data
from singletons import RC_models, statment
from version_control.configs import actual_version
__version__ = actual_version

class RezonantColumnProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelRezonantColumn()
        self._create_Ui()
        #self.open_widget.button_open_file.clicked.connect(self._open_file)
        self.open_widget.button_open_path.clicked.connect(self._open_path)
        self.test_processing_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.identification_widget = RezonantColumnIdentificationUI()
        self.open_widget = RezonantColumnOpenTestUI()
        self.layout.addWidget(self.identification_widget)
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)
        self.test_processing_widget = RezonantColumnUI()
        self.layout.addWidget(self.test_processing_widget)
        self.save_widget = Save_Dir()
        self.layout.addWidget(self.save_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        if self._model._test_data.G_array is not None:
            self._model.set_borders(int(self.test_processing_widget.cut_slider.low()),
                                                        int(self.test_processing_widget.cut_slider.high()))
            self._plot()

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_processing_widget.cut_slider.setMinimum(0)
        self.test_processing_widget.cut_slider.setMaximum(len)
        self.test_processing_widget.cut_slider.setLow(0)
        self.test_processing_widget.cut_slider.setHigh(len)

    def _open_path(self):
        """Открытие файла опыта"""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.open_widget.set_file_path("")
            self._plot()
            try:
                self._model.open_path(path)
                self._cut_slider_set_len(len(self._model._test_data.G_array))
                self.open_widget.set_file_path(path)
            except (ValueError, IndexError, FileNotFoundError):
                pass
            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_processing_widget.plot(plots, res)

class RezonantColumnSoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()
        self.test_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)
        self.test_widget.sliders.signal[object].connect(self._params_slider_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.identification_widget = RezonantColumnIdentificationUI()
        self.test_widget = RezonantColumnSoilTestUI()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self._refresh)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.identification_widget)
        self.layout.addWidget(self.test_widget)
        self.save_widget = Save_Dir()
        self.layout.addWidget(self.save_widget)
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
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _refresh(self):
        try:
            RC_models[statment.current_test].set_test_params()
            self._cut_slider_set_len(len(RC_models[statment.current_test]._test_data.G_array))
            self._plot()
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

class RezonantColumnProcessingApp(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = RezonantColumnStatment()
        self.tab_2 = RezonantColumnProcessingWidget()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self._set_save_directory)
        self.tab_1.signal[bool].connect(self.tab_2.identification_widget.set_params)
        self.tab_2.save_widget .save_button.clicked.connect(self.save_report)

    def _set_save_directory(self, signal):
        self.tab_2.save_widget.set_directory(signal, "Резонансная колонка")

    def _set_save_directory(self, signal):
        self.tab_4.save.set_directory(signal, "Резонансная колонка")

    def save_report(self):
        try:
            assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
            len(self.tab_2.test._model._test_data.G_array)
            # assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            file_path_name = self.tab_1.get_lab_number().replace("/", "-").replace("*", "")

            save = self.tab_2.save.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            file_name = save + "/" + "Отчет " + file_path_name + "-РК" + ".pdf"

            """if test_parameter['equipment'] == "Прибор: Геотек":
                test_time = geoteck_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["sigma3"], self.Data["frequency"], self.Data["Points"], self.file.Data_phiz[self.file.Lab]["Ip"])

            elif test_parameter['equipment'] == "Прибор: Вилли":
                test_time = willie_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["frequency"], self.Data["N"], self.Data["Points"],
                                 self.Setpoint, self.Arrays["cell_press"], self.file.Data_phiz[self.file.Lab]["Ip"])"""
            test_param = self.tab_1.get_data()
            test_parameter = {"reference_pressure": test_param.reference_pressure}

            test_result = self.tab_2.test._model.get_test_results()

            results = {"G0": test_result["G0"], "gam07": test_result["threshold_shear_strain"]}

            report_rc(file_name, self.tab_1.get_customer_data(),
                      self.tab_1.get_physical_data(),
                      self.tab_1.get_lab_number(),
                      os.getcwd() + "/project_data/", test_parameter, results,
                      self.tab_2.test.test_processing_widget.save_canvas(), __version__)

            shutil.copy(file_name, self.tab_2.save.report_directory + "/" + file_name[len(file_name) -
                                                                                      file_name[::-1].index("/"):])
            QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")

            set_cell_data(self.tab_1.path,
                          "HL" + str(self.tab_1.get_physical_data()[self.tab_1.get_lab_number()]["Nop"]),
                          test_result["G0"], sheet="Лист1")
            set_cell_data(self.tab_1.path,
                          "HK" + str(self.tab_1.get_physical_data()[self.tab_1.get_lab_number()]["Nop"]),
                          test_result["threshold_shear_strain"], sheet="Лист1")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(self.tab_1.get_lab_number()))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError:
            QMessageBox.critical(self, "Ошибка", "Не загружен файл опыта", QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

class RezonantColumnSoilTestApp(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QHBoxLayout(self)
        self.save_massage = True

        self.tab_widget = QTabWidget()
        self.tab_1 = RezonantColumnStatment()
        self.tab_2 = RezonantColumnSoilTestWidget()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.statment_directory[str].connect(lambda x:
                                                   self.tab_2.save_widget.set_directory(x, "Резонансная колонка"))
        self.tab_1.signal[bool].connect(self.tab_2.set_test_params)
        self.tab_1.signal[bool].connect(self.tab_2.identification_widget.set_params)
        self.tab_2.save_widget.save_button.clicked.connect(self.save_report)
        self.tab_2.save_widget.save_all_button.clicked.connect(self.save_all_reports)

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.splitter_table_vertical.addWidget(self.button_predict)

    def _predict(self):
        if len(statment):
            dialog = PredictRCTestResults()
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                dialog.get_data()
                RC_models.generateTests()
                RC_models.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]), name="rc_models.pickle")
                statment.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]),
                              name="Резонансная колонка.pickle")
                app_logger.info("Новые параметры ведомости и модели сохранены")

    @log_this(app_logger, "debug")
    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.current_test.replace("/", "-").replace("*", "")

            save = self.tab_2.save_widget.arhive_directory + "/" + file_path_name
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

            report_rc(file_name, data_customer,
                      statment[statment.current_test].physical_properties,
                      statment.getLaboratoryNumber(),
                      os.getcwd() + "/project_data/", statment[statment.current_test].mechanical_properties, results,
                      self.tab_2.test_widget.save_canvas(), __version__)

            number = statment[statment.current_test].physical_properties.sample_number + 7
            set_cell_data(self.tab_1.path, "HL" + str(number), test_result["G0"], sheet="Лист1")
            set_cell_data(self.tab_1.path, "HK" + str(number), test_result["threshold_shear_strain"], sheet="Лист1")

            shutil.copy(file_name, self.tab_2.save_widget.report_directory + "/" + file_name[len(file_name) -
                                                                                      file_name[::-1].index("/"):])
            RC_models[statment.current_test].save_log_file(save)
            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            RC_models.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]), name="rc_models.pickle")
            statment.dump(''.join(os.path.split(self.tab_2.save_widget.directory)[:-1]),
                          name="Резонансная колонка.pickle")

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

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



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = RezonantColumnSoilTestApp()
    ex.show()
    sys.exit(app.exec_())