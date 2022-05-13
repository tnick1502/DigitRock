from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QGroupBox, QTableWidget, QDialog, \
    QComboBox, QWidget, QHeaderView, QTableWidgetItem, QFileSystemModel, QTreeView, QLineEdit, QSplitter, QPushButton, \
    QVBoxLayout, QLabel, QMessageBox, QProgressBar, QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtGui import QPainter, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
import sys
import os

from openpyxl import load_workbook
from general.excel_functions import cfe_test_type_columns, k0_test_type_column, column_fullness_test, read_customer
from general.initial_tables import TableCastomer, ComboBox_Initial_Parameters, TableVertical, TablePhysicalProperties

from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties, VibrationCreepProperties
from excel_statment.position_configs import IdentificationColumns

from loggers.logger import app_logger, log_this

from singletons import statment

class Float_Slider(QSlider):  # получает на входе размер окна. Если передать 0 то размер автоматический
    def __init__(self, m):
        super().__init__(m)
        self.slider_order = 1
        self.disabled = False

    def order(self, x):
        return 1 / x

    def set_borders(self, minimum, maximum):
        if minimum <= 0:
            self.setMinimum(0)
            self.slider_order = 100 / (maximum)
            self.setMaximum(int(maximum * self.slider_order))
        else:
            self.slider_order = max([self.order(minimum), 100 / (maximum - minimum)])
            self.setMinimum(int(minimum * self.slider_order))
            self.setMaximum(int(maximum * self.slider_order))

    def current_value(self):
        if self.disabled:
            return None
        return float(self.value()) / self.slider_order

    def set_value(self, val):
        if val:
            self.setValue(int(val * self.slider_order))
        else:
            self.setDisabled(True)


class Slider(QSlider):  # получает на входе размер окна. Если передать 0 то размер автоматический
    def __init__(self, m):
        super().__init__(m)
        self.slider_order = 1
        self.disabled = False
        self.delta = 0

    def order(self, x):
        return 1 / x

    def set_borders(self, minimum, maximum):
        if minimum == 0:
            if maximum < 0:
                self.delta = maximum
                maximum = maximum + self.delta
            self.setMinimum(0)
            self.slider_order = 100 / (maximum)
            self.setMaximum(maximum * self.slider_order)
        else:
            if minimum < 0:
                self.delta = minimum + 1
            minimum = minimum + self.delta
            maximum = maximum + self.delta
            self.slider_order = max([self.order(minimum), 100 / (maximum - minimum)])
            self.setMinimum(minimum * self.slider_order)
            self.setMaximum(maximum * self.slider_order)

    def current_value(self):
        if self.disabled:
            return None
        return float(self.value()) / self.slider_order - self.delta

    def set_value(self, val):
        val = val + self.delta
        if val:
            self.setValue(val * self.slider_order)
        else:
            self.setDisabled(True)


class RangeSlider(QSlider):
    sliderMoved = QtCore.pyqtSignal(int, int)

    """ A slider for ranges.

        This class provides a dual-slider for ranges, where there is a defined
        maximum and minimum, as is a normal slider, but instead of having a
        single slider value, there are 2 slider values.

        This class emits the same signals as the QSlider base class, with the 
        exception of valueChanged
    """

    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)

        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QStyle.SC_None
        self.tick_interval = 0
        self.tick_position = QSlider.NoTicks
        self.hover_control = QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

    def low(self):
        return self._low

    def setLow(self, low: int):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high):
        self._high = high
        self.update()

    def paintEvent(self, event):
        # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QPainter(self)
        style = QApplication.style()

        # draw groove
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.siderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QStyle.SC_SliderGroove
        if self.tickPosition() != self.NoTicks:
            opt.subControls |= QStyle.SC_SliderTickmarks
        style.drawComplexControl(QStyle.CC_Slider, opt, painter, self)
        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)

        # drawSpan
        # opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.subControls = QStyle.SC_SliderGroove
        # if self.tickPosition() != self.NoTicks:
        #    opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
        opt.siderValue = 0
        # print(self._low)
        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        # print(low_rect, high_rect)
        low_pos = self.__pick(low_rect.center())
        high_pos = self.__pick(high_rect.center())

        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)

        c = QtCore.QRect(low_rect.center(), high_rect.center()).center()
        # print(min_pos, max_pos, c)
        if opt.orientation == QtCore.Qt.Horizontal:
            span_rect = QtCore.QRect(QtCore.QPoint(min_pos, c.y() - 2), QtCore.QPoint(max_pos, c.y() + 1))
        else:
            span_rect = QtCore.QRect(QtCore.QPoint(c.x() - 2, min_pos), QtCore.QPoint(c.x() + 1, max_pos))

        # self.initStyleOption(opt)
        # print(groove.x(), groove.y(), groove.width(), groove.height())
        if opt.orientation == QtCore.Qt.Horizontal:
            groove.adjust(0, 0, -1, 0)
        else:
            groove.adjust(0, 0, 0, -1)

        if True:  # self.isEnabled():
            highlight = self.palette().color(QPalette.Highlight)
            painter.setBrush(QBrush(highlight))
            painter.setPen(QPen(highlight, 0))
            # painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Dark), 0))
            '''
            if opt.orientation == QtCore.Qt.Horizontal:
                self.setupPainter(painter, opt.orientation, groove.center().x(), groove.top(), groove.center().x(), groove.bottom())
            else:
                self.setupPainter(painter, opt.orientation, groove.left(), groove.center().y(), groove.right(), groove.center().y())
            '''
            # spanRect =
            painter.drawRect(span_rect.intersected(groove))
            # painter.drawRect(groove)

        for i, value in enumerate([self._low, self._high]):
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = QStyle.SC_SliderHandle  # | QtWidgets.QStyle.SC_SliderGroove
            else:
                opt.subControls = QStyle.SC_SliderHandle

            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
            else:
                opt.activeSubControls = self.hover_control

            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QStyle.CC_Slider, opt, painter, self)

    def mousePressEvent(self, event):
        event.accept()

        style = QApplication.style()
        button = event.button()

        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts

        if button:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit

                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos

        self.update()

        # self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)
        self.sliderMoved.emit(self._low, self._high)

    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QApplication.style()

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        return style.sliderValueFromPosition(self.minimum(), self.maximum(),
                                             pos - slider_min, slider_max - slider_min,
                                             opt.upsideDown)

if __name__ == "__main__":
    pass

class Progressbar(QWidget):
    def __init__(self, count):
        super().__init__()
        self.count = count
        self.setWindowTitle('Процесс выполнения')
        self.progressBar = QProgressBar(self)
        self.label = QLabel("Процесс выполнения: 0 из {}".format(self.count))
        layout = QVBoxLayout(self)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.label)
        self.set_params(0)

    def set_params(self, val):
        self.progressBar.setProperty("value", round(val*100/self.count))
        self.label.setText("Процесс выполнения: {} из {}".format(val, self.count))


if __name__ == "__main__":
    main = QApplication(sys.argv)
    window = Slider(Qt.Horizontal)
    window.set_borders(-10, 10)
    window.set_value(0)

    def on_move():
        print(window.current_value())
    window.sliderMoved.connect(on_move)
    # timer = QtCore.QTimer()
    #
    # def h():
    #     [i*i for i in range(1000000)]
    #
    #
    # def onTimer():
    #     for i in range(6):
    #         h()
    #         window.set_params(i)
    #
    # timer.singleShot(1000, onTimer)
    # timer.start(1000)

    window.show()
    sys.exit(main.exec_())
