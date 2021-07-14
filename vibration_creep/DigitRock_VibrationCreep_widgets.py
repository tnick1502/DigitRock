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
from general.reports import report_VibrationCreep

class DigitRock_VibrationCreepSoilTest(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = Statment_Vibration_Creep()
        self.tab_2 = VibrationCreepSoilTestWidget()
        self.tab_3 = Save_Dir("Виброползучесть")

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.tab_widget.addTab(self.tab_3, "Сохранение отчета")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self.tab_3.get_save_directory)
        self.tab_1.signal[object].connect(self.tab_2.identification.set_data)
        self.tab_1.signal[object].connect(self.tab_2.set_test_params)
        self.tab_3.save_button.clicked.connect(self.save_report)

    def identification_set_data(self, data):
        self.tab_2.widget.identification.set_data(data)

    def save_report(self):
        #try:
            #assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
        params = self.tab_2.get_test_params()

        test_parameter = {'sigma_3': params["sigma_3"], 't': params["t"],
                          'frequency': params["frequency"],
                          'Rezhim': 'Изотропная реконсолидация, девиаторное циклическое нагружение',
                          'Oborudovanie': "Wille Geotechnik 13-HG/020:001", 'h': 76, 'd': 38}

        test_result = self.tab_2.get_test_results()

        save = self.tab_3.arhive_directory + "/" + self.tab_1.get_lab_number()
        save = save.replace("*", "")
        if os.path.isdir(save):
            pass
        else:
            os.mkdir(save)

        Name = "Отчет " + self.tab_1.get_lab_number().replace("*", "") + "-ВП" + ".pdf"

        pick_deviator, _ = self.tab_2.static_widget.deviator_loading.save_canvas()

        pick_vc, pick_c = self.tab_2.dynamic_widget.save_canvas()

        report_VibrationCreep(save + "/" + Name, self.tab_1.get_customer_data(),
                             self.tab_1.get_physical_data(), self.tab_1.get_lab_number(),
                             os.getcwd() + "/project_data/",
                             test_parameter, self.tab_2.static_widget.get_test_results(),
                             [pick_vc, pick_deviator, pick_c], 1.1)

        shutil.copy(save + "/" + Name, self.tab_3.report_directory + "/" + Name)
        QMessageBox.about(self, "Сообщение", "Успешно сохранено")

        """except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)"""



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = DigitRock_VibrationCreepSoilTest()
    ex.show()
    sys.exit(app.exec_())
