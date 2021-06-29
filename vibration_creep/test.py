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
from general.general_functions import read_json_file
from dataclasses import dataclass

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))

"""DataModelVibrationCreep = AttrDict({
    "strain_dynamic": None,
    "start_dynamic": None,  # Начало циклического нагружения
    "deviator_dynamic": None,
    "time": None,
    "cycles_dynamic": None,  # Ось циклов
    "creep_curve": None
})"""

class DataModelVibrationCreep:
    strain_dynamic: type(np.array([]))
    start_dynamic: int  # Начало циклического нагружения
    deviator_dynamic: type(np.array([]))
    time: type(np.array([]))
    cycles_dynamic: type(np.array([]))  # Ось циклов
    creep_curve: type(np.array([]))

"""TestResultModelVibrationCreep = AttrDict({
    "Kd": None,
    "E50d": None,
    "E50": None
})"""

class TestResultModelVibrationCreep:
    Kd: float
    E50d: float
    E50: float

class ModelVibrationCreep:
    """Модель виброползучести"""
    def __init__(self):
        # Основные массивы опыта
        self._static_test_data = ModelTriaxialDeviatorLoading()

        # Массив опытов с данными из DataModelVibrationCreep
        self._dynamic_tests = []

        # Массив результатов с данными TestResultModelVibrationCreep
        self._test_results = []

    def set_static_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора Геотек"""
        self._static_test_data.set_test_data(test_data)

    def add_dynamic_test(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора Wille"""
        self._dynamic_tests.append(DataModelVibrationCreep())
        self._dynamic_tests[0].strain_dynamic = test_data["strain"]
        self._dynamic_tests[0].deviator_dynamic = test_data["deviator"]
        self._dynamic_tests[0].time = test_data["time"]
        print(max(self._dynamic_tests[0].deviator_dynamic))

        self._test_results.append(TestResultModelVibrationCreep())

        self._dynamic_tests.append(DataModelVibrationCreep())
        self._dynamic_tests[1].strain_dynamic = test_data["strain"]*1.1
        self._dynamic_tests[1].deviator_dynamic = test_data["deviator"]*1.4
        self._dynamic_tests[1].time = test_data["time"]*1.1
        self._test_results.append(TestResultModelVibrationCreep())
        print(max(self._dynamic_tests[-1].deviator_dynamic))

        print([(max(i.deviator_dynamic)) for i in self._dynamic_tests])
        self._test_processing()

    def set_static_test_path(self, path):
        try:
            self.set_static_test_data(ModelTriaxialStaticLoad.open_geotek_log(path)["deviator_loading"])
        except:
            pass

    def set_dynamic_test_path(self, path):
        try:
            self.add_dynamic_test(ModelTriaxialCyclicLoading.open_wille_log(path))
        except:
            pass

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return [i.get_dict() for i in self._test_result]

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        static_plots = self._static_test_data.get_plot_data()
        E50 = []
        E50d = []

        for dyn_test, test_result in zip(self._dynamic_tests, self._test_results):
            if test_result.E50d:
                E50d.append(point_to_xy(Point(x=0, y=0), Point(
                    x=1.1 * np.max(dyn_test.deviator_dynamic) / (test_result.E50d * 1000),
                    y=1.1 * np.max(dyn_test.deviator_dynamic))))
            else:
                E50d.append(None)

            if test_result.E50:
                E50.append(point_to_xy(Point(x=0, y=0), Point(
                    x=1.1 * np.max(dyn_test.deviator_dynamic) / (test_result.E50 * 1000),
                    y=1.1 * np.max(dyn_test.deviator_dynamic))))
            else:
                E50.append(None)
        return {"strain_dynamic": [i.strain_dynamic for i in self._dynamic_tests],
                "deviator_dynamic": [i.deviator_dynamic for i in self._dynamic_tests],
                "time": [i.time[i.start_dynamic:] for i in self._dynamic_tests],
                "creep_curve": [i.creep_curve for i in self._dynamic_tests],
                "strain": static_plots["strain"],
                "deviator": static_plots["deviator"],
                "E50d": E50d,
                "E50": E50}

    def plotter(self, save_path=None):
        """остроитель опыта"""

        figure = plt.figure(figsize=[9.3, 6])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПа")
        ax_creep = figure.add_subplot(2, 1, 2)
        ax_creep.set_xscale("log")
        ax_creep.set_xlabel("Время")
        ax_creep.set_ylabel("Пластическая деформация, д.е.")

        plot_data = self.get_plot_data()

        ax_deviator.plot(plot_data["strain"][:-5000], plot_data["deviator"][:-5000], alpha=0.5)

        for i, color in zip(range(len(plot_data["strain_dynamic"])), ["tomato", "forestgreen", "purple"]):
            print(self._test_results[i].Kd)
            ax_deviator.plot(plot_data["strain_dynamic"][i], plot_data["deviator_dynamic"][i], alpha=0.5, linewidth=0.5,
                             color=color)
            if plot_data["creep_curve"][i] is not None:
                ax_creep.plot(plot_data["time"][i], plot_data["creep_curve"][i], alpha=0.5, linewidth=0.5,
                             color=color)
            if plot_data["E50d"][i]:
                ax_deviator.plot(*plot_data["E50d"][i], **plotter_params["black_dotted_line"])

        #if plot_data["E50"]:
            #ax_deviator.plot(*plot_data["E50"], **plotter_params["black_dotted_line"])

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass
        plt.show()

    def _test_processing(self):
        """Обработка результатов опыта"""
        if (not self._static_test_data.get_test_results()["qf"]) is not None:
            for dyn_test, test_result in zip(self._dynamic_tests, self._test_results):
                if dyn_test.strain_dynamic is not None:
                    qf = self._static_test_data.get_test_results()["qf"]*0.6
                    test_result.E50 = ModelVibrationCreep.find_E50_dynamic(dyn_test.strain_dynamic,
                                                                         dyn_test.deviator_dynamic, qf*1000)
                    if test_result.E50:
                        test_result.E50d = ModelVibrationCreep.find_E50d(dyn_test.strain_dynamic,
                                                                               dyn_test.deviator_dynamic)
                        test_result.Kd = np.round((test_result.E50d / test_result.E50), 2)

                        dyn_test.time, dyn_test.creep_curve = ModelVibrationCreep.plastic_creep(dyn_test.strain_dynamic,
                                                                                       dyn_test.deviator_dynamic,
                                                                                                dyn_test.time)

                    else:
                        test_result.E50d = None
                        test_result.Kd = None
                else:
                    pass
        else:
            pass

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
    a.set_static_test_path(file2)
    a.set_dynamic_test_path(file)
    a.plotter()