"""Модуль математических моделей статического трехосного нагружения. Содержит модели:
    ModelMohrCircles - модель обработчика кругов мора.
    Принцип работы:
        Опыты подаются в модель методом add_test(). Подается путь к файлу, После считывания данные передаются в
        обработчики частей опыта. Для удаления опытов используется метод dell_test
        Обработка опыта происходит методом _test_processing() после открытия хотя бы 3х опытов.
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelShearSoilTest - модель математического моделирования кругов мора.
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

from cvi.cvi_writer import save_cvi_shear
from shear_test.shear_dilatancy_test_model import ModelShearDilatancy, ModelShearDilatancySoilTest
from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, \
    mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_tau_max, \
    define_E50, create_json_file
from configs.plot_params import plotter_params
from singletons import statment, Shear_models

class ModelShear:
    """Класс моделирования опыта FCE"""
    def __init__(self):
        # Основные модели опыта
        self._tests = []
        self._test_data = AttrDict({"fi": None, "c": None})
        self._test_result = AttrDict({"fi": None, "c": None, "m": None})
        self._test_reference_params = AttrDict({"p_ref": None, "Eref": None})

    def add_test(self, file_path):
        """Добавление опытов"""
        test = ModelShearDilatancy()
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
            return test.get_test_results()["sigma"]

        if len(self._tests) >= 2:
            self._tests.sort(key=sort_key)

    def set_reference_params(self, p_ref, Eref):
        self._test_reference_params.p_ref = p_ref
        self._test_reference_params.Eref = Eref

    def get_sigma_tau_max(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 2:
            tau = []
            sigma = []

            for test in self._tests:
                results = test.get_test_results()
                sigma.append(np.round(results["sigma"], 3))
                tau.append(np.round(results["tau_max"], 3))
            return sigma, tau
        return None, None

    def get_sigma_u(self):
        """Получение массивов давлений грунтов"""
        pass
        # if len(self._tests) >= 2:
        #     u = []
        #     for test in self._tests:
        #         results = test.get_test_results()
        #         u.append(np.round(results["max_pore_pressure"]/1000, 3))
        #     return u
        return None

    def get_E50(self):
        """Получение массивов давлений грунтов"""
        # pass
        if len(self._tests) > 2:
            E50 = []

            for test in self._tests:
                results = test.get_test_results()
                E50.append(round(results["E50"], 3))
            return E50

        return None, None

    def _check_clone(self, check_test):
        """Проверяем, был ли открыт такой опыт уже"""
        for test in self._tests:
            if check_test.get_test_results()["sigma"] == \
                    test.get_test_results()["sigma"] and \
                    check_test.get_test_results()["tau_max"] == \
                    test.get_test_results()["tau_max"]:
                return False
        return True

    def _test_processing(self):
        """Обработка опытов"""
        sigma, tau = self.get_sigma_tau_max()
        if sigma is not None:

            c, fi = ModelShear.cf_shear([i*1000 for i in sigma], tau)

            self._test_result.c = np.round(c/1000, 3)
            self._test_result.fi = np.round(np.rad2deg(np.arctan(fi)), 1)# round(np.rad2deg(np.arctan(fi)), 1)

    def get_test_results(self):
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Подготовка данных для построения"""
        if len(self._tests) >= 3:
            strain = []
            deviator = []
            for test in self._tests:
                plots = test.get_plot_data()
                strain.append(plots["strain"])
                deviator.append(plots["deviator"])

            sigma, tau_max = self.get_sigma_tau_max()
            sigma = [i for i in sigma]
            tau_max = [i/1000. for i in tau_max]
            # mohr_x, mohr_y = ModelMohrCircles.mohr_circles(sigma_3, sigma_1)

            line_x = np.linspace(0, sigma[-1], 100)
            line_y = line(np.tan(np.deg2rad(self._test_result.fi)), self._test_result.c, line_x)

            x_lims = (0, np.max(sigma) * 1.1)
            y_lims = (0, np.max(tau_max) * 1.1)

            return {"strain": strain,
                    "deviator": deviator,
                    "sigma": sigma,
                    "tau_max": tau_max,
                    "mohr_line_x": line_x,
                    "mohr_line_y": line_y,
                    "x_lims": x_lims,
                    "y_lims": y_lims}
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
        ax_deviator.set_xlabel("Абсолютная деформация $l_1$, мм")
        ax_deviator.set_ylabel("Касательное напряжение τ, МПа")

        ax_cycles = figure.add_subplot(2, 1, 2)
        ax_cycles.grid(axis='both')
        ax_cycles.set_xlabel("Нормальное напряжение σ, МПа")
        ax_cycles.set_ylabel("Касательное напряжение τ, МПа")

        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots is not None:
            for i in range(len(plots["strain"])):
                ax_deviator.plot(plots["strain"][i], plots["deviator"][i], **plotter_params["main_line"])
                #ax_cycles.plot(plots["mohr_x"][i], plots["mohr_y"][i], **plotter_params["main_line"])

            lim = ax_deviator.get_xlim()
            h, d = self._test_data.equipment_sample_h_d
            if d == 71.4:
                xlim = 7.25
            elif d == 150:
                xlim = 16

            ax_deviator.set_xlim([lim[0], xlim])
            ax_cycles.scatter(plots["sigma"],plots["tau_max"],color=['r', 'r', 'r'])
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

    # @staticmethod
    # def mohr_cf(sigma3, sigma1, stab=False):
    #     """Расчет c и f. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""

    #     if stab == False:
    #         sig = list(map(lambda x, y: (x + y) / 2, sigma1, sigma3))
    #         t = list(map(lambda x, y: (x - y) / 2, sigma1, sigma3))
    #     else:
    #         sig = sigma3
    #         t = sigma1

    #     sigSum = sum(sig)
    #     tSum = sum(t)

    #     sigtSum = sum(list(map(lambda x, y: x * y, sig, t)))
    #     sigSqr = sum([v * v for v in sig])
    #     n = len(sigma3)
    #     if n == 1:
    #         fi = t[0] / sig[0]
    #         c = 0
    #     else:
    #         fi = (n * sigtSum - tSum * sigSum) / (n * sigSqr - sigSum * sigSum)
    #         c = (tSum * sigSqr - sigSum * sigtSum) / (n * sigSqr - sigSum * sigSum)

    #     return c, fi


    @staticmethod
    def cf_shear(sigma, tau):
        # непосредственно МНК имеем уравнение y = Ap
        _matrix_A = np.vstack([sigma, np.ones(len(sigma))]).T
        # определяем новые фи и с
        fi, c = np.linalg.lstsq(_matrix_A, tau, rcond=None)[0]
        return c, fi


    # @staticmethod
    # def mohr_cf_stab(sigma3, sigma1):
    #     """Расчет c и f. Сигма 1 и 3 задаются как массивы любых размеров, U задается как массив, либо как 0 или не задается вообще"""
    #     c, fi = ModelMohrCircles.mohr_cf(sigma3, sigma1, True)
    #     cS = c / (2 * (fi ** 0.5))
    #     phiS = ((fi - 1) / (2 * (fi ** 0.5)))
    #
    #     return cS, phiS

    @staticmethod
    def cf_stab(sigma, tau):
        # непосредственно МНК имеем уравнение y = Ap
        _matrix_A = np.vstack([sigma, np.ones(len(sigma))]).T
        # определяем новые фи и с
        fi, c = np.linalg.lstsq(_matrix_A, tau, rcond=None)[0]

    @staticmethod
    def calculate_m(sigma: List, E50: List, Eref: float, p_ref: float, c: float, fi: float) -> float:
        """Функция поиска степенного параметра упрочнения из нескольких опытов
        :param sigma_3 - массив обжимающих давлений
        :param E50 - массив модулей E50
        :param Eref - модуль деформации Е50 при референтном давлении
        :param p_ref - референтное давление"""

        fi = np.deg2rad(fi)

        def E50_from_sigma_3(sigma, m):
            return (Eref * ((c * np.cos(fi) + sigma * np.sin(fi)) / (
                    c * np.cos(fi) + p_ref * np.sin(fi))) ** m)

        popt, pcov = curve_fit(E50_from_sigma_3, sigma, E50)
        m = popt
        return np.round(m[0], 2)

class ModelShearSoilTest(ModelShear):
    """Класс моделирования опыта FCE"""
    def __init__(self):
        super().__init__()
        self._test_params = None
        self._reference_pressure_array = None

        self.pre_defined_kr_fgs = None

        self._noise_data = {}

    def add_test_st(self, pre_defined_xc=None):
        """Добавление опытов"""
        test = ModelShearDilatancySoilTest()
        test.set_test_params(pre_defined_xc=pre_defined_xc)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()

    def set_reference_pressure_array(self, reference_pressure_array):
        self._reference_pressure_array = reference_pressure_array

    def _test_modeling(self):
        self._tests = []
        self.set_reference_params(statment[statment.current_test].mechanical_properties.sigma, statment[statment.current_test].mechanical_properties.E50)

        self._reference_pressure_array = statment[statment.current_test].mechanical_properties.pressure_array["current"]

        sigma_array = []
        tau_array = []
        # sigma_1_array = []
        E50_array = []
        # if statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or statment.general_parameters.test_mode == 'Трёхосное сжатие НН':
        #     u_array = statment[statment.current_test].mechanical_properties.u
        # else:
        #     u_array = [0 for i in self._reference_pressure_array]

        sigma_origin = statment[statment.current_test].mechanical_properties.sigma
        # qf_origin = statment[statment.current_test].mechanical_properties.tau_max
        tau_origin = statment[statment.current_test].mechanical_properties.tau_max
        E50_origin = statment[statment.current_test].mechanical_properties.E50
        u_origin = statment[statment.current_test].mechanical_properties.u

        for num, sigma in enumerate(self._reference_pressure_array):
            sigma_array.append(sigma)
            tau_array.append(define_tau_max(sigma, statment[statment.current_test].mechanical_properties.c * 1000,
                                      statment[statment.current_test].mechanical_properties.fi))


        c = 0
        fi = 0

        current_c = np.round(statment[statment.current_test].mechanical_properties.c, 3)
        current_fi = np.round(statment[statment.current_test].mechanical_properties.fi, 1)

        # count = 0
        while True:
            if (c == current_c and fi == current_fi):
                break

            # if count > 5:
            #     break


            tau = ModelShearSoilTest.lse_faker(np.array(sigma_array),
                                               np.array(tau_array),
                                               statment[statment.current_test].mechanical_properties.fi,
                                               statment[statment.current_test].mechanical_properties.c * 1000)

            for i in range(len(tau)):
                tau_array[i] = round(tau[i], 3)
                # sigma_1_array[i] = round(qf_array[i] + sigma_3_array[i], 3)

                E50_array.append(define_E50(
                    statment[statment.current_test].mechanical_properties.E50,
                    statment[statment.current_test].mechanical_properties.c*1000,
                    statment[statment.current_test].mechanical_properties.fi,
                    sigma_array[i],
                    statment[statment.current_test].mechanical_properties.sigma,
                    statment[statment.current_test].mechanical_properties.m))


            c, fi = ModelShearSoilTest.cf_shear(
                [np.round(sigma , 3) for sigma in sigma_array],
                [np.round(tau, 3) for tau in tau_array])
                #[np.round(sigma_3/1000 - pore, 3) for sigma_3, pore in zip(sigma_3_array, u_origin)],
                #[np.round(sigma_1/1000 - pore, 3) for sigma_1, pore in zip(sigma_1_array, u_origin)])
            c = round(c/1000, 3)
            fi = round(np.rad2deg(np.arctan(fi)), 1)
            # count += 1

        # ПРОВЕРКА РАСПОЛОЖЕНИЯ ХС ДЛЯ ВСЕХ ТРЕХ ОПЫТОВ
        #   Проходим с конца по опытам и замеряем хс, если хс выходит за заданную границу, то снижаем коэф. сдвига
        #   см. ModelShearDilatancySoilTest.define_xc_value_residual_strength

        _if_xc_all = []  # 1, 0 есть пик или нет
        _xc_all = []  # значения хс
        _k_all = []  # коэф. коррекции к
        _phys = statment[statment.current_test].physical_properties

        # определяем есть ли "пики"
        for i, sigma in enumerate(sigma_array):
            # Если в предыдущем опыте есть пик, то пик будет в любом случае
            if len(_if_xc_all) == 0:
                _if_xc_all.append(ModelShearDilatancySoilTest.xc_from_qf_e_if_is(sigma, _phys.type_ground, _phys.e,
                                                                                 _phys.Ip, _phys.Il, _phys.Ir,
                                                                                 statment.general_parameters.test_mode))
            elif not _if_xc_all[-1]:
                _if_xc_all.append(ModelShearDilatancySoilTest.xc_from_qf_e_if_is(sigma, _phys.type_ground, _phys.e,
                                                                                 _phys.Ip, _phys.Il, _phys.Ir,
                                                                                 statment.general_parameters.test_mode))
            elif _if_xc_all[-1] == 1:
                _if_xc_all.append(1)

            # считаем xc
            if _if_xc_all[i]:
                _xc_all.append(ModelShearDilatancySoilTest.define_xc_qf_E(tau_array[i], E50_array[i]))
            else:
                _xc_all.append(0.15)

            # считаем коэф. коррекции
            if sigma <= 200:
                _k_all.append(1.2)
            elif sigma >= 200 and sigma < 500:
                _k_all.append(0.000333 * sigma + 1.1333)
            else:
                _k_all.append(1.3)

        # print(f"ХС ДО {_xc_all}")

        # Коррекция хс
        XC_LIM_k = 0.11
        XC_LIM_E = 0.11

        if _phys.Ip is not None and _phys.Il is not None:
            if (np.any(np.asarray(_xc_all) > XC_LIM_E) and np.any(np.asarray(_if_xc_all))) and\
                    ((_phys.Ip <= 7 and _phys.Il <= 0) or (_phys.Ip > 7 and _phys.Il <= 0.25)):
                # print('твердый')
                XC_LIM_E = 0.06

        for i in range(len(sigma_array) - 1, -1, -1):
            if not _if_xc_all[i]:
                continue

            indexes, = np.where(np.asarray([_xc_all[k] if _if_xc_all[k] else 0 for k in range(len(_xc_all))]) > XC_LIM_E)

            while len(indexes) > 0:
                rnd = np.random.uniform(1.4, 1.6)
                _E50 = ((1.37 / (XC_LIM_E-0.005))**10)**(1/8) * tau_array[indexes[0]] * rnd
                p_ref = sigma_array[indexes[0]]

                for j in range(len(E50_array)):
                    E50_array[j] = define_E50(_E50,
                                              statment[statment.current_test].mechanical_properties.c * 1000,
                                              statment[statment.current_test].mechanical_properties.fi,
                                              sigma_array[j],
                                              p_ref,
                                              statment[statment.current_test].mechanical_properties.m)
                    _xc_all[j] = ModelShearDilatancySoilTest.define_xc_qf_E(tau_array[j], E50_array[j])

                indexes, = np.where(np.asarray(_xc_all) > XC_LIM_E)

        # print(f"ХС ПОСЛЕ {_xc_all}")
        # теперь, заная есть ли пики и расположения хс можем провести коррекции
        # формируем итератор и движемся с конца, если при максимальном давлении кривая "помещается",
        # то поместятся и остальные
        for i in range(len(sigma_array) - 1, -1, -1):
            # пики дальше 0.14 игнорируем (фактически их не будет)
            if _xc_all[i] >= XC_LIM_k:
                continue

            while (_xc_all[i] * _k_all[i] > XC_LIM_k) and (_k_all[i] >= 1):
                # уменьшаем все коэффициенты меньше текущего (включая текущий) на 0.1 пока кривая не "войдет"
                _k_all = [_k_all[j] - 0.1 if j <= i else _k_all[j] for j in range(len(_k_all))]
        # если какой-то из k ушел меньше 1, то его нужно приравнять к 1
        for i in range(len(_k_all)):
            if _k_all[i] < 1:
                _k_all[i] = 1
            _xc_all[i] = _xc_all[i] * _k_all[i]

        for i in range(len(sigma_array)):
            statment[statment.current_test].mechanical_properties.sigma = sigma_array[i]
            statment[statment.current_test].mechanical_properties.tau_max = tau_array[i]
            # statment[statment.current_test].mechanical_properties.sigma_1 = sigma_1_array[i] + u_array[i]
            statment[statment.current_test].mechanical_properties.E50 = E50_array[i]
            # if statment.general_parameters.test_mode == 'Трёхосное сжатие КН' or statment.general_parameters.test_mode == 'Трёхосное сжатие НН':
            #     statment[statment.current_test].mechanical_properties.u = u_array[i]
            self.add_test_st(pre_defined_xc=_xc_all[i])

        statment[statment.current_test].mechanical_properties.sigma = sigma_origin
        statment[statment.current_test].mechanical_properties.tau_max = tau_origin
        # statment[statment.current_test].mechanical_properties.sigma_1 = sigma_1_origin
        statment[statment.current_test].mechanical_properties.E50 = E50_origin
        # statment[statment.current_test].mechanical_properties.u = u_origin

        self._test_processing()
        self.form_noise_data()

    def set_test_params(self):
        self._test_modeling()

    def form_noise_data(self):
        self._noise_data["b"] = np.round(np.random.uniform(0.95, 0.98), 2)

    def save_log_files(self, directory, nonzero_vertical_def=True):
        """Метод генерирует файлы испытания для всех кругов"""
        if len(self._tests) >= 3:
            for test in self._tests:
                results = test.get_test_results()
                path = os.path.join(directory, str(results["sigma"]))

                if not os.path.isdir(path):
                    os.mkdir(path)
                file_name = os.path.join(path, "Test.1.log")
                test.save_log_file(file_name, nonzero_vertical_def=nonzero_vertical_def)

    def save_cvi_file(self, file_path, file_name, isNaturalShear: bool = False):
        if isNaturalShear:
            b = statment[statment.current_test].physical_properties.Sr
        else:
            b = self._noise_data["b"]

        data = {
            "laboratory_number": statment[statment.current_test].physical_properties.laboratory_number,
            "borehole": statment[statment.current_test].physical_properties.borehole,
            "ige": statment[statment.current_test].physical_properties.ige,
            "depth": statment[statment.current_test].physical_properties.depth,
            "sample_composition": "Н" if statment[statment.current_test].physical_properties.type_ground in [1, 2, 3, 4,
                                                                                                             5] else "С",
            "b": b,

            "test_data": {
            }
        }
        if len(self._tests) >= 3:
            i = 1
            for test in self._tests:
                tau, absolute_deformation, tau_fail = test.get_cvi_data()

                data["test_data"][str(i)] = {
                    "tau": tau,
                    "absolute_deformation": absolute_deformation,
                    "tau_fail": tau_fail,
                    "sigma": np.round(test._test_params.sigma / 1000, 3)
                }

                i += 1

        save_cvi_shear(file_path=os.path.join(file_path, file_name), data=data)

    @staticmethod
    def lse_faker(sigma: np.array, tau: np.array, fi: float, c: float):
        """

        """
        # fi - в градусах, так что переводим в радианы
        # tan(np.deg2rad(fi)) - тангенс угла наклона касательной'''
        fi = np.tan(np.deg2rad(fi))

        # Если выбирать точку произвольно то
        # придется присать ограничения cons на расположения точек
        # после добавления шума
        fixed_point_index = 1

        noise = abs(tau[fixed_point_index]-tau[0]) * 0.2

        tau_with_noise = copy.deepcopy(tau)

        # добавляем шум к зафиксированной точке
        if np.random.randint(0, 2) == 0:
            tau_with_noise[fixed_point_index] -= noise
        else:
            tau_with_noise[fixed_point_index] += noise

        # for i in range(len(tau_with_noise)):
        #     if i == fixed_point_index:
        #         continue
        #     if i % 2 == 0:
        #         tau_with_noise += noise/4
        #     else:
        #         tau_with_noise -= noise/4

        def func(x):
            """x - массив tau без зафиксированной точки"""
            # возвращаем зафиксированную точку для подачи в метод наименьших квадратов (МНК)
            x = np.insert(x, fixed_point_index, tau_with_noise[fixed_point_index])
            # непосредственно МНК имеем уравнение y = Ap
            # _matrix_A = np.vstack([sigma, np.ones(len(sigma))]).T
            # определяем новые фи и с
            # _fi_new, _c_new = np.linalg.lstsq(_matrix_A, x, rcond=None)[0]
            _c_new, _fi_new = ModelShear.cf_shear(sigma, x)
            # критерий минимизации - ошибка между fi и c
            return abs(abs((_c_new - c)) + abs(100 * (_fi_new - fi)))

        initial = np.delete(tau_with_noise, fixed_point_index)
        from scipy.optimize import Bounds, minimize

        bnds = Bounds(np.zeros_like(initial), np.ones_like(initial) * np.inf)
        '''Граничные условия типа a <= xi <= b'''

        def constrains(x):
            """
            Функция ограничений на икс, должна подаваться в cons.
            Должна представлять собой массивы ограничений вида x1 - x2 < 0
            """

            # икс для фукнции оптимизации это два круга, поэтому возвращаем в икс убранный круг
            x = np.insert(x, fixed_point_index, tau_with_noise[fixed_point_index])

            # первое ограничение - каждая последующая сигма не меньше предыдущей
            first = np.array([x[i + 1] - x[i] for i in range(len(x) - 1)])

            # замыкаем последний на первый на всякий случай
            second = np.array([x[-1] - x[0]])

            _res = np.hstack((first, second))
            return _res

        cons = {'type': 'ineq',
                'fun': constrains
                }
        '''Нелинейные ограничения типа cj(x)>=0'''

        res = minimize(func, initial, method='SLSQP', constraints=cons, bounds=bnds, options={'ftol': 1e-8})
        res = res.x

        # Результат:
        tau_with_noise = np.insert(res, fixed_point_index, tau_with_noise[fixed_point_index])
        # Проверка:
        matrix_A = np.vstack([sigma, np.ones(len(sigma))]).T
        fi_new, c_new = np.linalg.lstsq(matrix_A, np.round(tau_with_noise, 3), rcond=None)[0]

        # print(f"Было:\n {np.round(np.rad2deg(np.arctan(fi)),1)}, {np.round(c,3)} "
        #       f"Стало:\n {np.round(np.rad2deg(np.arctan(fi_new)),1)}, {np.round(c_new,3)}")
        # plt.scatter(sigma, tau_with_noise, color=['r', 'r', 'r'])

        return np.round(tau_with_noise, 3)

if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"

    """a = ModelShearDilatancy()
    from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad
    a.set_test_data(ModelTriaxialStaticLoad.open_geotek_log(file)["shear_dilatancy"])
    a.plotter()
    plt.show()"""
    a = ModelShearSoilTest()
    statment.load(r"C:\Users\Пользователь\Documents\Срез природное.pickle")
    statment.current_test = "89-4"
    a.set_test_params()
    a.plotter()
    plt.show()


