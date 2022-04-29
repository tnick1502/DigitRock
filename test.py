import numpy as np
import matplotlib.pyplot as plt

def exponent(x, amplitude, slant):
    """Функция построения экспоненты
        Входные параметры: x - значение или массив абсцисс,
                           amplitude - значение верхней асимптоты,
                           slant - приведенный угол наклона (пологая - 1...3, резкая - 10...20 )"""

    k = slant/(max(x))
    return amplitude*(-np.e**(-k*x) + 1)


x = np.linspace(0, 10, 1000)

plt.plot(x, -exponent(x, 1, 1))
plt.show()