# coding: utf-8

# In[ ]:


from scipy.optimize import fsolve
import math
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QFrame, QSlider, QLabel
from PyQt5 import QtCore
from scipy import interpolate

import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np
import math
from scipy.interpolate import make_interp_spline, BSpline
from scipy.interpolate import splev, splrep

import os

from scipy.special import comb
from scipy.optimize import fsolve
import math
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QFrame, QSlider, QLabel
from PyQt5 import QtCore
from scipy import interpolate

import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# from matplotlib.pyplot import gca

import numpy as np
import math
from scipy.interpolate import make_interp_spline
from scipy.interpolate import splev, splrep



# coding: utf-8

# In[34]:


#print(compute_l2_norm(arr = np.array([(1, 2), (3, 1.5), (0, 5.5)])))



# from consolidation_functions import *


def bezier_curve_exp(p1_l1, p2_l1, p1_l2, p2_l2, node1, node2, x_grid):
    """
    Требуется модуль: from scipy.optimize import fsolve
    Функция построения кривой Безье на оссновании двух прямых,
    задаваемых точками 'point_line' типа [x,y],
    на узлах node типа [x,y]
    с построением промежуточного узла в точке пересечения поданных прямых.
    Функция возвращает значения y=f(x) на сетке по оси Ox.

    Пример:
    Соединяем две прямые от точки [x_given,y_given] до точки [x[index_x_start[0]], y_start[0]]
    xgi, = np.where(x > x_given) # некая точка после которой нужно переходить к кривой безье
    y_Bezier_line = bezier_curve([0,0],[x_given,y_given], #Первая и Вторая точки первой прямой
                                 [x_given, k * x_given + b], #Первая точка второй прямой (k и b даны)
                                 [x[index_x_start[0]],y_start[0]], #Вторая точка второй прямой
                                 [x_given, y_given], #Первый узел (здесь фактически это 2 точка первой прямой)
                                 [x[index_x_start[0]], y_start[0]], #Второй узел
                                                                # (здесь фактически это 2 точка второй прямой)
                                 x[xgi[0]:index_x_start[0]]
                                 )

    :param p1_l1: Первая точка первой прямой [x,y]
    :param p2_l1: Вторая точка первой прямой [x,y]
    :param p1_l2: Первая точка второй прямой [x,y]
    :param p2_l2: Вторая точка второй прямой [x,y]
    :param node1: Первый узел [x,y]
    :param node2: Второй узел [x,y]
    :param x_grid: Сетка по Ох на которой необходимо посчитать f(x)
    :return: Значения y=f(x) на сетке x_grid
    """

    def bernstein_poly(_i, n, t):
        """
         Полином Бернштейна стпени n, i - функция t
        """
        return comb(n, _i) * (t ** _i) * (1 - t) ** (n - _i)

    def bezier_curve_local(nodes, n_times=1000):
        """
        На основании набора узлов возвращает
        кривую Безье определяемую узлами
        Точки задаются в виде:
           [ [1,1],
             [2,3],
              [4,5], ..[Xn, Yn] ]
        nTimes - число точек для вычисления значений
        """

        n_points = len(nodes)
        x_points = np.array([p[0] for p in nodes])
        y_points = np.array([p[1] for p in nodes])

        t = np.linspace(0.0, 1.0, n_times)

        polynomial_array = np.array([bernstein_poly(_i, n_points - 1, t) for _i in range(0, n_points)])

        x_values_l = np.dot(x_points, polynomial_array)
        y_values_l = np.dot(y_points, polynomial_array)
        return x_values_l, y_values_l

    def intersect(xp1, yp1, xp2, yp2, xp3, yp3, xp4, yp4):
        """
        Функция пересечения двух прямых, заданных точками
        :param xp1: x точки 1 на прямой 1
        :param yp1: y точки 1 на прямой 1
        :param xp2: x точки 2 на прямой 1
        :param yp2: y точки 2 на прямой 1
        :param xp3: x точки 1 на прямой 2
        :param yp3: y точки 1 на прямой 2
        :param xp4: x точки 2 на прямой 2
        :param yp4: y точки 2 на прямой 2
        :return: точка пересечения прямых [x,y]
        """

        def form_line(_xp1, _yp1, _xp2, _yp2):
            k = (_yp2 - _yp1) / (_xp2 - _xp1)
            b = _yp1 - k * _xp1
            return k, b

        kl1, bl1 = form_line(xp1, yp1, xp2, yp2)
        kl2, bl2 = form_line(xp3, yp3, xp4, yp4)
        x_p_inter = (bl1 - bl2) / (kl2 - kl1)
        y_p_inter = kl1 * x_p_inter + bl1
        return x_p_inter, y_p_inter

    # Определяем точки пересечения прямых
    xl1, yl1 = intersect(p1_l1[0], p1_l1[1],
                         p2_l1[0], p2_l1[1],
                         p1_l2[0], p1_l2[1],
                         p2_l2[0], p2_l2[1])

    # Строим кривую Безье
    x_values, y_values = bezier_curve_local([node1, [xl1, yl1], node2], n_times=len(x_grid))

    # Адаптация кривой под равномерный шаг по х
    bezier_spline = interpolate.make_interp_spline(x_values, y_values, k=1, bc_type=None)
    y_values = bezier_spline(x_grid)

    return y_values


def deviator_loading_deviation_exp(strain, deviator, fracture_strain):
    # Добавим девиации после 0.6qf для кривой без пика
    qf = max(deviator)
    deviation_1 = qf / 100
    deviation_2 = qf / 60

    i_60, = np.where(deviator >= 0.51 * qf)
    i_90, = np.where(deviator >= 0.98 * qf)
    i_end, = np.where(strain >= 0.15)
    i_xc, = np.where(strain >= fracture_strain)
    if fracture_strain >= 0.14:  # без пика
        curve = create_deviation_curve(strain[i_60[0]:i_xc[0]], deviation_1 * 2,
                                       points=np.random.uniform(3, 7), borders="zero_diff",
                                       low_first_district=1, one_side=True) + create_deviation_curve(
            strain[i_60[0]:i_xc[0]], deviation_1,
            points=np.random.uniform(20, 30), borders="zero_diff",
            low_first_district=1, one_side=True)
        deviation_array = -np.hstack((np.zeros(i_60[0]),
                                      -curve,
                                      np.zeros(len(strain) - i_xc[0])))
    else:

        try:
            i_xc1, = np.where(deviator[i_xc[0]:] <= qf - deviation_2)
            i_xc_m, = np.where(deviator >= qf - deviation_1 * 2)
            points_1 = round(fracture_strain * 100)
            if points_1 < 3:
                points_1 = 3

            curve_1 = create_deviation_curve(strain[i_60[0]:i_xc_m[0]], deviation_1 * 1.5,
                                             points=np.random.uniform(3, 4), val=(1, 0.1), borders="zero_diff",
                                             low_first_district=1) + create_deviation_curve(
                strain[i_60[0]:i_xc_m[0]], deviation_1 / 2,
                points=np.random.uniform(points_1, points_1 * 3), borders="zero_diff",
                low_first_district=1)

            points_2 = round((0.15 - fracture_strain) * 100)
            if points_2 < 3:
                points_2 = 3

            deviation_2 = ((deviator[i_xc[0]] - deviator[i_end[0]]) / 14) * (points_2 / 10)

            curve_2 = create_deviation_curve(strain[i_xc[0] + i_xc1[0]:i_end[0]],
                                             deviation_2, val=(0.1, 1),
                                             points=np.random.uniform(points_2, int(points_2 * 3)), borders="zero_diff",
                                             low_first_district=2) + create_deviation_curve(
                strain[i_xc[0] + i_xc1[0]:i_end[0]],
                deviation_2 / 3, val=(0.1, 1),
                points=np.random.uniform(points_2 * 3, int(points_2 * 5)), borders="zero_diff",
                low_first_district=2)
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          curve_1, np.zeros(i_xc[0] - i_xc_m[0]),
                                          np.zeros(i_xc1[0]),
                                          curve_2,
                                          np.zeros(len(strain) - i_end[0])))
        except (ValueError, IndexError):
            print("Ошибка девиаций девиатора")
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          create_deviation_curve(strain[i_60[0]:i_90[0]], deviation_1,
                                                                 points=np.random.uniform(3, 6), borders="zero_diff",
                                                                 low_first_district=1),
                                          create_deviation_curve(strain[i_90[0]:i_end[0]], deviation_2, val=(1, 0.1),
                                                                 points=np.random.uniform(10, 15), borders="zero_diff",
                                                                 low_first_district=3,
                                                                 one_side=True),
                                          np.zeros(len(strain) - i_end[0])))

    return deviation_array


def sensor_accuracy_exp(x, y, fracture_strain, noise_level=1.0):
    """возвразщает зашумеленную функцию без шума в характерных точках"""

    noise = np.random.uniform(-noise_level, noise_level, len(x))
    index_qf_half, = np.where(y >= np.max(y) / 2)
    index_qf, = np.where(y >= np.max(y))
    if fracture_strain > max(x):  # если хс последня точка в массиве или дальше
        index_qf, = np.where(x >= max(x))
    for _i in range(len(y)):  # наложение шума кроме промежутков для характерных точек
        is_excluded_points = (_i < index_qf_half[0] - 2) or \
                             ((_i > index_qf_half[0] + 2) and ([_i] < index_qf[0] - 2)) or \
                             (_i > index_qf[0] + 2)
        if is_excluded_points:
            if y[_i] + noise[_i] < np.max(y):
                y[_i] = y[_i] + noise[_i]
            else:
                # в районе максимума шум меньше первоначального
                y[_i] = y[_i] - np.random.uniform(0.1, 0.5) * noise_level
    return y


def hevisaid_exp(x, offset, smoothness):
    """возвращет функцию Хевисайда 0<=y<=1, которая задает коэффициент влияния kp

    :param x: точки, в которых вычислять значение
    :param offset: смещение относительно х=0
    :param smoothness: гладкость перехода, при smoothness = 0 выраждается в фукнцию Хевисаида
    """
    return 1. / (1. + np.exp(-2 * 10 / smoothness * (x - offset)))


def smoothness_condition_exp(strain_at_50_percent_strength):
    """возвращает предельное значение fracture_strain при котором возможно
    построение заданной функции

    :param strain_at_50_percent_strength: деформация в 50% прочности
    """
    SMOOTHNESS_OFFSET = 0.6 / 100  # 0.6 возможно является максимальным х на сетке
    return 2 * strain_at_50_percent_strength + SMOOTHNESS_OFFSET


def gaus_exp(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """функция Гаусса для участка x>fracture_strain"""
    gaus_height = qf - residual_strength  # высота функции Гаусса
    gaus_smoothness = (-1) * np.log(0.1 / gaus_height) / ((residual_strength_strain - fracture_strain) ** 2)
    # резкость функции Гаусаа (считается из условия равенства заданной точности в точке х50
    return gaus_height * (np.exp(-gaus_smoothness * ((x - fracture_strain) ** 2))) + residual_strength


def parab_exp(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """Парабола для участка x>fracture_strain """
    # k*x^2 + b
    k_par = -((residual_strength - qf) / (residual_strength_strain - fracture_strain) ** 2)
    return -k_par * ((x - fracture_strain) ** 2) + qf


def exp_for_compare(x, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator):
    """возвращает координаты y итоговой фукнции по законам гиперболы, экспоненты и тангенса"""
    # Константы
    E50_LIMIT = 70000
    '''Е50 после которого необходимо переходить от эспоненты к тангенсу'''
    OC_STRAIN_CUT = 0.151
    '''значение по которому обрезается точка х переуплотнния'''
    ZERO_OFFSET = 0.000001
    '''смещение для расчета 0 значений в особенностях'''

    def exponent_error(height_smoothness: list):
        """возвращает ошибки в коэффициентах, вычисляются в точках qf и qf/2

        :param height_smoothness: list : exp_relative_height, exp_smoothness
        """
        _exp_relative_height, _exp_smoothness = height_smoothness  # коэффициенты экспоненты
        return -1 * _exp_relative_height * (np.exp(-_exp_smoothness * strain_at_50_strength) - 1) - qf / 2, \
               -1 * _exp_relative_height * (np.exp(-_exp_smoothness * fracture_strain) - 1) - qf

    if E50 > 40000:
        # начальные приближения для расчета коэффициентов
        exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, np.array([1, 1]))
        initial_exp_relative_height = 1
        error = exponent_error([exp_relative_height, exp_smoothness])

        # персчет значений при ошибках построения
        while abs(error[0]) >= 10 or abs(error[1]) >= 10:
            initial_exp_relative_height += 1
            exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, np.array([initial_exp_relative_height, 1]))
            error = exponent_error([exp_relative_height, exp_smoothness])

    else:
        # начальные приближения для расчета коэффициентов
        initial_exp_relative_height, initial_exp_smoothness = 600, 1
        _initial = np.array([initial_exp_relative_height, initial_exp_smoothness])
        exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, _initial)

        initial_exp_relative_height = 1
        error = exponent_error([exp_relative_height, exp_smoothness])

        # персчет значений при ошибках построения
        WHILE_COUNT = 0

        # пока

        def is_negative():
            return (exp_relative_height <= 0) or (exp_smoothness <= 0)

        # пока

        def is_not_changed():
            return exp_relative_height == initial_exp_relative_height or exp_smoothness == initial_exp_smoothness

        # пока произведение коээфициентов (приблизительно равно E50) меньше 1000
        def is_lower_1000():
            return exp_relative_height * exp_smoothness < 1000

        # пока
        def is_error(_error):
            """превышение переменной error предела на ошибку EPS"""
            EPS = 550
            return abs(_error[0]) >= EPS or abs(_error[1]) >= EPS

        while is_negative() or is_not_changed() or is_lower_1000() or (is_error(error) and WHILE_COUNT < 50):
            initial_exp_relative_height += 1
            _initial = np.array([initial_exp_relative_height, initial_exp_smoothness])
            exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, _initial)
            error = exponent_error([exp_relative_height, exp_smoothness])
            if is_error(error):
                WHILE_COUNT += 1


    def dev_load_exp(_x):
        """считает значения экспоненты на х"""
        return -exp_relative_height * (np.exp(-exp_smoothness * _x) - 1)


    # изначальный расчет возвращаемой фукнции
    result_y = dev_load_exp(x)

    OC_strain = 0.  # абцисса точки переуплотнения

    return result_y, OC_strain


def cos_par_exp_exp(x, E50, qf, strain_at_50_strength, fracture_strain, correction=0):
    """возвращает функцию косинуса
     и параболы для участка strain_at_50_strength qf"""

    SHIFT = (fracture_strain - strain_at_50_strength) / 2
    '''смещение: коэффицент учитывающий влияние на высоту функции при различных значениях E50'''

    if E50 < 5340:
        vl = 0
    elif (E50 <= 40000) and (E50 >= 5340):
        kvl = 1 / 34660
        bvl = -5340 * kvl
        vl = kvl * E50 + bvl  # 1. / 40000. * E50 - 1. / 8
    elif E50 > 40000:
        vl = 1.
    else:
        vl = None

    height = 0.035 * qf * vl - correction  # высота функции
    if height < 0:
        height = 0

    k_of_parab = height / (-fracture_strain + strain_at_50_strength + SHIFT) ** 2

    # фиромирование функции
    # if x is greater then strain_at_50_strength : x_gr_x50
    _i, = np.where(x > strain_at_50_strength)
    x_low_x50 = x[:_i[0]] if _i.size > 0 else x
    x_gr_x50 = x[_i[0]:] if _i.size > 0 else np.array([])

    # if x is greater then strain_at_50_strength + SHIFT : x_gr_x50sm
    j, = np.where(x_gr_x50 > strain_at_50_strength + SHIFT)
    x_gr_x50_low_x50sm = x_gr_x50[:j[0]] if j.size > 0 else x_gr_x50
    x_gr_x50sm = x_gr_x50[j[0]:] if j.size > 0 else np.array([])

    # if x is greater then fracture_strain : x_gr_xc
    l, = np.where(x_gr_x50sm > fracture_strain)
    x_gr_x50sm_low_xc = x_gr_x50sm[:l[0]] if l.size > 0 else x_gr_x50sm
    x_gr_xc = x_gr_x50sm[l[0]:] if l.size > 0 else np.array([])

    _first_zero_part = np.full(len(x_low_x50), 0)
    _cos_part = (height * 0.5 * (np.cos((1. / SHIFT) *
                                        np.pi * (x_gr_x50_low_x50sm - strain_at_50_strength) - np.pi) + 1))
    _parab_part = (-1) * k_of_parab * (x_gr_x50sm_low_xc - strain_at_50_strength - SHIFT) ** 2 + height
    _last_zero_part = np.full(len(x_gr_xc), 0)

    return np.hstack((_first_zero_part, _cos_part, _parab_part, _last_zero_part))


def loop_exp(x, y, Eur, unload_deviator, re_load_deviator, noise_params=None):
    """Рассчитывает петлю разгрузки -- повторного нагружения
    :param x: массив значений x
    :param y: массив значений y
    :param Eur: recommended: 3*E50
    :param unload_deviator: девиатор разгрузки
    :param re_load_deviator: девиатор повторной нагрузки
    :param noise_params: optional, default None, параметры для моделирования шума list[float, float]

    Returns
    --------
    loop_x -- x координаты петли \n
    loop_y -- y координаты петли \n
    connection_indexes -- tuple[index_connection_unload[0], index_connection_return_on_load[0])]\n
    loop_indexes -- tuple[real_unload_index, real_re_load_index, real_return_on_load_index]\n
    loop_strain_values --tuple[unload_strain, re_load_strain, return_on_load_point_strain]\n
    """

    # индекс 1 точки
    index_unload_point, = np.where(y >= unload_deviator)

    if not np.size(index_unload_point) > 0:
        unload_deviator = np.max(y)
        index_unload_point, = np.where(y >= unload_deviator)

    index_unload_point = index_unload_point[0]

    # точка появления петли
    unload_strain = x[index_unload_point]
    unload_deviator = y[index_unload_point]

    # точка конца петли
    index_re_load_point, = np.where(y == np.max(y))
    index_re_load_point = index_re_load_point[-1]

    k = (0.3 / (-x[index_re_load_point])) * unload_strain + 0.4
    dynamic_ratio = -3 * 10 ** (-9) * Eur + k * unload_strain  # 0.00095

    # Точка возврата на кривую
    return_on_load_point_strain = unload_strain + dynamic_ratio
    assert return_on_load_point_strain < x.max(), "Ошибка построения петли при заданном Eur"
    index_return_on_load, = np.where(x >= return_on_load_point_strain)
    index_return_on_load = index_return_on_load[0]
    # задаем последнюю точку в общем массиве кривой девиаторного нагружения
    return_on_load_point_strain = x[index_return_on_load]
    if return_on_load_point_strain <= unload_strain:
        index_return_on_load = index_unload_point + 1
        return_on_load_point_strain = x[index_return_on_load]
    return_on_load_deviator = y[index_return_on_load]

    D1_return_on_load = (y[index_return_on_load + 1] - y[index_return_on_load]) / \
                        (x[index_return_on_load + 1] - x[index_return_on_load])
    '''производная кривой девиаторного нагружения в точке конца петли'''

    E0 = (y[1] - y[0]) / (x[1] - x[0])  # производная кривой девиаторного нагружения в 0
    # ограничение на E0 (не больше чем модуль петли разгрузки)
    if E0 < Eur:
        E0 = 1.1 * Eur

    # ограничение на угол наклона участка повтороной нагрузки,
    # чтобы исключить пересечение петли и девиаторной кривой
    min_E0 = unload_deviator / unload_strain  # максимальный угол наклона петли

    # коррекция Eur
    if Eur < 1.1 * min_E0:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        Eur = 1.1 * min_E0
        E0 = 1.1 * Eur

    # вычисляется из оординаты и угла наклона петли
    re_load_strain = (re_load_deviator - unload_deviator + Eur * unload_strain) / Eur
    index_re_load, = np.where(x >= re_load_strain)
    index_re_load = index_re_load[0]
    re_load_strain = x[index_re_load]

    # если точка 2 совпадает с точкой один или правее, то меняем точку 2 на предыдущую
    if index_re_load >= index_unload_point:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        index_re_load = index_unload_point - 1
        re_load_strain = x[index_re_load]

    # участок разгрузки
    unload_part_x = np.linspace(unload_strain, re_load_strain,
                                int(abs(re_load_strain - unload_strain) / (x[1] - x[0]) + 1))
    # участок повторной нагрузки
    reload_part_x = np.linspace(re_load_strain, return_on_load_point_strain,
                                int(abs(return_on_load_point_strain - re_load_strain) / (x[1] - x[0]) + 1))

    # 0.8 * Eur + 60000  # производная в точке начала разгрузки (близка к бесконечности) #???
    dynamic_D1 = 2 * Eur

    # формируем разгрузку
    spline_unload = interpolate.make_interp_spline([re_load_strain, unload_strain],
                                                   [re_load_deviator, unload_deviator], k=3,
                                                   bc_type=([(2, 0)], [(1, dynamic_D1)]))
    unload_part_y = spline_unload(unload_part_x)  # участок разгрузки

    # формируем повторное нагружение
    point_1_l1 = [re_load_strain - 0.2 * re_load_strain,
                  E0 * (re_load_strain - 0.2 * re_load_strain) +
                  (re_load_deviator - E0 * re_load_strain)]
    point_2_l1 = [re_load_strain, re_load_deviator]
    point_1_l2 = [return_on_load_point_strain, return_on_load_deviator]
    point_2_l2 = [return_on_load_point_strain - 0.1 * return_on_load_point_strain,
                  D1_return_on_load * (return_on_load_point_strain - 0.1 * return_on_load_point_strain) +
                  (return_on_load_deviator - D1_return_on_load * return_on_load_point_strain)]

    _bezier_curve = bezier_curve_exp(point_1_l1, point_2_l1, point_1_l2, point_2_l2,
                                     [re_load_strain, re_load_deviator],
                                     [return_on_load_point_strain, return_on_load_deviator],
                                     reload_part_x)
    reload_part_y = _bezier_curve

    # устраняем повторяющуюся точку 2
    reload_part_x = reload_part_x[1:]
    reload_part_y = reload_part_y[1:]

    # соединяем  участки разгрузки и нагрузки в петлю
    loop_x = np.hstack((unload_part_x, reload_part_x))

    # определяем индексы, по которым будет петля будет "крепиться" к исходной кривой
    index_connection_unload, = np.where(x >= unload_strain)
    index_connection_return_on_load, = np.where(x >= return_on_load_point_strain)

    if noise_params:
        unload_part_y = unload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(unload_part_y))
        reload_part_y = reload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(reload_part_y))
        unload_part_y = discrete_array(unload_part_y, noise_params[1])
        reload_part_y = discrete_array(reload_part_y, noise_params[1])

    loop_y = np.hstack((unload_part_y, reload_part_y))

    real_unload_index = index_connection_unload[0] + 1
    # первая точка петли на самом деле принадлежит исходной кривой
    real_re_load_index = index_connection_unload[0] + len(unload_part_y)
    # -1 + 1 = 0 т.к. самая нижняя точка петли принадлежит разгрузке
    real_return_on_load_index = index_connection_unload[0] + len(loop_x) - 2
    # -1 - 1 = -2 т.к. последняя точка петли так же на самом деле принадлежит кривой

    # Для присоединения петли к исходной кривой
    connection_indexes = (index_connection_unload[0], index_connection_return_on_load[0])
    #
    loop_indexes = (real_unload_index, real_re_load_index, real_return_on_load_index)
    #
    # Для работы фукнции объемной деформации
    loop_strain_values = (unload_strain, re_load_strain, return_on_load_point_strain)
    #

    return loop_x, loop_y, connection_indexes, loop_indexes, loop_strain_values


def dev_loading_exp(qf, E50, **kwargs):
    """
    Кусочная функция: на участке [0,fracture_strain]-сумма функций гиперболы и
    (экспоненты или тангенса) и кусочной функции синуса и парболы
    на участке [fracture_strain...]-половина функции Гаусса или параболы

    :param qf: double
        qf
    :param E50: double
        E50
    :param kwargs: optional:
        fracture_strain;
        residual_strength_strain;
        residual_strength;
        OC_deviator;
        gaus_or_par;
        amount_points;
        Eur, default None, True для петли;
        unload_deviator;
        re_load_deviator;
        noise_off, default None, True для отключения шумов и "ступеней";
    :return: strain_required_grid - х координаты полученной кривой;
        deviator_required_grid - у координаты полученной кривой;
        [[strain_at_50_strength, qf / 2], [OC_strain, OC_deviator], [fracture_strain, qf],
         [residual_strength_strain, residual_strength]] - расчетные параметры;
        loop_strain_values if Eur, tuple - strain координаты точек петли;
        loop_indexes if Eur, tuple - индексы самой петли, точки кривой не включены
    """

    # Константы
    STRAIN_LIMIT = 0.15
    STRAIN_CALC_LIMIT = 0.6
    NOISE_LEVEL = 1.0
    DISCRETE_ARRAY_LEVEL = 0.5
    DISCRETE_ARRAY_LOOP_LEVEL = 2 * DISCRETE_ARRAY_LEVEL
    #
    _0002_QF = 0.002 * qf

    # Параметры
    try:
        kwargs["fracture_strain"]
    except KeyError:
        kwargs["fracture_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength_strain"]
    except KeyError:
        kwargs["residual_strength_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength"]
    except KeyError:
        kwargs["residual_strength"] = qf

    try:
        kwargs["OC_deviator"]
    except KeyError:
        kwargs["OC_deviator"] = 0

    try:
        kwargs["gaus_or_par"]
    except KeyError:
        kwargs["gaus_or_par"] = 0

    try:
        kwargs["amount_points"]
    except KeyError:
        kwargs["amount_points"] = 700

    try:
        kwargs["Eur"]
    except KeyError:
        kwargs["Eur"] = None

    try:
        kwargs["unload_deviator"]
    except KeyError:
        kwargs["unload_deviator"] = 0.8 * qf

    try:
        kwargs["re_load_deviator"]
    except KeyError:
        kwargs["re_load_deviator"] = 10

    try:
        kwargs["noise_off"]
    except KeyError:
        kwargs["noise_off"] = None

    #
    fracture_strain = kwargs.get('fracture_strain')
    residual_strength_strain = kwargs.get('residual_strength_strain')
    residual_strength = kwargs.get('residual_strength')
    OC_deviator = kwargs.get('OC_deviator')
    gaus_or_par = kwargs.get('gaus_or_par')  # 0 - гаус, 1 - парабола
    amount_points = kwargs.get('amount_points')
    Eur = kwargs.get('Eur')
    unload_deviator = kwargs.get('unload_deviator')
    re_load_deviator = kwargs.get('re_load_deviator')
    noise_off = kwargs.get("noise_off")

    if noise_off:
        NOISE_LEVEL = None
        DISCRETE_ARRAY_LEVEL = None
        DISCRETE_ARRAY_LOOP_LEVEL = None
    # расчёт ведется с числом точек amount_points на длине STRAIN_CALC_LIMIT
    AMOUNT_POINTS_ON_CALC = int((amount_points * STRAIN_CALC_LIMIT / STRAIN_LIMIT) / (STRAIN_CALC_LIMIT / STRAIN_LIMIT))
    # значения будут возвращаться с числом точек amount_points но на длине STRAIN_LIMIT
    AMOUNT_POINTS_ON_RETURN = int(AMOUNT_POINTS_ON_CALC * (STRAIN_CALC_LIMIT / STRAIN_LIMIT))

    # Ограничения
    if unload_deviator > qf:
        unload_deviator = qf
    if unload_deviator < 20.0:
        unload_deviator = 20.0
    if fracture_strain > 0.11:
        fracture_strain = 0.15
    if residual_strength >= qf:
        residual_strength = qf
    strain_at_50_strength = (qf / 2.) / E50
    if fracture_strain < strain_at_50_strength:
        fracture_strain = strain_at_50_strength * 1.1  # хс не может быть меньше strain_at_50_strength

    # Сетки
    strain = np.linspace(0, STRAIN_CALC_LIMIT, AMOUNT_POINTS_ON_CALC)

    # Начало построения фукнции

    # считаем предельное значение fracture_strain
    fracture_strain_limit = smoothness_condition_exp(strain_at_50_strength)

    if strain_at_50_strength >= fracture_strain:
        # если strain_at_50_strength > fracture_strain, fracture_strain сдвигается в 0.15,
        # х2,residual_strength перестает учитываться,
        # в качестве функции используется сумма гиперболы, экспоненты или тангенса и функции синуса и параболы

        fracture_strain = STRAIN_LIMIT
        #
        deviator, OC_strain = exp_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #

        if fracture_strain <= fracture_strain_limit:
            # проверка на условие гладкости, если условие не соблюдается
            # передвинуть xс в предельное значение
            fracture_strain = fracture_strain_limit
            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = exp_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par_exp_exp(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #

        # residual_strength_strain,residual_strength не выводится
        residual_strength_strain = fracture_strain
        residual_strength = qf

    else:
        #
        deviator, OC_strain = exp_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #
        if fracture_strain <= fracture_strain_limit:
            fracture_strain = fracture_strain_limit

            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = exp_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            #

        if fracture_strain > STRAIN_LIMIT:
            #
            deviator, OC_strain = exp_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par_exp_exp(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #
            # residual_strength_strain,residual_strength не выводится
            residual_strength_strain = fracture_strain
            residual_strength = qf

        else:
            # минимально допустимое расстояния между хс и х2
            if fracture_strain >= 0.8 * residual_strength_strain:
                residual_strength_strain = 1.2 * fracture_strain
            # минимально допустимое расстояние мужду residual_strength и qf
            if residual_strength >= qf:
                residual_strength = 0.98 * qf

            # Примеряем положение кривой - оно не должно быть выше qf
            _i, = np.where(strain >= fracture_strain)  # >= намеренно
            _i = _i[0]
            _gip_exp_tg, *_ = exp_for_compare(strain[:_i], E50, qf, strain_at_50_strength,
                                              fracture_strain, OC_deviator)
            _cos_par = cos_par_exp_exp(strain[:_i], E50, qf, strain_at_50_strength, fracture_strain)
            maximum = max(np.hstack((_gip_exp_tg + _cos_par, np.full(len(strain[_i:]), 0.0)))
                          if _i.size > 0 else np.full(len(strain), 0.0))

            is_max_lower_qf = maximum < (qf + _0002_QF)

            _i, = np.where(strain > fracture_strain)  # > намеренно
            if is_max_lower_qf:
                correction = 0
            else:
                # если максимум суммарной функции на участке от 0 до хс превышает qf, то уменьшаем
                # высоту функции синуса и параболы на величину разницы в точке fracture_strain
                correction = abs(maximum - qf + 2 * _0002_QF)

            if _i.size > 0:
                _i = _i[0]
                _gip_exp_tg, *_ = exp_for_compare(strain[:_i], E50, qf, strain_at_50_strength,
                                                  fracture_strain, OC_deviator)
                _cos_par = cos_par_exp_exp(strain[:_i], E50, qf, strain_at_50_strength,
                                           fracture_strain, correction)
                if gaus_or_par == 1:
                    _gaus_or_par = parab_exp(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                             residual_strength)
                else:
                    _gaus_or_par = gaus_exp(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                            residual_strength)
                deviator = np.hstack((_gip_exp_tg + _cos_par, _gaus_or_par))

            else:
                deviator = (strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)[0] \
                           + cos_par_exp_exp(strain, E50, qf, strain_at_50_strength, fracture_strain, correction)

    if OC_deviator > (0.8 * qf):  # не выводить точку OC_strain, OC_deviator
        OC_strain = fracture_strain
        OC_deviator = qf

    # переход к нужной сетке (strain_required_grid необходимо обрезать по х = STRAIN_LIMIT чтобы получить amount_points
    strain_required_grid = np.linspace(strain.min(initial=None), strain.max(initial=None), AMOUNT_POINTS_ON_RETURN)
    # интерполяция  для сглаживания в пике
    spl = make_interp_spline(strain, deviator, k=5)
    deviator_required_grid = spl(strain_required_grid)

    loop_indexes = None

    def noise(result):
        """На кладывает девиации, шум и дискретизацию в соответствии с NOISE_LEVEL и DISCRETE_ARRAY_LEVEL"""
        if not noise_off:
            result += deviator_loading_deviation_exp(strain_required_grid, result, fracture_strain)
            result = sensor_accuracy_exp(strain_required_grid, result, fracture_strain, noise_level=NOISE_LEVEL)
            result = discrete_array(result, DISCRETE_ARRAY_LEVEL)
        return result

    if Eur:
        x_loop, y_loop, connection_to_curve_indexes, loop_indexes, loop_strain_values = \
            loop_exp(strain_required_grid, deviator_required_grid, Eur, unload_deviator, re_load_deviator,
                     [NOISE_LEVEL, DISCRETE_ARRAY_LOOP_LEVEL] if not noise_off else None)

        #
        # deviator_required_grid = noise(deviator_required_grid)

        deviator_required_grid = np.hstack((deviator_required_grid[:connection_to_curve_indexes[0]], y_loop,
                                            deviator_required_grid[connection_to_curve_indexes[1] + 1:]))
        strain_required_grid = np.hstack((strain_required_grid[:connection_to_curve_indexes[0]], x_loop,
                                          strain_required_grid[connection_to_curve_indexes[1] + 1:]))
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.
    else:
        # deviator_required_grid = noise(deviator_required_grid)
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.

    # наложение хода штока и обрезка функций
    # rod_move_result = initial_free_rod_move(strain_required_grid,
    #                                         deviator_required_grid,
    #                                         strain_cut=STRAIN_LIMIT,
    #                                         noise=(NOISE_LEVEL, DISCRETE_ARRAY_LEVEL) if not noise_off else None)
    # strain_required_grid = rod_move_result[0]
    # deviator_required_grid = rod_move_result[1]
    # len_rod_move = rod_move_result[2]
    loop_indexes_with_rod = None if not Eur else (loop_indexes[i] + len_rod_move for i in range(len(loop_indexes)))

    return strain_required_grid, deviator_required_grid


def initial_free_rod_move(strain, deviator, strain_cut=0.151, noise=None):
    """
    Обрезает strain и deviator по strain_cut и
    возвращает strain, deviator с присоединенным ходом штока и длину хода штока (в точках)

    :param strain:
    :param deviator:
    :param strain_cut: optional, default = 0.151, значение, по которому обрезаются массивы
    :param noise: optional, default None, параметры для моделирования шума tuple[float, float]

    Returns
    -------
    strain -- cut strain with rod \n
    deviator -- cut deviator with rod \n
    len_rod_move -- len of rod in points: len(strain_start)
    """
    _i, = np.where(strain > strain_cut)
    assert _i.size > 0, "Ошибка обрезки, strain_cut не может быть больше max(strain)"
    strain = strain[:_i[0]]
    deviator = deviator[:_i[0]]

    strain_last_point = np.random.uniform(0.005, 0.01) - (strain[-1] - strain[-2])
    '''положительная последняя точка х для метрвого хода штока'''

    strain_start = np.linspace(0, strain_last_point, int(strain_last_point / (strain[-1] - strain[-2])) + 1)
    '''положительный масив х для метрвого хода штока'''

    SLANT = np.random.uniform(20, 30)
    '''наклон функции экспоненты'''
    AMPLITUDE = np.random.uniform(15, 25)
    '''высота функции экспоненты'''

    # определяем абциссу метрвого хода штока
    deviator_start = exponent(strain_start, AMPLITUDE, SLANT)
    # смещение массива x для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    strain_start -= strain_start[-1] + (strain[-1] - strain[-2])
    # смещение массива y для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    deviator_start -= deviator_start[-1]

    if noise:
        assert len(noise) == 2, "noise должен содерждать значение для шума и значение для уровня ступеней"
        deviator_start = deviator_start + np.random.uniform(-noise[0], noise[0], len(deviator_start))
        deviator_start = discrete_array(deviator_start, noise[1])  # наложение ступенчватого шума на мертвый ход штока

    strain = np.hstack((strain_start, strain))  # добавление начального участка в функцию девиаторного нагружения
    strain += abs(strain[0])  # смещение начала кривой девиаторного нагруружения в 0

    deviator = np.hstack((deviator_start, deviator))  # добавление начального участка в функцию девиаторного нагружения
    deviator += abs(deviator[0])  # смещение начала кривой девиаторного нагружения в 0
    deviator[0] = 0.  # искусственное зануление первой точки

    len_rod_move = len(strain_start)

    return strain, deviator, len_rod_move









#------------------------------------------------------------------------------------------------------------------------


def bezier_curve(p1_l1, p2_l1, p1_l2, p2_l2, node1, node2, x_grid):
    """
    Требуется модуль: from scipy.optimize import fsolve
    Функция построения кривой Безье на оссновании двух прямых,
    задаваемых точками 'point_line' типа [x,y],
    на узлах node типа [x,y]
    с построением промежуточного узла в точке пересечения поданных прямых.
    Функция возвращает значения y=f(x) на сетке по оси Ox.

    Пример:
    Соединяем две прямые от точки [x_given,y_given] до точки [x[index_x_start[0]], y_start[0]]
    xgi, = np.where(x > x_given) # некая точка после которой нужно переходить к кривой безье
    y_Bezier_line = bezier_curve([0,0],[x_given,y_given], #Первая и Вторая точки первой прямой
                                 [x_given, k * x_given + b], #Первая точка второй прямой (k и b даны)
                                 [x[index_x_start[0]],y_start[0]], #Вторая точка второй прямой
                                 [x_given, y_given], #Первый узел (здесь фактически это 2 точка первой прямой)
                                 [x[index_x_start[0]], y_start[0]], #Второй узел
                                                                # (здесь фактически это 2 точка второй прямой)
                                 x[xgi[0]:index_x_start[0]]
                                 )

    :param p1_l1: Первая точка первой прямой [x,y]
    :param p2_l1: Вторая точка первой прямой [x,y]
    :param p1_l2: Первая точка второй прямой [x,y]
    :param p2_l2: Вторая точка второй прямой [x,y]
    :param node1: Первый узел [x,y]
    :param node2: Второй узел [x,y]
    :param x_grid: Сетка по Ох на которой необходимо посчитать f(x)
    :return: Значения y=f(x) на сетке x_grid
    """

    def bernstein_poly(_i, n, t):
        """
         Полином Бернштейна стпени n, i - функция t
        """
        return comb(n, _i) * (t ** _i) * (1 - t) ** (n - _i)

    def bezier_curve_local(nodes, n_times=1000):
        """
        На основании набора узлов возвращает
        кривую Безье определяемую узлами
        Точки задаются в виде:
           [ [1,1],
             [2,3],
              [4,5], ..[Xn, Yn] ]
        nTimes - число точек для вычисления значений
        """

        n_points = len(nodes)
        x_points = np.array([p[0] for p in nodes])
        y_points = np.array([p[1] for p in nodes])

        t = np.linspace(0.0, 1.0, n_times)

        polynomial_array = np.array([bernstein_poly(_i, n_points - 1, t) for _i in range(0, n_points)])

        x_values_l = np.dot(x_points, polynomial_array)
        y_values_l = np.dot(y_points, polynomial_array)
        return x_values_l, y_values_l

    def intersect(xp1, yp1, xp2, yp2, xp3, yp3, xp4, yp4):
        """
        Функция пересечения двух прямых, заданных точками
        :param xp1: x точки 1 на прямой 1
        :param yp1: y точки 1 на прямой 1
        :param xp2: x точки 2 на прямой 1
        :param yp2: y точки 2 на прямой 1
        :param xp3: x точки 1 на прямой 2
        :param yp3: y точки 1 на прямой 2
        :param xp4: x точки 2 на прямой 2
        :param yp4: y точки 2 на прямой 2
        :return: точка пересечения прямых [x,y]
        """

        def form_line(_xp1, _yp1, _xp2, _yp2):
            k = (_yp2 - _yp1) / (_xp2 - _xp1)
            b = _yp1 - k * _xp1
            return k, b

        kl1, bl1 = form_line(xp1, yp1, xp2, yp2)
        kl2, bl2 = form_line(xp3, yp3, xp4, yp4)
        x_p_inter = (bl1 - bl2) / (kl2 - kl1)
        y_p_inter = kl1 * x_p_inter + bl1
        return x_p_inter, y_p_inter

    # Определяем точки пересечения прямых
    xl1, yl1 = intersect(p1_l1[0], p1_l1[1],
                         p2_l1[0], p2_l1[1],
                         p1_l2[0], p1_l2[1],
                         p2_l2[0], p2_l2[1])

    # Строим кривую Безье
    x_values, y_values = bezier_curve_local([node1, [xl1, yl1], node2], n_times=len(x_grid))

    # Адаптация кривой под равномерный шаг по х
    bezier_spline = interpolate.make_interp_spline(x_values, y_values, k=1, bc_type=None)
    y_values = bezier_spline(x_grid)

    return y_values


def deviator_loading_deviation(strain, deviator, fracture_strain):
    # Добавим девиации после 0.6qf для кривой без пика
    qf = max(deviator)
    deviation_1 = qf / 100
    deviation_2 = qf / 60

    i_60, = np.where(deviator >= 0.51 * qf)
    i_90, = np.where(deviator >= 0.98 * qf)
    i_end, = np.where(strain >= 0.15)
    i_xc, = np.where(strain >= fracture_strain)
    if fracture_strain >= 0.14:  # без пика
        curve = create_deviation_curve(strain[i_60[0]:i_xc[0]], deviation_1 * 2,
                                       points=np.random.uniform(3, 7), borders="zero_diff",
                                       low_first_district=1, one_side=True) + create_deviation_curve(
            strain[i_60[0]:i_xc[0]], deviation_1,
            points=np.random.uniform(20, 30), borders="zero_diff",
            low_first_district=1, one_side=True)
        deviation_array = -np.hstack((np.zeros(i_60[0]),
                                      -curve,
                                      np.zeros(len(strain) - i_xc[0])))
    else:

        try:
            i_xc1, = np.where(deviator[i_xc[0]:] <= qf - deviation_2)
            i_xc_m, = np.where(deviator >= qf - deviation_1 * 2)
            points_1 = round(fracture_strain * 100)
            if points_1 < 3:
                points_1 = 3

            curve_1 = create_deviation_curve(strain[i_60[0]:i_xc_m[0]], deviation_1 * 1.5,
                                             points=np.random.uniform(3, 4), val=(1, 0.1), borders="zero_diff",
                                             low_first_district=1) + create_deviation_curve(
                strain[i_60[0]:i_xc_m[0]], deviation_1 / 2,
                points=np.random.uniform(points_1, points_1 * 3), borders="zero_diff",
                low_first_district=1)

            points_2 = round((0.15 - fracture_strain) * 100)
            if points_2 < 3:
                points_2 = 3

            deviation_2 = ((deviator[i_xc[0]] - deviator[i_end[0]]) / 14) * (points_2 / 10)

            curve_2 = create_deviation_curve(strain[i_xc[0] + i_xc1[0]:i_end[0]],
                                             deviation_2, val=(0.1, 1),
                                             points=np.random.uniform(points_2, int(points_2 * 3)), borders="zero_diff",
                                             low_first_district=2) + create_deviation_curve(
                strain[i_xc[0] + i_xc1[0]:i_end[0]],
                deviation_2 / 3, val=(0.1, 1),
                points=np.random.uniform(points_2 * 3, int(points_2 * 5)), borders="zero_diff",
                low_first_district=2)
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          curve_1, np.zeros(i_xc[0] - i_xc_m[0]),
                                          np.zeros(i_xc1[0]),
                                          curve_2,
                                          np.zeros(len(strain) - i_end[0])))
        except (ValueError, IndexError):
            print("Ошибка девиаций девиатора")
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          create_deviation_curve(strain[i_60[0]:i_90[0]], deviation_1,
                                                                 points=np.random.uniform(3, 6), borders="zero_diff",
                                                                 low_first_district=1),
                                          create_deviation_curve(strain[i_90[0]:i_end[0]], deviation_2, val=(1, 0.1),
                                                                 points=np.random.uniform(10, 15), borders="zero_diff",
                                                                 low_first_district=3,
                                                                 one_side=True),
                                          np.zeros(len(strain) - i_end[0])))

    return deviation_array


def sensor_accuracy(x, y, fracture_strain, noise_level=1.0):
    """возвразщает зашумеленную функцию без шума в характерных точках"""

    noise = np.random.uniform(-noise_level, noise_level, len(x))
    index_qf_half, = np.where(y >= np.max(y) / 2)
    index_qf, = np.where(y >= np.max(y))
    if fracture_strain > max(x):  # если хс последня точка в массиве или дальше
        index_qf, = np.where(x >= max(x))
    for _i in range(len(y)):  # наложение шума кроме промежутков для характерных точек
        is_excluded_points = (_i < index_qf_half[0] - 2) or \
                             ((_i > index_qf_half[0] + 2) and ([_i] < index_qf[0] - 2)) or \
                             (_i > index_qf[0] + 2)
        if is_excluded_points:
            if y[_i] + noise[_i] < np.max(y):
                y[_i] = y[_i] + noise[_i]
            else:
                # в районе максимума шум меньше первоначального
                y[_i] = y[_i] - np.random.uniform(0.1, 0.5) * noise_level
    return y


def hevisaid(x, offset, smoothness):
    """возвращет функцию Хевисайда 0<=y<=1, которая задает коэффициент влияния kp

    :param x: точки, в которых вычислять значение
    :param offset: смещение относительно х=0
    :param smoothness: гладкость перехода, при smoothness = 0 выраждается в фукнцию Хевисаида
    """
    return 1. / (1. + np.exp(-2 * 10 / smoothness * (x - offset)))


def smoothness_condition(strain_at_50_percent_strength):
    """возвращает предельное значение fracture_strain при котором возможно
    построение заданной функции

    :param strain_at_50_percent_strength: деформация в 50% прочности
    """
    SMOOTHNESS_OFFSET = 0.6 / 100  # 0.6 возможно является максимальным х на сетке
    return 2 * strain_at_50_percent_strength + SMOOTHNESS_OFFSET


def gaus(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """функция Гаусса для участка x>fracture_strain"""
    gaus_height = qf - residual_strength  # высота функции Гаусса
    gaus_smoothness = (-1) * np.log(0.1 / gaus_height) / ((residual_strength_strain - fracture_strain) ** 2)
    # резкость функции Гаусаа (считается из условия равенства заданной точности в точке х50
    return gaus_height * (np.exp(-gaus_smoothness * ((x - fracture_strain) ** 2))) + residual_strength


def parab(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """Парабола для участка x>fracture_strain """
    # k*x^2 + b
    k_par = -((residual_strength - qf) / (residual_strength_strain - fracture_strain) ** 2)
    return -k_par * ((x - fracture_strain) ** 2) + qf


def gip_exp_tg(x, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator):
    """возвращает координаты y итоговой фукнции по законам гиперболы, экспоненты и тангенса"""
    # Константы
    E50_LIMIT = 70000
    '''Е50 после которого необходимо переходить от эспоненты к тангенсу'''
    OC_STRAIN_CUT = 0.151
    '''значение по которому обрезается точка х переуплотнния'''
    ZERO_OFFSET = 0.000001
    '''смещение для расчета 0 значений в особенностях'''

    influence_ratio_hyperbole_or_exp = 1.
    '''influence_ratio_hyperbole_or_exp - линейный коэффициент учета влияния функции гиперболы и экспоненты'''

    OC_influence_ratio = np.full(len(x), 1)
    '''OC_influence_ratio - коэффициент влияния на influence_ratio_hyperbole_or_exp,
     учитывающий переуплотнение OC_deviator для переуплотнения'''

    if E50 <= E50_LIMIT:
        influence_ratio_hyperbole_or_exp = 1. / 68000. * E50 - 1. / 34
    elif E50 > E50_LIMIT:
        influence_ratio_hyperbole_or_exp = 1.

    def exponent_error(height_smoothness: list):
        """возвращает ошибки в коэффициентах, вычисляются в точках qf и qf/2

        :param height_smoothness: list : exp_relative_height, exp_smoothness
        """
        _exp_relative_height, _exp_smoothness = height_smoothness  # коэффициенты экспоненты
        return -1 * _exp_relative_height * (np.exp(-_exp_smoothness * strain_at_50_strength) - 1) - qf / 2, \
               -1 * _exp_relative_height * (np.exp(-_exp_smoothness * fracture_strain) - 1) - qf

    def tan_error(half_height_smoothness):
        """возвращает ошибки в коэффициентах арктангенса, вычисляются в точках qf и qf/2"""
        _tan_half_height, _tan_smoothness = half_height_smoothness  # коэффициенты тангенса
        return (_tan_half_height * ((np.arctan(_tan_smoothness * strain_at_50_strength)) / (0.5 * np.pi)) - qf / 2,
                _tan_half_height * ((np.arctan(_tan_smoothness * fracture_strain)) / (0.5 * np.pi)) - qf)

    if E50 > 40000:
        # начальные приближения для расчета коэффициентов
        exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, np.array([1, 1]))
        initial_exp_relative_height = 1
        error = exponent_error([exp_relative_height, exp_smoothness])

        # персчет значений при ошибках построения
        while abs(error[0]) >= 10 or abs(error[1]) >= 10:
            initial_exp_relative_height += 1
            exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, np.array([initial_exp_relative_height, 1]))
            error = exponent_error([exp_relative_height, exp_smoothness])

    else:
        # начальные приближения для расчета коэффициентов
        initial_exp_relative_height, initial_exp_smoothness = 600, 1
        _initial = np.array([initial_exp_relative_height, initial_exp_smoothness])
        exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, _initial)

        initial_exp_relative_height = 1
        error = exponent_error([exp_relative_height, exp_smoothness])

        # персчет значений при ошибках построения
        WHILE_COUNT = 0

        # пока

        def is_negative():
            return (exp_relative_height <= 0) or (exp_smoothness <= 0)

        # пока

        def is_not_changed():
            return exp_relative_height == initial_exp_relative_height or exp_smoothness == initial_exp_smoothness

        # пока произведение коээфициентов (приблизительно равно E50) меньше 1000
        def is_lower_1000():
            return exp_relative_height * exp_smoothness < 1000

        # пока
        def is_error(_error):
            """превышение переменной error предела на ошибку EPS"""
            EPS = 550
            return abs(_error[0]) >= EPS or abs(_error[1]) >= EPS

        while is_negative() or is_not_changed() or is_lower_1000() or (is_error(error) and WHILE_COUNT < 50):
            initial_exp_relative_height += 1
            _initial = np.array([initial_exp_relative_height, initial_exp_smoothness])
            exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, _initial)
            error = exponent_error([exp_relative_height, exp_smoothness])
            if is_error(error):
                WHILE_COUNT += 1

    # коэффициенты гиперболы
    hyp_x_offset = -2 / fracture_strain + 1 / strain_at_50_strength
    hyp_y_offset = qf * (hyp_x_offset * strain_at_50_strength + 1.) / (2. * strain_at_50_strength)

    def dev_load_hyp(_x):
        """считает значения гиперболы на х, коэффициенты созависимы"""
        return hyp_y_offset * _x / (1 + hyp_x_offset * _x)

    def dev_load_exp(_x):
        """считает значения экспоненты на х"""
        return -exp_relative_height * (np.exp(-exp_smoothness * _x) - 1)

    if E50 > 50000:
        tan_half_height, tan_smoothness, *_ = fsolve(tan_error, np.array([1, 1]))
    else:
        tan_half_height, tan_smoothness, *_ = fsolve(tan_error, np.array([600, 1]))

    # изначальный расчет возвращаемой фукнции
    result_y = (OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x) + \
               (1. - OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_exp(x)

    OC_strain = 0.  # абцисса точки переуплотнения

    if (OC_deviator != 0) & (OC_deviator <= qf / 2):
        # если OC_deviator находится до qf/2, то OC_strain рассчитывается из функции гиперболы
        OC_strain = OC_deviator / (hyp_y_offset - OC_deviator * hyp_x_offset)

        _i, = np.where(x > OC_strain)
        if _i.size >= 1:
            _i = _i[0]

            _hevisaid_smoothness = abs(10 * (strain_at_50_strength - OC_strain + ZERO_OFFSET))
            _hevisaid_part = 2 * hevisaid(x[_i:], OC_strain, _hevisaid_smoothness) - 1
            OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part))

            if OC_deviator == qf / 2:
                OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), np.full(len(x[_i:]), 1.0)))

            j, = np.where(x > strain_at_50_strength)
            if j.size >= 1:
                j = j[0]
                hyp_part = (1 - OC_influence_ratio[:_i] * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x[:_i])
                exp_part = (OC_influence_ratio[:_i] * influence_ratio_hyperbole_or_exp) * dev_load_exp(x[:_i])
                before_i_part = hyp_part + exp_part

                hyp_part = (1 - OC_influence_ratio[_i:j] * (1 - influence_ratio_hyperbole_or_exp)) * dev_load_hyp(
                    x[_i:j])
                exp_part = (OC_influence_ratio[_i:j] * (1 - influence_ratio_hyperbole_or_exp)) * dev_load_exp(x[_i:j])
                middle_part = hyp_part + exp_part

                hyp_part = (OC_influence_ratio[j:] * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x[j:])
                exp_part = (1. - OC_influence_ratio[j:] * influence_ratio_hyperbole_or_exp) * dev_load_exp(x[j:])
                after_j_part = hyp_part + exp_part

                result_y = np.hstack((before_i_part, middle_part, after_j_part))

            else:

                hyp_part = (1. - OC_influence_ratio[:_i] * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x[:_i])
                exp_part = (OC_influence_ratio[:_i] * influence_ratio_hyperbole_or_exp) * dev_load_exp(x[:_i])
                before_i_part = hyp_part + exp_part
                hyp_part = (1. - OC_influence_ratio[_i:] * (1 - influence_ratio_hyperbole_or_exp)) * dev_load_hyp(
                    x[_i:])
                exp_part = (OC_influence_ratio[_i:] * (1 - influence_ratio_hyperbole_or_exp)) * dev_load_exp(x[_i:])
                after_i_part = hyp_part + exp_part
                result_y = np.hstack((before_i_part, after_i_part))
        else:
            OC_influence_ratio = np.full(len(x), 0.0)
            hyp_part = (OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x)
            exp_part = (1. - OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_exp(x)
            result_y = hyp_part + exp_part

    # если OC_deviator находится после qf/2 и E50 находится до E50_LIMIT
    # то OC_strain рассчитывается из функции экспоненты
    elif (OC_deviator != 0.) & (OC_deviator > qf / 2.) & (E50 <= E50_LIMIT):

        def oc_strain_exp_error(xocr_calc):
            """возвращает ошибку вычисления OC_strain в точке переуплотнения через фукнцию экспоненты"""
            return -exp_relative_height * (np.exp(-exp_smoothness * xocr_calc) - 1) - OC_deviator

        OC_strain, *_ = fsolve(oc_strain_exp_error, np.array(0))

        # обрезка точки переуплотнения, чтобы избежать ошибок в расчетах
        if OC_strain > OC_STRAIN_CUT:
            OC_strain = OC_STRAIN_CUT

        if OC_deviator > (0.8 * qf):
            OC_influence_ratio = np.full(len(x), 0.0)
        else:
            _i, = np.where(x > OC_strain)
            assert _i.size > 0, "Нет точек х после OC_strain ?"
            _i = _i[0]
            j, = np.where(x > fracture_strain)
            if j.size < 1:
                _hevisaid_smoothness = ((abs(OC_strain - strain_at_50_strength)) /
                                        (influence_ratio_hyperbole_or_exp + ZERO_OFFSET)) * 10
                _hevisaid_part = 2 * hevisaid(x[_i:], OC_strain, _hevisaid_smoothness) - 1
                OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part))

            else:
                j = j[0]
                _hevisaid_smoothness = ((abs(OC_strain - strain_at_50_strength)) /
                                        (influence_ratio_hyperbole_or_exp + ZERO_OFFSET)) * 10
                _hevisaid_part = 2 * hevisaid(x[_i:j], OC_strain, _hevisaid_smoothness) - 1
                OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part, np.full(len(x[j:]), 1.0)))

        result_y = ((OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x) +
                    (1. - OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_exp(x))

    # если OC_deviator находится после qf/2 и E50 находится после E50_LIMIT,
    # то OC_strain рассчитывается из функции тангенса, так как переуплотнение плавнее
    elif (OC_deviator != 0.) & (OC_deviator > qf / 2.) & (E50 > E50_LIMIT):

        def oc_strain_tan_error(_OC_strain):
            """возвращает ошибку вычисления OC_strain в точке переуплотнения через фукнцию тангенса"""
            return tan_half_height * ((np.arctan(tan_smoothness * _OC_strain)) / (0.5 * np.pi)) - OC_deviator

        OC_strain, *_ = fsolve(oc_strain_tan_error, np.array(0))

        # обрезка точки переуплотнения, чтобы избежать ошибок в расчетах
        if OC_strain > OC_STRAIN_CUT:
            OC_strain = OC_STRAIN_CUT

        if OC_deviator > (0.8 * qf):
            OC_influence_ratio = np.full(len(x), 0.0)
        else:
            _i, = np.where(x > OC_strain)
            assert _i.size > 0, "Нет точек х после OC_strain ?"
            _i = _i[0]
            _j, = np.where(x > fracture_strain)
            if _j.size < 1:
                _hevisaid_smoothness = ((abs(OC_strain - strain_at_50_strength)) /
                                        (influence_ratio_hyperbole_or_exp + ZERO_OFFSET)) * 10
                _hevisaid_part = 2 * hevisaid(x[_i:], OC_strain, _hevisaid_smoothness) - 1
                OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part))
            else:
                _j = _j[0]
                _hevisaid_smoothness = ((abs(OC_strain - strain_at_50_strength)) /
                                        (influence_ratio_hyperbole_or_exp + ZERO_OFFSET)) * 10
                _hevisaid_part = 2 * hevisaid(x[_i:_j], OC_strain, _hevisaid_smoothness) - 1
                OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part, np.full(len(x[_j:]), 1.0)))

        j, = np.where(x > strain_at_50_strength)
        assert j.size > 0, "Нет точек х больше strain_at_50_strength ?"
        j = j[0]
        hyp_part = (OC_influence_ratio[:j] * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x[:j])
        exp_part = (1. - OC_influence_ratio[:j] * influence_ratio_hyperbole_or_exp) * dev_load_exp(x[:j])
        before_j_part = hyp_part + exp_part
        hyp_part = (OC_influence_ratio[j:] * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x[j:])
        tan_part = (1. - OC_influence_ratio[j:] * influence_ratio_hyperbole_or_exp) * \
                   (tan_half_height * ((np.arctan(tan_smoothness * x[j:])) / (0.5 * np.pi)))
        after_j_part = hyp_part + tan_part
        result_y = np.hstack((before_j_part, after_j_part))

    # ограничение на OC_deviator (если ограничение не выполняется, то
    # строится сумма функций экспоненты и кусочной функции синуса и параболы для E50<=E50_LIMIT и
    # тангенса и кусочной функции синуса и параболы для E50>E50_LIMIT
    elif OC_deviator > (0.8 * qf):
        OC_influence_ratio = np.full(len(x), 0)
        result_y = ((OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x) +
                    (1. - OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_exp(x))

    return result_y, OC_strain


def cos_par(x, E50, qf, strain_at_50_strength, fracture_strain, correction=0):
    """возвращает функцию косинуса
     и параболы для участка strain_at_50_strength qf"""

    SHIFT = (fracture_strain - strain_at_50_strength) / 2
    '''смещение: коэффицент учитывающий влияние на высоту функции при различных значениях E50'''

    if E50 < 5340:
        vl = 0
    elif (E50 <= 40000) and (E50 >= 5340):
        kvl = 1 / 34660
        bvl = -5340 * kvl
        vl = kvl * E50 + bvl  # 1. / 40000. * E50 - 1. / 8
    elif E50 > 40000:
        vl = 1.
    else:
        vl = None

    height = 0.035 * qf * vl - correction  # высота функции
    if height < 0:
        height = 0

    k_of_parab = height / (-fracture_strain + strain_at_50_strength + SHIFT) ** 2

    # фиромирование функции
    # if x is greater then strain_at_50_strength : x_gr_x50
    _i, = np.where(x > strain_at_50_strength)
    x_low_x50 = x[:_i[0]] if _i.size > 0 else x
    x_gr_x50 = x[_i[0]:] if _i.size > 0 else np.array([])

    # if x is greater then strain_at_50_strength + SHIFT : x_gr_x50sm
    j, = np.where(x_gr_x50 > strain_at_50_strength + SHIFT)
    x_gr_x50_low_x50sm = x_gr_x50[:j[0]] if j.size > 0 else x_gr_x50
    x_gr_x50sm = x_gr_x50[j[0]:] if j.size > 0 else np.array([])

    # if x is greater then fracture_strain : x_gr_xc
    l, = np.where(x_gr_x50sm > fracture_strain)
    x_gr_x50sm_low_xc = x_gr_x50sm[:l[0]] if l.size > 0 else x_gr_x50sm
    x_gr_xc = x_gr_x50sm[l[0]:] if l.size > 0 else np.array([])

    _first_zero_part = np.full(len(x_low_x50), 0)
    _cos_part = (height * 0.5 * (np.cos((1. / SHIFT) *
                                        np.pi * (x_gr_x50_low_x50sm - strain_at_50_strength) - np.pi) + 1))
    _parab_part = (-1) * k_of_parab * (x_gr_x50sm_low_xc - strain_at_50_strength - SHIFT) ** 2 + height
    _last_zero_part = np.full(len(x_gr_xc), 0)

    return np.hstack((_first_zero_part, _cos_part, _parab_part, _last_zero_part))


def loop(x, y, Eur, unload_deviator, re_load_deviator, noise_params=None):
    """Рассчитывает петлю разгрузки -- повторного нагружения
    :param x: массив значений x
    :param y: массив значений y
    :param Eur: recommended: 3*E50
    :param unload_deviator: девиатор разгрузки
    :param re_load_deviator: девиатор повторной нагрузки
    :param noise_params: optional, default None, параметры для моделирования шума list[float, float]

    Returns
    --------
    loop_x -- x координаты петли \n
    loop_y -- y координаты петли \n
    connection_indexes -- tuple[index_connection_unload[0], index_connection_return_on_load[0])]\n
    loop_indexes -- tuple[real_unload_index, real_re_load_index, real_return_on_load_index]\n
    loop_strain_values --tuple[unload_strain, re_load_strain, return_on_load_point_strain]\n
    """

    # индекс 1 точки
    index_unload_point, = np.where(y >= unload_deviator)

    if not np.size(index_unload_point) > 0:
        unload_deviator = np.max(y)
        index_unload_point, = np.where(y >= unload_deviator)

    index_unload_point = index_unload_point[0]

    # точка появления петли
    unload_strain = x[index_unload_point]
    unload_deviator = y[index_unload_point]

    # точка конца петли
    index_re_load_point, = np.where(y == np.max(y))
    index_re_load_point = index_re_load_point[-1]

    k = (0.3 / (-x[index_re_load_point])) * unload_strain + 0.4
    dynamic_ratio = -3 * 10 ** (-9) * Eur + k * unload_strain  # 0.00095

    # Точка возврата на кривую
    return_on_load_point_strain = unload_strain + dynamic_ratio
    assert return_on_load_point_strain < x.max(), "Ошибка построения петли при заданном Eur"
    index_return_on_load, = np.where(x >= return_on_load_point_strain)
    index_return_on_load = index_return_on_load[0]
    # задаем последнюю точку в общем массиве кривой девиаторного нагружения
    return_on_load_point_strain = x[index_return_on_load]
    if return_on_load_point_strain <= unload_strain:
        index_return_on_load = index_unload_point + 1
        return_on_load_point_strain = x[index_return_on_load]
    return_on_load_deviator = y[index_return_on_load]

    D1_return_on_load = (y[index_return_on_load + 1] - y[index_return_on_load]) / \
                        (x[index_return_on_load + 1] - x[index_return_on_load])
    '''производная кривой девиаторного нагружения в точке конца петли'''

    E0 = (y[1] - y[0]) / (x[1] - x[0])  # производная кривой девиаторного нагружения в 0
    # ограничение на E0 (не больше чем модуль петли разгрузки)
    if E0 < Eur:
        E0 = 1.1 * Eur

    # ограничение на угол наклона участка повтороной нагрузки,
    # чтобы исключить пересечение петли и девиаторной кривой
    min_E0 = unload_deviator / unload_strain  # максимальный угол наклона петли

    # коррекция Eur
    if Eur < 1.1 * min_E0:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        Eur = 1.1 * min_E0
        E0 = 1.1 * Eur

    # вычисляется из оординаты и угла наклона петли
    re_load_strain = (re_load_deviator - unload_deviator + Eur * unload_strain) / Eur
    index_re_load, = np.where(x >= re_load_strain)
    index_re_load = index_re_load[0]
    re_load_strain = x[index_re_load]

    # если точка 2 совпадает с точкой один или правее, то меняем точку 2 на предыдущую
    if index_re_load >= index_unload_point:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        index_re_load = index_unload_point - 1
        re_load_strain = x[index_re_load]

    # участок разгрузки
    unload_part_x = np.linspace(unload_strain, re_load_strain,
                                int(abs(re_load_strain - unload_strain) / (x[1] - x[0]) + 1))
    # участок повторной нагрузки
    reload_part_x = np.linspace(re_load_strain, return_on_load_point_strain,
                                int(abs(return_on_load_point_strain - re_load_strain) / (x[1] - x[0]) + 1))

    # 0.8 * Eur + 60000  # производная в точке начала разгрузки (близка к бесконечности) #???
    dynamic_D1 = 2 * Eur

    # формируем разгрузку
    spline_unload = interpolate.make_interp_spline([re_load_strain, unload_strain],
                                                   [re_load_deviator, unload_deviator], k=3,
                                                   bc_type=([(2, 0)], [(1, dynamic_D1)]))
    unload_part_y = spline_unload(unload_part_x)  # участок разгрузки

    # формируем повторное нагружение
    point_1_l1 = [re_load_strain - 0.2 * re_load_strain,
                  E0 * (re_load_strain - 0.2 * re_load_strain) +
                  (re_load_deviator - E0 * re_load_strain)]
    point_2_l1 = [re_load_strain, re_load_deviator]
    point_1_l2 = [return_on_load_point_strain, return_on_load_deviator]
    point_2_l2 = [return_on_load_point_strain - 0.1 * return_on_load_point_strain,
                  D1_return_on_load * (return_on_load_point_strain - 0.1 * return_on_load_point_strain) +
                  (return_on_load_deviator - D1_return_on_load * return_on_load_point_strain)]

    _bezier_curve = bezier_curve(point_1_l1, point_2_l1, point_1_l2, point_2_l2,
                                 [re_load_strain, re_load_deviator],
                                 [return_on_load_point_strain, return_on_load_deviator],
                                 reload_part_x)
    reload_part_y = _bezier_curve

    # устраняем повторяющуюся точку 2
    reload_part_x = reload_part_x[1:]
    reload_part_y = reload_part_y[1:]

    # соединяем  участки разгрузки и нагрузки в петлю
    loop_x = np.hstack((unload_part_x, reload_part_x))

    # определяем индексы, по которым будет петля будет "крепиться" к исходной кривой
    index_connection_unload, = np.where(x >= unload_strain)
    index_connection_return_on_load, = np.where(x >= return_on_load_point_strain)

    if noise_params:
        unload_part_y = unload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(unload_part_y))
        reload_part_y = reload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(reload_part_y))
        unload_part_y = discrete_array(unload_part_y, noise_params[1])
        reload_part_y = discrete_array(reload_part_y, noise_params[1])

    loop_y = np.hstack((unload_part_y, reload_part_y))

    real_unload_index = index_connection_unload[0] + 1
    # первая точка петли на самом деле принадлежит исходной кривой
    real_re_load_index = index_connection_unload[0] + len(unload_part_y)
    # -1 + 1 = 0 т.к. самая нижняя точка петли принадлежит разгрузке
    real_return_on_load_index = index_connection_unload[0] + len(loop_x) - 2
    # -1 - 1 = -2 т.к. последняя точка петли так же на самом деле принадлежит кривой

    # Для присоединения петли к исходной кривой
    connection_indexes = (index_connection_unload[0], index_connection_return_on_load[0])
    #
    loop_indexes = (real_unload_index, real_re_load_index, real_return_on_load_index)
    #
    # Для работы фукнции объемной деформации
    loop_strain_values = (unload_strain, re_load_strain, return_on_load_point_strain)
    #

    return loop_x, loop_y, connection_indexes, loop_indexes, loop_strain_values


def dev_loading(qf, E50, **kwargs):
    """
    Кусочная функция: на участке [0,fracture_strain]-сумма функций гиперболы и
    (экспоненты или тангенса) и кусочной функции синуса и парболы
    на участке [fracture_strain...]-половина функции Гаусса или параболы

    :param qf: double
        qf
    :param E50: double
        E50
    :param kwargs: optional:
        fracture_strain;
        residual_strength_strain;
        residual_strength;
        OC_deviator;
        gaus_or_par;
        amount_points;
        Eur, default None, True для петли;
        unload_deviator;
        re_load_deviator;
        noise_off, default None, True для отключения шумов и "ступеней";
    :return: strain_required_grid - х координаты полученной кривой;
        deviator_required_grid - у координаты полученной кривой;
        [[strain_at_50_strength, qf / 2], [OC_strain, OC_deviator], [fracture_strain, qf],
         [residual_strength_strain, residual_strength]] - расчетные параметры;
        loop_strain_values if Eur, tuple - strain координаты точек петли;
        loop_indexes if Eur, tuple - индексы самой петли, точки кривой не включены
    """

    # Константы
    STRAIN_LIMIT = 0.15
    STRAIN_CALC_LIMIT = 0.6
    NOISE_LEVEL = 1.0
    DISCRETE_ARRAY_LEVEL = 0.5
    DISCRETE_ARRAY_LOOP_LEVEL = 2 * DISCRETE_ARRAY_LEVEL
    #
    _0002_QF = 0.002 * qf

    # Параметры
    try:
        kwargs["fracture_strain"]
    except KeyError:
        kwargs["fracture_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength_strain"]
    except KeyError:
        kwargs["residual_strength_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength"]
    except KeyError:
        kwargs["residual_strength"] = qf

    try:
        kwargs["OC_deviator"]
    except KeyError:
        kwargs["OC_deviator"] = 0

    try:
        kwargs["gaus_or_par"]
    except KeyError:
        kwargs["gaus_or_par"] = 0

    try:
        kwargs["amount_points"]
    except KeyError:
        kwargs["amount_points"] = 700

    try:
        kwargs["Eur"]
    except KeyError:
        kwargs["Eur"] = None

    try:
        kwargs["unload_deviator"]
    except KeyError:
        kwargs["unload_deviator"] = 0.8 * qf

    try:
        kwargs["re_load_deviator"]
    except KeyError:
        kwargs["re_load_deviator"] = 10

    try:
        kwargs["noise_off"]
    except KeyError:
        kwargs["noise_off"] = None

    #
    fracture_strain = kwargs.get('fracture_strain')
    residual_strength_strain = kwargs.get('residual_strength_strain')
    residual_strength = kwargs.get('residual_strength')
    OC_deviator = kwargs.get('OC_deviator')
    gaus_or_par = kwargs.get('gaus_or_par')  # 0 - гаус, 1 - парабола
    amount_points = kwargs.get('amount_points')
    Eur = kwargs.get('Eur')
    unload_deviator = kwargs.get('unload_deviator')
    re_load_deviator = kwargs.get('re_load_deviator')
    noise_off = kwargs.get("noise_off")

    if noise_off:
        NOISE_LEVEL = None
        DISCRETE_ARRAY_LEVEL = None
        DISCRETE_ARRAY_LOOP_LEVEL = None
    # расчёт ведется с числом точек amount_points на длине STRAIN_CALC_LIMIT
    AMOUNT_POINTS_ON_CALC = int((amount_points * STRAIN_CALC_LIMIT / STRAIN_LIMIT) / (STRAIN_CALC_LIMIT / STRAIN_LIMIT))
    # значения будут возвращаться с числом точек amount_points но на длине STRAIN_LIMIT
    AMOUNT_POINTS_ON_RETURN = int(AMOUNT_POINTS_ON_CALC * (STRAIN_CALC_LIMIT / STRAIN_LIMIT))

    # Ограничения
    if unload_deviator > qf:
        unload_deviator = qf
    if unload_deviator < 20.0:
        unload_deviator = 20.0
    if fracture_strain > 0.11:
        fracture_strain = 0.15
    if residual_strength >= qf:
        residual_strength = qf
    strain_at_50_strength = (qf / 2.) / E50
    if fracture_strain < strain_at_50_strength:
        fracture_strain = strain_at_50_strength * 1.1  # хс не может быть меньше strain_at_50_strength

    # Сетки
    strain = np.linspace(0, STRAIN_CALC_LIMIT, AMOUNT_POINTS_ON_CALC)

    # Начало построения фукнции

    # считаем предельное значение fracture_strain
    fracture_strain_limit = smoothness_condition(strain_at_50_strength)

    if strain_at_50_strength >= fracture_strain:
        # если strain_at_50_strength > fracture_strain, fracture_strain сдвигается в 0.15,
        # х2,residual_strength перестает учитываться,
        # в качестве функции используется сумма гиперболы, экспоненты или тангенса и функции синуса и параболы

        fracture_strain = STRAIN_LIMIT
        #
        deviator, OC_strain = gip_exp_tg(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #

        if fracture_strain <= fracture_strain_limit:
            # проверка на условие гладкости, если условие не соблюдается
            # передвинуть xс в предельное значение
            fracture_strain = fracture_strain_limit
            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = gip_exp_tg(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #

        # residual_strength_strain,residual_strength не выводится
        residual_strength_strain = fracture_strain
        residual_strength = qf

    else:
        #
        deviator, OC_strain = gip_exp_tg(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #
        if fracture_strain <= fracture_strain_limit:
            fracture_strain = fracture_strain_limit

            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = gip_exp_tg(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            #

        if fracture_strain > STRAIN_LIMIT:
            #
            deviator, OC_strain = gip_exp_tg(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #
            # residual_strength_strain,residual_strength не выводится
            residual_strength_strain = fracture_strain
            residual_strength = qf

        else:
            # минимально допустимое расстояния между хс и х2
            if fracture_strain >= 0.8 * residual_strength_strain:
                residual_strength_strain = 1.2 * fracture_strain
            # минимально допустимое расстояние мужду residual_strength и qf
            if residual_strength >= qf:
                residual_strength = 0.98 * qf

            # Примеряем положение кривой - оно не должно быть выше qf
            _i, = np.where(strain >= fracture_strain)  # >= намеренно
            _i = _i[0]
            _gip_exp_tg, *_ = gip_exp_tg(strain[:_i], E50, qf, strain_at_50_strength,
                                         fracture_strain, OC_deviator)
            _cos_par = cos_par(strain[:_i], E50, qf, strain_at_50_strength, fracture_strain)
            maximum = max(np.hstack((_gip_exp_tg + _cos_par, np.full(len(strain[_i:]), 0.0)))
                          if _i.size > 0 else np.full(len(strain), 0.0))

            is_max_lower_qf = maximum < (qf + _0002_QF)

            _i, = np.where(strain > fracture_strain)  # > намеренно
            if is_max_lower_qf:
                correction = 0
            else:
                # если максимум суммарной функции на участке от 0 до хс превышает qf, то уменьшаем
                # высоту функции синуса и параболы на величину разницы в точке fracture_strain
                correction = abs(maximum - qf + 2 * _0002_QF)

            if _i.size > 0:
                _i = _i[0]
                _gip_exp_tg, *_ = gip_exp_tg(strain[:_i], E50, qf, strain_at_50_strength,
                                             fracture_strain, OC_deviator)
                _cos_par = cos_par(strain[:_i], E50, qf, strain_at_50_strength,
                                   fracture_strain, correction)
                if gaus_or_par == 1:
                    _gaus_or_par = parab(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                         residual_strength)
                else:
                    _gaus_or_par = gaus(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                        residual_strength)
                deviator = np.hstack((_gip_exp_tg + _cos_par, _gaus_or_par))

            else:
                deviator = (strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)[0] \
                           + cos_par(strain, E50, qf, strain_at_50_strength, fracture_strain, correction)

    if OC_deviator > (0.8 * qf):  # не выводить точку OC_strain, OC_deviator
        OC_strain = fracture_strain
        OC_deviator = qf

    # переход к нужной сетке (strain_required_grid необходимо обрезать по х = STRAIN_LIMIT чтобы получить amount_points
    strain_required_grid = np.linspace(strain.min(initial=None), strain.max(initial=None), AMOUNT_POINTS_ON_RETURN)
    # интерполяция  для сглаживания в пике
    spl = make_interp_spline(strain, deviator, k=5)
    deviator_required_grid = spl(strain_required_grid)

    loop_indexes = None

    def noise(result):
        """На кладывает девиации, шум и дискретизацию в соответствии с NOISE_LEVEL и DISCRETE_ARRAY_LEVEL"""
        if not noise_off:
            result += deviator_loading_deviation(strain_required_grid, result, fracture_strain)
            result = sensor_accuracy(strain_required_grid, result, fracture_strain, noise_level=NOISE_LEVEL)
            result = discrete_array(result, DISCRETE_ARRAY_LEVEL)
        return result

    if Eur:
        x_loop, y_loop, connection_to_curve_indexes, loop_indexes, loop_strain_values = \
            loop(strain_required_grid, deviator_required_grid, Eur, unload_deviator, re_load_deviator,
                 [NOISE_LEVEL, DISCRETE_ARRAY_LOOP_LEVEL] if not noise_off else None)

        #
        # deviator_required_grid = noise(deviator_required_grid)

        deviator_required_grid = np.hstack((deviator_required_grid[:connection_to_curve_indexes[0]], y_loop,
                                            deviator_required_grid[connection_to_curve_indexes[1] + 1:]))
        strain_required_grid = np.hstack((strain_required_grid[:connection_to_curve_indexes[0]], x_loop,
                                          strain_required_grid[connection_to_curve_indexes[1] + 1:]))
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.
    else:
        # deviator_required_grid = noise(deviator_required_grid)
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.

    # наложение хода штока и обрезка функций
    # rod_move_result = initial_free_rod_move(strain_required_grid,
    #                                         deviator_required_grid,
    #                                         strain_cut=STRAIN_LIMIT,
    #                                         noise=(NOISE_LEVEL, DISCRETE_ARRAY_LEVEL) if not noise_off else None)
    # strain_required_grid = rod_move_result[0]
    # deviator_required_grid = rod_move_result[1]
    # len_rod_move = rod_move_result[2]
    loop_indexes_with_rod = None if not Eur else (loop_indexes[i] + len_rod_move for i in range(len(loop_indexes)))

    return strain_required_grid, deviator_required_grid, [[strain_at_50_strength, qf / 2], [fracture_strain, qf], [residual_strength_strain, residual_strength]]


def initial_free_rod_move(strain, deviator, strain_cut=0.151, noise=None):
    """
    Обрезает strain и deviator по strain_cut и
    возвращает strain, deviator с присоединенным ходом штока и длину хода штока (в точках)

    :param strain:
    :param deviator:
    :param strain_cut: optional, default = 0.151, значение, по которому обрезаются массивы
    :param noise: optional, default None, параметры для моделирования шума tuple[float, float]

    Returns
    -------
    strain -- cut strain with rod \n
    deviator -- cut deviator with rod \n
    len_rod_move -- len of rod in points: len(strain_start)
    """
    _i, = np.where(strain > strain_cut)
    assert _i.size > 0, "Ошибка обрезки, strain_cut не может быть больше max(strain)"
    strain = strain[:_i[0]]
    deviator = deviator[:_i[0]]

    strain_last_point = np.random.uniform(0.005, 0.01) - (strain[-1] - strain[-2])
    '''положительная последняя точка х для метрвого хода штока'''

    strain_start = np.linspace(0, strain_last_point, int(strain_last_point / (strain[-1] - strain[-2])) + 1)
    '''положительный масив х для метрвого хода штока'''

    SLANT = np.random.uniform(20, 30)
    '''наклон функции экспоненты'''
    AMPLITUDE = np.random.uniform(15, 25)
    '''высота функции экспоненты'''

    # определяем абциссу метрвого хода штока
    deviator_start = exponent(strain_start, AMPLITUDE, SLANT)
    # смещение массива x для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    strain_start -= strain_start[-1] + (strain[-1] - strain[-2])
    # смещение массива y для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    deviator_start -= deviator_start[-1]

    if noise:
        assert len(noise) == 2, "noise должен содерждать значение для шума и значение для уровня ступеней"
        deviator_start = deviator_start + np.random.uniform(-noise[0], noise[0], len(deviator_start))
        deviator_start = discrete_array(deviator_start, noise[1])  # наложение ступенчватого шума на мертвый ход штока

    strain = np.hstack((strain_start, strain))  # добавление начального участка в функцию девиаторного нагружения
    strain += abs(strain[0])  # смещение начала кривой девиаторного нагруружения в 0

    deviator = np.hstack((deviator_start, deviator))  # добавление начального участка в функцию девиаторного нагружения
    deviator += abs(deviator[0])  # смещение начала кривой девиаторного нагружения в 0
    deviator[0] = 0.  # искусственное зануление первой точки

    len_rod_move = len(strain_start)

    return strain, deviator, len_rod_move









#------------------------------------------------------------------------------------------------------------------------


def bezier_curve_gip(p1_l1, p2_l1, p1_l2, p2_l2, node1, node2, x_grid):
    """
    Требуется модуль: from scipy.optimize import fsolve
    Функция построения кривой Безье на оссновании двух прямых,
    задаваемых точками 'point_line' типа [x,y],
    на узлах node типа [x,y]
    с построением промежуточного узла в точке пересечения поданных прямых.
    Функция возвращает значения y=f(x) на сетке по оси Ox.

    Пример:
    Соединяем две прямые от точки [x_given,y_given] до точки [x[index_x_start[0]], y_start[0]]
    xgi, = np.where(x > x_given) # некая точка после которой нужно переходить к кривой безье
    y_Bezier_line = bezier_curve([0,0],[x_given,y_given], #Первая и Вторая точки первой прямой
                                 [x_given, k * x_given + b], #Первая точка второй прямой (k и b даны)
                                 [x[index_x_start[0]],y_start[0]], #Вторая точка второй прямой
                                 [x_given, y_given], #Первый узел (здесь фактически это 2 точка первой прямой)
                                 [x[index_x_start[0]], y_start[0]], #Второй узел
                                                                # (здесь фактически это 2 точка второй прямой)
                                 x[xgi[0]:index_x_start[0]]
                                 )

    :param p1_l1: Первая точка первой прямой [x,y]
    :param p2_l1: Вторая точка первой прямой [x,y]
    :param p1_l2: Первая точка второй прямой [x,y]
    :param p2_l2: Вторая точка второй прямой [x,y]
    :param node1: Первый узел [x,y]
    :param node2: Второй узел [x,y]
    :param x_grid: Сетка по Ох на которой необходимо посчитать f(x)
    :return: Значения y=f(x) на сетке x_grid
    """

    def bernstein_poly(_i, n, t):
        """
         Полином Бернштейна стпени n, i - функция t
        """
        return comb(n, _i) * (t ** _i) * (1 - t) ** (n - _i)

    def bezier_curve_local(nodes, n_times=1000):
        """
        На основании набора узлов возвращает
        кривую Безье определяемую узлами
        Точки задаются в виде:
           [ [1,1],
             [2,3],
              [4,5], ..[Xn, Yn] ]
        nTimes - число точек для вычисления значений
        """

        n_points = len(nodes)
        x_points = np.array([p[0] for p in nodes])
        y_points = np.array([p[1] for p in nodes])

        t = np.linspace(0.0, 1.0, n_times)

        polynomial_array = np.array([bernstein_poly(_i, n_points - 1, t) for _i in range(0, n_points)])

        x_values_l = np.dot(x_points, polynomial_array)
        y_values_l = np.dot(y_points, polynomial_array)
        return x_values_l, y_values_l

    def intersect(xp1, yp1, xp2, yp2, xp3, yp3, xp4, yp4):
        """
        Функция пересечения двух прямых, заданных точками
        :param xp1: x точки 1 на прямой 1
        :param yp1: y точки 1 на прямой 1
        :param xp2: x точки 2 на прямой 1
        :param yp2: y точки 2 на прямой 1
        :param xp3: x точки 1 на прямой 2
        :param yp3: y точки 1 на прямой 2
        :param xp4: x точки 2 на прямой 2
        :param yp4: y точки 2 на прямой 2
        :return: точка пересечения прямых [x,y]
        """

        def form_line(_xp1, _yp1, _xp2, _yp2):
            k = (_yp2 - _yp1) / (_xp2 - _xp1)
            b = _yp1 - k * _xp1
            return k, b

        kl1, bl1 = form_line(xp1, yp1, xp2, yp2)
        kl2, bl2 = form_line(xp3, yp3, xp4, yp4)
        x_p_inter = (bl1 - bl2) / (kl2 - kl1)
        y_p_inter = kl1 * x_p_inter + bl1
        return x_p_inter, y_p_inter

    # Определяем точки пересечения прямых
    xl1, yl1 = intersect(p1_l1[0], p1_l1[1],
                         p2_l1[0], p2_l1[1],
                         p1_l2[0], p1_l2[1],
                         p2_l2[0], p2_l2[1])

    # Строим кривую Безье
    x_values, y_values = bezier_curve_local([node1, [xl1, yl1], node2], n_times=len(x_grid))

    # Адаптация кривой под равномерный шаг по х
    bezier_spline = interpolate.make_interp_spline(x_values, y_values, k=1, bc_type=None)
    y_values = bezier_spline(x_grid)

    return y_values


def deviator_loading_deviation_gip(strain, deviator, fracture_strain):
    # Добавим девиации после 0.6qf для кривой без пика
    qf = max(deviator)
    deviation_1 = qf / 100
    deviation_2 = qf / 60

    i_60, = np.where(deviator >= 0.51 * qf)
    i_90, = np.where(deviator >= 0.98 * qf)
    i_end, = np.where(strain >= 0.15)
    i_xc, = np.where(strain >= fracture_strain)
    if fracture_strain >= 0.14:  # без пика
        curve = create_deviation_curve(strain[i_60[0]:i_xc[0]], deviation_1 * 2,
                                       points=np.random.uniform(3, 7), borders="zero_diff",
                                       low_first_district=1, one_side=True) + create_deviation_curve(
            strain[i_60[0]:i_xc[0]], deviation_1,
            points=np.random.uniform(20, 30), borders="zero_diff",
            low_first_district=1, one_side=True)
        deviation_array = -np.hstack((np.zeros(i_60[0]),
                                      -curve,
                                      np.zeros(len(strain) - i_xc[0])))
    else:

        try:
            i_xc1, = np.where(deviator[i_xc[0]:] <= qf - deviation_2)
            i_xc_m, = np.where(deviator >= qf - deviation_1 * 2)
            points_1 = round(fracture_strain * 100)
            if points_1 < 3:
                points_1 = 3

            curve_1 = create_deviation_curve(strain[i_60[0]:i_xc_m[0]], deviation_1 * 1.5,
                                             points=np.random.uniform(3, 4), val=(1, 0.1), borders="zero_diff",
                                             low_first_district=1) + create_deviation_curve(
                strain[i_60[0]:i_xc_m[0]], deviation_1 / 2,
                points=np.random.uniform(points_1, points_1 * 3), borders="zero_diff",
                low_first_district=1)

            points_2 = round((0.15 - fracture_strain) * 100)
            if points_2 < 3:
                points_2 = 3

            deviation_2 = ((deviator[i_xc[0]] - deviator[i_end[0]]) / 14) * (points_2 / 10)

            curve_2 = create_deviation_curve(strain[i_xc[0] + i_xc1[0]:i_end[0]],
                                             deviation_2, val=(0.1, 1),
                                             points=np.random.uniform(points_2, int(points_2 * 3)), borders="zero_diff",
                                             low_first_district=2) + create_deviation_curve(
                strain[i_xc[0] + i_xc1[0]:i_end[0]],
                deviation_2 / 3, val=(0.1, 1),
                points=np.random.uniform(points_2 * 3, int(points_2 * 5)), borders="zero_diff",
                low_first_district=2)
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          curve_1, np.zeros(i_xc[0] - i_xc_m[0]),
                                          np.zeros(i_xc1[0]),
                                          curve_2,
                                          np.zeros(len(strain) - i_end[0])))
        except (ValueError, IndexError):
            print("Ошибка девиаций девиатора")
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          create_deviation_curve(strain[i_60[0]:i_90[0]], deviation_1,
                                                                 points=np.random.uniform(3, 6), borders="zero_diff",
                                                                 low_first_district=1),
                                          create_deviation_curve(strain[i_90[0]:i_end[0]], deviation_2, val=(1, 0.1),
                                                                 points=np.random.uniform(10, 15), borders="zero_diff",
                                                                 low_first_district=3,
                                                                 one_side=True),
                                          np.zeros(len(strain) - i_end[0])))

    return deviation_array


def sensor_accuracy_gip(x, y, fracture_strain, noise_level=1.0):
    """возвразщает зашумеленную функцию без шума в характерных точках"""

    noise = np.random.uniform(-noise_level, noise_level, len(x))
    index_qf_half, = np.where(y >= np.max(y) / 2)
    index_qf, = np.where(y >= np.max(y))
    if fracture_strain > max(x):  # если хс последня точка в массиве или дальше
        index_qf, = np.where(x >= max(x))
    for _i in range(len(y)):  # наложение шума кроме промежутков для характерных точек
        is_excluded_points = (_i < index_qf_half[0] - 2) or \
                             ((_i > index_qf_half[0] + 2) and ([_i] < index_qf[0] - 2)) or \
                             (_i > index_qf[0] + 2)
        if is_excluded_points:
            if y[_i] + noise[_i] < np.max(y):
                y[_i] = y[_i] + noise[_i]
            else:
                # в районе максимума шум меньше первоначального
                y[_i] = y[_i] - np.random.uniform(0.1, 0.5) * noise_level
    return y


def hevisaid_gip(x, offset, smoothness):
    """возвращет функцию Хевисайда 0<=y<=1, которая задает коэффициент влияния kp

    :param x: точки, в которых вычислять значение
    :param offset: смещение относительно х=0
    :param smoothness: гладкость перехода, при smoothness = 0 выраждается в фукнцию Хевисаида
    """
    return 1. / (1. + np.exp(-2 * 10 / smoothness * (x - offset)))


def smoothness_condition_gip(strain_at_50_percent_strength):
    """возвращает предельное значение fracture_strain при котором возможно
    построение заданной функции

    :param strain_at_50_percent_strength: деформация в 50% прочности
    """
    SMOOTHNESS_OFFSET = 0.6 / 100  # 0.6 возможно является максимальным х на сетке
    return 2 * strain_at_50_percent_strength + SMOOTHNESS_OFFSET


def gaus_gip(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """функция Гаусса для участка x>fracture_strain"""
    gaus_height = qf - residual_strength  # высота функции Гаусса
    gaus_smoothness = (-1) * np.log(0.1 / gaus_height) / ((residual_strength_strain - fracture_strain) ** 2)
    # резкость функции Гаусаа (считается из условия равенства заданной точности в точке х50
    return gaus_height * (np.exp(-gaus_smoothness * ((x - fracture_strain) ** 2))) + residual_strength


def parab_gip(x, qf, fracture_strain, residual_strength_strain, residual_strength):
    """Парабола для участка x>fracture_strain """
    # k*x^2 + b
    k_par = -((residual_strength - qf) / (residual_strength_strain - fracture_strain) ** 2)
    return -k_par * ((x - fracture_strain) ** 2) + qf


def gip_for_compare(x, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator):
    """возвращает координаты y итоговой фукнции по законам гиперболы, экспоненты и тангенса"""
    # Константы
    E50_LIMIT = 70000
    '''Е50 после которого необходимо переходить от эспоненты к тангенсу'''
    OC_STRAIN_CUT = 0.151
    '''значение по которому обрезается точка х переуплотнния'''
    ZERO_OFFSET = 0.000001
    '''смещение для расчета 0 значений в особенностях'''


    # коэффициенты гиперболы
    hyp_x_offset = -2 / fracture_strain + 1 / strain_at_50_strength
    hyp_y_offset = qf * (hyp_x_offset * strain_at_50_strength + 1.) / (2. * strain_at_50_strength)

    def dev_load_hyp(_x):
        """считает значения гиперболы на х, коэффициенты созависимы"""
        return hyp_y_offset * _x / (1 + hyp_x_offset * _x)


    result_y = dev_load_hyp(x)
    OC_strain = 0

    return result_y, OC_strain


def cos_par_exp_gip(x, E50, qf, strain_at_50_strength, fracture_strain, correction=0):
    """возвращает функцию косинуса
     и параболы для участка strain_at_50_strength qf"""

    SHIFT = (fracture_strain - strain_at_50_strength) / 2
    '''смещение: коэффицент учитывающий влияние на высоту функции при различных значениях E50'''

    if E50 < 5340:
        vl = 0
    elif (E50 <= 40000) and (E50 >= 5340):
        kvl = 1 / 34660
        bvl = -5340 * kvl
        vl = kvl * E50 + bvl  # 1. / 40000. * E50 - 1. / 8
    elif E50 > 40000:
        vl = 1.
    else:
        vl = None

    height = 0.035 * qf * vl - correction  # высота функции
    if height < 0:
        height = 0

    k_of_parab = height / (-fracture_strain + strain_at_50_strength + SHIFT) ** 2

    # фиромирование функции
    # if x is greater then strain_at_50_strength : x_gr_x50
    _i, = np.where(x > strain_at_50_strength)
    x_low_x50 = x[:_i[0]] if _i.size > 0 else x
    x_gr_x50 = x[_i[0]:] if _i.size > 0 else np.array([])

    # if x is greater then strain_at_50_strength + SHIFT : x_gr_x50sm
    j, = np.where(x_gr_x50 > strain_at_50_strength + SHIFT)
    x_gr_x50_low_x50sm = x_gr_x50[:j[0]] if j.size > 0 else x_gr_x50
    x_gr_x50sm = x_gr_x50[j[0]:] if j.size > 0 else np.array([])

    # if x is greater then fracture_strain : x_gr_xc
    l, = np.where(x_gr_x50sm > fracture_strain)
    x_gr_x50sm_low_xc = x_gr_x50sm[:l[0]] if l.size > 0 else x_gr_x50sm
    x_gr_xc = x_gr_x50sm[l[0]:] if l.size > 0 else np.array([])

    _first_zero_part = np.full(len(x_low_x50), 0)
    _cos_part = (height * 0.5 * (np.cos((1. / SHIFT) *
                                        np.pi * (x_gr_x50_low_x50sm - strain_at_50_strength) - np.pi) + 1))
    _parab_part = (-1) * k_of_parab * (x_gr_x50sm_low_xc - strain_at_50_strength - SHIFT) ** 2 + height
    _last_zero_part = np.full(len(x_gr_xc), 0)

    return np.hstack((_first_zero_part, _cos_part, _parab_part, _last_zero_part))


def loop_gip(x, y, Eur, unload_deviator, re_load_deviator, noise_params=None):
    """Рассчитывает петлю разгрузки -- повторного нагружения
    :param x: массив значений x
    :param y: массив значений y
    :param Eur: recommended: 3*E50
    :param unload_deviator: девиатор разгрузки
    :param re_load_deviator: девиатор повторной нагрузки
    :param noise_params: optional, default None, параметры для моделирования шума list[float, float]

    Returns
    --------
    loop_x -- x координаты петли \n
    loop_y -- y координаты петли \n
    connection_indexes -- tuple[index_connection_unload[0], index_connection_return_on_load[0])]\n
    loop_indexes -- tuple[real_unload_index, real_re_load_index, real_return_on_load_index]\n
    loop_strain_values --tuple[unload_strain, re_load_strain, return_on_load_point_strain]\n
    """

    # индекс 1 точки
    index_unload_point, = np.where(y >= unload_deviator)

    if not np.size(index_unload_point) > 0:
        unload_deviator = np.max(y)
        index_unload_point, = np.where(y >= unload_deviator)

    index_unload_point = index_unload_point[0]

    # точка появления петли
    unload_strain = x[index_unload_point]
    unload_deviator = y[index_unload_point]

    # точка конца петли
    index_re_load_point, = np.where(y == np.max(y))
    index_re_load_point = index_re_load_point[-1]

    k = (0.3 / (-x[index_re_load_point])) * unload_strain + 0.4
    dynamic_ratio = -3 * 10 ** (-9) * Eur + k * unload_strain  # 0.00095

    # Точка возврата на кривую
    return_on_load_point_strain = unload_strain + dynamic_ratio
    assert return_on_load_point_strain < x.max(), "Ошибка построения петли при заданном Eur"
    index_return_on_load, = np.where(x >= return_on_load_point_strain)
    index_return_on_load = index_return_on_load[0]
    # задаем последнюю точку в общем массиве кривой девиаторного нагружения
    return_on_load_point_strain = x[index_return_on_load]
    if return_on_load_point_strain <= unload_strain:
        index_return_on_load = index_unload_point + 1
        return_on_load_point_strain = x[index_return_on_load]
    return_on_load_deviator = y[index_return_on_load]

    D1_return_on_load = (y[index_return_on_load + 1] - y[index_return_on_load]) / \
                        (x[index_return_on_load + 1] - x[index_return_on_load])
    '''производная кривой девиаторного нагружения в точке конца петли'''

    E0 = (y[1] - y[0]) / (x[1] - x[0])  # производная кривой девиаторного нагружения в 0
    # ограничение на E0 (не больше чем модуль петли разгрузки)
    if E0 < Eur:
        E0 = 1.1 * Eur

    # ограничение на угол наклона участка повтороной нагрузки,
    # чтобы исключить пересечение петли и девиаторной кривой
    min_E0 = unload_deviator / unload_strain  # максимальный угол наклона петли

    # коррекция Eur
    if Eur < 1.1 * min_E0:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        Eur = 1.1 * min_E0
        E0 = 1.1 * Eur

    # вычисляется из оординаты и угла наклона петли
    re_load_strain = (re_load_deviator - unload_deviator + Eur * unload_strain) / Eur
    index_re_load, = np.where(x >= re_load_strain)
    index_re_load = index_re_load[0]
    re_load_strain = x[index_re_load]

    # если точка 2 совпадает с точкой один или правее, то меняем точку 2 на предыдущую
    if index_re_load >= index_unload_point:
        # print("\nВНИМАНИЕ: Eur изменен!\n")
        index_re_load = index_unload_point - 1
        re_load_strain = x[index_re_load]

    # участок разгрузки
    unload_part_x = np.linspace(unload_strain, re_load_strain,
                                int(abs(re_load_strain - unload_strain) / (x[1] - x[0]) + 1))
    # участок повторной нагрузки
    reload_part_x = np.linspace(re_load_strain, return_on_load_point_strain,
                                int(abs(return_on_load_point_strain - re_load_strain) / (x[1] - x[0]) + 1))

    # 0.8 * Eur + 60000  # производная в точке начала разгрузки (близка к бесконечности) #???
    dynamic_D1 = 2 * Eur

    # формируем разгрузку
    spline_unload = interpolate.make_interp_spline([re_load_strain, unload_strain],
                                                   [re_load_deviator, unload_deviator], k=3,
                                                   bc_type=([(2, 0)], [(1, dynamic_D1)]))
    unload_part_y = spline_unload(unload_part_x)  # участок разгрузки

    # формируем повторное нагружение
    point_1_l1 = [re_load_strain - 0.2 * re_load_strain,
                  E0 * (re_load_strain - 0.2 * re_load_strain) +
                  (re_load_deviator - E0 * re_load_strain)]
    point_2_l1 = [re_load_strain, re_load_deviator]
    point_1_l2 = [return_on_load_point_strain, return_on_load_deviator]
    point_2_l2 = [return_on_load_point_strain - 0.1 * return_on_load_point_strain,
                  D1_return_on_load * (return_on_load_point_strain - 0.1 * return_on_load_point_strain) +
                  (return_on_load_deviator - D1_return_on_load * return_on_load_point_strain)]

    _bezier_curve = bezier_curve_gip(point_1_l1, point_2_l1, point_1_l2, point_2_l2,
                                     [re_load_strain, re_load_deviator],
                                     [return_on_load_point_strain, return_on_load_deviator],
                                     reload_part_x)
    reload_part_y = _bezier_curve

    # устраняем повторяющуюся точку 2
    reload_part_x = reload_part_x[1:]
    reload_part_y = reload_part_y[1:]

    # соединяем  участки разгрузки и нагрузки в петлю
    loop_x = np.hstack((unload_part_x, reload_part_x))

    # определяем индексы, по которым будет петля будет "крепиться" к исходной кривой
    index_connection_unload, = np.where(x >= unload_strain)
    index_connection_return_on_load, = np.where(x >= return_on_load_point_strain)

    if noise_params:
        unload_part_y = unload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(unload_part_y))
        reload_part_y = reload_part_y + np.random.uniform(-noise_params[0], noise_params[0], len(reload_part_y))
        unload_part_y = discrete_array(unload_part_y, noise_params[1])
        reload_part_y = discrete_array(reload_part_y, noise_params[1])

    loop_y = np.hstack((unload_part_y, reload_part_y))

    real_unload_index = index_connection_unload[0] + 1
    # первая точка петли на самом деле принадлежит исходной кривой
    real_re_load_index = index_connection_unload[0] + len(unload_part_y)
    # -1 + 1 = 0 т.к. самая нижняя точка петли принадлежит разгрузке
    real_return_on_load_index = index_connection_unload[0] + len(loop_x) - 2
    # -1 - 1 = -2 т.к. последняя точка петли так же на самом деле принадлежит кривой

    # Для присоединения петли к исходной кривой
    connection_indexes = (index_connection_unload[0], index_connection_return_on_load[0])
    #
    loop_indexes = (real_unload_index, real_re_load_index, real_return_on_load_index)
    #
    # Для работы фукнции объемной деформации
    loop_strain_values = (unload_strain, re_load_strain, return_on_load_point_strain)
    #

    return loop_x, loop_y, connection_indexes, loop_indexes, loop_strain_values


def dev_loading_gip(qf, E50, **kwargs):
    """
    Кусочная функция: на участке [0,fracture_strain]-сумма функций гиперболы и
    (экспоненты или тангенса) и кусочной функции синуса и парболы
    на участке [fracture_strain...]-половина функции Гаусса или параболы

    :param qf: double
        qf
    :param E50: double
        E50
    :param kwargs: optional:
        fracture_strain;
        residual_strength_strain;
        residual_strength;
        OC_deviator;
        gaus_or_par;
        amount_points;
        Eur, default None, True для петли;
        unload_deviator;
        re_load_deviator;
        noise_off, default None, True для отключения шумов и "ступеней";
    :return: strain_required_grid - х координаты полученной кривой;
        deviator_required_grid - у координаты полученной кривой;
        [[strain_at_50_strength, qf / 2], [OC_strain, OC_deviator], [fracture_strain, qf],
         [residual_strength_strain, residual_strength]] - расчетные параметры;
        loop_strain_values if Eur, tuple - strain координаты точек петли;
        loop_indexes if Eur, tuple - индексы самой петли, точки кривой не включены
    """

    # Константы
    STRAIN_LIMIT = 0.15
    STRAIN_CALC_LIMIT = 0.6
    NOISE_LEVEL = 1.0
    DISCRETE_ARRAY_LEVEL = 0.5
    DISCRETE_ARRAY_LOOP_LEVEL = 2 * DISCRETE_ARRAY_LEVEL
    #
    _0002_QF = 0.002 * qf

    # Параметры
    try:
        kwargs["fracture_strain"]
    except KeyError:
        kwargs["fracture_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength_strain"]
    except KeyError:
        kwargs["residual_strength_strain"] = STRAIN_LIMIT

    try:
        kwargs["residual_strength"]
    except KeyError:
        kwargs["residual_strength"] = qf

    try:
        kwargs["OC_deviator"]
    except KeyError:
        kwargs["OC_deviator"] = 0

    try:
        kwargs["gaus_or_par"]
    except KeyError:
        kwargs["gaus_or_par"] = 0

    try:
        kwargs["amount_points"]
    except KeyError:
        kwargs["amount_points"] = 700

    try:
        kwargs["Eur"]
    except KeyError:
        kwargs["Eur"] = None

    try:
        kwargs["unload_deviator"]
    except KeyError:
        kwargs["unload_deviator"] = 0.8 * qf

    try:
        kwargs["re_load_deviator"]
    except KeyError:
        kwargs["re_load_deviator"] = 10

    try:
        kwargs["noise_off"]
    except KeyError:
        kwargs["noise_off"] = None

    #
    fracture_strain = kwargs.get('fracture_strain')
    residual_strength_strain = kwargs.get('residual_strength_strain')
    residual_strength = kwargs.get('residual_strength')
    OC_deviator = kwargs.get('OC_deviator')
    gaus_or_par = kwargs.get('gaus_or_par')  # 0 - гаус, 1 - парабола
    amount_points = kwargs.get('amount_points')
    Eur = kwargs.get('Eur')
    unload_deviator = kwargs.get('unload_deviator')
    re_load_deviator = kwargs.get('re_load_deviator')
    noise_off = kwargs.get("noise_off")

    if noise_off:
        NOISE_LEVEL = None
        DISCRETE_ARRAY_LEVEL = None
        DISCRETE_ARRAY_LOOP_LEVEL = None
    # расчёт ведется с числом точек amount_points на длине STRAIN_CALC_LIMIT
    AMOUNT_POINTS_ON_CALC = int((amount_points * STRAIN_CALC_LIMIT / STRAIN_LIMIT) / (STRAIN_CALC_LIMIT / STRAIN_LIMIT))
    # значения будут возвращаться с числом точек amount_points но на длине STRAIN_LIMIT
    AMOUNT_POINTS_ON_RETURN = int(AMOUNT_POINTS_ON_CALC * (STRAIN_CALC_LIMIT / STRAIN_LIMIT))

    # Ограничения
    if unload_deviator > qf:
        unload_deviator = qf
    if unload_deviator < 20.0:
        unload_deviator = 20.0
    if fracture_strain > 0.11:
        fracture_strain = 0.15
    if residual_strength >= qf:
        residual_strength = qf
    strain_at_50_strength = (qf / 2.) / E50
    if fracture_strain < strain_at_50_strength:
        fracture_strain = strain_at_50_strength * 1.1  # хс не может быть меньше strain_at_50_strength

    # Сетки
    strain = np.linspace(0, STRAIN_CALC_LIMIT, AMOUNT_POINTS_ON_CALC)

    # Начало построения фукнции

    # считаем предельное значение fracture_strain
    fracture_strain_limit = smoothness_condition_gip(strain_at_50_strength)

    if strain_at_50_strength >= fracture_strain:
        # если strain_at_50_strength > fracture_strain, fracture_strain сдвигается в 0.15,
        # х2,residual_strength перестает учитываться,
        # в качестве функции используется сумма гиперболы, экспоненты или тангенса и функции синуса и параболы

        fracture_strain = STRAIN_LIMIT
        #
        deviator, OC_strain = gip_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #

        if fracture_strain <= fracture_strain_limit:
            # проверка на условие гладкости, если условие не соблюдается
            # передвинуть xс в предельное значение
            fracture_strain = fracture_strain_limit
            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = gip_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par_exp_gip(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #

        # residual_strength_strain,residual_strength не выводится
        residual_strength_strain = fracture_strain
        residual_strength = qf

    else:
        #
        deviator, OC_strain = gip_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
        #
        if fracture_strain <= fracture_strain_limit:
            fracture_strain = fracture_strain_limit

            if (fracture_strain > 0.11) and (fracture_strain < STRAIN_LIMIT):
                fracture_strain = STRAIN_LIMIT
            #
            deviator, OC_strain = gip_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            #

        if fracture_strain > STRAIN_LIMIT:
            #
            deviator, OC_strain = gip_for_compare(strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par_exp_gip(strain, E50, qf, strain_at_50_strength, fracture_strain)
            #
            # residual_strength_strain,residual_strength не выводится
            residual_strength_strain = fracture_strain
            residual_strength = qf

        else:
            # минимально допустимое расстояния между хс и х2
            if fracture_strain >= 0.8 * residual_strength_strain:
                residual_strength_strain = 1.2 * fracture_strain
            # минимально допустимое расстояние мужду residual_strength и qf
            if residual_strength >= qf:
                residual_strength = 0.98 * qf

            # Примеряем положение кривой - оно не должно быть выше qf
            _i, = np.where(strain >= fracture_strain)  # >= намеренно
            _i = _i[0]
            _gip_exp_tg, *_ = gip_for_compare(strain[:_i], E50, qf, strain_at_50_strength,
                                              fracture_strain, OC_deviator)
            _cos_par = cos_par_exp_gip(strain[:_i], E50, qf, strain_at_50_strength, fracture_strain)
            maximum = max(np.hstack((_gip_exp_tg + _cos_par, np.full(len(strain[_i:]), 0.0)))
                          if _i.size > 0 else np.full(len(strain), 0.0))

            is_max_lower_qf = maximum < (qf + _0002_QF)

            _i, = np.where(strain > fracture_strain)  # > намеренно
            if is_max_lower_qf:
                correction = 0
            else:
                # если максимум суммарной функции на участке от 0 до хс превышает qf, то уменьшаем
                # высоту функции синуса и параболы на величину разницы в точке fracture_strain
                correction = abs(maximum - qf + 2 * _0002_QF)

            if _i.size > 0:
                _i = _i[0]
                _gip_exp_tg, *_ = gip_for_compare(strain[:_i], E50, qf, strain_at_50_strength,
                                                  fracture_strain, OC_deviator)
                _cos_par = cos_par_exp_gip(strain[:_i], E50, qf, strain_at_50_strength,
                                           fracture_strain, correction)
                if gaus_or_par == 1:
                    _gaus_or_par = parab_gip(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                             residual_strength)
                else:
                    _gaus_or_par = gaus_gip(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                            residual_strength)
                deviator = np.hstack((_gip_exp_tg + _cos_par, _gaus_or_par))

            else:
                deviator = (strain, E50, qf, strain_at_50_strength, fracture_strain, OC_deviator)[0] \
                           + cos_par_exp_gip(strain, E50, qf, strain_at_50_strength, fracture_strain, correction)

    if OC_deviator > (0.8 * qf):  # не выводить точку OC_strain, OC_deviator
        OC_strain = fracture_strain
        OC_deviator = qf

    # переход к нужной сетке (strain_required_grid необходимо обрезать по х = STRAIN_LIMIT чтобы получить amount_points
    strain_required_grid = np.linspace(strain.min(initial=None), strain.max(initial=None), AMOUNT_POINTS_ON_RETURN)
    # интерполяция  для сглаживания в пике
    spl = make_interp_spline(strain, deviator, k=5)
    deviator_required_grid = spl(strain_required_grid)

    loop_indexes = None

    def noise(result):
        """На кладывает девиации, шум и дискретизацию в соответствии с NOISE_LEVEL и DISCRETE_ARRAY_LEVEL"""
        if not noise_off:
            result += deviator_loading_deviation_gip(strain_required_grid, result, fracture_strain)
            result = sensor_accuracy_gip(strain_required_grid, result, fracture_strain, noise_level=NOISE_LEVEL)
            result = discrete_array(result, DISCRETE_ARRAY_LEVEL)
        return result

    if Eur:
        x_loop, y_loop, connection_to_curve_indexes, loop_indexes, loop_strain_values = \
            loop_gip(strain_required_grid, deviator_required_grid, Eur, unload_deviator, re_load_deviator,
                     [NOISE_LEVEL, DISCRETE_ARRAY_LOOP_LEVEL] if not noise_off else None)

        #
        # deviator_required_grid = noise(deviator_required_grid)

        deviator_required_grid = np.hstack((deviator_required_grid[:connection_to_curve_indexes[0]], y_loop,
                                            deviator_required_grid[connection_to_curve_indexes[1] + 1:]))
        strain_required_grid = np.hstack((strain_required_grid[:connection_to_curve_indexes[0]], x_loop,
                                          strain_required_grid[connection_to_curve_indexes[1] + 1:]))
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.
    else:
        # deviator_required_grid = noise(deviator_required_grid)
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.

    # наложение хода штока и обрезка функций
    # rod_move_result = initial_free_rod_move(strain_required_grid,
    #                                         deviator_required_grid,
    #                                         strain_cut=STRAIN_LIMIT,
    #                                         noise=(NOISE_LEVEL, DISCRETE_ARRAY_LEVEL) if not noise_off else None)
    # strain_required_grid = rod_move_result[0]
    # deviator_required_grid = rod_move_result[1]
    # len_rod_move = rod_move_result[2]
    loop_indexes_with_rod = None if not Eur else (loop_indexes[i] + len_rod_move for i in range(len(loop_indexes)))

    return strain_required_grid, deviator_required_grid


def initial_free_rod_move_gip(strain, deviator, strain_cut=0.151, noise=None):
    """
    Обрезает strain и deviator по strain_cut и
    возвращает strain, deviator с присоединенным ходом штока и длину хода штока (в точках)

    :param strain:
    :param deviator:
    :param strain_cut: optional, default = 0.151, значение, по которому обрезаются массивы
    :param noise: optional, default None, параметры для моделирования шума tuple[float, float]

    Returns
    -------
    strain -- cut strain with rod \n
    deviator -- cut deviator with rod \n
    len_rod_move -- len of rod in points: len(strain_start)
    """
    _i, = np.where(strain > strain_cut)
    assert _i.size > 0, "Ошибка обрезки, strain_cut не может быть больше max(strain)"
    strain = strain[:_i[0]]
    deviator = deviator[:_i[0]]

    strain_last_point = np.random.uniform(0.005, 0.01) - (strain[-1] - strain[-2])
    '''положительная последняя точка х для метрвого хода штока'''

    strain_start = np.linspace(0, strain_last_point, int(strain_last_point / (strain[-1] - strain[-2])) + 1)
    '''положительный масив х для метрвого хода штока'''

    SLANT = np.random.uniform(20, 30)
    '''наклон функции экспоненты'''
    AMPLITUDE = np.random.uniform(15, 25)
    '''высота функции экспоненты'''

    # определяем абциссу метрвого хода штока
    deviator_start = exponent(strain_start, AMPLITUDE, SLANT)
    # смещение массива x для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    strain_start -= strain_start[-1] + (strain[-1] - strain[-2])
    # смещение массива y для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    deviator_start -= deviator_start[-1]

    if noise:
        assert len(noise) == 2, "noise должен содерждать значение для шума и значение для уровня ступеней"
        deviator_start = deviator_start + np.random.uniform(-noise[0], noise[0], len(deviator_start))
        deviator_start = discrete_array(deviator_start, noise[1])  # наложение ступенчватого шума на мертвый ход штока

    strain = np.hstack((strain_start, strain))  # добавление начального участка в функцию девиаторного нагружения
    strain += abs(strain[0])  # смещение начала кривой девиаторного нагруружения в 0

    deviator = np.hstack((deviator_start, deviator))  # добавление начального участка в функцию девиаторного нагружения
    deviator += abs(deviator[0])  # смещение начала кривой девиаторного нагружения в 0
    deviator[0] = 0.  # искусственное зануление первой точки

    len_rod_move = len(strain_start)

    return strain, deviator, len_rod_move






class App(QMainWindow):  # Окно и виджеты на нем

    def __init__(self):
        super().__init__()
        self.title = 'Девиаторное нагружение'
        self.left = 100
        self.top = 30
        self.width = 800
        self.height = 600
        self.setWindowTitle(self.title)

        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = Main()
        self.setCentralWidget(self.table_widget)

        self.show()


class Main(QWidget):

    def __init__(self):
        super().__init__()

        self.params = {"qf": 650, "e50": 3119, "qf2": 560, "xc": 0.07, "xc2": 0.115}

        self.createIU()

        x, y, points = dev_loading(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                             residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        x1, y1 = dev_loading_exp(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                             residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        x2, y2 = dev_loading_gip(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                                 residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        i, = np.where(x > 0.151)

        self.canvas.plot(x[:i[0]], y[:i[0]], x1[:i[0]], y1[:i[0]], x2[:i[0]], y2[:i[0]], self.params, points)


    def createIU(self):
        self.layout = QGridLayout()

        self.qf_slider = QSlider(QtCore.Qt.Horizontal)
        self.qf_slider.setMinimum(200)
        self.qf_slider.setMaximum(3000)
        self.qf_slider.setValue(self.params["qf"])
        self.qf_slider.setTickInterval(1)
        self.qf_slider.sliderMoved.connect(self.plot)

        self.e50_slider = QSlider(QtCore.Qt.Horizontal)
        self.e50_slider.setMinimum(2000)
        self.e50_slider.setMaximum(140000)
        self.e50_slider.setValue(self.params["e50"])
        self.e50_slider.setTickInterval(10)
        self.e50_slider.sliderMoved.connect(self.plot)

        self.xc_slider = QSlider(QtCore.Qt.Horizontal)
        self.xc_slider.setMinimum(1)
        self.xc_slider.setMaximum(150)
        self.xc_slider.setValue(self.params["xc"] * 1000)
        self.xc_slider.setTickInterval(1)
        self.xc_slider.sliderMoved.connect(self.plot)

        self.xc2_slider = QSlider(QtCore.Qt.Horizontal)
        self.xc2_slider.setMinimum(1)
        self.xc2_slider.setMaximum(150)
        self.xc2_slider.setValue(self.params["xc2"] * 1000)
        self.xc2_slider.setTickInterval(1)
        self.xc2_slider.sliderMoved.connect(self.plot)

        self.qf2_slider = QSlider(QtCore.Qt.Horizontal)
        self.qf2_slider.setMinimum(200)
        self.qf2_slider.setMaximum(1400)
        self.qf2_slider.setValue(self.params["qf2"])
        self.qf2_slider.setTickInterval(1)
        self.qf2_slider.sliderMoved.connect(self.plot)


        self.canvas = Canvas()

        self.layout.addWidget(QLabel("qf"), 0, 0)
        self.layout.addWidget(self.qf_slider, 0, 1)

        self.layout.addWidget(QLabel("e50"), 1, 0)
        self.layout.addWidget(self.e50_slider, 1, 1)

        self.layout.addWidget(QLabel("xc"), 2, 0)
        self.layout.addWidget(self.xc_slider, 2, 1)

        self.layout.addWidget(QLabel("qf2"), 3, 0)
        self.layout.addWidget(self.qf2_slider, 3, 1)

        self.layout.addWidget(QLabel("xc2"), 4, 0)
        self.layout.addWidget(self.xc2_slider, 4, 1)


        self.layout.addWidget(self.canvas, 5, 0, -1, -1)

        self.setLayout(self.layout)

    def plot(self):
        self.get_params()

        # self.qf2_slider.setMaximum(self.params["qf"]*0.99)
        self.canvas.clear()

        x, y, points =  dev_loading(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                             residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        x1, y1 = dev_loading_exp(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                             residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        x2, y2 = dev_loading_gip(self.params["qf"], self.params["e50"], fracture_strain=self.params["xc"],
                                 residual_strength_strain=self.params["xc2"], residual_strength=self.params["qf2"])
        i, = np.where(x > 0.151)

        self.canvas.plot(x[:i[0]], y[:i[0]], x1[:i[0]], y1[:i[0]], x2[:i[0]], y2[:i[0]], self.params, points)

    def get_params(self):
        self.params["qf"] = float(self.qf_slider.value())
        self.params["e50"] = float(self.e50_slider.value())
        self.params["qf2"] = float(self.qf2_slider.value())
        self.params["xc"] = float(self.xc_slider.value()) / 1000
        self.params["xc2"] = float(self.xc2_slider.value()) / 1000



class Canvas(QFrame):  # получает на входе размер окна. Если передать 0 то размер автоматический
    def __init__(self, xsize=0, ysize=0):
        super().__init__()
        if xsize != 0:
            self.setFixedWidth(xsize)
        elif ysize != 0:
            self.setFixedHeight(ysize)

        self.setStyleSheet('background: #ffffff')
        self.setFrameShape(QFrame.StyledPanel)
        # self.setLineWidth(0.6)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)

        self.figure = plt.figure()
        # plt.rcParams['figure.figsize'] = 10, 5
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.canvas, 0, 0)
        self.layout.addWidget(self.toolbar, 1, 0, -1, -1)

        self.ax1 = self.figure.add_subplot(111)

        self.figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.12, hspace=0.07, left=0.1)
        self.ax1.grid(axis='both', linewidth='0.6')
        self.ax1.set_xlabel("Вертикальная деформация, д.е.", fontfamily='Times New Roman', fontsize=11)
        self.ax1.set_ylabel("Девиатор, кПа", fontfamily='Times New Roman', fontsize=11)

    def clear(self):
        self.ax1.clear()
        self.ax1.grid(axis='both', linewidth='0.6')
        self.ax1.set_xlabel("Вертикальная деформация, д.е.", fontfamily='Times New Roman', fontsize=11)
        self.ax1.set_ylabel("Девиатор, кПа", fontfamily='Times New Roman', fontsize=11)

    def plot(self, x, y, x1, y1, x2, y2,  params, points=False):

        self.ax1.plot(x, y, label = 'средняя')
        self.ax1.plot( x1, y1, label = 'экспонента')
        self.ax1.plot(x2, y2, label = 'гипербола')

        self.ax1.plot([], [], color="white", label="$q_f$ = " + str(params["qf"]))
        self.ax1.plot([], [], color="white", label="$E_{50}$ = " + str(params["e50"]))
        self.ax1.plot([], [], color="white", label="$q_f2$ = " + str(params["qf2"]))
        self.ax1.plot([], [], color="white", label="$x_c$ = " + str(params["xc"]))
        self.ax1.plot([], [], color="white", label="$x_c$2 = " + str(params["xc2"]))

        if points:
            for i in range(len(points)):
                if points[i][0] < 0.151:
                    self.ax1.scatter(*points[i])

        self.ax1.legend()

        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = App()
    sys.exit(app.exec_())

