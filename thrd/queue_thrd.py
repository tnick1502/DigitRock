from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressDialog, QPushButton
import threading
import time
import sys
from queue import Empty, Queue
#queue_interface = Queue()

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class QueueInterface(Queue, metaclass=Singleton):
    pass

queue_interface = QueueInterface()

class MyProgress(QProgressDialog):
    def __init__(self, parent=None):
        super().__init__("", "", 0, 100, parent=parent)
        self.setCancelButton(None)
        self.setValue(0)
        self.setGeometry(500, 400, 300, 80)
        self.show()

    def run(self):
        while True:
            time.sleep(0.1)
            try:
                data = queue_interface.get(block=False)
            except Empty:
                pass
            else:
                if data.get("label", None):
                    self.setLabelText(data["label"])

                if data.get("window_title", None):
                    self.setWindowTitle(data["window_title"])

                if data.get("maximum", None):
                    self.setMaximum(data["maximum"])

                if data.get("value", None):
                    self.setValue(data["value"])

                if data.get("break", None):
                    break
        self.close()
        return

class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.left = 1000
        self.top = 500
        self.width = 100
        self.height = 100
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.button = QPushButton("Press")
        self.button.clicked.connect(self.press)
        self.setCentralWidget(self.button)
        self.show()

    def press(self):
        def s():
            queue_interface.put({"window_title": "Процесс ..."})
            queue_interface.put({"label": "Процесс ..."})
            queue_interface.put({"maximum": 50})

            for i in range(50):
                time.sleep(0.1)
                queue_interface.put({"value": i + 1})

            queue_interface.put({"break": True})
            return

        self.progress = MyProgress()
        thr1 = threading.Thread(target=s, args=())
        thr2 = threading.Thread(target=self.progress.run, args=())
        thr1.start()
        thr2.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    progress = App()
    sys.exit(app.exec_())