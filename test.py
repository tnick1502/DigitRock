#!/usr/bin/env python
# -.- coding: utf-8 -.-
import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class Tab(QtWidgets.QWidget):
    popOut = QtCore.pyqtSignal(QtWidgets.QWidget)
    popIn = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)

        popOutButton = QtWidgets.QPushButton('Pop Out')
        popOutButton.clicked.connect(lambda: self.popOut.emit(self))
        popInButton = QtWidgets.QPushButton('Pop In')
        popInButton.clicked.connect(lambda: self.popIn.emit(self))

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(popOutButton)
        layout.addWidget(popInButton)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        pop_out = menu.addAction('Открыть окно')
        pop_in = menu.addAction('Свернуть окно')
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == pop_out:
            self.popOut.emit(self)
        elif action == pop_in:
              self.popIn.emit(self)


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__()

        self.button = QtWidgets.QPushButton('Add Tab')
        self.button.clicked.connect(self.createTab)
        self._count = 0
        self.tab = QtWidgets.QTabWidget()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.addWidget(self.tab)

    def createTab(self):
        tab = Tab()
        tab.setWindowTitle('%d' % self._count)
        tab.popIn.connect(self.addTab)
        tab.popOut.connect(self.removeTab)
        self.tab.addTab(tab, '%d' % self._count)
        self._count += 1

    def addTab(self, widget):
        if self.tab.indexOf(widget) == -1:
            widget.setWindowFlags(QtCore.Qt.Widget)
            self.tab.addTab(widget, widget.windowTitle())

    def removeTab(self, widget):
        index = self.tab.indexOf(widget)
        if index != -1:
            self.tab.removeTab(index)
            widget.setWindowFlags(QtCore.Qt.Window)
            widget.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    w = Window()
    w.show()

    sys.exit(app.exec_())