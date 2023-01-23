from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, \
    QLineEdit, QPushButton, QScrollArea, QRadioButton, QButtonGroup, QFileDialog, QTabWidget, QTextEdit, QGridLayout, \
    QStyledItemDelegate, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox, QProgressDialog
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from PyQt5.QtGui import QPalette, QBrush
import matplotlib.pyplot as plt
import shutil
import threading
from general.reports import report_vibration_strangth
from excel_statment.initial_tables import LinePhysicalProperties

from general.general_functions import create_path
from static_loading.mohr_circles_wiggets import MohrWidget, MohrWidgetSoilTest
from excel_statment.initial_statment_widgets import VibrationStrangthStatment
from general.save_widget import Save_Dir
from excel_statment.functions import set_cell_data
from excel_statment.position_configs import c_fi_E_PropertyPosition
from general.reports import report_consolidation, report_FCE, report_FC, report_FC_KN, report_E
from static_loading.triaxial_static_widgets_UI import ModelTriaxialItemUI, ModelTriaxialFileOpenUI, \
    ModelTriaxialReconsolidationUI, \
    ModelTriaxialConsolidationUI, ModelTriaxialDeviatorLoadingUI
from general.general_widgets import Float_Slider
from configs.styles import style
from singletons import E_models, FC_models, statment, VibrationFC_models
from loggers.logger import app_logger, log_this, handler
from tests_log.widget import TestsLogWidget
from tests_log.equipment import static
from tests_log.test_classes import TestsLogTriaxialStatic
import os
from version_control.configs import actual_version
from authentication.control import control

__version__ = actual_version
import numpy as np
from general.general_statement import StatementGenerator


class VibrationStrangthSoilTestApp(QWidget):

    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = VibrationStrangthStatment()
        self.tab_2 = MohrWidgetSoilTest()
        self.tab_3 = MohrWidgetSoilTest(model="VibrationFC_models")
        self.tab_4 = Save_Dir(
            {
                "standart": "Вибропрочность",
                "cryo": "Криовибропрочность",
            })
        # self.Tab_3.Save.save_button.clicked.connect(self.save_report)

        self.tab_widget.addTab(self.tab_1, "Обработка файла ведомости")
        self.tab_widget.addTab(self.tab_2, "Опыт FC")
        self.tab_widget.addTab(self.tab_3, "Опыт FC вибро")
        self.tab_widget.addTab(self.tab_4, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.signal[bool].connect(self.set_test_parameters)
        self.tab_1.statment_directory[str].connect(lambda x: self.tab_4.update(x))

        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_4.jornal_button.clicked.connect(self.jornal)

        self.tab_4.general_statment_button.clicked.connect(self.general_statment)

        self.save_massage = True
        # self.Tab_1.folder[str].connect(self.Tab_2.Save.get_save_folder_name)

        #self.tab_2.line_for_phiz.addStretch(-1)
        #self.physical_line_1.refresh_button.clicked.connect(self.tab_2.refresh)
        #self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line_1_1_layout.insertWidget(0, self.physical_line_1)
        self.physical_line_1.refresh_button.clicked.connect(self.tab_2.refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.line_1_1_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3.refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)


    def keyPressEvent(self, event):
        if statment.current_test:
            list = [x for x in statment]
            index = list.index(statment.current_test)
            if str(event.key()) == "90":
                if index >= 1:
                    statment.current_test = list[index - 1]
                    self.set_test_parameters(True)
            elif str(event.key()) == "88":
                if index < len(list) - 1:
                    statment.current_test = list[index + 1]
                    self.set_test_parameters(True)

    def set_test_parameters(self, params):
        self.tab_2.item_identification.set_data()
        self.tab_3.item_identification.set_data()
        self.tab_2.set_params()
        self.tab_3.set_params()
        self.physical_line_1.set_data()
        self.physical_line_2.set_data()

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.current_test.replace("/", "-").replace("*", "")

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
                              "mode": "НН, девиаторное нагружение в кинематическом режиме " + s,
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

            if statment.general_parameters.test_mode:
                name = file_path_name + " " + statment.general_data.object_number + " ТД" + ".pdf"

                FC_models[statment.current_test].save_log_files(save, file_path_name)
                VibrationFC_models[statment.current_test].save_log_files(save, file_path_name)

                shutil.copy(os.path.join(save, f"{file_path_name} FC ЦВИ.xls"),
                            statment.save_dir.cvi_directory + "/" + f"{file_path_name} FC ЦВИ.xls")

                FC_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"FC_models{statment.general_data.get_shipment_number()}.pickle"))

                VibrationFC_models.dump(os.path.join(statment.save_dir.save_directory,
                                                     f"VibrationFC_models{statment.general_data.get_shipment_number()}.pickle"))

                test_result = {}
                test_result["sigma_3_mohr"], test_result["sigma_1_mohr"] = FC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()
                test_result["c"], test_result["fi"], test_result["m"] = \
                FC_models[statment.current_test].get_test_results()["c"], \
                FC_models[statment.current_test].get_test_results()["fi"], \
                FC_models[statment.current_test].get_test_results()["m"]

                test_result["u_mohr"] = FC_models[statment.current_test].get_sigma_u()

                test_result["sigma_3_mohr"] += test_result["u_mohr"]
                test_result["sigma_1_mohr"] += test_result["u_mohr"]

                test_result["sigma_3_mohr_vs"], test_result["sigma_1_mohr_vs"] = VibrationFC_models[
                    statment.current_test].get_sigma_3_1()

                test_result["u_mohr_vs"] = VibrationFC_models[statment.current_test].get_sigma_u()

                test_result["sigma_3_mohr_vs"] += test_result["u_mohr_vs"]
                test_result["sigma_1_mohr_vs"] += test_result["u_mohr_vs"]

                test_result["c_vs"], test_result["fi_vs"], test_result["m"] = \
                    VibrationFC_models[statment.current_test].get_test_results()["c"], \
                    VibrationFC_models[statment.current_test].get_test_results()["fi"], \
                    VibrationFC_models[statment.current_test].get_test_results()["m"]

                test_result["u_mohr_vs"] = VibrationFC_models[statment.current_test].get_sigma_u()

                report_vibration_strangth(save + "/" + name, data_customer,
                                          statment[statment.current_test].physical_properties,
                                          statment.getLaboratoryNumber(), os.getcwd() + "/project_data/",
                                          test_parameter, test_result,
                                          (*self.tab_2.save_canvas(),
                                           *self.tab_3.save_canvas()), self.tab_4.report_type, "{:.2f}".format(__version__))

                shutil.copy(save + "/" + name, statment.save_dir.report_directory + "/" + name)

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path,
                              (c_fi_E_PropertyPosition["Трёхосное сжатие НН"][0][0] + str(number),
                               (number, c_fi_E_PropertyPosition["Трёхосное сжатие НН"][1][0])),
                              test_result["c"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              ("CJ" + str(number),
                               (number, 87)),
                              test_result["c_vs"], sheet="Лист1", color="FF6961")

                set_cell_data(self.tab_1.path,
                              ("CB" + str(number),
                               (number, 79)),
                              np.round(test_result["c_vs"] / test_result["c"], 2), sheet="Лист1", color="FF6961")

                #set_cell_data(self.tab_1.path,
                              #("FV" + str(number),
                               #(number, 177)),
                              #test_result["sigma_3_mohr_vs"], sheet="Лист1", color="FF6961")

            # statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
            # name=statment.general_parameters.test_mode + ".pickle")

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(
                    f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            control()

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

            try:
                statment.save([FC_models, VibrationFC_models],
                              [f"FC_models{statment.general_data.get_shipment_number()}.pickle",
                               f"VibrationFC_models{statment.general_data.get_shipment_number()}.pickle"])
            except Exception as err:
                QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        t = threading.Thread(target=save)
        progress.show()
        t.start()

    def jornal(self):
        if statment.tests == {}:
            QMessageBox.critical(self, "Ошибка", "Загрузите объект", QMessageBox.Ok)
        else:
            self.dialog = TestsLogWidget(static, TestsLogTriaxialStatic, self.tab_1.path)
            self.dialog.show()

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        _statment = StatementGenerator(self, path=s, statement_structure_key="Kcu")
        _statment.show()
