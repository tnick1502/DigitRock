# coding: utf-8

# In[34]:


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
from scipy.signal import argrelextrema


from general.general_functions import *

def compute_l2_norm(x: numpyArray['N2', float]) -> numpyArray['N1', float]:
    return x**2

#print(compute_l2_norm(arr = np.array([(1, 2), (3, 1.5), (0, 5.5)])))



# from consolidation_functions import *


def find_first_step(strain, deviator):
    # Начальная ступень графика

    if np.size(strain) > 3:
        m = 0
        while (abs(sum(deviator[m + 11:m + 21]) - sum(deviator[m + 10:m + 20])) - abs(
                sum(deviator[m + 1:m + 11]) - sum(deviator[m:m + 10]))) < 5:
            if m > len(strain) - 40:
                break
            m += 1

        if m == 0:
            while (abs(sum(deviator[m + 11:m + 21]) - sum(deviator[m + 10:m + 20])) - abs(
                    sum(deviator[m + 1:m + 11]) - sum(deviator[m:m + 10]))) < 10:
                if m > len(strain) - 40:
                    break
                m += 1
        if strain[m] > 5:
            m = 0

        if deviator[m] > 0.3 * max(deviator):
            m = 0

        return m
    else:
        return 0


def find_first_step_for_soil_test(strain):
    # Начальная ступень графика
    i, = np.where((strain - (strain[-1] - 0.15)) > 0)
    return i[0] - 1


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


def find_Eur(strain, deviator, reload):
    """Поиск Eur"""

    # Проверяем, есть ли разгрзка и не отрезали ли ее
    if len(reload) == 2 and reload[0] > 0 and reload != [0, 0]:
        try:
            point1 = np.argmin(deviator[reload[0]: reload[1]]) + reload[0]  # минимум на разгрузке
            point2 = reload[0]  # максимум на разгрузке

            if (strain[point2] - strain[point1]) < 0.000001:
                Eur = "-"
            else:
                Eur = round(((deviator[point2] - deviator[point1]) / (strain[point2] - strain[point1])) / 1000, 2)
        except ValueError:
            Eur = "-"
    else:
        Eur = "-"

    return Eur


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

def deviation_volume_strain1(x, x_given, xc, len_x_dilatacy, deviation=0.0015):
    index_x_given, = np.where(x >= x_given)
    n = xc / 0.15
    index_x_start_dilatacy, = np.where(x >= (xc - len_x_dilatacy * 2))
    index_x_end_dilatacy, = np.where(x >= (xc + len_x_dilatacy * 2))

    if xc >= 0.14:
        deviation_vs = np.hstack((np.zeros(index_x_given[0]),
                                  create_deviation_curve(x[index_x_given[0]:], deviation * 2 * n,
                                                         points=np.random.uniform(5, 10),
                                                         val=(0.3, 1), borders='zero diff') + create_deviation_curve(
                                      x[index_x_given[0]:],
                                      deviation * 0.7 * n, points=np.random.uniform(15, 30),
                                      val=(0.3, 1), borders='zero diff')))
        return deviation_vs

    if xc <= 0.03:
        deviation_vs = np.hstack((np.zeros(index_x_given[0]),
                                  create_deviation_curve(x[index_x_given[0]:], deviation * 2 * n,
                                                         points=np.random.uniform(5, 10),
                                                         val=(0.3, 1), borders='zero diff') + create_deviation_curve(
                                      x[index_x_given[0]:],
                                      deviation * 0.7 * n, points=np.random.uniform(15, 30),
                                      val=(0.3, 1), borders='zero diff')))
        return deviation_vs

    try:
        deviation_vs = np.hstack((np.zeros(index_x_given[0]),
                                  create_deviation_curve(x[index_x_given[0]:index_x_start_dilatacy[0]],
                                                         deviation * 2 * n, points=np.random.uniform(5, 10),
                                                         val=(0.3, 1), borders='zero diff') + create_deviation_curve(
                                      x[index_x_given[0]:index_x_start_dilatacy[0]],
                                      deviation * 0.7 * n, points=np.random.uniform(15, 30),
                                      val=(0.3, 1), borders='zero diff'),

                                  np.zeros(len(x[index_x_start_dilatacy[0]:index_x_end_dilatacy[0] + 1])),
                                  create_deviation_curve(x[index_x_end_dilatacy[0] + 1:], deviation, val=(0.3, 1),
                                                         borders='zero diff')))
        return deviation_vs

    except (ValueError, IndexError):
        deviation_vs = np.hstack((np.zeros(len(x[:index_x_given[0]])),
                                  create_deviation_curve(x[index_x_given[0]:index_x_start_dilatacy[0]], deviation / 8,
                                                         val=(1, 0.3), borders='zero diff'),
                                  np.zeros(len(x[index_x_start_dilatacy[0]:index_x_end_dilatacy[0] + 1])),
                                  create_deviation_curve(x[index_x_end_dilatacy[0] + 1:], deviation, val=(0.3, 1),
                                                         borders='zero diff')))
        return deviation_vs

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
def params_gip_exp_tg(x, e50, qf, x50, xc, qocr):
    '''возвращает коэффициенты гиперболы, экспоненты и тангенса'''
    k = 1.  # k - линейный коэффициент учета влияния функции гиперболы и экспоненты
    kp = np.linspace(0, 1, len(x))  # kp - коэффициент влияния на k, учитывающий переуплотнение qocr
    # для переуплотнения

    if e50 <= 70000:
        k = 1. / 68000. * e50 - 1. / 34
    elif e50 > 70000:
        k = 1.

    for i in range(len(x)):
        kp[i] = 1.

    def equations_e(p_e):
        a1_e, k1_e = p_e  # коэффициенты экспоненты
        return -a1_e * (np.exp(-k1_e * x50) - 1) - qf / 2, -a1_e * (np.exp(-k1_e * xc) - 1) - qf

    # начальные приближения заданные по участкам
    if e50 > 40000:
        a1_e, k1_e = fsolve(equations_e, (1, 1))
        nach_pr_a1_e = 1
        error = equations_e([a1_e, k1_e])
        while abs(error[0]) >= 10 or abs(error[1]) >= 10:
            nach_pr_a1_e += 1
            a1_e, k1_e = fsolve(equations_e, (nach_pr_a1_e, 1))
            error = equations_e([a1_e, k1_e])

    else:
        nach_pr_a1_e, nach_pr_k1_e = 600, 1
        a1_e, k1_e = fsolve(equations_e, (nach_pr_a1_e, nach_pr_k1_e))
        nach_pr_a1_e = 1
        error = equations_e([a1_e, k1_e])
        count = 0
        while (a1_e <= 0) or (k1_e <= 0) or (a1_e == nach_pr_a1_e or k1_e == nach_pr_k1_e) or (
                a1_e * k1_e < 1000) or (
                (abs(error[0]) >= 550 or abs(error[1]) >= 550) and count < 50):  # если начальное приближение a1_e
            # или k1_e равно 1 или произведение коээфициентов (приблизительно равно e50)
            #  меньше 1000, то ищутся другие начальные приближения
            nach_pr_a1_e += 1
            a1_e, k1_e = fsolve(equations_e, (nach_pr_a1_e, nach_pr_k1_e))
            error = equations_e([a1_e, k1_e])
            if (abs(error[0]) >= 550 or abs(error[1]) >= 550):
                count += 1

    # коэффициенты гиперболы
    k1_g = -2 / xc + 1 / x50
    a1_g = qf * (k1_g * x50 + 1.) / (2. * x50)

    def equations_t(p_t):
        a1_t, k1_t = p_t  # коэффициенты тангенса
        return ((a1_t * ((np.arctan(k1_t * x50)) / (0.5 * np.pi)) - qf / 2),
                (a1_t * ((np.arctan(k1_t * xc)) / (0.5 * np.pi)) - qf))

    if e50 > 50000:
        a1_t, k1_t = fsolve(equations_t, (1, 1))
    else:
        a1_t, k1_t = fsolve(equations_t, (600, 1))

    xocr = 0.  # абцисса точки переуплотнения
    if (qocr != 0.) & (qocr <= qf / 2.):  # если qocr находится до qf/2, то xocr рассчитывается
        # из функции гиперболы
        xocr = qocr / (a1_g - qocr * k1_g)
        for i in range(len(x)):
            kp[i] = form_kp(x[i], qf, k, xocr, xc, qocr, x50)

    elif (qocr != 0.) & (qocr > qf / 2.) & (e50 <= 70000):  # если qocr находится после qf/2 и e50 находится до 70000,
        # то xocr рассчитывается из функции экспоненты
        def equations_xocr(xocr):
            return (-a1_e * (np.exp(-k1_e * xocr) - 1) - qocr)

        xocr = fsolve(equations_xocr, 0)
        for i in range(len(x)):
            kp[i] = form_kp(x[i], qf, k, xocr, xc, qocr, x50)

    elif (qocr != 0.) & (qocr > qf / 2.) & (e50 > 70000):  # если qocr находится после qf/2 и e50 находится после 70000,
        # то xocr рассчитывается из функции тангенса, так как переуплотнение плавнее
        def equations2(xocr):
            return (a1_t * ((np.arctan(k1_t * xocr)) / (0.5 * np.pi)) - qocr)

        xocr = fsolve(equations2, 0)
        for i in range(len(x)):
            kp[i] = form_kp(x[i], qf, k, xocr, xc, qocr, x50)

    elif qocr > (0.8 * qf):  # ограничение на qocr (если ограничение не выполняется, то
        # строится сумма функций экспоненты и кусочной функции синуса и параболы для e50<=70000
        # и тангенса и кусочной функции синуса и параболы для e50>70000
        for i in range(len(x)):
            kp[i] = 0.

    return a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr


def hevisaid(x, sdvig, delta_x):
    ''' возвращет функцию Хевисайда, которая задает коэффициент влияния kp'''
    return 1. / (1. + np.exp(-2 * 10 / delta_x * (x - sdvig)))


def gip_and_exp_or_tg(x, e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, qocr,
                      xocr):
    '''сумма функций гиперболы и экспоненты с учетом коэффициентов влияния'''

    ret = ((kp * k) * (a1_g * x / (1 + k1_g * x)) + (
            (1. - kp * k) * (-a1_e * (np.exp(-k1_e * x) - 1))))  # сумма гиперболы и экспоненты

    if (qocr > qf / 2.) & (qocr != 0.) & (x > x50) & (e50 <= 70000):
        ret = ((kp * k) * (a1_g * x / (1 + k1_g * x)) + (
                (1. - kp * k) * (-a1_e * (np.exp(-k1_e * x) - 1))))  # сумма гиперболы и экспоненты (x>x50)

    elif (qocr > qf / 2.) & (qocr != 0.) & (x > x50) & (e50 > 70000):
        ret = ((kp * k) * (a1_g * x / (1 + k1_g * x)) + (
                (1. - kp * k) * (
                a1_t * ((np.arctan(k1_t * x)) / (0.5 * np.pi)))))  # сумма гиперболы и тангенса (x>x50)
    elif (qocr > 0.8 * qf) & (qocr != 0.):
        ret = ((kp * k) * (a1_g * x / (1 + k1_g * x)) + (
                (1. - kp * k) * (-a1_e * (np.exp(
            -k1_e * x) - 1))))  # в случае невыполнения ограничения на qocr, строится только экспонента (kp=0)

    if (qocr <= qf / 2.) & (qocr != 0.) & (
            x <= x50):
        if x <= xocr:  # сумма функций с учетом коэффициентов влияния до xocr (x<x50)
            ret = ((1. - kp * k) * (a1_g * x / (1 + k1_g * x)) + (
                    (kp * k) * (-a1_e * (np.exp(-k1_e * x) - 1))))  # сумма гиперболы и экспоненты
        else:  # сумма функций с учетом коэффициентов влияния после xocr (x<x50)
            ret = ((1. - kp * (1 - k)) * (a1_g * x / (1 + k1_g * x)) + (
                    (kp * (1 - k)) * (-a1_e * (np.exp(-k1_e * x) - 1))))  # сумма гиперболы и экспоненты

    return ret


def cos_par(x, e50, qf, x50, xc, hlow):
    '''возвращает функцию косинуса
     и параболы для участка x50 qf'''

    sm = (xc - x50) / 2  # смещение
    # коэффицент учитывающий влияние на высоту функции при различных значениях e50
    if e50 < 5340:
        vl = 0
    elif (e50 <= 40000) and (e50 >= 5340):
        kvl = 1 / 34660
        bvl = -5340 * kvl
        vl = kvl * e50 + bvl  # 1. / 40000. * e50 - 1. / 8
    elif e50 > 40000:
        vl = 1.

    h = 0.035 * qf * vl - hlow  # высота функции
    if h < 0:
        h = 0

    k = h / (-xc + x50 + sm) ** 2

    # фиромирование функции
    if x < x50:
        cos_par = 0
    elif (x >= x50) and (x <= x50 + sm):
        cos_par = h * (1 / 2) * (np.cos((1. / sm) * np.pi * (x - x50) - np.pi) + 1)  # косинус
    elif (x > x50 + sm) and (x < xc):
        cos_par = -k * (x - x50 - sm) ** 2 + h  # парабола
    elif x >= xc:
        cos_par = 0

    return cos_par


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


def smoothness_condition(qf, x50):
    '''возвращает предельное значение xc при котором возможно
    построение заданной функции'''
    k_lim = qf / (2 * x50)
    x_lim = (qf / k_lim)

    x_lim += 0.6 / 100

    return x_lim


def form_kp(x: float, qf, k, xocr, xc, qocr, x50):
    '''вовзращает коэффициент влияния kp'''
    kp = 1.
    if qocr > qf / 2.:  # если qsr на участке от qf / 2

        if qocr > (0.8 * qf):  # ограничение на qocr если ограничение не выполняется, то
            # строится экспоненты
            kp = 0.

        else:
            if x <= xocr:  # принудительное зануление отрицательной части функции Хевисайда
                kp = 0.
            elif (x > xocr) & (x <= xc):
                delta = ((abs(xocr - x50)) / (k + 0.000001)) * 10  # ширина Хевисайда
                kp = 2 * hevisaid(x, xocr, delta) - 1.

    elif (qocr < qf / 2.) & (qocr != 0.):  # если qsr на участке до qf / 2.
        if x > xocr:

            delta = abs(10 * (x50 - xocr + 0.000001))  # ширина Хевисайда
            kp = 2 * hevisaid(x, xocr, delta) - 1
        else:
            kp = 0.  # принудительное зануление отрицательной части функции Хевисайда

    elif qocr == 0.:  # для нулевого переуплотнения
        kp = 1.

    elif qocr == qf / 2.:  # для qocr == qf/2.
        if x <= xocr:  # до xsr строится функция гиперболы
            kp = 0.
        if x > xocr:
            kp = 1.  # после хsr строится функция суммы гиперболы и экспоненты
            # или тангенса с учетом коэффициентов влияния
    if (xocr == 0.) & (qocr <= (0.8 * qf)):
        kp = 1.

    return kp


def sensor_accuracy(x, y, qf, x50, xc):
    '''возвразщает зашумеленную функцию без шума в характерных точках'''

    sh = np.random.uniform(-1, 1, len(x))
    index_qf_half, = np.where(y >= np.max(y) / 2)
    index_qf, = np.where(y >= np.max(y))
    if xc > max(x):  # если хс последня точка в массиве или дальше
        index_qf, = np.where(x >= max(x))
    for i in range(len(y)):  # наложение шума кроме промежутков для характерных точек
        if (i < index_qf_half[0] - 2) or ((i > index_qf_half[0] + 2) and ([i] < index_qf[0] - 2)) or (
                i > index_qf[0] + 2):
            if (y[i] + sh[i] < np.max(y)):
                y[i] = y[i] + sh[i]
            else:
                y[i] = y[i] - np.random.uniform(0.1, 0.5)  # в районе максимума шум меньше первоначального
    return y


def loop(x, y, Eur, y_rel_p, point2_y):

    # ip1, = np.where(np.abs(y-y_rel_p) <= 0.0001)  # ищем нужный индекс в исходном массиве
    ip1, = np.where(y >= y_rel_p)

    if not np.size(ip1) > 0:
        y_rel_p = np.max(y)
        ip1, = np.where(y >= y_rel_p)

    # точка появления петли
    point1_x = x[ip1[0]]
    point1_y = y[ip1[0]]

    # точка конца петли
    index_x2, = np.where(y == np.max(y))
    k = (0.3 / (-x[index_x2[-1]])) * point1_x + 0.4
    din_koef = -3 * 10 ** (-9) * Eur + k * point1_x ## 0.00095
    point3_x = point1_x + din_koef
    ip3, = np.where(x >= point3_x)
    point3_x = x[ip3[0]]  # задаем последнюю точку в общем массиве кривой девиаторного нагружения
    if point3_x <= point1_x:
        ip3[0] = ip1[0]+1
        point3_x = x[ip3[0]]  # задаем последнюю точку в общем массиве кривой девиаторного нагружения
    point3_y = y[ip3[0]]  # задаем последнюю точку в общем массиве кривой девиаторного нагружения


    d1_p3 = (y[ip3[0] + 1] - y[ip3[0]]) / (x[ip3[0] + 1] - x[ip3[0]])  # производная
    # кривой девиаторного нагружения в точке конца петли
    E0 = (y[1] - y[0]) / (x[1] - x[0])  # производная кривой девиаторного нагружения в 0
    # ограничение на E0 (не больше чем модуль петли разгрузки)
    if E0 < Eur:
        E0 = 1.1 * Eur


    # ограничение на угол наклона участка повтороной нагрузки,
    # чтобы исключить пересечение петли и девиаторной кривой
    min_E0 = point1_y / point1_x  # максимальный угол наклона петли

    if Eur < 1.1 * min_E0:
        #print("\nВНИМАНИЕ: Eur изменен!\n")
        Eur = 1.1 * min_E0
        E0 = 1.1 * Eur

    point2_x = (point2_y - point1_y + Eur * point1_x) / Eur  # вычисляется из оординаты
    # и угла наклона петли
    ip2x, = np.where(x >= point2_x)
    point2_x = x[ip2x[0]]  # ???

    if ip2x[0] >= ip1[0]: # если точка 2 совпадает с точкой один или правее, то меняем точку 2 на предыдущую
        #print("\nВНИМАНИЕ: Eur изменен!\n")
        ip2x[0] = ip1[0] - 1
        point2_x = x[ip2x[0]]

    x1_l = np.linspace(point1_x, point2_x, int(abs(point2_x - point1_x) / (x[1] - x[0]) + 1))  # участок разгрузки
    x2_l = np.linspace(point2_x, point3_x,
                       int(abs(point3_x - point2_x) / (x[1] - x[0]) + 1))  # участок повторной нагрузки

    din_pr = 2 * Eur ## 0.8 * Eur + 60000  # производная в точке начала разгрузки (близка к бесконечности) #???
    spl1 = interpolate.make_interp_spline([point2_x, point1_x],
                                          [point2_y, point1_y], k=3,
                                          bc_type=([(2, 0)], [(1, din_pr)]))
    y1_l = spl1(x1_l)  # участок разгрузки

    crosspoint_y = point1_y * 0.97  # точка пересечения участка разгрузки и повторной нагрузки
    icp, = np.where(crosspoint_y >= y1_l)
    #crosspoint_x = x1_l[icp[0]]  # точка пересечения участка разгрузки и повторной нагрузки

    '''
    spl2 = interpolate.make_interp_spline([point2_x, crosspoint_x, point3_x],
                                          [point2_y, crosspoint_y, point3_y], k=3,
                                          bc_type=([(1, E0)], [(1, d1_p3)]))  # участок повторной нагрузки
    y2_l = spl2(x2_l)
    '''

    b_c = bezier_curve([point2_x - 0.2 * point2_x, E0 * (point2_x - 0.2 * point2_x) + (point2_y - E0 * point2_x)],
                       [point2_x, point2_y],
                       [point3_x, point3_y],
                       [point3_x - 0.1 * point3_x, d1_p3 * (point3_x - 0.1 * point3_x) + (point3_y - d1_p3 * point3_x)],
                       [point2_x, point2_y],
                       [point3_x, point3_y],
                       x2_l)
    y2_l = b_c

    # устраняем повторяющуюся точку 2
    x2_l = x2_l[1:]
    y2_l = y2_l[1:]

    # соединяем  участки разгрузки и нагрузки в петлю
    x_loop = np.hstack((x1_l, x2_l))
    y_loop = np.hstack((y1_l, y2_l))

    return x_loop, y_loop, point1_x, point1_y, point2_x, point2_y, point3_x, point3_y, x1_l, x2_l, y1_l, y2_l

def cos_ocr(x, y,  qf, qocr, xc):
    '''возвращает функцию косинуса
     и параболы для участка x50 qf'''

    index_xocr, = np.where(y > qocr)
    xocr = x[index_xocr[0]]
    proiz_ocr= (y[index_xocr[0]+1]-y[index_xocr[0]])/\
         (x[index_xocr[0]+1]-x[index_xocr[0]])

    count = 0
    while proiz_ocr <= 0 and count < 10:
        proiz_ocr = (y[index_xocr[0] + 1 + count] - y[index_xocr[0]]) / (x[index_xocr[0] + 1 + count] - x[index_xocr[0]])
        count += 1

    # print(f"deviator loading functions : cos_ocr : proiz_ocr = {proiz_ocr}")

    if proiz_ocr < 20000:
        vl_h = 0.3
    elif (proiz_ocr >= 20000) and (proiz_ocr <= 80000):
        kvl = 0.7/ 60000
        bvl = 0.3 - 20000 * kvl
        vl_h = kvl * proiz_ocr + bvl  # 1. / 40000. * e50 - 1. / 8
    elif proiz_ocr > 80000:
        vl_h = 1

    max_y_initial = max(y)

    index_max = np.argmax(y)

    h = 0.2 * qf * vl_h # высота функции

    if h > 0.8 * qocr:
        h = 0.8 * qocr

    sm = xocr

    k = h / (sm) ** 2

    index_2xocr, = np.where(x >= xc)
    index_xocr, = np.where(x >= xocr)

    cos_par = np.hstack((-k * (x[:index_xocr[0]] - sm) ** 2 + h,
                         h * (1 / 2) * (np.cos((1. / (xc - sm)) * np.pi * (x[index_xocr[0]:index_2xocr[0]] + (xc - 2 * sm)) - np.pi) + 1),
                         np.zeros(len(x[index_2xocr[0]:]))))

    # proiz_ocr = [(y[i]+cos_par[i] - y[i+1]-cos_par[i + 1])/ (x[i] - x[i + 1]) for i in range(len(x)-1)]
    # plt.plot(x[:-1], proiz_ocr)

    extremums = argrelextrema(y+cos_par, np.greater)

    y_ocr = y + cos_par

    count = 0
    while ((max(y + cos_par) > max_y_initial) or (
            (extremums[0][0] < index_max) and y_ocr[extremums[0][0]] > 0.9 * max_y_initial)) and count < 200:

        if max(y + cos_par) > max_y_initial:
            xc = xc - 0.0001
            if xc >= sm:
                index_2xocr, = np.where(x >= xc)
                index_xocr, = np.where(x >= xocr)

                cos_par = np.hstack((-k * (x[:index_xocr[0]] - sm) ** 2 + h,
                                     h * (1 / 2) * (np.cos((1. / (xc - sm)) * np.pi * (
                                             x[index_xocr[0]:index_2xocr[0]] + (xc - 2 * sm)) - np.pi) + 1),
                                     np.zeros(len(x[index_2xocr[0]:]))))
        #
        y_ocr = y + cos_par
        delta = 0.01 * h

        if (extremums[0][0] < index_max) and y_ocr[extremums[0][0]] > 0.95 * max_y_initial:
            h = h - delta
            k = h / (sm) ** 2
            index_2xocr, = np.where(x >= xc)
            index_xocr, = np.where(x >= xocr)

            cos_par = np.hstack((-k * (x[:index_xocr[0]] - sm) ** 2 + h,
                                 h * (1 / 2) * (np.cos((1. / (xc - sm)) * np.pi * (
                                         x[index_xocr[0]:index_2xocr[0]] + (xc - 2 * sm)) - np.pi) + 1),
                                 np.zeros(len(x[index_2xocr[0]:]))))
            extremums = argrelextrema(y + cos_par, np.greater)
        #
        y_ocr = y + cos_par
        count = count + 1
        # print(f"cos_ocr : COUNT : {count}")

    return cos_par


def dev_loading(qf, e50, x50, xc, x2, qf2, gaus_or_par, amount_points):
    qocr = 0  # !!!
    '''кусочная функция: на участкe [0,xc]-сумма функций гиперболы и
    (экспоненты или тангенса) и кусочной функции синуса и парболы
    на участке [xc...]-половина функции Гаусса или параболы'''
    if xc < x50:
        xc = x50 * 1.1  # хс не может быть меньше x50
    x = np.linspace(0, 0.6, int((amount_points * 0.6 / 0.15) / 4))
    y = np.linspace(0, 0.6, int((amount_points * 0.6 / 0.15) / 4))
    a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc,
                                                                        qocr)  # считаем  k1, k, xocr на участке до x50, начальное значение kp
    # считаем предельное значение xc
    for i in range(len(x)):
        xcpr = smoothness_condition(qf, x50)

    if (x50 >= xc):  # если x50>xc, xc сдвигается в 0.15, х2,qf2 перестает учитываться,
        # в качестве функции используется сумма гиперболы, экспоненты или тангенса
        # и функции синуса и параболы
        xc = 0.15
        a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
        for i in range(len(x)):
            xcpr = smoothness_condition(qf, x50)
        if xc <= xcpr:  # проверка на условие гладкости, если условие не соблюдается,
            # передвинуть xс в предельное значение
            xc = xcpr
            if (xc>0.11) and (xc<0.15):
                xc=0.15
            a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
        for i in range(len(x)):
            y[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp[i], k, qocr,
                                     xocr) + cos_par(x[i], e50, qf, x50,
                                                     xc)  # формирование функции девиаторного нагружения
        x2 = xc  # x2,qf2 не выводится
        qf2 = qf  # x2,qf2 не выводится

    else:
        a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
        for i in range(len(x)):
            xcpr = smoothness_condition(qf, x50)  # считаем предельно значение xc
        if xc <= xcpr:
            xc = xcpr
            if (xc>0.11) and (xc<0.15):
                xc=0.15
            a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
        if (xc > 0.15):
            a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
            for i in range(len(x)):
                y[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp[i], k, qocr,
                                         xocr) + cos_par(x[i], e50, qf, x50, xc,
                                                         0)  # формирование функции девиаторного нагружения
            x2 = xc  # x2,qf2 не выводится
            qf2 = qf  # x2,qf2 не выводится

        else:
            if xc >= 0.8 * x2:  # минимально допустимое расстояния между хс и х2
                x2 = 1.2 * xc
            if qf2 >= qf:  # минимально допустимое расстояние мужду qf2 и qf
                qf2 = 0.98 * qf

            a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp, k, xocr = params_gip_exp_tg(x, e50, qf, x50, xc, qocr)
            gip_and_exp_or_tg_cos_par = np.linspace(0, 0.6, int((amount_points * 0.6 / 0.15) / 4))
            for i in range(len(x)):
                if x[i] < xc:
                    gip_and_exp_or_tg_cos_par[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t,
                                                                     k1_t,
                                                                     kp[i], k, qocr, xocr) + cos_par(x[i], e50, qf, x50,
                                                                                                     xc,
                                                                                                     0)
                else:
                    gip_and_exp_or_tg_cos_par[i] = 0.

            maximum = max(gip_and_exp_or_tg_cos_par)

            for i in range(len(x)):

                if x[i] <= xc:
                    if maximum < (qf + 0.002 * qf):
                        y[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t,
                                                 kp[i], k, qocr, xocr) + cos_par(x[i], e50, qf, x50, xc, 0)
                    # если максимум суммарной функции на участке от 0 до хс превышает qf, то уменьшаем
                    # высоту функции синуса и параболы на величину разницы в точке xc
                    elif maximum >= abs(qf + 0.002 * qf):
                        y[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t,
                                                 kp[i], k, qocr, xocr) + cos_par(x[i], e50, qf, x50, xc,
                                                                                 abs(maximum - qf + 2 * 0.002 * qf))
                    else:
                        y[i] = gip_and_exp_or_tg(x[i], e50, x50, qf, a1_g, k1_g, a1_e, k1_e, a1_t, k1_t, kp[i], k, qocr,
                                                 xocr)


                elif (x[i] > xc) & (gaus_or_par == 0):
                    y[i] = gaus(x[i], qf, xc, x2, qf2)
                elif (x[i] > xc) & (gaus_or_par == 1):
                    y[i] = parab(x[i], qf, xc, x2, qf2)

    if qocr > (0.8 * qf):  # не выводить точку xocr, qocr
        xocr = xc
        qocr = qf
    xnew = np.linspace(x.min(), x.max(), int(amount_points * 0.6 / 0.15))  # интерполяция  для сглаживания в пике
    spl = make_interp_spline(x, y, k=5)
    y_smooth = spl(xnew)

    xold = xnew  # масиив х без учета петли (для обьемной деформации)

    return xold, xnew, y_smooth, qf, xc, x2, qf2, e50


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


def curve(qf, e50, **kwargs):
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

    if y_rel_p > qf:
        y_rel_p = qf
    if y_rel_p < 20.0:
        y_rel_p = 20.0

    if xc>0.11:
        xc=0.15

    # ограничение на qf2
    if qf2 >= qf:
        qf2 = qf
    x50 = (qf / 2.) / e50

    x_old, x, y, qf, xc, x2, qf2, e50 = dev_loading(qf, e50, x50, xc, x2, qf2, gaus_or_par, amount_points)  # x_old - без участка разгрузки, возвращается для обьемной деформации
    # x - c участком разгрузки или без в зависимости от того передан ли Eur

    if qocr > (0.6 * qf):
        qocr = 0.6 * qf

    cos = cos_ocr(x, y, qf, qocr, xc)

    index_xocr, = np.where(y >= qocr)
    xocr = x[index_xocr[0]]

    y_ocr = y + cos

    index_qf2ocr, = np.where(y_ocr >= qf / 2)

    x_qf2ocr = np.interp(qf / 2, [y_ocr[index_qf2ocr[0] - 1], y_ocr[index_qf2ocr[0]]],
                         [x[index_qf2ocr[0] - 1], x[index_qf2ocr[0]]])

    index_x50, = np.where(x >= x50)

    is_OCR = False
    if cos[index_x50[0]] > 0:
        is_OCR = True
        a = np.interp(x50, [x[index_x50[0] - 1], x[index_x50[0]]], [y_ocr[index_x50[0] - 1], y_ocr[index_x50[0]]])
        delta = abs(a - qf / 2)

        e50_ocr = (qf / 2 - delta) / x50
        x50_ocr = (qf / 2) / e50_ocr
        # index_x50_ocr, = np.where(x >= x50_ocr)
        # x50_ocr = x[index_x50_ocr[0]]

        x_old, x, y_ocr, qf, xc, x2, qf2, e50_ocr = dev_loading(qf, e50_ocr, x50_ocr, xc, x2, qf2, gaus_or_par, amount_points)

        y_ocr = y_ocr + cos

        a = np.interp(x50, [x[index_x50[0] - 1], x[index_x50[0]]], [y_ocr[index_x50[0] - 1], y_ocr[index_x50[0]]])
        n = 0

        while abs((a / x50 - (qf / 2) / x50)) > 50 and n < 30:
            a = np.interp(x50, [x[index_x50[0] - 1], x[index_x50[0]]], [y_ocr[index_x50[0] - 1], y_ocr[index_x50[0]]])

            n = n + 1
            delta_ocr = (a - qf / 2)

            delta = delta + delta_ocr

            e50_ocr = (qf / 2 - delta) / x50
            x50_ocr = (qf / 2) / e50_ocr

            x_old, x, y_ocr, qf, xc, x2, qf2, e50_ocr = dev_loading(qf, e50_ocr, x50_ocr, xc, x2, qf2, gaus_or_par, amount_points)
            #
            y_ocr = y_ocr + cos

    y = copy.deepcopy(y_ocr)

    x_loop, y_loop, point1_x, point1_y, point2_x, point2_y, point3_x, point3_y, x1_l, x2_l, y1_l, y2_l = loop(x,
                                                                                                              y,
                                                                                                              Eur,
                                                                                                              y_rel_p, point2_y)
    index_point1_x, = np.where(x >= point1_x)
    index_point3_x, = np.where(x >= point3_x)
    index_point1_y, = np.where(y >= point1_y)
    index_point3_y, = np.where(y >= point3_y)

    y += deviator_loading_deviation(x, y, xc)

    y = sensor_accuracy(x, y, qf, x50, xc)  # шум на кривой без петли
    y = discrete_array(y, 0.5)  # ступеньки на кривой без петли

    #
    if not Eur and is_OCR:
        y_ocr = copy.deepcopy(y)
        index_qf2ocr, = np.where(y_ocr >= qf / 2)
        x_qf2ocr = np.interp(qf / 2, [y_ocr[index_qf2ocr[0] - 1], y_ocr[index_qf2ocr[0]]],
                             [x[index_qf2ocr[0] - 1], x[index_qf2ocr[0]]])
        delta = x50 / x_qf2ocr

        x = x * delta
        index_x50, = np.where(x >= x50)
        y_qf2ocr = np.interp(x50, [x[index_x50[0] - 1], x[index_x50[0]]], [y_ocr[index_x50[0] - 1], y_ocr[index_x50[0]]])
        k = y_qf2ocr / (qf / 2)
        y_ocr = y_ocr / k
        y = copy.deepcopy(y_ocr)
    #


    y1_l = y1_l + np.random.uniform(-1, 1, len(y1_l))  # шум на петле
    y2_l = y2_l + np.random.uniform(-1, 1, len(y2_l))  # шум на петле
    y1_l = discrete_array(y1_l, 1)  # ступени на петле
    y2_l = discrete_array(y2_l, 1)  # cтупени на петле

    y_loop = np.hstack((y1_l, y2_l))  # петля

    if Eur:
        y = np.hstack((y[:index_point1_x[0]],
                              y_loop, y[index_point3_x[0] + 1:]))  # кривая с петлей
        x = np.hstack((x[:index_point1_x[0]], x_loop, x[index_point3_x[0] + 1:]))  # кривая с петлей

    point1_x_index = index_point1_x[0] + 1  # первая точка петли на самом деле принадлежит исходной кривой
    point2_x_index = index_point1_x[0] + len(y1_l)  # -1 + 1 = 0 т.к. самая нижняя точка петли принадлежит разгрузке
    point3_x_index = index_point1_x[0] + len(x_loop) - 2  # -1 - 1 = -2 т.к. последняя точка петли так же на самом деле принадлежит кривой
    y[0] = 0.


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

    y1_start = spline([x_start[0], 0], [0, y1_bias], x_start, 0, y1_proiz,
                      k=3)  # метрвый ход штока кривой обьемной деформации
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
        e50_U = U / x50
        x_old, x_U, y_U, *__ = dev_loading(U, e50_U, x50,  kwargs.get('xc'), 1.2* kwargs.get('xc'), np.random.uniform(0.3, 0.7)*U,
                                        0, amount_points, 0.8*U, False, 10)
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

    x, y, y1, y2, indexs_loop, a = curve(800, 29710.0, xc=0.15, x2=0.16, qf2=500, qocr=0, m_given=0.35,
                                         amount_points=500, angle_of_dilatacy=6, y_rel_p=596, point2_y=382, Eur=150000)

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
    plt.plot(x, y)
    #with open("C:/Users/Пользователь/Desktop/test_file.txt", "w") as file:
        #for i in range(len(y)):
            #file.write(str(np.round(-x[i], 4)).replace(".", ",") + "\t" + str(np.round(y[i], 4)).replace(".", ",")+ "\n")
    # plt.plot(x, z1, label="Статическая кривая")
    # plt.scatter(x[i], z[i], color = "red")
    # plt.plot(ff, f(ff), linewidth =3, label = "Динамическая кривая")
    plt.legend()
    plt.show()
