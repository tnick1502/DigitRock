"""Модуль графического интерфейса моделей циклического нагружения. Содердит программы:
    TriaxialCyclicLoading_Processing - Обработка циклического нагружения
    TriaxialCyclicLoading_SoilTest - модуль моделирования циклического нагружения
    """
from PyQt5.QtWidgets import QApplication, QGridLayout, QFrame, QLabel, QHBoxLayout,\
    QVBoxLayout, QGroupBox, QWidget, QLineEdit, QPushButton, QTableWidget, QDialog, QHeaderView,  QTableWidgetItem, \
    QHeaderView, QDialogButtonBox, QFileDialog, QMessageBox, QItemDelegate, QComboBox
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import os
import numpy as np
import sys
from io import BytesIO

from general.initial_tables import Table
from general.general_functions import read_json_file
from configs.plot_params import plotter_params

plt.style.use('bmh')


class RayleighDampingUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    При создании требуется выбрать модель трехосного нагружения методом set_model(model).
    Класс реализует Построение 3х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.12, "wspace": 0.12, "hspace": 0.07, "left": 0.07}

        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QHBoxLayout()
        self.graph = QGroupBox("Демпфирование по Релею")
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.graph_canvas_layout = QHBoxLayout()

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setStyleSheet('background: #ffffff')
        self.frame_layout = QVBoxLayout()
        self.figure = plt.figure()
        self.figure.subplots_adjust(**self.plot_params)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.grid(axis='both', linewidth='0.4')

        self.ax.set_xlabel("Частота, Гц")
        self.ax.set_ylabel("Коэффициент демпфирования, %")

        self.canvas.draw()
        self.frame_layout.setSpacing(0)
        self.frame_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.frame_layout.addWidget(self.toolbar)
        self.frame.setLayout(self.frame_layout)

        self.graph_canvas_layout.addWidget(self.frame)

        self.graph_layout.addLayout(self.graph_canvas_layout)

        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, res):
        """Построение графиков опыта"""
        try:
            self.ax.clear()
            self.ax.set_xlabel("Частота, Гц")
            self.ax.set_ylabel("Коэффициент демпфирования, %")

            if plots:
                self.ax.scatter(plots["frequency"], plots["damping_ratio"], s=50, color="tomato")
                self.ax.plot(plots["frequency_rayleigh"], plots["damping_rayleigh"])

                self.ax.plot([], [], label="alpha = " + str(res["alpha"]), color="#eeeeee")
                self.ax.plot([], [], label="betta = " + str(res["betta"]), color="#eeeeee")
                self.ax.legend()
            self.canvas.draw()

        except:
            pass

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, ax, file_type):
            try:
                ax.get_legend().remove()
                canvas.draw()

                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                ax.legend(loc='upper left')
                canvas.draw()
            except AttributeError:
                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                canvas.draw()
            return path

        return save(self.figure, self.canvas, [5.7, 4.75], self.ax, "jpg")

class CyclicDampingUnitUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    Класс реализует Построение 4х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    signal = pyqtSignal(object)
    def __init__(self, number=None):
        """Определяем основную структуру данных"""
        super().__init__()

        # Параметры построения для всех графиков
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.15, "wspace": 0.12, "hspace": 0.07, "left": 0.15}
        self.number = number
        self._create_UI()

        self.setFixedHeight(320)
        self.setFixedWidth(300)

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QVBoxLayout()
        self.graph = QGroupBox()
        self.graph_layout = QVBoxLayout()
        self.graph.setLayout(self.graph_layout)

        self.deviator_frame = QFrame()
        self.deviator_frame.setFrameShape(QFrame.StyledPanel)
        self.deviator_frame.setStyleSheet('background: #ffffff')
        self.deviator_frame_layout = QVBoxLayout()
        self.deviator_figure = plt.figure()
        self.deviator_figure.subplots_adjust(**self.plot_params)
        self.deviator_canvas = FigureCanvas(self.deviator_figure)
        self.deviator_ax = self.deviator_figure.add_subplot(111)
        self.deviator_ax.grid(axis='both', linewidth='0.4')
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, кПа")

        self.deviator_canvas.draw()
        self.deviator_frame_layout.setSpacing(0)
        self.deviator_frame_layout.addWidget(self.deviator_canvas)
        self.deviator_frame.setLayout(self.deviator_frame_layout)

        self.graph_layout.addWidget(self.deviator_frame)
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setFixedHeight(20)
        self.graph_layout.addWidget(self.refresh_button)
        self.refresh_button.clicked.connect(lambda : self.signal.emit(self.number))
        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, results):
        """Построение графиков опыта"""

        self.deviator_ax.clear()
        self.deviator_ax.set_xlabel("Относительная деформация $ε_1$, д.е.")
        self.deviator_ax.set_ylabel("Девиатор q, кПа")

        self.deviator_ax.plot(plots["strain"], plots["deviator"])

        if plots["damping_strain"] is not None:
            self.deviator_ax.fill(plots["damping_strain"], plots["damping_deviator"],
                                  color="tomato", alpha=0.5, zorder=5)

            self.deviator_ax.plot([], [], label="ζ, %" + ", д.е. = " + str(results["damping_ratio"]),
                                       color="#eeeeee")


        self.deviator_ax.legend(loc='upper left')

        self.deviator_canvas.draw()

    def save_canvas(self, format_="svg"):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, ax, file_type):
            try:
                ax.get_legend().remove()
                canvas.draw()

                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                ax.legend(loc='upper left')
                canvas.draw()
            except AttributeError:
                path = BytesIO()
                size = figure.get_size_inches()
                figure.set_size_inches(size_figure)
                if file_type == "svg":
                    figure.savefig(path, format='svg', transparent=True)
                elif file_type == "jpg":
                    figure.savefig(path, format='jpg', dpi=500, bbox_inches='tight')
                path.seek(0)
                figure.set_size_inches(size)
                canvas.draw()
            return path

        if format_ == "jpg":
            import matplotlib as mpl
            mpl.rcParams['agg.path.chunksize'] = len(self.model._test_data.cycles)
            format = 'jpg'
        else:
            format = 'svg'

        return save(self.deviator_figure, self.deviator_canvas, [5, 4.75], self.deviator_ax, "jpg")

class CyclicDampingUI(QWidget):
    """Интерфейс обработчика циклического трехосного нагружения.
    Класс реализует Построение 4х графиков опыта циклического разрушения, также таблицы результатов опыта."""
    signal = pyqtSignal(object)
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._create_UI()

    def _create_UI(self):
        """Создание данных интерфейса"""
        self.layout = QHBoxLayout()
        for i in range(5):
            setattr(self, f"test_{i+1}", CyclicDampingUnitUI(i))
            test = getattr(self, f"test_{i+1}")
            self.layout.addWidget(test)
            test.signal[object].connect(lambda x: self.signal.emit(x))

        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)

    def plot(self, plots, results):
        """Построение графиков опыта"""
        for i, plot, result in zip(range(5), plots, results):
            test = getattr(self, f"test_{i + 1}")
            test.plot(plot, result)

    def save_canvas(self, format_="svg"):
        """Сохранение графиков для передачи в отчет"""
        canvases = []
        for i in range(5):
            test = getattr(self, f"test_{i + 1}")
            canvases.append(test.save_canvas())
        return canvases



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicDampingUI()
    ex.show()
    sys.exit(app.exec_())
