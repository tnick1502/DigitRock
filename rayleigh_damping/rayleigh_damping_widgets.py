
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHBoxLayout, QTabWidget, \
    QDialog, QTableWidget, QGroupBox, QPushButton, QComboBox, QDialogButtonBox, QTableWidgetItem, QHeaderView, \
    QTextEdit, QProgressDialog
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
import sys
import shutil
import os
import threading
from authentication.request_qr import request_qr
from authentication.control import control

from excel_statment.initial_tables import LinePhysicalProperties
from excel_statment.initial_statment_widgets import RayleighDampingStatment
from static_loading.triaxial_static_test_widgets import TriaxialStaticLoading_Sliders
from general.reports import report_RayleighDamping, zap
from general.save_widget import Save_Dir
from rayleigh_damping.rayleigh_damping_widgets_UI import RayleighDampingUI, CyclicDampingUI, ResultsUI
from excel_statment.initial_tables import TableVertical
from excel_statment.functions import set_cell_data
from general.report_general_statment import save_report
from singletons import RayleighDamping_models, statment
from loggers.logger import app_logger, handler
from version_control.configs import actual_version
from general.tab_view import TabMixin, AppMixin
__version__ = actual_version
from general.general_statement import StatementGenerator
from metrics.session_writer import SessionWriter

class RayleighDampingWidget(TabMixin, QWidget):
    """Виджет для открытия и обработки файла прибора. Связывает классы ModelTriaxialCyclicLoading_FileOpenData и
    ModelTriaxialCyclicLoadingUI"""
    signal = pyqtSignal()
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_Ui()

        self.sliders.signal[object].connect(self._sliders_moove)

    def _create_Ui(self):
        self.main_layout = QVBoxLayout(self)
        fill_keys = {
            "laboratory_number": "Лаб. ном.",
            "E50": "Модуль деформации E50, кПа",
            "c": "Сцепление с, МПа",
            "fi": "Угол внутреннего трения, град",
            "qf": "Максимальный девиатор qf, кПа",
            "sigma_3": "Обжимающее давление 𝜎3, кПа",
            "frequency": "Частота, Гц",
            "t": "Касательное напряжение",
        }
        self.identification = TableVertical(fill_keys)
        self.sliders = TriaxialStaticLoading_Sliders(
            {
                "alpha": "alpha",
                "betta": "betta",
                "Ms": "Ms",
            })
        #self.identification.setFixedWidth(350)
        #self.identification.setFixedHeight(700)
        self.layout_1 = QHBoxLayout()
        self.layout_1_1 = QVBoxLayout()
        self.layout_1_1_1 = QHBoxLayout()
        self.rayleigh_widget = RayleighDampingUI()
        self.damping_widget = CyclicDampingUI()
        self.damping_widget.signal[object].connect(self._refresh_one)
        self.result_widget = ResultsUI()

        self.layout_1_1.addWidget(self.identification)
        self.layout_1_1_1.addWidget(self.sliders)
        self.layout_1_1_1.addWidget(self.result_widget)
        self.layout_1_1.addLayout(self.layout_1_1_1)

        self.layout_1.addLayout(self.layout_1_1)
        self.layout_1.addWidget(self.rayleigh_widget)

        self.main_layout.addLayout(self.layout_1)
        self.main_layout.addWidget(self.damping_widget)

        self.main_layout.setContentsMargins(5, 5, 5, 5)

    def set_test_params(self, params):
        """Полкчение параметров образца и передача в классы модели и ползунков"""
        self.sliders.set_sliders_params(
            {
                "alpha": {"value": statment[statment.current_test].mechanical_properties.alpha,
                          "borders": [0.05, 0.3]},
                "betta": {"value": statment[statment.current_test].mechanical_properties.betta,
                          "borders": [0.001, 0.005]},
                "Ms": {"value": statment[statment.current_test].mechanical_properties.Ms,
                          "borders": [50, 300]}
            })
        self._plot()
        self.signal.emit()

    def _refresh(self):
        try:
            RayleighDamping_models[statment.current_test].set_test_params()
            self._plot()
            self.signal.emit()
        except KeyError:
            pass

    def _sliders_moove(self, param):
        statment[statment.current_test].mechanical_properties.alpha = param["alpha"]
        statment[statment.current_test].mechanical_properties.betta = param["betta"]
        statment[statment.current_test].mechanical_properties.Ms = param["Ms"]
        self._refresh()


    def _refresh_one(self, i):
        RayleighDamping_models[statment.current_test].set_one_test_params(i)
        self.set_test_params(True)
        try:
            RayleighDamping_models[statment.current_test].set_one_test_params(i)
            self.set_test_params(True)
        except:
            pass

    def _plot(self):
        """Построение графиков опыта"""
        plots, results = [], []
        for test in RayleighDamping_models[statment.current_test]._tests:
            plots.append(test.get_plot_data())
            results.append(test.get_test_results())

        self.damping_widget.plot(plots, results)

        plot = RayleighDamping_models[statment.current_test].get_plot_data()
        res = RayleighDamping_models[statment.current_test].get_test_results()
        self.rayleigh_widget.plot(plot, res)
        self.result_widget.set_data(res)

        #plots = self._model._static_test_data.get_plot_data()
        #res = self._model._static_test_data.get_test_results()
        #self.static_widget.plot(plots, res)

class RayleighDampingSoilTestApp(AppMixin, QWidget):
    def __init__(self, parent=None, geometry=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)

        if geometry is not None:
            self.setGeometry(geometry["left"], geometry["top"], geometry["width"], geometry["height"])
        # Создаем вкладки
        self.layout = QHBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_1 = RayleighDampingStatment()

        self.tab_3 = RayleighDampingWidget()
        self.tab_3.popIn.connect(self.addTab)
        self.tab_3.popOut.connect(self.removeTab)

        self.tab_4 = Save_Dir(result_table_params={
            "alpha": lambda lab: RayleighDamping_models[lab].get_test_results()['alpha'],
            "betta": lambda lab: RayleighDamping_models[lab].get_test_results()["betta"],
            "Коэф. демпфирования": lambda lab: str(RayleighDamping_models[lab].get_test_results()["damping_ratio"]),
        })
        self.tab_4.popIn.connect(self.addTab)
        self.tab_4.popOut.connect(self.removeTab)

        self.tab_widget.addTab(self.tab_1, "Идентификация пробы")
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
        self.tab_4.save_all_button.clicked.connect(self.save_all_reports)
        #self.tab_3.signal.connect(self.tab_4.result_table.update)

        self.button_predict = QPushButton("Прогнозирование")
        self.button_predict.setFixedHeight(50)
        self.button_predict.clicked.connect(self._predict)
        self.tab_1.layuot_for_button.addWidget(self.button_predict)

        self.save_massage = True

        self.tab_4.general_statment_button.clicked.connect(self.general_statment)

        self.physical_line_2 = LinePhysicalProperties()
        self.tab_3.main_layout.insertWidget(0, self.physical_line_2)
        self.physical_line_2.refresh_button.clicked.connect(self.tab_3._refresh)
        self.physical_line_2.save_button.clicked.connect(self.save_report_and_continue)
        self.tab_4.roundFI_btn.hide()

    def _set_params(self, param):
        self.tab_3.set_test_params(param)
        self.tab_3.identification.set_data()
        self.physical_line_2.set_data()

    def save_report(self):
        try:
            assert statment.current_test, "Не выбран образец в ведомости"
            file_path_name = statment.getLaboratoryNumber().replace("/", "-").replace("*", "")

            RayleighDamping_models.dump(os.path.join(statment.save_dir.save_directory,
                                        f"RayleighDamping_models{statment.general_data.get_shipment_number()}.pickle"))

            #statment.dump(''.join(os.path.split(self.tab_4.directory)[:-1]),
                          #name=statment.general_parameters.test_mode + ".pickle")

            test_parameter = {'sigma3': statment[statment.current_test].mechanical_properties.sigma_3,
                              'sigma1': statment[statment.current_test].mechanical_properties.sigma_3,
                              'tau': statment[statment.current_test].mechanical_properties.t,
                              'K0': statment[statment.current_test].mechanical_properties.K0,
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

            RayleighDamping_models[statment.current_test].save_log_files(save)

            data_customer = statment.general_data
            date = statment[statment.current_test].physical_properties.date
            if date:
                data_customer.end_date = date

            test_result = RayleighDamping_models[statment.current_test].get_test_results()
            data = {
                "laboratory": "mdgt",
                "password": "it_user",

                "test_name": "Cyclic",
                "object": str(statment.general_data.object_number),
                "laboratory_number": str(statment.current_test),
                "test_type": "rayleigh_damping",

                "data": {
                    "Лаболаторный номер:": str(statment.current_test),
                    "Обжимающее давление 𝜎3, МПа:": str(
                        np.round(statment[statment.current_test].mechanical_properties.sigma_3 / 1000, 3)),
                    "Коэффициент Релея α, c:": str(test_result["alpha"]),
                    "Коэффициент Релея β, 1 / c:": str(test_result["betta"])
                }
            }

            if self.tab_4.qr:
                qr = None  # qr = request_qr(data)
            else:
                qr = None


            report_RayleighDamping(save + "/" + file_name, data_customer,
                                  statment[statment.current_test].physical_properties,
                                  statment.getLaboratoryNumber(),
                                  os.getcwd() + "/project_data/",
                                  test_parameter, RayleighDamping_models[statment.current_test].get_test_results(),
                                  [self.tab_3.rayleigh_widget.save_canvas(),
                                   *self.tab_3.damping_widget.save_canvas()],
                                  "{:.2f}".format(__version__), qr_code=qr)


            number = statment[statment.current_test].physical_properties.sample_number + 7

            res = RayleighDamping_models[statment.current_test].get_test_results()
            damping_ratio = "; ".join([zap(f, 2) for f in res["damping_ratio"]])

            set_cell_data(self.tab_1.path, ("IL" + str(number), (number, 245)), damping_ratio, sheet="Лист1", color="FF6961")
            set_cell_data(self.tab_1.path, ("IM" + str(number), (number, 246)), zap(res["alpha"], 3), sheet="Лист1", color="FF6961")
            set_cell_data(self.tab_1.path, ("IN" + str(number), (number, 247)), zap(res["betta"], 5), sheet="Лист1", color="FF6961")
            #set_cell_data(self.tab_1.path, ("CB" + str(number), (number, 79)), Kd, sheet="Лист1", color="FF6961")



            shutil.copy(save + "/" + file_name, statment.save_dir.report_directory + "/" + file_name)

            if self.save_massage:
                QMessageBox.about(self, "Сообщение", "Успешно сохранено")
                app_logger.info(f"Проба {statment.current_test} успешно сохранена в папке {save}")

            self.tab_1.table_physical_properties.set_row_color(
                self.tab_1.table_physical_properties.get_row_by_lab_naumber(statment.current_test))

            control()


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

        _statment = StatementGenerator(self, path=s, statement_structure_key="rayleigh_damping")
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
