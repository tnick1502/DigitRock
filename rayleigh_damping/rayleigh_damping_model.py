"""Модуль математических моделей циклического нагружения. Содержит модели:
    ModelVibrationCreep - модель обработчика данных опыта выброползучести.
        Модель имеет 2 типа данных: динамический опыт и статический.
        За статическую часть отвечает модель ModelTriaxialStaticLoading.
        Данные подаются в модель методом set_static_test_data(test_data) и set_dynamic_test_data(test_data) c
        определенными ключами. Функция открытия файла прибора динамики open_wille_log() находится в классе
        ModelTriaxialCyclicLoading. Функция открытия для статического опыта в модуле triaxial_deviator_loading_model
        Обработка опыта происходит с помощью метода _test_processing().
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()"""

__version__ = 1

import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import copy
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution
import warnings

from general.general_functions import point_to_xy, Point
from configs.plot_params import plotter_params
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad, ModelTriaxialStaticLoadSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoading, ModelTriaxialCyclicLoadingSoilTest
from general.general_functions import read_json_file, sigmoida, mirrow_element
from dataclasses import dataclass
from singletons import statment, E_models
from scipy.optimize import least_squares

@dataclass
class TestResults:
    alpha: float = None
    betta: float = None
    frequency: list = None
    damping_ratio: list = None

    def get_dict(self):
        return {
            "alpha": self.alpha,
            "betta": self.betta,
            "frequency": self.frequency,
            "damping_ratio": self.damping_ratio,
        }

class ModelRayleighDamping:
    """Модель виброползучести"""
    def __init__(self):
        # Основные массивы опыта
        self._tests = []

        # Массив результатов с данными TestResultModelVibrationCreep
        self._test_results = TestResults()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_results.get_dict()

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        return {
            "frequency": self._test_results.frequency,
            "damping_ratio": self._test_results.damping_ratio,

            "frequency_rayleigh": np.linspace(0.08, 10.5, 100),
            "damping_rayleigh": ModelRayleighDamping.define_damping_ratio(
                self._test_results.alpha, self._test_results.betta, np.linspace(0.08, 10.5, 100))
        }

    def _test_processing(self):
        """Обработка результатов опыта"""
        frequency = []
        damping_ratio = []

        for test in self._tests:
            frequency.append(test._test_params.frequency)
            damping_ratio.append(np.round(test._test_result.damping_ratio, 2))

        self._test_results = TestResults()

        self._test_results.frequency = np.array(frequency)
        self._test_results.damping_ratio = np.array(damping_ratio)
        self._test_results.alpha, self._test_results.betta = ModelRayleighDamping.define_rayleigh_coefficients(
            self._test_results.frequency*2*np.pi, self._test_results.damping_ratio/100)

        self._test_results.alpha = np.round(self._test_results.alpha, 3)
        self._test_results.betta = np.round(self._test_results.betta, 5)

    @staticmethod
    def define_rayleigh_coefficients(frequency: np.array, damping_ratio: np.array):
        """
            Подается 2 массива. На картинке дзетта, в функции `damping_ratio`, и частота омега - `frequency`.
             Получается 2 точки на этих осях. ню1 - alpha, ню2- betta.
            Если подается массив размером 2, то alpha, betta по формуле с картинки справа которая.
             Если массивы пазмером больше 2, то методом наименьших квадратов
        """

        def lse_damping_ratio(__frequency, __damping_ratio):
            """
            Выполняет МНК приближение прямой вида alpha / (2 * frequency) + betta * frequency / 2

            :param __damping_ratio: array-like, координаты y
            :param __frequency: array-like, координаты x
            :return: float, коэффициенты k, b и ошибка
            """

            def fun(x, __freq, __damping):
                return x[0] / (2 * __freq) + x[1] * __freq / 2 - __damping

            x0 = [0.5, 0.5]

            res_lsq = least_squares(fun, x0, loss='soft_l1', f_scale=0.1, args=(__frequency, __damping_ratio))
            _alpha = res_lsq.x[0]
            _betta = res_lsq.x[1]

            return _alpha, _betta

        # Проверки
        frequency = np.asarray(frequency)
        damping_ratio = np.asarray(damping_ratio)
        len_frequency = len(frequency)
        len_damping_ratio = len(damping_ratio)

        if not (len_frequency > 1 and len_damping_ratio > 1):
            raise ValueError('frequency and damping_ratio must be greater than 2 (including)')

        if len_frequency != len_damping_ratio:
            raise ValueError('frequency and damping_ratio must be equal length')

        if not np.all(np.all(frequency[1:] >= frequency[:-1])):
            raise ValueError('frequency must be strictly increasing')

        # Вариант - 1: длина равна 2-м.
        if len_frequency == 2:
            alpha = 2 * frequency[0] * frequency[1] / (frequency[1] ** 2 - frequency[0] ** 2)
            alpha = alpha * (damping_ratio[0] * frequency[1] - damping_ratio[1] * frequency[0])
            betta = 2 * (damping_ratio[1] * frequency[1] - damping_ratio[0] * frequency[0]) / (
                        frequency[1] ** 2 - frequency[0] ** 2)
            return alpha, betta

        # Вариант - 2: мнк-приближение.
        alpha, betta = lse_damping_ratio(frequency, damping_ratio)
        return alpha, betta

    @staticmethod
    def define_damping_ratio(alpha: float, betta: float, frequency: float):
        damping_ratio = 0.5*(alpha / (frequency * 2 * np.pi) + betta * frequency * 2 * np.pi)
        return damping_ratio * 100

class ModelRayleighDampingSoilTest(ModelRayleighDamping):
    """Модель виброползучести"""

    def set_test_params(self):
        self._tests = []

        frequency_origin = statment[statment.current_test].mechanical_properties.frequency

        alpha = statment[statment.current_test].mechanical_properties.alpha
        betta = statment[statment.current_test].mechanical_properties.betta

        damping_ratio_origin = [np.round(ModelRayleighDamping.define_damping_ratio(alpha, betta, f) *
                                np.random.uniform(0.9, 1.1), 2) for f in frequency_origin]

        for frequency, damping_ratio in zip(frequency_origin, damping_ratio_origin):
            statment[statment.current_test].mechanical_properties.frequency = frequency
            statment[statment.current_test].mechanical_properties.damping_ratio = damping_ratio
            self._tests.append(ModelTriaxialCyclicLoadingSoilTest())
            self._tests[-1].set_test_params()

        statment[statment.current_test].mechanical_properties.frequency = frequency_origin
        statment[statment.current_test].mechanical_properties.damping_ratio = damping_ratio_origin
        self._test_processing()

    def set_one_test_params(self, i):
        frequency_origin = statment[statment.current_test].mechanical_properties.frequency
        damping_ratio_origin = statment[statment.current_test].mechanical_properties.damping_ratio

        statment[statment.current_test].mechanical_properties.frequency = statment[statment.current_test].mechanical_properties.frequency[i]
        statment[statment.current_test].mechanical_properties.damping_ratio = statment[statment.current_test].mechanical_properties.damping_ratio[i]
        self._tests[i].set_test_params()

        statment[statment.current_test].mechanical_properties.frequency = frequency_origin
        statment[statment.current_test].mechanical_properties.damping_ratio = damping_ratio_origin
        self._test_processing()

    def save_log_files(self, directory):
        """Метод генерирует файлы испытания для всех кругов"""
        for i, test in enumerate(self._tests):
            path = os.path.join(directory, str(statment[statment.current_test].mechanical_properties.frequency[i]))
            if not os.path.isdir(path):
                os.mkdir(path)
            test.generate_log_file(path)





if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    """file = "C:/Users/Пользователь/Desktop/Опыты/Опыт Виброползучесть/Песок 1/E50/Косинусное значения напряжения.txt"
    file2 = "C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив/10-2/0.2.log"
    a = ModelVibrationCreep()
    a.set_static_test_path(file2)
    a.set_dynamic_test_path(file)
    a.plotter()"""

    a = ModelVibrationCreepSoilTest()
    statment.load(r"C:\Users\Пользователь\Desktop\test\Виброползучесть.pickle")
    statment.current_test = "1-2"
    E_models.setModelType(ModelTriaxialStaticLoadSoilTest)

    E_models.load(r"C:\Users\Пользователь\Desktop\test\E_models.pickle")

    a.set_test_params()
    a.plotter()
    plt.show()

