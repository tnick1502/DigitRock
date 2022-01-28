import time
from typing import Optional

import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt


def find_zero_crossings(__x) -> list:
    """
    Определяет сколько раз значения в массиве переходят со стороны `value` < `0` в сторону `value` > `0`.

    Возвращает число переходов и индексы точек До перехода
    """
    assert len(__x) > 1, "x should have more than 1 point"

    zero_crossings_indexes = []

    for i in range(1, len(__x) - 1):
        if to_positive_zero_cross(__x[i], __x[i + 1]) or to_negative_zero_cross(__x[i], __x[i + 1]):
            zero_crossings_indexes.append(i + 1)

    # skip first stabilization loop
    # zero_crossings_indexes = zero_crossings_indexes[1:]

    # add last loop if no crossing
    if __x[-1] < 0 or __x[-1] > 0:
        zero_crossings_indexes.append(len(__x)-1)

    return zero_crossings_indexes


def to_positive_zero_cross(first_point: float, second_point: float, value: Optional[float] = 0) -> bool:
    """
    Определяет расположение значений `first_point` и `second_point` относительно прямой y = `value`.

    Если при движении от `first_point` к `second_point` прямая y = `value` пересекается снизу вверх, возвращает True
    """
    return (first_point <= value) and (second_point > value)


def to_negative_zero_cross(first_point: float, second_point: float, value: Optional[float] = 0) -> bool:
    """
    Определяет расположение значений `first_point` и `second_point` относительно прямой y = `value`.

    Если при движении от `first_point` к `second_point` прямая y = `value` пересекается снизу вверх, возвращает True
    """
    return (first_point >= value) and (second_point < value)


def interpolator(__x: np.ndarray, __y: np.ndarray, points_per_interval: Optional[int] = 100):
    len_x = len(__x)
    dy = [(__y[i + 1] - __y[i]) / (__x[i + 1] - __x[i]) for i in range(len_x - 1)]
    dy.append((__y[-1] - __y[-2]) / (__x[-1] - __x[-2]))  # append last point

    indexes = find_zero_crossings(dy)
    indexes.insert(0, 0)

    new_x = []
    step = None
    len_indexes = len(indexes)
    for i in range(len_indexes - 1):
        num = points_per_interval if not step else int((x[indexes[i + 1]] - x[indexes[i]])/step) + 1
        new_x = np.hstack((new_x, np.linspace(x[indexes[i]], x[indexes[i + 1]], num)))
        if not step:
            step = new_x[1] - new_x[0]

    f = interp1d(__x, __y)

    return new_x, f(new_x)



if __name__ == "__main__":
    x = np.linspace(0, 10, num=500000, endpoint=True)
    A = 5
    k = 2
    # Asin(kx + (0.1pi + 0.0002x))
    y = A * np.sin(k * x + (0.1 * np.pi + 0.0002 * x))

    tic = time.perf_counter()
    rez_x, rez_y = interpolator(x, y, points_per_interval=10)
    toc = time.perf_counter()
    print(f"Вычисление заняло {toc - tic:0.4f} секунд")

    plt.plot(x, y, 'o', rez_x, rez_y, '-')
    plt.legend([f'len data: {len(x)}', f'len interpolated : {len(rez_y)}'], loc='best')
    plt.show()
