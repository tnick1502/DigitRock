#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from PyQt5.QtWidgets import QWidget, QApplication, QFileSystemModel, QTreeView, QLabel, QLineEdit, QGridLayout, \
    QVBoxLayout, QPushButton, QCompleter


class BackupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dir = r'Z:/DigitRock Models Backup/'
        self.pathRoot = self.dir

        self.interface()

    def interface(self):

        self.model = QFileSystemModel(self)

        self.model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.model.setRootPath(self.pathRoot)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.treeView = QTreeView(self)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.indexRoot)
        self.treeView.clicked.connect(self.on_treeView_clicked)

        self.treeView.hideColumn(1)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)
        self.treeView.setSortingEnabled(True)

        # self.labelFileName = QLabel(self)
        # self.labelFileName.setText("File Name:")

        # self.lineEditFileName = QLineEdit(self)

        # self.labelFilePath = QLabel(self)
        # self.labelFilePath.setText("File Path:")

        self.label_object = QLabel(self)
        self.label_object.setText('Object:')
        self.line2 = QLineEdit(self)
        self.line2.setReadOnly(True)

        self.label_model = QLabel(self)
        self.label_model.setText('Model:')
        self.line3 = QLineEdit(self)
        self.line3.setReadOnly(True)

        self.label_date = QLabel(self)
        self.label_date.setText('Date:')
        self.line4 = QLineEdit(self)
        self.line4.setReadOnly(True)

        self.Btn_Open = QPushButton(self)
        self.Btn_Open.setText("Open")
        self.Btn_Open.clicked.connect(self.open_btn)

        self.label_search = QLabel(self)
        self.label_search.setText('Search:')
        self.txt_search = QLineEdit(self)
        self.txt_search.textChanged[str].connect(self.onChanged2)
        self.txt_search.returnPressed.connect(self.onChanged)

        # self.lineEditFilePath = QLineEdit(self)

        self.gridLayout = QGridLayout()
        # self.gridLayout.addWidget(self.labelFileName, 0, 0)
        # self.gridLayout.addWidget(self.lineEditFileName, 0, 1)
        # self.gridLayout.addWidget(self.labelFilePath, 1, 0)
        # self.gridLayout.addWidget(self.lineEditFilePath, 1, 1)
        self.gridLayout.addWidget(self.label_search, 2, 0)
        self.gridLayout.addWidget(self.txt_search, 2, 1)

        self.gridLayout2 = QGridLayout()
        self.gridLayout2.addWidget(self.treeView, 0, 0)

        self.gridLayout3 = QGridLayout()
        self.gridLayout3.addWidget(self.label_object, 0, 2)
        self.gridLayout3.addWidget(self.line2, 0, 3)
        self.gridLayout3.addWidget(self.label_model, 1, 2)
        self.gridLayout3.addWidget(self.line3, 1, 3)
        self.gridLayout3.addWidget(self.label_date, 2, 2)
        self.gridLayout3.addWidget(self.line4, 2, 3)

        self.gridLayout3.addWidget(self.Btn_Open, 4, 3)

        self.gridLayout2.addLayout(self.gridLayout3, 0, 1)

        self.root_folder = [f.path for f in os.scandir(self.dir) if f.is_dir()]

        self.layout_left = QVBoxLayout(self)
        self.layout_left.addLayout(self.gridLayout)
        self.layout_left.addLayout(self.gridLayout2)
        self.comp = []

    def _accept_index(self, idx):
        if idx.isValid():
            text = idx.data(QtCore.Qt.DisplayRole)
            if self.filterRegExp().indexIn(text) >= 0:
                return True
            for row in range(idx.model().rowCount(idx)):
                if self._accept_index(idx.model().index(row, 0, idx)):
                    return True

        return False

    def filterAcceptsRow(self, sourceRow, sourceParent):
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self._accept_index(idx)

    def onChanged2(self, text):
        if self.txt_search.text() == "":
            self.model.setRootPath(self.dir)
            self.indexRoot = self.model.index(self.model.rootPath())

            self.treeView.setModel(self.model)

            self.treeView.setRootIndex(self.indexRoot)
        finders = []

        for i in range(len(self.root_folder)):
            self.root_folder[i] = str(self.root_folder[i]).split("/")[-1]
            if self.txt_search.text() in self.root_folder[i] and self.txt_search.text() != "":
                finders.append(self.root_folder[i])
        completer = QCompleter(finders)

        if text in finders:

            pass
        else:
            if self.comp == []:
                completer.setFilterMode(Qt.MatchContains)
                self.txt_search.setCompleter(completer)
                self.comp.append(completer)
            if self.comp[-1] == completer:
                pass
            else:

                completer.setFilterMode(Qt.MatchContains)
                self.txt_search.setCompleter(completer)
                self.comp.append(completer)

    def onChanged(self):
        finders = []
        filter = []
        backup_folderroot = self.dir
        backup_pathroot = self.pathRoot
        id = []
        for i in range(len(self.root_folder)):
            self.root_folder[i] = str(self.root_folder[i]).split("/")[-1]
            if self.txt_search.text() in self.root_folder[i] and self.txt_search.text() != "":
                finders.append(self.root_folder[i])
                id.append(i)
                filter.append("*." + self.root_folder[i])
                self.pathRoot = self.dir + finders[0]
                print(self.dir + finders[0])

        # print(finders)
        # print(filter)

        self.model = QFileSystemModel(self)

        self.model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)

        self.model.setRootPath(self.dir)
        if self.txt_search.text() == "":
            self.model.setRootPath(self.dir)
        else:
            self.model.setRootPath(self.pathRoot)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.treeView.setModel(self.model)

        self.treeView.setRootIndex(self.indexRoot)

    def open_btn(self):
        if self.line4.text() != "":
            os.startfile(self.dir + self.lvl1 + "/" + self.lvl2 + "/" + self.lvl3)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_treeView_clicked(self, index):
        self.line2.setText("")
        self.line3.setText("")
        self.line4.setText("")
        indexItem = self.model.index(index.row(), 0, index.parent())
        self.informer(self.dir, self.model.filePath(indexItem))

        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)

        # self.lineEditFileName.setText(fileName)
        # self.lineEditFilePath.setText(filePath)

    def informer(self, dir_root, path_index):

        self.index_path = path_index.replace(dir_root, "")
        if self.index_path.count('/') >= 2:
            self.lvl1, self.lvl2, self.lvl3 = self.index_path.split("/")[0], self.index_path.split("/")[1], \
                                              self.index_path.split("/")[2]
            self.line2.setText(self.lvl1)
            self.line3.setText(self.lvl2)
            self.line4.setText(self.lvl3)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName('BackUp')

    main = BackupWidget()
    main.resize(666, 333)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())