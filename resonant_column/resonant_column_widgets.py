from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QMessageBox
import numpy as np
import sys

from resonant_column_widgets_UI import RezonantColumnUI, RezonantColumnOpenTestUI
from rezonant_column_hss_model import ModelRezonantColumn

class RezonantColumnProcessingWidget(QWidget):
    """Виджет для открытия и обработки файла прибора"""
    def __init__(self):
        """Определяем основную структуру данных"""
        super().__init__()
        self._model = ModelRezonantColumn()
        self._create_Ui()
        #self.open_widget.button_open_file.clicked.connect(self._open_file)
        self.open_widget.button_open_path.clicked.connect(self._open_path)
        self.test_processing_widget.cut_slider.sliderMoved.connect(self._cut_sliders_moove)

    def _create_Ui(self):
        self.layout = QVBoxLayout(self)
        self.open_widget = RezonantColumnOpenTestUI()
        self.open_widget.setFixedHeight(100)
        self.layout.addWidget(self.open_widget)
        self.test_processing_widget = RezonantColumnUI()
        self.layout.addWidget(self.test_processing_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _cut_sliders_moove(self):
        if self._model._test_data.G_array is not None:
            self._model.set_borders(int(self.test_processing_widget.cut_slider.low()),
                                                        int(self.test_processing_widget.cut_slider.high()))
            self._plot()

    def _cut_slider_set_len(self, len):
        """Определение размера слайдера. Через длину массива"""
        self.test_processing_widget.cut_slider.setMinimum(0)
        self.test_processing_widget.cut_slider.setMaximum(len)
        self.test_processing_widget.cut_slider.setLow(0)
        self.test_processing_widget.cut_slider.setHight(len)

    def _open_path(self):
        """Открытие файла опыта"""
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.open_widget.set_file_path("")
            self._plot()
            try:
                self._model.open_path(path)
                try:
                    self._cut_slider_set_len(len(self._model._test_data.G_array))
                except:
                    pass
                self.open_widget.set_file_path(path)
            except (ValueError, IndexError, FileNotFoundError):
                pass
            self._plot()

    def _plot(self):
        """Построение графиков опыта"""
        plots = self._model.get_plot_data()
        res = self._model.get_test_results()
        self.test_processing_widget.plot(plots, res)



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = RezonantColumnProcessingWidget()
    ex.show()
    sys.exit(app.exec_())