import time

from excel_statment.initial_tables import LinePhysicalProperties
from excel_statment.position_configs import MechanicalPropertyPosition
from version_control.configs import actual_version
__version__ = actual_version
# system
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QDialog, QHBoxLayout, \
    QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QHeaderView, QTableWidgetItem, QTabWidget, \
    QTextEdit, QProgressDialog
import os
from PyQt5.QtCore import Qt
import numpy as np
import sys
import shutil
import threading
# global
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from loggers.logger import app_logger, log_this, handler
from singletons import K0_models, statment
from excel_statment.initial_statment_widgets import K0Statment
from authentication.control import control
from excel_statment.initial_statment_widgets import TableCastomer
from excel_statment.functions import set_cell_data
from general.report_general_statment import save_report
from general.general_statement import StatementGenerator
from general.save_widget import Save_Dir
from general.reports import report_k0, report_k0ur
# local
from k0_test.triaxial_k0_widgets_UI import K0UI, K0OpenTestUI, \
    K0SoilTestUI, K0IdentificationUI
from k0_test.triaxial_k0_model import ModelK0
from authentication.request_qr import request_qr
from metrics.session_writer import SessionWriter
from general.movie_label import Loader

class K0ProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self.model = ModelK0()
        self._create_Ui()
        # self.open_widget.button_open_file.clicked.connect(self._open_file)
        self.open_widget.button_open_path.clicked.connect(self._open_path)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.identification_widget = K0IdentificationUI()
        self.open_widget = K0OpenTestUI()
        self.layout.addWidget(self.identification_widget)
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)
        self.test_processing_widget = K0UI()
        self.layout.addWidget(self.test_processing_widget)
        self.save_widget = Save_Dir()
        self.layout.addWidget(self.save_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _open_path(self):
        """Открытие файла опыта"""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.open_widget.set_file_path("")
            self._plot()
            try:
                self._model.open_path(path)
                self.open_widget.set_file_path(path)
            except (ValueError, IndexError, FileNotFoundError):
                pass
            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_processing_widget.plot(plots, res)


class K0SoilTestWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()
        self.test_widget.sliders.signal[object].connect(self._params_slider_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.line_1 = QHBoxLayout()
        self.identification_widget = K0IdentificationUI()
        self.test_widget = K0SoilTestUI()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setFixedHeight(120)
        self.line_1.addWidget(self.identification_widget)
        self.line_for_phiz = QVBoxLayout()
        self.line_1.addLayout(self.line_for_phiz)

        self.layout.addLayout(self.line_1)
        self.layout.addWidget(self.test_widget)
        self.save_widget = Save_Dir(qr=True)
        self.layout.addWidget(self.save_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def set_test_params(self, params):
        try:
            self.test_widget.sliders.set_sliders_params(K0_models[statment.current_test].get_draw_params())
            self._plot()
        except KeyError:
            pass

    @log_this(app_logger, "debug")
    def _params_slider_moove(self, params):
        try:
            K0_models[statment.current_test].set_draw_params(params)
            self.set_test_params(True)
        except KeyError:
            pass

    # @log_this(app_logger, "debug")
    def _refresh(self):
        try:
            K0_models[statment.current_test].set_test_params()
            self.test_widget.sliders.set_sliders_params(K0_models[statment.current_test].get_draw_params())
            self._plot()
        except KeyError:
            pass

    def _plot(self):
        """Построение графиков опыта"""
        try:
            plots = K0_models[statment.current_test].get_plot_data()
            res = K0_models[statment.current_test].get_test_results()
            self.test_widget.plot(plots, res)
        except KeyError:
            pass


class K0ProcessingApp(QWidget):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Создаем вкладки
        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = K0Statment()
        self.tab_2 = K0ProcessingWidget()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)

        self.tab_1.statment_directory[str].connect(self._set_save_directory)
        self.tab_1.signal[bool].connect(self.tab_2.identification_widget.set_params)
        self.tab_2.save_widget .save_button.clicked.connect(self.save_report)

    def _set_save_directory(self, signal):
        self.tab_2.save_widget.set_directory(signal, "Трехосное сжатие K0")

    def _set_save_directory(self, signal):
        self.tab_4.save.set_directory(signal, "Трехосное сжатие K0")

    def save_report(self):
        try:
            assert self.tab_1.get_lab_number(), "Не выбран образец в ведомости"
            # assert self.tab_2.test_processing_widget.model._test_data.cycles, "Не выбран файл прибора"
            file_path_name = self.tab_1.get_lab_number().replace("/", "-").replace("*", "")

            save = self.tab_2.save.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            file_name = save + "/" + "Отчет " + file_path_name + "-K0" + ".pdf"

            test_param = self.tab_1.get_data()
            test_parameter = {"reference_pressure": test_param.reference_pressure}

            test_result = self.tab_2.test._model.get_test_results()

            results = {"G0": test_result["G0"], "gam07": test_result["threshold_shear_strain"]}


            report_k0(file_name, self.tab_1.get_customer_data(),
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


class K0SoilTestApp(QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])

        # Создаем вкладки
        self.layout = QHBoxLayout(self)
        self.save_massage = True

        self.tab_widget = QTabWidget()
        self.tab_1 = K0Statment()
        self.tab_2 = K0SoilTestWidget()

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
        self.tab_widget.addTab(self.tab_2, "Обработка")
        self.layout.addWidget(self.tab_widget)
        self.log_widget = QTextEdit()
        self.log_widget.setFixedWidth(300)
        self.layout.addWidget(self.log_widget)

        handler.emit = lambda record: self.log_widget.append(handler.format(record))

        self.tab_1.statment_directory[str].connect(lambda x: self.tab_2.save_widget.update(x))

        self.physical_line_1 = LinePhysicalProperties()
        self.tab_2.line_for_phiz.addWidget(self.physical_line_1)
        self.tab_2.line_for_phiz.addStretch(-1)

        self.tab_1.signal[bool].connect(self.set_test_parameters)

        self.physical_line_1.refresh_button.clicked.connect(self.tab_2._refresh)
        self.physical_line_1.save_button.clicked.connect(self.save_report_and_continue)

        self.tab_2.save_widget.save_button.clicked.connect(self.save_report)
        self.tab_2.save_widget.save_all_button.clicked.connect(self.save_all_reports)

        # self.button_predict = QPushButton("Прогнозирование")
        # self.button_predict.setFixedHeight(50)
        # self.button_predict.clicked.connect(self._predict)
        # self.tab_1.splitter_table_vertical.addWidget(self.button_predict)

        self.tab_2.save_widget.general_statment_button.clicked.connect(self.general_statment)

        self.tab_2.save_widget.roundFI_btn.hide()

        self.loader = Loader(window_title="Сохранение протоколов...", start_message="Сохранение протоколов...",
                        message_port=7783, parent=self)

    def save_report(self, save_all_mode=False):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.current_test.replace("/", "-").replace("*", "")

            read_parameters = self.tab_1.open_line.get_data()

            save = statment.save_dir.arhive_directory + "/" + file_path_name
            save = save.replace("*", "")

            if os.path.isdir(save):
                pass
            else:
                os.mkdir(save)

            file_name = save + "/" + "Отчет " + file_path_name + "-БП" + ".pdf"

            test_result = K0_models[statment.current_test].get_test_results()

            results = {"K0nc": test_result["K0nc"], "sigma_1": test_result["sigma_1"], "sigma_3": test_result["sigma_3"]}
            if read_parameters["test_mode"] == K0Statment.test_modes[1]:
                results["Nuur"] = test_result["Nuur"]
                results["K0oc"] = test_result["K0oc"]
                results["sigma_1_ur"] = test_result["sigma_1_ur"]
                results["sigma_3_ur"] = test_result["sigma_3_ur"]

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date

            if self.tab_2.save_widget.qr:
                qr = request_qr()
            else:
                qr = None

            if date:
                data_customer.end_date = date

            if read_parameters["test_mode"] == K0Statment.test_modes[0]:
                report_k0(file_name, data_customer,
                          statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(),
                          os.getcwd() + "/project_data/", statment[statment.current_test].mechanical_properties, results,
                          self.tab_2.test_widget.save_canvas(), __version__, qr_code=qr)
            if read_parameters["test_mode"] == K0Statment.test_modes[1]:
                report_k0ur(file_name, data_customer,
                          statment[statment.current_test].physical_properties,
                          statment.getLaboratoryNumber(),
                          os.getcwd() + "/project_data/", statment[statment.current_test].mechanical_properties, results,
                          self.tab_2.test_widget.save_canvas(), __version__, qr_code=qr)

            number = statment[statment.current_test].physical_properties.sample_number + 7

            shutil.copy(file_name, statment.save_dir.report_directory + "/" + file_name[len(file_name) -
                                                                                      file_name[::-1].index("/"):])

            K0_models[statment.current_test].save_log_file(save + "/" + f"{file_path_name}.log")
            K0_models[statment.current_test].save_cvi_file(save, f"{file_path_name} ЦВИ.xls")
            shutil.copy(os.path.join(save, f"{file_path_name} ЦВИ.xls"),
                        statment.save_dir.cvi_directory + "/" + f"{file_path_name} ЦВИ.xls")

            set_cell_data(self.tab_1.path,
                          (MechanicalPropertyPosition["K0nc"][0] + str(number),
                           (number, MechanicalPropertyPosition["K0nc"][1])),
                          test_result["K0nc"], sheet="Лист1", color="FF6961")

            if read_parameters["test_mode"] == K0Statment.test_modes[1]:
                set_cell_data(self.tab_1.path,
                              (MechanicalPropertyPosition["Nuur"][0] + str(number),
                               (number, MechanicalPropertyPosition["Nuur"][1])),
                              test_result["Nuur"], sheet="Лист1", color="FF6961")
                set_cell_data(self.tab_1.path,
                              (MechanicalPropertyPosition["K0oc"][0] + str(number),
                               (number, MechanicalPropertyPosition["K0oc"][1])),
                              test_result["K0oc"], sheet="Лист1", color="FF6961")

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Отчет успешно сохранен")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            if read_parameters["test_mode"] == K0Statment.test_modes[0]:
                K0_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"k0_models{statment.general_data.get_shipment_number()}.pickle"))
            if read_parameters["test_mode"] == K0Statment.test_modes[1]:
                K0_models.dump(os.path.join(statment.save_dir.save_directory,
                                            f"k0ur_models{statment.general_data.get_shipment_number()}.pickle"))
            control()
            return True, 'Успешно'

        except AssertionError as error:
            # self.loader.critical("Ошибка", str(error))
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
            return False, f'{str(error)}'

        except PermissionError:
            # self.loader.critical("Ошибка", "Закройте файл отчета")
            if not save_all_mode:
                QMessageBox.critical(self, "Ошибка", "Закройте файл отчета", QMessageBox.Ok)
            return False, 'Не закрыт файл отчета'

    def save_all_reports(self):
        if self.loader.is_running:
            QMessageBox.critical(self, "Ошибка", "Закройте окно сохранения")
            return
        count = len(statment)
        Loader.send_message(self.loader.port, f"Сохранено 0 из {count}")

        def save():
            for i, test in enumerate(statment):
                self.save_massage = False
                statment.setCurrentTest(test)
                self.tab_2.set_test_params(True)
                try:
                    is_ok, message = self.save_report(save_all_mode=True)
                    if not is_ok:
                        self.loader.close_OK(f"Ошибка сохранения пробы {statment.current_test}\n{message}.\nОперация прервана.")
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

            read_parameters = self.tab_1.open_line.get_data()
            try:
                models = [model for model in [K0_models] if len(model)]

                names = []
                if len(K0_models):
                    if read_parameters["test_mode"] == K0Statment.test_modes[0]:
                        names.append(f"k0_models{statment.general_data.get_shipment_number()}.pickle")

                    if read_parameters["test_mode"] == K0Statment.test_modes[1]:
                        names.append(f"k0ur_models{statment.general_data.get_shipment_number()}.pickle")

                statment.save(models, names)
            except Exception as err:
                QMessageBox.critical(self, "Ошибка", f"Ошибка бекапа модели {str(err)}", QMessageBox.Ok)

        t = threading.Thread(target=save)
        self.loader.start()
        t.start()

        SessionWriter.write_session(len(statment))

    def general_statment(self):
        try:
            s = statment.general_data.path
        except:
            s = None

        _statment = StatementGenerator(self, path=s, statement_structure_key="Resonance column")
        _statment.show()

    def set_test_parameters(self, params):
        self.tab_2.set_test_params(params)
        self.tab_2.identification_widget.set_data()
        self.physical_line_1.set_data()

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
        SessionWriter.write_test()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = K0SoilTestApp()
    ex.show()
    sys.exit(app.exec_())
