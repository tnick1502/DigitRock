# coding: utf-8

# In[34]:
import copy
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

from general.general_functions import *


def find_E50_qf(strain, deviator):
    """Определение параметров qf и E50"""
    qf = np.max(deviator)

    # Найдем область E50
    imax, = np.where(deviator > qf / 2)
    imin, = np.where(deviator < qf / 2)
    imax = imax[0]
    imin = imin[-1]

    E50 = (qf / 2) / (
        np.interp(qf / 2, np.array([deviator[imin], deviator[imax]]), np.array([strain[imin], strain[imax]])))

    return round(E50 / 1000, 2), round(qf / 1000, 2)


def find_puasson_dilatancy(strain, deviator, volume_strain):
    # Коэффициент Пуассона и дилатансия
    qf = np.max(deviator)

    # Найдкм коэффициент пуассона
    strain25 = (np.interp(qf / 4, deviator, strain))
    index_02qf, = np.where(deviator >= 0.25 * qf)

    puasson = abs(((np.interp(strain25, strain, volume_strain)) + strain25) / (2 * - strain25))

    # Найдкм угол дилатансии
    i_top = np.argmax(deviator)

    if strain[i_top] >= 0.14:
        dilatancy = "-"
    else:

        scale = (max(volume_strain) - min(volume_strain)) / 5
        x_area = 0.003
        if x_area <= (strain[i_top + 1] - strain[i_top - 1]):
            x_area = (strain[i_top + 2] - strain[i_top - 2])

        i_begin, = np.where(strain >= strain[i_top] - x_area)
        i_end, = np.where(strain >= strain[i_top] + x_area)
        x_dilatancy = strain[i_begin[0]:i_end[0]]
        y_dilatancy = volume_strain[i_begin[0]:i_end[0]]

        # p = np.polyfit(x_dilatancy, y_dilatancy, 1)
        # approx = np.polyval(p, x_dilatancy)
        # A1 = (approx[-1] - approx[0]) / (x_dilatancy[-1] - x_dilatancy[0])
        # B1 = np.polyval(p, 0)

        A1, B1 = line_approximate(x_dilatancy, y_dilatancy)
        B1 = volume_strain[i_top] - A1 * strain[i_top]

        dilatancy_begin, = np.where(line(A1, B1, strain) >= volume_strain[i_top] - scale)
        dilatancy_end, = np.where(line(A1, B1, strain) >= volume_strain[i_top] + scale)

        try:
            dilatancy = (
                round(A1 * (180 / np.pi), 2), [strain[dilatancy_begin[0]], strain[dilatancy_end[0]]],
                [line(A1, B1, strain[dilatancy_begin[0]]), line(A1, B1, strain[dilatancy_end[0]])])
        except IndexError:
            dilatancy = "-"

    return round(puasson, 2), dilatancy


def deviator_loading_deviation(strain, deviator, xc):
    # Добавим девиации после 0.6qf для кривой без пика
    qf = max(deviator)
    devition_1 = qf / 100
    devition_2 = qf / 60

    i_60, = np.where(deviator >= 0.51 * qf)
    i_90, = np.where(deviator >= 0.98 * qf)
    i_end, = np.where(strain >= 0.15)
    i_xc, = np.where(strain >= xc)
    if xc >= 0.14:  # без пика
        try:
            curve = create_deviation_curve(strain[i_60[0]:i_xc[0]], devition_1/2,
                                           points=np.random.uniform(6, 15), borders="zero_diff",
                                           low_first_district=1, one_side=True) + \
                    create_deviation_curve(strain[i_60[0]:i_xc[0]], devition_1,
                                           points=np.random.uniform(20, 30), borders="zero_diff",
                                           low_first_district=1, one_side=True)
            deviation_array = -np.hstack((np.zeros(i_60[0]),
                                          curve,
                                          np.zeros(len(strain) - i_xc[0])))
        except IndexError:
            deviation_array = np.zeros(len(strain))

    else:

        try:
            i_xc1, = np.where(deviator[i_xc[0]:] <= qf - devition_2)
            i_xc_m, = np.where(deviator >= qf - devition_1 * 2)
            points_1 = round((xc) * 100)
            if points_1 < 3:
                points_1 = 3

            curve_1 = create_deviation_curve(strain[i_60[0]:i_xc_m[0]], devition_1 * 1.5,
                                             points=np.random.uniform(3, 4), val=(1, 0.1), borders="zero_diff",
                                             low_first_district=1) + create_deviation_curve(
                strain[i_60[0]:i_xc_m[0]], devition_1 / 2,
                points=np.random.uniform(points_1, points_1 * 3), borders="zero_diff",
                low_first_district=1)

            points_2 = round((0.15 - xc) * 100)
            if points_2 < 3:
                points_2 = 3

            devition_2 = ((deviator[i_xc[0]] - deviator[i_end[0]]) / 14) * (points_2 / 10)

            curve_2 = create_deviation_curve(strain[i_xc[0] + i_xc1[0]:i_end[0]],
                                             devition_2, val=(0.1, 1),
                                             points=np.random.uniform(points_2, int(points_2 * 3)), borders="zero_diff",
                                             low_first_district=2) + create_deviation_curve(
                strain[i_xc[0] + i_xc1[0]:i_end[0]],
                devition_2 / 3, val=(0.1, 1),
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
                                          create_deviation_curve(strain[i_60[0]:i_90[0]], devition_1,
                                                                 points=np.random.uniform(3, 6), borders="zero_diff",
                                                                 low_first_district=1),
                                          create_deviation_curve(strain[i_90[0]:i_end[0]], devition_2, val=(1, 0.1),
                                                                 points=np.random.uniform(10, 15), borders="zero_diff",
                                                                 low_first_district=3,
                                                                 one_side=True),
                                          np.zeros(len(strain) - i_end[0])))

    return deviation_array


def deviation_volume_strain(x, x_given, xc, len_x_dilatacy, deviation=0.0015):
    index_x_given, = np.where(x >= x_given)
    n = 1
    index_x_start_dilatacy, = np.where(x >= (xc - len_x_dilatacy * 2))
    index_x_end_dilatacy, = np.where(x >= (xc + len_x_dilatacy * 2))
    if xc <=0.14:
        def deviation_array(x, i_1, i_2, deviation_val, count_1=20, count_2=50):
            points_count = (i_2 - i_1)
            points_1 = int(points_count / count_1)
            points_2 = int(points_count / count_2)

            if (points_1 >= 3) and (points_2 >= 3):
                array = deviation_val * create_deviation_curve(x[i_1: i_2], 1, points=points_1, val=(0.3, 1), borders='zero diff') + \
                                   deviation * 0.3 * create_deviation_curve(x[i_1: i_2], 1, points=points_2, val=(0.3, 1), borders='zero diff')
            elif (points_1 >= 3) and (points_2 < 3):
                array = deviation_val * create_deviation_curve(x[i_1: i_2], 1, points=points_1, val=(0.3, 1), borders='zero diff')
            else:
                array = np.zeros(i_2 - i_1)

            return array

        try:
            starn_puasson = np.zeros(index_x_given[0])
            puasson_start_dilatacy = deviation_array(x, index_x_given[0], index_x_start_dilatacy[0], deviation/2)
            start_dilatacy_end_dilatacy = deviation_array(x, index_x_start_dilatacy[0], index_x_end_dilatacy[0], deviation/10)
            end_dilatacy_end = deviation_array(x, index_x_end_dilatacy[0], len(x), deviation)

            deviation_vs = np.hstack((starn_puasson, puasson_start_dilatacy, start_dilatacy_end_dilatacy, end_dilatacy_end))
        except IndexError:
            deviation_vs = np.hstack((np.zeros(index_x_given[0]),
                                      deviation * 2 * n * create_deviation_curve(x[index_x_given[0]:], 1,
                                                                                 points=np.random.uniform(5, 10),
                                                                                 val=(0.3, 1), borders='zero diff') +
                                      deviation * 0.7 * n * create_deviation_curve(
                                          x[index_x_given[0]:], 1, points=np.random.uniform(15, 30),
                                          val=(0.3, 1), borders='zero diff')))

        return deviation_vs
    else:
        deviation_vs = np.hstack((np.zeros(index_x_given[0]),
                                  deviation * 2 * n * create_deviation_curve(x[index_x_given[0]:], 1,
                                                                             points=np.random.uniform(5, 10),
                                                                             val=(0.3, 1), borders='zero diff') +
                                  deviation * 0.7 * n * create_deviation_curve(
                                      x[index_x_given[0]:], 1, points=np.random.uniform(15, 30),
                                      val=(0.3, 1), borders='zero diff')))
        return deviation_vs


# Девиаторное нагружение

def hevisaid(x, sdvig, delta_x):
    ''' возвращет функцию Хевисайда, которая задает коэффициент влияния kp'''
    return 1. / (1. + np.exp(-2 * 10 / delta_x * (x - sdvig)))


def cos_par(x, E, qf, strain_at_50_strength, fracture_strain, correction=0):
    """возвращает функцию косинуса
     и параболы для участка strain_at_50_strength qf"""

    SHIFT = (fracture_strain - strain_at_50_strength) / 2
    '''смещение: коэффицент учитывающий влияние на высоту функции при различных значениях E50'''

    if E < 5340:
        vl = 0
    elif (E <= 40000) and (E >= 5340):
        kvl = 1 / 34660
        bvl = -5340 * kvl
        vl = kvl * E + bvl  # 1. / 40000. * E50 - 1. / 8
    elif E > 40000:
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


def gaus(x, qf, xc, x2, qf2):
    '''функция Гаусса для участка x>xc'''
    a_gaus = qf - qf2  # высота функции Гаусса
    k_gaus = (-1) * np.log(0.1 / a_gaus) / ((x2 - xc) ** 2)  # резкость функции Гаусаа
    # (считается из условия равенства заданной точности в точке х50
    return a_gaus * (np.exp(-k_gaus * ((x - xc) ** 2))) + qf2


def parab(x, qf, xc, x2, qf2):
    '''функция Гаусса для участка x>xc'''
    k_par = -((qf2 - qf) / (x2 - xc) ** 2)
    return -k_par * ((x - xc) ** 2) + qf


def smoothness_condition(qf, E, strain_at_50_strength, q_E):
    return (qf - (q_E - E * strain_at_50_strength)) / E


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

    k = (0.3 / (-x[index_re_load_point])) * unload_strain + 0.6
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

    if (x[index_return_on_load + 1] - x[index_return_on_load]) == 0:
        D1_return_on_load = (y[index_return_on_load + 2] - y[index_return_on_load]) / \
                            (x[index_return_on_load + 2] - x[index_return_on_load])
    else:
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
    if Eur < 0.9 * min_E0:
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
    point_1_l1 = [re_load_strain - 0.2 * re_load_strain - 0.2,
                  E0 * (re_load_strain - 0.2 * re_load_strain - 0.2) +
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


# Обьемная деформация
def spline(x_for_part, y_for_part, x_for_inter, a, b, k=3):
    '''x_for_part, y_for_part - координаты точек интерполяци;
    a, b - значения производной на концах; k-степень сплайна'''
    spl = interpolate.make_interp_spline(x_for_part, y_for_part, k,
                                         bc_type=([(1, a)], [(1, b)]))
    return spl(x_for_inter)


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

    def bernstein_poly(i, n, t):
        """
         Полином Бернштейна стпени n, i - функция t
        """
        return comb(n, i) * (t ** i) * (1 - t) ** (n - i)

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

        polynomial_array = np.array([bernstein_poly(i, n_points - 1, t) for i in range(0, n_points)])

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

        def line(xp1, yp1, xp2, yp2):
            k = (yp2 - yp1) / (xp2 - xp1)
            b = yp1 - k * xp1
            return k, b

        kl1, bl1 = line(xp1, yp1, xp2, yp2)
        kl2, bl2 = line(xp3, yp3, xp4, yp4)
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


def volumetric_deformation(x, x_given, m_given, xc, v_d2, x_end, angle_of_dilatancy,
                           angle_end, len_x_dilatacy, v_d_xc, len_line_end, Eur, point1_x, point2_x, point3_x):
    """
        Функция построения обьемной деформации соединением сплайна и двух кривых Безьею

        :param x_given: точка в которой задан коэффициент Пуассона
        :m_given: коэффициент Пуассона
        :xc: точка разрушения
        :v_d2: значение обьемной деформации в последней точке
        :x_end: последняя точка массива х для кривой обьемной деформаци
        :angle_of_dilatancy: угол дилатансии от 0 до 40 градусов
        :angle_end: угол наклона последнего линейного участка от 0 до 30 градусов
        :len_x_dilatacy: длина линенйного участка дилатансии
        :v_d_xc: значение обьемной деформации в точке хс
        :len_line_end: длина последнего линейного участка
        """

    v_d_given = -x_given * (1 - 2 * m_given)  # коэффициент Пуассона пересчитанный в обьемную деформацию

    if angle_of_dilatancy >= 0:
        index_x_start_dilatacy, = np.where(x >= (xc - len_x_dilatacy / 2))  # индекс начала линейного участка дилатансии
        index_x_end_dilatacy, = np.where(x >= (xc + len_x_dilatacy / 2))  # индекс конца линейного участка дилатансии
        # линейный участок (xc находится в середине линейного участка)
        x_dilatancy = np.linspace(x[index_x_start_dilatacy[0]], x[index_x_end_dilatacy[0]],
                                  int(abs(x[index_x_end_dilatacy[0]] - x[index_x_start_dilatacy[0]]) / (
                                          x[-1] - x[-2]) + 1))
        b_dilatancy = v_d_xc - angle_of_dilatancy * xc
        v_d_dilatancy = angle_of_dilatancy * x_dilatancy + b_dilatancy
        # сплайн участка от 0 до xc используется только для участка от 0 до x_given
        spl_before_dilatancy = interpolate.make_interp_spline([0, x_given, x[index_x_start_dilatacy[0]]],
                                                              [0, v_d_given, v_d_dilatancy[0]], k=3,
                                                              bc_type=([(2, 0)], [(1, angle_of_dilatancy)]))
        v_d_before_dilatacy = spl_before_dilatancy(x[:index_x_start_dilatacy[0]])

        index_x_line_end_start, = np.where(x >= (x_end - len_line_end))  # индекс начала последнего линейного участка
        # линейный участок (x_end находится в начале линейного участка)
        x_line_end = np.linspace(x[index_x_line_end_start[0]], (x[-1]),
                                 int(abs(x[index_x_line_end_start[0]] - (x[-1])) / (x[-1] - x[-2]) + 1))
        b_end = (v_d2 - angle_end * x_end) * np.random.uniform(0.3, 0.8)
        v_d_line_end = angle_end * x_line_end + b_end

        # функция Безье для учатска до хc
        xgi, = np.where(x > x_given)
        y_Bezier_line = bezier_curve([0, 0], [x_given, v_d_given],  # Первая и Вторая точки первой прямой
                                     [x_given, angle_of_dilatancy * x_given + b_dilatancy],
                                     # Первая точка второй прямой
                                     [x[index_x_start_dilatacy[0]], v_d_dilatancy[0]],  # Вторая точка второй прямой
                                     [x_given, v_d_given],  # Первый узел (здесь фактически это 2 точка первой прямой)
                                     [x[index_x_start_dilatacy[0]], v_d_dilatancy[0]],  # Второй узел
                                     # (здесь фактически это 2 точка второй прямой)
                                     x[xgi[0]:index_x_start_dilatacy[0]]
                                     )
        # функция Безье для учатска после хc
        y_Bezier_line_1 = bezier_curve([x_dilatancy[0], v_d_dilatancy[0]],  # Первая точка второй прямой
                                       [x_dilatancy[-1], v_d_dilatancy[-1]],  # Первая и Вторая точки первой прямой
                                       [x_line_end[0], v_d_line_end[0]],  # Первая точка второй прямой
                                       [x_line_end[-1], v_d_line_end[-1]],  # Вторая точка второй прямой
                                       [x_dilatancy[-1], v_d_dilatancy[-1]],
                                       # Первый узел (здесь фактически это 2 точка первой прямой)
                                       [x_line_end[0], v_d_line_end[0]],  # Второй узел
                                       # (здесь фактически это 2 точка второй прямой)
                                       x[index_x_end_dilatacy[0] + 1:index_x_line_end_start[0]]
                                       )
        # замена сплайна на участке x_given, xc кривыми Безье
        for i in range(len(y_Bezier_line)):
            v_d_before_dilatacy[i + xgi[0]] = y_Bezier_line[i]
        v_d = np.hstack((v_d_before_dilatacy, v_d_dilatancy, y_Bezier_line_1, v_d_line_end))
    # в случае отрицательных углов дилатансии строится экпонента
    else:
        k1_e = np.random.uniform(10, 30)

        def equations_e(a1_e):
            # коэффициенты экспоненты
            return a1_e * (np.exp(-k1_e * x_given) - 1) - v_d_given

        a1_e = fsolve(equations_e, (-abs(v_d_given)))
        v_d = a1_e * (np.exp(-k1_e * x) - 1)

    if Eur:
        # если подается Eur то строится участок соответсвующий петле разгрузке на кривой девиаторного нагружения
        ip1, = np.where(x >= point1_x)
        point1_y = v_d[ip1[0]]
        ip2, = np.where(x >= point2_x)
        point2_y = 1.1 * point1_y
        ip3, = np.where(x >= point3_x)
        point3_y = v_d[ip3[0]]
        d1_p3 = (v_d[ip3[0] + 1] - v_d[ip3[0]]) / (x[ip3[0] + 1] - x[ip3[0]])
        x1_l = np.linspace(point1_x, point2_x,
                           int(abs(point2_x - point1_x) / (x[1] - x[0]) + 1))  # участок соответствующей разгрузке
        x2_l = np.linspace(point2_x, point3_x,
                           int(abs(point3_x - point2_x) / (
                                   x[1] - x[0]) + 1))  # участок соответствующей повторной нагрузке
        # прямая соответсвующая участку разгрузки
        k12 = (point1_y - point2_y) / (point1_x - point2_x)
        b12 = point1_y - k12 * point1_x
        y1_l = k12 * x1_l + b12

        # сплайн соответствующий повтороной нагрузке
        spl2 = interpolate.make_interp_spline([point2_x, point3_x],
                                              [point2_y, (point3_y - abs(point2_y - point1_y))], k=3,
                                              bc_type=([(2, 0)], [
                                                  (1, d1_p3)]))  # точка 3 сдвинута из-за сдвига кривой после точки 2
        y2_l = spl2(x2_l)
        y2_l = y2_l[1:]  # учет повторяющейся точки
        y_loop = np.hstack((y1_l, y2_l))  # изгиб соответсвующий петле

        # поиск начала и конца петли для совпадения шага
        ip1_y, = np.where(x >= point1_x)
        ip3_y, = np.where(x >= point3_x)

        v_d = np.hstack(
            (v_d[:ip1_y[0]], y_loop, v_d[ip3_y[0] + 1:] - abs(
                point2_y - point1_y)))  # кривая с петлей, часть кривой после точки 2, сдвинута вниз
        # на расстояние abs(point2_y-point1_y)

    return v_d, v_d_given


def gip_exp_tg(x, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator):
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

    if E <= E50_LIMIT:
        influence_ratio_hyperbole_or_exp = 1. / 68000. * E - 1. / 34
    elif E > E50_LIMIT:
        influence_ratio_hyperbole_or_exp = 1.

    def exponent_error(height_smoothness: list):
        """возвращает ошибки в коэффициентах, вычисляются в точках qf и qf/2

        :param height_smoothness: list : exp_relative_height, exp_smoothness
        """
        _exp_relative_height, _exp_smoothness = height_smoothness  # коэффициенты экспоненты
        return -1 * _exp_relative_height * (np.exp(-_exp_smoothness * strain_at_50_strength) - 1) - q_E, \
               -1 * _exp_relative_height * (np.exp(-_exp_smoothness * fracture_strain) - 1) - qf

    def tan_error(half_height_smoothness):
        """возвращает ошибки в коэффициентах арктангенса, вычисляются в точках qf и qf/2"""
        _tan_half_height, _tan_smoothness = half_height_smoothness  # коэффициенты тангенса
        return (_tan_half_height * ((np.arctan(_tan_smoothness * strain_at_50_strength)) / (0.5 * np.pi)) - q_E,
                _tan_half_height * ((np.arctan(_tan_smoothness * fracture_strain)) / (0.5 * np.pi)) - qf)

    if E > 40000:
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
            EPS_q_E = 5
            EPS_qf = 550
            return abs(_error[0]) >= EPS_q_E or abs(_error[1]) >= EPS_qf

        while is_negative() or is_not_changed() or is_lower_1000() or (is_error(error) and WHILE_COUNT < 50):
            initial_exp_relative_height += 1
            _initial = np.array([initial_exp_relative_height, initial_exp_smoothness])
            exp_relative_height, exp_smoothness, *_ = fsolve(exponent_error, _initial)
            error = exponent_error([exp_relative_height, exp_smoothness])
            if is_error(error):
                WHILE_COUNT += 1

    # коэффициенты гиперболы
    # hyp_x_offset = -2 / fracture_strain + 1 / strain_at_50_strength
    # hyp_y_offset = qf * (hyp_x_offset * strain_at_50_strength + 1.) / (2. * strain_at_50_strength)
    hyp_x_offset = -(fracture_strain * q_E - strain_at_50_strength * qf) / \
                   (strain_at_50_strength * fracture_strain * q_E - strain_at_50_strength * fracture_strain * qf)

    hyp_y_offset = (strain_at_50_strength * q_E * qf - fracture_strain * q_E * qf) / \
                   (strain_at_50_strength * fracture_strain * q_E - strain_at_50_strength * fracture_strain * qf)

    def dev_load_hyp(_x):
        """считает значения гиперболы на х, коэффициенты созависимы"""
        return hyp_y_offset * _x / (1 + hyp_x_offset * _x)

    def dev_load_exp(_x):
        """считает значения экспоненты на х"""
        return -exp_relative_height * (np.exp(-exp_smoothness * _x) - 1)

    if E > 50000:
        tan_half_height, tan_smoothness, *_ = fsolve(tan_error, np.array([1, 1]))
    else:
        tan_half_height, tan_smoothness, *_ = fsolve(tan_error, np.array([600, 1]))

    # изначальный расчет возвращаемой фукнции
    result_y = (OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_hyp(x) + \
               (1. - OC_influence_ratio * influence_ratio_hyperbole_or_exp) * dev_load_exp(x)

    OC_strain = 0.  # абцисса точки переуплотнения

    if (OC_deviator != 0) & (OC_deviator <= q_E):
        # если OC_deviator находится до qf/2, то OC_strain рассчитывается из функции гиперболы
        OC_strain = OC_deviator / (hyp_y_offset - OC_deviator * hyp_x_offset)

        _i, = np.where(x > OC_strain)
        if _i.size >= 1:
            _i = _i[0]

            _hevisaid_smoothness = abs(10 * (strain_at_50_strength - OC_strain + ZERO_OFFSET))
            _hevisaid_part = 2 * hevisaid(x[_i:], OC_strain, _hevisaid_smoothness) - 1
            OC_influence_ratio = np.hstack((np.full(len(x[:_i]), 0.0), _hevisaid_part))

            if OC_deviator == q_E:
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
    elif (OC_deviator != 0.) & (OC_deviator > q_E) & (E <= E50_LIMIT):

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
    elif (OC_deviator != 0.) & (OC_deviator > q_E) & (E > E50_LIMIT):

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


def dev_loading(qf, E, sigma3, K0, **kwargs):
    """
    Кусочная функция: на участке [0,fracture_strain]-сумма функций гиперболы и
    (экспоненты или тангенса) и кусочной функции синуса и парболы
    на участке [fracture_strain...]-половина функции Гаусса или параболы

    :param qf: double
        qf
    :param E: double
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
    X_LIMIT = 0.15
    X_CALC_LIMIT = 0.6
    NOISE_LEVEL = 1.0
    DISCRETE_ARRAY_LEVEL = 0.5
    DISCRETE_ARRAY_LOOP_LEVEL = 2 * DISCRETE_ARRAY_LEVEL
    #
    _0002_QF = 0.002 * qf

    # Параметры
    try:
        kwargs["fracture_strain"]
    except KeyError:
        kwargs["fracture_strain"] = X_LIMIT

    try:
        kwargs["residual_strength_strain"]
    except KeyError:
        kwargs["residual_strength_strain"] = X_LIMIT

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

    try:
        kwargs["eps_cons"]
    except KeyError:
        kwargs["eps_cons"] = 0.1

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
    eps_cons = kwargs.get("eps_cons")

    if noise_off:
        NOISE_LEVEL = None
        DISCRETE_ARRAY_LEVEL = None
        DISCRETE_ARRAY_LOOP_LEVEL = None
    # расчёт ведется с числом точек amount_points на длине X_CALC_LIMIT
    AMOUNT_POINTS_ON_CALC = int((amount_points * X_CALC_LIMIT / X_LIMIT) / (X_CALC_LIMIT / X_LIMIT))
    # значения будут возвращаться с числом точек amount_points но на длине X_LIMIT
    AMOUNT_POINTS_ON_RETURN = int(AMOUNT_POINTS_ON_CALC * (X_CALC_LIMIT / X_LIMIT))

    #
    qc = sigma3 * (1 / K0 - 1)
    q_E = 0.6 * qc + 0.6 * sigma3

    while (qf - qc) < 30:
        if qc < 0:
            qc = qc + 0.05
        qc = qc - 0.05

    # Коррекция qf
    qf = qf - qc
    _0002_QF = 0.002 * qf

    if q_E > 0.8 * qf:
        q_E = 0.8 * qf

    # Ограничения
    if unload_deviator > qf:
        unload_deviator = qf
    if unload_deviator < 20.0:
        unload_deviator = 20.0
    if fracture_strain > 0.11:
        fracture_strain = 0.15
    if residual_strength >= qf:
        residual_strength = qf

    strain_at_50_strength = (q_E) / E

    if fracture_strain < strain_at_50_strength:
        fracture_strain = strain_at_50_strength * 1.1  # хс не может быть меньше strain_at_50_strength

    # Сетки
    strain = np.linspace(0, X_CALC_LIMIT, AMOUNT_POINTS_ON_CALC)

    # Начало построения фукнции

    # считаем предельное значение fracture_strain
    fracture_strain_limit = smoothness_condition(qf, E, strain_at_50_strength, q_E)

    if strain_at_50_strength >= fracture_strain:
        # если strain_at_50_strength > fracture_strain, fracture_strain сдвигается в 0.15,
        # х2,residual_strength перестает учитываться,
        # в качестве функции используется сумма гиперболы, экспоненты или тангенса и функции синуса и параболы

        fracture_strain = X_LIMIT
        #
        deviator, OC_strain = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)
        #

        if fracture_strain <= fracture_strain_limit:
            # проверка на условие гладкости, если условие не соблюдается
            # передвинуть xс в предельное значение
            fracture_strain = fracture_strain_limit
            if (fracture_strain > 0.11) and (fracture_strain < X_LIMIT):
                fracture_strain = X_LIMIT
            #
            deviator, OC_strain = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par(strain, E, qf, strain_at_50_strength, fracture_strain)
            #

        # residual_strength_strain,residual_strength не выводится
        residual_strength_strain = fracture_strain
        residual_strength = qf

    else:
        #
        deviator, OC_strain = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)
        #
        if fracture_strain <= fracture_strain_limit:
            fracture_strain = fracture_strain_limit

            if (fracture_strain > 0.11) and (fracture_strain < X_LIMIT):
                fracture_strain = X_LIMIT
            #
            deviator, OC_strain = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)
            #

        if fracture_strain > X_LIMIT:
            #
            deviator, OC_strain = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)
            deviator += cos_par(strain, E, qf, strain_at_50_strength, fracture_strain)
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
            _gip_exp_tg, *_ = gip_exp_tg(strain[:_i], E, qf, q_E, strain_at_50_strength,
                                         fracture_strain, OC_deviator)
            _cos_par = cos_par(strain[:_i], E, qf, strain_at_50_strength, fracture_strain)
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
                _gip_exp_tg, *_ = gip_exp_tg(strain[:_i], E, qf, q_E, strain_at_50_strength,
                                             fracture_strain, OC_deviator)
                _cos_par = cos_par(strain[:_i], E, qf, strain_at_50_strength,
                                   fracture_strain, correction)
                if gaus_or_par == 1:
                    _gaus_or_par = parab(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                         residual_strength)
                else:
                    _gaus_or_par = gaus(strain[_i:], qf, fracture_strain, residual_strength_strain,
                                        residual_strength)
                if q_E > qf / 2:
                    deviator = np.hstack((_gip_exp_tg + _cos_par, _gaus_or_par))
                else:
                    deviator = np.hstack((_gip_exp_tg + _cos_par, _gaus_or_par))

            else:
                deviator = gip_exp_tg(strain, E, qf, q_E, strain_at_50_strength, fracture_strain, OC_deviator)[0] \
                           + cos_par(strain, E, qf, strain_at_50_strength, fracture_strain, correction)

    if OC_deviator > (0.8 * qf):  # не выводить точку OC_strain, OC_deviator
        OC_strain = fracture_strain
        OC_deviator = qf

    # переход к нужной сетке (strain_required_grid необходимо обрезать по х = X_LIMIT чтобы получить amount_points
    strain_required_grid = np.linspace(strain.min(initial=None), strain.max(initial=None), AMOUNT_POINTS_ON_RETURN)

    strain_required_grid_no_loop = copy.deepcopy(strain_required_grid)
    # интерполяция  для сглаживания в пике
    spl = make_interp_spline(strain, deviator, k=5)
    deviator_required_grid = spl(strain_required_grid)

    def noise(result):
        """На кладывает девиации, шум и дискретизацию в соответствии с NOISE_LEVEL и DISCRETE_ARRAY_LEVEL"""
        if not noise_off:
            result += deviator_loading_deviation(strain_required_grid, result, fracture_strain)
            result = sensor_accuracy(strain_required_grid, result, fracture_strain, noise_level=NOISE_LEVEL)
            result = discrete_array(result, DISCRETE_ARRAY_LEVEL)
        return result

    # смещение кривой на девиатор консолидации
    deviator_required_grid += qc
    proiz = (deviator_required_grid[1] - deviator_required_grid[0]) / \
            (strain_required_grid[1] - strain_required_grid[0])
    x_max = deviator_required_grid[0] / proiz
    if eps_cons > x_max:
        eps_cons = x_max
    strain_required_grid += eps_cons

    eps_for_spline_cons = np.linspace(0, strain_required_grid[0],
                                      int(strain_required_grid[0] / (strain_required_grid[1] -
                                                                     strain_required_grid[0])) + 1)

    # При K0 = 1 : qc = 0, eps_cons == 0 и никаких сдвигов нет
    if qc != 0:
        x_for_spline = [0, strain_required_grid[0]]
        y_for_spline = [0, deviator_required_grid[0]]

        spline = interpolate.make_interp_spline(x_for_spline, y_for_spline, k=3, bc_type=([(2, 0)], [(1, proiz)]))
        spline_cons = spline(eps_for_spline_cons)

        strain_required_grid = np.hstack((eps_for_spline_cons[:-1], strain_required_grid))
        deviator_required_grid = np.hstack((spline_cons[:-1], deviator_required_grid))

    if Eur:
        x_loop, y_loop, connection_to_curve_indexes, loop_indexes, loop_strain_values = \
            loop(strain_required_grid, deviator_required_grid, Eur, unload_deviator, re_load_deviator,
                 [NOISE_LEVEL, DISCRETE_ARRAY_LOOP_LEVEL] if not noise_off else None)

        #
        deviator_required_grid = noise(deviator_required_grid)

        deviator_required_grid = np.hstack((deviator_required_grid[:connection_to_curve_indexes[0]], y_loop,
                                            deviator_required_grid[connection_to_curve_indexes[1] + 1:]))
        strain_required_grid = np.hstack((strain_required_grid[:connection_to_curve_indexes[0]], x_loop,
                                          strain_required_grid[connection_to_curve_indexes[1] + 1:]))
        # Первая точка кривой всегда в нуле
        deviator_required_grid[0] = 0.

        _points = ((strain_at_50_strength, q_E + qc), (OC_strain, OC_deviator + qc),
                   (fracture_strain, qf + qc), (residual_strength_strain, residual_strength + qc))

        return strain_required_grid_no_loop, strain_required_grid, \
               deviator_required_grid, _points, loop_strain_values, loop_indexes

    deviator_required_grid = noise(deviator_required_grid)
    # Первая точка кривой всегда в нуле
    deviator_required_grid[0] = 0.

    _points = ((strain_at_50_strength + eps_cons, q_E + qc), (OC_strain + eps_cons, OC_deviator + qc),
               (fracture_strain + eps_cons, qf + qc), (residual_strength_strain + eps_cons, residual_strength + qc))
    return strain_required_grid_no_loop, strain_required_grid, \
           deviator_required_grid, _points, None, None


def curve(qf, E, sigma3, K0, **kwargs):
    try:
        kwargs["xc"]
    except KeyError:
        kwargs["xc"] = 0.15

    try:
        kwargs["x2"]
    except KeyError:
        kwargs["x2"] = 0.15

    try:
        kwargs["qf2"]
    except KeyError:
        kwargs["qf2"] = qf

    try:
        kwargs["qocr"]
    except KeyError:
        kwargs["qocr"] = 0

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
        kwargs["Eur"] = False

    try:
        kwargs["y_rel_p"]
    except KeyError:
        kwargs["y_rel_p"] = 0.8 * qf

    try:
        kwargs["point2_y"]
    except KeyError:
        kwargs["point2_y"] = 10

    try:
        kwargs["U"]
    except KeyError:
        kwargs["U"] = None

    try:
        kwargs["eps_cons"]
    except KeyError:
        kwargs["eps_cons"] = 0.1

    xc = kwargs.get('xc')
    x2 = kwargs.get('x2')
    qf2 = kwargs.get('qf2')
    qocr = kwargs.get('qocr')
    gaus_or_par = kwargs.get('gaus_or_par')  # 0 - гаус, 1 - парабола
    amount_points = kwargs.get('amount_points')
    Eur = kwargs.get('Eur')
    y_rel_p = kwargs.get('y_rel_p')
    point2_y = kwargs.get('point2_y')
    U = kwargs.get('U')
    eps_cons = kwargs.get("eps_cons")

    if y_rel_p > qf:
        y_rel_p = qf
    if y_rel_p < 20.0:
        y_rel_p = 20.0

    if xc>0.11:
        xc=0.15

    # ограничение на qf2
    if qf2 >= qf:
        qf2 = qf
    x50 = (qf / 2.) / E

    strain_no_loop, strain, deviator, adv, loop_strain_values, loop_indexes = dev_loading(qf, E, sigma3, K0,
                                                                                          fracture_strain=xc,
                                                                                          residual_strength_strain=x2,
                                                                                          residual_strength=qf2,
                                                                                          OC_deviator=qocr,
                                                                                          gaus_or_par=gaus_or_par,
                                                                                          amount_points=amount_points,
                                                                                          Eur=Eur,
                                                                                          unload_deviator=y_rel_p,
                                                                                          re_load_deviator=point2_y,
                                                                                          eps_cons=eps_cons)
    x_old = copy.deepcopy(strain_no_loop)
    x = copy.deepcopy(strain)
    y = copy.deepcopy(deviator)
    qf = adv[2][1]
    xc = adv[2][0]
    x2 = adv[3][0]
    qf2 = adv[3][1]
    xocr = adv[1][0]
    E = adv[1][1]

    if Eur:
        point1_x = loop_strain_values[0]
        point2_x = loop_strain_values[1]
        point3_x = loop_strain_values[2]
        point1_x_index = loop_indexes[0]
        point2_x_index = loop_indexes[1]
        point3_x_index = loop_indexes[2]
    else:
        point1_x = 0
        point2_x = 0
        point3_x = 0
        point1_x_index = 0
        point2_x_index = 0
        point3_x_index = 0


    # ограничение на хс (не меньше чем x_given)
    if xc <= 0.025:
        xc = np.random.uniform(0.025, 0.03)
    # Точки нужно задавать на сетке:
    index_xc, = np.where(x_old >= xc)
    xc = x_old[index_xc[0]]

    # x_given определяется на 20 процентах нагружения
    index_02qf, = np.where(y >= 0.5 * qf)
    x_given = x_old[index_02qf[0]]
    x_end = 0.15  # последняя точка обьемной деформации
    # обрезаем массив до x_end
    index_xend, = np.where(x_old >= x_end)
    x_end = x_old[index_xend[0]]

    len_x_dilatacy = (x_old[-1] - x_old[-2]) * 10  # длина линейного участка дилатансии
    len_line_end = (x_old[-1] - x_old[-2]) * 2  # длина последнего линейного участка




    """
            Функция построения обьемной деформации соединением сплайна и двух кривых Безьею

            :param x_given: точка в которой задан коэффициент Пуассона
            :m_given: коэффициент Пуассона
            :xc: точка разрушения
            :v_d2: значение обьемной деформации в последней точке
            :x_end: последняя точка массива х для кривой обьемной деформаци
            :angle_of_dilatancy: угол дилатансии от 0 до 40 градусов
            :angle_end: угол наклона последнего линейного участка от 0 до 30 градусов
            :len_x_dilatacy: длина линенйного участка дилатансии
            :v_d_xc: значение обьемной деформации в точке хс
            :len_line_end: длина последнего линейного участка
            """
    # коэффициент Пуассона
    try:
        kwargs["m_given"]
    except KeyError:
        kwargs["m_given"] = 0.15
    # значение обьемной деформации в точке хс
    try:
        kwargs["v_d_xc"]
    except KeyError:
        kwargs["v_d_xc"] = np.random.uniform(-0.0003, -0.00005)  # max = 0.005 # np.random.uniform(-0.003, 0.0001)
    # угол дилатансии
    try:
        kwargs["angle_of_dilatacy"] = np.tan(kwargs["angle_of_dilatacy"] * np.pi / 180)
    except KeyError:
        kwargs["angle_of_dilatacy"] = np.tan(30 * np.pi / 180)  # np.random.uniform(0.015, 0.03)

    is_no_peak = xc >= 0.15
    if is_no_peak:
        #print(is_no_peak)
        xc = np.random.uniform(0.2, 0.3)
        # old: xc =  x_old[-1] - len_x_dilatacy - 5 * (x_old[-1] - x_old[-2]) - len_line_end
    #для отрицательного угла дилатансии
    if kwargs["angle_of_dilatacy"] < 0:
        xc = np.random.uniform(0.2, 0.3)
        kwargs["angle_of_dilatacy"] = np.tan(30 * np.pi / 180)

    if xc > x_end - len_x_dilatacy / 2 - 5 * (x_old[-1] - x_old[-2]):  # если xc>чем точка начала
        # последнего линейного участка -5 шагов, то сдвигаем х_end за область 0.15
        x_end = x_end + abs(x_end - len_x_dilatacy / 2 - 5 * (x_old[-1] - x_old[-2]) - xc)

    # Прямая из х_given в хс
    if kwargs["v_d_xc"] < (-x_given * (1 - 2 * kwargs["m_given"])) / x_given * (xc - len_x_dilatacy / 2) * 0.8:
        local = (-x_given * (1 - 2 * kwargs["m_given"])) / x_given * (xc - len_x_dilatacy / 2) * 0.8
        kwargs["v_d_xc"] = local + abs(local) * 0.2

    # Ограничение на "угол" дилатансии, связанное с положеним точки хс и x_given
    # при положительных v_d_xc и малых значениях "угла" дилатансии
    if kwargs["angle_of_dilatacy"] < (kwargs["v_d_xc"] - (-x_given * (1 - 2 * kwargs["m_given"]))) / (
            xc - x_given) * 1.2:
        local = (kwargs["angle_of_dilatacy"] / 1.2 * (xc - x_given) + (-x_given * (1 - 2 * kwargs["m_given"])))

        # print('ВНИМАНИЕ! (2) v_d_xc ИЗМЕНЕН C ', kwargs["v_d_xc"], ' НА ', local - abs(local) * 0.2)
        # для получения бОльших значений v_d_xc необходимо увеличить угол angle_of_dilatacy
        kwargs["v_d_xc"] = local - abs(local) * 0.2

        # Вариант ограничения на угол angle_of_dilatacy:
        # kwargs["angle_of_dilatacy"] = (v_d_xc - (-x_given*(1-2*kwargs["m_given"]))) / (xc - x_given)
        # print('ВНИМАНИЕ! angle_of_dilatacy ИЗМЕНЕН')

    try:
        kwargs["angle_of_end"] = np.tan(kwargs["angle_of_end"] * np.pi / 180)
    except KeyError:
        kwargs["angle_of_end"] = np.tan(1 * np.pi / 180)  # np.random.uniform(0.015, 0.03)

    # TODO: возможно скорректировать условие на угол
    # угол наклона последнего линейного участка
    if kwargs["angle_of_end"] > 2 / 3 * kwargs["angle_of_dilatacy"]:
        kwargs["angle_of_end"] = 2 / 3 * kwargs["angle_of_dilatacy"]
        # print('ВНИМАНИЕ! angle_of_end ИЗМЕНЕН')
        # print(kwargs["angle_of_end"])

    v_d_xc = kwargs["v_d_xc"]
    # if kwargs["angle_of_dilatacy"]<= 0:
    #     v_d_xc = 0 #np.random.uniform(-0.0015, 0.0015) - np.random.uniform(0.0025, 0.0015)
    # else:
    #     v_d_xc = 0 #np.random.uniform(-0.0015, -0.0015) - (0.0025 - kwargs["angle_of_dilatacy"]*0.0001)

    # КОЭФ. b ПРЯМОЙ ИЗ ХС
    b_dilatancy = v_d_xc - kwargs["angle_of_dilatacy"] * xc
    # y В ТОЧКЕ (xc + len_x_dilatacy / 2)
    v_d_dilatancy_end = kwargs["angle_of_dilatacy"] * (xc + len_x_dilatacy / 2) + b_dilatancy
    # b = kx1 - y1; y2 = kx2 + b
    y_end_lim = kwargs["angle_of_end"] * (x_end - (xc + len_x_dilatacy / 2)) + v_d_dilatancy_end
    ang = np.tan(kwargs["angle_of_end"]) * 180 / np.pi
    try:
        kwargs["v_d2"]
    except:
        kwargs["v_d2"] = (((kwargs["angle_of_dilatacy"] -
                            abs(kwargs["angle_of_dilatacy"] - kwargs["angle_of_end"]) * np.random.uniform(0.2, 0.6))
                           * (x_end - len_line_end) + b_dilatancy))
        # np.random.uniform(-0.006, 0.001)  #
    if kwargs["v_d2"] <= y_end_lim:  # ТОЧКА НЕ НИЖЕ ЧЕМ ПРЕДЕЛЬНОЕ ЗНАЧЕНИЕ
        local = (kwargs["angle_of_dilatacy"] * (x_end - len_line_end) + b_dilatancy)
        h = abs(local - y_end_lim)
        if y_end_lim > 1 * 10 ** (-4):
            # print('(1)')
            # kwargs["v_d2"] = y_end_lim * 1.5
            kwargs["v_d2"] = y_end_lim + abs(h) * 0.2
        elif y_end_lim < -1 * 10 ** (-4):
            # print('(2)')
            # kwargs["v_d2"] = y_end_lim / 1.5
            kwargs["v_d2"] = y_end_lim + abs(h) * 0.2
        elif abs(y_end_lim) <= 1 * 10 ** (-4):
            # print('(3)')
            kwargs["v_d2"] = (2 * abs(v_d_dilatancy_end - v_d_xc) + abs(
                y_end_lim)) * 1.2  # abs(-x_given*(1-2*kwargs["m_given"]))*0.1
        # print('ВНИМАНИЕ! v_d2 ИЗМЕНЕН НИЖНИЙ ПРЕДЕЛ')
        # print('y_end_lim=', y_end_lim)
        # print('v_d2=', kwargs["v_d2"])
    # if abs(v_d_dilatancy_end) >= (kwargs["angle_of_dilatacy"] * (x_end - 20*len_line_end) + b_dilatancy):
    #     smooth_param = v_d_dilatancy_end-abs(v_d_dilatancy_end)*
    # else:
    #     smooth_param = 20

    # Ограничение на положение точки v_d2 (координата y) в x_end
    # смещение формируется за счет "уменьшения" угла дилатансии"
    # угол дилатансии не может быть "уменьшен" так, чтобы стать меньше angle_of_end
    # следовательно, "уменьшение" происходит пропорционально их разнице
    # чем Больше последняя константа, тем Больше уменьшение
    angle_of_dilatacy_max_limit_param = abs(kwargs["angle_of_dilatacy"] - kwargs["angle_of_end"]) * 0.2

    if (kwargs["v_d2"]) >= (((kwargs["angle_of_dilatacy"] - angle_of_dilatacy_max_limit_param)
                             * (x_end - len_line_end) + b_dilatancy)):

        kwargs["v_d2"] = (((kwargs["angle_of_dilatacy"] - angle_of_dilatacy_max_limit_param)
                           * (x_end - len_line_end) + b_dilatancy))

        # print('dil=', kwargs["angle_of_dilatacy"] * 0.6)
        # print('end=', kwargs["angle_of_end"])
        # local = (kwargs["angle_of_dilatacy"] * (x_end - len_line_end) + b_dilatancy)
        # h = abs(local - y_end_lim)
        # kwargs["v_d2"] = local - abs(h) * 0.2
        if kwargs["v_d2"] <= v_d_dilatancy_end:
            kwargs["v_d2"] = (kwargs["angle_of_dilatacy"] * (x_end - len_line_end) + b_dilatancy)
        # print('ВНИМАНИЕ! v_d2 ИЗМЕНЕН ВЕРХНИЙ ПРЕДЕЛ')
        # np.random.uniform(0, 0.015)  # np.random.uniform(0.015, 0.03)

    # print(kwargs["v_d2"])
    # print(v_d_dilatancy_end)

    m_given = kwargs.get('m_given')
    v_d2 = kwargs.get('v_d2')
    angle_of_dilatacy = kwargs.get('angle_of_dilatacy')
    angle_of_end = kwargs.get('angle_of_end')

    # x_vertex = np.random.uniform(x_given + 0.3 * (xc - x_given),
    #                              x_given + 0.7 * (xc - x_given))  # абцисса вершины обьемной деформации

    # y1, v_d_given = volumetric_deformation(x_old, x_given, m_given, xc + np.random.uniform(0.005, 0.01), v_d2, x_end, angle_of_dilatacy,
    #                                        angle_of_end, len_x_dilatacy, v_d_xc, len_line_end, Eur, point1_x, point2_x,
    #                                        point3_x)

    y1, v_d_given = volumetric_deformation(x_old, x_given, m_given, xc, v_d2, x_end, angle_of_dilatacy,
                                           angle_of_end, len_x_dilatacy, v_d_xc, len_line_end, Eur, point1_x, point2_x,
                                           point3_x)
    index_x2, = np.where(x >= 0.15)
    y1 = y1[:index_x2[0]]
    x = x[:index_x2[0]]
    y = y[:index_x2[0]]

    # формирование начального участка функции девиаторного нагружения
    y_bias = np.random.uniform(0.005, 0.015)  # смещение y
    y1_bias = np.random.uniform(0.001, 0.002)
    y2, v_d_given2 = volumetric_deformation(x_old, x_given, m_given, xc, v_d2, x_end, angle_of_dilatacy,
                                            angle_of_end, len_x_dilatacy, v_d_xc, len_line_end, Eur, point1_x, point2_x,
                                            point3_x)
    y2 = y2[:index_x2[0]]
    if not Eur:
        try:
            y1 += deviation_volume_strain(x, x_given, x[np.argmax(y)], 0.008, 0.001)
            y2 += deviation_volume_strain(x, x_given, 0.15, 0.005, 0.002)
        except:
            pass


    random_param = np.random.uniform(-0.00125 / 4., 0.00125 / 4., len(y1))
    y1 += random_param
    y2 += random_param

    y1_proiz = (y1[1] - y1[0]) / (x[1] - x[0])

    x_last_point = np.random.uniform(0.005, 0.01) - (
            x[-1] - x[-2])  # положительная последняя точка х для метрвого хода штока
    x_start = np.linspace(0, x_last_point,
                          int(x_last_point / (x[-1] - x[-2])) + 1)  # положительный масив х для метрвого хода штока
    slant = np.random.uniform(20, 30)  # наклон функции экспоненты
    amplitude = np.random.uniform(15, 25)  # высота функции экспоненты
    y_start = exponent(x_start, amplitude, slant)  # абциссы метрвого хода штока
    x_start -= x_start[
                   -1] + (x[-1] - x[
        -2])  # смещение массива x для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    y_start -= y_start[
        -1]  # смещение массива y для метрвого хода штока кривой девиаторного нагружения в отрицальную область
    y_start = y_start + np.random.uniform(-1, 1, len(y_start))
    y_start = discrete_array(y_start, 0.5)  # наложение ступенчватого шума на мертвый ход штока
    x = np.hstack((x_start, x))  # добавление начального участка в функцию девиаторного нагружения

    x += abs(x[0])  # смещение начала кривой девиаторного нагруружения в 0

    y = np.hstack((y_start, y))  # добавление начального участка в функцию девиаторного нагружения
    y += abs(y[0])  # смещение начала кривой девиаторного нагружения в 0
    y[0] = 0.  # искусственное зануление первой точки

    # метрвый ход штока кривой обьемной деформации
    y1_start = spline([x_start[0], 0], [0, y1_bias], x_start, 0, y1_proiz, k=3)
    y1 = np.hstack((y1_start, y1 + y1_bias))  # добавление мертвого хода штока в функцию обьемной деформации
    y2 = np.hstack((y1_start, y2 + y1_bias))

    y1[0] = 0.  # искусственное зануление первой точки
    y2[0] = 0.

    random_param = np.random.uniform(-0.00125 / 8., 0.00125 / 8., len(y1))
    y1 = y1 + random_param
    y1 = discrete_array(y1, 0.00125 / 2.)  # дискретизация по уровню функции обьемной деформации
    y2 = y2 + random_param
    y2 = discrete_array(y2, 0.00125 / 8.)  # дискретизация по уровню функции обьемной деформации

    if Eur:
        # для записи в файл
        point1_x_index = point1_x_index + len(x_start)
        point2_x_index = point2_x_index + len(x_start)
        point3_x_index = point3_x_index + len(x_start)

        # + 1 для последней разгрузки потому что точка принадлежит кривой как и в петле
        indexs_loop = [point1_x_index, point2_x_index, point3_x_index]
    else:
        indexs_loop = [0, 0, 0]

    if U:
        E_U = U / x50
        x_old, x_U, y_U, *__ = dev_loading(U, E_U, sigma3, K0, fracture_strain=kwargs.get('xc'),
                                           residual_strength_strain=1.2 * kwargs.get('xc'),
                                           residual_strength=np.random.uniform(0.3, 0.7)*U,
                                           OC_deviator=0, gaus_or_par=0, amount_points=amount_points,
                                           unload_deviator=0.8*U, Eur=False, re_load_deviator=10, eps_cons=eps_cons)
        index_x2, = np.where(x_U >= 0.15)
        x_U = x_U[:index_x2[0]]
        y_U = y_U[:index_x2[0]]

        #x_last_point = np.random.uniform(0.005, 0.01) - (x_U[-1] - x_U[-2])
        x_start = np.linspace(0, x_last_point, int(x_last_point / (x_U[-1] - x_U[-2])) + 1)
        slant = np.random.uniform(20, 30)
        #amplitude = np.random.uniform(15, 25)
        amplitude *= np.random.uniform(1, 2)
        y_start = exponent(x_start, amplitude, slant)
        x_start -= x_start[-1] + (x_U[-1] - x_U[-2])
        y_start -= y_start[-1]
        y_start = y_start + np.random.uniform(-1, 1, len(y_start))
        y_start = discrete_array(y_start, 0.5)
        x_U = np.hstack((x_start, x_U))

        x_U += abs(x_U[0])

        y_U = np.hstack((y_start, y_U))
        y_U += abs(y_U[0])
        y_U[0] = 0.

        """u = exponent(x[len(x_start):np.argmax(y)] - x[len(x_start)], U, np.random.uniform(8, 10)) + amplitude
        y_start = np.linspace(0, amplitude, len(x_start))
        u *= (np.max(u)/(U+amplitude))
        shape = np.random.uniform(0.005, 0.01)
        fall = np.random.uniform(0.05, 0.1) * U
        i, = np.where(x > x[np.argmax(y)] + shape)
        u_fall = step_sin(mirrow_element(x[np.argmax(y): i[0]], (x[np.argmax(y)] + x[i[0]])/2), fall/2, (x[np.argmax(y)] + x[i[0]])/2, shape) + U + amplitude - fall/2
        y_U = np.hstack((
            y_start,
            u,
            u_fall,
            np.full(len(y) - len(u) - len(y_start) - len(u_fall), u_fall[-1])
        ))
        y_U += abs(y_U[0])
        y_U[0] = 0.
        y_U += create_deviation_curve(x, 10, points=np.random.uniform(5, 8), low_first_district=1)
        y_U += np.random.uniform(-3, 3, len(y_U))
        y_U[0] = 0.
        y_U *= ((U + amplitude )/ np.max(y_U))
        y_U[0] = 0.
        discrete_array(y_start, 0.5)
        y_U[len(x_start)] = amplitude
        y_U[len(x_start) + 1] = amplitude
        y_U[len(x_start) - 1] = amplitude"""

        return x, y, y1, y2, indexs_loop, len(x_start)

    return x, y, y1, y2, indexs_loop, len(x_start)


def vol_test():
    m_given_all = [0.15, 0.2, 0.45]
    v_d_xc_all = [-0.01, 0, 0.0001, 0.005]
    angle_of_dilatacy_all = [0.1, 1, 10, 40]
    angle_of_end_all = [0, 1, 5, 30]
    v_d2_all = [-0.8, -0.001, 0, 0.001, 0.8]

    for i in range(len(m_given_all)):
        for k in range(len(v_d_xc_all)):
            for l in range(len(angle_of_dilatacy_all)):
                for m in range(len(angle_of_end_all)):
                    for n in range(len(v_d2_all)):
                        x, y, z, x_given, v_d_given, xc, v_d_xc \
                            = volumetric_deformation_test(m_given_all[i], v_d_xc_all[k],
                                                          np.arctan(angle_of_dilatacy_all[l] * np.pi / 180),
                                                          np.arctan(angle_of_end_all[m] * np.pi / 180), v_d2_all[n])

                        plt.figure(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1) + str(n + 1))
                        plt.plot(x, z)
                        plt.scatter(x_given, v_d_given, color='red')
                        plt.scatter(xc, v_d_xc, color='green')
                        plt.savefig(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1) + str(n + 1) + '.png')


# Запись в файл
def text_file(file_path, point_time, time, volumetric_deformation, x, y, z, indexs_loop, press_initial=150,
              E=50000, time_initial=3600, cell_press_initial=0, current_cell_press=150, deviator_initial=0,
              velocity_d=0.075, time_initial_d=5000, vert_def_initial_d=-0.1, cell_press_initial_d=150,
              pore_press_initial_d=0):
    """Сохранение текстового файла формата Willie.
                Передается папка, массивы"""
    p = os.path.join(file_path, "Консолидация+Девиаторное нагружение.txt")

    def make_string(data, i):
        s = ""
        for key in data:
            s += str(data[key][i]) + '\t'
        s += '\n'
        return (s)

    # Запись файла для консолидации
    k = -3
    qv_loading_stage = (k * press_initial / E) * (
        np.random.uniform(1.5, 2))  # смещение по оси y прямой начального участка кривой консолидации
    pressure_velosity = np.random.uniform(4, 5)  # скорость нагружения
    load_stage_start_time = press_initial / pressure_velosity  # начало начального участка кривой консолидации
    b = qv_loading_stage  # параметр прямой начального участка консолидации
    k = -b / load_stage_start_time  # параметр прямой начального участка консолидации
    load_stage_time = (np.linspace(-load_stage_start_time, 0, int(load_stage_start_time / (point_time / 60)
                                                                  + 1)))  # массив времени для начального участка
    # с таким же шагом, что в консолидации
    load_stage = -k * load_stage_time + b  # начальный участок кривой консолидации

    time = np.hstack((load_stage_time, time)) + load_stage_start_time + time_initial  # массив времени смещенный в 0
    # и от 0 на величину начального значения времени time_initial
    volumetric_deformation = np.hstack(
        (load_stage, volumetric_deformation))  # обьемная деформации из консолидации для нового участка времени

    # на начальном участке времени записываем 'LoadStage', на основном Stabilization
    action = []
    action_changed = []
    index_last_loadstage, = np.where(time >= load_stage_start_time + time_initial)
    for i in range(len(time)):
        if i <= index_last_loadstage[0]:
            action.append('LoadStage')
        else:
            action.append('Stabilization')

    # на последнем 'LoadStage' - 'True'
    Last_Load_Stage_flag = 1
    for i in range(len(action) - 1):
        if (action[i + 1] == "Stabilization") and (Last_Load_Stage_flag):
            action_changed.append('True' + '')
            Last_Load_Stage_flag = 0
        else:
            action_changed.append('')
    action_changed.append('True')

    poissons_ratio = np.random.uniform(0.2, 0.3)
    vertical_deformation = -volumetric_deformation / (1 - 2 * poissons_ratio)

    # на начальном участке времени линейно убывает от cell_press_initial до current_cell_press, далее постоянно
    cell_press = np.zeros(len(time))
    for i in range(len(time)):
        if time[i] <= load_stage_start_time + time_initial:
            cell_press[i] = ((cell_press_initial - current_cell_press) / (
                    time_initial - time_initial - load_stage_start_time)) * time[i] + cell_press_initial - (
                                    (cell_press_initial - current_cell_press) / (
                                    time_initial - time_initial - load_stage_start_time)) * time_initial
        else:
            cell_press[i] = current_cell_press

    # запись девиаторного нагружения в файл
    h = 76
    time_d = time_initial_d + (x * h) / velocity_d  # массив времени девиаторного нагружения
    action_d = np.full(len(time_d), 'WaitLimit')
    # indexs_loop = [point1_x_index[0], point2_x_index[0], point3_x_index[0], len(x) - len(x_unload), Eur]

    if indexs_loop[4]:
        for i in range(len(action_d)):
            if i >= indexs_loop[0] and i < indexs_loop[1]:
                action_d[i] = 'CyclicUnloading'
            elif i >= indexs_loop[1] and i <= indexs_loop[2]:
                action_d[i] = 'CyclicLoading'
            elif i >= indexs_loop[3]:
                action_d[i] = 'Unloading'
    else:
        for i in range(len(action_d)):
            if i >= indexs_loop[3]:
                action_d[i] = 'Unloading'
    action_changed_d = []
    # for i in range(len(action_d) - 1):
    #     action_changed_d.append('')
    # action_changed_d.append('True')

    Last_WaitLimit_flag = 1
    for i in range(len(action_d) - 1):
        if action_d[i] == "WaitLimit" and action_d[i + 1] == "Unloading" and Last_WaitLimit_flag:
            action_changed_d.append('True' + '')
            Last_WaitLimit_flag = 0
        else:
            action_changed_d.append('')
    action_changed_d.append('')

    def round_array(x, count=0):
        '''Функция округления для заданного числа знаков'''
        for i in range(len(x)):
            x[i] = round(x[i], count)
        return x

    data = {
        "Time": round_array(np.hstack((time, time_d)), count=3),
        "Action": np.hstack((action, action_d)),
        "Action_Changed": np.hstack((action_changed, action_changed_d)),
        "SampleHeight_mm": round_array(np.full(len(np.hstack((time, time_d))), 76)),
        "SampleDiameter_mm": round_array(np.full(len(np.hstack((time, time_d))), 38)),
        "Deviator_kPa": round_array(np.hstack((np.full(len(np.hstack((time))), deviator_initial), y))),
        "VerticalDeformation_mm": round_array(np.hstack((vertical_deformation, -abs(x * h + vert_def_initial_d))),
                                              count=6),
        "CellPress_kPa": round_array(
            np.hstack((cell_press, np.full(len(time_d), cell_press_initial_d))) + np.random.uniform(-0.1, 0.1, len(
                np.hstack((time, time_d)))), count=6),
        "CellVolume_mm3": round_array(np.hstack((abs(
            volumetric_deformation) * np.pi * 19 ** 2 * 76 + create_deviation_curve(time, 0.1, val=(1, 1),
                                                                                    points=False),
                                                 z * np.pi * 19 ** 2 * 76)), count=4),
        "PorePress_kPa": round_array(np.hstack((np.full(len(time), 0),
                                                np.full(len(time_d), pore_press_initial_d) + np.random.uniform(-0.1,
                                                                                                               0.1, len(
                                                        time_d))))),
        "PoreVolume_mm3": round_array(
            np.hstack((abs(volumetric_deformation) * np.pi * 19 ** 2 * 76, z * np.pi * 19 ** 2 * 76))),
        "VerticalPress_kPa": round_array(np.hstack(
            (cell_press + np.full(len(time), deviator_initial), y + cell_press_initial_d)) + np.random.uniform(-0.1,

                                                                                                               0.1, len(
                np.hstack((time, time_d)))), count=6),
        "Trajectory": np.hstack((np.full(len(time), 'Consolidation'), np.full(len(time_d), 'CTC')))

    }
    # for key in data:
    #     print(key)
    #     print(len(data[key]))

    with open(p, "w") as file:
        file.write(
            "Time" + '\t' + "Action" + '\t' + "Action_Changed" + '\t' + "SampleHeight_mm" + '\t' + "SampleDiameter_mm" + '\t' +
            "Deviator_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "CellPress_kPa" + '\t' + "CellVolume_mm3" + '\t' +
            "PorePress_kPa" + '\t' + "PoreVolume_mm3" + '\t' + "VerticalPress_kPa" + '\t' +
            "Trajectory" + '\n')
        for i in range(len(data["Time"])):
            file.write(make_string(data, i))

    file.close()


def volumetric_deformation_test(m_given, v_d_xc, angle_of_dilatacy, angle_of_end, v_d2):
    x, y, z, x_given, v_d_given, xc, v_d_xc = curve(30 * 5, 8220 * 5, xc=0.02, x2=0.15, qf2=100, m_given=m_given,
                                                    amount_points=500, v_d_xc=v_d_xc,
                                                    angle_of_dilatacy=angle_of_dilatacy,
                                                    angle_of_end=angle_of_end,
                                                    v_d2=v_d2)

    return x, y, z, x_given, v_d_given, xc, v_d_xc




if __name__ == '__main__':
    versions = {
        "Triaxial_Dynamic_Soil_Test": 1.71,
        "Triaxial_Dynamic_Processing": 1.71,
        "Resonance_Column_Siol_Test": 1.1,
        "Resonance_Column_Processing": 1.1
    }
    from matplotlib import rcParams

    rcParams['font.family'] = 'Times New Roman'
    rcParams['font.size'] = '12'
    rcParams['axes.edgecolor'] = 'black'
    plt.grid(axis='both', linewidth='0.6')
    # plt.xlabel("Относительная вертикальная деформация $ε_1$, д.е")
    # plt.ylabel("Девиатор q, кПа")
    #    x1, y1, x_log1, y_0_xca1, point_time1 = function_consalidation(Cv=0.379, point_time=1, reverse=1, last_point=250)

    # {'E50': 29710.0, 'sigma_3': 186.4, 'sigma_1': 981.1, 'c': 0.001, 'fi': 42.8, 'qf': 794.7, 'K0': 0.5,
    #  'Cv': 1.906625504418318, 'Ca': 0.006335165735463461, 'poisson': 0.34, 'build_press': 500.0, 'pit_depth': 7.0,
    #  'Eur': 61121, 'dilatancy': 10.55, 'OCR': 1, 'm': 0.64, 'lab_number': '7а-1',
    #  'data_phiz': {'borehole': '7а', 'depth': 19.0, 'name': 'Песок крупный неоднородный', 'ige': '-', 'rs': 2.73,
    #                'r': '-', 'rd': '-', 'n': '-', 'e': 0.5, 'W': 12.8, 'Sr': '-', 'Wl': '-', 'Wp': '-', 'Ip': '-',
    #                'Il': '-', 'Ir': '-', 'str_index': '-', 'gw_depth': '-', 'build_press': 500.0, 'pit_depth': 7.0,
    #                '10': '-', '5': '-', '2': 6.8, '1': 39.2, '05': 28.0, '025': 9.2, '01': 6.1, '005': 10.7, '001': '-',
    #                '0002': '-', '0000': '-', 'Nop': 7, 'flag': False}, 'test_type': 'Трёхосное сжатие с разгрузкой'}
    # (596.48, 382.8)

    x, y, y1, y2, indexs_loop, a, x_U, y_U = curve(800, 29710.0, xc=0.15, x2=0.16, qf2=500, qocr=0, m_given=0.35,
                                 amount_points=500, angle_of_dilatacy=6, y_rel_p=596, point2_y=382, U=300)

    #
    # i, = np.where(x >= max(x) - 0.15)
    # x = x[i[0]:] - x[i[0]]
    # z = z[i[0]:] - z[i[0]]
    # z1 = z1[i[0]:] - z1[i[0]]
    # y = y[i[0]:] - y[i[0]]
    # pu, d = find_puasson_dilatancy(x, y, z)
    # d = d[0]
    # y += np.random.uniform(-1, 1, len(y))
    # #E, q = find_E50_qf(x, y)
    # #print(E)
    # i = np.argmax(y)
    # y -= y[0]
    plt.plot(x[a:] - x[a], y[a:] - y[a], x[a:] - x[a], y_U[a:] - y_U[a])
    #with open("C:/Users/Пользователь/Desktop/test_file.txt", "w") as file:
        #for i in range(len(y)):
            #file.write(str(np.round(-x[i], 4)).replace(".", ",") + "\t" + str(np.round(y[i], 4)).replace(".", ",")+ "\n")
    # plt.plot(x, z1, label="Статическая кривая")
    # plt.scatter(x[i], z[i], color = "red")
    # plt.plot(ff, f(ff), linewidth =3, label = "Динамическая кривая")
    plt.legend()
    plt.show()
