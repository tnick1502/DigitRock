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

__version__ = 1

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import pchip_interpolate
import scipy.ndimage as ndimage

from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, define_qf, define_E50
from static_loading.consolidation_functions import function_consalidation, function_consalidation_without_Cv
from configs.plot_params import plotter_params

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
        self._interpolation_param = 2
        self.points_count = 50
        self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}

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
             "first_line_end_point": Point(x=None, y=None),  # Правая точка первого прямолинейного участка
             "second_line_start_point": Point(x=None, y=None),  # Левая точка второго прямолинейного участка
             "second_line_end_point": Point(x=None, y=None),
             "Cv": Point(x=None, y=None)})  # Правая точка второго прямолинейного участка

        # Результаты опыта
        self._test_result = AttrDict({"Cv_sqrt": None,
                                      "t50_sqrt": None,
                                      "t90_sqrt": None,
                                      "t100_sqrt": None,
                                      "strain100_sqrt": None,
                                      "Cv_log": None,
                                      "Ca_log": None,
                                      "t50_log": None,
                                      "t100_log": None,
                                      "strain100_log": None,
                                      "d0": None,
                                      "velocity": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._reset_data()

        if test_data:
            self._test_data.time = test_data["time"]

            # Объемная деформация до обработки
            self._test_data.pore_volume_strain = test_data["pore_volume_strain"]
            self._test_data.cell_volume_strain = test_data["cell_volume_strain"]
            self._test_data.delta_h_reconsolidation = round(test_data["delta_h_reconsolidation"], 4)
            self._test_data.delta_h_consolidation = round(test_data["delta_h_consolidation"], 4)

            if abs(np.mean(self._test_data.pore_volume_strain - self._test_data.pore_volume_strain[0])) > 0.01:
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
                self.change_borders(0, len(self._test_data.time))
            elif abs(np.mean(self._test_data.cell_volume_strain - self._test_data.cell_volume_strain[0])) > 0.01:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                self.current_volume_strain = {"current": "cell_volume", "pore_volume": False, "cell_volume": True}
                self.change_borders(0, len(self._test_data.time))
            else:
                print("Этап консолидации не проводился")
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
                    "time_sqrt_origin": self._test_data.time**0.5,
                    "time_log_origin": np.log(self._test_data.time + 1),
                    "time_sqrt": self._test_data.time_sqrt,
                    "time_log": self._test_data.time_log,
                    "volume_strain_approximate": self._test_data.volume_strain_approximate}

    def choise_volume_strain(self, volume_strain):
        """Выбор данных с порового валюмометра или волюмометра с камеры для последующей обработки"""
        if self._test_data.time_sqrt is not None:
            if volume_strain == "pore_volume":
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                self.change_borders(0, len(self._test_data.time))
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                self.change_borders(0, len(self._test_data.time))

    def get_current_volume_strain(self):
        """Метод возвращает действующий волюмометр
                При получении данных проверяется, какие волюмометры были активны. Приоритетный волюмометр выбирается как
                 поровый, если в нем нет данных, то выберется камеры"""
        return self.current_volume_strain

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
                sqrt_t90_text =  Point(x=self.processed_points_sqrt.Cv.x,
                                       y=max(self._test_data.volume_strain_approximate[0],
                                             self.processed_points_sqrt.Cv.y) - 2.70 * mooveY)
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
                                                                       self.processed_points_sqrt.line_start_point.y) - 5 * mooveY),
                                                           Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                 y=self._test_data.volume_strain_approximate[
                                                                     index_sqrt_strain_100[0]]))
                    sqrt_t100_horizontal_line =  point_to_xy(
                        Point(x=4 * mooveX, y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]),
                        Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                              y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]))

                    sqrt_t100_text =  Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                            y=max(self._test_data.volume_strain_approximate[0],
                                                  self.processed_points_sqrt.Cv.y) - 2.70 * mooveY)

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


            if self.processed_points_log.Cv:
                mooveX = (self._test_data.time_log[-1] - self._test_data.time_log[0]) * 2 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[0]) \
                         * 3 / 100

                log_t100_vertical_line = point_to_xy(
                    Point(x=self.processed_points_log.Cv.x, y=self._test_data.volume_strain_approximate[0] - 4 * mooveY),
                    Point(x=self.processed_points_log.Cv.x, y=self.processed_points_log.Cv.y))
                log_t100_horizontal_line = point_to_xy(Point(x=5 * mooveX, y=self.processed_points_log.Cv.y),
                    Point(x=self.processed_points_log.Cv.x, y=self.processed_points_log.Cv.y))

                log_t100_text = Point(x=self.processed_points_log.Cv.x,
                                        y=self._test_data.volume_strain_approximate[0] - 4 * mooveY)
                log_strain100_text =  Point(x=5 * mooveX, y=self.processed_points_log.Cv.y)
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

                    "sqrt_t50_vertical_line": sqrt_t50_vertical_line,
                    "sqrt_t50_horizontal_line": sqrt_t50_horizontal_line,
                    "sqrt_t50_text": sqrt_t50_text,
                    "sqrt_strain50_text": sqrt_strain50_text,

                    "sqrt_t90_vertical_line": sqrt_t90_vertical_line,
                    "sqrt_t90_horizontal_line": sqrt_t90_horizontal_line,
                    "sqrt_t90_text": sqrt_t90_text,
                    "sqrt_strain90_text": sqrt_strain90_text,

                    "sqrt_t100_vertical_line":sqrt_t100_vertical_line,
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

        else: return None

    def get_plot_data_sqrt(self):
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
                sqrt_t90_text =  Point(x=self.processed_points_sqrt.Cv.x,
                                       y=max(self._test_data.volume_strain_approximate[0],
                                             self.processed_points_sqrt.Cv.y) - 2.70 * mooveY)
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
                                                                       self.processed_points_sqrt.line_start_point.y) - 5 * mooveY),
                                                           Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                                                 y=self._test_data.volume_strain_approximate[
                                                                     index_sqrt_strain_100[0]]))
                    sqrt_t100_horizontal_line =  point_to_xy(
                        Point(x=4 * mooveX, y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]),
                        Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                              y=self._test_data.volume_strain_approximate[index_sqrt_strain_100[0]]))

                    sqrt_t100_text = Point(x=self._test_data.time_sqrt[index_sqrt_strain_100[0]],
                                            y=max(self._test_data.volume_strain_approximate[0],
                                                  self.processed_points_sqrt.Cv.y) - 2.70 * mooveY)

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

                    "sqrt_t50_vertical_line": sqrt_t50_vertical_line,
                    "sqrt_t50_horizontal_line": sqrt_t50_horizontal_line,
                    "sqrt_t50_text": sqrt_t50_text,
                    "sqrt_strain50_text": sqrt_strain50_text,

                    "sqrt_t90_vertical_line": sqrt_t90_vertical_line,
                    "sqrt_t90_horizontal_line": sqrt_t90_horizontal_line,
                    "sqrt_t90_text": sqrt_t90_text,
                    "sqrt_strain90_text": sqrt_strain90_text,

                    "sqrt_t100_vertical_line":sqrt_t100_vertical_line,
                    "sqrt_t100_horizontal_line": sqrt_t100_horizontal_line,
                    "sqrt_t100_text": sqrt_t100_text,
                    "sqrt_strain100_text": sqrt_strain100_text}

        else: return None

    def get_plot_data_log(self):
        """Получение данных для построения графиков"""
        if self._test_data.volume_strain_approximate is not None:
            if self.processed_points_log.Cv:
                mooveX = (self._test_data.time_log[-1] - self._test_data.time_log[0]) * 2 / 100
                mooveY = (-self._test_data.volume_strain_approximate[-1] + self._test_data.volume_strain_approximate[0]) \
                         * 3 / 100

                log_t100_vertical_line = point_to_xy(
                    Point(x=self.processed_points_log.Cv.x,
                          y=self._test_data.volume_strain_approximate[0] - 4 * mooveY),
                    Point(x=self.processed_points_log.Cv.x, y=self.processed_points_log.Cv.y))
                log_t100_horizontal_line = point_to_xy(Point(x=5 * mooveX, y=self.processed_points_log.Cv.y),
                                                       Point(x=self.processed_points_log.Cv.x,
                                                             y=self.processed_points_log.Cv.y))

                log_t100_text = Point(x=self.processed_points_log.Cv.x,
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

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '10'
        rcParams['axes.edgecolor'] = 'black'


        plots = self.get_plot_data()
        res = self.get_test_results()
        if plots is not None:
            figure = plt.figure(figsize = [9.3, 6])
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
            ax_sqrt.plot(plots["time_sqrt"], plots["volume_strain_approximate"], **plotter_params["static_loading_main_line"])

            # Линии обработки
            if plots["sqrt_line_points"]:
                # Основные линии обработки
                ax_sqrt.plot(*point_to_xy(plots["sqrt_line_points"].line_start_point, plots["sqrt_line_points"].line_end_point),
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
                    ax_sqrt.plot(*plots["sqrt_t90_horizontal_line"], **plotter_params["static_loading_black_dotted_line"])

                    if plots["sqrt_t100_vertical_line"]:
                        ax_sqrt.plot(*plots["sqrt_t50_vertical_line"], **plotter_params["static_loading_black_dotted_line"])
                        ax_sqrt.plot(*plots["sqrt_t50_horizontal_line"], **plotter_params["static_loading_black_dotted_line"])
                        ax_sqrt.plot(*plots["sqrt_t100_vertical_line"], **plotter_params["static_loading_black_dotted_line"])
                        ax_sqrt.plot(*plots["sqrt_t100_horizontal_line"], **plotter_params["static_loading_black_dotted_line"])

                    # Текстовые подписи
                    ax_sqrt.text(*plots["sqrt_t90_text"], '$\sqrt{t_{90}}$', horizontalalignment='center',
                                 verticalalignment='bottom')
                    ax_sqrt.text(*plots["sqrt_strain90_text"], '$ε_{90}$', horizontalalignment='right',
                                 verticalalignment='center')
                    ax_sqrt.text(*plots["sqrt_t50_text"], '$\sqrt{t_{50}}$', horizontalalignment='center',
                                 verticalalignment='bottom')
                    ax_sqrt.text(*plots["sqrt_strain50_text"], '$ε_{50}$', horizontalalignment='right',
                                 verticalalignment='center')
                    if plots["sqrt_t100_text"]:
                        ax_sqrt.text(*plots["sqrt_t100_text"], '$\sqrt{t_{100}}$', horizontalalignment='center',
                                     verticalalignment='bottom')
                        ax_sqrt.text(*plots["sqrt_strain100_text"], '$ε_{100}$', horizontalalignment='right',
                                     verticalalignment='center')

                    ax_sqrt.plot([], [], label="$C_{v}$" + " = " + str(res["Cv_sqrt"]),
                                      color="#eeeeee")
                    ax_sqrt.plot([], [], label="$t_{100}$" + " = " + str(round(res["t100_sqrt"])),
                                      color="#eeeeee")
                    ax_sqrt.legend()

            # Логарифм
            # Основной график
            ax_log.plot(plots["time_log"], plots["volume_strain_approximate"], **plotter_params["static_loading_main_line"])

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
                    ax_log.plot(*plots["log_t100_horizontal_line"], **plotter_params["static_loading_black_dotted_line"])

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
        self._test_data.time_sqrt = np.linspace(0, self._test_data.time_cut[-1] ** 0.5, self.points_count)
        self._test_data.time_log = np.log(self._test_data.time_sqrt ** 2 + 1)

        if type == "poly":
            # Аппроксимация полиномом
            poly_pow = param
            self._test_data.volume_strain_approximate = np.polyval(np.polyfit(self._test_data.time_cut**0.5,
                                                                              self._test_data.volume_strain_cut,
                                                                              poly_pow), self._test_data.time_sqrt)

        elif type == "ermit":
            # Интерполяция Эрмита
            self._test_data.time_sqrt, self._test_data.volume_strain_cut = make_increas(self._test_data.time_sqrt,
                                                                                    self._test_data.volume_strain_cut)
            self._test_data.time_log = np.log(self._test_data.time_sqrt ** 2 + 1)
            self._test_data.volume_strain_approximate = pchip_interpolate(self._test_data.time_cut**0.5,
                                                                          self._test_data.volume_strain_cut,
                                                                          self._test_data.time_sqrt)
            self._test_data.volume_strain_approximate = \
                ndimage.gaussian_filter(self._test_data.volume_strain_approximate, param, order=0)

    def _cut(self):
        """Создание новых обрезанных массивов"""
        self._test_data.time_cut = self._test_data.time[
                                     self._test_cut_position.left:self._test_cut_position.right] - \
                                     self._test_data.time[self._test_cut_position.left]
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
            self._test_result.Cv_sqrt = round(((0.848 * 3.8 * 3.8) / (4 * self.processed_points_sqrt.Cv.x ** 2)), 3)
            self._test_result.t90_sqrt = self.processed_points_sqrt.Cv.x ** 2

            self._test_result.t100_sqrt, self._test_result.strain100_sqrt = interpolated_intercept(
                self._test_data.time_sqrt, np.full(len(self._test_data.time_sqrt),
                                                   ((self.processed_points_sqrt.Cv.y -
                                                     self._test_data.volume_strain_approximate[0]) / 0.9) +
                                                   self._test_data.volume_strain_approximate[0]),
                self._test_data.volume_strain_approximate)


            if self._test_result.t100_sqrt==0 or self._test_result.strain100_sqrt==0:
                self._test_result.t100_sqrt = None
                self._test_result.t50_sqrt = None
                self._test_result.strain50_sqrt = None
                self._test_result.strain100_sqrt = None
            else:
                self._test_result.t100_sqrt = self._test_result.t100_sqrt ** 2

                self._test_result.t50_sqrt, self._test_result.strain50_sqrt = interpolated_intercept(
                    self._test_data.time_sqrt, np.full(len(self._test_data.time_sqrt),

                                                       (self._test_result.strain100_sqrt -
                                                        self._test_data.volume_strain_approximate[0])/2 +
                                                       self._test_data.volume_strain_approximate[0]),
                    self._test_data.volume_strain_approximate)

                self._test_result.t50_sqrt = self._test_result.t50_sqrt ** 2

                self._test_result.velocity = (76 - self._test_data.delta_h_consolidation) * 0.15 / \
                                             (self._test_result.t50_sqrt * 64)

        else:
            self._test_result.Cv_sqrt = None
            self._test_result.t50_sqrt = None
            self._test_result.t90_sqrt = None
            self._test_result.t100_sqrt = None
            self._test_result.strain100_sqrt = None
            self._test_result.strain50_sqrt = None

    def _log_processing(self, processed_points_log=None):

        if processed_points_log:
            self.processed_points_log = processed_points_log
        else:
            self.processed_points_log = ModelTriaxialConsolidation.define_log_consolidation_points(
                self._test_data.time_log,
                self._test_data.volume_strain_approximate)

        self.processed_points_log.Cv = ModelTriaxialConsolidation.define_cv_log(self._test_data.time_log,
                                                                                self.processed_points_log)
        if self.processed_points_log.Cv:
            if self.processed_points_log.Cv.y > np.max(self._test_data.volume_strain_approximate):
                self.processed_points_log.Cv = None

        if self.processed_points_log.Cv:
            self._test_result.d0 = ModelTriaxialConsolidation.find_d0(self._test_data.time_log,
                                                                      self._test_data.volume_strain_approximate)

            strain50 = interpolated_intercept(self._test_data.time_log, np.full(len(self._test_data.time_log),
                                                                                ((self.processed_points_log.Cv.y +
                                                                                  self._test_result.d0) / 2)),
                                              self._test_data.volume_strain_approximate)
            self._test_result.t50_log = round(np.e ** strain50[0])


            self._test_result.Cv_log = round(((3.8 * 3.8 * 0.197) / (4 * self._test_result.t50_log)), 3)
            self._test_result.Ca_log = round(((abs(self.processed_points_log.second_line_end_point.y) -
                                                abs(abs(self.processed_points_log.second_line_start_point.y)))
                                               / (self.processed_points_log.second_line_end_point.x -
                                                  self.processed_points_log.second_line_start_point.x)), 4)



            self._test_result.t100_log = round(np.e ** self.processed_points_log.Cv.x)
            self._test_result.strain100_log = self.processed_points_log.Cv.y

        else:
            self._test_result.d0 = None
            self._test_result.t50_log = None
            self._test_result.Cv_log = None
            self._test_result.Ca_log = None
            self._test_result.t100_log = None
            self._test_result.strain100_log = None


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

            processed_points_log.first_line_start_point.x = time[index_line_1_start[0]]
            processed_points_log.first_line_start_point.y = line_1[index_line_1_start[0]]

            processed_points_log.first_line_end_point.x = time[index_line_1_end[0]]
            processed_points_log.first_line_end_point.y = line_1[index_line_1_end[0]]

            processed_points_log.second_line_start_point.x = time[int(len(time)/10)]
            processed_points_log.second_line_start_point.y = line_2[int(len(time)/10)]

            processed_points_log.second_line_end_point.x = time[-1]
            processed_points_log.second_line_end_point.y = line_2[-1]
        except IndexError:
            index_line_1_start, = np.where(volume_strain <(volume_strain[-1] - volume_strain[0])*0.1 + volume_strain[0])
            index_line_1_end, = np.where(volume_strain < (volume_strain[-1] - volume_strain[0])*0.8 + volume_strain[0])

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
            A = (points_consolidations.line_end_point.y - points_consolidations.line_start_point.y)/\
                (points_consolidations.line_end_point.x - points_consolidations.line_start_point.x)
            B = points_consolidations.line_start_point.y
            _line = np.array(line(A/1.15, B, time))

            xc, yc = interpolated_intercept(time, volume_strain, _line)
        else:
            return None

        if yc:
            Cv = Point(x=xc, y=yc)
        else:
            Cv = None

        return Cv

    @staticmethod
    def define_cv_log(time, points_consolidations):
        A1 = (points_consolidations.first_line_end_point.y - points_consolidations.first_line_start_point.y) / \
            (points_consolidations.first_line_end_point.x - points_consolidations.first_line_start_point.x)
        B1 = points_consolidations.first_line_end_point.y - A1*points_consolidations.first_line_end_point.x
        _line1 = np.array(line(A1, B1, time))

        A2 = (points_consolidations.second_line_end_point.y - points_consolidations.second_line_start_point.y) / \
             (points_consolidations.second_line_end_point.x - points_consolidations.second_line_start_point.x)
        B2 = points_consolidations.second_line_end_point.y - A2*points_consolidations.second_line_end_point.x
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

    def set_test_params(self, test_params):
        """Установка основных параметров опыта"""
        self._test_params.Cv = test_params.Cv
        self._test_params.Ca = test_params.Ca
        self._test_params.E = test_params.E50
        self._test_params.sigma_3 = test_params.sigma_3
        self._test_params.K0 = test_params.K0

        self._draw_params.max_time = (((0.848 * 3.8 * 3.8) / (4 * test_params.Cv)))*np.random.uniform(4, 5)
        self._draw_params.volume_strain_90 = np.random.uniform(0.14, 0.2)

        self._test_data.delta_h_consolidation = round((76 * (self._test_params.sigma_3 / (3 * self._test_params.E)) \
                                                + self._test_data.delta_h_reconsolidation), 5)
        self._test_modeling()
        self._test_data.volume_strain = self._test_data.pore_volume_strain
        self.change_borders(0, len(self._test_data.time))

    def set_delta_h_reconsolidation(self, delta_h_reconsolidation):
        self._test_data.delta_h_reconsolidation = round(delta_h_reconsolidation, 5)

    def get_delta_h_consolidation(self):
        return self._test_data.delta_h_consolidation

    def get_dict(self, effective_stress_after_reconsolidation):
       return ModelTriaxialConsolidationSoilTest.dictionary_consalidation(self._test_data.time,
                                                                          self._test_data.pore_volume_strain,
                                                                          self._test_data.cell_volume_strain,
                                                                          velocity=10, sigma_3=self._test_params.sigma_3,
                                                                          delta_h_consolidation=self._test_data.delta_h_consolidation,
                                                                          delta_h_reconsolidation=self._test_data.delta_h_reconsolidation,
                                                                          effective_stress_after_reconsolidation=effective_stress_after_reconsolidation)

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""
        params = {"max_time": {"value": self._draw_params.max_time, "borders":
            [self._draw_params.max_time/2, self._draw_params.max_time*10]},
                  "volume_strain_90":  {"value": self._draw_params.volume_strain_90, "borders":
            [self._draw_params.volume_strain_90/2, self._draw_params.volume_strain_90*3]}}
        return params

    def set_draw_params(self, params):
        """Устанавливает переданные параметры отрисовки, считанные с ползунков, на модель"""
        self._draw_params.max_time = params["max_time"]
        self._draw_params.volume_strain_90 = params["volume_strain_90"]
        while self.get_test_results()["velocity"] is None:
            self._test_modeling()
            self._test_data.volume_strain = self._test_data.pore_volume_strain
            self.change_borders(0, len(self._test_data.time))

    def _test_modeling(self):
        """Функция моделирования опыта"""

        random = np.random.choice([2, 3])
        if self._test_params.Cv >= 0.1:
            point_time = 1/60
        else:
            point_time = 1

        if random == 1:
            self._test_data.time, self._test_data.pore_volume_strain = function_consalidation(Cv=self._test_params.Cv,
                                                        volume_strain_90=-self._draw_params.volume_strain_90,
                                                        deviation=0.003,
                                                        Ca=-self._test_params.Ca,
                                                        E=self._test_params.E,
                                                        sigma_3=self._test_params.sigma_3,
                                                        max_time=self._draw_params.max_time,
                                                        point_time=point_time,
                                                        approximate=True)
        elif random == 2:
            self._test_data.time, self._test_data.pore_volume_strain = function_consalidation(Cv=self._test_params.Cv,
                                                        volume_strain_90=-self._draw_params.volume_strain_90,
                                                        deviation=0.003,
                                                        Ca=-self._test_params.Ca,
                                                        E=self._test_params.E,
                                                        sigma_3=self._test_params.sigma_3,
                                                        max_time=self._draw_params.max_time,
                                                                                              point_time=point_time,
                                                                                              approximate=False)
        elif random == 3:
            self._test_data.time, self._test_data.pore_volume_strain = function_consalidation_without_Cv(Cv=self._test_params.Cv,
                                                        volume_strain_90=-self._draw_params.volume_strain_90,
                                                        deviation=0.003,
                                                        Ca=-self._test_params.Ca,
                                                        E=self._test_params.E,
                                                        sigma_3=self._test_params.sigma_3,
                                                        point_time=point_time,
                                                        max_time=self._draw_params.max_time)


        self._test_data.cell_volume_strain = self._test_data.pore_volume_strain + \
                                             create_deviation_curve(self._test_data.time,
                            abs(self._test_data.pore_volume_strain[-1] - self._test_data.pore_volume_strain[0]) * 0.1,
                                                                    val = (1, 0.1), points = np.random.uniform(5, 20))

        self._test_data.time = np.round(self._test_data.time, 3)
        self._test_data.cell_volume_strain = np.round(
            self._test_data.cell_volume_strain * np.pi * (19 ** 2) / (76 - self._test_data.delta_h_reconsolidation) /
            (np.pi * (19 ** 2) / (76 - self._test_data.delta_h_reconsolidation)), 6)
        self._test_data.pore_volume_strain = np.round(
            self._test_data.pore_volume_strain * np.pi * (19 ** 2) / (76 - self._test_data.delta_h_reconsolidation) /
            (np.pi * (19 ** 2) / (76 - self._test_data.delta_h_reconsolidation)), 6)

    @staticmethod
    def dictionary_consalidation(time, pore_volume_strain, cell_volume_strain, velocity=1, sigma_3=150,
                                 delta_h_consolidation=0, delta_h_reconsolidation=0,
                                 effective_stress_after_reconsolidation=0):
        """Формирует словарь консолидации"""
        # Создаем массив набора нагрузки до обжимающего давления консолидации
        sigma_3 -= effective_stress_after_reconsolidation
        load_stage_time = round(sigma_3 / velocity, 2)
        load_stage_time_array = np.arange(0, load_stage_time, 0.25)

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

        vertical_deformation = np.linspace(0, delta_h_consolidation - delta_h_reconsolidation, len(pore_volume_strain))

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
            "CellVolume_mm3": -cell_volume_strain * np.pi * (19 ** 2) * (76-delta_h_reconsolidation),
            "PorePress_kPa": np.random.uniform(-1, 1, len(time)),
            "PoreVolume_mm3": pore_volume_strain * np.pi * (19 ** 2) * (76-delta_h_reconsolidation),
            "VerticalPress_kPa": cell_press + np.random.uniform(-0.1, 0.1, len(time)),
            "Trajectory": np.full(len(time), 'Consolidation')
        }
        #plt.plot((data["Time"][len(load_stage_time_array):] - data["Time"][len(load_stage_time_array)]) ** 0.5,
                 #data["PoreVolume_mm3"][len(load_stage_time_array):]/ (np.pi * (19 ** 2) * (76-delta_h_reconsolidation)))
        plt.plot((data["Time"] - data["Time"][0]) ** 0.5,
                 data["PoreVolume_mm3"])
        plt.show()
        return data


if __name__ == '__main__':
    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"
    param = {'E50': 30495, 'sigma_3': 170, 'sigma_1': 800, 'c': 0.025, 'fi': 45, 'qf': 700, 'K0': 0.5,
             'Cv': 0.013, 'Ca': 0.001, 'poisson': 0.32, 'build_press': 500.0, 'pit_depth': 7.0,
             'dilatancy': 4.95, 'OCR': 1, 'm': 0.61, 'lab_number': '7а-1', 'data_phiz': {'borehole': '7а',
                                                                                         'depth': 19.0,
                                                                                         'name': 'Песок крупный неоднородный',
                                                                                         'ige': '-', 'rs': 2.73,
                                                                                         'r': '-', 'rd': '-', 'n': '-',
                                                                                         'e': '-', 'W': 12.8, 'Sr': '-',
                                                                                         'Wl': '-', 'Wp': '-',
                                                                                         'Ip': '-', 'Il': '-',
                                                                                         'Ir': '-', 'str_index': '-',
                                                                                         'gw_depth': '-',
                                                                                         'build_press': 500.0,
                                                                                         'pit_depth': 7.0, '10': '-',
                                                                                         '5': '-', '2': 6.8, '1': 39.2,
                                                                                         '05': 28.0, '025': 9.2,
                                                                                         '01': 6.1, '005': 10.7,
                                                                                         '001': '-', '0002': '-',
                                                                                         '0000': '-', 'Nop': 7,
                                                                                         'flag': False},
             'test_type': 'Трёхосное сжатие (E)'}

    a = ModelTriaxialConsolidationSoilTest()
    a.set_test_params(param)
    a.plotter()
    plt.show()
