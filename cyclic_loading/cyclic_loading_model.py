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
    create_acute_sine_array, AttrDict, mirrow_element, create_json_file, read_json_file
from cyclic_loading.strangth_functions import define_t_rel
from configs.plot_params import plotter_params
from datetime import timedelta
from typing import Optional, Tuple
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from loggers.logger import app_logger
from singletons import statment

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
                                      "conclusion": None, # заключение о разжижаемости
                                      "damping_ratio": None, # коэффициент демпфирования
                                      't_max_static': None,
                                      't_max_dynamic': None,
                                      })

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
                    "PPR_lim": PPR_lim,
                    "damping_deviator": self._damping_deviator,
                    "damping_strain": self._damping_strain}

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

        if statment.general_parameters.test_mode == "Динамическая прочность на сдвиг":
            self._test_result.fail_cycle_criterion_strain = ModelTriaxialCyclicLoading.define_fail_cycle(
                self._test_data.cycles,
                (self._test_data.strain >= 0.10))
            self._test_result.fail_cycle_criterion_stress = ModelTriaxialCyclicLoading.define_fail_cycle(
                self._test_data.cycles,
                (self._test_data.mean_effective_stress <= 0))
            self._test_result.fail_cycle_criterion_PPR = ModelTriaxialCyclicLoading.define_fail_cycle(
                self._test_data.cycles,
                (self._test_data.PPR >= 0.95))
        else:
            self._test_result.fail_cycle_criterion_strain = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                              (self._test_data.strain >= 0.05))
            self._test_result.fail_cycle_criterion_stress = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                              (self._test_data.mean_effective_stress <= 0))
            self._test_result.fail_cycle_criterion_PPR = ModelTriaxialCyclicLoading.define_fail_cycle(self._test_data.cycles,
                                                                           (self._test_data.PPR >= 1))

        self._test_result.fail_cycle = min([i for i in [self._test_result.fail_cycle_criterion_strain,
                                                        self._test_result.fail_cycle_criterion_stress,
                                                        self._test_result.fail_cycle_criterion_PPR] if i], default=None)

        self._damping_strain = None
        self._damping_deviator = None

        try:
            self._test_result.damping_ratio, self._damping_strain, self._damping_deviator = \
                ModelTriaxialCyclicLoading.define_damping_ratio(
                self._test_data.strain, self._test_data.deviator, remove_plastic_strains=False)
            self._test_result.damping_ratio = np.round(self._test_result.damping_ratio, 2)
        except:
            pass

        #plt.plot(self._test_data.strain, self._test_data.deviator)
        #plt.fill(strain, deviator, color="tomato", alpha=0.5, zorder=5)
        #plt.show()

        if statment.general_parameters.test_mode == "Динамическая прочность на сдвиг":
            dyn_puasson = 0.2
            G = self._test_result.E_values[1] / (2 * (1 + dyn_puasson))
            self._test_result.gamma_critical = self._test_params.t / G

        if self._test_result.fail_cycle_criterion_stress or self._test_result.fail_cycle_criterion_PPR:
            self._test_result.conclusion = "Грунт разжижается"
        elif self._test_result.fail_cycle_criterion_strain:
            self._test_result.conclusion = "Грунт динамически неустойчив"
            self._test_result.fail_cycle = None
        else:
            self._test_result.conclusion = "Грунт не разжижается"



        u = np.round((self._test_result.max_PPR * statment[statment.current_test].mechanical_properties.sigma_3) / 1000, 2)

        parameters = self.get_test_parameters()

        self._test_result.t_rel_static = np.round(define_t_rel(
            c=statment[statment.current_test].mechanical_properties.c,
            fi=statment[statment.current_test].mechanical_properties.fi,
            sigma_3=parameters['sigma_3'] / 1000,
            sigma_1=parameters['sigma_1'] / 1000
        ), 3)


        if parameters['sigma_3'] / 1000 - u < 0:
            sigma_3_dyn = 0
            sigma_1_dyn = parameters['sigma_1'] / 1000 - parameters['sigma_3'] / 1000
        else:
            sigma_3_dyn = parameters['sigma_3'] / 1000 - u
            sigma_1_dyn = parameters['sigma_1'] / 1000 - u

        self._test_result.t_rel_dynamic = np.round(define_t_rel(
            c=statment[statment.current_test].mechanical_properties.c,
            fi=statment[statment.current_test].mechanical_properties.fi,
            sigma_3=sigma_3_dyn,
            sigma_1=sigma_1_dyn
        ), 3)

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
        test_data["mean_effective_stress"] = (test_data["deviator"] + test_data["cell_pressure"] * (2 - 3 * test_data["PPR"])) / 3
        try:
            processing_parameters = read_json_file("/".join(os.path.split(file_path)[:-1]) + "/processing_parameters.json")
            test_data["frequency"], test_data["points"] = processing_parameters["frequency"], processing_parameters["points_in_cycle"]
            test_data["cycles"] = test_data["time"] * test_data["frequency"]
            test_data["sigma_3"] = processing_parameters["sigma_3"]
            test_data["sigma_1"] = processing_parameters["sigma_1"]
            test_data["t"] = processing_parameters["t"]
            test_data["K0"] = processing_parameters["K0"]
        except (FileNotFoundError, KeyError):
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

    @staticmethod
    def define_damping_ratio(strain: np.ndarray, deviator: np.ndarray,
                             evaluate_on_first_cycles: Optional[int] = 0,
                             remove_plastic_strains: Optional[bool] = True,
                             plot: Optional[bool] = False) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Определяет коэффициент демпфирования по файлу опыта с динамического стабилометра.

        Определение коэффициента происходит путем построения осредненной петли гистерезиса и
        оценки поглощенной энергии и энергии деформации согласно [1]_

        По умолчанию расчет проводится с исключением пластических деформаций. Для проведения расчета
        с пластическими деформациями установить `remove_plastic_strains` = False.

        Для построения следующих графиков установить `plot` = True:
            1. деформации/девиатор + осредненная петля гистерезиса
            2. время/деформации + время/деформации без пластических

        Возвращает коэффициент демпфирования (damping_ratio), деформации (filer_strain) и
        девиатор (filer_deviator) осредненной петли.

        .. [1] Geotechnical earthquake engineering / Steven L. Kramer, стр. 568

        http://www.mkamalian.ir/Uploads/Books/GEE%20(K).pdf

        Parameters
        ----------
        strain : np.ndarray
            Массив деформаций
        deviator : np.ndarray
            Массив девиатора
        evaluate_on_first_cycles : int, optional
            Число первых циклов, на которых происходит вычисление. При =0 учитываются все циклы.
        remove_plastic_strains : bool, optional
            Флаг расчета без пластических деформаций: True - без, False - с
        plot : bool, optional
            Флаг построения графиков

        """

        assert len(deviator) > 1, "deviator should have more than 1 point"
        assert len(deviator) == len(strain), "strain and deviator is different in size"

        loops_indexes = ModelTriaxialCyclicLoading.separate_deviator_loops(deviator)

        if evaluate_on_first_cycles:
            loops_indexes = loops_indexes[:2 + evaluate_on_first_cycles]
            strain = strain[:loops_indexes[-1] + 1]
            deviator = deviator[:loops_indexes[-1] + 1]

        if remove_plastic_strains:
            try:
                strain = ModelTriaxialCyclicLoading.plastic_strains_remover(strain, deviator,
                                                                            loops_indexes=loops_indexes, plot=plot)
            except:
                pass

        mean_strain, mean_deviator = ModelTriaxialCyclicLoading.define_mean_loop(strain, deviator,
                                                                                 loops_indexes=loops_indexes)

        FILTER_RATIO = 10
        filer_deviator = ModelTriaxialCyclicLoading.array_smoother(mean_deviator, ratio=FILTER_RATIO)
        filer_strain = ModelTriaxialCyclicLoading.array_smoother(mean_strain, ratio=FILTER_RATIO)

        dissipated_energy = ModelTriaxialCyclicLoading.area(filer_strain, filer_deviator)
        strain_energy = abs(max(filer_strain)) ** 2 * (abs(max(filer_deviator)) / abs(max(filer_strain))) / 2
        damping_ratio = dissipated_energy / (4 * np.pi) / strain_energy * 100

        if plot:
            plt.figure()
            plt.plot(strain, deviator, label="Файл прибора")
            plt.plot(filer_strain, filer_deviator, label="Осредненные данные")
            plt.legend()
            plt.show()

        return damping_ratio, filer_strain, filer_deviator

    @staticmethod
    def plastic_strains_remover(strain: np.ndarray, deviator: np.ndarray, loops_indexes: np.ndarray = None,
                                plot: Optional[bool] = False) -> np.ndarray:
        """
        Удаляет из дефораций (`strain`) пластические деформации путем выделения тренда
        методом скользящего среднего.
        Девиатор (`deviator`) необходим для корректного определения петель (цикличности).
        Половина первого пропускаемого цикла (петля) заполняется нулями в массиве тренда --
        эта часть в исходных дефорациях останется на месте
        (см. алгорим декомпозиции временного ряда методом скользящего среднего).

        Для построения графиков время/деформации + время/деформации без пластических указать `plot`=True

        Возвращает деформации без тренда (длины `strain`)
        """
        if loops_indexes is None:
            loops_indexes = ModelTriaxialCyclicLoading.separate_deviator_loops(deviator)

        season = min([loops_indexes[i + 1] - loops_indexes[i] + 1 for i in range(len(loops_indexes) - 1)])
        season -= 1
        trend = ModelTriaxialCyclicLoading.trend_decomposition(strain, season)

        # Для того, чтобы корректно вычесть из деформаций их пластическую часть, массив с трендом необходимо дополнить
        # нулями с начала. Добавляемая длина будет соответствовать половине длины первого цикла
        removed_len = int(season / 2) if season % 2 == 0 else int((season - 1) / 2)
        strain_to_remove = np.hstack((np.zeros(removed_len), trend))

        if plot:
            plt.figure()
            _time = ModelTriaxialCyclicLoading.time_series(strain)
            plt.plot(_time, strain, '-.b', label='Деформации')
            plt.plot(_time, strain - strain_to_remove, 'r', label='Без пластических деформаций')
            plt.legend()
            plt.show()

        return strain - strain_to_remove

    @staticmethod
    def separate_deviator_loops(deviator: np.ndarray) -> np.ndarray:
        """Определяет петли в девиаторе и возвращает индексы в массиве, соответствующие началу каждой петли"""
        assert len(deviator) > 1, "deviator should have more than 1 point"
        smooth_array = ModelTriaxialCyclicLoading.array_filter(deviator)
        count, indexes = ModelTriaxialCyclicLoading.find_to_positive_zero_crossings(smooth_array)
        return np.array(indexes)

    @staticmethod
    def array_filter(x: np.ndarray) -> np.ndarray:
        """
        Применяет фильтр `Savitzky–Golay` к массиву данных с адаптируемым под длину массива окном

        https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter
        """
        assert len(x) > 1, "x should have more than 1 point"
        frame = int(2 * int(len(x) ** 0.5 / 2) + 1)
        #
        # С адаптицией выходит накладка - под файлы с прибора окно адаптируется плохо, вернее сказать, не правильно
        # Опыт показал, что окно должно быть длиной 21 или меньше, зависит от данных.
        #
        return savgol_filter(x, frame if frame < 21 else 21, 2)

    @staticmethod
    def find_to_positive_zero_crossings(x: np.ndarray) -> Tuple[int, list]:
        """
        Определяет сколько раз значения в массиве переходят со стороны
        `value` < `x[0]` в сторону `value` > `x[0]`.

        Возвращает число переходов и индексы точек До перехода
        """
        assert len(x) > 1, "x should have more than 1 point"

        zero_crossings_indexes = []

        for i in range(1, len(x) - 1):
            if ModelTriaxialCyclicLoading.to_positive_zero_cross(x[i], x[i + 1], value=x[0]):
                zero_crossings_indexes.append(i + 1)

        # skip first stabilization loop
        # zero_crossings_indexes = zero_crossings_indexes[1:]

        # add last loop if no crossing
        if x[-1] < 0:
            zero_crossings_indexes.append(len(x) - 1)

        return len(zero_crossings_indexes), zero_crossings_indexes

    @staticmethod
    def to_positive_zero_cross(first_point: float, second_point: float, value: Optional[float] = 0) -> bool:
        """
        Определяет расположение значений `first_point` и `second_point`
        относительно прямой y = `value`.

        Если при движении от `first_point` к `second_point` прямая y = `value`
        пересекается снизу вверх, возвращает True
        """
        return (first_point <= value) and (second_point > value)

    @staticmethod
    def trend_decomposition(x: np.ndarray, season: int, smooth_ending: Optional[bool] = True) -> np.ndarray:
        """
        Выделяет тренд из временного ряда `x` на основе цикличности (сезонности -- `season`)
        методом скользящего среднего (moving averages).
        Это обозначается season-MA (2-MA, 3-MA, 4-MA, etc.).
        Цикличность следует определять отдельно и подавать сюда. Качество выделения тренда напрямую зависит
        от этого параметра.

        Для четной цикличности применятся season-MA к которому применяется 2-MA
        для обеспечения симметричности результата.

        Parameters
        ----------
        x : np.ndarray
            временной ряд
        season : int
            при четном (even) season применяется 2xseason-MA, при нечетном (odd) season-MA.
        smooth_ending: bool
            при True обеспечиват дополнение результирующего массива еще одним циклом для гладкости
            перехода к временному ряду.

        Returns
        -------
        np.ndarray
            массив длины (len(x) - (season - 1)) для неченого порядка и (len(x) - season) для четного,
            при smooth_ending=True массив расширается с конца на season

        """

        assert len(x) > season, "lenght of x can't be smaller than season"

        x = np.asarray(x)

        # even_moving_average и odd_moving_average наверняка можно объединить
        def even_moving_average(_x, _season):
            """Скользящее среденее четного порядка. 2-MA, 4-MA, etc."""
            periods = int(_season / 2)
            return [np.mean([_x[t + j] for j in range(-periods, periods)]) for t in
                    range(periods, len(_x) - periods + 1)]

        def odd_moving_average(_x, _season):
            """Скользящее среденее нечетного порядка. 3-MA, 5-MA, etc."""
            periods = int((_season - 1) / 2)
            return [np.mean([_x[t + j] for j in range(-periods, periods + 1)]) for t in
                    range(periods, len(_x) - periods)]

        if season % 2 == 0:
            # Скользящее среднее четного порядка за которым следует скользящее среднее порядка 2 согласно алгоритму
            _series = even_moving_average(x, season)
            _series = even_moving_average(_series, 2)
            left_values = x[-int(season):]
        else:
            _series = odd_moving_average(x, season)
            left_values = x[-int(season) + 1:]

        if smooth_ending:
            while len(left_values) > season / 2:
                _series.append(np.mean(left_values))
                left_values = np.delete(left_values, 0)

        return np.array(_series)

    @staticmethod
    def define_mean_loop(strain: np.ndarray, deviator: np.ndarray,
                         loops_indexes: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Строит осредненную петлю гистерезиса по заданным массивам деформаций (`strain`)
        и девиатора (`deviator`).
        Возвращает одну осредненную петлю гистерезиса
        """
        assert len(deviator) > 1, "deviator should have more than 1 point"
        assert len(deviator) == len(strain), "strain and deviator is different in size"

        if loops_indexes is None:
            loops_indexes = ModelTriaxialCyclicLoading.separate_deviator_loops(deviator)

        loops_count = len(loops_indexes) - 1
        '''loops count starts from 0'''

        # print('Human loops count = ', loops_count + 1)

        if loops_count == 0:
            return np.array(strain[loops_indexes[0]:]), np.array(strain[loops_indexes[0]:])

        deviator_loops = [deviator[loops_indexes[i]:loops_indexes[i + 1] + 1] for i in range(loops_count)]
        strain_loops = [strain[loops_indexes[i]:loops_indexes[i + 1] + 1] for i in range(loops_count)]

        min_loop_length = min([loops_indexes[i + 1] - loops_indexes[i] + 1 for i in range(loops_count)])

        mean_deviator_loop = [np.mean([deviator_loops[i][j] for i in range(loops_count)]) for j in
                              range(min_loop_length)]
        mean_strain_loop = [np.mean([strain_loops[i][j] for i in range(loops_count)]) for j in range(min_loop_length)]

        return np.array(mean_strain_loop), np.array(mean_deviator_loop)

    @staticmethod
    def area(x: np.ndarray, y: np.ndarray) -> float:
        """Вычисляет площадь области внутри кривой"""
        result_area = ModelTriaxialCyclicLoading.square_under_line(x, y)
        if result_area < 0:
            result_area = ModelTriaxialCyclicLoading.square_under_line(x[::-1], y[::-1])
        assert result_area > 0, "area is negative"
        return result_area

    @staticmethod
    def square_under_line(x, y):
        """
        Функция определяет площадь под графиком методом трапеций. На вход подаются массивы точек по осям

        Обход фукнции должен быть по часовой стрелке, иначе получается отрицательный результат
        """
        square = 0
        for i in range(len(x) - 1):
            a = (x[i + 1] - x[i])
            low_side = min([y[i + 1], y[i]])
            delta = abs(y[i + 1] - y[i])
            square += a * (low_side + 0.5 * delta)
        return square

    @staticmethod
    def array_smoother(x: np.ndarray, ratio: Optional[int] = 4) -> np.ndarray:
        """
        Сглаживает массив, расширяя его в `ratio` раз путем интерполирования данных массива.
        Интерполяция квадратичная.
        """
        _time = ModelTriaxialCyclicLoading.time_series(x)
        func = interp1d(_time, x, "quadratic")
        x = np.linspace(_time[0], _time[-1], len(x) * ratio)
        return func(x)

    @staticmethod
    def time_series(x: np.ndarray) -> np.ndarray:
        """
        Возвращает массив целых чисел по размеру `x`: [0,1,2,...,len(`x`)-1]:
        """
        time = np.linspace(0, len(x) - 1, len(x))
        return time

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
        self._cosine = False

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

        self._noise_data = {}

    def get_test_parameters(self):
        return {
            'sigma_3': self._test_params.sigma_3,
            'sigma_1': self._test_params.sigma_1,
            't': self._test_params.t,
        }

    def set_test_params(self, cosine=False):
        """Функция принимает параметры опыта для дальнейших построений.
        n_fail моделируется из кривой CSR. Если нет разжижения - n_fail = None"""

        self._cosine = cosine

        self._test_params.cycles_count = statment[statment.current_test].mechanical_properties.cycles_count
        if self._test_params.cycles_count < 5:
            self._test_params.cycles_count = 5

        self._test_params.n_fail = statment[statment.current_test].mechanical_properties.n_fail
        Mcsr = statment[statment.current_test].mechanical_properties.Mcsr

        self._test_params.sigma_1 = statment[statment.current_test].mechanical_properties.sigma_1
        self._test_params.t = statment[statment.current_test].mechanical_properties.t
        self._test_params.K0 = statment[statment.current_test].mechanical_properties.K0
        self._test_params.qf = statment[statment.current_test].mechanical_properties.qf
        self._test_params.qf_2 = statment[statment.current_test].mechanical_properties.qf
        self._test_params.sigma_3 = statment[statment.current_test].mechanical_properties.sigma_3
        self._test_params.physical = statment[statment.current_test].physical_properties
        self._test_params.Cv = statment[statment.current_test].mechanical_properties.Cv
        self._test_params.damping_ratio = statment[statment.current_test].mechanical_properties.damping_ratio

        self._test_params.c = statment[statment.current_test].mechanical_properties.c
        self._test_params.fi = statment[statment.current_test].mechanical_properties.fi
        self._test_params.E = statment[statment.current_test].mechanical_properties.E50
        self._test_params.frequency = statment[statment.current_test].mechanical_properties.frequency
        self._test_params.frequency = self._test_params.frequency
        self._test_params.points_in_cycle = 20
        self._test_params.deviator_start_value = self._test_params.sigma_1 - self._test_params.sigma_3
        self._test_params.reverse = ModelTriaxialCyclicLoadingSoilTest.check_revers(self._test_params.sigma_1,
                                                                                     self._test_params.sigma_3,
                                                                                     2*self._test_params.t)

        try:
            self._test_params.qf = statment[statment.current_test].mechanical_properties.qf
            self._test_params.Kd = statment[statment.current_test].mechanical_properties.Kd
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

        self._test_modeling(statment[statment.current_test].mechanical_properties.Ms)

        self._test_params.reconsolidation_time = (((0.848 * 3.8 * 3.8) /
                                                   (4 * statment[statment.current_test].mechanical_properties.Cv))) * \
                                                 np.random.uniform(5, 7) * 60 + np.random.uniform(3000, 5000)

        if self._test_params.reconsolidation_time > 55000:
            self._test_params.reconsolidation_time = np.random.uniform(40000, 55000)

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
            "strain_max": {"value": self._draw_params.strain_max, "borders": [0, 0.12]},
            "strain_slant": {"value": self._draw_params.strain_slant,
                              "borders": [self._draw_params.strain_slant/5, int(self._test_params.cycles_count*0.9)]},
            "strain_E0": {"value": self._draw_params.strain_E0,
                           "borders": [self._draw_params.strain_E0/5, self._draw_params.strain_E0*5]},
            "strain_rise_after_fail": {"value": self._draw_params.strain_rise_after_fail,
                           "borders": [self._draw_params.strain_rise_after_fail/3,
                                       self._draw_params.strain_rise_after_fail*3]},
            "strain_stabilization": {"value": self._draw_params.strain_stabilization,
                           "borders": [0, 0.5]},
            "strain_phase_offset": {"value": self._draw_params.strain_phase_offset,
                                 "borders": [0, 0.5 * np.pi]}
        }

        # Ошибка свзяанная с выставлением значения в нуль:
        #  Если подать ровно ноль, ползунок выключается со значеним None
        if self._draw_params.PPR_phase_offset == 0.0:
            self._draw_params.PPR_phase_offset = 0.0000001

        PPR_params = {
            "PPR_n_fail": self._test_params.n_fail,
            "PPR_max": {"value": self._draw_params.PPR_max, "borders": [0.1, 1.2]},
            "PPR_slant": {"value": self._draw_params.PPR_slant,
                          "borders": [self._draw_params.PPR_slant/5, 0.7 * self._test_params.cycles_count]},
            "PPR_skempton": {"value": self._draw_params.PPR_skempton,
                          "borders": [self._draw_params.PPR_skempton/5, self._draw_params.PPR_skempton*5]},
            "PPR_rise_after_fail": {"value": self._draw_params.PPR_rise_after_fail,
                          "borders": [self._draw_params.PPR_rise_after_fail/5, self._draw_params.PPR_rise_after_fail*3]},
            "PPR_phase_offset": {"value": self._draw_params.PPR_phase_offset,
                          "borders": [0, 0.5 * np.pi]}
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
        self._draw_params.strain_phase_offset = strain_params["strain_phase_offset"]
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
        self._test_params.n_fail = round(PPR_params["PPR_n_fail"])
        if self._test_params.n_fail == self._test_params.cycles_count:
            self._test_params.n_fail = None
        self._draw_params.PPR_max = PPR_params["PPR_max"]
        self._draw_params.PPR_slant = PPR_params["PPR_slant"]
        self._draw_params.PPR_skempton = PPR_params["PPR_skempton"]
        self._draw_params.PPR_rise_after_fail = PPR_params["PPR_rise_after_fail"]
        self._draw_params.PPR_phase_offset = PPR_params["PPR_phase_offset"]

        self._modeling_PPR()
        Ms = ModelTriaxialCyclicLoadingSoilTest.define_Ms(
                self._test_params.c, self._test_params.fi, 1 / self._test_data.PPR[-1], self._test_params.sigma_3,
                self._test_params.sigma_1, self._test_params.t, self._test_params.cycles_count,
                self._test_params.physical.e, self._test_params.physical.Il)

        if self._test_params.n_fail:
            if self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05, 0.06)
            self._modeling_strain()
        else:
            if self._test_params.reverse:
                self._draw_params.strain_max = np.random.uniform(0, 0.005)
            else:
                self._draw_params.strain_max = np.random.uniform(0.05 / Ms, 0.06 / Ms)
            self._modeling_strain()
        self._test_processing()

    def get_processing_parameters(self):
        return {
            "sigma_1": float(self._test_params.sigma_1),
            "sigma_3": float(self._test_params.sigma_3),
            "frequency": float(self._test_params.frequency),
            "t": float(self._test_params.frequency),
            "points_in_cycle": float(self._test_params.points_in_cycle),
            "K0": float(self._test_params.K0),
        }

    def set_processing_parameters(self, params):
        self._test_params.sigma_1 = params["sigma_1"]
        self._test_params.sigma_3 = params["sigma_3"]
        self._test_params.t = params["t"]
        self._test_params.K0 = params["K0"]

    def generate_log_file(self, file_path, post_name=None):
        noise_data = self._noise_data
        ModelTriaxialCyclicLoadingSoilTest.generate_willie_log_file(file_path, self._test_data.deviator,
                                                                    self._test_data.PPR, self._test_data.strain,
                                                                    self._test_params.frequency,
                                                                    self._test_params.cycles_count,
                                                                    self._test_params.points_in_cycle,
                                                                    self._test_data.setpoint,
                                                                    self._test_data.cell_pressure,
                                                                    self._test_params.reconsolidation_time,
                                                                    post_name, noise_data=noise_data)
        #print(self.get_processing_parameters())
        create_json_file(f"{file_path}/processing_parameters.json", self.get_processing_parameters())

    def _define_draw_params(self, Mcsr=None):
        """Определение параметров отрисовки графиков.
        Eсли грунт не разжижился, ассимптота PPR моделируется через коэффициент запаса(отношение текущего CSR к
        максимальному)
        Ассимптота деформаций моделируется через p-t координаты через коэффициент запаса относительно кривой
        критического состояния. В случае реверсного нагружения ассимпота близка к 0"""

        # Погрешность девиатора и коэффициент сгрлаживания девиатора
        self._draw_params.deviator_deviation = 1
        self._draw_params.deviator_filter = 0.5
        # Значение начального модуля деформации. Амплитуда деформации рассчитывется как амплитуда девиатора деленая
        # на значение модуля
        self._draw_params.strain_E0 = ModelTriaxialCyclicLoadingSoilTest.define_E0(self._test_params.physical.Il,
                                                self._test_params.E, self._test_params.t*2, \
                                    define_qf(self._test_params.sigma_3, self._test_params.c , self._test_params.fi))

        if self._test_params.Kd:
            self._draw_params.strain_E0*=np.random.uniform(4, 6)

        # Параметр, отвечающий за рост деформации после цикла разрушения
        self._draw_params.strain_rise_after_fail = np.random.uniform(2, 3)

        # Стабилизация деформации к ассимптоте
        self._draw_params.strain_stabilization = np.random.uniform(0.01, 0.03)

        self._draw_params.strain_phase_offset = self._test_params.damping_ratio/40

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
        if self._test_params.cycles_count > 200 and self._test_params.cycles_count < 1000:
            self._draw_params.PPR_slant = np.random.uniform(100, 200)
        elif self._test_params.cycles_count > 1000:
            self._draw_params.PPR_slant = np.random.uniform(0.1, 0.2) * self._test_params.cycles_count
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
        self._draw_params.PPR_phase_offset = ModelTriaxialCyclicLoadingSoilTest.initial_PPR_phase_offset(
            self._test_params.physical.Il, self._test_params.frequency)
        if self._test_params.n_fail:
            fail_cycle = self._test_params.n_fail
            self._draw_params.strain_slant = fail_cycle*np.random.uniform(0.6, 0.7)
        else:
            # Наклон графика деформации
            if self._test_params.cycles_count < 50:
                self._draw_params.strain_slant = np.random.uniform(0.6, 0.7) * self._test_params.cycles_count
            elif self._test_params.cycles_count > 300:
                self._draw_params.strain_slant = np.random.uniform(0.3, 0.5) * self._test_params.cycles_count
            else:
                self._draw_params.strain_slant = self._test_params.cycles_count * np.random.uniform(0.6, 0.7)

    def _modeling_deviator(self):
        """Функция моделирования девиаторного нагружения"""
        # Массив setpoint - идеальная кривая, к которой стремится пид-регулятор
        if self._cosine:
            self._test_data.setpoint = ModelTriaxialCyclicLoadingSoilTest.create_deviator_array(self._test_data.cycles[len(self._load_stage.deviator):] - self._test_data.cycles[len(self._load_stage.deviator)],
                                                                                                2 * self._test_params.t,
                                                                                                self._test_params.deviator_start_value,
                                                                                                fail_cycle=self._test_params.n_fail,
                                                                                                points=self._test_params.points_in_cycle)
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
                phase_shift=self._draw_params.strain_phase_offset -0.5*np.pi, stabilization=self._draw_params.strain_stabilization)
            self._test_data.strain -= self._test_data.strain[0]
            self._test_data.strain = np.hstack((self._load_stage.strain,
                                                self._test_data.strain + np.max(self._load_stage.strain)))

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
                phase_shift=self._draw_params.strain_phase_offset, stabilization=self._draw_params.strain_stabilization)
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
        self._test_result.E_values = (E_module[0], E_module[-1])
        self._test_data.strain = ndimage.gaussian_filter(self._test_data.strain, self._draw_params.strain_filter,
                                                         order=0)
        self._test_data.strain[0] = 0

    def _modeling_PPR(self):
        """Функция моделирования PPR

        Логика работы:
        Массив PPR может строиться 2мя методами. В цикл разрушения, если он определен, иои с помощь ассимптоты и
        наклона"""
        if self._cosine:
            PPR = ModelTriaxialCyclicLoadingSoilTest.create_PPR_array(
                self._test_data.cycles[len(self._load_stage.deviator):] -
                self._test_data.cycles[len(self._load_stage.deviator)],
                self._test_params.t,
                self._draw_params.PPR_skempton,
                self._test_data.cell_pressure[len(self._load_stage.deviator):], self._draw_params.PPR_max,
                self._draw_params.PPR_slant,
                self._draw_params.PPR_phase_offset + 0.5*np.pi,
                self._draw_params.PPR_deviation,
                ModelTriaxialCyclicLoadingSoilTest.check_revers(self._test_params.sigma_1,
                                                                self._test_params.sigma_3,
                                                                2 * self._test_params.t),
                self._test_params.n_fail,
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

        self._test_data.mean_effective_stress = (self._test_data.deviator + 3 * self._test_data.cell_pressure * (1 - self._test_data.PPR))/3

    def _test_modeling(self, Ms=None):
        """Функция моделирования опыта"""
        self._test_data.cycles = np.linspace(0, self._test_params.cycles_count,
                                             self._test_params.points_in_cycle * self._test_params.cycles_count + 1)
        #self._test_data.time = self._test_data.cycles / self._test_params.frequency
        # Этап нагружения
        if self._cosine:
            self._load_stage.time, self._load_stage.strain, self._load_stage.deviator = ModelTriaxialCyclicLoadingSoilTest.dev_loading(
                self._test_params.qf,
                self._test_params.E, self._test_params.qf/2, frequency=self._test_params.frequency)
            np.array(self._load_stage.time)
            #self._load_stage.deviator += self._test_params.deviator_start_value
            self._test_data.cycles = np.hstack((np.array(self._load_stage.time)*self._test_params.frequency,
                                                self._test_data.cycles + self._load_stage.time[-1]*self._test_params.frequency))

        self._test_data.time = self._test_data.cycles/self._test_params.frequency


        self._test_params.len_cycles = len(self._test_data.cycles)


        #self._test_data.cell_pressure = ModelTriaxialCyclicLoadingSoilTest.create_cell_press_willie_array(self._test_params.sigma_3, self._test_data.cycles,
                                                                #self._test_params.frequency)

        self._test_data.cell_pressure = np.full(len(self._test_data.cycles), self._test_params.sigma_3)
        self._modeling_deviator()
        self._modeling_PPR()

        if not Ms:
            Ms = ModelTriaxialCyclicLoadingSoilTest.define_Ms(
                self._test_params.c, self._test_params.fi, 1 / self._test_data.PPR[-1], self._test_params.sigma_3,
                self._test_params.sigma_1, self._test_params.t, self._test_params.cycles_count,
                self._test_params.physical.e, self._test_params.physical.Il)

        if self._test_params.Kd:
            if self._test_params.Kd >= 0.9:
                k = 1
            else:
                k = 1 + (1 - self._test_params.Kd) * 1.5

            self._draw_params.strain_max = self._load_stage.strain[-1] * (1 - self._test_params.Kd) - (self._test_params.t / self._draw_params.strain_E0)
        else:
            self._draw_params.strain_max = np.random.uniform(0.05 / Ms, 0.06 / Ms)

        self._modeling_strain()

        if self._test_params.Kd:
            strain_cyclic = self._test_data.strain[len(self._load_stage.strain):]
            strain_cyclic -= strain_cyclic[0]

            self._load_stage.strain[-1] / self._test_params.Kd

            #strain_cyclic *= (
                       # ((self._load_stage.strain[-1] / self._test_params.Kd) - self._load_stage.strain[-1]) / np.max(
                    #strain_cyclic))
            strain_cyclic *= (
                        ((self._load_stage.strain[-1] / self._test_params.Kd) - self._load_stage.strain[-1]) /(
                    strain_cyclic[-1]))
            self._test_data.strain = np.hstack((self._load_stage.strain, strain_cyclic + self._load_stage.strain[-1]))

        self.form_noise_data()
            #self._test_data.strain *= ((self._load_stage.strain[-1] * self._test_params.Kd)/np.max(self._test_data.strain - self._load_stage.strain[-1])) - self._load_stage.strain[-1]

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

    def form_noise_data(self):
        deviator = self._test_data.deviator
        self._noise_data["pore_pressure_after_consolidation"] = np.random.uniform(300, 500)
        self._noise_data["force_initial"] = np.random.uniform(15, 40)
        self._noise_data["piston_position_initial"] = np.random.uniform(5, 20)
        self._noise_data["vertical_strain_initial"] = np.random.uniform(0, 0.001)
        self._noise_data["diameter"] = np.random.uniform(38.001, 38.002, len(deviator))
        self._noise_data["external_displacement_coefficient"] = np.random.uniform(50, 80)
        self._noise_data["sample_height"] = round(np.random.uniform(75.970000, 76.000000), 5)
        self._noise_data["Diameter under isotropic conditions"] = np.random.uniform(38.001, 38.002, len(deviator))

    @property
    def test_duration(self):
        duration_sec = (self._test_params.cycles_count / self._test_params.frequency) + 1 / \
               (self._test_params.points_in_cycle * self._test_params.frequency) + \
               self._test_params.reconsolidation_time
        return timedelta(seconds=duration_sec)

    @staticmethod
    def critical_line(c, fi, mean_effective_stress):
        c = c * 1000
        fi = np.deg2rad(fi)
        k = (6 * np.sin(fi) / (3 - np.sin(fi)))
        return c + 0.5 * k * mean_effective_stress

    @staticmethod
    def define_Ms(c, fi, Mcsr, sigma_3, sigma_1, t, cycles_count, e, Il) -> float:
        """Функция находит зависимость параметра Msf от физических свойств и параметров нагрузки
        Средняя линия отклонения деформации будет определена как 0.05 / Msf"""
        if (sigma_1 - sigma_3) <= 1.5*t:
            return np.round(np.random.uniform(100, 500), 2)

        e = e if e else np.random.uniform(0.6, 0.7)
        Il = Il if Il else np.random.uniform(-0.1, 0.3)

        def define_qf(sigma_3, c, fi):
            """Функция определяет qf через обжимающее давление и c fi"""
            fi = fi * np.pi / 180
            return np.round(
                (2 * (c * 1000 + (np.tan(fi)) * sigma_3)) / (np.cos(fi) - np.tan(fi) + np.sin(fi) * np.tan(fi)), 1)

        qf = define_qf(sigma_3*(1 - 1 / Mcsr), c, fi)

        max_deviator = sigma_1 - sigma_3 + 2*t

        #Ms = ModelTriaxialCyclicLoadingSoilTest.critical_line(
            #c, fi, (1 - 1 / Mcsr) * max_deviator) / max_deviator if Mcsr else 1

        Ms = 0.8 * qf / max_deviator if Mcsr else 1

        CSR_dependence = sigmoida(mirrow_element(t/sigma_1, 0.5), 2, 0.9, 2.1, 1.5)
        e_dependence = sigmoida(mirrow_element(e, 0.5), 0.7, 0.5, 0.9, 1.5)
        Il_dependence = sigmoida(mirrow_element(Il, 0.5), 0.7, 0.5, 1, 1.5)
        cycles_count_dependence = sigmoida(mirrow_element(cycles_count, 100), 0.3, 100, 1.1, 250)

        Ms *= (CSR_dependence * e_dependence * Il_dependence * cycles_count_dependence)

        if Ms <= 0.7:
            Ms = np.random.uniform(0.6, 0.8)

        return np.round(Ms, 2)

    @staticmethod
    def influence_of_frequency_on_strain(frequency) -> float:
        """коэффициент отвечает за рост деформации с увеличением частоты"""
        return 1 + 0.003 * frequency

    @staticmethod
    def stabilization_logarithm(x, amplitude, x85, stabilization_ratio) -> np.array:
        """Стабилизированный логарифм - выходит на прямую"""
        y = logarithm(x, amplitude, x85) - logarithm(x, amplitude * stabilization_ratio, int(0.9 * x[-1]))
        if y[-1] == 0:
            return np.full(len(y), 0)
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

            amplitude_second_area = sigmoida(x[fail_cycle * points:], amplitude * 0.03, center_sigmoida_second_area,
                                             amplitude * 0.03 / 2, (x[-1] - center_sigmoida_second_area) * 2)

            amplitude_second_area -= [amplitude_second_area[0] - amplitude]

            amplitude = np.hstack((amplitude_first_area, amplitude_second_area))

        # step_sin(x, 0.1*np.pi, 5, 0.25) - заужает пики синусоиды
        return amplitude * np.sin(x * 2 * np.pi + step_sin(x, -0.03*np.pi, 5, 0.25) + phase_shift) + offset

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

        def rise(x, val):
            i, = np.where(x >= 500)
            i = int(i[0] * np.random.uniform(0.8, 1.5))
            if i <= len(x) + 100:
                return np.hstack((np.zeros(i),
                                  step_sin(x[i:], val, x[i] + (x[-1] - x[i]) / 2, (len(x) - i) * 2) + val))

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
            E = without_fail(x, val, degradation_percent, np.random.uniform(0.5, 0.7) * x[-1])
            if x[-1] >= 700:
                return E + rise(x, (E[0] - E[-1])*np.random.uniform(0.2, 0.4))
            else:
                return E

    @staticmethod
    def create_strain_array(x, deviator_amplitude, E_module, strain_max, x_85, phase_shift=0, stabilization=0):
        """Создаем массив деформаций"""
        strain_amplitude = deviator_amplitude / E_module

        return np.array(strain_amplitude * np.sin(x * 2 * np.pi + step_sin(x + phase_shift/6, np.random.uniform(0.09, 0.12)*np.pi, 5, 0.25) + phase_shift)) + \
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
                try:
                    PPR_exp += np.hstack(
                        (create_deviation_curve(x[:i1[0]], PPR_max / 30, (1, 0.1), np.random.uniform(6, 12),
                                                "zero_diff"), np.zeros(len(x) - i1[0])))
                except ValueError:
                    pass
            try:
                PPR_exp += np.hstack((create_deviation_curve(x[:i1[0]], PPR_max / 50, (1, 0.1), i1[0] / 5, "zero_diff"),
                                  np.zeros(len(x) - i1[0])))
            except (ValueError, ZeroDivisionError):
                pass

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

        #PPR_sin = PPR_exp + amplitude * create_acute_sine_array(x * 2 * np.pi + step_sin(x + phase_offset_array/6, np.random.uniform(0.01, 0.03)*np.pi, 5, 0.25) + phase_offset_array,
                                                                #k) - amplitude * PPR_exp / PPR_max

        PPR_sin = PPR_exp + amplitude * create_acute_sine_array(
            x * 2 * np.pi + phase_offset_array, k) - amplitude * PPR_exp / PPR_max

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
            if not Il:
                Il = np.random.uniform(-0.1, 0.05)
            return define_E_q_until_05(E50, q, qf, sigmoida(Il, 1.5, 0.5, 3.5, 1.2))

    @staticmethod
    def dependence_skempton_Il_frequency(Il, frequency):
        """Находит зависимость коэффициента скемптона от консистенции и частоты"""
        if not Il:
            dependence_skempton_Il = np.random.uniform(0.27, 0.3)
        else:
            dependence_skempton_Il = sigmoida(Il, 0.1, 0.5, 0.2, 1.2)

        dependence_skempton_frequency = sigmoida(mirrow_element(frequency, 5), 0.1, 5, 0.1, 10)

        return dependence_skempton_Il + dependence_skempton_frequency

    @staticmethod
    def initial_PPR_phase_offset(Il, frequency):
        """Находит зависимость начального смещения фаз в зависимости от Il  частоты"""
        if not Il:
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
        if len(time)<= 10:
            time = np.linspace(0, end_time, 10)
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
    def generate_willie_log_file(file_path, deviator, PPR, strain, frequency, N, points_in_cycle, setpoint,
                                 cell_pressure, reconsolidation_time, post_name=None, time=None, noise_data=None):
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
                except IndexError:
                    pass
            s += '\n'
            return (s)

        pore_pressure_after_consolidation = noise_data["pore_pressure_after_consolidation"]


        """if not Ip:
            time_initial = np.random.uniform(7200.000000, 18000.000000)  # Начальное время опыта
        else:
            time_initial = np.random.uniform(22000.000000, 55000.000000)  # Начальное время опыта"""
        force_initial = noise_data["force_initial"]
        piston_position_initial = noise_data["piston_position_initial"]
        vertical_strain_initial = noise_data["vertical_strain_initial"]
        diameter = noise_data["diameter"]
        sample_area_initial = np.pi * (diameter[0] / 2) ** 2
        sample_area = np.pi * (diameter / 2) ** 2

        external_displacement_coefficient = noise_data["external_displacement_coefficient"]

        piston_area = 314.159265
        sample_height = noise_data["sample_height"]

        if time is None:
            time = np.round((np.arange(0, (N / frequency) + 1 / (points_in_cycle * frequency),
                                   1 / (points_in_cycle * frequency)) + reconsolidation_time), 4)

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
            "Diameter under isotropic conditions":  noise_data["Diameter under isotropic conditions"],
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

        #return time[-1] + time_initial


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

    a = ModelTriaxialCyclicLoadingSoilTest()
    #file = "C:/Users/Пользователь/Desktop/Опыты/264-21 П-57 11.7 Обжимающее давление = 120.txt"
    #file = "C:/Users/Пользователь/Desktop/Опыты/718-20 PL20-Skv139 0.2  Обжимающее давление = 25.txt"
    statment.load("C:/Users/Пользователь/Desktop/Новая папка (4)/statment.pickle")
    statment.current_test = "SBT21-SGMM B-1-1-2"
    a.set_test_params()
    a.plotter()


