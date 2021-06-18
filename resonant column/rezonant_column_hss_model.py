"""Модуль математических моделей циклического нагружения. Содержит модели:
    ModelTriaxialCyclicLoading - модель обработчика данных опыта.
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора open_wille_log() находится в модуле самом классе как метод класса
        Обработка опыта происходит с помощью метода _test_processing(). При неправильном автоопределении частоты можно
        подать ее самостоятельно с помощью метода set_frequency(frequency)
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialDynamicLoadingSoilTest - модель математического моделирования данных опыта. Наследует методы
    _test_processing(), get_test_results(), plotter(), а также структуру данных из ModelTriaxialCyclicLoading
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод _define_draw_params() определяет основные характеристики отрисовки опыта.
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_strain_params() и set_PPR_params() устанавливает позьзовательские значения параметров отрисовки.
        Методы _modeling_deviator(), _modeling_strain(), _modeling_PPR() моделируют соотвествующие массивы опытных
        данных. Вызываются при передачи пользовательских параметров отрисовки.
        Метод _test_modeling() содержит _modeling_deviator(), _modeling_strain(), _modeling_PPR(). Вызывается один раз
        для нахождения начальных параметров в методе set_test_params()."""

__version__ = 1

import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import scipy.ndimage as ndimage

from general.general_functions import define_qf, create_deviation_curve, current_exponent, step_sin, logarithm, sigmoida,\
    create_acute_sine_array, AttrDict, mirrow_element
from cyclic_loading.cyclic_stress_ratio_function import define_fail_cycle
from configs.plot_params import plotter_params

class ModelRezonantColumn:
    """Модель обработки циклического нагружения

    Логика работы:
        - Данные принимаются в set_test_data(). значально все данные обнуляются методом _reset_data()

        - Обработка опыта производится методом _test_processing.

        - Метод set_frequency позволяет задать частоту для масштабирования оси х. Используется в случае неправильной
        работы метода определения частоты

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""

    def __init__(self):
        """Определяем основную структуру данных"""
        # Структура дынных
        self._test_data = AttrDict({"time": None,
                                    "cycles": None,
                                    "cell_pressure": None,
                                    "setpoint": None,
                                    "strain": None,
                                    "deviator": None,
                                    "PPR": None,
                                    "mean_effective_stress": None})

        self._test_params = AttrDict({"frequency": None,
                                      "points_in_cycle": None})

        # Результаты опыта
        self._test_result = AttrDict({"max_PPR": None,
                                      "max_strain": None,
                                      "fail_cycle": None,  # номер цикла или False (минимальный из последующих)
                                      "fail_cycle_criterion_strain": None,  # номер цикла или False
                                      "fail_cycle_criterion_stress": None,  # номер цикла или False
                                      "fail_cycle_criterion_PPR": None,  # номер цикла или False
                                      "conclusion": None})  # заключение о разжижаемости

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._test_data.cycles = test_data["cycles"]
        self._test_data.time = test_data["time"]
        self._test_params.frequency = test_data["frequency"]
        self._test_params.points_in_cycle = test_data["points"]
        self._test_data.deviator = test_data["deviator"]
        self._test_data.PPR = test_data["PPR"]
        self._test_data.strain = test_data["strain"]
        self._test_data.mean_effective_stress = test_data["mean_effective_stress"]
        self._test_data.cell_pressure = test_data["cell_pressure"]

        self._test_processing()

    def get_test_params(self):
        return self._test_params.get_dict()

    def set_frequency(self, frequency):
        """Изменение частоты опыта"""
        self._test_params.frequency = frequency
        self._test_data.cycles = self._test_data.time * self._test_params.frequency

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Возвращает данные для построения"""
        if self._test_data.strain is None:
            return None
        else:
            strain_lim = []
            if np.min(self._test_data.strain) < 0:
                strain_lim.append(np.min(self._test_data.strain) - 0.005)
            else:
                strain_lim.append(-0.005)
            if np.max(self._test_data.strain) > 0.0475:
                strain_lim.append(np.max(self._test_data.strain) + 0.0025)
            else:
                strain_lim.append(0.05)

            PPR_lim = []
            if np.min(self._test_data.PPR) < 0:
                PPR_lim.append(np.min(self._test_data.PPR) - 0.1)
            else:
                PPR_lim.append(-0.1)
            if np.max(self._test_data.PPR) > 0.95:
                PPR_lim.append(np.max(self._test_data.PPR) + 0.05)
            else:
                PPR_lim.append(1)

            return {"cycles": self._test_data.cycles,
                    "deviator": self._test_data.deviator,
                    "strain": self._test_data.strain,
                    "PPR": self._test_data.PPR,
                    "mean_effective_stress": self._test_data.mean_effective_stress,
                    "strain_lim": strain_lim,
                    "PPR_lim": PPR_lim}

    def plotter(self, save_path=None):
        """Построение графиков опыта. Если передать параметр save_path, то графики сохраняться туда"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '14'
        rcParams['axes.edgecolor'] = 'black'

        plot_data = self.get_plot_data()

        if plot_data:
            figure = plt.figure(figsize = [9.3, 6])
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

            ax_deviator = figure.add_subplot(2, 2, 1)
            ax_deviator.grid(axis='both')
            ax_deviator.set_xlabel("Число циклов N, ед.")
            ax_deviator.set_ylabel("Девиатор q, кПА")

            ax_strain = figure.add_subplot(2, 2, 2)
            ax_strain.grid(axis='both')
            ax_strain.set_xlabel("Число циклов N, ед.")
            ax_strain.set_ylabel("Относительная деформация $ε_1$, д.е.")

            ax_strain.set_ylim(plot_data["strain_lim"])


            ax_PPR = figure.add_subplot(2, 2, 3)
            ax_PPR.grid(axis='both')
            ax_PPR.set_xlabel("Число циклов N, ед.")
            ax_PPR.set_ylabel("Приведенное поровое давление PPR, д.е.")

            ax_PPR.set_ylim(plot_data["PPR_lim"])


            ax_stresses = figure.add_subplot(2, 2, 4)
            ax_stresses.grid(axis='both')
            ax_stresses.set_xlabel("Среднее эффективное напряжение p', кПа")
            ax_stresses.set_ylabel("Касательное напряжение τ, кПа")

            ax_deviator.plot(plot_data["cycles"], plot_data["deviator"], **plotter_params["main_line"])
            ax_strain.plot(plot_data["cycles"], plot_data["strain"], **plotter_params["main_line"])
            ax_PPR.plot(plot_data["cycles"], plot_data["PPR"], **plotter_params["main_line"])
            ax_stresses.plot(plot_data["mean_effective_stress"], plot_data["deviator"] / 2, **plotter_params["main_line"])

            try:
                xlims = ax_stresses.get_xlim()
                ylims = ax_stresses.get_ylim()
                ax_stresses.plot(self._test_data.mean_effective_stress, self.critical_line, label="CSL",
                                 **plotter_params["dotted_line"])

                i, Msf = ModelTriaxialCyclicLoadingSoilTest.intercept_CSL(self._test_data.deviator / 2,
                                                                           self.critical_line, **plotter_params["dotted_line"])
                if i:
                    ax_stresses.scatter(self._test_data.mean_effective_stress[i], self._test_data.deviator[i] / 2,
                                        zorder=5, s=40, **plotter_params["dotted_line"])

                ax_stresses.legend()
                ax_stresses.set_xlim(xlims)
                ax_stresses.set_ylim(ylims)
            except:
                pass

            if save_path:
                try:
                    plt.savefig(save_path, format="png")
                except:
                    pass

            plt.show()

    def _test_processing(self):
        """Обработка опыта"""
        self._test_result.max_PPR = round(np.max(self._test_data.PPR), 3)
        self._test_result.max_strain = round(np.max(self._test_data.strain), 3)

        self._test_result.fail_cycle_criterion_strain = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                          (self._test_data.strain >= 0.05))
        self._test_result.fail_cycle_criterion_stress = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                          (self._test_data.mean_effective_stress <= 0))
        self._test_result.fail_cycle_criterion_PPR = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                       (self._test_data.PPR >= 1))

        self._test_result.fail_cycle = min([i for i in [self._test_result.fail_cycle_criterion_strain,
                                                        self._test_result.fail_cycle_criterion_stress,
                                                        self._test_result.fail_cycle_criterion_PPR] if i], default=None)

        if self._test_result.fail_cycle_criterion_stress or self._test_result.fail_cycle_criterion_PPR:
            self._test_result.conclusion = "Грунт склонен к разжижению"
        elif self._test_result.fail_cycle_criterion_strain:
            self._test_result.conclusion = "Грунт динамически неустойчив"
        else:
            self._test_result.conclusion = "Грунт не склонен к разжижению"

    @staticmethod
    def define_fail_cycle(cycles, condisions):
        """Функция находит номер цикла разрушения заданному критерию. Возвращает None, если критерий не выполнился"""

        def return_current_cycle(cycles, fail):
            try:
                return int(cycles[fail[0]])
            except IndexError:
                return None

        fail_cycles, = np.where(condisions)

        return return_current_cycle(cycles, fail_cycles)

    @staticmethod
    def open_wille_log(file_path, define_frequency=True):
        """Функция считывания файла опыта с прибора Вилли"""
        test_data = {"time": np.array([]), "cycles": np.array([]), "deviator": np.array([]), "strain": np.array([]),
                  "PPR": np.array([]), "mean_effective_stress": np.array([]), "cell_pressure": 0, "frequency": 0}

        columns_key = ["Time", 'Deviator', 'Piston position', 'Pore pressure', 'Cell pressure', "Sample height"]

        # Считываем файл
        f = open(file_path)
        lines = f.readlines()
        f.close()

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_key:  # по нужным столбцам
            index = (lines[0].split("\t").index(key)) #
            read_data[key] = np.array(list(map(lambda x: float(x.split("\t")[index]), lines[2:])))

        u_consolidations = read_data['Pore pressure'][0]

        test_data["cell_pressure"] = read_data['Cell pressure'] - u_consolidations
        pore_pressure = read_data['Pore pressure'] - u_consolidations
        test_data["PPR"] = pore_pressure / test_data["cell_pressure"]
        test_data["time"] = read_data["Time"] - read_data["Time"][0]
        test_data["deviator"] = read_data['Deviator']
        test_data["strain"] = (read_data['Piston position'] / read_data['Sample height']) - \
                              (read_data['Piston position'][0] / read_data['Sample height'][0])
        test_data["mean_effective_stress"] = ((test_data["cell_pressure"] * (1 - test_data["PPR"])) * 3 +
                                              test_data["deviator"])/3

        if define_frequency:
            test_data["frequency"], test_data["points"] = ModelTriaxialCyclicLoading.find_frequency(test_data["time"],
                                                                                                    test_data["deviator"])
            test_data["cycles"] = test_data["time"] * test_data["frequency"]
        else:
            pass

        return test_data

    @staticmethod
    def open_geotek_log(file_path, define_frequency=True):
        """Функция считывания файла опыта с прибора Вилли"""
        test_data = {"time": np.array([]), "cycles": np.array([]), "deviator": np.array([]), "strain": np.array([]),
                     "PPR": np.array([]), "mean_effective_stress": np.array([]), "cell_pressure": 0, "frequency": 0}

        columns_key = ["Test_Dyn_halfcycles", "Test_Dyn_time", "Test_DynVerticalPress_kPa_value",
                       "Test_DynPorePress_kPa_value", "Test_DynVerticalDeformation_mm_value"]

        # Считываем файл
        f = open(file_path)
        lines = f.readlines()
        f.close()

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_key:  # по нужным столбцам
            index = (lines[0].split("\t").index(key))  #
            read_data[key] = np.array(list(map(lambda x: float(x.split("\t")[index].replace(",", ".")), lines[1:])))

        test_data["cell_pressure"] = float(file_path[file_path.index("=") + 1: len(file_path) - file_path[::-1].index(".")].strip())
        u_consolidations = read_data["Test_DynPorePress_kPa_value"][0]
        test_data["PPR"] = (read_data["Test_DynPorePress_kPa_value"] - u_consolidations) / test_data["cell_pressure"]
        test_data["time"] = read_data["Test_Dyn_time"] - read_data["Test_Dyn_time"][0]
        test_data["deviator"] = read_data["Test_DynVerticalPress_kPa_value"] - test_data["cell_pressure"]
        test_data["strain"] = (read_data["Test_DynVerticalDeformation_mm_value"] - \
                              read_data["Test_DynVerticalDeformation_mm_value"][0]) / 100
        test_data["mean_effective_stress"] = ((test_data["cell_pressure"] * (1 - test_data["PPR"])) * 3 +
                                              test_data["deviator"]) / 3

        if define_frequency:
            test_data["frequency"], test_data["points"] = ModelTriaxialCyclicLoading.find_frequency(test_data["time"],
                                                                                                     test_data["deviator"])
            test_data["cycles"] = test_data["time"] * test_data["frequency"]
        else:
            pass

        return test_data

    @staticmethod
    def find_frequency(time, deviator):
        """Функция поиска частоты девиаторного нагружения"""
        mid_deviator = ((max(deviator) - min(deviator)) / 2) + min(deviator)
        k = 0
        for i in range(len(time) - 1):
            if deviator[i + 1] >= mid_deviator and deviator[i] < mid_deviator:
                k += 1
        k += 1
        h = round(k / time[-1], 1)

        h = round(h, 2)
        points = round(len(time) / (max(time) * h))

        return h, points



if __name__ == '__main__':

    #file = "C:/Users/Пользователь/Desktop/Тест/Циклическое трехосное нагружение/Архив/19-1/Косинусное значение напряжения.txt"
    file = "Z:/МДГТ - Механика/6. Циклика/499-20 с прибора/1-7/Косинусное значения напряжения.txt"
    #a = ModelTriaxialCyclicLoading()
    #a.set_test_data(ModelTriaxialCyclicLoading.open_wille_log(file))
    #print(a.get_test_results())
    #a.plotter()

    #file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    #file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1375\Test\Test.1.log"
    #a = ModelTriaxialStaticLoading()
    #a.set_test_data(openfile(file)["DeviatorLoading"])
    #a.plotter()

    #a.plotter()

    """a = ModelTriaxialCyclicLoading()
    a.set_test_data(ModelTriaxialCyclicLoading.open_geotek_log("C:/Users/Пользователь/Desktop/Опыты/264-21 П-57 11.7 Обжимающее давление = 120.txt"))
    a.plotter()"""

    a = ModelTriaxialCyclicLoadingSoilTest()
    params = {'E': 50000.0, 'c': 0.023, 'fi': 8.2,
     'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'depth': 9.8, 'Ip': 17.9,
     'Il': 0.79, 'K0': 1, 'groundwater': 0.0, 'ro': 1.76, 'balnost': 2.0, 'magnituda': 5.0, 'rd': '0.912', 'N': 1200,
     'MSF': '2.82', 'I': 2.0, 'sigma1': 96, 't': 22.56, 'sigma3': 96, 'ige': '-', 'Nop': 20, 'lab_number': '4-5',
     'data_phiz': {'borehole': 'rete', 'depth': 9.8,
                   'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'ige': '-',
                   'rs': 2.73, 'r': 1.76, 'rd': 1.23, 'n': 55.0, 'e': 1.22, 'W': 43.4, 'Sr': 0.97, 'Wl': 47.1,
                   'Wp': 29.2, 'Ip': 17.9, 'Il': 0.79, 'Ir': 6.8, 'str_index': 'l', 'gw_depth': 0.0, 'build_press': '-',
                   'pit_depth': '-', '10': '-', '5': '-', '2': '-', '1': '-', '05': '-', '025': 0.3, '01': 0.1,
                   '005': 17.7, '001': 35.0, '0002': 18.8, '0000': 28.1, 'Nop': 20}, 'test_type': 'Сейсморазжижение'}
    a.set_test_params(params)
    a.plotter()