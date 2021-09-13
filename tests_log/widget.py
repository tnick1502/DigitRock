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

from general.initial_tables import Table, Table_Castomer
from general.general_widgets import Float_Slider
from general.general_functions import read_json_file, create_json_file
from configs.styles import style
from general.report_general_statment import save_report
from general.excel_data_parser import dataToDict, dictToData, CyclicData
from general.initial_tables import Table_Castomer



class TestsLogWidget(QWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self):
        super().__init__()
        self.createIU()

    def createIU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        self.box_statment = QGroupBox("Ведомость")
        self.box_statment.setFixedHeight(150)
        self.box_statment_layout = QGridLayout()
        self.box_statment.setLayout(self.box_statment_layout)
        self.box_statment_open_button = QPushButton("Выбрать ведомость")
        self.box_statment_path_line = QLineEdit()
        self.box_statment_path_line.setDisabled(True)
        self.box_statment_widget = Table_Castomer()
        self.box_statment_layout.addWidget(self.box_statment_open_button, 0, 0, 1, 1)
        self.box_statment_layout.addWidget(self.box_statment_path_line , 0, 1, 1, 5)
        self.box_statment_layout.addWidget(self.box_statment_widget, 1, 0, 2, 6)

        self.box_test_path = QGroupBox("Папка с опытами")
        self.box_test_path.setFixedHeight(70)
        self.box_test_path_layout = QGridLayout()
        self.box_test_path.setLayout(self.box_test_path_layout)
        self.box_test_path_open_button = QPushButton("Выбрать папку с опытами")
        self.box_test_path_path_line = QLineEdit()
        self.box_test_path_path_line.setDisabled(True)
        self.box_statment_widget = Table_Castomer()
        self.box_test_path_layout.addWidget(self.box_test_path_open_button, 0, 0, 1, 1)
        self.box_test_path_layout.addWidget(self.box_test_path_path_line, 0, 1, 1, 5)


        self.layout.addWidget(self.box_statment)
        self.layout.addWidget(self.box_test_path)




if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = TestsLogWidget()
    ex.show()
    sys.exit(app.exec_())
