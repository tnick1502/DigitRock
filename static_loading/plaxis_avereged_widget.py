from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout, QGroupBox, QWidget, QScrollArea, \
    QTableWidgetItem, QRadioButton, QButtonGroup
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import sys
import os

from excel_statment.initial_tables import TableVertical
from general.general_functions import read_json_file
from static_loading.plaxis_averaged_model import AveragedStatment

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))
plt.style.use('bmh')

model = AveragedStatment()

class ResultTable(TableVertical):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        fill_keys = {
            "averaged_E50": "Модуль деформации E50, кПа",
            "averaged_qf": "Максимальный девиатор qf, кПа",
            "averaged_Eur": "Модуль повторного нагружения, МПа",
            "averaged_c": "Сцепление с, МПа",
            "averaged_fi": "Угол внутреннего трения, град",
            "averaged_poissons_ratio": "Коэффициент Пуассона",
            "averaged_dilatancy_angle": "Угол дилатансии, град",
        }
        super().__init__(fill_keys=fill_keys, size={"size": 100, "size_fixed_index": [1]})

    def set_data(self, data: dict):
        """Получение данных, Заполнение таблицы параметрами"""
        self._clear_table()

        replaceNone = lambda x: str(x) if x is not None else "-"

        for i, key in enumerate(self._fill_keys):
            attr = replaceNone(data.get(key, None))
            self.setItem(i, 1, QTableWidgetItem(attr))

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
        self.param_radio_button_1 = QRadioButton('Секторальная разбивка')
        self.param_radio_button_1.param_type = 'sectors'
        self.param_radio_button_2 = QRadioButton('Полином')
        self.param_radio_button_1.param_type = 'poly'
        if model[self.EGE].approximate_type == 'sectors':
            self.param_radio_button_1.setChecked(True)
        elif model[self.EGE].approximate_type == 'poly':
            self.param_radio_button_2.setChecked(True)
        self.param_button_group = QButtonGroup()
        self.param_button_group.addButton(self.param_radio_button_1)
        self.param_button_group.addButton(self.param_radio_button_2)
        self.param_button_group.buttonClicked.connect(self.radio_button_clicked)
        self.param_box_layout.addWidget(self.param_radio_button_1, 1)
        self.param_box_layout.addWidget(self.param_radio_button_2, 2)

        self.results_box = QGroupBox("Результаты обработки")
        self.results_box.setFixedHeight(200)
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
        self.results_table.set_data(model[self.EGE].get_results())

        plot_data = model[self.EGE].get_plot_data()

        for key in plot_data:
            if key == "averaged":
                if plot_data[key]["strain"] is not None:
                    self.plot_ax.plot(
                        plot_data[key]["strain"], plot_data[key]["deviator"],
                        label=key, linewidth=3, linestyle="-")
            else:
                self.plot_ax.plot(
                    plot_data[key]["strain"], plot_data[key]["deviator"],
                    label=key, linewidth=1, linestyle="-", alpha=0.6)

        self.plot_ax.legend()
        self.plot_canvas.draw()

    def radio_button_clicked(self, obj):
        if self.param_button_group.id(obj) == -3:
            model[self.EGE].set_approximate_type("poly")
        elif self.param_button_group.id(obj) == -2:
            model[self.EGE].set_approximate_type("sectors")
        self.plot()

class AverageWidget(QGroupBox):
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        model.__init__()
        self._create_UI()
        self.plot()
        self.setMinimumHeight(800)
        self.setMinimumWidth(1200)

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout_wiget = QVBoxLayout()

        for EGE in model:
            setattr(self, f"deviator_{EGE}", DeviatorItemUI(EGE, parent=self))
            widget = getattr(self, f"deviator_{EGE}")
            self.layout_wiget.addWidget(widget)

        self.wiget = QWidget()
        self.wiget.setLayout(self.layout_wiget)
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setWidget(self.wiget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.area)

    def plot(self):
        """Построение графиков опыта"""
        for EGE in model:
            widget = getattr(self, f"deviator_{EGE}")
            widget.plot()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = DeviatorItemUI()
    ex.show()
    sys.exit(app.exec_())