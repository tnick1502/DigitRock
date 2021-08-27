__version__ = "1.0.0"

from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QMessageBox, QFileDialog
from PyQt5.QtCore import pyqtSignal
import os
import sys
import shutil


from static_loading.triaxial_static_test_widgets import TriaxialStaticWidget, TriaxialStaticWidgetSoilTest
from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from general.general_widgets import TriaxialStaticStatment
from general.reports import report_consolidation, report_FCE, report_FC
from general.save_widget import Save_Dir
from general.excel_functions import set_cell_data
from general.test import get_reprocessing
#from test import LoadingWindow


class DigitRock_TriaxialStatick(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()

        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = TriaxialStaticStatment()
        self.tab_2 = TriaxialStaticWidget()
        self.tab_3 = MohrWidget()
        self.tab_4 = Save_Dir("Девиаторное нагружение")
        #self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Е")
        self.tab_widget.addTab(self.tab_3, "Опыт FC")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.signal[object].connect(self.tab_2.item_identification.set_data)
        self.tab_1.signal[object].connect(self.tab_3.item_identification.set_data)
        #self.Tab_1.signal[object].connect(self.report_params)
        #self.Tab_1.signal[object].connect(self.Tab_4.get_data)
        #self.Tab_1.signal[object].connect(self.Tab_3.get_data)
        self.tab_1.statment_directory[str].connect(self.tab_4.get_save_directory)
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

            save = self.tab_4.arhive_directory + "/" + self.tab_1.get_lab_number()
            save = save.replace("*", "")
            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if read_parameters["test_type"] == "Трёхосное сжатие (E)":
                assert self.tab_2._model.deviator_loading._test_params.sigma_3, "Не загружен файл опыта"
                #Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-ДН" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " +\
                       self.tab_1.get_customer_data()["object_number"] + " ТС Р" + ".pdf"

                report_consolidation(save + "/" + Name, self.tab_1.get_customer_data(),
                                 self.tab_1.get_physical_data(), self.tab_1.get_lab_number(),
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 (*self.tab_2.consolidation.save_canvas(),
                                  *self.tab_2.deviator_loading.save_canvas()), 1.1)
            elif read_parameters["test_type"] == "Трёхосное сжатие (F, C, E)":
                assert self.tab_3._model._test_result.fi, "Не загружен файл опыта"
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = self.tab_3._model.get_sigma_3_1()
                test_result["c"], test_result["fi"] = self.tab_3._model.get_test_results()["c"], self.tab_3._model.get_test_results()["fi"]
                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-КМ" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") +\
                       " " + self.tab_1.get_customer_data()["object_number"] + " ТД" + ".pdf"

                report_FCE(save + "/" + Name, self.tab_1.get_customer_data(), self.tab_1.get_physical_data(),
                           self.tab_1.get_lab_number(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                           (*self.tab_2.deviator_loading.save_canvas(),
                            *self.tab_3.save_canvas()), 1.1)

            shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)
            QMessageBox.about(self, "Сообщение", "Успешно сохранено")

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

class DigitRock_TriaxialStatickSoilTest(QWidget):

    def __init__(self):
        super(QWidget, self).__init__()

        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = TriaxialStaticStatment()
        self.tab_2 = TriaxialStaticWidgetSoilTest()
        self.tab_3 = MohrWidgetSoilTest()
        self.tab_4 = Save_Dir("Девиаторное нагружение")
        # self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт Е")
        self.tab_widget.addTab(self.tab_3, "Опыт FC")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.signal[object].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(self.tab_4.get_save_directory)
        #self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_button.clicked.connect(self.save_report)
        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

    def set_test_parameters(self, params):
        param = self.tab_1.open_line.get_data()
        if param["test_type"] == 'Трёхосное сжатие (F, C, E)':
            self.tab_2.item_identification.set_data(params)
            self.tab_3.item_identification.set_data(params)
            self.tab_2.set_params(params)
            self.tab_3.set_params(params)
        elif param["test_type"] == 'Трёхосное сжатие (F, C)':
            self.tab_3.item_identification.set_data(params)
            self.tab_3.set_params(params)
        elif param["test_type"] == 'Трёхосное сжатие (E)':
            self.tab_2.item_identification.set_data(params)
            self.tab_2.set_params(params)
        elif param["test_type"] == "Трёхосное сжатие с разгрузкой":
            self.tab_2.item_identification.set_data(params)
            self.tab_2.set_params(params)

    def save_report(self):

        try:
            assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
            #assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            read_parameters = self.tab_1.open_line.get_data()

            test_parameter = {"equipment": read_parameters["equipment"],
                              "mode": "КД, девиаторное нагружение в кинематическом режиме",
                              "sigma_3": self.tab_2._model.deviator_loading._test_params.sigma_3,
                              "K0": self.tab_2._model.consolidation._test_params.K0,
                              "h": 76,
                              "d": 38}

            test_result = self.tab_2.get_test_results()

            save = self.tab_4.arhive_directory + "/" + self.tab_1.get_lab_number()
            save = save.replace("*", "")
            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if read_parameters["test_type"] == "Трёхосное сжатие (E)":
                assert self.tab_2._model.deviator_loading._test_params.sigma_3, "Не загружен файл опыта"
                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-ДН" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " +\
                       self.tab_1.get_customer_data()["object_number"] + " ТС Р" + ".pdf"
                self.tab_2._model.save_log_file(save + "/" + "Test.1.log")

                report_consolidation(save + "/" + Name, self.tab_1.get_customer_data(),
                                 self.tab_1.get_physical_data(), self.tab_1.get_lab_number(),
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 (*self.tab_2.consolidation.save_canvas(),
                                  *self.tab_2.deviator_loading.save_canvas()), 1.1)

                shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)

                set_cell_data(self.tab_1.path,
                              "BK" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["E50"], sheet="Лист1", color="FF6961")

            elif read_parameters["test_type"] == "Трёхосное сжатие с разгрузкой":
                assert self.tab_2._model.deviator_loading._test_params.sigma_3, "Не загружен файл опыта"
                # Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-Р" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " +\
                       self.tab_1.get_customer_data()["object_number"] + " ТС Р" + ".pdf"
                self.tab_2._model.save_log_file(save + "/" + "Test.1.log")

                report_consolidation(save + "/" + Name, self.tab_1.get_customer_data(),
                                 self.tab_1.get_physical_data(), self.tab_1.get_lab_number(),
                                 os.getcwd() + "/project_data/",
                                 test_parameter, test_result,
                                 (*self.tab_2.consolidation.save_canvas(),
                                  *self.tab_2.deviator_loading.save_canvas(size=[[6, 4], [6, 2]])), 1.1)

                shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)

                set_cell_data(self.tab_1.path,
                              'GI' + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["Eur"], sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path,
                              "BN" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["E50"], sheet="Лист1", color="FF6961")

            elif read_parameters["test_type"] == "Трёхосное сжатие (F, C, E)":
                assert self.tab_3._model._test_result.fi, "Не загружен файл опыта"

                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = self.tab_3._model.get_sigma_3_1()
                test_result["c"], test_result["fi"] = self.tab_3._model.get_test_results()["c"], self.tab_3._model.get_test_results()["fi"]
                #Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-КМ" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") +\
                       " " + self.tab_1.get_customer_data()["object_number"] + " ТД" + ".pdf"
                self.tab_2._model.save_log_file(save + "/" + "Test.1.log")
                self.tab_3._model.save_log_files(save)

                report_FCE(save + "/" + Name, self.tab_1.get_customer_data(), self.tab_1.get_physical_data(),
                           self.tab_1.get_lab_number(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                           (*self.tab_2.deviator_loading.save_canvas(),
                            *self.tab_3.save_canvas()), 1.1)

                shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)

                set_cell_data(self.tab_1.path,
                              "BE" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["E50"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              "BC" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              "BD" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["fi"], sheet="Лист1", color="FF6961")

            elif read_parameters["test_type"] == 'Трёхосное сжатие (F, C)':
                assert self.tab_3._model._test_result.fi, "Не загружен файл опыта"
                test_parameter["K0"] = self.tab_3._model._test_params['K0']
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = self.tab_3._model.get_sigma_3_1()
                test_result["c"], test_result["fi"] = self.tab_3._model.get_test_results()["c"], self.tab_3._model.get_test_results()["fi"]
                #Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-КМ" + ".pdf"
                Name = self.tab_1.get_lab_number().replace("*", "") + " " +\
                       self.tab_1.get_customer_data()["object_number"] + " ТД" + ".pdf"
                # self.tab_2._model.save_log_file(save + "/" + "Test.1.log")
                self.tab_3._model.save_log_files(save)

                report_FC(save + "/" + Name, self.tab_1.get_customer_data(), self.tab_1.get_physical_data(),
                           self.tab_1.get_lab_number(), os.getcwd() + "/project_data/",
                           test_parameter, test_result,
                          (*self.tab_3.save_canvas(),
                           *self.tab_3.save_canvas()), 1.1)

                shutil.copy(save + "/" + Name, self.tab_4.report_directory + "/" + Name)

                set_cell_data(self.tab_1.path,
                              "BG" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["fi"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              "BF" + str(self.tab_1.get_physical_data().sample_number + 7),
                              test_result["c"], sheet="Лист1", color="FF6961")

            QMessageBox.about(self, "Сообщение", "Успешно сохранено")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(self.tab_1.get_lab_number()))


        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        #except TypeError as error:
            #QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)

    def reprocessing(self):
        dir = QFileDialog.getExistingDirectory(self, "Выберите папку с архивом")
        if dir:
              tests = get_reprocessing(dir)
              print(tests)
              self.tab_2._open_file(tests['10-2']["E"])

