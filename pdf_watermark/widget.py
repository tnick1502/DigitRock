from thrd.socket_thd import MyProgress
from PyQt5.QtWidgets import QApplication, QMessageBox
from pdf_watermark.model import WaterMarks
import threading
import sys



class PDFWatermark(MyProgress):  # Окно и виджеты на нем

    def __init__(self, dir):
        self._port = 50501
        try:
            MyProgress.__init__(self, port=self._port)
            self._model = WaterMarks(dir, port=self._port)
        except AssertionError as error:
            self.close()
            QMessageBox.critical(self, "Ошибка", str(error), QMessageBox.Ok)
        else:
            self.run_process()

    def run_process(self):
        threading.Thread(target=self._model.process, args=()).start()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    progress = PDFWatermark(r"C:\Users\Пользователь\Desktop\test\Трёхосное сжатие (F, C, E)\Трёхосное сжатие (F, C, E) - 1")
    sys.exit(app.exec_())