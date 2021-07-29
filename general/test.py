import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 1, 100)
def sigmoida(x, amplitude, x_indent, y_indent, shape):
    """Функция построения сигмоиды
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       x_indent - положение центра по оси x,
                       y_indent - положение центра по оси y,
                       shape - размах отображения по оси x"""

    k = 10 / shape
    return ((amplitude * 2) / (1 + np.e ** (-k * (x - x_indent)))) + (y_indent - amplitude)
plt.plot(x, sigmoida(x, 3, 0.5, 5, 1.2))
plt.show()