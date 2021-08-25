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
        для нахождения начальных параметров в методе set_test_params().

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

from general.general_functions import define_qf, create_deviation_curve, current_exponent, step_sin, logarithm, sigmoida,\
    create_acute_sine_array, AttrDict, mirrow_element
from configs.plot_params import plotter_params

class ModelTriaxialCyclicLoading:
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
        plot_data = self.get_plot_data()

        if plot_data:
            figure = plt.figure(figsize = [9.3, 6])
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

            ax_deviator = figure.add_subplot(2, 2, 1)
            ax_deviator.set_xlabel("Число циклов N, ед.")
            ax_deviator.set_ylabel("Девиатор q, кПА")

            ax_strain = figure.add_subplot(2, 2, 2)
            ax_strain.set_xlabel("Число циклов N, ед.")
            ax_strain.set_ylabel("Относительная деформация $ε_1$, д.е.")

            ax_strain.set_ylim(plot_data["strain_lim"])


            ax_PPR = figure.add_subplot(2, 2, 3)
            ax_PPR.set_xlabel("Число циклов N, ед.")
            ax_PPR.set_ylabel("Приведенное поровое давление PPR, д.е.")

            ax_PPR.set_ylim(plot_data["PPR_lim"])


            ax_stresses = figure.add_subplot(2, 2, 4)
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
            self._test_result.fail_cycle = None
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
                       "Test_DynPorePress_kPa_value", "Test_DynVerticalDeformation_mm_value",]

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
            index_1, = np.where(read_data["Test_Dyn_halfcycles"] == 2)
            index_2, = np.where(read_data["Test_Dyn_halfcycles"] == 4)
            T = test_data["time"][index_2[0]] - test_data["time"][index_1[0]]
            test_data["frequency"], test_data["points"] = 1/T, len(test_data["time"][index_1[0]:index_2[0]])
            test_data["cycles"] = test_data["time"] * test_data["frequency"]
        else:
            pass

        return test_data

    @staticmethod
    def find_frequency(time, deviator):
        """Функция поиска частоты девиаторного нагружения"""
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
        deviator = deviator[index_1:]
        time = time[index_1:] - time[index_1]

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

class ModelTriaxialCyclicLoadingSoilTest(ModelTriaxialCyclicLoading):
    """Модель моделирования циклического нагружения
    Наследует обработчик и структуру данных из ModelTriaxialCyclicLoading

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_params() передать на ползунки
        Важный параметр - n_fail. Он отвечает за выбор метода построения PPR(в цикл или без разрушения), также
        определяет резкий рост амплитуды на кривой деформации

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.


        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта"""
    def __init__(self):
        super().__init__()

        # Переменная отвечает за то, чтобы первая четверть периода синусоиды была догрузка
        self._cosine = True

        self._draw_params = AttrDict({"deviator_deviation": None,
                                      "deviator_filter": None,

                                      "strain_max": None,
                                      "strain_slant": None,
                                      "strain_rise_after_fail": None,
                                      "strain_deviation": None,
                                      "strain_filter": None,
                                      "strain_E0": None,
                                      "strain_stabilization": None,

                                      "PPR_max": None,
                                      "PPR_slant": None,
                                      "PPR_rise_after_fail": None,
                                      "PPR_skempton": None,
                                      "PPR_deviation": None,
                                      "PPR_filter": None,
                                      "PPR_phase_offset": None})

        self._load_stage = AttrDict({"time": None,
                                            "strain": None,
                                            "deviator": None})

        self._test_params = AttrDict({"frequency": None,
                                      "points_in_cycle": None,
                                      "cycles_count": None,
                                      "n_fail": None,
                                      "sigma_1": None,
                                      "qf": None,
                                      "t": None,
                                      "sigma_3": None,
                                      "K0": None,
                                      "c": None,
                                      "fi": None,
                                      "E": None,
                                      "len_cycles": None,
                                      "deviator_start_value": None,
                                      "reverse": None})

    def set_test_params(self, params):
        """Функция принимает параметры опыта для дальнейших построений.
        n_fail моделируется из кривой CSR. Если нет разжижения - n_fail = None"""
        self._test_params.cycles_count = params.cycles_count
        if self._test_params.cycles_count < 5:
            self._test_params.cycles_count = 5

        self._test_params.n_fail = params.n_fail
        Mcsr = params.Mcsr

        self._test_params.sigma_1 = params.sigma_1
        self._test_params.t = params.t
        self._test_params.K0 = params.K0
        self._test_params.qf = params.qf
        self._test_params.sigma_3 = params.sigma_3
        self._test_params.physical = params.physical_properties
        self._test_params.c = params.c
        self._test_params.fi = params.fi
        self._test_params.E = params.E50
        self._test_params.frequency = params.frequency
        self._test_params.points_in_cycle = 20
        self._test_params.deviator_start_value = self._test_params.sigma_1 - self._test_params.sigma_3
        self._test_params.reverse = ModelTriaxialCyclicLoadingSoilTest.check_revers(self._test_params.sigma_1,
                                                                                     self._test_params.sigma_3,
                                                                                     2*self._test_params.t)

        try:
            self._test_params.qf = params.qf
            self._test_params.Kd = params.Kd
            self._test_params.deviator_start_value = 0
        except AttributeError:
            self._test_params.qf = 0
            self._test_params.deviator_start_value = self._test_params.sigma_1 - self._test_params.sigma_3
            self._test_params.Kd = None

        #self._test_params.n_fail, Mcsr = define_fail_cycle(self._test_params.cycles_count, self._test_params.sigma_1,
                                       #self._test_params.t, self._test_params.physical["Ip"],
                                       #self._test_params.physical["Il"], self._test_params.physical["e"])

        if self._test_params.n_fail:
            if self._test_params.n_fail > self._test_params.cycles_count - 5:
                self._test_params.n_fail = self._test_params.cycles_count - 5

        self._define_draw_params(Mcsr)
        self._test_modeling(params.Msf)
        self._test_processing()

    def get_data_for_vibration_creep(self):
        #print("data from math model", len(self._test_data.time), len(self._test_data.deviator))
        return {
            "strain": self._test_data.strain,
            "deviator": self._test_data.deviator,
            "time": self._test_data.time,
            "frequency": self._test_params.frequency,
            "start_dynamic": len(self._load_stage.deviator)
        }

    def get_draw_params(self):
        """Считывание параметров отрисовки(для передачи на слайдеры)"""
        strain_params = {
            "strain_max": {"value": self._draw_params.strain_max, "borders": [0, 0.08]},
            "strain_slant": {"value": self._draw_params.strain_slant,
                              "borders": [self._draw_params.strain_slant/5, int(self._test_params.cycles_count*0.9)]},
            "strain_E0": {"value": self._draw_params.strain_E0,
                           "borders": [self._draw_params.strain_E0/5, self._draw_params.strain_E0*5]},
            "strain_rise_after_fail": {"value": self._draw_params.strain_rise_after_fail,
                           "borders": [self._draw_params.strain_rise_after_fail/3,
                                       self._draw_params.strain_rise_after_fail*3]},
            "strain_stabilization": {"value": self._draw_params.strain_stabilization,
                           "borders": [0, 0.5]},
        }

        PPR_params = {
            "PPR_n_fail": self._test_params.n_fail,
            "PPR_max": {"value": self._draw_params.PPR_max, "borders": [0.1, 1.1]},
            "PPR_slant": {"value": self._draw_params.PPR_slant,
                          "borders": [self._draw_params.PPR_slant/5, self._draw_params.PPR_slant*5]},
            "PPR_skempton": {"value": self._draw_params.PPR_skempton,
                          "borders": [self._draw_params.PPR_skempton/5, self._draw_params.PPR_skempton*5]},
            "PPR_rise_after_fail": {"value": self._draw_params.PPR_rise_after_fail,
                          "borders": [self._draw_params.PPR_rise_after_fail/5, self._draw_params.PPR_rise_after_fail*3]},
            "PPR_phase_offset": {"value": self._draw_params.PPR_phase_offset,
                          "borders": [self._draw_params.PPR_phase_offset/5, self._draw_params.PPR_phase_offset*5]}
        }

        cycles_count_params = {
            "cycles_count": {"value": self._test_params.cycles_count,
                             "borders": [3, self._test_params.cycles_count if self._test_params.cycles_count > 5 else 5]}
        }

        return strain_params, PPR_params, cycles_count_params

    def set_strain_params(self, strain_params):
        """Установка пользовательских параметров отрисовки деформации"""
        self._draw_params.strain_max = strain_params["strain_max"]
        self._draw_params.strain_stabilization = strain_params["strain_stabilization"]
        self._draw_params.strain_slant = strain_params["strain_slant"]
        self._draw_params.strain_E0 = strain_params["strain_E0"]
        self._draw_params.strain_rise_after_fail = strain_params["strain_rise_after_fail"]
        self._modeling_strain()
        self._test_processing()

    def get_cycles_count(self):
        return self._test_params.cycles_count

    def set_cycles_count(self, cycles_count):
        self._test_params.cycles_count = int(cycles_count)

        if self._test_params.n_fail:
            if self._test_params.n_fail >= int(0.8*cycles_count):
                self._test_params.n_fail = int(0.8*cycles_count)

        self._define_draw_params()
        self._test_modeling()
        self._test_processing()

    def set_PPR_params(self, PPR_params):
        """Установка пользовательских параметров отрисовки PPR"""
        self._test_params.n_fail = int(PPR_params["PPR_n_fail"])
        if self._test_params.n_fail == self._test_params.cycles_count:
            self._test_params.n_fail = None
        self._draw_params.PPR_max = PPR_params["PPR_max"]
        self._draw_params.PPR_slant = PPR_params["PPR_slant"]
        self._draw_params.PPR_skempton = PPR_params["PPR_skempton"]
        self._draw_params.PPR_rise_after_fail = PPR_params["PPR_rise_after_fail"]
        self._draw_params.PPR_phase_offset = PPR_params["PPR_phase_offset"]

        self._modeling_PPR()
        i, Msf = ModelTriaxialCyclicLoadingSoilTest.intercept_CSL(self._test_data.deviator / 2, self.critical_line)
        if Msf:
            if self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05 / Msf, 0.06 / Msf)
            self._modeling_strain()
        else:
            if self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05, 0.06)
            self._modeling_strain()
        self._test_processing()

    def generate_log_file(self, file_path, post_name=None):
        ModelTriaxialCyclicLoadingSoilTest.generate_willie_log_file(file_path, self._test_data.deviator,
                                                                    self._test_data.PPR, self._test_data.strain,
                                                                    self._test_params.frequency,
                                                                    self._test_params.cycles_count,
                                                                    self._test_params.points_in_cycle,
                                                                    self._test_data.setpoint,
                                                                    self._test_data.cell_pressure,
                                                                    self._test_params.physical.Ip,
                                                                    post_name)

    def _define_draw_params(self, Mcsr=None):
        """Определение параметров отрисовки графиков.
        Eсли грунт не разжижился, ассимптота PPR моделируется через коэффициент запаса(отношение текущего CSR к
        максимальному)
        Ассимптота деформаций моделируется через p-t координаты через коэффициент запаса относительно кривой
        критического состояния. В случае реверсного нагружения ассимпота близка к 0"""

        # Погрешность девиатора и коэффициент сгрлаживания девиатора
        self._draw_params.deviator_deviation = 1
        self._draw_params.deviator_filter = 0.5

        # Параметр, показывающий наличие реверсного нагружения
        if self._test_params.reverse:
            self._draw_params.strain_max = np.random.uniform(0, 0.005)
        else:
            self._draw_params.strain_max = np.random.uniform(0.02, 0.04)

        # Наклон графика деформации
        if self._test_params.cycles_count > 300:
            self._draw_params.strain_slant = np.random.uniform(0.3, 0.5)*self._test_params.cycles_count
        else:
            self._draw_params.strain_slant = self._test_params.cycles_count * np.random.uniform(0.7, 0.8)

        # Значение начального модуля деформации. Амплитуда деформации рассчитывется как амплитуда девиатора деленая
        # на значение модуля
        self._draw_params.strain_E0 = ModelTriaxialCyclicLoadingSoilTest.define_E0(self._test_params.physical.Il,
                                                self._test_params.E, self._test_params.t*2, \
                                    define_qf(self._test_params.sigma_3, self._test_params.c , self._test_params.fi))
        # Параметр, отвечающий за рост деформации после цикла разрушения
        self._draw_params.strain_rise_after_fail = np.random.uniform(2, 3)

        # Стабилизация деформации к ассимптоте
        self._draw_params.strain_stabilization = 0.1

        # Погрешность и коэффициент сглаживания
        self._draw_params.strain_deviation = 0.0001
        self._draw_params.strain_filter = 0.5

        # Ассимптота графика PPR. Если есть разрушение - не учитывается
        if Mcsr:
            self._draw_params.PPR_max = 1/Mcsr
        else:
            self._draw_params.PPR_max = 4 * self._test_params.t * np.random.uniform(0.3, 0.5) / self._test_params.sigma_3 \
                                        + np.random.uniform(0.2, 0.3)

        # Наклон графика PPR. Если есть разрушение - не учитывается
        if self._test_params.cycles_count > 200:
            self._draw_params.PPR_slant = np.random.uniform(100, 200)
        else:
            self._draw_params.PPR_slant = self._test_params.cycles_count * np.random.uniform(0.7, 0.8)
        # Динамический коэффициент скемптона. Амплитуда PPR = PPR_skempton*_test_params.t/ _test_params.sigma_3
        self._draw_params.PPR_skempton = ModelTriaxialCyclicLoadingSoilTest.dependence_skempton_Il_frequency(self._test_params.physical.Il,
                                                                          self._test_params.frequency)/3
        # Параметр, отвечающий за рост деформации после цикла разрушения
        self._draw_params.PPR_rise_after_fail = np.random.uniform(0.8, 1)
        # Погрешность и коэффициент сглаживания
        self._draw_params.PPR_deviation = 0.01
        self._draw_params.PPR_filter = 0.05
        self._draw_params.PPR_phase_offset = ModelTriaxialCyclicLoadingSoilTest.initial_PPR_phase_offset(self._test_params.physical.Il,
                                                                      self._test_params.frequency)
        if self._test_params.n_fail:
            fail_cycle = self._test_params.n_fail
            self._draw_params.strain_slant = fail_cycle*np.random.uniform(0.6, 0.7)
        else:
            fail_cycle = self._test_params.cycles_count

            if fail_cycle > 300:
                self._draw_params.strain_slant = np.random.uniform(0.5, 0.6)*self._test_params.cycles_count
            else:
                self._draw_params.strain_slant = fail_cycle*np.random.uniform(0.5, 0.6)

    def _modeling_deviator(self):
        """Функция моделирования девиаторного нагружения"""
        # Массив setpoint - идеальная кривая, к которой стремится пид-регулятор
        if self._cosine:
            self._test_data.setpoint = ModelTriaxialCyclicLoadingSoilTest.create_deviator_array(self._test_data.cycles[len(self._load_stage.deviator):] - self._test_data.cycles[len(self._load_stage.deviator)],
                                                                                                2 * self._test_params.t,
                                                                                                self._test_params.deviator_start_value,
                                                                                                fail_cycle=self._test_params.n_fail,
                                                                                                points=self._test_params.points_in_cycle,
                                                                                                phase_shift=0.5*np.pi)

            self._test_data.setpoint = np.hstack((self._load_stage.deviator + self._test_params.deviator_start_value,
                                                self._test_data.setpoint +
                                                self._test_params.qf/2))
        else:
            self._test_data.setpoint = ModelTriaxialCyclicLoadingSoilTest.create_deviator_array(self._test_data.cycles,
                                                                                                2 * self._test_params.t,
                                                                                                self._test_params.deviator_start_value,
                                                                                                fail_cycle=self._test_params.n_fail,
                                                                                                points=self._test_params.points_in_cycle)

        # Создадим массив девиаторного нагружения
        self._test_data.deviator = self._test_data.setpoint + np.random.uniform(-self._draw_params.deviator_deviation,
                                                                                    self._draw_params.deviator_deviation,
                                                                                    self._test_params.len_cycles)

        #self._test_data.deviator = ndimage.gaussian_filter(self._test_data.deviator, self._draw_params.deviator_filter,
                                                         #order=0)

    def _modeling_strain(self):
        """Функция моделирования вертикальной деформации

        Логика работы:
        - Изначально задается массив E. Он незначительно падает до точки разрушения, после чего начинает подать
         значительно. Функция нелинейная, с помощью E моделируется амплитуда размаха деформации.

         - Функция деформации задается через логарифм. Это позволяет выходить на прямую линию при юольшом числе
         циклов"""
        # Создадим массив моделя E. Он отвечает за рост амплитуды
        if self._cosine:
            E_module = ModelTriaxialCyclicLoadingSoilTest.create_E_module_array(self._test_data.cycles[len(self._load_stage.strain):] - self._test_data.cycles[len(self._load_stage.strain)],
                                                                                self._draw_params.strain_E0,
                                                                                (-0.3 * self._draw_params.PPR_max) + 1,
                                                                                fail_cycle=self._test_params.n_fail,
                                                                                reverse=self._test_params.reverse,
                                                                                rise_after_fail=self._draw_params.strain_rise_after_fail)
            # Создадим массив вертикальной деформации
            self._test_data.strain = ModelTriaxialCyclicLoadingSoilTest.create_strain_array(
                self._test_data.cycles[len(self._load_stage.strain):] - self._test_data.cycles[len(self._load_stage.strain)],
                2 * self._test_params.t, E_module, self._draw_params.strain_max, self._draw_params.strain_slant,
                phase_shift=np.random.uniform(0.501, 0.505)*np.pi, stabilization=self._draw_params.strain_stabilization)
            self._test_data.strain -= self._test_data.strain[0]

            self._test_data.strain = np.hstack((self._load_stage.strain,
                                                self._test_data.strain + self._load_stage.strain[-1]))

            self._test_data.strain += np.random.uniform(-self._draw_params.strain_deviation,
                                                        self._draw_params.strain_deviation,
                                                        self._test_params.len_cycles) + \
                                      create_deviation_curve(self._test_data.cycles,
                                                             self._draw_params.strain_max / 150, (1, 0.1),
                                                             points=self._test_params.cycles_count) + \
                                      create_deviation_curve(self._test_data.cycles,
                                                             self._draw_params.strain_max / 80, (1, 0.1),
                                                             np.random.uniform(8, 15))

        else:
            E_module = ModelTriaxialCyclicLoadingSoilTest.create_E_module_array(
                self._test_data.cycles,
                self._draw_params.strain_E0,
                (-0.3 * self._draw_params.PPR_max) + 1,
                fail_cycle=self._test_params.n_fail,
                reverse=self._test_params.reverse,
                rise_after_fail=self._draw_params.strain_rise_after_fail)
            # Создадим массив вертикальной деформации
            self._test_data.strain = ModelTriaxialCyclicLoadingSoilTest.create_strain_array(
                self._test_data.cycles,
                2 * self._test_params.t,
                E_module,
                self._draw_params.strain_max,
                self._draw_params.strain_slant,
                phase_shift=np.random.uniform(0.005, 0.02) * np.pi, stabilization=self._draw_params.strain_stabilization)
            self._test_data.strain += np.random.uniform(-self._draw_params.strain_deviation,
                                                        self._draw_params.strain_deviation,
                                                        self._test_params.len_cycles) + \
                                      create_deviation_curve(self._test_data.cycles,
                                                             self._draw_params.strain_max / 40, (1, 0.1),
                                                             points=self._test_params.cycles_count) + \
                                      create_deviation_curve(self._test_data.cycles,
                                                             self._draw_params.strain_max / 25, (1, 0.1),
                                                             np.random.uniform(8, 15))

        #self._test_data.strain = np.hstack((self._load_stage.strain, self._test_data.strain)) [len(self._load_stage.time):]
        # Накладываем погрешности на вертикальную деформацию

        self._test_data.strain = ndimage.gaussian_filter(self._test_data.strain, self._draw_params.strain_filter,
                                                         order=0)
        self._test_data.strain[0] = 0

    def _modeling_PPR(self):
        """Функция моделирования PPR

        Логика работы:
        Массив PPR может строиться 2мя методами. В цикл разрушения, если он определен, иои с помощь ассимптоты и
        наклона"""
        if self._cosine:
            PPR = ModelTriaxialCyclicLoadingSoilTest.create_PPR_array(self._test_data.cycles[len(self._load_stage.deviator):] - self._test_data.cycles[len(self._load_stage.deviator)] , self._test_params.t,
                                                       self._draw_params.PPR_skempton,
                                                       self._test_data.cell_pressure[len(self._load_stage.deviator):], self._draw_params.PPR_max,
                                                       self._draw_params.PPR_slant,
                                                       self._draw_params.PPR_phase_offset, self._draw_params.PPR_deviation,
                                                       ModelTriaxialCyclicLoadingSoilTest.check_revers(self._test_params.sigma_1,
                                                                                                       self._test_params.sigma_3,
                                                                    2 * self._test_params.t), self._test_params.n_fail,
                                                                                       self._draw_params.PPR_rise_after_fail)

            self._test_data.PPR = np.hstack((np.random.uniform(-0.003, 0.003, len(self._load_stage.deviator)), PPR))

        else:
            self._test_data.PPR = ModelTriaxialCyclicLoadingSoilTest.create_PPR_array(
                self._test_data.cycles, self._test_params.t,
                self._draw_params.PPR_skempton,
                self._test_data.cell_pressure, self._draw_params.PPR_max,
                self._draw_params.PPR_slant,
                self._draw_params.PPR_phase_offset, self._draw_params.PPR_deviation,
                ModelTriaxialCyclicLoadingSoilTest.check_revers(self._test_params.sigma_1,
                                                                self._test_params.sigma_3,
                                                                2 * self._test_params.t), self._test_params.n_fail,
                self._draw_params.PPR_rise_after_fail)

        self._test_data.PPR[0] = 0

        self._test_data.mean_effective_stress = np.array(
            ((self._test_data.cell_pressure * (1 - self._test_data.PPR)) * 3 + self._test_data.deviator) / 3)

        self._test_data.mean_effective_stress = (self._test_data.deviator + self._test_data.cell_pressure * (2 - 3*self._test_data.PPR))/3

    def _test_modeling(self, Msf=None):
        """Функция моделирования опыта"""
        self._test_data.cycles = np.linspace(0, self._test_params.cycles_count,
                                             self._test_params.points_in_cycle * self._test_params.cycles_count + 1)
        #self._test_data.time = self._test_data.cycles / self._test_params.frequency
        # Этап нагружения
        if self._cosine:
            self._load_stage.time, self._load_stage.strain, self._load_stage.deviator = ModelTriaxialCyclicLoadingSoilTest.dev_loading(
                define_qf(self._test_params.sigma_3, self._test_params.c, self._test_params.fi),
                self._test_params.E, self._test_params.qf/2 + 2 * self._test_params.t, frequency=self._test_params.frequency)
            np.array(self._load_stage.time)
            #self._load_stage.deviator += self._test_params.deviator_start_value
            self._test_data.cycles = np.hstack((np.array(self._load_stage.time)*self._test_params.frequency,
                                                self._test_data.cycles + self._load_stage.time[-1]*self._test_params.frequency))
            #self._test_data.time = np.hstack((self._load_stage.time, self._test_data.time + self._load_stage.time[-1]))

            #self._test_data.cycles = np.hstack((np.linspace(0, 0.25, len(self._load_stage.time)),
                                                #self._test_data.cycles[int(self._test_params.points_in_cycle/4):]))

        self._test_data.time = self._test_data.cycles/self._test_params.frequency


        """self._test_data.cycles = np.hstack((self._load_stage.time * self._test_params.frequency,
                                            np.arange(self._load_stage.time[-1] * self._test_params.frequency,
                                                      self._test_params.cycles_count + 1 / self._test_params.cycles_count +
                                                      self._load_stage.time[-1] * self._test_params.frequency,
                                                      1 / self._test_params.points_in_cycle)))"""

        self._test_params.len_cycles = len(self._test_data.cycles)


        self._test_data.cell_pressure = ModelTriaxialCyclicLoadingSoilTest.create_cell_press_willie_array(self._test_params.sigma_3, self._test_data.cycles,
                                                                self._test_params.frequency)
        self._modeling_deviator()
        self._modeling_PPR()

        if not Msf:
            Msf = ModelTriaxialCyclicLoadingSoilTest.define_Msf(
                self.c, self.fi, 1/self._test_data.PPR[-1], self.sigma_3, self.sigma_1, self.physical.e,
                self.physical.Il, self.qf, self.t)

        if self._test_params.Kd:
            if self._test_params.Kd >= 0.9:
                k = 1
            else:
                k = 1 + (1 - self._test_params.Kd) * 1.2
            self._draw_params.strain_max = self._load_stage.strain[-1] * (1 - self._test_params.Kd) * k

        #elif self._test_params.reverse:
            #self._draw_params.strain_max = np.random.uniform(0, 0.005)
        else:
            self._draw_params.strain_max = np.random.uniform(0.05 / Msf, 0.06 / Msf)

        self._modeling_strain()

        """i, Msf = ModelTriaxialCyclicLoadingSoilTest.intercept_CSL(self._test_data.deviator/2, self.critical_line)
        if Msf:
            if self._test_params.Kd:
                if self._test_params.Kd >= 0.9:
                    k = 1
                else:
                    k = 1 + (1 - self._test_params.Kd) * 1.2
                self._draw_params.strain_max = self._load_stage.strain[-1] * (1 - self._test_params.Kd) * k

            elif self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05 / Msf, 0.06 / Msf)
            self._modeling_strain()
        else:
            if self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05, 0.06)
                self._modeling_strain()"""

    def _critical_line(self):
        """Построение линии критического разрушения Мора-Кулона в t-p осях"""
        c = self._test_params.c * 1000
        fi = np.deg2rad(self._test_params.fi)
        k = (6 * np.sin(fi) / (3 - np.sin(fi)))
        self.critical_line = c + 0.5 * k * self._test_data.mean_effective_stress

    @staticmethod
    def critical_line(c, fi, mean_effective_stress):
        c = c * 1000
        fi = np.deg2rad(fi)
        k = (6 * np.sin(fi) / (3 - np.sin(fi)))
        return c + 0.5 * k * mean_effective_stress

    @staticmethod
    def define_Msf(c, fi, Mcsr, sigma_3, sigma_1, e, Il, qf, t):
        if (sigma_1 - sigma_3) <= 1.5*t:
            return np.round(np.random.uniform(100, 500), 2)

        max_deviator = sigma_1 - sigma_3 + 2*t
        if Mcsr:
            critical = ModelTriaxialCyclicLoadingSoilTest.critical_line(c, fi, (1 - 1/Mcsr)*max_deviator)
            Msf = critical/max_deviator
        else:
            Msf = 1
        #print("Нагрузка ", Msf)
        Msf *= sigmoida(mirrow_element(2*t/qf, 0.5), 0.5, 0.5, 0.5, 1.5)
        #print("циклы ", Msf)
        Msf *= sigmoida(mirrow_element(e, 0.5), 0.7, 0.5, 1, 1.5)
        #print("е ", Msf)
        if Il:
            Msf *= sigmoida(mirrow_element(Il, 0.5), 0.7, 0.5, 1, 1.5)
        else:
            Msf *= sigmoida(mirrow_element(np.random.uniform(-0.1, 0.3), 0.5), 0.7, 0.5, 1, 1.5)
        #print("Il ", Msf)

        if Msf <= 0.7:
            Msf = np.random.uniform(0.6, 0.8)

        return np.round(Msf, 2)

    @staticmethod
    def influence_of_frequency_on_strain(frequency) -> float:
        """коэффициент отвечает за рост деформации с увеличением частоты"""
        return 1 + 0.003 * frequency

    @staticmethod
    def stabilization_logarithm(x, amplitude, x85, stabilization_ratio) -> np.array:
        """Стабилизированный логарифм - выходит на прямую"""
        y = logarithm(x, amplitude, x85) - logarithm(x, amplitude * stabilization_ratio, int(0.9 * x[-1]))
        y *= (amplitude / y[-1])
        return y

    @staticmethod
    def intercept_CSL(t, CSL) -> tuple:
        """Поиск точки пересечения критической линии Мора кулона"""
        for i in range(len(t)):
            if t[i] >= CSL[i]:
                return [i, None]

        index_min = np.argmin(CSL - t)

        Msf = CSL[index_min] / t[index_min]

        return [None, Msf if Msf > 0.9 else np.random.uniform(0.85, 0.95)]

    @staticmethod
    def create_deviator_array(x, amplitude, offset, fail_cycle=False, phase_shift=0, points=20) -> np.array:
        """Создаем массив девиаторного нагружения"""
        if fail_cycle:
            amplitude_first_area = np.linspace(amplitude, amplitude, fail_cycle * points)
            center_sigmoida_second_area = ((x[-1] - x[fail_cycle * points]) / 2) + x[fail_cycle * points]

            amplitude_second_area = sigmoida(x[fail_cycle * points:], amplitude * 0.1, center_sigmoida_second_area,
                                             amplitude * 0.1 / 2, (x[-1] - center_sigmoida_second_area) * 2)

            amplitude_second_area -= [amplitude_second_area[0] - amplitude]

            amplitude = np.hstack((amplitude_first_area, amplitude_second_area))

        return amplitude * np.sin(x * 2 * np.pi + phase_shift) + offset

    @staticmethod
    def create_E_module_array(x, val, degradation_percent, fail_cycle=None, reverse=False, rise_after_fail=None):
        """Создаем массив модуля деформации грунта
        Входные параметры: x - массив циклов нагружения
                           val - начальное значение модуля деформации
                           degradation_percent - на сколько диградирует модуль в конце. задается долями единицы
                           fail_cycle - цикл разрушения"""
        def without_fail(x, val, degradation_percent, x_95):
            return val - current_exponent(x, val * (1 - degradation_percent), x_95, offset=0)

        def create_amp(x, k, reverse):
            """Функция для снижения амплитуды в одну сторону"""
            k = np.linspace(k[0], k[1], len(x))
            if reverse:
                return k * np.sin(x * 2 * np.pi + np.pi) + (1 + k)
            else:
                return k * np.sin(x * 2 * np.pi) + (1 + k)

        if fail_cycle and fail_cycle < x[-1] - 1:
            i_f, = np.where(x > fail_cycle)
            i_fail = i_f[0]
            #amp_fail, = np.where(x > fail_cycle + 50)
            #amp_fail = amp_fail[0]
            until_fail = without_fail(x[:i_fail], val, degradation_percent, np.random.uniform(0.8, 0.95) * x[-1])
            xc = x[i_fail] + (x[-1] - x[i_fail]) * 0.5
            shape = x[-1] - x[i_fail]
            ost = np.random.uniform(2000, 3000)
            if until_fail[-1] <= ost:
                y = without_fail(x, val, degradation_percent*3, np.random.uniform(0.8, 0.95) * x[-1])
                y*= np.hstack((1 / create_amp(x, [0, rise_after_fail/3], reverse)))
            else:
                amp = (until_fail[-1] - ost) / 2
                after_fail = -step_sin(x[i_fail:], amp, xc, shape) + until_fail[-1] - amp

                y = np.hstack((until_fail, after_fail))
                y *= np.hstack((np.full(i_fail, 1),
                                   1 / create_amp(x[i_fail:], [0, rise_after_fail], reverse)))

            return y
        else:
            return without_fail(x, val, degradation_percent, np.random.uniform(0.5, 0.7) * x[-1])

    @staticmethod
    def create_strain_array(x, deviator_amplitude, E_module, strain_max, x_85, phase_shift=0, stabilization=0):
        """Создаем массив деформаций"""
        strain_amplitude = deviator_amplitude / E_module

        return np.array(strain_amplitude * np.sin(x * 2 * np.pi + phase_shift)) + \
               ModelTriaxialCyclicLoadingSoilTest.stabilization_logarithm(x, strain_max, x_85, stabilization)

    @staticmethod
    def dependence_PPR_phase_offset_count_cycles(cycles_count):
        """Находим начальное смещения фазы от количества циклов"""
        a = np.pi / 2
        return sigmoida(cycles_count, 0.15 * a, 5000, 0.15 * a, 20000)

    @staticmethod
    def create_PPR_phase_offset_array(x, phase_offset):
        """Строит массив смещения фазы от количества циклов"""
        cycles_count = int(max(x))
        half_of_cycles_count = int(max(x) / 2)
        amp = ModelTriaxialCyclicLoadingSoilTest.dependence_PPR_phase_offset_count_cycles(int(max(x))) / 2
        return sigmoida(x, amp, half_of_cycles_count, phase_offset + amp, cycles_count)

    @staticmethod
    def create_PPR_array(x, tau, skempton, sigma3, PPR_max, PPR_slant, offset, PPR_deviation, check_reverse,
                                 n_fail=None, rise_after_fail=None):
        """Создаем массив PPR"""
        # Смещение фаз с числом циклов
        phase_offset_array = ModelTriaxialCyclicLoadingSoilTest.create_PPR_phase_offset_array(x, offset)

        def current_exponent_PPR(x, amplitude, x_fail):
            """Функция построения экспоненты, которая строится в точку разжижения
                Входные параметры: x - значение или массив абсцисс,
                                   amplitude - значение верхней асимптоты,
                                   x_95 - значение x, в котором функция достигнет значения 0.95 от ассимптоты"""
            k = -np.log(-(1 / amplitude) + 1) / x_fail
            y = amplitude * (-np.e ** (-k * x) + 1)
            return y

        # Верхняя ограничевающая функция
        if n_fail:
            PPR_max = np.random.uniform(1.05, 1.15)
            PPR_exp = current_exponent_PPR(x, PPR_max, n_fail)

            i1, = np.where(x > n_fail - 1)
            i2, = np.where(x > n_fail + 1)

            try:
                PPR_exp += np.hstack(
                    (create_deviation_curve(x[:i1[0]], PPR_max / 30, (1, 0.1), np.random.uniform(6, 12),
                                            "zero_diff"), np.zeros(i2[0] - i1[0]),
                     create_deviation_curve(x[i2[0]:], PPR_max / 100, (1, 1), (len(x) - i2[0]) / 200,
                                            "zero_diff")))
            except:
                PPR_exp += np.hstack(
                    (create_deviation_curve(x[:i1[0]], PPR_max / 30, (1, 0.1), np.random.uniform(6, 12),
                                            "zero_diff"), np.zeros(len(x) - i1[0])))
            PPR_exp += np.hstack((create_deviation_curve(x[:i1[0]], PPR_max / 50, (1, 0.1), i1[0] / 5, "zero_diff"),
                                  np.zeros(len(x) - i1[0])))

        else:
            PPR_exp = current_exponent(x, PPR_max, PPR_slant)
            PPR_exp += create_deviation_curve(x, PPR_max / 30, (1, 0.1), np.random.uniform(6, 12), "zero_diff")
            PPR_exp += create_deviation_curve(x, PPR_max / 50, (1, 0.1), len(x) / 5, "zero_diff")

        # Амплитуда
        # Максисальное значение амплитуды
        amplitude = 2 * tau * skempton / sigma3
        # На начальных циклах амплитуда мала, потом по экспоненте растет до максимального значения
        initial_PPR_amplitude = np.random.uniform(0.6, 0.7)
        if x[-1] > 300:
            amplitude_exp = initial_PPR_amplitude + current_exponent(x, 1 - initial_PPR_amplitude,
                                                                     np.random.uniform(180, 250))
        else:
            amplitude_exp = initial_PPR_amplitude + current_exponent(x, 1 - initial_PPR_amplitude,
                                                                     x[-1] / np.random.uniform(1.3, 1.5))
        amplitude *= amplitude_exp

        if n_fail:
            i_fail, = np.where(x >= n_fail+1)
            i_fail = i_fail[0]
            rise = rise_after_fail * amplitude[i_fail] / 2

            center_sigmoida = (x[-1] - x[i_fail]) / 2 + x[i_fail]
            amplitude += sigmoida(x, rise, (x[-1] - x[i_fail]) / 2 + x[i_fail], rise / 2,
                                  (x[-1] - center_sigmoida) * 2)

            amplitude += create_deviation_curve(x, max(amplitude) / 20, (1, 0.1), np.random.uniform(20, 30),
                                                "zero_diff")

            if check_reverse:
                k = np.hstack((np.linspace(0.8, 0.7, i_fail), np.linspace(0.7, 0.5, len(x) - i_fail)))
            else:
                k = np.linspace(0.95, 0.8, len(x))
        else:
            k = np.linspace(1, 1, len(x))

        PPR_sin = PPR_exp + amplitude * create_acute_sine_array(x * 2 * np.pi + phase_offset_array,
                                                                k) - amplitude * PPR_exp / PPR_max

        # Девиации PPR
        PPR_sin += np.random.uniform(-PPR_deviation, 0, len(PPR_exp))

        if n_fail:
            PPR_sin *= 1/max(PPR_sin[i_fail:i_fail+20])
            for i in range(i_fail):
                if PPR_sin[i] >=1:
                    PPR_sin[i] = np.random.uniform(0.99, 0.9999)
            """for i in range(i_fail, len(x)):
                if PPR_sin[i] >=1:
                    PPR_sin[i] = np.random.uniform(0.99, 0.9999)"""


        return PPR_sin

    @staticmethod
    def check_revers(sigma1, sigma3, amplitude):
        q_cons = (sigma1 - sigma3)
        if q_cons - 0.7*amplitude < 0:
            return True
        else:
            return False

    @staticmethod
    def define_E0(Il, E50, q, qf):
        """Находит модуль деформации в петле
        Входные параметры: Il - индекс текучести
                           E50 - молдуль 50% прочности
                           q - текущая нагрузка
                           qf - прочность"""
        if not Il:
            Il = np.random.uniform(0, 0.3)

        def define_E_q_after_05(E50, q, qf):
            """Функция считает модуль в петле"""
            Emin = qf / 0.15
            if Emin <= 2000: Emin = np.random.uniform(1500, 2500)
            k = (E50 - Emin) / 0.5
            E = (E50 + 0.5 * k) - ((q / qf)) * k
            if E < Emin:
                return Emin
            else:
                return (E50 + 0.5 * k) - ((q / qf)) * k

        def define_E_q_until_05(E50, q, qf, depemdance_IL):
            """Функция считает модуль в петле"""
            k = (0.5 * E50 / 0.5) * depemdance_IL
            return (0.5 * k + E50) - ((q / qf)) * k

        if q >= 0.5 * qf:  # Модуль плавно деградирует к от Е50 к минимальному
            return define_E_q_after_05(E50, q, qf)
        else:
            if Il == "-":
                Il = np.random.uniform(-0.1, 0.05)
            return define_E_q_until_05(E50, q, qf, sigmoida(Il, 1.5, 0.5, 3.5, 1.2))

    @staticmethod
    def dependence_skempton_Il_frequency(Il, frequency):
        """Находит зависимость коэффициента скемптона от консистенции и частоты"""
        if Il == "-":
            dependence_skempton_Il = np.random.uniform(0.27, 0.3)
        else:
            dependence_skempton_Il = sigmoida(Il, 0.1, 0.5, 0.2, 1.2)

        dependence_skempton_frequency = sigmoida(mirrow_element(frequency, 5), 0.1, 5, 0.1, 10)

        return dependence_skempton_Il + dependence_skempton_frequency

    @staticmethod
    def initial_PPR_phase_offset(Il, frequency):
        """Находит зависимость начального смещения фаз в зависимости от Il  частоты"""
        if Il == "-":
            Il = np.random.uniform(-0.1, 0.05)
        a = np.pi / 2

        return sigmoida(Il, 0.03 * a, 0.5, 0.03 * a, 1.2) + sigmoida(frequency, 0.2 * a, 25, 0.2 * a, 50)

    @staticmethod
    def create_cell_press_willie_array(sigma3, x, frequency):
        """Строит массив давления в камере для вилли"""

        # Частота колебаний для давления в камере будет приметно 50 Гц
        cell_press_noise_frequency = 2 * np.pi * np.random.uniform(45, 55) / frequency

        cell_press_with_random = sigma3 - 0.5 + 0.5 * np.sin(x * cell_press_noise_frequency) + np.random.uniform(-0.5,
                                                                                                                 0,
                                                                                                                 len(x))
        cell_press_with_random_and_sensor = np.zeros(len(cell_press_with_random))
        for i in range(len(x)):
            cell_press_with_random_and_sensor[i] = cell_press_with_random[int(i - i % 5)]

        return cell_press_with_random

    @staticmethod
    def dev_loading(qf, E50, q_end, points_in_sec=1, frequency=None):
        """Функция построения частично заданного девиаторного нагружения"""
        # Проверка входных параметровfre
        if q_end > 0.8 * qf:
            qf = q_end * 2

        def hyp_deviator(strain, E50, qf):
            """Гиперболическая функция девиаторного нагружения"""
            Ei = ((2 * E50) / (2. - 1.))
            return strain * Ei / (1 + Ei * strain / qf)

        def hyp_strain(deviator, E50, qf):
            """Гиперболическая функция деформации от девиатора"""
            Ei = (2 * E50) / (2. - 1.)
            return deviator / (Ei * (1 - deviator / qf))

        def exp_deviator(strain, E50, qf):
            """Экспоненциальная функция девиаторного нагружения"""
            return -qf * (np.exp((np.log(0.5) / ((qf / 2) / E50)) * strain) - 1)

        def exp_strain(deviator, E50, qf):
            """Экспоненциальная функция деформации от девиатора"""
            return np.log(-deviator / qf + 1) / (np.log(0.5) / ((qf / 2) / E50))

        if frequency:
            end_time = 0.25/frequency
        else:
            end_time = q_end

        time = np.linspace(0, end_time, round(points_in_sec * q_end))
        a = 2#np.random.randint(0, 2)
        #strain = np.linspace(0, hyp_strain(q_end, E50, qf), len(time)) if a == 1 else np.linspace(0,
                                                                                                  #exp_strain(q_end, E50,
                                                                                                             #qf),
                                                                                                  #len(time))
        strain = hyp_strain(np.linspace(0, q_end, len(time)), E50, qf) if a == 1 else \
            exp_strain(np.linspace(0, q_end, len(time)), E50, qf)
        deviator = hyp_deviator(strain, E50, qf) if a == 1 else exp_deviator(strain, E50, qf)

        return time, strain, deviator

    @staticmethod
    def generate_willie_log_file(file_path, deviator, PPR, strain, frequency, N, points_in_cycle, setpoint, cell_pressure, Ip, post_name=None):
        """Сохранение текстового файла формата Willie.
                    Передается папка, массивы"""
        if post_name:
            p = os.path.join(file_path, "Косинусное значение напряжения " + post_name + ".txt")
        else:
            p = os.path.join(file_path, "Косинусное значение напряжения.txt")

        def wille_number_format(x):
            x = "{:.6f}".format(x)
            s = str(x)
            if s == "-0.000000":
                s = "0.000000"
            return s

        def make_string(data, i):
            s = ""
            for key in data:
                try:
                    s += wille_number_format(data[key][i]) + '\t'
                except ValueError:
                    s += data[key][i] + '\t'
            s += '\n'
            return (s)

        pore_pressure_after_consolidation = np.random.uniform(300, 500)
        if Ip == "-":
            time_initial = np.random.uniform(7200.000000, 18000.000000)  # Начальное время опыта
        else:
            time_initial = np.random.uniform(22000.000000, 55000.000000)  # Начальное время опыта
        force_initial = np.random.uniform(15, 40)
        piston_position_initial = np.random.uniform(5, 20)
        vertical_strain_initial = np.random.uniform(0, 0.001)
        diameter = np.random.uniform(38.001, 38.002, len(deviator))
        sample_area_initial = np.pi * (diameter[0] / 2) ** 2
        sample_area = np.pi * (diameter / 2) ** 2

        external_displacement_coefficient = np.random.uniform(50, 80)

        piston_area = 314.159265
        sample_height = round(np.random.uniform(75.970000, 76.000000), 5)

        time = np.round((np.arange(0, (N / frequency) + 1 / (points_in_cycle * frequency),
                                   1 / (points_in_cycle * frequency)) + time_initial), 4)

        data = {
            "Time": time,
            "point_number": range(1, len(deviator) + 1),
            "Time2": time,
            "External displacement": strain / external_displacement_coefficient,

            "Vertical force": deviator / (sample_area_initial / 10),
            "Vertical force (Gross value)": (deviator / (sample_area_initial / 10)) - force_initial,
            "Vertical force (Setpoint)": setpoint / (sample_area_initial / 10),

            "Piston position": np.round(((strain + vertical_strain_initial) * sample_height), 4),
            "Piston position (Gross value)": np.round(
                ((strain + vertical_strain_initial) * sample_height) - piston_position_initial, 4),
            "Piston position (Setpoint)": np.round(((strain + vertical_strain_initial) * sample_height), 4),

            "Cell volume change": ["0.000000" for _ in range(len(deviator))],

            "Sample height": [sample_height for _ in range(len(deviator))],

            "Pore pressure": (PPR * cell_pressure) + pore_pressure_after_consolidation,
            "Pore volume change (water)": ["0.000000" for _ in range(len(deviator))],
            "Backpressure": ["0.000000" for _ in range(len(deviator))],
            "Cell pressure": cell_pressure + pore_pressure_after_consolidation,
            "Cell pressure (Gross value)": cell_pressure + pore_pressure_after_consolidation,
            "Cell pressure (Setpoint)": [np.mean(cell_pressure + pore_pressure_after_consolidation) for _ in
                                         range(len(deviator))],

            "Sample area under isotropic conditions": sample_area,
            "Initial sample height under anisotropic conditions": [sample_height for _ in range(len(deviator))],
            "Settlement under anisotropic conditions": np.round(((strain * 76) / 500), 6),

            "Vertical strain": strain + vertical_strain_initial,
            "Sample surface area under anisotropic conditions": sample_area,
            "Vertical stress under anistropic conditions": (
                                                                       cell_pressure + pore_pressure_after_consolidation) + deviator,
            "Piston area": [piston_area for _ in range(len(deviator))],
            "Initial sample area": [sample_area_initial for _ in range(len(deviator))],
            "Drainage valve": ["True" for _ in range(len(deviator))],
            "Volume": ["86.192736" for _ in range(len(deviator))],
            "Sample Area under isotropic conditions": sample_area,
            "Diameter under isotropic conditions": np.random.uniform(38.001, 38.002, len(deviator)),
            "Vertical stress under isotropic conditions": (
                                                                      cell_pressure + pore_pressure_after_consolidation) + deviator,
            "Deviator": deviator,
            "Deviator(shearing)": deviator,
            "Axial displacement 1": ["0.000000" for _ in range(len(deviator))],
            "Axial displacement 2": ["0.000000" for _ in range(len(deviator))]
        }

        with open(p, "w") as file:
            file.write(
                "		Time	External displacement	Vertical force	Vertical force (Gross value)	Vertical force (Setpoint)	Piston position	Piston position (Gross value)	Piston position (Setpoint)	Cell volume change	Sample height	Pore pressure	Pore volume change (water)	Backpressure	Cell pressure	Cell pressure (Gross value)	Cell pressure (Setpoint)	Sample area under isotropic conditions	Initial sample height under anisotropic conditions	Settlement under anisotropic conditions	Vertical strain	Sample surface area under anisotropic conditions	Vertical stress under anistropic conditions	Piston area	Initial sample area	Drainage valve	Volume	Sample Area under isotropic conditions	Diameter under isotropic conditions	Vertical stress under isotropic conditions	Deviator	Deviator (shearing)	Axial displacement 1	Axial displacement 2" + '\n')
            file.write(
                "		s	mm	N	N	N	mm	mm	mm	ml	mm	kPa	ml	kPa	kPa	kPa	kPa	mm2	mm	mm	%	mm2	kPa	mm2	mm2	bool	ml	mm2	mm	kPa	kPa	kPa	mm	mm" + '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))
        file.close()

        return time[-1] + time_initial


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
    file = "C:/Users/Пользователь/Desktop/Опыты/264-21 П-57 11.7 Обжимающее давление = 120.txt"
    file = "C:/Users/Пользователь/Desktop/Опыты/718-20 PL20-Skv139 0.2  Обжимающее давление = 25.txt"
    a.set_test_data(ModelTriaxialCyclicLoading.open_geotek_log(file))
    a.plotter()"""

    a = ModelTriaxialCyclicLoadingSoilTest()
    params = {'E': 50000.0, 'c': 0.023, 'fi': 45,
     'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'depth': 9.8, 'Ip': 17.9,
     'Il': 0.79, 'K0': 1, 'groundwater': 0.0, 'ro': 1.76, 'balnost': 2.0, 'magnituda': 5.0, 'rd': '0.912', 'N':10,
     'MSF': '2.82', 'I': 2.0, 'sigma1': 100, 't': 10, 'sigma3': 100, 'ige': '-', 'Nop': 20, 'lab_number': '4-5',
     'data_phiz': {'borehole': 'rete', 'depth': 9.8,
                   'name': 'Глина легкая текучепластичная пылеватая с примесью органического вещества', 'ige': '-',
                   'rs': 2.73, 'r': 1.76, 'rd': 1.23, 'n': 55.0, 'e': 1.22, 'W': 43.4, 'Sr': 0.97, 'Wl': 47.1,
                   'Wp': 29.2, 'Ip': 17.9, 'Il': 0.79, 'Ir': 6.8, 'str_index': 'l', 'gw_depth': 0.0, 'build_press': '-',
                   'pit_depth': '-', '10': '-', '5': '-', '2': '-', '1': '-', '05': '-', '025': 0.3, '01': 0.1,
                   '005': 17.7, '001': 35.0, '0002': 18.8, '0000': 28.1, 'Nop': 20}, 'test_type': 'Сейсморазжижение',
                               "frequency": 3, "n_fail": None, "Mcsr": 5}
    a.set_test_params(params)
    a.plotter()