import os
import copy
from random import choices

import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
from scipy.optimize import Bounds, minimize
from scipy.interpolate import make_interp_spline

from excel_statment.properties_model import K0Properties
from general.general_functions import AttrDict, discrete_array, exponent, create_json_file, mirrow_element, \
    array_discreate_noise
from singletons import statment


class ModelK0:
    """Модель обработки резонансной колонки
    Логика работы:
        - Данные принимаются в set_test_data()

        - Обработка опыта производится методом _test_processing.

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""

    MIN_LSE_PNTS = 4
    '''Минимальное число точек, необходимых для расчета'''

    def __init__(self):
        """Определяем основную структуру данных"""
        # Структура дынных
        self.test_data = AttrDict({'sigma_1': np.asarray([]), 'sigma_3': np.asarray([]),
                                   'action': np.asarray([]), 'time': np.asarray([])})
        self._is_kinematic_mode = False
        '''Режим испытания'''

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({'left': None, 'right': None})

        # Результаты опыта
        self._test_result = AttrDict({'K0': None, 'sigma_p': None,
                                      'sigma_1': np.asarray([]), 'sigma_3': np.asarray([])})

        #
        self.__debug_data = AttrDict({'sigma_1': np.asarray([]), 'sigma_3': np.asarray([]), 'is_ok': False})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        if 'sigma_1' not in test_data or 'sigma_3' not in test_data:
            raise RuntimeWarning('test_data должен содержать sigma_1 и sigma_3')

        self.test_data.sigma_1 = test_data['sigma_1']
        self.test_data.sigma_3 = test_data['sigma_3']

        if 'action' in test_data:
            self.test_data.action = test_data['action']
            self._is_kinematic_mode = ModelK0.is_kinematic_mode(self.test_data.action)

        if 'time' in test_data:
            self.test_data.time = test_data['time']

        self._test_cut_position.left = 0
        self._test_cut_position.right = len(self.test_data.sigma_3)

        self._test_processing()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        _results = self._test_result
        return _results

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
        # try:
        self._test_result.sigma_1, self._test_result.sigma_3 = self.test_data.sigma_1, self.test_data.sigma_3
        if len(self.test_data.action) > 0:
            if self._is_kinematic_mode:
                pass
            else:
                self._test_result.sigma_1, self._test_result.sigma_3 = ModelK0.parse_step_mode_data(self.test_data)

                if self.__debug_data:
                    self.check_debug()

        self._test_result.K0, self._test_result.sigma_p = ModelK0.define_ko(self._test_result.sigma_1,
                                                                            self._test_result.sigma_3)
        # except:
        #     #app_logger.exception("Ошибка обработки данных РК")
        #     pass

    def get_plot_data(self):
        """Возвращает данные для построения"""
        if self._test_result.sigma_1 is None or self._test_result.sigma_3 is None:
            return None
        else:
            line_shift = 0.050  # сдвиги для отображения кривой

            index_sigma_p, = np.where(self._test_result.sigma_1 >= self._test_result.sigma_p)
            index_sigma_p = index_sigma_p[0] if len(index_sigma_p) > 0 else 0

            sigma_1_cut = self._test_result.sigma_1[index_sigma_p:]
            sigma_3_cut = self._test_result.sigma_3[index_sigma_p:]

            first_point = sigma_1_cut[0] + line_shift
            k0_line_sigma_1 = np.linspace(first_point, sigma_1_cut[-1] + line_shift)
            b = sigma_3_cut[0] - sigma_1_cut[0] * self._test_result.K0

            k0_line_sigma_3 = self._test_result.K0 * k0_line_sigma_1 + b

            return {"sigma_1": self._test_result.sigma_1,
                    "sigma_3": self._test_result.sigma_3,
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
            ax_K0.set_xlabel("Горизонтальное напряжение σ_3, МПа")
            ax_K0.set_ylabel("Вертикальное напряжение σ_1, МПа")

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

    def set_debug_data(self, data):
        self.__debug_data.sigma_1 = data[0]
        self.__debug_data.sigma_3 = data[1]

    def check_debug(self):

        assert len(self.__debug_data.sigma_1) == len(self._test_result.sigma_1)
        assert len(self.__debug_data.sigma_3) == len(self._test_result.sigma_3)

        for i in range(len(self._test_result.sigma_1)):
            assert round(self.__debug_data.sigma_1[i], 3) == round(self._test_result.sigma_1[i], 3)
            assert round(self.__debug_data.sigma_3[i], 3) == round(self._test_result.sigma_3[i], 3)

        self.__debug_data.is_ok = True

    @property
    def is_debug_ok(self):
        return self.__debug_data.is_ok

    @staticmethod
    def is_kinematic_mode(action):
        """
            Определяет режим испытания по массиву action из файла прибора .log
            Ступенчатый режим должен содержать участки стаблизации 'Stabilization'
            Кинематический режим должен содержать записи 'WaitLimit'
        """
        if len(action) < 1:
            return False

        if 'Stabilization' in action and 'WaitLimit' not in action:
            return False

        if 'WaitLimit' in action:
            return True

        return False

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
    def parse_step_mode_data(test_data: 'AttrDict'):
        action = copy.deepcopy(test_data.action)
        sigma_1 = np.asarray([])
        sigma_3 = np.asarray([])

        first_load_i, = np.where(action == 'LoadStage')
        if len(first_load_i) < 1:
            return sigma_1, sigma_3
        cut = first_load_i[0]
        action = action[first_load_i[0]:]

        sigma_1 = np.append(sigma_1, test_data.sigma_1[cut])
        sigma_3 = np.append(sigma_3, test_data.sigma_3[cut])

        first_stab_i, = np.where(action == 'Stabilization')
        if len(first_stab_i) < 1:
            return sigma_1, sigma_3
        cut += first_stab_i[0]
        action = action[first_stab_i[0]:]

        while len(action) > 0:
            first_load_i, = np.where(action == 'LoadStage')

            if len(first_load_i) < 1:
                sigma_1 = np.append(sigma_1, test_data.sigma_1[-1])
                sigma_3 = np.append(sigma_3, test_data.sigma_3[-1])
                break

            cut += first_load_i[0]
            action = action[first_load_i[0]:]

            sigma_1 = np.append(sigma_1, test_data.sigma_1[cut - 1])
            sigma_3 = np.append(sigma_3, test_data.sigma_3[cut - 1])

            first_stab_i, = np.where(action == 'Stabilization')
            cut += first_stab_i[0]
            action = action[first_stab_i[0]:]

        sigma_1 = np.round(sigma_1, 0) / 1000
        sigma_3 = np.round(sigma_3, 0) / 1000

        return sigma_1, sigma_3

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

        lse_pnts = ModelK0.MIN_LSE_PNTS

        if len(sigma_1) <= lse_pnts:
            defined_k0, *__ = ModelK0.lse_linear_estimation(sigma_1, sigma_3)
            defined_sigma_p = sigma_1[0]
            return (defined_k0, defined_sigma_p) if no_round else (round(defined_k0, 2), defined_sigma_p)

        # Итеративнй поиск прямолинейного участка с конца:
        #   1. Считаем к0 по последним lse_pnts точкам
        #   2. Сравниваем МНК ошибку с предыдущей
        #   3. Если ошибка выросла более чем на 100%, то завершаем поиск прямой
        #
        #   Логика в следующем: если нашли точку перегиба, то, не учитывая ее, стороим К0
        #   определенное давление в перегибе определяется в точке перегиба

        current_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])
        prev_residuals = residuals
        lse_pnts = lse_pnts + 1

        while lse_pnts <= len(sigma_1) - 1:
            current_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])
            if (residuals > 1e-8 and (residuals > prev_residuals)) \
                    and abs(residuals - prev_residuals)/prev_residuals*100 > 100:
                lse_pnts = lse_pnts - 1
                break
            prev_residuals = residuals
            lse_pnts = lse_pnts + 1

        lse_pnts = lse_pnts - 1
        # Считаем полученный к0 по отобранным точкам
        defined_k0, b, residuals = ModelK0.lse_linear_estimation(sigma_1[-lse_pnts:], sigma_3[-lse_pnts:])

        # Сигма точки перегиба можем взять прям из данных
        defined_sigma_p = sigma_1[-lse_pnts-1]

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
    Наследует обработчик и структуру данных из ModelK0

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта
    """

    SENSOR_LIMITS = (2.308, 2.309)
    'Пределы чувствительности датчика - определены из файла прибора'

    def __init__(self):
        super().__init__()

        self._test_params = AttrDict({"K0": None,
                                      "OCR": None,
                                      "depth": None,
                                      "sigma_p": None,
                                      "sigma_3_p": None,
                                      "sigma_1_step": None,  # входной параметр для ступенчатого режима
                                      "sigma_1_max": None,
                                      "mode_kinematic": False,  # True в кинематическом режме
                                      'speed': None})  # входной параметр для кинематики

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

            self._test_params.mode_kinematic = K0Properties.is_kinematic_mode(statment.general_parameters.test_mode)

        self._test_modeling()

    def set_draw_params(self, params):
        """Считывание параметров отрисовки(для передачи на слайдеры)"""
        from excel_statment.properties_model import K0Properties

        if params["OCR"] is None:
            params["OCR"] = 0
        self._test_params.OCR = round(params["OCR"], 2)

        self._test_params.sigma_p, self._test_params.sigma_3_p = K0Properties.define_sigma_p(self._test_params.OCR,
                                                                                             self._test_params.depth,
                                                                                             self._test_params.K0)

        self._test_params.sigma_1_step = round(round(params["sigma_1_step"], 0)*0.050, 2)

        num_steps = (round(params["sigma_1_max"], 2) // (self._test_params.sigma_1_step*1000))
        self._test_params.sigma_1_max = num_steps * self._test_params.sigma_1_step

        self._test_modeling()

    def _test_modeling(self):
        """
        Прицип алгоритма:
            1. Точка перегиба - `(_sigma_p, _sigma_3_p)` определеяется через define_sigma_p в K0Properties
            2. Производим синтез прямолинейного участка с наклоном К0. Он должен идти из точки перегиба до
                `sigma_1_max` с шагом `sigma_1_step`.
            3. Создаем криволинейный участок кубическим сплайном в точку перегиба
            4. Далее два режима работы - ступенчатый и кинематический.

            В СТУПЕЧАТОМ
                Первая точка линейного участка (она же последняя точка криволинейного)
                это Последняя точка перегиба! Таким образом, в зависимсоти от того, где реально располагается перегиб
                это точка или опеределится как перегиб в define_k0 или нет, если перегиб фактически находится ниже нее

                5. Производим уточнение сетки по сигма1 - она должна идти с заданным шагом
                6. Накладываем шум на прямолинейный участок через `lse_faker()`.
            В КИНЕМАТИЧЕСКОМ
                5. Производим формироавние сетки с учетом скорости нагружения
                6. Накладываем шумы на график
        """
        # Верификация заданных параметров моделирования
        self.verify_test_params()
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

        # Кинематический режим:
        if self._test_params.mode_kinematic:
            sigma_1, sigma_3 = ModelK0SoilTest._kinematic_mode_modeling(sigma_1_spl, sgima_1_synth,
                                                                        sigma_3_spl, sgima_3_synth, self._test_params)
        # Ступенчатый режим:
        else:
            sigma_1, sigma_3, action, time, debug_data = ModelK0SoilTest._step_mode_modeling(sigma_1_spl, sgima_1_synth,
                                                                                             sigma_3_spl, sgima_3_synth,
                                                                                             self._test_params)

        self.set_debug_data(debug_data)
        self.set_test_data({'sigma_1': sigma_1, 'sigma_3': sigma_3, 'action': action, 'time': time})

    def verify_test_params(self):
        """
        Проводит верификацию заданных параметров моделирования, включая округления.
        ВНИМАНИЕ! Верфикация параметров как Физических характеристик должна проводится в `properties_model`
        """
        # Округления
        SGMA1MAX_PREC = 2

        self._test_params.sigma_1_max = round(self._test_params.sigma_1_max, SGMA1MAX_PREC)
        self._test_params.sigma_1_step = round(self._test_params.sigma_1_step, SGMA1MAX_PREC)

        # Геометрические условие:
        if self._test_params.sigma_1_max - self._test_params.sigma_1_step < self._test_params.sigma_p:
            _min_sigma_1 = self._test_params.sigma_p // self._test_params.sigma_1_step
            self._test_params.sigma_1_max = (_min_sigma_1 + ModelK0.MIN_LSE_PNTS) * self._test_params.sigma_1_step

    def save_log_file(self, file_path):
        """Метод генерирует логфайл прибора"""
        if self._test_params.mode_kinematic:
            #
            TIME = 5000
            # Формируем массивы данных
            #
            deviator = ModelK0SoilTest.form_time_array(self.test_data.sigma_3*1000, points_count=TIME)
            #
            strain = np.zeros_like(deviator)  # np.random.uniform(-0.1, 0.1, len(deviator))
            #
            vertical_pressure = ModelK0SoilTest.form_time_array(self.test_data.sigma_1*1000, points_count=TIME)
            #   Подготовка под наличие разгрузки
            reload_points = [0, 0, 0]
            #
            cell_volume_strain = np.zeros_like(deviator)  # np.random.uniform(-0.1, 0.1, len(deviator))
            #
            pore_volume_strain = np.zeros_like(deviator)  # np.random.uniform(-0.1, 0.1, len(deviator))
            #
            if TIME <= 499:
                time = [i / 20 for i in range(len(deviator))]
            elif 499 < TIME <= 2999:
                time = [i / 2 for i in range(len(deviator))]
            else:
                time = [i * 3 for i in range(len(deviator))]

            # Формируем словари с данными
            #   реконсолидации нет
            reconsolidation_dict = None
            #   консолидация стандартная
            consolidation_dict = None  # ModelK0SoilTest.dictionary_without_VFS(sigma_3=100, velocity=49)
            #


            deviator_loading_dict = ModelK0SoilTest.dictionary_deviator_loading_kinematic(strain,
                                                                                          deviator,
                                                                                          pore_volume_strain,
                                                                                          cell_volume_strain,
                                                                                          reload_points,
                                                                                          pore_pressure=vertical_pressure,
                                                                                          time=time)
            main_dict = ModelK0SoilTest.triaxial_deviator_loading_dictionary(reconsolidation_dict,
                                                                             consolidation_dict,
                                                                             deviator_loading_dict)
        else:
            # Формируем словари с данными
            #   реконсолидации нет
            reconsolidation_dict = None
            #   консолидация стандартная
            consolidation_dict = ModelK0SoilTest.dictionary_without_VFS(sigma_3=100+np.random.uniform(0.5, 1.5))
            #
            #   Подготовка под наличие разгрузки
            reload_points = [0, 0, 0]
            #

            pore_pressure = self.test_data.sigma_1
            vertical_pressure = self.test_data.sigma_3
            action = self.test_data.action
            time = self.test_data.time

            deviator_loading_dict = ModelK0SoilTest.dictionary_deviator_loading_step(pore_pressure, vertical_pressure,
                                                                                     reload_points,
                                                                                     action, time)

            main_dict = ModelK0SoilTest.triaxial_deviator_loading_dictionary(reconsolidation_dict,
                                                                             consolidation_dict,
                                                                             deviator_loading_dict, no_last_start=True)

        ModelK0SoilTest.text_file(file_path, main_dict)

        # create_json_file('/'.join(os.path.split(file_path)[:-1]) + "/processing_parameters.json",
        #                  self.get_processing_parameters())

        # try:
        #     plaxis = self.deviator_loading.get_plaxis_dictionary()
        #     with open('/'.join(os.path.split(file_path)[:-1]) + "/plaxis_log.txt", "w") as file:
        #         for i in range(len(plaxis["strain"])):
        #             file.write(f"{plaxis['strain'][i]}\t{plaxis['deviator'][i]}\n")
        # except Exception as err:
        #     app_logger.exception(f"Проблема сохранения массива для plaxis {statment.current_test}")

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""

        params = {"OCR": {"value": self._test_params.OCR, "borders": [0, 3]},
                  "sigma_1_step": {"value": round((self._test_params.sigma_1_step*1000)/(0.050*1000), 0),
                                   "borders": [0, 100]},
                  "sigma_1_max": {"value": self._test_params.sigma_1_max*1000, "borders": [600, 3000]}}

        return params

    @staticmethod
    def _step_mode_modeling(sigma_1_spl, sgima_1_synth, sigma_3_spl, sgima_3_synth, params: 'AttrDict'):
        """ Выполняет задание сетки нагружений и формирует шумы. Не должна вызываться вне test_modeling """
        # 5 - уточнение сетки
        #   Строим сплайн для всей кривой
        spl = make_interp_spline(np.hstack((sigma_1_spl[:-1], sgima_1_synth)),
                                 np.hstack((sigma_3_spl[:-1], sgima_3_synth)), k=1)

        #   Считаем число точек и задаем сетку на Сигма1
        num: int = int((params.sigma_1_max * 1000) / (params.sigma_1_step * 1000)) + 1
        sgima_1_mesh = np.linspace(0, params.sigma_1_max, num)
        index_sigma_p, = np.where(sgima_1_mesh >= params.sigma_p)
        #   Формируем участки
        sgima_1_synth = sgima_1_mesh[index_sigma_p[0]:]
        sgima_3_synth = spl(sgima_1_synth)

        sigma_1_spl = sgima_1_mesh[:index_sigma_p[0] + 1]
        sigma_3_spl = spl(sigma_1_spl)

        # 6 - накладываем шум на прямолинейный участок и объединяем
        sigma_1, sigma_3 = ModelK0SoilTest.lse_faker(sgima_1_synth, sgima_3_synth,
                                                     sigma_1_spl, sigma_3_spl,
                                                     params.K0)

        sigma_1_res = sigma_1 * 1000
        sigma_3_res = sigma_3 * 1000
        sigma_1_as_v_p = np.asarray([])
        action = np.asarray([])
        time = np.asarray([])
        sigma_3_as_p_p = np.asarray([])

        for i in range(1, len(sigma_1_res)):
            sensor = np.random.uniform(ModelK0SoilTest.SENSOR_LIMITS[0], ModelK0SoilTest.SENSOR_LIMITS[1])

            res = ModelK0SoilTest._form_step(sigma_1_res[i], sigma_1_res[i - 1], sigma_3_res[i], sigma_3_res[i - 1],
                                             sigma_1_as_v_p, sigma_3_as_p_p,
                                             action, time, sensor)
            sigma_1_as_v_p, action, time, sigma_3_as_p_p = res

        return sigma_1_as_v_p, sigma_3_as_p_p, action, time, (sigma_1, sigma_3)

    @staticmethod
    def _kinematic_mode_modeling(sigma_1_spl, sgima_1_synth, sigma_3_spl, sgima_3_synth, params: 'AttrDict'):
        # 4 - уточнение сетки
        #   Строим сплайн для всей кривой
        spl = make_interp_spline(np.hstack((sigma_1_spl[:-1], sgima_1_synth)),
                                 np.hstack((sigma_3_spl[:-1], sgima_3_synth)), k=1)

        #   Считаем число точек и задаем сетку на Сигма1
        velocity = 0.49 / 1000  # в кПа

        num: int = int((params.sigma_1_max * 1000) / (velocity * 1000)) + 1
        sgima_1_mesh = np.linspace(0, params.sigma_1_max, num)
        index_sigma_p, = np.where(sgima_1_mesh >= params.sigma_p)
        #   Формируем участки
        sgima_1_synth = sgima_1_mesh[index_sigma_p[0]:]
        sgima_3_synth = spl(sgima_1_synth)

        sigma_1_spl = sgima_1_mesh[:index_sigma_p[0] + 1]
        sigma_3_spl = spl(sigma_1_spl)

        # накладываем шум на прямолинейный участок и объединяем
        # sigma_1, sigma_3 = ModelK0SoilTest.lse_faker(sgima_1_synth, sgima_3_synth,
        #                                              sigma_1_spl, sigma_3_spl,
        #                                              params.K0, params.sigma_p)
        sigma_1 = np.hstack((sigma_1_spl[:-1], sgima_1_synth))
        sigma_3 = np.hstack((sigma_3_spl[:-1], sgima_3_synth))
        return sigma_1, sigma_3

    @staticmethod
    def lse_faker(sigma_1_line: np.array, sigma_3_line: np.array,
                  sigma_1_spl: np.array, sigma_3_spl: np.array, K0: float, noise: float=None):
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
        :param noise: уровень шума, при None определяется автоматически
        :return: Два массива Сигма 1 и Сигма 3 единой кривой (криволинейный и линейный участки)
        """

        # Точка начала прямолинейного участка должна быть зафиксирована,
        #   так как происходят некорретные сдвиги по шумам
        sigma_3_line_fixed = sigma_3_line[0]
        '''точка начала прямолинейного участка'''
        sigma_1_line_fixed = sigma_1_line[0]
        '''точка начала прямолинейного участка'''

        # Проверка числа узов
        if len(sigma_3_line) < 2:
            _sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1_line))
            _sigma_3 = np.hstack((sigma_3_spl[:-1], sigma_3_line))
            return _sigma_1, _sigma_3

        # Если выбирать точку произвольно то
        #   придется присать ограничения cons на расположения точек
        #   после добавления шума
        fixed_point_index = 1

        if not noise:
            noise = abs(sigma_3_line[fixed_point_index] - sigma_3_line[0]) * 0.05

        sigma_3_noise = copy.deepcopy(sigma_3_line)

        # добавляем шум к зафиксированной точке
        rnd = np.random.randint(0, 2)
        if rnd == 0:
            sigma_3_noise[fixed_point_index] -= noise
        else:
            sigma_3_noise[fixed_point_index] += noise

        # накладываем шумы на всю сигму
        for i in range(fixed_point_index, len(sigma_3_noise)):
            if i == fixed_point_index:
                continue

            sigma_3_noise[i] += np.random.uniform(-noise, noise)

        def func(x):
            """x - массив sigma_3 без зафиксированной точки"""
            # возвращаем зафиксированную точку для подачи в МНК
            x = np.insert(x, fixed_point_index, sigma_3_noise[fixed_point_index])
            x[0] = sigma_3_line_fixed  # оставляем первую точку на месте

            x = np.hstack((sigma_3_spl[:-1], x))
            __sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1_line))

            _K0_new, _sigma_p_new = ModelK0.define_ko(__sigma_1, x, no_round=True)

            return abs(_K0_new - K0) + abs(_sigma_p_new - sigma_1_line_fixed)

        initial = np.delete(sigma_3_noise, fixed_point_index)
        bnds = Bounds(np.zeros_like(initial), np.ones_like(initial) * np.inf)
        '''Граничные условия типа a <= xi <= b'''

        def constrains(x):
            x = np.insert(x, fixed_point_index, sigma_3_noise[fixed_point_index])

            # первое ограничение - каждая последующая сигма не меньше предыдущей
            first = np.array([x[j + 1] - x[j] for j in range(len(x) - 1)])

            # замыкаем последний на первый на всякий случай
            second = np.array([x[-1] - x[0]])

            third = np.array([0.025-abs(x[j]-sigma_3_line[j]) for j in range(len(x))])

            res = np.hstack((first, second, third))
            return res

        cons = {'type': 'ineq',
                'fun': constrains}
        '''Нелинейные ограничения типа cj(x)>=0'''

        res = minimize(func, initial, method='SLSQP', constraints=cons, bounds=bnds, tol=1e-6)
        res = res.x

        # Результат:
        sigma_3_noise = np.insert(res, fixed_point_index, sigma_3_noise[fixed_point_index])
        sigma_3_noise[0] = sigma_3_line_fixed

        # Соединение
        _sigma_1 = np.hstack((sigma_1_spl[:-1], sigma_1_line))
        _sigma_3 = np.hstack((sigma_3_spl[:-1], sigma_3_noise))

        # Проверка:
        K0_new, sigma_p_new = ModelK0.define_ko(_sigma_1, _sigma_3)

        print(f"Было:\n{K0} {sigma_1_line_fixed}\n"
              f"Стало:\n{K0_new} {sigma_p_new}")

        if K0 != K0_new or (sigma_p_new > sigma_1_line_fixed):
            print("Слишком большая ошибка в К0, Пробую уменьшить шум")
            if noise < 1:
                print("Слишком большая ошибка в К0")
                _sigma_1, _sigma_3 = ModelK0SoilTest.lse_faker(sigma_1_line, sigma_3_line, sigma_1_spl, sigma_3_spl,
                                                               K0, noise=0)
            else:
                _sigma_1, _sigma_3 = ModelK0SoilTest.lse_faker(sigma_1_line, sigma_3_line, sigma_1_spl, sigma_3_spl,
                                                               K0, noise=noise*0.95)

        return _sigma_1, _sigma_3

    @staticmethod
    def dictionary_without_VFS(sigma_3=100, velocity=49):

        time = [np.random.uniform(10.0, 15.0)]
        action = ['Start']
        action_changed = ['True']
        trajectory = ['ReconsolidationWoDrain']

        time.append(time[-1])
        action.append('LoadStage')
        action_changed.append('')
        trajectory.append(trajectory[-1])

        time.append(time[-1]+np.random.uniform(1.0, 2.0))
        action.append('LoadStage')
        action_changed.append('True')
        trajectory.append(trajectory[-1])

        time.append(time[-1])
        action.append('Wait')
        action_changed.append('')
        trajectory.append(trajectory[-1])

        time.append(time[-1] + np.random.uniform(4.0, 5.0))
        action.append('Wait')
        action_changed.append('True')
        trajectory.append('Consolidation')

        time.append(time[-1])
        action.append('LoadStage')
        action_changed.append('')
        trajectory.append('Consolidation')

        rnd = 3#np.random.randint(3, 3)
        exp_grid = np.linspace(0, rnd - 1, rnd)
        vertical_press_exp = exponent(exp_grid, sigma_3, slant=20)
        vertical_press = np.zeros_like(time)
        vertical_press = np.hstack((vertical_press, vertical_press_exp))

        time_load = [np.random.uniform(5.0, 6.0), np.random.uniform(9.0, 11.0), np.random.uniform(20.0, 31.0),
                     np.random.uniform(40.0, 46.0), np.random.uniform(49.0, 51.0)]

        for i in range(rnd):
            time.append(time[-1] + time_load[i])

        action = np.hstack((np.asarray(action), np.full(rnd, 'LoadStage')))
        action_changed = np.hstack((np.asarray(action_changed), np.full(rnd, '')))
        trajectory = np.hstack((np.asarray(trajectory), np.full(rnd, 'Consolidation')))

        time = np.hstack((np.asarray(time), np.asarray(time[-1])))
        action = np.hstack((action, ['LoadStage']))
        action_changed = np.hstack((action_changed, ['True']))
        trajectory = np.hstack((trajectory, ['Consolidation']))
        vertical_press = np.hstack((vertical_press, np.asarray(vertical_press[-1])))

        time = np.hstack((time, np.asarray(time[-1])))
        action = np.hstack((action, ['Stabilization']))
        action_changed = np.hstack((action_changed, ['']))
        trajectory = np.hstack((trajectory, ['Consolidation']))
        vertical_press = np.hstack((vertical_press, np.asarray(vertical_press[-1])))

        time = np.hstack((time, np.asarray(time[-1]) + np.random.uniform(1.0, 2.0)))
        action = np.hstack((action, ['Stabilization']))
        action_changed = np.hstack((action_changed, ['True']))
        trajectory = np.hstack((trajectory, ['CTC']))
        vertical_press = np.hstack((vertical_press, np.asarray(vertical_press[-1])))

        data = {
            "Time": time,
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 76)),
            "SampleDiameter_mm": np.round(np.full(len(time), 38)),
            "Deviator_kPa": np.full(len(time), 0),
            "VerticalDeformation_mm": np.full(len(time), 0),
            "CellPress_kPa": choices([-0.5221, 0, 0.5221, 2*0.5221], k=len(vertical_press)),
            "CellVolume_mm3": np.zeros_like(vertical_press),
            "PorePress_kPa": np.full(len(time), 0),
            "PoreVolume_mm3": np.full(len(time), 0),
            "VerticalPress_kPa": vertical_press,
            "Trajectory": trajectory
        }

        return data

    @staticmethod
    def dictionary_deviator_loading_kinematic(strain, deviator, pore_volume_strain, cell_volume_strain, indexs_loop,
                                              pore_pressure, time, delta_h_consolidation=0,):
        """Формирует словарь девиаторного нагружения"""
        # index_unload, = np.where(strain >= strain[-1] * 0.92)  # индекс абциссы конца разгрузки
        # x_unload_p = strain[index_unload[0]]  # деформация на конце разгрузки
        # y_unload_p = - 0.05 * max(deviator)  # девиатор на конце разгрузки
        #
        # x_unload = np.linspace(strain[-1], x_unload_p, 8 + 1)  # массив деформаций разгрузки с другим шагом
        # spl = make_interp_spline([x_unload_p, strain[-1]],
        #                                      [y_unload_p, deviator[-1]], k=3,
        #                                      bc_type=([(1, 0)], [(1, deviator[-1] * 200)]))
        # y_unload = spl(x_unload)  # массив значений девиатора при разгрузке
        # z_unload_p = min(pore_volume_strain) * 1.05  # обьемная деформация на конце разгрузки
        # spl = make_interp_spline([x_unload_p, strain[-1]],
        #                                      [z_unload_p, pore_volume_strain[-1]], k=3,
        #                                      bc_type=([(1, 0)], [(1, abs(pore_volume_strain[-1] - z_unload_p) * 200)]))
        # unload_pore_volume_strain = spl(x_unload)  # массив обьемных деформаций при разгрузке
        #
        # y_unload = y_unload + np.random.uniform(-1, 1, len(y_unload))  # наложение  шума на разгрузку
        # y_unload = discrete_array(y_unload, 1)  # наложение ступенатого шума на разгрузку
        #
        # z_unload_p = min(cell_volume_strain) * 1.05
        # spl = make_interp_spline([x_unload_p, strain[-1]],
        #                                      [z_unload_p, cell_volume_strain[-1]], k=3,
        #                                      bc_type=([(1, 0)], [(1, abs(cell_volume_strain[-1] - z_unload_p) * 200)]))
        # unload_cell_volume_strain = spl(x_unload)
        #
        # # Расширяем массивы на разгрузку
        # cell_volume_strain = np.hstack((cell_volume_strain, unload_cell_volume_strain[1:]))
        # strain = np.hstack((strain, x_unload[1:]))
        # deviator = np.hstack((deviator, y_unload[1:]))
        # pore_volume_strain = np.hstack((pore_volume_strain, unload_pore_volume_strain[1:]))
        #
        # end_unload = len(strain) - len(x_unload) + 1  # индекс конца разгрузки в масииве
        #
        # # запись девиаторного нагружения в файл
        # time = np.hstack((time, deviator[-1] + np.linspace(1, len(y_unload[1:]), len(y_unload[1:]))))

        action = ['WaitLimit' for __ in range(len(time))]

        # pore_pressure = np.hstack((
        #     pore_pressure,
        #     np.linspace(pore_pressure[-1], pore_pressure[-1] * np.random.uniform(0.3, 0.5), len(time) - len(pore_pressure))
        # ))
        #
        # if indexs_loop[0] != 0:
        #     for i in range(len(action)):
        #         if i >= indexs_loop[0] and i < indexs_loop[1]:
        #             action[i] = 'CyclicUnloading'
        #         elif i >= indexs_loop[1] and i <= indexs_loop[2]:
        #             action[i] = 'CyclicLoading'
        #         elif i >= end_unload:
        #             action[i] = 'Unload'
        # else:
        #     for i in range(len(action)):
        #         if i >= end_unload:
        #             action[i] = 'Unload'

        action_changed = []
        Last_WaitLimit_flag = 1
        for i in range(len(action) - 1):
            if action[i] == "WaitLimit" and action[i + 1] == "Unload" and Last_WaitLimit_flag:
                action_changed.append('True' + '')
                Last_WaitLimit_flag = 0
            else:
                action_changed.append('')
        action_changed.append('')

        data = {
            "Time": time,
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 76)),
            "SampleDiameter_mm": np.round(np.full(len(time), 38)),
            "Deviator_kPa": np.round(deviator, 4),
            "VerticalDeformation_mm": strain * (76 - delta_h_consolidation),
            "CellPress_kPa": np.full(len(time), 0) + np.random.uniform(0, 1.57, len(time)),
            "CellVolume_mm3": (cell_volume_strain * np.pi * 19 ** 2 * (76 - delta_h_consolidation)),
            "PorePress_kPa": pore_pressure,
            "PoreVolume_mm3": pore_volume_strain * np.pi * 19 ** 2 * (76 - delta_h_consolidation),
            "VerticalPress_kPa": deviator + np.random.uniform(-0.1, 0.1, len(time)),
            "Trajectory": np.full(len(time), 'CTC')}

        return data

    @staticmethod
    def dictionary_deviator_loading_step(pore_pressure, vertical_pressure, indexs_loop, action, time,
                                         delta_h_consolidation=0,):
        """Формирует словарь девиаторного нагружения"""

        # Разгрукза формируется так же как обычный шаг (экспонентой) вдвое выше текущего значения
        #   затем значения обращаются и экспонента стремится к нулю
        #   Однако разргрузка происходит не ровно до нуля!
        unload_point_s1 = 2*vertical_pressure[-1] + np.random.randint(1, 3)*ModelK0SoilTest.SENSOR_LIMITS[0]
        unload_point_s3 = 2*pore_pressure[-1] + np.random.randint(1, 3)*ModelK0SoilTest.SENSOR_LIMITS[0]
        unload_point_s3 -= np.random.uniform(40, 50)  # разгрукзка по сигма3 происходит не до пред нулевых значений!

        res = ModelK0SoilTest._form_step(unload_point_s1, vertical_pressure[-1], unload_point_s3, pore_pressure[-1], reload=True)
        vertical_p_reload, action_reload, time_reload, pore_pressure_reload = res

        vertical_p_reload = np.asarray([mirrow_element(elem, vertical_pressure[-1]) for elem in vertical_p_reload])
        pore_pressure_reload = np.asarray([mirrow_element(elem, pore_pressure[-1]) for elem in pore_pressure_reload])

        action_reload = np.full(len(action_reload), 'Unload')
        vertical_pressure = np.hstack((vertical_pressure, vertical_p_reload))
        pore_pressure = np.hstack((pore_pressure, pore_pressure_reload))
        action = np.hstack((action, action_reload))
        time_reload += time[-1]
        time = np.hstack((time, time_reload))

        assert (len(action) == len(vertical_pressure))\
               and (len(vertical_pressure) == len(pore_pressure))\
               and (len(pore_pressure) == len(time))

        action_changed = []
        for i in range(len(action) - 1):
            if action[i] == "LoadStage" and action[i + 1] == "Stabilization":
                action_changed.append('True' + '')
            elif action[i] == "Stabilization" and action[i + 1] == "LoadStage":
                action_changed.append('True' + '')
            elif action[i] == "Stabilization" and action[i + 1] == "Unload":
                action_changed.append('True' + '')
            else:
                action_changed.append('')
        action_changed.append('')

        deviator = np.round(vertical_pressure, 4) + np.random.uniform(-0.1, 0.1, len(vertical_pressure))
        deviator[0] = 0.0

        data = {
            "Time": time,
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 76)),
            "SampleDiameter_mm": np.round(np.full(len(time), 38)),
            "Deviator_kPa": deviator,
            "VerticalDeformation_mm": np.zeros_like(vertical_pressure),
            "CellPress_kPa": choices([-0.5221, 0, 0.5221, 2*0.5221], k=len(vertical_pressure)),
            "CellVolume_mm3": np.zeros_like(vertical_pressure),
            "PorePress_kPa": np.round(pore_pressure, 4),
            "PoreVolume_mm3": np.zeros_like(vertical_pressure),
            "VerticalPress_kPa": np.round(vertical_pressure, 4),
            "Trajectory": np.full(len(time), 'CTC')}

        return data

    @staticmethod
    def triaxial_deviator_loading_dictionary(b_test, consolidation, deviator_loading, no_last_start=False):

        start = np.random.uniform(0.5, 0.8)
        if no_last_start:
            dict = {
                'Time': [0, 0, np.round(start, 3), np.round(start + 0.1, 3)],
                'Action': ["", "", "Start", "Start"],
                'Action_Changed': ["", "True", "", ""],
                'SampleHeight_mm': np.full(4, 76),
                'SampleDiameter_mm': np.full(4, 38),
                'Deviator_kPa': np.full(4, 0),
                'VerticalDeformation_mm': np.full(4, 0),
                'CellPress_kPa': np.full(4, 0),
                'CellVolume_mm3': np.full(4, 0),
                'PorePress_kPa': np.full(4, 0),
                'PoreVolume_mm3': np.full(4, 0),
                'VerticalPress_kPa': np.full(4, 0),
                'Trajectory': np.full(4, "HC")
            }
        else:
            dict = {
                'Time': [0, 0, np.round(start, 3), np.round(start + 0.1, 3), np.round(start + 2, 3)],
                'Action': ["", "", "Start", "Start", "Start"],
                'Action_Changed': ["", "True", "", "", "True"],
                'SampleHeight_mm': np.full(5, 76),
                'SampleDiameter_mm': np.full(5, 38),
                'Deviator_kPa': np.full(5, 0),
                'VerticalDeformation_mm': np.full(5, 0),
                'CellPress_kPa': np.full(5, 0),
                'CellVolume_mm3': np.full(5, 0),
                'PorePress_kPa': np.full(5, 0),
                'PoreVolume_mm3': np.full(5, 0),
                'VerticalPress_kPa': np.full(5, 0),
                'Trajectory': np.full(5, "HC")
            }

        data_start = ModelK0SoilTest.addition_of_dictionaries(dict, b_test, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        data = ModelK0SoilTest.addition_of_dictionaries(copy.deepcopy(data_start), consolidation, initial=True,
                                                                        skip_keys=["SampleHeight_mm",
                                                                                   "SampleDiameter_mm"])

        dictionary = ModelK0SoilTest.addition_of_dictionaries(copy.deepcopy(data), deviator_loading, initial=True,
                                              skip_keys=["SampleHeight_mm", "SampleDiameter_mm", "Action_Changed"])

        dictionary["Time"] = ModelK0SoilTest.current_value_array(dictionary["Time"], 3)
        dictionary["Deviator_kPa"] = ModelK0SoilTest.current_value_array(dictionary["Deviator_kPa"], 4)

        # Для части девиаторного нагружения вертикальная деформация хода штока должна писаться со знаком "-"
        CTC_index, = np.where(dictionary["Trajectory"] == 'CTC')
        str = ModelK0SoilTest.current_value_array(dictionary["VerticalDeformation_mm"][:CTC_index[0]], 5)
        str.extend(ModelK0SoilTest.current_value_array(dictionary["VerticalDeformation_mm"][CTC_index[0]:], 5,
                                                       change_negatives=False))
        dictionary["VerticalDeformation_mm"] = str

        dictionary["CellPress_kPa"] = ModelK0SoilTest.current_value_array(dictionary["CellPress_kPa"], 5)
        dictionary['CellVolume_mm3'] = ModelK0SoilTest.current_value_array(dictionary["CellVolume_mm3"], 5)
        dictionary['PoreVolume_mm3'] = ModelK0SoilTest.current_value_array(dictionary["PoreVolume_mm3"], 5)
        dictionary["PorePress_kPa"] = ModelK0SoilTest.current_value_array(dictionary["PorePress_kPa"], 5)
        dictionary["VerticalPress_kPa"] = ModelK0SoilTest.current_value_array(dictionary["VerticalPress_kPa"], 5)

        return dictionary

    @staticmethod
    def addition_of_dictionaries(data1, data2, initial=True, skip_keys=None):
        if data1 is None and data2 is None:
            return None
        elif data1 is None:
            return copy.deepcopy(data2)
        elif data2 is None:
            return copy.deepcopy(data1)

        dictionary_1 = copy.deepcopy(data1)
        dictionary_2 = copy.deepcopy(data2)
        if skip_keys is None:
            skip_keys = ['']
        keys_d1 = list(dictionary_1.keys())  # массив ключей словаря 1
        len_d1_elem = len(dictionary_1[keys_d1[0]])  # длина массива под произвольным ключем словаря 1
        keys_d2 = list(dictionary_2.keys())  # массив ключей словаря 2
        len_d2_elem = len(dictionary_2[keys_d2[0]])  # длина массива под произвольным ключем словаря 2

        for key in dictionary_1:
            if key in dictionary_2:  # если ключ есть в словаре 2
                if initial and (str(type(dictionary_1[key][0])) not in ["<class 'str'>", "<class 'numpy.str_'>"]) and (
                        key not in skip_keys):  # если initial=True и элементы под ключем не строки
                    # к эламентам словаря 2 прибавляется последний элемент словаря 1 под одним ключем
                    for val in range(len(dictionary_2[key])):
                        dictionary_2[key][val] += dictionary_1[key][-1]
                dictionary_1[key] = np.append(dictionary_1[key], dictionary_2[key])
            else:  # если ключа нет в словаре 2
                dictionary_1[key] = np.append(dictionary_1[key], np.full(len_d2_elem, ''))

        for key in dictionary_2:  # если ключа нет в словаре 1
            if key not in dictionary_1:
                dictionary_1[key] = np.append(np.full(len_d1_elem, ''), dictionary_2[key])

        return dictionary_1

    @staticmethod
    def current_value_array(array, number, change_negatives=True):
        s = []
        for i in range(len(array)):
            num = ModelK0SoilTest.number_format(array[i], number, change_negatives=change_negatives).replace(".", ",")
            if num in ["0,0", "0,00", "0,000", "0,0000", "0,00000", "0,000000"]:
                num = "0"
            s.append(num)
        return s

    @staticmethod
    def number_format(x, characters_number=0, split=".", change_negatives=True):
        """Функция возвращает число с заданным количеством знаков после запятой
        :param characters_number: количество знаков после запятой
        :param format: строка или число
        :param split: кразделитель дробной части. точка или запятая
        :param change_negatives: удаление начального знака минус"""

        if str(type(x)) in ["<class 'numpy.float64'>", "<class 'numpy.int32'>", "<class 'int'>", "<class 'float'>"]:
            # установим нужный формат
            _format = "{:." + str(characters_number) + "f}"
            round_x = np.round(x, characters_number)
            x = _format.format(round_x)

            # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
            if change_negatives:
                if x[0] == "-":
                    x = x[1:len(x)]

            if split == ".":
                return x
            elif split == ",":
                return x.replace(".", ",")


        else:
            _format = "{:." + str(characters_number) + "f}"

            if str(type(x)) == "<class 'numpy.ndarray'>":
                x = list(x)

            for i in range(len(x)):
                # Уберем начальный минус  (появляется, например, когда округляем -0.0003 до 1 знака)
                x[i] = _format.format(x[i])
                if change_negatives:
                    if x[i][0] == "-":
                        x[i] = x[i][1:len(x)]

                if split == ".":
                    pass
                elif split == ",":
                    x[i].replace(".", ",")

            return x

    @staticmethod
    def text_file(file_path, data):
        """Сохранение текстового файла формата Willie.
                    Передается папка, массивы"""
        p = os.path.join(file_path, "Тест.log")

        def make_string(data, i):
            s = ""
            for key in data:
                s += str(data[key][i]) + '\t'
            s += '\n'
            return (s)

        with open(file_path, "w") as file:
            file.write(
                "Time" + '\t' + "Action" + '\t' + "Action_Changed" + '\t' + "SampleHeight_mm" + '\t' + "SampleDiameter_mm" + '\t' +
                "Deviator_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "CellPress_kPa" + '\t' + "CellVolume_mm3" + '\t' +
                "PorePress_kPa" + '\t' + "PoreVolume_mm3" + '\t' + "VerticalPress_kPa" + '\t' +
                "Trajectory" + '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

    @staticmethod
    def form_time_array(x, points_count: int = 5000, discrete_level=0.5, noise=0.4):
        _t = np.linspace(0, len(x) - 1, points_count)
        spl = make_interp_spline(ModelK0SoilTest.time_series(x), x, k=1)
        _x = spl(_t)

        if noise:
            sh = np.random.uniform(-noise, noise, len(_x))
            _x += sh

        if discrete_level:
            _x = discrete_array(_x, discrete_level)

        return _x

    @staticmethod
    def time_series(x: np.ndarray) -> np.ndarray:
        """
        Возвращает массив целых чисел по размеру `x`: [0,1,2,...,len(`x`)-1]:
        """
        time = np.linspace(0, len(x) - 1, len(x))
        return time

    @staticmethod
    def _form_step(sigma_1_i, sigma_1_i_prev, sigma_3_i, sigma_3_i_prev, sigma_1=np.asarray([]), sigma_3=np.asarray([]),
                   action=np.asarray([]), time=np.asarray([]),
                   sensor_s1=2.3088, stab_len: int = 365, reload: bool = False):

        # в случае разгрузки участок стабилизации длинее
        if reload:
            stab_len *= 2

        rnd = np.random.randint(6, 8)
        '''число тиков нагрузки'''

        _is_first_sigma_3 = len(sigma_3) == 0

        sensor_s3 = 0.52143
        '''шум датчика сигма3'''

        num_s3_stabs_err = np.random.randint(30, 40)
        '''число "опусканий" сигма3 на этапе стабилизации'''
        if _is_first_sigma_3 and not reload:
            num_s3_stabs_err = np.random.randint(10, 20)

        _s3_exp_slant = 3
        '''резкость экспоненты для убывания сигма3 во время стаблизации'''
        if reload:
            _s3_exp_slant = 5

        time_load = [0, np.random.uniform(0.5, 1.0), np.random.uniform(1.0, 2.0), np.random.uniform(2.0, 3.0),
                     np.random.uniform(5.0, 6.0), np.random.uniform(9.0, 11.0), np.random.uniform(20.0, 31.0),
                     np.random.uniform(40.0, 46.0), np.random.uniform(49.0, 51.0)]
        '''Временные тики во время этапов нагрузки и выхода на стабилизацию'''

        # Первый блок : нагрузка до значения
        exp_grid = np.linspace(0, rnd - 1, rnd)
        sigma_1_step = exponent(exp_grid, sigma_1_i - sigma_1_i_prev, 10)
        sigma_1_step = sigma_1_step + sigma_1_i_prev

        sigma_3_overload = sigma_3_i+num_s3_stabs_err*sensor_s3
        sigma_3_lim = sigma_3_overload - sigma_3_i_prev
        sigma_3_step = exponent(exp_grid, sigma_3_lim, 10)
        sigma_3_step = sigma_3_step + sigma_3_i_prev

        #   Время во время нагрузки формируется исходя из "скоростей" нагрузок в time_load
        time_i = np.asarray([time_load[i] for i in range(len(sigma_1_step))])
        for i in range(1, len(time_i)):
            time_i[i] += time_i[i-1]
        if len(time) > 0:  # не забываем прибавить время с предыдущего участка
            time_i += time[-1]

        time = np.hstack((time, time_i))
        sigma_1 = np.hstack((sigma_1, sigma_1_step))
        action = np.hstack((action, np.full(len(sigma_1_step), 'LoadStage')))
        sigma_3 = np.hstack((sigma_3, sigma_3_step))

        # Второй блок : стабилизация
        #   первая стаблизация повторяет последнюю нагрузку
        action = np.hstack((action, ['Stabilization']))
        time = np.hstack((time, np.asarray(time[-1])))
        sigma_1 = np.hstack((sigma_1, np.asarray(sigma_1[-1])))
        sigma_3 = np.hstack((sigma_3, np.asarray(sigma_3[-1])))

        #       коррекция для соблюдения погрешностей датчика - при стаблизации значение "скачет" туда-сюда
        # сигма1
        correction = sensor_s1 - (sigma_1[-1] - sigma_1_i)
        sigma_1_step = np.full(stab_len, sigma_1[-1]) + correction
        rnd = choices([0, 1], weights=[0.8, 0.2], k=len(sigma_1_step))
        sigma_1_step = np.asarray([sigma_1_i if rnd[i] else sigma_1_step[i] for i in range(len(sigma_1_step))])

        # сигма3
        #
        exp_grid = np.linspace(0, stab_len - 1, stab_len)
        sigma_3_step = exponent(exp_grid, abs(sigma_3_overload-sigma_3_i), slant=_s3_exp_slant)
        sigma_3_step = sigma_3_step + sigma_3_overload
        sigma_3_step = np.asarray([mirrow_element(elem, sigma_3_overload) for elem in sigma_3_step])

        for i in range(1, len(sigma_3_step)):
            if sigma_3_step[i]-sigma_3_step[i-1] <= -0.52143:
                sigma_3_step[i] = sigma_3_step[i-1] - sensor_s3
            elif sigma_3_step[i]-sigma_3_step[i-1] >= 0.52143:
                sigma_3_step[i] = sigma_3_step[i - 1] + sensor_s3
            else:
                sigma_3_step[i] = sigma_3_step[i-1]

        if reload:
            for i in range(1, len(sigma_3_step)):
                rnd = np.random.randint(0, 1)
                if rnd:
                    sigma_3_step = np.asarray([sigma_3_step[:i], sigma_3_step[i:] - sensor_s3])

        #   Время во время стаблизации состоит из двух подэтапов
        #       сначала идет "разгон" до нужного времени, а потом тики по 60 секунд
        time_i = [time[-1] + time_load[1]]
        for i in range(1, len(sigma_1_step)):
            if i <= 6:
                time_i.append(time_i[-1] + time_load[i+1])
            else:
                time_i.append(time_i[-1] + 60)
        time_i = np.asarray(time_i)

        #
        sigma_1 = np.hstack((sigma_1, sigma_1_step))
        action = np.hstack((action, np.full(len(sigma_1_step), 'Stabilization')))
        time = np.hstack((time, time_i))
        sigma_3 = np.hstack((sigma_3, sigma_3_step))

        #   последняя стабилизация дважды
        sigma_1 = np.hstack((sigma_1, np.asarray(sigma_1_i)))
        sigma_3 = np.hstack((sigma_3, np.asarray(sigma_3_i)))
        action = np.hstack((action, ['Stabilization']))
        time = np.hstack((time, np.asarray(time[-1])))

        return sigma_1, action, time, sigma_3
