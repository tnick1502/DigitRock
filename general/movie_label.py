import pickle
import socket
import sys
import threading

from PyQt5.QtCore import Qt, QByteArray, QObject, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QDialog,\
    QDesktopWidget
from PyQt5.QtGui import QMovie

from typing import Tuple

# Для примера
import numpy
# Для примера
gifFile = "loading.gif"


class MovieObject(QObject):
    """
    Базовый класс, представляющий собой объект с добавленным в него `QMovie`.
    Необходим для создания различных вариантов двигающихся объектов, например, `QLable` с gif

    Атрибуты
    ----------
    object: QObject
        Объект `QObject`, который устанавливается при помощи `set_object`

    Методы
    -------
    set_object(movie_object: 'QObject')
        Устанавливает объект `QObject`
    set_scaled_size(width: int, height: int)
        Изменяет размер `QMovie`
    restart()
        Перезапускает `QMovie`
    get_movie()
        Повращает текущий `QMovie`
    """

    def __init__(self, movie_file: str, parent: 'QObject' = None):
        """
        Инициализирует QObject, QMovie

        :param movie_file: Путь к файлу
        :param parent: (опционально) родитель для элемента. Влияет на относительное расположение `self`
        """
        # Инициализация родителя
        super().__init__()

        # Создаем экземпляр объекта, который заменится наследником через `set_object`.
        self.object: 'QObject' = QObject(parent)

        # Задаем основные параметры

        # Файл анимации
        self.movie_file = movie_file
        # Все видео, gif и т.п. в QT задаются через QMovie
        self.movie = QMovie(self.movie_file, QByteArray(), parent)
        # Получаем исходный размер картинки
        self.size = self.movie.scaledSize()

        # Параметр кэширования выставляем на "Полностью", чтобы можно было зацикливать анимацию
        self.movie.setCacheMode(QMovie.CacheAll)

        # Запускаем
        self.movie.start()
        self.movie.setPaused(False)

    def set_object(self, movie_object: 'QObject'):
        """Устанавливает действующий объект для класса"""
        self.object = movie_object
        self.object.setMovie(self.movie)

    def set_scaled_size(self, width: int, height: int):
        """
        Устанавливает размеры для QMovie и для самого класса.
        Иногда нарушается качество, так что лучше использовать картинку подходящего размера.
        """
        self.movie.setScaledSize(QSize(width, height))
        self.size = self.movie.scaledSize()
        self.object.setFixedSize(self.size)
        self.object.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # После изменения размера анимацию нужно перезапустить
        self.restart()

    def restart(self):
        """Перезапускает анимацию"""
        self.movie.stop()
        self.movie.start()

    def get_movie(self) -> 'QMovie':
        """Возвращает текущий QMovie"""
        return self.movie


class MovieLabel(MovieObject):
    """
    Класс-наследник от `MovieObject`. Используется для добавления gif. В качестве объекта выступает QLabel.
    """
    def __init__(self, gif_file: str, parent: 'QObject' = None):
        # Инициализация родителя для создания QMovie с gif
        super().__init__(gif_file, parent)
        # Создание QLabel и его подстановка в класс
        self.label = QLabel()
        self.set_object(self.label)


class Loader(QDialog):
    """
    Класс загрузчика. Реализован через `QDialog` поскольку нет необходимости в методе `run` у `QProgress`.
    Получение сообщений от async фукнций реализовано через сокеты.ъ
    Может получает сообщения однопоточно, тогда вызывает `QApplication.processEvents()` для обновления интерфейса.
    В случае не async выполнения фукнций в потоке с загрузчиком, изображение двигаться не будет.
    Может быть проинициализирован заранее, поскольку запускается отдельно методом show().

    Пример использования см. ниже в App.
    """
    # Размер буфера для сообщений socket.
    BUFFER_SIZE = 4096

    def __init__(self, start_message: 'str' = '',
                 window_title: 'str' = 'Загрузка...',
                 gif: 'str' = "./general/loading.gif",
                 message_port: 'int' = 7777,
                 modal: 'bool' = False,
                 size: Tuple['int', 'int'] = (300, 80),
                 parent: 'QWidget' = None):
        """
        Инициализация лоадера происходит отдельно от его отображения.

        :param start_message: представляет собой изначальное сообщение, которое отображает лоадер.
        :param gif: путь к файлу с gif
        :param message_port: порт обмена сообщениями
        :param modal: позволяет созать модальный лоадер, блокирующий пользование основным приложением
        :param size: размеры лоадера (на размеры gif не влияет
        :param parent: родительский элемент для Qt
        """

        super().__init__(parent)

        if modal:
            self.setWindowModality(Qt.WindowModal)

        # Отключение кнопки закрыть, поскольку другие потоки она НЕ прерывает.
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setContentsMargins(0, 0, 0, 0)
        self.width = 300
        self.height = 80
        # Окно распологаем по центру
        left = int(abs((QDesktopWidget().screenGeometry().width() - self.width) / 2.0))
        top = int(abs((QDesktopWidget().screenGeometry().height() - self.height) / 2.0))
        self.setGeometry(left, top, self.width, self.height)
        # Запрещаем изменение размера пользователем
        self.setFixedSize(self.width, self.height)

        self.setWindowTitle(str(window_title))

        # Флаг сосотояния работы лоадера, блокирует нежелательное повeдение при True
        self.__is_running = False
        # Поток для сокета
        self.__thread = None

        # Основная структура виджета
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

        # Создание Gif
        self.gif_widget = QWidget()
        self.gif_layout = QHBoxLayout()
        self.gif_widget.setLayout(self.gif_layout)

        self.gif_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_layout.setContentsMargins(0, 0, 0, 0)
        self.gif_layout.setSpacing(0)

        self.gif_label = MovieLabel(gif, self)
        self.gif_label.set_scaled_size(5*16, 5*9)
        self.gif_layout.addWidget(self.gif_label.label)
        self.layout.addWidget(self.gif_widget)

        # Текстовое сообщение
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.message_label)
        self.__set_message(start_message)

        # Задание порта и сокета для получения сообщений
        self.__port = message_port
        self.sock = socket.socket()
        self.sock.bind(('', self.port))
        self.sock.listen(10)

    def __run(self):
        """
        Запускает работу сокета по прослушиванию сообщений. Вызывается только через `show`
        """
        while self.__is_running:
            conn, addr = self.sock.accept()
            all_data = bytearray()
            while True and self.__is_running:
                data = conn.recv(Loader.BUFFER_SIZE)
                if not data:
                    break
                all_data += data

            if all_data:
                message = pickle.loads(all_data)
            else:
                message = ''

            if not message:
                conn.close()
                self.close()
                break

            self.__set_message(str(message))

        return

    def __set_message(self, message):
        """Устанавливает сообщение на элементы виджета"""
        #self.setWindowTitle(str(message))
        self.message_label.setText(str(message))
        QApplication.processEvents()

    def show(self):
        """Отображает лоадер пользователю и запускает поток с сокетом"""
        if self.__is_running:
            return
        self.__is_running = True
        self.__thread = threading.Thread(target=self.__run, args=())
        self.__thread.start()
        super().show()

    def close(self) -> bool:
        """Закрывает лоадер и останавливает поток с сокетом"""
        super().close()
        self.__is_running = False
        return False

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, value):
        self.__port = value

    def set_message(self, message):
        """
        Устанавливает текущее сообщение для виджета.
        Для использования ВНЕ потоков threading.Thread.
        Работает не через сокет.
        """
        if not self.__is_running:
            return
        self.__set_message(message)

    @staticmethod
    def send_message(port, message):
        """
        Устанавливает текущее сообщение для виджета.
        Для использования ВНУТРИ потоков threading.Thread.
        Работает через сокет.
        """
        if port:
            sock = socket.socket()
            sock.settimeout(1)
            is_ok = sock.connect_ex(('localhost', port))
            print(is_ok)
            if is_ok == 0:
                sock.sendall(pickle.dumps(message))
            sock.close()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        # Разметка тестового приложения
        self.title = "Тестовое приложение"
        self.setWindowTitle(self.title)
        self.mainWidget = QWidget()
        self.layout = QHBoxLayout(self)
        self.mainWidget.setLayout(self.layout)
        self.setCentralWidget(self.mainWidget)

        # Основная часть

        # Инициализация лоадера
        loader = Loader("Моделирование", gif=gifFile)
        # ОБъявление фукнции для вызова
        def function_to_call(a1, a2, a3, a4):
            value = 1
            while value <= 10:
                numpy.sort(numpy.random.uniform(0.0, 1.0, 10000000))
                # Отправка сообщений из другого потока должна осуществляться через Loader.send_message
                Loader.send_message(loader.port, f'Моделирование : {value}/10')
                #
                value += 1

            # Лоадер необходимо закрывать вручную
            loader.close()

        # Кнопка запуска фукнции
        def on_btn():
            # Использование класса
            loader.show()
            # Реальные действия должны быть выделены в отдельный поток
            threading.Thread(target=function_to_call, args=(1, 2, 3, 4)).start()

        btn = QPushButton('Старт')
        btn.clicked.connect(on_btn)
        self.layout.addWidget(btn)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = App()
    ex.show()
    sys.exit(app.exec_())
