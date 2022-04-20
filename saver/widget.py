from thrd.socket_thd import MyProgress
from PyQt5.QtWidgets import QApplication, QMessageBox
from saver.savers_models import SaverModel
import threading
import sys

class XMLWidget(MyProgress):  # Окно и виджеты на нем

    def __init__(self, dir):
        self._port = 50505
        try:
            MyProgress.__init__(self, port=self._port)
            self._model = SaverModel(dir, port=self._port)
        except AssertionError as error:
            self.close()
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
        else:
            self.run_process()

    def run_process(self):
        threading.Thread(target=self._model.process, args=()).start()