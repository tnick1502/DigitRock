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
import scipy.ndimage as ndimage

from general.general_functions import AttrDict, point_to_xy, Point
from static_loading.deviator_loading_model import ModelTriaxialDeviatorLoading
from configs.plot_params import plotter_params
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoading


class ModelVibrationCreep:
    """Модель виброползучести"""
    def __init__(self):
        # Основные массивы опыта
        self._static_test_data = ModelTriaxialDeviatorLoading()

        self._dynamic_test_data = AttrDict({"strain_dynamic": None,
                                            "start_dynamic": None,  # Начало циклического нагружения
                                            "deviator_dynamic": None,
                                            "time": None,
                                            "cycles_dynamic": None,  # Ось циклов
                                            "creep_curve": None})
        # Результаты опыта
        self._test_result = AttrDict({"Kd": None,
                                      "E50d": None,
                                      "E50": None})

    def set_static_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора Геотек"""
        self._static_test_data.set_test_data(test_data)

    def set_dynamic_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора Wille"""
        self._dynamic_test_data.strain_dynamic = test_data["strain"]
        self._dynamic_test_data.deviator_dynamic = test_data["deviator"]
        self._dynamic_test_data.time = test_data["time"]
        self._test_processing()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        static_plots = self._static_test_data.get_plot_data()
        if self._test_result.E50d:
            E50d = point_to_xy(Point(x=0, y=0), Point(
                x=1.1 * np.max(self._dynamic_test_data.deviator_dynamic) / (self._test_result.E50d * 1000),
                y=1.1 * np.max(self._dynamic_test_data.deviator_dynamic)))
        else:
            E50d = None

        if self._test_result.E50:
            E50 = point_to_xy(Point(x=0, y=0), Point(
                x=1.1 * np.max(self._dynamic_test_data.deviator_dynamic) / (self._test_result.E50 * 1000),
                y=1.1 * np.max(self._dynamic_test_data.deviator_dynamic)))
        else:
            E50 = None

        return {"strain_dynamic": self._dynamic_test_data.strain_dynamic,
                "deviator_dynamic": self._dynamic_test_data.deviator_dynamic,
                "time": self._dynamic_test_data.time[self._dynamic_test_data.start_dynamic:],
                "creep_curve": self._dynamic_test_data.creep_curve,
                "strain": static_plots["strain"],
                "deviator": static_plots["deviator"],
                "E50d": E50d,
                "E50": E50}

    def plotter(self, save_path=None):
        """остроитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '12'
        rcParams['axes.edgecolor'] = 'black'

        figure = plt.figure(figsize=[9.3, 6])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.grid(axis='both')
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПА")
        ax_creep = figure.add_subplot(2, 1, 2)
        ax_creep.grid(axis='both')
        ax_creep.set_xscale("log")
        ax_creep.set_xlabel("Время")
        ax_creep.set_ylabel("Пластическая деформация, д.е.")

        plot_data = self.get_plot_data()

        ax_deviator.plot(plot_data["strain"], plot_data["deviator"])
        ax_deviator.plot(plot_data["strain_dynamic"], plot_data["deviator_dynamic"])
        if plot_data["creep_curve"] is not None:
            ax_creep.plot(plot_data["time"], plot_data["creep_curve"])

        if plot_data["E50d"]:
            ax_deviator.plot(*plot_data["E50d"], **plotter_params["black_dotted_line"])
        if plot_data["E50"]:
            ax_deviator.plot(*plot_data["E50"], **plotter_params["black_dotted_line"])

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass
        plt.show()

    def _test_processing(self):
        """Обработка результатов опыта"""
        if (not self._static_test_data.get_test_results()["qf"]) or (self._dynamic_test_data.strain_dynamic is None):
            pass
        else:
            qf = self._static_test_data.get_test_results()["qf"]
            self._test_result.E50 = ModelVibrationCreep.find_E50_dynamic(self._dynamic_test_data.strain_dynamic,
                                                                         self._dynamic_test_data.deviator_dynamic, qf*1000)
            if self._test_result.E50:
                self._test_result.E50d = ModelVibrationCreep.find_E50d(self._dynamic_test_data.strain_dynamic,
                                                                       self._dynamic_test_data.deviator_dynamic)
                self._test_result.Kd = round((self._test_result.E50d / self._test_result.E50), 2)

                self._dynamic_test_data.time, self._dynamic_test_data.creep_curve = ModelVibrationCreep.plastic_creep(self._dynamic_test_data.strain_dynamic,
                                                                               self._dynamic_test_data.deviator_dynamic, self._dynamic_test_data.time)

            else:
                self._test_result.E50d = None
                self._test_result.Kd = None

    @staticmethod
    def plastic_creep(strain, deviator, time):  # ось циклов, ось девиатора
        # Поиск начала девиаторного нагружения
        for i in range(len(deviator) - 5):
            if deviator[i + 1] < deviator[i] and deviator[i + 2] < deviator[i + 1] and deviator[i + 3] < deviator[i + 2] and deviator[i + 4] < deviator[i + 3] and deviator[
                i + 5] < deviator[i + 4] and deviator[i + 6] < deviator[i + 5] and deviator[i + 7] < deviator[i + 6] and deviator[i + 8] < deviator[i + 7] and deviator[
                i + 9] < deviator[i + 8]:
                k = i
                break

        # Приводим массивы к правильному виду
        strain = strain[k:]
        deviator = deviator[k:]
        time = time[k:]

        creep = []
        time_creep = []

        nul = np.mean(deviator)  # (max(Y)+min(Y))/2

        for i in range(0, len(deviator) - 1):
            if deviator[i] > nul and deviator[i + 1] < nul:
                creep.append(strain[i])
                time_creep.append(time[i])

        creep = list(map(lambda x: x - creep[0], creep))
        time_creep = list(map(lambda x: x - time_creep[0], time_creep))

        return np.array(time_creep), np.array(creep)

    @staticmethod
    def find_E50d(strain, deviator):
        for i in range(len(deviator)):
            if (deviator[i] > deviator[i + 1]) and (deviator[i] > deviator[i + 2]) \
                    and (deviator[i] > deviator[i + 3]) and (deviator[i] > deviator[i + 4]) \
                    and (deviator[i] > deviator[i + 5]) and (deviator[i] > deviator[i + 6]) \
                    and (deviator[i] > deviator[i + 7]) and (deviator[i] > deviator[i + 8]) \
                    and (deviator[i] > deviator[i + 9]) and (deviator[i] > deviator[i + 10]) \
                    and (deviator[i] > deviator[i + 11]) and (deviator[i] > deviator[i + 12]) \
                    and (deviator[i] > deviator[i + 13]) and (deviator[i] > deviator[i + 14]) \
                    and (deviator[i] > deviator[i + 15]) and (i > int(len(deviator) * 3 / 4)):
                index_1 = i
                break
        # plt.scatter(strain[index_1], deviator[index_1])
        mean_dinamic_load = np.mean(deviator[index_1:])
        E50d = mean_dinamic_load / strain[-1]
        return round(E50d / 1000, 2)

    @staticmethod
    def find_E50_dynamic(strain, deviator, qf):
        """Определение параметра E50 по динамической кривой при наличии qf"""
        i_half_qf, = np.where(deviator > qf / 2.1)
        if len(i_half_qf):
            E50 = (qf / 2) / (strain[i_half_qf[0]])
            return round(E50 / 1000, 2)
        else:
            return None




if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    file = "C:/Users/Пользователь/Desktop/Опыты/Опыт Виброползучесть/Песок 1/E50/Косинусное значения напряжения.txt"
    file2 = "C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив/10-2/0.2.log"
    a = ModelVibrationCreep()
    a.set_static_test_data(ModelTriaxialStaticLoad.open_geotek_log(file2)["deviator_loading"])
    a.set_dynamic_test_data(ModelTriaxialCyclicLoading.open_wille_log(file))
    a.plotter()