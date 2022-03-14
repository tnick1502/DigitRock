from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressDialog, QPushButton
import threading
import time
import sys
import socket
import pickle

BUFFER_SIZE = 1024

def send_to_server(port, data):
    if port:
        sock = socket.socket()
        sock.connect(('localhost', port))
        sock.sendall(pickle.dumps(data))
        sock.close()
    else:
        pass


class MyProgress(QProgressDialog):
    def __init__(self, port, parent=None):
        super().__init__("", "", 0, 100, parent=parent)
        self.setCancelButton(None)
        self.setValue(0)
        self.port = port
        self.setGeometry(500, 400, 300, 80)
        threading.Thread(target=self.run, args=()).start()
        self.show()

    def run(self):
        sock = socket.socket()
        sock.bind(('', self.port))
        sock.listen(5)
        while True:
            conn, addr = sock.accept()
            all_data = bytearray()
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                all_data += data

            data = pickle.loads(all_data)

            if data.get("label", None):
                self.setLabelText(data["label"])

            if data.get("window_title", None):
                self.setWindowTitle(data["window_title"])

            if data.get("maximum", None):
                self.setMaximum(data["maximum"])

            if data.get("value", None):
                self.setValue(data["value"])

            if data.get("break", None):
                conn.close()
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
        self.port = 5000
        self.show()

    def press(self):
        def s(port):
            send_to_server(port, {"window_title": "Процесс ..."})
            send_to_server(port, {"label": "Процесс ..."})
            send_to_server(port, {"maximum": 5})

            for i in range(5):
                time.sleep(1)
                send_to_server(port, {"value": i + 1})

            send_to_server(port, {"break": True})

        self.progress = MyProgress(port=self.port)
        threading.Thread(target=s, args=(self.port,)).start()
        self.port += 1


if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    progress = App()
    sys.exit(app.exec_())