# coding: utf-8

# In[17]:
import os
import sys
import matplotlib.pyplot as plt
import math
from scipy import interpolate


from general.general_functions import *
from static_loading.deviator_loading_functions import bezier_curve

def find_d0(time, strain):
    """Поиск d0 для вторичной консолидации"""
    d0 = strain[0] + (np.interp(0.1, time, strain)-np.interp(0.4, time, strain))
    return d0


def spline(x_for_part, y_for_part, x_for_inter, a, b, k=3):
    '''x_for_part, y_for_part - координаты точек интерполяци;
    a, b - значения производной на концах; k-степень сплайна'''
    spl = interpolate.make_interp_spline(x_for_part, y_for_part, k,
                                         bc_type=([(1, a)], [(1, b)]))
    return spl(x_for_inter)

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

def consolidation_deviation(x_time, xc, deviation):
    """Функция создает массив девиаций для кривой консолидации"""
    i, = np.where(x_time > xc ** 2)
    i_1 = int(i[0] / 2)
    i_2 = i[0]

    deviation_array = np.hstack((create_deviation_curve(x_time[0:i_1], deviation, val=(1, 1),
                                                        points=np.random.uniform(2, 3), borders="zero_diff"),
                                 create_deviation_curve(x_time[i_1:i_2], deviation / 5, val=(1, 0.1),
                                                        points=np.random.uniform(2, 3), borders="zero_diff"),
                                 create_deviation_curve(x_time[i_2:len(x_time)], deviation / 10, val=(1, 0.1),
                                                        points=np.random.uniform(3, 4), borders="zero_diff")))

    return deviation_array

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


def function_consalidation(Cv=3, volume_strain_90=-np.random.uniform(0.14, 0.2),
                           Ca=False, deviation=0.003, reverse=False, point_time=0.25,
                           max_time=False, E=np.random.uniform(20000, 50000), sigma_3=100, approximate=False, h=76):
    '''Создание кривой консолидации
    Входные параметры:  Cv - коэффициент консолидации,
                        deviation - значение для наложения девиаций,
                        Ca - коэффициент вторичной консолидации,
                        point_time - период записи точек по времени в минутах(меньше 0.5),
                        reverse - начальный участок (True - выпуклый),
                        max_time - последняя точка, ограничивающая график по времени(не может быть меньше, чем 3*t90)
                        volume_strain_90 = объемная деформация на 90% консолидации(за вычитом начального смещения)
                        E, sigma_3 - модуль деформации и обжимающее давление консолидации - для расчета объемной
                            деформации на этапе приложения нагрузки'''
    if Ca == "-":
        Ca = np.random.uniform(0.01, 0.001)
    if approximate:
        Cv *= 0.6

    # Проверка заданного времени консолидации. Если его нет, найдем автоматически, с условием выполнения t100
    if not max_time:
        max_time = np.random.uniform(((0.848 * (h/2) * (h/2)) / (4 * Cv)) * 3, (((0.848 * (h/2) * (h/2)) / (4 * Cv))) * 4)
    # else:
    ## Условие выполнения 100% консолидации
    # if max_time < ((0.848 * 38 * 38) / (4 * Cv)) * 2.5:
    # max_time = np.random.uniform(((0.848 * 38 * 38) / (4 * Cv)) * 2.5, (((0.848 * 38 * 38) / (4 * Cv))) * 3)

    # Расчет смещения объемной деформации на этапе приложения нагрузки
    load_stage_strain = -3 * (sigma_3 / E) * np.random.uniform(2, 3)

    xc = math.sqrt((0.848 * ((h/2)/10) * ((h/2)/10)) / (4 * Cv))
    len_x = max_time ** 0.5
    x = np.linspace(0, len_x, 1000)

    yP = -np.random.uniform(0.1 * abs(volume_strain_90), 0.15 * abs(volume_strain_90))
    b1 = np.random.uniform(0.3, 0.5) * yP
    k1 = (volume_strain_90 - b1) / xc
    b2 = b1
    k2 = k1 * 1.15
    y2 = k2 * x + b2  # прямая для второго участка
    yK = volume_strain_90 + np.random.uniform(0.1 * abs(volume_strain_90), 0.15 * abs(volume_strain_90))
    xP = (yP - b2) / k2
    xK = (yK - b2) / k2

    '''интерполяция первого участка (0, xP)'''
    x_for_part1 = [0, xP]
    y_for_part1 = [0, yP]
    if reverse:
        y_part1 = spline(x_for_part1, y_for_part1, x, k2 / 10, k2, k=3)
    else:
        y_part1 = spline(x_for_part1, y_for_part1, x, 3 * k2, k2, k=3)

    '''интерполяция третьего участка (xP, xK)'''
    x_for_part3 = [xK, xc]
    y_for_part3 = [yK, volume_strain_90]
    y_part3 = spline(x_for_part3, y_for_part3, x, k2, k2 / 5, k=3)

    y_0_xc = np.linspace(0, 2 * xc, len(x))
    for i in range(len(x)):
        if x[i] < xP:
            y_0_xc[i] = y_part1[i]
        elif (x[i] >= xP) and (x[i] <= xK):
            y_0_xc[i] = y2[i]
        elif x[i] > xK:
            y_0_xc[i] = y_part3[i]

    '''переход в логарифмический масштаб'''
    x_log = np.log(x ** 2 + 1)
    xc_log = np.log(xc ** 2 + 1)
    y_0_xca = np.linspace(0, len_x, len(x))

    yca = 1.15 * volume_strain_90
    index_xca_log, = np.where(x_log >= xc_log)
    pr_xc = (y_0_xc[index_xca_log[0] - 1] - y_0_xc[index_xca_log[0] - 2]) / (
            x_log[index_xca_log[0] - 1] - x_log[index_xca_log[0] - 2])
    b_straight_from_xc = volume_strain_90 - pr_xc * xc_log
    xca_log =(yca - b_straight_from_xc) / pr_xc
    b4 = yca - Ca * xca_log
    y4 = Ca * x_log + b4
    x_for_part5 = [np.log(xc ** 2 + 1), xca_log]
    y_for_part5 = [volume_strain_90, yca]
    y_part5 = spline(x_for_part5, y_for_part5, x_log, pr_xc, Ca, k=3)  # интерполяция пятого участка

    for i in range(len(x_log)):
        if x_log[i] < xc_log:
            y_0_xca[i] = y_0_xc[i]
        elif (x_log[i] >= xc_log) and (x_log[i] <= xca_log):
            y_0_xca[i] = y_part5[i]
        elif x_log[i] > xca_log:
            y_0_xca[i] = y4[i]

    '''переход в обычный масштаб с заданным количеством точек по х'''
    x_time = np.arange(0, round(max_time), point_time)
    x_for_time = x ** 2
    y_for_time = y_0_xca
    spl = interpolate.make_interp_spline(x_for_time, y_for_time, k=3)
    y_time = spl(x_time)




    if Ca == -0.00001:
        # index_xca_log, = np.where(x_log >= xca_log * 1.2)
        index_xca, = np.where(x_time >= ((np.exp(xca_log) - 1)) * 1.2)
        # x_log = x_log[:index_xca_log[0]]
        # y_0_xca = y_0_xca[:index_xca_log[0]]
        x_time = x_time[:index_xca[0]]
        y_time = y_time[:index_xca[0]]

    y_time += load_stage_strain
    if approximate:
        try:
            if max_time > 4*(((0.848 * ((h/2)/10) * ((h/2)/10)) / (4 * Cv))):
                y_time = -((approximate_sqr_consolidation_more_current(x_time ** 0.5, (-y_time - (-y_time[0]))))) + y_time[0]
            else:
                y_time = -((approximate_sqr_consolidation(x_time ** 0.5, (-y_time - (-y_time[0]))))) + y_time[0]
        except RuntimeError:
            pass


    y_time += consolidation_deviation(x_time, xc, deviation)
    y_time += np.random.uniform(-0.0001, 0.0001, len(y_time))
    y_time = discrete_array(y_time, 0.0001)

    return x_time, y_time

def function_consalidation_without_Cv(Cv=3, volume_strain_90=-np.random.uniform(0.14, 0.2),
                           Ca=False, deviation=0.003, reverse=False, point_time=0.25,
                           max_time=False, h=76, E=np.random.uniform(20000, 50000), sigma_3=100):
    '''Создание кривой консолидации
    Входные параметры:  Cv - коэффициент консолидации,
                        deviation - значение для наложения девиаций,
                        Ca - коэффициент вторичной консолидации,
                        point_time - период записи точек по времени в минутах(меньше 0.5),
                        reverse - начальный участок (True - выпуклый),
                        max_time - последняя точка, ограничивающая график по времени(не может быть меньше, чем 3*t90)
                        volume_strain_90 = объемная деформация на 90% консолидации(за вычитом начального смещения)
                        E, sigma_3 - модуль деформации и обжимающее давление консолидации - для расчета объемной
                            деформации на этапе приложения нагрузки'''
    if Ca =="-":
        Ca = np.random.uniform(0.01, 0.001)
    Cv *= 1.5
    # Проверка заданного времени консолидации. Если его нет, найдем автоматически, с условием выполнения t100
    if not max_time:
        max_time = np.random.uniform(((0.848 * (h/2) * (h/2)) / (4 * Cv)) * 3, (((0.848 * (h/2) * (h/2)) / (4 * Cv))) * 4)
    # else:
    ## Условие выполнения 100% консолидации
    # if max_time < ((0.848 * 38 * 38) / (4 * Cv)) * 2.5:
    # max_time = np.random.uniform(((0.848 * 38 * 38) / (4 * Cv)) * 2.5, (((0.848 * 38 * 38) / (4 * Cv))) * 3)

    # Расчет смещения объемной деформации на этапе приложения нагрузки
    load_stage_strain = -3 * (sigma_3 / E) * np.random.uniform(2, 3)

    max_time = max_time ** 0.5

    xc = math.sqrt((0.848 * ((h/2)/10) * ((h/2)/10)) / (4 * Cv))
    len_x = max_time
    x = np.linspace(0, len_x, 1000)

    yP = -np.random.uniform(0.1 * abs(volume_strain_90), 0.15 * abs(volume_strain_90))
    b1 = np.random.uniform(0.3, 0.5) * yP
    k1 = (volume_strain_90 - b1) / xc
    b2 = b1
    k2 = k1 * 1.15
    y2 = k2 * x + b2  # прямая для второго участка
    yK = volume_strain_90 + np.random.uniform(0.1 * abs(volume_strain_90), 0.15 * abs(volume_strain_90))
    xP = (yP - b2) / k2
    xK = (yK - b2) / k2

    '''интерполяция первого участка (0, xP)'''
    x_for_part1 = [0, xP]
    y_for_part1 = [0, yP]
    if reverse:
        y_part1 = spline(x_for_part1, y_for_part1, x, k2 / 10, k2, k=3)
    else:
        y_part1 = spline(x_for_part1, y_for_part1, x, 3 * k2, k2, k=3)

    # '''интерполяция третьего участка (xP, xK)'''
    # x_for_part3 = [xK, xc]
    # y_for_part3 = [yK, volume_strain_90]
    # y_part3 = spline(x_for_part3, y_for_part3, x, k2, k2 / 5, k=3)

    index_xK, = np.where(x >= xK)
    y_0_xc = np.linspace(0, yK, len(x[:index_xK[0]+1]))
    for i in range(len(x[:index_xK[0]+1])):
        if x[i] < xP:
            y_0_xc[i] = y_part1[i]
        elif (x[i] >= xP) and (x[i] <= xK):
            y_0_xc[i] = y2[i]

    '''переход в логарифмический масштаб'''
    x_log = np.log(x ** 2 + 1)
    xK_log = np.log(xK ** 2 + 1)
    y_0_xca = np.linspace(0, len_x, len(x))

    yca = 1.3 * volume_strain_90
    index_xca_log, = np.where(x_log >= xK_log)
    pr_xc = (y_0_xc[index_xca_log[0] - 1] - y_0_xc[index_xca_log[0] - 2]) / (
            x_log[index_xca_log[0] - 1] - x_log[index_xca_log[0] - 2])
    b_straight_from_xc = volume_strain_90 - pr_xc * xK_log
    xca_log = ((yca - b_straight_from_xc) / pr_xc)*2
    b4 = yca - Ca * xca_log
    y4 = Ca * x_log + b4
    x_for_part5 = [np.log(xK ** 2 + 1), xca_log]
    y_for_part5 = [yK, yca]
    y_part5 = spline(x_for_part5, y_for_part5, x_log, pr_xc, Ca, k=3)  # интерполяция пятого участка

    for i in range(len(x_log)):
        if x_log[i] < xK_log:
            y_0_xca[i] = y_0_xc[i]
        elif (x_log[i] >= xK_log) and (x_log[i] <= xca_log):
            y_0_xca[i] = y_part5[i]
        elif x_log[i] > xca_log:
            y_0_xca[i] = y4[i]

    '''переход в обычный масштаб с заданным количеством точек по х'''
    x_time = (np.linspace(0, len_x ** 2, int(len_x ** 2 / point_time + 1)))
    x_for_time = x ** 2
    y_for_time = y_0_xca
    spl = interpolate.make_interp_spline(x_for_time, y_for_time, k=3)
    y_time = spl(x_time)

    # a1, = np.where(x_time >= xP**2)
    # a2, = np.where(x_time >= xc**2)
    # # if ca:
    #     y_time = y_time + np.hstack((np.zeros(a1[0]+1),create_deviation_curve(x_time[a1[0]+1:a2[0]], 0.001, val=(1, 1), points=10), 0,
    #                                  create_deviation_curve(x_time[a2[0] + 1:], 0.001, val=(1, 1), points=2)))
    # else:
    #     y_time = y_time + np.hstack(
    #         (create_deviation_curve(x_time[:a2[0]], 0.001, val=(1, 1), points=False), np.zeros(len(x_time[a2[0]:]))))

    # """ Зададим девиации
    #     Реализуем 2 варианта.
    #     1 - Предпочтительный по умолчанию. Делим кривую на 4 части
    #     2 - При большом времени. Девиации задаются через характерные точки
    #
    #     Второй вариант реализуется автоматически при большом времени"""
    #
    # if max_time > xc * 3:
    #     deviation_variant = 2
    # else:
    #     deviation_variant = 1
    #
    # if deviation_variant == 1:
    #     # Реализация первого варианта
    #
    #     i_1 = int(len(x_time) / 4)  # Поделим на 4 части нашу кривую
    #     i_2 = i_1 + int(len(x_time) / 4)
    #     i_3 = i_2 + int(len(x_time) / 4)
    #
    #     try:
    #         deviation_array = np.hstack((create_deviation_curve(x_time[0:i_1], deviation, val=(1, 1),
    #                                                             points=np.random.uniform(3, 5), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_1:i_2], deviation / 5, val=(1, 0.1),
    #                                                             points=np.random.uniform(5, 8), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_2:i_3], deviation / 8, val=(1, 0.1),
    #                                                             points=np.random.uniform(3, 4), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_3:len(x_time)], deviation / 10, val=(1, 0.1),
    #                                                             points=np.random.uniform(3, 4), borders="zero_diff")))
    #     except ValueError:
    #         deviation_array = np.hstack((create_deviation_curve(x_time[0:i_1], deviation, val=(1, 1),
    #                                                             points=np.random.uniform(3, 5), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_1:i_2], deviation / 5, val=(1, 0.1),
    #                                                             points=np.random.uniform(3, 4), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_2:i_3], deviation / 8, val=(1, 0.1),
    #                                                             points=np.random.uniform(3, 4), borders="zero_diff"),
    #                                      create_deviation_curve(x_time[i_3:len(x_time)], deviation / 10, val=(1, 0.1),
    #                                                             points=np.random.uniform(3, 4), borders="zero_diff")))
    #
    # elif deviation_variant == 2:
    #     # Реализация второго варианта
    #
    #     i, = np.where(x_time > xc ** 2)
    #     i_1 = int(3 * i[0] / 4)
    #     i_2 = int(len(x_time) - i_1)
    #     deviation_array = np.hstack((create_deviation_curve(x_time[0:i_1], deviation, val=(1, 1),
    #                                                         points=np.random.uniform(3, 5), borders="zero_diff"),
    #                                  create_deviation_curve(x_time[i_1:i_2], deviation / 5, val=(1, 0.1),
    #                                                         points=np.random.uniform(3, 5), borders="zero_diff"),
    #                                  create_deviation_curve(x_time[i_2:len(x_time)], deviation / 10, val=(1, 0.1),
    #                                                         points=np.random.uniform(3, 4), borders="zero_diff")))
    #
    # y_time += deviation_array

    if Ca == -0.00001:
        # index_xca_log, = np.where(x_log >= xca_log * 1.2)
        index_xca, = np.where(x_time >= ((np.exp(xca_log) - 1)) * 1.2)
        # x_log = x_log[:index_xca_log[0]]
        # y_0_xca = y_0_xca[:index_xca_log[0]]
        x_time = x_time[:index_xca[0]]
        y_time = y_time[:index_xca[0]]

    y_time += load_stage_strain

    y_time += consolidation_deviation(x_time, xc, deviation)
    y_time += np.random.uniform(-0.0001, 0.0001, len(y_time))
    y_time = discrete_array(y_time, 0.0001)

    return x_time, y_time#, x_log, y_0_xca, y_0_xc, x

def function_consalidation2(Cv=3, Ca="-",deviation=0.003, point_time=0.25,
                           max_time=False, E=np.random.uniform(20000, 50000), sigma_3=100):
    '''Создание кривой консолидации
    Входные параметры:  Cv - коэффициент консолидации,
                        deviation - значение для наложения девиаций,
                        Ca - коэффициент вторичной консолидации,
                        point_time - период записи точек по времени в минутах(меньше 0.5),
                        max_time - последняя точка, ограничивающая график по времени(не может быть меньше, чем 3*t90)
                        volume_strain_90 = объемная деформация на 90% консолидации(за вычитом начального смещения)
                        E, sigma_3 - модуль деформации и обжимающее давление консолидации - для расчета объемной
                            деформации на этапе приложения нагрузки'''

    if Ca == "-":
        Ca = np.random.uniform(0.01, 0.001)

    # Проверка заданного времени консолидации. Если его нет, найдем автоматически, с условием выполнения t100
    if not max_time:
        max_time = np.random.uniform(((0.848 * 38 * 38) / (4 * Cv)) * 3, (((0.848 * 38 * 38) / (4 * Cv))) * 4)

    # Расчет смещения объемной деформации на этапе приложения нагрузки
    load_stage_strain = -3 * (sigma_3 / E) * np.random.uniform(2, 3)


    x = np.linspace(0, max_time, int(max_time/point_time)+1) # ось времени в обычном масштабе
    x_log = np.log(x+1) # ось времени в логарифмическом масштабе (+1 - соответсвует области определения логарифма)

    time_50=(0.197*3.8*3.8)/(4*Cv) # время 50% консолидации, высчитывается по формуле из ГОСТ 12248
    ln_time_50=np.log(time_50+1) # время 50% консолидации в логарифмическом масштабе
    index_ln_time_50, = np.where(x_log>=ln_time_50) # задаем время 50% консолидации на сетке
    ln_time_50 = x_log[index_ln_time_50[0]] # задаем время 50% консолидации на сетке

    time_100=2*time_50 # время 100% консолидации
    ln_time_100=np.log(time_100+1) # время 100% консолидации в логарифмическом масштабе
    index_ln_time_100, = np.where(x_log>=ln_time_100) # задаем время 100% консолидации на сетке
    ln_time_100 = x_log[index_ln_time_100[0]] # задаем время 100% консолидации на сетке

    vol_def_100= - np.random.uniform(0.3, 0.4) # обьемная деформация при 100% консолидации
    vol_def_50= load_stage_strain+(vol_def_100-load_stage_strain)/2 # обьемная деформация при 50% консолидации
    time_end_one_part=time_100/100 # время конца начального участка (задает первую точку перегиба)
    ln_time_end_one_part=np.log(time_end_one_part+1) # время конца начального участка в логарифмическом масштабе
    index_time_end_one_part, = np.where(x_log>=ln_time_end_one_part) # задаем время конца начального участка на сетке
    ln_time_end_one_part = x_log[index_time_end_one_part[0]] # задаем время конца начального участка на сетке

    vol_def_end_one_part=load_stage_strain+((load_stage_strain-vol_def_50)/(0-ln_time_50))/100*ln_time_end_one_part # обьемная деформация в конце начального участка
    b_ca=vol_def_100-Ca*ln_time_100 # коэффицент смещения первой прямой для безье проходящей через (начальную точку и конец начального участка)
    ln_time_ca=ln_time_100*1.3 # начало участка вторичной консолидации
    vol_def_xca=Ca*ln_time_ca+b_ca # обьемная деформация в начале вторичной консолидации





    x_per_1_2, y_per_1_2 = intersect(0, load_stage_strain, ln_time_end_one_part, vol_def_end_one_part, ln_time_50, vol_def_50,
                             ln_time_100, vol_def_100) # точка пересечния первой и второй прямой (для безье)

    uzel_1 = x_per_1_2 + (ln_time_50 - x_per_1_2) * 0.7 # узел до которого задается первый безье
    index_uzla_1, = np.where(x_log >= uzel_1) # задаем узел до которого задается первый безье на сетке
    uzel_1 = x_log[index_uzla_1[0]] # задаем узел до которого задается первый безье на сетке
    uzel_2=ln_time_50+(ln_time_100-ln_time_50)*0.7 # узел до которого задается второй безье



    y_Bezier_line_2 = bezier_curve([ln_time_50, vol_def_50], [ln_time_100, vol_def_100],  # Первая и вторая точки первой прямой
                                   [ln_time_100, vol_def_100], [ln_time_ca, vol_def_xca],  # Первая и вторая точки второй прямой
                                   [uzel_2, ((vol_def_50-vol_def_100)/(ln_time_50-ln_time_100))*
                                    uzel_2+(vol_def_50-((vol_def_50-vol_def_100)/(ln_time_50-ln_time_100))*ln_time_50)], # Первый узел
                                   [ln_time_ca, vol_def_xca],  # Второй узел
                                   x_log)



    y_Bezier_line_1 = bezier_curve([0, load_stage_strain], [ln_time_end_one_part, vol_def_end_one_part],# Первая и Вторая точки первой прямой
                                   [ln_time_50, vol_def_50], [ln_time_100, vol_def_100],  # Первая и вторая точки второй прямой
                                   [0, load_stage_strain],  # Первый узел
                                   [uzel_1, y_Bezier_line_2[index_uzla_1[0]]],  # Второй узел (задается как точка на первом безье)
                                   x_log[:index_uzla_1[0]])
    y=np.hstack((y_Bezier_line_1, y_Bezier_line_2[index_uzla_1[0]:])) # соединяем два безье

    if Ca == -0.00001: # при таком Cа, обрезаем кривую консолидации раньше на 1.1 времени вторичной консолидации
        index_ln_xca, = np.where(x_log >= 1.1*ln_time_ca)
        index_xca,= np.where(x >= np.exp(1.1*ln_time_ca)+1)
        x_log=x_log[:index_ln_xca[0]+1]
        x = x_log[:index_xca[0] + 1]
        y=y[:index_ln_xca[0]+1]

    #y += consolidation_deviation(x, time_100, deviation)
    y += np.random.uniform(-0.0001, 0.0001, len(y))
    y = discrete_array(y, 0.0001)

    return x, y


def approximate_sqr_consolidation(x, y):

    def func(x, amplitude, slant, pow, a):
        return amplitude * (-np.e ** (-slant * x ** pow) + 1)

    def sumOfSquaredError(parameterTuple):
        warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
        val = func(x, *parameterTuple)
        return np.sum((x - val) ** 2.0)

    def generate_Initial_Parameters():
        # min and max used for bounds
        maxX = np.max(x)
        maxY = np.max(y)

        parameterBounds = []
        parameterBounds.append([0.7*maxY, maxY*10])
        parameterBounds.append([3 / maxX, 300 / maxX])
        parameterBounds.append([0, 3])
        parameterBounds.append([0, 10])

        result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
        return result.x, parameterBounds
    geneticParameters, bounds = generate_Initial_Parameters()
    popt, pcov = curve_fit(func, x, y, geneticParameters, method="dogbox", maxfev=5000)
    amplitude, slant, pow, a = popt
    return func(x, amplitude, slant, pow, a)


def approximate_sqr_consolidation_more_current(x, y):

    def func(x, amplitude, slant, pow, a, b):
        return amplitude * (-np.e ** (-slant * x ** pow) + 1) + a*x**2 + b*x

    def sumOfSquaredError(parameterTuple):
        warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
        val = func(x, *parameterTuple)
        return np.sum((x - val) ** 2.0)

    def generate_Initial_Parameters():
        # min and max used for bounds
        maxX = np.max(x)
        maxY = np.max(y)

        parameterBounds = []
        parameterBounds.append([0.7*maxY, maxY*10])
        parameterBounds.append([3 / maxX, 300 / maxX])
        parameterBounds.append([0, 3])
        parameterBounds.append([-10, 10])
        parameterBounds.append([-10, 10])

        result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
        return result.x
    geneticParameters = generate_Initial_Parameters()

    popt, pcov = curve_fit(func, x, y, geneticParameters, method="dogbox", maxfev=5000)
    amplitude, slant, pow, a, b = popt
    return func(x, amplitude, slant, pow, a, b)


if __name__ == "__main__":
    Cv = 2
    t_test = 5*(((0.848 * 3.8 * 3.8) / (4 * Cv)))

    #print(test_params["Cv"], test_params["Ca"], test_params["E50"], test_params["sigma_3"], test_params["K0"],
          #self._draw_params.max_time, self._draw_params.volume_strain_90)

    1.772
    0.00683413097031166
    28440.0
    186.4
    0.5
    7.7679012557423475
    0.17770291565322646
    x1, y1 = function_consalidation(Cv=2, Ca=-0.01765, point_time=1/120, max_time=706,
                                    volume_strain_90=-0.17770291565322646, E=96000, sigma_3=50)

    #x2, y2 = function_consalidation(Cv=Cv, Ca=-0.01,  point_time=1/2, max_time=t_test,deviation=0.003, approximate=True)
    #x3, y3 = function_consalidation_without_Cv(Cv=Cv, Ca=-0.01, point_time=1,deviation=0.003, max_time=t_test)

    def func(x, amplitude, slant, pow, a, b):
        return amplitude * (-np.e ** (-slant * x ** pow) + 1) + a*x**2 + b*x

    fig = plt.figure(figsize=(10, 10))
    ax1 = plt.subplot()

    #y2 = func(x1, max(-y1-(-y1[0])), 10/max(x1), 1, 0.01, -1)

    ax1.plot(x1, y1, label = "Метод без аппроксимации")
    #ax1.plot(x2**0.5, y2, label = "Метод с аппроксимацией")
    #ax1.plot(x3**0.5, y3, label = "Метод без аппроксимации с меньшец точностью , но красивее")

    ax1.legend()
    #ax1.plot(x_log1, y_0_xca1)
    plt.show()