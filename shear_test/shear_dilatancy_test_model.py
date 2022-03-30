"""Модуль математических моделей девиаторного нагружения. Содержит модели:

    ModelShearDilatancy - модель обработчика данных опыта девиаторного нагружения.
    Принцип работы:
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора openfile() находится в кдассе обработки triaxial_statick_loading
        Обработка опыта происходит с помощью метода _test_processing(). Метод change_borders() служит для обработки
        границ массивов, причем обрезанные части все равно записываются в файл прибора
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelShearDilatancySoilTest - модель математического моделирования данных опыта девиаторного нагружения.
    Наследует методы  _test_processing(), get_test_results(), plotter(), а также структуру данных из
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_draw_params() устанавливает позьзовательские значения параметров отрисовки.
        Метод_test_modeling моделируют соотвествующие массивы опытных данных. Вызыванется при передачи пользовательских
         параметров отрисовки.."""

__version__ = 1

import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

from cvi.cvi_writer import save_cvi_shear_dilatancy
from excel_statment.properties_model import ShearProperties
from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, exponent, create_json_file
from typing import Dict, List
from shear_test.shear_dilatancy_functions import curve_shear_dilatancy
from configs.plot_params import plotter_params
from intersect import intersection
from singletons import statment
import copy

class ModelShearDilatancy:
    """Модель обработки девиаторного нагружения

    Логика работы:
        - Данные принимаются в set_test_data(). значально все данные обнуляются методом _reset_data()

        - Производится выбор рабочей кривой объемной деформации. Если кривая Поровой отжатой жидкости писалась, то она
        становится рабочей, иначе кривая отжатой жидкости из камеры

        - Производится определение точки мертвого хода штока функцией cls.find_friction_step(). После чего позиция
        мертвого хода подается в метод change_borders(left, right). Далее метод _cut() обрезает массивы по левой и
        правой границе. Обработка производится для обрезанной части. Объемная деформация аппроксимируется методом
        self._approximate_volume_strain() полиномом 15 степени

        - Обработка опыта производится методом _test_processing. qf и E50 проводится функцией cls.define_E50_qf().
        Eur брабатывается функцией cls.define_Eur(). Коэффициент пуассона и дилатансия определяется функцией
        cls.define_poissons_dilatancy(). Угол дилатансии определяется как наклон в точке пика

        - Метод get_plot_data подготавливает данные для построения. Метод plotter позволяет построить графики с помощью
        matplotlib"""
    def __init__(self):
        self._reset_data()
        # Для передачи на радиобаттон значений ненулевых датчиков
        self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
        self.plotter_params = {"main_line": {"width": 2.5, "color": None, "style": "-"},
                               "scatter_line": {"width": 20, "color": "sandybrown", "style": None},
                               "help_line": {"width": 1.5, "color": "red", "style": "-"},
                               "dotted_line": {"width": 1.5, "color": "red", "style": "--"}}

    def _reset_data(self):
        """Обнуление входных параметров и результатов для обработки нового опыта"""
        self._test_data = AttrDict({"strain": None,
                                    "deviator": None,

                                    "pore_pressure": None,
                                    "reload_points": None,

                                    "volume_strain": None,
                                    "volume_strain_approximate": None,

                                    "pore_volume_strain": None,
                                    "cell_volume_strain": None,

                                    "strain_cut": None,
                                    "pore_pressure_cut": None,
                                    "volume_strain_cut": None,
                                    "deviator_cut": None,
                                    "reload_points_cut": None})

        self._test_params = AttrDict({"sigma": None, "u": None, "K0": 1})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None,
                                            "right": None})

        # Результаты опыта
        self._test_result = AttrDict({"E50": None,
                                      "E": None,
                                      "Eur": None,
                                      "tau_max": None,
                                      "max_pore_pressure": None,
                                      "poissons_ratio": None,
                                      "dilatancy_angle": None})

    def set_test_data(self, test_data):
        """Получение и обработка массивов данных, считанных с файла прибора"""
        self._reset_data()
        if test_data:
            self._test_data.strain = test_data["strain"]
            self._test_data.deviator = test_data["deviator"]
            self._test_data.pore_volume_strain = test_data["pore_volume_strain"]
            self._test_data.cell_volume_strain = test_data["cell_volume_strain"]
            self._test_data.reload_points = test_data["reload_points"]

            self._test_params.sigma = round((test_data["sigma"]), 3)
            self._test_params.u = round((test_data["u"]), 2)

            if np.mean(self._test_data.pore_volume_strain) != 0:
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                self.current_volume_strain = {"current": "cell_volume", "pore_volume": False, "cell_volume": True}

            step = ModelShearDilatancy.find_friction_step(self._test_data.strain, self._test_data.deviator)
            self.change_borders(step, len(self._test_data.strain))
        else:
            print("Этап девиаторноо нагружения не проводился")

    def choise_volume_strain(self, volume_strain):
        """Выбор данных с порового валюмометра или волюмометра с камеры для последующей обработки"""
        if self._test_data.strain is not None:
            if volume_strain == "pore_volume":
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                step = ModelShearDilatancy.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                step = ModelShearDilatancy.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))

    def get_current_volume_strain(self):
        """Метод возвращает действующий волюмометр
        При получении данных проверяется, какие волюмометры были активны. Приоритетный волюмометр выбирается как
         поровый, если в нем нет данных, то выберется камеры"""
        return self.current_volume_strain

    def change_borders(self, left, right):
        """Выделение границ для обрезки значений всего опыта"""
        self._test_cut_position.left = 0
        self._test_cut_position.right = -1
        self._cut()
        self._approximate_volume_strain()
        self._test_processing()

    def get_borders(self):
        """Метод вернет грацицы массивов после обработки"""
        return self._test_cut_position.get_dict()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        dict = copy.deepcopy(self._test_result.get_dict())
        dict["sigma"] = np.round(self._test_params.sigma / 1000, 3)
        return dict

    def get_plot_data(self):
        """Получение данных для построения графиков"""

        if self._test_result.dilatancy_angle:
            dilatancy = {"x": self._test_result.dilatancy_angle[1],
                               "y": self._test_result.dilatancy_angle[2]}
        else:
            dilatancy = None

        return {"strain": self._test_data.strain_cut,
                "deviator": self._test_data.deviator_cut / 1000,
                "strain_cut": self._test_data.strain[0:self._test_cut_position.left] -
                              self._test_data.strain[self._test_cut_position.left],
                "deviator_cut": (self._test_data.deviator[0:self._test_cut_position.left] -
                                self._test_data.deviator[self._test_cut_position.left]) / 1000,
                "volume_strain": self._test_data.volume_strain_cut,
                "volume_strain_approximate": self._test_data.volume_strain_approximate,

                "sigma": self._test_params.sigma/1000,
                "dilatancy": dilatancy}

    def check_none(self):
        if self._test_data.strain is None:
            return False
        else: return True

    def plotter(self, save_path=None):
        """Построитель опыта"""
        from matplotlib import rcParams
        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = '12'
        rcParams['axes.edgecolor'] = 'black'

        figure = plt.figure(figsize = [9.3, 6])
        figure.subplots_adjust(right=0.98, top=0.98, bottom=0.1, wspace=0.25, hspace=0.25, left=0.1)

        ax_deviator = figure.add_subplot(2, 1, 1)
        ax_deviator.grid(axis='both')
        ax_deviator.set_xlabel("Абсолютная деформация $l_1$, мм")
        ax_deviator.set_ylabel("Касательное напряжение τ, МПа")

        ax_volume_strain = figure.add_subplot(2, 1, 2)
        ax_volume_strain.grid(axis='both')
        ax_volume_strain.set_xlabel("Абсолютная деформация $l_1$, мм")
        ax_volume_strain.set_ylabel("Абсолютная \n вертикальная деформация $h_1$, мм")


        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots["strain"] is not None:
            ax_deviator.plot(plots["strain"], plots["deviator"], **plotter_params["static_loading_main_line"])
            ax_deviator.plot(plots["strain_cut"], plots["deviator_cut"], **plotter_params["static_loading_main_line"])
            lim = ax_deviator.get_xlim()
            ax_deviator.set_xlim([lim[0], 7.25])
            # if plots["E50"]:
            #     ax_deviator.plot(*plots["E50"], **plotter_params["static_loading_sandybrown_dotted_line"])
            #     ax_deviator.plot(plots["E"]["x"], plots["E"]["y"], **plotter_params["static_loading_sandybrown_dotted_line"])
            # if plots["Eur"]:
            #     ax_deviator.plot(*plots["Eur"], **plotter_params["static_loading_sandybrown_dotted_line"])

            # ax_deviator.plot([], [], label="$E_{50}$" + ", MПа = " + str(res["E50"]), color="#eeeeee")
            # ax_deviator.plot([], [], label="$E$" + ", MПа = " + str(res["E"][0]), color="#eeeeee")
            ax_deviator.plot([], [], label="$q_{f}$" + ", MПа = " + str(res["tau_max"]), color="#eeeeee")
            # if res["Eur"]:
            #     ax_deviator.plot([], [], label="$E_{ur}$" + ", MПа = " + str(res["Eur"]), color="#eeeeee")


            ax_volume_strain.plot(plots["strain"], plots["volume_strain"], **plotter_params["static_loading_main_line"])
            ax_volume_strain.plot(plots["strain"], plots["volume_strain_approximate"], **plotter_params["static_loading_black_dotted_line"])
            if plots["dilatancy"]:
                ax_volume_strain.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"], **plotter_params["static_loading_black_dotted_line"])


            ax_volume_strain.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                  color="#eeeeee")
            if res["dilatancy_angle"] is not None:
                ax_volume_strain.plot([], [], label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                      color="#eeeeee")

            ax_volume_strain.set_xlim([lim[0], 7.25])

            ax_deviator.legend()
            ax_volume_strain.legend()

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass

    def get_plaxis_dictionary(self) -> dict:
        return ModelShearDilatancy.plaxis_dictionary(self._test_data.strain_cut,
                                                     self._test_data.deviator_cut,
                                                     self._test_data.reload_points if self._test_data.reload_points else [0, 0, 0])

    def _approximate_volume_strain(self):
        """Аппроксимация объемной деформации для удобства обработки"""
        while True:
            try:
                deg = 10
                if deg > len(self._test_data.strain_cut):
                    deg = len(self._test_data.strain_cut)
                self._test_data.volume_strain_approximate = np.polyval(np.polyfit(self._test_data.strain_cut,
                                                                                  self._test_data.volume_strain_cut,
                                                                                  deg), self._test_data.strain_cut)
                break
            except:
                continue

    def _cut(self):
        """Создание новых обрезанных массивов"""
        self._test_data.strain_cut = self._test_data.strain - self._test_data.strain[0]

        self._test_data.volume_strain_cut = self._test_data.volume_strain - self._test_data.volume_strain[0]

        self._test_data.deviator_cut = self._test_data.deviator - self._test_data.deviator[0]

        self._test_data.pore_pressure_cut = self._test_data.pore_pressure - self._test_data.pore_pressure[0]

        if self._test_data.reload_points:
            self._test_data.reload_points_cut = [self._test_data.reload_points[0] - self._test_cut_position.left,
                                                 self._test_data.reload_points[1] - self._test_cut_position.left,
                                                 self._test_data.reload_points[2] - self._test_cut_position.left]

    def _test_processing(self):
        """Обработка опыта девиаторного нагружения"""
        self._test_result.tau_max = np.round(np.max(self._test_data.deviator_cut), 3)
        #
        # self._test_result.Eur = \
        #     ModelShearDilatancy.define_Eur(self._test_data.strain_cut,
        #                           self._test_data.deviator_cut, self._test_data.reload_points_cut)


        self._test_result.poissons_ratio = ModelShearDilatancy.define_poissons(self._test_data.strain_cut,
                                                                               self._test_data.deviator_cut,
                                                                               self._test_data.volume_strain_approximate)

        self._test_result.dilatancy_angle = ModelShearDilatancy.define_dilatancy(self._test_data.strain_cut,
                                                                                 self._test_data.deviator_cut,
                                                                                 self._test_data.volume_strain_approximate)

        # print(f"Dilatancy Test Processing - dilatancy angle: {self._test_result.dilatancy_angle}")

        # self._test_result.E = ModelShearDilatancy.define_E(self._test_data.strain_cut,
        #                           self._test_data.deviator_cut, self._test_params.sigma_3)
        #
        # self._test_result.max_pore_pressure = np.round(np.max(self._test_data.pore_pressure_cut))
        #
        # if self._test_result.max_pore_pressure <= 5:
        #     self._test_result.max_pore_pressure = 0

    def get_processing_parameters(self):
        "Функция возвращает данные по обрезанию краев графиков"
        return {
            "cut": {
                "left": self._test_cut_position.left,
                "right": self._test_cut_position.right
            },
            "sigma": self._test_params.sigma
        }

    def set_processing_parameters(self, params):
        self._test_params.sigma = params["sigma"]
        self.change_borders(params["cut"]["left"], params["cut"]["right"])

    @staticmethod
    def find_friction_step(strain, deviator):
        """Функция поиска начального хода штока"""
        try:
            i_less_then_5, = np.where(deviator<=5)
            strain0 = np.array(strain)
            strain, deviator = np.array(strain), np.array(deviator)

            strain, deviator = make_increas(np.array(strain), np.array(deviator))
            deviator, strain = make_increas(np.array(deviator), np.array(strain))

            if np.max(deviator)>200:
                i, = np.where(deviator>=70)
            else:
                i, = np.where(deviator >= np.max(deviator)*0.3)
            strain, deviator = strain[:i[0]], deviator[:i[0]]

            xxx = np.delete(np.hstack((strain, [strain[-1]])), [0])
            i, = np.where(strain0 >= strain[np.argmax(xxx-strain)+1] - 0.0003)

            if strain0[i[0]] >= 0.2:
                return 0
            else:
                return i[0] + 6
        except:
            return 0

    @staticmethod
    def define_E50_qf(strain, deviator):
        """Определение параметров qf и E50"""
        qf = np.max(deviator)
        # Найдем область E50
        i_07qf, = np.where(deviator > qf * 0.5)
        imax, = np.where(deviator[:i_07qf[0]] > qf / 2)
        imin, = np.where(deviator[:i_07qf[0]] < qf / 2)
        imax = imax[0]
        imin = imin[-1]

        E50 = (qf / 2) / (
            np.interp(qf / 2, np.array([deviator[imin], deviator[imax]]), np.array([strain[imin], strain[imax]])))

        return np.round(E50 / 1000, 1), np.round(qf / 1000, 3)

    @staticmethod
    def define_E(strain, deviator, sigma_3):
        """Определение параметров qf и E50"""
        i_start_E = 0 #i_start_E, = np.where(deviator >= sigma_3)
        i_end_E, = np.where(deviator >= 0.6*sigma_3)

        if len(i_end_E):
            i_end_E = i_end_E[0]
        else:
            i_end_E = len(deviator) - 1

        E = (deviator[i_end_E] - deviator[0])/(strain[i_end_E] - strain[0])
        i_end_for_plot, = np.where(line(E, 0, strain) >= 0.9 * np.max(deviator))

        #A1, B1 = line_approximate(strain[i_start_E:i_end_E], deviator[i_start_E:i_end_E])

        #E = (line(A1, B1, strain[i_start_E]) - line(A1, B1, strain[i_end_E])) / (strain[i_start_E] -
          #                                                                             strain[i_end_E])
        #i_end_for_plot, = np.where(line(A1, B1, strain) >= 0.9 * np.max(deviator))

        #return (round(E / 1000, 2), [strain[i_start_E[0]], strain[i_end_for_plot[0]]],
                #[line(A1, B1, strain[i_start_E[0]]), line(A1, B1, strain[i_end_for_plot[0]])])

        #return (round(E / 1000, 1), [strain[i_start_E], strain[i_end_for_plot[0]]],
                    #[line(A1, B1, strain[i_start_E]), line(A1, B1, strain[i_end_for_plot[0]])])
        return (round(E / 1000, 1), [0, strain[i_end_for_plot[0]]],
                [0, line(E, 0, strain[i_end_for_plot[0]])])

    @staticmethod
    def define_Eur(strain, deviator, reload):
        """Поиск Eur"""
        # Проверяем, есть ли разгрзка и не отрезали ли ее

        if reload is not None:
            if reload[0] > 0 and reload != [0, 0, 0]:
                try:
                    reload[0] -= 1
                    reload[1] -= 1
                    reload[-1] += 1
                    #point1 = reload[1]#np.argmin(deviator[reload[0]: reload[2]]) + reload[0]  # минимум на разгрузке
                    #point2 = reload[0]  # максимум на разгрузке

                    #if (strain[point2] - strain[point1]) < 0.000001:
                        #Eur = None
                    #else:
                        #Eur = round(((deviator[point2] - deviator[point1]) / (strain[point2] - strain[point1])) / 1000, 2)
                    x, y = intersection(strain[reload[0]:reload[1]], deviator[reload[0]:reload[1]],
                                        strain[reload[1]:reload[2]], deviator[reload[1]:reload[2]])
                    if len(x) > 0:
                        Eur = round(((y[0] - deviator[reload[1]]) / (x[0] - strain[reload[1]])) / 1000, 1)
                    else:
                        Eur = None

                except ValueError:
                    Eur = None
            else:
                Eur = None

            return Eur
        else:
            return None

    @staticmethod
    def define_poissons(strain, deviator, volume_strain):
        # Коэффициент Пуассона
        qf = np.max(deviator)
        strain50 = (np.interp(qf / 5, deviator, strain))
        puasson = (np.interp(strain50, strain, volume_strain) / strain50)/(71.4/35)
        return -np.round(puasson, 2)

    @staticmethod
    def define_dilatancy(strain, deviator, volume_strain):
        # Найдкм угол дилатансии
        i_top = np.argmax(deviator)

        if i_top >= len(strain) - 2:
            i_top = len(strain) - 2

        x_area = (strain[i_top + 1] - strain[i_top])

        i_begin = i_top  # np.where(strain >= strain[i_top])
        i_end, = np.where(strain >= strain[i_top] + x_area)
        i_end = i_end[0]

        A1, B1 = line_approximate(strain[i_begin:i_end + 1], volume_strain[i_begin:i_end + 1])
        B1 = volume_strain[i_top] - A1 * strain[i_top]

        delta_EpsV = line(A1, B1, strain[i_end]) - line(A1, B1, strain[i_begin])
        delta_Eps1 = (strain[i_end] - strain[i_begin])

        # dilatancy_value = np.rad2deg(np.arcsin(delta_EpsV / (delta_EpsV + 2 * delta_Eps1)))
        dilatancy_value = np.rad2deg(np.arctan(delta_EpsV / delta_Eps1))

        dilatancy_plot_param = int(len(volume_strain) / 10)

        if dilatancy_plot_param == 0:
            dilatancy_plot_param = 1

        begin = i_top - dilatancy_plot_param
        if begin < 0:
            begin = 0
        end = i_top + dilatancy_plot_param

        if end >= len(volume_strain):
            end = - 1

        dilatancy = (round(dilatancy_value, 2), [strain[begin], strain[end]],
                     [line(A1, B1, strain[begin]), line(A1, B1, strain[end])])

        return dilatancy

    @staticmethod
    def plaxis_dictionary(strain: np.array, deviator: np.array, index_loop: list) -> dict:
        """Функция осущетвляет обработку массивов напряжений и деформаций, прореживает их до заданного числа с
        сохранением ключевых точек - qf, 05qf и, при наличии, всех точек index_loop"""

        def list_generator(x: np.array, point_count: int, do_not_skip_index: list) -> np.array:
            """Прореживает массив x до заданного числа точек point_count с сохранением индексов do_not_skip_indeх"""
            k = int(len(x) / point_count)
            return np.array([val for i, val in enumerate(x) if i % k == 0 or (i in do_not_skip_index)])

        point_count = 100
        index_qf = np.argmax(deviator)

        index_05qf, = np.where(deviator > deviator[index_qf] / 2)
        index_05qf = index_05qf[0]

        if index_loop[-1] <= 0:
            if len(strain) < 100:
                return {"strain": -strain,
                        "deviator": deviator}
            return {"strain": -list_generator(strain, point_count, [index_qf, index_05qf]),
                    "deviator": list_generator(deviator, point_count, [index_qf, index_05qf])}

        else:
            index_loop[1] -= 1  # на деле точка сдвинута, её нужно скорректировать
            before_loop_points_count = int(point_count * index_loop[0] / len(strain))
            after_loop_points_count = point_count - before_loop_points_count

            strain_before_loop = list_generator(strain[:index_loop[0]], before_loop_points_count - 2,
                                                [index_qf, index_05qf])
            deviator_before_loop = list_generator(deviator[:index_loop[0]], before_loop_points_count - 2,
                                                  [index_qf, index_05qf])

            strain_after_loop = list_generator(strain[index_loop[-1]:], after_loop_points_count - 2,
                                               [index_qf - index_loop[-1], index_05qf - index_loop[-1]])
            deviator_after_loop = list_generator(deviator[index_loop[-1]:], after_loop_points_count - 2,
                                                 [index_qf - index_loop[-1], index_05qf - index_loop[-1]])

            strain_loop_unloading = strain[index_loop[0]:index_loop[1]]
            deviator_loop_unloading = deviator[index_loop[0]:index_loop[1]]
            strain_loop_reloading = strain[index_loop[1]:index_loop[-1]]
            deviator_loop_reloading = deviator[index_loop[1]:index_loop[-1]]

            if index_loop[1] - index_loop[0] > 5:
                strain_loop_unloading = list_generator(strain_loop_unloading, 5 - 1, [index_05qf - index_loop[0]])
                deviator_loop_unloading = list_generator(deviator_loop_unloading, 5 - 1, [index_05qf - index_loop[0]])
            if index_loop[-1] - index_loop[1] > 5:
                strain_loop_reloading = list_generator(strain_loop_reloading, 5 - 1, [index_05qf - index_loop[1]])
                deviator_loop_reloading = list_generator(deviator_loop_reloading, 5 - 1, [index_05qf - index_loop[1]])

            return {"strain": -np.hstack(
                (strain_before_loop, strain_loop_unloading, strain_loop_reloading, strain_after_loop)),
                    "deviator": np.hstack(
                        (deviator_before_loop, deviator_loop_unloading, deviator_loop_reloading, deviator_after_loop))}

class ModelShearDilatancySoilTest(ModelShearDilatancy):
    """Модель моделирования девиаторного нагружения
    Наследует обработчик и структуру данных из ModelShearDilatancy

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта"""
    def __init__(self):
        super().__init__()
        self._test_params = AttrDict({"tau_max": None,
                                      "sigma": None,
                                      "dilatancy_angle": None,
                                      "sigma_3": None,
                                      "E50": None,
                                      "c": None,
                                      "K0": None,
                                      "fi": None,
                                      "unloading_borders": None,
                                      "data_phiz": None,
                                      "u": 0,
                                      "delta_h_consolidation": 0,
                                      "velocity": 1})

        self._draw_params = AttrDict({"fail_strain": None,
                                      "residual_strength_param": None,
                                      "residual_strength": None,
                                      "qocr": None,
                                      "poisson": None,
                                      "dilatancy": None,
                                      "volumetric_strain_xc": None})

    def set_test_params(self):
        """Установка основных параметров опыта"""
        self._test_params.E50 = statment[statment.current_test].mechanical_properties.E50

        # print(f"self._test_params.E50 : {self._test_params.E50}")

        # print(f"E50 : {self._test_params.E50}")

        self._test_params.tau_max = statment[statment.current_test].mechanical_properties.tau_max
        self._test_params.sigma = statment[statment.current_test].mechanical_properties.sigma
        self._draw_params.dilatancy = statment[statment.current_test].mechanical_properties.dilatancy_angle
        self._test_params.c = statment[statment.current_test].mechanical_properties.c
        self._test_params.fi = statment[statment.current_test].mechanical_properties.fi
        self._test_params.data_physical = statment[statment.current_test].physical_properties
        self._test_params.velocity = ModelShearDilatancySoilTest.define_velocity(
                 statment[statment.current_test].physical_properties.Ip, statment[statment.current_test].physical_properties.type_ground)
        _test_mode = statment.general_parameters.test_mode

        xc, residual_strength = ModelShearDilatancySoilTest.define_xc_value_residual_strength(
            statment[statment.current_test].physical_properties, statment[statment.current_test].mechanical_properties.sigma,
            statment[statment.current_test].mechanical_properties.tau_max, statment[statment.current_test].mechanical_properties.E50, _test_mode)


        if xc <= 0.14:
            xc *= np.random.uniform(0.8, 1.05)
            residual_strength *= np.random.uniform(0.8, 1)

            xc_sigma = lambda sigma: 1-0.0005 * sigma
            xc *= xc_sigma(self._test_params.sigma)

            residual_strength *= xc_sigma(self._test_params.sigma)


        #self._test_params.E50 = (self._test_params.tau_max/xc)*np.random.uniform(2.0, 5.0)

        self._draw_params.fail_strain = xc
        self._draw_params.residual_strength_param = \
            ModelShearDilatancySoilTest.residual_strength_param_from_xc(xc)

        self._draw_params.residual_strength_param *= np.random.uniform(0.8, 1.2)

        if ShearProperties.shear_type(_test_mode) == ShearProperties.SHEAR_DD:
            residual_strength = residual_strength + (1-residual_strength)*0.8


        self._draw_params.residual_strength = statment[statment.current_test].mechanical_properties.tau_max*residual_strength


        self._draw_params.qocr = 0

        self._draw_params.poisson = statment[statment.current_test].mechanical_properties.poisons_ratio
        self._draw_params.volumetric_strain_xc = (0.002 - self._draw_params.dilatancy * 0.0002) * np.random.uniform(0.9, 1.1)

        count = 0
        self._test_modeling()
        dilatancy_angle = self._test_result.dilatancy_angle[0]
        while abs(dilatancy_angle - self._draw_params.dilatancy) > 1. and count < 20:
            self._test_modeling()
            dilatancy_angle = self._test_result.dilatancy_angle[0]
            count = count + 1


    def set_velocity_delta_h(self, velocity, delta_h_consolidation):
        """Передача в модель скорости нагружения и уменьшения образца на предыдущих этапах
        Скорость отвечает за количество точек на кривой девиатора и за время при сохранении словаря
        Перемещение отвечает за пересчет деформации для корретной обработки опыта после сохранения"""
        self._test_params.velocity = velocity
        self._test_params.delta_h_consolidation = delta_h_consolidation

    def get_dict(self):
        return ModelShearDilatancySoilTest.dictionary_deviator_loading(self._test_data.strain,
                                                                       self._test_data.deviator,
                                                                       self._test_data.pore_volume_strain,
                                                                       self._test_params.sigma,
                                                                       self._test_params.velocity)

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""

        params = {"E50": {"value": self._test_params.E50, "borders": [100, 100000]},
                  "fail_strain": {"value": self._draw_params.fail_strain, "borders": [0.03, 0.15]},
                  "residual_strength_param": {"value": self._draw_params.residual_strength_param, "borders": [0.05, 0.6]},
                  "residual_strength": {"value": self._draw_params.residual_strength,
                                        "borders": [self._test_params.tau_max*0.5, self._test_params.tau_max]},
                  "qocr": {"value": self._draw_params.qocr, "borders": [0, self._test_params.tau_max]},
                  "poisson": {"value": self._draw_params.poisson, "borders": [0.25, 0.45]},
                  "dilatancy": {"value": self._draw_params.dilatancy, "borders": [-20, 25]},
                  "volumetric_strain_xc": {"value": self._draw_params.volumetric_strain_xc, "borders": [0, 0.008]}}
        return params

    def set_draw_params(self, params):
        """Устанавливает переданные параметры отрисовки, считанные с ползунков, на модель"""
        self._test_params.E50 = params["E50"]
        self._draw_params.fail_strain = params["fail_strain"]
        self._draw_params.residual_strength_param = params["residual_strength_param"]
        self._draw_params.residual_strength = params["residual_strength"]
        self._draw_params.qocr = params["qocr"]
        self._draw_params.poisson = params["poisson"]
        self._draw_params.dilatancy = params["dilatancy"]
        self._draw_params.volumetric_strain_xc = params["volumetric_strain_xc"]
        """self._draw_params.dilatancy = np.rad2deg(np.arctan(2 * np.sin(np.deg2rad(params["dilatancy"])) /
                                                           (1 - np.sin(np.deg2rad(params["dilatancy"])))))"""

        self._test_modeling()

    def _test_modeling(self):
        """Функция моделирования опыта"""
        # Время проведения опыта
        # if self._test_params.velocity is None:
        #     print("Ошибка в обработки консолидации")
        # max_time = int((0.15 * (76 - self._test_params.delta_h_consolidation))/self._test_params.velocity)
        # if max_time <= 500:
        #     max_time = 500

        amount_point=int(7.14/0.25)+1

        # dilatancy = np.rad2deg(np.arctan(2 * np.sin(np.deg2rad(self._draw_params.dilatancy)) /
        #                      (1 - np.sin(np.deg2rad(self._draw_params.dilatancy)))))
        dilatancy = self._draw_params.dilatancy
        

        if self._test_params.tau_max >= 150:

            self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
            self._test_data.cell_volume_strain, self._test_data.reload_points, begin = curve_shear_dilatancy(
                self._test_params.tau_max, self._test_params.E50, xc=self._draw_params.fail_strain,
                x2=self._draw_params.residual_strength_param,
                qf2=self._draw_params.residual_strength,
                qocr=self._draw_params.qocr,
                m_given=self._draw_params.poisson,
                amount_points=amount_point*20+1,
                angle_of_dilatacy=dilatancy,
                v_d_xc=-self._draw_params.volumetric_strain_xc)

            # self._test_data.strain = (self._test_data.strain/0.15)*0.1*71.4
            # self._test_data.pore_volume_strain = self._test_data.pore_volume_strain/((((1-2*self._draw_params.poisson)/(self._draw_params.poisson*(71.4/35))))/71.4/0.1*0.15)

        else:
            k = 250/self._test_params.tau_max
            # print('<150', self._draw_params.fail_strain)
            # print(f"_test_params.E50 * k: {self._test_params.E50 * k}")

            self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
            self._test_data.cell_volume_strain, self._test_data.reload_points, begin = curve_shear_dilatancy(
            self._test_params.tau_max * k,
            self._test_params.E50 * k,
            xc=self._draw_params.fail_strain,
            x2=self._draw_params.residual_strength_param,
            qf2=self._draw_params.residual_strength * k,
            qocr=self._draw_params.qocr,
            m_given=self._draw_params.poisson,
            amount_points=amount_point*20+1,
            angle_of_dilatacy=dilatancy,
            v_d_xc=-self._draw_params.volumetric_strain_xc)

            self._test_data.deviator /= k


        _strain = np.array([self._test_data.strain[i] for i in range(0, len(self._test_data.strain), 20)])
        self._test_data.deviator = np.interp(_strain, self._test_data.strain, self._test_data.deviator)
        self._test_data.pore_volume_strain = np.interp(_strain, self._test_data.strain,
                                                       self._test_data.pore_volume_strain)
        self._test_data.cell_volume_strain = np.interp(_strain, self._test_data.strain,
                                                       self._test_data.cell_volume_strain)
        self._test_data.strain = copy.deepcopy(_strain)

        self._test_data.deviator = np.round(self._test_data.deviator, 3)
        self._test_data.strain = np.round(self._test_data.strain, 6)

        i_end = ModelShearDilatancySoilTest.define_final_loading_point(self._test_data.deviator, 0.08 + np.random.uniform(0.01, 0.03))
        self._test_data.strain = self._test_data.strain[:i_end]
        self._test_data.deviator = self._test_data.deviator[:i_end]
        self._test_data.pore_volume_strain = self._test_data.pore_volume_strain[:i_end]
        self._test_data.cell_volume_strain = self._test_data.cell_volume_strain[:i_end]

        self._test_data.pore_pressure = np.random.uniform(-1, 1, len(self._test_data.strain))

        # Действия для того, чтобы полученный массив данных записывался в словарь для последующей обработки

        k = np.max(np.round(self._test_data.deviator[begin:] - self._test_data.deviator[begin], 3)) / self._test_params.tau_max
        self._test_data.deviator = np.round(self._test_data.deviator/k, 3)

        self._test_data.strain = (self._test_data.strain / 0.15) * 0.1 * 71.4
        self._test_data.pore_volume_strain = self._test_data.pore_volume_strain / (((
                    (1 - 2 * self._draw_params.poisson) / (
                        self._draw_params.poisson * (71.4 / 35)))) / 71.4 / 0.1 * 0.15)

        self._test_data.strain = np.round(self._test_data.strain, 6)
        self._test_data.pore_volume_strain = np.round(self._test_data.pore_volume_strain,6)
        self._test_data.cell_volume_strain = np.round(self._test_data.cell_volume_strain,6)

        #i_end, = np.where(self._test_data.strain > self._draw_params.fail_strain + np.random.uniform(0.03, 0.04))
        #if len(i_end):
            #self.change_borders(begin, i_end[0])
        #else:
        # self._test_data.deviator = ModelShearDilatancySoilTest.list_generator(self._test_data.deviator, amount_point)
        # self._test_data.strain = ModelShearDilatancySoilTest.list_generator(self._test_data.strain, amount_point)
        # self._test_data.pore_volume_strain = ModelShearDilatancySoilTest.list_generator(self._test_data.pore_volume_strain , amount_point)

        self._test_data.volume_strain = self._test_data.pore_volume_strain

        self.change_borders(begin, len(self._test_data.volume_strain))

    def get_duration(self):
        return int((self._test_data.strain[-1] * (76 - self._test_params.delta_h_consolidation)) / self._test_params.velocity)

    def get_cvi_data(self):
        """Возвращает параметры отрисовки для установки на ползунки"""
        tau = self._test_data.deviator
        absolute_deformation = self._test_data.strain
        tau_fail = self._test_result.tau_max

        return np.array(tau), np.array(absolute_deformation), np.array(tau_fail)

    def save_cvi_file(self, file_path, file_name):

        data = {
            "laboratory_number": statment[statment.current_test].physical_properties.laboratory_number,
            "borehole": statment[statment.current_test].physical_properties.borehole,
            "ige": statment[statment.current_test].physical_properties.ige,
            "depth": statment[statment.current_test].physical_properties.depth,
            "sample_composition": "Н" if statment[statment.current_test].physical_properties.type_ground in [1, 2, 3, 4,
                                                                                                             5] else "С",
            "b": np.round(np.random.uniform(0.95, 0.98), 2),

            "test_data": {
            }
        }

        tau, absolute_deformation, tau_fail = self.get_cvi_data()

        data["test_data"][1] = {
            "tau": tau,
            "absolute_deformation": absolute_deformation,
            "tau_fail": tau_fail,
            "sigma": np.round(self._test_params.sigma / 1000, 3)
        }

        save_cvi_shear_dilatancy(file_path=os.path.join(file_path, file_name), data=data)


    @staticmethod
    def define_pore_pressure_array(strain, start, pore_pressure, amplitude):
        u = exponent(strain[start:] - strain[start], pore_pressure, np.random.uniform(8, 10)) + amplitude
        y_start = np.linspace(0, amplitude, start)
        y_U = np.hstack((y_start, u))
        y_U += abs(y_U[0])
        y_U[0] = 0.
        #y_U += create_deviation_curve(strain, u/20, points=np.random.uniform(15, 30), low_first_district=1)
        #y_U += create_deviation_curve(strain, u/50, points=np.random.uniform(50, 70), low_first_district=1)
        y_U += np.random.uniform(-3, 3, len(y_U))
        y_U[0] = 0.
        y_U *= ((pore_pressure + amplitude) / np.max(y_U))
        y_U[0] = 0.
        y_U = discrete_array(y_U, 0.5)
        y_U[start] = amplitude
        y_U[start + 1] = amplitude
        y_U[start - 1] = amplitude
        return y_U

    @staticmethod
    def define_k_q(il, e0, sigma3):
        """ Функция определяет насколько выраженный пик на диаграмме
        :param il: показатель текучести
        :param e0: пористость
        :param sigma3: обжимающее напряжение в кПа
        :return: отношение qr к qf
        """
        # Параметры, определяющие распределения
        # Для песков:

        if not e0:
            e0 = np.random.uniform(0.5, 0.7)

        sand_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
        sand_sigma3_max = 1000
        sand_k_e0_min = 0  # значения понижающего коэффициента показателя пористости e0 соответвующее минимальному s3
        sand_k_e0_max = 0.15  # соответствующее макисмальному s3

        sand_e0_red_min = 0.4  # размах приведенной пористости для сигмоиды
        sand_e0_red_max = 0.8
        sand_k_q_min = 0.5  # значения k_q соотв. минимальному e0приведенн
        sand_k_q_max = 0.8  # значения k_q соотв. максимальному e0приведенн

        # Для глин:
        clay_sigma3_min = 100  # размах напряжений (s3) для сигмоиды
        clay_sigma3_max = 1000
        clay_k_il_min = 0  # значения понижающего коэффициента показателя текучести IL соответвующее минимальному s3
        clay_k_il_max = 0.3  # соответствующее макисмальному s3

        clay_il_red_min = 0  # размах приведенного показателя текучести для сигмоиды
        clay_il_red_max = 1
        clay_k_q_min = 0.9  # значения k_q соотв. минимальному ILприведенн
        clay_k_q_max = 0.95  # значения k_q соотв. максимальному ILприведенн

        if not il or il == 0:  # Пески

            # Заивсимость k_e0 от sigma3
            sand_s3_0 = (sand_sigma3_max + sand_sigma3_min) / 2  # x_0
            sand_shape_s3 = sand_sigma3_max - sand_sigma3_min  # delta x

            k_e0_0 = (sand_k_e0_max + sand_k_e0_min) / 2  # y_0
            amplitude_k_e0 = (sand_k_e0_max - sand_k_e0_min) / 2  # amplitude y

            k_e0 = sigmoida(sigma3, amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3)
            e0_red = e0 - k_e0

            # plot_sigmoida(amplitude_k_e0, sand_s3_0, k_e0_0, sand_shape_s3,
            # sand_sigma3_min, sand_sigma3_max, sigma3, k_e0, 'K_e0 от sigma3')

            # Заивсимость k_q от e0приведенной
            e0_red_0 = (sand_e0_red_max + sand_e0_red_min) / 2  # x0
            shape_e0_red = sand_e0_red_max - sand_e0_red_min

            k_q_0 = (sand_k_q_max + sand_k_q_min) / 2  # y0
            amplitude_k_q = (sand_k_q_max - sand_k_q_min) / 2

            k_q = sigmoida(e0_red, amplitude_k_q, e0_red_0, k_q_0, shape_e0_red)

            # plot_sigmoida(amplitude_k_q, e0_red_0, k_q_0, shape_e0_red,
            # sand_e0_red_min, sand_e0_red_max, e0_red, k_q, 'K_q от e0привед')

        else:  # Глины
            # Заивсимость k_il от sigma3
            clay_s3_0 = (clay_sigma3_max + clay_sigma3_min) / 2  # x_0
            clay_shape_s3 = clay_sigma3_max - clay_sigma3_min  # delta x

            k_il_0 = (clay_k_il_max + clay_k_il_min) / 2  # y_0
            amplitude_k_il = (clay_k_il_max - clay_k_il_min) / 2  # amplitude y

            k_il = sigmoida(sigma3, amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3)
            il_red = il - k_il

            # plot_sigmoida(amplitude_k_il, clay_s3_0, k_il_0, clay_shape_s3,
            # clay_sigma3_min, clay_sigma3_max, sigma3, k_il, 'K_IL от sigma3')

            # Заивсимость k_q от IL приведенной
            il_red_0 = (clay_il_red_max + clay_il_red_min) / 2  # x0
            shape_il_red = clay_il_red_max - clay_il_red_min

            k_q_0 = (clay_k_q_max + clay_k_q_min) / 2  # y0
            amplitude_k_q = (clay_k_q_max - clay_k_q_min) / 2

            k_q = sigmoida(il_red, amplitude_k_q, il_red_0, k_q_0, shape_il_red)

            # plot_sigmoida(amplitude_k_q, il_red_0, k_q_0, shape_il_red,
            # clay_il_red_min, clay_il_red_max, il_red, k_q, 'K_IL от sigma3')

        return k_q

    @staticmethod
    def dependence_Eur(E50: float, qf: float, Il: float, initial_unloading_deviator: float) -> float:
        """ Определение модуля Eur
        :param E50: модуль деформации
        :param qf: девиатор разрушения
        :param Il: показатель текучести
        :param initial_unloading_deviator: точка начала разгрузки
        :return: Eur"""

        if not Il:
            Il = np.random.uniform(-0.1, 0.1)

        def dependence_Eur_on_Il(Il):
            """Находит зависимость коэффициента k (Eur = Esec*k) в зависимости от Il"""
            return sigmoida(Il, 1.5, 0.5, 3.5, 1.2)

        def exp_strain(deviator, E50, qf):
            """Экспоненциальная функция деформации от девиатора"""
            return np.log(-deviator / qf + 1) / (np.log(0.5) / ((qf / 2) / E50))

        if initial_unloading_deviator >= qf:
            raise ValueError("Точка начала разгрузки выше девиатора разрушения")

        # Секущий модуль в точке разгрузки
        Esec = initial_unloading_deviator / exp_strain(initial_unloading_deviator, E50, qf)

        return Esec * dependence_Eur_on_Il(Il)

    @staticmethod
    def xc_from_qf_e_if_is(sigma_3, type_ground, e, Ip, Il, Ir, test_mode):
        """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50, если по параметрам материала
        пик есть, если нет, возвращает xc = 0.15. Обжимающее напряжение должно быть в кПа"""
        sigma3mor = sigma_3 / 1000  # так как дается в КПа, а необходимо в МПа
        if (ShearProperties.shear_type(test_mode) == ShearProperties.SHEAR_DD) and type_ground > 5:
            # if sigma_3 <= 0.1:
            #     return 0
            # else:
            def scheme(sigma3mor):
                if sigma3mor <= 0.1:
                    kr_fgs = np.random.choice([0, 1], p=[0.7, 0.3])
                else:
                    kr_fgs = 1
                return kr_fgs

            if Il <= 0.25:
                kr_fgs = scheme(sigma3mor)
                return kr_fgs
            elif Il > 0.25 and Il <= 0.3:
                a = scheme(sigma3mor)
                kr_fgs = np.random.choice([a, 0], p=[0.3, 0.7])
                return kr_fgs
            elif Il > 0.3:
                kr_fgs = 0
                return kr_fgs



        none_to_zero = lambda x: 0 if not x else x
        Ip = Ip if Ip else 0
        Il = Il if Il else 0.5
        e0 = e if e else 0.65
        Ir = Ir if Ir else 0

        if Il > 0.35 and Ir >= 50:
            return 0

        if e0 == 0:
            dens_sand = 2  # средней плотности
        elif type_ground <= 3:
            if e0 <= 0.55:
                dens_sand = 1  # плотный
            elif e0 <= 0.7:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.7
                dens_sand = 3  # рыхлый
        elif type_ground == 4:
            if e0 <= 0.6:
                dens_sand = 1  # плотный
            elif e0 <= 0.75:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.75
                dens_sand = 3  # рыхлый
        elif type_ground == 5:
            if e0 <= 0.6:
                dens_sand = 1  # плотный
            elif e0 <= 0.8:
                dens_sand = 2  # средней плотности
            else:  # e0 > 0.8
                dens_sand = 3  # рыхлый
        else:
            dens_sand = 0


        # if type_ground == 3 or type_ground == 4:  # Процентное содержание гранул размером 10 и 5 мм больше половины
        #     kr_fgs = 1
        if none_to_zero(Ip) == 0:  # число пластичности. Пески (и торф?)
            if dens_sand == 1 or type_ground == 1:  # любой плотный или гравелистый песок
                kr_fgs = 1
            elif type_ground == 2:  # крупный песок
                if sigma3mor <= 0.1:
                    kr_fgs = round(np.random.uniform(0, 1))
                else:
                    kr_fgs = 1
            elif type_ground == 3:  # песок средней групности
                if sigma3mor <= 0.15 and dens_sand == 3:  # песок средней крупности рыхлый
                    kr_fgs = 0
                elif sigma3mor <= 0.15 and dens_sand == 2:  # песок средней крупности средней плотности
                    kr_fgs = round(np.random.uniform(0, 1))
                else:  # песок средней групности и sigma3>0.15
                    kr_fgs = 1
            elif type_ground == 4:  # мелкий песок
                if sigma3mor < 0.1 and dens_sand == 3:  # мелкий песок рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (sigma3mor <= 0.15 and dens_sand == 2):
                    kr_fgs = round(np.random.uniform(0, 1))  # мелкий песок рыхлый s3<=0.2 и средней плотности s3<=0.15
                else:  # мелкий песок рыхлый s3>=0.2 и средней плотности s3>=0.15 (плотный закрыт раньше)
                    kr_fgs = 1
            elif type_ground == 5:  # песок пылеватый
                if sigma3mor < 0.1 and dens_sand == 3:  # песок пылеватый рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (
                        sigma3mor <= 0.1 and dens_sand == 2):  # песок пылева-
                    kr_fgs = round(
                        np.random.uniform(0, 1))  # тый рыхлый 0.1<=s3<=0.2 и пылеватый средней плотности s3<=0.1
                else:  # песок пылеватый рыхлый s3>0.2 и пылеватый средней плотности s3>0.1 (плотный закрыт раньше)
                    kr_fgs = 1
            elif type_ground == 9:  # Торф
                kr_fgs = 0
            else:
                kr_fgs = 0

        elif Ip <= 7:  # число пластичности. Супесь

            if Il > 1:  # показатель текучести. больше 1 - текучий
                kr_fgs = 0
            elif 0 < Il <= 1:  # показатель текучести. от 0 до 1 - пластичный (для супеси)
                kr_fgs = round(np.random.uniform(0, 1))
            else:  # <=0 твердый
                kr_fgs = 1

        elif Ip > 7:  # суглинок и глина
            if Il > 0.5:  # показатель текучести.от 0.5 мягко- и текучепласт., текучий (для суглинков и глины)
                kr_fgs = 0
            elif 0.25 < Il <= 0.5:  # от 0.25 до 0.5 тугопластичный (для суглинков и глины)
                kr_fgs = round(np.random.uniform(0, 1))
            else:  # меньше 0.25 твердый и полутвердый (для суглинков и глины)
                kr_fgs = 1
        else:
            kr_fgs = 0
        return kr_fgs

    @staticmethod
    def define_xc_qf_E(qf, E50):
        """Функция определяет координату пика в зависимости от максимального девиатора и модуля"""

        try:
            k = E50 / qf
        except (ValueError, ZeroDivisionError):
            return 0.15

        # Если все норм, то находим Xc
        xc = 1.37 / (k ** 0.8)

        # Проверим значение
        if xc >= 0.15:
            xc = 0.15

        elif xc <= qf / E50:
            xc = qf / E50

        return xc

    @staticmethod
    def residual_strength_param_from_xc(xc):
        """Функция находит параметр падения остатичной прочности в зависимости от пика"""

        param = 0.33 - 1.9 * (0.15 - xc)

        return param

    @staticmethod
    def define_xc_value_residual_strength(data_phiz, sigma_3, qf, E, test_mode):

        xc = ModelShearDilatancySoilTest.xc_from_qf_e_if_is(sigma_3, data_phiz.type_ground, data_phiz.e,
                                                           data_phiz.Ip, data_phiz.Il, data_phiz.Ir, test_mode)

        if sigma_3 <= 200:
            k = 1
        elif sigma_3 >= 200 and sigma_3 < 500:
            k = 0.002 * sigma_3 + 0.6
        else:
            k = 1.6

        if xc:
            xc = ModelShearDilatancySoilTest.define_xc_qf_E(qf, E)
            if ShearProperties.shear_type(test_mode) == ShearProperties.SHEAR_DD:
                xc = xc*k

        else:
            xc = 0.15

        if xc != 0.15:
            residual_strength = ModelShearDilatancySoilTest.define_k_q(data_phiz.Il, data_phiz.e, sigma_3)

        else:
            residual_strength = 0.95

        if xc <= 0.03:
            xc = np.random.uniform(0.025, 0.03)
            if ShearProperties.shear_type(test_mode) == ShearProperties.SHEAR_DD:
                xc = xc*k

        return xc, residual_strength

    @staticmethod
    def define_dilatancy_from_xc_qres(xc, qres):
        """Определяет угол дилатансии"""
        k_xc = sigmoida(mirrow_element(xc, 0.075), 5, 0.075, 5, 0.15)
        k_qres = sigmoida(mirrow_element(qres, 0.75), 5, 0.75, 5, 0.5)
        angle_of_dilatancy = k_xc + k_qres

        return round(angle_of_dilatancy, 1)

    @staticmethod
    def define_OCR_from_xc(xc):
        return 5.5 - 30 * xc

    @staticmethod
    def dictionary_deviator_loading(strain, tau, vertical_strain, sigma, velocity):
        """Формирует словарь девиаторного нагружения"""

        time_end = (7.14 / velocity) * 60
        time = np.linspace(0, time_end, len(strain)) + 0.004
        time_initial = np.hstack((np.full(5, 0.004), np.repeat(np.array([60 + np.random.uniform(0.3, 0.6),
                                                                         1860 + np.random.uniform(0.3, 0.6)]), 2)))
        time = np.hstack((time_initial, time[1:] + time_initial[-1]))
        time= np.hstack((time, np.array(time[-1]), np.array(time[-1])+ np.random.uniform(100, 120)))

        action = [''] * 2 + ['Start'] * 2 + ['LoadStage'] * 2 + \
                 ['Wait'] * 2 + ['WaitLimit'] * (len(time) - 10) + ['Unload'] * 2
        action_changed = ['', 'True'] * 4 + [''] * (len(time) - 8)
        action_changed[-3] = "True"

        vertical_press = np.hstack((np.full(5, 0),
                                    np.full(len(time) - 7,
                                            sigma + np.random.uniform(-2, 0.1, len(time)-7))))
        vertical_press = np.hstack((vertical_press, np.array([vertical_press[-1], np.random.uniform(1, 2)])))
        vertical_deformation = np.hstack((np.full(5, 0),
                                          np.repeat(np.random.uniform(0.3, 0.7, 2), 2), -vertical_strain[1:]))
        vertical_deformation = np.hstack((vertical_deformation, np.array([vertical_deformation[-1], np.random.uniform(-0.5, -0.1)])))

        shear_deformation = np.hstack((np.full(5, 0),
                                       np.repeat(np.random.uniform(0.1, 0.15, 2), 2), strain[1:]))
        shear_deformation = np.hstack((shear_deformation, np.array([shear_deformation[-1], np.random.uniform(0.1, 0.3)])))
        shear_press = np.hstack((np.full(5, 0),
                                 np.repeat(np.random.uniform(3, 6, 2), 2), tau[1:]))
        shear_press = np.hstack((shear_press, np.array([shear_press[-1],
                                                                   np.random.uniform(-50, -40)])))
        stage = ['Пуск'] * 3 + ['Вертикальное нагружение'] * 4 + ['Срез'] * (len(time) - 7)

        data = {
            "Time": np.round(time,3),
            "Action": action,
            "Action_Changed": action_changed,
            "SampleHeight_mm": np.round(np.full(len(time), 35)),
            "SampleDiameter_mm": np.round(np.full(len(time), 71.4),1),
            "VerticalPress_kPa": np.round(vertical_press, 4),
            "VerticalDeformation_mm": np.round(vertical_deformation,7),
            "ShearDeformation_mm": np.round(shear_deformation,8),
            "ShearPress_kPa": np.round(shear_press, 6),
            "Stage": stage
        }

        return data

    @staticmethod
    def define_velocity(Ip: float, type_ground: int) -> float:
        if type_ground == 1 or type_ground == 2 \
                or type_ground == 3 or type_ground == 4 \
                or type_ground == 5 or type_ground == 6:
            return 0.5
        elif type_ground == 7:
            if Ip is None:
                Ip = np.random.uniform(12, 17)
            if Ip <= 12:
                return 0.1
            else:
                return 0.005
        elif type_ground == 8:
            if Ip is None:
                Ip = np.random.uniform(12, 17)
            if Ip <= 30:
                return 0.02
            else:
                return 0.01
        elif type_ground == 9:
            return 0.01

    @staticmethod
    def define_unloading_points(Il, type_ground, sigma_mean: float, sigma_1: float) -> float:
        """ Рассчет начала разгрузки в зависимости от грансостава и среднеобжимающего давления
            :param physical_data: словарь с физическими параметрами
            :param sigma_1: эффективное значение sigma_3c
            :return: девиатор начала разгрузки"""

        def type_from_Il_loam(Il):
            if Il:
                if Il <= 0.5:
                    return [0.1, 0.2]
                elif Il > 0.5:
                    return [0.08, 0.15]
            else:
                return [0, 0]

        def type_from_Il_clay(Il):
            if Il:
                if Il <= 0.5:
                    return [0.06, 0.15]
                elif Il > 0.5:
                    return [0.05, 0.1]
            else:
                return [0, 0]

        # Функция рассчета начала разгрузки по ГОСТ 12248-2020
        deviator_start_unloading = lambda step_1, step_2: sigma_mean * (step_1 + step_2)

        # Рассчет начала разгрузки в зависимости от грансостава
        dependence_deviator_start_unloading_on_type_ground = {
            1: deviator_start_unloading(0.3, 0.3),
            2: deviator_start_unloading(0.3, 0.3),
            3: deviator_start_unloading(0.3, 0.3),
            4: deviator_start_unloading(0.3, 0.3),
            5: deviator_start_unloading(0.3, 0.3),
            6: deviator_start_unloading(0.1, 0.2),
            7: deviator_start_unloading(*type_from_Il_loam(Il)),
            8: deviator_start_unloading(*type_from_Il_clay(Il)),
            9: deviator_start_unloading(0.05, 0.1)
        }

        return (dependence_deviator_start_unloading_on_type_ground[type_ground], 10)

    @staticmethod
    def define_final_loading_point(deviator: List, persent: float) -> int:
        """ Рассчет начала разгрузки в зависимости от грансостава и среднеобжимающего давления
            :param deviator: массив девиаторного нагружения
            :param persent: процент падения девиатора (в сотых)
            :return: индекс точки падения девиатора на заданный процент"""

        i_max = np.argmax(deviator)

        i, = np.where(deviator[i_max:] <= (1 - persent) * np.max(deviator))

        return i[0] + i_max if len(i) != 0 else len(deviator)

    @staticmethod
    def list_generator(x: np.array, point_count: int) -> np.array:
        """Прореживает массив x до заданного числа точек point_count с сохранением индексов do_not_skip_indeх"""
        k = int(len(x) / point_count)
        return np.array([val for i, val in enumerate(x) if i % k == 0])


    def save_log_file(self, file_path):
        """Метод генерирует логфайл прибора"""
        deviator_loading_dict = self.get_dict()

        main_dict = deviator_loading_dict

        ModelShearDilatancySoilTest.text_file(file_path, main_dict)
        create_json_file('/'.join(os.path.split(file_path)[:-1]) + "/processing_parameters.json",
                         self.get_processing_parameters())



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
                "VerticalPress_kPa" + '\t' + "VerticalDeformation_mm" + '\t' + "ShearDeformation_mm" + '\t' +
                "ShearPress_kPa" + '\t' + "Stage"+ '\n')
            for i in range(len(data["Time"])):
                file.write(make_string(data, i))

if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"

    """a = ModelShearDilatancy()
    from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad
    a.set_test_data(ModelTriaxialStaticLoad.open_geotek_log(file)["shear_dilatancy"])
    a.plotter()
    plt.show()"""
    a = ModelShearDilatancySoilTest()
    statment.load(r"C:\Users\Пользователь\Documents\Срез дилатансия.pickle")
    statment.current_test = "89-4"
    a.set_test_params()
    a.plotter()
    plt.show()