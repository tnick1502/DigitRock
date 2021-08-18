"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
__version__ = 1

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QTabWidget, QDialog
from PyQt5.QtCore import pyqtSignal
import os
import sys
import shutil

from general.save_widget import Save_Dir
from resonant_column.resonant_column_widgets import RezonantColumnProcessingWidget, RezonantColumnSoilTestWidget
from general.general_widgets import Statment_Rezonant_Column
from general.reports import report_rc
from general.excel_functions import set_cell_data
from resonant_column.resonant_column_widgets import PredictRCTestResults

class RezonantColumn_Processing_Tab(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.test = RezonantColumnProcessingWidget()
        self.save = Save_Dir("G0")

        self.layout.addWidget(self.test)
        self.layout.addWidget(self.save)

        self.layout.setContentsMargins(5, 5, 5, 5)

class DigitRock_RezonantColumn_Processing(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = Statment_Rezonant_Column()
        self.tab_2 = RezonantColumn_Processing_Tab()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self.tab_2.save.get_save_directory)
        self.tab_1.signal[object].connect(self.tab_2.test.identification_widget.set_params)
        self.tab_2.save.save_button.clicked.connect(self.save_report)

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
            test_param = self.tab_1.get_test_data()
            test_parameter = {"Pref": test_param[self.tab_1.get_lab_number()]["Pref"]}

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


class RezonantColumn_SoilTest_Tab(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.test = RezonantColumnSoilTestWidget()
        self.save = Save_Dir("G0")

        self.layout.addWidget(self.test)
        self.layout.addWidget(self.save)

        self.layout.setContentsMargins(5, 5, 5, 5)

class DigitRock_RezonantColumn_SoilTest(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = Statment_Rezonant_Column()
        self.tab_2 = RezonantColumn_SoilTest_Tab()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self.tab_2.save.get_save_directory)
        self.tab_1.signal[object].connect(self.tab_2.test.set_test_params)
        self.tab_1.signal[object].connect(self.tab_2.test.identification_widget.set_params)
        self.tab_2.save.save_button.clicked.connect(self.save_report)
        self.tab_2.test.test_widget.sliders.signal[object].connect(self._params_slider_moove)

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.splitter_table_vertical.addWidget(self.button_predict)

    def _predict(self):
        if self.tab_1._data_test is not None:
            dialog = PredictRCTestResults(self.tab_1._data_test, self.tab_1.get_customer_data())
            dialog.show()

            if dialog.exec() == QDialog.Accepted:
                self.tab_1._data_test = dialog.get_data()

    def _params_slider_moove(self, params):
        self.tab_2.test._model.set_draw_params(params)
        self.tab_2.test._plot()

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
            test_param = self.tab_1.get_test_data()
            test_parameter = {"Pref": test_param[self.tab_1.get_lab_number()]["Pref"]}

            test_result = self.tab_2.test._model.get_test_results()

            results = {"G0": test_result["G0"], "gam07": test_result["threshold_shear_strain"]}

            report_rc(file_name, self.tab_1.get_customer_data(),
                      self.tab_1.get_physical_data(),
                      self.tab_1.get_lab_number(),
                      os.getcwd() + "/project_data/", test_parameter, results,
                      self.tab_2.test.test_widget.save_canvas(), __version__)

            set_cell_data(self.tab_1.path,
                          "HL" + str(self.tab_1.get_physical_data()[self.tab_1.get_lab_number()]["Nop"]),
                          test_result["G0"], sheet="Лист1")
            set_cell_data(self.tab_1.path,
                          "HK" + str(self.tab_1.get_physical_data()[self.tab_1.get_lab_number()]["Nop"]),
                          test_result["threshold_shear_strain"], sheet="Лист1")

            shutil.copy(file_name, self.tab_2.save.report_directory + "/" + file_name[len(file_name) -
                                                                                      file_name[::-1].index("/"):])
            self.tab_2.test._model.save_log_file(save)
            QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(self.tab_1.get_lab_number()))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError:
            QMessageBox.critical(self, "Ошибка", "Не загружен файл опыта", QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)




if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = DigitRock_RezonantColumn_Processing()
    ex.show()
    sys.exit(app.exec_())
