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
                                                        points=np.random.uniform(2, 3), borders="zero_diff", one_side=True),
                                 create_deviation_curve(x_time[i_1:i_2], deviation / 5, val=(1, 0.1),
                                                        points=np.random.uniform(2, 3), borders="zero_diff",  one_side=True),
                                 np.zeros(len(x_time[i_2:len(x_time)]))
                                 ))

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
                           Cv:float=3,
                           max_time = np.random.uniform(800, 1200),
                           Ca=-0.001,
                           reverse=True,
                           point_time=0.25,
                           initial_bend_coff=0.,
                           noise=0.0001):
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

    initial_bend = 0#initial_bend_coff*load_stage_strain

    #print(f"initial_bend_coff = {initial_bend_coff}")
    delta = abs(load_stage_strain-initial_bend)
    final_volume_strain += delta

    deviation = abs(np.random.uniform(0.0005, 0.0001)*final_volume_strain)

    t_90_sqrt = math.sqrt((0.848 * 2 * 2) / (4 * Cv))
    t_90_log = np.log10(t_90_sqrt ** 2 )

    # Ограничения
    if max_time < (t_90_sqrt)**2:
        max_time = np.random.uniform(4, 5)*t_90_sqrt**2

    max_time_sqrt = max_time ** 0.5
    max_time_log = np.log10(max_time_sqrt ** 2)

    # Ограничения
    if (load_stage_strain-(final_volume_strain - Ca * max_time_log)) / Ca >= 0:
        print('tut')
        Ca = ((load_stage_strain - final_volume_strain) / (0 - max_time_log))*0.90

    time_line = np.linspace(0.1, max_time_sqrt**2, 10000)
    time_line_sqrt = np.array([t**0.5 for t in time_line])#np.linspace(1, max_time_sqrt, 10000)
    time_line_log = np.log10(time_line_sqrt ** 2)

    # Расчет t_creep_sqrt, volume_strain_creep
    t_creep_log = t_90_log + abs(max_time_log - t_90_log)*np.random.uniform(0.6, 0.7) # 0.4 0.6
    t_creep_sqrt = (10**t_creep_log)**0.5
    volume_strain_creep = Ca*t_creep_log + final_volume_strain - Ca * max_time_log

    # ограничения на деформацию t90
    max_volume_strain_90 = final_volume_strain/max_time_log * t_90_log + (load_stage_strain)# прямая из 0 в максимальное время
    myb = final_volume_strain - Ca * max_time_log
    min_volume_strain = Ca*t_90_log + final_volume_strain - Ca * max_time_log # последний линейный участок

    #volume_strain_90 = abs(max_volume_strain_90-min_volume_strain) * np.random.uniform(0.3, 0.35) + min_volume_strain
    volume_strain_90 = abs(max_volume_strain_90 - min_volume_strain) * np.random.uniform(0.14, 0.15) + min_volume_strain #(0.1, 0.13)
    # volume_strain_90 = max_volume_strain_90

    yP = np.random.uniform(load_stage_strain - 0.3 * abs(volume_strain_90 - load_stage_strain),
                            load_stage_strain - 0.3 * abs(volume_strain_90 - load_stage_strain))

    k1 = (volume_strain_90) / (t_90_sqrt)
    b1 = 0
    k2 = k1 * 1.15
    b2 = 0
    y2 = k2 * (time_line_sqrt) + b2  # прямая для второго участка
    yK = volume_strain_90 + np.random.uniform(0.55 * abs(yP-volume_strain_90), 0.55 * abs(yP-volume_strain_90))
    xP = (yP - b2) / k2
    xK = (yK - b2) / k2



    '''интерполяция первого участка (0, xP)'''
    x_for_part1 = [0, xP]
    y_for_part1 = [0, yP]

    if reverse:
         y_part1 = bezier_curve([0,initial_bend], [xP,initial_bend], [xP,yP], [xK, yK], [0,initial_bend], [xP, yP], time_line_sqrt)
        #y_part1 = spline([0, xP], [-0.2*final_volume_strain, yP], time_line_sqrt, k2/100, k2, k=3)
    else:
        y_part1 = spline(x_for_part1, y_for_part1, time_line_sqrt, -3 * abs(k2), -abs(k2), k=3)

    '''интерполяция третьего участка (xK, t90)'''

    # print(f"xK = {xK}; t_90_sqrt = {t_90_sqrt}")
    # print(f"yK = {yK}; volume_strain_90 = {volume_strain_90}")

    x_for_part3 = [xK, t_90_sqrt]
    y_for_part3 = [yK, volume_strain_90]
    y_part3 = spline(x_for_part3, y_for_part3, time_line_sqrt, -abs(k2), -abs(k2/2), k=3)
    # y_part1 = bezier_curve([xK, yK], [xP, yP], [t_90_sqrt, volume_strain_90], [xK, yK], [0, initial_bend], [xP, yP],
    #                        time_line_sqrt)

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
    pr_xc = (y_0_xc[index_xca_log[0]] - y_0_xc[index_xca_log[0] - 2]) / (
            time_line_log[index_xca_log[0]] - time_line_log[index_xca_log[0] - 2])

    b4 = volume_strain_creep - Ca * t_creep_log
    y4 = Ca * time_line_log + b4

    x_for_part5 = [np.log10(t_90_sqrt ** 2), t_creep_log]
    y_for_part5 = [volume_strain_90, volume_strain_creep]
    y_part5 = spline(x_for_part5, y_for_part5, time_line_log, pr_xc, Ca, k=3)  # интерполяция пятого участка

    y_part5 = bezier_curve([t_90_log, volume_strain_90], [np.log10(xK**2), yK], [t_creep_log, volume_strain_creep], [max_time_log, final_volume_strain],
                           [t_90_log, volume_strain_90], [t_creep_log, volume_strain_creep], time_line_log)

    for i in range(len(time_line_log)):
        if time_line_log[i] < t_90_log:
            volume_strain_line[i] = y_0_xc[i]
        elif (time_line_log[i] >= t_90_log) and (time_line_log[i] <= t_creep_log):
            volume_strain_line[i] = y_part5[i]
        elif time_line_log[i] > t_creep_log:
            volume_strain_line[i] = y4[i]

    '''переход в обычный масштаб с заданным количеством точек по х'''
    #x_time = np.arange(0, round(max_time), point_time)
    x_for_time = np.array([t**2 for t in time_line_sqrt])#time_line_sqrt ** 2
    y_for_time = np.array([strain for strain in volume_strain_line])#volume_strain_line
    #spl = interpolate.make_interp_spline(x_for_time, y_for_time, k=3)
    #y_time = spl(x_time)

    x_time = x_for_time
    y_time = y_for_time

    y_time -= delta

    # plt.plot(np.log(x_time+1), y_time,np.log(x_time+1), y_time-consolidation_deviation(x_time, t_90_sqrt, deviation) )
    # plt.show()
    # print(f"load_stage_strain : {load_stage_strain}; result : {y_time[0]}")
    # print(f"final_volume_strain : {final_volume_strain - delta}; result : {y_time[-1]}")
    # print(f"max_time : {max_time_sqrt**2}; result : {x_time[-1]}")
    # print(f"x_time : {x_time[0]}")
    y_time -= consolidation_deviation(x_time, t_90_sqrt, deviation)
    y_time += np.random.uniform(-noise, noise, len(y_time))
    y_time = discrete_array(y_time, noise*2)
    #return x_time, y_time
    return x_time, y_time, np.array([10**t_90_log, 10**t_creep_log, 10**max_time_log, (xP**2),  (xK**2)]), \
         np.array([volume_strain_90, volume_strain_creep, final_volume_strain, yP, yK])-delta
    # return x_time, y_time, [t_90_sqrt, max_time_sqrt, xP, xK], \
    #        [volume_strain_90,
    #                  final_volume_strain, yP, yK]



def define_final_deformation(p, Eref, m, pref=0.15):
    p_i = 0
    eps = 0
    step = 0.001
    while p_i <= p:
        p_i += step
        E_i = Eref * ((p_i) / (pref)) ** m
        eps = step / E_i + eps
    if eps >= 0.3:
        eps = np.random.uniform(0.3, 0.35)
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
                        print(f"FINALE DEFORMATION = {define_final_deformation(P_TEST[i], Eref_TEST[k], M_TEST[l])}")
                        x1, y1, xp, yp = function_consalidation(define_final_deformation(P_TEST[i], Eref_TEST[k], M_TEST[l]), Cv=Cv_TEST[m], Ca=Ca_TEST[n],
                                                                reverse=True, max_time=1300,
                                                                point_time=0.001)

                        plt.figure(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1)+ str(n + 1))
                        print(str(i + 1) + str(k + 1) + str(l + 1) + str(m + 1)+ str(n + 1))
                        # plt.plot(np.log10(x1+1), y1)
                        plt.plot(x1, y1)
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
def ordering(time_model, strain_model):
    """
                Функция пересечения двух прямых, заданных точками
                :param path: путь до файла
                :param time_model: время возвращаемое функцией консолидации
                :param strain_model: деформация возвращаемая функцией консолидации
                :param pressure: максимальное давление консолидации
                :param report_number: имя файла
                """

    # time_model *= 60
    t0 = np.random.uniform(low=20, high=21)
    hours = math.floor(time_model[-1] / 3600)
    time = [t for t in
                      [0, 15, 30, 60, 2 * 60, 5 * 60, 10 * 60, 20 * 60, 30 * 60] + [h * 3600 for h in
                                                                                    range(1, hours + 1)]]
    time = np.round(np.array(time))
    strain = np.interp(time, time_model, strain_model)
    return time, np.array(strain)

if __name__ == "__main__":

    e = define_final_deformation(0.3, 1, 0.8)
    print('e', e)

    x1, y1, a, b = function_consalidation(e, Cv=0.008, reverse=True, max_time=1300.3552717734859, point_time=0.001,
                                          Ca=-0.002)
    xsqrt = np.array([x**0.5 for x in x1])
    xnormal = np.array([x ** 2 for x in xsqrt])
    # vol_test()
    # x1, y1 = function_consalidation(-0.06113427426476852, Cv=0.1, reverse=True, max_time=500, point_time=0.0025, Ca=-0.01082)

    # time_sqrt = np.linspace(0, x1[-1]  0.5, 50)
    #
    # volume_strain_approximate = pchip_interpolate(x1  0.5, y1, time_sqrt)

    # x, y = ordering(x1, y1)
    # fig = plt.figure(figsize=(10, 10))
    # ax1 = plt.subplot()
    # ax2 = plt.subplot()

    # plt.figure()
    # #
    # # #ax1.scatter(np.array(xp),np.array(yp), color=['yellow', 'green','blue', 'red', 'pink'])
    # # #ax1.plot(time_sqrt, volume_strain_approximate)
    # # # plt.plot(x1**0.5, y1)
    # plt.figure()
    # plt.plot(np.log10(x1+1), y1)
    # plt.scatter(a, b, color=['yellow', 'green','blue', 'red', 'pink'])

    # ax1.legend()
    # save_device2('C:\\Users\\Пользователь', x1, y1, 0.3)

    fig, axes = plt.subplots(2, 1)

    axes[1].plot((x1), y1)
    axes[1].set_xscale("log")
    axes[1].scatter(a, b, color=['yellow', 'green', 'blue', 'red', 'pink'])

    axes[0].plot(xsqrt, y1)
    plt.show()

    for i in range(len(x1)):
        print(f"{x1[i] ** 0.5}\t{y1[i]}".replace(".",","))

'''    e=define_final_deformation(0.3, 1, 0.3)
    x1, y1, a, b= function_consalidation(e, Cv=0.1, reverse=True, max_time=130.3552717734859, point_time=0.001, Ca=-0.1)
    #vol_test()
    #x1, y1 = function_consalidation(-0.06113427426476852, Cv=0.1, reverse=True, max_time=500, point_time=0.0025, Ca=-0.01082)

    # time_sqrt = np.linspace(0, x1[-1] ** 0.5, 50)
    #
    #volume_strain_approximate = pchip_interpolate(x1 ** 0.5, y1, time_sqrt)

    #x, y = ordering(x1, y1)
    #fig = plt.figure(figsize=(10, 10))
    # ax1 = plt.subplot()
    # ax2 = plt.subplot()

    # plt.figure()
    # #
    # # #ax1.scatter(np.array(xp),np.array(yp), color=['yellow', 'green','blue', 'red', 'pink'])
    # # #ax1.plot(time_sqrt, volume_strain_approximate)
    # # # plt.plot(x1**0.5, y1)
    # plt.figure()
    # plt.plot(np.log10(x1+1), y1)
    # plt.scatter(a, b, color=['yellow', 'green','blue', 'red', 'pink'])

    # ax1.legend()
    # save_device2('C:\\Users\\Пользователь', x1, y1, 0.3)


    x1 = np.array([1,2,3,4,5,6,7,8,9,10,11])
    x1 = x1*x1
    y1 = [-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11]

    fig, axes = plt.subplots(2, 1)

    axes[0].plot(x1**0.5, y1)

    axes[1].plot(np.log10(x1+1), y1)
    #axes[1].set_xscale("log")
    #axes[2].plot(x1, y1)
    plt.show()'''