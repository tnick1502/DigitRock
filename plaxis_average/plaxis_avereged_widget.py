from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, QScrollArea, \
    QTableWidgetItem, QRadioButton, QButtonGroup, QLabel, QPushButton, QMessageBox, QLineEdit, QFileDialog, QDialog, QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import sys
import os

from excel_statment.initial_tables import TableVertical
from general.general_functions import read_json_file
from plaxis_average.model import averaged_model
from plaxis_average.statment import averaged_statment
from general.general_widgets import Float_Slider
from singletons import E_models
from configs.styles import style
from singletons import statment
from general.reports import report_averaged
from version_control.configs import actual_version
from io import BytesIO

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    pass
    #plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

class Sliders(QWidget):
    """Виджет с ползунками для регулирования значений переменных.
    При перемещении ползунков отправляет 2 сигнала."""
    signal = pyqtSignal(object)

    def __init__(self, params):
        """Определяем основную структуру данных"""
        super().__init__()
        self._params = params

        self._activate = False

        self._createUI("Настройки аппроксимации", params)

    def _createUI(self, name, params):
        self.layout = QVBoxLayout(self)
        setattr(self, "{}_box".format(name), QGroupBox(name))
        box = getattr(self, "{}_box".format(name))
        setattr(self, "{}_box_layout".format(name), QVBoxLayout())
        box_layout = getattr(self, "{}_box_layout".format(name))

        for var in params:
            if params[var]:
                # Создадим подпись слайдера
                label = QLabel(params[var])  # Создааем подпись
                label.setFixedWidth(150)  # Фиксируем размер подписи

                # Создадим слайдер
                setattr(self, "{name_var}_slider".format(name_var=var),
                        Float_Slider(Qt.Horizontal))
                slider = getattr(self, "{name_var}_slider".format(name_var=var))

                # Создадим строку со значнием
                setattr(self, "{name_var}_label".format(name_var=var), QLabel())
                slider_label = getattr(self, "{name_var}_label".format(name_var=var))
                slider_label.setFixedWidth(40)
                # slider_label.setStyleSheet(style)

                # Создадтм строку для размещения
                setattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var), QHBoxLayout())
                line = getattr(self, "{name_widget}_{name_var}_line".format(name_widget=name, name_var=var))

                # СРазместим слайдер и подпись на строке
                line.addWidget(label)
                line.addWidget(slider)
                line.addWidget(slider_label)
                box_layout.addLayout(line)
                func = getattr(self, "_sliders_moove".format(name_widget=name, name_var=var))
                slider.sliderMoved.connect(func)
                release = getattr(self, "_sliders_released".format(name_widget=name, name_var=var))
                slider.sliderReleased.connect(release)
                slider.setStyleSheet(style)
            else:
                label = QLabel(params[var])  # Создааем подпись
                label.setFixedWidth(150)  # Фиксируем размер подписи
                setattr(self, "{name_widget}_{name_var}_empty".format(name_widget=name,
                                                                      name_var=var), QHBoxLayout())
                line = getattr(self, "{name_widget}_{name_var}_empty".format(name_widget=name,
                                                                             name_var=var))
                line.addWidget(label)
                box_layout.addLayout(line)

        box.setLayout(box_layout)

        self.layout.addWidget(box)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _get_slider_params(self, params):
        """Получение по ключам значения со всех слайдеров"""
        return_params = {}
        for key in params:
            slider = getattr(self, "{}_slider".format(key))
            if key == 'max_deformation_param':
                return_params[key] = float(slider.current_value())
            else:
                return_params[key] = int(round(slider.current_value()))
        return return_params

    def _set_slider_labels_params(self, params):
        """Установка по ключам текстовых полей значений слайдеров"""
        for key in params:
            label = getattr(self, "{}_label".format(key))
            label.setText(str(params[key]))

    def _sliders_moove(self):
        """Обработка перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params(self._params)
            self._set_slider_labels_params(params)

    def _sliders_released(self):
        """Обработка окончания перемещения слайдеров деформации"""
        if self._activate:
            params = self._get_slider_params(self._params)
            self._set_slider_labels_params(params)
            self.signal.emit(params)

    def set_params(self, params):
        """становка заданых значений на слайдеры"""
        for var in params:
            current_slider = getattr(self, "{name_var}_slider".format(name_var=var))
            if params[var]["value"]:
                current_slider.set_borders(*params[var]["borders"])
            current_slider.set_value(params[var]["value"])

        self._activate = True

        self._sliders_moove()

class ResultTable(TableVertical):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        fill_keys = {
            "averaged_E50": "Модуль деформации E50, МПа",
            "averaged_qf": "Максимальный девиатор qf, МПа",
        }
        super().__init__(fill_keys=fill_keys, size={"size": 100, "size_fixed_index": [1]})

    def set_data(self, data: dict):
        """Получение данных, Заполнение таблицы параметрами"""
        self._clear_table()

        replaceNone = lambda x: str(x) if x is not None else "-"

        for i, key in enumerate(self._fill_keys):
            attr = replaceNone(data.get(key, None))
            self.setItem(i, 1, QTableWidgetItem(attr))

class Info(QDialog):
    def __init__(self, text='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._UI()
        self.textbox.setText(text)
        self.show()

    def _UI(self):
        self.setWindowTitle("Информация")
        self.setFixedWidth(500)
        self.setFixedHeight(600)
        self.layout = QVBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.setLayout(self.layout)
        self.textbox = QTextEdit()
        self.textbox.setDisabled(True)

        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(lambda: self.close())

        self.layout_buttons.addStretch(-1)
        self.layout_buttons.addWidget(self.ok_button)

        self.layout.addWidget(self.textbox)
        self.layout.addLayout(self.layout_buttons)

class DeviatorItemUI(QGroupBox):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self, EGE: str = None, parent=None):
        """Определяем основную структуру данных"""
        super().__init__(parent=parent)
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.1, "wspace": 0.12, "hspace": 0.07, "left": 0.07}
        self.setTitle(f"ИГЭ: {EGE}")
        self.EGE = EGE
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()

        self.widgets_line = QHBoxLayout()

        self.param_box = QGroupBox("Параметры усреднения")
        self.param_box_layout = QVBoxLayout()

        self.param_box.setLayout(self.param_box_layout)
        self.radio_button_layout = QHBoxLayout()
        self.param_radio_button_1 = QRadioButton('Секторальная разбивка')
        self.param_radio_button_1.param_type = 'sectors'
        self.param_radio_button_2 = QRadioButton('Полином')
        self.param_radio_button_1.param_type = 'poly'
        
        self.param_button_group = QButtonGroup()
        self.param_button_group.addButton(self.param_radio_button_1)
        self.param_button_group.addButton(self.param_radio_button_2)
        self.param_button_group.buttonClicked.connect(self.radio_button_clicked)
        self.radio_button_layout.addWidget(self.param_radio_button_1, 1)
        self.radio_button_layout.addWidget(self.param_radio_button_2, 2)

        self.param_radio_button_2.setChecked(True)
        #self.param_box_layout.addLayout(self.radio_button_layout)
        '''
        if averaged_model[self.EGE].approximate_type == 'sectors':
            self.param_radio_button_1.setChecked(True)
        elif averaged_model[self.EGE].approximate_type == 'poly':
            self.param_radio_button_2.setChecked(True)

        if averaged_model[self.EGE].approximate_type == 'sectors':
            self.param_radio_button_1.setChecked(True)
            self.param_slider = Sliders({"param": "Степень полинома", 'filter_param': 'Степень сглаживания'})
            self.param_slider.set_params(
                {"param": {"value": averaged_model[self.EGE].approximate_param_sectors, "borders": [50, 1000]}})
        elif averaged_model[self.EGE].approximate_type == 'poly':
            self.param_radio_button_2.setChecked(True)
            self.param_slider = Sliders({"param": "Параметр аппроксимации"})
            self.param_slider.set_params(
                {"param": {"value": averaged_model[self.EGE].approximate_param_poly, "borders": [3, 15]}})
        '''

        self.param_slider = Sliders({"param": "Степень полинома", 'max_deformation_param': 'Максимальная деформация'})
        self.param_slider.set_params(
            {
                "param": {"value": averaged_model[self.EGE].approximate_param_poly, "borders": [2, 15]},
                "max_deformation_param": {"value": averaged_model[self.EGE].approximate_param_max_deformation, "borders": [0.02, 0.15]},
            })

        self.param_slider.signal[object].connect(self.slider_moove)
        self.param_box_layout.addWidget(self.param_slider)

        self.results_box = QGroupBox("Результаты обработки")
        self.results_box.setFixedHeight(150)
        self.results_box_layout = QVBoxLayout()
        self.results_box.setLayout(self.results_box_layout)
        self.results_table = ResultTable()
        self.results_box_layout.addWidget(self.results_table)

        self.widgets_line.addWidget(self.param_box)
        self.widgets_line.addWidget(self.results_box)

        self.plot_frame = QFrame()
        self.plot_frame.setFixedHeight(500)
        self.plot_frame.setFrameShape(QFrame.StyledPanel)
        self.plot_frame.setStyleSheet('background: #ffffff')
        self.plot_frame_layout = QVBoxLayout()
        self.plot_figure = plt.figure()
        self.plot_figure.subplots_adjust(**self.plot_params)
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_ax = self.plot_figure.add_subplot(111)
        self.plot_ax.grid(axis='both', linewidth='0.4')
        self.plot_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.plot_ax.set_ylabel("Девиатор напряжений $q$', МПa")
        self.plot_canvas.draw()
        self.plot_frame_layout.setSpacing(0)
        self.plot_frame_layout.addWidget(self.plot_canvas)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self)
        self.plot_frame_layout.addWidget(self.plot_toolbar)
        self.plot_frame.setLayout(self.plot_frame_layout)

        self.layout.addLayout(self.widgets_line)
        self.layout.addWidget(self.plot_frame)

        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self):
        """Построение графиков опыта"""
        self.plot_ax.clear()
        self.plot_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.plot_ax.set_ylabel("Девиатор напряжений $q$', МПa")
        results = averaged_model[self.EGE].get_results()
        self.results_table.set_data(results)

        plot_data = averaged_model[self.EGE].get_plot_data()

        max_strain = max(plot_data["averaged"]["strain"])

        for key in plot_data:
            if key == "averaged":
                if plot_data[key]["strain"] is not None:
                    self.plot_ax.plot(
                        plot_data[key]["strain"], plot_data[key]["deviator"],
                        label=key, linewidth=3, linestyle="-")
            else:
                i, = np.where(plot_data[key]["strain"] >= max_strain)

                if len(i):
                    i = i[0]
                else:
                    i = len(plot_data[key]["strain"])

                plot_data[key]["strain"] = plot_data[key]["strain"][:i]
                plot_data[key]["deviator"] = plot_data[key]["deviator"][:i]

                i_max = np.argmax(plot_data[key]["deviator"])

                if (plot_data[key]["strain"][i_max] <= 0.98 * max(plot_data[key]["strain"])) and (0.97 * plot_data[key]["deviator"][i_max] >= plot_data[key]["deviator"][-1]):
                    self.plot_ax.plot(
                        plot_data[key]["strain"][:i_max], plot_data[key]["deviator"][:i_max],
                        label=key, linewidth=1, linestyle="-", alpha=0.6)
                    self.plot_ax.plot(
                        plot_data[key]["strain"][i_max:], plot_data[key]["deviator"][i_max:],
                        linewidth=0.5, linestyle="--", alpha=0.5, color='gray')
                else:
                    self.plot_ax.plot(
                        plot_data[key]["strain"], plot_data[key]["deviator"],
                        label=key, linewidth=1, linestyle="-", alpha=0.6)

        self.plot_ax.plot(
            [0, 0.9 * results["averaged_qf"] / results["averaged_E50"]],
            [0, 0.9 * results["averaged_qf"]],
            linewidth=1, linestyle="-", alpha=0.6, color="black")

        self.plot_ax.legend()
        self.plot_canvas.draw()

    def radio_button_clicked(self, obj):
        try:
            if self.param_button_group.id(obj) == -3:
                averaged_model[self.EGE].set_approximate_type("poly", averaged_model[self.EGE].approximate_param_poly)
                self.param_slider.set_params(
                    {"param": {"value": averaged_model[self.EGE].approximate_param_poly, "borders": [3, 15]}})
            elif self.param_button_group.id(obj) == -2:
                averaged_model[self.EGE].set_approximate_type("sectors", averaged_model[self.EGE].approximate_param_sectors)
                self.param_slider.set_params(
                    {"param": {"value": averaged_model[self.EGE].approximate_param_sectors, "borders": [50, 1000]}})
        except Exception as err:
            print(err)
        self.plot()

    def slider_moove(self, param):
        try:
            if averaged_model[self.EGE].approximate_type == "poly":
                averaged_model[self.EGE].set_approximate_type(
                    approximate_type="poly", approximate_param=param["param"], approximate_max_deformation=param["max_deformation_param"]
                )
            elif averaged_model[self.EGE].approximate_type == "sectors":
                averaged_model[self.EGE].set_approximate_type("sectors", param["param"])
            self.plot()
        except Exception as err:
            print(err)

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""
        path = BytesIO()
        size = self.plot_figure.get_size_inches()
        self.plot_figure.set_size_inches([6.7, 4.2])
        self.plot_figure.savefig(path, format='svg', transparent=True)
        path.seek(0)
        self.plot_figure.set_size_inches(size)
        self.plot_canvas.draw()

        return path

class AverageWidget(QGroupBox):
    def __init__(self):
        super().__init__()
        self._create_UI()
        self.plot()
        self.setMinimumHeight(800)
        self.setMinimumWidth(1200)

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout_wiget = QVBoxLayout()

        self.open_box = QGroupBox("Ведомость")
        self.open_box_layout = QHBoxLayout()
        self.open_box.setLayout(self.open_box_layout)
        self.open_box.setFixedHeight(70)

        self.statment_button = QPushButton("Выбрать ведомость")
        self.statment_button.clicked.connect(self.statment_button_click)
        self.open_box_layout.addWidget(self.statment_button)
        self.statment_button.setFixedWidth(120)

        self.statment_line = QLineEdit()
        self.statment_line.setDisabled(True)
        self.open_box_layout.addWidget(self.statment_line)

        self.info_button = QPushButton("Информация")
        self.info_button.clicked.connect(self.info)
        self.open_box_layout.addWidget(self.info_button)
        self.info_button.setFixedWidth(120)

        self.layout_wiget.addWidget(self.open_box)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_report)
        self.layout_wiget.addWidget(self.save_button)

        self.wiget = QWidget()
        self.wiget.setLayout(self.layout_wiget)
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setWidget(self.wiget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.area)

    def _create_EGE_UI(self):
        for EGE in averaged_model:
            setattr(self, f"deviator_{EGE}", DeviatorItemUI(EGE, parent=self))
            widget = getattr(self, f"deviator_{EGE}")
            self.layout_wiget.addWidget(widget)

    def plot(self):
        """Построение графиков опыта"""
        for EGE in averaged_model:
            widget = getattr(self, f"deviator_{EGE}")
            widget.plot()

    def load_model(self):
        try:
            model_file = self._model_file()

            if os.path.exists(model_file):
                averaged_model.load(model_file)
            else:
                averaged_model.set_data()
        except:
            pass

    def save_model(self):
        model_file = self._model_file()
        averaged_model.dump(model_file)

    def info(self):
        text = '''
МОДУЛЬ УСРЕДНЕНИЯ ДЕВИАТОРНЫХ КРИВЫХ
        
Алгоритм:
Кривые берутся из модели. Максимальная деформация усредненной кривой берется функцией максимума от самой длинной кривой с пиком, либо 0.1. Для усреднения все кривые с пиком продляются до максимальной деформации из точки пика, а кривые без пика обрезаются до значения максимальной деформации.
        '''
        self.info = Info(text)

    def statment_button_click(self):
        path = QFileDialog.getOpenFileName(self, 'Open file')[0]
        if path != "":
            try:
                averaged_statment.setExcelFile(path)
                averaged_model.set_data()
                self.statment_line.setText("")
                self.load_model()
                self._create_EGE_UI()
                self.plot()
                self.statment_line.setText(path)
            except Exception as error:
                self.statment_line.setText("")
                QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

    def _model_file(self):
        if statment.general_data.shipment_number:
            shipment_number = f" - {statment.general_data.shipment_number}"
        else:
            shipment_number = ""

        return os.path.join(statment.save_dir.save_directory, "plaxisAvereged" + shipment_number + ".pickle")

    def save_report(self):
        try:
            dir = os.path.split(averaged_statment.excel_path)[0]

            file_name = dir + "/" + "Отчет по усреднению девиаторных нагружений.pdf"

            data = {key: averaged_model[key].get_results() for key in averaged_model}

            averaged_statment_data = averaged_statment.getAvarange()


            for EGE in data:
                widget = getattr(self, f"deviator_{EGE}")
                data[EGE]["pick"] = widget.save_canvas()
                data[EGE]['averaged_statment_data'] = averaged_statment_data[EGE]

            report_averaged(
                file_name=file_name,
                data_customer=statment.general_data,
                path=os.getcwd() + "/project_data/",
                data=data,
                version=actual_version,
                qr_code=None)

            self.save_model()

            averaged_model.save_plaxis(os.path.join(dir, "plaxis_averaged_curves"))

            averaged_statment.save_excel()

            QMessageBox.about(self, "Сообщение", f"Отчет успешно сохранен: {file_name}")
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #averaged_statment.setExcelFile(r"C:\Users\Пользователь\Desktop\Новая папка (3)\1.xls")
    E_models.load(r"C:\Users\Пользователь\Desktop\Новая папка (3)\Трёхосное сжатие (E)\E_models - 1.0.pickle")
    #averaged_model.set_data()
    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = AverageWidget()
    ex.show()
    sys.exit(app.exec_())