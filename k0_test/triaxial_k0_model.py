import os
import copy
import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
from scipy.optimize import Bounds, minimize
from scipy.interpolate import make_interp_spline

from general.general_functions import AttrDict
from singletons import statment


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
            line_shift = 0.050  # сдвиги для отображения кривой

            index_sigma_p, = np.where(self.test_data.sigma_1 >= self._test_result.sigma_p)
            index_sigma_p = index_sigma_p[0] if len(index_sigma_p) > 0 else 0

            sigma_1_cut = self.test_data.sigma_1[index_sigma_p:]
            sigma_3_cut = self.test_data.sigma_3[index_sigma_p:]

            first_point = sigma_1_cut[0] + line_shift
            k0_line_sigma_1 = np.linspace(first_point, sigma_1_cut[-1] + line_shift)
            b = sigma_3_cut[0] - sigma_1_cut[0] * self._test_result.K0

            k0_line_sigma_3 = self._test_result.K0 * k0_line_sigma_1 + b

            return {"sigma_1": self.test_data.sigma_1,
                    "sigma_3": self.test_data.sigma_3,
                    "k0_line_x": k0_line_sigma_3,
                    "k0_line_y": k0_line_sigma_1}

    def plotter(self, save_path=None):
        """Построение графиков опыта. Если передать параметр save_path, то графики сохраняться туда"""
        plot_data = self.get_plot_data()
        res = self.get_test_results()

        if plot_data:
            figure = plt.figure()
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.2, hspace=0.2, left=0.08)

            ax_K0 = figure.add_subplot(1, 1, 1)
            ax_K0.set_xlabel("Горизонтальное напряжение __, МПа")
            ax_K0.set_ylabel("Вертикальное напряжение __, МПа")

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

        :param sigma_3: array-like
        :param sigma_1: array-like
        :param no_round: bool, True - если необходимо не округлять результат
        :return: defined_k0 и defined_m
        """
        sigma_1 = np.asarray(sigma_1)
        sigma_3 = np.asarray(sigma_3)

        lse_pnts = 4

        if len(sigma_1) <= lse_pnts:
            defined_k0, *__ = ModelK0.lse_linear_estimation(sigma_1, sigma_3)
            defined_sigma_p = sigma_1[-lse_pnts]
            return (defined_k0, defined_sigma_p) if no_round else (round(defined_k0, 2), defined_sigma_p)

        # Итеративнй поиск прямолинейного участка с конца:
        #   1. Считаем к0 по последним lse_pnts точкам
        #   2. Сравниваем МНК ошибку с предыдущей
        #   3. Если ошибка выросла более чем на 100%, то завершаем поиск прямой
        #

        current_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])
        prev_residuals = residuals

        while lse_pnts < len(sigma_1):
            lse_pnts = lse_pnts + 1
            current_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])

            if residuals > prev_residuals and abs(residuals - prev_residuals)/prev_residuals*100 > 100:
                lse_pnts = lse_pnts - 1
                break
            prev_residuals = residuals

        # Считаем полученный к0 по отобранным точкам
        defined_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])

        # Сигма точки перегиба можем взять прям из данных
        defined_sigma_p = sigma_1[-lse_pnts]

        return (defined_k0, defined_sigma_p) if no_round else (round(defined_k0, 2), defined_sigma_p)

    @staticmethod
    def lse_linear_estimation(__x, __y):
        """
        Выполняет МНК приближение прямой вида kx+b к набору данных

        :param __x: array-like, координаты х
        :param __y: array-like, координаты y
        :return: float, коэффициенты k, b и ошибка
        """

        __x = np.asarray(__x)
        __y = np.asarray(__y)

        A = np.vstack([__x, np.ones(len(__x))]).T

        res = lstsq(A, __y, rcond=None)
        k, b = res[0]
        residuals = res[1]

        return k, b, residuals


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
                                      "sigma_p": None,
                                      "sigma_3_p": None,
                                      "sigma_1_step": None,
                                      "sigma_1_max": None})

    def set_test_params(self, test_params=None):
        if test_params:
            try:
                self._test_params.K0 = test_params["K0"]
            except KeyError:
                self._test_params.K0 = 0.5
            try:
                self._test_params.OCR = test_params["OCR"]
            except KeyError:
                self._test_params.OCR = np.random.uniform(1, 2.5)
            try:
                self._test_params.depth = test_params["depth"]
            except KeyError:
                self._test_params.depth = 1
            try:
                self._test_params.sigma_1_step = test_params["sigma_1_step"]
            except KeyError:
                self._test_params.sigma_1_step = 0.200
            try:
                self._test_params.sigma_1_max = test_params["sigma_1_max"]
            except KeyError:
                self._test_params.sigma_1_max = 2.0
            try:
                self._test_params.sigma_p = test_params["sigma_p"]
            except KeyError:
                self._test_params.sigma_p = 0
            try:
                self._test_params.sigma_3_p = test_params["sigma_3_p"]
            except KeyError:
                self._test_params.sigma_3_p = 0
        else:
            self._test_params.K0 = statment[statment.current_test].mechanical_properties.K0
            self._test_params.OCR = statment[statment.current_test].mechanical_properties.OCR
            self._test_params.depth = statment[statment.current_test].physical_properties.depth

            self._test_params.sigma_1_step = statment[statment.current_test].mechanical_properties.sigma_1_step
            self._test_params.sigma_1_max = statment[statment.current_test].mechanical_properties.sigma_1_max

            self._test_params.sigma_p = statment[statment.current_test].mechanical_properties.sigma_p
            self._test_params.sigma_3_p = statment[statment.current_test].mechanical_properties.sigma_3_p

        self._test_modeling()

    def set_draw_params(self, params):
        """Считывание параметров отрисовки(для передачи на слайдеры)"""
        from excel_statment.properties_model import K0Properties

        self._test_params.K0 = round(params["K0"], 2)
        self._test_params.OCR = round(params["OCR"], 2)
        self._test_params.depth = round(params["depth"], 2)

        self._test_params.sigma_p, self._test_params.sigma_3_p = K0Properties.define_sigma_p(self._test_params.OCR,
                                                                                             self._test_params.depth,
                                                                                             self._test_params.K0)

        self._test_params.sigma_1_step = int(params["sigma_1_step"])*0.050
        self._test_params.sigma_1_max = round(params["sigma_1_max"], 3)

        self._test_modeling()

    def _test_modeling(self):
        """
        Прицип алгоритма:
            1. Точка перегиба - `(_sigma_p, _sigma_3_p)` определеяется через define_sigma_p в K0Properties
            2. Производим синтез прямолинейного участка с наклоном К0. Он должен идти из точки перегиба до
                `sigma_1_max` с шагом `sigma_1_step`.
            3. Создаем криволинейный участок кубическим сплайном в точку перегиба
            4. Производим уточнение сетки по сигма1 - она должна идти с заданным шагом
            5. Накладываем шум на прямолинейный участок через `lse_faker()`.
        """
        # 2 - формируем прямолинейный участок
        sgima_1_synth = np.linspace(self._test_params.sigma_p, self._test_params.sigma_1_max, 50)
        sgima_3_synth = self._test_params.K0 * (sgima_1_synth - self._test_params.sigma_p) + self._test_params.sigma_3_p

        # 3 - формируем криволинейный участок если есть бытовое давление
        sigma_1_spl = np.asarray([])
        sigma_3_spl = np.asarray([])

        if self._test_params.sigma_p > 0:
            bounds = ([(2, 0.0)], [(1, 1/self._test_params.K0)])
            spl = make_interp_spline([0, sgima_3_synth[0]], [0, sgima_1_synth[0]], k=3, bc_type=bounds)

            sigma_3_spl = np.linspace(0, sgima_3_synth[0], 50)
            sigma_1_spl = spl(sigma_3_spl)
            sigma_1_spl[0] = 0


        #
        #   Пока осталвляем это для дебага
        _test_x = np.hstack((sigma_3_spl[:-1], sgima_3_synth))
        _test_y = np.hstack((sigma_1_spl[:-1], sgima_1_synth))
        #

        plt.figure()
        plt.plot(_test_x, _test_y)
        # plt.plot(sgima_3_mesh, sgima_1_mesh)
        plt.scatter(np.hstack((sigma_3_spl[:-1], sgima_3_synth)), np.hstack((sigma_1_spl[:-1], sgima_1_synth)))
        # plt.scatter(sigma_3, sigma_1)
        plt.show()

        # 4 - уточнение сетки
        #   Строим сплайн для всей кривой
        spl = make_interp_spline(np.hstack((sigma_1_spl[:-1], sgima_1_synth)),
                                 np.hstack((sigma_3_spl[:-1], sgima_3_synth)), k=1)

        #   Считаем число точек и задаем сетку на Сигма1
        num: int = int((self._test_params.sigma_1_max*1000) / (self._test_params.sigma_1_step*1000)) + 1
        sgima_1_mesh = np.linspace(0, self._test_params.sigma_1_max, num)

        sgima_3_mesh = spl(sgima_1_mesh)

        index_sigma_p, = np.where(sgima_1_mesh >= self._test_params.sigma_p)
        #   Формируем участки
        sgima_1_synth = sgima_1_mesh[index_sigma_p[0]:]
        sgima_3_synth = spl(sgima_1_synth)

        sigma_1_spl = sgima_1_mesh[:index_sigma_p[0] + 1]
        sigma_3_spl = spl(sigma_1_spl)

        # накладываем шум на прямолинейный участок и объединяем
        sigma_1, sigma_3 = ModelK0SoilTest.lse_faker(sgima_1_synth, sgima_3_synth,
                                                     sigma_1_spl, sigma_3_spl,
                                                     self._test_params.K0)


        #
        #   Пока осталвляем это для дебага
        plt.figure()
        plt.plot(_test_x, _test_y)
        plt.plot(sgima_3_mesh, sgima_1_mesh)
        plt.scatter(np.hstack((sigma_3_spl[:-1], sgima_3_synth)), np.hstack((sigma_1_spl[:-1], sgima_1_synth)))
        plt.scatter(sigma_3, sigma_1)
        plt.show()
        #

        self.set_test_data({"sigma_1": sigma_1, "sigma_3": sigma_3})

    @staticmethod
    def lse_faker(sigma_1_line: np.array, sigma_3_line: np.array,
                  sigma_1_spl: np.array, sigma_3_spl: np.array, K0: float):
        """
            Принцип работы следующий:
                шумы накладываются на линейный участок графика, по которому определяется К0.
                1. Чтобы корректно наложить шум, фиксируется одна точка, после чего на нее накладывается сдвиг.
                2. На все остальные точки кроме первой накладывается чуть меньший шум (чтобы увеличить итоговый разборс)
                3. Проводитися оптимизация положения всех точек кроме первой и зафиксированной.
                4. Фукнцией оптимизации служит полный алгортим определния К0 из кривой включая нелинейный участок
                5. Критерий минимизации - минимум абсолютной ошибки определения К0
                Иначе говоря, не зафиксированные точки двигаются, пока из заданной кривой не будет корретно
                    определяться К0

        :param sigma_1_line: Сигма 1 линейного устастка
        :param sigma_3_line: Сигма 3 линейного участка
        :param sigma_1_spl: Сигма 1 нелинейного участка (включая первую точку линейного участка)
        :param sigma_3_spl: Сигма 3 нелинейного участка (включая первую точку линейного участка)
        :param K0: заданный К0
        :return: Два массива Сигма 1 и Сигма 3 единой кривой (криволинейный и линейный участки)
        """

        # Точка начала прямолинейного участка должна быть зафиксирована,
        #   так как происходят некорретные сдвиги по шумам
        sigma_3_line_fixed = sigma_3_line[0]
        '''точка начала прямолинейного участка'''

        # Если выбирать точку произвольно то
        #   придется присать ограничения cons на расположения точек
        #   после добавления шума
        fixed_point_index = 1

        noise = abs(sigma_3_line[fixed_point_index] - sigma_3_line[0]) * 0.4

        sigma_3_noise = copy.deepcopy(sigma_3_line)

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
            x[0] = sigma_3_line_fixed  # оставляем первую точку на месте

            x = np.hstack((sigma_3_spl[:-1], x))
            __sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1_line))

            _K0_new, _sigma_p_new = ModelK0.define_ko(__sigma_1, x, no_round=True)
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
        sigma_3_noise[0] = sigma_3_line_fixed

        # Соединение
        _sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1_line))
        _sigma_3 = np.hstack((sigma_3_spl[:-1], sigma_3_noise))

        # Проверка:
        K0_new, sigma_p_new = ModelK0.define_ko(_sigma_1, _sigma_3)

        # print(f"Было:\n{K0}\n"
        #       f"Стало:\n{K0_new}")

        if K0 != K0_new:
            raise RuntimeWarning("Слишком большая ошибка в К0")

        return _sigma_1, _sigma_3
