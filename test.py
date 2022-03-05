
import hashlib

def hash_id(labolatory_number: str, object_number: str):
    hash_object = hashlib.sha1(f"{object_number} {labolatory_number}".encode("utf-8"))
    return hash_object.hexdigest()


import matplotlib.pyplot as plt
import numpy as np

def exponent(x, amplitude, slant):
    """Функция построения экспоненты
        Входные параметры: x - значение или массив абсцисс,
                           amplitude - значение верхней асимптоты,
                           slant - приведенный угол наклона (пологая - 1...3, резкая - 10...20 )"""
    k = slant/(max(x))
    return amplitude*(-np.e**(-k*x) + 1)



plt.plot(0.005, 1.08/2,s = 10, color="black")
plt.show()
