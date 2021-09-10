import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib import rcParams
from datetime import datetime, timedelta

rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = '10'
rcParams['axes.edgecolor'] = 'black'
plt.style.use('bmh')

def splitting_test_first(test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test = random.choice(test_times)                  # берем лучайный образец
        test_stab_dict["stab_{}".format(i)].append(random_test)  # закидываем на стабилометр
        test_times.remove(random_test)                           # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while test_times:
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой
        max_time = sum(test_stab_dict["stab_1"])                 # максимальная загрузка по времени

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time = sum(test_stab_dict["stab_{}".format(i)])
                min_time_stab = i
            if sum(test_stab_dict["stab_{}".format(i)]) > max_time:
                max_time = sum(test_stab_dict["stab_{}".format(i)])


        # добавим к наименее загруженному стабилометру опыт, длина которого ближе всего к max_time - min_time
        difference = max_time - min_time
        _temp = list(map(lambda x: abs(x - difference), test_times))
        current_test = test_times[_temp.index(min(_temp))]
        test_stab_dict["stab_{}".format(min_time_stab)].append(current_test)
        test_times.remove(current_test)

    return test_stab_dict

def splitting_test_random(_test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test = random.choice(_test_times)                  # берем лучайный образец
        test_stab_dict["stab_{}".format(i)].append(random_test)  # закидываем на стабилометр
        _test_times.remove(random_test)                           # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while _test_times:
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой
        max_time = sum(test_stab_dict["stab_1"])                 # максимальная загрузка по времени

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time_stab = i

        random_test = random.choice(_test_times)  # берем лучайный образец
        test_stab_dict["stab_{}".format(min_time_stab)].append(random_test)
        _test_times.remove(random_test)


    return test_stab_dict

def splitting_test_gradient_time(test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test = max(test_times)                  # берем лучайный образец
        test_stab_dict["stab_{}".format(i)].append(random_test)  # закидываем на стабилометр
        test_times.remove(random_test)                           # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while test_times:
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time_stab = i

        random_test = max(test_times)  # берем лучайный образец
        test_stab_dict["stab_{}".format(min_time_stab)].append(random_test)
        test_times.remove(random_test)


    return test_stab_dict


def splitting_test_numpy(test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test_i = np.random.choice(range(len(test_times)))   # берем лучайный образец
        test_stab_dict["stab_{}".format(i)].append(test_times[random_test_i])  # закидываем на стабилометр
        test_times = np.delete(test_times, random_test_i)                      # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while len(test_times):
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой
        max_time = sum(test_stab_dict["stab_1"])                 # максимальная загрузка по времени

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time = sum(test_stab_dict["stab_{}".format(i)])
                min_time_stab = i
            if sum(test_stab_dict["stab_{}".format(i)]) > max_time:
                max_time = sum(test_stab_dict["stab_{}".format(i)])


        # добавим к наименее загруженному стабилометру опыт, длина которого ближе всего к max_time - min_time
        current_test_i = np.argmin(abs(test_times - (max_time - min_time)))
        test_stab_dict["stab_{}".format(min_time_stab)].append(test_times[current_test_i])
        test_times = np.delete(test_times, current_test_i)

    return test_stab_dict

def splitting_test_random_numpy(test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test_i = np.random.choice(range(len(test_times)))  # берем лучайный образец
        test_stab_dict["stab_{}".format(i)].append(test_times[random_test_i])  # закидываем на стабилометр
        test_times = np.delete(test_times, random_test_i)  # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while len(test_times):
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time_stab = i

        random_test_i = np.random.choice(range(len(test_times)))               # берем лучайный образец
        test_stab_dict["stab_{}".format(min_time_stab)].append(test_times[random_test_i])  # закидываем на стабилометр
        test_times = np.delete(test_times, random_test_i)  # удаляем опыт из списка


    return test_stab_dict

def splitting_test_gradient_time_numpy(test_times, stab_number):
    """Функция принимает массив из времен опытов и раскидывает их по заданному числу стабилометров"""

    # список стабилометров с оптами
    test_stab_dict = {"stab_{}".format(i): list() for i in range(1, stab_number + 1)}

    # заполняем первую партию
    for i in range(1, stab_number + 1):
        random_test_i = np.argmax(test_times)  # берем самый длинный образец
        test_stab_dict["stab_{}".format(i)].append(test_times[random_test_i])  # закидываем на стабилометр
        test_times = np.delete(test_times, random_test_i)  # удаляем опыт из списка

    # распределяем оставшиеся опыты
    while len(test_times):
        min_time = sum(test_stab_dict["stab_1"])                 # минимальная загрузка по времени
        min_time_stab = 1                                        # номер стабилометра с мин. загрузкой

        # найдем наименее и наиболее загруженный стабилометр
        for i in range(1, stab_number + 1):
            if sum(test_stab_dict["stab_{}".format(i)]) < min_time:
                min_time_stab = i

        random_test_i = np.argmax(test_times)  # берем самый длинный образец
        test_stab_dict["stab_{}".format(min_time_stab)].append(test_times[random_test_i])  # закидываем на стабилометр
        test_times = np.delete(test_times, random_test_i)  # удаляем опыт из списка


    return test_stab_dict



if __name__ == '__main__':

    test_time = np.hstack((np.random.uniform(2, 3, 700), np.random.uniform(20, 30, 700)))              # массив длительностей опытов
    all_time = sum(test_time)
    stab_number = 10                                      # число рабочих стабилометров

    stabs1 = splitting_test_numpy(test_time, stab_number)
    stabs2 = splitting_test_random_numpy(test_time, stab_number)
    stabs3 = splitting_test_gradient_time_numpy(test_time, stab_number)

    stabs1_s = []
    stabs1_s_max = []
    stabs2_s = []
    stabs2_s_max = []
    stabs3_s = []
    stabs3_s_max = []

    for i in range(1, stab_number + 1):
        stabs1_s.append(sum(stabs1["stab_{}".format(i)]))
        stabs2_s.append(sum(stabs2["stab_{}".format(i)]))
        stabs3_s.append(sum(stabs3["stab_{}".format(i)]))

    fig, axes = plt.subplots(3, 1)

    fig.subplots_adjust(right=0.95, top=0.95, bottom=0.05, wspace=0.2, hspace=0.2, left=0.05)

    axes[0].bar(list(stabs1.keys()), [sum(stabs1["stab_{}".format(i)]) for i in range(1, stab_number + 1)])
    axes[0].set_title('Рандом + логика. Общее время на объект: {} часов'.format(round(max(stabs1_s), 2)))

    axes[1].bar(list(stabs2.keys()), [sum(stabs2["stab_{}".format(i)]) for i in range(1, stab_number + 1)])
    axes[1].set_title('Рандом. Общее время на объект: {} часов'.format(round(max(stabs2_s), 2)))

    axes[2].bar(list(stabs3.keys()), [sum(stabs3["stab_{}".format(i)]) for i in range(1, stab_number + 1)])
    axes[2].set_title('Сначала долгие, потом короткие. Общее время на объект: {} часов'.format(round(max(stabs3_s), 2)))

    plt.show()