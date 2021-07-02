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
import copy

from general.general_functions import AttrDict, point_to_xy, Point
from configs.plot_params import plotter_params
from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad, ModelTriaxialStaticLoadSoilTest
from cyclic_loading.cyclic_loading_model import ModelTriaxialCyclicLoading, ModelTriaxialCyclicLoadingSoilTest
from general.general_functions import read_json_file
from dataclasses import dataclass

try:
    plt.rcParams.update(read_json_file(os.getcwd() + "/configs/rcParams.json"))
except FileNotFoundError:
    plt.rcParams.update(read_json_file(os.getcwd()[:-15] + "/configs/rcParams.json"))

class DataModelVibrationCreep:
    strain_dynamic: type(np.array([])) = None
    start_dynamic: int = None # Начало циклического нагружения
    deviator_dynamic: type(np.array([])) = None
    time: type(np.array([])) = None
    cycles_dynamic: type(np.array([])) = None # Ось циклов
    creep_curve: type(np.array([])) = None
    frequency: float = None

class TestResultModelVibrationCreep:
    Kd: float = None
    E50d: float = None
    E50: float = None

    def get_dict(self):
        return {
            "Kd": self.Kd,
            "E50d": self.E50d,
            "E50": self.E50
        }


class ModelVibrationCreep:
    """Модель виброползучести"""
    def __init__(self):
        # Основные массивы опыта
        self._static_test_data = ModelTriaxialStaticLoad()

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
        self._dynamic_tests[-1].strain_dynamic = test_data["strain"]
        self._dynamic_tests[-1].deviator_dynamic = test_data["deviator"]
        self._dynamic_tests[-1].time = test_data["time"]
        self._dynamic_tests[-1].frequency = test_data["frequency"]
        self._dynamic_tests[-1].start_dynamic = \
            ModelVibrationCreep.define_start_dynamic(self._dynamic_tests[-1].deviator_dynamic)
        self._test_results.append(TestResultModelVibrationCreep())

        """self._dynamic_tests.append(DataModelVibrationCreep())
        self._dynamic_tests[-1].strain_dynamic = test_data["strain"]*1.2
        self._dynamic_tests[-1].deviator_dynamic = test_data["deviator"]*1.03
        self._dynamic_tests[-1].time = test_data["time"]*1.1
        self._dynamic_tests[-1].frequency= test_data["frequency"]*0.9
        self._dynamic_tests[-1].start_dynamic = \
            ModelVibrationCreep.define_start_dynamic(self._dynamic_tests[-1].deviator_dynamic)
        self._test_results.append(TestResultModelVibrationCreep())

        self._dynamic_tests.append(DataModelVibrationCreep())
        self._dynamic_tests[-1].strain_dynamic = test_data["strain"] * 1.4
        self._dynamic_tests[-1].deviator_dynamic = test_data["deviator"] * 1.05
        self._dynamic_tests[-1].time = test_data["time"] * 1.1
        self._dynamic_tests[-1].frequency = test_data["frequency"]*0.7
        self._dynamic_tests[-1].start_dynamic = \
            ModelVibrationCreep.define_start_dynamic(self._dynamic_tests[-1].deviator_dynamic)
        self._test_results.append(TestResultModelVibrationCreep())"""

        self._test_processing()

    def set_static_test_path(self, path):
        try:
            self._static_test_data.set_test_file_path(path)
        except:
            pass

    def set_dynamic_test_path(self, path):
        try:
            self.add_dynamic_test(ModelTriaxialCyclicLoading.open_wille_log(path))
        except:
            pass

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return [i.get_dict() for i in self._test_results]

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        static_plots = self._static_test_data.deviator_loading.get_plot_data()
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
                "time": [i.time for i in self._dynamic_tests],
                "creep_curve": [i.creep_curve for i in self._dynamic_tests],
                "strain": static_plots["strain"],
                "deviator": static_plots["deviator"],
                "E50d": E50d,
                "E50": E50,
                "frequency": [i.frequency for i in self._dynamic_tests]}

    def plotter(self, save_path=None):
        """остроитель опыта"""

        figure = plt.figure(figsize=[9.3, 6])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПа")
        ax_creep = figure.add_subplot(2, 1, 2)
        ax_creep.set_xscale("log")#, basex=np.e)
        ax_creep.set_xlabel("Время")
        ax_creep.set_ylabel("Пластическая деформация, д.е.")

        plot_data = self.get_plot_data()
        result_data = self.get_test_results()

        ax_deviator.plot(plot_data["strain"], plot_data["deviator"], alpha=0.5)
        lims = [min([min(x) for x in plot_data["creep_curve"]]) , max([max(x) for x in plot_data["creep_curve"]])*1.05]

        for i, color in zip(range(len(plot_data["strain_dynamic"])), ["tomato", "forestgreen", "purple"]):
            plot_data["creep_curve"][i] -= plot_data["creep_curve"][i][0]
            ax_deviator.plot(plot_data["strain_dynamic"][i], plot_data["deviator_dynamic"][i], alpha=0.5, linewidth=1,
                             color=color, label="Kd = " + str(result_data[i]["Kd"]) + "; frequency = " + str(plot_data["frequency"][i]) + " Hz")

            #plt.axes([0.3, 0.6, .2, .2])
            #plt.plot(plot_data["creep_curve"][i], plot_data["deviator_dynamic"][i][len(plot_data["deviator_dynamic"][i]) - len(plot_data["creep_curve"][i]):],
                     #alpha=0.5, linewidth=1, color=color)
            #plt.grid()
            #plt.title('Динамическая нагрузка', fontsize=10)
            #plt.xlim(*lims)
            #plt.xticks([])
            #plt.yticks([])

            if plot_data["creep_curve"][i] is not None:
                ax_creep.plot(plot_data["time"][i], plot_data["creep_curve"][i], alpha=0.5, color=color,
                              label="frequency = " + str(plot_data["frequency"][i]) + " Hz")

            if plot_data["E50d"][i]:
                ax_deviator.plot(*plot_data["E50d"][i], **plotter_params["black_dotted_line"])

            if plot_data["E50"][i]:
                ax_deviator.plot(*plot_data["E50"][i], **plotter_params["black_dotted_line"])


            ax_deviator.legend()
            ax_creep.legend()

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
        if self._static_test_data.get_test_results()["qf"] is not None:
            for dyn_test, test_result in zip(self._dynamic_tests, self._test_results):
                if dyn_test.strain_dynamic is not None:
                    qf = self._static_test_data.get_test_results()["qf"]

                    test_result.E50, test_result.E50d = \
                        ModelVibrationCreep.find_E50d(dyn_test.strain_dynamic, dyn_test.deviator_dynamic,
                                                      start_dynamic=dyn_test.start_dynamic)
                    test_result.Kd = np.round((test_result.E50d / test_result.E50), 2)

                    dyn_test.time, dyn_test.creep_curve = \
                        ModelVibrationCreep.plastic_creep(dyn_test.strain_dynamic, dyn_test.deviator_dynamic,
                                                          dyn_test.time, start_dynamic=dyn_test.start_dynamic)

                    """test_result.E50 = ModelVibrationCreep.find_E50_dynamic(dyn_test.strain_dynamic,
                                                                         dyn_test.deviator_dynamic, qf*1000)
                    if test_result.E50:
                        test_result.E50d = ModelVibrationCreep.find_E50d(dyn_test.strain_dynamic,
                                                                               dyn_test.deviator_dynamic)
                        test_result.Kd = np.round((test_result.E50d / test_result.E50), 2)

                        dyn_test.time, dyn_test.creep_curve = ModelVibrationCreep.plastic_creep(dyn_test.strain_dynamic,
                                                                                       dyn_test.deviator_dynamic,
                                                                                                dyn_test.time)"""

                else:
                    test_result.E50d = None
                    test_result.Kd = None
        else:
            pass

    @staticmethod
    def plastic_creep(strain, deviator, time, start_dynamic=None):  # ось циклов, ось девиатора
        _start_dynamic = start_dynamic

        # Приводим массивы к правильному виду
        strain = strain[_start_dynamic:]
        deviator = deviator[_start_dynamic:]
        time = time[_start_dynamic:]

        creep = []
        time_creep = []

        nul = np.mean(deviator)  # (max(Y)+min(Y))/2

        for i in range(0, len(deviator) - 1):
            if deviator[i] > nul and deviator[i + 1] < nul:
                creep.append(strain[i])
                time_creep.append(time[i])

        creep = list(map(lambda x: x - creep[0], creep))
        time_creep = list(map(lambda x: x - time_creep[0], time_creep))

        #return np.array(time_creep), np.array(creep)
        return time - time[0], strain - strain[0]

    @staticmethod
    def find_E50d(strain, deviator, start_dynamic=False):
        start = start_dynamic
        mean_dynamic_load = np.mean(np.array(deviator[int(start):]))

        if deviator[-1] >= mean_dynamic_load:
            i, = np.where(np.array(deviator[::-1]) < mean_dynamic_load)
            E50d = mean_dynamic_load / strain[len(strain) - i[0]]

        elif deviator[-1] < mean_dynamic_load:
            i, = np.where(np.array(deviator[::-1]) > mean_dynamic_load)
            E50d = mean_dynamic_load / strain[len(strain) - i[0]]


        if deviator[int(start)] >= mean_dynamic_load:
            i, = np.where(np.array(deviator[:int(start)]) < mean_dynamic_load)
            E50 = mean_dynamic_load / strain[int(start) + i[0]]

        elif deviator[int(start)] < mean_dynamic_load:
            i, = np.where(np.array(deviator[:int(start)]) > mean_dynamic_load)
            E50 = mean_dynamic_load / strain[int(start) + i[0]]

        E50 = mean_dynamic_load / np.min(strain[int(start):])

        plt.plot(strain, deviator)
        plt.scatter(strain[int(start)], deviator[int(start)], color="red")
        plt.show()

        return (round(E50 / 1000, 2), round(E50d / 1000, 2))

    @staticmethod
    def find_E50_dynamic(strain, deviator, qf):
        """Определение параметра E50 по динамической кривой при наличии qf"""
        i_half_qf, = np.where(deviator > qf/2)
        if len(i_half_qf):
            E50 = (qf / 2) / (strain[i_half_qf[0]])
            return round(E50 / 1000, 2)
        else:
            return None

    @staticmethod
    def define_start_dynamic(deviator):
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
        return index_1

class ModelVibrationCreepSoilTest(ModelVibrationCreep):
    """Модель виброползучести"""
    def __init__(self):
        # Основные массивы опыта
        self._static_test_data = ModelTriaxialStaticLoadSoilTest()

        # Массив моделей опытов
        self._dynamic_tests_models = []

        # Массив опытов с данными из DataModelVibrationCreep
        self._dynamic_tests = []

        # Массив результатов с данными TestResultModelVibrationCreep
        self._test_results = []

    def set_static_test_params(self, params):
        self._static_test_data.set_test_params(params)

    def set_dynamic_test_params(self, params):
        for frequency in params["frequency"]:
            self._dynamic_tests_models.append(ModelTriaxialCyclicLoadingSoilTest(False))
            params_for_current_test = copy.copy(params)
            params_for_current_test["frequency"] = frequency
            params_for_current_test["E"] = params_for_current_test["E"]*np.random.uniform(0.95, 1.03)
            self._dynamic_tests_models[-1].set_test_params(params_for_current_test)

        for test in self._dynamic_tests_models:
            self._dynamic_tests.append(DataModelVibrationCreep())
            test_data = test.get_data_for_vibration_creep()
            self._dynamic_tests[-1].strain_dynamic = test_data["strain"]
            self._dynamic_tests[-1].deviator_dynamic = test_data["deviator"]
            self._dynamic_tests[-1].time = test_data["time"]
            self._dynamic_tests[-1].frequency = test_data["frequency"]
            self._dynamic_tests[-1].start_dynamic = test_data["start_dynamic"]
            self._test_results.append(TestResultModelVibrationCreep())

        self._test_processing()


if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    file = "C:/Users/Пользователь/Desktop/Опыты/Опыт Виброползучесть/Песок 1/E50/Косинусное значения напряжения.txt"
    file2 = "C:/Users/Пользователь/Desktop/Тест/Девиаторное нагружение/Архив/10-2/0.2.log"
    a = ModelVibrationCreep()
    a.set_static_test_path(file2)
    a.set_dynamic_test_path(file)
    a.plotter()


    """a = ModelVibrationCreepSoilTest()
    static_params = {'E': 50000.0, 'sigma_3': 100, 'sigma_1': 300, 'c': 0.025, 'fi': 45, 'qf': 593.8965363, 'K0': 0.5,
             'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'build_press': 500.0, 'pit_depth': 7.0, 'Eur': '-',
             'dilatancy': 4.95, 'OCR': 1, 'm': 0.61, 'lab_number': '7а-1', 'data_phiz': {'borehole': '7а',
                                                                                             'depth': 19.0, 'name': 'Песок крупный неоднородный', 'ige': '-', 'rs': 2.73, 'r': '-', 'rd': '-', 'n': '-', 'e': '-', 'W': 12.8, 'Sr': '-', 'Wl': '-', 'Wp': '-', 'Ip': '-', 'Il': '-', 'Ir': '-', 'str_index': '-', 'gw_depth': '-', 'build_press': 500.0, 'pit_depth': 7.0, '10': '-', '5': '-', '2': 6.8, '1': 39.2, '05': 28.0, '025': 9.2, '01': 6.1, '005': 10.7, '001': '-', '0002': '-', '0000': '-', 'Nop': 7, 'flag': False}, 'test_type':
                         'Трёхосное сжатие (E)'}
    a.set_static_test_params(static_params)
    dynamic_params = {'E': 50000.0, 'c': 0.023, 'fi': 45, 'qf': 593.8965363,
     'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'depth': 9.8, 'Ip': 17.9,
     'Il': 0.79, 'K0': 1, 'groundwater': 0.0, 'ro': 1.76, 'balnost': 2.0, 'magnituda': 5.0, 'rd': '0.912', 'N': 100,
     'MSF': '2.82', 'I': 2.0, 'sigma1': 100, 't': 10, 'sigma3': 100, 'ige': '-', 'Nop': 20, 'lab_number': '4-5',
     'data_phiz': {'borehole': 'rete', 'depth': 9.8,
                   'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'ige': '-',
                   'rs': 2.73, 'r': 1.76, 'rd': 1.23, 'n': 55.0, 'e': 1.22, 'W': 43.4, 'Sr': 0.97, 'Wl': 47.1,
                   'Wp': 29.2, 'Ip': 17.9, 'Il': 0.79, 'Ir': 6.8, 'str_index': 'l', 'gw_depth': 0.0, 'build_press': '-',
                   'pit_depth': '-', '10': '-', '5': '-', '2': '-', '1': '-', '05': '-', '025': 0.3, '01': 0.1,
                   '005': 17.7, '001': 35.0, '0002': 18.8, '0000': 28.1, 'Nop': 20}, 'test_type': 'Сейсморазжижение',
                               "frequency": [1], "n_fail": None, "Mcsr": 100}

    a.set_dynamic_test_params(dynamic_params)
    a.plotter()"""
