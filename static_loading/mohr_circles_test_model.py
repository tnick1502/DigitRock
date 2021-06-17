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
from scipy.optimize import fsolve

from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad, ModelTriaxialStaticLoadSoilTest
from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from general.plot_params import plotter_params


class ModelMohrCircles:
    """Класс моделирования опыта FCE"""
    def __init__(self):
        # Основные модели опыта
        self._tests = []
        self._test_data = AttrDict({"fi": None, "c": None})
        self._test_result = AttrDict({"fi": None, "c": None})

    def add_test(self, file_path):
        """Добавление опытов"""
        test = ModelTriaxialStaticLoad()
        test_data = ModelTriaxialStaticLoad.open_geotek_log(file_path)
        test.set_test_data(test_data)
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

    def get_sigma_3_1(self):
        """Получение массивов давлений грунтов"""
        if len(self._tests) >= 2:
            sigma_1 = []
            sigma_3 = []

            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                sigma_3.append(round((results["sigma_3"] - results["u"]), 3))
                sigma_1.append(round(results["sigma_3"] + results["qf"] - results["u"], 3))
            return sigma_3, sigma_1

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
        sigma_3, sigma_1 = self.get_sigma_3_1()

        if sigma_3 is not None:
            c, fi = ModelMohrCircles.mohr_cf_stab(sigma_3, sigma_1)
            self._test_result.c = round(np.arctan(c), 3)
            self._test_result.fi = round(np.rad2deg(np.arctan(fi)), 1)# round(np.rad2deg(np.arctan(fi)), 1)

    def get_test_results(self):
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Подготовка данных для построения"""
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

            return {"strain": strain,
                    "deviator": deviator,
                    "mohr_x": mohr_x,
                    "mohr_y": mohr_y,
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

            ax_cycles.set_xlim(*plots["x_lims"])
            ax_cycles.set_ylim(*plots["y_lims"])

            ax_cycles.legend()

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass

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

class ModelMohrCirclesSoilTest(ModelMohrCircles):
    """Класс моделирования опыта FCE"""
    def __init__(self):
        super().__init__()
        self._test_params = None
        self._reference_pressure_array = None

    def add_test(self, params):
        """Добавление опытов"""
        test = ModelTriaxialStaticLoadSoilTest()
        test.set_test_params(params)
        if self._check_clone(test):
            self._tests.append(test)
            self.sort_tests()
            self._test_processing()

    def set_test_params(self, params):
        self._test_params = params

    def set_reference_pressure_array(self, reference_pressure_array):
        self._reference_pressure_array = reference_pressure_array

    def _test_modeling(self):
        if self._test_params is not None and self._reference_pressure_array is not None:

            self._tests = []

            mohr_params = []
            for num, sigma_3 in enumerate(self._reference_pressure_array):
                mohr_params.append(copy.copy(self._test_params))
                mohr_params[num]["sigma_3"] = sigma_3
                mohr_params[num]["qf"] = define_qf(sigma_3, self._test_params["c"], self._test_params["fi"])
                mohr_params[num]["sigma_1"] = round(mohr_params[num]["qf"] + mohr_params[num]["sigma_3"])

            c = 0
            fi = 0

            while True:
                if (c == round(self._test_params["c"], 3) and fi == round(self._test_params["fi"], 1)):
                    break

                qf = ModelMohrCirclesSoilTest.new_noise_for_mohrs_circles(
                    np.array([param["sigma_3"] for param in mohr_params]),
                    np.array([param["sigma_1"] for param in mohr_params]), self._test_params["fi"],
                    self._test_params["c"] * 1000)

                for i in range(len(qf)):
                    mohr_params[i]["qf"] = round(qf[i], 3)
                    mohr_params[i]["sigma_1"] = round(mohr_params[i]["qf"] + mohr_params[i]["sigma_3"], 3)
                    mohr_params[i]["E"] = define_E50(self._test_params["E"], self._test_params["c"] * 1000,
                                                     self._test_params["fi"], mohr_params[i]["sigma_3"],
                                                     self._test_params["sigma_3"], self._test_params["m"])

                #print(mohr_params[0]["sigma_1"])
                #print(mohr_params[1]["sigma_1"])
                #print(mohr_params[2]["sigma_1"])

                c, fi = ModelMohrCirclesSoilTest.mohr_cf_stab([x["sigma_3"]/1000 for x in mohr_params],
                                                                   [x["sigma_1"]/1000 for x in mohr_params])
                c = round(np.arctan(c), 3)
                fi = round(np.rad2deg(np.arctan(fi)), 1)

            for param in mohr_params:
                self.add_test(param)
            #print(self.get_sigma_3_1())

    def save_log_files(self, directory):
        """Метод генерирует файлы испытания для всех кругов"""
        if len(self._tests) >= 3:
            for test in self._tests:
                results = test.deviator_loading.get_test_results()
                file_name = os.path.join(directory, str(results["sigma_3"]) + ".log")
                test.save_log_file(file_name)

    @staticmethod
    def new_noise_for_mohrs_circles(sigma3, sigma1, fi, c):
        '''fi - в градусах, так что
        tan(np.deg2rad(fi)) - тангенс угла наклона касательной
        '''

        fi = np.tan(np.deg2rad(fi))

        # выбираем случайную окружность. считаем ее индекс:
        fixed_circle_index = np.random.randint(0, len(sigma1) - 1)

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

        return np.round(qf_with_noise, 1)


if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"
    #file = r"C:\Users\Пользователь\Desktop\Девиаторное нагружение\Архив\7а-1\Test sigma3=186.4.log"
    #a = ModelTriaxialStaticLoading()
    #a.set_test_data(openfile(file)["DeviatorLoading"])
    #a.plotter()



    #file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1375\Test\Test.1.log"

    #a = ModelTriaxialConsolidationSoilTest()
    #a.set_test_params({"Cv": 0.178,
                       #"Ca": 0.0001,
                      # "E": 50000,
                      # "sigma_3": 100,
                      # "K0": 1})
    #a.plotter()
    #a = ModelTriaxialReconsolidation()
    #a.open_file(file)
    #open_geotek_log(file)

    #a = ModelTriaxialStaticLoadSoilTest()
    param = {'E': 30495, 'sigma_3': 170, 'sigma_1': 800, 'c': 0.025, 'fi': 45, 'qf': 700, 'K0': 0.5,
             'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'build_press': 500.0, 'pit_depth': 7.0, 'Eur': '-',
             'dilatancy': 4.95, 'OCR': 1, 'm': 0.61, 'lab_number': '7а-1', 'data_phiz': {'borehole': '7а',
                                                                                             'depth': 19.0, 'name': 'Песок крупный неоднородный', 'ige': '-', 'rs': 2.73, 'r': '-', 'rd': '-', 'n': '-', 'e': '-', 'W': 12.8, 'Sr': '-', 'Wl': '-', 'Wp': '-', 'Ip': '-', 'Il': '-', 'Ir': '-', 'str_index': '-', 'gw_depth': '-', 'build_press': 500.0, 'pit_depth': 7.0, '10': '-', '5': '-', '2': 6.8, '1': 39.2, '05': 28.0, '025': 9.2, '01': 6.1, '005': 10.7, '001': '-', '0002': '-', '0000': '-', 'Nop': 7, 'flag': False}, 'test_type': 'Трёхосное сжатие (E)'}


    a = ModelMohrCirclesSoilTest()
    a.set_test_params(param)
    a.set_reference_pressure_array([100, 200, 400])
    a._test_modeling()
    a.plotter()
    a.save_log_files("C:/Users/Пользователь/Desktop")
    plt.show()


