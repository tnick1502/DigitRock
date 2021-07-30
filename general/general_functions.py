import numpy as np
import os
import string
import random
#from numba import njit
from scipy.interpolate import interp1d, splrep, splev, make_interp_spline, BSpline, pchip_interpolate, griddata
from scipy.optimize import curve_fit
import scipy.ndimage as ndimage
from scipy.optimize import differential_evolution
import warnings
import sys
import json
from typing import List, Dict, TypeVar, Generic, Tuple, Union, Optional
import copy
from dataclasses import dataclass
from scipy.optimize import fsolve

Shape = TypeVar("Shape")
DType = TypeVar("DType")

class numpyArray(np.ndarray, Generic[Shape, DType]):
    """
    Use this to type-annotate numpy arrays, e.g.
        image: Array['H,W,3', np.uint8]
        xy_points: Array['N,2', float]
        nd_mask: Array['...', bool]
    """
    pass

class AttrDict:
    def __init__(self, data):
        for n, v in data.items():
            self.__setattr__(n, v)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __setitem__(self, key, value):
        # Возможность добавления атрибута в класс с помощью записи словаря object[key] = value
        self.__setattr__(key, value)

    def __iter__(self):
        return iter(self.__dict__)

    def get_dict(self):
        return self.__dict__

    def get_all_values(self):
        return (getattr(self, i) for i in iter(self.__dict__))

@dataclass
class Point:
    """Класс реализует точку с координатами x, y"""
    x: float
    y: float

    def __iter__(self):
        """Метод реализует поведение класса при передаче в построитель x.scatter(*Point)"""
        return (getattr(self, i) for i in iter(self.__dict__))

    def __eq__(self, other):
        """Метод реализует сравл=нение 2х точек по значениям x и y"""
        if isinstance(other, Point):
            return [getattr(self, i) for i in iter(self.__dict__)] == [getattr(other, i) for i in iter(self.__dict__)]
        else:
            raise TypeError("Wrong other class")

    def __bool__(self):
        """Метод для реализации поведения if Point:. озвращант False если одна из координат не заполнена"""
        return None not in self.__dict__.values()

def point_to_xy(*args) -> List:
    """Функция принимает точки класса Point и разбивает их на массивы x, y"""
    x = []
    y = []
    for arg in args:
        x.append(arg.x)
        y.append(arg.y)
    return [x, y]

# Версии
import json
# Создание файла версий
def create_programm_version_json_file(versions):
    # Актуальные версии программ
    # Запишем их в файл
    with open('Z:/НАУКА/Разработка/Аctual Programs Version.json', 'w') as file:
        json.dump(versions, file)

# Чтении актуальной версии
def verify_programm_version(program_name, program_version):
    # Откроем файл версий
    path = existing(["//192.168.0.1/files/НАУКА/Разработка/Аctual Programs Version.json",
                     "Z:/НАУКА/Разработка/Аctual Programs Version.json"])

    with open(path, 'r') as file:
        json_data = json.load(file)

    # Сравним текущую и актуальную версию
    if json_data[program_name] == program_version: return True
    else: return False

# Создание файла версий
def create_json_file(path, data):
    """Создает файл и записывает в него словарь питон"""
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)

def read_json_file(path):
    """Читает JSON в словарь питон"""
    with open(path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    return json_data



# Основные функции
#@njit
def hyperbole(x, slant, amplitude):  # x-координата, a-наклон,b-верхнее ограничение
    """Функция построения гиперболы
        Входные параметры: x - значение или массив абсцисс
                           slant - угол наклона,
                           amplitude - значение верхней асимптоты"""

    return ((x * slant) / (1 + x * slant / (amplitude + 0.0001)))

#@njit
def exponent(x, amplitude, slant):
    """Функция построения экспоненты
        Входные параметры: x - значение или массив абсцисс,
                           amplitude - значение верхней асимптоты,
                           slant - приведенный угол наклона (пологая - 1...3, резкая - 10...20 )"""

    k = slant/(max(x))
    return amplitude*(-np.e**(-k*x) + 1)

def create_stabil_exponent(x, amplituda, slant, y0=0):
    ''' Функция построение смещенной по оси Y на y0 экспоненты, достигающей точно значения y0+amplituda в последней
    точке.
    К экспоненте прибавляется функция прямой пропорциональности, которая в начале равна нулю, а в последней точке
    приобретает значение, которое необходимо прибавить к экспоненете для достижения точного значения
    Использует функцию exponent(x, amplituda, slant)

    :param x: Одномерный массив от нуля
    :param amplituda: Величина, на которую изменится искомая величина по экспоненте
    :param slant: Приведенный угол наклона экспоненты (пологая - 1...3, резкая - 10...20, прямая - ноль)
    :param y0: Начальное значение искомой величины

    :return: Одномерный нампаевский массив значений изменяющихся по экспоненте от значения y0 на amplituda
    '''
    x = np.array(x)
    if x[0] != 0:
        x -= x[0]

    y = exponent(x, amplituda, slant) + y0
    k_add = (y0 + amplituda - y[-1]) / (x[-1] - x[0])
    y2 = y + k_add * (x - x[0])

    return y2

def current_exponent(x, amplitude, x_95, offset=0):
    """Функция построения экспоненты, которая строится в точку, а не в ассимптоту
        Входные параметры: x - значение или массив абсцисс,
                           amplitude - значение верхней асимптоты,
                           x_95 - значение x, в котором функция достигнет значения 0.95 от ассимптоты
                           offset - значение, добавляемое к ассимптоте. Для моделирования ползучести"""
    if x_95 == 0:
        x_95 = 1
    k = -np.log(0.05) / x_95
    y = amplitude*(-np.e**(-k*x) + 1)

    if offset:
        y_creep = np.log(0.01*x+1)
        y += y_creep * (offset/y_creep[-1])

    y += np.linspace(0, amplitude - y[-1] + offset, len(y))
    return y


def logarithm(x, amplitude, x_85):
    """Функция построения экспоненты
        Входные параметры: x - значение или массив абсцисс,
                           amplitude - значение функции в последней точке,
                           x_95 - значение x, в котором функция достигнет значения 0.85 от ассимптоты"""
    if x_85 > x[-1]:
        x_85 = x[-3]
    elif x_85 <= 0:
        x_85 = 1

    xn = np.linspace(0, 10, len(x))
    k = (x_85*(10/x[-1]) - 10) ** 12 / 12000000
    #k = (x_85*(10/x[-1])-10)**10/300000
    return amplitude*np.log(k * xn + 1) / (np.log(k * xn[-1] + 1))

#@njit
def sigmoida(x, amplitude, x_indent, y_indent, shape):
    """Функция построения сигмоиды
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       x_indent - положение центра по оси x,
                       y_indent - положение центра по оси y,
                       shape - размах отображения по оси x"""

    k = 10 / shape
    return ((amplitude * 2) / (1 + np.e ** (-k * (x - x_indent)))) + (y_indent - amplitude)

def step_sin(x, amplitude, xc, shape):
    """Функция построения сглаженного хевисайда по синусу
    Входные параметры: x - значение или массив абсцисс
                       amplitude - фмплитуда сигмоиды,
                       xc - центр
                       shape - размах отображения по оси x"""
    return amplitude * np.sin(2 * np.pi * (x - xc) * (1 / (shape * 2)))

def create_acute_sine_array(x, k):
    """Функцичя строит синусоиду с возможностью задать острые концы"""

    def acute_sine(x, k):
        return 2 * (np.sin(0.5 * x + 0.25 * np.pi) ** 2) ** k - 1

    sin = acute_sine(x, k)

    i = 0
    while x[i] <= 0.25:
        sin[i] = np.sin(x[i])
        i += 1

    return sin

def mirrow_element(val, ax):
    """Зеркальное отражение элемента относительно оси"""
    return val - 2 * (val - ax)

def create_deviation_curve(x, amplitude, val = (1, 1), points = False, borders = False, one_side = False, low_first_district = False):
    """Возвращает рандомную кривую с размерностью, как x.
    Входные параметры:  :param x: входной массив
                        :param amplitude: размах
                        :param val: значение в первой и последней точке
                        :param points: количество точек изгиба
                        :param borders: условие производной на границах. чтобы было 0 подаем 'zero_diff'
                        :param one_side: делает кривую со значениями больше 0. Подается True, False
                        :param low_first_district: задает начальный участок с меньшими значениями,
                         чтобы не было видно скачка производной. Подается как число начальных участков"""

    def random_value_in_array(x):
        """Возвращает рандомное значение в пределах массива"""
        return np.random.uniform(min(x), max(x))

    def split_amplitude(amplitude, points_of_deviations_count, val, low_first_district):
        """Делает линейную зависимость амплитуды от точки"""
        x = np.linspace(0, points_of_deviations_count - 1, points_of_deviations_count)

        if low_first_district:
            return np.hstack((np.array([amplitude / 10 for _ in range(low_first_district)]), np.array(
                [((i / x[-1]) * (val[1] * amplitude - val[0] * amplitude)) + val[0] * amplitude for i in
                 x[low_first_district:]])))
        else:
            return np.array([((i / x[-1]) * (val[1] * amplitude - val[0] * amplitude)) + val[0] * amplitude for i in x])

    def create_amplitude_array(amplitude, x, val):
        """Делает массив с линейной зависимостью амплитуды от точки"""
        return np.linspace(amplitude*val[0], amplitude*val[1], len(x))

    # Определим количество точек условного перегиба
    if points:
        points_of_deviations_count = int(points)
    else:
        points_of_deviations_count = int(np.random.uniform(5, 10))

    if low_first_district:
        if low_first_district > points - 1:
            low_first_district = points - 1

    def create_deviations_array(amplitude, points_of_deviations_count, val, low_first_district):
        """Делает массив с линейной зависимостью амплитуды от точки"""

        # Определим начение y в каждой точке перегиба
        if one_side:
            y_points_of_deviations_array = np.hstack((0, np.array([np.random.uniform(amp/3, amp) for amp in split_amplitude(amplitude, points_of_deviations_count, val, low_first_district)]), 0))
        else:
            y_points_of_deviations_array = np.hstack((0, np.array(
                [np.random.uniform(-amp, amp) for amp in split_amplitude(amplitude, points_of_deviations_count, val, low_first_district)]), 0))

        # Определим начение x в каждой точке перегиба
        x_points_of_deviations_array = np.hstack((x[0],
                                                  np.array([random_value_in_array(i) for i in np.hsplit(x[:int(points_of_deviations_count*(len(x)//points_of_deviations_count))], points_of_deviations_count)]),
                                                           x[-1]))
        return x_points_of_deviations_array, y_points_of_deviations_array

    x_points_of_deviations_array, y_points_of_deviations_array = create_deviations_array(amplitude, points_of_deviations_count, val, low_first_district)

    # Создадим сплайн
    if borders == "zero_diff":
        iterpolate_curve = make_interp_spline(x_points_of_deviations_array, y_points_of_deviations_array, k=3,
                                              bc_type="clamped")
        deviation_curve = iterpolate_curve(x)

        if one_side:
            while min(deviation_curve)<0:
                x_points_of_deviations_array, y_points_of_deviations_array = \
                    create_deviations_array(amplitude, points_of_deviations_count, val, low_first_district)
                iterpolate_curve = make_interp_spline(x_points_of_deviations_array, y_points_of_deviations_array, k=3,
                                                      bc_type="clamped")
                deviation_curve = iterpolate_curve(x)

    else:
        iterpolate_curve = splrep(x_points_of_deviations_array, y_points_of_deviations_array, k=3)
        deviation_curve = np.array(splev(x, iterpolate_curve, der=0))

        if one_side:
            while min(deviation_curve)<0:
                x_points_of_deviations_array, y_points_of_deviations_array = \
                    create_deviations_array(amplitude, points_of_deviations_count, val, low_first_district)
                iterpolate_curve = splrep(x_points_of_deviations_array, y_points_of_deviations_array, k=3)
                deviation_curve = np.array(splev(x, iterpolate_curve, der=0))

    # Нормируем сплайнн
    if amplitude != 0:
        amplitude_array = create_amplitude_array(amplitude, x, val)
        imax = np.argmax((np.abs(deviation_curve) + min(np.abs(deviation_curve)/1000))/amplitude_array)
        if deviation_curve[imax] != 0 and amplitude_array[imax]!=0:
            deviation_curve /= deviation_curve[imax]/amplitude_array[imax]

    #xvals, yvals = bezier_curve(x, deviation_curve, nTimes=50)

    return deviation_curve

def find_line_area(x, y, d, step, Uslovie = [0.8, 1]):
    '''Для полученных массивов определим границы по углу наклона'''
    def findKoeff(x, y, d, step):
        '''Берем одну точку из общего массива и по 3 с каждой стороны от нее
                   Проводим через этот набор аппроксимирующую кривую и смотрим, сколько точек из общего массива еше попали на заданную дистанцию от кривой'''
        def distanse(x, y, A, B):
            ''' Возвращает расстояние между точнкой и прямой'''
            return (abs(A * x - y + B)) / ((A ** 2 + 1) ** 0.5)

        arrayA = []  # Массив углов наклона
        arrayB = []  # Массив смещений
        arrayPointsCount = []  # Массив колличества точет, аппроксимированных данной кривой

        for i in range(step, len(x) - step):

            xData = np.array(x[i - step: i + step])
            yData = np.array(y[i - step: i + step])

            # Аппроксимация
            p = np.polyfit(xData, yData, 1)
            ya = np.polyval(p, xData)

            A = (ya[-1] - ya[0]) / (xData[-1] - xData[0])
            B = np.polyval(p, 0)

            # Обнуляем количество точек
            points = 0
            iEnd = i

            # Проходим по всем точкам и смотрим дистанцию
            for g in range(len(x)):
                if distanse(x[g], y[g], A, B) < d * distanse(x[i], y[i], A, B):
                    if g <= iEnd + 10:
                        iEnd = g
                        points += 1

            arrayA.append(A)
            arrayB.append(B)
            arrayPointsCount.append(points)


        return np.array(arrayA), np.array(arrayB), np.array(arrayPointsCount)


    A, B, Points = findKoeff(x, y, d, step)
    M1 = []
    A1 = []
    B1 = []

    for i in range(len(A)):
        if abs(A[i]) >= Uslovie[0] * abs(min(A)) and abs(A[i]) <= Uslovie[1] * abs(min(A)):
            M1.append(Points[i])
            A1.append(A[i])
            B1.append(B[i])

    M = np.array(M1)
    i = np.argmax(M)
    A = A1[i]
    B = B1[i]

    return A, B

def find_line_koef(x, y):
    """Функция возвращает коэффициенты аппроксимации прямой A, B"""

    p = np.polyfit(x, y, 1) # Линейная аппроксимация
    ya = np.polyval(p, x)
    A = (ya[-1] - ya[0]) / (x[-1] - x[0])
    B = np.polyval(p, 0)

    return A, B

def line(A, B, x):
    '''фенкция построения линии'''
    return x * A + B

def interpolated_intercept(x, y1, y2):
    """Find the intercept of two curves, given by the same x data"""

    def intercept(point1, point2, point3, point4):


        def line(p1, p2):
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0]*p2[1] - p2[0]*p1[1])
            return A, B, -C



        def intersection(L1, L2):
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]

            x = Dx / D
            y = Dy / D
            return x, y



        L1 = line([point1[0],point1[1]], [point2[0],point2[1]])
        L2 = line([point3[0],point3[1]], [point4[0],point4[1]])



        R = intersection(L1, L2)



        return R



    idx = np.argwhere(np.diff(np.sign(y1 - y2)) != 0)
    xc, yc = intercept((x[idx], y1[idx]),((x[idx+1], y1[idx+1])), ((x[idx], y2[idx])), ((x[idx+1], y2[idx+1])))
    try:
        if len(xc) > 1:
            return xc[-1][-1], yc[-1][-1]
        else:
            return xc[0][0], yc[0][0]
    except IndexError:
        return 0, 0

def discrete_array(array, n_step):
    """Функция делает массив дискретным по заданнаму шагу датчика
    Входные параметры: array - массив данных
    n_step - значение шага"""
    current_val = (array[0]//n_step)*n_step # значение массива с учетом шага в заданной точке
    for i in range(1, len(array)): # перебираем весь массив
        count_step = (array[i]-current_val)//n_step
        array[i] = current_val + count_step*n_step
        current_val = array[i]
    return array

def array_discreate_noise(array, discreate_step, num_format, koef_noise_before=float(1), koef_noise_after=0.01):
    ''' Данная функция преобразует одномерный массив "гладких" данных в данные, которые можно было бы получишь с
            помощью испытательного оборудования:
                1. На плавно изменяющиеся данные накладывает шум, соизмеримый с погрешностью измерения оборудования.
                2. Налкадывает дискретный фильтр, который имитирует получение данных с помощью датчиков, с заданным шагом
                    измерения. Результат - дискретный набор данных с нулями после последней значащей цифры.
                3. Накладываем микрошум на все цифры после последней значащей.
                4. Оставляет только заданное количество цифр после запятой.
            Использует функцию discrete_array(array,discreate_step)

            :param array: Одномерный массив, который подвергается обработке
            :param discreate_step: Шаг измерений датчика для дискретизации массива
            :param num_format: Количество знаков после запятой
            :param koef_noise_before: Коэффициент, указывающий во сколько раз шум, накладываемый ДО дискретизации меньше
                самого шага дискретизации. Данный шум является погрешностью измерений датчика. Как правило соизмерим с шагом
                дискретизации
            :param koef_noise_after: Коэффициент, указывающий во сколько раз шум, накладываемый ПОСЛЕ дискретизации меньше
                самого шага дискретизации. Данный шум нужен только для того, чтобы числа были не ровные. Как правило меньше
                шага дискретизации на порядок
            :return: Список с данными типа float (Одномерный массив) с заданным количеством цифр после запятой
            '''
    # Амплитуда шума, накладываемого ДО дискретизации и соответствующая погрешности измерений
    measurement_error = koef_noise_before * discreate_step

    # Амплитуда микрошума, накладываемого ПОСЛЕ дискретизации
    noise_step = koef_noise_after * discreate_step

    new_array = discrete_array(array + np.random.uniform(-measurement_error, measurement_error, len(array)),
                               discreate_step) + np.random.uniform(-noise_step, noise_step, len(array))
    str_for_format = "{:." + str(num_format) + "f}"
    new_array = [float(str_for_format.format(x)) for x in new_array]
    return new_array

def number_format(x, characters_number = 0, split = "."):
    """Функция возвращает число с заданным количеством знаков после запятой
    :param characters_number: количество знаков после запятой
    :param format: строка или число
    :param split: кразделитель дробной части. точка или запятая"""

    if str(type(x)) in ["<class 'numpy.float64'>", "<class 'numpy.int32'>", "<class 'int'>", "<class 'float'>"]:
        # установим нужный формат
        _format = "{:." + str(characters_number) + "f}"
        x = _format.format(x)

        # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
        if x[0] == "-":
            x = x[1:len(x)]

        if split == ".":
            return x
        elif split == ",":
            return x.replace(".", ",")


    else:
        _format = "{:." + str(characters_number) + "f}"

        if str(type(x)) == "<class 'numpy.ndarray'>":
            x = list(x)

        for i in range(len(x)):
            # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
            x[i] = _format.format(x[i])
            if x[i][0] == "-":
                x[i] = x[i][1:len(x)]

            if split == ".":
                pass
            elif split == ",":
                x[i].replace(".", ",")

        return x

def sec_to_days(time, param = "sec_to_days"):
    """Функция переводит секунты в дни"""
    if param == "sec_to_days":
        days = int(time // (3600 * 24))
        hours = int((time - days*(3600 * 24)) // 3600)
        minutes = int((time - days*(3600 * 24) - hours*3600) // 60)
        seconds = (time - days*(3600 * 24) - hours*3600 - minutes*60)
        return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}
    elif param == "min_to_days":
        days = int(time // (60 * 24))
        hours = int((time - days * (60 * 24)) // 60)
        minutes = int(time - days * (60 * 24) - hours * 60)
        seconds = (time - days * (60 * 24) - hours * 60 - minutes) * 60
        return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}

def line_approximate(x, y):

    def func(x, a, b):
        return a * x + b

    popt, pcov = curve_fit(func, x, y, method="dogbox")

    return popt

def make_increas(x, y):
    """Функция берет список массивов и проверяет первый на возрастание. Если оно не постоянно, то во всех массивах удаляет падающие элементы"""
    flag = True
    while flag:
        flag = False
        i_del = []
        for i in range(len(x) - 1):
            if x[i + 1] <= x[i]:
                i_del.append(i + 1)
                flag = True
        if flag:
            x = np.delete(x, i_del)
            y = np.delete(y, i_del)
    return [x, y]


def create_path(path):
    """Проверяет наличие директории, если ее нет, то создает"""
    if os.path.isdir(path):
        pass
    else:
        os.mkdir(path)

def match_keys_in_dict(dict_1, dict_2):
    """Удавляет из первого словаря ключи, которых нет во втором"""
    key1 = [i for i in dict_1]
    key2 = [j for j in dict_2]

    for i in key1:
        if i not in key2:
            dict_1.pop(i)
    return dict_1, dict_2


def get_all_files_hz(rootdir, mindepth = 1, maxdepth = float('inf')):
    """
    Usage:

    d = get_all_files(rootdir, mindepth = 1, maxdepth = 2)

    This returns a list of all files of a directory, including all files in
    subdirectories. Full paths are returned.

    WARNING: this may create a very large list if many files exists in the
    directory and subdirectories. Make sure you set the maxdepth appropriately.

    rootdir  = existing directory to start
    mindepth = int: the level to start, 1 is start at root dir, 2 is start
               at the sub direcories of the root dir, and-so-on-so-forth.
    maxdepth = int: the level which to report to. Example, if you only want
               in the files of the sub directories of the root dir,
               set mindepth = 2 and maxdepth = 2. If you only want the files
               of the root dir itself, set mindepth = 1 and maxdepth = 1
    """
    rootdir = os.path.normcase(rootdir)
    file_paths = []
    root_depth = rootdir.rstrip(os.path.sep).count(os.path.sep) - 1
    for dirpath, dirs, files in os.walk(rootdir):
        depth = dirpath.count(os.path.sep) - root_depth
        if mindepth <= depth <= maxdepth:
            for filename in files:
                if (filename .endswith(".xls") or filename .endswith(".xlsx")) and "мех" in filename:
                    file_paths.append(os.path.join(dirpath, filename))
        elif depth > maxdepth:
            del dirs[:]
    return file_paths

def get_all_files(rootdir, sec_after_mod = 86400):
    import time
    #rootdir = os.path.normcase(rootdir)
    file_paths = []
    for dirpath, dirs, files in os.walk(rootdir):
        for filename in files:
            if (filename.endswith(".xls") or filename.endswith(".xlsx")) and "мех" in filename and ((time.time() - os.path.getmtime(os.path.join(dirpath, filename))) < sec_after_mod):
                print(filename)
                file_paths.append(os.path.join(dirpath, filename))
    return file_paths

def get_all_files(dir):
    file_paths = []
    for dirpath, dirs, files in os.walk(dir):
        for filename in files:
            file_paths.append(os.path.join(dirpath, filename))
    return file_paths


# Общие
def define_type_ground(data_gran, Ip, Ir):
    """Функция определения типа грунта через грансостав"""

    def f_zero(a):
        return 0 if a == '-' else a

    gran_struct = ['10', '5', '2', '1', '05', '025', '01', '005', '001', '0002', '0000']  # гран состав
    accumulate_gran = [f_zero(data_gran[gran_struct[0]])]  # Накоплено процентное содержание
    for i in range(10):
        accumulate_gran.append(accumulate_gran[i] + f_zero(data_gran[gran_struct[i + 1]]))

    if f_zero(Ir) >= 50:  # содержание органического вещества Iom=hg10=Ir
        type_ground = 9  # Торф
    elif f_zero(Ip) < 1:  # число пластичности
        if accumulate_gran[2] > 25:
            type_ground = 1  # Песок гравелистый
        elif accumulate_gran[4] > 50:
            type_ground = 2  # Песок крупный
        elif accumulate_gran[5] > 50:
            type_ground = 3  # Песок средней крупности
        elif accumulate_gran[6] >= 75:
            type_ground = 4  # Песок мелкий
        else:
            type_ground = 5  # Песок пылеватый
    elif 1 <= Ip < 7:
        type_ground = 6  # Супесь
    elif 7 <= Ip < 17:
        type_ground = 7  # Суглинок
    else:  # data['Ip'] >= 17:
        type_ground = 8  # Глина
    if data_gran["Ir"] != "-" and data_gran["Ir"] >= 10:
        type_ground = 9

    return type_ground
# Refactor
def define_kf(physical_data: Dict) -> float:
    """ Определение коэффициента фильтрации по грансоставу
        :param data: словарь с физическими параметрами
        :return: kf в метрах/сутки"""

    try:
        e = float(physical_data["e"])
    except ValueError:
        e = np.random.uniform(0.5, 0.8)

    # Функция сигмоиды для kf
    kf_sigmoida = lambda e, e_min, e_max, k_min, k_max: sigmoida(e, amplitude=(k_max - k_min) / 2,
                                                                 x_indent=e_min + (e_max - e_min) / 2,
                                                                 y_indent=k_min + (k_max - k_min) / 2,
                                                                 shape=e_max - e_min)
    # Общие параметры сигмоиды
    e_borders = [0.3, 1.2]

    # Зависимость коэффициента фильтрации от грансостава
    dependence_kf_on_type_ground = {
        1: kf_sigmoida(e, *e_borders, 8.64, 86.4),
        2: kf_sigmoida(e, *e_borders, 8.64, 86.4),
        3: kf_sigmoida(e, *e_borders, 0.864, 86.4),
        4: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-2), 0.864),
        5: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-2), 0.864),
        6: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-4), 8.64 * 10 ** (-2)),
        7: kf_sigmoida(e, *e_borders, 8.64 * 10 ** (-5), 8.64 * 10 ** (-4)),
        8: kf_sigmoida(e, *e_borders, 0.0000001, 8.64 * 10 ** (-5))
    }

    return dependence_kf_on_type_ground[define_type_ground(physical_data, physical_data["Ip"], physical_data["Ir"])]
# Refactor
def define_Cv(physical_data: Dict, m: float = 0.6) -> float:
    """ Определение коэффициента первичной консолидации Сv в см^2/мин
        :param physical_data: словарь с физическими параметрами
        :param m: коэффициент относительной сжимаемости
        :return: Cv в см^2/мин"""

    kf = define_kf(physical_data)

    # Переведем м/сут в см/мин
    kf *= 0.0694444

    # Переведем 1/МПа в 1 / (кгс / см2)
    m /= 10.197162

    # Удельный вес воды в кгс/см3
    gamma = 0.001

    Cv = kf / (m * gamma)

    if Cv > 1.2:
        return np.round(np.random.uniform(0.7, 1.2), 4)
    elif Cv <= 0.02:
        return np.round(np.random.uniform(0.01, 0.02), 4)
    return np.round(Cv, 4)

# Refactor
def unique_number(length: int = 5, prefix: str = None, postfix: str = None, digits: bool = True, upper: bool = True) -> str:
    """Функция создает уникальный шифр
    :argument
        :param length- длина генерируемой части (default 5)
        :param prefix - префикс к генерируемой последовательности (default None)
        :param postfix - постфикс к генерируемой последовательности (default None)
        :param digits - включает/ выключает наличие цифр (default True)
        :param upper - сделать все буквы заглавными/строчными(default True)
    :return -> str
    """
    charters = string.ascii_letters + string.digits if digits else string.ascii_letters
    random_array = random.choices(charters, k=length)
    unique_number = ''.join(str(i) for i in random_array)

    unique_number = prefix + unique_number if prefix else unique_number
    unique_number = unique_number + postfix if postfix else unique_number

    return unique_number.upper() if upper else unique_number.lower()

# Девиатор
def xc_from_qf_E(qf, E50):
    """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50"""

    # Проверим входные данные на ошибки
    try:
        k = E50 / qf
    except (ValueError, ZeroDivisionError):
        return 0.15

    # Если все норм, то находим Xc
    xc = 1.37 / (k ** (0.8))

    # Проверим значение
    if xc >= 0.15:
        xc = 0.15
    elif xc <= qf / E50:
        xc = qf / E50
    elif xc <= 0.025:
        xc = np.random.uniform(0.025, 0.03)

    return xc

def residual_strength_param_from_xc(xc):
    """Функция находит параметр падения остатичной прочности в зависимости от пика"""

    param = 0.33 - 1.9 * (0.15 - xc)

    return param

def define_k_q(il, e0, sigma3):
    """ Функция определяет насколько выраженный пик на диаграмме
    :param il: показатель текучести
    :param e0: пористость
    :param sigma3: обжимающее напряжение в кПа
    :return: отношение qr к qf
    """
    # Параметры, определяющие распределения
    # Для песков:

    if e0 == "-":
        e0 = np.random.uniform(0.5, 0.7)

    sand_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
    sand_sigma3_max = 1000
    sand_k_e0_min = 0  # значения понижающего коэффициента показателя пористости e0 соответвующее минимальному s3
    sand_k_e0_max = 0.15  # соответствующее макисмальному s3

    sand_e0_red_min = 0.4  # размах приведенной пористости для сигмоиды
    sand_e0_red_max = 0.8
    sand_k_q_min = 0.5  # значения k_q соотв. минимальному e0приведенн
    sand_k_q_max = 0.8  # значения k_q соотв. максимальному e0приведенн

    # Для глин:
    clay_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
    clay_sigma3_max = 1000
    clay_k_il_min = 0  # значения понижающего коэффициента показателя текучести IL соответвующее минимальному s3
    clay_k_il_max = 0.3  # соответствующее макисмальному s3

    clay_il_red_min = 0  # размах приведенного показателя текучести для сигмоиды
    clay_il_red_max = 1
    clay_k_q_min = 0.6  # значения k_q соотв. минимальному ILприведенн
    clay_k_q_max = 0.95  # значения k_q соотв. максимальному ILприведенн

    if il == 0 or il == '-':  # Пески

        # Заивсимость k_e0 от sigma3
        sand_s3_0 = (sand_sigma3_max + sand_sigma3_min) / 2  # x_0
        sand_shape_s3 = sand_sigma3_max - sand_sigma3_min  # delta x

        k_e0_0 = (sand_k_e0_max + sand_k_e0_min) / 2  # y_0
        amplitude_k_e0 = (sand_k_e0_max - sand_k_e0_min) / 2  # amplitude y

        k_e0 = sigmoida(sigma3, amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3)
        e0_red = e0 - k_e0

        # plot_sigmoida(amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3,
        # sand_sigma3_min, sand_sigma3_max, sigma3, k_e0, 'K_e0 от sigma3')

        # Заивсимость k_q от e0приведенной
        e0_red_0 = (sand_e0_red_max + sand_e0_red_min) / 2  # x0
        shape_e0_red = sand_e0_red_max - sand_e0_red_min

        k_q_0 = (sand_k_q_max + sand_k_q_min) / 2  # y0
        amplitude_k_q = (sand_k_q_max - sand_k_q_min) / 2

        k_q = sigmoida(e0_red, amplitude_k_q, e0_red_0, k_q_0, shape_e0_red)

        # plot_sigmoida(amplitude_k_q, e0_red_0, k_q_0, shape_e0_red,
        # sand_e0_red_min, sand_e0_red_max, e0_red, k_q, 'K_q от e0привед')

    else:  # Глины
        # Заивсимость k_il от sigma3
        clay_s3_0 = (clay_sigma3_max + clay_sigma3_min) / 2  # x_0
        clay_shape_s3 = clay_sigma3_max - clay_sigma3_min  # delta x

        k_il_0 = (clay_k_il_max + clay_k_il_min) / 2  # y_0
        amplitude_k_il = (clay_k_il_max - clay_k_il_min) / 2  # amplitude y

        k_il = sigmoida(sigma3, amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3)
        il_red = il - k_il

        # plot_sigmoida(amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3,
        # clay_sigma3_min, clay_sigma3_max, sigma3, k_il, 'K_IL от sigma3')

        # Заивсимость k_q от IL приведенной
        il_red_0 = (clay_il_red_max + clay_il_red_min) / 2  # x0
        shape_il_red = clay_il_red_max - clay_il_red_min

        k_q_0 = (clay_k_q_max + clay_k_q_min) / 2  # y0
        amplitude_k_q = (clay_k_q_max - clay_k_q_min) / 2

        k_q = sigmoida(il_red, amplitude_k_q, il_red_0, k_q_0, shape_il_red)

        # plot_sigmoida(amplitude_k_q, il_red_0, k_q_0, shape_il_red,
        # clay_il_red_min, clay_il_red_max, il_red, k_q, 'K_IL от sigma3')

    return k_q

def define_xc_qf_E(qf, E50):
    try:
        k = E50/ qf
    except (ValueError, ZeroDivisionError):
        return 0.15

    # Если все норм, то находим Xc
    xc = 1.37 / (k ** 0.8)
    # Проверим значение
    if xc >= 0.15:
        xc = 0.15
    elif xc <= qf / E50:
        xc = qf / E50
    return xc

def xc_from_qf_e_if_is(data, sigma3mor, qf_, e50_):
    """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50, если по параметрам материала
    пик есть, если нет, возвращает xc = 0.15. Обжимающее напряжение должно быть в кПа"""

    def f_zero(a):
        return 0 if a == '-' else a

    gran_struct = ['10', '5', '2', '1', '05', '025', '01', '005', '001', '0002', '0000']  # гран состав
    accumulate_gran = [f_zero(data[gran_struct[0]])]  # Накоплено процентное содержание
    for i in range(10):
        accumulate_gran.append(accumulate_gran[i] + f_zero(data[gran_struct[i + 1]]))

    # Определяем тип грунта
    type_ground = define_type_ground(data, data["Ip"], data["Ir"])


    # определяем степень плотности песка (если type_ground = 1...5)
    e0 = f_zero(data['e'])  # пористость
    if e0 == 0:
        dens_sand = 2  # средней плотности
    elif type_ground <= 3:
        if e0 <= 0.55:
            dens_sand = 1  # плотный
        elif e0 <= 0.7:
            dens_sand = 2  # средней плотности
        else:  # e0 > 0.7
            dens_sand = 3  # рыхлый
    elif type_ground == 4:
        if e0 <= 0.6:
            dens_sand = 1  # плотный
        elif e0 <= 0.75:
            dens_sand = 2  # средней плотности
        else:  # e0 > 0.75
            dens_sand = 3  # рыхлый
    elif type_ground == 5:
        if e0 <= 0.6:
            dens_sand = 1  # плотный
        elif e0 <= 0.8:
            dens_sand = 2  # средней плотности
        else:  # e0 > 0.8
            dens_sand = 3  # рыхлый
    else:
        dens_sand = 0

    sigma3mor = sigma3mor / 1000  # так как дается в КПа, а необходимо в МПа
    if accumulate_gran[1] > 50:  # Процентное содержание гранул размером 10 и 5 мм больше половины
        kr_fgs = 1
    elif f_zero(data['Ip']) == 0:  # число пластичности. Пески (и торф?)
        if dens_sand == 1 or type_ground == 1:  # любой плотный или гравелистый песок
            kr_fgs = 1
        elif type_ground == 2:  # крупный песок
            if sigma3mor <= 0.1:
                kr_fgs = round(np.random.uniform(0, 1))
            else:
                kr_fgs = 1
        elif type_ground == 3:  # песок средней групности
            if sigma3mor <= 0.15 and dens_sand == 3:  # песок средней крупности рыхлый
                kr_fgs = 0
            elif sigma3mor <= 0.15 and dens_sand == 2:  # песок средней крупности средней плотности
                kr_fgs = round(np.random.uniform(0, 1))
            else:  # песок средней групности и sigma3>0.15
                kr_fgs = 1
        elif type_ground == 4:  # мелкий песок
            if sigma3mor < 0.1 and dens_sand == 3:  # мелкий песок рыхлый s3<0.1
                kr_fgs = 0
            elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (sigma3mor <= 0.15 and dens_sand == 2):
                kr_fgs = round(np.random.uniform(0, 1))  # мелкий песок рыхлый s3<=0.2 и средней плотности s3<=0.15
            else:  # мелкий песок рыхлый s3>=0.2 и средней плотности s3>=0.15 (плотный закрыт раньше)
                kr_fgs = 1
        elif type_ground == 5:  # песок пылеватый
            if sigma3mor < 0.1 and dens_sand == 3:  # песок пылеватый рыхлый s3<0.1
                kr_fgs = 0
            elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (sigma3mor <= 0.1 and dens_sand == 2):  # песок пылева-
                kr_fgs = round(np.random.uniform(0, 1))  # тый рыхлый 0.1<=s3<=0.2 и пылеватый средней плотности s3<=0.1
            else:  # песок пылеватый рыхлый s3>0.2 и пылеватый средней плотности s3>0.1 (плотный закрыт раньше)
                kr_fgs = 1
        elif type_ground == 9:  # Торф
            kr_fgs = 0
        else:
            kr_fgs = 0

    elif data['Ip'] <= 7:  # число пластичности. Супесь

        if f_zero(data['Il']) > 1:  # показатель текучести. больше 1 - текучий
            kr_fgs = 0
        elif 0 < f_zero(data['Il']) <= 1:  # показатель текучести. от 0 до 1 - пластичный (для супеси)
            kr_fgs = round(np.random.uniform(0, 1))
        else:  # <=0 твердый
            kr_fgs = 1

    elif data['Ip'] > 7:  # суглинок и глина
        if f_zero(
                data['Il']) > 0.5:  # показатель текучести.от 0.5 мягко- и текучепласт., текучий (для суглинков и глины)
            kr_fgs = 0
        elif 0.25 < f_zero(data['Il']) <= 0.5:  # от 0.25 до 0.5 тугопластичный (для суглинков и глины)
            kr_fgs = round(np.random.uniform(0, 1))
        else:  # меньше 0.25 твердый и полутвердый (для суглинков и глины)
            kr_fgs = 1
    else:
        kr_fgs = 0

    return kr_fgs

def mohr_circles(sigma3, sigma1):
    """Построение кругов мора. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""

    def Round(x, a, b):
        val = np.full(len(x), 0.)
        for i in range(len(x)):
            val[i] = ((((b - a) ** 2) / 4) - ((((2 * x[i]) - b - a) ** 2) / 4))
            if val[i] < 0.:
                val[i] = 0.
        return val ** 0.5

    kol = len(sigma3)

    X = np.zeros(shape=(kol, 1000))
    Y = np.zeros(shape=(kol, 1000))
    for i in range(kol):
        X[i] = np.linspace(sigma3[i], sigma1[i], 1000)
        Y[i] = Round(X[i], sigma3[i], sigma1[i])

    return X, Y

def mohr_cf(sigma3, sigma1, stab=False):
    """Расчет c и f. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""

    if stab == False:
        sig = list(map(lambda x, y: (x + y) / 2, sigma1, sigma3))
        t = list(map(lambda x, y: (x - y) / 2, sigma1, sigma3))
    else:
        sig = sigma3
        t = sigma1


    sigSum = sum(sig)
    tSum = sum(t)

    sigtSum = sum(list(map(lambda x, y: x * y, sig, t)))
    sigSqr = sum([v * v for v in sig])
    n = len(sigma3)
    if n == 1:
        fi = t[0] / sig[0]
        c = 0
    else:
        fi = (n * sigtSum - tSum * sigSum) / (n * sigSqr - sigSum * sigSum)
        c = (tSum * sigSqr - sigSum * sigtSum) / (n * sigSqr - sigSum * sigSum)

    return c, fi

def mohr_cf_stab(sigma3, sigma1):
    """Расчет c и f. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""

    c, fi = mohr_cf(sigma3, sigma1, True)
    cS = c / (2 * (fi ** 0.5))
    phiS = ((fi - 1) / (2 * (fi ** 0.5)))

    return cS, phiS

def define_qf(sigma_3, c, fi):
    """Функция определяет qf через обжимающее давление и c fi"""
    fi = fi * np.pi / 180
    return round((2 * (c * 1000 + (np.tan(fi)) * sigma_3)) / (np.cos(fi) - np.tan(fi) + np.sin(fi) * np.tan(fi)), 7)

def define_sigma_3(K0, z):
    """Функция определяет обжимающее давление"""
    return round(K0 * (2 * 9.81 * z), 1)

def define_E50(E50ref, c, fi, sigma_3, p_ref, m, deviation=0.1):
    """Расчет E50 через параметр умрочнения"""
    fi = np.deg2rad(fi)
    up = c*np.cos(fi)+sigma_3*np.sin(fi)
    down = c*np.cos(fi)+p_ref*np.sin(fi)
    E50 = (E50ref*(up/down)**m) * np.random.uniform(1 - deviation, 1 + deviation)
    return E50

def define_poissons_ratio(Rc, Ip, Il, Ir, size_10, size_5, size_2):

    round_ratio = 2 # число знаков после запятой

    def check_size(size):
        """Проверка заполненности размеров"""
        if size == "-":
            return 0
        else:
            return size

    # Скала
    if Rc != "-":
        if (Rc > 0) and (Rc <= 50):
            return round(np.random.uniform(0.22, 0.28), round_ratio)
        elif (Rc > 50) and (Rc <= 150):
            return round(np.random.uniform(0.18, 0.25), round_ratio)
        elif (Rc > 150):
            return round(np.random.uniform(0.18, 0.25), round_ratio)

    # Крупнообломочный
    if (check_size(size_10)+check_size(size_5)+check_size(size_2)) > 50:
        return round(np.random.uniform(0.18, 0.27), round_ratio)

    # Торф
    if (Ir != "-") and (Ir >= 50):
        return round(np.random.uniform(0.35, 0.4), round_ratio)

    # Пески
    if Ip == "-":
        return round(np.random.uniform(0.25, 0.35), round_ratio)


    # Глины, суглинки
    if Ip != "-":

        if Il == "-": # проверка на заполненность
            Il = 0.5

        if Ip >= 17:
            if Il <= 0:
                return round(np.random.uniform(0.2, 0.3), round_ratio)
            elif (Il > 0) and (Il <= 0.25):
                return round(np.random.uniform(0.3, 0.38), round_ratio)
            elif (Il > 0.25) and (Il <= 0.75):
                return round(np.random.uniform(0.35, 0.42), round_ratio)
            elif Il > 0.75:
                return round(np.random.uniform(0.4, 0.47), round_ratio)
        elif (Ip >= 7) and (Ip < 17):
            if Il <= 0:
                return round(np.random.uniform(0.22, 0.32), round_ratio)
            elif (Il > 0) and (Il <= 0.25):
                return round(np.random.uniform(0.28, 0.35), round_ratio)
            elif (Il > 0.25) and (Il <= 0.75):
                return round(np.random.uniform(0.33, 0.4), round_ratio)
            elif Il > 0.75:
                return round(np.random.uniform(0.38, 0.47), round_ratio)
        elif (Ip >= 1) and (Ip < 7):
            if Il <= 0:
                return round(np.random.uniform(0.21, 0.26), round_ratio)
            elif (Il > 0) and (Il <= 0.75):
                return round(np.random.uniform(0.25, 0.32), round_ratio)
            elif Il > 0.75:
                return round(np.random.uniform(0.3, 0.36), round_ratio)
        else:
            return round(np.random.uniform(0.25, 0.35), round_ratio)

def dependence_E0_Il(Il):
    """Находит зависимость коэффициента k (E0 = E*k) в зависимости от Il"""
    if Il == "-":
        Il = np.random.uniform(-0.1, 0.05)
    return sigmoida(Il, 4, 0.5, 6, 1.2)

def define_ID(type_ground, rs, e):
    """Функция рассчитывает параметр ID"""
    if type_ground == 1:
        rmin = np.random.uniform(1.55, 1.65)
        rmax = np.random.uniform(1.75, 1.9)
    elif type_ground == 2:
        rmin = np.random.uniform(1.55, 1.65)
        rmax = np.random.uniform(1.75, 1.9)
    elif type_ground == 3:
        rmin = np.random.uniform(1.5, 1.59)
        rmax = np.random.uniform(1.7, 1.85)
    elif type_ground == 4:
        rmin = np.random.uniform(1.4, 1.48)
        rmax = np.random.uniform(1.6, 1.7)
    elif type_ground == 5:
        rmin = np.random.uniform(1.3, 1.4)
        rmax = np.random.uniform(1.55, 1.6)

    if rs=='-':
        rs=np.random.uniform(0.99 * rmin, 0.99 * rmax)

    emin = (rs - rmax) / rmax
    emax = (rs - rmin) / rmin
    if e == '-':
        e = np.random.uniform(0.99 * emin, 0.99 * emax)
    if e < emin:
        e = np.random.uniform(0.99 * emin, 0.99 * emax)

    ID = (emax - e) / (emax - emin)

    return ID

def define_dilatancy(data_gran, rs, e, sigma_1, sigma_3, fi, OCR, Ip, Ir):
    """Определяет угол дилатансии
    data_gran - словарь гран состава
    rs - плотность грунта
    e - коэффициент пористости
    fi - угол внутреннего трения
    OCR - параметр переуплотнения
    """
    p = (sigma_1 + 2 * sigma_3) / 3
    if define_type_ground(data_gran, Ip, Ir) <=5:
        ID = define_ID(define_type_ground(data_gran, Ip, Ir), rs, e)
        IR = ID * (10 - np.log(p)) - 1
        angle_of_dilatancy=(3 * IR / 0.8) # в градусах
    else:
        Mc = (6 * np.sin(np.deg2rad(fi))) / (3 - np.sin(np.deg2rad(fi))) * ((1 / OCR) ** np.random.uniform(0.4, 0.6))
        q = sigma_1 - sigma_3
        n = q / p
        Dmcc = (Mc ** 2 - n ** 2) / (2 * n)
        angle_of_dilatancy=np.rad2deg(np.arcsin(Dmcc / (-2+Dmcc)))

    return round(angle_of_dilatancy, 1)

def define_dilatancy_from_xc_qres(xc, qres):
    """Определяет угол дилатансии"""
    k_xc = sigmoida(mirrow_element(xc, 0.075), 5, 0.075, 5, 0.15)
    k_qres = sigmoida(mirrow_element(qres, 0.75), 5, 0.75, 5, 0.5)
    angle_of_dilatancy = k_xc + k_qres

    return round(angle_of_dilatancy, 1)

def define_m(e, Il):
    """Функция расчета параметра m - показатель степени для зависимости жесткости от уровня напряжений
     Входные параметры:
        :param e: пористость
        :param Il: число пластичности"""

    if Il == "-" or e == "-":

        return round(np.random.uniform(0.5, 0.65), 2)

    else:

        default_Il = [-0.25, 0, 0.25, 0.5, 0.75, 1]
        default_e = [0.5, 0.8, 1.2]
        default_m = [0.5, 0.6, 0.6, 0.7, 0.8, 0.8, 0.4, 0.5, 0.6, 0.7, 0.7, 0.9, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]

        if Il < default_Il[0]:
            Il = default_Il[0]
        if Il > default_Il[-1]:
            Il = default_Il[-1]
        if e < default_e[0]:
            e = default_e[0]
        if e > default_e[-1]:
            e = default_e[-1]

        default_e_Il = []
        for _e in default_e:
            default_e_Il.extend(list(map(lambda Il: [_e, Il], default_Il)))

        m = griddata(default_e_Il, default_m, (e, Il), method='cubic').item()

        try:
            return round(m, 2)
        except:
            round(np.random.uniform(0.5, 0.65), 2)


def define_OCR_from_xc(xc):
    return 5.5-30*xc

def new_noise_for_mohrs_circles(sigma3, sigma1, fi, c):
    '''fi - в градусах, так что
    tan(np.deg2rad(fi)) - тангенс угла наклона касательной
    '''

    fi = np.tan(np.deg2rad(fi))

    # выбираем случайную окружность. считаем ее индекс:
    fixed_circle_index = np.random.randint(0, len(sigma1)-1)

    # генерируем случайной значение
    a = np.random.uniform(np.min(sigma1 - sigma3) / 5, np.min(sigma1 - sigma3) / 4)

    # создаем копию массива для зашумленных значений
    sigma1_with_noise = copy.deepcopy(sigma1)

    # добавляем шум к зафиксированной окружности
    sigma1_with_noise[fixed_circle_index] -= a


    def func(x):
        '''x - массив sigma_1 без зафиксированной окружности'''

        # возвращаем зафиксированную огружность для подачи в фукнцию mohr_cf_stab
        x = np.insert(x, fixed_circle_index, sigma1_with_noise[fixed_circle_index])
        # определяем новые фи и с для измененной окружности
        c_new, fi_new = mohr_cf_stab(sigma3, x)
        # критерий минимизации - ошибка между fi и c для несмещенных кругов
        return c_new - c, fi_new - fi


    # начальное приближение для расчета оставшихся sigma_1
    # задается через удаление зафиксированной окружности из массива
    # чтобы fsolve не изменял зафиксированную окружность
    initial = np.delete(sigma1_with_noise, fixed_circle_index)
    root = fsolve(func, initial)
    sigma1_with_noise = np.insert(root, fixed_circle_index, sigma1_with_noise[fixed_circle_index])
    qf_with_noise=sigma1_with_noise-sigma3


    return np.round(qf_with_noise, 1)







if __name__ == '__main__':

    versions = {
        "Triaxial_Dynamic_Soil_Test": 1.8,
        "Triaxial_Dynamic_Processing": 1.8,
        "Resonance_Column_Siol_Test": 1.1,
        "Resonance_Column_Processing": 1.1
    }
    structure = {"trigger": ["CA"],
                 "sequence": ["A", "B", "C"],
                 "columns_title": ["Лаб.номер", "Скважина", "Глубина"]}

    structures = {"trigger": ["CA"],  #None
                 "columns": {"0": {"title": "Скважина", "cell": "B"},
                             "1": {"title": "Лаб.номер", "cell": "A"},
                             "2": {"title": "Глубина", "cell": "C"}}}

    structures = {"resonance_column": {"trigger": ["CA"],  #None
                                       "columns": {"0": {"title": "Скважина", "cell": "B"},
                                                         "1": {"title": "Лаб.номер", "cell": "A"},
                                                         "2": {"title": "Глубина", "cell": "C"}}},
                  "triaxial_cyclic": {"trigger": ["CA"],  # None
                                       "columns": {"0": {"title": "Лаб.номер", "cell": "A"},
                                                   "1": {"title": "Скважина", "cell": "B"},
                                                   "2": {"title": "Глубина", "cell": "C"}}}
                  }

    rcParams = {'font_size': 46,
                'transparency': 45,
                'text': "НЕ ДЛЯ\nОТЧЕТА"}


    create_json_file("C:/Users/Пользователь/Desktop/configs.json", rcParams)
