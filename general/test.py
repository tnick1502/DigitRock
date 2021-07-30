from typing import TypeVar, Generic, Tuple, Union, Optional
import numpy as np
import matplotlib.pyplot as plt
def sigmoida(x, amplitude, x_indent, y_indent, shape):
    """Функция построения сигмоиды
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       x_indent - положение центра по оси x,
                       y_indent - положение центра по оси y,
                       shape - размах отображения по оси x"""

    k = 10 / shape
    return ((amplitude * 2) / (1 + np.e ** (-k * (x - x_indent)))) + (y_indent - amplitude)

r = {"sdf": "ewr"}

print()