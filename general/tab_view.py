#!/usr/bin/env python
# -.- coding: utf-8 -.-
import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class TabMixin(QtWidgets.QWidget):
    popOut = QtCore.pyqtSignal(QtWidgets.QWidget)
    popIn = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, parent=None):
        super(TabMixin, self).__init__(parent)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        pop_out = menu.addAction('Открыть окно')
        pop_in = menu.addAction('Свернуть окно')
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == pop_out:
            self.popOut.emit(self)
        elif action == pop_in:
              self.popIn.emit(self)

    def closeEvent(self, evnt):
        self.popIn.emit(self)


class AppMixin(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AppMixin, self).__init__()

    def addTab(self, widget):
        if self.tab_widget.indexOf(widget) == -1:
            widget.setWindowFlags(QtCore.Qt.Widget)
            self.tab_widget.addTab(widget, widget.windowTitle())

    def removeTab(self, widget):
        index = self.tab_widget.indexOf(widget)

        tabBar = self.tab_widget.tabBar()
        title = str(tabBar.tabText(index))

        if index != -1:
            self.tab_widget.removeTab(index)
            widget.setWindowFlags(QtCore.Qt.Window)
            widget.setWindowTitle(title)
            widget.move(50, 50)
            widget.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    w = Window()
    w.show()

    sys.exit(app.exec_())