# coding: utf-8

# In[17]:
import os
import sys
import matplotlib.pyplot as plt
import math
from scipy import interpolate

import numpy as np


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


def function_consalidation(final_volume_strain,
                           Cv=3,
                           max_time = np.random.uniform(800, 1200),
                           Ca=-0.001,
                           reverse=True,
                           point_time=0.25):
    '''
    Создание кривой консолидации
    Входные параметры:  Cv - коэффициент консолидации,
                        max_time - последняя точка, ограничивающая график по времени(не может быть меньше, чем 3*t90)
                        Ca - коэффициент вторичной консолидации,
                        deviation - значение для наложения девиаций,
                        reverse - начальный участок (True - выпуклый),
                        point_time - период записи точек по времени в минутах(меньше 0.5)
                        '''

    # Расчет смещения объемной деформации на этапе приложения нагрузки
    load_stage_strain = final_volume_strain*np.random.uniform(0.1, 0.2)
    final_volume_strain -= load_stage_strain
    deviation = np.random.uniform(0.01, 0.02)*final_volume_strain

    t_90_sqrt = math.sqrt((0.848 * 7.1 * 7.1) / (4 * Cv))
    t_90_log = np.log10(t_90_sqrt ** 2 + 1)

    # Ограничения
    if max_time < (t_90_sqrt)**2:
        max_time = np.random.uniform(4, 5)*t_90_sqrt**2

    max_time_sqrt = max_time ** 0.5
    max_time_log = np.log10(max_time_sqrt ** 2 + 1)

    # Ограничения
    if -(final_volume_strain - Ca * max_time_log) / Ca >= 0:
        print('tut')
        Ca = ((0 - final_volume_strain) / (0 - max_time_log))


    time_line_sqrt = np.linspace(0, max_time_sqrt, 10000)
    time_line_log = np.log10(time_line_sqrt ** 2 + 1)

    # Расчет t_creep_sqrt, volume_strain_creep
    t_creep_log = t_90_log + abs(max_time_log - t_90_log)*np.random.uniform(0.3, 0.35) # 0.4 0.6
    t_creep_sqrt = (10**t_creep_log-1)**0.5
    volume_strain_creep = Ca*t_creep_log + final_volume_strain - Ca * max_time_log

    # ограничения на деформацию t90
    max_volume_strain_90 = final_volume_strain/max_time_log * t_90_log # прямая из 0 в максимальное время
    myb = final_volume_strain - Ca * max_time_log
    min_volume_strain = Ca*t_90_log + final_volume_strain - Ca * max_time_log # последний линейный участок

    #volume_strain_90 = abs(max_volume_strain_90-min_volume_strain) * np.random.uniform(0.3, 0.35) + min_volume_strain
    volume_strain_90 = abs(max_volume_strain_90 - min_volume_strain) * np.random.uniform(0.5, 0.6) + min_volume_strain

    yP = -np.random.uniform(0.20 * abs(volume_strain_90), 0.25 * abs(volume_strain_90))
    k1 = (volume_strain_90) / (t_90_sqrt-1)
    b1 = -k1
    k2 = k1 * 1.15
    b2 = -k2
    y2 = k2 * (time_line_sqrt) + b2  # прямая для второго участка
    yK = volume_strain_90 + np.random.uniform(0.35 * abs(volume_strain_90), 0.40 * abs(volume_strain_90))
    xP = (yP - b2) / k2
    xK = (yK - b2) / k2

    '''интерполяция первого участка (0, xP)'''
    x_for_part1 = [0, xP]
    y_for_part1 = [0, yP]
    if reverse:
        y_part1 = bezier_curve([0,0], [xP,0], [xP,yP], [-b2/k2,0], [0,0], [xP, yP], time_line_sqrt)
    else:
        y_part1 = spline(x_for_part1, y_for_part1, time_line_sqrt, -3 * abs(k2), -abs(k2), k=3)

    '''интерполяция третьего участка (xK, t90)'''
    x_for_part3 = [xK, t_90_sqrt]
    y_for_part3 = [yK, volume_strain_90]
    y_part3 = spline(x_for_part3, y_for_part3, time_line_sqrt, -abs(k2), -abs(k2/2), k=3)

    y_0_xc = np.zeros_like(time_line_sqrt)
    for i in range(len(time_line_sqrt)):
        if time_line_sqrt[i] < xP:
            y_0_xc[i] = y_part1[i]
        elif (time_line_sqrt[i] >= xP) and (time_line_sqrt[i] <= xK):
            y_0_xc[i] = y2[i]
        elif time_line_sqrt[i] > xK:
            y_0_xc[i] = y_part3[i]

    volume_strain_line = np.zeros_like(time_line_sqrt)
    index_xca_log, = np.where(time_line_log >= t_90_log)
    pr_xc = (y_0_xc[index_xca_log[0] - 1] - y_0_xc[index_xca_log[0] - 2]) / (
            time_line_log[index_xca_log[0] - 1] - time_line_log[index_xca_log[0] - 2])

    b4 = volume_strain_creep - Ca * t_creep_log
    y4 = Ca * time_line_log + b4

    x_for_part5 = [np.log10(t_90_sqrt ** 2 + 1), t_creep_log]
    y_for_part5 = [volume_strain_90, volume_strain_creep]
    y_part5 = spline(x_for_part5, y_for_part5, time_line_log, pr_xc, Ca, k=3)  # интерполяция пятого участка

    y_part5 = bezier_curve([t_90_log, volume_strain_90], [np.log10(xK**2 + 1), yK], [t_creep_log, volume_strain_creep], [max_time_log, final_volume_strain],
                           [t_90_log, volume_strain_90], [t_creep_log, volume_strain_creep], time_line_log)

    for i in range(len(time_line_log)):
        if time_line_log[i] < t_90_log:
            volume_strain_line[i] = y_0_xc[i]
        elif (time_line_log[i] >= t_90_log) and (time_line_log[i] <= t_creep_log):
            volume_strain_line[i] = y_part5[i]
        elif time_line_log[i] > t_creep_log:
            volume_strain_line[i] = y4[i]

    '''переход в обычный масштаб с заданным количеством точек по х'''
    x_time = np.arange(0, round(max_time), point_time)
    x_for_time = time_line_sqrt ** 2
    y_for_time = volume_strain_line
    spl = interpolate.make_interp_spline(x_for_time, y_for_time, k=3)
    y_time = spl(x_time)

    x_time = x_for_time
    y_time = y_for_time

    y_time += load_stage_strain

    y_time += consolidation_deviation(x_time, t_90_sqrt, deviation)
    y_time += np.random.uniform(-0.0004, 0.0004, len(y_time))
    y_time = discrete_array(y_time, 0.0008)
    return x_time, y_time
    #return x_time, y_time, np.array([t_90_log, t_creep_log, max_time_log, np.log10(xP**2+1),  np.log10(xK**2+1)]), \
    #      np.array([volume_strain_90  + load_stage_strain, volume_strain_creep  + load_stage_strain, final_volume_strain  + load_stage_strain, yP+ load_stage_strain, yK+ load_stage_strain])
    # return x_time, y_time, [t_90_sqrt, max_time_sqrt, xP, xK], \
    #        [volume_strain_90 + load_stage_strain,
    #                  final_volume_strain + load_stage_strain, yP + load_stage_strain, yK + load_stage_strain]



def define_final_deformation(p, Eref, m, pref=0.15):
    p_i = 0
    eps = 0
    step = 0.001
    while p_i <= p:
        p_i += step
        E_i = Eref * ((p_i) / (pref)) ** m
        eps = step / E_i + eps
    return -eps




def vol_test():
    P_TEST = [0.3, 1.0, 8.0]
    Eref_TEST = [1.0, 10.0, 50.0]
    M_TEST = [0.3, 0.8, 1.0]
    Cv_TEST = [0.001, 0.01, 0.1, 1.0, 1.5]
    Ca_TEST = [-0.0001, -0.01, -0.1, -1.0]


    for i in range(len(P_TEST)):
        for k in range(len(Eref_TEST)):
            for l in range(len(M_TEST)):
                for m in range(len(Cv_TEST)):
                    for n in range(len(Ca_TEST)):
                        x1, y1, xp, yp = function_consalidation(define_final_deformation(P_TEST[i], Eref_TEST[k], M_TEST[l]), Cv=Cv_TEST[m], Ca=Ca_TEST[n],
                                                                reverse=True, max_time=1200,
                                                                point_time=0.001)

                        plt.figure(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1)+ str(n + 1))
                        print(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1)+ str(n + 1))
                        plt.plot(np.log10(x1+1), y1)
                        plt.scatter(xp, yp, color=['yellow', 'green','blue', 'red', 'pink'] )
                        plt.savefig(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1) + str(n + 1) + '.png')


def save_device2(path: str, ts, epss, pressure):

    header1 = "SampleHeight;SampleDiameter;TaskID;TaskName;TaskTypeID;TaskTypeName;AlgorithmID;AlgorithmName;Sample"
    header2 = ';'.join(['20', '71.4', '0', '', '', '', '', 'Компрессионное сжатие', ''])
    header3 = "ID;DateTime;Press;Deformation;StabEnd;Consolidation"

    report_number = "-".join(['ЛАБОРАТОРНЫЙ-НОМЕР', 'НОМЕР-ОБЪЕКТА', 'КК'])

    pressure_array = np.hstack(([0], np.full(len(ts)-1, pressure)))
    stab_end = np.zeros_like(pressure_array)
    stab_end[-1] = 1
    consolidation_array = np.ones_like(stab_end)
    consolidation_array[0] = 0

    with open(path + "\\" + report_number + ".csv", 'w', encoding='utf-8') as f:
        f.write(header1 + '\n')
        f.write(header2 + '\n')
        f.write(header3 + '\n')

        for i in range(len(ts)):
            f.write(';'.join([str(i+1),
                              str(ts[i]),
                              str(pressure_array[i]),
                              str(epss[i]),
                              str(stab_end[i]),
                              str(consolidation_array[i])]) + '\n')

    print("{} saved".format(path))
    return path


def define_loading_pressure(pmax, build_press: float, pit_depth: float, depth: float):
    """Функция рассчета максимального давления"""
    if pmax:
        return pmax
    if build_press:
        if not pit_depth:
            pit_depth = 0
        sigma_max = (2 * (depth - pit_depth) * 10) / 1000 + build_press if (depth - pit_depth) > 0 else (2 * 10 * depth) / 1000
        return sigma_max
    else:
        return np.round((2 * 10 * depth) / 1000, 3)


def round_pmax(sigma, param=5):
    sigma = round(sigma * 1000)
    integer = sigma // 10
    remains = sigma % 10
    if remains == 0:
        return (integer * 10) / 1000
    elif remains <= param:
        return (integer * 10 + param) / 1000
    else:
        return (integer * 10 + 10) / 1000


if __name__ == "__main__":

    # finale = define_final_deformation(0.3, 10, 0.3)
    # print(finale)
    # x1, y1, xp, yp = function_consalidation(finale, Cv=1,reverse=True, max_time=800, point_time=0.001, Ca=-0.001)
    # #x1, y1 = function_consalidation(-0.06113427426476852, Cv=0.1, reverse=True, max_time=500, point_time=0.0025, Ca=-0.01082)
    #
    # time_sqrt = np.linspace(0, x1[-1] ** 0.5, 50)
    #
    # volume_strain_approximate = pchip_interpolate(x1 ** 0.5, y1, time_sqrt)
    #
    #
    # fig = plt.figure(figsize=(10, 10))
    # ax1 = plt.subplot()
    #
    #
    # ax1.scatter(np.array(xp),np.array(yp), color=['yellow', 'green','blue', 'red', 'pink'])
    # #ax1.plot(time_sqrt, volume_strain_approximate)
    # ax1.plot(np.log10(x1+1),y1)
    # ax1.legend()
    # save_device2('C:\\Users\\Пользователь', x1, y1, 0.3)
    #plt.show()
    # vol_test()
    print(define_loading_pressure(None, None, None, 1.5))


