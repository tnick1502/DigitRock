import os
import copy
import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
from scipy.optimize import Bounds, minimize

from general.general_functions import AttrDict


class ModelK0:
    """Модель обработки резонансной колонки
    Логика работы:
        - Данные принимаются в set_test_data()

        - Обработка опыта производится методом _test_processing.

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""

    def __init__(self):
        """Определяем основную структуру данных"""
        # Структура дынных
        self.test_data = AttrDict({"sigma_1": None, "sigma_3": None})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None, "right": None})

        # Результаты опыта
        self._test_result = AttrDict({"K0": None, "M": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        if "sigma_1" not in test_data or "sigma_3" not in test_data:
            raise RuntimeWarning("test_data должен содержать sigma_1 и sigma_3")

        self.test_data.sigma_1 = test_data["sigma_1"]
        self.test_data.sigma_3 = test_data["sigma_3"]

        self._test_cut_position.left = 0
        self._test_cut_position.right = len(self.test_data.sigma_3)

        self._test_processing()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_result.get_dict()

    def open_path(self, path):
        data = {}
        for dirpath, dirs, files in os.walk(path):
            for filename in files:
                if filename == "RCCT.txt":
                    data.update(ModelK0.open_K0_log(os.path.join(os.path.join(dirpath, filename))))
        self.set_test_data(data)

    def set_borders(self, left, right):
        """Выделение границ для обрезки значений всего опыта"""
        if (right - left) >= 3:
            self._test_cut_position.left = left
            self._test_cut_position.right = right
            self._test_processing()

    def _test_processing(self):
        """Обработка опыта"""
        try:
            sigma_1_cut = self.test_data.sigma_1[self._test_cut_position.left: self._test_cut_position.right]
            sigma_3_cut = self.test_data.sigma_3[self._test_cut_position.left: self._test_cut_position.right]
            self._test_result.K0, self._test_result.M = ModelK0.define_ko(sigma_3_cut, sigma_1_cut)
        except:
            #app_logger.exception("Ошибка обработки данных РК")
            pass

    def get_plot_data(self):
        """Возвращает данные для построения"""
        if self.test_data.sigma_1 is None or self.test_data.sigma_3 is None:
            return None
        else:
            sigma_1_cut = self.test_data.sigma_1[self._test_cut_position.left: self._test_cut_position.right]
            sigma_3_cut = self.test_data.sigma_3[self._test_cut_position.left: self._test_cut_position.right]

            first_point = sigma_3_cut[0] + (sigma_3_cut[1] - sigma_3_cut[0]) * np.random.uniform(0., 1.)
            k0_line_x = np.linspace(first_point, sigma_3_cut[-1]*1.05)
            k0_line_y = 1/self._test_result.K0 * (k0_line_x - self._test_result.M)
            return {
                "sigma_1": sigma_1_cut,
                "sigma_3": sigma_3_cut,
                "k0_line_x": k0_line_x,
                "k0_line_y": k0_line_y
            }

    def plotter(self, save_path=None):
        """Построение графиков опыта. Если передать параметр save_path, то графики сохраняться туда"""
        plot_data = self.get_plot_data()
        res = self.get_test_results()

        if plot_data:
            figure = plt.figure()
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.2, hspace=0.2, left=0.08)

            ax_K0 = figure.add_subplot(1, 1, 1)
            ax_K0.set_xlabel("Вертикальное напряжение __, МПа")
            ax_K0.set_ylabel("Горизонтальное напряжение __, МПа")

            ax_K0.scatter(plot_data["sigma_3"], plot_data["sigma_1"], label="test data", color="tomato")
            ax_K0.plot(plot_data["k0_line_x"], plot_data["k0_line_y"], label="approximate data")

            ax_K0.scatter([], [], label="$K0$" + " = " + str(res["K0"]), color="#eeeeee")

            ax_K0.legend()

            if save_path:
                try:
                    plt.savefig(save_path, format="png")
                except:
                    pass

            plt.show()

    @staticmethod
    def open_K0_log(file_path):

        test_data = {"sigma_1": np.array([]), "sigma_3": np.array([])}

        columns_key = ['ShearStrain1[]', 'G1[MPa]']

        # Считываем файл
        with open(file_path) as file:
            lines = file.readlines()

        # Словарь считанных данных по ключам колонок
        read_data = {}

        for key in columns_key:  # по нужным столбцам
            index = (lines[0].split("; ").index(key))  #
            read_data[key] = np.array(list(map(lambda x: float(x.split("; ")[index]), lines[1:])))

        test_data["sigma_1"] = read_data['ShearStrain1[]']
        test_data["sigma_3"] = read_data['G1[MPa]']

        return test_data

    @staticmethod
    def define_ko(sigma_3, sigma_1, no_round=False):
        """
        сигма3 = к0 * сигма1 + М
        поэтому мы меняем местами сигму3 и сигму1
        при печати мы будем делать обратную замену

        :param sigma_3: array-like
        :param sigma_1: array-like
        :param no_round: bool, True - если необходимо не округлять результат
        :return: defined_k0 и defined_m
        """
        sigma_1 = np.asarray(sigma_1)
        sigma_3 = np.asarray(sigma_3)

        defined_k0, defined_m = ModelK0.lse_linear_estimation(sigma_1, sigma_3)
        return (defined_k0, defined_m) if no_round else (round(defined_k0, 2), round(defined_m, 2))

    @staticmethod
    def lse_linear_estimation(__x, __y):
        """
        Выполняет МНК приближение прямой вида kx+b к набору данных

        :param __x: array-like, координаты х
        :param __y: array-like, координаты y
        :return: float, коэффициенты k и b
        """

        __x = np.asarray(__x)
        __y = np.asarray(__y)

        A = np.vstack([__x, np.ones(len(__x))]).T

        k, b = lstsq(A, __y, rcond=None)[0]

        return k, b


class ModelK0SoilTest(ModelK0):
    """
    Модель моделирования девиаторного нагружения
    Наследует обработчик и структуру данных из ModelTriaxialDeviatorLoading

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта
    """
    def __init__(self):
        super().__init__()

        self._test_params = AttrDict({"K0": None,
                                      "M": None,
                                      "sigma_1_step": None,
                                      "sigma_1_max": None})

    def set_test_params(self, test_params=None):
        if test_params:
            self._test_params.K0 = test_params["K0"]
            self._test_params.M = test_params["M"]
            self._test_params.sigma_1_step = test_params["sigma_1_step"]
            self._test_params.sigma_1_max = test_params["sigma_1_max"]
        else:
            pass
            # statment[statment.current_test].mechanical_properties.K0

        self._test_modeling()

    def set_draw_params(self, params):
        """Считывание параметров отрисовки(для передачи на слайдеры)"""
        # self._draw_params.G0_ratio = params["G0_ratio"]
        # self._draw_params.threshold_shear_strain_ratio = params["threshold_shear_strain_ratio"]
        self._test_params.K0 = params["K0"]
        self._test_params.M = params["M"]

        self._test_modeling()

    def _test_modeling(self):
        delta_sigma_1 = self._test_params.sigma_1_max  # + self._test_params.M - self._test_params.M
        num = int(delta_sigma_1/self._test_params.sigma_1_step) + 1
        sgima_1_synth = np.linspace(self._test_params.M, self._test_params.sigma_1_max+self._test_params.M, num)
        sgima_3_synth = self._test_params.K0 * sgima_1_synth + self._test_params.M

        sigma_1, sigma_3 = ModelK0SoilTest.lse_faker(sgima_1_synth, sgima_3_synth,
                                                     self._test_params.K0, self._test_params.M)

        self.set_test_data({"sigma_1": sigma_1, "sigma_3": sigma_3})

    @staticmethod
    def lse_faker(sigma_1: np.array, sigma_3: np.array, K0: float, M: float):
        """

        """

        # Если выбирать точку произвольно то
        # придется присать ограничения cons на расположения точек
        # после добавления шума
        fixed_point_index = 1

        noise = abs(sigma_3[fixed_point_index] - sigma_3[0]) * 0.4

        sigma_3_noise = copy.deepcopy(sigma_3)

        # добавляем шум к зафиксированной точке
        if np.random.randint(0, 2) == 0:
            sigma_3_noise[fixed_point_index] -= noise
        else:
            sigma_3_noise[fixed_point_index] += noise

        # накладываем шумы на всю сигму
        for i in range(1, len(sigma_3_noise)):
            if i % 2 == 0:
                sigma_3_noise[i] += noise / 4
            else:
                sigma_3_noise[i] -= noise / 4

        def func(x):
            """x - массив sigma_3 без зафиксированной точки"""
            # возвращаем зафиксированную точку для подачи в МНК
            x = np.insert(x, fixed_point_index, sigma_3_noise[fixed_point_index])
            x[0] = M  # оставляем первую точку на месте
            _K0_new, _M_new = ModelK0.define_ko(x, sigma_1, no_round=True)
            return abs(abs((_M_new - M)) + abs((_K0_new - K0)))

        initial = np.delete(sigma_3_noise, fixed_point_index)
        bnds = Bounds(np.zeros_like(initial), np.ones_like(initial) * np.inf)
        '''Граничные условия типа a <= xi <= b'''
        cons = {'type': 'ineq',
                'fun': lambda x: np.hstack((np.array([x[ind] for ind in range(len(x))]),
                                            np.array([x[ind+1] - x[ind] for ind in range(len(x) - 1)])))
                }
        '''Нелинейные ограничения типа cj(x)>=0'''

        res = minimize(func, initial, method='SLSQP', constraints=cons, bounds=bnds, options={'ftol': 0})
        res = res.x

        # Результат:
        sigma_3_noise = np.insert(res, fixed_point_index, sigma_3_noise[fixed_point_index])
        sigma_3_noise[0] = M
        # Проверка:
        K0_new, M_new = ModelK0.define_ko(sigma_3_noise, sigma_1)

        print(f"Было:\n{K0}, {M}\n"
              f"Стало:\n{K0_new}, {M_new}")

        if K0 != K0_new:
            raise RuntimeWarning("Слишком большая ошибка в К0")

        return sigma_1, sigma_3_noise


# _test_params = {"K0": 0.42, "M": 0.1, "sigma_1_step": 0.2, "sigma_1_max": 2.0}
# model = ModelK0SoilTest()
# model.set_test_params(_test_params)
# model.plotter()
