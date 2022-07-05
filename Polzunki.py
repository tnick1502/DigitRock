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
        result = fsolve(equations_e, (nach_pr_a1_e, nach_pr_k1_e), full_output=1)
        a1_e, k1_e = result[0]

        bad_progress_count = 0 # если в result[2] находится 4 или 5, то вылезает предупреждение с прохой сходимостью
        # мы будем делать 50 итераций чтобы попытаться избавиться от этого предупреждения

        nach_pr_a1_e = 1
        error = equations_e([a1_e, k1_e])
        count = 0
        while (a1_e <= 0) or (k1_e <= 0) or (a1_e == nach_pr_a1_e or k1_e == nach_pr_k1_e) or (
                a1_e * k1_e < 1000) or (
                (abs(error[0]) >= 550 or abs(error[1]) >= 550) and
                count < 50) or (
                result[2] in (4, 5) and bad_progress_count < 50 and qf < 251):  # если начальное приближение a1_e
            # или k1_e равно 1 или произведение коээфициентов (приблизительно равно e50)
            #  меньше 1000, то ищутся другие начальные приближения
            nach_pr_a1_e += 1
            result = fsolve(equations_e, (nach_pr_a1_e, nach_pr_k1_e), full_output=1)
            a1_e, k1_e = result[0]

            if result[2] in (4, 5):
                bad_progress_count += 1

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

    x = np.asarray(x)
    y = np.asarray(y)

    max_y = np.max(y)

    sh = np.random.uniform(-0.4, 0.4, len(x))
    index_qf_half, = np.where(y >= max_y / 2)
    index_qf, = np.where(y >= max_y)

    max_x = np.max(x)

    if xc > max_x:  # если хс последня точка в массиве или дальше
        index_qf, = np.where(x >= max_x)

    y_res = y + sh

    # пропускаем нужные точки
    y_res[index_qf_half[0] - 2] = y[index_qf_half[0] - 2]
    y_res[index_qf_half[0] - 1] = y[index_qf_half[0] - 1]
    y_res[index_qf_half[0] - 0] = y[index_qf_half[0] - 0]
    y_res[index_qf_half[0] + 1] = y[index_qf_half[0] + 1]
    y_res[index_qf_half[0] + 2] = y[index_qf_half[0] + 2]

    y_res[index_qf[0] - 2] = y[index_qf[0] - 2]
    y_res[index_qf[0] - 1] = y[index_qf[0] - 1]
    y_res[index_qf[0] - 0] = y[index_qf[0] - 0]

    try:
        y_res[index_qf[0] + 1] = y[index_qf[0] + 1]
    except IndexError:
        pass
    try:
        y_res[index_qf[0] + 2] = y[index_qf[0] + 2]
    except IndexError:
        pass


    # в районе максимума шум меньше первоначального
    indexes, = np.where(y_res > max_y)
    if len(indexes) > 0:
        for i in indexes:
            y_res[i] = y[i] - np.random.uniform(0.05, 0.025)
    # print(indexes, index_qf_half[0], index_qf[0])

    # y_test = copy.deepcopy(y)
    # for i in range(len(y_test)):  # наложение шума кроме промежутков для характерных точек
    #     if (i < index_qf_half[0] - 2) or ((i > index_qf_half[0] + 2) and ([i] < index_qf[0] - 2)) or (
    #             i > index_qf[0] + 2):
    #         if (y_test[i] + sh[i] < np.max(y_test)):
    #             y_test[i] = y_test[i] + sh[i]
    #         else:
    #             y_test[i] = y_test[i] - np.random.uniform(0.05, 0.025)  # в районе максимума шум меньше первоначального
    #
    # for i in range(len(y_test)):
    #     errr = abs(y_test[i] - y_res[i])
    #     if errr > 0.05:
    #         print(i, errr)

    return y_res



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

    # участок разгрузки
    x1_l = np.linspace(point1_x, point2_x, int(abs(point2_x - point1_x) / (x[1] - x[0]) + 1))
    # участок повторной нагрузки
    x2_l = np.linspace(point2_x, point3_x, int(abs(point3_x - point2_x) / (x[1] - x[0]) + 1))

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

    if len(extremums) < 1 or len(extremums[0]) < 1:
        extremums = [[0]]

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
                                                     xc, 0)  # формирование функции девиаторного нагружения
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
    xocr=0
    qocr=0

    return xold, xnew, y_smooth, qf, xc, x2, qf2, e50, xocr, qocr


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
        kwargs["max_time"]
    except KeyError:
        kwargs["max_time"] = 500

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
    max_time = kwargs.get('max_time')
    Eur = kwargs.get('Eur')
    y_rel_p = kwargs.get('y_rel_p')
    point2_y = kwargs.get('point2_y')
    U = kwargs.get('U')

    if max_time < 50:
        max_time = 50
    if max_time <= 499:
        amount_points = max_time * 20
        amount_points_for_stock = np.random.uniform(1, 3)*20
    elif max_time > 499 and max_time <= 2999:
        amount_points = max_time * 2
        amount_points_for_stock = np.random.uniform(5, 10)*2
    else:
        amount_points = max_time/3
        amount_points_for_stock = np.random.uniform(15, 20)/3
    if Eur:
        amount_points = amount_points*10


    qf_old = qf
    if qf < 150:
        k_low_qf = 250 / qf
        if Eur:
            qf = qf * k_low_qf
            e50 = e50 * k_low_qf
            qf2 = qf2 * k_low_qf
            Eur = Eur * k_low_qf
            # amount_points = amount_points * 6
            y_rel_p = y_rel_p * k_low_qf
            point2_y = point2_y * k_low_qf
        else:
            qf = qf * k_low_qf
            e50 = e50 * k_low_qf
            qf2 = qf2 * k_low_qf


    if y_rel_p > qf:
        y_rel_p = qf
    if y_rel_p < 20.0:
        y_rel_p = 20.0

    if xc>0.111:
        xc=0.15

    # ограничение на qf2
    if qf2 >= qf:
        qf2 = qf
    x50 = (qf / 2.) / e50

    x_old, x, y, qf, xc, x2, qf2, e50, xocr, qocr = dev_loading(qf, e50, x50, xc, x2, qf2, gaus_or_par, amount_points)


    # w_file(x, y)

    return x, y, [[x50, qf / 2], [xocr, qocr], [xc, qf], [x2, qf2]]


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

        self.params = {"qf": 2500, "e50": 27374, "qf2": 560, "xc": 0.07, "xc2": 0.15, "qocr": 0}

        self.createIU()

        x, y, points = curve(self.params["qf"], self.params["e50"], xc=self.params["xc"],
                             x2=self.params["xc2"], qf2=self.params["qf2"], qocr=self.params["qocr"])

        i, = np.where(x > 0.151)

        self.canvas.plot(x[:i[0]]*71, y[:i[0]], self.params, points)

    def createIU(self):
        self.layout = QGridLayout()

        self.qf_slider = QSlider(QtCore.Qt.Horizontal)
        self.qf_slider.setMinimum(100)
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
        self.qf2_slider.setMinimum(100)
        self.qf2_slider.setMaximum(1400)
        self.qf2_slider.setValue(self.params["qf2"])
        self.qf2_slider.setTickInterval(1)
        self.qf2_slider.sliderMoved.connect(self.plot)

        self.qocr_slider = QSlider(QtCore.Qt.Horizontal)
        self.qocr_slider.setMinimum(0)
        self.qocr_slider.setMaximum(16000)
        self.qocr_slider.setValue(self.params["qocr"])
        self.qocr_slider.setTickInterval(1)
        self.qocr_slider.sliderMoved.connect(self.plot)

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

        self.layout.addWidget(QLabel("qocr"), 5, 0)
        self.layout.addWidget(self.qocr_slider, 5, 1)

        self.layout.addWidget(self.canvas, 6, 0, -1, -1)

        self.setLayout(self.layout)

    def plot(self):
        self.get_params()

        # self.qf2_slider.setMaximum(self.params["qf"]*0.99)
        self.qocr_slider.setMaximum(self.params["qf"])
        self.canvas.clear()

        x, y, points = curve(self.params["qf"], self.params["e50"], xc=self.params["xc"],
                             x2=self.params["xc2"], qf2=self.params["qf2"], qocr=self.params["qocr"])

        i, = np.where(x > 0.151)

        self.canvas.plot(x[:i[0]]*71, y[:i[0]], self.params, points)

    def get_params(self):
        self.params["qf"] = float(self.qf_slider.value())
        self.params["e50"] = float(self.e50_slider.value())
        self.params["qf2"] = float(self.qf2_slider.value())
        self.params["xc"] = float(self.xc_slider.value()) / 1000
        self.params["xc2"] = float(self.xc2_slider.value()) / 1000
        self.params["qocr"] = float(self.qocr_slider.value())


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

    def plot(self, x, y, params, points=False):

        self.ax1.plot(x, y)
        self.ax1.plot([], [], color="white", label="$q_f$ = " + str(params["qf"]))
        self.ax1.plot([], [], color="white", label="$E_{50}$ = " + str(params["e50"]))
        self.ax1.plot([], [], color="white", label="$q_f2$ = " + str(params["qf2"]))
        self.ax1.plot([], [], color="white", label="$x_c$ = " + str(params["xc"]))
        self.ax1.plot([], [], color="white", label="$x_c$2 = " + str(params["xc2"]))
        self.ax1.plot([], [], color="white", label="$q_{ocr}$ = " + str(params["qocr"]))

        if points:
            for i in range(len(points)):
                if points[i][0] < 0.151:
                    points[i][0] *= 71
                    self.ax1.scatter(*points[i])


        self.ax1.legend()

        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Now use a palette to switch to dark colors:
    app.setStyle('Fusion')
    ex = App()
    sys.exit(app.exec_())

