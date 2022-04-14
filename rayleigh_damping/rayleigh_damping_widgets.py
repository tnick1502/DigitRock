
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QTabWidget, \
    QDialog, QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QTableWidgetItem, QHeaderView, \
    QTextEdit, QProgressDialog
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

class RayleighDampingWidget(TabMixin, QWidget):
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
            "frequency": "Частота, Гц",
        }
        self.identification = TableVertical(fill_keys, size={"size": 100, "size_fixed_index": [1]})
        self.identification.setFixedWidth(350)
        self.identification.setFixedHeight(700)
        self.layout.addWidget(self.dynamic_widget)

        self.layout_2.addWidget(self.identification)
        self.layout.addLayout(self.layout_2)
        self.layout_2.addStretch(-1)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addLayout(self.layout)

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

        self.tab_4 = Save_Dir(result_table_params={
            "Kd": lambda lab: "; ".join([str(i["Kd"]) for i in VC_models[lab].get_test_results()]),
            "E50d": lambda lab: "; ".join([str(i["E50d"]) for i in VC_models[lab].get_test_results()]),
            "E50": lambda lab: "; ".join([str(i["E50"]) for i in VC_models[lab].get_test_results()]),
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

        self.tab_1.statment_directory[str].connect(lambda signal: self.tab_4.update())
        #self.tab_1.signal[object].connect(self.tab_2.identification.set_data)
        self.tab_1.signal[bool].connect(self._set_params)
        self.tab_4.save_button.clicked.connect(self.save_report)
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        self.tab_2.signal[bool].connect(self.tab_3.set_test_params)
        self.tab_3.signal.connect(self.tab_4.result_table.update)

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

    def _set_params(self, param):
        self.tab_2.set_params(param)
        self.tab_3.set_test_params(param)
        self.tab_3.identification.set_data()
        self.tab_2.item_identification.set_data()
        self.physical_line_1.set_data()
        self.physical_line_2.set_data()

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            VC_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"VC_models{statment.general_data.get_shipment_number()}.pickle"))
            E_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"E_models{statment.general_data.get_shipment_number()}.pickle"))

            #statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
                          #name=statment.general_parameters.test_mode + ".pickle")

            test_parameter = {'sigma_3': statment[statment.current_test].mechanical_properties.sigma_3,
                              't': statment[statment.current_test].mechanical_properties.t,
                              'frequency': statment[statment.current_test].mechanical_properties.frequency,
                              'Rezhim': 'Изотропная реконсолидация, девиаторное циклическое нагружение',
                              'Oborudovanie': "Wille Geotechnik 13-HG/020:001", 'h': 76, 'd': 38}

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

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
                                       *self.tab_2.deviator_loading.save_canvas(format=["jpg", "jpg"])],
                                      "{:.2f}".format(__version__))

                Kd = ""
                Ed = ""
                E50 = ""
                prediction = ""
                for i in range(len(res)):
                    Kd += zap(res[i]["Kd"], 2) + "; "
                    Ed += zap(res[i]["E50d"], 1) + "; "
                    E50 += zap(res[i]["E50"], 1) + "; "
                    prediction += zap(res[i]["prediction"]["50_years"], 3) + "; "

                number = statment[statment.current_test].physical_properties.sample_number + 7

                set_cell_data(self.tab_1.path, ("IH" + str(number), (number, 241)), E50, sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path, ("II" + str(number), (number, 242)), Ed, sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path, ("CB" + str(number), (number, 79)), Kd, sheet="Лист1", color="FF6961")


            else:
                pick_vc, pick_c = self.tab_3.dynamic_widget.save_canvas()
                report_VibrationCreep(save + "/" + file_name, data_customer,
                                      statment[statment.current_test].physical_properties,
                                      statment.getLaboratoryNumber(),
                                      os.getcwd() + "/project_data/",
                                      test_parameter, E_models[statment.current_test].get_test_results(),
                                      VC_models[statment.current_test].get_test_results(),
                                      [pick_vc, pick_c, *self.tab_2.deviator_loading.save_canvas(format=["jpg", "jpg"])], "{:.2f}".format(__version__))
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


            shutil.copy(save + "/" + file_name, statment.save_dir.report_directory + "/" + file_name)

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))


        except AssertionError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except TypeError as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            app_logger.exception(f"Не выгнан {statment.current_test}")

        except PermissionError:
            QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)
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
                self._set_params(True)
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

        _statment = StatementGenerator(self, path=s, statement_structure_key="triaxial_cyclic")
        _statment.show()

    def save_report_and_continue(self):
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