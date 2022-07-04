"""Модуль математических моделей девиаторного нагружения. Содержит модели:

    ModelTriaxialDeviatorLoading - модель обработчика данных опыта девиаторного нагружения.
    Принцип работы:
        Данные подаются в модель методом set_test_data(test_data) с определенными ключами. Функция открытия файла
        прибора openfile() находится в кдассе обработки triaxial_statick_loading
        Обработка опыта происходит с помощью метода _test_processing(). Метод change_borders() служит для обработки
        границ массивов, причем обрезанные части все равно записываются в файл прибора
        Метод plotter() позволяет вывести графики обработанного опыта
        Результаты получаются методом get_test_results()

    ModelTriaxialDeviatorLoadingSoilTest - модель математического моделирования данных опыта девиаторного нагружения.
    Наследует методы  _test_processing(), get_test_results(), plotter(), а также структуру данных из
    Принцип работы:
        Параметры опыта подаются в модель с помощью метода set_test_params().
        Метод get_params() Возвращает основные параметры отрисовки для последующей передачи на слайдеры
        Метод set_draw_params() устанавливает позьзовательские значения параметров отрисовки.
        Метод_test_modeling моделируют соотвествующие массивы опытных данных. Вызыванется при передачи пользовательских
         параметров отрисовки.."""

__version__ = 1

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

from general.general_functions import sigmoida, make_increas, line_approximate, line, define_poissons_ratio, mirrow_element, \
    define_dilatancy, define_type_ground, AttrDict, find_line_area, interpolated_intercept, Point, point_to_xy, \
    array_discreate_noise, create_stabil_exponent, discrete_array, create_deviation_curve, exponent
from typing import Dict, List, Tuple
from static_loading.deviator_loading_functions import curve
from configs.plot_params import plotter_params
from intersect import intersection
from singletons import statment
import copy

from dataclasses import dataclass

@dataclass
class test_params:
    qf = None,
    sigma_3 = None
    E50 = None
    c = None
    K0 = None
    fi = None
    unloading_borders = None
    data_phiz = None
    u = 0
    delta_h_consolidation = 0
    velocity = 1

class ModelTriaxialDeviatorLoading:
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
                                    "reload_points_cut": None,
                                    "E_processing_points_index": None})

        self._test_params = AttrDict({"sigma_3": None, "u": None, "K0": 1})

        # Положение для выделения опыта из общего массива
        self._test_cut_position = AttrDict({"left": None,
                                            "right": None})

        # Результаты опыта
        self._test_result = AttrDict({"E50": None,
                                      "E": None,
                                      "Eur": None,
                                      "qf": None,
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

            self._test_params.sigma_3 = round((test_data["sigma_3"]), 3)
            self._test_params.u = round((test_data["u"]), 2)

            if np.mean(self._test_data.pore_volume_strain) != 0:
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                self.current_volume_strain = {"current": "pore_volume", "pore_volume": True, "cell_volume": True}
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                self.current_volume_strain = {"current": "cell_volume", "pore_volume": False, "cell_volume": True}

            step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
            self.change_borders(step, len(self._test_data.strain))
        else:
            print("Этап девиаторноо нагружения не проводился")

    def choise_volume_strain(self, volume_strain):
        """Выбор данных с порового валюмометра или волюмометра с камеры для последующей обработки"""
        if self._test_data.strain is not None:
            if volume_strain == "pore_volume":
                self._test_data.volume_strain = self._test_data.pore_volume_strain
                step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))
            else:
                self._test_data.volume_strain = self._test_data.cell_volume_strain
                step = ModelTriaxialDeviatorLoading.find_friction_step(self._test_data.strain, self._test_data.deviator)
                self.change_borders(step, len(self._test_data.strain))

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
        self._approximate_volume_strain()


        q_c = self._test_params.sigma_3 * ((1 / self._test_params.K0) - 1)

        q_c2 = self._test_params.sigma_3 * ((1.6 / self._test_params.K0) - 1)

        if self._test_params.K0 == 1:
            i_start_E = 0
        else:
            i_start_E, = np.where(self._test_data.deviator_cut >= q_c)
            if len(i_start_E):
                i_start_E = i_start_E[0]
            else:
                i_start_E = 0

        if q_c == 0:
            i_end_E, = np.where(self._test_data.deviator_cut >= np.max(self._test_data.deviator_cut)*np.random.uniform(0.2, 0.3))
            if len(i_end_E):
                i_end_E = i_end_E[0]
            else:
                i_end_E = len(self._test_data.deviator_cut) - 1
        else:
            i_end_E, = np.where(self._test_data.deviator_cut >= q_c2)
            if len(i_end_E):
                i_end_E = i_end_E[0]
            else:
                i_end_E = len(self._test_data.deviator_cut) - 1

        if i_end_E <= i_start_E:
            i_end_E = i_start_E + 1

        self._test_params.E_processing_points_index = [i_start_E, i_end_E]

        self._test_result.E50, self._test_result.qf = \
            ModelTriaxialDeviatorLoading.define_E50_qf(self._test_data.strain_cut, self._test_data.deviator_cut)

        self._test_result.E = ModelTriaxialDeviatorLoading.define_E(self._test_data.strain_cut,
                                                                    self._test_data.deviator_cut,
                                                                    self._test_params.E_processing_points_index)

        if self._test_result.E[0] <= self._test_result.E50/1000:
            i_start_E = 0
            i_end_E, = np.where(self._test_data.deviator_cut >= np.max(self._test_data.deviator_cut) * np.random.uniform(0.25, 0.35))
            i_end_E = i_end_E[0]
            self._test_params.E_processing_points_index = [i_start_E, i_end_E]
        else:
            pass#print(self._test_params.data_physical.laboratory_number, self._test_params.sigma_3, q_c, q_c2)

        self._test_processing()

    def get_borders(self):
        """Метод вернет грацицы массивов после обработки"""
        return self._test_cut_position.get_dict()

    def get_test_results(self):
        """Получение результатов обработки опыта"""
        dict = copy.deepcopy(self._test_result.get_dict())
        dict["sigma_3"] = np.round((self._test_params.sigma_3 - float(dict["max_pore_pressure"])) / 1000, 3)
        dict["q_res"] = np.round((self._test_data.deviator_cut[-1]) / 1000, 3)

        dict["K_E50"] = np.round(self._test_result.E[0]/self._test_result.E50, 2)
        dict["K_Eur"] = np.round(self._test_result.Eur/self._test_result.E[0], 2) if self._test_result.Eur else None

        return dict

    def get_plot_data(self):
        """Получение данных для построения графиков"""
        if self._test_result.E50:
            E50 = point_to_xy(Point(x=0, y=0), Point(
                    x=0.9 * self._test_result.qf * 1000/ (self._test_result.E50*1000),
                    y=0.9 * self._test_result.qf))

            E = {"x": self._test_result.E[1],
                 "y": np.array(self._test_result.E[2]) / 1000}

        else:
            E50 = None
            E = None

        if self._test_result.Eur:

            b = self._test_data.deviator_cut[self._test_data.reload_points_cut[1]] - \
                self._test_result.Eur*1000*self._test_data.strain_cut[self._test_data.reload_points_cut[1]]

            line_ = line(self._test_result.Eur*1000, b, self._test_data.strain_cut)
            _begin, = np.where(line_ >= self._test_data.deviator_cut[self._test_data.reload_points_cut[1]])
            _end, = np.where(line_ >= self._test_data.deviator_cut[self._test_data.reload_points_cut[2]])

            Eur = point_to_xy(Point(x=self._test_data.strain_cut[_begin[0]],
                                    y=line_[_begin[0]] / 1000),
                              Point(x=self._test_data.strain_cut[_end[0]],
                                    y=line_[_end[0]] / 1000))

            _begin, = np.where(self._test_data.deviator_cut >=
                               self._test_data.deviator_cut[self._test_data.reload_points_cut[1] - 5])
            _end, = np.where(self._test_data.deviator_cut >=
                               self._test_data.deviator_cut[self._test_data.reload_points_cut[2] + 5])

            strain_Eur = self._test_data.strain_cut[:_end[0]]
            deviator_Eur = self._test_data.deviator_cut[:_end[0]]/1000

        else:
            Eur = None
            strain_Eur = None
            deviator_Eur = None

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
                "E50": E50,
                "E": E,
                "E_point_1": (self._test_data.strain_cut[self._test_params.E_processing_points_index[0]],
                              (self._test_data.deviator_cut[self._test_params.E_processing_points_index[0]] + self._test_params.sigma_3)/1000),
                "E_point_2": (self._test_data.strain_cut[self._test_params.E_processing_points_index[1]],
                              (self._test_data.deviator_cut[self._test_params.E_processing_points_index[1]] + self._test_params.sigma_3) / 1000),
                "Eur": Eur,
                "strain_Eur": strain_Eur,
                "deviator_Eur": deviator_Eur,
                "sigma_3": self._test_params.sigma_3/1000,
                "dilatancy": dilatancy,}

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
        ax_deviator.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_deviator.set_ylabel("Девиатор q, кПА")

        ax_volume_strain = figure.add_subplot(2, 1, 2)
        ax_volume_strain.grid(axis='both')
        ax_volume_strain.set_xlabel("Относительная деформация $ε_1$, д.е.")
        ax_volume_strain.set_ylabel("Объемная деформация $ε_v$, д.е.")

        plots = self.get_plot_data()
        res = self.get_test_results()

        if plots["strain"] is not None:
            ax_deviator.plot(plots["strain"], plots["deviator"], **plotter_params["static_loading_main_line"])
            ax_deviator.plot(plots["strain_cut"], plots["deviator_cut"], **plotter_params["static_loading_main_line"])
            if plots["E50"]:
                ax_deviator.plot(*plots["E50"], **plotter_params["static_loading_sandybrown_dotted_line"])
                ax_deviator.plot(plots["E"]["x"], plots["E"]["y"], **plotter_params["static_loading_sandybrown_dotted_line"])
            if plots["Eur"]:
                ax_deviator.plot(*plots["Eur"], **plotter_params["static_loading_sandybrown_dotted_line"])

            ax_deviator.plot([], [], label="$E_{50}$" + ", MПа = " + str(res["E50"]), color="#eeeeee")
            ax_deviator.plot([], [], label="$E$" + ", MПа = " + str(res["E"][0]), color="#eeeeee")
            ax_deviator.plot([], [], label="$q_{f}$" + ", MПа = " + str(res["qf"]), color="#eeeeee")
            if res["Eur"]:
                ax_deviator.plot([], [], label="$E_{ur}$" + ", MПа = " + str(res["Eur"]), color="#eeeeee")


            ax_volume_strain.plot(plots["strain"], plots["volume_strain"], **plotter_params["static_loading_main_line"])
            ax_volume_strain.plot(plots["strain"], plots["volume_strain_approximate"], **plotter_params["static_loading_black_dotted_line"])
            if plots["dilatancy"]:
                ax_volume_strain.plot(plots["dilatancy"]["x"], plots["dilatancy"]["y"], **plotter_params["static_loading_black_dotted_line"])


            ax_volume_strain.plot([], [], label="Poissons ratio" + ", д.е. = " + str(res["poissons_ratio"]),
                                  color="#eeeeee")
            if res["dilatancy_angle"] is not None:
                ax_volume_strain.plot([], [], label="Dilatancy angle" + ", град. = " + str(res["dilatancy_angle"][0]),
                                      color="#eeeeee")

            ax_volume_strain.set_xlim(ax_deviator.get_xlim())

            ax_deviator.legend()
            ax_volume_strain.legend()

        if save_path:
            try:
                plt.savefig(save_path, format="png")
            except:
                pass

    def get_plaxis_dictionary(self) -> dict:
        return ModelTriaxialDeviatorLoading.plaxis_dictionary(self._test_data.strain_cut,
                                                              self._test_data.deviator_cut,
                                                              self._test_data.reload_points if self._test_data.reload_points else [0, 0, 0])

    def _approximate_volume_strain(self):
        """Аппроксимация объемной деформации для удобства обработки"""
        while True:
            try:
                self._test_data.volume_strain_approximate = np.polyval(
                    np.polyfit(self._test_data.strain_cut,
                               self._test_data.volume_strain_cut, 15),
                    self._test_data.strain_cut)
                break
            except:
                continue

    def _cut(self):
        """Создание новых обрезанных массивов"""
        self._test_data.strain_cut = self._test_data.strain[
                                     self._test_cut_position.left:self._test_cut_position.right] - \
                                     self._test_data.strain[self._test_cut_position.left]
        self._test_data.volume_strain_cut = self._test_data.volume_strain[
                                            self._test_cut_position.left:self._test_cut_position.right] - \
                                            self._test_data.volume_strain[self._test_cut_position.left]
        self._test_data.deviator_cut = self._test_data.deviator[
                                       self._test_cut_position.left:self._test_cut_position.right] - \
                                       self._test_data.deviator[self._test_cut_position.left]

        self._test_data.pore_pressure_cut = self._test_data.pore_pressure[
                                       self._test_cut_position.left:self._test_cut_position.right] - \
                                       self._test_data.pore_pressure[self._test_cut_position.left]
        if self._test_data.reload_points:
            self._test_data.reload_points_cut = [self._test_data.reload_points[0] - self._test_cut_position.left,
                                                 self._test_data.reload_points[1] - self._test_cut_position.left,
                                                 self._test_data.reload_points[2] - self._test_cut_position.left]

    def _test_processing(self):
        """Обработка опыта девиаторного нагружения"""
        self._test_result.E50, self._test_result.qf = \
            ModelTriaxialDeviatorLoading.define_E50_qf(self._test_data.strain_cut, self._test_data.deviator_cut)

        self._test_result.Eur = \
            ModelTriaxialDeviatorLoading.define_Eur(self._test_data.strain_cut,
                                  self._test_data.deviator_cut, self._test_data.reload_points_cut)
        if self._test_data.volume_strain_approximate is not None:
            self._test_result.poissons_ratio = ModelTriaxialDeviatorLoading.define_poissons(self._test_data.strain_cut,
                                      self._test_data.deviator_cut,
                                        self._test_data.volume_strain_approximate)

            self._test_result.dilatancy_angle = ModelTriaxialDeviatorLoading.define_dilatancy(self._test_data.strain_cut,
                                      self._test_data.deviator_cut,
                                        self._test_data.volume_strain_approximate)
        else:
            self._test_result.poissons_ratio = 0.3
            self._test_result.dilatancy_angle =[12, 3, 10]

        self._test_result.E = ModelTriaxialDeviatorLoading.define_E(self._test_data.strain_cut,
                                  self._test_data.deviator_cut, self._test_params.E_processing_points_index)

        self._test_result.max_pore_pressure = np.round(np.max(self._test_data.pore_pressure_cut), 1)

        if self._test_result.max_pore_pressure <= 1.3:
            self._test_result.max_pore_pressure = 0

        if statment.general_parameters.test_mode != 'Трёхосное сжатие КН':
            self._test_result.max_pore_pressure = 0



        self._test_result.Eps50 = (self._test_result.qf*0.5) / self._test_result.E50
        self._test_result.qf50 = self._test_result.qf*0.5 / 1000

        self._test_result.E50 = np.round(self._test_result.E50 / 1000, 1)
        self._test_result.qf = np.round(self._test_result.qf / 1000, 3)

    def define_click_point(self, x, y):
        a = (np.max(self._test_data.strain_cut) / 20) ** 2
        b = (np.max(self._test_data.deviator_cut/1000) / 20) ** 2

        point_1 = Point(x=self._test_data.strain_cut[self._test_params.E_processing_points_index[0]],
                        y=(self._test_data.deviator_cut[self._test_params.E_processing_points_index[0]] + self._test_params.sigma_3)/1000)

        point_2 = Point(x=self._test_data.strain_cut[self._test_params.E_processing_points_index[1]],
                        y=(self._test_data.deviator_cut[self._test_params.E_processing_points_index[1]] + self._test_params.sigma_3)/1000)

        if (((x - point_1.x) ** 2) / a) + (((y - point_1.y) ** 2) / b) <= 1:
            return 1
        elif (((x - point_2.x) ** 2) / a) + (((y - point_2.y) ** 2) / b) <= 1:
            return 2
        else:
            return None

    def moove_catch_point(self, x, y, point_identificator):
        """Метод обрабатывает значения полученной точки и запускает перерасчет"""
        y = y*1000 - self._test_params.sigma_3
        i, = np.where(self._test_data.deviator_cut >= y)

        if len(i):
            index = self._test_params.E_processing_points_index

            self._test_params.E_processing_points_index[point_identificator - 1] = i[0]

            if self._test_params.E_processing_points_index[0] >= self._test_params.E_processing_points_index[1]:
                self._test_params.E_processing_points_index = index

            else:
                self._test_result.E = ModelTriaxialDeviatorLoading.define_E(self._test_data.strain_cut,
                                                                            self._test_data.deviator_cut,
                                                                            self._test_params.E_processing_points_index)

    def set_E_processing_points(self, point_1, point_2):
        self._test_params.E_processing_points_index = (point_1, point_2)
        self._test_result.E = ModelTriaxialDeviatorLoading.define_E(self._test_data.strain_cut,
                                                                    self._test_data.deviator_cut,
                                                                    self._test_params.E_processing_points_index)

    def get_E_processing_points(self):
        return self._test_params.E_processing_points_index

    def get_processing_parameters(self):
        "Функция возвращает данные по обрезанию краев графиков"
        return {
            "cut": {
                "left": self._test_cut_position.left,
                "right": self._test_cut_position.right
            },
            "sigma_3": self._test_params.sigma_3
        }

    def set_processing_parameters(self, params):
        self._test_params.sigma_3 = params["sigma_3"]
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
        i_07qf, = np.where(deviator > qf * 0.7)
        imax, = np.where(deviator[:i_07qf[0]] > qf / 2)
        imin, = np.where(deviator[:i_07qf[0]] < qf / 2)
        imax = imax[0]
        imin = imin[-1]

        E50 = (qf / 2) / (
            np.interp(qf / 2, np.array([deviator[imin], deviator[imax]]), np.array([strain[imin], strain[imax]])))

        return E50, qf

    @staticmethod
    def define_E_true_gost(strain, deviator, sigma_3, K0):
        """Определение параметров qf и E50"""
        q_c = sigma_3 * ((1 / K0) - 1)

        if K0 == 1:
            i_start_E = 0
        else:
            i_start_E, = np.where(deviator >= q_c)
            i_start_E = i_start_E[0]

        i_end_E, = np.where(deviator >= (1.6 * q_c) + (0.6 * sigma_3))

        if len(i_end_E):
            i_end_E = i_end_E[0]
        else:
            i_end_E = len(deviator) - 1

        E = (deviator[i_end_E] - deviator[i_start_E])/(strain[i_end_E] - strain[i_start_E])
        b = q_c - strain[i_start_E] * E
        i_end_for_plot, = np.where(line(E, b, strain) >= 0.8 * np.max(deviator))

        #A1, B1 = line_approximate(strain[i_start_E:i_end_E], deviator[i_start_E:i_end_E])

        #E = (line(A1, B1, strain[i_start_E]) - line(A1, B1, strain[i_end_E])) / (strain[i_start_E] -
          #                                                                             strain[i_end_E])
        #i_end_for_plot, = np.where(line(A1, B1, strain) >= 0.9 * np.max(deviator))

        #return (round(E / 1000, 2), [strain[i_start_E[0]], strain[i_end_for_plot[0]]],
                #[line(A1, B1, strain[i_start_E[0]]), line(A1, B1, strain[i_end_for_plot[0]])])

        #return (round(E / 1000, 1), [strain[i_start_E], strain[i_end_for_plot[0]]],
                    #[line(A1, B1, strain[i_start_E]), line(A1, B1, strain[i_end_for_plot[0]])])
        return (round(E / 1000, 1), [strain[i_start_E], strain[i_end_for_plot[0]]],
                [deviator[i_start_E], line(E, b, strain[i_end_for_plot[0]])])

    @staticmethod
    def define_E(strain: np.array, deviator: np.array, E_processing_points_index: tuple):
        """Определение параметра E"""
        E = np.round((deviator[E_processing_points_index[1]] - deviator[E_processing_points_index[0]]) /
                        (strain[E_processing_points_index[1]] - strain[E_processing_points_index[0]]), 1)

        b = deviator[E_processing_points_index[0]] - strain[E_processing_points_index[0]] * E

        i_end_for_plot, = np.where(line(E, b, strain) >= 0.9 * np.max(deviator))

        if len(i_end_for_plot):
            i_end_for_plot = i_end_for_plot[0]
        else:
            i_end_for_plot = len(deviator) - 1

        return (round(E / 1000, 1), [strain[E_processing_points_index[0]], strain[i_end_for_plot]],
                [deviator[E_processing_points_index[0]], line(E, b, strain[i_end_for_plot])])

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
        strain50 = (np.interp(qf / 2, deviator, strain))
        puasson = (1 + (np.interp(strain50, strain, volume_strain) / strain50)) / 2
        return np.round(puasson, 2)

    @staticmethod
    def define_dilatancy(strain, deviator, volume_strain):
        # Найдкм угол дилатансии
        i_top = np.argmax(deviator)

        if strain[i_top] >= 0.14:
            dilatancy = None
        else:
            x_area = 0.002
            if x_area <= (strain[i_top + 1] - strain[i_top - 1]):
                x_area = (strain[i_top + 2] - strain[i_top - 2])

            i_begin, = np.where(strain >= strain[i_top] - x_area)
            i_end, = np.where(strain >= strain[i_top] + x_area)

            if len(i_end) < 1:
                i_end = [len(strain) - 1]
                i_begin = [i_top - (i_end[0] - i_top)]

            A1, B1 = line_approximate(strain[i_begin[0]:i_end[0]], volume_strain[i_begin[0]:i_end[0]])
            B1 = volume_strain[i_top] - A1 * strain[i_top]

            delta_EpsV = line(A1, B1, strain[i_end[0]]) - line(A1, B1, strain[i_begin[0]])
            delta_Eps1 = (strain[i_end[0]] - strain[i_begin[0]])

            dilatancy_value = np.rad2deg(np.arcsin(delta_EpsV / (delta_EpsV + 2 * delta_Eps1)))

            dilatancy_plot_param = int(len(volume_strain)/10)
            begin = i_top - dilatancy_plot_param
            end = i_top + dilatancy_plot_param

            if end >= len(volume_strain):
                end = len(volume_strain) - 1

            dilatancy = (
                round(dilatancy_value, 2), [strain[begin], strain[end]],
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

            while (before_loop_points_count < 3 or after_loop_points_count < 3) and point_count < 200:
                point_count = point_count + 1
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

class ModelTriaxialDeviatorLoadingSoilTest(ModelTriaxialDeviatorLoading):
    """Модель моделирования девиаторного нагружения
    Наследует обработчик и структуру данных из ModelTriaxialDeviatorLoading

    Логика работы:
        - Параметры опыта передаются в set_test_params(). Автоматически подпираются данные для отрисовки -
        self.draw_params. После чего параметры отрисовки можно считать методом get_draw_params()  передать на ползунки

        - Параметры опыта и данные отрисовки передаются в метод _test_modeling(), который моделирует кривые.

        - Метод set_draw_params(params) установливает параметры, считанные с позунков и производит отрисовку новых
         данных опыта"""
    def __init__(self):
        super().__init__()
        self._test_params = AttrDict({"qf": None,
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
                                      "volumetric_strain_xc": None,
                                      "Eur": None,
                                      "amplitude": None,
                                      "free_deviations": None})

        self.pre_defined_kr_fgs = None

    def set_test_params(self, pre_defined_kr_fgs=None):
        """Установка основных параметров опыта"""
        self._test_params.qf = statment[statment.current_test].mechanical_properties.qf

        self._test_params.sigma_3 = statment[statment.current_test].mechanical_properties.sigma_3

        if statment.general_parameters.test_mode == "Виброползучесть":
            self._test_params.E50 = statment[statment.current_test].mechanical_properties.E50 * np.random.uniform(0.9, 1.1)
        else:
            self._test_params.E50 = statment[statment.current_test].mechanical_properties.E50

        self._test_params.K0 = statment[statment.current_test].mechanical_properties.K0
        self._test_params.c = statment[statment.current_test].mechanical_properties.c
        self._test_params.fi = statment[statment.current_test].mechanical_properties.fi
        self._test_params.Eur = statment[statment.current_test].mechanical_properties.Eur
        self._test_params.data_physical = statment[statment.current_test].physical_properties
        xc, residual_strength, self.pre_defined_kr_fgs = ModelTriaxialDeviatorLoadingSoilTest.define_xc_value_residual_strength(
            statment[statment.current_test].physical_properties, statment[statment.current_test].mechanical_properties.sigma_3,
            statment[statment.current_test].mechanical_properties.qf, statment[statment.current_test].mechanical_properties.E50,
            pre_defined_kr_fgs=pre_defined_kr_fgs)
        if isinstance(statment[statment.current_test].mechanical_properties.u, list):
            self._test_params.u = None
        else:
            self._test_params.u = statment[statment.current_test].mechanical_properties.u

        if xc <= 0.14:
            xc *= np.random.uniform(0.8, 1.05)
            residual_strength *= np.random.uniform(0.8, 1)

            xc_sigma_3 = lambda sigma_3: 1-0.0005 * sigma_3
            xc *= xc_sigma_3(self._test_params.sigma_3)

            residual_strength *= xc_sigma_3(self._test_params.sigma_3)

        self._draw_params.fail_strain = xc
        self._draw_params.residual_strength_param = \
            ModelTriaxialDeviatorLoadingSoilTest.residual_strength_param_from_xc(xc)

        self._draw_params.residual_strength_param *= np.random.uniform(0.8, 1.2)

        self._draw_params.residual_strength = statment[statment.current_test].mechanical_properties.qf*residual_strength
        self._draw_params.amplitude = 0.05
        self._draw_params.free_deviations = True
        if statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res":
            self._draw_params.residual_strength = statment[statment.current_test].mechanical_properties.q_res
            self._draw_params.amplitude = 0.00001#[self._test_params.qf / 200, self._test_params.qf / 120]
            self._draw_params.free_deviations = False
        self._draw_params.qocr = 0

        if self._test_params.Eur:
            self.unloading_borders = ModelTriaxialDeviatorLoadingSoilTest.define_unloading_points(
                statment[statment.current_test].physical_properties.Il,
                statment[statment.current_test].physical_properties.type_ground,
                self._test_params.sigma_3, statment[statment.current_test].mechanical_properties.K0)

            if statment.general_parameters.test_mode == "Трёхосное сжатие с разгрузкой (plaxis)":
                self.unloading_borders = (self._test_params.qf/2, 10)

            if type(self._test_params.Eur) is bool:
                self._draw_params.Eur = ModelTriaxialDeviatorLoadingSoilTest.dependence_Eur(
                    E50=self._test_params.E50, Il=statment[statment.current_test].physical_properties.Il,
                    type_ground=statment[statment.current_test].physical_properties.type_ground)
            else:
                self._draw_params.Eur = self._test_params.Eur
        else:
            self._draw_params.Eur = None

        self._draw_params.poisson = statment[statment.current_test].mechanical_properties.poisons_ratio
        self._draw_params.dilatancy = statment[statment.current_test].mechanical_properties.dilatancy_angle

        self._draw_params.volumetric_strain_xc = (0.006 - self._draw_params.dilatancy * 0.0002) * np.random.uniform(0.9, 1.1)
        #alpha = np.deg2rad(test_params.dilatancy_angle)
        #self._draw_params.dilatancy = np.rad2deg(np.arctan(2 * np.sin(alpha) / (1 - np.sin(alpha))))
        #print(statment[statment.current_test].physical_properties.laboratory_number)
        self._test_modeling()

    def set_velocity_delta_h(self, velocity, delta_h_consolidation):
        """Передача в модель скорости нагружения и уменьшения образца на предыдущих этапах
        Скорость отвечает за количество точек на кривой девиатора и за время при сохранении словаря
        Перемещение отвечает за пересчет деформации для корретной обработки опыта после сохранения"""
        self._test_params.velocity = velocity
        self._test_params.delta_h_consolidation = delta_h_consolidation

    def get_dict(self, sample_size: Tuple[int, int] = (76, 38)):
        return ModelTriaxialDeviatorLoadingSoilTest.dictionary_deviator_loading(self._test_data.strain,
                                                                                self._test_data.deviator,
                                    self._test_data.pore_volume_strain, self._test_data.cell_volume_strain,
                                    self._test_data.reload_points, pore_pressure=self._test_data.pore_pressure,
                                    time=self._test_data.time, velocity=self._test_params.velocity,
                                    delta_h_consolidation = self._test_params.delta_h_consolidation,
                                    sample_size=sample_size)

    def get_draw_params(self):
        """Возвращает параметры отрисовки для установки на ползунки"""
        Eur = {"value": self._draw_params.Eur, "borders": [self._draw_params.Eur/2, self._draw_params.Eur*5]} if self._draw_params.Eur else {"value": None}
        #print(self._test_params.__dict__)

        params = {"fail_strain": {"value": self._draw_params.fail_strain, "borders": [0.03, 0.15]},
                  "residual_strength_param": {"value": self._draw_params.residual_strength_param, "borders": [0.05, 0.6]},
                  "residual_strength": {"value": self._draw_params.residual_strength,
                                        "borders": [self._test_params.qf*0.3, self._test_params.qf]},
                  "qocr": {"value": self._draw_params.qocr+1, "borders": [0.0, self._test_params.qf]},
                  "poisson": {"value": self._draw_params.poisson, "borders": [0.25, 0.45]},
                  "dilatancy": {"value": self._draw_params.dilatancy, "borders": [1, 25]},
                  "volumetric_strain_xc": {"value": self._draw_params.volumetric_strain_xc, "borders": [0, 0.008]},
                  "Eur": Eur,
                  "amplitude": {"value": self._draw_params.amplitude, "borders": [0.000001, 0.1]}}
        return params

    def set_draw_params(self, params):
        """Устанавливает переданные параметры отрисовки, считанные с ползунков, на модель"""
        self._draw_params.fail_strain = params["fail_strain"]
        self._draw_params.residual_strength_param = params["residual_strength_param"]
        self._draw_params.residual_strength = params["residual_strength"]
        self._draw_params.qocr = params["qocr"]
        self._draw_params.poisson = params["poisson"]
        self._draw_params.dilatancy = params["dilatancy"]
        self._draw_params.volumetric_strain_xc = params["volumetric_strain_xc"]
        self._draw_params.Eur = params["Eur"]
        self._draw_params.amplitude = params["amplitude"]
        """self._draw_params.dilatancy = np.rad2deg(np.arctan(2 * np.sin(np.deg2rad(params["dilatancy"])) /
                                                           (1 - np.sin(np.deg2rad(params["dilatancy"])))))"""

        self._test_modeling()

    def _test_modeling(self):
        """Функция моделирования опыта"""
        # Время проведения опыта

        if self._test_params.velocity is None:
            print("Ошибка в обработки консолидации")
        max_time = int((0.15 * (76 - self._test_params.delta_h_consolidation))/self._test_params.velocity)
        if max_time <= 50:
            max_time = int(np.random.uniform(50, 70))

        if max_time >= 2800:
            max_time = int(np.random.uniform(2500, 3000))

        dilatancy = np.rad2deg(np.arctan(2 * np.sin(np.deg2rad(self._draw_params.dilatancy)) /
                             (1 - np.sin(np.deg2rad(self._draw_params.dilatancy)))))

        if self._test_params.Eur:
            self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
            self._test_data.cell_volume_strain, self._test_data.reload_points, self._test_data.time, begin = curve(self._test_params.qf, self._test_params.E50, xc=self._draw_params.fail_strain,
                                                                x2=self._draw_params.residual_strength_param,
                                                                qf2=self._draw_params.residual_strength,
                                                                qocr=self._draw_params.qocr,
                                                                amplitude=(self._draw_params.amplitude,
                                                                           self._draw_params.free_deviations),
                                                                m_given=self._draw_params.poisson,
                                                                max_time=max_time,
                                                                angle_of_dilatacy=dilatancy,
                                                                Eur=self._draw_params.Eur,
                                                                y_rel_p=self.unloading_borders[0],
                                                                point2_y=self.unloading_borders[1],
                                                                v_d_xc=-self._draw_params.volumetric_strain_xc,
                                                                U=self._test_params.u)
        else:
            self._test_data.strain, self._test_data.deviator, self._test_data.pore_volume_strain, \
            self._test_data.cell_volume_strain, self._test_data.reload_points, self._test_data.time, begin = curve(
                self._test_params.qf, self._test_params.E50, xc=self._draw_params.fail_strain,
                x2=self._draw_params.residual_strength_param,
                qf2=self._draw_params.residual_strength,
                qocr=self._draw_params.qocr,
                amplitude=(self._draw_params.amplitude, self._draw_params.free_deviations),
                m_given=self._draw_params.poisson,
                 max_time=max_time,
                angle_of_dilatacy=dilatancy,
                v_d_xc=-self._draw_params.volumetric_strain_xc,
                U=None)

        self._test_data.deviator = np.round(self._test_data.deviator, 3)
        self._test_data.strain = np.round(
            self._test_data.strain * (76 - self._test_params.delta_h_consolidation)/ (
                                             76 - self._test_params.delta_h_consolidation), 6)

        # Объем штока
        V = np.pi * 10 * 10 * self._test_data.cell_volume_strain * 76
        strain_V = V/(np.pi * 19 * 19 * 76)

        self._test_data.cell_volume_strain = self._test_data.cell_volume_strain + strain_V


        self._test_data.pore_volume_strain = np.round((self._test_data.pore_volume_strain * np.pi * 19 ** 2 * (
                    76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                    76 - self._test_params.delta_h_consolidation)), 6)
        self._test_data.cell_volume_strain = np.round((self._test_data.cell_volume_strain * np.pi * 19 ** 2 * (
                    76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                    76 - self._test_params.delta_h_consolidation)), 6)

        if statment.general_parameters.test_mode != "Трёхосное сжатие (F, C) res":
            i_end = ModelTriaxialDeviatorLoadingSoilTest.define_final_loading_point(self._test_data.deviator, 0.08 + np.random.uniform(0.01, 0.03))
            self._test_data.time = self._test_data.time[:i_end]
            self._test_data.strain = self._test_data.strain[:i_end]
            self._test_data.deviator = self._test_data.deviator[:i_end]
            self._test_data.pore_volume_strain = self._test_data.pore_volume_strain[:i_end]
            self._test_data.cell_volume_strain = self._test_data.cell_volume_strain[:i_end]

        if self._test_params.u:
            self._test_data.pore_pressure = ModelTriaxialDeviatorLoadingSoilTest.define_pore_pressure_array(
                self._test_data.strain, begin, self._test_params.u,
                self._test_data.deviator[begin]*np.random.uniform(1, 2))
        else:
            self._test_data.pore_pressure = np.random.uniform(-1, 1, len(self._test_data.strain))

        #plt.plot(self._test_data.strain, self._test_data.pore_pressure)
       # plt.plot(self._test_data.strain, self._test_data.deviator)
        #plt.show()

        # Действия для того, чтобы полученный массив данных записывался в словарь для последующей обработки
        # k = np.max(np.round(self._test_data.deviator[begin:] - self._test_data.deviator[begin], 3)) / self._test_params.qf
        # self._test_data.deviator = np.round(self._test_data.deviator/k, 3)

        self._test_data.strain = np.round(
            self._test_data.strain * (76 - self._test_params.delta_h_consolidation) / (
                    76 - self._test_params.delta_h_consolidation), 6)

        self._test_data.pore_volume_strain = np.round((self._test_data.pore_volume_strain * np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)), 6)
        self._test_data.cell_volume_strain = np.round((self._test_data.cell_volume_strain * np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)) / (np.pi * 19 ** 2 * (
                76 - self._test_params.delta_h_consolidation)), 6)

        self._test_data.volume_strain = self._test_data.pore_volume_strain
        #i_end, = np.where(self._test_data.strain > self._draw_params.fail_strain + np.random.uniform(0.03, 0.04))
        #if len(i_end):
            #self.change_borders(begin, i_end[0])
        #else:
        self.change_borders(begin, len(self._test_data.volume_strain))
        #print(statment[statment.current_test].physical_properties.laboratory_number, self._test_result["E50"])
        #print(self._test_params.__dict__)

    def get_cvi_data(self, points: int = 10):
        """Возвращает параметры отрисовки для установки на ползунки"""
        strain_array = []
        main_stress_array = []
        volume_strain_array = []
        argmax = np.argmax(self._test_data.deviator_cut)

        index = [int(i) for i in range(0, argmax, int(argmax/(points-2)))] + [argmax]

        for i in index:
            strain_array.append(np.round(self._test_data.strain_cut[i], 3))
            main_stress_array.append(np.round((self._test_data.deviator_cut[i] / 1000) + self._test_params.sigma_3/1000, 3))
            volume_strain_array.append(np.round(self._test_data.volume_strain_cut[i], 3))

        return np.array(strain_array), np.array(main_stress_array), np.array(volume_strain_array)

    def get_duration(self):
        return np.max(self._test_data.time)#)int((self._test_data.strain[-1] * (76 - self._test_params.delta_h_consolidation)) / self._test_params.velocity)

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
        clay_k_q_min = 0.6  # значения k_q соотв. минимальному ILприведенн
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
    def dependence_Eur_old(E50: float, qf: float, Il: float, initial_unloading_deviator: float) -> float:
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
    def dependence_Eur(E50: float, Il: float, type_ground: int) -> float:
        """ Определение модуля Eur
        :param E50: модуль деформации
        :param Il: показатель текучести
        :param type_ground: гран состав
        :return: Eur"""

        if Il == None:
            Il = np.random.uniform(0.25, 0.75)

        def dependence_Eur_of_clay():
            if type_ground == 6 or type_ground == 7 or type_ground == 8:
                if Il <= 0:
                    return np.random.uniform(2.5, 3.5)
                elif Il > 0 and Il <= 0.25:
                    return np.random.uniform(3, 5)
                elif Il > 0.25 and Il <= 0.5:
                    return np.random.uniform(4, 7)
                elif Il > 0.5 and Il <= 0.75:
                    return np.random.uniform(4.8, 7.3)
                elif Il > 0.75:
                    return np.random.uniform(5.8, 9)

        dependence_Eur = {
            1: np.random.uniform(3, 4),  # Песок гравелистый
            2: np.random.uniform(3.3, 4.3),  # Песок крупный
            3: np.random.uniform(4, 5),  # Песок средней крупности
            4: np.random.uniform(4, 5.5),  # Песок мелкий
            5: np.random.uniform(4, 5.5),  # Песок пылеватый
            6: dependence_Eur_of_clay(),  # Супесь
            7: dependence_Eur_of_clay(),  # Суглинок
            8: dependence_Eur_of_clay(),  # Глина
            9: np.random.uniform(3, 5),  # Торф
        }

        return E50 * dependence_Eur[type_ground]

    @staticmethod
    def xc_from_qf_e_if_is(sigma_3, type_ground, e, Ip, Il, Ir=None):
        """Функция находит деформацию пика девиаорного нагружения в зависимости от qf и E50, если по параметрам материала
        пик есть, если нет, возвращает xc = 0.15. Обжимающее напряжение должно быть в кПа"""
        none_to_zero = lambda x: 0 if not x else x
        Ip = Ip if Ip else 0
        Il = Il if Il else 0.5
        e0 = e if e else 0.65
        Ir = Ir if Ir else 0

        _is_random = False

        if Il > 0.35 and Ir >= 50:
            return 0, False

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

        sigma3mor = sigma_3 / 1000  # так как дается в КПа, а необходимо в МПа
        # if type_ground == 3 or type_ground == 4:  # Процентное содержание гранул размером 10 и 5 мм больше половины
        #     kr_fgs = 1
        if none_to_zero(Ip) == 0:  # число пластичности. Пески (и торф?)
            if dens_sand == 1 or type_ground == 1:  # любой плотный или гравелистый песок
                kr_fgs = 1
            elif type_ground == 2:  # крупный песок
                if sigma3mor <= 0.1:
                    kr_fgs = round(np.random.uniform(0, 1))
                    _is_random = True
                else:
                    kr_fgs = 1
            elif type_ground == 3:  # песок средней групности
                if sigma3mor <= 0.15 and dens_sand == 3:  # песок средней крупности рыхлый
                    kr_fgs = 0
                elif sigma3mor <= 0.15 and dens_sand == 2:  # песок средней крупности средней плотности
                    kr_fgs = round(np.random.uniform(0, 1))
                    _is_random = True
                else:  # песок средней групности и sigma3>0.15
                    kr_fgs = 1
            elif type_ground == 4:  # мелкий песок
                if sigma3mor < 0.1 and dens_sand == 3:  # мелкий песок рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (sigma3mor <= 0.15 and dens_sand == 2):
                    kr_fgs = round(np.random.uniform(0, 1))  # мелкий песок рыхлый s3<=0.2 и средней плотности s3<=0.15
                    _is_random = True
                else:  # мелкий песок рыхлый s3>=0.2 и средней плотности s3>=0.15 (плотный закрыт раньше)
                    kr_fgs = 1
            elif type_ground == 5:  # песок пылеватый
                if sigma3mor < 0.1 and dens_sand == 3:  # песок пылеватый рыхлый s3<0.1
                    kr_fgs = 0
                elif (0.1 <= sigma3mor <= 0.2 and dens_sand == 3) or (
                        sigma3mor <= 0.1 and dens_sand == 2):  # песок пылева-
                    kr_fgs = round(
                        np.random.uniform(0, 1))  # тый рыхлый 0.1<=s3<=0.2 и пылеватый средней плотности s3<=0.1
                    _is_random = True
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
                _is_random = True
            else:  # <=0 твердый
                kr_fgs = 1

        elif Ip > 7:  # суглинок и глина
            if Il > 0.5:  # показатель текучести.от 0.5 мягко- и текучепласт., текучий (для суглинков и глины)
                kr_fgs = 0
            elif 0.25 < Il <= 0.5:  # от 0.25 до 0.5 тугопластичный (для суглинков и глины)
                kr_fgs = round(np.random.choice([0, 1], p=[0.7, 0.3]))
                _is_random = True
            else:  # меньше 0.25 твердый и полутвердый (для суглинков и глины)
                kr_fgs = 1
        else:
            kr_fgs = 0
        return kr_fgs, _is_random

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
    def define_xc_value_residual_strength(data_phiz, sigma_3, qf, E, pre_defined_kr_fgs=None):

        xc = 1

        _defined_kr_fgs, is_random = ModelTriaxialDeviatorLoadingSoilTest.xc_from_qf_e_if_is(sigma_3,
                                                                                             data_phiz.type_ground,
                                                                                             data_phiz.e,
                                                                                             data_phiz.Ip,
                                                                                             data_phiz.Il)

        if not pre_defined_kr_fgs:
            xc = _defined_kr_fgs
        elif pre_defined_kr_fgs == 1:
            # для опыта Трёхосное сжатие (F, C) res если отсутствие пика выпадает не из генерации случайного числа,
            # то пика не должно быть, для всех остальных опытов при наличии предопределенного kr выбираем его
            if (statment.general_parameters.test_mode == "Трёхосное сжатие (F, C) res"
                    and not is_random and _defined_kr_fgs == 0):
                xc = _defined_kr_fgs
            else:
                xc = pre_defined_kr_fgs

        if xc:
            xc = ModelTriaxialDeviatorLoadingSoilTest.define_xc_qf_E(qf, E)
            pre_defined_kr_fgs = 1
        else:
            xc = 0.15
            pre_defined_kr_fgs = None

        if xc != 0.15:
            residual_strength = ModelTriaxialDeviatorLoadingSoilTest.define_k_q(data_phiz.Il, data_phiz.e, sigma_3)
        else:
            residual_strength = 0.95

        return xc, residual_strength, pre_defined_kr_fgs

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
    def dictionary_deviator_loading(strain, deviator, pore_volume_strain, cell_volume_strain, indexs_loop,
                                    pore_pressure, time, velocity=1, delta_h_consolidation=0,
                                    sample_size: Tuple[int, int] = (76, 38)):
        """Формирует словарь девиаторного нагружения"""
        index_unload, = np.where(strain >= strain[-1] * 0.92)  # индекс абциссы конца разгрузки
        x_unload_p = strain[index_unload[0]]  # деформация на конце разгрузки
        y_unload_p = - 0.05 * max(deviator)  # девиатор на конце разгрузки

        x_unload = np.linspace(strain[-1], x_unload_p, 8 + 1)  # массив деформаций разгрузки с другим шагом
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [y_unload_p, deviator[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, deviator[-1] * 200)]))
        y_unload = spl(x_unload)  # массив значений девиатора при разгрузке
        z_unload_p = min(pore_volume_strain) * 1.05  # обьемная деформация на конце разгрузки
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [z_unload_p, pore_volume_strain[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, abs(pore_volume_strain[-1] - z_unload_p) * 200)]))
        unload_pore_volume_strain = spl(x_unload)  # массив обьемных деформаций при разгрузке

        y_unload = y_unload + np.random.uniform(-1, 1, len(y_unload))  # наложение  шума на разгрузку
        y_unload = discrete_array(y_unload, 1)  # наложение ступенатого шума на разгрузку

        z_unload_p = min(cell_volume_strain) * 1.05
        spl = make_interp_spline([x_unload_p, strain[-1]],
                                             [z_unload_p, cell_volume_strain[-1]], k=3,
                                             bc_type=([(1, 0)], [(1, abs(cell_volume_strain[-1] - z_unload_p) * 200)]))
        unload_cell_volume_strain = spl(x_unload)

        # Расширяем массивы на разгрузку
        cell_volume_strain = np.hstack((cell_volume_strain, unload_cell_volume_strain[1:]))
        strain = np.hstack((strain, x_unload[1:]))
        deviator = np.hstack((deviator, y_unload[1:]))
        pore_volume_strain = np.hstack((pore_volume_strain, unload_pore_volume_strain[1:]))

        end_unload = len(strain) - len(x_unload) + 1  # индекс конца разгрузки в масииве

        # запись девиаторного нагружения в файл
        time = np.hstack((time, deviator[-1] + np.linspace(1, len(y_unload[1:]), len(y_unload[1:]))))

        action = ['WaitLimit' for __ in range(len(time))]
        pore_pressure = np.hstack((
            pore_pressure,
            np.linspace(pore_pressure[-1], pore_pressure[-1] * np.random.uniform(0.3, 0.5), len(time) - len(pore_pressure))
        ))

        if indexs_loop[0] != 0:
            for i in range(len(action)):
                if i >= indexs_loop[0] and i < indexs_loop[1]:
                    action[i] = 'CyclicUnloading'
                elif i >= indexs_loop[1] and i <= indexs_loop[2]:
                    action[i] = 'CyclicLoading'
                elif i >= end_unload:
                    action[i] = 'Unload'
        else:
            for i in range(len(action)):
                if i >= end_unload:
                    action[i] = 'Unload'

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
            "SampleHeight_mm": np.round(np.full(len(time), sample_size[0])),
            "SampleDiameter_mm": np.round(np.full(len(time), sample_size[1])),
            "Deviator_kPa": np.round(deviator, 4),
            "VerticalDeformation_mm": strain * (sample_size[0] - delta_h_consolidation),
            "CellPress_kPa": np.full(len(time), 0) + np.random.uniform(-0.1, 0.1, len(time)),
            "CellVolume_mm3": (cell_volume_strain * np.pi * 19 ** 2 * (sample_size[0] - delta_h_consolidation)),
            "PorePress_kPa": pore_pressure,
            "PoreVolume_mm3": pore_volume_strain * np.pi * 19 ** 2 * (sample_size[0] - delta_h_consolidation),
            "VerticalPress_kPa": deviator + np.random.uniform(-0.1, 0.1, len(time)),
            "Trajectory": np.full(len(time), 'CTC')}

        return data

    @staticmethod
    def define_unloading_points(Il, type_ground, sigma_3: float, K0: float) -> Tuple[float, float]:
        """ Рассчет начала разгрузки в зависимости от грансостава и среднеобжимающего давления
            :param physical_data: словарь с физическими параметрами
            :param sigma_1: эффективное значение sigma_3c
            :return: девиатор начала разгрузки"""

        sigma_1 = sigma_3/K0
        sigma_mean = (sigma_1 + 2*sigma_3)/3
        q_c = sigma_1 - sigma_3#sigma_3 * (1/K0-1)

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
        deviator_start_unloading = lambda step_1, step_2: sigma_mean * (step_1 + step_2) + q_c

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

        return (
        dependence_deviator_start_unloading_on_type_ground[type_ground], 10 + q_c)

    @staticmethod
    def define_final_loading_point(deviator: List, persent: float) -> int:
        """ Рассчет начала разгрузки в зависимости от грансостава и среднеобжимающего давления
            :param deviator: массив девиаторного нагружения
            :param persent: процент падения девиатора (в сотых)
            :return: индекс точки падения девиатора на заданный процент"""

        i_max = np.argmax(deviator)

        i, = np.where(deviator[i_max:] <= (1 - persent) * np.max(deviator))

        return i[0] + i_max if len(i) != 0 else len(deviator)


if __name__ == '__main__':

    file = r"C:\Users\Пользователь\PycharmProjects\Willie\Test.1.log"
    file = r"Z:\МДГТ - Механика\3. Трехосные испытания\1365\Test\Test.1.log"

    """a = ModelTriaxialDeviatorLoading()
    from static_loading.triaxial_static_loading_test_model import ModelTriaxialStaticLoad
    a.set_test_data(ModelTriaxialStaticLoad.open_geotek_log(file)["deviator_loading"])
    a.plotter()
    plt.show()"""
    a = ModelTriaxialDeviatorLoadingSoilTest()
    statment.load(r"C:\Users\Пользователь\Desktop\test\Трёхосное сжатие (E).pickle")
    statment.current_test = "21-21-20"
    a.set_test_params()
    a.plotter()
    plt.show()