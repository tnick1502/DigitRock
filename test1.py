from general.general_functions import sigmoida, mirrow_element
import numpy as np
import matplotlib.pyplot as plt

e = np.linspace(0.5, 0.9, 1000)

plt.plot(e, sigmoida(mirrow_element(e, 0.5), 0.2, 0, 0.8, 2))
plt.show()

def sig(x, amplitude, x_indent, y_indent, shape):
    """Функция построения сигмоиды
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       x_indent - положение центра по оси x,
                       y_indent - положение центра по оси y,
                       shape - размах отображения по оси x"""
    pass