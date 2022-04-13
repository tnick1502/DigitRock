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
        self.plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.22, "wspace": 0.12, "hspace": 0.07, "left": 0.12}

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
                self.ax.scatter(plots["frequency"], plots["damping_ratio"], s=10, color="tomato")
                self.ax.plot(plots["frequency_rayleigh"], plots["damping_rayleigh"])

                self.ax.plot([], [], label="alpha = " + str(res["alpha"]), color="#eeeeee")
                self.ax.plot([], [], label="betta = " + str(res["alpha"]), color="#eeeeee")
                self.ax.legend()
            self.canvas.draw()

        except:
            pass

    def save_canvas(self):
        """Сохранение графиков для передачи в отчет"""

        def save(figure, canvas, size_figure, file_type):
            path = BytesIO()
            size = figure.get_size_inches()
            figure.set_size_inches(size_figure)
            if file_type == "svg":
                figure.savefig(path, format='svg', transparent=True)
            elif file_type == "jpg":
                figure.savefig(path, format='jpg', dpi=200, bbox_inches='tight')
            path.seek(0)
            figure.set_size_inches(size)
            canvas.draw()
            return path

        return save(self.figure, self.canvas, [6, 4], "svg")



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = RayleighDampingUI()
    ex.show()
    sys.exit(app.exec_())
