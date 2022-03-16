from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressDialog, QPushButton
from PyQt5.QtCore import QSize, QTimer
import threading
import time
import sys
#from queue import Empty, Queue

class Empty(Exception):
    pass

class Queue(list):
    """Реализация очереди через список"""
    def __init__(self):
        self._lock = threading.Lock()

    def get(self, id=None):
        self._empty_test()
        if id:
            for i in range(len(self)):
                if self[i]["id"] == id:
                    data = self[i]
                    self.pop(i)
                    return data
            raise Empty("Queue is empty")
        else:
            data = self[0]
            self.pop(0)
            return data

    def _empty_test(self):
        """Проверка на заполненость"""
        if len(self) == 0:
            raise Empty("Queue is empty")

    def put(self, data):
        self.append(data)

queue_interface = Queue()


class MyProgress(QProgressDialog):
    def __init__(self, id=None, parent=None):
        super().__init__("", "", 0, 100, parent=parent)
        self.setCancelButton(None)
        self.setValue(0)
        self._id = id
        self.setGeometry(800, 200 + id%4*120, 300, 80)
        self.show()

    def run(self):
        while True:
            time.sleep(0.1)
            try:
                data = queue_interface.get(id=self._id)
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
        self.id = 0
        self.show()

    def press(self):
        self.id += 1
        def s(id):
            queue_interface.put({"window_title": f"Процесс {id}", "id": id})
            queue_interface.put({"label": "Процесс ...", "id": id})
            queue_interface.put({"maximum": 50, "id": id})

            for i in range(50):
                time.sleep(0.1)
                queue_interface.put({"value": i + 1, "id": id})

            queue_interface.put({"break": True, "id": id})
            return

        self.progress = MyProgress(self.id)
        thr1 = threading.Thread(target=s, args=(self.id, ))
        thr2 = threading.Thread(target=self.progress.run, args=())
        thr1.start()
        thr2.start()

app = QApplication(sys.argv)
app.setStyle('Fusion')

progress = App()
sys.exit(app.exec_())