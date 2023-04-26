"""Модуль математических моделей статического трехосного нагружения. Содержит модели:
    ModelMohrCircles - модель обработчика кругов мора.
    Принцип работы:
        Опыты подаются в модель методом add_test(). Подается путь к файлу, После считывания данные передаются в
        обработчики частей опыта. Для удаления опытов используется метод dell_test
        Обработка опыта происходит методом _test_processing() после открытия хотя бы 3х опытов.
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelMohrCirclesSoilTest - модель математического моделирования кругов мора.
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Далее данные генерируются автоматически"""

__version__ = 1

import numpy as np
import copy
import os
import matplotlib.pyplot as plt
from typing import List
from scipy.optimize import fsolve, curve_fit
from scipy.optimize import differential_evolution
import warnings

from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad, ModelTriaxialStaticLoadSoilTest
from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from configs.plot_params import plotter_params
from singletons import statment, E_models, FC_models
from cvi.cvi_writer import save_cvi_FC

class ModelMohrCircles:
    """Класс моделирования опыта FCE"""
    def __init__(self):
        # Основные модели опыта
        self._tests = []
        self._test_data = AttrDict({"fi": None, "c": None})
        self._test_result = AttrDict({"fi": None, "c": None, "m_plaxis": None, "m_approximate": None, "c_res": None, "fi_res": None})
        self._m_approximate_type = None
        self._test_reference_params = AttrDict({"p_ref": None, "Eref": None})

    def add_test(self, file_path):
        """Добавление опытов"""
        test = ModelTriaxialStaticLoad()
        test.set_test_file_path(file_path)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()
            self._test_processing()

    def dell_test(self, i):
        """Удаление опытов"""
        self._tests.pop(i)
        self._test_processing()

    def get_tests(self):
        """Чтение всех опытов"""
        return self._tests

    def sort_tests(self):
        """Сортировка опытов по возрастанию обжимающего давления"""
        def sort_key(test):
            return test.deviator_loading.get_test_results()["sigma_3"]

        if len(self._tests) >= 2:
            self._tests.sort(key=sort_key)

    def set_reference_params(self, p_ref, Eref):
        self._test_reference_params.p_ref = p_ref
        self._test_reference_params.Eref = Eref

    def get_sigma_3_1(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 1:
            sigma_1 = []
            sigma_3 = []

            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                sigma_3.append(np.round(results["sigma_3"], 3))
                sigma_1.append(np.round(results["sigma_3"] + results["qf"], 3))
            return sigma_3, sigma_1
        return None, None

    def get_sigma_1_res(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 2:
            sigma_1_res = []

            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                sigma_1_res.append(np.round(results["sigma_3"] + results["q_res"], 3))
            return sigma_1_res
        return None

    def get_sigma_3_deviator(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 1:
            sigma_3 = []
            deviator = []

            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                sigma_3.append(np.round(results["sigma_3"], 3))
                deviator.append(np.round(results["qf"], 3))
            return sigma_3, deviator
        return None, None

    def get_sigma_u(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 1:
            u = []
            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                u.append(np.round(results["max_pore_pressure"]/1000, 3))
            return u
        return None

    def get_E50(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 2:
            E50 = []

            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                E50.append(round(results["E50"], 3))
            return E50

        return None, None

    def _check_clone(self, check_test):
        """Проверяем, был ли открыт такой опыт уже"""
        for test in self._tests:
            if check_test.deviator_loading.get_test_results()["sigma_3"] == \
                    test.deviator_loading.get_test_results()["sigma_3"] and \
                    check_test.deviator_loading.get_test_results()["qf"] == \
                    test.deviator_loading.get_test_results()["qf"] and \
                    check_test.deviator_loading.get_test_results()["u"] == \
                    test.deviator_loading.get_test_results()["u"]:
                return False
        return True

    def _test_processing(self):
        """Обработка опытов"""
        self._m_approximate_type = "plaxis"
        if statment.general_parameters.test_mode == "Трёхосное сжатие НН" or statment.general_parameters.test_mode == "Вибропрочность":
            self._test_result.fi = 0
            t = [test.deviator_loading.get_test_results()["qf"]/2 for test in self._tests]
            self._test_result.c = sum(t)/len(t)
        elif statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
            sigma_3, sigma_1 = self.get_sigma_3_1()
            sigma_1_res = self.get_sigma_1_res()
            if sigma_3 is not None:
                c, fi = ModelMohrCircles.mohr_cf_stab(sigma_3, sigma_1)
                self._test_result.c = np.round(np.arctan(c), 3)
                self._test_result.fi = np.round(np.rad2deg(np.arctan(fi)), 1)  # round(np.rad2deg(np.arctan(fi)), 1)

                c_res, fi_res = ModelMohrCircles.mohr_cf_stab(sigma_3, sigma_1_res)
                self._test_result.c_res = np.round(np.arctan(c_res), 3)
                self._test_result.fi_res = np.round(np.rad2deg(np.arctan(fi_res)), 1)

                self.plot_data_m = None, None

                if self._test_reference_params.p_ref and self._test_reference_params.Eref:
                    E50 = self.get_E50()
                    self._test_result.m_plaxis, self._test_result.m_approximate, self.plot_data_m, self.plot_data_m_line = ModelMohrCircles.calculate_m(
                        sigma_3, E50, self._test_reference_params.Eref / 1000,
                                      self._test_reference_params.p_ref / 1000,
                        statment[statment.current_test].mechanical_properties.c,
                        statment[statment.current_test].mechanical_properties.fi)

                    self._test_result.m = self._test_result.m_plaxis
        else:
            sigma_3, sigma_1 = self.get_sigma_3_1()
            if sigma_3 is not None:
                c, fi = ModelMohrCircles.mohr_cf_stab(sigma_3, sigma_1)
                self._test_result.c = np.round(np.arctan(c), 3)
                self._test_result.fi = np.round(np.rad2deg(np.arctan(fi)), 1)# round(np.rad2deg(np.arctan(fi)), 1)

                self.plot_data_m = None, None

                if self._test_reference_params.p_ref and self._test_reference_params.Eref:
                    E50 = self.get_E50()
                    self._test_result.m_plaxis, self._test_result.m_approximate, self.plot_data_m, self.plot_data_m_line_plaxis, self.plot_data_m_line_approximate, = ModelMohrCircles.calculate_m(
                        sigma_3, E50, self._test_reference_params.Eref/1000,
                        self._test_reference_params.p_ref/1000,
                        statment[statment.current_test].mechanical_properties.c,
                        statment[statment.current_test].mechanical_properties.fi)
                    self.plot_data_m_line = self.plot_data_m_line_plaxis
                    self._test_result.m = self._test_result.m_plaxis

    def set_m_type(self, type):
        if type == "plaxis":
            self._test_result.m = self._test_result.m_plaxis
            self.plot_data_m_line = self.plot_data_m_line_plaxis
            self._m_approximate_type = "plaxis"
        elif type == "approximate":
            self._test_result.m = self._test_result.m_approximate
            self.plot_data_m_line = self.plot_data_m_line_approximate
            self._m_approximate_type = "approximate"

    def get_test_results(self):
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Подготовка данных для построения"""
        if statment.general_parameters.test_mode == "Трёхосное сжатие НН" or statment.general_parameters.test_mode == "Вибропрочность":
            strain = []
            deviator = []
            s3 = []
            for test in self._tests:
                plots = test.deviator_loading.get_plot_data()
                s3.append(test.deviator_loading.get_test_results()["sigma_3"])
                strain.append(plots["strain"])
                deviator.append(plots["deviator"])

            mohr_x, mohr_y = ModelMohrCircles.mohr_circles([0 for _ in range(len(deviator))], [np.max(d) for d in deviator])

            for i in range(len(mohr_x)):
                mohr_x[i] += s3[i]

            line_x = np.linspace(0, np.max(deviator[-1]) + s3[0], 10)
            line_y = np.full(10, np.max(deviator[-1]) / 2)

            x_lims = (s3[0], np.max(deviator[-1]) * 1.1 + s3[0])
            y_lims = (0, np.max(deviator[-1]) * 1.1 * 0.5)

            return {"strain": strain,
                    "deviator": deviator,
                    "mohr_x": mohr_x,
                    "mohr_y": mohr_y,
                    "mohr_line_x": line_x,
                    "mohr_line_y": line_y,
                    "x_lims": x_lims,
                    "y_lims": y_lims}

        if len(self._tests) >= 3:
            strain = []
            deviator = []
            for test in self._tests:
                plots = test.deviator_loading.get_plot_data()
                strain.append(plots["strain"])
                deviator.append(plots["deviator"])

            sigma_3, sigma_1 = self.get_sigma_3_1()
            mohr_x, mohr_y = ModelMohrCircles.mohr_circles(sigma_3, sigma_1)

            line_x = np.linspace(0, sigma_1[-1], 100)
            line_y = line(np.tan(np.deg2rad(self._test_result.fi)), self._test_result.c, line_x)

            x_lims = (0, sigma_1[-1] * 1.1)
            y_lims = (0, sigma_1[-1] * 1.1 * 0.5)

            if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                sigma_1_res = self.get_sigma_1_res()
                mohr_x_res, mohr_y_res = ModelMohrCircles.mohr_circles(sigma_3, sigma_1_res)
                line_y_res = line(np.tan(np.deg2rad(self._test_result.fi_res)), self._test_result.c_res, line_x)
                return {"strain": strain,
                        "deviator": deviator,
                        "mohr_x": mohr_x,
                        "mohr_y": mohr_y,
                        "mohr_x_res": mohr_x_res,
                        "mohr_y_res": mohr_y_res,
                        "mohr_line_x": line_x,
                        "mohr_line_y": line_y,
                        "mohr_line_y_res": line_y_res,
                        "x_lims": x_lims,
                        "y_lims": y_lims,
                        "plot_data_m": self.plot_data_m,
                        "plot_data_m_line": self.plot_data_m_line}
            else:
                return {"strain": strain,
                        "deviator": deviator,
                        "mohr_x": mohr_x,
                        "mohr_y": mohr_y,
                        "mohr_line_x": line_x,
                        "mohr_line_y": line_y,
                        "x_lims": x_lims,
                        "y_lims": y_lims,
                        "plot_data_m": self.plot_data_m,
                        "plot_data_m_line": self.plot_data_m_line}
        else:
            return None

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '12'
        rcParams['axes.edgecolor'] = 'black'

        figure = plt.figure(figsize = [7, 7])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.grid(axis='both')
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПА")

        ax_cycles = figure.add_subplot(2, 1, 2)
        ax_cycles.grid(axis='both')
        ax_cycles.set_xlabel("σ, МПа")
        ax_cycles.set_ylabel("τ, МПа")

        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots is not None:
            for i in range(len(plots["strain"])):
                ax_deviator.plot(plots["strain"][i], plots["deviator"][i], **plotter_params["main_line"])
                ax_cycles.plot(plots["mohr_x"][i], plots["mohr_y"][i], **plotter_params["main_line"])

            ax_cycles.plot(plots["mohr_line_x"], plots["mohr_line_y"], **plotter_params["main_line"])

            ax_cycles.plot([], [], label="c" + ", МПа = " + str(res["c"]), color="#eeeeee")
            ax_cycles.plot([], [], label="fi" + ", град. = " + str(res["fi"]), color="#eeeeee")
            ax_cycles.plot([], [], label="m" + ", МПа$^{-1}$ = " + str(res["m"]), color="#eeeeee")

            ax_cycles.set_xlim(*plots["x_lims"])
            ax_cycles.set_ylim(*plots["y_lims"])

            ax_cycles.legend()

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass

    def __iter__(self):
        for test in self._tests:
            yield test

    def __len__(self):
        return len(self._tests)

    @staticmethod
    def mohr_circles(sigma3, sigma1):
        """Построение кругов мора. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как
        0 или не задается вообще"""

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

    @staticmethod
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

    @staticmethod
    def mohr_cf_stab(sigma3, sigma1):
        """Расчет c и f. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""
        c, fi = ModelMohrCircles.mohr_cf(sigma3, sigma1, True)
        cS = c / (2 * (fi ** 0.5))
        phiS = ((fi - 1) / (2 * (fi ** 0.5)))

        return cS, phiS

    @staticmethod
    def calculate_m(sigma_3: List, E50: List, Eref: float, p_ref: float, c: float, fi: float) -> float:
        """Функция поиска степенного параметра упрочнения из нескольких опытов
        :param sigma_3 - массив обжимающих давлений
        :param E50 - массив модулей E50
        :param Eref - модуль деформации Е50 при референтном давлении
        :param p_ref - референтное давление"""

        fi = np.deg2rad(fi)

        def E50_from_sigma_3(sigma, m):
            return (Eref * ((c * np.cos(fi) + sigma * np.sin(fi)) / (
                    c * np.cos(fi) + p_ref * np.sin(fi))) ** m)

        def line(x, a, b):
            return a * x + b

        popt, pcov = curve_fit(E50_from_sigma_3, sigma_3, E50)
        m_plaxis = popt
        m_plaxis = np.round(m_plaxis[0], 2)


        plot_data_y = [np.log(E50i/Eref) for E50i in E50]
        plot_data_x = [np.log((c*(1/np.tan(fi)) + sigma_3i) / (c*(1/np.tan(fi)) + p_ref)) for sigma_3i in sigma_3]

        popt, pcov = curve_fit(line, np.array(plot_data_x), np.array(plot_data_y))
        m_line_approximate, b = popt
        m_line_approximate = np.round(m_line_approximate, 2)

        plot_data_x_line = [np.log((c * (1 / np.tan(fi)) + sigma_3i) / (c * (1 / np.tan(fi)) + p_ref)) for sigma_3i in
                       [sigma_3[0]*0.9, sigma_3[-1]*1.1]]

        plot_data_y_line_1 = [m_plaxis * x for x in plot_data_x_line]
        plot_data_y_line_2 = [m_line_approximate * x + b for x in plot_data_x_line]

        return m_plaxis, m_line_approximate, [plot_data_x, plot_data_y], [plot_data_x_line, plot_data_y_line_1], [plot_data_x_line, plot_data_y_line_2]

class ModelMohrCirclesSoilTest(ModelMohrCircles):
    """Класс моделирования опыта FCE"""
    def __init__(self):
        super().__init__()
        self._test_params = None
        self._reference_pressure_array = None
        self.pre_defined_kr_fgs = None
        self.current_kr_fgs_ind = None
        self.test_mode = statment.general_parameters.test_mode
        self.is_split_deviator = False

        self._b_noise = None

    def add_test_st(self, pre_defined_kr_fgs=None):
        """Добавление опытов"""
        test = ModelTriaxialStaticLoadSoilTest()

        if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
            pre_defined_kr_fgs = 1
            self.pre_defined_kr_fgs = pre_defined_kr_fgs

        test.set_test_params(statment.general_parameters.reconsolidation, pre_defined_kr_fgs=pre_defined_kr_fgs)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()
            if statment.general_parameters.test_mode in ["Трёхосное сжатие (F, C, E)", 'Трёхосное сжатие (F, C, Eur)']:
                test_kr_fgs = test.deviator_loading.pre_defined_kr_fgs
                if test_kr_fgs and self.current_kr_fgs_ind is not None and self.pre_defined_kr_fgs is not None:
                    for i in range(self.current_kr_fgs_ind, len(self.pre_defined_kr_fgs)):
                        self.pre_defined_kr_fgs[i] = 1
            else:
                self.pre_defined_kr_fgs = test.deviator_loading.pre_defined_kr_fgs

    def add_test_st_NN(self):
        """Добавление опытов"""
        test = ModelTriaxialStaticLoadSoilTest()
        test.set_test_params(reconsolidation=None, consolidation=None)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()

    def set_reference_pressure_array(self, reference_pressure_array):
        self._reference_pressure_array = reference_pressure_array

    def _test_modeling(self):
        if statment.general_parameters.test_mode in ["Трёхосное сжатие (F, C, E)", 'Трёхосное сжатие (F, C, Eur)']:
            pre_defined_kr_fgs = E_models[statment.current_test].deviator_loading.pre_defined_kr_fgs
            sigma = E_models[statment.current_test].deviator_loading._test_params["sigma_3"]
            _pre_defined_kr_fgs = []
            _pressure_array = statment[statment.current_test].mechanical_properties.pressure_array["current"]
            for press in _pressure_array:
                if pre_defined_kr_fgs:
                    if press >= sigma:
                        _pre_defined_kr_fgs.append(1)
                    else:
                        _pre_defined_kr_fgs.append(None)
                else:
                    if press <= sigma:
                        _pre_defined_kr_fgs.append(0)
                    else:
                        _pre_defined_kr_fgs.append(None)
            self.pre_defined_kr_fgs = _pre_defined_kr_fgs

        self._tests = []

        if statment.general_parameters.test_mode == "Трёхосное сжатие НН" or statment.general_parameters.test_mode == "Вибропрочность":
            self.add_test_st_NN()
        else:
            self.set_reference_params(statment[statment.current_test].mechanical_properties.sigma_3, statment[statment.current_test].mechanical_properties.E50)

            self._reference_pressure_array = statment[statment.current_test].mechanical_properties.pressure_array["current"]

            sigma_3_array = []
            qf_array = []
            sigma_1_array = []
            E50_array = []
            if statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or statment.general_parameters.test_mode == 'Вибропрочность':
                u_array = statment[statment.current_test].mechanical_properties.u
                if type(u_array) != list:
                    u_array = [0 for i in self._reference_pressure_array]
            else:
                u_array = [0 for i in self._reference_pressure_array]

            sigma_3_origin = statment[statment.current_test].mechanical_properties.sigma_3
            qf_origin = statment[statment.current_test].mechanical_properties.qf
            sigma_1_origin = statment[statment.current_test].mechanical_properties.sigma_1
            E50_origin = statment[statment.current_test].mechanical_properties.E50
            u_origin = statment[statment.current_test].mechanical_properties.u
            Eur_origin = statment[statment.current_test].mechanical_properties.Eur
            statment[statment.current_test].mechanical_properties.Eur = None

            for num, sigma_3 in enumerate(self._reference_pressure_array):
                sigma_3_array.append(sigma_3 - u_array[num])
                qf_array.append(define_qf(sigma_3, statment[statment.current_test].mechanical_properties.c,
                                          statment[statment.current_test].mechanical_properties.fi))
                sigma_1_array.append(np.round(qf_array[-1] + sigma_3_array[-1], 3))

            c = 0
            fi = 0

            current_c = np.round(statment[statment.current_test].mechanical_properties.c, 3)
            current_fi = np.round(statment[statment.current_test].mechanical_properties.fi, 1)

            count = 0
            while True:
                if (c == current_c and fi == current_fi):
                    break

                if count > 5:
                    break

                qf = ModelMohrCirclesSoilTest.new_noise_for_mohrs_circles(
                    np.array(sigma_3_array), np.array(sigma_1_array),
                    statment[statment.current_test].mechanical_properties.fi,
                    statment[statment.current_test].mechanical_properties.c * 1000)

                for i in range(len(qf)):
                    qf_array[i] = round(qf[i], 3)
                    sigma_1_array[i] = round(qf_array[i] + sigma_3_array[i], 3)
                    E50_array.append(define_E50(
                        statment[statment.current_test].mechanical_properties.E50,
                        statment[statment.current_test].mechanical_properties.c * 1000,
                        statment[statment.current_test].mechanical_properties.fi,
                        sigma_3_array[i],
                        statment[statment.current_test].mechanical_properties.sigma_3,
                        statment[statment.current_test].mechanical_properties.m) * np.random.uniform(0.95, 1.05))


                c, fi = ModelMohrCirclesSoilTest.mohr_cf_stab(
                    [np.round(sigma_3 / 1000, 3) for sigma_3 in sigma_3_array],
                    [np.round(sigma_1/1000, 3) for sigma_1 in sigma_1_array])
                    #[np.round(sigma_3/1000 - pore, 3) for sigma_3, pore in zip(sigma_3_array, u_origin)],
                    #[np.round(sigma_1/1000 - pore, 3) for sigma_1, pore in zip(sigma_1_array, u_origin)])
                c = round(c, 3)
                fi = round(np.rad2deg(np.arctan(fi)), 1)

                count += 1

            if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                q_res_normal = np.asarray([np.round(float(define_qf(sigma_3_array[i],
                                                             statment[statment.current_test].mechanical_properties.c_res,
                                                             statment[statment.current_test].mechanical_properties.fi_res)), 1) for i in range(len(sigma_1_array))])
                sigma_1_res = q_res_normal + sigma_3_array
                q_res_noised = ModelMohrCirclesSoilTest.new_noise_for_mohrs_circles(np.asarray(sigma_3_array), np.asarray(sigma_1_res),
                                                                                  statment[statment.current_test].mechanical_properties.fi_res,
                                                                                  statment[statment.current_test].mechanical_properties.c_res*1000)

            for i in range(len(sigma_1_array)):
                statment[statment.current_test].mechanical_properties.sigma_3 = sigma_3_array[i] + u_array[i]
                statment[statment.current_test].mechanical_properties.qf = qf_array[i]
                statment[statment.current_test].mechanical_properties.sigma_1 = sigma_1_array[i] + u_array[i]
                statment[statment.current_test].mechanical_properties.E50 = E50_array[i]

                if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
                    statment[statment.current_test].mechanical_properties.q_res = q_res_noised[i]

                if statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or statment.general_parameters.test_mode == 'Трёхосное сжатие НН' or statment.general_parameters.test_mode == 'Вибропрочность':
                    statment[statment.current_test].mechanical_properties.u = u_array[i]
                if statment.general_parameters.test_mode == 'Трёхосное сжатие НН' or statment.general_parameters.test_mode == "Вибропрочность":
                    self.add_test_st_NN()
                else:
                    if statment.general_parameters.test_mode in ["Трёхосное сжатие (F, C, E)", 'Трёхосное сжатие (F, C, Eur)']:
                        self.current_kr_fgs_ind = i
                        self.add_test_st(pre_defined_kr_fgs=self.pre_defined_kr_fgs[i])
                    else:
                        self.add_test_st(pre_defined_kr_fgs=self.pre_defined_kr_fgs)

            self.pre_defined_kr_fgs = None

            statment[statment.current_test].mechanical_properties.sigma_3 = sigma_3_origin
            statment[statment.current_test].mechanical_properties.qf = qf_origin
            statment[statment.current_test].mechanical_properties.sigma_1 = sigma_1_origin
            statment[statment.current_test].mechanical_properties.E50 = E50_origin
            statment[statment.current_test].mechanical_properties.u = u_origin
            statment[statment.current_test].mechanical_properties.Eur = Eur_origin

        self._b_noise = np.round(np.random.uniform(0.95, 0.98), 2)
        self._test_processing()

    def set_test_params(self):
        self._test_modeling()

    def save_log_files(self, directory, name, sample_size=(76, 38), save_plaxis=False):
        """Метод генерирует файлы испытания для всех кругов"""

        data = {
            "laboratory_number": statment[statment.current_test].physical_properties.laboratory_number,
            "borehole": statment[statment.current_test].physical_properties.borehole,
            "ige": statment[statment.current_test].physical_properties.ige,
            "depth": statment[statment.current_test].physical_properties.depth,
            "sample_composition": "Н" if statment[statment.current_test].physical_properties.type_ground in [1,
                                                                                                             2,
                                                                                                             3,
                                                                                                             4,
                                                                                                             5] else "С",
            "b": self._b_noise,

            "test_data": {
            }
        }

        if len(self._tests) >= 1:
            i = 1
            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                path = os.path.join(directory, str(results["sigma_3"]))

                if not os.path.isdir(path):
                    os.mkdir(path)
                file_name = os.path.join(path, f"{name}.log")
                test.save_log_file(file_name, sample_size=sample_size, save_plaxis=save_plaxis)


                strain, main_stress, volume_strain = test.deviator_loading.get_cvi_data()

                data["test_data"][str(i)] = {
                    "main_stress": main_stress,
                    "strain": strain,
                    "volume_strain": volume_strain,
                    "sigma_3": np.round(test.deviator_loading._test_params.sigma_3 / 1000, 3)
                }

                i += 1

            save_cvi_FC(file_path=os.path.join(directory, f"{name} FC ЦВИ.xls"), data=data)


    @staticmethod
    def noise_for_mohrs_circles(sigma3, sigma1, fi, c):
        '''fi - в градусах, так что
        tan(np.deg2rad(fi)) - тангенс угла наклона касательной
        '''

        fi = np.tan(np.deg2rad(fi))

        # выбираем случайную окружность. считаем ее индекс:
        # Исправление: Вторая окружность никогда не меньше первой
        # поэтому выбираем из первой и тертьей
        fixed_circle_index = 1 # circles_pos[np.random.randint(0, 1)]  # np.random.randint(0, len(sigma1) - 1)

        # генерируем случайной значение
        a = np.random.uniform(np.min(sigma1 - sigma3) / 5, np.min(sigma1 - sigma3) / 4) / 2


        # создаем копию массива для зашумленных значений
        sigma1_with_noise = copy.deepcopy(sigma1)

        # добавляем шум к зафиксированной окружности
        if np.random.randint(0, 2) == 0:
            sigma1_with_noise[fixed_circle_index] -= a

        else:
            sigma1_with_noise[fixed_circle_index] += a

        def func(x):
            '''x - массив sigma_1 без зафиксированной окружности'''
            # возвращаем зафиксированную огружность для подачи в фукнцию mohr_cf_stab
            x = np.insert(x, fixed_circle_index, sigma1_with_noise[fixed_circle_index])
            # определяем новые фи и с для измененной окружности
            c_new, fi_new = ModelMohrCirclesSoilTest.mohr_cf_stab(sigma3, x)
            # критерий минимизации - ошибка между fi и c для несмещенных кругов
            return c_new - c, fi_new - fi

        # начальное приближение для расчета оставшихся sigma_1
        # задается через удаление зафиксированной окружности из массива
        # чтобы fsolve не изменял зафиксированную окружность
        initial = np.delete(sigma1_with_noise, fixed_circle_index)
        root = fsolve(func, initial)
        sigma1_with_noise = np.insert(root, fixed_circle_index, sigma1_with_noise[fixed_circle_index])
        qf_with_noise = sigma1_with_noise - sigma3
        c_new, fi_new = ModelMohrCirclesSoilTest.mohr_cf_stab(np.round(sigma3, 3), np.round(sigma1_with_noise, 3))
        return np.round(qf_with_noise, 1)

    @staticmethod
    def new_noise_for_mohrs_circles(sigma3: list, sigma1: list, fi: float, c: float, loops: int = 0) -> list:
        """ Генерация шума для кругов мора
        Аргументы:
            :param sigma3: массив sigma3 для количества кругов > 2
            :param sigma1: массив sigma1 для количества кругов > 2
            :param fi: угол внутреннего трения
            :param c: сцепление
            :param loops: число самозацикливаний
            :return: значение девиатора с шумом"""

        '''fi - в градусах, так что
        tan(np.deg2rad(fi)) - тангенс угла наклона касательной'''
        fi = np.tan(np.deg2rad(fi))

        fixed_circle_index = 1  # circles_pos[np.random.randint(0, 1)]  # np.random.randint(0, len(sigma1) - 1)

        # генерируем случайной значение
        a = np.random.uniform(np.min(sigma1 - sigma3) / 5, np.min(sigma1 - sigma3) / 4) / 2

        # создаем копию массива для зашумленных значений
        sigma1_with_noise = copy.deepcopy(sigma1)

        # добавляем шум к зафиксированной окружности
        if np.random.randint(0, 2) == 0:
            sigma1_with_noise[fixed_circle_index] -= a

        else:
            sigma1_with_noise[fixed_circle_index] += a

        def func(x):
            """x - массив sigma_1 без зафиксированной окружности"""
            # возвращаем зафиксированную огружность для подачи в фукнцию mohr_cf_stab
            x = np.insert(x, fixed_circle_index, sigma1_with_noise[fixed_circle_index])
            # определяем новые фи и с для измененной окружности
            c_new, fi_new = ModelMohrCirclesSoilTest.mohr_cf_stab(sigma3, x)
            # критерий минимизации - ошибка между fi и c для несмещенных кругов
            return abs(abs(c_new - c) + abs(100 * (fi_new - fi)))

        initial = np.delete(sigma1_with_noise, fixed_circle_index)
        from scipy.optimize import Bounds, minimize
        bnds = Bounds(np.zeros_like(initial), np.ones_like(initial) * np.inf)

        def constrains(x):
            """
            Функция ограничений на икс, должна подаваться в cons.
            Должна представлять собой массивы ограничений вида x1 - x2 >= 0
            """

            # икс для фукнции оптимизации это два круга, поэтому возвращаем в икс убранный круг
            x = np.insert(x, fixed_circle_index, sigma1_with_noise[fixed_circle_index])

            # первое ограничение - каждая последующая сигма не меньше предыдущей
            first = np.array([x[i + 1] - x[i] for i in range(len(x) - 1)])

            # замыкаем последний на первый на всякий случай
            second = np.array([x[-1] - x[0]])

            # здесь считаем тау - каждый следующий тау не меньше предыдущего (- погреность)
            EPS = 1
            third = np.array([(x[i + 1] - sigma3[i+1])/2 - (x[i] - sigma3[i])/2 - EPS for i in range(len(x) - 1)])

            res = np.hstack((first, second, third))
            return res

        cons = {'type': 'ineq',
                'fun': constrains}

        res = minimize(func, initial, method='SLSQP', constraints=cons, bounds=bnds, options={'ftol': 1e-9})
        # res = minimize(func, initial, method='SLSQP', constraints=cons, bounds=bnds,
        #                options={'ftol': 1e-9, 'maxiter': 50}) # отбойник на 50
        error = res.fun
        res = res.x
        sigma1_with_noise = np.insert(res, fixed_circle_index, sigma1_with_noise[fixed_circle_index])

        qf_with_noise = sigma1_with_noise - sigma3

        if np.any(qf_with_noise[1:] < qf_with_noise[:-1]):
            raise RuntimeWarning(f"Круги имеют ошибочные размеры : tau : {qf_with_noise / 2}")

        assert sum([abs(sigma1[i] - sigma1_with_noise[i]) < 10 ** (-1) for i in range(len(sigma1))]) < 2, \
            "Два круга не зашумлены!"

        if error > 5 and loops < 100:
            print(f'looping with error = {error}')
            loops = loops + 1
            qf_with_noise = ModelMohrCirclesSoilTest.new_noise_for_mohrs_circles(sigma3, sigma1, np.rad2deg(np.arctan(fi)), c, loops)

        return np.round(qf_with_noise, 1)

if __name__ == '__main__':

    param = {"ee": {'physical_properties': {'laboratory_number': '89-3', 'borehole': 89.0, 'depth': 6.0,
                                            'soil_name': 'Суглинок полутвёрдый', 'ige': None, 'rs': 2.71, 'r': 2.16,
                                            'rd': 1.89, 'n': 30.1, 'e': 0.43, 'W': 21.9, 'Sr': 0.88, 'Wl': 21.9,
                                            'Wp': 12.8,
                                            'Ip': 9.1, 'Il': 0.13, 'Ir': None, 'stratigraphic_index': None,
                                            'ground_water_depth': None, 'granulometric_10': None,
                                            'granulometric_5': None,
                                            'granulometric_2': None, 'granulometric_1': None, 'granulometric_05': None,
                                            'granulometric_025': None, 'granulometric_01': None,
                                            'granulometric_005': None,
                                            'granulometric_001': None, 'granulometric_0002': None,
                                            'granulometric_0000': None,
                                            'complete_flag': False, 'sample_number': 53, 'type_ground': 7, 'Rc': None},
                    'Cv': 0.128, 'Ca': 0.01126, 'm': 0.6, 'E50': 29600.0, 'c': 0.06, 'fi': 24.6, 'K0': 0.7,
                    'dilatancy_angle': 17.05, 'sigma_3': 100, 'qf': 329.5, 'sigma_1': 429.5, 'poisons_ratio': 0.34,
                    'OCR': 1,
                    'build_press': 150.0, 'pit_depth': 4.0, 'Eur': None}}
    a = ModelMohrCirclesSoilTest()
    a.set_test_params(param["ee"])
    a.set_reference_pressure_array([100, 200, 400])
    a._test_modeling()
    a.plotter()
    a.save_log_files("C:/Users/Пользователь/Desktop")
    plt.show()
