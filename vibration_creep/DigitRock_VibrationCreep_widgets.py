"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
__version__ = 1

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QTabWidget, \
    QDialog
from PyQt5.QtCore import pyqtSignal
import os
import time
import sys
import pyautogui
import shutil

from general.save_widget import Save_Dir
from vibration_creep.vibration_creep_widgets import VibrationCreepSoilTestWidget
from general.general_widgets import Statment_Vibration_Creep
from general.reports import report_triaxial_cyclic


class VibrationCreepSoilTest_Tab(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self.widget = VibrationCreepSoilTestWidget()
        self._create_UI()

    def _create_UI(self):
        self.layout = QVBoxLayout(self)
        self.save_widget = Save_Dir("Циклическое трехосное нагружение")
        self.save_widget.setFixedHeight(240)
        self.widget.layout.addWidget(self.save_widget)
        self.layout.addWidget(self.widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_params(self, params):
        self.widget.set_test_params(params)

class DigitRock_VibrationCreepSoilTest(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = Statment_Vibration_Creep()
        self.tab_2 = VibrationCreepSoilTest_Tab()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self.tab_2.save_widget.get_save_directory)
        self.tab_1.signal[object].connect(self.tab_2.widget.set_test_params)
        self.tab_2.save_widget.save_button.clicked.connect(self.save_report)

    def identification_set_data(self, data):
        self.tab_2.widget.identification.set_data(data)

    def save_report(self):

        def check_none(s):
            if s:
                return str(s)
            else:
                return "-"

        test_parameter = self.tab_1.table.open_line.get_data()

        try:
            assert self.tab_1.table.get_lab_number(), "Не выбран образец в ведомости"
            len(self.tab_2.widget._model._test_data.cycles)
            # assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            file_path_name = self.tab_1.table.get_lab_number().replace("/", "-").replace("*", "")

            save = self.tab_2.save_widget.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            if test_parameter["test_type"] == "Сейсморазжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-С" + ".pdf"
            elif test_parameter["test_type"] == "Штормовое разжижение":
                file_name = save + "/" + "Отчет " + file_path_name + "-ШТ" + ".pdf"

            """if test_parameter['equipment'] == "Прибор: Геотек":
                test_time = geoteck_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["sigma3"], self.Data["frequency"], self.Data["Points"], self.file.Data_phiz[self.file.Lab]["Ip"])

            elif test_parameter['equipment'] == "Прибор: Вилли":
                test_time = willie_text_file(save, self.Powerf, self.Arrays["PPR"], self.Arrays["Strain"], self.Data["frequency"], self.Data["N"], self.Data["Points"],
                                 self.Setpoint, self.Arrays["cell_press"], self.file.Data_phiz[self.file.Lab]["Ip"])"""

            if test_parameter['equipment'] == 'Прибор: Вилли':
                equipment = "Wille Geotechnik 13-HG/020:001"
                h = 76
                d = 38
            else:
                equipment = "Динамический стабилометр Геотек"
                h = 100
                d = 50

            params = self.tab_2.widget._model.get_test_params()

            test_parameter = {'sigma3': params["sigma_3"], 'sigma1': params["sigma_1"], 'tau': params["t"], 'K0': 1,
                              'frequency': params["frequency"],
                              "Hw": params.get("Hw", None),
                              "rw": params.get("rw", None),
                              'I': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]["balnost"],
                              'M': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]["magnituda"],
                              'MSF': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]['MSF'],
                              'rd': self.tab_1.table.get_test_data()[self.tab_1.table.get_lab_number()]['rd'],
                              'type': test_parameter["test_type"],
                              'Rezhim': 'Анизотропная реконсолидация, девиаторное циклическое нагружение',
                              'Oborudovanie': equipment, 'h': h, 'd': d}

            test_result = self.tab_2.widget._model.get_test_results()

            results = {'PPRmax': test_result['max_PPR'], 'EPSmax': test_result['max_strain'],
                       'res': test_result['conclusion'], 'nc': check_none(test_result['fail_cycle'])}

            report_triaxial_cyclic(file_name, self.tab_1.table.get_customer_data(),
                                   self.tab_1.table.get_physical_data(),
                                   self.tab_1.table.get_lab_number(),
                                   os.getcwd() + "/project_data/", test_parameter, results,
                                   self.tab_2.widget.test_widget.save_canvas(), __version__)

            try:
                if test_parameter['Oborudovanie'] == "Wille Geotechnik 13-HG/020:001":
                    self.tab_2.generate_log_file(save)
            except AttributeError:
                pass

            shutil.copy(file_name, self.tab_2.save_widget.report_directory + "/" + file_name[len(file_name) -
                                                                                 file_name[::-1].index("/"):])
            QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
            self.tab_1.table.table_physical_properties.set_row_color(
                self.tab_1.table.table_physical_properties.get_row_by_lab_naumber(self.tab_1.table.get_lab_number()))

        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", "Не загружен файл опыта", QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = DigitRock_VibrationCreepSoilTest()
    ex.show()
    sys.exit(app.exec_())
