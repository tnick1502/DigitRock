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



class TestsLogWidget(QWidget):
    """Класс отрисовывает таблицу физических свойств"""
    def __init__(self, data, data_customer):
        super().__init__()
        self.createIU()

    def createIU(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.box_statment = QGroupBox("Ведомость")
        self.box_statment_layout = QGridLayout()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = CyclicLoadingUISoilTest()
    ex.show()
    sys.exit(app.exec_())
