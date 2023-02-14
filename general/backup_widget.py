import sys
import subprocess

from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QTreeView, QHBoxLayout, QApplication, QLabel, QLineEdit, QVBoxLayout, QCompleter, \
    QPushButton

import os
from sys import platform

class DictForQTreeView():
    global DirPath, TakeSubfolders, BuildingAnArraySkeleton, SortingAnArray, Sorting_1lvl_main, Sorting_2lvl_Sub, Sorting_3lvl_SubSub, CreatingTheFinalDictionary, CreatingADictionaryForTheFinalDictionary
    def pather():
        if platform == "linux" or platform == "linux2":
            DirPath = "/home/drawmang/disk-z/DigitRock Models Backup/"
        elif platform == "win32":
            DirPath = "Z:\\DigitRock Models Backup\\"
        return DirPath

    DirPath = pather()

    def TakeSubfolders(folder_path) -> list:


        LVLmain = [f.path for f in os.scandir(folder_path) if f.is_dir()]

        return LVLmain

    def BuildingAnArraySkeleton():

        Dir_1lvl_main = TakeSubfolders(DirPath)
        Dir_2lvl_sub = []
        Dir_3lvl_subsub = []

        for i in range(len(Dir_1lvl_main)):
            Dir_2lvl_sub.append(TakeSubfolders(Dir_1lvl_main[0]))


            for i2 in range(len(Dir_2lvl_sub[i])):
                Dir_3lvl_subsub.append(TakeSubfolders(Dir_2lvl_sub[i][i2]))

        return Dir_1lvl_main, Dir_2lvl_sub, Dir_3lvl_subsub

    def SortingAnArray():
        MainPath, Sub_path, Subsub_path = BuildingAnArraySkeleton()

        sorting_main = Sorting_1lvl_main(MainPath)
        sorting_sub = Sorting_2lvl_Sub(Sub_path)
        sorting_sub_sub = Sorting_3lvl_SubSub(Subsub_path)

        return sorting_main, sorting_sub, sorting_sub_sub

    def Sorting_1lvl_main(main):
        temp = []

        for i in range(len(main)):
            if platform == "linux" or platform == "linux2":
                temp.append(str(main[i]).split("/")[-1])
            elif platform == "win32":
                temp.append(str(main[i]).split("\\")[-1])

        Folder_name = temp

        return Folder_name

    def Sorting_2lvl_Sub(sub):
        arr = []

        for i in range(len(sub)):
            temp = []
            for i2 in range(len(sub[i])):
                if platform == "linux" or platform == "linux2":
                    temp.append(str(sub[i][i2]).split("/")[-1])
                elif platform == "win32":
                    temp.append(str(sub[i][i2]).split("\\")[-1])
            arr.append(temp)

        return arr

    def Sorting_3lvl_SubSub(subsub):
        arr_subsub = []

        for i in range(len(subsub)):
            temp = []
            for i2 in range(len(subsub[i])):
                if platform == "linux" or platform == "linux2":
                    temp.append(str(subsub[i][i2]).split("/")[-1])
                elif platform == "win32":
                    temp.append(str(subsub[i][i2]).split("\\")[-1])
            arr_subsub.append(temp)

        return arr_subsub

    def SortingSubsubForSub(subsub, lensub, inter):
        subsub_for_sub = []

        for i in range(lensub):
            subsub_for_sub.append(subsub[i + inter])

        return subsub_for_sub

    def CreatingADictionaryBasedOnSkeletonSorting():
        main, sub, subsub = SortingAnArray()
        dict_main = CreatingTheFinalDictionary(dict_main={}, main=main, sub=sub, subsub=subsub)
        print(dict_main)
        return dict_main

    def CreatingTheFinalDictionary(dict_main, main, sub, subsub,):
        sub_main = CreatingADictionaryForTheFinalDictionary(sub, subsub)
        dict_main = dict.fromkeys(main, sub_main)

        return dict_main

    def CreatingADictionaryForTheFinalDictionary(sub, subsub):
        submain = {}
        for i in range(len(sub)):
            for i2 in range(len(sub[i])):
                submain[str(sub[i][i2])] = subsub[i2]

        return submain

class TreeView(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        layout_main = QHBoxLayout(self)
        layout_main_right = QVBoxLayout(self)
        layout_main_left = QVBoxLayout(self)
        layout_main_left_search = QVBoxLayout(self)
        layout_main_right_buttons = QHBoxLayout(self)
        self.root_path = DictForQTreeView.pather()
        self.tree = DictForQTreeView.CreatingADictionaryBasedOnSkeletonSorting()

        backup_treeview_data = self.tree

        self.treeView = QTreeView(self)
        self.treeView.clicked.connect(self.Item_click)

        self.label_search = QLabel(self)
        self.label_search.setText('Search:')
        self.txtbox_search = QLineEdit(self)
        self.txtbox_search.textChanged.connect(self.onChanged)
        self.txtbox_search.setCompleter(QCompleter(backup_treeview_data))

        self.label_object = QLabel(self)
        self.label_object.setText('Object:')
        self.line2 = QLineEdit(self)
        self.line2.setReadOnly(True)

        self.Btn_Open = QPushButton(self)
        self.Btn_Open.setText("Open")
        self.Btn_Open.clicked.connect(self.open_btn)
        #self.btn_OK = QPushButton(self)
        #self.btn_OK.setText("OK")

        layout_main_right_buttons.addWidget(self.Btn_Open)
        #layout_main_right_buttons.addWidget(self.btn_OK)

        self.label_model = QLabel(self)
        self.label_model.setText('Model:')
        self.line3 = QLineEdit(self)
        self.line3.setReadOnly(True)

        self.label_date = QLabel(self)
        self.label_date.setText('Date:')
        self.line4 = QLineEdit(self)
        self.line4.setReadOnly(True)

        layout_main.addLayout(layout_main_left)
        layout_main.addLayout(layout_main_right)
        layout_main.addLayout(layout_main)

        layout_main_right.addWidget(self.label_object)
        layout_main_right.addWidget(self.line2)
        layout_main_right.addWidget(self.label_model)
        layout_main_right.addWidget(self.line3)
        layout_main_right.addWidget(self.label_date)
        layout_main_right.addWidget(self.line4)
        layout_main_right.addLayout(layout_main_right_buttons)

        layout_main_left_search.addWidget(self.label_search)
        layout_main_left_search.addWidget(self.txtbox_search)
        layout_main_left.addLayout(layout_main_left_search)
        layout_main_left.addWidget(self.treeView)
        layout_main_left.addLayout(layout_main_left)

        self.root_model = QStandardItemModel()
        self.treeView.setModel(self.root_model)
        self._populateTree(self.tree, self.root_model.invisibleRootItem())

    def open_btn(self):
        if self.line2.text() and self.line3.text() and self.line4.text():
            path = os.path.join(DictForQTreeView.pather(), self.line2.text(), self.line3.text(), self.line4.text())
            os.startfile(path)


    def onChanged(self):

        _backup = self.tree
        self.root_model = QStandardItemModel()
        self.tree = {key: val for key, val in _backup.items() if self.txtbox_search.text() in key}
        self.treeView.setModel(self.root_model)
        self._populateTree(self.tree, self.root_model.invisibleRootItem())

        self.tree = _backup

    def Item_click(self,*args):
        for index in self.treeView.selectedIndexes():
            data = "/" + index.data()

            while index.parent().isValid():

                index = index.parent()
                data = "/" + index.data() + data

            data=data.split("/")

            del data[0]
            self.line2.setText("")
            self.line3.setText("")
            self.line4.setText("")

            if len(data) <= 3:

                for i in range(len(data)):

                    code = """self.line{NUMB}.setText(data[{INDEX}])"""
                    code = code.replace("{NUMB}",str(i+2))
                    code = code.replace("{INDEX}",str(i))

                    exec(code)


    def _populateTree(self, children, parent):

        for child in sorted(children):

            child_item = QStandardItem(child)
            parent.appendRow(child_item)

            if isinstance(children, dict):

                self._populateTree(children[child], child_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = TreeView()
    main.show()
    sys.exit(app.exec_())