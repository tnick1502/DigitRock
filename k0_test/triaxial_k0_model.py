import os
import copy
import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
from scipy.optimize import Bounds, minimize
from scipy.interpolate import make_interp_spline

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
        self._test_result = AttrDict({"K0": None, "sigma_p": None})

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
            self._test_result.K0, self._test_result.sigma_p = ModelK0.define_ko(sigma_1_cut, sigma_3_cut)
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
            k0_line_x = np.linspace(first_point, sigma_3_cut[-1] * 1.001)
            k0_line_y = 1/self._test_result.K0 * (k0_line_x - self._test_result.sigma_p)
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
    def define_ko(sigma_1, sigma_3, no_round=False):
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

        defined_k0, defined_sigma_p = ModelK0.lse_linear_estimation(sigma_1, sigma_3)
        return (defined_k0, defined_sigma_p) if no_round else (round(defined_k0, 2), round(defined_sigma_p, 2))

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
                                      "OCR": None,
                                      "depth": None,
                                      "sigma_1_step": None,
                                      "sigma_1_max": None})

    def set_test_params(self, test_params=None):
        if test_params:
            self._test_params.K0 = test_params["K0"]

            try:
                self._test_params.OCR = test_params["OCR"]
            except KeyError:
                self._test_params.OCR = np.random.uniform(1, 2.5)

            try:
                self._test_params.depth = test_params["depth"]
            except KeyError:
                self._test_params.depth = 1

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
        self._test_params.OCR = params["OCR"]

        self._test_modeling()

    def _test_modeling(self):
        # определяем точку перегиба
        _sigma_p, _sigma_3_p = self.define_sigma_p()

        # формируем прямолинейный участок
        delta_sigma_1 = self._test_params.sigma_1_max - _sigma_p  # + self._test_params.sigma_p - self._test_params.sigma_p
        num = int(delta_sigma_1/self._test_params.sigma_1_step) + 1
        sgima_1_synth = np.linspace(0, self._test_params.sigma_1_max - _sigma_p, num) + _sigma_p
        sgima_3_synth = self._test_params.K0 * (sgima_1_synth - _sigma_p) + _sigma_3_p

        # накладываем шум на прямолинейный участок
        sigma_1, sigma_3 = ModelK0SoilTest.lse_faker(sgima_1_synth, sgima_3_synth,
                                                     self._test_params.K0, _sigma_3_p)

        # формируем криволинейный участок если есть бытовое давление
        if _sigma_p > 0:
            bounds = ([(2, 0.0)], [(1, 1/self._test_params.K0)])
            spl = make_interp_spline([0, sgima_3_synth[0]], [0, sgima_1_synth[0]], k=3, bc_type=bounds)

            sigma_3_spl = np.linspace(0, sgima_3_synth[0], int(delta_sigma_1/self._test_params.sigma_1_step) + 1)
            sigma_1_spl = spl(sigma_3_spl)

            # соединяем
            sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1))
            sigma_3 = np.hstack((sigma_3_spl[:-1], sigma_3))

        self.set_test_data({"sigma_1": sigma_1, "sigma_3": sigma_3})

    def define_sigma_p(self):
        # бытовое давление (точка перегиба) определяется из OCR через ro*g*h, где h - глубина залгания грунта
        sigma_p = self._test_params.OCR * 2 * 10 * self._test_params.depth
        # сигма 3 при этом давлении неизвестно, но мы знаем, что наклон точно больше, чем наклон прямолинейного участка
        sigma_3_p = self._test_params.K0 * (1/np.random.uniform(2.5, 3.0)) * sigma_p

        # значения получаем в кпа, поэтому делим на 1000

        return sigma_p/1000, sigma_3_p/1000

    @staticmethod
    def lse_faker(sigma_1: np.array, sigma_3: np.array, K0: float, sigma_3_p: float):
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
            if i == fixed_point_index:
                continue
            if i % 2 == 0:
                sigma_3_noise[i] += noise / 4
            else:
                sigma_3_noise[i] -= noise / 4

        def func(x):
            """x - массив sigma_3 без зафиксированной точки"""
            # возвращаем зафиксированную точку для подачи в МНК
            x = np.insert(x, fixed_point_index, sigma_3_noise[fixed_point_index])
            x[0] = sigma_3_p  # оставляем первую точку на месте
            _K0_new, _sigma_p_new = ModelK0.define_ko(sigma_1, x, no_round=True)
            return abs(_K0_new - K0)

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
        sigma_3_noise[0] = sigma_3_p
        # Проверка:
        K0_new, sigma_p_new = ModelK0.define_ko(sigma_1, sigma_3_noise)

        print(f"Было:\n{K0}\n"
              f"Стало:\n{K0_new}")

        if K0 != K0_new:
            raise RuntimeWarning("Слишком большая ошибка в К0")

        return sigma_1, sigma_3_noise
