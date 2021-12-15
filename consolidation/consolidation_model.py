"""Модуль математических моделей консолидации. Содержит модели:
    ModelTriaxialConsolidation - модель обработчика данных опыта консолидации.
    Принцип работы:
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора openfile() находится в модуле text_file_functions
        Обработка опыта происходит с помощью метода _sqrt_processing() для метода квадратного корня и _log_processing
        для метода логарифма. Метод change_borders() служит для обработки границ массивов
        Метод _interpolate_volume_strain интерполирует/аппроксимирует объемную деформацию для обработки
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialConsolidationSoilTest - модель математического моделирования данных опыта консолидации.
    Наследует методы  _test_processing(), get_test_results(), plotter(), а также структуру данных из
    ModelTriaxialConsolidation
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_draw_params() устанавливает позьзовательские значения параметров отрисовки.
        Метод_test_modeling моделируют соотвествующие массивы опытных данных. Вызыванется при передачи пользовательских
         параметров отрисовки.."""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import pchip_interpolate
import scipy.ndimage as ndimage
import math
from datetime import timedelta
import copy

from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, \
    mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from consolidation.function_consalidation_for_compr import function_consalidation, define_final_deformation
from configs.plot_params import plotter_params
from singletons import statment
from intersect import intersection

class ModelTriaxialConsolidation:
    """Модель обработки консолидации

    Логика работы:
        - Данные принимаются в set_test_data(). значально все данные обнуляются методом _reset_data(). self.points_count
        отвечает за количество точек в интерполированной объемной деформации

        - Производится выбор рабочей кривой объемной деформации. Если кривая Поровой отжатой жидкости писалась, то она
        становится рабочей, иначе кривая отжатой жидкости из камеры

        - Возможно обрезание массивов данных методом change_borders(left, right). Метод _cut() обрезает массивы по левой
        и правой границе. Обработка производится для обрезанной части. Объемная деформация интерполируется методом
        _interpolate_volume_strain(). Есть возможность интерполяции полиномом Эрмита или полиномом с заданной степенью.

        - Обработка опыта производится методом _sqrt_processing и _log_processing. Методы находят прямые участки, их
        пересечения с графиком и тд. Основные параметры - точки прямых линий для прямолинейных участков. Метод сам
        определяет эти точки, если их не подать, иначе производит рассчет с заданными.

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""

    def __init__(self):
        self._reset_data()
        self._interpolation_type = "ermit"
        self._interpolation_param = 0.5
        self.points_count = 50
        self.catch_point_identificator = None

    def _reset_data(self):
        """Обнуление входных параметров и результатов для обработки нового опыта"""
        self._test_data = AttrDict({"time": None,
                                    "time_sqrt": None,
                                    "time_log": None,

                                    "pore_volume_strain": None,
                                    "cell_volume_strain": None,

                                    "volume_strain": None,
                                    "volume_strain_approximate": None,

                                    "time_cut": None,
                                    "volume_strain_approximate_cut": None,
                                    "delta_h_reconsolidation": 0,
                                    "delta_h_consolidation": 0})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None,
                                            "right": None})

        # Точки построения обработки (прямых линий)
        self.processed_points_sqrt = AttrDict(
            {"line_start_point": Point(x=None, y=None),  # Левая точка прямолинейного участка. х - всегда = 0
             "line_end_point": Point(x=None, y=None),  # Правая точка прямолинейного участка
             "Cv": Point(x=None, y=None)})  # Пересечение участка с углом 0.9

        self.processed_points_log = AttrDict(
            {"first_line_start_point": Point(x=None, y=None),  # Левая точка первого прямолинейного участка
             "first_line_start_point": Point(x=None, y=None),  # Правая точка первого прямолинейного участка
             "second_line_start_point": Point(x=None, y=None),  # Левая точка второго прямолинейного участка
             "second_line_start_point": Point(x=None, y=None),
             "Cv": Point(x=None, y=None)})  # Правая точка второго прямолинейного участка

        # Результаты опыта
        self._test_result = AttrDict({"Cv_sqrt": None,
                                      "t50_sqrt": None,
                                      "strain50": None,
                                      "t90_sqrt": None,
                                      "t100_sqrt": None,
                                      "strain100_sqrt": None,
                                      "Cv_log": None,
                                      "Ca_log": None,
                                      "t50_log": None,
                                      "t100_log": None,
                                      "strain100_log": None,
                                      "d0": None,
                                      "velocity": None,
                                      "Kf_log": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._reset_data()

        if test_data:
            self._test_data.time = test_data["time"]

            # Объемная деформация до обработки
            self._test_data.volume_strain = test_data["strain"]
        else:
            print("Этап консолидации не проводился")

    def set_interpolation_type(self, interpolation_type):
        """Смена способа интерполяции исходных данных"""
        if self._test_data.time_sqrt is not None:
            self._interpolation_type = interpolation_type
            self._interpolate_volume_strain(type=self._interpolation_type, param=self._interpolation_param)
            self._sqrt_processing()
            self._log_processing()

    def set_interpolation_param(self, interpolation_param):
        """Настройка параметров интерполяции"""
        if self._test_data.time_sqrt is not None:
            self._interpolation_param = interpolation_param
            self._interpolate_volume_strain(type=self._interpolation_type, param=self._interpolation_param)
            return {"volume_strain": self._test_data.volume_strain,
                    "time": self._test_data.time,
                    "time_sqrt_origin": self._test_data.time ** 0.5,
                    "time_log_origin": np.log10(self._test_data.time),
                    "time_sqrt": self._test_data.time_sqrt,
                    "time_log": self._test_data.time_log,
                    "volume_strain_approximate": self._test_data.volume_strain_approximate}

    def change_borders(self, left, right):
        """Выделение границ для обрезки значений всего опыта"""
        self._test_cut_position.left = left
        self._test_cut_position.right = right
        self._cut()
        self._interpolate_volume_strain(type=self._interpolation_type, param=self._interpolation_param)
        self._sqrt_processing()
        self._log_processing()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        return self._test_result.get_dict()

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        if self._test_data.volume_strain_approximate is not None:
            if self.processed_points_sqrt.Cv:
                mooveX = (self._test_data.time_sqrt[-1] - self._test_data.time_sqrt[0]) * 1 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[
                    0]) * 3 / 100

                sqrt_t90_vertical_line = point_to_xy(Point(x=self.processed_points_sqrt.Cv.x,
                                                           y=max(self._test_data.volume_strain_approximate[0],
                                                                 self.processed_points_sqrt.line_start_point.y) - 5 * mooveY),
                                                     Point(x=self.processed_points_sqrt.Cv.x,
                                                           y=self.processed_points_sqrt.Cv.y))
                sqrt_t90_horizontal_line = point_to_xy(Point(x=4 * mooveX, y=self.processed_points_sqrt.Cv.y),
                                                       Point(x=self.processed_points_sqrt.Cv.x,
                                                             y=self.processed_points_sqrt.Cv.y))
                sqrt_t90_text = Point(x=self.processed_points_sqrt.Cv.x,
                                      y=max(self._test_data.volume_strain_approximate[0],
                                            self.processed_points_sqrt.line_start_point.y))
                sqrt_strain90_text = Point(x=4 * mooveX, y=max(self._test_data.volume_strain_approximate[0],
                                                               self.processed_points_sqrt.line_start_point.y))

            else:
                sqrt_t90_vertical_line = None
                sqrt_t90_horizontal_line = None
                sqrt_t90_text = None
                sqrt_strain90_text = None

            if self._test_result.strain100_sqrt:

                index_sqrt_strain_100, = np.where(
                    self._test_data.volume_strain_approximate <= self._test_result.strain100_sqrt)

                if len(index_sqrt_strain_100):
                    sqrt_t100_vertical_line = point_to_xy(Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                y=max(self._test_data.volume_strain_approximate[0],
                                                                      self.processed_points_sqrt.line_start_point.y) - 5 * mooveY),
                                                          Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                y=self._test_data.volume_strain_approximate[
                                                                    index_sqrt_strain_100[0]]))
                    sqrt_t100_horizontal_line = point_to_xy(
                        Point(x=4 * mooveX, y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]),
                        Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                              y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]))

                    sqrt_t100_text = Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                           y=max(self._test_data.volume_strain_approximate[0],
                                                 self.processed_points_sqrt.line_start_point.y))

                    sqrt_strain100_text = Point(x=4 * mooveX,
                                                y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]])
                else:
                    sqrt_t100_vertical_line = None
                    sqrt_t100_horizontal_line = None
                    sqrt_t100_text = None
                    sqrt_strain100_text = None
            else:
                sqrt_t100_vertical_line = None
                sqrt_t100_horizontal_line = None
                sqrt_t100_text = None
                sqrt_strain100_text = None

            if self.processed_points_log.Cv:
                time_log = self._test_data.time

                mooveX = (time_log[-1] - time_log[0]) * 2 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[0]) \
                         * 3 / 100

                log_t100_vertical_line = point_to_xy(
                    Point(x=10**(self.processed_points_log.Cv.x),
                          y=self._test_data.volume_strain_approximate[0] - 4 * mooveY),
                    Point(x=10**(self.processed_points_log.Cv.x), y=self.processed_points_log.Cv.y))
                log_t100_horizontal_line = point_to_xy(Point(x=5 * mooveX, y=self.processed_points_log.Cv.y),
                                                       Point(x=10**(self.processed_points_log.Cv.x),
                                                             y=self.processed_points_log.Cv.y))

                log_t100_text = Point(x=10**(self.processed_points_log.Cv.x),
                                      y=self._test_data.volume_strain_approximate[0] - 4 * mooveY)
                log_strain100_text = Point(x=5 * mooveX, y=self.processed_points_log.Cv.y)
                d0 = Point(x=self._test_data.time_log[0], y=self._test_result.d0)
            else:
                log_t100_vertical_line = None
                log_t100_horizontal_line = None
                log_t100_text = None
                log_strain100_text = None
                d0 = None

            return {"volume_strain_approximate": self._test_data.volume_strain_approximate,

                    "time_sqrt": self._test_data.time_sqrt,
                    "sqrt_line_points": self.processed_points_sqrt,

                    "sqrt_t90_vertical_line": sqrt_t90_vertical_line,
                    "sqrt_t90_horizontal_line": sqrt_t90_horizontal_line,
                    "sqrt_t90_text": sqrt_t90_text,
                    "sqrt_strain90_text": sqrt_strain90_text,

                    "sqrt_t100_vertical_line": sqrt_t100_vertical_line,
                    "sqrt_t100_horizontal_line": sqrt_t100_horizontal_line,
                    "sqrt_t100_text": sqrt_t100_text,
                    "sqrt_strain100_text": sqrt_strain100_text,

                    "time_log": self._test_data.time_log,
                    "log_line_points": self.processed_points_log,
                    "log_line_1": self.processed_points_log,
                    "d0": d0,

                    "log_t100_vertical_line": log_t100_vertical_line,
                    "log_t100_horizontal_line": log_t100_horizontal_line,
                    "log_t100_text": log_t100_text,
                    "log_strain100_text": log_strain100_text}

        else:
            return None

    def get_plot_data_sqrt(self):
        """Получение данных для построения графиков"""
        if self._test_data.volume_strain_approximate is not None:
            if self.processed_points_sqrt.Cv:
                mooveX = (self._test_data.time_sqrt[-1] - self._test_data.time_sqrt[0]) * 1 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[
                    0]) * 3 / 100

                sqrt_t90_vertical_line = point_to_xy(Point(x=self.processed_points_sqrt.Cv.x,
                                                           y=max(self._test_data.volume_strain_approximate[0],
                                                                 self.processed_points_sqrt.line_start_point.y) - 4 * mooveY),
                                                     Point(x=self.processed_points_sqrt.Cv.x,
                                                           y=self.processed_points_sqrt.Cv.y))
                sqrt_t90_horizontal_line = point_to_xy(Point(x=5 * mooveX, y=self.processed_points_sqrt.Cv.y),
                                                       Point(x=self.processed_points_sqrt.Cv.x,
                                                             y=self.processed_points_sqrt.Cv.y))
                sqrt_t90_text = Point(x=self.processed_points_sqrt.Cv.x,
                                      y=max(self._test_data.volume_strain_approximate[0],
                                            self.processed_points_sqrt.line_start_point.y) - 2.70 * mooveY)
                sqrt_strain90_text = Point(x=4 * mooveX, y=self.processed_points_sqrt.Cv.y)

            else:
                sqrt_t90_vertical_line = None
                sqrt_t90_horizontal_line = None
                sqrt_t90_text = None
                sqrt_strain90_text = None

            if self._test_result.strain100_sqrt:

                index_sqrt_strain_100, = np.where(
                    self._test_data.volume_strain_approximate <= self._test_result.strain100_sqrt)

                if len(index_sqrt_strain_100):
                    sqrt_t100_vertical_line = point_to_xy(Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                y=max(self._test_data.volume_strain_approximate[0],
                                                                      self.processed_points_sqrt.line_start_point.y) - 4 * mooveY),
                                                          Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                y=self._test_data.volume_strain_approximate[
                                                                    index_sqrt_strain_100[0]]))
                    sqrt_t100_horizontal_line = point_to_xy(
                        Point(x=4 * mooveX, y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]),
                        Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                              y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]))

                    sqrt_t100_text = Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                           y=max(self._test_data.volume_strain_approximate[0],
                                                 self.processed_points_sqrt.line_start_point.y) - 2.70 * mooveY)

                    sqrt_strain100_text = Point(x=4 * mooveX,
                                                y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]])
                else:
                    sqrt_t100_vertical_line = None
                    sqrt_t100_horizontal_line = None
                    sqrt_t100_text = None
                    sqrt_strain100_text = None

                index_sqrt_strain_50, = np.where(
                    self._test_data.volume_strain_approximate <= self._test_result.strain50_sqrt)

                if len(index_sqrt_strain_50):
                    sqrt_t50_vertical_line = point_to_xy(Point(x=self._test_data.time_sqrt[index_sqrt_strain_50[0]],
                                                               y=max(self._test_data.volume_strain_approximate[0],
                                                                     self.processed_points_sqrt.line_start_point.y) - 5 * mooveY),
                                                         Point(x=self._test_data.time_sqrt[index_sqrt_strain_50[0]],
                                                               y=self._test_data.volume_strain_approximate[
                                                                   index_sqrt_strain_50[0]]))
                    sqrt_t50_horizontal_line = point_to_xy(
                        Point(x=4 * mooveX, y=self._test_data.volume_strain_approximate[index_sqrt_strain_50[0]]),
                        Point(x=self._test_data.time_sqrt[index_sqrt_strain_50[0]],
                              y=self._test_data.volume_strain_approximate[index_sqrt_strain_50[0]]))

                    sqrt_t50_text = Point(x=self._test_data.time_sqrt[index_sqrt_strain_50[0]],
                                          y=max(self._test_data.volume_strain_approximate[0],
                                                self.processed_points_sqrt.Cv.y) - 2.70 * mooveY)

                    sqrt_strain50_text = Point(x=4 * mooveX,
                                               y=self._test_data.volume_strain_approximate[index_sqrt_strain_50[0]])
                else:
                    sqrt_t50_vertical_line = None
                    sqrt_t50_horizontal_line = None
                    sqrt_t50_text = None
                    sqrt_strain50_text = None

            else:
                sqrt_t100_vertical_line = None
                sqrt_t100_horizontal_line = None
                sqrt_t100_text = None
                sqrt_strain100_text = None

                sqrt_t50_vertical_line = None
                sqrt_t50_horizontal_line = None
                sqrt_t50_text = None
                sqrt_strain50_text = None

            return {"volume_strain_approximate": self._test_data.volume_strain_approximate,

                    "time_sqrt": self._test_data.time_sqrt,
                    "sqrt_line_points": self.processed_points_sqrt,

                    "time": self._test_data.time_cut**0.5,
                    "volume_strain": self._test_data.volume_strain,

                    "sqrt_t50_vertical_line": sqrt_t50_vertical_line,
                    "sqrt_t50_horizontal_line": sqrt_t50_horizontal_line,
                    "sqrt_t50_text": sqrt_t50_text,
                    "sqrt_strain50_text": sqrt_strain50_text,

                    "sqrt_t90_vertical_line": sqrt_t90_vertical_line,
                    "sqrt_t90_horizontal_line": sqrt_t90_horizontal_line,
                    "sqrt_t90_text": sqrt_t90_text,
                    "sqrt_strain90_text": sqrt_strain90_text,

                    "sqrt_t100_vertical_line": sqrt_t100_vertical_line,
                    "sqrt_t100_horizontal_line": sqrt_t100_horizontal_line,
                    "sqrt_t100_text": sqrt_t100_text,
                    "sqrt_strain100_text": sqrt_strain100_text}

        else:
            return None

    def get_plot_data_log(self):
        """Получение данных для построения графиков"""
        if self._test_data.volume_strain_approximate is not None:
            if self.processed_points_log.Cv:
                mooveX = (self._test_data.time_log[-1] - self._test_data.time_log[0]) * 2 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[0]) \
                         *3 / 100

                log_t100_vertical_line = point_to_xy(
                    Point(x=self.processed_points_log.Cv.x,
                          y=self._test_data.volume_strain_approximate[0] - 4 * mooveY),
                    Point(x=self.processed_points_log.Cv.x, y=self.processed_points_log.Cv.y))
                log_t100_horizontal_line = point_to_xy(Point(x=4 * mooveX, y=self.processed_points_log.Cv.y),
                                                       Point(x=self.processed_points_log.Cv.x,
                                                             y=self.processed_points_log.Cv.y))

                log_t100_text = Point(x=self.processed_points_log.Cv.x,
                                      y=self._test_data.volume_strain_approximate[0] - 3 * mooveY)
                log_strain100_text = Point(x=3 * mooveX, y=self.processed_points_log.Cv.y)
                d0 = Point(x=self._test_data.time_log[0], y=self._test_result.d0)
                d0_line = point_to_xy(Point(x=self._test_data.time_log[0] + 1.5 * mooveX,
                                            y=self._test_result.d0),
                                        Point(x=self._test_data.time_log[-1],
                                              y=self._test_result.d0))
            else:
                log_t100_vertical_line = None
                log_t100_horizontal_line = None
                log_t100_text = None
                log_strain100_text = None
                d0 = None
                d0_line = None

            return {"volume_strain_approximate": self._test_data.volume_strain_approximate,
                    "time": self._test_data.time_cut,
                    "volume_strain": self._test_data.volume_strain_cut,

                    "time_log": self._test_data.time_log,
                    "log_line_points": self.processed_points_log,
                    "log_line_1": self.processed_points_log,
                    "d0": d0,
                    "d0_line": d0_line,

                    "log_t100_vertical_line": log_t100_vertical_line,
                    "log_t100_horizontal_line": log_t100_horizontal_line,
                    "log_t100_text": log_t100_text,
                    "log_strain100_text": log_strain100_text}
        else:
            return None

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '10'
        rcParams['axes.edgecolor'] = 'black'

        plots = self.get_plot_data()
        res = self.get_test_results()
        if plots is not None:
            plots = self.get_plot_data_sqrt()
            figure = plt.figure(figsize=[9.3, 6])
            figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

            ax_sqrt = figure.add_subplot(2, 1, 1)
            ax_sqrt.grid(axis='both')
            ax_sqrt.set_xlabel("Время, мин")
            ax_sqrt.set_ylabel("Объемная деформация $ε_v$, д.е.")

            ax_log = figure.add_subplot(2, 1, 2)
            ax_log.grid(axis='both')
            ax_log.set_xlabel("Время, мин")
            ax_log.set_ylabel("Объемная деформация $ε_v$, д.е.")

            # Квадратный корень
            # Основной график
            ax_sqrt.plot(plots["time_sqrt"], plots["volume_strain_approximate"],
                         **plotter_params["static_loading_main_line"])

            # Линии обработки
            if plots["sqrt_line_points"]:
                # Основные линии обработки
                ax_sqrt.plot(
                    *point_to_xy(plots["sqrt_line_points"].line_start_point, plots["sqrt_line_points"].line_end_point),
                    **plotter_params["static_loading_sandybrown_line"])
                if plots["sqrt_line_points"].Cv:
                    ax_sqrt.plot(*point_to_xy(plots["sqrt_line_points"].line_start_point, plots["sqrt_line_points"].Cv),
                                 **plotter_params["static_loading_sandybrown_line"])

                    # Точки концов линий
                    ax_sqrt.scatter(*plots["sqrt_line_points"].line_start_point, zorder=5, color="dimgray")
                    ax_sqrt.scatter(*plots["sqrt_line_points"].line_end_point, zorder=5, color="dimgray")

                    # Точки обработки
                    ax_sqrt.scatter(*plots["sqrt_line_points"].Cv, zorder=5, color="tomato")

                    # Пунктирные линии
                    ax_sqrt.plot(*plots["sqrt_t90_vertical_line"], **plotter_params["static_loading_black_dotted_line"])
                    ax_sqrt.plot(*plots["sqrt_t90_horizontal_line"],
                                 **plotter_params["static_loading_black_dotted_line"])

                    if plots["sqrt_t100_vertical_line"]:
                        # ax_sqrt.plot(*plots["sqrt_t50_vertical_line"], **plotter_params["static_loading_black_dotted_line"])
                        # ax_sqrt.plot(*plots["sqrt_t50_horizontal_line"], **plotter_params["static_loading_black_dotted_line"])
                        ax_sqrt.plot(*plots["sqrt_t100_vertical_line"],
                                     **plotter_params["static_loading_black_dotted_line"])
                        ax_sqrt.plot(*plots["sqrt_t100_horizontal_line"],
                                     **plotter_params["static_loading_black_dotted_line"])

                    # Текстовые подписи
                    ax_sqrt.text(*plots["sqrt_t90_text"], '$\sqrt{t_{90}}$', horizontalalignment='center',
                                 verticalalignment='bottom')
                    ax_sqrt.text(*plots["sqrt_strain90_text"], '$ε_{90}$', horizontalalignment='right',
                                 verticalalignment='center')
                    # ax_sqrt.text(*plots["sqrt_t50_text"], '$\sqrt{t_{50}}$', horizontalalignment='center',
                    # verticalalignment='bottom')
                    # ax_sqrt.text(*plots["sqrt_strain50_text"], '$ε_{50}$', horizontalalignment='right',
                    # verticalalignment='center')
                    if plots["sqrt_t100_text"]:
                        ax_sqrt.text(*plots["sqrt_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                     verticalalignment='bottom')
                        ax_sqrt.text(*plots["sqrt_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                     verticalalignment='center')

                    ax_sqrt.plot([], [], label="$C_{v}$" + " = " + str(res["Cv_sqrt"]),
                                 color="#eeeeee")
                    #ax_sqrt.plot([], [], label="$t_{100}$" + " = " + str(round(res["t100_sqrt"])),
                                 #color="#eeeeee")
                    ax_sqrt.legend()

            plots = self.get_plot_data_log()
            # Логарифм
            # Основной график
            ax_log.plot(plots["time_log"], plots["volume_strain_approximate"],
                        **plotter_params["static_loading_main_line"])

            # Линии обработки
            if plots["log_line_points"]:
                # Основные линии обработки
                ax_log.plot(*point_to_xy(plots["log_line_points"].first_line_start_point,
                                         plots["log_line_points"].first_line_end_point),
                            **plotter_params["static_loading_sandybrown_line"])
                ax_log.plot(*point_to_xy(plots["log_line_points"].second_line_start_point,
                                         plots["log_line_points"].second_line_end_point),
                            **plotter_params["static_loading_sandybrown_line"])

                # Точки концов линий
                ax_log.scatter(*plots["log_line_points"].first_line_start_point, zorder=5, color="dimgray")
                ax_log.scatter(*plots["log_line_points"].first_line_end_point, zorder=5, color="dimgray")
                ax_log.scatter(*plots["log_line_points"].second_line_start_point, zorder=5, color="dimgray")
                ax_log.scatter(*plots["log_line_points"].second_line_end_point, zorder=5, color="dimgray")

                # Точки обработки
                if plots["log_line_points"].Cv:
                    ax_log.scatter(*plots["log_line_points"].Cv, zorder=5, color="tomato")
                    ax_log.scatter(*plots["d0"], zorder=5, color="tomato")

                    # Пунктирные линии
                    ax_log.plot(*plots["log_t100_vertical_line"], **plotter_params["static_loading_black_dotted_line"])
                    ax_log.plot(*plots["log_t100_horizontal_line"],
                                **plotter_params["static_loading_black_dotted_line"])

                    # Текстовые подписи
                    ax_log.text(*plots["log_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                verticalalignment='bottom')
                    ax_log.text(*plots["log_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                verticalalignment='center')

                    ax_log.plot([], [], label="$C_{v}$" + " = " + str(res["Cv_log"]), color="#eeeeee")
                    ax_log.plot([], [], label="$t_{100}$" + " = " + str(res["t100_log"]),
                                color="#eeeeee")
                    ax_log.plot([], [], label="$C_{a}$" + " = " + str(res["Ca_log"]), color="#eeeeee")
                    ax_log.legend()

            if save_path:
                try:
                    plt.savefig(save_path, format="png")
                except:
                    pass

    def check_none(self):
        """Проверка заполнености массива времени"""
        if self._test_data.time is None:
            return False
        else:
            return True

    def define_click_point(self, x, y, consolidation_type):
        """Метод принимает координаты точки и тип консолидации. Возвращает номер точки или None"""
        if all((self.processed_points_sqrt.line_start_point, self.processed_points_sqrt.line_end_point)):

            if consolidation_type == "sqrt":
                # Определим координаты элипса для определения точки
                a = (np.max(self._test_data.time_sqrt) / 20) ** 2
                b = (np.min(self._test_data.volume_strain_approximate) / 20) ** 2

                if (((x - self.processed_points_sqrt.line_start_point.x) ** 2) / a) + (
                        ((y - self.processed_points_sqrt.line_start_point.y) ** 2) / b) <= 1:
                    return "line_start_point"
                elif (((x - self.processed_points_sqrt.line_end_point.x) ** 2) / a) + (
                        ((y - self.processed_points_sqrt.line_end_point.y) ** 2) / b) <= 1:
                    return "line_end_point"
                else:
                    return None

            elif consolidation_type == "log":
                a = (np.max(self._test_data.time_log) / 20) ** 2
                b = (np.min(self._test_data.volume_strain_approximate) / 20) ** 2

                if (((x - self.processed_points_log.first_line_start_point.x) ** 2) / a) + (
                        ((y - self.processed_points_log.first_line_start_point.y) ** 2) / b) <= 1:
                    return "first_line_start_point"
                elif (((x - self.processed_points_log.first_line_end_point.x) ** 2) / a) + (
                        ((y - self.processed_points_log.first_line_end_point.y) ** 2) / b) <= 1:
                    return "first_line_end_point"
                elif (((x - self.processed_points_log.second_line_start_point.x) ** 2) / a) + (
                        ((y - self.processed_points_log.second_line_start_point.y) ** 2) / b) <= 1:
                    return "second_line_start_point"
                elif (((x - self.processed_points_log.second_line_end_point.x) ** 2) / a) + (
                        ((y - self.processed_points_log.second_line_end_point.y) ** 2) / b) <= 1:
                    return "second_line_end_point"
                else:
                    return None

    def moove_catch_point(self, x, y, point_identificator, canvas):
        """Метод обрабатывает значения полученной точки и запускает перерасчет"""
        if canvas == "sqrt":
            object = getattr(self.processed_points_sqrt, point_identificator)
            if point_identificator == "line_start_point":
                object.x = 0
            else:
                object.x = x
            object.y = y
            self._sqrt_processing(processed_points_sqrt=self.processed_points_sqrt)
        if canvas == "log":
            object = getattr(self.processed_points_log, point_identificator)
            object.x = x
            object.y = y
            self._log_processing(processed_points_log=self.processed_points_log)

    def get_processing_parameters(self):
        "Словарь данных обработки для преобработки"
        return {
            "cut": {
                "left": self._test_cut_position.left,
                "right": self._test_cut_position.right
            },

            "interpolate": {
                "type": self._interpolation_type,
                "param": self._interpolation_param
            },

            "points": {
                "sqrt": {
                    "line_start_point": {
                        "x": self.processed_points_sqrt.line_start_point.x,
                        "y": self.processed_points_sqrt.line_start_point.y
                    },
                    "line_end_point": {
                        "x": self.processed_points_sqrt.line_end_point.x,
                        "y": self.processed_points_sqrt.line_end_point.y
                    }
                },
                "log": {
                    "first_line_start_point": {
                        "x": self.processed_points_log.first_line_start_point.x,
                        "y": self.processed_points_log.first_line_start_point.y
                    },
                    "first_line_end_point": {
                        "x": self.processed_points_log.first_line_end_point.x,
                        "y": self.processed_points_log.first_line_end_point.y
                    },
                    "second_line_start_point": {
                        "x": self.processed_points_log.second_line_start_point.x,
                        "y": self.processed_points_log.second_line_start_point.y
                    },
                    "second_line_end_point": {
                        "x": self.processed_points_log.second_line_end_point.x,
                        "y": self.processed_points_log.second_line_end_point.y
                    },
                }
            }
        }

    def set_processing_parameters(self, params):
        self._test_cut_position.left = params["cut"]["left"]
        self._test_cut_position.right = params["cut"]["right"]
        self._cut()
        self._interpolate_volume_strain(type=params["interpolate"]["type"], param=params["interpolate"]["param"])
        processed_points_sqrt = AttrDict(
            {
                "line_start_point": Point(x=params["points"]["sqrt"]["line_start_point"]["x"],
                                          y=params["points"]["sqrt"]["line_start_point"]["y"]),
                "line_end_point": Point(x=params["points"]["sqrt"]["line_end_point"]["x"],
                                        y=params["points"]["sqrt"]["line_end_point"]["y"])
            })
        processed_points_log = AttrDict(
            {
                "first_line_start_point": Point(x=params["points"]["log"]["first_line_start_point"]["x"],
                                                y=params["points"]["log"]["first_line_start_point"]["y"]),
                "first_line_end_point": Point(x=params["points"]["log"]["first_line_end_point"]["x"],
                                              y=params["points"]["log"]["first_line_end_point"]["y"]),
                "second_line_start_point": Point(x=params["points"]["log"]["second_line_start_point"]["x"],
                                                 y=params["points"]["log"]["second_line_start_point"]["y"]),
                "second_line_end_point": Point(x=params["points"]["log"]["second_line_end_point"]["x"],
                                               y=params["points"]["log"]["second_line_end_point"]["y"])
            })

        self._sqrt_processing(processed_points_sqrt)
        self._log_processing(processed_points_log)

    def _interpolate_volume_strain(self, type="poly", param=8):
        """Интерполяция объемной деформации для удобства обработки"""

        # Сделаем чтобы на осях кв.корня и логарифма шаг по оси был постоянным
        self._test_data.time_sqrt = np.linspace(self._test_data.time_cut[0] ** 0.5, self._test_data.time_cut[-1] ** 0.5, self.points_count)
        #self._test_data.time_log = np.log10(np.linspace(0., self._test_data.time_cut[-1] ** 0.5, self.points_count))
        print(f"self._test_data.time_cut[0] ** 0.5 : {self._test_data.time_cut[0] ** 0.5}")
        if type == "poly":
            # Аппроксимация полиномом
            poly_pow = param
            self._test_data.volume_strain_approximate = np.polyval(np.polyfit(self._test_data.time_cut ** 0.5,
                                                                              self._test_data.volume_strain_cut,
                                                                              poly_pow), self._test_data.time_sqrt)

        elif type == "ermit":
            # Интерполяция Эрмита
            self._test_data.time_sqrt, self._test_data.volume_strain_cut = make_increas(self._test_data.time_sqrt,
                                                                                        self._test_data.volume_strain_cut)
            self._test_data.time_log = np.log10(self._test_data.time_sqrt ** 2)

            self._test_data.volume_strain_approximate = pchip_interpolate(self._test_data.time_cut ** 0.5,
                                                                          self._test_data.volume_strain_cut,
                                                                          self._test_data.time_sqrt)
            self._test_data.volume_strain_approximate = \
                ndimage.gaussian_filter(self._test_data.volume_strain_approximate, param, order=0)

    def _cut(self):
        """Создание новых обрезанных массивов"""
        self._test_data.time_cut = self._test_data.time[
                                   self._test_cut_position.left:self._test_cut_position.right] # - \
                                   #self._test_data.time[self._test_cut_position.left]
        self._test_data.volume_strain_cut = self._test_data.volume_strain[
                                            self._test_cut_position.left:self._test_cut_position.right]

    def _sqrt_processing(self, processed_points_sqrt=None):

        if processed_points_sqrt:
            self.processed_points_sqrt = processed_points_sqrt
        else:
            self.processed_points_sqrt = ModelTriaxialConsolidation.define_sqrt_consolidation_points(
                self._test_data.time_sqrt,
                self._test_data.volume_strain_approximate)

        self.processed_points_sqrt.Cv = ModelTriaxialConsolidation.define_cv_sqrt(self._test_data.time_sqrt,
                                                                                  self._test_data.volume_strain_approximate,
                                                                                  self.processed_points_sqrt)
        if self.processed_points_sqrt.Cv:
            self._test_result.Cv_sqrt = round(((0.848 * 2 * 2) / (4 * self.processed_points_sqrt.Cv.x ** 2)), 3)
            self._test_result.t90_sqrt = self.processed_points_sqrt.Cv.x ** 2
            # print(f"sqrt T90 processing: {self.processed_points_sqrt.Cv.x}")
            # print(f"{self._test_result.Cv_sqrt}")

            self._test_result.t100_sqrt, self._test_result.strain100_sqrt = interpolated_intercept(
                self._test_data.time_sqrt, np.full(len(self._test_data.time_sqrt),
                                                   ((self.processed_points_sqrt.Cv.y -
                                                     self._test_data.volume_strain_approximate[0]) / 0.9) +
                                                   self._test_data.volume_strain_approximate[0]),
                self._test_data.volume_strain_approximate)
            if self._test_result.t100_sqrt == 0 or self._test_result.strain100_sqrt == 0:
                self._test_result.t100_sqrt = None
                self._test_result.strain100_sqrt = None
            else:
                self._test_result.t100_sqrt = self._test_result.t100_sqrt ** 2

                self._test_result.t50_sqrt, self._test_result.strain50_sqrt = interpolated_intercept(
                    self._test_data.time_sqrt, np.full(len(self._test_data.time_sqrt),

                                                       (self._test_result.strain100_sqrt -
                                                        self._test_data.volume_strain_approximate[0]) / 2 +
                                                       self._test_data.volume_strain_approximate[0]),
                    self._test_data.volume_strain_approximate)

                self._test_result.t50_sqrt = self._test_result.t50_sqrt ** 2

                self._test_result.velocity = (76 - self._test_data.delta_h_consolidation) * 0.15 / \
                                             (self._test_result.t50_sqrt * 64)
        else:
            self._test_result.Cv_sqrt = None
            self._test_result.t90_sqrt = None
            self._test_result.t100_sqrt = None
            self._test_result.strain100_sqrt = None

    def _log_processing(self, processed_points_log=None):

        if processed_points_log:
            self.processed_points_log = processed_points_log
        else:
            self.processed_points_log = ModelTriaxialConsolidation.define_log_consolidation_points(
                self._test_data.time_log,
                self._test_data.volume_strain_approximate)

        self.processed_points_log.Cv = ModelTriaxialConsolidation.define_cv_log(self._test_data.time_log,
                                                                                self.processed_points_log,
                                                                                self._test_data.volume_strain_approximate)
        if self.processed_points_log.Cv:
            if self.processed_points_log.Cv.y > np.max(self._test_data.volume_strain_approximate):
                self.processed_points_log.Cv = None
            self._test_result.d0 = ModelTriaxialConsolidation.find_d0(10**self._test_data.time_log,
                                                                      self._test_data.volume_strain_approximate)

            '''strain50 = interpolated_intercept(self._test_data.time_log, np.full(len(self._test_data.time_log),
                                                                                ((self.processed_points_log.Cv.y +
                                                                                  self._test_result.d0) / 2)),
                                              self._test_data.volume_strain_approximate)
            self._test_result.t50_log = round(10 ** strain50[0])'''
            #
            x, y = intersection(
                x1=self._test_data.time_log,
                y1=np.full(len(self._test_data.time_log), ((self.processed_points_log.Cv.y + self._test_result.d0) / 2)),
                x2=self._test_data.time_log,
                y2=self._test_data.volume_strain_approximate,
            )

            self._test_result.t50_log = 10**x[0]

            self._test_result.Cv_log = np.round(((2 * 2 * 0.197) / (4 * self._test_result.t50_log)), 4)

            self._test_result.Ca_log = np.round(((abs(self.processed_points_log.second_line_end_point.y) -
                                               abs(abs(self.processed_points_log.second_line_start_point.y)))
                                              / (self.processed_points_log.second_line_end_point.x -
                                                 self.processed_points_log.second_line_start_point.x)), 4)

            self._test_result.t100_log = np.round(10**self.processed_points_log.Cv.x )
            self._test_result.strain100_log = self.processed_points_log.Cv.y

            self._test_result.Kf_log = ModelTriaxialConsolidation.define_Kf(self._test_result.strain100_log,
                                                                            self._test_result.d0, self._test_params.p_max,
                                                                            self._test_result.Cv_log)

        else:
            self._test_result.d0 = None
            self._test_result.t50_log = None
            self._test_result.Cv_log = None
            self._test_result.Ca_log = None
            self._test_result.t100_log = None
            self._test_result.strain100_log = None
            self._test_result.Kf_log = None

    @staticmethod
    def define_Kf(strain100, strain0, pmax, Cv):
        """Рассчет коэффиуиента фильтрации"""
        Cv = Cv / ((10 ** 4) * 60)  # м2/c
        E_filtr_cons = pmax / abs(strain0 - strain100)
        E_filtr_cons *= 10 ** 6  # Па
        gamma = 9.81 * 10 ** 3
        Kf = (Cv * gamma) / E_filtr_cons
        Kf *= 86400  # м/сут
        return Kf

    @staticmethod
    def define_sqrt_consolidation_points(time, volume_strain):
        """Поиск точек кривой прямолинейного участка консолидации в масштабе квадратного корня"""

        def define_AB(time, volume_strain, params):
            processed_points_sqrt = AttrDict({"line_start_point": Point(x=None, y=None),
                                              "line_end_point": Point(x=None, y=None),
                                              "Cv": Point(x=None, y=None)})

            A, B = find_line_area(time, volume_strain, *params)
            line_1 = np.array(line(A, B, time))
            end_point, = np.where(line_1 < np.min(volume_strain))

            if len(end_point) == 0:
                processed_points_sqrt.line_start_point = None
                processed_points_sqrt.line_end_point = None
                processed_points_sqrt.Cv = None
            else:
                processed_points_sqrt.line_end_point.x = time[end_point[0]]
                processed_points_sqrt.line_end_point.y = line_1[end_point[0]]
                processed_points_sqrt.line_start_point.x = 0
                processed_points_sqrt.line_start_point.y = B
            return processed_points_sqrt

        for params in [(0.3, 3, [0.95, 1]), (0.5, 10, [0.9, 1])]:
            processed_points_sqrt = define_AB(time, volume_strain, params)
            if all(processed_points_sqrt):
                return processed_points_sqrt

        return AttrDict({"line_start_point": Point(x=time[0], y=volume_strain[0]),
                         "line_end_point": Point(x=time[-1], y=volume_strain[-1])})

    @staticmethod
    def define_log_consolidation_points(time, volume_strain):
        """Поиск точек консолидации"""
        processed_points_log = AttrDict(
            {"first_line_start_point": Point(x=None, y=None),
             "first_line_end_point": Point(x=None, y=None),
             "second_line_start_point": Point(x=None, y=None),
             "second_line_end_point": Point(x=None, y=None)})

        len_time = len(time)
        A1, B1 = find_line_area(time[0:int(len_time * 0.8)],
                                volume_strain[0:int(len_time * 0.8)], 0.5, 3, [0.8, 1])
        A2, B2 = find_line_area(time[int(len_time * 0.75):len_time],
                                volume_strain[int(len_time * 0.75):len_time], 1, 5, [0.3, 1])

        line_1 = line(A1, B1, time)
        line_2 = line(A2, B2, time)

        try:
            index_line_1_start, = np.where(line_1 < volume_strain[0])
            index_line_1_end, = np.where(line_1 < 1.05 * volume_strain[-1])

            processed_points_log.first_line_start_point.x = (time[index_line_1_start[0]])
            processed_points_log.first_line_start_point.y = line_1[index_line_1_start[0]]

            processed_points_log.first_line_end_point.x = (time[index_line_1_end[0]])
            processed_points_log.first_line_end_point.y = line_1[index_line_1_end[0]]

            processed_points_log.second_line_start_point.x = (time[int(len(time) / 10)])
            processed_points_log.second_line_start_point.y = line_2[int(len(time) / 10)]

            processed_points_log.second_line_end_point.x = (time[-1])
            processed_points_log.second_line_end_point.y = line_2[-1]
        except IndexError:
            index_line_1_start, = np.where(
                volume_strain < (volume_strain[-1] - volume_strain[0]) * 0.1 + volume_strain[0])
            index_line_1_end, = np.where(
                volume_strain < (volume_strain[-1] - volume_strain[0]) * 0.8 + volume_strain[0])

            processed_points_log.first_line_start_point.x = time[index_line_1_start[0]]
            processed_points_log.first_line_start_point.y = line_1[index_line_1_start[0]]

            processed_points_log.first_line_end_point.x = time[index_line_1_end[0]]
            processed_points_log.first_line_end_point.y = line_1[index_line_1_end[0]]

            processed_points_log.second_line_start_point.x = time[int(len(time) / 3)]
            processed_points_log.second_line_start_point.y = volume_strain[int(len(time) / 3)]

            processed_points_log.second_line_end_point.x = time[-1]
            processed_points_log.second_line_end_point.y = volume_strain[-1]

        return processed_points_log

    @staticmethod
    def define_cv_sqrt(time, volume_strain, points_consolidations):
        if points_consolidations.line_end_point:
            A = (points_consolidations.line_end_point.y - points_consolidations.line_start_point.y) / \
                (points_consolidations.line_end_point.x - points_consolidations.line_start_point.x)
            B = points_consolidations.line_start_point.y
            _line = np.array(line(A / 1.15, B, time))

            xc, yc = interpolated_intercept(time, volume_strain, _line)
        else:
            return None

        if yc:
            Cv = Point(x=xc, y=yc)
        else:
            Cv = None

        return Cv

    @staticmethod
    def define_cv_log(time, points_consolidations, vs):
        A1 = (points_consolidations.first_line_end_point.y - points_consolidations.first_line_start_point.y) / \
             (points_consolidations.first_line_end_point.x - points_consolidations.first_line_start_point.x)
        B1 = points_consolidations.first_line_end_point.y - A1 * points_consolidations.first_line_end_point.x
        _line1 = np.array(line(A1, B1, time))

        A2 = (points_consolidations.second_line_end_point.y - points_consolidations.second_line_start_point.y) / \
             (points_consolidations.second_line_end_point.x - points_consolidations.second_line_start_point.x)
        B2 = points_consolidations.second_line_end_point.y - A2 * points_consolidations.second_line_end_point.x
        _line2 = np.array(line(A2, B2, time))

        xc, yc = interpolated_intercept(time, _line1, _line2)

        if yc and str(yc) != "nan":
            Cv = Point(x=xc, y=yc)
        else:
            Cv = None

        return Cv

    @staticmethod
    def find_d0(time, strain):
        """Поиск d0 для вторичной консолидации"""
        d0 = strain[0] + (np.interp(0.1, time, strain) - np.interp(0.4, time, strain))
        return d0

class ModelTriaxialConsolidationSoilTest(ModelTriaxialConsolidation):
    """Модель моделирования дконсолидации
    Наследует обработчик и структуру данных из ModelTriaxialConsolidation

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые. Кривые
        рандомно выбираются из 3х возможных вариантов функций

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых"""

    def __init__(self):
        super().__init__()
        self._test_params = AttrDict({"Cv": None,
                                      "Ca": None,
                                      "E": None,
                                      "sigma_3": None,
                                      "K0": None})

        self._draw_params = AttrDict({"max_time": None})

    def set_test_params(self):
        """Установка основных параметров опыта"""
        self._test_params.Cv = statment[statment.current_test].mechanical_properties.Cv
        self._test_params.Ca = statment[statment.current_test].mechanical_properties.Ca
        self._test_params.Eoed = statment[statment.current_test].mechanical_properties.Eoed
        self._test_params.p_max = statment[statment.current_test].mechanical_properties.p_max
        self._test_params.m = statment[statment.current_test].mechanical_properties.m

        self._draw_params.max_time = (((0.848 * 2 * 2) / (4 * self._test_params.Cv))) *2*2* np.random.uniform(5, 7)
        self._draw_params.strain = define_final_deformation(self._test_params.p_max, self._test_params.Eoed,
                                                            self._test_params.m)

        self._draw_params.Cv = self._test_params.Cv
        self._draw_params.Ca = self._test_params.Ca

        self._test_modeling()
        self.change_borders(0, len(self._test_data.time))

    def get_dict(self, effective_stress_after_reconsolidation):
        return ModelTriaxialConsolidationSoilTest.dictionary_consalidation(self._test_data.time,
                                                                           self._test_data.pore_volume_strain,
                                                                           self._test_data.cell_volume_strain,
                                                                           velocity=100,
                                                                           sigma_3=self._test_params.sigma_3,
                                                                           delta_h_consolidation=self._test_data.delta_h_consolidation,
                                                                           delta_h_reconsolidation=self._test_data.delta_h_reconsolidation,
                                                                           effective_stress_after_reconsolidation=effective_stress_after_reconsolidation)

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""
        params = {
            "max_time":
                {"value": self._draw_params.max_time,
                 "borders": [self._draw_params.max_time / 2, self._draw_params.max_time * 10]},
            "strain":
                {"value": -self._draw_params.strain,
                 "borders":[-self._draw_params.strain / 2, -self._draw_params.strain * 2]},
            "Cv":
                {"value": self._test_params.Cv,
                 "borders": [self._test_params.Cv / 5, self._draw_params.Cv * 5]},
            "Ca":
                {"value": self._test_params.Ca,
                 "borders": [self._test_params.Ca / 5, self._draw_params.Ca * 5]}
        }

        return params

    def set_draw_params(self, params):
        """Устанавливает переданные параметры отрисовки, считанные с ползунков, на модель"""
        self._draw_params.max_time = params["max_time"]
        self._draw_params.strain = - params["strain"]
        self._draw_params.Cv = params["Cv"]
        self._draw_params.Ca = params["Ca"]
        self._test_modeling()
        self.change_borders(0, len(self._test_data.time))

    def _test_modeling(self):
        """Функция моделирования опыта"""
        self._test_data.time, self._test_data.volume_strain, *__ = function_consalidation(
            self._draw_params.strain,
            Cv=self._draw_params.Cv,
            reverse=True,
            max_time=self._draw_params.max_time,
            Ca=-self._draw_params.Ca)




        # self._test_data.time = np.round(self._test_data.time, 3)

        # self._test_data.volume_strain = np.round(
        # self._test_data.volume_strain * np.pi * (19 ** 2) / (76) /
        # (np.pi * (19 ** 2) / (76)), 6)
        for i in range(len(self._test_data.volume_strain)):
            self._test_data.volume_strain[i] = ModelTriaxialConsolidationSoilTest.round_srain(self._test_data.volume_strain[i])

        _time, _volume_strain = ModelTriaxialConsolidationSoilTest.ordering(self._test_data.time, self._test_data.volume_strain)
        self._test_data.time, self._test_data.volume_strain = copy.deepcopy(_time), copy.deepcopy(_volume_strain)

    def save_log(self, path, name):
        if statment[statment.current_test].mechanical_properties.p_max >= 1:
            ModelTriaxialConsolidationSoilTest.save_device(path=path, time_model=self._test_data.time,
                                                       strain_model=self._test_data.volume_strain,
                                                       pressure=self._test_params.p_max,
                                                       report_number=name, device=True)
        else:
            ModelTriaxialConsolidationSoilTest.save_device(path=path, time_model=self._test_data.time,
                                                           strain_model=self._test_data.volume_strain,
                                                           pressure=self._test_params.p_max,
                                                           report_number=name, device=False)

    @property
    def test_duration(self):
        return timedelta(minutes=self._test_data.time[-1])

    @staticmethod
    def ordering(_time_model, _strain_model):
        """
                    Функция пересечения двух прямых, заданных точками
                    :param path: путь до файла
                    :param time_model: время возвращаемое функцией консолидации
                    :param strain_model: деформация возвращаемая функцией консолидации
                    :param pressure: максимальное давление консолидации
                    :param report_number: имя файла
                    """

        time_model = copy.deepcopy(_time_model)
        strain_model = copy.deepcopy(_strain_model)


        time_model *= 60
        t0 = np.random.uniform(low=20, high=21)
        hours = math.floor(time_model[-1] / 3600)
        time = [t for t in
                [6, 15, 30, 60, 2 * 60, 5 * 60, 10 * 60, 20 * 60, 30 * 60] + [h * 3600 for h in
                                                                              range(1, hours + 1)]]
        time = [t/60.0 for t in time]
        time = np.array(time)
        strain = np.interp(time, _time_model, _strain_model)
        return time, np.array(strain)

    @staticmethod
    def save_device(path: str, time_model, strain_model, pressure,
                    report_number="-".join(['ЛАБОРАТОРНЫЙ-НОМЕР', 'НОМЕР-ОБЪЕКТА', 'КК']), device=False):
        """
                    Функция пересечения двух прямых, заданных точками
                    :param path: путь до файла
                    :param time_model: время возвращаемое функцией консолидации
                    :param strain_model: деформация возвращаемая функцией консолидации
                    :param pressure: максимальное давление консолидации
                    :param report_number: имя файла
                    """

        header1 = "SampleHeight;SampleDiameter;TaskID;TaskName;TaskTypeID;TaskTypeName;AlgorithmID;AlgorithmName;Sample"
        header2 = ';'.join(['20', '71.4', '0', '', '', '', '', 'Компрессионное сжатие', ''])
        header3 = "ID;DateTime;Press;Deformation;StabEnd;Consolidation"

        time = time_model * 60 + np.round(np.random.uniform(0.1, 0.8, len(time_model)), 6)
        strain = np.hstack((np.array([0]), strain_model[:-1]))
        if device:
            pressure_array = np.hstack((np.array([0]), np.full(len(time) - 1, pressure)))
        else:
            pressure_array = np.hstack(([0], np.full(len(time) - 1, pressure))) + \
                             create_deviation_curve(time, 0.1 * pressure, val=(1, 1), points=np.random.uniform(4, 5),
                                                    borders="zero_diff")
        stab_end = np.zeros_like(pressure_array)
        stab_end[-1] = 1
        consolidation_array = np.ones_like(stab_end)
        consolidation_array[0] = 0

        with open(path + "\\" + report_number + ".csv", 'w', encoding='utf-8') as f:
            f.write(header1 + '\n')
            f.write(header2 + '\n')
            f.write(header3 + '\n')

            for i in range(len(time)):
                f.write(';'.join([f'{i + 1}',
                                  f'{np.round(time[i], 6):.6f}',
                                  f'{np.round(pressure_array[i], 2):.2f}' if device
                                  else f'{np.round(pressure_array[i], 4):.4f}',
                                  f'{round(abs(strain[i]) * 20, 2):.2f}',
                                  f'{int(stab_end[i])}',
                                  f'{int(consolidation_array[i])}']) + '\n')
        print("{} saved".format(path))
        return path

    @staticmethod
    def dictionary_consalidation(time, pore_volume_strain, cell_volume_strain, velocity=1, sigma_3=150,
                                 delta_h_consolidation=0, delta_h_reconsolidation=0,
                                 effective_stress_after_reconsolidation=0):
        """Формирует словарь консолидации"""
        # Создаем массив набора нагрузки до обжимающего давления консолидации
        sigma_3 -= effective_stress_after_reconsolidation
        load_stage_time = round(sigma_3 / velocity, 2)
        load_stage_time_array = np.arange(0, load_stage_time, 0.25)

        length = len(pore_volume_strain)

        load_stage_pore_volume_strain = np.linspace(0, pore_volume_strain[0], len(load_stage_time_array))
        load_stage_cell_volume_strain = np.linspace(0, cell_volume_strain[0], len(load_stage_time_array))

        # Добавим набор нагрузки к основным массивам
        time = np.hstack((load_stage_time_array, time + load_stage_time_array[-1]))

        pore_volume_strain = np.hstack((load_stage_pore_volume_strain, pore_volume_strain))
        cell_volume_strain = np.hstack((load_stage_cell_volume_strain, cell_volume_strain))

        # На нэтапе нагружения 'LoadStage', на основном опыте Stabilization
        index_last_loadstage, = np.where(time >= load_stage_time)
        action = ['LoadStage' for _ in range(index_last_loadstage[0])] + \
                 ['Stabilization' for _ in range(len(time) - index_last_loadstage[0])]

        action_changed = ['' for _ in range(len(time))]
        action_changed[action.index('Stabilization') - 1] = "True"
        action_changed[-1] = 'True'

        h = delta_h_consolidation - delta_h_reconsolidation
        vertical_deformation = np.hstack((
            np.linspace(0, h, len(load_stage_time_array)),
            np.random.uniform(0.9 * h, 1.1 * h, length)))

        vertical_deformation[-1] = h

        # vertical_deformation = np.linspace(0, delta_h_consolidation - delta_h_reconsolidation, len(pore_volume_strain))

        # на этапе приложения нагрузки растет от 0 до sigma_3, далее постоянно
        cell_press = np.hstack((np.linspace(0, sigma_3, len(load_stage_time_array)),
                                np.full(len(time) - len(load_stage_time_array), sigma_3)))
        data = {
            "Time": time,
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 76)),
            "SampleDiameter_mm": np.round(np.full(len(time), 38)),
            "Deviator_kPa": np.random.uniform(-1, 1, len(time)),
            "VerticalDeformation_mm": vertical_deformation,
            "CellPress_kPa": cell_press + np.random.uniform(-0.1, 0.1, len(time)),
            "CellVolume_mm3": -cell_volume_strain * np.pi * (19 ** 2) * (76 - delta_h_reconsolidation),
            "PorePress_kPa": np.random.uniform(-1, 1, len(time)),
            "PoreVolume_mm3": pore_volume_strain * np.pi * (19 ** 2) * (76 - delta_h_reconsolidation),
            "VerticalPress_kPa": cell_press + np.random.uniform(-0.1, 0.1, len(time)),
            "Trajectory": np.full(len(time), 'Consolidation')
        }
        return data

    @staticmethod
    def round_srain(x: float, precision = 4) -> float:
        """Rounds value as sensor with sensitivity = 0.0005:
            0.0000 - 0.0000
            0.0001 - 0.0000
            0.0002 - 0.0000
            0.0003 - 0.0005
            0.0004 - 0.0005
            0.0005 - 0.0005
            0.0006 - 0.0005
            0.0007 - 0.0005
            0.0008 - 0.0010
            0.0009 - 0.0010
            0.0010 - 0.0010
            0.0063 - 0.0065
        """
        order = 10 ** precision

        condition = round(x % 10 ** (-(precision - 1)) * order, 1)

        if 0 < condition <= 2:
            return round(x // (10 / order) / (order / 10), precision)
        if 2 < condition < 8:
            return round(x // (10 / order) / (order / 10) + 5 / order, precision)
        if condition >= 8:
            return round(x // (10 / order) / (order / 10) + 1 / (order / 10), precision)
        return round(x, precision)


if __name__ == '__main__':
    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"


    a = ModelTriaxialConsolidationSoilTest()
    statment.load(r"C:\Users\Пользователь\Desktop\test\Консолидация.pickle")
    statment.current_test = "2-1"
    a.set_test_params()
    a.plotter()
    plt.show()



